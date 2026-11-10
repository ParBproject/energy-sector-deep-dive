"""Copy pinned results into web/public/data/ for the explorer (``make export``)."""

from __future__ import annotations

import json

from src.analysis.common import RESULTS, ROOT
from src.data import snapshot
from src.export import vintage

WEB_DATA = ROOT / "web" / "public" / "data"
FILES = [
    "market_sizing.json",
    "returns.json",
    "fundamentals.json",
    "clustering.json",
    "factor_model.json",
    "scenarios.json",
]


def timeseries() -> dict:
    """Weekly (Friday) total-return indices = 100 at the first week, for the hero chart."""
    import numpy as np

    from src.analysis.common import SEGMENT_ORDER, daily_returns, segment_returns

    r = daily_returns()
    weekly = (1 + r).resample("W-FRI").prod(min_count=1)
    seg = (1 + segment_returns(r)).resample("W-FRI").prod(min_count=1)
    idx = lambda w: (100 * w.fillna(1).cumprod()).round(2)  # noqa: E731
    out = {
        "dates": [d.strftime("%Y-%m-%d") for d in weekly.index],
        "base": 100,
        "frequency": "weekly, Friday close",
        "segments": {},
        "symbols": {},
    }
    for s in SEGMENT_ORDER:
        out["segments"][s] = idx(seg[s]).tolist()
    for c in weekly.columns:
        out["symbols"][c] = [None if np.isnan(v) else v for v in idx(weekly[c]).tolist()]
    return out


EIA_LABELS = {
    "crude_production_us": ("US crude oil field production", "kb/d"),
    "crude_stocks_us": ("US commercial crude stocks (ex-SPR)", "million bbl"),
    "rotary_rigs_us": ("US crude + gas rotary rigs", "rigs"),
}


def _with_vintage(name: str, payload: dict) -> dict:
    return {"vintage": vintage.for_export(name, payload), **payload}


def eia_payload() -> dict:
    """Committed EIA snapshot -> chart-ready JSON.

    ``as_of`` stays the retrieval date. Each series carries its own observation date, and a
    publish date when the metadata has one. The pull date is only ``retrieved_at`` / vintage.
    """
    from src.data import eia_snapshot

    m = eia_snapshot.meta()
    series = {}
    for name, info in m["series"].items():
        s = eia_snapshot.series(name)
        label, units = EIA_LABELS[name]
        scale = 1 / 1000 if units == "million bbl" else 1  # kbbl -> million bbl
        dated = eia_snapshot.series_vintage(info)
        series[name] = {
            "label": label,
            "units": units,
            "series_id": info["series_id"],
            "frequency": info["frequency"],
            "latest_period": dated["latest_period"],
            "observation_date": dated["observation_date"],
            **{k: dated[k] for k in ("published", "published_as") if k in dated},
            "dates": [d.strftime("%Y-%m-%d") for d in s.index],
            "values": [round(v * scale, 3) for v in s.tolist()],
        }
    return {
        "as_of": m["as_of"],
        "retrieved_at": m["retrieved_at"],
        "source": m["source"],
        "vintage": vintage.eia_vintage(),
        "series": series,
    }


def export() -> dict:
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        payload = _with_vintage(name, json.loads((RESULTS / name).read_text()))
        (WEB_DATA / name).write_text(json.dumps(payload, indent=2) + "\n")
    ts = _with_vintage("timeseries.json", timeseries())
    (WEB_DATA / "timeseries.json").write_text(json.dumps(ts, separators=(",", ":")))
    (WEB_DATA / "eia.json").write_text(json.dumps(eia_payload(), separators=(",", ":")))
    m = snapshot.manifest()
    returns = json.loads((RESULTS / "returns.json").read_text())
    index = {
        "as_of": returns["as_of"],
        "snapshot_built_at": m["built_at"],
        "vintage": vintage.for_export("returns.json", returns),
        "datasets": vintage.catalog(),
        "files": [*FILES, "timeseries.json", "eia.json"],
        "sources": {
            "market_sizing.json": (
                "SEC EDGAR 10-K XBRL (point-in-time); top-down: U.S. EIA x FRED WTI"
            ),
            "returns.json": "yfinance adjusted closes",
            "fundamentals.json": "SEC EDGAR 10-K XBRL + yfinance",
            "clustering.json": "derived: results/returns.json + fundamentals.json",
            "factor_model.json": "yfinance, FRED DGS10, Fama-French",
            "scenarios.json": "yfinance, Fama-French, commodity-price-forecaster (vendored)",
            "timeseries.json": "yfinance adjusted closes, weekly total-return index",
            "eia.json": "U.S. EIA API v2 (MCRFPUS2, WCESTUS1, E_ERTRRO_XR0_NUS_C)",
        },
    }
    (WEB_DATA / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    return index


if __name__ == "__main__":
    print(json.dumps(export(), indent=2))
