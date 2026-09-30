"""Validate, select, clean, standardize, fit PCA and serialize; no HTTP code."""

from __future__ import annotations

import csv
import io
import warnings
from dataclasses import dataclass
from typing import BinaryIO

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .errors import PipelineError


@dataclass(frozen=True)
class AnalysisResult:
    metadata: dict
    csv_bytes: bytes


def _validate_csv_shape(stream: BinaryIO, max_rows: int, max_columns: int, max_cells: int):
    """Stream a strict UTF-8 CSV pass before allocating pandas/NumPy matrices."""
    stream.seek(0)
    text = io.TextIOWrapper(stream, encoding="utf-8-sig", newline="")
    try:
        reader = csv.reader(text, strict=True)
        header = next((row for row in reader if row), None)
        if header is None:
            raise PipelineError("INVALID_CSV", "The CSV is empty.", 400)
        names = [name.strip() for name in header]
        if not all(names) or len(names) != len(set(names)):
            raise PipelineError("INVALID_CSV", "Use unique, non-empty column headers.", 400)
        if len(names) > max_columns:
            raise PipelineError("DATASET_TOO_LARGE", f"Use at most {max_columns} columns.", 413)
        rows = 0
        for row in reader:
            if not row:
                continue
            if len(row) != len(names):
                raise PipelineError("INVALID_CSV", "CSV rows must have the same width as the header.", 400)
            rows += 1
            if rows > max_rows or rows * len(names) > max_cells:
                raise PipelineError(
                    "DATASET_TOO_LARGE",
                    f"Use at most {max_rows:,} rows and {max_cells:,} total cells.",
                    413,
                )
        if not rows:
            raise PipelineError("INVALID_CSV", "The CSV has a header but no data rows.", 400)
        return names
    except (UnicodeError, csv.Error) as error:
        raise PipelineError("INVALID_CSV", "Use a well-formed, UTF-8 encoded CSV.", 400) from error
    finally:
        text.detach()  # Keep Flask's upload stream open for the pandas pass.
        stream.seek(0)


def analyze_csv(
    stream: BinaryIO,
    components: int,
    *,
    max_rows: int = 50_000,
    max_columns: int = 500,
    max_cells: int = 2_000_000,
) -> AnalysisResult:
    """Fit on the current file; not a predictive model or a reusable serving API."""
    if not isinstance(components, int) or isinstance(components, bool) or components < 1:
        raise PipelineError("COMPONENTS_OUT_OF_RANGE", "Use at least one whole-number component.")
    names = _validate_csv_shape(stream, max_rows, max_columns, max_cells)
    try:
        dataframe = pd.read_csv(
            stream,
            names=names,
            header=0,
            encoding="utf-8-sig",
            low_memory=False,
            on_bad_lines="error",
            float_precision="round_trip",
        )
    except (ValueError, UnicodeError, pd.errors.ParserError) as error:
        raise PipelineError("INVALID_CSV", "The CSV could not be parsed.", 400) from error

    numeric = dataframe.select_dtypes(include=[np.number])
    ignored = [column for column in dataframe.columns if column not in numeric.columns]
    if numeric.empty or numeric.shape[1] == 0:
        raise PipelineError("NO_NUMERIC_FEATURES", "The CSV must contain at least one numeric column.")

    values = numeric.to_numpy(dtype=np.float64)
    missing_cells = int(np.isnan(values).sum())
    infinite_cells = int(np.isinf(values).sum())
    valid_rows = np.isfinite(values).all(axis=1)
    cleaned = values[valid_rows]
    if len(cleaned) < 2:
        raise PipelineError("INSUFFICIENT_ROWS", "At least two complete numeric rows are required.")

    # Equality of min/max avoids an overflow-prone variance calculation.
    varying = cleaned.max(axis=0) != cleaned.min(axis=0)
    constant_columns = numeric.columns[~varying].tolist()
    feature_names = numeric.columns[varying].tolist()
    cleaned = cleaned[:, varying]
    if not feature_names:
        raise PipelineError("ZERO_VARIANCE", "All numeric columns are constant after cleaning.")
    maximum_components = min(len(cleaned) - 1, len(feature_names))
    if components > maximum_components:
        raise PipelineError(
            "COMPONENTS_OUT_OF_RANGE",
            f"Use 1 to {maximum_components} components after cleaning and removing constant columns.",
        )

    model = Pipeline([("scale", StandardScaler()), ("pca", PCA(n_components=components, svd_solver="full"))])
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            scores = model.fit_transform(cleaned)
            pca = model.named_steps["pca"]
            ratios = pca.explained_variance_ratio_
            scaled = model.named_steps["scale"].transform(cleaned)
            reconstructed = pca.inverse_transform(scores)
            reconstruction_mse = float(np.mean((scaled - reconstructed) ** 2))
        if not np.isfinite(scores).all() or not np.isfinite(ratios).all():
            raise ValueError("Non-finite PCA output")
        if not np.isfinite(reconstruction_mse):
            raise ValueError("Non-finite reconstruction error")
    except (ValueError, FloatingPointError, RuntimeWarning, np.linalg.LinAlgError) as error:
        raise PipelineError(
            "COMPUTATION_FAILED",
            "The numeric values could not be processed safely. Check their scale and variation.",
        ) from error

    columns = [f"PC_{number}" for number in range(1, components + 1)]
    reduced = pd.DataFrame(scores, columns=columns)
    csv_bytes = reduced.to_csv(index=False).encode("utf-8")
    cumulative_percent = np.minimum(np.cumsum(ratios) * 100, 100).tolist()
    top_loadings = []
    for number, weights in enumerate(pca.components_, 1):
        indexes = np.argsort(np.abs(weights))[::-1][:5]
        top_loadings.append(
            {
                "component": f"PC_{number}",
                "features": [
                    {"name": feature_names[index], "weight": float(weights[index])} for index in indexes
                ],
            }
        )

    metadata = {
        "original_rows": len(dataframe),
        "processed_rows": len(cleaned),
        "dropped_rows": int((~valid_rows).sum()),
        "original_columns": len(dataframe.columns),
        "original_features": len(numeric.columns),
        "numeric_features_used": len(feature_names),
        "reduced_features": components,
        "maximum_components": maximum_components,
        "feature_names": feature_names,
        "ignored_columns": ignored,
        "constant_columns": constant_columns,
        "missing_cells": missing_cells,
        "infinite_cells": infinite_cells,
        "explained_variance_ratio": ratios.tolist(),
        "variance_by_component": (ratios * 100).tolist(),
        "cumulative_variance_percent": cumulative_percent,
        "explained_variance_percent": float(ratios.sum() * 100),
        "standardized_reconstruction_mse": reconstruction_mse,
        "variance_basis": "Standardized non-constant numeric features, after complete-case cleaning",
        "preprocessing": {
            "numeric_selection": "pandas numeric dtypes; no coercion of mixed text columns",
            "missing_policy": "Drop rows with NaN or infinite values in any selected numeric column",
            "constant_policy": "Remove constant numeric columns after row cleaning",
            "scaling": "StandardScaler: mean 0, population standard deviation 1",
            "solver": "Full SVD; no whitening",
        },
        "preview": reduced.head(10).round(6).to_dict(orient="records"),
        "preview_source_rows": (np.flatnonzero(valid_rows)[:10] + 1).tolist(),
        "top_loadings": top_loadings,
        "output_bytes": len(csv_bytes),
    }
    return AnalysisResult(metadata=metadata, csv_bytes=csv_bytes)
