from pytest_verify.plugin import (
    _compare_json,
    _compare_text,
    _compare_bin,
    _compare_xml,
)


def test_compare_text_identical():
    assert _compare_text("hello", "hello")
    assert not _compare_text("hello", "world")


def test_compare_bin_exact():
    assert _compare_bin(b"abc", b"abc")
    assert not _compare_bin(b"abc", b"xyz")


def test_compare_json_ignore_fields():
    old = '{"id": 1, "name": "Mohamed"}'
    new = '{"id": 2, "name": "Mohamed"}'
    assert _compare_json(old, new, ignore_fields=["id"])


def test_compare_json_tolerance():
    old = '{"value": 3.1415}'
    new = '{"value": 3.1416}'
    assert _compare_json(old, new, abs_tol=1e-3)


def test_compare_xml_order_insensitive():
    old = "<root><a>1</a><b>2</b></root>"
    new = "<root><b>2</b><a>1</a></root>"
    assert _compare_xml(old, new)


def test_compare_xml_order_sensitive():
    old = "<root><a>1</a><b>2</b></root>"
    new = "<root><b>2</b><a>1</a></root>"
    assert not _compare_xml(old, new, ignore_order_xml=False)
