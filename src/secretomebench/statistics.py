"""Statistics with assay and biological-unit guardrails."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import t as student_t, ttest_ind, ttest_rel
from statsmodels.stats.multitest import multipletests

from .assays import compare_assays
from .normalization import convert_concentration
from .schema import EvidenceBundle


def _measurement_frame(bundle: EvidenceBundle) -> pd.DataFrame:
    """Join relational records while preserving original reported values and provenance fields."""
    rows = []
    samples = {s.sample_id: s for s in bundle.samples}
    experiments = {e.experiment_id: e for e in bundle.experiments}
    assays = {a.assay_id: a for a in bundle.assays}
    for m in bundle.measurements:
        s = samples.get(m.sample_id) if m.sample_id else None
        e = experiments[m.experiment_id]; a = assays[m.assay_id]
        rows.append({"measurement_id": m.measurement_id, "study_id": m.study_id, "experiment_id": m.experiment_id,
                     "sample_id": m.sample_id, "biological_unit_id": s.biological_unit_id if s else None,
                     "replicate_type": s.replicate_type if s else "condition_summary", "group": s.group if s else None,
                     "paired_block": s.paired_block if s else None, "assay_id": a.assay_id,
                     "assay_type": a.assay_type_reported, "assay_family": a.assay_family,
                     "analyte": a.analyte_normalized or a.analyte_reported,
                     "analyte_class": a.analyte_class, "specimen_type": a.specimen_type,
                     "normalization": a.normalization_method_reported, "value_reported": m.value_reported,
                     "unit_reported": m.unit_reported, "result_kind": m.result_kind,
                     "reported_mean": m.reported_mean, "reported_sd": m.reported_sd,
                     "reported_se": m.reported_se, "sample_size_reported": m.sample_size_reported,
                     "value_normalized": m.value_normalized, "unit_normalized": m.unit_normalized,
                     "medium": e.medium_normalized or e.medium_reported,
                     "conditioning_duration_hours": e.conditioning_duration_hours,
                     "licensing": e.licensing_normalized or e.licensing_reported,
                     "source_id": m.provenance.source_id, "locator": m.provenance.locator,
                     "extraction_method": m.provenance.extraction_method.value,
                     "review_status": m.provenance.review_status.value})
    return pd.DataFrame(rows)


def compare_groups(bundle: EvidenceBundle, *, experiment_id: str, assay_id: str,
                   group_a: str, group_b: str, paired: bool = False) -> dict[str, object]:
    """Compare groups within one controlled experiment and assay after technical replicate aggregation.

    Cross-study comparisons are intentionally not inferred here. Technical repeats are averaged
    within biological unit before testing. Requires individual observations and biological units.
    """
    rows = _measurement_frame(bundle)
    rows = rows[(rows.experiment_id == experiment_id) & (rows.assay_id == assay_id)]
    rows = rows[(rows.result_kind == "individual") & rows.sample_id.notna() & rows.group.notna()].copy()
    assay = next(a for a in bundle.assays if a.assay_id == assay_id)
    if rows.empty:
        return {"status": "not_estimable", "reason": "No measurements for requested experiment and assay"}
    if rows.biological_unit_id.isna().any():
        return {"status": "not_estimable", "reason": "Individual sample-level values and biological units are required"}
    rows = rows[rows.group.isin([group_a, group_b])].copy()
    if assay.analyte_class == "secreted_protein" and assay.specimen_type == "conditioned_medium":
        converted = rows.apply(lambda r: convert_concentration(float(r.value_reported), str(r.unit_reported),
                             analyte_class=assay.analyte_class, specimen_type=assay.specimen_type), axis=1)
        rows["value"] = [x[0] for x in converted]
    else:
        units = rows.unit_reported.dropna().unique()
        if len(units) != 1:
            return {"status": "not_comparable", "reason": "Non-concentration values with differing units"}
        rows["value"] = rows.value_normalized.fillna(rows.value_reported)
    if rows.value.isna().any():
        return {"status": "not_estimable", "reason": "Missing individual values"}
    # Collapse technical measurements from the same unit and group.
    bio = rows.groupby(["biological_unit_id", "group"], as_index=False, dropna=False).value.mean()
    a = bio.loc[bio.group == group_a, "value"].to_numpy(float)
    b = bio.loc[bio.group == group_b, "value"].to_numpy(float)
    if paired:
        paired_rows = bio.pivot(index="biological_unit_id", columns="group", values="value").dropna(subset=[group_a, group_b])
        if len(paired_rows) < 2:
            return {"status": "not_estimable", "reason": "Paired comparison requires >=2 paired biological units"}
        a = paired_rows[group_a].to_numpy(float); b = paired_rows[group_b].to_numpy(float)
        differences = a - b
        stat, p = ttest_rel(a, b)
        se = float(np.std(differences, ddof=1) / np.sqrt(len(differences)))
        df = len(differences) - 1
        design = "paired within-experiment t-test"
    else:
        if len(a) < 2 or len(b) < 2:
            return {"status": "not_estimable", "reason": "Welch comparison requires >=2 biological units per group"}
        stat, p = ttest_ind(a, b, equal_var=False)
        var_a = float(np.var(a, ddof=1)); var_b = float(np.var(b, ddof=1))
        se = float(np.sqrt(var_a / len(a) + var_b / len(b)))
        numerator = (var_a / len(a) + var_b / len(b)) ** 2
        denominator = ((var_a / len(a)) ** 2 / (len(a) - 1) + (var_b / len(b)) ** 2 / (len(b) - 1))
        df = float(numerator / denominator) if denominator > 0 else len(a) + len(b) - 2
        design = "Welch two-sample t-test within experiment"
    diff = float(np.mean(a) - np.mean(b))
    critical = float(student_t.ppf(.975, df))
    return {"status": "computed", "design": design, "n_biological_a": len(a), "n_biological_b": len(b),
            "mean_a": float(np.mean(a)), "mean_b": float(np.mean(b)), "difference_a_minus_b": diff,
            "standard_error_difference": se, "ci_lower": diff - critical * se, "ci_upper": diff + critical * se,
            "degrees_freedom": float(df), "t_statistic": float(stat), "p_value": float(p),
            "unit": "pg/mL" if assay.analyte_class == "secreted_protein" and assay.specimen_type == "conditioned_medium" else str(rows.unit_reported.iloc[0]),
            "assay_id": assay_id, "interpretation": "within-experiment association; not a general treatment effect"}


def adjust_p_values(p_values: list[float], *, method: str = "fdr_bh") -> np.ndarray:
    """Adjust a declared family of tests; callers define the family."""
    if method not in {"fdr_bh", "holm", "bonferroni"}:
        raise ValueError("method must be fdr_bh, holm, or bonferroni")
    if not p_values:
        return np.array([], dtype=float)
    return multipletests(p_values, method=method)[1]


def compare_assay_records(bundle: EvidenceBundle, assay_a: str, assay_b: str) -> dict[str, object]:
    """Expose the reason two assay definitions can or cannot share a quantitative stratum."""
    assays = {a.assay_id: a for a in bundle.assays}
    result = compare_assays(assays[assay_a], assays[assay_b])
    return {"assay_a": assay_a, "assay_b": assay_b, "comparable": result.comparable, "reasons": list(result.reasons)}
