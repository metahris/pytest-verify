from pytest_verify.plugin import _compare_xml


def test_compare_xml_order_insensitive():
    old = "<root><a>1</a><b>2</b></root>"
    new = "<root><b>2</b><a>1</a></root>"
    assert _compare_xml(old, new)  # default ignore_order_xml=True


def test_compare_xml_order_sensitive():
    old = "<root><a>1</a><b>2</b></root>"
    new = "<root><b>2</b><a>1</a></root>"
    assert not _compare_xml(old, new, ignore_order_xml=False)


def test_compare_xml_nested_order_sensitive():
    old = """
    <company>
      <employees>
        <person name="John" role="Developer"/>
        <person name="Mary" role="Manager"/>
      </employees>
    </company>
    """
    new = """
    <company>
      <employees>
        <person name="Mary" role="Manager"/>
        <person name="John" role="Developer"/>
      </employees>
    </company>
    """
    # Order matters
    assert not _compare_xml(old, new, ignore_order_xml=False)

    # Order ignored
    assert _compare_xml(old, new, ignore_order_xml=True)


def test_compare_xml_ignore_attributes():
    old = '<user id="1" name="Ali"/>'
    new = '<user id="2" name="Ali"/>'
    assert _compare_xml(old, new, ignore_fields=["id"])

    # Should fail when not ignoring
    assert not _compare_xml(old, new)


def test_compare_xml_ignore_nested_fields():
    old = """
    <data>
      <user>
        <id>1</id>
        <name>Ayoub</name>
      </user>
    </data>
    """
    new = """
    <data>
      <user>
        <id>2</id>
        <name>Ayoub</name>
      </user>
    </data>
    """
    assert _compare_xml(old, new, ignore_fields=["id"])
    assert not _compare_xml(old, new, ignore_fields=[])


def test_compare_xml_numeric_tolerance():
    old = "<metrics><score>99.95</score></metrics>"
    new = "<metrics><score>99.96</score></metrics>"

    # Within tolerance
    assert _compare_xml(old, new, abs_tol=0.02)

    # Should fail when tolerance too small
    assert not _compare_xml(old, new, abs_tol=0.0001)


def test_compare_xml_type_mismatch():
    old = "<root><age>30</age></root>"
    new = "<root><age>thirty</age></root>"
    assert not _compare_xml(old, new)


def test_compare_xml_deep_nested_ignore_fields():
    old = """
    <organization>
      <departments>
        <department>
          <name>IT</name>
          <manager id="1">Ali</manager>
        </department>
        <department>
          <name>HR</name>
          <manager id="2">Sarah</manager>
        </department>
      </departments>
    </organization>
    """
    new = """
    <organization>
      <departments>
        <department>
          <name>IT</name>
          <manager id="3">Ali</manager>
        </department>
        <department>
          <name>HR</name>
          <manager id="4">Sarah</manager>
        </department>
      </departments>
    </organization>
    """
    assert _compare_xml(old, new, ignore_fields=["id"])


def test_compare_xml_order_and_fields_mix():
    old = """
    <root>
      <item id="1" value="A"/>
      <item id="2" value="B"/>
    </root>
    """
    new = """
    <root>
      <item id="2" value="B"/>
      <item id="1" value="A"/>
    </root>
    """
    # Ignore order and ID field
    assert _compare_xml(old, new, ignore_fields=["id"], ignore_order_xml=True)

    # Fail if order-sensitive
    assert not _compare_xml(old, new, ignore_order_xml=False)