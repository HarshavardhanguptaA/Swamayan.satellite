"""Render live Google Earth Engine imagery and AOI previews in Streamlit using Folium."""

from __future__ import annotations


OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'


def build_sentinel2_folium_map(aoi, collection, bounds):
    """Create a Folium map containing real Sentinel-2 Earth Engine tiles."""
    import folium

    min_lon, min_lat, max_lon, max_lat = bounds
    center = [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]

    # Build a real satellite image composite in Earth Engine.
    composite = collection.median().clip(aoi)

    # Sentinel-2 SR reflectance is scaled by 10,000.
    vis_params = {
        "bands": ["B4", "B3", "B2"],
        "min": 0,
        "max": 3000,
        "gamma": 1.1,
    }

    # Request a real Earth Engine map tile URL.
    map_info = composite.getMapId(vis_params)
    tile_fetcher = map_info.get("tile_fetcher")
    tile_url = getattr(tile_fetcher, "url_format", None)

    if not tile_url:
        tile_url = map_info.get("urlFormat")

    if not tile_url:
        raise RuntimeError(
            "Earth Engine did not provide an imagery tile URL. "
            "Check authentication, project access and the selected dates."
        )

    # Create the interactive map without geemap using OpenStreetMap
    map_view = folium.Map(
        location=center,
        zoom_start=11,
        tiles="OpenStreetMap",
        attr=OSM_ATTRIBUTION,
        control_scale=True,
    )

    folium.TileLayer(
        tiles=tile_url,
        attr="Google Earth Engine | Copernicus Sentinel-2",
        name="Sentinel-2 true-colour imagery",
        overlay=True,
        control=True,
        show=True,
        opacity=0.95,
    ).add_to(map_view)

    # Draw the configured area of interest.
    folium.Rectangle(
        bounds=[
            [min_lat, min_lon],
            [max_lat, max_lon],
        ],
        color="#0B9188",
        weight=2.5,
        fill=True,
        fill_color="#0B9188",
        fill_opacity=0.08,
        tooltip="Area of interest",
    ).add_to(map_view)

    folium.LayerControl(collapsed=False).add_to(map_view)

    return map_view


def render_sentinel2_preview(aoi, collection, bounds, height=500):
    """Display the Earth Engine-backed Folium map inside Streamlit."""
    import streamlit as st
    import streamlit.components.v1 as components

    try:
        map_view = build_sentinel2_folium_map(aoi, collection, bounds)

        components.html(
            map_view.get_root().render(),
            height=height,
            scrolling=False,
        )
    except Exception as exc:
        st.error(f"Unable to render the Sentinel-2 preview map: {exc}")


def render_aoi_preview(bounds, height=350):
    """Render an interactive AOI boundary map using standard OpenStreetMap."""
    import folium
    import streamlit as st
    import streamlit.components.v1 as components

    min_lon, min_lat, max_lon, max_lat = bounds
    center = [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]

    try:
        map_view = folium.Map(
            location=center,
            zoom_start=10,
            tiles="OpenStreetMap",
            attr=OSM_ATTRIBUTION,
            control_scale=True,
        )

        folium.Rectangle(
            bounds=[
                [min_lat, min_lon],
                [max_lat, max_lon],
            ],
            color="#0B9188",
            weight=2.5,
            fill=True,
            fill_color="#0B9188",
            fill_opacity=0.12,
            tooltip="Area of Interest (AOI)",
        ).add_to(map_view)

        components.html(
            map_view.get_root().render(),
            height=height,
            scrolling=False,
        )
    except Exception as exc:
        st.warning(f"Unable to load interactive map preview: {exc}")
