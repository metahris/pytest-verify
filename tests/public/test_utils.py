from pytest_verify.plugin import (
    _detect_format,
    _serialize_result,
    _get_snapshot_paths,
)
from pathlib import Path

def test_detect_format_for_json():
    assert _detect_format({"a": 1}) == "json"

def test_detect_format_for_xml():
    xml_data = "<root><item>1</item></root>"
    assert _detect_format(xml_data) == "xml"

def test_detect_format_for_text():
    assert _detect_format("hello") == "txt"

def test_detect_format_for_binary():
    assert _detect_format(b"abc") == "bin"

def test_serialize_result_json():
    result = {"key": "value"}
    serialized = _serialize_result(result, "json")
    assert '"key": "value"' in serialized

def test_get_snapshot_paths_creates_correct_files(tmp_path: Path):
    expected, actual = _get_snapshot_paths("test_case", "json", tmp_path)
    assert expected.name == "test_case.expected.json"
    assert actual.name == "test_case.actual.json"
    assert expected.parent.exists()
