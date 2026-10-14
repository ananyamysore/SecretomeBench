"""Deterministic synthetic secretome evidence fixtures for software validation only."""

from __future__ import annotations

from datetime import date

from .schema import (Assay, BiologicalSample, EvidenceBundle, Experiment, ExtractionMethod,
                     Measurement, Provenance, Study)


def _prov(record_id: str, locator: str = "synthetic fixture") -> Provenance:
    return Provenance(source_id=f"SYNTH-{record_id}", citation="Synthetic test fixture; not a publication",
                      locator=locator, extraction_method=ExtractionMethod.SYNTHETIC,
                      source_date=date(2026, 1, 1), license_or_access_terms="Synthetic generated fixture; no external source or license claim",
                      verified=False, verification_note="Synthetic record; no external source", extraction_confidence=1.0)


def make_synthetic_bundle() -> EvidenceBundle:
    """Generate unit-equivalent, assay-incompatible, missing, technical, and contradictory records."""
    studies = [
        Study(study_id="synthetic_study_A", publication_id="SYN-001", title="Synthetic example A",
              tissue_source_reported="BM MSC", cell_source_normalized="bone_marrow", publication_year=2026,
              provenance=_prov("study-a")),
        Study(study_id="synthetic_study_B", publication_id="SYN-002", title="Synthetic example B",
              tissue_source_reported="adipose MSC", cell_source_normalized="adipose", publication_year=2026,
              provenance=_prov("study-b")),
    ]
    experiments = [
        Experiment(experiment_id="exp_A", study_id="synthetic_study_A", cell_passage_reported="P4",
                   medium_reported="alpha-MEM", medium_normalized="alpha_mem", conditioning_duration_reported="24 h",
                   conditioning_duration_hours=24, licensing_reported="IFN-γ 10 ng/mL", licensing_normalized="ifng",
                   cytokines_reported="IFN-γ 10 ng/mL", design="controlled in vitro", provenance=_prov("exp-a")),
        Experiment(experiment_id="exp_B", study_id="synthetic_study_B", medium_reported=None,
                   conditioning_duration_reported=None, licensing_reported="unlicensed", licensing_normalized="none",
                   design="controlled in vitro", provenance=_prov("exp-b")),
    ]
    assays = [
        Assay(assay_id="elisa_il6", assay_type_reported="ELISA", assay_family="elisa", analyte_reported="Interleukin-6",
              analyte_normalized="IL6", analyte_class="secreted_protein", specimen_type="conditioned_medium",
              normalization_method_reported="concentration per volume", provenance=_prov("assay-elisa")),
        Assay(assay_id="qpcr_ido", assay_type_reported="RT-qPCR", assay_family="qpcr", analyte_reported="IDO",
              analyte_normalized="IDO1", analyte_class="transcript", specimen_type="cell_lysate",
              normalization_method_reported="relative expression; housekeeping normalized", provenance=_prov("assay-qpcr")),
    ]
    samples = []; measurements = []
    study_values = {"exp_A": {"control": [100, 110, 90], "licensed": [200, 210, 190]},
                    "exp_B": {"control": [0.16, 0.15, 0.17], "licensed": [0.10, 0.09, 0.11]}}
    study_ids = {"exp_A": "synthetic_study_A", "exp_B": "synthetic_study_B"}
    for exp_id, groups in study_values.items():
        for group, vals in groups.items():
            for i, value in enumerate(vals):
                unit_id = f"{exp_id}_{group}_{i+1}"
                sample_id = f"sample_{unit_id}"
                samples.append(BiologicalSample(sample_id=sample_id, experiment_id=exp_id,
                    biological_unit_id=unit_id, group=group, condition_reported=group,
                    condition_normalized=group, provenance=_prov(sample_id)))
                unit = "pg/mL" if exp_id == "exp_A" else "ng/mL"
                measurements.append(Measurement(measurement_id=f"il6_{unit_id}", study_id=study_ids[exp_id],
                    experiment_id=exp_id, sample_id=sample_id, assay_id="elisa_il6", value_reported=float(value),
                    unit_reported=unit, original_text=f"{value} {unit}", provenance=_prov(f"il6-{unit_id}", "synthetic table")))
                # A technical replicate shares the independent biological unit and must not inflate n.
                if i == 0:
                    tech_id = f"technical_{unit_id}"
                    samples.append(BiologicalSample(sample_id=tech_id, experiment_id=exp_id,
                        biological_unit_id=unit_id, replicate_type="technical", group=group,
                        provenance=_prov(tech_id)))
                    measurements.append(Measurement(measurement_id=f"il6_{tech_id}", study_id=study_ids[exp_id],
                        experiment_id=exp_id, sample_id=tech_id, assay_id="elisa_il6", value_reported=float(value * 1.02),
                        unit_reported=unit, original_text=f"technical repeat {value * 1.02} {unit}", provenance=_prov(f"il6-{tech_id}")))
    # qPCR is deliberately incompatible with extracellular protein concentrations.
    for i, (sample, value) in enumerate(zip([s for s in samples if s.replicate_type == "biological"], [1.0, 1.2, 1.1, 2.0, 2.1, 1.9] * 2)):
        measurements.append(Measurement(measurement_id=f"ido_{i}", study_id=study_ids[sample.experiment_id],
            experiment_id=sample.experiment_id, sample_id=sample.sample_id, assay_id="qpcr_ido",
            value_reported=value, unit_reported="2^-ΔΔCt", original_text=f"relative expression {value}",
            provenance=_prov(f"ido-{i}")))
    # A reported mean without n/uncertainty illustrates irrecoverable uncertainty.
    measurements.append(Measurement(measurement_id="summary_without_uncertainty", study_id="synthetic_study_B",
        experiment_id="exp_B", assay_id="elisa_il6", result_kind="summary", reported_mean=0.13,
        unit_reported="ng/mL", original_text="mean 0.13 ng/mL", provenance=_prov("summary", "synthetic supplement table")))
    return EvidenceBundle(studies=studies, experiments=experiments, samples=samples, assays=assays,
                          measurements=measurements)
