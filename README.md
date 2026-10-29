# Energy Sector Deep Dive

[![CI](https://github.com/ParBproject/energy-sector-deep-dive/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ParBproject/energy-sector-deep-dive/actions/workflows/ci.yml)

[![Energy Sector Explorer](docs/img/hero.png)](https://parbproject.github.io/energy-sector-deep-dive/)

**[Open the explorer](https://parbproject.github.io/energy-sector-deep-dive/)** · **[Notes on the results](docs/findings.md)**

How five groups of US oil and gas companies (integrated majors, producers, pipelines, refiners, and oilfield services) have moved with oil, gas, XLE, and the S&P 500 since 2015. The calculations are in `src/`. The same outputs feed the notebooks and the [explorer](https://parbproject.github.io/energy-sector-deep-dive/).

This sits next to [commodity-price-forecaster](https://github.com/ParBproject/commodity-price-forecaster). Both use Yahoo `CL=F`, `BZ=F`, and `NG=F` for WTI, Brent, and Henry Hub.

## Universe

Fixed as of 2015-01-02. Current tickers, and notes on renames and predecessors, are in [`config/universe.yaml`](config/universe.yaml).

| Segment | Tickers |
|---|---|
| Integrated majors | XOM, CVX, COP |
| Exploration & production | EOG, DVN, FANG, OXY, APA |
| Midstream | KMI, WMB, OKE, ET |
| Refining | MPC, VLO, PSX |
| Oilfield services | SLB, HAL, BKR |
| Benchmarks | XLE, SPY / ^GSPC |

These are names that still trade. Anadarko, Noble, Concho, Pioneer, Marathon Oil, Hess, Cimarex, Chesapeake (old equity), Whiting, Spectra, Tesoro/Andeavor, Cameron, FMC Technologies, and Weatherford were in the 2015 set. The config lists what happened to each. Segment returns do not include them.

## Data

| Source | What | Access |
|---|---|---|
| [yfinance](https://github.com/ranaroussi/yfinance) | Adjusted daily closes, benchmarks, front-month futures | no key |
| [FRED](https://fred.stlouisfed.org/) | WTI, Brent, and Henry Hub spot, 10y and 3m rates, CPI, industrial production | `FRED_API_KEY` optional; otherwise keyless `fredgraph.csv` |
| [SEC EDGAR XBRL](https://www.sec.gov/edgar/sec-api-documentation) | Company facts, with filing dates | no key; `SEC_USER_AGENT` required |
| [EIA API v2](https://www.eia.gov/opendata/) | US crude production, stocks, rotary rigs | `EIA_API_KEY` |
| [Baker Hughes rig count](https://rigcount.bakerhughes.com/) | Weekly North America rigs | manual file, or the EIA series above |
| [Fama-French](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) | Daily 3 factors | no key |

Columns are listed in [`docs/data_dictionary.md`](docs/data_dictionary.md). Raw pulls land in `data/raw/` (gitignored) with the fetch date. A small snapshot in `data/snapshot/` is committed so tests and the explorer data can be rebuilt offline.

## Explorer

![Explorer: segment filter, date range, company panel, and the oil scenario](docs/img/demo.gif)

Six views share one set of filters, stored in the URL: overview, returns, fundamentals, clusters, factor model, and oil scenario. There is a skip link, a visible focus ring, and a company picker. Escape closes the detail panel. Charts have an accessible name. Motion follows `prefers-reduced-motion`.

<!-- findings:start -->
## Returns, sizing and fundamentals

_From `results/*.json`, via `python -m scripts.run_m2`. Data as of 2026-10-22._

### Oil beta
![Oil beta](docs/img/oil_beta.png)

- **Exploration & production** is the most oil-sensitive segment: beta 0.55 per 1% WTI move (HAC t = 9.1). **Refining & marketing** is the least: 0.27. XLE: 0.35; S&P 500: 0.07.

| Segment | Oil beta | 95% CI | R² | 60d corr WTI (latest) | 60d corr S&P (latest) |
|---|---|---|---|---|---|
| Integrated majors | 0.35 | 0.28 to 0.43 | 0.31 | 0.64 | -0.43 |
| Exploration & production | 0.55 | 0.43 to 0.67 | 0.35 | 0.68 | -0.29 |
| Pipelines & midstream | 0.31 | 0.22 to 0.41 | 0.20 | 0.11 | -0.09 |
| Refining & marketing | 0.27 | 0.20 to 0.34 | 0.12 | 0.33 | -0.17 |
| Oilfield services | 0.40 | 0.31 to 0.50 | 0.25 | 0.11 | 0.15 |

![Rolling correlations](docs/img/rolling_corr.png)

### Drawdowns in the three shocks
![Drawdowns](docs/img/drawdowns.png)

| Shock | Integrated majors | Exploration & production | Pipelines & midstream | Refining & marketing | Oilfield services | XLE | S&P 500 | WTI |
|---|---|---|---|---|---|---|---|---|
| 2015-16 oil bust | -33.4% | -43.0% | -71.3% | -31.4% | -39.2% | -36.1% | -13.0% | -57.3% |
| 2020 COVID crash | -57.5% | -78.7% | -65.6% | -66.8% | -72.1% | -60.6% | -33.7% | -71.1% |
| 2022 rate shock | -26.1% | -31.6% | -20.9% | -29.3% | -40.7% | -26.0% | -24.5% | -42.6% |

### Market sizing (proxy)
![Segment revenue](docs/img/segment_revenue.png)

- Top-down: US field crude output in 2025 was 13,662 kb/d (4.99bn bbl), worth **$326bn** at monthly average WTI (EIA MCRFPUS2 x FRED DCOILWTICO; EIA data as of 2026-10-29). Wellhead value at WTI Cushing spot; realized prices differ by grade and basin. Crude only: excludes natural gas, NGLs and refined products. Production for recent months is EIA's estimate and is revised in later releases.
- Bottom-up proxy: the universe reported **$1,278bn** of FY2025 revenue (17 of 18 companies; missing: APA). Average WTI in 2025: $65.39/bbl.
- Shares of that revenue: Integrated majors 45.4%, Exploration & production 6.0%, Pipelines & midstream 11.6%, Refining & marketing 30.3%, Oilfield services 6.7%.
- Caveats: Revenue is global and consolidated, not US-only. Segments double count: refiners' revenue includes crude bought from producers. Majors' and refiners' revenue include pass-through product sales, so revenue overstates value added; it measures scale of flows, not market value. Survivor universe of 18 names: excludes private producers and acquired/bankrupt names. Companies without a standard us-gaap revenue tag are left out, not estimated.

### Fundamentals (point-in-time, filing dates)
![Fundamentals heatmap](docs/img/fundamentals_heatmap.png)

| Segment median | Capex / revenue | Capex / operating cash flow | (Operating cash flow - capex) / market cap | Total debt / (total debt + equity) | (Dividends + buybacks) / operating cash flow |
|---|---|---|---|---|---|
| Integrated majors | 8.9% | 52.8% | 3.5% | 17.6% | 72.2% |
| Exploration & production | 25.2% | 60.3% | 6.5% | 35.1% | 24.9% |
| Pipelines & midstream | 13.6% | 59.2% | 4.0% | 62.6% | 44.0% |
| Refining & marketing | 2.6% | 42.2% | 3.6% | 40.4% | 63.1% |
| Oilfield services | 4.7% | 33.4% | 5.9% | 27.2% | 54.2% |

Not computed where a company files the input under a non-standard tag (left blank rather than estimated): capex_intensity: APA, COP, PSX, VLO; reinvestment_rate: COP, PSX, VLO; fcf_yield: COP, PSX, VLO; payout_ratio: APA, ET, FANG.
<!-- findings:end -->

<!-- m3-findings:start -->
## Clustering, factors and scenarios

_From `results/*.json`, via `python -m scripts.run_m3`._

### Clustering vs the five segments
![Clusters](docs/img/clusters.png)

- k-means (k=5): silhouette 0.27, adjusted Rand vs the 5 segments **0.61**. Ward hierarchical: silhouette 0.27, ARI 0.61.
- The segments themselves score a silhouette of only 0.10 on these features. Best k by silhouette: 6 (k-means).
- 13 of 108 feature cells were imputed (universe median per feature, flagged; then z-scored). Complete-case check (12 companies, dropping APA, COP, ET, FANG, PSX, VLO): ARI 0.76.

### Factor model (weekly, HAC)
![Factor t-stats](docs/img/factor_tstats.png)

- Sample 2015-01-09 to 2026-08-28 (608 weeks). Crack-spread proxy: weekly change in (Brent - WTI) / WTI from BZ=F and CL=F futures; RBOB/heating-oil futures not in snapshot. No dollar-index series is in the snapshot.

| Segment | In-sample R² | OOS R², same-week factors | OOS R², last week's factors |
|---|---|---|---|
| Integrated majors | 0.69 | 67.6% | -6.0% |
| Exploration & production | 0.69 | 66.8% | -5.6% |
| Pipelines & midstream | 0.54 | 53.3% | -7.7% |
| Refining & marketing | 0.57 | 57.1% | -3.7% |
| Oilfield services | 0.65 | 64.2% | -5.8% |

Out-of-sample R² is versus an expanding historical mean, refit weekly after 156 training weeks. The same-week column uses that week's factors. The last column uses the previous week's factors.

![Walk-forward OOS R²](docs/img/oos_r2.png)

### Oil scenarios (sensitivity, not a signal)
![Scenario fan](docs/img/scenario_fan.png)

| Segment | Weekly oil beta | Expected move if WTI -10% | 95% band (beta SE) |
|---|---|---|---|
| Integrated majors | 0.34 | -3.4% | -5.0% to -1.7% |
| Exploration & production | 0.55 | -5.5% | -7.7% to -3.3% |
| Pipelines & midstream | 0.31 | -3.1% | -4.8% to -1.3% |
| Refining & marketing | 0.31 | -3.1% | -4.9% to -1.3% |
| Oilfield services | 0.41 | -4.1% | -6.0% to -2.2% |

Forecaster tie-in: the latest one-step WTI forecast published by [commodity-price-forecaster](https://github.com/ParBproject/commodity-price-forecaster) (ARIMA(1,1,1), week 2026-09-27, commit `78b63d2`) implied -0.07%; WTI actually moved -7.87%. That step is already realized, so the explorer defaults to a slider and offers the forecast only as a preset.
<!-- m3-findings:end -->

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

pytest -q
ruff check . && ruff format --check .

# optional keys
export FRED_API_KEY=...        # otherwise keyless fredgraph.csv
export EIA_API_KEY=...         # only to refresh data/snapshot/eia.*
export SEC_USER_AGENT="Your Name you@example.com"

python -m scripts.build_snapshot   # refetch into data/raw/ and rebuild data/snapshot/
python -m scripts.run_m2           # results for sizing, returns, fundamentals; README block; charts
python -m scripts.run_m3           # clustering, factor model, scenarios
python -m scripts.make_notebooks   # rebuild and execute notebooks/
```

SEC asks clients for a `Name email` User-Agent. The code reads `SEC_USER_AGENT`. If that is unset it uses `Par Bahrae githubproproject@proton.me`. In GitHub Actions the value comes from the `SEC_USER_AGENT` repository secret.

## Layout

```
config/universe.yaml   2015 universe, segments, and M&A / bankruptcy notes
src/data/              cached loaders: prices, fred, edgar, eia, rigs, famafrench, snapshot
src/analysis/          returns, fundamentals, clustering, factor model
src/scenarios/         oil-price what-if
src/export/            JSON for the explorer, and the README numbers
scripts/               build_snapshot.py, refresh_eia.py
data/snapshot/         committed data and manifest.json
notebooks/  results/  docs/img/  web/
tests/
```

## EIA refresh

[`.github/workflows/eia-refresh.yml`](.github/workflows/eia-refresh.yml) pulls three series, checks them, and only then replaces `data/snapshot/eia.csv.gz` and `eia_meta.json`.

| Series | EIA id | Frequency | Used for |
|---|---|---|---|
| US field crude production, kb/d | `MCRFPUS2` | monthly | top-down size (times FRED WTI), overview chart |
| US commercial crude stocks ex-SPR, kbbl | `WCESTUS1` | weekly | overview chart |
| US crude and gas rotary rigs | `E_ERTRRO_XR0_NUS_C` | monthly, published with a lag | overview chart |

The workflow runs Thursdays at 15:30 UTC, after EIA's Wednesday Weekly Petroleum Status Report, and on manual dispatch. It needs the `EIA_API_KEY` secret. A series that is empty, non-numeric, outside a wide physical range, duplicated, stale, or shorter than the snapshot already committed fails the run. Nothing is filled in or carried forward, and the previous files stay. On success it rebuilds `results/`, the number blocks in this file, and `web/public/data/`, runs the tests, commits the data to `main`, and pushes the explorer to `gh-pages`. EIA charts show the as-of date from `eia_meta.json`.

A pull request that touches the EIA code fetches into a scratch directory and uploads an `eia-preview` artifact. It does not commit. Locally: `EIA_API_KEY=... python -m scripts.refresh_eia` (`--check` validates without writing).

## Deploying the explorer

The EIA workflow rebuilds and deploys it. To deploy by hand: `cd web && npm run build` (the Vite `base` is `/energy-sector-deep-dive/`), then push `web/dist` plus `.nojekyll` to `gh-pages`.

## License

MIT

## Screenshots

![Overview](docs/img/ui_m6_desktop_overview.png)
![Returns with company panel](docs/img/ui_m6_desktop_returns_panel.png)
![Scenario](docs/img/ui_m6_desktop_scenario.png)
![Mobile overview](docs/img/ui_m6_mobile_overview.png)
