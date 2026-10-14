"""CLI for validation, synthetic demonstration, schema export, and review edits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ingestion import load_bundle, write_bundle
from .pipeline import run_bundle, run_config
from .provenance import update_review
from .schema import AnalysisConfig, EvidenceBundle, ReviewStatus
from .synthetic import make_synthetic_bundle


def main() -> None:
    """Execute the SecretomeBench command-line workflow."""
    parser = argparse.ArgumentParser(prog="secretomebench")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Validate a JSON evidence bundle")
    validate.add_argument("bundle")
    analyze = sub.add_parser("analyze", help="Run a local evidence analysis and export tables")
    analyze.add_argument("bundle"); analyze.add_argument("--out", default="results")
    configured = sub.add_parser("run", help="Run a schema-validated analysis configuration")
    configured.add_argument("config")
    demo = sub.add_parser("synthetic", help="Run offline synthetic evidence example")
    demo.add_argument("--out", default="results/synthetic")
    schema = sub.add_parser("schema", help="Export JSON Schemas for evidence and analysis config")
    schema.add_argument("--out", default="docs/schema-v1.json")
    review = sub.add_parser("review", help="Change review status while preserving source content")
    review.add_argument("bundle"); review.add_argument("record_id")
    review.add_argument("status", choices=[x.value for x in ReviewStatus]); review.add_argument("--note")
    review.add_argument("--correct", action="append", default=[], metavar="FIELD=JSON_VALUE",
                        help="Correct a normalized field while retaining the reported source field")
    review.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "validate":
        bundle = load_bundle(args.bundle)
        print(json.dumps({"valid": True, "studies": len(bundle.studies), "experiments": len(bundle.experiments),
                          "samples": len(bundle.samples), "assays": len(bundle.assays),
                          "measurements": len(bundle.measurements)}, indent=2))
    elif args.command == "analyze":
        bundle = load_bundle(args.bundle)
        run_bundle(bundle, args.out, label="user-provided evidence", config={"mode": "analyze", "bundle": args.bundle}, inputs=[args.bundle])
    elif args.command == "run":
        run_config(args.config)
    elif args.command == "synthetic":
        bundle = make_synthetic_bundle()
        run_bundle(bundle, args.out, label="synthetic software demonstration", config={"mode": "synthetic"})
    elif args.command == "schema":
        target = Path(args.out); target.parent.mkdir(parents=True, exist_ok=True)
        schema_doc = {"schema_version": "1.0.0", "evidence_bundle": EvidenceBundle.model_json_schema(),
                      "analysis_config": AnalysisConfig.model_json_schema()}
        target.write_text(json.dumps(schema_doc, indent=2) + "\n", encoding="utf-8")
    elif args.command == "review":
        bundle = load_bundle(args.bundle)
        corrections = {}
        for item in args.correct:
            field, separator, value = item.partition("=")
            if not separator: parser.error("--correct must use FIELD=JSON_VALUE")
            corrections[field] = json.loads(value)
        edited = update_review(bundle, record_id=args.record_id, status=ReviewStatus(args.status),
                               note=args.note, corrections=corrections)
        write_bundle(edited, args.out)


if __name__ == "__main__":
    main()
