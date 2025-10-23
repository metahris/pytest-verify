from pytest_verify.plugin import _compare_xml

debug = True


# --------------------------------------------------------------------------
# 1️⃣ BASIC TESTS — direct equality and simple mismatches
# --------------------------------------------------------------------------

def test_identical_xml():
    xml1 = "<root><x>1</x><y>2</y></root>"
    xml2 = "<root><x>1</x><y>2</y></root>"
    assert _compare_xml(xml1, xml2, show_debug=debug)


def test_simple_value_mismatch():
    xml1 = "<root><x>1</x></root>"
    xml2 = "<root><x>2</x></root>"
    assert not _compare_xml(xml1, xml2, show_debug=debug)


def test_type_mismatch_numeric_vs_text():
    xml1 = "<root><x>1</x></root>"
    xml2 = "<root><x>1.0</x></root>"
    # Both are numeric -> passes
    assert _compare_xml(xml1, xml2, show_debug=debug)


def test_tag_mismatch():
    xml1 = "<root><x>1</x></root>"
    xml2 = "<root><y>1</y></root>"
    assert not _compare_xml(xml1, xml2, show_debug=debug)


# --------------------------------------------------------------------------
# 2️⃣ TOLERANCE TESTS — abs_tol and rel_tol
# --------------------------------------------------------------------------

def test_global_abs_tolerance():
    xml1 = "<sensor><temp>20.0</temp></sensor>"
    xml2 = "<sensor><temp>20.05</temp></sensor>"
    assert _compare_xml(xml1, xml2, abs_tol=0.1, show_debug=debug)


def test_global_tolerance_fail():
    xml1 = "<sensor><temp>20.0</temp></sensor>"
    xml2 = "<sensor><temp>21.0</temp></sensor>"
    assert not _compare_xml(xml1, xml2, abs_tol=0.5, show_debug=debug)


def test_relative_tolerance_success():
    xml1 = "<sensor><humidity>100.0</humidity></sensor>"
    xml2 = "<sensor><humidity>104.0</humidity></sensor>"
    assert _compare_xml(xml1, xml2, rel_tol=0.05, show_debug=debug)  # 5% tolerance


# --------------------------------------------------------------------------
# 3️⃣ PATH-LEVEL TOLERANCE TESTS
# --------------------------------------------------------------------------

def test_per_path_abs_tolerance():
    xml1 = "<root><a>1.0</a><b>2.0</b></root>"
    xml2 = "<root><a>1.5</a><b>2.9</b></root>"
    abs_tol_fields = {"/root/b": 1.0}
    assert _compare_xml(xml1, xml2, abs_tol=0.5, abs_tol_fields=abs_tol_fields, show_debug=debug)


def test_per_path_rel_tolerance():
    xml1 = "<values><x>100</x><y>200</y></values>"
    xml2 = "<values><x>110</x><y>210</y></values>"
    rel_tol_paths = {"/values/x": 0.2}  # 20%
    assert _compare_xml(xml1, xml2, rel_tol=0.05, rel_tol_fields=rel_tol_paths, show_debug=debug)


# --------------------------------------------------------------------------
# 4️⃣ IGNORED PATHS
# --------------------------------------------------------------------------

def test_ignore_path_simple():
    xml1 = "<root><id>1</id><timestamp>now</timestamp></root>"
    xml2 = "<root><id>1</id><timestamp>later</timestamp></root>"
    ignore_fields = ["/root/timestamp"]
    assert _compare_xml(xml1, xml2, ignore_fields=ignore_fields, show_debug=debug)


def test_ignore_fields_complex():
    """
    Ignore multiple paths with different patterns:
      - Exact path: /user/profile/updated_at
      - Wildcard: /devices/*/debug
      - Recursive: //trace
    """
    xml1 = """
    <data>
        <user>
            <id>7</id>
            <profile><updated_at>2025-10-14T10:00:00Z</updated_at><age>30</age></profile>
        </user>
        <devices>
            <device><id>d1</id><debug>alpha</debug><temp>20.0</temp></device>
            <device><id>d2</id><debug>beta</debug><temp>20.1</temp></device>
        </devices>
        <sessions>
            <session><events><event><meta><trace>abc</trace></meta><value>10.0</value></event></events></session>
            <session><events><event><meta><trace>def</trace></meta><value>10.5</value></event></events></session>
        </sessions>
    </data>
    """

    xml2 = """
    <data>
        <user>
            <id>7</id>
            <profile><updated_at>2025-10-15T10:00:05Z</updated_at><age>30</age></profile>
        </user>
        <devices>
            <device><id>d1</id><debug>changed</debug><temp>20.05</temp></device>
            <device><id>d2</id><debug>changed</debug><temp>20.18</temp></device>
        </devices>
        <sessions>
            <session><events><event><meta><trace>xyz</trace></meta><value>10.01</value></event></events></session>
            <session><events><event><meta><trace>uvw</trace></meta><value>10.52</value></event></events></session>
        </sessions>
    </data>
    """

    ignore_fields = [
        "/data/user/profile/updated_at",
        "/data/devices/*/debug",
        "//trace",
    ]

    assert _compare_xml(
        xml1, xml2,
        ignore_fields=ignore_fields,
        abs_tol=0.05,
        rel_tol=0.02,
        show_debug=debug
    )


# --------------------------------------------------------------------------
# 5️⃣ ORDER AND STRUCTURE TESTS
# --------------------------------------------------------------------------

def test_child_count_mismatch():
    xml1 = "<items><item>1</item><item>2</item></items>"
    xml2 = "<items><item>1</item></items>"
    assert not _compare_xml(xml1, xml2, show_debug=debug)


def test_element_wildcard_tolerance():
    xml1 = """
    <sensors>
        <sensor><temp>20.0</temp></sensor>
        <sensor><temp>21.0</temp></sensor>
    </sensors>
    """
    xml2 = """
    <sensors>
        <sensor><temp>20.2</temp></sensor>
        <sensor><temp>21.1</temp></sensor>
    </sensors>
    """
    abs_tol_fields = {"//sensor/temp": 0.5}
    assert _compare_xml(xml1, xml2, abs_tol_fields=abs_tol_fields, show_debug=debug)


# --------------------------------------------------------------------------
# 6️⃣ COMPLEX REAL-WORLD EXAMPLE — Weather station
# --------------------------------------------------------------------------

def test_complex_weather_station():
    xml1 = """
    <station>
        <id>ST-42</id>
        <location>Paris</location>
        <version>1.0</version>
        <metrics>
            <temperature>21.5</temperature>
            <humidity>48.0</humidity>
            <pressure>1013.2</pressure>
            <wind_speed>5.4</wind_speed>
        </metrics>
        <status><battery_level>96.0</battery_level></status>
    </station>
    """

    xml2 = """
    <station>
        <id>ST-42</id>
        <location>Paris</location>
        <version>1.03</version>
        <metrics>
            <temperature>21.6</temperature>
            <humidity>49.3</humidity>
            <pressure>1013.5</pressure>
            <wind_speed>5.6</wind_speed>
        </metrics>
        <status><battery_level>94.8</battery_level></status>
    </station>
    """

    abs_tol_fields = {
        "/station/version": 0.1,
        "/station/metrics/humidity": 2.0,
        "/station/status/battery_level": 2.0,
    }

    rel_tol_fields = {
        "/station/metrics/wind_speed": 0.05,
    }

    assert _compare_xml(
        xml1,
        xml2,
        abs_tol=0.05,
        rel_tol=0.01,
        abs_tol_fields=abs_tol_fields,
        rel_tol_fields=rel_tol_fields,
        show_debug=True
    )
