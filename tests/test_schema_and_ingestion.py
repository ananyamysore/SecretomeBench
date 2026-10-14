import pytest
from pydantic import ValidationError

from secretomebench.provenance import duplicate_publication_records, update_review
from secretomebench.schema import EvidenceBundle, ReviewStatus, Study
from secretomebench.synthetic import make_synthetic_bundle


def test_synthetic_bundle_validates_and_retains_raw_fields():
    bundle = make_synthetic_bundle()
    row = next(x for x in bundle.measurements if x.measurement_id == "il6_exp_A_control_1")
    assert row.value_reported == 100
    assert row.unit_reported == "pg/mL"
    assert row.provenance.source_id.startswith("SYNTH-")


def test_missing_biological_unit_rejected():
    with pytest.raises(ValidationError):
        from secretomebench.schema import BiologicalSample
        BiologicalSample(sample_id="x", experiment_id="e", replicate_type="biological",
                         provenance=make_synthetic_bundle().studies[0].provenance)


def test_review_workflow_preserves_source_fields():
    bundle = make_synthetic_bundle()
    reviewed = update_review(bundle, record_id="summary_without_uncertainty", status=ReviewStatus.CONFIRMED,
                             note="Checked synthetic row")
    row = next(x for x in reviewed.measurements if x.measurement_id == "summary_without_uncertainty")
    assert row.provenance.review_status == ReviewStatus.CONFIRMED
    assert row.reported_mean == .13 and row.reported_sd is None


def test_review_correction_changes_normalized_field_not_source_value():
    bundle = make_synthetic_bundle()
    edited = update_review(bundle, record_id="il6_exp_A_control_1", status=ReviewStatus.CORRECTED,
                           corrections={"value_normalized": 101.0, "unit_normalized": "pg/mL"})
    row = next(x for x in edited.measurements if x.measurement_id == "il6_exp_A_control_1")
    assert row.value_reported == 100 and row.unit_reported == "pg/mL"
    assert row.value_normalized == 101
    with pytest.raises(ValueError, match="normalized field"):
        update_review(bundle, record_id="il6_exp_A_control_1", status=ReviewStatus.CORRECTED,
                      corrections={"value_reported": 999})


def test_duplicate_publications_are_flagged_not_dropped():
    bundle = make_synthetic_bundle()
    duplicate = Study(study_id="second_record", publication_id="SYN-001", title="Additional table record",
                      provenance=bundle.studies[0].provenance)
    candidate = bundle.model_copy(update={"studies": [*bundle.studies, duplicate]})
    report = duplicate_publication_records(candidate)
    assert report and report[0]["study_ids"] == ["synthetic_study_A", "second_record"]
    assert len(candidate.studies) == 3
