import json

from pytest_verify.plugin import _compare_ndarray


def test_compare_ndarray_equal():
    old = json.dumps([[1, 2, 3]])
    new = json.dumps([[1, 2, 3]])
    assert _compare_ndarray(old, new)


def test_compare_ndarray_tolerance():
    old = json.dumps([[1.0, 2.0, 3.0]])
    new = json.dumps([[1.001, 2.0, 3.0]])
    assert _compare_ndarray(old, new, abs_tol=0.01)
    assert not _compare_ndarray(old, new, abs_tol=0.0001)


def test_compare_ndarray_shape_mismatch():
    old = json.dumps([[1, 2, 3]])
    new = json.dumps([[1, 2], [3, 4]])
    assert not _compare_ndarray(old, new)


def test_compare_ndarray_nan_handling():
    old = json.dumps([[1, None, 3]])
    new = json.dumps([[1, None, 3]])
    assert _compare_ndarray(old, new)


def test_compare_ndarray_type_mismatch():
    old = json.dumps([[1, 2, 3]])
    new = json.dumps([["1", "2", "3"]])
    # Even though shapes match, dtype mismatch → False
    assert not _compare_ndarray(old, new)
