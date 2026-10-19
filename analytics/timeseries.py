"""Extract real region-mean feature time series from Earth Engine collections."""

from __future__ import annotations

from collections.abc import Sequence

import ee
import pandas as pd


def extract_timeseries(collection, band_name, region, scale=30, reducer=None, max_images=2500):
    """Return a DataFrame with a UTC ``date`` and one column per selected band.

    ``band_name`` may be a single band or a sequence. The query is executed
    against Earth Engine; no synthetic or fallback observations are generated.
    ``scale`` should reflect the dataset's native resolution (or a coarser
    resolution appropriate to the AOI).
    """
    bands = [band_name] if isinstance(band_name, str) else list(band_name)
    if not bands:
        raise ValueError("At least one band name is required.")
    if reducer is None:
        reducer = ee.Reducer.mean()

    count = int(collection.size().getInfo())
    columns = ["date", *bands]
    if count == 0:
        empty = pd.DataFrame(columns=columns)
        empty.attrs["image_count"] = 0
        return empty
    if count > max_images:
        raise ValueError(
            f"The selected period contains {count:,} images, above the safe limit "
            f"of {max_images:,}. Choose a shorter date range."
        )

    def image_to_feature(image):
        stats = image.select(bands).reduceRegion(
            reducer=reducer,
            geometry=region,
            scale=scale,
            maxPixels=1e9,
            bestEffort=True,
            tileScale=4,
        )
        props = {"date": image.date().format("YYYY-MM-dd")}
        for band in bands:
            props[band] = stats.get(band)
        return ee.Feature(None, props)

    feature_collection = collection.map(image_to_feature)
    response = feature_collection.getInfo()
    records = []
    for feature in response.get("features", []):
        props = feature.get("properties", {})
        date_value = props.get("date")
        if not date_value:
            continue
        row = {"date": date_value}
        for band in bands:
            value = props.get(band)
            row[band] = float(value) if value is not None else float("nan")
        # Ignore rows where every requested band is masked over this AOI.
        if any(pd.notna(row[band]) for band in bands):
            records.append(row)

    if not records:
        empty = pd.DataFrame(columns=columns)
        empty.attrs["image_count"] = count
        return empty

    frame = pd.DataFrame.from_records(records, columns=columns)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce", utc=True).dt.tz_localize(None)
    frame = frame.dropna(subset=["date"]).sort_values("date")
    frame = frame.groupby("date", as_index=False)[bands].mean(numeric_only=True)
    frame = frame.reset_index(drop=True)
    frame.attrs["image_count"] = count
    return frame
