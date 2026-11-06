"""Closed-form checks for lag, expanding-window OLS, and out-of-sample R².

Pinned ``results/factor_model.json`` only catches a bug that disagrees with the
snapshot. These cases use a few hand-built rows, so a wrong shift, a window that
includes the test week, or a swapped R² denominator fails on its own.
"""

import numpy as np
import pandas as pd
import pytest

from src.analysis import factor_model as fm


def _fridays(n: int, start: str = "2020-01-03") -> pd.DatetimeIndex:
    return pd.date_range(start, periods=n, freq="W-FRI")


def test_lagged_shifts_week_t_values_onto_week_t_plus_1():
    idx = _fridays(4)
    panel = pd.DataFrame(
        {"oil": [10.0, 20.0, 30.0, 40.0], "gas": [1.0, 2.0, 3.0, 4.0]},
        index=idx,
    )
    out = fm.lagged(panel, ["oil", "gas"])
    assert list(out.columns) == ["oil", "gas"]
    assert out.index.equals(panel.index)
    assert out.iloc[0].isna().all()
    # value known at the start of week t+1 is week t's factor, not week t+1's
    np.testing.assert_array_equal(out.iloc[1:].to_numpy(), panel.iloc[:-1].to_numpy())
    assert out.loc[idx[1], "oil"] == 10.0
    assert out.loc[idx[2], "gas"] == 2.0

    lag2 = fm.lagged(panel, ["oil"], lag=2)
    assert lag2.iloc[:2, 0].isna().all()
    assert lag2.loc[idx[2], "oil"] == 10.0
    assert lag2.loc[idx[3], "oil"] == 20.0


def test_walk_forward_matches_hand_solved_ols_each_window():
    """One factor, three expanding windows. Slopes are the textbook formulas.

    Train x=[1,2,3], y=[1,2,4]:
      b = (sum xy - n xbar ybar) / (sum xx - n xbar^2) = 3/2, a = -2/3
      test x=4 → pred = 16/3, hist mean = 7/3
    Train x=[1,2,3,4], y=[1,2,4,3]:
      b = 4/5, a = 1/2; test x=5 → pred = 9/2, hist mean = 5/2
    Train x=[1,2,3,4,5], y=[1,2,4,3,6]:
      b = 11/10, a = -1/10; test x=6 → pred = 13/2, hist mean = 16/5
    The test row's own y is not in that window: the last target is 0, and
    including it would move the third slope off 11/10.
    """
    idx = _fridays(6)
    x = pd.DataFrame({"f": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}, index=idx)
    y = pd.Series([1.0, 2.0, 4.0, 3.0, 6.0, 0.0], index=idx)
    wf = fm.walk_forward(y, x, min_train=3)

    assert wf.index.equals(idx[3:])
    assert wf["y"].tolist() == [3.0, 6.0, 0.0]
    assert wf["pred"].tolist() == pytest.approx([16 / 3, 9 / 2, 13 / 2])
    assert wf["hist_mean"].tolist() == pytest.approx([7 / 3, 5 / 2, 16 / 5])
    # train_end is the last training Friday: idx[2], idx[3], idx[4] for the three tests
    pd.testing.assert_index_equal(pd.DatetimeIndex(wf["train_end"]), idx[2:5], check_names=False)
    assert (pd.DatetimeIndex(wf["train_end"]) < wf.index).all()


