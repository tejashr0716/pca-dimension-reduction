"""Flask application for CSV PCA dimensionality reduction."""

from __future__ import annotations

import io
import time
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# This demo has no persistent storage. Each completed analysis is retained in
# process memory long enough for the corresponding browser to download its CSV.
analysis_results: dict[str, bytes] = {}


def error_response(message: str, status_code: int):
    """Return a consistent JSON error response."""
    return jsonify({"error": message}), status_code


@app.errorhandler(RequestEntityTooLarge)
def handle_large_upload(_: RequestEntityTooLarge):
    return error_response("File is too large. The maximum upload size is 50 MB.", 413)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/analyze")
def analyze():
    if "file" not in request.files:
        return error_response("Missing CSV file. Send it using the 'file' field.", 400)

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return error_response("No file was selected.", 400)
    if Path(secure_filename(uploaded_file.filename)).suffix.lower() != ".csv":
        return error_response("Invalid file type. Upload a .csv file.", 400)

    raw_components = request.form.get("components", "").strip()
    try:
        components = int(raw_components)
    except ValueError:
        return error_response("Components must be a whole number.", 400)
    if components < 1:
        return error_response("Components must be at least 1.", 400)

    start_time = time.perf_counter()
    try:
        dataframe = pd.read_csv(uploaded_file)
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
        return error_response(f"Could not read the CSV file: {exc}", 400)

    original_rows = len(dataframe)
    numeric_dataframe = dataframe.select_dtypes(include=[np.number]).copy()
    if numeric_dataframe.shape[1] == 0:
        return error_response("The dataset does not contain numeric columns.", 400)

    numeric_values = numeric_dataframe.to_numpy(dtype=np.float64, copy=False)
    invalid_mask = ~np.isfinite(numeric_values)
    missing_values_removed = int(invalid_mask.sum())
    cleaned_dataframe = numeric_dataframe.replace([np.inf, -np.inf], np.nan).dropna(axis=0)
    processed_rows, original_features = cleaned_dataframe.shape

    if processed_rows < 2:
        return error_response("At least two complete rows are required after cleaning.", 400)

    maximum_components = min(processed_rows, original_features)
    if components > maximum_components:
        return error_response(
            f"Components must be between 1 and {maximum_components} for this dataset.", 400
        )

    standardized_data = StandardScaler().fit_transform(cleaned_dataframe.to_numpy())
    pca = PCA(n_components=components)
    transformed_data = pca.fit_transform(standardized_data)
    reduced_columns = [f"PC_{index}" for index in range(1, components + 1)]
    reduced_dataframe = pd.DataFrame(transformed_data, columns=reduced_columns)
    processing_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    analysis_id = str(uuid.uuid4())
    analysis_results[analysis_id] = reduced_dataframe.to_csv(index=False).encode("utf-8")
    variance_by_component = (pca.explained_variance_ratio_ * 100).round(4).tolist()
    preview = reduced_dataframe.head(10).round(5).to_dict(orient="records")

    return jsonify(
        {
            "analysis_id": analysis_id,
            "original_rows": original_rows,
            "processed_rows": processed_rows,
            "original_features": original_features,
            "reduced_features": components,
            "missing_values_removed": missing_values_removed,
            "processing_time_ms": processing_time_ms,
            "explained_variance_percent": round(float(sum(variance_by_component)), 4),
            "variance_by_component": variance_by_component,
            "preview": preview,
        }
    )


@app.get("/api/download")
def download():
    analysis_id = request.args.get("analysis_id", "")
    csv_bytes = analysis_results.get(analysis_id)
    if csv_bytes is None:
        return error_response("No analysis result was found. Run PCA before downloading.", 404)

    return send_file(
        io.BytesIO(csv_bytes),
        mimetype="text/csv",
        as_attachment=True,
        download_name="pca_reduced_data.csv",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
