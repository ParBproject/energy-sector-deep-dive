"""Point-in-time fundamentals from EDGAR company facts (filing dates, never period ends)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.common import SEGMENT_ORDER, as_of_date, segment_map
from src.data import edgar, snapshot, universe

# Fallback order per line item: first tag a company reports wins.
METRIC_TAGS = {
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsToAcquireOilAndGasPropertyAndEquipment",
        "PaymentsToExploreAndDevelopOilAndGasProperties",
        "PaymentsToAcquireOilAndGasProperty",
    ],
    "dividends": [
        "PaymentsOfDividendsCommonStock",
        "PaymentsOfOrdinaryDividends",
        "PaymentsOfDividends",
        "DistributionMadeToLimitedPartnerCashDistributionsPaid",
    ],
    "buybacks": ["PaymentsForRepurchaseOfCommonStock", "PaymentsForRepurchaseOfEquity"],
    "equity": ["StockholdersEquity", "PartnersCapital"],
}
DEBT_TAGS = [
    ["LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities"],
    ["LongTermDebt"],
    ["LongTermDebtNoncurrent", "LongTermDebtCurrent"],
    ["LongTermDebtNoncurrent", "DebtCurrent"],
    ["LongTermDebtNoncurrent"],
    ["LongTermDebtAndCapitalLeaseObligations", "DebtCurrent"],
    ["LongTermDebtAndCapitalLeaseObligations"],
]
RATIOS = {
    "capex_intensity": "Capex / revenue",
    "reinvestment_rate": "Capex / operating cash flow",
    "fcf_yield": "(Operating cash flow - capex) / market cap",
    "debt_to_capital": "Total debt / (total debt + equity)",
    "payout_ratio": "(Dividends + buybacks) / operating cash flow",
}


def _facts_preferring_current_registrant() -> pd.DataFrame:
    """Drop predecessor-CIK rows for any period the current registrant also reports.

    Baker Hughes Holdings LLC (CIK 808362) still files alongside BKR, and XOM's new holding
    company re-reports comparatives, so we avoid mixing two filers for one period.
    """
    f = snapshot.edgar_facts()
    current = edgar.ticker_to_cik_offline(f)
    f = f.assign(
        is_current=[current.get(t) == c for t, c in zip(f["ticker"], f["cik"], strict=True)]
    )
    keys = ["ticker", "concept", "unit", "start", "end"]
    cur_keys = set(map(tuple, f.loc[f["is_current"], keys].astype(str).values))
    pred = f.loc[~f["is_current"], keys].astype(str).apply(tuple, axis=1)
    drop = pred[pred.isin(cur_keys)].index
    return f.drop(index=drop)


def annual_facts(when: str) -> pd.DataFrame:
    """Full-fiscal-year flows and year-end balances known (filed) on ``when``."""
    f = edgar.as_of(_facts_preferring_current_registrant(), when)
    f = f[f["unit"].isin(["USD", "shares"])]
    days = (pd.to_datetime(f["end"]) - pd.to_datetime(f["start"])).dt.days
    return f.assign(duration=days)


def _day(value) -> str | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value)[:10]
    return None if text in {"", "NaT", "None", "nan"} else text


def _latest_annual_flow(f: pd.DataFrame, ticker: str, tags: list[str], end: str | None = None):
    """First tag in ``tags`` reported for a full fiscal year (ending ``end`` if given).

    The fourth item is that fact's EDGAR ``filed`` date, when a row was selected.
    """
    sub = f[(f["ticker"] == ticker) & f["concept"].isin(tags) & f["duration"].between(350, 380)]
    if end is not None:
        sub = sub[sub["end"] == end]
    for tag in tags:
        s = sub[sub["concept"] == tag]
        if not s.empty:
            row = s.sort_values(["end", "filed"]).iloc[-1]
            return row["value"], row["end"], tag, _day(row["filed"])
    return np.nan, None, None, None


def _instant_row(f: pd.DataFrame, ticker: str, tag: str, end: str | None):
    s = f[(f["ticker"] == ticker) & (f["concept"] == tag) & f["start"].isna()]
    if end is not None:
        s = s[s["end"] == end]
    return None if s.empty else s.sort_values(["end", "filed"]).iloc[-1]


def _instant(f: pd.DataFrame, ticker: str, tag: str, end: str | None):
    row = _instant_row(f, ticker, tag, end)
    return np.nan if row is None else row["value"]


def company_metrics(when: str | None = None) -> pd.DataFrame:
    when = when or as_of_date()
    f = annual_facts(when)
    prices = snapshot.prices().loc[:when]
    rows = []
    for ticker, seg in segment_map().items():
        cfo, fy_end, _, cfo_filed = _latest_annual_flow(f, ticker, METRIC_TAGS["cfo"])
        row = {"ticker": ticker, "segment": seg, "fiscal_year_end": fy_end, "cfo": cfo}
        ends = [_day(fy_end)]
        filed = [cfo_filed]
        sources = {}
        for k in ("revenue", "capex", "dividends", "buybacks"):
            # only combine figures from the same fiscal year as operating cash flow
            val, _, tag, fact_filed = _latest_annual_flow(f, ticker, METRIC_TAGS[k], end=fy_end)
            row[k], sources[k] = val, tag
            filed.append(fact_filed)
        row["equity"] = np.nan
        for tag in METRIC_TAGS["equity"]:
            picked = _instant_row(f, ticker, tag, fy_end)
            value = np.nan if picked is None else picked["value"]
            if not np.isnan(value):
                row["equity"] = value
                sources["equity"] = tag
                break
        debt = np.nan
        for combo in DEBT_TAGS:
            picked = [_instant_row(f, ticker, t, fy_end) for t in combo]
            vals = [np.nan if r is None else r["value"] for r in picked]
            if not np.isnan(vals[0]):
                debt = float(np.nansum(vals))
                sources["debt"] = "+".join(combo)
                break
        row["debt"] = debt
        shares = f[(f["ticker"] == ticker) & (f["concept"] == "EntityCommonStockSharesOutstanding")]
        shares = shares.sort_values(["filed", "end"])
        if shares.empty:
            row["shares"] = np.nan
            row["shares_end"] = None
            row["shares_filed"] = None
        else:
            last = shares.iloc[-1]
            row["shares"] = last["value"]
            # Cover-page shares are often a later 10-Q. Keep them off the annual-flow vintage.
            row["shares_end"] = _day(last["end"])
            row["shares_filed"] = _day(last["filed"])
        row["price"] = prices[ticker].dropna().iloc[-1]
        row["market_cap"] = row["shares"] * row["price"]
        row["tag_sources"] = sources
        kept_ends = [d for d in ends if d]
        kept_filed = [d for d in filed if d]
        row["annual_end"] = max(kept_ends) if kept_ends else None
        row["annual_filed"] = max(kept_filed) if kept_filed else None
        rows.append(row)
    m = pd.DataFrame(rows).set_index("ticker")
    m["capex_intensity"] = m["capex"] / m["revenue"]
    m["reinvestment_rate"] = m["capex"] / m["cfo"]
    m["fcf"] = m["cfo"] - m["capex"]
    m["fcf_yield"] = m["fcf"] / m["market_cap"]
    m["debt_to_capital"] = m["debt"] / (m["debt"] + m["equity"])
    m["payout_ratio"] = (m["dividends"] + m["buybacks"]) / m["cfo"]
    return m


def source_vintage(when: str | None = None) -> dict:
    """Vintage of the annual 10-K flows, with a later share count kept secondary.

    ``observation_date`` / ``published`` are the latest fiscal period end and 10-K filing
    among the annual flow facts (revenue, cash flow, capex, dividends, buybacks). Year-end
    equity that a later 10-Q restates does not move those dates: the period is still the
    fiscal year. Cover-page share counts, often a later quarter, go on ``shares``.
    """
    m = company_metrics(when)
    ends = [d for d in m["annual_end"].tolist() if d]
    filed = [d for d in m["annual_filed"].tolist() if d]
    if not ends or not filed:
        return {}
    out = {
        "observation_date": max(ends),
        "published": max(filed),
        "published_as": "filed",
    }
    share_ends = [d for d in m["shares_end"].tolist() if d]
    share_filed = [d for d in m["shares_filed"].tolist() if d]
    if share_ends and share_filed:
        share_obs, share_pub = max(share_ends), max(share_filed)
        if share_obs > out["observation_date"] or share_pub > out["published"]:
            out["shares"] = {
                "observation_date": share_obs,
                "published": share_pub,
                "published_as": "filed",
            }
    return out


def percentile_ranks(m: pd.DataFrame) -> pd.DataFrame:
    """Percentile rank (0-1, higher = larger value) of each ratio within its segment."""
    return m.groupby("segment")[list(RATIOS)].rank(pct=True)


def compute(when: str | None = None) -> dict:
    when = when or as_of_date()
    m = company_metrics(when)
    ranks = percentile_ranks(m)
    seg_median = m.groupby("segment")[list(RATIOS)].median().reindex(SEGMENT_ORDER)
    cols = [
        "segment",
        "fiscal_year_end",
        "revenue",
        "cfo",
        "capex",
        "fcf",
        "dividends",
        "buybacks",
        "debt",
        "equity",
        "shares",
        "price",
        "market_cap",
        *RATIOS,
    ]
    companies = {
        t: {
            **m.loc[t, cols].to_dict(),
            "tag_sources": m.loc[t, "tag_sources"],
            "segment_percentile": ranks.loc[t].to_dict(),
        }
        for t in m.index
    }
    missing = {k: sorted(m.index[m[k].isna()]) for k in RATIOS}
    return {
        "as_of": when,
        "method": (
            "For each company, the latest full fiscal year whose 10-K was filed on or before as_of "
            "(EDGAR `filed` date). Market cap = latest cover-page shares outstanding filed by "
            "as_of x adjusted close on as_of. Percentiles rank within segment (3-5 names), "
            "higher = larger value."
        ),
        "definitions": RATIOS,
        "segment_median": seg_median.to_dict(orient="index"),
        "companies": companies,
        "missing": missing,
        "universe_size": len(universe.companies()),
    }
