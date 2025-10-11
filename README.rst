pytest-verify
=============

**pytest-verify** is a snapshot testing plugin for **pytest** that helps ensure your test outputs remain consistent across runs.

It automatically saves and compares snapshots of your test results and optionally provides a **visual diff viewer** for reviewing differences directly in your terminal.

---

Installation
------------

Basic installation::

    pip install pytest-verify

With optional visual diff viewer::

    pip install pytest-verify[diff]

The ``[diff]`` extra installs an enhanced terminal-based diff viewer for reviewing snapshot differences interactively.

If you plan to test **pandas**, **numpy**, or **pydantic** objects, install extras::

    pip install pytest-verify[pandas,numpy,pydantic]

You can also combine everything::

    pip install pytest-verify[all]

---

Usage
-----

You can decorate any pytest test function that **returns a value** with ``@verify_snapshot``.

- On the **first run**, pytest-verify creates baseline snapshots.
- On **subsequent runs**, it compares the new output with the saved expected snapshot and highlights differences.

If outputs differ, you’ll see a colorized diff in the terminal or, if installed, the visual diff viewer will open automatically.

---

Basic Example (Text)
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pytest_verify import verify_snapshot

    @verify_snapshot()
    def test_greeting():
        return "Hello, pytest-verify!"

**First run:**
  - Creates two files inside ``__snapshots__/``:
    - ``test_greeting.expected.txt``
    - ``test_greeting.actual.txt``

**Subsequent runs:**
  - Compares the new output with the existing expected snapshot.
  - If they differ, a diff is shown (or the visual diff viewer opens if installed).

**Snapshot mismatch with diff viewer**

.. image:: docs/test_text_failed.png
   :alt: Snapshot diff viewer example
   :align: center
   :width: 600px

---
 - At some point, 'test_greetings()' started returning "Hello, pytest-verify, your're so cool!".

 🗨️  Test FAILED, pytest-verify will ask whether to replace the expected snapshot with the new one or not.

JSON Example (Ignored Fields & Tolerance)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pytest_verify import verify_snapshot

    @@verify_snapshot()
    def test_simple_json_snapshot():
        return {"name": "Mohamed", "age": 28, "country": "Morocco"}

**Snapshot mismatch with diff viewer**

.. image:: docs/test_simple_json_failed.png
   :alt: Snapshot diff viewer example
   :align: center
   :width: 600px

---

Ignore specific JSON fields:

.. code-block:: python

    @verify_snapshot(ignore_fields=["duration", "timestamp"])
    def test_json_with_ignore_fields():
        return {
            "Job": "get_price",
            "price": "100",
            "duration": "20s",
            "timestamp": "2025-10-09T12:00:00Z"
        }

---

Test numeric tolerance on floating-point values:

.. code-block:: python

    @verify_snapshot(abs_tol=1e-4, rel_tol=1e-4)
    def test_json_with_tolerances():
        return {"temperature": 21.0001, "humidity": 59.9999}

---

Fails if order of list elements changes:

.. code-block:: python

    @verify_snapshot(ignore_order_json=False)
    def test_json_order_sensitive():
        return {
            "users": [
                {"id": 1, "job_name": "get_price"},
                {"id": 2, "job_name": "get_delta"}
            ]
        }

---

.. image:: docs/test_json_order_failed.png
   :alt: Snapshot diff viewer example
   :align: center
   :width: 600px

---

XML Example (Order Sensitivity)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pytest_verify import verify_snapshot

    @verify_snapshot(ignore_order_xml=False)
    def test_xml_snapshot_order_sensitive():
        return """
        <users>
            <user id="1">Mohamed</user>
            <user id="2">Adnane</user>
        </users>
        """

If you reorder the elements, the test will fail.

**# should fail example:**

.. code-block:: xml

    <users>
        <user id="2">Adnane</user>
        <user id="1">Mohamed</user>
    </users>

---

.. image:: docs/test_xml_order_failed.png
   :alt: Snapshot diff viewer example
   :align: center
   :width: 600px

---

it is order-insensitive by default ``ignore_order_xml=True``.

Verify that small numeric differences in XML attributes or values are tolerated within the given abs/rel tolerance.

.. code-block:: python

    @verify_snapshot(abs_tol=1e-3, rel_tol=1e-3)
    def test_xml_with_numeric_tolerance():
        return """
        <measurements>
            <temperature value="20.001" unit="C"/>
            <pressure>101.325</pressure>
        </measurements>
        """

Dataclass Example
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from dataclasses import dataclass
    from pytest_verify import verify_snapshot

    @dataclass
    class User:
        id: int
        name: str
        country: str

    @verify_snapshot(ignore_fields=["id"])
    def test_dataclass_snapshot():
        return User(id=123, name="Ayoub", country="France")

The dataclass is automatically serialized to JSON and compared on each test run.

---

Pydantic Example (Float Tolerance)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pydantic import BaseModel
    from pytest_verify import verify_snapshot

    class Product(BaseModel):
        id: int
        name: str
        price: float

    @verify_snapshot(ignore_fields=["id"], abs_tol=1e-3)
    def test_pydantic_snapshot():
        return Product(id=1, name="Laptop", price=999.999)

**Requires:** ``pip install pytest-verify[pydantic]``

---

Pandas DataFrame Example
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    from pytest_verify import verify_snapshot

    @verify_snapshot(ignore_columns=["timestamp"], abs_tol=1e-4)
    def test_dataframe_snapshot():
        df = pd.DataFrame({
            "timestamp": ["2025-10-09T12:00:00Z", "2025-10-09T12:05:00Z"],
            "city": ["Paris", "Lyon"],
            "temperature": [20.001, 19.999],
            "humidity": [55, 60],
        })
        return df

This test compares DataFrames with numerical tolerance and ignored columns.

**Requires:** ``pip install pytest-verify[pandas]``

---

NumPy Array Example
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import numpy as np
    from pytest_verify import verify_snapshot

    @verify_snapshot(abs_tol=1e-4, rel_tol=1e-4)
    def test_numpy_snapshot():
        return np.array([[1.0001, 2.0001], [3.0002, 4.0003]])

**Requires:** ``pip install pytest-verify[numpy]``


---

Behavior Summary
----------------

======================  ===========================================================
Step                    Description
======================  ===========================================================
First run               Creates both `.expected` and `.actual` snapshots (identical)
Later runs              Compares new output with existing `.expected`
Match                   ✅ Confirms match and updates snapshot
Mismatch                ⚠️ Shows diff or opens visual viewer
Accept changes           📝 Updates `.expected` and saves a `.bak` backup
======================  ===========================================================

---

Visual Diff Viewer
------------------

If installed via ``[diff]``, pytest-verify automatically uses a visual diff viewer:

- Opens automatically when snapshots differ.
- Allows reviewing and accepting/rejecting changes interactively.
- Works entirely within the terminal — no external tools required.

**Requires:** ``pip install pytest-verify[diff]``

---

Developer Notes
---------------

Local installation for development::

    pip install -e '.[all]'

Run tests::

    pytest -s

Clean old snapshots::

    find . -name "*.actual.*" -delete

---

License
-------

Licensed under the **Apache License 2.0**.

Author
------

**Mohamed Tahri**  
Email: simotahri1@gmail.com  
GitHub: https://github.com/metahris/pytest-verify
