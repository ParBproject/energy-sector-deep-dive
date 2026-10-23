"""Committed EIA snapshot: ``data/snapshot/eia.csv.gz`` + ``data/snapshot/eia_meta.json``.

Written only by ``scripts/refresh_eia.py``, and only after every series has been fetched and
validated. Both files are staged as temp files and swapped in with ``os.replace`` so a failed
or partial pull never touches the last good snapshot.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.data.eia import DEFAULT_SERIES
from src.data.snapshot import SNAPSHOT_DIR

DATA_FILE = "eia.csv.gz"
META_FILE = "eia_meta.json"
SOURCE_LABEL = "U.S. EIA"
START = "2015-01"


@dataclass(frozen=True)
class Spec:
    frequency: str  # "monthly" | "weekly"
    units: str
    lo: float  # sanity range for every observation
    hi: float
    max_stale_days: int  # latest observation must be newer than this vs. retrieval date


# Ranges are deliberately wide (physical plausibility, not forecasts):
# US crude output has been ~9-14 mb/d since 2015; commercial stocks ~300-540 mb; rigs ~240-1,900.
SPECS = {
    "crude_production_us": Spec("monthly", "kb/d", 3_000, 25_000, 200),
    "crude_stocks_us": Spec("weekly", "kbbl", 150_000, 800_000, 30),
    "rotary_rigs_us": Spec("monthly", "rigs", 50, 5_000, 200),
}
COLUMNS = ["name", "series", "period", "date", "value", "units"]


class ValidationError(ValueError):
    pass


def to_date(period: pd.Series) -> pd.Series:
    """EIA periods are 'YYYY-MM' (monthly) or 'YYYY-MM-DD' (weekly)."""
    s = period.astype(str)
    s = s.where(s.str.len() > 7, s + "-01")
    return pd.to_datetime(s, format="%Y-%m-%d", errors="raise")


def tidy(name: str, raw: pd.DataFrame) -> pd.DataFrame:
    _, series_id, _ = DEFAULT_SERIES[name]
    df = raw.copy()
    df.insert(0, "name", name)
    df["date"] = to_date(df["period"]).dt.strftime("%Y-%m-%d")
    return df[COLUMNS]


def validate(name: str, df: pd.DataFrame, prev: pd.DataFrame | None, today: pd.Timestamp) -> None:
    """Raise ValidationError unless ``df`` is a sane, complete, forward-moving series."""
    spec, (_, series_id, _) = SPECS[name], DEFAULT_SERIES[name]
    if df is None or df.empty:
        raise ValidationError(f"{name}: no rows")
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValidationError(f"{name}: missing columns {sorted(missing)}")
    if set(df["series"]) != {series_id}:
        raise ValidationError(f"{name}: unexpected series ids {sorted(set(df['series']))}")
    if df["value"].isna().any():
        raise ValidationError(f"{name}: {int(df['value'].isna().sum())} non-numeric values")
    bad = df[(df["value"] < spec.lo) | (df["value"] > spec.hi)]
    if not bad.empty:
        r = bad.iloc[0]
        raise ValidationError(
            f"{name}: value {r['value']} at {r['period']} outside [{spec.lo}, {spec.hi}]"
        )
    dates = pd.to_datetime(df["date"])
    if dates.duplicated().any():
        raise ValidationError(f"{name}: duplicate periods")
    if not dates.is_monotonic_increasing:
        raise ValidationError(f"{name}: periods not sorted ascending")
    if dates.min() > pd.Timestamp(START + "-01") + pd.Timedelta(days=40):
        raise ValidationError(f"{name}: history starts {dates.min().date()}, expected {START}")
    latest = dates.max()
    if latest > today + pd.Timedelta(days=1):
        raise ValidationError(f"{name}: latest period {latest.date()} is in the future")
    if (today - latest).days > spec.max_stale_days:
        raise ValidationError(
            f"{name}: latest period {latest.date()} is older than {spec.max_stale_days} days"
        )
    if prev is not None and not prev.empty:
        prev_latest = pd.to_datetime(prev["date"]).max()
        if latest < prev_latest:
            raise ValidationError(
                f"{name}: latest period {latest.date()} moved backwards from {prev_latest.date()}"
            )
        if len(df) < len(prev):
            raise ValidationError(f"{name}: history shrank from {len(prev)} to {len(df)} rows")


def load(directory: Path = SNAPSHOT_DIR) -> pd.DataFrame | None:
    path = directory / DATA_FILE
    return pd.read_csv(path, dtype={"period": str}) if path.exists() else None


def meta(directory: Path = SNAPSHOT_DIR) -> dict | None:
    path = directory / META_FILE
    return json.loads(path.read_text()) if path.exists() else None


def series(name: str, directory: Path = SNAPSHOT_DIR) -> pd.Series:
    """One committed EIA series as a float Series indexed by period start date."""
    df = load(directory)
    if df is None:
        raise FileNotFoundError(f"{directory / DATA_FILE} not committed")
    g = df[df["name"] == name]
    return pd.Series(g["value"].to_numpy(float), index=pd.to_datetime(g["date"]), name=name)


def build_meta(frames: dict[str, pd.DataFrame], retrieved_at: datetime) -> dict:
    out = {
        "source": SOURCE_LABEL,
        "api": "https://api.eia.gov/v2",
        "retrieved_at": retrieved_at.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "as_of": retrieved_at.astimezone(timezone.utc).date().isoformat(),
        "series": {},
    }
    for name, df in frames.items():
        route, series_id, desc = DEFAULT_SERIES[name]
        spec = SPECS[name]
        units = sorted({u for u in df["units"].dropna().astype(str)}) or [spec.units]
        out["series"][name] = {
            "series_id": series_id,
            "route": route,
            "description": desc,
            "frequency": spec.frequency,
            "units": units[0],
            "rows": int(len(df)),
            "first_period": str(df["period"].iloc[0]),
            "latest_period": str(df["period"].iloc[-1]),
            "latest_value": float(df["value"].iloc[-1]),
        }
    return out


def write_atomic(frames: dict[str, pd.DataFrame], meta_obj: dict, directory: Path) -> None:
    """Stage both files, then swap them in. Called only after every series validated."""
    directory.mkdir(parents=True, exist_ok=True)
    data = pd.concat([frames[n] for n in SPECS], ignore_index=True)[COLUMNS]
    tmp_data = directory / (DATA_FILE + ".tmp")
    tmp_meta = directory / (META_FILE + ".tmp")
    try:
        data.to_csv(tmp_data, index=False, compression={"method": "gzip", "mtime": 0})
        tmp_meta.write_text(json.dumps(meta_obj, indent=2) + "\n")
        os.replace(tmp_data, directory / DATA_FILE)
        os.replace(tmp_meta, directory / META_FILE)
    finally:
        for p in (tmp_data, tmp_meta):
            p.unlink(missing_ok=True)
