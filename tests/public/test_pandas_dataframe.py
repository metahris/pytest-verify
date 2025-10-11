import pandas as pd
from pytest_verify import verify_snapshot

@verify_snapshot(ignore_columns=["timestamp"], abs_tol=1e-4)
def test_dataframe_snapshot():
    """Tests DataFrame snapshot with numeric tolerance and ignored columns."""
    df = pd.DataFrame({
        "timestamp": [
            "2025-10-09T12:00:00Z",
            "2025-10-09T12:05:00Z"
        ],
        "product": ["x", "y"],
        "price": [20.001, 19.999]
    })
    return df
