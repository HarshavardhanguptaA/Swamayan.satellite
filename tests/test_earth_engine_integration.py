"""Offline pipeline smoke tests; real Earth Engine integration is opt-in."""

import os
import pytest


@pytest.mark.skipif(os.getenv("SWAYAMYAN_RUN_EE_INTEGRATION") != "1",
                    reason="Set SWAYAMYAN_RUN_EE_INTEGRATION=1 after Earth Engine authentication.")
def test_earth_engine_initialization():
    from gee.auth import initialize_earth_engine
    project = os.getenv("EE_PROJECT_ID", "")
    initialize_earth_engine(project)
