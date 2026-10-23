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
