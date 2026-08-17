"""Generate a correlated 2,000-row, 100-feature CSV for PCA demonstrations."""

from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 42
ROWS = 2_000
FEATURES = 100
LATENT_FACTORS = 12
OUTPUT_FILE = Path(__file__).with_name("sample_100d_data.csv")


def main():
    rng = np.random.default_rng(RANDOM_SEED)
    latent_data = rng.normal(0, 1, size=(ROWS, LATENT_FACTORS))
    feature_loadings = rng.normal(0, 1, size=(LATENT_FACTORS, FEATURES))
    noise = rng.normal(0, 0.18, size=(ROWS, FEATURES))
    data = latent_data @ feature_loadings + noise

    # Vectorized placement of a small number of missing values.
    missing_positions = rng.choice(ROWS * FEATURES, size=80, replace=False)
    row_indices, column_indices = np.unravel_index(missing_positions, (ROWS, FEATURES))
    data[row_indices, column_indices] = np.nan

    columns = [f"feature_{number:03d}" for number in range(1, FEATURES + 1)]
    dataframe = pd.DataFrame(data, columns=columns)

    dataframe.to_csv(OUTPUT_FILE, index=False)
    print(f"Created {OUTPUT_FILE.name}: {ROWS} rows, {FEATURES} numeric features, 80 NaN values.")


if __name__ == "__main__":
    main()
