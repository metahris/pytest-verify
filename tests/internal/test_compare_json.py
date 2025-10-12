from pytest_verify.plugin import _compare_json


def test_compare_json_ignore_fields():
    old = '{"id": 1, "name": "Mohamed"}'
    new = '{"id": 2, "name": "Mohamed"}'
    assert _compare_json(old, new, ignore_fields=["id"])


def test_compare_json_ignore_fields_nested():
    old = '{"user": {"id": 1, "name": "Ayoub"}, "active": true}'
    new = '{"user": {"id": 2, "name": "Ayoub"}, "active": true}'
    assert _compare_json(old, new, ignore_fields=["id"])

    # Should fail if not ignoring 'id'
    assert not _compare_json(old, new, ignore_fields=[])


def test_compare_json_tolerance():
    old = '{"value": 3.1415}'
    new = '{"value": 3.1416}'
    # Small difference — within tolerance
    assert _compare_json(old, new, abs_tol=1e-3)

    # Should fail if tolerance too small
    assert not _compare_json(old, new, abs_tol=1e-6)


def test_compare_json_order_insensitive():
    old = '{"fruits": ["apple", "banana"]}'
    new = '{"fruits": ["banana", "apple"]}'
    # Default ignore_order_json=True
    assert _compare_json(old, new)


def test_compare_json_order_sensitive():
    old = '{"fruits": ["apple", "banana"]}'
    new = '{"fruits": ["banana", "apple"]}'
    assert not _compare_json(old, new, ignore_order_json=False)


def test_compare_json_nested_structure_order_sensitive():
    old = """
    {
      "team": {
        "members": [
          {"name": "John", "role": "Developer"},
          {"name": "Mary", "role": "Manager"}
        ]
      }
    }
    """
    new = """
    {
      "team": {
        "members": [
          {"name": "Mary", "role": "Manager"},
          {"name": "John", "role": "Developer"}
        ]
      }
    }
    """
    # Order matters → should fail
    assert not _compare_json(old, new, ignore_order_json=False)

    # Order ignored → should pass
    assert _compare_json(old, new, ignore_order_json=True)


def test_compare_json_deep_nested_ignore_fields():
    old = """
    {
      "company": {
        "departments": [
          {"name": "IT", "manager": {"id": 1, "name": "Ali"}},
          {"name": "HR", "manager": {"id": 2, "name": "Sarah"}}
        ]
      }
    }
    """
    new = """
    {
      "company": {
        "departments": [
          {"name": "IT", "manager": {"id": 3, "name": "Ali"}},
          {"name": "HR", "manager": {"id": 4, "name": "Sarah"}}
        ]
      }
    }
    """
    # Ignore all 'id' fields at any depth
    assert _compare_json(old, new, ignore_fields=["id"])


def test_compare_json_type_mismatch():
    old = '{"age": "30"}'
    new = '{"age": 30}'
    # String vs number should fail
    assert not _compare_json(old, new)