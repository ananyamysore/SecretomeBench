"""Evidence validation, harmonization, analysis, and export orchestration."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .assays import compare_assays
from .evidence import evidence_table, review_table
from .heterogeneity import heterogeneity_profile
from .missingness import field_completeness
from .normalization import convert_concentration
from .provenance import duplicate_publication_records, run_manifest, write_run_manifest
from .reporting import write_report
from .schema import EvidenceBundle
from .schema import AnalysisConfig
from .statistics import compare_groups


def normalized_evidence(bundle: EvidenceBundle) -> pd.DataFrame:
    """Add valid concentration conversions to a derived table; source evidence remains unchanged."""
    frame = evidence_table(bundle)
    for idx, row in frame.iterrows():
        if row.value_reported is not None and pd.notna(row.value_reported):
            assay = next(a for a in bundle.assays if a.assay_id == row.assay_id)
            if assay.analyte_class == "secreted_protein" and assay.specimen_type == "conditioned_medium":
                try:
                    value, unit = convert_concentration(float(row.value_reported), str(row.unit_reported),
                        analyte_class=assay.analyte_class, specimen_type=assay.specimen_type)
                    frame.loc[idx, "value_normalized"] = value
                    frame.loc[idx, "unit_normalized"] = unit
                    frame.loc[idx, "normalization_note"] = "explicit mass-concentration conversion"
                except ValueError as exc:
                    frame.loc[idx, "normalization_note"] = f"not converted: {exc}"
    return frame


def run_bundle(bundle: EvidenceBundle, output_dir: str | Path, *, label: str = "user evidence",
               config: dict[str, object] | None = None, inputs: list[str | Path] | None = None,
               paired_test: bool = False) -> dict[str, pd.DataFrame]:
    """Validate an evidence bundle, derive compatible summaries, and export traceable artifacts."""
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    evidence = normalized_evidence(bundle)
    fields = ["medium", "conditioning_duration_hours", "licensing", "value_reported", "unit_reported",
              "reported_sd", "reported_se", "sample_id", "source_id", "locator"]
    completeness = field_completeness(evidence, fields=fields, group_by="study_id")
    comparisons = []
    for assay in bundle.assays:
        groups_by_experiment: dict[str, list[str]] = {}
        for sample in bundle.samples:
            if sample.group:
                groups_by_experiment.setdefault(sample.experiment_id, [])
                if sample.group not in groups_by_experiment[sample.experiment_id]:
                    groups_by_experiment[sample.experiment_id].append(sample.group)
        for experiment_id, groups in groups_by_experiment.items():
            if len(groups) >= 2 and evidence[(evidence.experiment_id == experiment_id) & (evidence.assay_id == assay.assay_id)].shape[0]:
                result = compare_groups(bundle, experiment_id=experiment_id, assay_id=assay.assay_id,
                                        group_a=groups[0], group_b=groups[1], paired=paired_test)
                comparisons.append({"experiment_id": experiment_id, "assay_id": assay.assay_id,
                                    "group_a": groups[0], "group_b": groups[1], **result})
    compatibility = []
    for i, left in enumerate(bundle.assays):
        for right in bundle.assays[i + 1:]:
            check = compare_assays(left, right)
            compatibility.append({"assay_a": left.assay_id, "assay_b": right.assay_id,
                                  "comparable": check.comparable, "reasons": ";".join(check.reasons)})
    tables = {"evidence": evidence, "review_queue": review_table(bundle), "completeness": completeness,
              "within_experiment_comparisons": pd.DataFrame(comparisons),
              "assay_compatibility": pd.DataFrame(compatibility),
              "heterogeneity": heterogeneity_profile(evidence),
              "duplicate_publications": pd.DataFrame(duplicate_publication_records(bundle))}
    write_report(tables, output, label=label, summary={"n_studies": len(bundle.studies),
                 "n_experiments": len(bundle.experiments), "n_measurements": len(bundle.measurements)})
    bundle_path = output / "validated_evidence.json"
    bundle_path.write_text(bundle.model_dump_json(indent=2) + "\n", encoding="utf-8")
    manifest = run_manifest(config or {"mode": "bundle", "label": label}, inputs)
    write_run_manifest(manifest, output / "run_manifest.json")
    return tables


def run_config(config_path: str | Path) -> dict[str, pd.DataFrame]:
    """Validate and execute an analysis manifest; relative paths resolve from its directory."""
    config_path = Path(config_path).resolve()
    config = AnalysisConfig.model_validate_json(config_path.read_text(encoding="utf-8"))
    input_path = Path(config.input_bundle)
    if not input_path.is_absolute(): input_path = config_path.parent / input_path
    output_path = Path(config.output_dir)
    if not output_path.is_absolute(): output_path = config_path.parent / output_path
    bundle = EvidenceBundle.model_validate_json(input_path.read_text(encoding="utf-8"))
    return run_bundle(bundle, output_path, label=config.label, config=config.model_dump(mode="json"),
                      inputs=[config_path, input_path], paired_test=config.analysis.within_experiment_test == "paired_t")
