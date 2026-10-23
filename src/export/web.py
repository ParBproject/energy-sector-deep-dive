"""Copy pinned results into web/public/data/ for the explorer (``make export``)."""

from __future__ import annotations

import json
import shutil

from src.analysis.common import RESULTS, ROOT
from src.data import snapshot

WEB_DATA = ROOT / "web" / "public" / "data"
FILES = [
    "market_sizing.json",
    "returns.json",
    "fundamentals.json",
    "clustering.json",
    "factor_model.json",
    "scenarios.json",
]


def timeseries() -> dict:
    """Weekly (Friday) total-return indices = 100 at the first week, for the hero chart."""
    import numpy as np

    from src.analysis.common import SEGMENT_ORDER, daily_returns, segment_returns

    r = daily_returns()
    weekly = (1 + r).resample("W-FRI").prod(min_count=1)
    seg = (1 + segment_returns(r)).resample("W-FRI").prod(min_count=1)
    idx = lambda w: (100 * w.fillna(1).cumprod()).round(2)  # noqa: E731
    out = {
        "dates": [d.strftime("%Y-%m-%d") for d in weekly.index],
        "base": 100,
        "frequency": "weekly, Friday close",
        "segments": {},
        "symbols": {},
    }
    for s in SEGMENT_ORDER:
        out["segments"][s] = idx(seg[s]).tolist()
    for c in weekly.columns:
        out["symbols"][c] = [None if np.isnan(v) else v for v in idx(weekly[c]).tolist()]
    return out


def export() -> dict:
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(RESULTS / name, WEB_DATA / name)
    (WEB_DATA / "timeseries.json").write_text(json.dumps(timeseries(), separators=(",", ":")))
    m = snapshot.manifest()
    index = {
        "as_of": json.loads((RESULTS / "returns.json").read_text())["as_of"],
        "snapshot_built_at": m["built_at"],
        "files": [*FILES, "timeseries.json"],
        "sources": {
            "market_sizing.json": "SEC EDGAR 10-K XBRL (point-in-time)",
            "returns.json": "yfinance adjusted closes",
            "fundamentals.json": "SEC EDGAR 10-K XBRL + yfinance",
            "clustering.json": "derived: results/returns.json + fundamentals.json",
            "factor_model.json": "yfinance, FRED DGS10, Fama-French",
            "scenarios.json": "yfinance, Fama-French, commodity-price-forecaster (vendored)",
            "timeseries.json": "yfinance adjusted closes, weekly total-return index",
        },
    }
    (WEB_DATA / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    return index


if __name__ == "__main__":
    print(json.dumps(export(), indent=2))
