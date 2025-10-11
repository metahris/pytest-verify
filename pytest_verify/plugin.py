from __future__ import annotations

import difflib
import inspect
import json
import math
import shutil
import subprocess
import xml.dom.minidom
import xml.etree.ElementTree as ET
from functools import wraps
from pathlib import Path

import click
from rich.console import Console
from rich.syntax import Syntax

import dataclasses

# Optional dependencies
try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
except ImportError:
    pd = None

console = Console()


# ========== HELPERS ========== #

def _detect_format(result) -> str:
    """Detect snapshot format based on type."""
    if BaseModel and isinstance(result, BaseModel):
        return "pydantic"
    if dataclasses.is_dataclass(result):
        return "dataclass"
    if np and isinstance(result, np.ndarray):
        return "ndarray"
    if pd and isinstance(result, pd.DataFrame):
        return "dataframe"
    if isinstance(result, (dict, list)):
        return "json"
    if isinstance(result, bytes):
        return "bin"
    if isinstance(result, str):
        if result.strip().startswith("<") and result.strip().endswith(">"):
            return "xml"
        return "txt"
    return "txt"


def _serialize_result(result, fmt: str) -> str | bytes:
    """Serialize Python result to string or bytes."""
    if fmt == "pydantic":
        if not BaseModel:
            raise ImportError(
                "Pydantic support requires 'pydantic'. Install via: pip install pytest-verify[pydantic]"
            )
        data = result.model_dump()
        return json.dumps(data, indent=2, sort_keys=True)

    if fmt == "dataclass":
        data = dataclasses.asdict(result)
        return json.dumps(data, indent=2, sort_keys=True)

    if fmt == "ndarray":
        if not np:
            raise ImportError(
                "NumPy support requires 'numpy'. Install via: pip install pytest-verify[numpy]"
            )
        return json.dumps(result.tolist(), indent=2)

    if fmt == "dataframe":
        if not pd:
            raise ImportError(
                "Pandas support requires 'pandas'. Install via: pip install pytest-verify[pandas]"
            )
        return result.to_csv(index=False)

    if fmt == "json":
        return json.dumps(result, indent=2, sort_keys=True)

    if fmt == "xml":
        try:
            parsed = xml.dom.minidom.parseString(result)
            return parsed.toprettyxml()
        except Exception:
            return str(result)

    if fmt == "txt":
        return str(result)

    if fmt == "bin":
        return result

    return str(result)


def _get_snapshot_paths(func_name: str, fmt: str, dir: str | Path) -> tuple[Path, Path]:
    """Return paths for expected and actual snapshots based on format."""
    # Choose file extension based on detected format
    ext = (
        ".json" if fmt in {"json", "pydantic", "dataclass", "ndarray"} else
        ".xml" if fmt == "xml" else
        ".bin" if fmt == "bin" else
        ".csv" if fmt == "dataframe" else
        ".txt"
    )

    base = Path(dir) / f"{func_name}"
    expected = base.with_suffix(f".expected{ext}")
    actual = base.with_suffix(f".actual{ext}")

    expected.parent.mkdir(exist_ok=True, parents=True)
    return expected, actual


def _load_snapshot(path: Path) -> str | bytes | None:
    """Read existing snapshot if available."""
    if not path.exists():
        return None
    mode = "rb" if path.suffix == ".bin" else "r"
    return path.read_bytes() if mode == "rb" else path.read_text(encoding="utf-8")


def _save_snapshot(path: Path, content: str | bytes):
    """Write snapshot to disk."""
    mode = "wb" if isinstance(content, bytes) else "w"
    if mode == "wb":
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    console.print(f"💾 [green]Saved snapshot:[/green] {path}")


def _backup_expected(path: Path):
    """Create a backup of the current expected snapshot before overwriting."""
    if not path.exists():
        return
    backup_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy(path, backup_path)
    console.print(f"🗂️  [yellow]Backup created:[/yellow] {backup_path}")


