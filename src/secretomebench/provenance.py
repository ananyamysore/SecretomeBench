"""Checksums, source lineage, and review actions."""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy
import statsmodels

from . import __version__
from .schema import EvidenceBundle, ReviewStatus


def sha256_file(path: str | Path) -> str:
    """Return SHA-256 for an input file using streaming reads."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run_manifest(config: dict[str, Any], inputs: list[str | Path] | None = None) -> dict[str, Any]:
    """Create software/configuration/input provenance for a reproducible analysis run."""
    return {"created_utc": datetime.now(timezone.utc).isoformat(), "config": config,
            "software": {"secretomebench": __version__, "python": platform.python_version(),
                         "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__,
                         "statsmodels": statsmodels.__version__},
            "input_checksums": {str(p): sha256_file(p) for p in (inputs or [])}}


def write_run_manifest(manifest: dict[str, Any], path: str | Path) -> None:
    """Write a machine-readable run manifest."""
    Path(path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_review(bundle: EvidenceBundle, *, record_id: str, status: ReviewStatus,
                  note: str | None = None, corrections: dict[str, object] | None = None) -> EvidenceBundle:
    """Return a reviewed copy; corrections target normalized fields and cannot overwrite source fields."""
    dumped = bundle.model_dump(mode="json")
    found = False
    for collection in ("studies", "experiments", "samples", "assays", "measurements"):
        id_key = {"studies": "study_id", "experiments": "experiment_id", "samples": "sample_id",
                  "assays": "assay_id", "measurements": "measurement_id"}[collection]
        for record in dumped[collection]:
            if record[id_key] == record_id:
                for field, value in (corrections or {}).items():
                    if field not in record or field == "provenance" or field.endswith("_reported") or field == "original_text":
                        raise ValueError(f"Correction must target an existing normalized field, got {field!r}")
                    record[field] = value
                record["provenance"]["review_status"] = status.value
                record["provenance"]["reviewer_note"] = note
                found = True
    if not found:
        raise KeyError(f"No evidence record with ID {record_id!r}")
    return EvidenceBundle.model_validate(dumped)


def duplicate_publication_records(bundle: EvidenceBundle) -> list[dict[str, object]]:
    """Flag reused publication identifiers for human review without deleting records."""
    grouped: dict[str, list[str]] = {}
    for study in bundle.studies:
        if study.publication_id:
            grouped.setdefault(study.publication_id.casefold().strip(), []).append(study.study_id)
    return [{"publication_id": publication_id, "study_ids": ids,
             "status": "review_possible_duplicate_or_multi_record_publication"}
            for publication_id, ids in grouped.items() if len(ids) > 1]
