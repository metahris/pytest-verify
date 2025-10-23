from pytest_verify import verify_snapshot


@verify_snapshot()
def test_basic_xml_snapshot():
    """Compares basic XML structure."""
    return "<user><name>Mohamed</name><age>28</age></user>"


@verify_snapshot()
def test_order_sensitive_xml_snapshot():
    """Ensures XML order sensitivity works when disabled."""
    return """
    <users>
        <user id="1">Mohamed</user>
        <user id="2">Adnane</user>
    </users>
    """


@verify_snapshot(abs_tol=1e-3, rel_tol=1e-3)
def test_xml_with_numeric_tolerance():
    """
    Verifies that small numeric differences in XML attributes or values
    are tolerated within the given abs/rel tolerance.
    """
    return """
    <measurements>
        <temperature value="20.001" unit="C"/>
        <pressure>101.325</pressure>
    </measurements>
    """


@verify_snapshot(abs_tol_fields={"//sensor/temp": 0.5})
def test_xml_abs_tol_fields():
    return """
    <sensors>
        <sensor><temp>20.0</temp></sensor>
        <sensor><temp>21.0</temp></sensor>
    </sensors>
    """
