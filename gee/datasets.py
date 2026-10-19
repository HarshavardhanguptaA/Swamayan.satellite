"""Dataset entry points for public Earth Engine satellite collections."""

from typing import Any

import ee

from config.constants import GPM, SENTINEL_2
from gee.indices import add_sentinel2_features, mask_sentinel2
from gee.landsat import load_landsat
from gee.modis import load_modis_lst
from gee.sentinel1 import load_sentinel1
from gee.temporal import daily_gpm_precipitation


def load_sentinel2(aoi: Any, start: str, end: str, cloud: int = 30) -> Any:
    """Load cloud-screened Sentinel-2 SR Harmonized scenes with indices added."""
    return (
        ee.ImageCollection(SENTINEL_2)
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud))
        .map(mask_sentinel2)
        .map(add_sentinel2_features)
    )


def load_gpm(aoi: Any, start: str, end: str) -> Any:
    """Load GPM IMERG V07 half-hourly data and aggregate to daily mm totals."""
    raw = (
        ee.ImageCollection(GPM)
        .filterBounds(aoi)
        .filterDate(start, end)
        .select("precipitation")
    )
    return daily_gpm_precipitation(raw, start, end)


# Explicit aliases keep old scripts working while using the corrected loaders.
load_sentinel1_collection = load_sentinel1
load_modis = load_modis_lst
load_landsat_collection = load_landsat
load_rainfall = load_gpm
