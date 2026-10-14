# SecretomeBench

SecretomeBench is a local, CPU-only Python toolkit for structured evidence extraction and cautious quantitative comparison of mesenchymal stromal cell (MSC) secretome studies. It keeps source-reported fields separate from normalized analysis fields and refuses to treat shared marker names as proof that different assay outputs are comparable.

This release ships no real papers or molecular datasets and makes no claim that any formulation is superior. Synthetic data are used only to test software behavior.

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e '.[test,dev]'
```

## Generate and analyze the synthetic evidence example

```bash
python examples/generate_synthetic.py
secretomebench validate examples/synthetic_evidence_generated.json
secretomebench analyze examples/synthetic_evidence_generated.json --out results/synthetic
secretomebench run configs/analysis.json
```

Or run the entire deterministic example directly:

```bash
secretomebench synthetic --out results/synthetic
```

`examples/synthetic_evidence.json` is a small inspectable fixture. The generator expands it into the broader deterministic validation fixture. Outputs include a validated evidence JSON bundle, traceable evidence and review CSVs, field completeness, assay compatibility decisions, within-experiment comparisons, heterogeneity descriptions, run manifest, report JSON, and a figure. Every demo output is marked synthetic.

## Use your evidence

Build an `EvidenceBundle` JSON using the versioned model; see [schema docs](docs/schema.md), [data dictionary](docs/data_dictionary.csv), and the [provenance template](configs/provenance_template.json). Keep papers/supplements and user-provided raw datasets outside the repository unless their licenses permit redistribution. Do not bypass access restrictions.

```bash
secretomebench validate path/to/evidence.json
secretomebench analyze path/to/evidence.json --out results/my-study
secretomebench run configs/analysis.json
secretomebench review path/to/evidence.json MEASUREMENT_ID corrected --correct value_normalized=101.0 --note "Corrected normalized conversion after review" --out reviewed.json
secretomebench schema --out docs/schema-v1.json
```

Review edits update provenance status and reviewer note while preserving source text, reported values, and the source record. Corrected or rejected records are not silently deleted; decide explicitly which records to include in a downstream analysis.

## Schema and evidence model

Records are linked as publication/source (`Study`) → experimental setup (`Experiment`) → independent biological unit (`BiologicalSample`) → method/analyte (`Assay`) → result (`Measurement`). Every entity has provenance fields. Original reported values, units, assay labels, culture conditions, and source locators remain available next to normalized fields. See [the extraction workflow](docs/extraction_workflow.md).

Supported assay families include ELISA, multiplex immunoassay, Western blot, qPCR, mass spectrometry, and unknown/unclassified. Comparability also requires compatible analyte class, specimen, normalization basis, and unit. Built-in conversion is limited to extracellular protein mass concentrations in conditioned medium: pg/mL, ng/mL, and µg/mL. Transcript abundance, secreted protein, intracellular protein, densitometry, and relative measurements stay distinct. Unknown units are not guessed.

IL-6 aliases map to `IL6`; IDO aliases map to `IDO1`. Alias mapping does not make qPCR and protein measurements equivalent.

## Statistics and interpretation

`compare_groups` analyzes only an explicitly requested assay within one experiment. It averages technical repeats within the shared biological-unit ID, then uses Welch’s independent-samples t-test or an optional paired test keyed to the same biological unit. The function reports nominal inference; callers must define the multiple-test family and call `adjust_p_values` when appropriate. It does not infer treatment effects across uncontrolled studies or automatically pool cross-study raw measurements.

Measurements without individual values or independent units remain descriptive. A reported mean without sample size or uncertainty does not yield an invented SD, SE, or confidence interval. Missing medium, duration, and other metadata remain missing and are reported in completeness tables.

The fixed-effect meta-analysis helper accepts prevalidated compatible independent study effect estimates; it does not decide whether records are comparable. See [statistical assumptions](docs/statistical_assumptions.md) and [assay comparability](docs/assay_comparability.md).

## Molecular dataset support

This release stores public dataset identifiers and preserves provenance but does not download data or implement transcriptomic/proteomic differential testing. Do not combine transcript and protein modalities. The core evidence workflow is functional without molecular datasets.

## Tests, lint, and benchmark

```bash
ruff check src tests examples benchmarks
python -m pytest
python benchmarks/benchmark_pipeline.py --records 1000 --seed 7
```

CI runs Python 3.11 and 3.12. Benchmark numbers depend on the host; none are claimed here.

## Sources and licensing

No external evidence source has been accessed or verified for the bundled demo. Synthetic fixtures contain no published results. Record source citation, DOI/PMID when verified, table/figure locator, source/access date, extraction method, verification state, and license/access terms for each real record. Software is MIT-licensed; source data have their own terms. More details: [data source policy](docs/data_sources.md).
