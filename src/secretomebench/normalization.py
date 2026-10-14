"""Inspectable, versioned, reversible metadata and explicit unit mappings."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


MAPPING_VERSION = "1.0.0"

# Keys are conservative normalized labels; mapping never overwrites reported fields.
CATEGORY_MAPS: dict[str, dict[str, str]] = {
    "cell_source": {"bone marrow": "bone_marrow", "bm": "bone_marrow", "adipose": "adipose",
                    "adipose tissue": "adipose", "umbilical cord": "umbilical_cord",
                    "uc": "umbilical_cord", "wharton's jelly": "whartons_jelly"},
    "medium": {"alpha-mem": "alpha_mem", "α-mem": "alpha_mem", "dmem": "dmem",
                "low glucose dmem": "dmem_low_glucose", "serum-free": "serum_free",
                "serum free": "serum_free", "x-vivo 10": "x_vivo_10"},
    "licensing": {"ifn-gamma": "ifng", "ifnγ": "ifng", "tnf-alpha": "tnfa", "tnf-α": "tnfa",
                  "unlicensed": "none", "none": "none"},
    "assay": {"elisa": "elisa", "western blot": "western_blot", "immunoblot": "western_blot",
              "qpcr": "qpcr", "rt-qpcr": "qpcr", "lc-ms/ms": "mass_spectrometry"},
}


def normalize_category(value: str | None, category: str) -> str | None:
    """Normalize known variants while preserving unknown values as explicit `unmapped:` labels."""
    if value is None or not str(value).strip():
        return None
    if category not in CATEGORY_MAPS:
        raise ValueError(f"Unknown category {category!r}; known categories: {sorted(CATEGORY_MAPS)}")
    key = " ".join(str(value).casefold().strip().split())
    return CATEGORY_MAPS[category].get(key, f"unmapped:{value.strip()}")


def harmonize_column(frame: pd.DataFrame, *, source: str, target: str, category: str,
                     version: str = MAPPING_VERSION) -> pd.DataFrame:
    """Add normalized and mapping-version columns; leave the raw source column untouched."""
    if source not in frame:
        raise ValueError(f"Missing source field {source!r}")
    out = frame.copy()
    out[target] = out[source].map(lambda value: normalize_category(value, category))
    out[f"{target}_mapping_version"] = version
    return out


def convert_duration(value: float, unit: str) -> tuple[float, str]:
    """Convert explicitly reported conditioning durations to hours."""
    factors = {"minute": 1 / 60, "minutes": 1 / 60, "min": 1 / 60, "h": 1.0,
               "hr": 1.0, "hour": 1.0, "hours": 1.0, "d": 24.0, "day": 24.0, "days": 24.0}
    key = unit.casefold().strip()
    if key not in factors:
        raise ValueError(f"Unsupported duration unit: {unit!r}")
    result = float(value) * factors[key]
    if result <= 0:
        raise ValueError("Conditioning duration must be positive")
    return result, "hours"


@dataclass(frozen=True)
class UnitConversion:
    factor_to_pg_ml: float
    unit_canonical: str = "pg/mL"


PROTEIN_CONCENTRATION_UNITS = {
    "pg/ml": UnitConversion(1.0), "pg/mL": UnitConversion(1.0),
    "ng/ml": UnitConversion(1_000.0), "ng/mL": UnitConversion(1_000.0),
    "ug/ml": UnitConversion(1_000_000.0), "µg/mL": UnitConversion(1_000_000.0),
    "μg/mL": UnitConversion(1_000_000.0),
}


def convert_concentration(value: float, unit: str, *, analyte_class: str,
                          specimen_type: str) -> tuple[float, str]:
    """Convert mass concentration to pg/mL only for extracellular protein concentrations.

    Does not convert qPCR, densitometry, intracellular expression, or normalized values.
    """
    if analyte_class != "secreted_protein" or specimen_type != "conditioned_medium":
        raise ValueError("Concentration conversion only applies to secreted protein in conditioned medium")
    try:
        conversion = PROTEIN_CONCENTRATION_UNITS[unit]
    except KeyError as exc:
        raise ValueError(f"Unsupported or ambiguous concentration unit: {unit!r}") from exc
    return float(value) * conversion.factor_to_pg_ml, conversion.unit_canonical
