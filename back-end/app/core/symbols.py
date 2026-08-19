"""Fixed trading-pair universe loaded from versioned config.

The list lives in ``app/feature_engineering/config/symbols.yml`` so the daily
jobs, the feature pipelines and the historical backfill all target the same
symbols. When the file is absent or empty, callers fall back to the dynamic
top-20-by-volume selection.
"""

from functools import lru_cache
from pathlib import Path

import yaml

_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "feature_engineering" / "config" / "symbols.yml"
)


@lru_cache(maxsize=1)
def load_tracked_symbols() -> tuple[str, ...]:
    """Return the fixed symbol list, or an empty tuple when not configured.

    Returns:
        Ordered, deduplicated, uppercased symbols from ``symbols.yml``;
        an empty tuple if the file is missing or has no ``symbols`` entries.
    """
    if not _CONFIG_PATH.exists():
        return ()
    loaded = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    entries = loaded.get("symbols") or []
    return tuple(
        dict.fromkeys(
            entry.strip().upper() for entry in entries if isinstance(entry, str) and entry.strip()
        )
    )
