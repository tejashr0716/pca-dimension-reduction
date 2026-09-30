"""Two-endpoint Flask API for an explainable CSV -> scaled PCA pipeline."""

from __future__ import annotations

import io
import re
import threading
from pathlib import Path
from time import perf_counter

from flask import Flask, jsonify, render_template, request, send_file, url_for
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from werkzeug.utils import secure_filename

from pca_pipeline.errors import PipelineError
from pca_pipeline.pipeline import analyze_csv
from pca_pipeline.store import ResultStore

ROOT = Path(__file__).resolve().parent
UPLOAD_LIMIT_BYTES = 50_000_000  # Decimal MB; applies to the whole HTTP request.


def create_app(test_config: dict | None = None) -> Flask:
    """An app factory makes independent clients, caches and limits testable."""
    app = Flask(__name__)
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=UPLOAD_LIMIT_BYTES,
        MAX_FORM_MEMORY_SIZE=500_000,
        MAX_FORM_PARTS=8,
        MAX_ROWS=50_000,
        MAX_COLUMNS=500,
        MAX_CELLS=2_000_000,
        RESULT_TTL_SECONDS=900,
        RESULT_MAX_ITEMS=16,
        RESULT_MAX_BYTES=64 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    app.extensions["results"] = ResultStore(
        ttl_seconds=app.config["RESULT_TTL_SECONDS"],
        max_items=app.config["RESULT_MAX_ITEMS"],
        max_bytes=app.config["RESULT_MAX_BYTES"],
    )
    app.extensions["analysis_slot"] = threading.BoundedSemaphore(1)

    def error_response(error: PipelineError):
        response = jsonify({"error": {"code": error.code, "message": error.message}})
        response.status_code = error.status
        if error.code == "SERVER_BUSY":
            response.headers["Retry-After"] = "2"
        return response

    @app.errorhandler(PipelineError)
    def handle_pipeline_error(error):
        return error_response(error)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_upload(_):
        limit = app.config["MAX_CONTENT_LENGTH"] / 1_000_000
        return error_response(
            PipelineError(
                "UPLOAD_TOO_LARGE",
                f"Upload rejected. The request limit is {limit:g} MB; form fields have smaller limits.",
                413,
            )
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return error_response(PipelineError("HTTP_ERROR", error.description, error.code or 500))

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unexpected PCA service error", exc_info=error)
        return error_response(
            PipelineError("INTERNAL_ERROR", "Analysis could not complete. Please try again.", 500)
        )

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        )
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            upload_limit_mb=app.config["MAX_CONTENT_LENGTH"] / 1_000_000,
            upload_limit_bytes=app.config["MAX_CONTENT_LENGTH"],
        )

    @app.get("/sample_100d_data.csv")
    def sample():
        """A static demo download, not a third REST API endpoint."""
        return send_file(ROOT / "sample_100d_data.csv", as_attachment=True, mimetype="text/csv")

    @app.post("/api/analyze")
    def analyze():
        if "file" not in request.files:
            raise PipelineError("MISSING_FILE", "Choose a CSV file using the 'file' field.", 400)
        uploaded = request.files["file"]
        if not uploaded.filename:
            raise PipelineError("MISSING_FILENAME", "No file was selected.", 400)
        filename = secure_filename(uploaded.filename)
        if Path(filename).suffix.lower() != ".csv":
            raise PipelineError("INVALID_FILE_TYPE", "Only .csv files are supported.", 415)
        raw_components = request.form.get("components", "").strip()
        if not re.fullmatch(r"[+-]?[0-9]{1,6}", raw_components):
            raise PipelineError("INVALID_COMPONENTS", "Components must be a whole number.", 400)
        components = int(raw_components)
        if components < 1:
            raise PipelineError("COMPONENTS_OUT_OF_RANGE", "Use at least one component.", 422)

        slot = app.extensions["analysis_slot"]
        if not slot.acquire(blocking=False):
            raise PipelineError("SERVER_BUSY", "Another analysis is running. Try again shortly.", 429)
        started = perf_counter()
        try:
            result = analyze_csv(
                uploaded.stream,
                components,
                max_rows=app.config["MAX_ROWS"],
                max_columns=app.config["MAX_COLUMNS"],
                max_cells=app.config["MAX_CELLS"],
            )
            analysis_id = app.extensions["results"].put(result.csv_bytes)
            payload = result.metadata | {
                "schema_version": "1.0",
                "filename": filename,
                "analysis_id": analysis_id,
                "download_url": url_for("download", analysis_id=analysis_id),
                "expires_in_seconds": app.config["RESULT_TTL_SECONDS"],
                "processing_time_ms": round((perf_counter() - started) * 1000, 2),
            }
            return jsonify(payload)
        finally:
            slot.release()

    @app.get("/api/download")
    def download():
        analysis_id = request.args.get("analysis_id", "")
        payload = app.extensions["results"].get(analysis_id)
        if payload is None:
            raise PipelineError(
                "RESULT_NOT_FOUND",
                "The result is missing or expired. Run the analysis again to download it.",
                404,
            )
        return send_file(
            io.BytesIO(payload),
            mimetype="text/csv",
            as_attachment=True,
            download_name="pca_reduced_data.csv",
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
