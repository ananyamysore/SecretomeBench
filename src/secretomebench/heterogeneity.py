"""Describe experimental heterogeneity and synthesize only compatible effects."""

from __future__ import annotations

import pandas as pd
from scipy.stats import chi2


HETEROGENEITY_FIELDS = ["cell_source_normalized", "medium_normalized", "conditioning_duration_hours",
                        "licensing_normalized", "assay_family", "analyte_class", "specimen_type",
                        "normalization_method_reported"]


def heterogeneity_profile(frame: pd.DataFrame, *, study_column: str = "study_id") -> pd.DataFrame:
    """Summarize distinct reported design values and missingness; no inferential pooling."""
    rows = []
    for field in HETEROGENEITY_FIELDS:
        if field not in frame:
            continue
        values = frame[field].dropna().astype(str)
        rows.append({"field": field, "n_observed": int(values.size), "n_missing": int(frame[field].isna().sum()),
                     "n_distinct": int(values.nunique()), "observed_values": ";".join(sorted(values.unique())),
                     "n_studies": int(frame.loc[frame[field].notna(), study_column].nunique()) if study_column in frame else None})
    return pd.DataFrame(rows)


def fixed_effect_meta_analysis(effects: pd.DataFrame, *, effect: str = "effect",
                               standard_error: str = "standard_error") -> dict[str, float | int | str]:
    """Fixed-effect inverse-variance meta-analysis for prevalidated compatible independent studies.

    This function cannot establish comparability itself; provide only same contrast, assay,
    analyte, unit, design class, and independent study estimates.
    """
    if not {effect, standard_error}.issubset(effects):
        raise ValueError("Effects table must contain effect and standard_error")
    data = effects[[effect, standard_error]].dropna()
    if len(data) < 2 or (data[standard_error] <= 0).any():
        return {"status": "not_estimable", "n_studies": len(data)}
    y = data[effect].to_numpy(float); v = data[standard_error].to_numpy(float) ** 2
    w = 1 / v; estimate = float((w * y).sum() / w.sum()); se = float((1 / w.sum()) ** .5)
    q = float((w * (y - estimate) ** 2).sum()); df = len(y) - 1
    return {"status": "computed_fixed_effect", "n_studies": len(y), "estimate": estimate,
            "standard_error": se, "ci_lower": estimate - 1.96 * se, "ci_upper": estimate + 1.96 * se,
            "cochran_q": q, "q_df": df, "q_p_value": float(chi2.sf(q, df)),
            "i_squared_percent": max(0.0, (q - df) / q) * 100 if q > 0 else 0.0}
