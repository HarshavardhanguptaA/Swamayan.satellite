"""Streamlit sidebar form for querying real Earth Engine datasets."""

from datetime import date, timedelta
import os

import streamlit as st

from config.constants import DEFAULT_AOI_BOUNDS, GEE_PROJECT_ID

DATASETS = ["Sentinel-2", "Sentinel-1", "MODIS LST", "Landsat 8/9", "GPM IMERG"]


def render_query_form():
    today = date.today()
    default_end = today - timedelta(days=10)
    default_start = default_end - timedelta(days=365)
    bounds_text = ", ".join(str(value) for value in DEFAULT_AOI_BOUNDS)
    ee_project_id = (os.getenv("EE_PROJECT_ID", "") or GEE_PROJECT_ID).strip()

    st.sidebar.header("Live data query")
    if not ee_project_id:
        st.sidebar.info("EE_PROJECT_ID environment variable is not configured.")

    with st.sidebar.form("earth_engine_query"):
        bounds_input = st.text_input("AOI bounds (min_lon, min_lat, max_lon, max_lat)", value=bounds_text)
        date_range = st.date_input("Observation date range", value=(default_start, default_end),
                                   min_value=date(2000, 1, 1), max_value=today)
        datasets = st.multiselect("Real datasets", DATASETS,
                                  default=["Sentinel-2", "Sentinel-1", "MODIS LST"])
        cloud_percent = st.slider("Maximum Sentinel-2 scene cloud (%)", 0, 100, 35, 5)
        temporal = st.selectbox("Temporal aggregation", ["Monthly", "Native cadence"], index=0,
                                help="Monthly is recommended for cross-sensor comparisons.")
        submitted = st.form_submit_button("Fetch real observations", type="primary", use_container_width=True)

    return {
        "submitted": submitted,
        "project_id": ee_project_id,
        "bounds_input": bounds_input,
        "date_range": date_range,
        "datasets": datasets,
        "cloud_percent": cloud_percent,
        "temporal": temporal,
    }
