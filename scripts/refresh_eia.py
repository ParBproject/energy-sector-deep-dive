"""Pull the EIA series the deep dive uses, validate them, and replace the committed snapshot.

    EIA_API_KEY=... python -m scripts.refresh_eia            # fetch + validate + write
    EIA_API_KEY=... python -m scripts.refresh_eia --check    # fetch + validate only

All-or-nothing: if any series fails to download or validate, nothing is written, the reason
goes to stderr and ``$GITHUB_STEP_SUMMARY``, and the exit code is 1. Values are never filled,
interpolated or carried forward.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.data import eia, eia_snapshot
from src.data.snapshot import SNAPSHOT_DIR

Fetcher = Callable[[str, str, str], pd.DataFrame]


def _summary(lines: list[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as fh:
            fh.write("\n".join(lines) + "\n")


def refresh(
    directory: Path = SNAPSHOT_DIR,
    fetch: Fetcher = eia.fetch_strict,
    now: datetime | None = None,
    write: bool = True,
) -> dict:
    """Return the new metadata. Raises (and writes nothing) on any fetch/validation failure."""
    now = now or datetime.now(timezone.utc)
    today = pd.Timestamp(now.date())
    prev = eia_snapshot.load(directory)
    frames: dict[str, pd.DataFrame] = {}
    for name, (route, series_id, _) in eia.DEFAULT_SERIES.items():
        spec = eia_snapshot.SPECS[name]
        start = eia_snapshot.START + ("-01" if spec.frequency == "weekly" else "")
        raw = fetch(route, series_id, start)
        df = eia_snapshot.tidy(name, raw)
        before = None if prev is None else prev[prev["name"] == name]
        eia_snapshot.validate(name, df, before, today)
        frames[name] = df
    m = eia_snapshot.build_meta(frames, now)
    if write:
        eia_snapshot.write_atomic(frames, m, directory)
    return m


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fetch and validate, write nothing")
    ap.add_argument("--out", type=Path, default=SNAPSHOT_DIR, help="snapshot directory")
    args = ap.parse_args(argv)
    try:
        m = refresh(directory=args.out, write=not args.check)
    except (eia.EIAError, eia_snapshot.ValidationError, ValueError) as exc:
        msg = f"{type(exc).__name__}: {exc}"
        print(f"EIA refresh FAILED, last good snapshot kept: {msg}", file=sys.stderr)
        _summary(
            [
                "## :x: EIA refresh failed",
                "",
                f"`{msg}`",
                "",
                "Nothing was written; the last good snapshot in `data/snapshot/` is unchanged.",
            ]
        )
        return 1
    rows = [
        f"| {n} | `{s['series_id']}` | {s['units']} | {s['rows']} | "
        f"{s['latest_period']} | {s['latest_value']:,.0f} |"
        for n, s in m["series"].items()
    ]
    lines = [
        f"## EIA refresh {'check ' if args.check else ''}OK · data as of {m['as_of']}",
        "",
        "| series | EIA id | units | rows | latest period | latest value |",
        "|---|---|---|---|---|---|",
        *rows,
    ]
    _summary(lines)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
