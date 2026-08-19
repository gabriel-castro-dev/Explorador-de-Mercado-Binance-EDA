"""Dump the API's OpenAPI schema to a JSON file (input for the front-end type codegen).

Usage (from back-end/):
    uv run python scripts/export_openapi.py ../front-end/openapi/openapi.json

Placeholder env vars are injected when absent so the export works offline (no .env needed);
``create_app()`` only reads settings, it does not connect to Supabase/Binance.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_PLACEHOLDERS = {
    "SUPABASE_URL": "https://placeholder.supabase.co",
    "SUPABASE_KEY": "placeholder",
    "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_placeholder",
    "BINANCE_API_KEY": "placeholder",
    "BINANCE_API_SECRET": "placeholder",
}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: export_openapi.py <output.json>", file=sys.stderr)
        return 2
    for key, value in _PLACEHOLDERS.items():
        os.environ.setdefault(key, value)

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.main import create_app  # noqa: E402 — after env/sys.path setup

    schema = create_app().openapi()
    output = Path(argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OpenAPI schema written to {output} ({len(schema.get('paths', {}))} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
