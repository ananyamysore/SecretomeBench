"""Machine-readable evidence outputs and reproducible figures."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def write_report(tables: dict[str, pd.DataFrame], output_dir: str | Path, *, label: str,
                 summary: dict[str, object] | None = None) -> None:
    """Write named CSV evidence tables, a descriptive plot, and an explicit methods/report JSON."""
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(output / f"{name}.csv", index=False)
    evidence = tables.get("evidence")
    if evidence is not None and not evidence.empty and "value_normalized" in evidence:
        plot_data = evidence.dropna(subset=["value_normalized"])
        fig, ax = plt.subplots(figsize=(8, 5))
        if not plot_data.empty:
            labels = plot_data.get("assay_family", pd.Series("assay", index=plot_data.index)).astype(str)
            for label_name, subset in plot_data.groupby(labels):
                ax.scatter([label_name] * len(subset), subset.value_normalized, alpha=.75, label=label_name)
            ax.tick_params(axis="x", rotation=30)
        ax.set_ylabel("Normalized reported value (assay-specific units)")
        ax.set_title(f"Evidence measurements — {label}")
        fig.tight_layout(); fig.savefig(output / "measurements.png", dpi=160); plt.close(fig)
    report = {"label": label, "summary": summary or {},
              "interpretation": "Evidence records and compatible within-experiment analyses; no claim of a superior formulation.",
              "limitations": ["Synthetic records are software fixtures, not biological evidence.",
                              "Cross-study associations are descriptive unless a compatible design and effect estimate justify synthesis."]}
    (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
