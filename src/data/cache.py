"""File cache for raw pulls.

Every pull is written to ``data/raw/<source>/<name>__<fetch-date>.csv`` with a
``.meta.json`` sidecar recording the fetch timestamp (UTC), URL and row count.
Re-reads use the newest file if it is younger than ``max_age_days``.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def raw_dir() -> Path:
    return Path(os.environ.get("ESD_RAW_DIR", ROOT / "data" / "raw"))


def safe_name(name: str) -> str:
    return _SAFE.sub("_", name).strip("_")


def raw_path(source: str, name: str, fetch_date: date | None = None) -> Path:
    fetch_date = fetch_date or datetime.now(timezone.utc).date()
    return raw_dir() / source / f"{safe_name(name)}__{fetch_date.isoformat()}.csv"


def _fetch_date(path: Path) -> date:
    return date.fromisoformat(path.stem.rsplit("__", 1)[1])


def latest(source: str, name: str) -> Path | None:
    files = sorted((raw_dir() / source).glob(f"{safe_name(name)}__*.csv"), key=_fetch_date)
    return files[-1] if files else None


def write(source: str, name: str, df: pd.DataFrame, url: str | None = None) -> Path:
    path = raw_path(source, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    meta = {
        "source": source,
        "name": name,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "url": url,
        "rows": int(len(df)),
    }
    path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2))
    return path


def cached(
    source: str,
    name: str,
    fetch: Callable[[], pd.DataFrame | None],
    max_age_days: int = 1,
    refresh: bool = False,
    url: str | None = None,
) -> pd.DataFrame | None:
    """Return the cached frame if fresh, else call ``fetch`` and cache the result.

    If ``fetch`` fails (returns None) a stale cached copy is returned rather than nothing.
    """
    path = latest(source, name)
    today = datetime.now(timezone.utc).date()
    if path and not refresh and (today - _fetch_date(path)).days <= max_age_days:
        return pd.read_csv(path)
    df = fetch()
    if df is None or df.empty:
        return pd.read_csv(path) if path else None
    write(source, name, df, url=url)
    return df
