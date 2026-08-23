"""Check that the Firestore rules deployed to the project match firestore.rules.

Read-only: it never deploys anything. A rules file sitting in the repo proves
nothing about what the project actually enforces, so this closes the loop.

Usage (from back-end/):
    uv run python scripts/check_firestore_rules.py [caminho/da/chave-admin.json]

This is an ops check, not a runtime path: reading rules needs a credential with
`firebaserules.viewer` (the Firebase Admin SDK service agent has it). The API's
runtime service account deliberately does NOT — it only carries datastore.user
and firebaseauth.admin — so pass an admin key explicitly, or point
FIREBASE_CREDENTIALS_PATH at one when running this.

Exit code 0 when they match, 1 when they drift, 2 on a configuration error.

To deploy after changing firestore.rules:
    firebase deploy --only firestore:rules
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import google.auth.transport.requests as google_requests
from google.oauth2 import service_account

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import get_settings  # noqa: E402

_RULES_FILE = Path(__file__).resolve().parents[1] / "firestore.rules"
_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
_RELEASE = "cloud.firestore"


def _credentials_info(explicit_path: str | None = None) -> dict:
    """Load the service account JSON from an explicit path or from settings."""
    if explicit_path:
        return json.loads(Path(explicit_path).read_text(encoding="utf-8"))
    settings = get_settings()
    if settings.FIREBASE_CREDENTIALS_PATH:
        return json.loads(Path(settings.FIREBASE_CREDENTIALS_PATH).read_text(encoding="utf-8"))
    if settings.FIREBASE_CREDENTIALS_JSON:
        return json.loads(settings.FIREBASE_CREDENTIALS_JSON)
    raise SystemExit("Configure FIREBASE_CREDENTIALS_PATH ou FIREBASE_CREDENTIALS_JSON.")


def _deployed_rules(session, project: str) -> str:
    """Fetch the source of the ruleset currently released for Firestore."""
    releases = session.get(
        f"https://firebaserules.googleapis.com/v1/projects/{project}/releases", timeout=30
    )
    if releases.status_code == 403:
        raise SystemExit(
            "403 ao ler as regras: esta credencial nao tem 'firebaserules.viewer'.\n"
            "A chave de runtime da API nao tem (e nao deve ter) esse papel. Rode com uma\n"
            "credencial administrativa:\n"
            "    uv run python scripts/check_firestore_rules.py caminho/da/chave-admin.json"
        )
    releases.raise_for_status()
    for release in releases.json().get("releases", []):
        if release.get("name", "").split("/")[-1] == _RELEASE:
            ruleset = session.get(
                f"https://firebaserules.googleapis.com/v1/{release['rulesetName']}", timeout=30
            )
            ruleset.raise_for_status()
            files = ruleset.json().get("source", {}).get("files", [])
            return "".join(file.get("content", "") for file in files)
    raise SystemExit(f"Nenhum release '{_RELEASE}' encontrado no projeto {project}.")


def _normalize(rules: str) -> str:
    """Reduce rules to what is actually enforced.

    Comments and whitespace do not change enforcement, and the deployed copy
    may have been pasted through the console without them. Comparing the
    normalized form keeps the check about semantics, not formatting.
    """
    lines = []
    for raw_line in rules.splitlines():
        line = raw_line.split("//", 1)[0].strip()
        if line:
            lines.append(" ".join(line.split()))
    return "\n".join(lines)


def main() -> int:
    explicit_path = sys.argv[1] if len(sys.argv) > 1 else None
    info = _credentials_info(explicit_path)
    project = info["project_id"]
    credentials = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
    session = google_requests.AuthorizedSession(credentials)

    deployed = _deployed_rules(session, project).strip()
    local = _RULES_FILE.read_text(encoding="utf-8").strip()
    if _normalize(deployed) == _normalize(local):
        print(f"OK: as regras publicadas em '{project}' aplicam o mesmo que firestore.rules.")
        if deployed != local:
            print("(diferem apenas em comentarios/espacos)")
        return 0

    print(
        f"DRIFT: as regras publicadas em '{project}' diferem de firestore.rules.", file=sys.stderr
    )
    print("Rode: firebase deploy --only firestore:rules", file=sys.stderr)
    print("\n--- publicado ---\n" + deployed, file=sys.stderr)
    print("\n--- repositorio ---\n" + local, file=sys.stderr)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        print(f"Falha ao verificar as regras: {error}", file=sys.stderr)
        sys.exit(2)
