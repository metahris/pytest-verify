from pytest_verify import verify_snapshot


@verify_snapshot()
def test_simple_json_snapshot():
    """Tests consistent JSON snapshot comparison."""
    return """{"name": "Mohamed", "age": 28, "country": "Morocco"}"""


@verify_snapshot(ignore_fields=["$.duration", "$.timestamp"])
def test_json_with_ignore_fields():
    """Ignores specific JSON fields like timestamps and durations."""
    return """
    {
        "Job": "get_price",
        "price": "100",
        "duration": "20s",
        "timestamp": "2025-10-09T12:00:00Z"
    }
    """


@verify_snapshot(abs_tol=1e-4, rel_tol=1e-4)
def test_json_with_tolerances():
    """Tests numeric tolerance on floating-point values."""
    return """{"temperature": 21.0001, "humidity": 59.9999}"""


@verify_snapshot()
def test_json_order_sensitive():
    """Fails if order of list elements changes."""
    return """{
        "timestamp": [
            "2025-10-09T12:00:00Z",
            "2025-10-09T12:05:00Z"
        ],
        "product": ["x", "y"],
        "price": [20.001, 19.999]
    }"""


@verify_snapshot(abs_tol_fields={"$.network.*.v": 1.0})
def test_abs_tol_fields():
    return '{"network": {"n1": {"v": 10}, "n2": {"v": 10}}}'
