"""Reusable quality masking and scaling entry points for supported collections."""

from gee.indices import mask_sentinel2
from gee.landsat import mask_landsat_c2, apply_landsat_scale_factors


def prepare_sentinel2_image(image):
    """Apply Sentinel-2 scene-classification masking before index calculation."""
    return mask_sentinel2(image)


def prepare_landsat_image(image):
    """Apply Landsat Collection 2 QA masking and scale/derive feature bands."""
    return apply_landsat_scale_factors(mask_landsat_c2(image))


__all__ = ["prepare_sentinel2_image", "prepare_landsat_image"]
