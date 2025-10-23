# pytest-verify

**pytest-verify** is a snapshot testing plugin for **pytest** that
ensures your test outputs remain consistent across runs.

It automatically saves and compares snapshots of your test results and
can launch a **visual diff viewer** for reviewing differences
directly in your terminal.

---

## Installation

Basic installation:

    pip install pytest-verify

---

## Usage Overview

Any pytest test that **returns a value** can be decorated with
`@verify_snapshot`.

- On the **first run**, pytest-verify creates baseline snapshots.
- On **subsequent runs**, it compares the new output with the expected
  snapshot.
- If differences are detected, a diff is displayed:

![screenshot](docs/images/test_simple_json_failed.png)

🗨⚠️  Test FAILED, pytest-verify will ask whether to replace the expected.

💡 How This Works ?
===================

``` python
from pytest_verify import verify_snapshot


@verify_snapshot(
    ignore_fields=[
        "$.user.profile.updated_at",
        "$.devices[*].debug",
        "$.sessions[*].events[*].meta.trace",
    ],
    abs_tol=0.05,
    rel_tol=0.02,
)
def test_ignore_multiple_fields():
    """
      - Exact path:            $.user.profile.updated_at
      - Array wildcard:        $.devices[*].debug
      - Deep nested wildcard:  $.sessions[*].events[*].meta.trace
    """
    return {
        "user": {
            "id": 7,
            "profile": {"updated_at": "2025-10-14T10:00:00Z", "age": 30},
        },
        "devices": [
            {"id": "d1", "debug": "alpha", "temp": 20.0},
            {"id": "d2", "debug": "beta", "temp": 20.1},
        ],
        "sessions": [
            {"events": [{"meta": {"trace": "abc"}, "value": 10.0}]},
            {"events": [{"meta": {"trace": "def"}, "value": 10.5}]},
        ],
    }
```


The decorator ``@verify_snapshot`` automatically performs the following steps:

1. **Format Detection**  
   Detects that the return value is a JSON snapshot (because the test returns a Python ``dict``).

2. **Serialization**  
   Serializes the result into a canonical, pretty-formatted JSON string.

3. **Comparison**  
   Compares the serialized result against the existing ``.expected.json`` snapshot file.


5. **Baseline Creation**  
   On the first test run, if no snapshot exists, a baseline file is created:

   ::

       __snapshots__/test_ignore_fields_complex.expected.json

6. **Subsequent Runs**  
   On later runs, the result is compared to the existing snapshot.
   If differences occur outside the ignored fields or tolerance limits,
   a unified diff is displayed in the terminal.


## Examples

``` python
from pytest_verify import verify_snapshot

@verify_snapshot()
def test_text_snapshot():
    return "Hello, pytest-verify!"
```

**Passes when:** - The returned text is identical to the saved
snapshot. - Whitespace at the start or end of the string is ignored.

**Fails when:** - The text content changes (e.g. `"Hello, pytest!"`).

---

``` python
from pytest_verify import verify_snapshot
# ignore fields
@verify_snapshot(ignore_fields=["id"])
def test_ignore_fields():
    return {"id": 2, "name": "Mohamed"}
```

**Passes when:** - Ignored fields differ (`id`), but all other keys
match.

**Fails when:** - Non-ignored fields differ (e.g. `"name"`).

---

``` python
# numeric tolerance
@verify_snapshot(abs_tol=1e-3; rel_tol=1e-3)
def test_with_tolerance():
    return {"value": 3.1416}
```

**Passes when:** - Numeric values differ slightly within tolerance
(`abs_tol=0.001`).

**Fails when:** - The numeric difference exceeds the allowed tolerance.

---

``` python
# abs tol fields in json
@verify_snapshot(abs_tol_fields = {"$.network.*.v": 1.0})
def test_abs_tol_fields():
    return '{"network": {"n1": {"v": 10}, "n2": {"v": 10}}}'
```

**Passes when:** - Numeric values of (`v`) differ within tolerance.

**Fails when:** - The numeric difference of (`v`) exceeds the allowed tolerance.

---

``` python
# yaml ignore order
@verify_snapshot(ignore_order_yaml=False)
def test_yaml_order_sensitive():
    return """
    fruits:
      - apple
      - banana
    """
```

**Passes when:** - The order of YAML list items is identical.

**Fails when:** - The order changes while order sensitivity is enforced.

---

``` python
# yanl ignore fields
@verify_snapshot(ignore_fields=["age"])
def test_yaml_ignore_fields():
    return """
    person:
      name: Alice
      age: 31
      city: Paris
    """
```

