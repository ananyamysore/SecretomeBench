"""Write a validated synthetic evidence dataset as JSON."""

import argparse
from pathlib import Path

from secretomebench.ingestion import write_bundle
from secretomebench.synthetic import make_synthetic_bundle

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="examples/synthetic_evidence_generated.json")
    target = Path(parser.parse_args().out)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_bundle(make_synthetic_bundle(), target)
    print(f"Wrote {target}")
