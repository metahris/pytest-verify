# pytest-verify

**pytest-verify** is a snapshot testing plugin for **pytest** that
ensures your test outputs remain consistent across runs.

It automatically saves and compares snapshots of your test results and
can optionally launch a **visual diff viewer** for reviewing differences
directly in your terminal.

---

## Installation

Basic installation:

    pip install pytest-verify

With optional diff viewer:

    pip install pytest-verify[diff]

The <span class="title-ref">\[diff\]</span> extra adds an enhanced
terminal-based diff viewer for reviewing snapshot differences
interactively.

---

## Usage Overview

Any pytest test that **returns a value** can be decorated with
`@verify_snapshot`.

- On the **first run**, pytest-verify creates baseline snapshots.
- On **subsequent runs**, it compares the new output with the expected
  snapshot.
- If differences are detected, a diff is displayed (or the visual viewer
  opens).

---

## Text Example

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

## JSON Examples

1.  **Ignore fields**

``` python
from pytest_verify import verify_snapshot

@verify_snapshot(ignore_fields=["id"])
def test_json_ignore_fields():
    return {"id": 2, "name": "Mohamed"}
```

**Passes when:** - Ignored fields differ (`id`), but all other keys
match.

**Fails when:** - Non-ignored fields differ (e.g. `"name"`).

---

2.  **Numeric tolerance**

``` python
@verify_snapshot(abs_tol=1e-3)
def test_json_with_tolerance():
    return {"value": 3.1416}
```

**Passes when:** - Numeric values differ slightly within tolerance
(`abs_tol=0.001`).

**Fails when:** - The numeric difference exceeds the allowed tolerance.

---

3.  **Nested structure (order-sensitive vs insensitive)**

``` python
@verify_snapshot(ignore_order_json=False)
def test_json_nested_structure_order_sensitive():
    return {
        "team": {
            "members": [
                {"name": "John", "role": "Developer"},
                {"name": "Mary", "role": "Manager"}
            ]
        }
    }
```

**Passes when:** - The order of nested list elements (`members`) matches
the snapshot.

**Fails when:** - The list order changes (e.g. `Mary` before `John`)
while `ignore_order_json=False`.

If you set `ignore_order_json=True`, this same test **passes** because
list order is ignored.

---

## YAML Examples

1.  **Order-sensitive**

``` python
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

2.  **Ignore fields**

``` python
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

3.  **Numeric tolerance**

``` python
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

## XML Examples

1.  **Order-sensitive**

``` python
@verify_snapshot(ignore_order_xml=False)
def test_xml_order_sensitive():
    return "<root><a>1</a><b>2</b></root>"
```

**Passes when:** - The element order matches the saved snapshot.

**Fails when:** - Elements are swapped (e.g. `<b>2</b><a>1</a>`).

---

2.  **Numeric tolerance**

``` python
@verify_snapshot(abs_tol=0.02)
def test_xml_numeric_tolerance():
    return "<metrics><score>99.96</score></metrics>"
```

**Passes when:** - Numeric differences are within tolerance.

**Fails when:** - Values differ by more than the allowed tolerance.

---

## Pandas DataFrame Examples

1.  **Ignore columns**

``` python
import pandas as pd
from pytest_verify import verify_snapshot

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

2.  **Numeric tolerance**

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

## NumPy Array Examples

1.  **Numeric tolerance**

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

2.  **Type mismatch**

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

3.  **Missing values**

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
<td>⚠️ Shows diff or opens visual viewer.</td>
<td></td>
</tr>
<tr>
<td><strong>Change accepted</strong></td>
<td colspan="2">📝 Updates expected snapshot and keeps backup.</td>
</tr>
</tbody>
</table>

---

## Visual Diff Viewer

When installed with `pytest-verify[diff]`, an interactive terminal-based
diff viewer opens when snapshots differ.

- Highlights changes side-by-side in your terminal
- Lets you accept or reject new snapshots
- Works without any external tools

---

## Developer Notes

Local installation for development:

    pip install -e '.[all]'

Run the test suite:

    pytest -s

Clean generated snapshots:

    find . -name "*.actual.*" -delete

---

## License

Licensed under the **Apache License 2.0**.

---

## Author

**Mohamed Tahri** Email: `simotahri1@gmail.com` GitHub:
<https://github.com/metahris/pytest-verify>
