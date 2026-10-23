"""SEC EDGAR XBRL company facts, kept point-in-time.

Each fact keeps both ``end`` (period end) and ``filed`` (date the filing hit EDGAR).
Any as-of lookup must use ``filed``: a FY2019 10-K with period end 2019-12-31 was not
public until it was filed (typically Feb 2020). Using ``end`` would leak future data.
"""

from __future__ import annotations

import logging
import os

import pandas as pd
import requests

from src.data import cache

log = logging.getLogger(__name__)
SOURCE = "edgar"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
# SEC asks for a descriptive User-Agent with contact info; override via SEC_USER_AGENT.
USER_AGENT = os.environ.get(
    "SEC_USER_AGENT",
    "ParBproject energy-sector-deep-dive githubproproject@proton.me",
)

# us-gaap tags. Companies tag the same line item differently, so each metric has a
# fallback list (see src/analysis/fundamentals.py::METRIC_TAGS).
CONCEPTS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "NetIncomeLoss",
    "Assets",
    "StockholdersEquity",
    "PartnersCapital",
    "LongTermDebt",
    "LongTermDebtNoncurrent",
    "LongTermDebtCurrent",
    "DebtCurrent",
    "LongTermDebtAndCapitalLeaseObligations",
    "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
    "NetCashProvidedByUsedInOperatingActivities",
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsToAcquireProductiveAssets",
    "PaymentsToAcquireOilAndGasPropertyAndEquipment",
    "PaymentsToAcquireOilAndGasProperty",
    "PaymentsToExploreAndDevelopOilAndGasProperties",
    "PaymentsOfDividends",
    "PaymentsOfDividendsCommonStock",
    "PaymentsOfOrdinaryDividends",
    "DistributionMadeToLimitedPartnerCashDistributionsPaid",
    "PaymentsForRepurchaseOfCommonStock",
    "PaymentsForRepurchaseOfEquity",
]
DEI_CONCEPTS = ["EntityCommonStockSharesOutstanding"]
FORMS = {"10-K", "10-Q", "10-K/A", "10-Q/A"}


def _get(url: str, timeout: int = 30) -> dict:
    r = requests.get(
        url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}, timeout=timeout
    )
    r.raise_for_status()
    return r.json()


def ticker_to_cik() -> dict[str, int]:
    df = cache.cached(
        SOURCE,
        "company_tickers",
        lambda: pd.DataFrame(_get(TICKERS_URL).values()),
        max_age_days=30,
        url=TICKERS_URL,
    )
    return {} if df is None else dict(zip(df["ticker"], df["cik_str"].astype(int), strict=True))


def flatten_facts(payload: dict, ticker: str, concepts=CONCEPTS) -> pd.DataFrame:
    rows = []
    all_facts = payload.get("facts", {})
    pairs = [("us-gaap", c) for c in concepts] + [("dei", c) for c in DEI_CONCEPTS]
    for taxonomy, concept in pairs:
        node = all_facts.get(taxonomy, {}).get(concept, {})
        for unit, facts in node.get("units", {}).items():
            for f in facts:
                if f.get("form") not in FORMS:
                    continue
                rows.append(
                    {
                        "ticker": ticker,
                        "cik": payload.get("cik"),
                        "concept": concept,
                        "unit": unit,
                        "value": f["val"],
                        "start": f.get("start"),
                        "end": f["end"],
                        "fy": f.get("fy"),
                        "fp": f.get("fp"),
                        "form": f["form"],
                        "filed": f["filed"],
                        "accn": f.get("accn"),
                    }
                )
    return pd.DataFrame(rows)


def load_company_facts(ticker: str, cik: int | None = None, refresh: bool = False):
    """Facts for one registrant. Pass ``cik`` to pull a predecessor registrant explicitly."""

    def fetch():
        c = cik or ticker_to_cik().get(ticker)
        if c is None:
            log.warning("No CIK for %s", ticker)
            return None
        try:
            return flatten_facts(_get(FACTS_URL.format(cik=c)), ticker)
        except Exception as exc:
            log.warning("EDGAR %s failed: %s", ticker, exc)
            return None

    return cache.cached(
        SOURCE, f"facts_{ticker}_{cik or 'current'}", fetch, max_age_days=7, refresh=refresh
    )


def as_of(facts: pd.DataFrame, when: str) -> pd.DataFrame:
    """Latest value per (ticker, concept, period) that was PUBLICLY FILED on or before ``when``.

    Restatements are handled naturally: a later filing for the same period only wins once
    its own ``filed`` date has passed.
    """
    f = facts[pd.to_datetime(facts["filed"]) <= pd.Timestamp(when)].copy()
    if f.empty:
        return f
    f = f.sort_values("filed")
    keys = ["ticker", "concept", "unit", "start", "end"]
    f = f.drop_duplicates(subset=keys, keep="last")
    return f.sort_values(["ticker", "concept", "end"]).reset_index(drop=True)


def ticker_to_cik_offline(facts: pd.DataFrame) -> dict[str, int]:
    """Current registrant per ticker from a facts frame: the CIK with the latest filing."""
    last = facts.sort_values("filed").groupby("ticker")["cik"].last()
    return {t: int(c) for t, c in last.items()}
