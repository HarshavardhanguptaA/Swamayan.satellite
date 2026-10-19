"""Statistical summaries used by the SWAYAMYAN dashboard."""

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


def correlation_metrics(x, y):
    pair = pd.DataFrame({"x": x, "y": y}).apply(pd.to_numeric, errors="coerce").dropna()
    if len(pair) < 3 or pair["x"].nunique() < 2 or pair["y"].nunique() < 2:
        return {"pearson_r": np.nan, "pearson_p": np.nan, "spearman_r": np.nan, "spearman_p": np.nan}
    pearson_r, pearson_p = pearsonr(pair["x"], pair["y"])
    spearman_r, spearman_p = spearmanr(pair["x"], pair["y"])
    return {"pearson_r": float(pearson_r), "pearson_p": float(pearson_p),
            "spearman_r": float(spearman_r), "spearman_p": float(spearman_p)}


def compute_dtr(df):
    frame = df.copy()
    if {"LST_Day_C", "LST_Night_C"}.issubset(frame.columns):
        frame["DTR_C"] = frame["LST_Day_C"] - frame["LST_Night_C"]
    elif {"LST_Day", "LST_Night"}.issubset(frame.columns):
        frame["DTR"] = frame["LST_Day"] - frame["LST_Night"]
    return frame


def feature_stability(series):
    values = pd.to_numeric(pd.Series(series), errors="coerce").dropna()
    if values.empty:
        return {"mean": np.nan, "std": np.nan, "cv": np.nan}
    mean = float(values.mean())
    std = float(values.std())
    cv = float(std / abs(mean)) if mean != 0 else np.nan
    return {"mean": mean, "std": std, "cv": cv}


def correlation_matrix(df, method="pearson"):
    """Pairwise-complete correlation matrix for numeric feature columns."""
    numeric = df.select_dtypes(include=["number"]).copy()
    numeric = numeric.loc[:, numeric.nunique(dropna=True) > 1]
    return numeric.corr(method=method, min_periods=3)
