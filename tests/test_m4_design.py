"""Python charts and the web export share the single token source."""

import json

import pytest

from src.analysis import charts
from src.analysis.common import RESULTS, ROOT
from src.export import web

TOKENS = ROOT / "web" / "src" / "design" / "tokens.json"


def test_charts_read_shared_tokens():
    t = json.loads(TOKENS.read_text())
    assert charts.EMERALD == t["color"]["accent"] == "#10B981"
    assert charts.BG == t["color"]["bg"]
    assert charts.SEG_COLORS == t["color"]["segment"]


def test_charts_module_has_no_hardcoded_hex_colours():
    import re

    src = (ROOT / "src" / "analysis" / "charts.py").read_text().split('"""', 2)[2]
    assert not re.findall(r"#[0-9A-Fa-f]{6}", src)


def test_web_export_copies_results_verbatim():
    web.export()
    for name in web.FILES:
        assert (web.WEB_DATA / name).read_bytes() == (RESULTS / name).read_bytes()
    index = json.loads((web.WEB_DATA / "index.json").read_text())
    assert set(index["sources"]) == {*web.FILES, "timeseries.json"}


def test_timeseries_export_shape_and_values():
    import numpy as np

    from src.analysis.common import daily_returns

    ts = web.timeseries()
    n = len(ts["dates"])
    assert all(len(v) == n for v in ts["segments"].values())
    assert all(len(v) == n for v in ts["symbols"].values())
    # XOM index over the full sample equals compounded daily returns
    r = daily_returns()["XOM"].fillna(0)
    assert ts["symbols"]["XOM"][-1] == pytest.approx(100 * np.prod(1 + r), abs=0.01)
