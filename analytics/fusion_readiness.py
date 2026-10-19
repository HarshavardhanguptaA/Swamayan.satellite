"""Statistical readiness diagnostics for feature-level fusion."""

import numpy as np


def detect_peak_lag(lag_dict):
    valid = [(lag, corr) for lag, corr in (lag_dict or {}).items()
             if corr is not None and np.isfinite(corr)]
    if not valid:
        return None, None
    return max(valid, key=lambda item: (abs(item[1]), -abs(item[0])))


def stability_score(x, y):
    """Coefficient of variation of rolling correlations (lower is steadier)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = min(len(x), len(y))
    x, y = x[:n], y[:n]
    if n < 6:
        return None
    window = max(3, n // 4)
    rolling = []
    for start in range(0, n - window + 1):
        xa, ya = x[start:start + window], y[start:start + window]
        valid = np.isfinite(xa) & np.isfinite(ya)
        xa, ya = xa[valid], ya[valid]
        if len(xa) >= 3 and np.std(xa) > 0 and np.std(ya) > 0:
            value = float(np.corrcoef(xa, ya)[0, 1])
            if np.isfinite(value):
                rolling.append(value)
    if len(rolling) < 2:
        return None
    rolling = np.asarray(rolling)
    return float(np.std(rolling) / (np.mean(np.abs(rolling)) + 1e-8))


def fusion_decision(corr, lag, stability):
    if corr is None or lag is None or not np.isfinite(corr):
        return "Insufficient valid observations to assess fusion readiness."
    if stability is None:
        return "A lagged relationship was measured, but there are too few observations to assess stability."
    if abs(corr) < 0.3:
        return "The strongest lagged relationship is weak; fusion is not recommended without additional evidence."
    if stability > 0.8:
        return "The relationship varies across the series; treat fusion results as exploratory."
    if lag == 0:
        return "A comparatively stable synchronous relationship was detected. A standardized feature-level composite is reasonable to test."
    return (f"A comparatively stable relationship was detected at lag {lag}. "
            "A lag-aligned feature-level composite can be explored; it is not a validated prediction model.")
