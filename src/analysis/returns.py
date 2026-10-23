"""Oil beta (HAC), rolling correlations with WTI and the S&P 500, and shock drawdowns."""

from __future__ import annotations

import pandas as pd
import statsmodels.api as sm

from src.analysis.common import (
    MARKET,
    OIL,
    SECTOR,
    SEGMENT_ORDER,
    as_of_date,
    daily_returns,
    segment_map,
    segment_returns,
)

HAC_LAGS = 5  # one trading week of serial correlation
WINDOW = 60
SHOCKS = {
    "2015-16 oil bust": ("2015-01-02", "2016-12-30"),
    "2020 COVID crash": ("2020-01-02", "2020-12-31"),
    "2022 rate shock": ("2022-01-03", "2022-12-30"),
}


def oil_beta(y: pd.Series, x: pd.Series) -> dict:
    """OLS y = a + b*x on daily returns, Newey-West (HAC) standard errors."""
    df = pd.concat([y, x], axis=1, keys=["y", "x"]).dropna()
    fit = sm.OLS(df["y"], sm.add_constant(df["x"])).fit(
        cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS}
    )
    lo, hi = fit.conf_int().loc["x"]
    return {
        "beta": fit.params["x"],
        "se_hac": fit.bse["x"],
        "t_hac": fit.tvalues["x"],
        "ci95": [lo, hi],
        "r2": fit.rsquared,
        "n": int(fit.nobs),
    }


def betas() -> dict:
    r = daily_returns()
    seg = segment_returns(r)
    oil = r[OIL]
    companies = {t: {"segment": s, **oil_beta(r[t], oil)} for t, s in segment_map().items()}
    segments = {s: oil_beta(seg[s], oil) for s in SEGMENT_ORDER}
    bench = {b: oil_beta(r[b], oil) for b in (SECTOR, MARKET)}
    return {"companies": companies, "segments": segments, "benchmarks": bench}


def rolling_corr(window: int = WINDOW) -> dict[str, pd.DataFrame]:
    r = daily_returns()
    seg = segment_returns(r)
    seg[SECTOR] = r[SECTOR]
    return {
        "wti": seg.rolling(window, min_periods=window).corr(r[OIL]),
        "spx": seg.rolling(window, min_periods=window).corr(r[MARKET]),
    }


def max_drawdown(ret: pd.Series) -> dict:
    wealth = (1 + ret.fillna(0)).cumprod()
    dd = wealth / wealth.cummax() - 1
    trough = dd.idxmin()
    peak = wealth.loc[:trough].idxmax()
    return {"max_drawdown": dd.min(), "peak": peak, "trough": trough}


def drawdowns() -> dict:
    r = daily_returns()
    seg = segment_returns(r)
    series = {
        **{s: seg[s] for s in SEGMENT_ORDER},
        SECTOR: r[SECTOR],
        MARKET: r[MARKET],
        OIL: r[OIL],
    }
    return {
        shock: {k: max_drawdown(v.loc[a:b]) for k, v in series.items()}
        for shock, (a, b) in SHOCKS.items()
    }


def compute() -> dict:
    rc = rolling_corr()
    latest = {k: v.dropna().iloc[-1] for k, v in rc.items()}
    corr = {
        "window_days": WINDOW,
        "as_of": str(rc["wti"].dropna().index[-1].date()),
        "latest": {
            s: {"wti": latest["wti"][s], "spx": latest["spx"][s]} for s in [*SEGMENT_ORDER, SECTOR]
        },
        "mean_full_period": {
            s: {"wti": rc["wti"][s].mean(), "spx": rc["spx"][s].mean()}
            for s in [*SEGMENT_ORDER, SECTOR]
        },
    }
    b = betas()
    seg_beta = b["segments"]
    return {
        "as_of": as_of_date(),
        "method": (
            "Daily simple returns of adjusted closes, 2015-01-02 to as_of. Oil = CL=F front-month "
            f"WTI future (same series as commodity-price-forecaster). OLS with HAC (Newey-West, "
            f"{HAC_LAGS} lags) standard errors. Segments are equal-weighted. Returns touching the "
            "negative 2020-04-20 settlement are excluded."
        ),
        "betas": b,
        "highest_beta_segment": max(seg_beta, key=lambda s: seg_beta[s]["beta"]),
        "lowest_beta_segment": min(seg_beta, key=lambda s: seg_beta[s]["beta"]),
        "correlations": corr,
        "drawdowns": drawdowns(),
    }
