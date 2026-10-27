"""Pinned clustering, factor and scenario results reproduce from the snapshot."""

import json

import pytest

from src.analysis import clustering, factor_model
from src.analysis.common import RESULTS, clean
from src.export import readme
from src.scenarios import forecaster, oil

CASES = {
    "clustering.json": clustering.compute,
    "factor_model.json": factor_model.compute,
    "scenarios.json": oil.compute,
}


@pytest.mark.parametrize("name", list(CASES))
def test_pinned_results_reproduce(name):
    pinned = json.loads((RESULTS / name).read_text())
    assert json.loads(json.dumps(clean(CASES[name]()))) == pinned


def test_headlines():
    cl = json.loads((RESULTS / "clustering.json").read_text())
    assert cl["k5"]["kmeans"]["adjusted_rand_vs_segments"] == pytest.approx(0.612, abs=1e-3)
    fm = json.loads((RESULTS / "factor_model.json").read_text())
    for s, v in fm["walk_forward_predictive_lag1"].items():
        assert v["vs_hist_mean"] < 0, s  # no forecastability claimed
    for s, v in fm["walk_forward_explanatory"].items():
        assert v["vs_hist_mean"] > 0.4, s


def test_readme_m3_section_rendered_from_results():
    text = (RESULTS.parent / "README.md").read_text()
    assert readme.render_m3() in text


def test_scenario_is_linear_and_bands_contain_mid():
    b = oil.weekly_betas()
    up, down = oil.scenario(10, b), oil.scenario(-10, b)
    for s in b:
        assert up[s]["expected_pct"] == pytest.approx(-down[s]["expected_pct"])
        lo, hi = up[s]["param_band_pct"]
        plo, phi = up[s]["prediction_band_pct"]
        assert plo < lo < up[s]["expected_pct"] < hi < phi
    assert oil.scenario(0, b)["upstream"]["param_band_pct"] == [0.0, 0.0]


def test_forecaster_vendor_and_slider_fallback(tmp_path):
    fc = forecaster.latest_one_step()
    assert fc["target_week"] == "2026-09-27" and "already realized" in fc["status"]
    assert fc["source_commit"].startswith("78b63d2")
    assert forecaster.latest_one_step(tmp_path / "missing.json") is None
