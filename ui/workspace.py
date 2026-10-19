"""SWAYAMYAN Analytical Workspace with four-step guided workflow."""

from __future__ import annotations

from datetime import date, timedelta
import os
import ee
import numpy as np
import pandas as pd
import streamlit as st


from analytics.fusion import build_feature_level_fusion
from analytics.fusion_readiness import detect_peak_lag, fusion_decision, stability_score
from analytics.lag_analysis import lag_correlation
from analytics.preprocessing import aggregate_feature_timeseries
from analytics.statistics import correlation_matrix
from config.constants import DEFAULT_AOI_BOUNDS, GEE_PROJECT_ID
from gee.auth import get_configured_project_id, initialize_earth_engine
from gee.datasets import load_sentinel2
from ui.charts import (
    correlation_heatmap,
    fusion_composite_chart,
    lag_correlation_plot,
    render_plotly_figure,
    timeseries_chart,
)
from ui.maps import render_aoi_preview, render_sentinel2_preview

DATASETS = ["Sentinel-2", "Sentinel-1", "MODIS LST", "Landsat 8/9", "GPM IMERG"]

# Palette constants (single source of truth — mirrors :root in styles.py)
_TEAL = "#0B6E6E"
_TEAL_DARK = "#095858"
_AQUA = "#5CC8C0"
_TEXT_MAIN = "#0A1F2C"
_TEXT_MUTED = "#52677A"
_TEXT_SUBTLE = "#7A8DA0"
_BORDER = "#DCE6E8"
_BG_ALT = "#F4F8F8"

PRESETS = {
    "Pune, India (Western Ghats fringe)": (73.75, 18.42, 73.98, 18.62),
    "Bengaluru, India (Urban & Lakes)": (77.50, 12.85, 77.72, 13.05),
    "New Delhi, India (Northern Plains)": (77.05, 28.50, 77.30, 28.75),
    "Central Amazon, Brazil (Rainforest)": (-60.10, -3.15, -59.85, -2.95),
    "Custom Bounding Box": None,
}


def feature_columns(df):
    if df is None or df.empty:
        return []
    return [col for col in df.columns if col != "date" and pd.to_numeric(df[col], errors="coerce").nunique(dropna=True) > 1]


