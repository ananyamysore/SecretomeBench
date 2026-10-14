"""Reproducible runtime and memory harness; no benchmark claims are embedded."""

from __future__ import annotations

import argparse
import json
import resource
import time

import pandas as pd

from secretomebench.normalization import harmonize_column


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=int, default=1000); parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    if args.records < 1: parser.error("--records must be >=1")
    frame = pd.DataFrame({"cell_source": ["bone marrow", "adipose", "umbilical cord"] * ((args.records + 2) // 3)})[:args.records]
    start = time.perf_counter(); result = harmonize_column(frame, source="cell_source", target="source_normalized", category="cell_source")
    elapsed = time.perf_counter() - start
    print(json.dumps({"records": args.records, "seed": args.seed, "elapsed_seconds": elapsed,
                      "peak_rss_platform_units": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      "result_rows": len(result)}, indent=2))


if __name__ == "__main__":
    main()
