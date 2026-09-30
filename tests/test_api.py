import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pca_pipeline.store import ResultStore

from .conftest import VALID_CSV, upload


def assert_error(response, status, code):
    assert response.status_code == status
    assert response.is_json
    assert response.json["error"]["code"] == code
    assert response.json["error"]["message"]
    assert response.headers["Cache-Control"] == "no-store"


# Eleven primary failure classes. Parametrizations cover multiple variants.
def test_01_missing_file(client):
    assert_error(client.post("/api/analyze", data={"components": "2"}), 400, "MISSING_FILE")


def test_02_missing_filename(client):
    assert_error(upload(client, filename=""), 400, "MISSING_FILENAME")


@pytest.mark.parametrize("filename", ["data.txt", "data.xlsx", "data.csv.exe", "data"])
def test_03_wrong_file_type(client, filename):
    assert_error(upload(client, filename=filename), 415, "INVALID_FILE_TYPE")


@pytest.mark.parametrize("components", ["", "abc", "1.5", "1e2", "10000000", "NaN"])
def test_04_invalid_component_format(client, components):
    assert_error(upload(client, components=components), 400, "INVALID_COMPONENTS")


@pytest.mark.parametrize("components", ["0", "-1", "4", "999999"])
def test_05_out_of_range_components(client, components):
    assert_error(upload(client, components=components), 422, "COMPONENTS_OUT_OF_RANGE")


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"a,b\n",
        b"\xff\xfe\x80",
        b"a,b\n1,2,3\n",
        b"a,b\n1\n",
        b'a,b\n"1,2\n',
        b"a,a\n1,2\n3,4\n",
        b"a, \n1,2\n3,4\n",
    ],
)
def test_06_invalid_csv(client, payload):
    assert_error(upload(client, payload), 400, "INVALID_CSV")


def test_07_non_numeric_dataset(client):
    assert_error(upload(client, b"name,city\nTejas,Bengaluru\nSam,Mysuru\n"), 422, "NO_NUMERIC_FEATURES")


@pytest.mark.parametrize("payload", [b"a,b\n1,2\n", b"a,b\n1,\n,2\n", b"a,b\n1,2\ninf,4\n"])
def test_08_insufficient_complete_rows(client, payload):
    assert_error(upload(client, payload, components="1"), 422, "INSUFFICIENT_ROWS")


def test_09_constant_dataset(client):
    assert_error(upload(client, b"a,b\n1,2\n1,2\n1,2\n", components="1"), 422, "ZERO_VARIANCE")


def test_10_default_upload_limit_is_decimal_50mb(app):
    assert app.config["MAX_CONTENT_LENGTH"] == 50_000_000


def test_10_real_oversized_request(client):
    payload = b"x" * 50_000_001
    assert_error(upload(client, payload), 413, "UPLOAD_TOO_LARGE")


@pytest.mark.parametrize("token", ["", "../etc/passwd", "not-a-result", "a" * 32])
def test_11_missing_invalid_unknown_download(client, token):
    assert_error(client.get("/api/download", query_string={"analysis_id": token}), 404, "RESULT_NOT_FOUND")


def test_11_expired_download(client, app):
    clock = [0]
    app.extensions["results"] = ResultStore(ttl_seconds=1, clock=lambda: clock[0])
    result = upload(client).json
    clock[0] = 1
    assert_error(client.get(result["download_url"]), 404, "RESULT_NOT_FOUND")


def test_two_rest_endpoints(app):
    rules = [rule.rule for rule in app.url_map.iter_rules() if rule.rule.startswith("/api/")]
    assert sorted(rules) == ["/api/analyze", "/api/download"]


def test_full_upload_download_round_trip(client):
    response = upload(client)
    assert response.status_code == 200
    data = response.json
    json.dumps(data, allow_nan=False)
    assert data["original_rows"] == data["processed_rows"] == 5
    assert data["original_features"] == 3
    assert data["reduced_features"] == 2
    assert data["maximum_components"] == 3
    assert len(data["analysis_id"]) == 32
    assert data["variance_by_component"] == pytest.approx(np.array(data["explained_variance_ratio"]) * 100)
    assert data["cumulative_variance_percent"][-1] == pytest.approx(data["explained_variance_percent"])
    result = client.get(data["download_url"])
    assert result.status_code == 200
    assert "attachment" in result.headers["Content-Disposition"]
    assert "pca_reduced_data.csv" in result.headers["Content-Disposition"]
    csv_data = pd.read_csv(io.BytesIO(result.data))
    assert csv_data.shape == (5, 2)
    assert csv_data.columns.tolist() == ["PC_1", "PC_2"]
    assert np.isfinite(csv_data).all().all()


def test_uppercase_extension_and_bom(client):
    assert upload(client, b"\xef\xbb\xbf" + VALID_CSV, filename="DATA.CSV").status_code == 200


def test_ignored_columns_and_missing_rows_are_reported(client):
    response = upload(
        client,
        b"a,b,label,fixed\n1,3,A,9\n2,,B,9\n3,6,C,9\n4,1,D,9\n5,2,E,9\n",
        components="2",
    )
    data = response.json
    assert response.status_code == 200
    assert data["ignored_columns"] == ["label"]
    assert data["constant_columns"] == ["fixed"]
    assert data["numeric_features_used"] == 2
    assert data["missing_cells"] == 1
    assert data["dropped_rows"] == 1
    assert data["preview_source_rows"] == [1, 3, 4, 5]


def test_api_security_headers_and_wrong_method(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert_error(client.get("/api/analyze"), 405, "HTTP_ERROR")


def test_busy_server_returns_retry_after(client, app):
    slot = app.extensions["analysis_slot"]
    slot.acquire()
    try:
        response = upload(client)
        assert_error(response, 429, "SERVER_BUSY")
        assert response.headers["Retry-After"] == "2"
    finally:
        slot.release()
    assert upload(client).status_code == 200


def test_failure_releases_analysis_slot(client):
    assert upload(client, b"a,b\n1,1\n1,1\n", "1").status_code == 422
    assert upload(client).status_code == 200


@pytest.mark.parametrize("limit_name,limit", [("MAX_ROWS", 4), ("MAX_COLUMNS", 2), ("MAX_CELLS", 10)])
def test_parsed_dataset_limits(client, app, limit_name, limit):
    app.config[limit_name] = limit
    assert_error(upload(client), 413, "DATASET_TOO_LARGE")


def test_internal_errors_do_not_leak_details(client, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("PRIVATE INTERNAL STACK")

    monkeypatch.setattr("app.analyze_csv", fail)
    response = upload(client)
    assert_error(response, 500, "INTERNAL_ERROR")
    assert b"PRIVATE" not in response.data


def test_demo_download_is_present(client):
    response = client.get("/sample_100d_data.csv")
    assert response.status_code == 200
    assert len(response.data) > 1_000_000


def test_full_size_sample_upload_does_not_hit_form_field_limit(client):
    sample = Path(__file__).resolve().parents[1] / "sample_100d_data.csv"
    response = upload(client, sample.read_bytes(), components="12", filename=sample.name)
    assert response.status_code == 200
    assert response.json["processed_rows"] == 1921
    assert round(response.json["explained_variance_percent"], 1) == 99.7
