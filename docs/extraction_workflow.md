# Evidence extraction and review

1. Record publication/source identity and access terms; do not bypass access restrictions.
2. Create one Study record per publication/data source and one Experiment per independently described setup.
3. Create sample records for independent biological units. Label technical repeats as technical and use their parent biological-unit ID.
4. Record original assay labels, specimen, analyte wording, units, values, uncertainty, sample size, and table/figure locator verbatim.
5. Add normalized values only through explicit mappings/conversions. Preserve original reported fields and mapping version.
6. Validate the JSON bundle with `secretomebench validate bundle.json`.
7. Review every extraction using the CSV `review_queue.csv`; mark confirmed/corrected/rejected with `secretomebench review bundle.json RECORD_ID STATUS --note '...' --out reviewed.json`. Use `--correct field=JSON_VALUE` only for normalized fields (for example, `--correct value_normalized=101.0`). Reported source values and text cannot be overwritten by review corrections. Rejected records remain in the reviewed bundle and must be excluded deliberately by downstream curation.
8. Run `secretomebench analyze reviewed.json --out results/`; retain the manifest and evidence tables.

Figure-digitized results must be labeled with the digitization method, software, calibration, and uncertainty. Do not treat them as directly reported table values. User-provided data remain separate from code and must be used under their applicable terms.
