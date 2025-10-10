pytest-verify
=============

**pytest-verify** is a snapshot testing plugin for **pytest** that helps you verify that your test outputs remain consistent across runs.

It saves and compares snapshots of your test results and optionally provides a **visual diff viewer** for reviewing differences in a stylish terminal UI.

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
The first run creates baseline snapshots, and subsequent runs compare outputs to detect changes.

Basic Example
~~~~~~~~~~~~~

.. code-block:: python

    from pytest_verify.plugin import verify_snapshot

    @verify_snapshot()
    def test_simple_output():
        return "Hello, pytest-verify!"

**First run:**
  - Creates two files inside ``__snapshots__/``
    - ``test_simple_output.expected.txt``
    - ``test_simple_output.actual.txt``

**Later runs:**
  - Compares new output with existing expected snapshot
  - If they differ, shows a diff (or opens the visual diff viewer if installed)

---

JSON Example (with ignored fields)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pytest_verify.plugin import verify_snapshot

    @verify_snapshot(ignore_fields=["timestamp", "id"])
    def test_json_output():
        return {
            "name": "Mohamed",
            "timestamp": "2025-10-09T12:00:00Z",
            "id": 999,
            "score": 42
        }

This ignores specific JSON fields such as timestamps or dynamic IDs when comparing snapshots.

---

XML Example (order sensitivity)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pytest_verify.plugin import verify_snapshot

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

If installed via ``[diff]``, pytest-verify automatically uses a visual diff viewer.

- Opens automatically when snapshots differ
- Allows reviewing and accepting/rejecting changes interactively
- Works entirely in the terminal
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
