"""Transparent, non-predictive feature-level fusion utilities."""

import numpy as np
import pandas as pd


def build_feature_level_fusion(df, feature_x, feature_y, lag=0):
    """Return a standardized equal-weight composite, optionally lag-aligning Y.

    Lag convention matches ``analytics.lag_analysis``: a positive lag means Y
    follows X. The output timeline is anchored to X; no pixel-level fusion is
    performed and no learned/optimal weights are implied.
    """
    if not {"date", feature_x, feature_y}.issubset(df.columns):
        raise ValueError("The selected features and date must exist in the input data.")
    pair = df[["date", feature_x, feature_y]].copy().sort_values("date")
    pair[feature_y] = pair[feature_y].shift(-int(lag))
    pair = pair.dropna(subset=[feature_x, feature_y]).reset_index(drop=True)
    if len(pair) < 3:
        raise ValueError("At least three lag-aligned observations are required for fusion.")

    x = pd.to_numeric(pair[feature_x], errors="coerce")
    y = pd.to_numeric(pair[feature_y], errors="coerce")
    sx, sy = float(x.std(ddof=0)), float(y.std(ddof=0))
    if not np.isfinite(sx) or not np.isfinite(sy) or sx == 0 or sy == 0:
        raise ValueError("Cannot fuse a feature with zero or invalid variance.")
    pair[f"{feature_x}_z"] = (x - x.mean()) / sx
    pair[f"{feature_y}_z"] = (y - y.mean()) / sy
    pair["Fused_feature_z"] = 0.5 * pair[f"{feature_x}_z"] + 0.5 * pair[f"{feature_y}_z"]
    return pair
