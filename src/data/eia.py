"""EIA API v2. Requires ``EIA_API_KEY``; without it every call skips and returns None."""

from __future__ import annotations

import logging
import os

import pandas as pd
import requests

from src.data import cache

log = logging.getLogger(__name__)
SOURCE = "eia"
BASE = "https://api.eia.gov/v2"

# route, series facet, description
DEFAULT_SERIES = {
    "crude_production_us": (
        "petroleum/crd/crpdn/data",
        "MCRFPUS2",
        "US field crude production (kb/d, monthly)",
    ),
    "crude_stocks_us": (
        "petroleum/stoc/wstk/data",
        "WCESTUS1",
        "US commercial crude stocks ex-SPR (kbbl, weekly)",
    ),
    "rotary_rigs_us": (
        "petroleum/crd/drill/data",
        "E_ERTRRO_XR0_NUS_C",
        "US crude+gas rotary rigs (monthly; Baker Hughes via EIA)",
    ),
}


def available() -> bool:
    return bool(os.environ.get("EIA_API_KEY"))


def _fetch(route: str, series: str, start: str, freq: str | None = None):
    key = os.environ.get("EIA_API_KEY")
    if not key:
        return None
    params = {
        "api_key": key,
        "data[0]": "value",
        "facets[series][]": series,
        "start": start[:7],
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 5000,
    }
    if freq:
        params["frequency"] = freq
    try:
        r = requests.get(f"{BASE}/{route}", params=params, timeout=30)
        r.raise_for_status()
        df = pd.DataFrame(r.json()["response"]["data"])
        return df[["period", "series", "value"]] if not df.empty else None
    except Exception as exc:
        log.warning("EIA %s failed: %s", series, exc)
        return None


def load_series(name: str, start: str = "2015-01", refresh: bool = False):
    if not available():
        log.info("EIA_API_KEY not set; skipping EIA series %s", name)
        return None
    route, series, _ = DEFAULT_SERIES[name]
    return cache.cached(SOURCE, name, lambda: _fetch(route, series, start), refresh=refresh)
