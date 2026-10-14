"""Validated evidence schemas. Reported and harmonized values are kept side by side."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExtractionMethod(StrEnum):
    DIRECT_TABLE = "direct_table"
    MANUAL_TRANSCRIPTION = "manual_transcription"
    COMPUTED_FROM_REPORTED = "computed_from_reported"
    FIGURE_DIGITIZED = "figure_digitized"
    USER_DATASET = "user_dataset"
    SYNTHETIC = "synthetic"


class ReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    REJECTED = "rejected"


class Provenance(BaseModel):
    """Traceable origin and review information for a single extracted value."""

    model_config = ConfigDict(extra="forbid")
    source_id: str
    citation: str | None = None
    source_url: str | None = None
    publication_id: str | None = None
    locator: str | None = None
    extraction_method: ExtractionMethod
    source_date: date | None = None
    license_or_access_terms: str | None = None
    verified: bool = False
    verification_note: str | None = None
    extraction_confidence: float | None = Field(default=None, ge=0, le=1)
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED
    reviewer_note: str | None = None


class Study(BaseModel):
    """Publication/source-level information."""

    model_config = ConfigDict(extra="forbid")
    study_id: str
    publication_id: str | None = None
    title: str | None = None
    citation: str | None = None
    source_url: str | None = None
    publication_year: int | None = Field(default=None, ge=1800, le=2200)
    species: str | None = None
    tissue_source_reported: str | None = None
    cell_source_normalized: str | None = None
    cell_source_mapping_version: str | None = None
    donor_characteristics_reported: str | None = None
    dataset_ids: list[str] = Field(default_factory=list)
    provenance: Provenance


class Experiment(BaseModel):
    """Experimental context for a secretome collection."""

    model_config = ConfigDict(extra="forbid")
    experiment_id: str
    study_id: str
    cell_passage_reported: str | None = None
    culture_history_reported: str | None = None
    medium_reported: str | None = None
    medium_normalized: str | None = None
    medium_mapping_version: str | None = None
    supplements_reported: str | None = None
    conditioning_duration_reported: str | None = None
    conditioning_duration_hours: float | None = Field(default=None, gt=0)
    licensing_reported: str | None = None
    licensing_normalized: str | None = None
    cytokines_reported: str | None = None
    cell_density_reported: str | None = None
    viability_reported: str | None = None
    collection_protocol_reported: str | None = None
    design: str | None = None
    provenance: Provenance


class BiologicalSample(BaseModel):
    """A biological replicate or condition-level aggregate; not a technical repeat."""

    model_config = ConfigDict(extra="forbid")
    sample_id: str
    experiment_id: str
    biological_unit_id: str | None = None
    replicate_type: Literal["biological", "technical"] = "biological"
    group: str | None = None
    paired_block: str | None = None
    condition_reported: str | None = None
    condition_normalized: str | None = None
    covariates: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance

    @model_validator(mode="after")
    def require_unit_for_biological(self) -> "BiologicalSample":
        if self.replicate_type == "biological" and not self.biological_unit_id:
            raise ValueError("biological_unit_id is required for biological replicates")
        return self


class Assay(BaseModel):
    """Measurement method and analyte identity."""

    model_config = ConfigDict(extra="forbid")
    assay_id: str
    assay_type_reported: str
    assay_family: str | None = None
    analyte_reported: str
    analyte_normalized: str | None = None
    analyte_class: Literal["secreted_protein", "transcript", "intracellular_protein", "lipid", "other"] = "secreted_protein"
    specimen_type: str = "conditioned_medium"
    normalization_method_reported: str | None = None
    detection_limit_reported: str | None = None
    provenance: Provenance


class Measurement(BaseModel):
    """A result record. `value_reported` and `unit_reported` are never overwritten."""

    model_config = ConfigDict(extra="forbid")
    measurement_id: str
    study_id: str
    experiment_id: str
    sample_id: str | None = None
    assay_id: str
    value_reported: float | None = None
    unit_reported: str | None = None
    result_kind: Literal["individual", "summary"] = "individual"
    reported_mean: float | None = None
    reported_sd: float | None = Field(default=None, ge=0)
    reported_se: float | None = Field(default=None, ge=0)
    sample_size_reported: int | None = Field(default=None, ge=1)
    value_normalized: float | None = None
    unit_normalized: str | None = None
    normalization_note: str | None = None
    original_text: str | None = None
    provenance: Provenance

    @model_validator(mode="after")
    def validate_value_kind(self) -> "Measurement":
        if self.result_kind == "individual" and self.value_reported is None:
            raise ValueError("individual measurements require value_reported")
        if self.result_kind == "summary" and self.reported_mean is None:
            raise ValueError("summary results require reported_mean")
        return self


class EvidenceBundle(BaseModel):
    """Complete relational evidence bundle with cross-record reference checks."""

    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0.0"
    studies: list[Study]
    experiments: list[Experiment]
    samples: list[BiologicalSample]
    assays: list[Assay]
    measurements: list[Measurement]

    @model_validator(mode="after")
    def validate_references(self) -> "EvidenceBundle":
        id_fields = {"studies": "study_id", "experiments": "experiment_id", "samples": "sample_id",
                     "assays": "assay_id", "measurements": "measurement_id"}
        for collection, field in id_fields.items():
            ids = [getattr(record, field) for record in getattr(self, collection)]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate identifiers in {collection}: {field} must be unique")
        study_ids = {x.study_id for x in self.studies}
        experiment_ids = {x.experiment_id for x in self.experiments}
        sample_ids = {x.sample_id for x in self.samples}
        assay_ids = {x.assay_id for x in self.assays}
        for exp in self.experiments:
            if exp.study_id not in study_ids:
                raise ValueError(f"Experiment references unknown study_id {exp.study_id!r}")
        for sample in self.samples:
            if sample.experiment_id not in experiment_ids:
                raise ValueError(f"Sample references unknown experiment_id {sample.experiment_id!r}")
        for row in self.measurements:
            if row.study_id not in study_ids or row.experiment_id not in experiment_ids:
                raise ValueError("Measurement references unknown study or experiment")
            exp = next(x for x in self.experiments if x.experiment_id == row.experiment_id)
            if exp.study_id != row.study_id:
                raise ValueError("Measurement study_id does not match its experiment's study_id")
            if row.sample_id is not None and row.sample_id not in sample_ids:
                raise ValueError(f"Measurement references unknown sample_id {row.sample_id!r}")
            if row.sample_id is not None:
                sample = next(x for x in self.samples if x.sample_id == row.sample_id)
                if sample.experiment_id != row.experiment_id:
                    raise ValueError("Measurement sample_id does not match its experiment_id")
            if row.assay_id not in assay_ids:
                raise ValueError(f"Measurement references unknown assay_id {row.assay_id!r}")
        return self


class AnalysisSettings(BaseModel):
    """Validated analysis choices recorded in an analysis configuration."""

    model_config = ConfigDict(extra="forbid")
    within_experiment_test: Literal["welch", "paired_t"] = "welch"
    technical_replicates: Literal["average within biological_unit_id before inference"] = "average within biological_unit_id before inference"
    cross_study_pooling: Literal[False] = False
    unit_conversion: Literal["explicit secreted-protein concentration conversions only"] = "explicit secreted-protein concentration conversions only"


class AnalysisConfig(BaseModel):
    """Validated manifest for one local evidence bundle run."""

    model_config = ConfigDict(extra="forbid")
    input_bundle: str
    output_dir: str = "results"
    label: str = "user-provided evidence"
    analysis: AnalysisSettings = AnalysisSettings()
