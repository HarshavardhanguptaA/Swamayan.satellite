"""Earth Engine temporal aggregation utilities."""

import ee


def daily_gpm_precipitation(collection, start_date, end_date):
    """Aggregate half-hourly IMERG rates into daily precipitation totals (mm/day).

    The IMERG ``precipitation`` band is a rate in mm/hour. Each image represents
    a half-hour interval, so rate × 0.5 hours is summed to obtain daily amount.
    ``end_date`` is exclusive, following Earth Engine filterDate semantics.
    """
    start = ee.Date(start_date)
    end = ee.Date(end_date)
    number_of_days = end.difference(start, "day").ceil()
    offsets = ee.List.sequence(0, number_of_days.subtract(1))

    def make_day(offset):
        day = start.advance(ee.Number(offset), "day")
        day_images = collection.filterDate(day, day.advance(1, "day"))
        daily_total = day_images.select("precipitation").sum().multiply(0.5).rename("GPM_Precip_mm")
        return daily_total.set({
            "system:time_start": day.millis(),
            "date": day.format("YYYY-MM-dd"),
            "source_image_count": day_images.size(),
        })

    return ee.ImageCollection.fromImages(offsets.map(make_day)).filter(
        ee.Filter.gt("source_image_count", 0)
    )
