# Statistical assumptions and limitations

`compare_groups` is restricted to one experiment and one assay. It aggregates technical repeats by biological unit and then runs either a Welch two-sample test or a paired t-test. The paired mode requires repeated observations keyed to the same biological unit. It reports the mean difference and nominal p-value; a declared family of p-values can be adjusted with `adjust_p_values`. This small-sample routine does not account for random effects, non-normality, censoring below detection limits, or complex repeated-measures designs.

The software does not infer treatment effects from study-level differences in cell source, medium, conditioning time, assay, and other covariates. Cross-study raw measurements are never automatically pooled. The fixed-effect helper accepts prevalidated comparable independent estimates, but this repository's synthetic workflow does not call meta-analysis.

Missing metadata and uncertainty remain missing and are summarized. A reported mean without n or variance does not yield a standard error or confidence interval. No sample size, SD, or value is imputed. Multiple measurements from one experiment are not independent replicates.

Molecular data are not bundled. A future transcriptomic/proteomic analysis must preserve original units, identifiers and normalization, analyze modalities separately, map identifiers transparently, and correct multiple tests. The schema can store dataset identifiers, but this release does not download public datasets.
