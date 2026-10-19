"""Landsat 8/9 Collection 2 Level-2 surface-reflectance and LST processing."""

import ee

from config.constants import LANDSAT_8, LANDSAT_9


def mask_landsat_c2(image):
    """Mask fill, dilated cloud, cirrus, cloud, cloud shadow and snow QA bits."""
    qa = image.select("QA_PIXEL")
    bad_bits = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5)
    return image.updateMask(qa.bitwiseAnd(bad_bits).eq(0))


def apply_landsat_scale_factors(image):
    """Apply official Collection 2 Level-2 scale factors and derive features."""
    sr = image.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5"]).multiply(0.0000275).add(-0.2)
    image = image.addBands(sr, None, True)

    blue = image.select("SR_B2")
    green = image.select("SR_B3")
    red = image.select("SR_B4")
    nir = image.select("SR_B5")
    ndvi_denominator = nir.add(red)
    ndwi_denominator = green.add(nir)
    ndvi = nir.subtract(red).divide(ndvi_denominator).updateMask(ndvi_denominator.neq(0)).rename("NDVI")
    ndwi = green.subtract(nir).divide(ndwi_denominator).updateMask(ndwi_denominator.neq(0)).rename("NDWI")
    denominator = nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
    evi = nir.subtract(red).multiply(2.5).divide(denominator).updateMask(denominator.neq(0)).rename("EVI")

    # ST_B10 is delivered as a scaled surface-temperature product in kelvin.
    lst_raw = image.select("ST_B10")
    lst_c = lst_raw.multiply(0.00341802).add(149.0).subtract(273.15).rename("LST_C")
    lst_c = lst_c.updateMask(lst_raw.gt(0))
    return (image.addBands(ndvi).addBands(ndwi).addBands(evi).addBands(lst_c)
            .copyProperties(image, ["system:time_start"]))


def load_landsat(aoi, start_date, end_date):
    """Merge Landsat 8 and 9 Level-2 scenes into a common feature collection."""
    l8 = ee.ImageCollection(LANDSAT_8).filterBounds(aoi).filterDate(start_date, end_date)
    l9 = ee.ImageCollection(LANDSAT_9).filterBounds(aoi).filterDate(start_date, end_date)
    return l8.merge(l9).map(mask_landsat_c2).map(apply_landsat_scale_factors)


# Backwards-compatible names used in early versions of this repository.
mask_landsat_l1 = mask_landsat_c2
compute_lst_from_bt = apply_landsat_scale_factors
