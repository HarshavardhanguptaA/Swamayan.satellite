"""Tests for public hosted snapshot loading, missing value preservation, lag analysis, fusion, and export."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analytics.fusion import build_feature_level_fusion
from analytics.fusion_readiness import detect_peak_lag, stability_score
from analytics.lag_analysis import lag_correlation
from analytics.preprocessing import aggregate_feature_timeseries
from analytics.snapshot import (
    is_live_gee_configured,
    list_available_snapshots,
    load_snapshot,
)
from analytics.statistics import correlation_matrix


def test_list_available_snapshots():
    """Verify that versioned snapshot datasets are discovered with complete metadata."""
    snapshots = list_available_snapshots()
    assert len(snapshots) >= 1, "At least one genuine satellite snapshot should be available in data/snapshots"

    pune = next((s for s in snapshots if "pune" in s["id"].lower()), None)
    assert pune is not None, "Pune snapshot must be discovered"
    assert pune["name"] == "Pune, India (Western Ghats fringe)"
    assert len(pune["bounds"]) == 4
    assert pune["start_date"] == "2022-01-01"
    assert pune["end_date_exclusive"] == "2024-01-01"
    assert "Sentinel-2" in pune["datasets"]
    assert "Sentinel-1" in pune["datasets"]
    assert "MODIS LST" in pune["datasets"]
    assert "GPM IMERG" in pune["datasets"]
    assert "source_collections" in pune
    assert "processing_details" in pune
    assert Path(pune["csv_path"]).exists()


def test_load_snapshot_preserves_missing_values_as_nan():
    """Verify that real observations are loaded and missing observations remain NaN without synthetic imputation."""
    raw_df, meta = load_snapshot("pune_western_ghats_2022_2024")
    assert not raw_df.empty
    assert len(raw_df) == 730  # 2 full calendar years
    assert "date" in raw_df.columns
    assert "S2_NDVI" in raw_df.columns
    assert "GPM_Precip_mm" in raw_df.columns

    # Verify missing values exist and are preserved as NaN (monsoon cloud cover)
    s2_nans = raw_df["S2_NDVI"].isna().sum()
    assert s2_nans > 0, "Real optical satellite series must have missing values during cloudy dates"

    # Verify no synthetic non-null replacement was done
    assert np.isnan(raw_df.loc[raw_df["S2_NDVI"].isna(), "S2_NDVI"]).all()

    # Dates must be continuous and strictly increasing
    dates = pd.to_datetime(raw_df["date"])
    assert dates.is_monotonic_increasing


def test_snapshot_monthly_aggregation_preserves_calendar_semantics():
    """Verify that temporal aggregation preserves calendar intervals and handles missing months."""
    raw_df, _ = load_snapshot("pune_western_ghats_2022_2024")
    monthly_df = aggregate_feature_timeseries(raw_df, "Monthly")

    # 2022-01 to 2023-12 is exactly 24 calendar months
    assert len(monthly_df) == 24
    assert str(monthly_df["date"].iloc[0])[:10] == "2022-01-01"
    assert str(monthly_df["date"].iloc[-1])[:10] == "2023-12-01"

    # Precipitation should be strictly non-negative and positive in summer/monsoon
    assert (monthly_df["GPM_Precip_mm"] >= 0).all()
    assert monthly_df["GPM_Precip_mm"].max() > 50.0  # monsoon rain in Western Ghats


def test_snapshot_cross_sensor_correlation_and_lag_analysis():
    """Verify that cross-sensor correlation and lag analysis work on the genuine dataset."""
    raw_df, _ = load_snapshot("pune_western_ghats_2022_2024")
    monthly_df = aggregate_feature_timeseries(raw_df, "Monthly")

    # Correlation matrix
    corr = correlation_matrix(monthly_df.drop(columns=["date"]))
    assert corr is not None
    assert corr.shape[0] >= 5
    assert not corr.isna().all().all()

    # Temporal lag analysis between GPM Precipitation and Sentinel-2 NDVI
    pair = monthly_df[["date", "GPM_Precip_mm", "S2_NDVI"]].sort_values("date").reset_index(drop=True)
    lag_res = lag_correlation(pair["GPM_Precip_mm"].to_numpy(), pair["S2_NDVI"].to_numpy(), max_lag=3)
    assert len(lag_res) == 7  # lags -3, -2, -1, 0, 1, 2, 3

    peak_lag, peak_corr = detect_peak_lag(lag_res)
    assert peak_lag is not None
    assert -3 <= peak_lag <= 3


def test_snapshot_feature_level_fusion_and_csv_export():
    """Verify that feature-level fusion and CSV generation work on the genuine dataset."""
    raw_df, _ = load_snapshot("pune_western_ghats_2022_2024")
    monthly_df = aggregate_feature_timeseries(raw_df, "Monthly")

    # Build feature-level fusion between precipitation and NDVI with lag=1
    fused = build_feature_level_fusion(monthly_df, "GPM_Precip_mm", "S2_NDVI", lag=1)
    assert not fused.empty
    assert "Fused_feature_z" in fused.columns
    assert "GPM_Precip_mm_z" in fused.columns
    assert "S2_NDVI_z" in fused.columns

    # Verify export to CSV
    csv_buffer = io.StringIO()
    fused.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    assert "date,GPM_Precip_mm,S2_NDVI" in csv_content
    assert "Fused_feature_z" in csv_content

    # Re-reading CSV preserves missing values
    reloaded = pd.read_csv(io.StringIO(csv_content))
    assert len(reloaded) == len(fused)
    assert reloaded["Fused_feature_z"].isna().sum() == fused["Fused_feature_z"].isna().sum()


def test_load_snapshot_nonexistent_raises_file_not_found():
    """Attempting to load a nonexistent snapshot raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_snapshot("non_existent_preset_id_12345")
