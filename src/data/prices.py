"""Daily prices via yfinance.

Commodity futures use the same Yahoo symbols and settings as
ParBproject/commodity-price-forecaster (``src/data_loader.py``): ``CL=F`` (WTI),
``BZ=F`` (Brent), ``NG=F`` (Henry Hub), ``auto_adjust=True``, Close column, forward-filled.
"""

from __future__ import annotations

import logging

import pandas as pd

from src.data import cache

log = logging.getLogger(__name__)
SOURCE = "yfinance"


def _download(symbols: list[str], start: str, end: str | None) -> pd.DataFrame | None:
    try:
        import yfinance as yf

        data = yf.download(
            symbols, start=start, end=end, auto_adjust=True, progress=False, group_by="column"
        )
    except Exception as exc:  # network / Yahoo errors
        log.warning("yfinance download failed: %s", exc)
        return None
    if data is None or data.empty:
        return None
    close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data[["Close"]]
    if not isinstance(data.columns, pd.MultiIndex):
        close.columns = symbols[:1]
    long = (
        close.rename_axis("date")
        .reset_index()
        .melt(id_vars="date", var_name="symbol", value_name="adj_close")
        .dropna(subset=["adj_close"])
    )
    long["date"] = pd.to_datetime(long["date"]).dt.strftime("%Y-%m-%d")
    return long.sort_values(["symbol", "date"]).reset_index(drop=True)


def load_prices(
    symbols: list[str], start: str = "2015-01-01", end: str | None = None, refresh: bool = False
) -> pd.DataFrame | None:
    """Long frame: date, symbol, adj_close (split/dividend-adjusted close)."""
    name = f"prices_{start}_{end or 'latest'}"
    return cache.cached(SOURCE, name, lambda: _download(symbols, start, end), refresh=refresh)


def to_wide(long: pd.DataFrame) -> pd.DataFrame:
    """Pivot to date x symbol, forward-filling gaps (matches the forecaster's ffill)."""
    wide = long.pivot(index="date", columns="symbol", values="adj_close")
    wide.index = pd.to_datetime(wide.index)
    return wide.sort_index().ffill()
