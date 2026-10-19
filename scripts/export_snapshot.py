"""Script to extract genuine multi-satellite observations from Google Earth Engine and export to versioned snapshot CSV + metadata."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics.preprocessing import merge_feature_frames
from app import DATASET_SCALES, _prefixed
from config.constants import GEE_PROJECT_ID
from gee.auth import get_configured_project_id, initialize_earth_engine
from gee.datasets import load_gpm, load_sentinel2
from gee.landsat import load_landsat
from gee.modis import load_modis_lst
from gee.sentinel1 import load_sentinel1
from analytics.timeseries import extract_timeseries
import ee


PRESETS = {
    "pune": {
        "id": "pune_western_ghats_2022_2024",
        "name": "Pune, India (Western Ghats fringe)",
        "bounds": [73.75, 18.42, 73.98, 18.62],
        "default_start": "2022-01-01",
        "default_end_exclusive": "2024-01-01",
    },
    "bengaluru": {
        "id": "bengaluru_urban_lakes_2022_2024",
        "name": "Bengaluru, India (Urban & Lakes)",
        "bounds": [77.50, 12.85, 77.72, 13.05],
        "default_start": "2022-01-01",
        "default_end_exclusive": "2024-01-01",
    },
}

SOURCE_COLLECTIONS = {
    "Sentinel-2": "COPERNICUS/S2_SR_HARMONIZED",
    "Sentinel-1": "COPERNICUS/S1_GRD",
    "MODIS LST": "MODIS/061/MOD11A2",
    "Landsat 8/9": "LANDSAT/LC08/C02/T1_L2 + LANDSAT/LC09/C02/T1_L2",
    "GPM IMERG": "NASA/GPM_L3/IMERG_V07",
}


def export_snapshot(
    preset_key: str = "pune",
    start_date: str | None = None,
    end_date_exclusive: str | None = None,
    output_dir: str = "data/snapshots",
    cloud_percent: int = 35,
    s1_orbit_pass: str = "DESCENDING",
):
    """Fetch genuine Earth Engine observations and write versioned CSV + JSON metadata."""
    preset = PRESETS.get(preset_key.lower())
    if not preset:
        raise ValueError(f"Unknown preset '{preset_key}'. Choose from: {list(PRESETS.keys())}")

    start = start_date or preset["default_start"]
    end_ex = end_date_exclusive or preset["default_end_exclusive"]
    bounds = preset["bounds"]
    snapshot_id = preset["id"]

    print(f"Initializing Earth Engine for snapshot '{preset['name']}'...")
    project_id = get_configured_project_id()
    initialize_earth_engine(project_id)

    aoi = ee.Geometry.Rectangle(bounds)
    datasets = ("Sentinel-2", "Sentinel-1", "MODIS LST", "Landsat 8/9", "GPM IMERG")

    loaders = {
        "Sentinel-2": lambda: load_sentinel2(aoi, start, end_ex, cloud_percent),
        "Sentinel-1": lambda: load_sentinel1(aoi, start, end_ex, orbit_pass=s1_orbit_pass),
        "MODIS LST": lambda: load_modis_lst(aoi, start, end_ex),
        "Landsat 8/9": lambda: load_landsat(aoi, start, end_ex),
        "GPM IMERG": lambda: load_gpm(aoi, start, end_ex),
    }
    band_map = {
        "Sentinel-2": (["NDVI", "NDWI", "EVI"], {"NDVI": "S2_NDVI", "NDWI": "S2_NDWI", "EVI": "S2_EVI"}),
        "Sentinel-1": (["VV", "VH"], {"VV": "S1_VV_dB", "VH": "S1_VH_dB"}),
        "MODIS LST": (["LST_Day_C", "LST_Night_C"], {"LST_Day_C": "MODIS_LST_Day_C", "LST_Night_C": "MODIS_LST_Night_C"}),
        "Landsat 8/9": (["NDVI", "NDWI", "EVI", "LST_C"], {"NDVI": "Landsat_NDVI", "NDWI": "Landsat_NDWI", "EVI": "Landsat_EVI", "LST_C": "Landsat_LST_C"}),
        "GPM IMERG": (["GPM_Precip_mm"], {"GPM_Precip_mm": "GPM_Precip_mm"}),
    }

    frames = []
    counts = {}
    warnings = []

    print(f"Extracting observations from {len(datasets)} sensors across [{start} to {end_ex}]...")
    for ds_name in datasets:
        print(f" -> Querying {ds_name}...")
        try:
            coll = loaders[ds_name]()
            bands, rename_map = band_map[ds_name]
            scale = DATASET_SCALES[ds_name]
            obs = extract_timeseries(coll, bands, aoi, scale=scale)
            source_count = int(obs.attrs.get("image_count", len(obs)))
            counts[ds_name] = {"images": source_count, "valid_dates": int(len(obs))}
            print(f"    Found {source_count} scenes, {len(obs)} valid dates.")
            if obs.empty:
                warnings.append(f"{ds_name} returned no valid observations.")
                continue
            obs = _prefixed(obs, rename_map)
            frames.append(obs)
        except Exception as exc:
            print(f"    Error querying {ds_name}: {exc}")
            warnings.append(f"{ds_name}: {exc}")

    if not frames:
        raise RuntimeError("Failed to extract any observations from Earth Engine.")

    print("Merging feature frames...")
    merged = merge_feature_frames(frames)
    print(f"Merged table shape: {merged.shape} ({len(merged)} days, {len(merged.columns) - 1} features)")

    # Save to directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    csv_file = out_path / f"{snapshot_id}.csv"
    meta_file = out_path / f"{snapshot_id}.meta.json"

    merged.to_csv(csv_file, index=False)
    print(f"Saved CSV: {csv_file} ({csv_file.stat().st_size} bytes)")

    extraction_time = datetime.now(timezone.utc).isoformat()

    metadata = {
        "id": snapshot_id,
        "name": preset["name"],
        "bounds": bounds,
        "start_date": start,
        "end_date_exclusive": end_ex,
        "extraction_timestamp_utc": extraction_time,
        "datasets": list(datasets),
        "dataset_counts": counts,
        "cloud_percent": cloud_percent,
        "s1_orbit_pass": s1_orbit_pass,
        "source_collections": SOURCE_COLLECTIONS,
        "dataset_scales_m": DATASET_SCALES,
        "columns": merged.columns.tolist(),
        "total_days": len(merged),
        "warnings": warnings,
        "processing_details": (
            "Genuine multi-satellite observations extracted directly from Google Earth Engine. "
            "Observations are merged on UTC calendar dates. Missing observations resulting from "
            "cloud occlusion, sensor orbit repeat intervals, or QA screening are preserved as NaN "
            "without synthetic interpolation or imputation."
        ),
        "version": "1.0.0",
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved Metadata: {meta_file}")
    return csv_file, meta_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export genuine Earth Engine observations to snapshot CSV.")
    parser.add_argument("--preset", default="pune", help="Preset key (pune, bengaluru)")
    parser.add_argument("--start", default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="End date exclusive (YYYY-MM-DD)")
    parser.add_argument("--outdir", default="data/snapshots", help="Output directory")
    args = parser.parse_args()

    export_snapshot(
        preset_key=args.preset,
        start_date=args.start,
        end_date_exclusive=args.end,
        output_dir=args.outdir,
    )
