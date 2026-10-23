"""Baker Hughes North America rig count.

rigcount.bakerhughes.com blocks scripted downloads (HTTP 403) and its spreadsheet URLs
change weekly, so the loader tries, in order:
1. a manually downloaded file at ``data/manual/rig_count.(csv|xlsx)`` (or ``RIG_COUNT_FILE``);
2. the EIA mirror of the Baker Hughes count (needs ``EIA_API_KEY``);
3. otherwise skips and returns None. It never synthesises data.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from src.data import cache, eia

log = logging.getLogger(__name__)
SOURCE = "rigcount"
MANUAL_DIR = cache.ROOT / "data" / "manual"


def _manual_file() -> Path | None:
    env = os.environ.get("RIG_COUNT_FILE")
    candidates = [Path(env)] if env else []
    candidates += [MANUAL_DIR / "rig_count.csv", MANUAL_DIR / "rig_count.xlsx"]
    return next((p for p in candidates if p.exists()), None)


def load_rig_count(refresh: bool = False) -> pd.DataFrame | None:
    path = _manual_file()
    if path is not None:
        df = pd.read_csv(path) if path.suffix == ".csv" else pd.read_excel(path)
        return cache.cached(SOURCE, "manual", lambda: df, refresh=True, url=str(path))
    df = eia.load_series("rotary_rigs_us", refresh=refresh)
    if df is None:
        log.info("Rig count unavailable: no manual file and no EIA_API_KEY")
    return df
