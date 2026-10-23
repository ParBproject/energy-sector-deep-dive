"""README charts: dark theme matching parbproject.github.io, emerald #10B981 accent."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from src.analysis.common import ROOT, SEGMENT_ORDER, segment_labels  # noqa: E402

IMG = ROOT / "docs" / "img"
BG, PANEL, TEXT, MUTED, GRID = "#0B0F14", "#111827", "#E5E7EB", "#9CA3AF", "#1F2937"
EMERALD = "#10B981"
SEG_COLORS = {
    "majors": EMERALD,
    "upstream": "#34D399",
    "midstream": "#60A5FA",
    "refiners": "#F59E0B",
    "services": "#A78BFA",
}


def theme() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": PANEL,
            "savefig.facecolor": BG,
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT,
            "text.color": TEXT,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "grid.color": GRID,
            "axes.grid": True,
            "grid.linewidth": 0.6,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "legend.frameon": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "DejaVu Sans",
        }
    )


def _save(fig, name: str, source: str) -> str:
    fig.text(0.01, 0.01, source, color=MUTED, fontsize=7.5, ha="left", va="bottom")
    IMG.mkdir(parents=True, exist_ok=True)
    path = IMG / name
    fig.savefig(path, dpi=160, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    return str(path.relative_to(ROOT))


def segment_revenue(sizing: dict) -> str:
    theme()
    labels = segment_labels()
    data = pd.DataFrame(sizing["segment_revenue_usd"]).sort_index() / 1e9
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bottom = np.zeros(len(data))
    for s in SEGMENT_ORDER:
        ax.bar(
            data.index.astype(str),
            data[s],
            bottom=bottom,
            color=SEG_COLORS[s],
            label=labels[s],
            width=0.7,
        )
        bottom += data[s].fillna(0).values
    ax.set_title("Reported revenue by segment, $bn (fiscal year)")
    ax.set_ylabel("$bn")
    ax.legend(ncol=5, loc="upper left", fontsize=8.5, bbox_to_anchor=(0, 1.0))
    ax.set_ylim(0, bottom.max() * 1.15)
    return _save(
        fig,
        "segment_revenue.png",
        "Source: SEC EDGAR 10-K XBRL, point-in-time. Global revenue, double counts the "
        "value chain; a proxy, not a market size.",
    )


def oil_beta(ret: dict) -> str:
    theme()
    labels = segment_labels()
    comp = pd.DataFrame(ret["betas"]["companies"]).T
    comp["order"] = comp["segment"].map(SEGMENT_ORDER.index)
    comp = comp.sort_values(["order", "beta"], ascending=[False, True])
    fig, ax = plt.subplots(figsize=(9, 6.2))
    y = np.arange(len(comp))
    err = np.array(
        [[b - c[0], c[1] - b] for b, c in zip(comp["beta"], comp["ci95"], strict=True)]
    ).T
    ax.barh(y, comp["beta"], color=[SEG_COLORS[s] for s in comp["segment"]], height=0.65)
    ax.errorbar(comp["beta"], y, xerr=err, fmt="none", ecolor=TEXT, elinewidth=0.8, capsize=2)
    ax.set_yticks(y, comp.index)
    xle = ret["betas"]["benchmarks"]["XLE"]["beta"]
    ax.axvline(xle, color=MUTED, ls="--", lw=1)
    ax.text(xle, len(comp) - 0.3, f" XLE {xle:.2f}", color=MUTED, fontsize=8, va="bottom")
    handles = [Patch(color=SEG_COLORS[s], label=labels[s]) for s in SEGMENT_ORDER]
    ax.legend(handles=handles, loc="lower right", fontsize=8.5)
    ax.set_title("Oil beta: daily return per 1% move in WTI (CL=F), 2015 to date")
    ax.set_xlabel("beta (95% CI, HAC standard errors)")
    return _save(fig, "oil_beta.png", "Source: yfinance adjusted closes; OLS with Newey-West SEs.")


def rolling_corr(rc: dict[str, pd.DataFrame]) -> str:
    theme()
    labels = segment_labels()
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True)
    for ax, key, title in [
        (axes[0], "wti", "with WTI (CL=F)"),
        (axes[1], "spx", "with S&P 500 (SPY)"),
    ]:
        df = rc[key]
        for s in SEGMENT_ORDER:
            ax.plot(df.index, df[s], color=SEG_COLORS[s], lw=1.0, label=labels[s], alpha=0.95)
        ax.axhline(0, color=MUTED, lw=0.7)
        ax.set_ylim(-1, 1)
        ax.set_title(f"Rolling 60-day correlation {title}", fontsize=11.5)
    axes[0].legend(ncol=5, fontsize=8, loc="lower left")
    return _save(
        fig, "rolling_corr.png", "Source: yfinance daily returns; equal-weighted segments."
    )


def drawdowns(ret: dict) -> str:
    theme()
    labels = {**segment_labels(), "XLE": "XLE", "SPY": "S&P 500", "CL=F": "WTI"}
    dd = pd.DataFrame(
        {k: {s: v["max_drawdown"] for s, v in d.items()} for k, d in ret["drawdowns"].items()}
    )
    keys = [*SEGMENT_ORDER, "XLE", "SPY", "CL=F"]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    x = np.arange(len(dd.columns))
    w = 0.8 / len(keys)
    colors = {**SEG_COLORS, "XLE": TEXT, "SPY": MUTED, "CL=F": "#EF4444"}
    for i, k in enumerate(keys):
        ax.bar(x + i * w - 0.4 + w / 2, dd.loc[k] * 100, w, color=colors[k], label=labels[k])
    ax.set_xticks(x, dd.columns)
    ax.set_ylabel("max drawdown, %")
    ax.set_title("Peak-to-trough drawdown within each shock window")
    ax.legend(ncol=4, fontsize=8, loc="lower left")
    return _save(
        fig, "drawdowns.png", "Source: yfinance; WTI excludes the negative 2020-04-20 print."
    )


def fundamentals_heatmap(fund: dict) -> str:
    theme()
    comp = fund["companies"]
    metrics = list(fund["definitions"])
    order = sorted(comp, key=lambda t: (SEGMENT_ORDER.index(comp[t]["segment"]), t))
    mat = np.array(
        [
            [
                comp[t]["segment_percentile"][m]
                if comp[t]["segment_percentile"][m] is not None
                else np.nan
                for m in metrics
            ]
            for t in order
        ],
        dtype=float,
    )
    fig, ax = plt.subplots(figsize=(8.5, 7))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("em", [PANEL, EMERALD])
    cmap.set_bad(GRID)
    ax.imshow(mat, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.grid(False)
    for i, t in enumerate(order):
        for j, m in enumerate(metrics):
            raw = comp[t][m]
            txt = "n/a" if raw is None else f"{raw * 100:.0f}%"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8, color=TEXT)
    ax.set_xticks(range(len(metrics)), [m.replace("_", "\n") for m in metrics], fontsize=8.5)
    ax.set_yticks(range(len(order)), [f"{t}  ({comp[t]['segment']})" for t in order], fontsize=8.5)
    ax.set_title(
        f"Fundamentals, point-in-time as of {fund['as_of']}: shade = percentile in segment"
    )
    return _save(
        fig,
        "fundamentals_heatmap.png",
        "Source: SEC EDGAR 10-K (filing-date as-of), yfinance price. Cell text = raw value.",
    )


# ── M3 ──────────────────────────────────────────────────────────────────────
MARKERS = {"majors": "o", "upstream": "s", "midstream": "D", "refiners": "^", "services": "v"}
CLUSTER_COLORS = [EMERALD, "#60A5FA", "#F59E0B", "#A78BFA", "#F472B6", "#E5E7EB"]


def clusters(cl: dict) -> str:
    theme()
    labels = segment_labels()
    pca, assign = cl["pca"], cl["k5"]["kmeans"]["assignments"]
    fig, ax = plt.subplots(figsize=(9, 5.6))
    for t, (x, y) in pca["coords"].items():
        seg = pca["segment"][t]
        ax.scatter(
            x,
            y,
            s=110,
            marker=MARKERS[seg],
            color=CLUSTER_COLORS[assign[t]],
            edgecolor=BG,
            linewidth=0.8,
        )
        ax.annotate(t, (x, y), xytext=(6, 4), textcoords="offset points", fontsize=8, color=TEXT)
    seg_h = [
        plt.Line2D([], [], marker=MARKERS[s], ls="", color=MUTED, label=labels[s])
        for s in SEGMENT_ORDER
    ]
    ax.legend(handles=seg_h, fontsize=8, loc="best", title="marker = segment", title_fontsize=8)
    ev = pca["explained_variance_ratio"]
    ax.set_xlabel(f"PC1 ({ev[0]:.0%} of variance)")
    ax.set_ylabel(f"PC2 ({ev[1]:.0%})")
    k5 = cl["k5"]["kmeans"]
    ax.set_title(
        f"k-means (k=5) on oil beta + fundamentals: colour = cluster, "
        f"ARI vs segments {k5['adjusted_rand_vs_segments']:.2f}"
    )
    return _save(
        fig,
        "clusters.png",
        f"Standardized features; {cl['n_imputed_cells']} imputed "
        "cells (universe median, flagged). Source: results/clustering.json",
    )


def oos_r2(fm: dict) -> str:
    theme()
    labels = segment_labels()
    ex = [fm["walk_forward_explanatory"][s]["vs_hist_mean"] for s in SEGMENT_ORDER]
    pr = [fm["walk_forward_predictive_lag1"][s]["vs_hist_mean"] for s in SEGMENT_ORDER]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    x = np.arange(len(SEGMENT_ORDER))
    ax.bar(
        x - 0.2,
        np.array(ex) * 100,
        0.38,
        color=EMERALD,
        label="same-week factors (exposure stability)",
    )
    ax.bar(
        x + 0.2, np.array(pr) * 100, 0.38, color="#EF4444", label="last week's factors (forecast)"
    )
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xticks(x, [labels[s] for s in SEGMENT_ORDER], fontsize=8.5)
    ax.set_ylabel("out-of-sample R², % vs historical mean")
    ax.set_title("Walk-forward factor model: explains well, forecasts nothing")
    ax.legend(fontsize=8.5, loc="center right")
    return _save(
        fig, "oos_r2.png", "Expanding window, refit weekly, first 156 weeks training only."
    )


def factor_tstats(fm: dict) -> str:
    theme()
    labels = segment_labels()
    facs = fm["factors"]
    mat = np.array([[fm["full_sample"][s]["t_hac"][f] for f in facs] for s in SEGMENT_ORDER])
    fig, ax = plt.subplots(figsize=(9, 4))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("div", ["#EF4444", PANEL, EMERALD])
    ax.imshow(np.clip(mat, -6, 6), cmap=cmap, vmin=-6, vmax=6, aspect="auto")
    ax.grid(False)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]:.1f}", ha="center", va="center", fontsize=8.5, color=TEXT)
    ax.set_xticks(range(len(facs)), facs)
    ax.set_yticks(range(len(SEGMENT_ORDER)), [labels[s] for s in SEGMENT_ORDER])
    ax.set_title("Weekly factor model: HAC t-statistics")
    return _save(
        fig,
        "factor_tstats.png",
        "brent_wti = crack-spread proxy (Brent-WTI spread change); no dollar series in snapshot.",
    )


def scenario_fan(sc: dict) -> str:
    theme()
    labels = segment_labels()
    grid = sorted(sc["grid"], key=float)
    xs = np.array([float(g) for g in grid])
    fig, ax = plt.subplots(figsize=(9, 5))
    for s in SEGMENT_ORDER:
        mid = np.array([sc["grid"][g][s]["expected_pct"] for g in grid])
        lo = np.array([sc["grid"][g][s]["param_band_pct"][0] for g in grid])
        hi = np.array([sc["grid"][g][s]["param_band_pct"][1] for g in grid])
        ax.plot(xs, mid, color=SEG_COLORS[s], lw=1.6, label=labels[s])
        ax.fill_between(xs, lo, hi, color=SEG_COLORS[s], alpha=0.18, lw=0)
    fc = sc["forecaster_input"]
    if "implied_move_pct" in fc:
        ax.axvline(fc["implied_move_pct"], color=TEXT, ls=":", lw=1)
        ax.text(
            fc["implied_move_pct"],
            ax.get_ylim()[1] * 0.9,
            f" forecaster step {fc['target_week']}\n ({fc['model']}, already realized)",
            fontsize=7.5,
            color=MUTED,
        )
    ax.axhline(0, color=MUTED, lw=0.6)
    ax.set_xlabel("WTI move over a week, %")
    ax.set_ylabel("expected segment move, %")
    ax.set_title("Oil sensitivity: what a WTI move has typically meant (not a signal)")
    ax.legend(fontsize=8.5, loc="upper left")
    return _save(
        fig,
        "scenario_fan.png",
        "Bands: 95% from HAC beta standard errors (parameter "
        "uncertainty only). Source: results/scenarios.json",
    )
