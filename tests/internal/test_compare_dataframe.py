from pytest_verify.plugin import _compare_dataframe


def test_compare_dataframe_equal():
    old = "A,B,C\n1,2,3\n4,5,6"
    new = "A,B,C\n1,2,3\n4,5,6"
    assert _compare_dataframe(old, new)


def test_compare_dataframe_ignore_columns():
    old = "A,B,C\n1,2,3\n4,5,6"
    new = "A,B,C\n1,9,3\n4,9,6"
    assert _compare_dataframe(old, new, ignore_columns=["B"])

    # Should fail if not ignoring
    assert not _compare_dataframe(old, new, ignore_columns=[])


def test_compare_dataframe_column_order_difference():
    old = "A,B,C\n1,2,3\n4,5,6"
    new = "C,B,A\n3,2,1\n6,5,4"
    # Should still pass (columns realigned)
    assert _compare_dataframe(old, new)


def test_compare_dataframe_shape_mismatch():
    old = "A,B\n1,2\n3,4"
    new = "A,B\n1,2"
    assert not _compare_dataframe(old, new)


def test_compare_dataframe_tolerance():
    old = "A,B\n1.00,2.00\n3.00,4.00"
    new = "A,B\n1.01,2.00\n3.00,4.00"
    assert _compare_dataframe(old, new, abs_tol=0.02)
    assert not _compare_dataframe(old, new, abs_tol=0.0001)


def test_compare_dataframe_non_numeric():
    old = "Name,Role\nAlice,Engineer\nBob,Manager"
    new = "Name,Role\nAlice,Engineer\nBob,Manager"
    assert _compare_dataframe(old, new)


def test_compare_dataframe_nan_equality():
    old = "A,B\n1,\n,3"
    new = "A,B\n1,\n,3"
    assert _compare_dataframe(old, new)


def test_compare_dataframe_column_difference():
    old = "A,B,C\n1,2,3"
    new = "A,B,D\n1,2,3"
    assert not _compare_dataframe(old, new)
