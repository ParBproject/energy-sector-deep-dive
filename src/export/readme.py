"""Render the README findings section from results/*.json (no hand-typed numbers)."""

from __future__ import annotations

from src.analysis.common import ROOT, SEGMENT_ORDER, read_json, segment_labels

START, END = "<!-- findings:start -->", "<!-- findings:end -->"


def _pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def _topdown_line(td: dict) -> str:
    if not td["available"]:
        return (
            f"- The top-down size (US output x WTI) is **not computed**: it needs "
            f"{td['requires']} ({td['reason']})."
        )
    return (
        f"- Top-down: US field crude output in {td['year']} was "
        f"{td['us_crude_production_avg_kbd']:,.0f} kb/d "
        f"({td['us_crude_production_bbl'] / 1e9:.2f}bn bbl), worth "
        f"**${td['us_crude_value_usd'] / 1e9:,.0f}bn** at monthly average WTI "
        f"(EIA MCRFPUS2 x FRED DCOILWTICO; EIA data as of {td['eia_as_of']}). "
        + " ".join(td["caveats"])
    )


def render() -> str:
    sz, rt, fd = (read_json(n) for n in ("market_sizing.json", "returns.json", "fundamentals.json"))
    lab = segment_labels()
    y = str(sz["latest_fiscal_year"])
    seg_b = rt["betas"]["segments"]
    lines = [
        START,
        "## Returns, sizing and fundamentals",
        "",
        f"_From `results/*.json`, via `python -m scripts.run_m2`. Data as of {rt['as_of']}._",
        "",
        "### Oil beta",
        "![Oil beta](docs/img/oil_beta.png)",
        "",
        f"- **{lab[rt['highest_beta_segment']]}** is the most oil-sensitive segment: beta "
        f"{seg_b[rt['highest_beta_segment']]['beta']:.2f} per 1% WTI move "
        f"(HAC t = {seg_b[rt['highest_beta_segment']]['t_hac']:.1f}). "
        f"**{lab[rt['lowest_beta_segment']]}** is the least: "
        f"{seg_b[rt['lowest_beta_segment']]['beta']:.2f}. XLE: "
        f"{rt['betas']['benchmarks']['XLE']['beta']:.2f}; S&P 500: "
        f"{rt['betas']['benchmarks']['SPY']['beta']:.2f}.",
        "",
        "| Segment | Oil beta | 95% CI | R² | 60d corr WTI (latest) | 60d corr S&P (latest) |",
        "|---|---|---|---|---|---|",
    ]
    for s in SEGMENT_ORDER:
        b, c = seg_b[s], rt["correlations"]["latest"][s]
        lines.append(
            f"| {lab[s]} | {b['beta']:.2f} | {b['ci95'][0]:.2f} to {b['ci95'][1]:.2f} | "
            f"{b['r2']:.2f} | {c['wti']:.2f} | {c['spx']:.2f} |"
        )
    lines += [
        "",
        "![Rolling correlations](docs/img/rolling_corr.png)",
        "",
        "### Drawdowns in the three shocks",
        "![Drawdowns](docs/img/drawdowns.png)",
        "",
        "| Shock | " + " | ".join(lab[s] for s in SEGMENT_ORDER) + " | XLE | S&P 500 | WTI |",
        "|---|" + "---|" * (len(SEGMENT_ORDER) + 3),
    ]
    for shock, d in rt["drawdowns"].items():
        keys = [*SEGMENT_ORDER, "XLE", "SPY", "CL=F"]
        lines.append(f"| {shock} | " + " | ".join(_pct(d[k]["max_drawdown"]) for k in keys) + " |")
    total = sz["total_revenue_latest_usd"] / 1e9
    lines += [
        "",
        "### Market sizing (proxy)",
        "![Segment revenue](docs/img/segment_revenue.png)",
        "",
        _topdown_line(sz["topdown_status"]),
        f"- Bottom-up proxy: the universe reported **${total:,.0f}bn** of FY{y} revenue "
        f"({sz['companies_reporting_by_year'][y]} of {fd['universe_size']} companies; missing: "
        f"{', '.join(sz['missing_revenue_latest_year']) or 'none'}). Average WTI in {y}: "
        f"${sz['wti_avg_latest_year_usd_bbl']:.2f}/bbl.",
        "- Shares of that revenue: "
        + ", ".join(f"{lab[s]} {_pct(sz['segment_share_latest'][s])}" for s in SEGMENT_ORDER)
        + ".",
        "- Caveats: " + " ".join(sz["caveats"]),
        "",
        "### Fundamentals (point-in-time, filing dates)",
        "![Fundamentals heatmap](docs/img/fundamentals_heatmap.png)",
        "",
        "| Segment median | " + " | ".join(fd["definitions"].values()) + " |",
        "|---|" + "---|" * len(fd["definitions"]),
    ]
    for s in SEGMENT_ORDER:
        med = fd["segment_median"][s]
        lines.append(f"| {lab[s]} | " + " | ".join(_pct(med[m]) for m in fd["definitions"]) + " |")
    miss = {k: v for k, v in fd["missing"].items() if v}
    lines += [
        "",
        "Not computed where a company files the input under a non-standard tag "
        "(left blank rather than estimated): "
        + "; ".join(f"{k}: {', '.join(v)}" for k, v in miss.items())
        + ".",
        END,
    ]
    return "\n".join(lines)


