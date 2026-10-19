"""MODIS MOD11A2 land-surface-temperature processing."""

import ee


def load_modis_lst(aoi, start_date, end_date):
    """Return quality-screened day/night land surface temperature in °C."""
    collection = (
        ee.ImageCollection("MODIS/061/MOD11A2")
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
    )

    def compute_lst(image):
        day_raw = image.select("LST_Day_1km")
        night_raw = image.select("LST_Night_1km")
        # MOD11A2 QC bits 0–1: retain only mandatory-QA good-quality pixels.
        day_good = image.select("QC_Day").bitwiseAnd(3).eq(0)
        night_good = image.select("QC_Night").bitwiseAnd(3).eq(0)
        day_good = day_good.And(day_raw.gte(7500)).And(day_raw.lte(65535))
        night_good = night_good.And(night_raw.gte(7500)).And(night_raw.lte(65535))

        lst_day = (
            day_raw.updateMask(day_good).multiply(0.02).subtract(273.15).rename("LST_Day_C")
        )
        lst_night = (
            night_raw.updateMask(night_good).multiply(0.02).subtract(273.15).rename("LST_Night_C")
        )
        return image.addBands(lst_day).addBands(lst_night).copyProperties(image, ["system:time_start"])

    return collection.map(compute_lst)
