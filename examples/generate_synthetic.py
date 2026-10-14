"""Write a validated synthetic evidence dataset as JSON."""

from pathlib import Path

from secretomebench.ingestion import write_bundle
from secretomebench.synthetic import make_synthetic_bundle

if __name__ == "__main__":
    target = Path("examples/synthetic_evidence.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    write_bundle(make_synthetic_bundle(), target)
    print(f"Wrote {target}")
