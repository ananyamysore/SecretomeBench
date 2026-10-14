"""Explicit analyte aliases and markers; aliases do not imply biological equivalence of assays."""

from __future__ import annotations

MARKER_CATALOG_VERSION = "1.0.0"

ALIASES = {
    "il-6": "IL6", "il6": "IL6", "interleukin 6": "IL6", "interleukin-6": "IL6",
    "ido": "IDO1", "ido1": "IDO1", "indoleamine 2,3-dioxygenase": "IDO1",
    "indoleamine 2,3-dioxygenase 1": "IDO1", "ptgs2": "PTGS2", "cox-2": "PTGS2",
    "pge2": "PGE2", "tgf-beta": "TGFB1", "tgfβ": "TGFB1",
}


def normalize_analyte(reported: str) -> str:
    """Normalize a known analyte alias or retain an inspectable `unmapped:` value."""
    key = " ".join(reported.casefold().strip().split())
    return ALIASES.get(key, f"unmapped:{reported.strip()}")


def measurement_class_for_marker(marker: str) -> str:
    """Return a conservative class for known secreted factors vs enzyme transcript/protein."""
    normalized = normalize_analyte(marker)
    if normalized in {"IL6", "PGE2", "TGFB1"}: return "secreted_protein_or_lipid"
    if normalized in {"IDO1", "PTGS2"}: return "intracellular_or_transcript_marker"
    return "unknown"
