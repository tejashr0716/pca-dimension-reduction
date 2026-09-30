"""Write machine-readable evidence for the resume metric and independent check."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import platform
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app  # noqa: E402
from pca_pipeline.pipeline import analyze_csv  # noqa: E402


def run_benchmark(source: Path) -> dict:
    started = perf_counter()
    with source.open("rb") as stream:
        result = analyze_csv(stream, 12)
    duration_ms = (perf_counter() - started) * 1000
    raw = pd.read_csv(source, float_precision="round_trip").to_numpy()
    clean = raw[np.isfinite(raw).all(axis=1)]
    scaled = (clean - clean.mean(axis=0)) / clean.std(axis=0, ddof=0)
    eigenvalues = np.linalg.eigvalsh(np.cov(scaled, rowvar=False))[::-1]
    independent_percent = float(eigenvalues[:12].sum() / eigenvalues.sum() * 100)
    measured_percent = result.metadata["explained_variance_percent"]
    if abs(measured_percent - independent_percent) > 1e-8:
        raise AssertionError("Independent covariance check did not reproduce the result.")
    if raw.shape != (2000, 100) or round(measured_percent, 1) != 99.7:
        raise AssertionError("The supplied benchmark does not support the stated resume claim.")
    exported = pd.read_csv(io.BytesIO(result.csv_bytes))
    client = create_app({"TESTING": True}).test_client()
    response = client.post(
        "/api/analyze",
        data={"file": (io.BytesIO(source.read_bytes()), source.name), "components": "12"},
    )
    assert response.status_code == 200
    download = client.get(response.json["download_url"])
    assert download.status_code == 200
    assert pd.read_csv(io.BytesIO(download.data)).shape == exported.shape
    assert abs(response.json["explained_variance_percent"] - measured_percent) < 1e-9
    return {
        "source": "Repository's original seed-42 synthetic correlated CSV; not real-world data",
        "source_path": source.name,
        "original_repository_commit": "63eeaace8a95c894e8cc524526c61ee1bd2f11bf",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "recipe": {
            "seed": 42,
            "rows": 2000,
            "features": 100,
            "latent_factors": 12,
            "noise_standard_deviation": 0.18,
            "missing_cells": 80,
        },
        "input_shape": list(raw.shape),
        "output_shape": list(exported.shape),
        "processed_rows": len(clean),
        "dropped_rows": len(raw) - len(clean),
        "retained_variance_percent": measured_percent,
        "retained_variance_percent_rounded_for_resume": round(measured_percent, 1),
        "independent_covariance_percent": independent_percent,
        "absolute_check_difference_percentage_points": abs(measured_percent - independent_percent),
        "standardized_reconstruction_mse": result.metadata["standardized_reconstruction_mse"],
        "variance_by_component": result.metadata["variance_by_component"],
        "cumulative_variance_percent": result.metadata["cumulative_variance_percent"],
        "api_upload_download_verified": True,
        "pipeline_duration_ms_this_machine_only": duration_ms,
        "runtime": {
            "python": platform.python_version(),
            "packages": {
                name: importlib.metadata.version(name)
                for name in ["Flask", "Werkzeug", "numpy", "pandas", "scikit-learn", "scipy"]
            },
        },
        "limitations": [
            "Variance is measured after scaling and dropping non-finite rows.",
            "Twelve latent factors make this synthetic dataset favorable to twelve PCA components.",
            "This is not classification accuracy, predictive quality or a universal CSV guarantee.",
            "The elapsed time is one local run, not a deployment SLA or load-test result.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=ROOT / "sample_100d_data.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/benchmark.json")
    args = parser.parse_args()
    evidence = run_benchmark(args.csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(
        f"Verified {evidence['input_shape']} -> {evidence['output_shape']}; "
        f"variance {evidence['retained_variance_percent']:.9f}%; "
        f"independent check difference "
        f"{evidence['absolute_check_difference_percentage_points']:.2e} percentage points."
    )
    print(f"Evidence written to {args.output}")


if __name__ == "__main__":
    main()
