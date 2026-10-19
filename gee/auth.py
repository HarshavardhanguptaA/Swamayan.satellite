"""Earth Engine initialization with actionable authentication errors."""

from __future__ import annotations

from typing import Any

import ee


def initialize_earth_engine(project_id: str | None = None) -> Any:
    """Initialize Earth Engine using the provided Cloud project.

    Authentication is intentionally not launched from inside Streamlit. Run
    ``earthengine authenticate`` once in the terminal, then set the
    EE_PROJECT_ID environment variable to a registered Google Cloud project.
    """
    import os
    from config.constants import GEE_PROJECT_ID

    project = (project_id or os.getenv("EE_PROJECT_ID", "") or GEE_PROJECT_ID).strip()
    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
    except Exception as exc:
        raise RuntimeError(
            "Google Earth Engine could not be initialized. Run `earthengine authenticate` "
            "in your terminal and ensure the EE_PROJECT_ID environment variable is set to "
            f"a registered Google Cloud project. Original error: {exc}"
        ) from exc
    return ee

