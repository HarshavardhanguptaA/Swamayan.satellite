import numpy as np
import pandas as pd
import pytest

from analytics.fusion import build_feature_level_fusion
from analytics.fusion_readiness import detect_peak_lag
from analytics.lag_analysis import lag_correlation
from analytics.preprocessing import aggregate_feature_timeseries, merge_feature_frames


def test_merge_feature_frames_keeps_missing_observations_missing():
    first = pd.DataFrame({"date": ["2024-01-01", "2024-02-01"], "S2_NDVI": [0.5, 0.6]})
    second = pd.DataFrame({"date": ["2024-02-01", "2024-03-01"], "S1_VV_dB": [-12.0, -11.0]})
    merged = merge_feature_frames([first, second])
    assert list(merged.columns) == ["date", "S2_NDVI", "S1_VV_dB"]
    assert len(merged) == 3
    assert pd.isna(merged.loc[0, "S1_VV_dB"])
    assert merged.loc[1, "S2_NDVI"] == pytest.approx(0.6)


def test_monthly_aggregation_sums_rain_but_averages_features():
    frame = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-02-01", "2024-04-01"]),
        "S2_NDVI": [0.2, 0.4, 0.6, 0.8],
        "GPM_Precip_mm": [2.0, 3.0, 4.0, 6.0],
    })
    monthly = aggregate_feature_timeseries(frame, "Monthly")
    assert len(monthly) == 4
    assert monthly.loc[0, "S2_NDVI"] == pytest.approx(0.3)
    assert monthly.loc[0, "GPM_Precip_mm"] == pytest.approx(5.0)
    assert monthly.loc[2, "date"] == pd.Timestamp("2024-03-01")
    assert pd.isna(monthly.loc[2, "S2_NDVI"])


def test_lag_sign_positive_when_y_follows_x():
    rng = np.random.default_rng(21)
    x = rng.normal(size=120)
    y = np.empty_like(x)
    y[:3] = rng.normal(size=3)
    y[3:] = x[:-3]
    correlations = lag_correlation(x, y, max_lag=5)
    best_lag, best_corr = detect_peak_lag(correlations)
    assert best_lag == 3
    assert best_corr > 0.95


def test_lag_analysis_handles_constant_series():
    result = lag_correlation(np.ones(12), np.arange(12), max_lag=2)
    assert all(np.isnan(value) for value in result.values())


def test_fusion_is_standardized_and_lag_aligned():
    dates = pd.date_range("2024-01-01", periods=20, freq="MS")
    x = np.arange(20, dtype=float)
    y = np.concatenate(([np.nan], x[:-1]))
    df = pd.DataFrame({"date": dates, "x": x, "y": y})
    fused = build_feature_level_fusion(df, "x", "y", lag=1)
    assert len(fused) == 19
    assert "Fused_feature_z" in fused.columns
    assert fused["Fused_feature_z"].mean() == pytest.approx(0.0, abs=1e-10)


def test_fusion_rejects_constant_features():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=5), "x": [1] * 5, "y": [2, 3, 4, 5, 6]})
    with pytest.raises(ValueError, match="zero or invalid variance"):
        build_feature_level_fusion(df, "x", "y")


def test_lag_correlation_preserves_calendar_month_semantics_with_gaps():
    """Missing calendar months (NaN) must not distort integer lag semantics."""
    rng = np.random.default_rng(42)
    n = 36
    x = rng.standard_normal(n)
    # y follows x by exactly 3 calendar months
    y = np.full(n, np.nan)
    y[3:] = x[:-3] + rng.standard_normal(n - 3) * 0.05
    # Insert missing months in y (e.g. cloud gaps)
    for missing_idx in [5, 11, 17, 23, 29]:
        y[missing_idx] = np.nan

    correlations = lag_correlation(x, y, max_lag=6)
    peak_lag, peak_corr = detect_peak_lag(correlations)

    assert peak_lag == 3
    assert peak_corr > 0.90


def test_lag_sign_negative_when_y_leads_x():
    """Negative lag means Y is observed earlier than X (Y leads X)."""
    rng = np.random.default_rng(84)
    n = 48
    y = rng.standard_normal(n)
    # x follows y by 2 months, which means y leads x by 2 months (lag = -2)
    x = np.full(n, np.nan)
    x[2:] = y[:-2] + rng.standard_normal(n - 2) * 0.02

    correlations = lag_correlation(x, y, max_lag=5)
    peak_lag, peak_corr = detect_peak_lag(correlations)

    assert peak_lag == -2
    assert peak_corr > 0.95


def test_detect_peak_lag_prefers_lag_closest_to_zero_on_ties():
    """When absolute correlations are tied, detect_peak_lag must prefer the lag closest to zero."""
    # Case 1: Monotone ramp where all lag windows have correlation 1.0
    ramp = np.arange(16, dtype=float)
    correlations = lag_correlation(ramp, ramp, max_lag=4)
    peak_lag, peak_corr = detect_peak_lag(correlations)
    assert peak_lag == 0
    assert peak_corr == pytest.approx(1.0)

    # Case 2: Explicit dictionary tie between lag 0 and lag 3
    tied_dict = {-3: 0.5, 0: 0.85, 1: 0.6, 3: 0.85}
    peak_lag, peak_corr = detect_peak_lag(tied_dict)
    assert peak_lag == 0
    assert peak_corr == 0.85

    # Case 3: Explicit dictionary tie between lag -1 and lag 2
    tied_dict_2 = {-2: 0.7, -1: 0.88, 0: 0.5, 2: 0.88}
    peak_lag, peak_corr = detect_peak_lag(tied_dict_2)
    assert peak_lag == -1  # abs(-1) < abs(2), so -1 is closer to zero than 2


def test_fusion_alignment_with_missing_monthly_observations():
    """Feature-level fusion aligns by calendar months even when series has NaN gaps."""
    dates = pd.date_range("2023-01-01", periods=24, freq="MS")
    rng = np.random.default_rng(123)
    x = rng.standard_normal(24)
    y = np.full(24, np.nan)
    # y follows x by 2 months
    y[2:] = x[:-2] * 1.5 + 0.5
    # Add gaps in x and y
    x[7] = np.nan
    y[14] = np.nan

    df = pd.DataFrame({"date": dates, "driver": x, "response": y})
    fused = build_feature_level_fusion(df, "driver", "response", lag=2)

    assert "Fused_feature_z" in fused.columns
    assert "driver_z" in fused.columns
    assert "response_z" in fused.columns
    # Check that driver_z and response_z are normalized to zero mean and unit variance
    assert fused["driver_z"].mean() == pytest.approx(0.0, abs=1e-7)
    assert fused["driver_z"].std(ddof=0) == pytest.approx(1.0, abs=1e-7)
    assert fused["response_z"].mean() == pytest.approx(0.0, abs=1e-7)
    assert fused["response_z"].std(ddof=0) == pytest.approx(1.0, abs=1e-7)
    assert fused["Fused_feature_z"].mean() == pytest.approx(0.0, abs=1e-7)
    # Since y was constructed from x[:-2], after lag=2 alignment they should be strongly correlated
    aligned_corr = np.corrcoef(fused["driver_z"], fused["response_z"])[0, 1]
    assert aligned_corr > 0.99
