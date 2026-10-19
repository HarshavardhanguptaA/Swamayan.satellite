"""Plotly chart builders styled for the SWAYAMYAN modern scientific design."""

from __future__ import annotations

from typing import Any, Mapping, Sequence
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

__all__ = [
    "preview_signal_chart",
    "correlation_heatmap",
    "lag_correlation_plot",
    "timeseries_chart",
    "fusion_composite_chart",
    "render_plotly_figure",
]

# Consistent scientific color and typography tokens
TEAL_PRIMARY = "#0B6E6E"
TEAL_DARK = "#095858"
AQUA_ACCENT = "#5CC8C0"
SLATE_NEGATIVE = "#64748B"
AMBER_ACCENT = "#F2994A"
TEAL_LIGHT_FILL = "rgba(11, 110, 110, 0.08)"
TEXT_COLOR = "#0A1F2C"
MUTED_TEXT = "#52677A"
MUTED_GRID = "rgba(220, 230, 232, 0.8)"
DM_SERIF_FONT = "'DM Serif Display', Georgia, serif"
INTER_FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"



def preview_signal_chart(
    months: Sequence[str] | None = None,
    values: Sequence[float] | None = None,
    title: str | None = None,
    height: int = 280,
) -> go.Figure:
    """Build the illustrative demonstration chart matching Screenshot 2.

    Uses deterministic seasonal values for the landing-page preview
    and clearly identifies the data as demonstration content.
    """
    if months is None:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    if values is None:
        x_nums = np.linspace(0, 2 * np.pi, len(months))
        calculated = 0.45 + 0.12 * np.sin(x_nums + 0.3) - 0.04 * np.cos(2 * x_nums)
        values = [round(float(v), 4) for v in calculated]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(months),
        y=list(values),
        mode="lines",
        line=dict(color=TEAL_PRIMARY, width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor=TEAL_LIGHT_FILL,
        connectgaps=False,
        hoverinfo="x+y",
        hovertemplate="%{x}: %{y:.2f}<br><span style='font-size:10px; color:#7A8DA0;'>Demonstration preview</span><extra></extra>",
        name="Feature Index (Demonstration)",
    ))

    layout_kwargs: dict[str, Any] = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=20, t=80 if title else 30, b=60),
        height=height,
        font=dict(family=INTER_FONT, color=TEXT_COLOR),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor="rgba(220, 230, 232, 1)",
            tickfont=dict(family=INTER_FONT, size=11, color=MUTED_TEXT),
        ),
        yaxis=dict(
            range=[0, 1.05],
            tickvals=[0, 0.25, 0.5, 0.75, 1],
            showgrid=True,
            gridcolor=MUTED_GRID,
            showline=False,
            tickfont=dict(family=INTER_FONT, size=11, color=MUTED_TEXT),
        ),
        hovermode="x unified",
        showlegend=False,
    )

    if title:
        layout_kwargs["title"] = dict(
            text=title,
            font=dict(family=DM_SERIF_FONT, size=16, color=TEXT_COLOR),
            x=0.02,
            xanchor="left",
            y=0.95,
            yanchor="top",
        )

    fig.update_layout(**layout_kwargs)
    return fig


def correlation_heatmap(corr_df: pd.DataFrame, title: str = "Cross-Satellite Feature Correlation") -> go.Figure:
    """Diverging correlation heatmap matching the white-dominant & teal theme."""
    colorscale = [
        [0.0, "#0A1F2C"],
        [0.35, SLATE_NEGATIVE],
        [0.5, "#ffffff"],
        [0.75, AQUA_ACCENT],
        [1.0, TEAL_PRIMARY],
    ]

    fig = px.imshow(
        corr_df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale=colorscale,
        zmin=-1,
        zmax=1,
        origin="lower",
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family=DM_SERIF_FONT, size=16, color=TEXT_COLOR),
            x=0.02,
            xanchor="left",
            y=0.95,
            yanchor="top",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=INTER_FONT, color=TEXT_COLOR),
        height=max(400, 42 * len(corr_df) + 160),
        margin=dict(l=60, r=40, t=80, b=60),
        coloraxis_colorbar=dict(
            title=dict(text="Correlation", font=dict(family=INTER_FONT, size=12)),
            thickness=14,
            len=0.8,
            tickfont=dict(family=INTER_FONT, size=11),
        ),
    )
    return fig


def lag_correlation_plot(lag_dict: Mapping[Any, Any], title: str = "Lag Correlation") -> go.Figure:
    """Minimal lag bar chart with explicit teal for positive lags and neutral slate for negative lags."""
    if not lag_dict:
        return go.Figure()

    lags = [k for k, v in lag_dict.items() if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not lags:
        return go.Figure()

    values = [float(lag_dict[k]) for k in lags]
    max_abs_idx = int(np.argmax([abs(v) for v in values])) if values else -1
    # Amber (#F2994A) for peak lag, teal (#0B6E6E) for positive, slate (#64748B) for negative
    colors = [
        AMBER_ACCENT if i == max_abs_idx else (TEAL_PRIMARY if val >= 0 else SLATE_NEGATIVE)
        for i, val in enumerate(values)
    ]

    fig = go.Figure(go.Bar(
        x=lags,
        y=values,
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="Lag %{x}: %{y:.3f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#94a3b8")
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family=DM_SERIF_FONT, size=16, color=TEXT_COLOR),
            x=0.02,
            xanchor="left",
            y=0.95,
            yanchor="top",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=INTER_FONT, color=TEXT_COLOR),
        xaxis=dict(
            title="Lag (timesteps; positive means Y follows X)",
            title_font=dict(family=INTER_FONT, size=12, color=MUTED_TEXT),
            tickfont=dict(family=INTER_FONT, size=11, color=MUTED_TEXT),
            gridcolor=MUTED_GRID,
            dtick=1,
        ),
        yaxis=dict(
            title="Pearson Correlation (r)",
            title_font=dict(family=INTER_FONT, size=12, color=MUTED_TEXT),
            range=[-1.1, 1.1],
            gridcolor=MUTED_GRID,
            tickfont=dict(family=INTER_FONT, size=11, color=MUTED_TEXT),
        ),
        height=380,
        margin=dict(l=60, r=30, t=80, b=60),
        bargap=0.35,
    )
    return fig