def _ask_to_replace(path: Path) -> bool:
    """Ask user whether to replace snapshot."""
    return click.confirm(f"Snapshot mismatch. Replace {path}?", default=False)


# ========== DIFF VIEWERS ========== #

def _show_diff_python(old: str, new: str, path: Path):
    """Fallback diff using difflib + rich."""
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=f"{path} (expected)",
        tofile=f"{path} (actual)",
        lineterm=""
    )
    diff_text = "\n".join(diff)
    syntax = Syntax(diff_text, "diff", theme="ansi_dark")
    console.print(syntax)


def _run_rust_diff(expected: Path, actual: Path) -> bool | None:
    """
    Try to run the Rust diff viewer if installed.
    Returns:
      True  → user accepted (exit code 0)
      False → user rejected (exit code 1)
      None  → viewer not available, use fallback
    """
    exe = shutil.which("verify-diff-bin")
    if not exe:
        return None
    try:
        result = subprocess.run([exe, str(expected), str(actual)])
        return result.returncode == 0
    except Exception:
        return None


# ========== COMPARERS ========== #

_COMPARERS = {}


def _register_comparer(fmt):
    def decorator(func):
        _COMPARERS[fmt] = func
        return func

    return decorator


@_register_comparer("json")
def _compare_json(
        old: str,
        new: str,
        *,
        ignore_fields=None,
        abs_tol=None,
        rel_tol=None,
        ignore_order_json=True,
) -> bool:
    """Compare JSON structures with optional field ignores, numeric tolerance, and array order control."""

    ignore_fields = ignore_fields or []
    abs_tol = abs_tol or 0
    rel_tol = rel_tol or 0

    def _is_number(v):
        try:
            float(v)
            return True
        except (ValueError, TypeError):
            return False

    def _remove_ignored(obj):
        if isinstance(obj, dict):
            return {k: _remove_ignored(v) for k, v in obj.items() if k not in ignore_fields}
        if isinstance(obj, list):
            return [_remove_ignored(i) for i in obj]
        return obj

    def _deep_compare(a, b):
        if type(a) != type(b):
            return False

        if isinstance(a, dict):
            if a.keys() != b.keys():
                return False
            return all(_deep_compare(a[k], b[k]) for k in a)

        if isinstance(a, list):
            if len(a) != len(b):
                return False
            if ignore_order_json:
                # Ignore list order
                return sorted(a, key=lambda x: str(x)) == sorted(b, key=lambda x: str(x))
            return all(_deep_compare(x, y) for x, y in zip(a, b))

        if _is_number(a) and _is_number(b):
            return math.isclose(float(a), float(b), abs_tol=abs_tol, rel_tol=rel_tol)

        return a == b

    old_obj = json.loads(old)
    new_obj = json.loads(new)

    return _deep_compare(_remove_ignored(old_obj), _remove_ignored(new_obj))


@_register_comparer("txt")
def _compare_text(old: str, new: str, **_):
    return old.strip() == new.strip()


@_register_comparer("bin")
def _compare_bin(old: bytes, new: bytes, **_):
    return old == new


