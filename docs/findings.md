# Findings

Price data runs through 2026-10-22. The EIA snapshot is as of 2026-10-23. Figures below are the ones in `results/*.json`, which `make results` rebuilds from `data/snapshot/`. The same files drive the [explorer](https://parbproject.github.io/energy-sector-deep-dive/).

## Oil beta

Daily returns on WTI returns, from 2015, with Newey-West standard errors (5 lags). Segments are equal-weighted.

| Segment | Oil beta | 95% CI | R² |
|---|---|---|---|
| Exploration & production | 0.55 | 0.43 to 0.67 | 0.35 |
| Oilfield services | 0.40 | 0.31 to 0.50 | 0.25 |
| Integrated majors | 0.35 | 0.28 to 0.43 | 0.31 |
| Pipelines & midstream | 0.31 | 0.22 to 0.41 | 0.20 |
| Refining & marketing | 0.27 | 0.20 to 0.34 | 0.12 |
| XLE / S&P 500 | 0.35 / 0.07 | | |

The latest 60-day correlation with WTI is 0.68 for E&P and 0.11 for midstream and for services. The full-sample beta is an average over the window.

## Drawdowns

Peak-to-trough inside each window in `src/analysis/returns.py`. The 2015–16 window is those two calendar years. The 2020 and 2022 windows are each calendar year, not a shorter event window.

| Window | Majors | E&P | Midstream | Refining | Services | XLE | S&P 500 | WTI |
|---|---|---|---|---|---|---|---|---|
| 2015–16 | −33.4% | −43.0% | −71.3% | −31.4% | −39.2% | −36.1% | −13.0% | −57.3% |
| 2020 | −57.5% | −78.7% | −65.6% | −66.8% | −72.1% | −60.6% | −33.7% | −71.1% |
| 2022 | −26.1% | −31.6% | −20.9% | −29.3% | −40.7% | −26.0% | −24.5% | −42.6% |

In the 2015–16 window, equal-weighted midstream fell more than WTI. In 2020, E&P fell the most. Midstream also has the highest segment median debt/capital (62.6%) in the latest 10-Ks. That ratio is a level, not a measured cause of the drawdown.

## Fundamentals and clustering

Ratios use 10-K facts whose filing date is on or before the as-of date. Latest segment medians:

- Majors: payout (dividends + buybacks) / operating cash flow 72.2%.
- Midstream: debt / capital 62.6%.
- E&P: capex / revenue 25.2%, and (operating cash flow − capex) / market cap 6.5%.

k-means with k=5 on oil beta and these ratios has an adjusted Rand index of 0.61 against the segment labels, and a silhouette of 0.27. Thirteen of 108 feature cells are the universe median, flagged as imputed. On the 12 companies with no missing ratios, the ARI is 0.76. The five E&P names share one cluster. WMB is alone in its cluster. The other clusters mix segments.

## Factor model

Weekly segment excess returns on WTI, Henry Hub, the change in (Brent − WTI) / WTI, the change in the 10-year yield, and the Fama-French market, size, and value factors. Standard errors are HAC. The walk-forward fit uses 156 training weeks, then refits every week, and scores against an expanding-mean baseline.

| Segment | In-sample R² | OOS R², same week | OOS R², lagged factors |
|---|---|---|---|
| Integrated majors | 0.69 | 67.6% | −6.0% |
| Exploration & production | 0.69 | 66.8% | −5.6% |
| Pipelines & midstream | 0.54 | 53.3% | −7.7% |
| Refining & marketing | 0.57 | 57.1% | −3.7% |
| Oilfield services | 0.65 | 64.2% | −5.8% |

Same-week factors are that week's realized values, so that column is a fit, not a forecast. Lagged factors are last week's values. Those out-of-sample R² are negative for every segment. `tests/test_leakage.py` checks that the walk-forward does not use future rows.

The Brent–WTI term is a stand-in. RBOB and heating-oil futures are not in the snapshot, so there is no 3-2-1 crack. There is no dollar-index series either.

## Market size

The 18 names reported $1,278bn of FY2025 revenue. Seventeen companies have a standard revenue tag; APA does not, and is left out rather than filled in. The total is global consolidated revenue. It counts the same barrel more than once when a refiner buys a producer's crude, and it includes product sales that pass through at market prices. It is a scale of reported sales, not a US market size.

US field crude production in 2025 averaged 13,662 kb/d in the EIA snapshot. Valued at the monthly average WTI spot, that is about $326bn. The exact figure is regenerated into the README from `results/market_sizing.json`, with the caveats stored next to it (Cushing spot rather than realized wellhead prices; crude only; recent months are EIA estimates and get revised).

## Limits

- Survivorship. The 18 names are the ones that still trade. Segment returns, especially E&P and services in 2015–16 and 2020, omit names that were bought or went through bankruptcy.
- Three to five names per segment. An equal-weighted index can be one company.
- Missing XBRL tags stay blank. COP, PSX, VLO, APA, ET, and FANG are each missing at least one ratio.
- The scenario tool multiplies a weekly oil beta by a WTI move and draws a 95% band from the beta's standard error. A 30% week is outside the usual range of the sample.
- Nothing here is a trading signal.

## Reproduce

```bash
make results    # results/*.json and charts from data/snapshot/
make export     # JSON for the explorer
make test       # ruff, pytest, vitest
make web        # production build
```
