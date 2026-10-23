import pandas as pd

from src.data import edgar, eia, famafrench, fred, prices, rigs, universe
from tests.conftest import FakeResponse


def test_universe_has_five_segments_and_fixed_tickers():
    df = universe.companies()
    assert set(df["segment"]) == {"majors", "upstream", "midstream", "refiners", "services"}
    assert len(df) == 18 and df["ticker"].is_unique
    cfg = universe.load_config()
    assert cfg["start_date"] == "2015-01-02"
    assert {"CL=F", "BZ=F", "NG=F"} <= set(universe.all_price_symbols())
    assert "PXD" in cfg["lost_to_ma_or_bankruptcy"]


def test_fred_keyless_uses_fredgraph_csv(monkeypatch):
    seen = {}

    def fake_get(url, params=None, timeout=None):
        seen["url"], seen["params"] = url, params
        return FakeResponse(text="observation_date,DCOILWTICO\n2015-01-02,52.72\n2015-01-05,.\n")

    monkeypatch.setattr(fred.requests, "get", fake_get)
    df = fred.load_series("DCOILWTICO")
    assert seen["url"] == fred.CSV_URL and "api_key" not in seen["params"]
    assert df.to_dict("records") == [
        {"date": "2015-01-02", "series_id": "DCOILWTICO", "value": 52.72}
    ]


def test_fred_uses_api_when_key_set(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "dummy")
    payload = {"observations": [{"date": "2015-01-02", "value": "3.0"}]}
    monkeypatch.setattr(
        fred.requests, "get", lambda url, params=None, timeout=None: FakeResponse(payload=payload)
    )
    assert fred.load_series("DGS10")["value"].tolist() == [3.0]


def test_fred_network_failure_returns_none(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("offline")

    monkeypatch.setattr(fred.requests, "get", boom)
    assert fred.load_series("DGS10") is None


def test_eia_and_rigs_skip_without_key():
    assert not eia.available()
    assert eia.load_series("crude_production_us") is None
    assert rigs.load_rig_count() is None


def test_rigs_reads_manual_file(tmp_path, monkeypatch):
    f = tmp_path / "rig_count.csv"
    f.write_text("date,us_total\n2015-01-02,1811\n")
    monkeypatch.setenv("RIG_COUNT_FILE", str(f))
    assert rigs.load_rig_count()["us_total"].tolist() == [1811]


def test_edgar_sends_user_agent(monkeypatch):
    seen = {}

    def fake_get(url, headers=None, timeout=None):
        seen.update(headers)
        return FakeResponse(payload={"cik": 1, "facts": {}})

    monkeypatch.setattr(edgar.requests, "get", fake_get)
    edgar._get("https://data.sec.gov/x")
    assert "@" in seen["User-Agent"] and len(seen["User-Agent"].split()) >= 2


def test_prices_download_shapes_long_frame(monkeypatch):
    idx = pd.to_datetime(["2015-01-02", "2015-01-05"])
    cols = pd.MultiIndex.from_product([["Close", "Open"], ["XOM", "CL=F"]])
    raw = pd.DataFrame([[90.0, 52.7, 0, 0], [88.0, None, 0, 0]], index=idx, columns=cols)
    import yfinance

    monkeypatch.setattr(yfinance, "download", lambda *a, **k: raw)
    long = prices.load_prices(["XOM", "CL=F"])
    assert list(long.columns) == ["date", "symbol", "adj_close"]
    assert len(long) == 3  # NaN dropped
    wide = prices.to_wide(long)
    assert wide.loc["2015-01-05", "CL=F"] == 52.7  # forward-filled like the forecaster


def test_famafrench_parse():
    text = (
        "header\n\n,Mkt-RF,SMB,HML,RF\n20150102,  -0.12,  -0.5, 0.1, 0.00\n"
        "20150105,-1.84,0.3,-0.6,0.00\n\nAnnual Factors\n"
    )
    df = famafrench.parse(text)
    assert df["date"].tolist() == ["2015-01-02", "2015-01-05"]
    assert abs(df["mkt_rf"].iloc[1] + 0.0184) < 1e-12
