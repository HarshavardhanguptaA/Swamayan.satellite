"""Pure-Python temporal alignment helpers for feature time series."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


def merge_feature_frames(frames: Sequence[pd.DataFrame]) -> pd.DataFrame:
    """Outer-join sensor series by acquisition date without inventing values."""
    usable = []
    for source in frames:
        if source is None or source.empty or "date" not in source.columns:
            continue
        frame = source.copy()
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.tz_localize(None)
        frame = frame.dropna(subset=["date"])
        value_columns = [column for column in frame.columns if column != "date"]
        if not value_columns:
            continue
        frame[value_columns] = frame[value_columns].apply(pd.to_numeric, errors="coerce")
        frame = frame.groupby("date", as_index=False)[value_columns].mean(numeric_only=True)
        usable.append(frame)

    if not usable:
        return pd.DataFrame(columns=["date"])

    merged = usable[0]
    for frame in usable[1:]:
        overlap = set(merged.columns).intersection(frame.columns) - {"date"}
        if overlap:
            raise ValueError(f"Duplicate feature names encountered: {sorted(overlap)}")
        merged = merged.merge(frame, on="date", how="outer", validate="one_to_one")
    return merged.sort_values("date").reset_index(drop=True)


def aggregate_feature_timeseries(df: pd.DataFrame, period: str = "Monthly") -> pd.DataFrame:
    """Collapse duplicate observation dates and optionally aggregate by month.

    Continuous satellite features are averaged. GPM daily precipitation totals
    are summed by month to preserve the physical meaning of accumulated rainfall.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=list(df.columns) if df is not None else ["date"])
    if "date" not in df.columns:
        raise ValueError("Input data must include a 'date' column.")

    frame = df.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.tz_localize(None)
    frame = frame.dropna(subset=["date"]).sort_values("date")
    value_columns = [column for column in frame.columns if column != "date"]
    frame[value_columns] = frame[value_columns].apply(pd.to_numeric, errors="coerce")
    frame = frame.groupby("date", as_index=False)[value_columns].mean(numeric_only=True)

    if period.lower() not in {"monthly", "month", "month start"}:
        return frame

    frame["date"] = frame["date"].dt.to_period("M").dt.to_timestamp()
    aggregations: Mapping[str, str] = {
        column: ("sum" if "precip" in column.lower() and "mm" in column.lower() else "mean")
        for column in value_columns
    }
    monthly = frame.groupby("date", as_index=False).agg(aggregations).sort_values("date")
    # Keep empty months as NaN so lag k always means k calendar months, rather
    # than the kth available observation after silently compressing gaps.
    month_index = pd.date_range(monthly["date"].min(), monthly["date"].max(), freq="MS")
    monthly = monthly.set_index("date").reindex(month_index)
    monthly.index.name = "date"
    return monthly.reset_index().sort_values("date").reset_index(drop=True)
