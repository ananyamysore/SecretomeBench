import json

import pytest
from pydantic import ValidationError

from secretomebench.pipeline import run_config
from secretomebench.schema import AnalysisConfig
from secretomebench.synthetic import make_synthetic_bundle


def test_analysis_config_rejects_implicit_cross_study_pooling():
    raw = {"input_bundle": "evidence.json", "analysis": {"cross_study_pooling": True}}
    with pytest.raises(ValidationError):
        AnalysisConfig.model_validate(raw)


def test_configured_pipeline_resolves_relative_input_and_output(tmp_path):
    bundle_path = tmp_path / "evidence.json"
    bundle_path.write_text(make_synthetic_bundle().model_dump_json(), encoding="utf-8")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"input_bundle": "evidence.json", "output_dir": "out",
                                      "label": "synthetic config test"}), encoding="utf-8")
    run_config(config_path)
    assert (tmp_path / "out" / "report.json").is_file()
