"""No look-ahead: walk-forward uses only past rows; lagged features are last week's values."""

import numpy as np
import pandas as pd
import pytest

from src.analysis import factor_model as fm


@pytest.fixture(scope="module")
def panel():
    return fm.weekly_panel()


def test_walk_forward_trains_strictly_before_each_test_week(panel):
    wf = fm.walk_forward(panel["y_upstream"], panel[fm.FACTORS], min_train=156)
    assert (pd.to_datetime(wf["train_end"]) < wf.index).all()
    # train_end is exactly the previous week: expanding window, nothing skipped or peeked
    pos = panel.index.get_indexer(wf.index)
    assert (panel.index[pos - 1] == pd.to_datetime(wf["train_end"])).all()


def test_walk_forward_prediction_unchanged_by_future_data(panel):
    y, X = panel["y_majors"], panel[fm.FACTORS]
    full = fm.walk_forward(y, X, min_train=156)
    cut = panel.index[300]
    truncated = fm.walk_forward(y.loc[:cut], X.loc[:cut], min_train=156)
    pd.testing.assert_series_equal(full.loc[:cut, "pred"], truncated["pred"])


def test_walk_forward_ignores_poisoned_future_targets(panel):
    y = panel["y_refiners"].copy()
    X = panel[fm.FACTORS]
    t = 200
    base = fm.walk_forward(y, X, min_train=156)
    y.iloc[t:] = 1e6  # poison everything from week t on
    poisoned = fm.walk_forward(y, X, min_train=156)
    # the prediction FOR week t only used weeks < t, so it must be identical
    assert poisoned["pred"].iloc[t - 156] == pytest.approx(base["pred"].iloc[t - 156])
    assert poisoned["hist_mean"].iloc[t - 156] == pytest.approx(base["hist_mean"].iloc[t - 156])


def test_lagged_features_are_previous_week(panel):
    lag = fm.lagged(panel, fm.FACTORS)
    assert lag.iloc[0].isna().all()
    np.testing.assert_array_equal(lag.iloc[1:].to_numpy(), panel[fm.FACTORS].iloc[:-1].to_numpy())
    assert (lag.index == panel.index).all()


def test_weekly_factors_built_from_data_within_the_week(panel):
    # d10y for week t = yield at end of week t minus end of week t-1 (no forward values)
    from src.data import snapshot

    f = snapshot.fred().pivot(index="date", columns="series_id", values="value")["DGS10"]
    wk = panel.index[100]
    expected = f.loc[:wk].iloc[-1] - f.loc[: wk - pd.Timedelta(days=7)].iloc[-1]
    assert panel.loc[wk, "d10y"] == pytest.approx(expected)


def test_panel_stops_at_last_fama_french_date(panel):
    from src.data import snapshot

    assert panel.index.max() <= snapshot.factors()["date"].max() + pd.Timedelta(days=6)
