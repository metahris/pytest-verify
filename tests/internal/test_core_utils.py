import json
import xml.etree.ElementTree as ET

import yaml

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

    yaml_str = """
    fruits:
      - apple
      - banana
    """
    assert _detect_format(yaml_str) == "yaml"


def test_serialize_json_format(tmp_path):
    data = {"x": 1, "y": 2}
    result = _serialize_result(data, "json")
    parsed = json.loads(result)
    assert parsed == data


def test_serialize_yaml_format(tmp_path):
    data = {"fruits": ["apple", "banana"], "count": 2}
    result = _serialize_result(data, "yaml")
    parsed = yaml.safe_load(result)
    assert parsed == data


def test_serialize_xml_format(tmp_path):
    data = "<root><item>A</item><item>B</item></root>"
    result = _serialize_result(data, "xml")

    # Parse both to ensure it is valid XML
    old_tree = ET.fromstring(data)
    new_tree = ET.fromstring(result)

    # Compare structure and values
    old_tags = [child.tag for child in old_tree]
    new_tags = [child.tag for child in new_tree]
    assert old_tags == new_tags

    old_texts = [child.text for child in old_tree]
    new_texts = [child.text for child in new_tree]
    assert old_texts == new_texts


def test_save_and_load_snapshot(tmp_path):
    file_path = tmp_path / "snap.txt"
    _save_snapshot(file_path, "hello")
    content = _load_snapshot(file_path)
    assert content == "hello"
