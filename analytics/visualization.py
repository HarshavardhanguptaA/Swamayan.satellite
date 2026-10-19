"""Reusable Plotly visualizations for extracted feature time series."""

import plotly.express as px


def feature_timeseries_chart(df, feature, title=None):
    if df is None or df.empty or not {"date", feature}.issubset(df.columns):
        raise ValueError("A non-empty date/feature DataFrame is required.")
    return px.line(df, x="date", y=feature, markers=True,
                   title=title or f"{feature} over time",
                   labels={"date": "Observation date", feature: feature})


def feature_distribution_chart(df, feature):
    if df is None or df.empty or feature not in df.columns:
        raise ValueError("A non-empty feature DataFrame is required.")
    return px.histogram(df, x=feature, nbins=30, title=f"Distribution of {feature}")
