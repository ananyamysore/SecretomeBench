import pytest

from secretomebench.schema import EvidenceBundle
from secretomebench.synthetic import make_synthetic_bundle


def test_unsupported_references_are_rejected():
    raw = make_synthetic_bundle().model_dump(mode="json")
    raw["measurements"][0]["assay_id"] = "missing_assay"
    with pytest.raises(ValueError, match="unknown assay_id"):
        EvidenceBundle.model_validate(raw)


def test_summary_without_sd_and_n_remains_missing():
    row = next(x for x in make_synthetic_bundle().measurements if x.result_kind == "summary")
    assert row.reported_mean is not None
    assert row.reported_sd is None
    assert row.sample_size_reported is None
