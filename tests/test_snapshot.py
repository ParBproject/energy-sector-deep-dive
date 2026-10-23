"""The committed snapshot must be real, recent enough, small, and readable offline."""

from src.data import snapshot, universe


def test_snapshot_size_under_limit():
    total = sum(p.stat().st_size for p in snapshot.SNAPSHOT_DIR.iterdir())
    assert total < 5_000_000


def test_snapshot_prices_cover_universe_from_2015():
    p = snapshot.prices()
    assert set(universe.all_price_symbols()) <= set(p.columns)
    assert str(p.index.min().date()) <= "2015-01-05"
    assert (p.loc["2015-01-02":"2015-01-09", ["XOM", "XLE", "CL=F"]].notna()).all().all()


def test_snapshot_fred_has_spot_benchmarks():
    ids = set(snapshot.fred()["series_id"])
    assert {"DCOILWTICO", "DCOILBRENTEU", "DHHNGSP"} <= ids


def test_snapshot_edgar_is_point_in_time_ready():
    f = snapshot.edgar_facts()
    assert set(universe.companies()["ticker"]) <= set(f["ticker"])
    assert (f["filed"] >= f["end"]).mean() > 0.99  # filings come after period end


def test_manifest_records_unavailable_sources():
    m = snapshot.manifest()["sources"]
    assert m["yfinance"]["ok"] and m["edgar"]["ok"]
    for k in ("eia", "rigcount"):
        assert m[k]["ok"] or m[k]["reason"]
