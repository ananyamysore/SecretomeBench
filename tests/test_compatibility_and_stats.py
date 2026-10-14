import pandas as pd

from secretomebench.assays import compare_assays
from secretomebench.markers import normalize_analyte
from secretomebench.normalization import convert_concentration, convert_duration, normalize_category
from secretomebench.pipeline import normalized_evidence, run_bundle
from secretomebench.statistics import compare_groups
from secretomebench.synthetic import make_synthetic_bundle


def test_equivalent_units_convert_but_only_for_secreted_protein():
    assert convert_concentration(.1, "ng/mL", analyte_class="secreted_protein",
                                 specimen_type="conditioned_medium") == (100., "pg/mL")
    import pytest
    with pytest.raises(ValueError, match="Unsupported"):
        convert_concentration(1., "ng/dL", analyte_class="secreted_protein", specimen_type="conditioned_medium")
    with pytest.raises(ValueError, match="only applies"):
        convert_concentration(1., "ng/mL", analyte_class="transcript", specimen_type="cell_lysate")
    assert convert_duration(1, "day") == (24., "hours")


def test_incompatible_assays_are_not_comparable():
    bundle = make_synthetic_bundle()
    elisa, qpcr = bundle.assays
    check = compare_assays(elisa, qpcr)
    assert not check.comparable
    assert "different_assay_family" in check.reasons
    assert "different_analyte_class" in check.reasons


def test_aliases_are_normalized_without_mixing_assay_types():
    assert normalize_analyte("Interleukin 6") == "IL6"
    assert normalize_analyte("indoleamine 2,3-dioxygenase") == "IDO1"
    assert normalize_category("BM", "cell_source") == "bone_marrow"
    assert normalize_category("unlisted medium", "medium").startswith("unmapped:")


def test_technical_replicates_collapse_to_biological_units():
    bundle = make_synthetic_bundle()
    result = compare_groups(bundle, experiment_id="exp_A", assay_id="elisa_il6",
                            group_a="licensed", group_b="control")
    assert result["status"] == "computed"
    assert result["n_biological_a"] == 3
    assert result["n_biological_b"] == 3
    assert result["unit"] == "pg/mL"
    assert result["ci_lower"] < result["difference_a_minus_b"] < result["ci_upper"]


def test_missingness_and_conflicting_study_directions_are_visible():
    bundle = make_synthetic_bundle()
    evidence = normalized_evidence(bundle)
    assert evidence.loc[evidence.experiment_id == "exp_B", "conditioning_duration_hours"].isna().all()
    a = evidence[(evidence.experiment_id == "exp_A") & (evidence.assay_id == "elisa_il6") & (evidence.group == "licensed")].value_normalized.mean()
    b = evidence[(evidence.experiment_id == "exp_B") & (evidence.assay_id == "elisa_il6") & (evidence.group == "licensed")].value_normalized.mean()
    assert a > 150 and b < 150  # synthetic contradiction in a common unit, not a pooled estimate


def test_pipeline_outputs_provenance_and_not_pooled_cross_study_results(tmp_path):
    bundle = make_synthetic_bundle()
    tables = run_bundle(bundle, tmp_path, label="synthetic test")
    assert {"evidence", "review_queue", "completeness", "within_experiment_comparisons", "assay_compatibility"}.issubset(tables)
    assert (tmp_path / "report.json").is_file()
    assert (tmp_path / "validated_evidence.json").is_file()
    assert (tmp_path / "run_manifest.json").is_file()
    assert tables["within_experiment_comparisons"].shape[0] == 4
    assert pd.read_csv(tmp_path / "evidence.csv").source_id.str.startswith("SYNTH-").all()
