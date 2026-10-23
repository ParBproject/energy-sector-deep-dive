"""Weekly segment factor model: full-sample HAC fit plus expanding-window walk-forward OOS R².

Factors (weekly, Friday close to Friday close):
- ``oil``: CL=F return;  ``gas``: NG=F return
- ``brent_wti``: weekly change in the Brent-WTI futures spread as a share of WTI. This is the
  documented CRACK-SPREAD PROXY: RBOB/heating-oil futures are not in the snapshot, so a true
  3-2-1 crack cannot be built. US refiners buy WTI-linked crude and sell Brent-linked products,
  so a wider Brent-WTI spread historically widened their margin. It is a proxy, not a crack.
- ``d10y``: weekly change in the 10-year Treasury yield (FRED DGS10), in percentage points
- ``mkt_rf``, ``smb``, ``hml``: Fama-French 3 factors compounded to weekly
- dollar proxy: none in the snapshot (no DXY/DTWEXBGS series); omitted and reported.

Target: segment excess return = equal-weight segment return - weekly risk-free (FF ``rf``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.analysis.common import SEGMENT_ORDER, daily_returns, segment_returns
from src.data import snapshot

FACTORS = ["oil", "gas", "brent_wti", "d10y", "mkt_rf", "smb", "hml"]
HAC_LAGS = 4
MIN_TRAIN_WEEKS = 156  # three years before the first out-of-sample week
WEEK = "W-FRI"
DOLLAR_PROXY = None


def _weekly_compound(daily: pd.DataFrame) -> pd.DataFrame:
    return (1 + daily).resample(WEEK).prod(min_count=1) - 1


def weekly_panel() -> pd.DataFrame:
    """One row per week: segment excess returns and contemporaneous factors.

    Weeks after the last Fama-French date are dropped rather than filled.
    """
    r = daily_returns()
    seg = _weekly_compound(segment_returns(r))
    p = snapshot.prices()
    ff = snapshot.factors().set_index("date")
    ffw = _weekly_compound(ff[["mkt_rf", "smb", "hml", "rf"]])
    ffw = ffw.loc[: ff.index.max()]
    wk_px = p[["CL=F", "BZ=F"]].resample(WEEK).last()
    fred = snapshot.fred().pivot(index="date", columns="series_id", values="value")
    out = pd.DataFrame(index=seg.index)
    out["oil"] = _weekly_compound(r[["CL=F"]])["CL=F"]
    out["gas"] = _weekly_compound(r[["NG=F"]])["NG=F"]
    spread = (wk_px["BZ=F"] - wk_px["CL=F"]) / wk_px["CL=F"].where(wk_px["CL=F"] > 0)
    out["brent_wti"] = spread.diff()
    out["d10y"] = fred["DGS10"].resample(WEEK).last().diff()
    out = out.join(ffw)
    for s in SEGMENT_ORDER:
        out[f"y_{s}"] = seg[s] - out["rf"]
    return out.dropna()


def full_sample(panel: pd.DataFrame | None = None) -> dict:
    panel = weekly_panel() if panel is None else panel
    X = sm.add_constant(panel[FACTORS])
    res = {}
    for s in SEGMENT_ORDER:
        fit = sm.OLS(panel[f"y_{s}"], X).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
        res[s] = {
            "coef": fit.params.to_dict(),
            "t_hac": fit.tvalues.to_dict(),
            "r2": fit.rsquared,
            "n": int(fit.nobs),
        }
    return res


def lagged(panel: pd.DataFrame, cols: list[str], lag: int = 1) -> pd.DataFrame:
    """Features known at the START of week t: the values from week t-lag."""
    return panel[cols].shift(lag)


def walk_forward(y: pd.Series, X: pd.DataFrame, min_train: int = MIN_TRAIN_WEEKS):
    """Expanding-window one-step OOS predictions.

    For each test week t, OLS is fit on rows strictly before t, then applied to X at t.
    Returns predictions, historical-mean baseline, and the last training date used per t.
    """
    df = pd.concat([y.rename("y"), X], axis=1).dropna()
    yv, Xv = df["y"].to_numpy(), np.column_stack([np.ones(len(df)), df[X.columns].to_numpy()])
    preds, means, train_end = [], [], []
    for t in range(min_train, len(df)):
        beta, *_ = np.linalg.lstsq(Xv[:t], yv[:t], rcond=None)
        preds.append(Xv[t] @ beta)
        means.append(yv[:t].mean())
        train_end.append(df.index[t - 1])
    idx = df.index[min_train:]
    return pd.DataFrame(
        {"y": yv[min_train:], "pred": preds, "hist_mean": means, "train_end": train_end},
        index=idx,
    )


def oos_r2(wf: pd.DataFrame) -> dict:
    sse = ((wf["y"] - wf["pred"]) ** 2).sum()
    return {
        "vs_hist_mean": 1 - sse / ((wf["y"] - wf["hist_mean"]) ** 2).sum(),
        "vs_zero": 1 - sse / (wf["y"] ** 2).sum(),
        "n_oos_weeks": len(wf),
        "first_oos_week": wf.index[0],
        "last_oos_week": wf.index[-1],
    }


def compute() -> dict:
    panel = weekly_panel()
    explanatory, predictive = {}, {}
    for s in SEGMENT_ORDER:
        y = panel[f"y_{s}"]
        explanatory[s] = oos_r2(walk_forward(y, panel[FACTORS]))
        predictive[s] = oos_r2(walk_forward(y, lagged(panel, FACTORS)))
    return {
        "sample": {
            "first_week": panel.index[0],
            "last_week": panel.index[-1],
            "n_weeks": len(panel),
        },
        "factors": FACTORS,
        "crack_spread_proxy": "weekly change in (Brent - WTI) / WTI from BZ=F and CL=F futures; "
        "RBOB/heating-oil futures not in snapshot",
        "dollar_proxy": DOLLAR_PROXY or "unavailable: no dollar index series in snapshot",
        "hac_lags": HAC_LAGS,
        "min_train_weeks": MIN_TRAIN_WEEKS,
        "full_sample": full_sample(panel),
        "walk_forward_explanatory": explanatory,
        "walk_forward_predictive_lag1": predictive,
        "notes": {
            "explanatory": "coefficients fit on past weeks only, applied to the SAME week's "
            "realized factors: tests whether exposures are stable, not whether returns are "
            "forecastable",
            "predictive_lag1": "coefficients fit on past weeks, applied to LAST week's factors: "
            "a genuine one-week-ahead forecast",
        },
    }
