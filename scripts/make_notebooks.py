"""Build and execute the three M2 narrative notebooks (outputs are committed)."""

from __future__ import annotations

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

from src.analysis.common import ROOT

SETUP = """import sys, json
sys.path.insert(0, "..")
import pandas as pd
pd.set_option("display.float_format", "{:,.3f}".format)
from IPython.display import Image, Markdown, display"""

NOTEBOOKS = {
    "01_market_sizing.ipynb": [
        (
            "md",
            "# 01 · Market sizing\n\nThe textbook top-down size of US upstream is *US crude output x WTI*. "
            "That needs a production volume series. EIA is unavailable here (no `EIA_API_KEY`) and the FRED "
            "snapshot contains prices, rates and indices but no volumes, so we **do not** invent one. "
            "Instead we build a bottom-up proxy from what companies actually reported in their 10-Ks, "
            "read point-in-time by filing date.",
        ),
        ("code", SETUP),
        ("code", "from src.analysis import sizing\nres = sizing.compute()\nres['topdown_status']"),
        ("md", "## Reported revenue by segment ($bn, fiscal year)"),
        ("code", "pd.DataFrame(res['segment_revenue_usd']).sort_index() / 1e9"),
        (
            "code",
            "display(Markdown(f\"FY{res['latest_fiscal_year']} total: **${res['total_revenue_latest_usd']/1e9:,.0f}bn**; "
            "missing: {', '.join(res['missing_revenue_latest_year']) or 'none'}\"))\n"
            "pd.Series(res['segment_share_latest'], name='share').map('{:.1%}'.format)",
        ),
        ("md", "## Why this is a proxy, not a market size"),
        ("code", "for c in res['caveats']:\n    print('-', c)"),
        ("code", "Image('../docs/img/segment_revenue.png')"),
        (
            "md",
            "**Takeaway.** Revenue is dominated by majors and refiners because their sales pass crude and "
            "products through at market prices; upstream and services are small by revenue but, as notebook 02 "
            "shows, carry most of the oil risk. A true top-down size waits on an EIA key.",
        ),
    ],
    "02_returns_beta_drawdowns.ipynb": [
        (
            "md",
            "# 02 · Returns, correlations and oil beta\n\nDaily simple returns of adjusted closes from 2015. "
            "Oil is the CL=F front-month WTI future, the same series the commodity forecaster uses. "
            "Segments are equal-weighted. Beta comes from OLS of daily returns on oil returns with "
            "Newey-West (HAC, 5 lags) standard errors. Returns touching the negative 2020-04-20 settlement are excluded.",
        ),
        ("code", SETUP),
        (
            "code",
            "from src.analysis import returns\nres = returns.compute()\n"
            "seg = pd.DataFrame(res['betas']['segments']).T[['beta','se_hac','t_hac','r2','n']]\nseg",
        ),
        (
            "code",
            "comp = pd.DataFrame(res['betas']['companies']).T[['segment','beta','t_hac','r2']]\n"
            "comp.sort_values('beta', ascending=False)",
        ),
        ("code", "Image('../docs/img/oil_beta.png')"),
        (
            "md",
            "## Rolling 60-day correlations\nThe sign flips with S&P are the interesting part: in oil-led "
            "markets energy decouples from the index.",
        ),
        ("code", "pd.DataFrame(res['correlations']['latest']).T"),
        ("code", "Image('../docs/img/rolling_corr.png')"),
        ("md", "## Drawdowns in the three shocks"),
        (
            "code",
            "pd.DataFrame({k: {s: v['max_drawdown'] for s, v in d.items()} for k, d in res['drawdowns'].items()})",
        ),
        ("code", "Image('../docs/img/drawdowns.png')"),
        (
            "code",
            "hi, lo = res['highest_beta_segment'], res['lowest_beta_segment']\n"
            "display(Markdown(f\"**Takeaway.** {hi} has the highest oil beta ({res['betas']['segments'][hi]['beta']:.2f}), "
            "{lo} the lowest ({res['betas']['segments'][lo]['beta']:.2f}). Even the highest R² is modest: oil explains "
            'well under half of daily segment variance."))',
        ),
    ],
    "03_fundamentals.ipynb": [
        (
            "md",
            "# 03 · Point-in-time fundamentals\n\nEach company's latest full fiscal year whose 10-K was **filed** "
            "on or before the as-of date (never the period end, which would leak data that wasn't public yet). "
            "Ratios are ranked as percentiles within each segment.",
        ),
        ("code", SETUP),
        (
            "code",
            "from src.analysis import fundamentals\nres = fundamentals.compute()\npd.Series(res['definitions'])",
        ),
        (
            "code",
            "comp = pd.DataFrame(res['companies']).T\n"
            "comp[['segment','fiscal_year_end', *res['definitions']]]",
        ),
        ("md", "## Segment medians"),
        ("code", "pd.DataFrame(res['segment_median']).T"),
        (
            "md",
            "## Point-in-time check\nThe same code as of 2025-12-31 sees FY2024 10-Ks, because FY2025 10-Ks were not yet filed.",
        ),
        (
            "code",
            "early = fundamentals.company_metrics('2025-12-31')\nearly['fiscal_year_end'].value_counts()",
        ),
        (
            "md",
            "## Gaps\nWhere a company files an input under a company-specific tag, the ratio is left blank, not estimated.",
        ),
        ("code", "{k: v for k, v in res['missing'].items() if v}"),
        ("code", "Image('../docs/img/fundamentals_heatmap.png')"),
    ],
    "04_clustering.ipynb": [
        (
            "md",
            "# 04 · Clustering\n\nDo oil beta and point-in-time fundamentals rediscover the five segments? "
            "Features are z-scored. Missing ratios are imputed with the **universe** median (not the segment "
            "median, which would leak the answer) and every imputed cell is flagged. A complete-case run is the check.",
        ),
        ("code", SETUP),
        (
            "code",
            "from src.analysis import clustering\nraw, z, seg, imputed = clustering.feature_matrix()\nraw.assign(segment=seg)",
        ),
        ("code", "imputed.sum().rename('imputed cells')"),
        ("code", "res = clustering.compute()\npd.DataFrame(res['silhouette_by_k'])"),
        (
            "code",
            "pd.DataFrame({n: {'silhouette': v['silhouette'], 'ARI vs segments': v['adjusted_rand_vs_segments']} for n, v in res['k5'].items()})",
        ),
        (
            "code",
            "pd.DataFrame({'segment': seg, 'kmeans': res['k5']['kmeans']['assignments'], 'ward': res['k5']['ward']['assignments']}).sort_values('kmeans')",
        ),
        ("code", "res['complete_case']"),
        ("code", "Image('../docs/img/clusters.png')"),
        (
            "code",
            "display(Markdown(f\"**Takeaway.** Clusters recover the segments only partly (ARI {res['k5']['kmeans']['adjusted_rand_vs_segments']:.2f}): "
            'producers group cleanly, while majors land with refiners on low leverage and high payouts, and WMB stands alone as the most levered, highest-reinvestment name."))',
        ),
    ],
    "05_factor_model.ipynb": [
        (
            "md",
            "# 05 · Weekly factor model and walk-forward test\n\nFactors: oil, gas, a crack-spread **proxy** "
            "(change in the Brent-WTI spread, because gasoline and heating-oil futures are not in the snapshot), "
            "the change in the 10-year yield and Fama-French 3. No dollar series exists in the snapshot, so none is used. "
            "Full-sample fits use HAC errors. Out-of-sample R² comes from an expanding window refit every week with no look-ahead.",
        ),
        ("code", SETUP),
        (
            "code",
            "from src.analysis import factor_model as fm\nres = fm.compute()\nres['sample'], res['crack_spread_proxy'], res['dollar_proxy']",
        ),
        ("code", "pd.DataFrame({s: v['coef'] for s, v in res['full_sample'].items()})"),
        ("code", "pd.DataFrame({s: v['t_hac'] for s, v in res['full_sample'].items()})"),
        ("code", "Image('../docs/img/factor_tstats.png')"),
        (
            "code",
            "pd.DataFrame({'explanatory (same-week factors)': {s: v['vs_hist_mean'] for s, v in res['walk_forward_explanatory'].items()},\n"
            "              'predictive (lag-1 factors)': {s: v['vs_hist_mean'] for s, v in res['walk_forward_predictive_lag1'].items()},\n"
            "              'predictive vs zero': {s: v['vs_zero'] for s, v in res['walk_forward_predictive_lag1'].items()}})",
        ),
        ("code", "Image('../docs/img/oos_r2.png')"),
        (
            "md",
            "**Takeaway.** The exposures are real and stable: same-week factors explain more than half of weekly variance out of sample. "
            "Last week's factors forecast nothing, with out-of-sample R² below zero against both baselines. That is what an efficient market predicts, "
            "and it is why the scenario tool is framed as sensitivity analysis.",
        ),
    ],
    "06_scenarios.ipynb": [
        (
            "md",
            "# 06 · Oil scenarios and the forecaster tie-in\n\nMaps a WTI % move to each segment's expected move using weekly oil betas with HAC bands. "
            "**This is sensitivity analysis, not a trading signal.**",
        ),
        ("code", SETUP),
        (
            "code",
            "from src.scenarios import oil, forecaster\nres = oil.compute()\npd.DataFrame(res['weekly_betas']).T",
        ),
        ("code", "pd.DataFrame(oil.scenario(-10, res['weekly_betas'])).T"),
        (
            "md",
            "## Commodity-forecaster input\nThe forecaster publishes rolling one-step **backtest** forecasts in `results/leaderboard.json`. "
            "A dated copy is vendored in `data/vendor/`. Its last step has already been realized, so it is shown as a preset next to the "
            "slider, not as a forward view.",
        ),
        ("code", "res['forecaster_input']"),
        ("code", "pd.DataFrame(res['forecaster_scenario']).T"),
        ("code", "Image('../docs/img/scenario_fan.png')"),
    ],
}


def main() -> None:
    nb_dir = ROOT / "notebooks"
    for name, cells in NOTEBOOKS.items():
        nb = nbf.v4.new_notebook()
        nb.metadata["kernelspec"] = {
            "name": "python3",
            "display_name": "Python 3",
            "language": "python",
        }
        nb.cells = [
            nbf.v4.new_markdown_cell(src) if kind == "md" else nbf.v4.new_code_cell(src)
            for kind, src in cells
        ]
        ExecutePreprocessor(timeout=600, kernel_name="python3").preprocess(
            nb, {"metadata": {"path": str(nb_dir)}}
        )
        nbf.write(nb, nb_dir / name)
        print("executed", name)


if __name__ == "__main__":
    main()
