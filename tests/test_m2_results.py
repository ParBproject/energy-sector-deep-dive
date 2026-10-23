"""Pinned M2 headline numbers must reproduce exactly from the committed snapshot."""

import json

import numpy as np
import pandas as pd
import pytest

from src.analysis import fundamentals, returns, sizing
from src.analysis.common import RESULTS, clean
from src.export import readme

CASES = {
    "market_sizing.json": sizing.compute,
    "returns.json": returns.compute,
    "fundamentals.json": fundamentals.compute,
}


@pytest.fixture(scope="module", params=list(CASES))
def pinned_and_fresh(request):
    pinned = json.loads((RESULTS / request.param).read_text())
    fresh = json.loads(json.dumps(clean(CASES[request.param]())))
    return pinned, fresh


def test_pinned_results_reproduce(pinned_and_fresh):
    pinned, fresh = pinned_and_fresh
    assert fresh == pinned


def test_headline_numbers_pinned():
    rt = json.loads((RESULTS / "returns.json").read_text())
    seg = rt["betas"]["segments"]
    assert rt["highest_beta_segment"] == "upstream"
    assert seg["upstream"]["beta"] == pytest.approx(0.551, abs=5e-4)
    assert rt["betas"]["benchmarks"]["XLE"]["beta"] == pytest.approx(0.346, abs=5e-3)
    sz = json.loads((RESULTS / "market_sizing.json").read_text())
    assert sz["latest_fiscal_year"] == 2025
    assert sz["total_revenue_latest_usd"] / 1e9 == pytest.approx(1278.1, abs=0.1)
    assert sz["topdown_status"]["available"] is False


def test_beta_matches_textbook_ols_point_estimate():
    r = returns.daily_returns()
    df = pd.concat([r["XOM"], r["CL=F"]], axis=1).dropna()
    slope = np.polyfit(df["CL=F"], df["XOM"], 1)[0]
    assert returns.betas()["companies"]["XOM"]["beta"] == pytest.approx(slope, rel=1e-9)


def test_negative_oil_print_excluded():
    r = returns.daily_returns()
    assert pd.isna(r.loc["2020-04-20", "CL=F"]) and pd.isna(r.loc["2020-04-21", "CL=F"])


def test_drawdown_helper():
    dd = returns.max_drawdown(pd.Series([0.1, -0.5, 0.2], index=pd.date_range("2020", periods=3)))
    assert dd["max_drawdown"] == pytest.approx(-0.5)


def test_fundamentals_respect_filing_dates():
    # Before FY2025 10-Ks were filed (Feb 2026) only FY2024 data may be visible.
    early = fundamentals.company_metrics("2025-12-31")
    assert set(early["fiscal_year_end"]) == {"2024-12-31"}
    late = fundamentals.company_metrics("2026-10-22")
    assert set(late["fiscal_year_end"]) == {"2025-12-31"}


def test_percentiles_within_segment_bounded():
    m = fundamentals.company_metrics()
    ranks = fundamentals.percentile_ranks(m)
    assert ((ranks > 0) & (ranks <= 1) | ranks.isna()).all().all()


def test_readme_findings_rendered_from_results():
    text = (RESULTS.parent / "README.md").read_text()
    assert readme.render() in text
