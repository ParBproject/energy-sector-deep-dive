"""Market sizing from what the snapshot actually has.

The textbook top-down size (US crude output x WTI) needs a production volume series. EIA is
unavailable (no ``EIA_API_KEY``) and the FRED snapshot holds prices, rates and indices but no
production volumes, so this module does NOT fabricate one. Instead it reports a bottom-up
proxy: summed reported revenue by segment from point-in-time 10-K filings, and states the
gaps (double counting along the value chain, global not US-only revenue, missing tags).
"""

from __future__ import annotations

import pandas as pd

from src.analysis.common import SEGMENT_ORDER, as_of_date, segment_map
from src.analysis.fundamentals import METRIC_TAGS, annual_facts
from src.data import snapshot

TOPDOWN_REQUIRES = "US crude oil field production volume (EIA PET MCRFPUS2), not in snapshot"


def revenue_by_year(when: str | None = None) -> pd.DataFrame:
    """Fiscal-year revenue per company (ticker x calendar year of FY end), known by ``when``."""
    f = annual_facts(when or as_of_date())
    f = f[f["duration"].between(350, 380) & f["concept"].isin(METRIC_TAGS["revenue"])]
    rows = []
    for (ticker, end), g in f.groupby(["ticker", "end"]):
        for tag in METRIC_TAGS["revenue"]:  # same fallback order as fundamentals
            hit = g[g["concept"] == tag]
            if not hit.empty:
                rows.append(
                    {"ticker": ticker, "year": int(end[:4]), "revenue": hit["value"].iloc[-1]}
                )
                break
    df = pd.DataFrame(rows).pivot_table(index="year", columns="ticker", values="revenue")
    return df.sort_index()


def compute(when: str | None = None) -> dict:
    when = when or as_of_date()
    rev = revenue_by_year(when)
    seg = segment_map()
    latest_year = int(rev.index[rev.notna().sum(axis=1) >= len(seg) // 2].max())
    # keep years where at most one company lacks a standard revenue tag
    years = [y for y in rev.index if y <= latest_year and rev.loc[y].notna().sum() >= len(seg) - 1]
    by_seg = {
        s: {
            int(y): rev.loc[y, [t for t in seg if seg[t] == s and t in rev]].sum(min_count=1)
            for y in years
        }
        for s in SEGMENT_ORDER
    }
    reporting = {int(y): int(rev.loc[y].notna().sum()) for y in years}
    missing_latest = sorted(t for t in seg if t not in rev or pd.isna(rev.loc[latest_year, t]))
    total_latest = sum(by_seg[s][latest_year] for s in SEGMENT_ORDER)
    fred = snapshot.fred()
    wti = fred[fred["series_id"] == "DCOILWTICO"]
    wti_year = wti[wti["date"].dt.year == latest_year]["value"].mean()
    return {
        "as_of": when,
        "latest_fiscal_year": latest_year,
        "approach": "bottom-up: summed reported revenue by segment (10-K, point-in-time)",
        "topdown_status": {
            "available": False,
            "requires": TOPDOWN_REQUIRES,
            "reason": "EIA_API_KEY not set; FRED snapshot has no production volume series",
        },
        "segment_revenue_usd": by_seg,
        "total_revenue_latest_usd": total_latest,
        "segment_share_latest": {s: by_seg[s][latest_year] / total_latest for s in SEGMENT_ORDER},
        "companies_reporting_by_year": reporting,
        "missing_revenue_latest_year": missing_latest,
        "wti_avg_latest_year_usd_bbl": wti_year,
        "caveats": [
            "Revenue is global and consolidated, not US-only.",
            "Segments double count: refiners' revenue includes crude bought from producers.",
            "Majors' and refiners' revenue include pass-through product sales, so revenue "
            "overstates value added; it measures scale of flows, not market value.",
            "Survivor universe of 18 names: excludes private producers and "
            "acquired/bankrupt names.",
            "Companies without a standard us-gaap revenue tag are left out, not estimated.",
        ],
    }
