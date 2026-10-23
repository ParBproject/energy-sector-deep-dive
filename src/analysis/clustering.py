"""Cluster companies on oil beta + point-in-time fundamentals; compare with the 5 segments."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score

from src.analysis import fundamentals, returns

FEATURES = [
    "oil_beta",
    "capex_intensity",
    "reinvestment_rate",
    "fcf_yield",
    "debt_to_capital",
    "payout_ratio",
]
K_RANGE = range(2, 7)
SEED = 0


def feature_matrix() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.DataFrame]:
    """Raw features, imputed-and-standardized features, and segment labels.

    Missing values are imputed with the UNIVERSE median (not the segment median, which
    would leak the label we later try to recover), and every imputed cell is flagged.
    """
    m = fundamentals.company_metrics()
    b = returns.betas()["companies"]
    raw = m[FEATURES[1:]].astype(float)
    raw.insert(0, "oil_beta", pd.Series({t: v["beta"] for t, v in b.items()}))
    imputed_mask = raw.isna()
    filled = raw.fillna(raw.median())
    z = (filled - filled.mean()) / filled.std(ddof=0)
    return raw, z, m["segment"], imputed_mask


def _kmeans(z: pd.DataFrame, k: int) -> np.ndarray:
    return KMeans(n_clusters=k, n_init=50, random_state=SEED).fit_predict(z.values)


def _ward(z: pd.DataFrame, k: int) -> np.ndarray:
    return fcluster(linkage(z.values, method="ward"), t=k, criterion="maxclust") - 1


def compute() -> dict:
    raw, z, seg, imputed = feature_matrix()
    out = {"features": FEATURES, "n_companies": len(z)}
    sil = {
        name: {k: silhouette_score(z.values, fn(z, k)) for k in K_RANGE}
        for name, fn in (("kmeans", _kmeans), ("ward", _ward))
    }
    labels5 = {"kmeans": _kmeans(z, 5), "ward": _ward(z, 5)}
    out["silhouette_by_k"] = sil
    out["best_k"] = {n: max(s, key=s.get) for n, s in sil.items()}
    out["k5"] = {
        n: {
            "silhouette": sil[n][5],
            "adjusted_rand_vs_segments": adjusted_rand_score(seg.values, lab),
            "assignments": dict(zip(z.index, map(int, lab), strict=True)),
        }
        for n, lab in labels5.items()
    }
    # segment labels used as a "clustering" for reference: how separable are segments?
    codes = pd.factorize(seg)[0]
    out["silhouette_of_true_segments"] = silhouette_score(z.values, codes)
    out["imputed_cells"] = {
        f: sorted(imputed.index[imputed[f]]) for f in FEATURES if imputed[f].any()
    }
    out["n_imputed_cells"] = int(imputed.values.sum())
    complete = ~imputed.any(axis=1)
    zc = raw[complete]
    zc = (zc - zc.mean()) / zc.std(ddof=0)
    out["complete_case"] = {
        "n_companies": int(complete.sum()),
        "dropped": sorted(raw.index[~complete]),
        "kmeans_k5_adjusted_rand": adjusted_rand_score(seg[complete].values, _kmeans(zc, 5)),
    }
    out["imputation"] = "universe median per feature, flagged; then z-scored"
    pca = PCA(n_components=2, random_state=SEED).fit(z.values)
    xy = pca.transform(z.values)
    out["pca"] = {
        "explained_variance_ratio": list(pca.explained_variance_ratio_),
        "coords": {t: list(xy[i]) for i, t in enumerate(z.index)},
        "segment": seg.to_dict(),
    }
    return out
