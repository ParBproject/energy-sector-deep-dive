# Findings: how US oil & gas segments trade against oil

*Data as of 2026-10-22. All numbers come from `results/*.json`, which `make results` rebuilds from the committed snapshot. Explore them in the [live explorer](https://parbproject.github.io/energy-sector-deep-dive/).*

## The short version

1. **Oil sensitivity follows the value chain.** Producers (E&P) move about 0.55% for every 1% move in WTI. Refiners move about 0.27%, because they buy crude as an input. Majors, services and midstream sit in between. All of these betas are well above the S&P 500's 0.07.
2. **Every segment fell hard in 2020, but the 2015–16 bust hit midstream hardest.** Equal-weighted midstream fell 71% in 2015–16, worse than WTI itself. That was a leverage and distribution story more than a commodity one.
3. **Fundamentals rediscover the segments.** k-means on five balance-sheet and cash-flow ratios recovers the segment labels with an adjusted Rand index of 0.61 (0.76 on complete cases).
4. **Factors explain returns but do not forecast them.** Oil, gas, Brent–WTI, 10-year rate and Fama-French factors explain 54–69% of weekly segment returns within the same week. Using *last* week's factors, out-of-sample R² is negative for every segment (−3.7% to −7.7%).
5. **The scenario tool is a sensitivity, not a signal.** If WTI falls 10%, a typical week sees E&P move −5.5% (95% band −7.7% to −3.3%). The commodity-forecaster preset is a dated, already-realized forecast.

## 1. Oil beta by segment

Daily returns regressed on WTI returns, 2015 onward, with HAC (Newey-West) standard errors.

| Segment | Oil beta | 95% CI | R² |
|---|---|---|---|
| Exploration & production | 0.55 | 0.43 to 0.67 | 0.35 |
| Oilfield services | 0.40 | 0.31 to 0.50 | 0.25 |
| Integrated majors | 0.35 | 0.28 to 0.43 | 0.31 |
| Pipelines & midstream | 0.31 | 0.22 to 0.41 | 0.20 |
| Refining & marketing | 0.27 | 0.20 to 0.34 | 0.12 |
| *XLE / S&P 500* | *0.35 / 0.07* | | |

Correlations drift a lot. The latest 60-day correlation with WTI is 0.68 for E&P but only 0.11 for midstream and services. A full-sample beta should be read as an average, not a constant.

## 2. Drawdowns in three shocks

Peak-to-trough within each window, using equal-weighted segment indices.

| Shock | Majors | E&P | Midstream | Refining | Services | XLE | S&P 500 | WTI |
|---|---|---|---|---|---|---|---|---|
| 2015–16 oil bust | −33% | −43% | **−71%** | −31% | −39% | −36% | −13% | −57% |
| 2020 COVID crash | −58% | **−79%** | −66% | −67% | −72% | −61% | −34% | −71% |
| 2022 rate shock | −26% | −32% | −21% | −29% | **−41%** | −26% | −25% | −43% |

## 3. Point-in-time fundamentals and clustering

Ratios come from 10-K XBRL facts that were **filed on or before the as-of date**, so the snapshot only uses information that was public at the time. The segment medians tell a coherent story:
- Majors pay out the most (72% of operating cash flow in dividends and buybacks).
- Midstream is the most levered (debt / capital 63%).
- E&P has the highest capex intensity (25% of revenue) and the highest FCF yield (6.5%).

Clustering the 18 companies on these features gives an adjusted Rand index of 0.61 against the segment labels, with a silhouette of 0.27. Some features were imputed, so the complete-case check matters: across the 12 companies with no missing ratios, ARI rises to 0.76.

## 4. Factor model

The model regresses weekly segment returns on WTI, Henry Hub gas, the Brent–WTI spread (crack-spread proxy), the change in the 10-year yield and the Fama-French market, size and value factors, using HAC errors and walk-forward refits (156-week training window, refit weekly, scored against an expanding-mean baseline).

| Segment | In-sample R² | OOS R², same week | OOS R², lagged factors |
|---|---|---|---|
| Integrated majors | 0.69 | 67.6% | −6.0% |
| Exploration & production | 0.69 | 66.8% | −5.6% |
| Pipelines & midstream | 0.54 | 53.3% | −7.7% |
| Refining & marketing | 0.57 | 57.1% | −3.7% |
| Oilfield services | 0.65 | 64.2% | −5.8% |

The same-week result shows the exposures are stable. The lagged result is the honest headline: these factors do not predict next week's segment returns, and the leakage tests in `tests/` guard that claim.

## 5. Market sizing (proxy)

The 18 names reported **$1,278bn** of FY2025 revenue (17 of 18 companies; APA has no standard revenue tag). This is a measure of the scale of cash flows, not a market size. It is global and consolidated, it double counts along the chain (refiners buy producers' crude), and it includes pass-through product sales. The top-down figure (US production × WTI) was not computed, because it needs an EIA key that the snapshot does not have.

## Limitations, stated plainly

- **Survivorship bias.** The universe is 18 names that survived to today. Anadarko, Noble, Concho, Pioneer, Hess, Andeavor, Weatherford and others are excluded, so segment returns, especially E&P and services in 2015–16 and 2020, look better than an investor at the time would have experienced.
- **Small segments.** With three to five names per segment, equal-weighted segment indices can be dominated by a single company.
- **Proxies.** The crack spread is proxied by the Brent–WTI spread, because RBOB and heating-oil futures are not in the snapshot. There is no dollar-index factor.
- **Missing tags are left blank, not estimated.** COP, PSX, VLO, APA, ET and FANG lack some ratios. Clustering imputes 13 of 108 cells with the universe median (flagged), so the complete-case ARI is reported alongside.
- **Linear, full-sample betas.** Betas vary by regime (see the rolling correlations), and the scenario tool applies a single linear beta with a 95% band from its standard error. Real moves of ±30% are outside the data's typical weekly range.
- **Not investment advice.** This is descriptive and sensitivity analysis only; nothing here is a trading signal.

## Reproduce

```bash
make results    # results/*.json and charts from data/snapshot/
make export     # web data for the explorer
make test       # ruff, pytest (incl. leakage and point-in-time tests), vitest
make web        # production build of the explorer
```
