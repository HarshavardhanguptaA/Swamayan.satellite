"""SWAYAMYAN: real-data multi-satellite Earth Observation analytics."""

from __future__ import annotations

from datetime import date, timedelta

import ee
import numpy as np
import pandas as pd
import streamlit as st

from analytics.preprocessing import aggregate_feature_timeseries, merge_feature_frames
from analytics.timeseries import extract_timeseries
from config.constants import GEE_PROJECT_ID
from gee.auth import initialize_earth_engine
from gee.datasets import load_gpm, load_sentinel2
from gee.landsat import load_landsat
from gee.modis import load_modis_lst
from gee.sentinel1 import load_sentinel1
from ui.landing import render_landing_page
from ui.styles import get_custom_css
from ui.workspace import (
    render_stepper,
    render_step_1_configure,
    render_step_2_explore,
    render_step_3_cross_sensor,
    render_step_4_fusion,
    render_workspace_header,
)

st.set_page_config(
    page_title="SWAYAMYAN — Multi-Satellite Earth Observation Analytics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply cohesive modern design system (white, near-black, teal, glassmorphism)
st.markdown(get_custom_css(), unsafe_allow_html=True)


DATASET_SCALES = {
    "Sentinel-2": 20,
    "Sentinel-1": 20,
    "MODIS LST": 1000,
    "Landsat 8/9": 30,
    "GPM IMERG": 11132,
}


def parse_aoi_bounds(raw):
    """Parse and validate lon/lat bounds: min_lon, min_lat, max_lon, max_lat."""
    try:
        bounds = tuple(float(part.strip()) for part in raw.split(","))
    except (AttributeError, ValueError) as exc:
        raise ValueError("Enter four numeric values: min_lon, min_lat, max_lon, max_lat.") from exc
    if len(bounds) != 4:
        raise ValueError("Enter exactly four values: min_lon, min_lat, max_lon, max_lat.")
    min_lon, min_lat, max_lon, max_lat = bounds
    if not (-180 <= min_lon < max_lon <= 180):
        raise ValueError("Longitude bounds must satisfy -180 ≤ min_lon < max_lon ≤ 180.")
    if not (-90 <= min_lat < max_lat <= 90):
        raise ValueError("Latitude bounds must satisfy -90 ≤ min_lat < max_lat ≤ 90.")
    if (max_lon - min_lon) * (max_lat - min_lat) > 4:
        raise ValueError("The AOI is too large for an interactive regional analysis. Use a smaller rectangle.")
    return bounds


def _prefixed(frame, rename_map):
    if frame is None or frame.empty:
        return frame
    return frame.rename(columns=rename_map)


@st.cache_data(ttl=3600, max_entries=8, show_spinner="Querying Google Earth Engine datasets…")
def fetch_real_data(project_id, bounds, start_date, end_date_exclusive, datasets, cloud_percent):
    """Fetch actual observations and cache only the resulting serializable tables."""
    initialize_earth_engine(project_id)
    aoi = ee.Geometry.Rectangle(list(bounds))
    frames = []
    counts = {}
    warnings = []

    # Every collection is filtered server-side. No fallback/mock observations exist.
    loaders = {
        "Sentinel-2": lambda: load_sentinel2(aoi, start_date, end_date_exclusive, cloud_percent),
        "Sentinel-1": lambda: load_sentinel1(aoi, start_date, end_date_exclusive),
        "MODIS LST": lambda: load_modis_lst(aoi, start_date, end_date_exclusive),
        "Landsat 8/9": lambda: load_landsat(aoi, start_date, end_date_exclusive),
        "GPM IMERG": lambda: load_gpm(aoi, start_date, end_date_exclusive),
    }
    band_map = {
        "Sentinel-2": (["NDVI", "NDWI", "EVI"], {"NDVI": "S2_NDVI", "NDWI": "S2_NDWI", "EVI": "S2_EVI"}),
        "Sentinel-1": (["VV", "VH"], {"VV": "S1_VV_dB", "VH": "S1_VH_dB"}),
        "MODIS LST": (["LST_Day_C", "LST_Night_C"], {"LST_Day_C": "MODIS_LST_Day_C", "LST_Night_C": "MODIS_LST_Night_C"}),
        "Landsat 8/9": (["NDVI", "NDWI", "EVI", "LST_C"], {"NDVI": "Landsat_NDVI", "NDWI": "Landsat_NDWI", "EVI": "Landsat_EVI", "LST_C": "Landsat_LST_C"}),
        "GPM IMERG": (["GPM_Precip_mm"], {"GPM_Precip_mm": "GPM_Precip_mm"}),
    }

    for dataset in datasets:
        try:
            collection = loaders[dataset]()
            bands, rename_map = band_map[dataset]
            scale = DATASET_SCALES[dataset]
            observations = extract_timeseries(collection, bands, aoi, scale=scale)
            source_count = int(observations.attrs.get("image_count", len(observations)))
            counts[dataset] = {"images": source_count, "valid_dates": int(len(observations))}
            if observations.empty:
                warnings.append(f"{dataset}: the collection had {source_count} images but no valid regional observations for these dates/AOI.")
                continue
            observations = _prefixed(observations, rename_map)
            frames.append(observations)
        except Exception as exc:
            warnings.append(f"{dataset}: {type(exc).__name__}: {exc}")

    if not frames:
        detail = "\n".join(warnings) if warnings else "No data was returned by the selected datasets."
        raise RuntimeError("No real observations could be extracted. Check the dates, AOI, dataset availability and Earth Engine access.\n" + detail)

    merged = merge_feature_frames(frames)
    if merged.empty or len(merged.columns) < 2:
        raise RuntimeError("Earth Engine returned no usable feature table for the chosen query.")
    return merged, counts, warnings


# Navigation State Management
if "view" not in st.session_state:
    st.session_state["view"] = "landing"

if "workspace_step" not in st.session_state:
    st.session_state["workspace_step"] = 1


# Render Views
if st.session_state["view"] == "landing":
    render_landing_page()
else:
    render_workspace_header()
    current_step = st.session_state.get("workspace_step", 1)
    render_stepper(current_step)

    if current_step == 1:
        render_step_1_configure(parse_aoi_bounds, fetch_real_data)
    elif current_step == 2:
        render_step_2_explore()
    elif current_step == 3:
        render_step_3_cross_sensor()
    elif current_step == 4:
        render_step_4_fusion()