def test_walk_forward_two_factor_normal_equations():
    """Intercept plus two regressors. First window interpolates; second is least squares.

    Rows (x1, x2, y) = (1,0,1), (2,1,2), (3,0,2), (4,1,3) lie on
    y = 1/2 + 1/2 x1 + 1/2 x2, so the test point (5, 0) predicts 3.
    Adding (5, 0, 5) and solving XtX beta = Xty with
    XtX = [[5, 15, 2], [15, 55, 6], [2, 6, 2]] and Xty = [13, 48, 5]
    gives beta = [-1/30, 9/10, -1/6]. The next point (6, 1) predicts 26/5.
    """
    idx = _fridays(6)
    factors = pd.DataFrame(
        {"x1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], "x2": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]},
        index=idx,
    )
    y = pd.Series([1.0, 2.0, 2.0, 3.0, 5.0, 4.0], index=idx)
    wf = fm.walk_forward(y, factors, min_train=4)

    assert wf["pred"].tolist() == pytest.approx([3.0, 26 / 5])
    assert wf["hist_mean"].tolist() == pytest.approx([2.0, 13 / 5])
    assert wf["y"].tolist() == [5.0, 4.0]
    pd.testing.assert_index_equal(pd.DatetimeIndex(wf["train_end"]), idx[3:5], check_names=False)
    assert (pd.DatetimeIndex(wf["train_end"]) < wf.index).all()


def test_walk_forward_drops_incomplete_rows_before_the_window():
    # Same complete rows as the one-factor case, with a poisoned incomplete row in front.
    idx = _fridays(7)
    x = pd.DataFrame({"f": [np.nan, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}, index=idx)
    y = pd.Series([999.0, 1.0, 2.0, 4.0, 3.0, 6.0, 0.0], index=idx)
    wf = fm.walk_forward(y, x, min_train=3)

    assert wf.index.equals(idx[4:])
    assert wf["pred"].tolist() == pytest.approx([16 / 3, 9 / 2, 13 / 2])
    assert 999.0 not in set(wf["y"])
    pd.testing.assert_index_equal(pd.DatetimeIndex(wf["train_end"]), idx[3:6], check_names=False)


def test_scrambling_rows_after_cut_does_not_change_earlier_predictions():
    idx = _fridays(8)
    x = pd.DataFrame({"f": [1.0, 2.0, 3.0, 4.0, 0.0, 1.0, 5.0, 2.0]}, index=idx)
    y = pd.Series([1.0, 2.0, 4.0, 3.0, 6.0, 1.0, 7.0, 8.0], index=idx)
    base = fm.walk_forward(y, x, min_train=4)
    cut = idx[5]
    assert (pd.DatetimeIndex(base["train_end"]) < base.index).all()
    # every training date is the previous kept row, never the test week itself
    kept = pd.concat([y.rename("y"), x], axis=1).dropna()
    for ts in base.index:
        pos = kept.index.get_loc(ts)
        assert base.loc[ts, "train_end"] == kept.index[pos - 1]

    x2, y2 = x.copy(), y.copy()
    after = idx[idx > cut]
    x2.loc[after] = x.loc[after[::-1]].to_numpy()
    y2.loc[after] = y.loc[after[::-1]].to_numpy()
    scrambled = fm.walk_forward(y2, x2, min_train=4)

    at_or_before = base.index[base.index <= cut]
    pd.testing.assert_series_equal(
        base.loc[at_or_before, "pred"], scrambled.loc[at_or_before, "pred"]
    )
    pd.testing.assert_series_equal(
        base.loc[at_or_before, "hist_mean"], scrambled.loc[at_or_before, "hist_mean"]
    )
    # the following week reads the scrambled feature row, so this is not a no-op
    later = idx[6]
    assert base.loc[later, "pred"] != pytest.approx(scrambled.loc[later, "pred"])


def test_oos_r2_matches_one_minus_sse_over_sst():
    """Denominators are the documented sums, not an in-sample grand mean.

    y = [1, 2, 3], pred = [1, 1, 4], hist_mean = [0, 1, 2]
    SSE = 0 + 1 + 1 = 2
    SST vs hist mean = 1 + 1 + 1 = 3 → R² = 1/3
    SST vs zero = 1 + 4 + 9 = 14 → R² = 6/7
    SST vs the grand mean of y is 2, which would give R² = 0. That is not this formula.
    """
    idx = pd.to_datetime(["2021-01-08", "2021-01-15", "2021-01-22"])
    wf = pd.DataFrame(
        {"y": [1.0, 2.0, 3.0], "pred": [1.0, 1.0, 4.0], "hist_mean": [0.0, 1.0, 2.0]},
        index=idx,
    )
    out = fm.oos_r2(wf)
    assert out["vs_hist_mean"] == pytest.approx(1 / 3)
    assert out["vs_zero"] == pytest.approx(6 / 7)
    assert out["n_oos_weeks"] == 3
    assert out["first_oos_week"] == idx[0]
    assert out["last_oos_week"] == idx[-1]

    # a bad forecast is allowed to score below zero; the ratio is not clipped
    bad = wf.copy()
    bad["pred"] = [5.0, -1.0, 3.0]
    # SSE = 16 + 9 + 0 = 25; SST_hist = 1 + 1 + 1 = 3; SST_zero = 14
    scored = fm.oos_r2(bad)
    assert scored["vs_hist_mean"] == pytest.approx(1 - 25 / 3)
    assert scored["vs_zero"] == pytest.approx(1 - 25 / 14)


def test_oos_r2_perfect_forecast_and_benchmark_forecasts():
    idx = pd.to_datetime(["2021-01-08", "2021-01-15", "2021-01-22"])
    wf = pd.DataFrame(
        {"y": [1.0, 2.0, 3.0], "pred": [1.0, 2.0, 3.0], "hist_mean": [0.0, 1.0, 2.0]},
        index=idx,
    )
    perfect = fm.oos_r2(wf)
    assert perfect["vs_hist_mean"] == 1
    assert perfect["vs_zero"] == 1

    as_hist = wf.copy()
    as_hist["pred"] = as_hist["hist_mean"]
    assert fm.oos_r2(as_hist)["vs_hist_mean"] == 0

    as_zero = wf.copy()
    as_zero["pred"] = 0.0
    assert fm.oos_r2(as_zero)["vs_zero"] == 0
