"""FRED series. Uses the API when ``FRED_API_KEY`` is set, else the keyless fredgraph.csv."""

from __future__ import annotations

import io
import logging
import os

import pandas as pd
import requests

from src.data import cache

log = logging.getLogger(__name__)
SOURCE = "fred"
API_URL = "https://api.stlouisfed.org/fred/series/observations"
CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# Spot benchmarks matching the forecaster's commodities, plus macro context.
DEFAULT_SERIES = {
    "DCOILWTICO": "WTI spot, Cushing ($/bbl)",
    "DCOILBRENTEU": "Brent spot, Europe ($/bbl)",
    "DHHNGSP": "Henry Hub natural gas spot ($/MMBtu)",
    "DGS10": "10-year Treasury yield (%)",
    "DTB3": "3-month T-bill rate (%)",
    "CPIAUCSL": "CPI, all urban consumers (index)",
    "INDPRO": "Industrial production index",
}


def _tidy(df: pd.DataFrame, series_id: str) -> pd.DataFrame:
    df = df.rename(columns={df.columns[0]: "date", df.columns[1]: "value"})[["date", "value"]]
    df["value"] = pd.to_numeric(df["value"].replace(".", None), errors="coerce")
    df.insert(1, "series_id", series_id)
    return df.dropna(subset=["value"]).reset_index(drop=True)


def _fetch(series_id: str, start: str, timeout: int = 30) -> pd.DataFrame | None:
    key = os.environ.get("FRED_API_KEY")
    try:
        if key:
            params = {
                "series_id": series_id,
                "api_key": key,
                "file_type": "json",
                "observation_start": start,
            }
            r = requests.get(API_URL, params=params, timeout=timeout)
            r.raise_for_status()
            obs = pd.DataFrame(r.json()["observations"])[["date", "value"]]
            return _tidy(obs, series_id)
        r = requests.get(CSV_URL, params={"id": series_id, "cosd": start}, timeout=timeout)
        r.raise_for_status()
        return _tidy(pd.read_csv(io.StringIO(r.text)), series_id)
    except Exception as exc:
        log.warning("FRED %s failed: %s", series_id, exc)
        return None


def load_series(series_id: str, start: str = "2015-01-01", refresh: bool = False):
    return cache.cached(
        SOURCE,
        series_id,
        lambda: _fetch(series_id, start),
        refresh=refresh,
        url=f"{CSV_URL}?id={series_id}",
    )


def load_many(ids=None, start: str = "2015-01-01", refresh: bool = False) -> pd.DataFrame:
    frames = [load_series(s, start, refresh) for s in (ids or DEFAULT_SERIES)]
    frames = [f for f in frames if f is not None]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
