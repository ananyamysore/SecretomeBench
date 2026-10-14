"""Missing-data and evidence completeness summaries."""

from __future__ import annotations

import pandas as pd


def field_completeness(frame: pd.DataFrame, *, fields: list[str], group_by: str | None = None) -> pd.DataFrame:
    """Report nonmissing/total counts and proportions by field, optionally by study."""
    absent = set(fields) - set(frame.columns)
    if absent:
        raise ValueError(f"Unknown fields: {sorted(absent)}")
    groups = [("all", frame)] if group_by is None else list(frame.groupby(group_by, dropna=False))
    rows = []
    for label, part in groups:
        for field in fields:
            present = int(part[field].notna().sum())
            rows.append({"group": label, "field": field, "n_total": len(part), "n_present": present,
                         "n_missing": len(part) - present,
                         "completeness_fraction": present / len(part) if len(part) else float("nan")})
    return pd.DataFrame(rows)


def measurement_completeness(measurements: pd.DataFrame) -> pd.DataFrame:
    """Summarize missing units, values, uncertainty, and sample links by study."""
    required = {"study_id", "value_reported", "unit_reported", "reported_sd", "reported_se", "sample_id"}
    if not required.issubset(measurements):
        raise ValueError(f"Missing required columns: {sorted(required - set(measurements.columns))}")
    return field_completeness(measurements, fields=sorted(required - {"study_id"}), group_by="study_id")
