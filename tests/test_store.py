from concurrent.futures import ThreadPoolExecutor

import pytest

from pca_pipeline.errors import PipelineError
from pca_pipeline.store import ResultStore


def test_store_put_and_get():
    store = ResultStore()
    token = store.put(b"test")
    assert len(token) == 32
    assert store.get(token) == b"test"
    assert store.cached_bytes == 4


def test_store_expiry_and_bytes():
    time = [0]
    store = ResultStore(ttl_seconds=10, clock=lambda: time[0])
    token = store.put(b"1234")
    time[0] = 10
    assert store.get(token) is None
    assert store.cached_bytes == 0


def test_count_limit_evicts_oldest():
    store = ResultStore(max_items=2)
    old = store.put(b"one")
    second = store.put(b"two")
    latest = store.put(b"three")
    assert store.get(old) is None
    assert store.get(second) == b"two"
    assert store.get(latest) == b"three"


def test_byte_limit_evicts_oldest():
    store = ResultStore(max_bytes=6)
    old = store.put(b"1234")
    latest = store.put(b"5678")
    assert store.get(old) is None
    assert store.get(latest) == b"5678"
    assert store.cached_bytes == 4


def test_result_too_large_is_rejected():
    store = ResultStore(max_bytes=3)
    with pytest.raises(PipelineError) as caught:
        store.put(b"1234")
    assert caught.value.code == "RESULT_TOO_LARGE"
    assert store.cached_bytes == 0


def test_tokens_are_unique_under_threads():
    store = ResultStore(max_items=1000)
    with ThreadPoolExecutor(max_workers=8) as pool:
        tokens = list(pool.map(lambda _: store.put(b"safe"), range(100)))
    assert len(set(tokens)) == 100
    assert store.cached_bytes == 400
    assert all(store.get(token) == b"safe" for token in tokens)


@pytest.mark.parametrize("kwargs", [{"ttl_seconds": 0}, {"max_items": 0}, {"max_bytes": -1}])
def test_invalid_cache_configuration(kwargs):
    with pytest.raises(ValueError):
        ResultStore(**kwargs)
