import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from generate_sample_data import generate_benchmark
from pca_pipeline.pipeline import analyze_csv

SAMPLE = Path(__file__).resolve().parents[1] / "sample_100d_data.csv"


def test_original_benchmark_recipe_is_preserved():
    actual = pd.read_csv(SAMPLE, float_precision="round_trip")
    generated = generate_benchmark()
    assert actual.shape == (2000, 100)
    assert int(actual.isna().sum().sum()) == 80
    np.testing.assert_allclose(actual, generated, rtol=1e-12, atol=1e-12, equal_nan=True)


def test_resume_benchmark_and_independent_covariance_check():
    with SAMPLE.open("rb") as stream:
        result = analyze_csv(stream, 12)
    metadata = result.metadata
    assert metadata["processed_rows"] == 1921
    assert metadata["dropped_rows"] == 79
    assert metadata["missing_cells"] == 80
    assert metadata["original_features"] == 100
    assert metadata["reduced_features"] == 12
    assert round(metadata["explained_variance_percent"], 1) == 99.7
    assert metadata["explained_variance_percent"] == pytest.approx(99.71897173598569, abs=1e-8)
    exported = pd.read_csv(io.BytesIO(result.csv_bytes))
    assert exported.shape == (1921, 12)

    # Independent path: manual scaling + covariance eigenvalues, no sklearn PCA.
    raw = pd.read_csv(SAMPLE, float_precision="round_trip").to_numpy()
    clean = raw[np.isfinite(raw).all(axis=1)]
    scaled = (clean - clean.mean(axis=0)) / clean.std(axis=0, ddof=0)
    eigenvalues = np.linalg.eigvalsh(np.cov(scaled, rowvar=False))[::-1]
    independent = eigenvalues[:12].sum() / eigenvalues.sum() * 100
    assert metadata["explained_variance_percent"] == pytest.approx(independent, abs=1e-9)
