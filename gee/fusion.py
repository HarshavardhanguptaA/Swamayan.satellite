"""Feature-level fusion compatibility exports.

Fusion is performed after extracting region-level feature time series; this
module intentionally does not combine satellite pixels in Earth Engine.
"""

from analytics.fusion import build_feature_level_fusion

__all__ = ["build_feature_level_fusion"]