def render_stepper(current_step):
    """Render a clickable 4-step progress stepper indicator."""
    steps = [
        (1, "Configure study"),
        (2, "Explore observations"),
        (3, "Cross-sensor analysis"),
        (4, "Feature-level fusion"),
    ]

    html_parts = ['<div class="sw-stepper-container">']
    for idx, name in steps:
        active_cls = "active" if current_step == idx else ("completed" if current_step > idx else "")
        check_icon = "✓" if current_step > idx else str(idx)
        html_parts.append(f'<div class="sw-step-item {active_cls}"><div class="sw-step-badge">{check_icon}</div><span>{name}</span></div>')
        if idx < 4:
            divider_cls = "active" if current_step > idx else ""
            html_parts.append(f'<div class="sw-step-divider {divider_cls}"></div>')
    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_workspace_header():
    """Top bar in workspace with branding and return-to-landing trigger."""
    top_c1, top_c2 = st.columns([8, 2])
    with top_c1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 14px;">
          <div style="width: 22px; height: 22px; border: 1.5px solid {_TEAL}; position: relative; display: flex; align-items: center; justify-content: center; border-radius: 0px !important;">
            <div style="width: 6px; height: 6px; background: {_TEAL}; border-radius: 0px !important;"></div>
            <div style="position: absolute; width: 28px; height: 14px; border: 1.5px solid rgba(11, 110, 110, 0.35); transform: rotate(-30deg); border-radius: 0px !important;"></div>
          </div>
          <span style="font-family: 'DM Serif Display', Georgia, serif; font-weight: 400; font-size: 1.25rem; color: {_TEXT_MAIN}; letter-spacing: 0.04em;">SWAYAMYAN</span>
          <span style="color: {_TEXT_SUBTLE}; font-size: 0.95rem;">/</span>
          <span style="color: {_TEXT_MUTED}; font-size: 0.95rem; font-weight: 500; font-family: 'Inter', sans-serif;">Analytical Workspace</span>
        </div>
        """, unsafe_allow_html=True)
    with top_c2:
        if st.button("← Landing page", key="ws_back_landing", use_container_width=True):
            st.session_state["view"] = "landing"
            st.rerun()


def render_step_1_configure(parse_aoi_bounds, fetch_real_data):
    """Step 1: Configure study area, sensors, temporal resolution and fetch data."""
    st.markdown('<span class="sw-section-tag">Step 01</span>', unsafe_allow_html=True)
    st.markdown(f"""
    <h2 style="font-size: 2.2rem; font-weight: 600; color: {_TEXT_MAIN}; margin-bottom: 8px;">
      Configure study parameters
    </h2>
    <p style="color: {_TEXT_MUTED}; font-size: 1.02rem; margin-bottom: 28px;">
      Define your Area of Interest (AOI), date window, and satellite sensor families to query live Google Earth Engine datasets.
    </p>
    """, unsafe_allow_html=True)

    today = date.today()
    default_end = today - timedelta(days=10)
    default_start = default_end - timedelta(days=365)

    col_form, col_map = st.columns([1.1, 1], gap="large")

    with col_form:
        # Preset selection
        selected_preset = st.selectbox(
            "Study area preset",
            list(PRESETS.keys()),
            index=0,
            key="preset_selection"
        )
        preset_coords = PRESETS[selected_preset]
        if preset_coords is not None:
            initial_bounds_str = f"{preset_coords[0]}, {preset_coords[1]}, {preset_coords[2]}, {preset_coords[3]}"
        else:
            initial_bounds_str = ", ".join(str(val) for val in DEFAULT_AOI_BOUNDS)

        bounds_input = st.text_input(
            "AOI bounds (min_lon, min_lat, max_lon, max_lat)",
            value=initial_bounds_str,
            help="Four comma-separated WGS84 coordinates defining the bounding box."
        )

        date_range = st.date_input(
            "Observation date range",
            value=(default_start, default_end),
            min_value=date(2000, 1, 1),
            max_value=today,
            help="Select start and end dates. 1 to 3 years recommended for optimal response."
        )

        datasets_selected = st.multiselect(
            "Satellite sensor collections",
            DATASETS,
            default=["Sentinel-2", "Sentinel-1", "MODIS LST"],
            help="Choose multi-satellite data sources to ingest."
        )

        c1, c2 = st.columns(2)
        with c1:
            cloud_thresh = st.slider(
                "Max Sentinel-2 scene cloud (%)",
                0, 100, 35, 5,
                help="Filters optical imagery by scene cloud coverage."
            )
        with c2:
            temporal_agg = st.selectbox(
                "Temporal aggregation",
                ["Monthly", "Native cadence"],
                index=0,
                help="Monthly regularizes satellite passes and averages continuous features while summing precipitation."
            )

        s1_pass_label = st.selectbox(
            "Sentinel-1 orbit pass",
            ["Descending (morning, recommended)", "Ascending (evening)", "Both (mixed geometry)"],
            index=0,
            help="Descending pass provides consistent morning acquisitions. Ascending is evening. Both mixes observation geometries with automatic fallback if scenes are absent."
        )
        s1_orbit_pass = "DESCENDING" if "Descending" in s1_pass_label else ("ASCENDING" if "Ascending" in s1_pass_label else "BOTH")

        ee_project_id = get_configured_project_id()
        if not ee_project_id:
            st.info(
                "ℹ️ **Earth Engine Configuration**: Project ID is not configured. "
                "Set `EE_PROJECT_ID` in your system environment or in Streamlit Secrets (`.streamlit/secrets.toml`)."
            )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        fetch_clicked = st.button("Fetch real observations →", type="primary", use_container_width=True)

    with col_map:
        st.markdown(f"""
        <div style="font-family: 'Inter', sans-serif; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: {_TEXT_SUBTLE}; margin-bottom: 8px;">
          AOI Geographic Preview
        </div>
        """, unsafe_allow_html=True)
        try:
            current_bounds = parse_aoi_bounds(bounds_input)
            render_aoi_preview(current_bounds, height=390)
            st.caption(f"Coordinates: Lon [{current_bounds[0]}°, {current_bounds[2]}°] · Lat [{current_bounds[1]}°, {current_bounds[3]}°]")
        except Exception:
            st.info("Enter valid bounding box coordinates to preview the map.")

    if fetch_clicked:
        st.session_state.pop("analysis_df", None)
        st.session_state.pop("raw_df", None)
        st.session_state.pop("analysis_config", None)
        st.session_state.pop("dataset_counts", None)
        st.session_state.pop("dataset_warnings", None)
        st.session_state["show_s2_preview"] = False
        try:
            ee_project_id = get_configured_project_id()
            if not ee_project_id:
                st.error("Google Earth Engine project is not configured. Please set `EE_PROJECT_ID` in your environment or in Streamlit Secrets.")
                st.info("Tip: Set `EE_PROJECT_ID` in your environment (e.g. `$env:EE_PROJECT_ID='your-project-id'`) or Streamlit Cloud Secrets.")
                st.stop()

            bounds = parse_aoi_bounds(bounds_input)
            if not datasets_selected:
                raise ValueError("Select at least one satellite dataset.")
            if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
                raise ValueError("Select both start and end dates.")
            start, end = date_range
            if start > end:
                raise ValueError("Start date must be before end date.")
            if (end - start).days > 1100:
                raise ValueError("Limit each query to about three years to keep Earth Engine requests responsive.")

            start_text = start.isoformat()
            end_exclusive = (end + timedelta(days=1)).isoformat()

            with st.spinner("Extracting multi-satellite observations from Google Earth Engine..."):
                raw_df, counts, warnings = fetch_real_data(
                    ee_project_id, bounds, start_text, end_exclusive,
                    tuple(datasets_selected), int(cloud_thresh),
                    s1_orbit_pass=s1_orbit_pass
                )
                result_df = aggregate_feature_timeseries(raw_df, temporal_agg)
                if result_df.empty:
                    raise RuntimeError("Earth Engine returned data, but no observations remained after temporal aggregation.")

                st.session_state["raw_df"] = raw_df
                st.session_state["analysis_df"] = result_df
                st.session_state["analysis_config"] = {
                    "project_id": ee_project_id,
                    "bounds": bounds,
                    "start_date": start_text,
                    "end_date": end.isoformat(),
                    "end_date_exclusive": end_exclusive,
                    "datasets": tuple(datasets_selected),
                    "cloud_percent": int(cloud_thresh),
                    "temporal": temporal_agg,
                    "s1_orbit_pass": s1_orbit_pass,
                }
                st.session_state["dataset_counts"] = counts
                st.session_state["dataset_warnings"] = warnings
                st.session_state["workspace_step"] = 2
                st.success("Successfully fetched real observations! Transitioning to Explore...")
                st.rerun()
        except Exception as exc:
            st.error(f"Data query failed: {exc}")
            st.info("Tip: For Earth Engine authentication, run `earthengine authenticate` in your terminal and ensure the Google Cloud Project has Earth Engine API enabled.")

    # If data already exists, show Next button
    if st.session_state.get("analysis_df") is not None:
        st.markdown("<hr style='border: none; border-top: 1px solid #e2e8f0; margin: 32px 0;'>", unsafe_allow_html=True)
        nav_c1, nav_c2 = st.columns([8, 2])
        with nav_c2:
            if st.button("Proceed to Explore →", type="primary", use_container_width=True):
                st.session_state["workspace_step"] = 2
                st.rerun()


def render_step_2_explore():
    """Step 2: Explore observations, metrics, time series, satellite preview, and table."""
    analysis_df = st.session_state.get("analysis_df")
    config = st.session_state.get("analysis_config")

    if analysis_df is None or config is None:
        st.warning("Please configure and fetch satellite observations in Step 1 first.")
        if st.button("← Go to Step 1: Configure study", type="primary"):
            st.session_state["workspace_step"] = 1
            st.rerun()
        return

    st.markdown('<span class="sw-section-tag">Step 02</span>', unsafe_allow_html=True)
    st.markdown(f"""
    <h2 style="font-size: 2.2rem; font-weight: 600; color: {_TEXT_MAIN}; margin-bottom: 8px;">
      Explore observations & coverage
    </h2>
    <p style="color: {_TEXT_MUTED}; font-size: 1.02rem; margin-bottom: 24px;">
      Inspect extracted time-series features, sensor data density, and live satellite true-colour composites.
    </p>
    """, unsafe_allow_html=True)

    # Display dataset warnings prominently if any collection was empty or fell back
    warnings = st.session_state.get("dataset_warnings", [])
    if warnings:
        for w in warnings:
            st.warning(f"⚠️ {w}")

    # Top metrics strip
    valid_features = feature_columns(analysis_df)
    obs_count = len(analysis_df)
    feat_count = len(valid_features)
    counts = st.session_state.get("dataset_counts", {})
    requested_datasets = config.get("datasets", ())
    total_requested = len(requested_datasets)
    ingested_sensors = sum(1 for d in requested_datasets if counts.get(d, {}).get("valid_dates", 0) > 0)
    sensors_label = f"{ingested_sensors} of {total_requested}" if (counts and ingested_sensors != total_requested) else str(total_requested)
    total_images = sum(v.get("images", 0) for v in counts.values()) if counts else obs_count

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Time Steps", obs_count)
    m2.metric("Usable Features", feat_count)
    m3.metric("Sensors Ingested", sensors_label)
    m4.metric("Total Scenes Queried", total_images)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Dataset coverage breakdown table
    if counts:
        has_empty_sensor = any(v.get("valid_dates", 0) == 0 for v in counts.values())
        with st.expander("Sensor coverage breakdown", expanded=bool(warnings or has_empty_sensor)):
            count_rows = []
            for dataset_name, values in counts.items():
                v_count = values.get("valid_dates", 0)
                status_str = "Active" if v_count > 0 else "Empty / No Valid Data"
                count_rows.append({
                    "Satellite Dataset": dataset_name,
                    "Scenes / Composites Ingested": values.get("images", 0),
                    "Valid Regional Observations": v_count,
                    "Status": status_str
                })
            st.dataframe(pd.DataFrame(count_rows), use_container_width=True, hide_index=True)

    # Feature Time Series Inspection
    if valid_features:
        with st.container(border=True):
            col_sel, _ = st.columns([1, 2])
            with col_sel:
                selected_feature = st.selectbox("Inspect feature time series", valid_features, key="step2_feature_sel")
            chart = timeseries_chart(analysis_df, selected_feature, config.get("temporal", "Monthly"))
            render_plotly_figure(chart)
    else:
        st.warning("No varying features available in the extracted data.")

    # Live Sentinel-2 Satellite Map Preview Card
    if "Sentinel-2" in config.get("datasets", ()):
        with st.container(border=True):
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
              <div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.8rem; font-weight: 600; color: #0B6E6E; text-transform: uppercase; letter-spacing: 0.08em;">Live Imagery</div>
                <h4 style="font-size: 1.25rem; margin: 4px 0;">Copernicus Sentinel-2 True-Colour Composite</h4>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if not st.session_state.get("show_s2_preview", False):
                if st.button("Render live Sentinel-2 map preview", key="step2_render_s2"):
                    st.session_state["show_s2_preview"] = True
                    st.rerun()
            else:
                try:
                    initialize_earth_engine(config["project_id"])
                    aoi = ee.Geometry.Rectangle(list(config["bounds"]))
                    collection = load_sentinel2(aoi, config["start_date"], config["end_date_exclusive"], config["cloud_percent"])
                    render_sentinel2_preview(aoi, collection, config["bounds"], height=480)
                except Exception as exc:
                    st.error(f"Unable to render the live Sentinel-2 map: {exc}")

    # Observation Data Table & Download
    with st.expander("Full observations data table", expanded=False):
        st.dataframe(analysis_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download extracted feature table (CSV)",
            analysis_df.to_csv(index=False).encode("utf-8"),
            file_name="swayamyan_real_observations.csv",
            mime="text/csv",
            key="step2_download_csv"
        )

    # Navigation Footer
    st.markdown("<hr style='border: none; border-top: 1px solid #e2e8f0; margin: 32px 0;'>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        if st.button("← Back to Configure", key="step2_back"):
            st.session_state["workspace_step"] = 1
            st.rerun()
    with b_col2:
        if st.button("Next: Cross-sensor analysis →", type="primary", key="step2_next", use_container_width=True):
            st.session_state["workspace_step"] = 3
            st.rerun()


def render_step_3_cross_sensor():
    """Step 3: Cross-sensor correlation matrix, temporal lag analysis, and interpretation."""
    analysis_df = st.session_state.get("analysis_df")
    config = st.session_state.get("analysis_config")

    if analysis_df is None or config is None:
        st.warning("Please configure and fetch observations first.")
        if st.button("← Go to Step 1"):
            st.session_state["workspace_step"] = 1
            st.rerun()
        return

    st.markdown('<span class="sw-section-tag">Step 03</span>', unsafe_allow_html=True)
    st.markdown(f"""
    <h2 style="font-size: 2.2rem; font-weight: 600; color: {_TEXT_MAIN}; margin-bottom: 8px;">
      Cross-sensor correlation & temporal lag
    </h2>
    <p style="color: {_TEXT_MUTED}; font-size: 1.02rem; margin-bottom: 24px;">
      Discover coupled environmental dynamics, lag relationships, and phase offsets between distinct sensors.
    </p>
    """, unsafe_allow_html=True)

    usable_features = feature_columns(analysis_df)

    # Section A: Correlation Matrix
    with st.container(border=True):
        method_col, _ = st.columns([1, 2])
        with method_col:
            method = st.radio("Correlation coefficient", ["pearson", "spearman"], horizontal=True, key="step3_corr_method")

        corr = correlation_matrix(analysis_df.drop(columns=["date"], errors="ignore"), method=method)
        if corr is not None and corr.shape[0] >= 2 and not corr.dropna(how="all").empty:
            render_plotly_figure(correlation_heatmap(corr, f"{method.title()} Cross-Sensor Correlation Matrix"))
            st.caption("Pairwise-complete observational correlation across overlapping dates. Does not imply causation.")
        else:
            st.info("At least two non-constant features with overlapping observations are required to compute the correlation matrix.")

    # Section B: Temporal Lag Analysis
    st.markdown(f"""
    <h3 style="font-size: 1.4rem; font-weight: 600; color: {_TEXT_MAIN}; margin-bottom: 8px;">
      Temporal lag analysis
    </h3>
    <p style="color: {_TEXT_MUTED}; font-size: 0.95rem; margin-bottom: 20px;">
      Determine whether a driver variable (e.g., precipitation or surface temperature) leads a response variable (e.g., NDVI vegetation response).
    </p>
    """, unsafe_allow_html=True)

    if len(usable_features) < 2:
        st.info("Fetch at least two features to compute temporal lag.")
    else:
        with st.container(border=True):
            col_x, col_y = st.columns(2)
            with col_x:
                feat_x = st.selectbox("Driver feature (X)", usable_features, key="step3_lag_x")
            with col_y:
                y_options = [f for f in usable_features if f != feat_x]
                feat_y = st.selectbox("Response feature (Y)", y_options, key="step3_lag_y")

            pair_all = analysis_df[["date", feat_x, feat_y]].sort_values("date").reset_index(drop=True)
            valid_pair = pair_all.dropna(subset=[feat_x, feat_y])

            if config.get("temporal") != "Monthly":
                st.warning("Temporal lag analysis requires regular monthly intervals. Switch aggregation to Monthly in Step 1.")
            elif len(valid_pair) < 4:
                st.warning(f"Only {len(valid_pair)} overlapping observations available for this pair. Choose another pair or expand the date range.")
            else:
                max_allowed_lag = max(1, min(12, (len(pair_all) - 3) // 2))
                max_lag = st.slider("Maximum lag search window (months)", 1, max_allowed_lag, min(3, max_allowed_lag), key="step3_max_lag")
                lag_result = lag_correlation(pair_all[feat_x].to_numpy(), pair_all[feat_y].to_numpy(), max_lag=max_lag)
                peak_lag, peak_corr = detect_peak_lag(lag_result)

                valid_lags = {k: v for k, v in lag_result.items() if v is not None and not np.isnan(v)}
                if valid_lags:
                    render_plotly_figure(lag_correlation_plot(lag_result, f"Lag Correlation: {feat_x} → {feat_y}"))
                else:
                    st.info("Insufficient variance across lag windows to compute correlation values.")

                if peak_lag is not None:
                    lag_direction = "follows" if peak_lag > 0 else ("leads" if peak_lag < 0 else "is synchronous with")
                    # BUG-03 fix: use palette constants instead of old hardcoded hex
                    st.markdown(f"""
                    <div style="background: {_BG_ALT}; border: 1px solid rgba(11, 110, 110, 0.22); border-radius: 0px !important; padding: 16px 22px; color: {_TEAL_DARK}; font-size: 0.95rem; font-family: 'Inter', sans-serif; line-height: 1.5;">
                      <strong>Peak finding:</strong> Strongest correlation <strong>r = {peak_corr:.3f}</strong> at <strong>lag {peak_lag} months</strong>.
                      Response variable <em>{feat_y}</em> {lag_direction} driver <em>{feat_x}</em>.
                    </div>
                    """, unsafe_allow_html=True)

    # Navigation Footer
    st.markdown("<hr style='border: none; border-top: 1px solid #e2e8f0; margin: 32px 0;'>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        if st.button("← Back to Observations", key="step3_back"):
            st.session_state["workspace_step"] = 2
            st.rerun()
    with b_col2:
        if st.button("Next: Feature-level fusion →", type="primary", key="step3_next", use_container_width=True):
            st.session_state["workspace_step"] = 4
            st.rerun()


def render_step_4_fusion():
    """Step 4: Feature-level fusion, readiness metrics, composite generation, and CSV download."""
    analysis_df = st.session_state.get("analysis_df")
    config = st.session_state.get("analysis_config")

    if analysis_df is None or config is None:
        st.warning("Please configure and fetch observations first.")
        if st.button("← Go to Step 1"):
            st.session_state["workspace_step"] = 1
            st.rerun()
        return

    st.markdown('<span class="sw-section-tag">Step 04</span>', unsafe_allow_html=True)
    st.markdown(f"""
    <h2 style="font-size: 2.2rem; font-weight: 600; color: {_TEXT_MAIN}; margin-bottom: 8px;">
      Feature-level fusion
    </h2>
    <p style="color: {_TEXT_MUTED}; font-size: 1.02rem; margin-bottom: 24px;">
      Create a defensible, standardized equal-weight composite signal from lag-aligned multi-satellite time series.
    </p>
    """, unsafe_allow_html=True)

    usable_features = feature_columns(analysis_df)
    if len(usable_features) < 2:
        st.info("At least two non-constant features are required for feature fusion.")
        return

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            fusion_x = st.selectbox("Anchor feature (A)", usable_features, key="step4_feat_x")
        with col2:
            y_opts = [f for f in usable_features if f != fusion_x]
            fusion_y = st.selectbox("Candidate feature (B)", y_opts, key="step4_feat_y")

        pair_all = analysis_df[["date", fusion_x, fusion_y]].sort_values("date").reset_index(drop=True)
        valid_pair = pair_all.dropna(subset=[fusion_x, fusion_y])

        st.markdown(f"""
        <div style="font-family: 'Inter', sans-serif; font-size: 0.85rem; color: {_TEXT_MUTED}; margin-top: 6px; margin-bottom: 18px;">
          Pairwise observation overlap: <strong>{len(valid_pair)}</strong> {config.get('temporal', 'monthly').lower()} time steps
        </div>
        """, unsafe_allow_html=True)

        if config.get("temporal") != "Monthly":
            st.warning("Monthly aggregation is recommended to ensure consistent lag duration.")
        elif len(valid_pair) < 6:
            st.warning("At least 6 overlapping observations are recommended to reliably determine the relationship.")
        else:
            max_allowed_lag = max(1, min(12, (len(pair_all) - 3) // 2))
            max_lag = st.slider("Fusion lag search window (months)", 1, max_allowed_lag, min(3, max_allowed_lag), key="step4_lag_slider")
            lag_res = lag_correlation(pair_all[fusion_x].to_numpy(), pair_all[fusion_y].to_numpy(), max_lag=max_lag)
            peak_lag, peak_corr = detect_peak_lag(lag_res)
            stability = stability_score(pair_all[fusion_x].to_numpy(), pair_all[fusion_y].to_numpy())

            # Readiness Metric Row
            m_a, m_b, m_c = st.columns(3)
            m_a.metric("Peak Lag", "N/A" if peak_lag is None else f"{peak_lag} mo")
            m_b.metric("Peak Correlation", "N/A" if peak_corr is None else f"{peak_corr:.3f}")
            m_c.metric("Rolling Stability Var", "N/A" if stability is None else f"{stability:.3f}")

            # Scientific Recommendation
            decision_text = fusion_decision(peak_corr, peak_lag, stability)
            st.info(f"**Scientist recommendation:** {decision_text}")

            align_to_peak = st.checkbox(
                "Align candidate feature B using the detected peak lag",
                value=True,
                help="Anchors time axis to feature A and shifts feature B by peak lag."
            )

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            make_fusion = st.button("Build feature-level composite", type="primary", key="step4_btn_fusion")

            if make_fusion:
                try:
                    used_lag = int(peak_lag) if align_to_peak and peak_lag is not None else 0
                    fused = build_feature_level_fusion(analysis_df, fusion_x, fusion_y, lag=used_lag)
                    st.session_state["fused_df"] = fused
                    st.session_state["fused_info"] = {"feat_x": fusion_x, "feat_y": fusion_y, "lag": used_lag}
                    st.success(f"Built standardized equal-weight composite from {len(fused)} observations (lag = {used_lag}).")
                except Exception as exc:
                    st.error(f"Fusion could not be completed: {exc}")

    # Show Fused Results if generated
    if "fused_df" in st.session_state:
        fused = st.session_state["fused_df"]
        finfo = st.session_state.get("fused_info", {})
        with st.container(border=True):
            if not fused.empty and "Fused_feature_z" in fused.columns and fused["Fused_feature_z"].notna().any():
                render_plotly_figure(
                    fusion_composite_chart(fused, f"Standardized Composite · {finfo.get('feat_x')} + {finfo.get('feat_y')} (lag={finfo.get('lag')})")
                )
            else:
                st.info("No data available")
            with st.expander("Fused composite data table", expanded=False):
                st.dataframe(fused, use_container_width=True, hide_index=True)
                st.download_button(
                    "Download fused feature table (CSV)",
                    fused.to_csv(index=False).encode("utf-8"),
                    file_name="swayamyan_feature_fusion.csv",
                    mime="text/csv",
                    key="step4_download_csv"
                )

    # Data Provenance and Catalog References
    with st.expander("Data provenance & scientific specifications", expanded=False):
        source_details = {
            "Sentinel-2": ("COPERNICUS/S2_SR_HARMONIZED", "NDVI, green-NIR NDWI, EVI; SCL cloud/shadow masking; reflectance scale factor 0.0001."),
            "Sentinel-1": ("COPERNICUS/S1_GRD", "VV/VH backscatter in dB; single log representation preserved."),
            "MODIS LST": ("MODIS/061/MOD11A2", "8-day 1km product; day/night LST scaled by 0.02 K and converted to °C; QC mandatory screening."),
            "Landsat 8/9": ("LANDSAT/LC08/C02/T1_L2 + LANDSAT/LC09/C02/T1_L2", "Collection 2 Level-2 surface reflectance and temperature; QA_PIXEL cloud mask."),
            "GPM IMERG": ("NASA/GPM_L3/IMERG_V07", "Half-hourly precipitation rate in mm/hour aggregated to daily totals."),
        }
        for name in config.get("datasets", ()):
            coll_id, proc = source_details[name]
            st.markdown(f"**{name}** (`{coll_id}`): {proc}")

    # Navigation Footer
    st.markdown("<hr style='border: none; border-top: 1px solid #e2e8f0; margin: 32px 0;'>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        if st.button("← Back to Cross-sensor analysis", key="step4_back"):
            st.session_state["workspace_step"] = 3
            st.rerun()
    with b_col2:
        if st.button("Configure new study ↺", key="step4_new_study", use_container_width=True):
            st.session_state["workspace_step"] = 1
            st.rerun()