FORECASTER_URL = "https://github.com/ParBproject/commodity-price-forecaster"
M3_START, M3_END = "<!-- m3-findings:start -->", "<!-- m3-findings:end -->"


def render_m3() -> str:
    cl, fm, sc = (read_json(n) for n in ("clustering.json", "factor_model.json", "scenarios.json"))
    lab = segment_labels()
    km, wd = cl["k5"]["kmeans"], cl["k5"]["ward"]
    lines = [
        M3_START,
        "## Clustering, factors and scenarios",
        "",
        "_From `results/*.json`, via `python -m scripts.run_m3`._",
        "",
        "### Clustering vs the five segments",
        "![Clusters](docs/img/clusters.png)",
        "",
        f"- k-means (k=5): silhouette {km['silhouette']:.2f}, adjusted Rand vs the 5 segments "
        f"**{km['adjusted_rand_vs_segments']:.2f}**. Ward hierarchical: silhouette "
        f"{wd['silhouette']:.2f}, ARI {wd['adjusted_rand_vs_segments']:.2f}.",
        f"- The segments themselves score a silhouette of only "
        f"{cl['silhouette_of_true_segments']:.2f} on these features. Best k by silhouette: "
        f"{cl['best_k']['kmeans']} (k-means).",
        f"- {cl['n_imputed_cells']} of {cl['n_companies'] * len(cl['features'])} feature cells "
        f"were imputed ({cl['imputation']}). Complete-case check "
        f"({cl['complete_case']['n_companies']} companies, dropping "
        f"{', '.join(cl['complete_case']['dropped'])}): ARI "
        f"{cl['complete_case']['kmeans_k5_adjusted_rand']:.2f}.",
        "",
        "### Factor model (weekly, HAC)",
        "![Factor t-stats](docs/img/factor_tstats.png)",
        "",
        f"- Sample {fm['sample']['first_week']} to {fm['sample']['last_week']} "
        f"({fm['sample']['n_weeks']} weeks). Crack-spread proxy: {fm['crack_spread_proxy']}. "
        + (
            "No dollar-index series is in the snapshot."
            if str(fm["dollar_proxy"]).startswith("unavailable")
            else f"Dollar: {fm['dollar_proxy']}."
        ),
        "",
        "| Segment | In-sample R² | OOS R², same-week factors | OOS R², last week's factors |",
        "|---|---|---|---|",
    ]
    for s in SEGMENT_ORDER:
        lines.append(
            f"| {lab[s]} | {fm['full_sample'][s]['r2']:.2f} | "
            f"{_pct(fm['walk_forward_explanatory'][s]['vs_hist_mean'])} | "
            f"{_pct(fm['walk_forward_predictive_lag1'][s]['vs_hist_mean'])} |"
        )
    lines += [
        "",
        "Out-of-sample R² is versus an expanding historical mean, refit weekly after "
        f"{fm['min_train_weeks']} training weeks. The same-week column uses that week's "
        "factors. The last column uses the previous week's factors.",
        "",
        "![Walk-forward OOS R²](docs/img/oos_r2.png)",
        "",
        "### Oil scenarios (sensitivity, not a signal)",
        "![Scenario fan](docs/img/scenario_fan.png)",
        "",
        "| Segment | Weekly oil beta | Expected move if WTI -10% | 95% band (beta SE) |",
        "|---|---|---|---|",
    ]
    for s in SEGMENT_ORDER:
        g = sc["grid"]["-10"][s]
        lines.append(
            f"| {lab[s]} | {sc['weekly_betas'][s]['beta']:.2f} | {g['expected_pct']:.1f}% | "
            f"{g['param_band_pct'][0]:.1f}% to {g['param_band_pct'][1]:.1f}% |"
        )
    fc = sc["forecaster_input"]
    if "implied_move_pct" in fc:
        lines += [
            "",
            f"Forecaster tie-in: the latest one-step WTI forecast published by "
            f"[commodity-price-forecaster]({FORECASTER_URL}) "
            f"({fc['model']}, week {fc['target_week']}, "
            f"commit `{fc['source_commit'][:7]}`) implied "
            f"{fc['implied_move_pct']:+.2f}%; WTI actually moved {fc['realized_move_pct']:+.2f}%. "
            "That step is already realized, so the explorer defaults to a slider and offers the "
            "forecast only as a preset.",
        ]
    lines.append(M3_END)
    return "\n".join(lines)


def _splice(text: str, start: str, end: str, block: str, before: str) -> str:
    if start in text:
        head, rest = text.split(start, 1)
        return head + block + rest.split(end, 1)[1]
    return text.replace(before, block + "\n\n" + before, 1)


def update_readme() -> str:
    path = ROOT / "README.md"
    text = path.read_text()
    block = render()
    text = _splice(text, START, END, block, "## How to run")
    try:
        text = _splice(text, M3_START, M3_END, render_m3(), "## How to run")
    except FileNotFoundError:
        pass
    path.write_text(text)
    return block
