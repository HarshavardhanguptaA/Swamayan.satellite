"""Spectral indices for Sentinel-2 Surface Reflectance imagery."""

from typing import Any

import ee

S2_BANDS = {"BLUE": "B2", "GREEN": "B3", "RED": "B4", "NIR": "B8"}
S2_SR_SCALE = 0.0001


def mask_sentinel2(image: Any) -> Any:
    """Mask no-data, defective, cloud-shadow, cloud, cirrus and snow SCL pixels."""
    scl = image.select("SCL")
    valid = (
        scl.neq(0)
        .And(scl.neq(1))
        .And(scl.neq(3))
        .And(scl.neq(7))
        .And(scl.neq(8))
        .And(scl.neq(9))
        .And(scl.neq(10))
        .And(scl.neq(11))
    )
    return image.updateMask(valid)


def add_ndvi(image: Any) -> Any:
    ndvi = image.normalizedDifference([S2_BANDS["NIR"], S2_BANDS["RED"]]).rename("NDVI")
    return image.addBands(ndvi)


def add_ndwi(image: Any) -> Any:
    # McFeeters green-NIR NDWI; this is not the NIR-SWIR moisture index.
    ndwi = image.normalizedDifference([S2_BANDS["GREEN"], S2_BANDS["NIR"]]).rename("NDWI")
    return image.addBands(ndwi)


def add_evi(image: Any) -> Any:
    """Compute EVI using reflectance scaled to physical units (0–1)."""
    nir = image.select(S2_BANDS["NIR"]).multiply(S2_SR_SCALE)
    red = image.select(S2_BANDS["RED"]).multiply(S2_SR_SCALE)
    blue = image.select(S2_BANDS["BLUE"]).multiply(S2_SR_SCALE)
    denominator = nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
    evi = nir.subtract(red).multiply(2.5).divide(denominator).updateMask(denominator.neq(0)).rename("EVI")
    return image.addBands(evi)


def add_sentinel2_features(image: Any) -> Any:
    return add_evi(add_ndwi(add_ndvi(image)))


def compute_ndvi(collection: Any) -> Any:
    return collection.map(add_ndvi)


def compute_ndwi(collection: Any) -> Any:
    return collection.map(add_ndwi)


def compute_evi(collection: Any) -> Any:
    return collection.map(add_evi)
