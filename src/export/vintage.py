"""Observation, publication and retrieval dates for each explorer export.

``observation_date`` is the latest period the dataset actually contains.
``published`` is a filing or publish date, and is omitted when the source does not record one.
``retrieved_at`` is the day the snapshot was pulled, which the UI shows after the other two.
"""

from __future__ import annotations

import pandas as pd

from src.analysis.common import as_of_date, read_json
from src.analysis.fundamentals import source_vintage
from src.analysis.sizing import revenue_source_vintage
from src.data import eia_snapshot, snapshot
from src.scenarios import forecaster


def pull_date() -> str:
    """Day the committed price/EDGAR/FRED/Fama-French snapshot was built."""
    return str(snapshot.manifest()["built_at"])[:10]


def price_vintage() -> dict:
    return {"observation_date": as_of_date(), "retrieved_at": pull_date()}


def fred_vintage() -> dict:
    """One observation date for the FRED extract, and one per series.

    FRED's fredgraph file does not include a release timestamp, so there is no publish date.
    """
    frame = snapshot.fred()
    series = {
        str(sid): {"observation_date": str(pd.to_datetime(g["date"]).max().date())}
        for sid, g in frame.groupby("series_id")
    }
    return {
        "observation_date": max(s["observation_date"] for s in series.values()),
        "retrieved_at": pull_date(),
        "series": series,
    }


def edgar_vintage() -> dict:
    """Latest period end and filing date in the committed EDGAR extract."""
    facts = snapshot.edgar_facts()
    end = pd.to_datetime(facts["end"], errors="coerce").max()
    filed = pd.to_datetime(facts["filed"], errors="coerce").max()
    return {
        "observation_date": str(end.date()),
        "published": str(filed.date()),
        "published_as": "filed",
        "retrieved_at": pull_date(),
    }


def famafrench_vintage() -> dict:
    """Ken French's file has no separate publication date; the last factor day is the vintage."""
    last = pd.to_datetime(snapshot.factors()["date"]).max()
    return {"observation_date": str(last.date()), "retrieved_at": pull_date()}


def eia_vintage() -> dict:
    """Per-series observation dates. No single date, because the series do not end together.

    ``retrieved_at`` is the pull date (``eia_meta.json`` ``as_of``). A publish date is included
    on a series only when the metadata recorded one.
    """
    meta = eia_snapshot.meta()
    series = {name: eia_snapshot.series_vintage(info) for name, info in meta["series"].items()}
    return {"retrieved_at": meta["as_of"], "series": series}


def forecaster_vintage() -> dict | None:
    """Vendored commodity-forecaster snapshot: last price day, commit date, vendor day."""
    raw = forecaster.load()
    if raw is None:
        return None
    published = str(raw.get("source_commit_date") or "")[:10]
    out = {
        "observation_date": raw["data"]["last_daily_date"],
        "retrieved_at": raw["vendored_on"],
    }
    if published:
        out["published"] = published
        out["published_as"] = "published"
    return out


def _with_pull(bounds: dict) -> dict:
    return {**bounds, "retrieved_at": pull_date()}


def for_export(name: str, payload: dict | None = None) -> dict:
    """Vintage block stored on one ``web/public/data`` file."""
    payload = payload or {}
    if name == "returns.json":
        obs = payload.get("as_of") or as_of_date()
        return {"observation_date": obs, "retrieved_at": pull_date()}
    if name == "timeseries.json":
        # Weekly points are labeled by Friday, which can sit after the last print in that week.
        # The observation is the last close those points are built from.
        return price_vintage()
    if name == "fundamentals.json":
        return _with_pull(source_vintage(payload.get("as_of")))
    if name == "market_sizing.json":
        return _with_pull(revenue_source_vintage(payload.get("as_of")))
    if name == "clustering.json":
        # Same fundamental features as the heatmap, including the later share-count filing.
        return _with_pull(source_vintage())
    if name == "factor_model.json":
        return {"observation_date": payload["sample"]["last_week"], "retrieved_at": pull_date()}
    if name == "scenarios.json":
        last = payload.get("sample", {}).get("last_week")
        if not last:
            last = read_json("factor_model.json")["sample"]["last_week"]
        out = {"observation_date": last, "retrieved_at": pull_date()}
        fc = forecaster_vintage()
        if fc:
            out["forecaster"] = fc
        return out
    if name == "eia.json":
        return eia_vintage()
    raise KeyError(name)


def catalog() -> dict:
    """Every source dataset, for ``index.json``."""
    out = {
        "yfinance": price_vintage(),
        "fred": fred_vintage(),
        "edgar": edgar_vintage(),
        "famafrench": famafrench_vintage(),
        "eia": eia_vintage(),
    }
    fc = forecaster_vintage()
    if fc:
        out["forecaster"] = fc
    return out
