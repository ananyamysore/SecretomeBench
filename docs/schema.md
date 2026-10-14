# Versioned evidence schema

The validated JSON models are `EvidenceBundle` and `AnalysisConfig` in `src/secretomebench/schema.py`. The current version is 1.0.0 (`configs/schema_version.json`). Generate their complete JSON Schemas with:

```bash
secretomebench schema --out docs/schema-v1.json
```

`AnalysisConfig` is a Pydantic-validated manifest; the example is `configs/analysis.json`. Its paths resolve relative to the config file.

Entities are `Study` (publication/source), `Experiment`, `BiologicalSample`, `Assay`, and `Measurement`; every entity requires a provenance object. Referential integrity is checked across the bundle. Biological samples require an independent `biological_unit_id`; technical repeats link to the same unit. Individual values and condition-level summaries are distinct result kinds. Original value, unit, text, and source locator remain available when a separate normalized value is added. See [`data_dictionary.csv`](data_dictionary.csv) for field definitions.

Evidence bundle JSON is intended for local, version-controlled review. For very large matrices, retain them in separate licensed source files and record their identifiers, checksums, and processing history rather than embedding them in this bundle.
