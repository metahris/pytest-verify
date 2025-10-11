import json
from pytest_verify.plugin import (
    _detect_format,
    _serialize_result,
    _save_snapshot,
    _load_snapshot,
)

def test_detect_format_various_types():
    assert _detect_format({"a": 1}) == "json"
    assert _detect_format(["x"]) == "json"
    assert _detect_format("<root></root>") == "xml"
    assert _detect_format("plain text") == "txt"
    assert _detect_format(b"bytes") == "bin"

def test_serialize_json_format(tmp_path):
    data = {"x": 1, "y": 2}
    result = _serialize_result(data, "json")
    parsed = json.loads(result)
    assert parsed == data

def test_save_and_load_snapshot(tmp_path):
    file_path = tmp_path / "snap.txt"
    _save_snapshot(file_path, "hello")
    content = _load_snapshot(file_path)
    assert content == "hello"
