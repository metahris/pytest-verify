from pytest_verify.plugin import _compare_json

debug = True


# --------------------------------------------------------------------------
# 1️⃣ BASIC TESTS — direct equality and simple mismatches
# --------------------------------------------------------------------------

def test_identical_dicts():
    a = '{"x": 1, "y": 2}'
    b = '{"x": 1, "y": 2}'
    assert _compare_json(a, b, show_debug=debug)


def test_simple_value_mismatch():
    a = '{"x": 1}'
    b = '{"x": 2}'
    assert not _compare_json(a, b, show_debug=debug)


def test_type_mismatch():
    a = '{"x": 1}'
    b = '{"x": "1"}'
    assert not _compare_json(a, b, show_debug=debug)


def test_key_mismatch():
    a = '{"x": 1}'
    b = '{"y": 1}'
    assert not _compare_json(a, b, show_debug=debug)


# --------------------------------------------------------------------------
# 2️⃣ TOLERANCE TESTS — abs_tol and rel_tol
# --------------------------------------------------------------------------

def test_global_abs_tolerance():
    a = '{"temp": 20.0}'
    b = '{"temp": 20.05}'
    assert _compare_json(a, b, abs_tol=0.1, show_debug=debug)


def test_global_tolerance_fail():
    a = '{"temp": 20.0}'
    b = '{"temp": 21.0}'
    assert not _compare_json(a, b, abs_tol=0.5, show_debug=debug)


def test_relative_tolerance_success():
    a = '{"humidity": 100.0}'
    b = '{"humidity": 104.0}'
    assert _compare_json(a, b, rel_tol=0.05, show_debug=debug)  # 5% tolerance


# --------------------------------------------------------------------------
# 3️⃣ FIELD-LEVEL TOLERANCE TESTS
# --------------------------------------------------------------------------

def test_per_field_abs_tolerance():
    a = '{"a": 1.0, "b": 2.0}'
    b = '{"a": 1.5, "b": 2.5}'
    abs_tol_fields = {"$.b": 1.0}
    assert _compare_json(a, b, abs_tol=0.5, abs_tol_fields=abs_tol_fields, show_debug=debug)


def test_per_field_rel_tolerance():
    a = '{"values": {"x": 100, "y": 200}}'
    b = '{"values": {"x": 110, "y": 210}}'
    rel_tol_fields = {"$.values.x": 0.2}  # 20%
    assert _compare_json(a, b, rel_tol=0.05, rel_tol_fields=rel_tol_fields, show_debug=debug)


# --------------------------------------------------------------------------
# 4️⃣ IGNORED FIELDS
# --------------------------------------------------------------------------

def test_ignore_path_root_field():
    a = '{"id": 1, "timestamp": "now"}'
    b = '{"id": 1, "timestamp": "later"}'

    # Ignore only the root timestamp field
    ignore_fields = ["$.timestamp"]

    assert _compare_json(a, b, ignore_fields=ignore_fields, show_debug=debug)


def test_ignore_fields_complex():
    """
    Ignore multiple paths with different patterns:
      - Exact path:            $.user.profile.updated_at
      - Array wildcard:        $.devices[*].debug
      - explicit deep trace path: $.sessions[*].events[*].meta.trace
    """
    a = """{
        "user": {
            "id": 7,
            "profile": {"updated_at": "2025-10-14T10:00:00Z", "age": 30}
        },
        "devices": [
            {"id": "d1", "debug": "alpha", "temp": 20.0},
            {"id": "d2", "debug": "beta", "temp": 20.1}
        ],
        "sessions": [
            {"events": [{"meta": {"trace": "abc"}, "value": 10.0}]},
            {"events": [{"meta": {"trace": "def"}, "value": 10.5}]}
        ]
    }"""

    b = """{
        "user": {
            "id": 7,
            "profile": {"updated_at": "2025-10-15T10:00:05Z", "age": 30}
        },
        "devices": [
            {"id": "d1", "debug": "changed", "temp": 20.05},
            {"id": "d2", "debug": "changed", "temp": 20.18}
        ],
        "sessions": [
            {"events": [{"meta": {"trace": "xyz"}, "value": 10.01}]},
            {"events": [{"meta": {"trace": "uvw"}, "value": 10.52}]}
        ]
    }"""

    # Ignore updated_at (exact), all device.debug (wildcard), any 'trace' anywhere (recursive)
    ignore_fields = [
        "$.user.profile.updated_at",
        "$.devices[*].debug",
        "$.sessions[*].events[*].meta.trace"
    ]

    # Small global tolerance to allow minor sensor/value drift
    assert _compare_json(
        a, b,
        ignore_fields=ignore_fields,
        abs_tol=0.05,
        rel_tol=0.02,
        show_debug=debug
    )


# --------------------------------------------------------------------------
# 5️⃣ LIST & WILDCARD TESTS
# --------------------------------------------------------------------------

def test_list_length_mismatch():
    a = '{"items": [1, 2, 3]}'
    b = '{"items": [1, 2]}'
    assert not _compare_json(a, b, show_debug=debug)


