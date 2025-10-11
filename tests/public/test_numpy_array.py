import numpy as np
from pytest_verify import verify_snapshot

@verify_snapshot(abs_tol=1e-5, rel_tol=1e-5)
def test_numpy_snapshot():
    """Tests NumPy array snapshot comparison with tolerances."""
    return np.array([[1.00001, 2.00002], [3.00003, 4.00004]])
