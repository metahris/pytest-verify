from pytest_verify import verify_snapshot


# === Simple string example ===
@verify_snapshot()
def test_simple_text():
    return "Hello, Ayoub!"


# === JSON example with ignored fields and tolerances ===
@verify_snapshot(ignore_fields=["timestamp"], abs_tol=0.01, rel_tol=0.001)
def test_json_api_response():
    return {
        "user": "Ayoub",
        "timestamp": "2025-10-09T12:02:00Z",
        "value": 995,
        "a": "Ayoub",
        "b": "2025-10-09T12:00:00Z",
        "c": 99.995,
        "f": "Anas",
        "g": "2025-10-09T12:00:00Z",
        "h": 99.995,
        "u": "Ayoub",
        "n": "2025-10-09T12:00:00Z",
        "t": 992
    }


# === JSON mismatch example (to test diff) ===
@verify_snapshot()
def test_diff_example():
    return {"status": "ok", "count": 42}

@verify_snapshot(ignore_order_json=False)
def test_json_list_unordered():
    return {"v": [3, 1, 2], "nums": "b"}

@verify_snapshot(ignore_order_xml=True)
def test_xml_strict_order():
    return """<user><name>Ayoub</name><age>27</age></user>"""
