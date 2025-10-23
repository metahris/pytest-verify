from pytest_verify import verify_snapshot


@verify_snapshot(ignore_fields=["timestamp"])
def test_yaml_snapshot():
    return """
    user:
      name: Mohamed
      id: 123
      timestamp: 2025-10-09
      active: true
    """


@verify_snapshot(ignore_order_yaml=False)
def test_yaml_ignore_list_order():
    return """
    steps:
      - do: f(x)
      - do: f'(x)
    """


@verify_snapshot(
    abs_tol_fields={"$.metrics.accuracy": 0.05},
    rel_tol_fields={"$.metrics.loss": 0.1},
    ignore_order_yaml=True
)
def test_yaml_numeric_tolerances():
    return """
    metrics:
      accuracy: 0.96
      loss: 0.105
      epoch: 10
    """
