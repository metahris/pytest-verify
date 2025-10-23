from pytest_verify.plugin import _compare_yaml


def test_compare_yaml_order_sensitive():
    old = """
    fruits:
      - apple
      - banana
    """
    new = """
    fruits:
      - banana
      - apple
    """
    # Order-sensitive: should detect difference
    assert not _compare_yaml(old, new, ignore_order_yaml=False)

def test_compare_yaml_order_insensitive():
    old = """
    fruits:
      - apple
      - banana
    """
    new = """
    fruits:
      - banana
      - apple
    """
    # Order-insensitive: should treat lists as equal
    assert _compare_yaml(old, new, ignore_order_yaml=True)

def test_compare_yaml_ignore_fields():
    old = """
    person:
      name: Alice
      age: 30
      city: Paris
    """
    new = """
    person:
      name: Alice
      age: 31
      city: Paris
    """
    # Should ignore 'age' field difference
    assert _compare_yaml(old, new, ignore_fields=["$.person.age"], show_debug=True)

    # Should fail if 'age' is not ignored
    assert not _compare_yaml(old, new)

def test_compare_yaml_nested_structure():
    old = """
    company:
      employees:
        - name: John
          role: Developer
        - name: Mary
          role: Manager
    """
    new = """
    company:
      employees:
        - name: Mary
          role: Manager
        - name: John
          role: Developer
    """
    # Should fail if order matters
    assert not _compare_yaml(old, new, ignore_order_yaml=False)

    # Should pass if order is ignored
    assert _compare_yaml(old, new, ignore_order_yaml=True)

def test_compare_yaml_numeric_tolerance():
    old = """
    metrics:
      accuracy: 99.95
    """
    new = """
    metrics:
      accuracy: 99.96
    """
    # Allow small tolerance
    assert _compare_yaml(old, new, abs_tol=0.02)

    # Should fail if tolerance too strict
    assert not _compare_yaml(old, new, abs_tol=0.0001)
