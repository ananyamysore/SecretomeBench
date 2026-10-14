"""Traceable evidence tables and user review exports."""

from __future__ import annotations

import pandas as pd

from .schema import EvidenceBundle
from .statistics import _measurement_frame


def evidence_table(bundle: EvidenceBundle) -> pd.DataFrame:
    """Flatten measurements with design and provenance lineage; reported values remain intact."""
    return _measurement_frame(bundle)


def review_table(bundle: EvidenceBundle) -> pd.DataFrame:
    """Return the evidence fields reviewers commonly confirm or edit, retaining original text."""
    frame = evidence_table(bundle)
    preferred = ["measurement_id", "study_id", "experiment_id", "sample_id", "analyte", "value_reported",
                 "unit_reported", "value_normalized", "unit_normalized", "medium", "conditioning_duration_hours",
                 "licensing", "assay_type", "source_id", "locator", "extraction_method", "review_status"]
    return frame[[c for c in preferred if c in frame]].copy()
