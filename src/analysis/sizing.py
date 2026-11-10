"""Market sizing from what the snapshot actually has.

Two views:

* Top-down: US field crude production (EIA ``MCRFPUS2``, from the committed EIA snapshot that
  ``scripts/refresh_eia.py`` refreshes weekly) x the monthly average WTI spot price (FRED
  ``DCOILWTICO``), summed over the calendar year. Computed only when all 12 months of
  production are in the snapshot; otherwise reported as unavailable, never estimated.
* Bottom-up proxy: summed reported revenue by segment from point-in-time 10-K filings, with the
  gaps stated (double counting along the value chain, global not US-only revenue, missing tags).
"""

from __future__ import annotations

import pandas as pd

from src.analysis.common import SEGMENT_ORDER, as_of_date, segment_map
from src.analysis.fundamentals import METRIC_TAGS, annual_facts
from src.data import eia_snapshot, snapshot

TOPDOWN_REQUIRES = "US crude oil field production volume (EIA PET MCRFPUS2), not in snapshot"


def _topdown_provenance(year: int, wti_daily: pd.Series) -> dict:
    """Observation dates of the inputs, with the EIA pull date kept separate.

    ``eia_as_of`` is the production series' latest observation, not the day it was downloaded.
    """
    out = {}
    m = eia_snapshot.meta()
    if m is not None and "crude_production_us" in m.get("series", {}):
        info = m["series"]["crude_production_us"]
        out["eia_as_of"] = eia_snapshot.observation_date(info["latest_period"])
        out["eia_retrieved_at"] = m["as_of"]
    year_obs = wti_daily[wti_daily.index.year == year].dropna()
    if not year_obs.empty:
        out["wti_observation_date"] = str(year_obs.index.max().date())
    return out


def chart_years(rev: pd.DataFrame) -> list[int]:
    """Years the revenue chart draws: up to the latest broadly reported year, and only years
    where at most one company is missing a revenue tag.
    """
    if rev.empty:
        return []
    n = len(segment_map())
    covered = rev.index[rev.notna().sum(axis=1) >= n // 2]
    if len(covered) == 0:
        return []
    latest = int(covered.max())
    return [
        int(y) for y in rev.index if int(y) <= latest and int(rev.loc[y].notna().sum()) >= n - 1
    ]


def vintage_for_revenue_rows(rows: list[dict], years: set[int]) -> dict:
    """Observation and filing dates for revenue rows whose year the chart keeps."""
    kept = [r for r in rows if r["year"] in years]
    if not kept:
        return {}
    return {
        "observation_date": max(r["end"] for r in kept),
        "published": max(r["filed"] for r in kept),
        "published_as": "filed",
    }


def _revenue_rows(when: str) -> list[dict]:
    f = annual_facts(when)
    f = f[f["duration"].between(350, 380) & f["concept"].isin(METRIC_TAGS["revenue"])]
    rows = []
    for (_, end), g in f.groupby(["ticker", "end"]):
        for tag in METRIC_TAGS["revenue"]:
            hit = g[g["concept"] == tag]
            if not hit.empty:
                end_s = str(end)[:10]
                rows.append(
                    {
                        "year": int(end_s[:4]),
                        "end": end_s,
                        "filed": str(hit.sort_values("filed")["filed"].iloc[-1])[:10],
                    }
                )
                break
    return rows


def revenue_source_vintage(when: str | None = None) -> dict:
    """Latest period end and filing date of the revenue facts the chart sums.

    Years the chart drops (a later fiscal year with too few companies reporting) do not
    move the stamp ahead of the bars.
    """
    when = when or as_of_date()
    years = set(chart_years(revenue_by_year(when)))
    return vintage_for_revenue_rows(_revenue_rows(when), years)


def topdown(year: int, wti: pd.DataFrame) -> dict:
    """US crude output value for ``year``: sum over months of kb/d x 1000 x days x avg WTI."""
    try:
        prod = eia_snapshot.series("crude_production_us")
    except FileNotFoundError:
        return {"available": False, "requires": TOPDOWN_REQUIRES, "reason": "no EIA snapshot"}
    prod = prod[prod.index.year == year]
    daily = wti.set_index("date")["value"]
    monthly = daily[daily.index.year == year].resample("MS").mean()
    provenance = _topdown_provenance(year, daily)
    if len(prod) < 12 or monthly.reindex(prod.index).isna().any():
        return {
            "available": False,
            "requires": TOPDOWN_REQUIRES,
            "reason": f"only {len(prod)} of 12 months of {year} production in the EIA snapshot",
            **provenance,
        }
    days = pd.Series(prod.index.days_in_month, index=prod.index)
    barrels = prod * 1000 * days
    value = (barrels * monthly.reindex(prod.index)).sum()
    return {
        "available": True,
        "year": year,
        "method": "sum over months of EIA MCRFPUS2 (kb/d) x 1000 x days x mean FRED DCOILWTICO",
        "us_crude_production_bbl": float(barrels.sum()),
        "us_crude_production_avg_kbd": float(barrels.sum() / days.sum() / 1000),
        "us_crude_value_usd": float(value),
        **provenance,
        "caveats": [
            "Wellhead value at WTI Cushing spot; realized prices differ by grade and basin.",
            "Crude only: excludes natural gas, NGLs and refined products.",
            "Production for recent months is EIA's estimate and is revised in later releases.",
        ],
    }


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
    years = chart_years(rev)
    latest_year = int(rev.index[rev.notna().sum(axis=1) >= len(seg) // 2].max())
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
    td = topdown(latest_year, wti)
    return {
        "as_of": when,
        "latest_fiscal_year": latest_year,
        "approach": "bottom-up: summed reported revenue by segment (10-K, point-in-time)",
        "topdown_status": td,
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
