"""Landing page for SWAYAMYAN matching the exact layout and aesthetics of the reference screenshots."""

import streamlit as st
from datetime import datetime
from ui.charts import preview_signal_chart, render_plotly_figure

# Palette constants (single source of truth — mirrors :root in styles.py)
_TEAL = "#0B6E6E"
_TEAL_DARK = "#095858"
_AQUA = "#5CC8C0"
_BANNER = "#0A3D42"
_TEXT_MAIN = "#0A1F2C"
_TEXT_MUTED = "#52677A"
_TEXT_SUBTLE = "#7A8DA0"
_BORDER = "#DCE6E8"
_BG_ALT = "#F4F8F8"


def render_landing_page():
    """Render the full landing page."""
    from ui.globe import render_earth_hero_graphic

    # ── Top Navigation Bar ────────────────────────────────────────────────
    st.markdown(f"""
    <div id="top" style="display:flex;align-items:center;justify-content:space-between;
         padding:12px 0 24px 0;border-bottom:1px solid {_BORDER};margin-bottom:36px;">
      <div style="display:flex;align-items:center;gap:14px;">
        <div style="width:24px;height:24px;border:2px solid {_TEAL};position:relative;
             display:flex;align-items:center;justify-content:center;">
          <div style="width:8px;height:8px;background:{_TEAL};"></div>
          <div style="position:absolute;width:30px;height:14px;border:1.5px solid rgba(11,110,110,0.4);
               transform:rotate(-30deg);"></div>
        </div>
        <span style="font-family:'DM Serif Display',Georgia,serif;font-weight:400;
              font-size:1.35rem;letter-spacing:0.04em;color:{_TEXT_MAIN};">SWAYAMYAN</span>
      </div>
      <div style="display:flex;align-items:center;gap:32px;font-size:0.95rem;
           color:{_TEXT_MUTED};font-weight:500;font-family:'Inter',sans-serif;">
        <a href="#platform" style="color:{_TEXT_MUTED};text-decoration:none;cursor:pointer;">Platform</a>
        <a href="#method"   style="color:{_TEXT_MUTED};text-decoration:none;cursor:pointer;">Method</a>
        <a href="#datasets" style="color:{_TEXT_MUTED};text-decoration:none;cursor:pointer;">Datasets</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 1. HERO SECTION ──────────────────────────────────────────────────
    hero_col_left, hero_col_right = st.columns([1.1, 1], gap="large")

    with hero_col_left:
        st.markdown(f"""
        <div class="sw-hero-tag" style="margin-bottom:18px;" id="platform">
          <span class="sw-label-pill">
            <span style="color:{_TEAL};font-size:14px;">■</span> MULTI-SENSOR EARTH OBSERVATION
          </span>
        </div>
        """, unsafe_allow_html=True)

        # DM Serif Display headline — upright then italic second sentence
        st.markdown(f"""
        <h1 class="sw-hero-h1" style="font-family:'DM Serif Display',Georgia,serif;font-weight:400;
            font-size:3.8rem;line-height:1.08;margin-bottom:24px;color:{_TEXT_MAIN};
            letter-spacing:-0.01em;">
          Correlate satellites.<br>
          <em>Fuse the signal.</em>
        </h1>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="sw-hero-subhead">
          <p style="font-size:1.35rem;font-weight:600;color:{_TEXT_MAIN};
               line-height:1.4;margin-bottom:14px;">
            Turn multi-satellite observations into meaningful environmental insights.
          </p>
          <p style="font-size:1.08rem;color:{_TEXT_MUTED};line-height:1.65;
               margin-bottom:38px;max-width:500px;">
            SWAYAMYAN brings temporal correlation and feature-level fusion into one clear,
            research-ready workspace.
          </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sw-hero-btns">', unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns([1, 1.2])
        with btn_c1:
            if st.button("Get started →", type="primary", key="hero_get_started", use_container_width=True):
                st.session_state["view"] = "workspace"
                st.session_state["workspace_step"] = 1
                st.rerun()
        with btn_c2:
            if st.button("▷ Explore the platform", key="hero_explore", use_container_width=True):
                st.session_state["view"] = "workspace"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with hero_col_right:
        import streamlit.components.v1 as components
        globe_html = render_earth_hero_graphic()
        components.html(globe_html, height=480, scrolling=False)

    st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)

    # ── 2. METRICS STRIP ─────────────────────────────────────────────────
    m_col1, m_col2, m_col3 = st.columns(3)

    def _metric_html(num_text, label_text):
        return f"""
        <div style="padding:14px 4px;border-left:2px solid {_TEAL};padding-left:18px;">
          <div style="font-family:'DM Serif Display',Georgia,serif;font-size:3.4rem;
               font-weight:400;color:{_TEXT_MAIN};line-height:1;
               letter-spacing:-0.02em;margin-bottom:8px;">{num_text}</div>
          <div style="font-family:'Inter',sans-serif;font-size:0.8rem;font-weight:600;
               letter-spacing:0.08em;color:{_TEXT_SUBTLE};text-transform:uppercase;">{label_text}</div>
        </div>
        """

    with m_col1:
        st.markdown(_metric_html("5", "Sensor families"), unsafe_allow_html=True)
    with m_col2:
        st.markdown(_metric_html("±12 mo", "Lag search window"), unsafe_allow_html=True)
    with m_col3:
        st.markdown(_metric_html("CSV", "Export for every result"), unsafe_allow_html=True)

    st.markdown("<div style='height:64px;'></div>", unsafe_allow_html=True)

    # ── 3. A CLEARER SIGNAL — 3 CAPABILITY CARDS ─────────────────────────
    st.markdown('<span class="sw-section-tag">A Clearer Signal</span>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="medium")

    _svg_layers = (
        '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>'
        '<polyline points="2 17 12 22 22 17"></polyline>'
        '<polyline points="2 12 12 17 22 12"></polyline></svg>'
    )
    _svg_calendar = (
        '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>'
        '<line x1="16" y1="2" x2="16" y2="6"></line>'
        '<line x1="8" y1="2" x2="8" y2="6"></line>'
        '<line x1="3" y1="10" x2="21" y2="10"></line></svg>'
    )
    _svg_star = (
        '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 '
        '5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>'
    )

    def _card_html(icon_svg, num, heading, body):
        return f"""
        <div class="sw-card" style="height:100%;">
          <div style="color:{_TEAL};margin-bottom:24px;font-size:24px;">{icon_svg}</div>
          <div style="font-family:'Inter',sans-serif;font-size:0.82rem;color:#94a3b8;
               font-weight:700;margin-bottom:12px;">{num}</div>
          <h3 style="font-size:1.45rem;margin-bottom:12px;">{heading}</h3>
          <p style="color:{_TEXT_MUTED};font-size:1.02rem;line-height:1.6;">{body}</p>
        </div>
        """

    with c1:
        st.markdown(_card_html(_svg_layers, "01", "Multi-sensor analytics",
            "Work across radar, optical, thermal, rainfall and land surface variables without "
            "manual data wrangling or pipeline overhead."), unsafe_allow_html=True)
    with c2:
        st.markdown(_card_html(_svg_calendar, "02", "Temporal correlation",
            "Reveal how environmental variables move together or lag each other over multi-season "
            "cycles with defensible lag search windows."), unsafe_allow_html=True)
    with c3:
        st.markdown(_card_html(_svg_star, "03", "Feature-level fusion",
            "Build a standardized composite from aligned real multi-satellite time series with "
            "automated stability scoring."), unsafe_allow_html=True)

    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)

    # ── 4. HOW IT WORKS ──────────────────────────────────────────────────
    st.markdown('<div id="method"></div>', unsafe_allow_html=True)
    st.markdown('<span class="sw-section-tag">How it works</span>', unsafe_allow_html=True)

    hw1, hw2, hw3 = st.columns(3, gap="medium")

    def _step_card(num, title, body):
        return f"""
        <div style="padding:28px 24px;border:1px solid {_BORDER};background:#fff;height:100%;">
          <div style="font-family:'DM Serif Display',Georgia,serif;font-size:2.8rem;
               font-weight:400;color:{_TEAL};opacity:0.35;line-height:1;margin-bottom:16px;">{num}</div>
          <h3 style="font-size:1.15rem;margin-bottom:10px;color:{_TEXT_MAIN};">{title}</h3>
          <p style="font-size:0.98rem;color:{_TEXT_MUTED};line-height:1.6;">{body}</p>
        </div>
        """

    with hw1:
        st.markdown(_step_card("1", "Configure study",
            "Select your area of interest, satellite collections, and observation window."),
            unsafe_allow_html=True)
    with hw2:
        st.markdown(_step_card("2", "Explore observations",
            "Inspect extracted time series, run lag correlation, and visualise cross-sensor alignment."),
            unsafe_allow_html=True)
    with hw3:
        st.markdown(_step_card("3", "Fuse features",
            "Combine the aligned signals into a single defensible composite ready for export."),
            unsafe_allow_html=True)

    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)

    # ── 5. FROM PIXELS TO PATTERNS ────────────────────────────────────────
    st.markdown('<span class="sw-section-tag">From Pixels to Patterns</span>', unsafe_allow_html=True)

    p_col1, p_col2 = st.columns([1.2, 1], gap="large")
    with p_col1:
        st.markdown(f"""
        <h2 style="font-size:3rem;font-weight:700;line-height:1.15;color:{_TEXT_MAIN};
             letter-spacing:-0.02em;">
          Earth observation is rich.<br>
          <span style="font-weight:400;color:{_TEXT_MAIN};">Understanding it shouldn't be hard.</span>
        </h2>
        """, unsafe_allow_html=True)

    with p_col2:
        st.markdown(f"""
        <div style="padding-top:10px;border-left:2px solid {_TEAL};padding-left:28px;">
          <p style="font-size:1.15rem;color:{_TEXT_MUTED};line-height:1.65;margin-bottom:24px;">
            Environmental change rarely appears in one layer. SWAYAMYAN helps researchers move from
            disconnected satellite products to a readable, defensible signal.
          </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("See how it works →", key="btn_see_how_it_works"):
            st.session_state["view"] = "workspace"
            st.rerun()

    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)

    # ── 6. DATA SOURCES STRIP ─────────────────────────────────────────────
    st.markdown('<div id="datasets"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="border-top:1px solid {_BORDER};border-bottom:1px solid {_BORDER};
         padding:28px 0;margin-bottom:0;">
      <span class="sw-section-tag" style="margin-bottom:20px;">Data sources</span>
      <div style="display:flex;align-items:center;gap:0;flex-wrap:wrap;">
        <div style="padding:0 28px;border-right:1px solid {_BORDER};">
          <div style="font-family:'Inter',sans-serif;font-size:0.88rem;font-weight:600;
               color:{_TEXT_MAIN};margin-bottom:2px;">Sentinel-1</div>
          <div style="font-size:0.75rem;color:{_TEXT_SUBTLE};">SAR · C-band</div>
        </div>
        <div style="padding:0 28px;border-right:1px solid {_BORDER};">
          <div style="font-family:'Inter',sans-serif;font-size:0.88rem;font-weight:600;
               color:{_TEXT_MAIN};margin-bottom:2px;">Sentinel-2</div>
          <div style="font-size:0.75rem;color:{_TEXT_SUBTLE};">Optical · MSI</div>
        </div>
        <div style="padding:0 28px;border-right:1px solid {_BORDER};">
          <div style="font-family:'Inter',sans-serif;font-size:0.88rem;font-weight:600;
               color:{_TEXT_MAIN};margin-bottom:2px;">MODIS</div>
          <div style="font-size:0.75rem;color:{_TEXT_SUBTLE};">Thermal · LST</div>
        </div>
        <div style="padding:0 28px;border-right:1px solid {_BORDER};">
          <div style="font-family:'Inter',sans-serif;font-size:0.88rem;font-weight:600;
               color:{_TEXT_MAIN};margin-bottom:2px;">Landsat 8/9</div>
          <div style="font-size:0.75rem;color:{_TEXT_SUBTLE};">Optical · OLI/TIRS</div>
        </div>
        <div style="padding:0 28px;border-right:1px solid {_BORDER};">
          <div style="font-family:'Inter',sans-serif;font-size:0.88rem;font-weight:600;
               color:{_TEXT_MAIN};margin-bottom:2px;">GPM IMERG</div>
          <div style="font-size:0.75rem;color:{_TEXT_SUBTLE};">Precipitation</div>
        </div>
        <div style="padding:0 28px;">
          <div style="font-family:'Inter',sans-serif;font-size:0.78rem;color:{_TEXT_SUBTLE};
               font-style:italic;">via Google Earth Engine</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)

    # ── 7. SIGNAL PREVIEW ────────────────────────────────────────────────
    analysis_df = st.session_state.get("analysis_df")
    config = st.session_state.get("analysis_config")

    has_real_data = False
    primary_feat = None
    latest_val = 0.482
    delta_str = "+4.2%"

    if analysis_df is not None and not analysis_df.empty:
        import pandas as pd
        from ui.workspace import feature_columns
        feats = feature_columns(analysis_df)
        if feats and feats[0] in analysis_df.columns:
            primary_feat = feats[0]
            valid_vals = pd.to_numeric(analysis_df[primary_feat], errors="coerce").dropna().values
            if len(valid_vals) > 0:
                has_real_data = True
                latest_val = float(valid_vals[-1])
                first_val = float(valid_vals[0])
                pct_delta = ((latest_val - first_val) / abs(first_val) * 100) if first_val != 0 else 0.0
                delta_str = f"{'+' if pct_delta >= 0 else ''}{pct_delta:.1f}%"

    status_label = "Verified regional observations" if has_real_data else "Demonstration preview (monthly NDVI)"

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
      <span class="sw-section-tag">Signal Preview</span>
      <span style="font-family:'Inter',sans-serif;font-size:0.85rem;color:{_TEAL};
            font-weight:600;display:flex;align-items:center;gap:8px;">
        <span>■</span> {status_label}
      </span>
    </div>
    <h2 style="font-size:2.6rem;font-weight:700;color:{_TEXT_MAIN};
         letter-spacing:-0.02em;margin-bottom:24px;">One view. Many perspectives.</h2>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        # BUG-06 fix: show actual feature name when real data is present
        if has_real_data and primary_feat:
            temporal_text = config.get("temporal", "Monthly").lower() if config else "monthly"
            card_label = f"{primary_feat} · {temporal_text}"
        else:
            card_label = "Vegetation index (NDVI), monthly"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <div style="font-family:'Inter',sans-serif;font-size:0.8rem;font-weight:600;
               letter-spacing:0.08em;color:{_TEXT_SUBTLE};text-transform:uppercase;">
            {card_label}
          </div>
          <div style="display:flex;align-items:baseline;gap:10px;">
            <span style="font-family:'Inter',sans-serif;font-size:1.8rem;font-weight:700;
                  color:{_TEXT_MAIN};letter-spacing:-0.02em;">{latest_val:.3f}</span>
            <span style="font-family:'Inter',sans-serif;font-size:0.82rem;font-weight:600;
                  color:{_TEAL};background:{_BG_ALT};border:1px solid rgba(11,110,110,0.3);
                  padding:2px 10px;">{delta_str}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if has_real_data and primary_feat:
            from ui.charts import timeseries_chart
            temp_name = config.get("temporal", "Monthly") if config else "Monthly"
            render_plotly_figure(timeseries_chart(analysis_df, primary_feat, temp_name, title=None))
        else:
            render_plotly_figure(preview_signal_chart(title=None))

    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)

    # ── 8. CTA BANNER ────────────────────────────────────────────────────────
    with st.container():
        st.markdown("""
        <div style="max-width:620px;position:relative;z-index:2;">
          <span style="font-family:'Inter',sans-serif;font-size:0.8rem;font-weight:700;
                letter-spacing:0.14em;text-transform:uppercase;color:#99f6e4;
                display:block;margin-bottom:18px;">The Analytical Workspace</span>
          <h2 style="font-size:3.6rem;line-height:1.08;font-weight:400;color:#ffffff;
               letter-spacing:-0.02em;margin-bottom:20px;
               font-family:'DM Serif Display',Georgia,serif;">
            Make the invisible<br>legible.
          </h2>
          <p style="font-size:1.25rem;color:#ccfbf1;line-height:1.5;margin-bottom:34px;">
            Configure your study, explore the signal, and build an insight you can stand behind.
          </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Start a study →", key="cta_start_study", type="primary"):
            st.session_state["view"] = "workspace"
            st.session_state["workspace_step"] = 1
            st.rerun()

    st.markdown("<div style='height:90px;'></div>", unsafe_allow_html=True)

    # ── 9. FOOTER ─────────────────────────────────────────────────────────
    current_year = datetime.now().year
    st.markdown(f"""
    <div style="border-top:1px solid {_BORDER};padding:34px 0 24px 0;display:flex;
         align-items:center;justify-content:space-between;font-size:0.95rem;
         color:{_TEXT_MUTED};font-family:'Inter',sans-serif;">
      <div style="display:flex;align-items:center;gap:12px;">
        <div style="width:20px;height:20px;border:1.5px solid {_TEAL};position:relative;
             display:flex;align-items:center;justify-content:center;">
          <div style="width:6px;height:6px;background:{_TEAL};"></div>
        </div>
        <span style="font-family:'DM Serif Display',Georgia,serif;font-weight:400;font-size:1.15rem;color:{_TEXT_MAIN};letter-spacing:0.04em;">SWAYAMYAN</span>
      </div>
      <div>Earth observation made legible.</div>
      <div>© {current_year} SWAYAMYAN</div>
    </div>
    """, unsafe_allow_html=True)


