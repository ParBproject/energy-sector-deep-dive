# Data dictionary

All raw pulls land in `data/raw/<source>/<name>__<YYYY-MM-DD>.csv` (fetch date, UTC) with a
`.meta.json` sidecar (`fetched_at`, `url`, `rows`). `data/raw/` is git-ignored. The committed,
offline snapshot lives in `data/snapshot/` (≈0.5 MB total) and is described by
`data/snapshot/manifest.json`, which records build time, coverage and any source that was unavailable.

## `data/snapshot/prices_daily.csv.gz` (yfinance)
| column | type | meaning |
|---|---|---|
| `date` | date | NYSE trading day, 2015-01-02 → snapshot build date |
| `<SYMBOL>` | float | split- and dividend-adjusted close (`auto_adjust=True`), forward-filled, 4 dp |

Symbols: the 18 companies in `config/universe.yaml`, benchmarks `XLE`, `SPY`, `^GSPC`, and the
front-month futures `CL=F` (WTI), `BZ=F` (Brent), `NG=F` (Henry Hub). The futures use exactly the
symbols and settings of `ParBproject/commodity-price-forecaster` (`src/data_loader.py`), so both
repos see the same oil and gas series. Front-month futures roll monthly; they are not a total-return series.

## `data/snapshot/fred.csv.gz` (FRED)
Long format: `date`, `series_id`, `value`. Pulled via the FRED API if `FRED_API_KEY` is set,
otherwise the keyless `fredgraph.csv` endpoint. Missing observations (`.`) are dropped.

| series_id | meaning | freq |
|---|---|---|
| DCOILWTICO | WTI spot, Cushing, $/bbl | daily |
| DCOILBRENTEU | Brent spot, Europe, $/bbl | daily |
| DHHNGSP | Henry Hub natural gas spot, $/MMBtu | daily |
| DGS10 | 10-year Treasury constant-maturity yield, % | daily |
| DTB3 | 3-month T-bill secondary market rate, % | daily |
| CPIAUCSL | CPI-U, SA, index | monthly |
| INDPRO | Industrial production index | monthly |

## `data/snapshot/edgar_facts.csv.gz` (SEC EDGAR XBRL company facts)
| column | meaning |
|---|---|
| `ticker` | universe ticker the fact is attributed to |
| `cik` | registrant CIK the fact came from (current or predecessor, see below) |
| `concept` | us-gaap tag (revenue, net income, assets, equity/partners' capital, debt, CFO, capex, dividends, buybacks; several alternative tags each, see `src/data/edgar.py::CONCEPTS`) or dei `EntityCommonStockSharesOutstanding` (cover-page share count) |
| `unit` | XBRL unit, usually `USD` |
| `value` | reported value |
| `start`, `end` | reporting period (`start` empty for instant facts like `Assets`) |
| `fy`, `fp` | fiscal year / period **of the filing** that reported the fact |
| `form` | 10-K, 10-Q or their amendments (8-Ks etc. are excluded) |
| `filed` | **date the filing became public on EDGAR. Use this for any as-of logic.** |
| `accn` | accession number of the filing |

Point-in-time rule: `src.data.edgar.as_of(facts, date)` keeps only facts with `filed <= date` and, per
period, the latest such filing, so restatements appear only once published. Never filter on `end`.

Predecessor registrants are pulled and merged so history starts in 2014: XOM (CIK 34088, new
registrant 2115436 from Aug 2026), APA (Apache Corp, CIK 6769), BKR (Baker Hughes Inc, CIK 808362).
Comparative prior-period values re-reported in later filings appear as separate rows with later `filed` dates.

## `data/snapshot/ff3_daily.csv.gz` (Kenneth French data library)
`date`, `mkt_rf`, `smb`, `hml`, `rf`: daily Fama-French 3 factors, converted from percent to decimal.
Ken French publishes with a lag of about one to two months.

## EIA and rig counts
| source | loader | status |
|---|---|---|
| EIA API v2 (crude production, crude stocks, rig count) | `src/data/eia.py`, `src/data/eia_snapshot.py` | committed in `data/snapshot/eia.csv.gz` (`name, series, period, date, value, units`) and `eia_meta.json`; refreshed weekly by `scripts/refresh_eia.py` with `EIA_API_KEY` |
| Baker Hughes rig count | `src/data/rigs.py` | rigcount.bakerhughes.com returns HTTP 403 to scripts. A downloaded file can go at `data/manual/rig_count.csv` (or `RIG_COUNT_FILE`). The explorer uses the EIA rig series instead. |

No source is ever filled with synthetic or interpolated data. A missing source stays missing.
