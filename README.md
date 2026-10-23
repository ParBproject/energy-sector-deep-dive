# Energy Sector Deep Dive

How do the five segments of US oil & gas (integrated majors, producers, pipelines, refiners
and oilfield services) actually trade against oil, gas, XLE and the S&P 500, from the 2015–16
bust through 2020 and 2022 to today? This repo is a reproducible, point-in-time research
pipeline whose results are presented in an interactive explorer.

It is the companion to [commodity-price-forecaster](https://github.com/ParBproject/commodity-price-forecaster).
Both use the same WTI, Brent and Henry Hub series (Yahoo `CL=F`, `BZ=F`, `NG=F`).

> Status: **Milestone 1 (scope and data)**. No analysis results yet. Everything below the roadmap is plumbing.

## Scope
- **Period:** 2015-01-02 to present, daily prices; quarterly and annual fundamentals.
- **Universe** (fixed as of 2015, see [`config/universe.yaml`](config/universe.yaml)):

| Segment | Tickers |
|---|---|
| Integrated majors | XOM, CVX, COP |
| Exploration & production | EOG, DVN, FANG, OXY, APA |
| Midstream | KMI, WMB, OKE, ET |
| Refining | MPC, VLO, PSX |
| Oilfield services | SLB, HAL, BKR |
| Benchmarks | XLE, SPY / ^GSPC |

- **Survivorship bias, stated plainly:** these are the names that survived. Anadarko, Noble,
  Concho, Pioneer, Marathon Oil, Hess, Cimarex, Chesapeake (old equity), Whiting, Spectra,
  Tesoro/Andeavor, Cameron, FMC Technologies and Weatherford were in the 2015 opportunity set
  and are listed with their fate in the config. Segment returns will be read with that in mind.

## Data sources
| Source | What | Access |
|---|---|---|
| [yfinance](https://github.com/ranaroussi/yfinance) | Adjusted daily closes, benchmarks, front-month futures | keyless |
| [FRED](https://fred.stlouisfed.org/) | WTI/Brent/Henry Hub spot, 10y and 3m rates, CPI, industrial production | `FRED_API_KEY` optional; falls back to keyless `fredgraph.csv` |
| [SEC EDGAR XBRL](https://www.sec.gov/edgar/sec-api-documentation) | Company facts with **filing dates** for point-in-time fundamentals | keyless; descriptive `SEC_USER_AGENT` required |
| [EIA API v2](https://www.eia.gov/opendata/) | US crude production, stocks, rotary rigs | `EIA_API_KEY` required |
| [Baker Hughes rig count](https://rigcount.bakerhughes.com/) | Weekly North America rigs | manual file (site blocks scripts) or EIA mirror |
| [Fama-French](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) | Daily 3 factors | keyless |

Column-level detail: [`docs/data_dictionary.md`](docs/data_dictionary.md). Every pull is cached
to `data/raw/` with its fetch date; a small real snapshot (≈0.5 MB) is committed in
`data/snapshot/` so tests and later milestones run offline.

## Roadmap
1. **M1 – Scope and data** ✅ universe, cached loaders, point-in-time EDGAR, offline snapshot, CI workflow (staged).
2. **M2 – Core analysis:** segment and company returns, drawdowns, oil/gas betas (rolling), correlation regimes, market sizing.
3. **M3 – Fundamentals and models:** point-in-time fundamentals comparison, clustering, a regression validated on held-out later data.
4. **M4 – Design system and explorer scaffold:** React + TypeScript + Vite in `web/`, dark theme with emerald `#10B981`, reading precomputed JSON from `src/export/`.
5. **M5 – Interactive explorer:** linked filters, brush-to-zoom, synced hover, sector → segment → company drill-down, compare pins, oil-scenario slider fed by the commodity forecaster (a what-if tool, not a signal).
6. **M6 – Polish and launch:** mobile (390 px first), Lighthouse ≥ 90 mobile performance and accessibility, README visuals, GitHub Pages deploy, portfolio-site card.

## How to run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

pytest -q            # offline: uses data/snapshot/ and mocked HTTP
ruff check . && ruff format --check .

# optional keys
export FRED_API_KEY=...        # otherwise keyless fredgraph.csv
export EIA_API_KEY=...         # otherwise EIA and rig count are skipped
export SEC_USER_AGENT="Your Name you@example.org"

python -m scripts.build_snapshot   # refetch everything into data/raw/ and rebuild data/snapshot/
```

## Repo layout
```
config/universe.yaml   fixed 2015 universe, segments, M&A / bankruptcy notes
src/data/              cached loaders: prices, fred, edgar, eia, rigs, famafrench, snapshot
src/analysis/          (M2–M3) returns, betas, fundamentals, clustering, regression
src/scenarios/         (M5) oil-price what-if mapping
src/export/            (M4) JSON for the web app
scripts/               build_snapshot.py
data/snapshot/         committed real data + manifest.json
notebooks/ results/ docs/img/ web/
tests/                 loaders, cache, point-in-time filing dates, snapshot
```

## License
MIT

> CI: the workflow is staged at [`docs/ci.yml.proposed`](docs/ci.yml.proposed). Move it to
> `.github/workflows/ci.yml` (needs a token with `workflow` scope, or the GitHub web UI) to enable ruff + pytest on every PR.
