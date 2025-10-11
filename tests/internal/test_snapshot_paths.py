from pytest_verify.plugin import _get_snapshot_paths, _backup_expected

def test_snapshot_paths(tmp_path):
    expected, actual = _get_snapshot_paths("test_func", "json", tmp_path)
    assert expected.name.endswith(".expected.json")
    assert actual.name.endswith(".actual.json")
    assert expected.parent.exists()

def test_backup_expected_creates_copy(tmp_path):
    original = tmp_path / "data.expected.txt"
    original.write_text("original content")

    _backup_expected(original)
    backup = tmp_path / "data.expected.txt.bak"
    assert backup.exists()
    assert backup.read_text() == "original content"
