"""Reproduce the repository's original synthetic benchmark, without tuning PCA."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42
ROWS = 2_000
FEATURES = 100
LATENT_FACTORS = 12
NOISE_STANDARD_DEVIATION = 0.18
MISSING_CELLS = 80
OUTPUT_FILE = Path(__file__).with_name("sample_100d_data.csv")


def generate_benchmark() -> pd.DataFrame:
    """X = Z @ W + Gaussian noise; missing cells are placed after generation."""
    rng = np.random.default_rng(RANDOM_SEED)
    latent = rng.normal(0, 1, size=(ROWS, LATENT_FACTORS))
    loadings = rng.normal(0, 1, size=(LATENT_FACTORS, FEATURES))
    noise = rng.normal(0, NOISE_STANDARD_DEVIATION, size=(ROWS, FEATURES))
    values = latent @ loadings + noise
    positions = rng.choice(ROWS * FEATURES, size=MISSING_CELLS, replace=False)
    row_indexes, column_indexes = np.unravel_index(positions, (ROWS, FEATURES))
    values[row_indexes, column_indexes] = np.nan
    return pd.DataFrame(values, columns=[f"feature_{number:03d}" for number in range(1, FEATURES + 1)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generate_benchmark().to_csv(args.output, index=False)
    print(f"Generated {args.output.name}: {ROWS:,} rows, {FEATURES} features, {MISSING_CELLS} missing cells.")
    print("Synthetic correlated data, not a real-world accuracy or performance benchmark.")


if __name__ == "__main__":
    main()