**Passes when:** - Ignored fields (`age`) differ.

**Fails when:** - Any non-ignored fields differ.

---

``` python
# numeric tolerance
@verify_snapshot(abs_tol=0.02)
def test_yaml_numeric_tolerance():
    return """
    metrics:
      accuracy: 99.96
    """
```

**Passes when:** - Numeric values differ within the given absolute
tolerance.

**Fails when:** - The difference exceeds the allowed tolerance.

---

``` python
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
```


``` python
# xml numeric tolerance
@verify_snapshot(abs_tol=0.02)
def test_xml_numeric_tolerance():
    return "<metrics><score>99.96</score></metrics>"
```

**Passes when:** - Numeric differences are within tolerance.

**Fails when:** - Values differ by more than the allowed tolerance.

---

``` python
# xml numeric tolerance per field
@verify_snapshot(abs_tol_fields={"//sensor/temp": 0.5})
def test_xml_abs_tol_fields():
    return """
    <sensors>
        <sensor><temp>20.0</temp></sensor>
        <sensor><temp>21.0</temp></sensor>
    </sensors>
    """
```

**Passes when:** - Numeric values of (`temp`) differ within tolerance.

**Fails when:** - The numeric difference of (`temp`) exceeds the allowed tolerance.


``` python
import pandas as pd
from pytest_verify import verify_snapshot

# ignore columns
@verify_snapshot(ignore_columns=["B"])
def test_dataframe_ignore_columns():
    df = pd.DataFrame({
        "A": [1, 4],
        "B": [2, 9],   # ignored column
        "C": [3, 6],
    })
    return df
```

**Passes when:** - Ignored columns differ (`B`), but all other columns
match.

**Fails when:** - Non-ignored columns differ or structure changes.

---

``` python
import pandas as pd
from pytest_verify import verify_snapshot

@verify_snapshot(abs_tol=0.02)
def test_dataframe_tolerance():
    df = pd.DataFrame({
        "A": [1.00, 3.00],
        "B": [2.00, 4.00],
    })
    return df
```

**Passes when:** - Numeric differences between runs are within tolerance
(≤ 0.02).

**Fails when:** - Numeric difference exceeds tolerance (e.g. 0.0001).

---

``` python
import numpy as np
from pytest_verify import verify_snapshot

@verify_snapshot(abs_tol=0.01)
def test_numpy_array_tolerance():
    return np.array([[1.001, 2.0, 3.0]])
```

**Passes when:** - Element-wise numeric differences are within 0.01.

**Fails when:** - Differences exceed tolerance.

---

``` python
import numpy as np
from pytest_verify import verify_snapshot

@verify_snapshot()
def test_numpy_array_type_mismatch():
    return np.array([["1", "2", "3"]], dtype=object)
```

**Passes when:** - Element types match expected (e.g. all numeric).

**Fails when:** - Element types differ (e.g. numeric vs string).

---

``` python
import numpy as np
from pytest_verify import verify_snapshot

@verify_snapshot()
def test_numpy_array_with_none():
    return np.array([[1, None, 3]], dtype=object)
```

**Passes when:** - Missing values (<span class="title-ref">None</span> /
<span class="title-ref">NaN</span>) are in the same positions.

**Fails when:** - Missing values occur in different positions or types
differ.

---

## Behavior Summary

<table style="width:99%;">
<colgroup>
<col style="width: 31%" />
<col style="width: 65%" />
<col style="width: 1%" />
</colgroup>
<thead>
<tr>
<th>Step</th>
<th>Description</th>
<th></th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>First run</strong></td>
<td>Creates both <code>.expected</code> and <code>.actual</code>
files.</td>
<td></td>
</tr>
<tr>
<td><strong>Subsequent runs</strong></td>
<td>Compares new output with the saved snapshot.</td>
<td></td>
</tr>
<tr>
<td><strong>Match found</strong></td>
<td colspan="2">✅ Snapshot confirmed and updated.</td>
</tr>
<tr>
<td><strong>Mismatch detected</strong></td>
<td>⚠️ Shows diff on terminal.</td>
<td></td>
</tr>
<tr>
<td><strong>Change accepted</strong></td>
<td colspan="2">📝 Updates expected snapshot and keeps backup.</td>
</tr>
</tbody>
</table>

---

## Developer Notes

Local installation for development:

    pip install -e '.[all]'

Run the test suite:

    pytest -v -s

---

## License

Licensed under the **Apache License 2.0**.

---

## Author

**Mohamed Tahri** Email: `simotahri1@gmail.com` GitHub:
<https://github.com/metahris/pytest-verify>
