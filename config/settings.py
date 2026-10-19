"""Backward-compatible aliases for configuration constants."""

from config.constants import (
    DEFAULT_AOI_BOUNDS,
    DEFAULT_END_DATE,
    DEFAULT_SCALE,
    DEFAULT_START_DATE,
    GEE_PROJECT_ID,
    MAP_CENTER,
    MAP_ZOOM,
)

__all__ = [
    "DEFAULT_AOI_BOUNDS", "DEFAULT_START_DATE", "DEFAULT_END_DATE",
    "DEFAULT_SCALE", "GEE_PROJECT_ID", "MAP_CENTER", "MAP_ZOOM",
]
