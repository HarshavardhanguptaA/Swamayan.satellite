"""Manual Earth Engine integration check for the MODIS LST loader."""

import os

import ee

from gee.auth import initialize_earth_engine
from gee.modis import load_modis_lst


if __name__ == "__main__":
    initialize_earth_engine(os.getenv("EE_PROJECT_ID", ""))
    aoi = ee.Geometry.Point([77.6, 12.9]).buffer(5000)
    collection = load_modis_lst(aoi, "2025-01-01", "2025-02-01")
    print("MODIS composite count:", collection.size().getInfo())
    image = collection.first()
    print("Derived bands:", image.select(["LST_Day_C", "LST_Night_C"]).bandNames().getInfo())
