"""Sentinel-1 SAR collection helpers."""

import ee


def load_sentinel1(aoi, start_date, end_date, orbit_pass="DESCENDING"):
    """Load dual-polarization IW scenes; COPERNICUS/S1_GRD values are already dB.

    ``orbit_pass`` may be ``"DESCENDING"`` (default), ``"ASCENDING"``, or
    ``"BOTH"`` (no pass filter). Maintaining a consistent orbit pass is scientifically
    recommended to avoid backscatter bias from differing look angles, but
    ascending pass or fallback may be necessary for regions lacking descending coverage.
    """
    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH"])
    )
    if orbit_pass and orbit_pass.upper() in ("ASCENDING", "DESCENDING"):
        return collection.filter(ee.Filter.eq("orbitProperties_pass", orbit_pass.upper()))
    return collection


def to_db(image):
    """Compatibility shim: Sentinel-1 GRD is already calibrated and log-scaled."""
    return image.copyProperties(image, ["system:time_start", "system:index"])
