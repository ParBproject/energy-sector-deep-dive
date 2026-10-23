"""Offline tests for the EIA refresh pipeline: parsing, validation, all-or-nothing writes."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone

import pandas as pd
import pytest

from scripts import refresh_eia
from src.data import eia, eia_snapshot
from src.data.snapshot import SNAPSHOT_DIR
from src.export import web

NOW = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
TODAY = pd.Timestamp("2026-10-23")


def _payload(series, periods, values, units="MBBL/D"):
    data = [
        {"period": p, "series": series, "value": str(v), "units": units}
        for p, v in zip(periods, values, strict=True)
    ]
    return {"response": {"total": len(data), "data": data}}


def _committed_frames() -> dict[str, pd.DataFrame]:
    df = eia_snapshot.load()
    return {n: g.reset_index(drop=True) for n, g in df.groupby("name")}


def _fetcher_from(frames, fail_on: str | None = None, mutate=None):
    """Replay the committed snapshot as if EIA returned it (optionally failing or mutated)."""
    by_id = {eia.DEFAULT_SERIES[n][1]: n for n in frames}

    def fetch(route, series_id, start):
        name = by_id[series_id]
        if name == fail_on:
            raise eia.EIAError(f"{series_id}: HTTP 503: Service Unavailable")
        f = frames[name][["period", "series", "value", "units"]].copy()
        return mutate(name, f) if mutate else f

    return fetch


@pytest.fixture
def snapdir(tmp_path):
    for f in (eia_snapshot.DATA_FILE, eia_snapshot.META_FILE):
        shutil.copy(SNAPSHOT_DIR / f, tmp_path / f)
    return tmp_path


def _bytes(d):
    return {f: (d / f).read_bytes() for f in (eia_snapshot.DATA_FILE, eia_snapshot.META_FILE)}


# --- parsing -----------------------------------------------------------------------------


def test_parse_response_ok():
    df = eia.parse_response(_payload("MCRFPUS2", ["2026-06", "2026-07"], [13900, 13948]), "X")
    assert df.columns.tolist() == ["period", "series", "value", "units"]
    assert df["value"].tolist() == [13900.0, 13948.0]


@pytest.mark.parametrize(
    "payload, msg",
    [
        ({"error": "API_KEY_INVALID"}, "EIA error"),
        ({"response": {"total": 0, "data": []}}, "0 rows"),
        ({"foo": 1}, "missing response.data"),
        ({"response": {"total": 1, "data": [{"period": "2026-01", "value": 1}]}}, "missing col"),
        (
            {"response": {"total": 9, "data": [{"period": "2026-01", "series": "S", "value": 1}]}},
            "truncated",
        ),
    ],
)
def test_parse_response_rejects_malformed(payload, msg):
    with pytest.raises(eia.EIAError, match=msg):
        eia.parse_response(payload, "X")


def test_fetch_strict_without_key_raises():
    with pytest.raises(eia.EIAError, match="not set"):
        eia.fetch_strict("r", "S", "2015-01")


# --- validation --------------------------------------------------------------------------


def test_committed_snapshot_is_valid():
    for name, df in _committed_frames().items():
        eia_snapshot.validate(name, df, df, pd.Timestamp(eia_snapshot.meta()["as_of"]))


@pytest.mark.parametrize(
    "name, mutate, msg",
    [
        ("crude_stocks_us", lambda d: d.iloc[0:0], "no rows"),
        ("crude_stocks_us", lambda d: d.assign(value=d["value"] * 100), "outside"),
        ("crude_production_us", lambda d: d.assign(value=float("nan")), "non-numeric"),
        ("crude_production_us", lambda d: d.iloc[::-1], "not sorted"),
        ("crude_production_us", lambda d: pd.concat([d, d.tail(1)]), "duplicate"),
        ("crude_production_us", lambda d: d.iloc[:-1], "moved backwards"),
        ("rotary_rigs_us", lambda d: d.assign(series="OTHER"), "unexpected series"),
    ],
)
def test_validate_rejects(name, mutate, msg):
    good = _committed_frames()[name]
    with pytest.raises(eia_snapshot.ValidationError, match=msg):
        eia_snapshot.validate(name, mutate(good.copy()), good, TODAY)


def test_validate_rejects_stale_and_future():
    good = _committed_frames()["crude_stocks_us"]
    with pytest.raises(eia_snapshot.ValidationError, match="older than"):
        eia_snapshot.validate("crude_stocks_us", good, None, TODAY + pd.Timedelta(days=120))
    with pytest.raises(eia_snapshot.ValidationError, match="future"):
        eia_snapshot.validate("crude_stocks_us", good, None, TODAY - pd.Timedelta(days=60))


# --- all-or-nothing refresh --------------------------------------------------------------


def test_api_failure_keeps_last_good_snapshot(snapdir, capsys, monkeypatch):
    before = _bytes(snapdir)
    fetch = _fetcher_from(_committed_frames(), fail_on="rotary_rigs_us")  # last series fails
    with pytest.raises(eia.EIAError, match="HTTP 503"):
        refresh_eia.refresh(snapdir, fetch=fetch, now=NOW)
    assert _bytes(snapdir) == before
    assert not list(snapdir.glob("*.tmp"))


def test_validation_failure_keeps_last_good_snapshot(snapdir):
    before = _bytes(snapdir)

    def bad(name, f):  # stocks come back with an impossible value
        if name == "crude_stocks_us":
            f.loc[f.index[-1], "value"] = -5
        return f

    with pytest.raises(eia_snapshot.ValidationError, match="outside"):
        refresh_eia.refresh(snapdir, fetch=_fetcher_from(_committed_frames(), mutate=bad), now=NOW)
    assert _bytes(snapdir) == before


def test_main_reports_failure_in_step_summary(snapdir, tmp_path, monkeypatch):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setattr(refresh_eia, "SNAPSHOT_DIR", snapdir)
    before = _bytes(snapdir)
    assert refresh_eia.main(["--out", str(snapdir)]) == 1  # no EIA_API_KEY in tests
    assert "EIA refresh failed" in summary.read_text()
    assert "EIA_API_KEY not set" in summary.read_text()
    assert _bytes(snapdir) == before


def test_successful_refresh_writes_both_files(snapdir):
    later = datetime(2026, 10, 30, 15, 30, tzinfo=timezone.utc)
    m = refresh_eia.refresh(snapdir, fetch=_fetcher_from(_committed_frames()), now=later)
    assert m["as_of"] == "2026-10-30"
    assert eia_snapshot.meta(snapdir) == m
    pd.testing.assert_frame_equal(eia_snapshot.load(snapdir), eia_snapshot.load())


# --- as-of stamp ---------------------------------------------------------------------------


def test_exported_as_of_matches_snapshot_metadata():
    meta = eia_snapshot.meta()
    exported = json.loads((web.WEB_DATA / "eia.json").read_text())
    assert exported == json.loads(json.dumps(web.eia_payload()))
    assert exported["as_of"] == meta["as_of"]
    for name, s in meta["series"].items():
        assert exported["series"][name]["latest_period"] == s["latest_period"]


def test_sizing_topdown_uses_committed_eia_as_of():
    sz = json.loads((web.WEB_DATA / "market_sizing.json").read_text())
    assert sz["topdown_status"]["eia_as_of"] == eia_snapshot.meta()["as_of"]
