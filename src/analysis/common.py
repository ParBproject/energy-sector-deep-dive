"""Helpers shared by the analyses. Everything reads the committed snapshot only."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.data import snapshot, universe
from src.data.cache import ROOT

RESULTS = ROOT / "results"
OIL, MARKET, SECTOR = "CL=F", "SPY", "XLE"
SEGMENT_ORDER = ["majors", "upstream", "midstream", "refiners", "services"]


def as_of_date() -> str:
    """Analysis date = last trading day in the price snapshot."""
    return str(snapshot.prices().index.max().date())


def segment_map() -> dict[str, str]:
    c = universe.companies()
    return dict(zip(c["ticker"], c["segment"], strict=True))


def segment_labels() -> dict[str, str]:
    c = universe.companies().drop_duplicates("segment")
    return dict(zip(c["segment"], c["segment_label"], strict=True))


def daily_returns() -> pd.DataFrame:
    """Simple daily returns of adjusted closes.

    CL=F settled at -$37.63 on 2020-04-20; returns touching a non-positive price are set to
    NaN rather than computed, since a percentage change through zero is meaningless.
    """
    p = snapshot.prices()
    r = p.pct_change(fill_method=None)
    bad = (p <= 0) | (p.shift(1) <= 0)
    r = r.mask(bad)
    return r.iloc[1:]


def segment_returns(r: pd.DataFrame | None = None) -> pd.DataFrame:
    """Equal-weighted daily segment returns (mean of available members each day)."""
    r = daily_returns() if r is None else r
    seg = segment_map()
    out = {s: r[[t for t, g in seg.items() if g == s]].mean(axis=1) for s in SEGMENT_ORDER}
    return pd.DataFrame(out)


def clean(obj):
    """Round floats to 6 dp and turn NaN into None so results JSON is stable and valid."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [clean(v) for v in obj]
    if isinstance(obj, float | np.floating):
        return None if not np.isfinite(obj) else round(float(obj), 6)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, pd.Timestamp):
        return str(obj.date())
    return obj


def write_json(name: str, payload: dict) -> Path:
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / name
    path.write_text(json.dumps(clean(payload), indent=2) + "\n")
    return path


def read_json(name: str) -> dict:
    return json.loads((RESULTS / name).read_text())