def timeseries_chart(
    df: pd.DataFrame,
    y_col: str,
    temporal_name: str = "Monthly",
    title: str | None = "__DEFAULT__",
) -> go.Figure:
    """Clean scientific time series plot with Inter and DM Serif Display typography."""
    plot_df = df.copy()
    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
    plot_df = plot_df.dropna(subset=["date", y_col]).sort_values("date")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df["date"],
        y=plot_df[y_col],
        mode="lines+markers",
        line=dict(color=TEAL_PRIMARY, width=2.5, shape="spline"),
        marker=dict(size=6, color=TEAL_DARK, line=dict(color="#ffffff", width=1.5)),
        fill="tozeroy",
        fillcolor=TEAL_LIGHT_FILL,
        connectgaps=False,
        name=y_col,
        hovertemplate="%{x|%Y-%m-%d}: %{y:.3f}<extra></extra>",
    ))
    
    chart_title = f"{y_col} · {temporal_name} time series" if title == "__DEFAULT__" else title
    
    layout_kwargs: dict[str, Any] = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=INTER_FONT, color=TEXT_COLOR),
        margin=dict(l=60, r=30, t=80 if chart_title else 30, b=60),
        height=380,
        xaxis=dict(
            title="Observation Date",
            title_font=dict(family=INTER_FONT, size=12, color=MUTED_TEXT),
            tickfont=dict(family=INTER_FONT, size=11, color=MUTED_TEXT),
            gridcolor=MUTED_GRID,
        ),
        yaxis=dict(
            title=y_col,
            title_font=dict(family=INTER_FONT, size=12, color=MUTED_TEXT),
            tickfont=dict(family=INTER_FONT, size=11, color=MUTED_TEXT),
            gridcolor=MUTED_GRID,
        ),
        hovermode="x unified",
    )
    if chart_title:
        layout_kwargs["title"] = dict(
            text=chart_title,
            font=dict(family=DM_SERIF_FONT, size=16, color=TEXT_COLOR),
            x=0.02,
            xanchor="left",
            y=0.95,
            yanchor="top",
        )
    fig.update_layout(**layout_kwargs)
    return fig


def fusion_composite_chart(df: pd.DataFrame, title: str = "Feature-Level Fusion Composite") -> go.Figure:
    """Plotly chart for the standardized equal-weight fused signal with Inter and DM Serif Display typography."""
    plot_df = df.dropna(subset=["date", "Fused_feature_z"]).sort_values("date") if "Fused_feature_z" in df.columns else df
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df["date"],
        y=plot_df["Fused_feature_z"],
        mode="lines+markers",
        line=dict(color=TEAL_PRIMARY, width=3, shape="spline"),
        marker=dict(size=7, color=TEAL_DARK, line=dict(color="#ffffff", width=2)),
        fill="tozeroy",
        fillcolor=TEAL_LIGHT_FILL,
        connectgaps=False,
        hovertemplate="%{x|%Y-%m-%d}: %{y:.3f} σ<extra></extra>",
    ))
    fig.add_hline(
        y=0,
        line_width=1,
        line_dash="dash",
        line_color="#94a3b8",
        annotation_text="Mean (0σ)",
        annotation_position="bottom right",
        annotation_font=dict(family=INTER_FONT, size=11, color=MUTED_TEXT),
    )
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family=DM_SERIF_FONT, size=16, color=TEXT_COLOR),
            x=0.02,
            xanchor="left",
            y=0.95,
            yanchor="top",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=INTER_FONT, color=TEXT_COLOR),
        margin=dict(l=60, r=30, t=80, b=60),
        height=380,
        xaxis=dict(
            title="Date",
            title_font=dict(family=INTER_FONT, size=12, color=MUTED_TEXT),
            tickfont=dict(family=INTER_FONT, size=11, color=MUTED_TEXT),
            gridcolor=MUTED_GRID,
        ),
        yaxis=dict(
            title="Standardized Composite (z-score)",
            title_font=dict(family=INTER_FONT, size=12, color=MUTED_TEXT),
            tickfont=dict(family=INTER_FONT, size=11, color=MUTED_TEXT),
            gridcolor=MUTED_GRID,
        ),
    )
    return fig


def render_plotly_figure(fig: go.Figure | None, use_container_width: bool = True, **kwargs) -> None:
    """Confirm every figure has at least one trace before rendering with theme=None, otherwise show st.info."""
    import streamlit as st
    kwargs.setdefault("config", {"displayModeBar": False, "displaylogo": False})
    if fig is not None and getattr(fig, "data", None) and len(fig.data) > 0:
        has_data = any(
            (getattr(trace, "x", None) is not None and len(trace.x) > 0) or
            (getattr(trace, "z", None) is not None and len(trace.z) > 0)
            for trace in fig.data
        )
        if has_data:
            st.plotly_chart(fig, use_container_width=use_container_width, theme=None, **kwargs)
            return
    st.info("No data available")

