"""Sensitivity analysis: map a WTI % move to each segment's expected % move.

This is SENSITIVITY ANALYSIS from historical co-movement, not a trading signal or forecast.
It uses a univariate weekly oil beta (segment excess return on CL=F return, HAC errors), so
the expected move already folds in whatever usually moves with oil. Two bands are given:
- ``param``: 95% band from the beta's HAC standard error only;
- ``prediction``: adds the residual volatility, i.e. where a single week typically lands.
"""

from __future__ import annotations

import numpy as np
import statsmodels.api as sm

from src.analysis.common import SEGMENT_ORDER
from src.analysis.factor_model import HAC_LAGS, weekly_panel
from src.scenarios import forecaster

Z95 = 1.959964
GRID = list(range(-30, 31, 5))


def weekly_betas() -> dict:
    panel = weekly_panel()
    out = {}
    for s in SEGMENT_ORDER:
        fit = sm.OLS(panel[f"y_{s}"], sm.add_constant(panel["oil"])).fit(
            cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS}
        )
        out[s] = {
            "alpha": fit.params["const"],
            "beta": fit.params["oil"],
            "se_hac": fit.bse["oil"],
            "resid_sd": float(np.std(fit.resid, ddof=2)),
            "r2": fit.rsquared,
            "n_weeks": int(fit.nobs),
        }
    return out


def scenario(move_pct: float, betas: dict | None = None) -> dict:
    """Expected segment move (%) for a WTI move of ``move_pct`` percent over one week."""
    betas = betas or weekly_betas()
    m = move_pct / 100
    res = {}
    for s, b in betas.items():
        mid = b["beta"] * m
        p_half = Z95 * b["se_hac"] * abs(m)
        pred_half = Z95 * np.sqrt((b["se_hac"] * m) ** 2 + b["resid_sd"] ** 2)
        res[s] = {
            "expected_pct": mid * 100,
            "param_band_pct": [(mid - p_half) * 100, (mid + p_half) * 100],
            "prediction_band_pct": [(mid - pred_half) * 100, (mid + pred_half) * 100],
        }
    return res


def compute() -> dict:
    betas = weekly_betas()
    fc = forecaster.latest_one_step()
    return {
        "framing": "Sensitivity analysis from historical weekly co-movement, 2015 onward. "
        "Not a trading signal and not a return forecast.",
        "weekly_betas": betas,
        "grid": {str(g): scenario(g, betas) for g in GRID},
        "forecaster_input": fc
        or {"status": "unavailable: no vendored forecast; slider-only input"},
        "forecaster_scenario": scenario(fc["implied_move_pct"], betas) if fc else None,
        "default_input": "slider",
    }
