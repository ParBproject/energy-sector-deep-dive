"""Python charts and the web export share the single token source."""

import json

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
    assert set(index["sources"]) == set(web.FILES)
