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

---

Usage
-----

You can decorate any pytest test function that **returns a value** with ``@verify_snapshot``.
On the first run, ``pytest-verify`` creates baseline snapshots. On subsequent runs, it compares the new output with the saved expected snapshot and highlights differences.

Basic Example
~~~~~~~~~~~~~

.. code-block:: python

    from pytest_verify import verify_snapshot

    @verify_snapshot()
    def test_simple_output():
        return "Hello, pytest-verify!"

**First run:**
  - Creates two files inside ``__snapshots__/``:
    - ``test_simple_output.expected.txt``
    - ``test_simple_output.actual.txt``

**Subsequent runs:**
  - Compares the new output with the existing expected snapshot.
  - If they differ, a diff is shown (or the visual diff viewer opens if installed).

---

JSON Example (with ignored fields)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pytest_verify import verify_snapshot

    @verify_snapshot(ignore_fields=["timestamp", "id"])
    def test_json_output():
        return {
            "name": "Mohamed",
            "timestamp": "2025-10-09T12:00:00Z",
            "id": 999,
            "score": 42
        }

This example ignores specific JSON fields (like timestamps or IDs) during comparison.

---

XML Example (order sensitivity)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pytest_verify import verify_snapshot

    @verify_snapshot(ignore_order_xml=False)
    def test_xml_order_sensitive():
        return """
        <users>
            <user id="1">Mohamed</user>
            <user id="2">Adnane</user>
        </users>
        """

Use ``ignore_order_xml=True`` to allow element reordering without failing.

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

---

Developer Notes
---------------

Local installation for development::

    pip install -e '.[diff]'

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
