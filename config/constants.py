"""Project-wide defaults for SWAYAMYAN.

Keep this module free of Earth Engine imports so the application and its
pure-Python tests can load configuration without authenticating.
"""

import os

GEE_PROJECT_ID = os.getenv("EE_PROJECT_ID", "").strip()

# Coordinates are ordered as min longitude, min latitude, max longitude,
# max latitude. This is a modest sample AOI; users can change it in the UI.
DEFAULT_AOI_BOUNDS = (77.5, 12.8, 77.7, 13.0)
DEFAULT_START_DATE = "2025-10-01"
DEFAULT_END_DATE = "2026-10-08"
DEFAULT_SCALE = 30

SENTINEL_2 = "COPERNICUS/S2_SR_HARMONIZED"
SENTINEL_1 = "COPERNICUS/S1_GRD"
MODIS_LST = "MODIS/061/MOD11A2"
LANDSAT_8 = "LANDSAT/LC08/C02/T1_L2"
LANDSAT_9 = "LANDSAT/LC09/C02/T1_L2"
GPM = "NASA/GPM_L3/IMERG_V07"

S2_SPECTRAL_BANDS = ["B2", "B3", "B4", "B8"]
S2_FEATURE_BANDS = ["NDVI", "NDWI", "EVI"]
S1_FEATURE_BANDS = ["VV", "VH"]
MODIS_FEATURE_BANDS = ["LST_Day_C", "LST_Night_C"]
LANDSAT_FEATURE_BANDS = ["NDVI", "NDWI", "EVI", "LST_C"]
GPM_FEATURE_BANDS = ["GPM_Precip_mm"]

# A view center is derived from the AOI at runtime; these are fallback values.
MAP_CENTER = [12.9, 77.6]
MAP_ZOOM = 8
