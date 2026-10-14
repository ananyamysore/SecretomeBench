"""User-controlled evidence ingestion from JSON bundles and relational CSV files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import EvidenceBundle


def load_bundle(path: str | Path) -> EvidenceBundle:
    """Load and validate a JSON EvidenceBundle; input values are not transformed."""
    return EvidenceBundle.model_validate_json(Path(path).read_text(encoding="utf-8"))


def load_csv_table(path: str | Path) -> pd.DataFrame:
    """Load a CSV/TSV table while preserving original string fields and missingness."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    return pd.read_csv(path, sep="\t" if path.suffix.lower() in {".tsv", ".txt"} else ",")


def write_bundle(bundle: EvidenceBundle, path: str | Path) -> None:
    """Write a validated bundle as transparent, indented JSON."""
    Path(path).write_text(bundle.model_dump_json(indent=2) + "\n", encoding="utf-8")


def import_measurements(path: str | Path) -> pd.DataFrame:
    """Import an evidence table and require provenance-bearing columns."""
    frame = load_csv_table(path)
    required = {"study_id", "experiment_id", "assay_id", "value_reported", "unit_reported", "source_id", "extraction_method"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Evidence table is missing required columns: {sorted(missing)}")
    return frame


def write_json_table(frame: pd.DataFrame, path: str | Path) -> None:
    """Write a table in JSON records format for lossless-ish review workflows."""
    frame.to_json(path, orient="records", indent=2, force_ascii=False)
