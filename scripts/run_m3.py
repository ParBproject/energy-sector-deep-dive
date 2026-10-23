"""Compute M3 results, pin them in results/*.json, export charts, refresh README findings."""

from __future__ import annotations

from src.analysis import charts, clustering, factor_model
from src.analysis.common import read_json, write_json
from src.export import readme
from src.scenarios import oil

OUTPUTS = {
    "clustering.json": clustering.compute,
    "factor_model.json": factor_model.compute,
    "scenarios.json": oil.compute,
}


def main() -> None:
    for name, fn in OUTPUTS.items():
        print("wrote", write_json(name, fn()))
    cl, fm, sc = (read_json(n) for n in OUTPUTS)
    for p in [
        charts.clusters(cl),
        charts.oos_r2(fm),
        charts.factor_tstats(fm),
        charts.scenario_fan(sc),
    ]:
        print("chart", p)
    readme.update_readme()
    print("README findings refreshed")


if __name__ == "__main__":
    main()
