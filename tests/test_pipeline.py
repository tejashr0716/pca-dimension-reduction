import io

import numpy as np
import pandas as pd
import pytest
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from pca_pipeline.errors import PipelineError
from pca_pipeline.pipeline import analyze_csv

from .conftest import VALID_CSV


def test_pipeline_matches_independent_sklearn_fit():
    x = pd.read_csv(io.BytesIO(VALID_CSV)).to_numpy()
    reference = PCA(n_components=2, svd_solver="full").fit_transform(StandardScaler().fit_transform(x))
    result = analyze_csv(io.BytesIO(VALID_CSV), 2)
    actual = pd.read_csv(io.BytesIO(result.csv_bytes)).to_numpy()
    np.testing.assert_allclose(actual, reference, rtol=1e-10, atol=1e-10)


def test_reconstruction_error_is_discarded_standardized_variance():
    result = analyze_csv(io.BytesIO(VALID_CSV), 2).metadata
    fraction_retained = result["explained_variance_percent"] / 100
    assert result["standardized_reconstruction_mse"] == pytest.approx(1 - fraction_retained, abs=1e-12)


def test_component_count_excludes_centering_zero_rank():
    with pytest.raises(PipelineError, match="1 to 1"):
        analyze_csv(io.BytesIO(b"a,b,c\n1,2,3\n2,4,6\n"), 2)


def test_infinite_rows_are_counted_and_removed():
    metadata = analyze_csv(io.BytesIO(b"a,b\n1,2\ninf,3\n4,5\n6,7\n"), 1).metadata
    assert metadata["infinite_cells"] == 1
    assert metadata["missing_cells"] == 0
    assert metadata["processed_rows"] == 3
    assert metadata["dropped_rows"] == 1


def test_mixed_text_is_not_silently_coerced():
    result = analyze_csv(io.BytesIO(b"a,mixed\n1,10\n2,broken\n3,30\n"), 1)
    assert result.metadata["ignored_columns"] == ["mixed"]
    assert result.metadata["processed_rows"] == 3


def test_extreme_values_do_not_create_non_finite_json():
    with pytest.raises(PipelineError) as caught:
        analyze_csv(io.BytesIO(b"a,b\n1e308,2\n-1e308,3\n1e308,4\n"), 1)
    assert caught.value.code == "COMPUTATION_FAILED"


def test_pipeline_does_not_close_upload_stream():
    stream = io.BytesIO(VALID_CSV)
    analyze_csv(stream, 2)
    assert not stream.closed


def test_stripped_headers_are_preserved_in_feature_names():
    metadata = analyze_csv(io.BytesIO(b" a , b \n1,3\n2,1\n3,5\n"), 1).metadata
    assert metadata["feature_names"] == ["a", "b"]


@pytest.mark.parametrize("components", [0, -1, 1.5, True])
def test_invalid_direct_pipeline_component_count(components):
    with pytest.raises(PipelineError):
        analyze_csv(io.BytesIO(VALID_CSV), components)


def test_top_loadings_are_sorted_by_absolute_weight():
    metadata = analyze_csv(io.BytesIO(VALID_CSV), 2).metadata
    for component in metadata["top_loadings"]:
        weights = [abs(feature["weight"]) for feature in component["features"]]
        assert weights == sorted(weights, reverse=True)
        assert sum(feature["weight"] ** 2 for feature in component["features"]) == pytest.approx(1)
