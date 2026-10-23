"""Fetch every source through the cached loaders and write the compact committed snapshot."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

import pandas as pd

from src.data import edgar, eia_snapshot, famafrench, fred, prices, rigs, universe
from src.data.snapshot import SNAPSHOT_DIR

START = "2015-01-01"
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    status: dict[str, dict] = {}

    long = prices.load_prices(universe.all_price_symbols(), start=START)
    wide = prices.to_wide(long).round(4)
    wide.to_csv(SNAPSHOT_DIR / "prices_daily.csv.gz", index_label="date")
    status["yfinance"] = {
        "ok": True,
        "symbols": list(wide.columns),
        "first": str(wide.index.min().date()),
        "last": str(wide.index.max().date()),
        "first_valid": {c: str(wide[c].first_valid_index().date()) for c in wide},
    }

    fr = fred.load_many(start=START)
    fr.to_csv(SNAPSHOT_DIR / "fred.csv.gz", index=False)
    status["fred"] = {
        "ok": not fr.empty,
        "series": sorted(fr["series_id"].unique()),
        "mode": "api" if fred.os.environ.get("FRED_API_KEY") else "fredgraph.csv",
    }

    frames, missing = [], []
    ciks = edgar.ticker_to_cik()
    for _, row in universe.companies().iterrows():
        for cik in [ciks.get(row.ticker), *row.predecessor_ciks]:
            f = edgar.load_company_facts(row.ticker, cik=cik)
            if f is None or f.empty:
                missing.append(f"{row.ticker}:{cik}")
            else:
                frames.append(f)
            time.sleep(0.2)  # SEC fair-access: well under 10 req/s
    facts = pd.concat(frames, ignore_index=True).drop_duplicates()
    facts = facts[facts["filed"] >= "2014-01-01"]
    facts.to_csv(SNAPSHOT_DIR / "edgar_facts.csv.gz", index=False)
    status["edgar"] = {
        "ok": True,
        "tickers": sorted(facts["ticker"].unique()),
        "missing": missing,
        "rows": int(len(facts)),
    }

    ff = famafrench.load_factors(start=START)
    ff.to_csv(SNAPSHOT_DIR / "ff3_daily.csv.gz", index=False)
    status["famafrench"] = {"ok": True, "last": ff["date"].max()}

    status["eia"] = {
        "ok": eia_snapshot.meta() is not None,
        "reason": "refreshed separately by scripts/refresh_eia.py (data/snapshot/eia.*)",
    }
    rc = rigs.load_rig_count()
    if rc is not None:
        rc.to_csv(SNAPSHOT_DIR / "rig_count.csv.gz", index=False)
    status["rigcount"] = {
        "ok": rc is not None,
        "reason": None
        if rc is not None
        else "Baker Hughes site returns 403 to scripts; EIA mirror needs EIA_API_KEY",
    }

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "start": START,
        "sources": status,
    }
    (SNAPSHOT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({k: v.get("ok") for k, v in status.items()}))


if __name__ == "__main__":
    main()
