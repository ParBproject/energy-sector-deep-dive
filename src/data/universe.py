"""Load the fixed 2015 company universe from config/universe.yaml."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from src.data.cache import ROOT

CONFIG = ROOT / "config" / "universe.yaml"


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(Path(path).read_text())


def companies(path: Path = CONFIG) -> pd.DataFrame:
    cfg = load_config(path)
    rows = []
    for seg, spec in cfg["segments"].items():
        for ticker, info in spec["members"].items():
            rows.append(
                {
                    "ticker": ticker,
                    "name": info["name"],
                    "segment": seg,
                    "segment_label": spec["label"],
                    "ticker_2015": info.get("ticker_2015", ticker),
                    "note": info.get("note", ""),
                    "predecessor_ciks": list(info.get("predecessor_ciks", [])),
                }
            )
    return pd.DataFrame(rows)


def all_price_symbols(path: Path = CONFIG) -> list[str]:
    cfg = load_config(path)
    return list(companies(path)["ticker"]) + list(cfg["benchmarks"]) + list(cfg["commodities"])