def test_array_specific_index_tolerance():
    a = '{"sensors": [{"temp": 20.0}, {"temp": 21.0}]}'
    b = '{"sensors": [{"temp": 20.05}, {"temp": 21.5}]}'
    abs_tol_fields = {"$.sensors[0].temp": 0.1, "$.sensors[1].temp": 1.0}  # only second sensor
    assert _compare_json(a, b, abs_tol_fields=abs_tol_fields, show_debug=debug)


def test_array_wildcard_tolerance():
    a = '{"sensors": [{"temp": 20.0}, {"temp": 21.0}]}'
    b = '{"sensors": [{"temp": 20.2}, {"temp": 21.1}]}'
    abs_tol_fields = {"$.sensors[*].temp": 0.5}
    assert _compare_json(a, b, abs_tol_fields=abs_tol_fields, show_debug=debug)


# --------------------------------------------------------------------------
# 6️⃣ PROPERTY & RECURSIVE WILDCARDS
# --------------------------------------------------------------------------

def test_property_wildcard_tolerance():
    a = '{"network": {"n1": {"v": 10}, "n2": {"v": 10}}}'
    b = '{"network": {"n1": {"v": 10.5}, "n2": {"v": 9.8}}}'
    abs_tol_fields = {"$.network.*.v": 1.0}
    assert _compare_json(a, b, abs_tol_fields=abs_tol_fields, show_debug=debug)


def test_deep_field_tolerance():
    a = '{"meta": {"deep": {"very": {"x": 100}}}}'
    b = '{"meta": {"deep": {"very": {"x": 101}}}}'
    abs_tol_fields = {"$.meta.deep.very.x": 2.0}
    assert _compare_json(a, b, abs_tol_fields=abs_tol_fields, show_debug=debug)


# --------------------------------------------------------------------------
# 7️⃣ COMPLEX SCENARIO — IoT network simulation
# --------------------------------------------------------------------------

def test_complex_nested_tolerance():
    old = """
    {
        "network": {
            "id": "site-001",
            "uptime_hours": 10234.5,
            "nodes": [
                {
                    "id": "N-A",
                    "metrics": {"temperature": 21.5, "humidity": 48.0, "voltage": 3.31, "packet_loss": 0.5}
                },
                {
                    "id": "N-B",
                    "metrics": {"temperature": 22.0, "humidity": 47.5, "voltage": 3.28, "packet_loss": 0.8}
                }
            ]
        },
        "gateway": {"battery": 87.0, "signal_strength": -68}
    }
    """

    new = """
    {
        "network": {
            "id": "site-001",
            "uptime_hours": 10236.2,
            "nodes": [
                {
                    "id": "N-A",
                    "metrics": {"temperature": 21.7, "humidity": 48.4, "voltage": 3.30, "packet_loss": 0.7}
                },
                {
                    "id": "N-B",
                    "metrics": {"temperature": 21.9, "humidity": 47.3, "voltage": 3.30, "packet_loss": 0.6}
                }
            ]
        },
        "gateway": {"battery": 86.2, "signal_strength": -70}
    }
    """

    abs_tol_fields = {
        "$.network.uptime_hours": 5.0,
        "$.gateway.battery": 2.0,
        "$.gateway.signal_strength": 3.0,
        "$.network.nodes[*].metrics.packet_loss": 0.5,
    }

    rel_tol_fields = {
        "$.network.nodes[*].metrics.temperature": 0.02,
        "$.network.nodes[*].metrics.humidity": 0.03,
        "$.network.nodes[*].metrics.voltage": 0.02,
    }

    assert _compare_json(
        old,
        new,
        abs_tol_fields=abs_tol_fields,
        rel_tol_fields=rel_tol_fields,
        show_debug=debug,
    )


def test_combined_global_and_field_tolerances():
    """
    Test a case mixing global and per-field tolerances:
    - Global tolerances: abs_tol=0.05, rel_tol=0.01
    - Field-specific tolerances override global ones
    - One field is ignored completely
    """

    a = """
    {
        "meta": {"version": 1.0, "id": "abc"},
        "sensor": {
            "temp": 21.5,
            "humidity": 48.0,
            "pressure": 101.3
        },
        "status": {
            "signal_strength": -70,
            "battery": 95.0
        }
    }
    """

    b = """
    {
        "meta": {"version": 1.02, "id": "abc"},
        "sensor": {
            "temp": 21.6,
            "humidity": 49.0, 
            "pressure": 101.4 
        },
        "status": {
            "signal_strength": -68,  
            "battery": 94.5  
        }
    }
    """

    abs_tol_fields = {
        "$.sensor.humidity": 2.0,  # large absolute tolerance
        "$.meta.version": 0.05  # tighter tolerance for version
    }

    rel_tol_fields = {
        "$.status.signal_strength": 0.05  # 5% relative tolerance allowed
    }

    ignore_fields = ["$.meta.id"]  # ignored entirely

    assert _compare_json(
        a,
        b,
        abs_tol=0.05,
        rel_tol=0.01,
        abs_tol_fields=abs_tol_fields,
        rel_tol_fields=rel_tol_fields,
        ignore_fields=ignore_fields,
        show_debug=True
    )
