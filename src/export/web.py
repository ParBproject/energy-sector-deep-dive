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


def export() -> dict:
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(RESULTS / name, WEB_DATA / name)
    m = snapshot.manifest()
    index = {
        "as_of": json.loads((RESULTS / "returns.json").read_text())["as_of"],
        "snapshot_built_at": m["built_at"],
        "files": FILES,
        "sources": {
            "market_sizing.json": "SEC EDGAR 10-K XBRL (point-in-time)",
            "returns.json": "yfinance adjusted closes",
            "fundamentals.json": "SEC EDGAR 10-K XBRL + yfinance",
            "clustering.json": "derived: results/returns.json + fundamentals.json",
            "factor_model.json": "yfinance, FRED DGS10, Fama-French",
            "scenarios.json": "yfinance, Fama-French, commodity-price-forecaster (vendored)",
        },
    }
    (WEB_DATA / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    return index


if __name__ == "__main__":
    print(json.dumps(export(), indent=2))
