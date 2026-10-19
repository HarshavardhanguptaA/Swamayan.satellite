"""Simple, guarded fusion diagnostics retained for backwards compatibility."""

import math


def fusion_readiness(correlation, stability_x, stability_y):
    if correlation is None or not math.isfinite(float(correlation)):
        return {"redundancy_score": math.nan, "complementarity_score": math.nan, "fusion_stability": math.nan}
    redundancy = min(1.0, abs(float(correlation)))
    cvs = [entry.get("cv") for entry in (stability_x, stability_y) if isinstance(entry, dict)]
    cvs = [abs(float(value)) for value in cvs if value is not None and math.isfinite(float(value))]
    # A finite, non-zero denominator avoids division-by-zero for constant features.
    denominator = sum(cvs)
    stability = 1.0 / denominator if denominator > 1e-12 else math.nan
    return {
        "redundancy_score": redundancy,
        "complementarity_score": 1.0 - redundancy,
        "fusion_stability": stability,
    }
