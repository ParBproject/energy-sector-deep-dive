"""Read the vendored, dated copy of ParBproject/commodity-price-forecaster's WTI forecasts.

The forecaster publishes ``results/leaderboard.json`` containing rolling-origin, one-step-ahead
BACKTEST forecasts with their realized actuals. It does not publish a forward-looking forecast
past its snapshot date. So the "latest forecast" here is the final backtest step: the forecast
made at the second-to-last week for the last week, which has already been realized.
Callers must therefore treat it as a reference preset; the slider is the primary input.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.data.cache import ROOT

VENDOR = ROOT / "data" / "vendor" / "commodity_forecaster_CLF_2026-09-30.json"


def load(path: Path = VENDOR) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def latest_one_step(path: Path = VENDOR) -> dict | None:
    d = load(path)
    if d is None:
        return None
    p = d["CL=F"]
    model = d["commodity_winner"]
    origin_price, target_actual = p["actual"][-2], p["actual"][-1]
    fc = p["forecasts"][model][-1]
    return {
        "model": model,
        "origin_week": p["dates"][-2],
        "target_week": p["dates"][-1],
        "origin_price": origin_price,
        "forecast_price": fc,
        "implied_move_pct": (fc / origin_price - 1) * 100,
        "realized_price": target_actual,
        "realized_move_pct": (target_actual / origin_price - 1) * 100,
        "status": "backtest step, already realized; not a forward forecast",
        "source_commit": d["source_commit"],
        "vendored_on": d["vendored_on"],
    }
