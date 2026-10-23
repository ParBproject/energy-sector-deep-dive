"""Fama-French 3 factors (daily) from Ken French's data library."""

from __future__ import annotations

import io
import logging
import zipfile

import pandas as pd
import requests

from src.data import cache

log = logging.getLogger(__name__)
SOURCE = "famafrench"
URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_daily_CSV.zip"
)


def parse(text: str) -> pd.DataFrame:
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip().startswith(",Mkt-RF"))
    rows = []
    for ln in lines[start + 1 :]:
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) < 5 or not parts[0].isdigit() or len(parts[0]) != 8:
            if rows:
                break
            continue
        rows.append(parts[:5])
    df = pd.DataFrame(rows, columns=["date", "mkt_rf", "smb", "hml", "rf"])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d").dt.strftime("%Y-%m-%d")
    for c in ["mkt_rf", "smb", "hml", "rf"]:
        df[c] = df[c].astype(float) / 100.0  # percent -> decimal
    return df


def _fetch():
    try:
        r = requests.get(URL, timeout=60)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            text = z.read(z.namelist()[0]).decode("latin-1")
        return parse(text)
    except Exception as exc:
        log.warning("Fama-French download failed: %s", exc)
        return None


def load_factors(start: str = "2015-01-01", refresh: bool = False):
    df = cache.cached(SOURCE, "ff3_daily", _fetch, max_age_days=30, refresh=refresh, url=URL)
    return None if df is None else df[df["date"] >= start].reset_index(drop=True)
