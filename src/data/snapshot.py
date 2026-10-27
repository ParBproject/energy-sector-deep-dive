"""Committed snapshot of fetched data, so tests run offline.

Build with ``python -m scripts.build_snapshot``; read with the helpers below.
"""

from __future__ import annotations

import json

import pandas as pd

from src.data.cache import ROOT

SNAPSHOT_DIR = ROOT / "data" / "snapshot"


def manifest() -> dict:
    return json.loads((SNAPSHOT_DIR / "manifest.json").read_text())


def prices() -> pd.DataFrame:
    df = pd.read_csv(SNAPSHOT_DIR / "prices_daily.csv.gz", parse_dates=["date"])
    return df.set_index("date")


def fred() -> pd.DataFrame:
    return pd.read_csv(SNAPSHOT_DIR / "fred.csv.gz", parse_dates=["date"])


def edgar_facts() -> pd.DataFrame:
    return pd.read_csv(SNAPSHOT_DIR / "edgar_facts.csv.gz")


def factors() -> pd.DataFrame:
    return pd.read_csv(SNAPSHOT_DIR / "ff3_daily.csv.gz", parse_dates=["date"])
