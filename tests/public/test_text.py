from pytest_verify import verify_snapshot

@verify_snapshot()
def test_basic_text_snapshot():
    """Verifies plain text snapshot comparison."""
    return "Hello, pytest-verify"

@verify_snapshot()
def test_multiline_text_snapshot():
    """Ensures diffs are handled correctly for multiline strings."""
    return """Line 1
Line 2
Line 3"""
