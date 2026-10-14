"""Execute the complete synthetic evidence workflow. No biological findings are implied."""

from secretomebench.synthetic import make_synthetic_bundle
from secretomebench.pipeline import run_bundle

if __name__ == "__main__":
    bundle = make_synthetic_bundle()
    run_bundle(bundle, "results/synthetic", label="synthetic software validation only",
               config={"mode": "synthetic", "fixture_version": "1.0"})
