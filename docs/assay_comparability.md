# Assay and unit comparability

Measurements are quantitatively comparable only when analyte identity, molecular level, specimen, assay family, normalization basis, and unit support a meaningful common scale. The current conservative compatibility checker keeps ELISA, multiplex immunoassays, Western blot densitometry, qPCR, mass spectrometry, and unknown assays separate unless their explicit family metadata and normalization agree.

Only secreted-protein mass concentrations in conditioned medium have built-in conversions among pg/mL, ng/mL, and µg/mL. No conversion is applied to transcript abundance, intracellular expression, densitometry, relative abundance, per-cell normalization, or unsupported units. Unknown categories remain visible as `unmapped:` values.

Common marker aliases include IL-6/IL6/Interleukin-6 → IL6 and IDO/indoleamine 2,3-dioxygenase → IDO1. Alias normalization identifies a target name; it does not make protein and transcript assays interchangeable. In particular, IDO1 qPCR is not an extracellular IDO protein concentration.
