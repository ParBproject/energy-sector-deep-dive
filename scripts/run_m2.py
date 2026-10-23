"""Compute M2 results, pin them in results/*.json, export charts, refresh README findings."""

from __future__ import annotations

from src.analysis import charts, fundamentals, returns, sizing
from src.analysis.common import write_json
from src.export import readme


def main() -> None:
    sz = sizing.compute()
    rt = returns.compute()
    fd = fundamentals.compute()
    for name, payload in [
        ("market_sizing.json", sz),
        ("returns.json", rt),
        ("fundamentals.json", fd),
    ]:
        print("wrote", write_json(name, payload))
    from src.analysis.common import read_json

    sz, rt, fd = (read_json(n) for n in ("market_sizing.json", "returns.json", "fundamentals.json"))
    for p in [
        charts.segment_revenue(sz),
        charts.oil_beta(rt),
        charts.rolling_corr(returns.rolling_corr()),
        charts.drawdowns(rt),
        charts.fundamentals_heatmap(fd),
    ]:
        print("chart", p)
    readme.update_readme()
    print("README findings refreshed")


if __name__ == "__main__":
    main()
