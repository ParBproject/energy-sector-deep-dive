"""Each explorer export records the observation date, and a filing or publish date when known."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from src.analysis import sizing
from src.analysis.common import as_of_date
from src.analysis.sizing import chart_years, vintage_for_revenue_rows
from src.data.snapshot import manifest
from src.export import vintage, web


def _load(name: str) -> dict:
    return json.loads((web.WEB_DATA / name).read_text())


def test_catalog_dates_are_not_the_pull():
    data = vintage.catalog()
    pull = manifest()["built_at"][:10]
    prices = data["yfinance"]
    assert prices["observation_date"] == as_of_date()
    assert prices["retrieved_at"] == pull
    assert prices["observation_date"] != pull
    assert "published" not in prices

    fred = data["fred"]
    assert fred["observation_date"] == max(s["observation_date"] for s in fred["series"].values())
    assert set(fred["series"]) >= {"DCOILWTICO", "CPIAUCSL", "DGS10"}
    assert "published" not in fred  # fredgraph has no release timestamp
    assert fred["series"]["CPIAUCSL"]["observation_date"] < fred["observation_date"]

    edgar = data["edgar"]
    assert edgar["published_as"] == "filed"
    assert edgar["observation_date"] < edgar["published"] < edgar["retrieved_at"] == pull

    ff = data["famafrench"]
    assert ff["observation_date"] < ff["retrieved_at"]
    assert "published" not in ff

    eia = data["eia"]
    assert "observation_date" not in eia
    assert eia["series"]["rotary_rigs_us"]["observation_date"] < eia["retrieved_at"]
    assert "published" not in eia["series"]["crude_stocks_us"]

    fc = data["forecaster"]
    assert fc["published_as"] == "published"
    assert fc["observation_date"] <= fc["published"] < fc["retrieved_at"]


def test_each_export_matches_the_vintage_helper():
    index = _load("index.json")
    assert index["vintage"] == vintage.for_export("returns.json", {"as_of": index["as_of"]})
    assert index["datasets"]["eia"]["series"]["crude_production_us"]["observation_date"]
    for name in index["files"]:
        doc = _load(name)
        raw = {k: v for k, v in doc.items() if k != "vintage"}
        assert doc["vintage"] == vintage.for_export(name, raw)
        if name == "eia.json":
            assert doc["vintage"]["retrieved_at"]
            continue
        v = doc["vintage"]
        assert v["observation_date"]
        assert v["retrieved_at"]


def test_filing_dates_are_on_edgar_exports_and_before_the_pull():
    sizing = _load("market_sizing.json")["vintage"]
    fundamentals = _load("fundamentals.json")["vintage"]
    clusters = _load("clustering.json")["vintage"]
    for v in (sizing, fundamentals, clusters):
        assert v["published_as"] == "filed"
        assert v["observation_date"] < v["published"] < v["retrieved_at"]
    # The heatmap's main numbers are the FY ratios, same period as the revenue chart.
    # A later cover-page share count is a secondary clause, not the "Data as of" date.
    assert fundamentals["observation_date"] == sizing["observation_date"]
    shares = fundamentals["shares"]
    assert shares["published_as"] == "filed"
    assert shares["observation_date"] > fundamentals["observation_date"]
    assert shares["published"] > fundamentals["published"]
    assert clusters == fundamentals


def test_revenue_stamp_ignores_a_year_the_chart_drops():
    # 10 of 18 names report a later June year-end: enough to be the "latest" year under the
    # broad-coverage rule, too few to be drawn. The stamp stays on the years the chart sums.
    rev = pd.DataFrame({f"T{i}": [1.0, 1.0] for i in range(18)}, index=[2025, 2026])
    rev.loc[2026, [f"T{i}" for i in range(8)]] = pd.NA
    assert int(rev.loc[2026].notna().sum()) == 10
    years = chart_years(rev)
    assert years == [2025]
    rows = [
        {"year": 2025, "end": "2025-12-31", "filed": "2026-02-26"},
        {"year": 2026, "end": "2026-06-30", "filed": "2026-08-15"},
    ]
    dated = vintage_for_revenue_rows(rows, set(years))
    assert dated == {
        "observation_date": "2025-12-31",
        "published": "2026-02-26",
        "published_as": "filed",
    }


def test_chart_years_cutoff_follows_the_frame_not_the_universe():
    # Four columns, not the 18-name universe. 2026 is reported by half the frame, so the old
    # half-coverage rule would call it latest, but it is missing more than one company.
    rev = pd.DataFrame({f"T{i}": [1.0, 1.0] for i in range(4)}, index=[2025, 2026])
    rev.loc[2026, ["T0", "T1"]] = pd.NA
    assert chart_years(rev) == [2025]


def _thin_later_year_frame() -> pd.DataFrame:
    rev = pd.DataFrame({f"T{i}": [1.0, 1.0] for i in range(18)}, index=[2025, 2026])
    rev.loc[2026, [f"T{i}" for i in range(8)]] = pd.NA
    return rev


def test_compute_latest_year_matches_the_stamp_when_a_later_year_is_thin(monkeypatch):
    rev = _thin_later_year_frame()
    rows = [
        {"year": 2025, "end": "2025-12-31", "filed": "2026-02-26"},
        {"year": 2026, "end": "2026-06-30", "filed": "2026-08-15"},
    ]
    stamp = vintage_for_revenue_rows(rows, set(chart_years(rev)))
    monkeypatch.setattr(sizing, "revenue_by_year", lambda when=None: rev)
    monkeypatch.setattr(
        sizing,
        "topdown",
        lambda year, wti: {"available": False, "requires": "test", "reason": "fixture"},
    )
    cols = list(rev.columns)
    segments = ["majors", "upstream", "midstream", "refiners", "services"]
    mapping = {c: segments[i % 5] for i, c in enumerate(cols)}
    monkeypatch.setattr(sizing, "segment_map", lambda: mapping)
    out = sizing.compute()
    assert out["latest_fiscal_year"] == int(stamp["observation_date"][:4]) == 2025
    for bars in out["segment_revenue_usd"].values():
        assert 2026 not in bars
        assert 2025 in bars


def test_compute_rejects_a_frame_with_no_chartable_year(monkeypatch):
    rev = pd.DataFrame({f"T{i}": [pd.NA] for i in range(4)}, index=[2026])
    rev.loc[2026, "T0"] = 1.0
    monkeypatch.setattr(sizing, "revenue_by_year", lambda when=None: rev)
    with pytest.raises(ValueError, match="enough companies"):
        sizing.compute()


def test_scenario_export_keeps_the_forecaster_publish_date():
    v = _load("scenarios.json")["vintage"]
    assert v["observation_date"] < v["retrieved_at"]
    assert "published" not in v
    fc = v["forecaster"]
    assert fc["published_as"] == "published"
    assert fc["observation_date"] <= fc["published"] < fc["retrieved_at"]
