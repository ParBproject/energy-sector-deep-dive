"""EIA API v2. Requires ``EIA_API_KEY``; without it every call skips and returns None.

``fetch_strict`` is used by the scheduled refresh (``scripts/refresh_eia.py``): it raises on
any HTTP/API/parse error instead of returning None, so a failed pull can never be mistaken
for an empty series.
"""

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


class EIAError(RuntimeError):
    """Any failure to obtain a well-formed series from the EIA API."""


def available() -> bool:
    return bool(os.environ.get("EIA_API_KEY"))


def _params(series: str, start: str, freq: str | None, key: str) -> dict:
    params = {
        "api_key": key,
        "data[0]": "value",
        "facets[series][]": series,
        "start": start,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 5000,
    }
    if freq:
        params["frequency"] = freq
    return params


def parse_response(payload: dict, series: str) -> pd.DataFrame:
    """EIA v2 JSON -> DataFrame[period, series, value, units]. Raises EIAError if malformed."""
    if not isinstance(payload, dict):
        raise EIAError(f"{series}: response is not a JSON object")
    if "error" in payload:
        raise EIAError(f"{series}: EIA error: {payload['error']}")
    try:
        data = payload["response"]["data"]
    except (KeyError, TypeError) as exc:
        raise EIAError(f"{series}: missing response.data") from exc
    if not data:
        raise EIAError(f"{series}: EIA returned 0 rows")
    df = pd.DataFrame(data)
    need = {"period", "series", "value"}
    if not need <= set(df.columns):
        raise EIAError(f"{series}: missing columns {sorted(need - set(df.columns))}")
    if "units" not in df:
        df["units"] = None
    df = df[["period", "series", "value", "units"]].copy()
    df["period"] = df["period"].astype(str)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    total = int(payload["response"].get("total", len(df)) or len(df))
    if total > len(df):
        raise EIAError(f"{series}: truncated response ({len(df)} of {total} rows)")
    return df


def fetch_strict(route: str, series: str, start: str, freq: str | None = None) -> pd.DataFrame:
    key = os.environ.get("EIA_API_KEY")
    if not key:
        raise EIAError("EIA_API_KEY not set")
    try:
        r = requests.get(f"{BASE}/{route}", params=_params(series, start, freq, key), timeout=60)
    except requests.RequestException as exc:  # never echo the URL: it carries the key
        raise EIAError(f"{series}: request failed: {type(exc).__name__}") from None
    if r.status_code != 200:
        body = r.text[:300].replace(key, "***")
        raise EIAError(f"{series}: HTTP {r.status_code}: {body}")
    try:
        payload = r.json()
    except ValueError:
        raise EIAError(f"{series}: response is not JSON") from None
    return parse_response(payload, series)


def _fetch(route: str, series: str, start: str, freq: str | None = None):
    try:
        return fetch_strict(route, series, start, freq)[["period", "series", "value"]]
    except EIAError as exc:
        log.warning("EIA %s failed: %s", series, exc)
        return None


def load_series(name: str, start: str = "2015-01", refresh: bool = False):
    if not available():
        log.info("EIA_API_KEY not set; skipping EIA series %s", name)
        return None
    route, series, _ = DEFAULT_SERIES[name]
    return cache.cached(SOURCE, name, lambda: _fetch(route, series, start), refresh=refresh)