@_register_comparer("xml")
def _compare_xml(
        old: str,
        new: str,
        *,
        ignore_fields=None,
        abs_tol=None,
        rel_tol=None,
        ignore_order_xml=True,
) -> bool:
    """Compare XML documents structurally with tolerance, ignored fields, and optional order control."""

    ignore_fields = set(ignore_fields or [])
    abs_tol = abs_tol or 0
    rel_tol = rel_tol or 0

    def _is_number(v):
        try:
            float(v)
            return True
        except (ValueError, TypeError):
            return False

    def _compare_txt(a, b):
        if _is_number(a) and _is_number(b):
            return math.isclose(float(a), float(b), abs_tol=abs_tol, rel_tol=rel_tol)
        return (a or "").strip() == (b or "").strip()

    def _compare_elements(e1, e2):
        if e1.tag in ignore_fields or e2.tag in ignore_fields:
            return True
        if e1.tag != e2.tag:
            return False

        # Compare attributes (unordered)
        attrs1 = {k: v for k, v in e1.attrib.items() if k not in ignore_fields}
        attrs2 = {k: v for k, v in e2.attrib.items() if k not in ignore_fields}
        if attrs1.keys() != attrs2.keys():
            return False
        for k in attrs1:
            if not _compare_txt(attrs1[k], attrs2[k]):
                return False

        # Compare text
        if not _compare_txt(e1.text or "", e2.text or ""):
            return False

        # Compare children
        c1, c2 = list(e1), list(e2)
        if len(c1) != len(c2):
            return False
        if ignore_order_xml:
            def key_fn(el): return (el.tag, tuple(sorted(el.attrib.items())))

            c1.sort(key=key_fn)
            c2.sort(key=key_fn)
        for child1, child2 in zip(c1, c2):
            if not _compare_elements(child1, child2):
                return False

        if not _compare_txt(e1.tail or "", e2.tail or ""):
            return False
        return True

    try:
        root1 = ET.fromstring(old)
        root2 = ET.fromstring(new)
    except ET.ParseError:
        return old.strip() == new.strip()

    return _compare_elements(root1, root2)


@_register_comparer("pydantic")
def _compare_pydantic(old: str, new: str, **kwargs):
    """Compare two Pydantic model snapshots as JSON."""
    return _compare_json(old, new, **kwargs)


@_register_comparer("dataclass")
def _compare_dataclass(old: str, new: str, **kwargs):
    """Compare dataclass snapshots as JSON."""
    return _compare_json(old, new, **kwargs)


@_register_comparer("ndarray")
def _compare_ndarray(old: str, new: str, *, abs_tol=None, rel_tol=None, **_):
    """Compare NumPy arrays element-wise with tolerance."""
    if np is None:
        raise ImportError("NumPy support requires 'numpy'. Install via: pip install pytest-verify[numpy]")

    old_arr = np.array(json.loads(old))
    new_arr = np.array(json.loads(new))
    if old_arr.shape != new_arr.shape:
        return False
    abs_tol = abs_tol or 0
    rel_tol = rel_tol or 0
    return np.allclose(old_arr, new_arr, atol=abs_tol, rtol=rel_tol)


@_register_comparer("dataframe")
def _compare_dataframe(
    old: str,
    new: str,
    *,
    ignore_columns=None,
    abs_tol: float | None = None,
    rel_tol: float | None = None,
    **_,
):
    """Compare Pandas DataFrames by content, with support for ignored columns and numeric tolerances."""
    if pd is None:
        raise ImportError("Pandas support requires 'pandas'. Install via: pip install pytest-verify[pandas]")

    from io import StringIO

    # Load both snapshots as DataFrames
    old_df = pd.read_csv(StringIO(old))
    new_df = pd.read_csv(StringIO(new))

    # Drop ignored columns if requested
    if ignore_columns:
        ignore_columns = [col for col in ignore_columns if col in old_df.columns or col in new_df.columns]
        old_df = old_df.drop(columns=[c for c in ignore_columns if c in old_df.columns], errors="ignore")
        new_df = new_df.drop(columns=[c for c in ignore_columns if c in new_df.columns], errors="ignore")

    # Ensure same columns and order
    if set(old_df.columns) != set(new_df.columns):
        return False

    # Align columns (to be consistent in order)
    old_df = old_df[new_df.columns]

    # Check shape
    if old_df.shape != new_df.shape:
        return False

    abs_tol = abs_tol or 0
    rel_tol = rel_tol or 0

    # Compare numeric and non-numeric separately
    try:
        for col in old_df.columns:
            old_col = old_df[col]
            new_col = new_df[col]

            # Case 1: Numeric comparison with tolerance
            if pd.api.types.is_numeric_dtype(old_col) and pd.api.types.is_numeric_dtype(new_col):
                # If any numeric mismatch exceeds tolerance → fail
                if not np.allclose(
                    old_col.fillna(0).to_numpy(),
                    new_col.fillna(0).to_numpy(),
                    atol=abs_tol,
                    rtol=rel_tol,
                    equal_nan=True,
                ):
                    return False
            else:
                # Case 2: Non-numeric exact comparison (ignoring NaN differences)
                if not old_col.fillna("").equals(new_col.fillna("")):
                    return False

        return True
    except Exception:
        return False



