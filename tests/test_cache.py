import json
from datetime import date

import pandas as pd

from src.data import cache


def test_write_uses_fetch_date_in_name_and_sidecar(isolated_raw_dir):
    df = pd.DataFrame({"a": [1, 2]})
    path = cache.write("src", "x=F", df, url="http://example")
    assert path.parent == isolated_raw_dir / "src"
    assert path.name.startswith("x_F__") and path.suffix == ".csv"
    date.fromisoformat(path.stem.rsplit("__", 1)[1])
    meta = json.loads(path.with_suffix(".meta.json").read_text())
    assert meta["rows"] == 2 and meta["url"] == "http://example" and "fetched_at" in meta


def test_cached_hits_cache_on_second_call():
    calls = []

    def fetch():
        calls.append(1)
        return pd.DataFrame({"v": [1]})

    cache.cached("s", "n", fetch)
    out = cache.cached("s", "n", fetch)
    assert len(calls) == 1 and out["v"].tolist() == [1]


def test_cached_refetches_when_stale_and_falls_back_on_failure(isolated_raw_dir):
    old = isolated_raw_dir / "s" / "n__2020-01-01.csv"
    old.parent.mkdir(parents=True)
    pd.DataFrame({"v": [9]}).to_csv(old, index=False)
    assert cache.cached("s", "n", lambda: None)["v"].tolist() == [9]  # stale copy beats nothing
    assert cache.cached("s", "n", lambda: pd.DataFrame({"v": [1]}))["v"].tolist() == [1]
    assert cache.latest("s", "n") != old


def test_cached_returns_none_when_nothing_available():
    assert cache.cached("s", "missing", lambda: None) is None
