"""Lagged Pearson correlation with an explicit lead/lag sign convention."""

import numpy as np


def lag_correlation(x, y, max_lag=8):
    """Correlate X(t) with Y(t + lag) over integer offsets.

    Positive lag means Y follows X by that many samples. Negative lag means
    Y is observed earlier than X. Inputs are assumed to be temporally aligned
    at a regular cadence (for cross-sensor work, monthly aggregation is safer).
    """
    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    n = min(len(x), len(y))
    x, y = x[:n], y[:n]
    if max_lag < 0:
        raise ValueError("max_lag must be non-negative")

    results = {}
    for lag in range(-int(max_lag), int(max_lag) + 1):
        if lag > 0:
            x_lag, y_lag = x[:-lag], y[lag:]
        elif lag < 0:
            x_lag, y_lag = x[-lag:], y[:lag]
        else:
            x_lag, y_lag = x, y

        valid = np.isfinite(x_lag) & np.isfinite(y_lag)
        x_valid, y_valid = x_lag[valid], y_lag[valid]
        if len(x_valid) < 3 or np.std(x_valid) == 0 or np.std(y_valid) == 0:
            results[lag] = np.nan
        else:
            results[lag] = float(np.corrcoef(x_valid, y_valid)[0, 1])
    return results
