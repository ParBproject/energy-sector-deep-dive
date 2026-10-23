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
