"""Snapshot management for public hosted mode using genuine Earth Engine satellite datasets."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from analytics.preprocessing import aggregate_feature_timeseries
from gee.auth import get_configured_project_id, is_cloud_run

DEFAULT_SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "data" / "snapshots"


def list_available_snapshots(snapshots_dir: Path | str | None = None) -> list[dict[str, Any]]:
    """Discover all exported observation snapshots in the snapshots directory."""
    dir_path = Path(snapshots_dir) if snapshots_dir else DEFAULT_SNAPSHOTS_DIR
    if not dir_path.exists():
        return []

    snapshots = []
    for meta_file in sorted(dir_path.glob("*.meta.json")):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            csv_file = meta_file.with_name(f"{meta.get('id', meta_file.stem.replace('.meta', ''))}.csv")
            if csv_file.exists():
                meta["csv_path"] = str(csv_file)
                meta["meta_path"] = str(meta_file)
                snapshots.append(meta)
        except Exception:
            continue
    return snapshots


def load_snapshot(
    snapshot_id_or_path: str,
    snapshots_dir: Path | str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load genuine satellite observations and metadata for a given snapshot.

    Preserves missing observations as NaN; never generates synthetic values.
    """
    dir_path = Path(snapshots_dir) if snapshots_dir else DEFAULT_SNAPSHOTS_DIR

    # Resolve CSV and meta files
    if Path(snapshot_id_or_path).suffix == ".csv":
        csv_file = Path(snapshot_id_or_path)
        meta_file = csv_file.with_name(f"{csv_file.stem}.meta.json")
    else:
        csv_file = dir_path / f"{snapshot_id_or_path}.csv"
        meta_file = dir_path / f"{snapshot_id_or_path}.meta.json"

    if not csv_file.exists():
        raise FileNotFoundError(f"Snapshot CSV file not found: {csv_file}")

    # Load observation dataframe
    df = pd.read_csv(csv_file)
    if "date" not in df.columns:
        raise ValueError(f"Snapshot CSV {csv_file.name} is missing required 'date' column.")

    df["date"] = df["date"].astype(str)

    # Ensure numeric columns remain float with NaNs preserved
    for col in df.columns:
        if col != "date":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Load metadata if present
    metadata: dict[str, Any] = {}
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = {
            "id": csv_file.stem,
            "name": csv_file.stem.replace("_", " ").title(),
            "columns": df.columns.tolist(),
            "total_days": len(df),
            "processing_details": "Genuine observation snapshot without metadata file.",
        }

    metadata["csv_path"] = str(csv_file)
    return df, metadata


def is_live_gee_configured() -> bool:
    """Check if Google Earth Engine credentials or environment variables are configured."""
    # 1. Cloud Run environment
    if is_cloud_run():
        return True

    # 2. Check if project ID is configured
    project_id = get_configured_project_id()
    if not project_id:
        return False

    # 3. Check for service account or local token file
    try:
        from gee.auth import _get_service_account_info
        if _get_service_account_info() is not None:
            return True
    except Exception:
        pass

    # 4. Check for local user Earth Engine credentials
    home = Path.home()
    ee_creds_legacy = home / ".config" / "earthengine" / "credentials"
    ee_creds_windows = Path(os.getenv("USERPROFILE", str(home))) / ".config" / "earthengine" / "credentials"
    if ee_creds_legacy.exists() or ee_creds_windows.exists():
        return True

    return False