def _compare_snapshots(old, new, fmt, **kwargs) -> bool:
    """Delegate comparison to the appropriate comparer."""
    comparer = _COMPARERS.get(fmt)
    if not comparer:
        console.print(f"[yellow]⚠️ No comparer for format '{fmt}', using text fallback[/yellow]")
        comparer = _compare_text

    # Filter kwargs to only those accepted by the comparer
    sig = inspect.signature(comparer)
    accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}

    return comparer(old, new, **accepted)


# ========== VERIFY ========== #

def verify_snapshot(
        snapshot_name: str | None = None,
        dir: str = "__snapshots__",  # default name for snapshot subfolder
        *,
        ignore_fields: list[str] | None = None,
        ignore_columns: list[str] | None = None,
        abs_tol: float | None = None,
        rel_tol: float | None = None,
        ignore_order_json: bool = True,
        ignore_order_xml: bool = True,
):
    """
    Decorator that saves and compares test results as snapshots.
    Snapshots are stored in a `__snapshots__` folder located
    next to the test file that defines the test function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # === Run test and serialize result ===
            result = func(*args, **kwargs)
            fmt = _detect_format(result)
            content = _serialize_result(result, fmt)

            # === Determine test file location ===
            test_file_path = Path(inspect.getfile(func)).resolve()
            snapshot_dir = test_file_path.parent / dir
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            # === Compute snapshot paths ===
            name = snapshot_name or func.__name__
            expected_path, actual_path = _get_snapshot_paths(name, fmt, snapshot_dir)

            # === First run: create baseline ===
            if not expected_path.exists():
                _save_snapshot(expected_path, content)
                _save_snapshot(actual_path, content)
                console.print(f"📸 First run → Created baseline snapshots for [bold]{name}[/bold]")
                return result

            # === Load expected + save new actual ===
            expected_content = _load_snapshot(expected_path)
            _save_snapshot(actual_path, content)

            # === Compare snapshots ===
            matches = _compare_snapshots(
                expected_content,
                content,
                fmt,
                ignore_fields=ignore_fields,
                ignore_columns=ignore_columns,
                abs_tol=abs_tol,
                rel_tol=rel_tol,
                ignore_order_json=ignore_order_json,
                ignore_order_xml=ignore_order_xml,
            )

            # === If matches ===
            if matches:
                console.print(f"✅ Snapshot matches: [green]{expected_path}[/green]")
                _save_snapshot(expected_path, content)
                return result

            # === Mismatch detected ===
            console.print(f"⚠️ Snapshot mismatch detected for [bold]{name}[/bold]")

            # Try Rust diff viewer first
            rust_result = _run_rust_diff(expected_path, actual_path)

            if rust_result:
                _backup_expected(expected_path)
                _save_snapshot(expected_path, content)
                console.print(f"📝 Snapshot updated → {expected_path}")
                return result

            elif rust_result is False:
                console.print(f"❌ Changes rejected by user for {expected_path}")
                raise AssertionError(f"Snapshot mismatch for {expected_path}")

            # === Fallback to Python diff ===
            _show_diff_python(
                expected_content.decode("utf-8") if isinstance(expected_content, bytes) else expected_content,
                content.decode("utf-8") if isinstance(content, bytes) else content,
                expected_path,
            )

            if _ask_to_replace(expected_path):
                _backup_expected(expected_path)
                _save_snapshot(expected_path, content)
                console.print(f"📝 Snapshot updated → {expected_path}")
            else:
                console.print(f"❌ Mismatch kept. Review: {expected_path} and {actual_path}")
                raise AssertionError(f"Snapshot mismatch for {expected_path}")

            return result

        return wrapper

    return decorator

