"""Conservative rules for determining measurement comparability."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import Assay


@dataclass(frozen=True)
class Comparability:
    comparable: bool
    reasons: tuple[str, ...]


def classify_assay(reported: str) -> str:
    """Map common assay labels to broad method families; unknown methods stay explicitly unknown."""
    label = reported.casefold()
    if "elisa" in label: return "elisa"
    if "western" in label or "immunoblot" in label: return "western_blot"
    if "qpcr" in label or "pcr" in label: return "qpcr"
    if "mass spec" in label or "lc-ms" in label: return "mass_spectrometry"
    if "multiplex" in label or "luminex" in label: return "multiplex_immunoassay"
    return "unknown"


def compare_assays(left: Assay, right: Assay) -> Comparability:
    """Compare measurements only when method, analyte class, specimen, and normalization align."""
    reasons = []
    family_a = left.assay_family or classify_assay(left.assay_type_reported)
    family_b = right.assay_family or classify_assay(right.assay_type_reported)
    if family_a == "unknown" or family_b == "unknown": reasons.append("unknown_assay_family")
    elif family_a != family_b: reasons.append("different_assay_family")
    if left.analyte_class != right.analyte_class: reasons.append("different_analyte_class")
    if left.specimen_type != right.specimen_type: reasons.append("different_specimen_type")
    if (left.analyte_normalized or left.analyte_reported.casefold()) != (right.analyte_normalized or right.analyte_reported.casefold()):
        reasons.append("different_analyte")
    if (left.normalization_method_reported or "") != (right.normalization_method_reported or ""):
        reasons.append("different_or_unknown_normalization")
    return Comparability(not reasons, tuple(reasons))


def assay_comparison_key(assay: Assay) -> tuple[str, str, str, str, str]:
    """Return a conservative stratum key, retaining unknown assay and normalization distinctions."""
    return (assay.assay_family or classify_assay(assay.assay_type_reported),
            assay.analyte_normalized or assay.analyte_reported.casefold(), assay.analyte_class,
            assay.specimen_type, assay.normalization_method_reported or "unspecified")
