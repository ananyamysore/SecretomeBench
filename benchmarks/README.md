# Runtime and memory benchmark

After installing `.[test]`, run:

```bash
python benchmarks/benchmark_pipeline.py --records 1000 --seed 7
```

The harness creates deterministic synthetic rows and measures validation plus harmonization elapsed time and peak resident memory. Values vary by OS, Python, and dependencies. No benchmark results or performance comparison are claimed in the repository.
