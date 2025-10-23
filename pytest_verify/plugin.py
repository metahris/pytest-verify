from __future__ import annotations

import dataclasses
import datetime
import difflib
import inspect
import json
import shutil
import xml.dom.minidom
from functools import wraps
from pathlib import Path
from typing import Dict, List

import click
import pytest
import yaml
from dictlens import compare_dicts
from rich.console import Console
from rich.syntax import Syntax
from xmllens import compare_xml

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
        stripped = result.strip()
        if stripped.startswith("<") and stripped.endswith(">"):
            return "xml"
        if any(ch in stripped for ch in [":", "-"]) and "\n" in stripped:
            try:
                yaml.safe_load(stripped)
                return "yaml"
            except Exception:
                pass
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

    if fmt == "yaml":
        try:
            # If the result is already a dict/list, just dump it
            if isinstance(result, (dict, list)):
                return yaml.dump(result, sort_keys=True, indent=2)
            # If it's a YAML string, parse and re-dump it canonically
            parsed = yaml.safe_load(result)
            return yaml.dump(parsed, sort_keys=True, indent=2)
        except Exception:
            return str(result)

    return str(result)


def _get_snapshot_paths(func_name: str, fmt: str, dir: str | Path) -> tuple[Path, Path]:
    """Return paths for expected and actual snapshots based on format."""
    # Choose file extension based on detected format
    ext = (
        ".json" if fmt in {"json", "pydantic", "dataclass", "ndarray"} else
        ".xml" if fmt == "xml" else
        ".yaml" if fmt == "yaml" else
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

def _show_diff(old: str, new: str, expected_path: Path, actual_path: Path, fmt: str = "txt"):
    """Display rich diff between expected and actual snapshots with structured support."""

    try:
        if fmt in {"json", "yaml"}:
            # Pretty print structured JSON/YAML data
            old_data = json.dumps(json.loads(old), indent=2, sort_keys=True)
            new_data = json.dumps(json.loads(new), indent=2, sort_keys=True)
            console.rule("[bold red]Expected[/bold red]")
            console.print(Syntax(old_data, "json", theme="ansi_dark", line_numbers=True))
            console.rule("[bold green]Actual[/bold green]")
            console.print(Syntax(new_data, "json", theme="ansi_dark", line_numbers=True))
            console.rule("[bold yellow]End of diff[/bold yellow]")
            return

        elif fmt == "xml":

            def _pretty_xml(text: str) -> str:
                try:
                    return xml.dom.minidom.parseString(text).toprettyxml()
                except Exception:
                    return text

            old_pretty = _pretty_xml(old)
            new_pretty = _pretty_xml(new)
            # Compute diff line by line
            diff = list(difflib.unified_diff(
                old_pretty.splitlines(),
                new_pretty.splitlines(),
                fromfile=f"{expected_path.name} (expected)",
                tofile=f"{actual_path.name} (actual)",
                lineterm=""
            ))
            if diff:
                console.rule("[bold red]XML Diff[/bold red]")
                diff_text = "\n".join(diff)
                console.print(Syntax(diff_text, "diff", theme="ansi_dark", line_numbers=True))
            else:
                # fallback — print both if somehow identical structurally but flagged different
                console.rule("[bold red]Expected XML[/bold red]")
                console.print(Syntax(old_pretty, "xml", theme="ansi_dark", line_numbers=True))
                console.rule("[bold green]Actual XML[/bold green]")
                console.print(Syntax(new_pretty, "xml", theme="ansi_dark", line_numbers=True))
            console.rule("[bold yellow]End of diff[/bold yellow]")
            return


    except Exception:
        # Fallback to raw diff for unexpected cases
        pass

    # Default: unified diff for text/unstructured formats
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=f"{expected_path.name} (expected)",
        tofile=f"{actual_path.name} (actual)",
        lineterm=""
    )
    diff_text = "\n".join(diff)
    syntax = Syntax(diff_text, "diff", theme="ansi_dark")
    console.print(syntax)


# ========== COMPARERS ========== #

_COMPARERS = {}


def _register_comparer(fmt):
    def decorator(func):
        _COMPARERS[fmt] = func
        return func

    return decorator


@_register_comparer('json')
def _compare_json(
        left: str,
        right: str,
        *,
        ignore_fields: List[str] = None,
        abs_tol: float = 0.0,
        rel_tol: float = 0.0,
        abs_tol_fields: Dict[str, float] = None,
        rel_tol_fields: Dict[str, float] = None,
        epsilon: float = 1e-12,
        show_debug: bool = False,
        **_,
) -> bool:
    left_obj = json.loads(left)
    right_obj = json.loads(right)
    return compare_dicts(
        left=left_obj,
        right=right_obj,
        ignore_fields=ignore_fields,
        abs_tol=abs_tol,
        rel_tol=rel_tol,
        abs_tol_fields=abs_tol_fields,
        rel_tol_fields=rel_tol_fields,
        epsilon=epsilon,
        show_debug=show_debug
    )


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
        ignore_fields: List[str] = None,
        abs_tol: float = 0.0,
        rel_tol: float = 0.0,
        abs_tol_fields: Dict[str, float] = None,
        rel_tol_fields: Dict[str, float] = None,
        epsilon: float = 1e-12,
        show_debug: bool = False,
        **_,
) -> bool:
    """Compare XML documents structurally with per-field numeric tolerances using XPath."""

    return compare_xml(
        xml_a=old,
        xml_b=new,
        ignore_fields=ignore_fields,
        abs_tol=abs_tol,
        rel_tol=rel_tol,
        abs_tol_fields=abs_tol_fields,
        rel_tol_fields=rel_tol_fields,
        epsilon=epsilon,
        show_debug=show_debug
    )


@_register_comparer("pydantic")
def _compare_pydantic(old: str, new: str, **kwargs):
    """Compare two Pydantic model snapshots serialized as JSON strings."""
    try:
        old_obj = json.loads(old)
        new_obj = json.loads(new)
    except Exception:
        return old.strip() == new.strip()
    return compare_dicts(old_obj, new_obj, **kwargs)


@_register_comparer("dataclass")
def _compare_dataclass(old: str, new: str, **kwargs):
    """Compare dataclass snapshots as JSON strings (parsed before comparison)."""
    try:
        old_obj = json.loads(old)
        new_obj = json.loads(new)
    except Exception:
        # fallback: if they’re not JSON, compare raw text
        return old.strip() == new.strip()
    return compare_dicts(old_obj, new_obj, **kwargs)


@_register_comparer("ndarray")
def _compare_ndarray(old: str, new: str, *, abs_tol=None, rel_tol=None, **_):
    """Compare NumPy arrays element-wise with tolerance and type awareness."""
    if not np:
        raise ImportError("NumPy support requires 'numpy'. Install via: pip install pytest-verify[numpy]")

    def _replace_none_with_nan(obj):
        if isinstance(obj, list):
            return [_replace_none_with_nan(i) for i in obj]
        return np.nan if obj is None else obj

    old_data = _replace_none_with_nan(json.loads(old))
    new_data = _replace_none_with_nan(json.loads(new))

    old_arr = np.array(old_data, dtype=object)
    new_arr = np.array(new_data, dtype=object)

    # Shape check first
    if old_arr.shape != new_arr.shape:
        return False

    abs_tol = abs_tol or 0
    rel_tol = rel_tol or 0

    # Type-aware comparison
    for a, b in zip(old_arr.flatten(), new_arr.flatten()):
        # Handle NaN
        if (a is None and b is None) or (isinstance(a, float) and isinstance(b, float)
                                         and np.isnan(a) and np.isnan(b)):
            continue

        # If types differ → fail immediately
        if type(a) != type(b):
            return False

        # If numeric → use tolerance
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if not np.isclose(a, b, atol=abs_tol, rtol=rel_tol, equal_nan=True):
                return False
        else:
            # Non-numeric strict equality
            if a != b:
                return False

    return True


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
    if not pd:
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


@_register_comparer("yaml")
def _compare_yaml(old: str, new: str, *, ignore_order_yaml=False, **kwargs):
    """
       Compare two YAML documents.

       By default, list order differences will cause mismatches.
       If ignore_order_yaml=True, lists are recursively sorted for order-insensitive comparison.
    """

    def default_serializer(obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return str(obj)

    def sort_nested(obj):
        """Recursively sort lists and dicts for order-insensitive comparison."""
        if isinstance(obj, dict):
            # Sort by key
            return {k: sort_nested(v) for k, v in sorted(obj.items())}
        elif isinstance(obj, list):
            # Sort lists if order should be ignored
            if ignore_order_yaml:
                # Sort list items deterministically
                try:
                    return sorted((sort_nested(i) for i in obj), key=lambda x: json.dumps(x, sort_keys=True))
                except TypeError:
                    # fallback: if un-sortable types, treat as set
                    return sorted((str(i) for i in obj))
            else:
                return [sort_nested(i) for i in obj]
        return obj

    old_obj = yaml.safe_load(old)
    new_obj = yaml.safe_load(new)

    old_sorted = sort_nested(old_obj)
    new_sorted = sort_nested(new_obj)

    old_json = json.dumps(old_sorted, indent=2, sort_keys=True, default=default_serializer)
    new_json = json.dumps(new_sorted, indent=2, sort_keys=True, default=default_serializer)

    return _compare_json(left=old_json, right=new_json, **kwargs)


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
        dir: str = "__snapshots__",
        *,
        ignore_fields: list[str] | None = None,
        ignore_columns: list[str] | None = None,
        abs_tol: float = 0.0,
        rel_tol: float = 0.0,
        abs_tol_fields: Dict[str, float] | None = None,
        rel_tol_fields: Dict[str, float] | None = None,
        epsilon: float = 1e-12,
        ignore_order_yaml: bool = True,
        show_debug: bool = False,
):
    """
    Decorator that saves and compares test results as snapshots.

    Exposes full control over structured comparison logic from dictlens/xmllens:
      - ignore_fields: list of JSONPath/XPath patterns to skip
      - abs_tol, rel_tol: global numeric tolerances
      - abs_tol_fields, rel_tol_fields: per-field tolerances
      - epsilon: minimal float threshold
      - ignore_columns: for DataFrame-based comparisons
      - ignore_order_yaml: allow unordered YAML comparison
      - show_debug: verbose debugging output

    On mismatch, prompts to update or keep the snapshot.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Run the actual test and get the result
            result = func(*args, **kwargs)

            # Detect format and serialize
            fmt = _detect_format(result)
            content = _serialize_result(result, fmt)

            # Determine snapshot paths
            test_file_path = Path(inspect.getfile(func)).resolve()
            snapshot_dir = test_file_path.parent / dir
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            name = snapshot_name or func.__name__
            expected_path, actual_path = _get_snapshot_paths(name, fmt, snapshot_dir)

            # First run → create baseline
            if not expected_path.exists():
                _save_snapshot(expected_path, content)
                _save_snapshot(actual_path, content)
                console.print(f"📸 First run → Created baseline for [bold]{name}[/bold]")
                return

            # Load and compare
            expected_content = _load_snapshot(expected_path)
            _save_snapshot(actual_path, content)

            matches = _compare_snapshots(
                expected_content,
                content,
                fmt,
                ignore_fields=ignore_fields,
                ignore_columns=ignore_columns,
                abs_tol=abs_tol,
                rel_tol=rel_tol,
                abs_tol_fields=abs_tol_fields,
                rel_tol_fields=rel_tol_fields,
                epsilon=epsilon,
                ignore_order_yaml=ignore_order_yaml,
                show_debug=show_debug,
            )

            # Match → OK
            if matches:
                console.print(f"✅ Snapshot matches: [green]{expected_path}[/green]")
                return

            # Mismatch
            console.print(f"⚠️ Snapshot mismatch detected for [bold]{name}[/bold]")
            _show_diff(
                expected_content.decode("utf-8") if isinstance(expected_content, bytes) else expected_content,
                content.decode("utf-8") if isinstance(content, bytes) else content,
                expected_path,
                actual_path,
                fmt
            )

            # ask to replace snapshot
            if _ask_to_replace(expected_path):
                _backup_expected(expected_path)
                _save_snapshot(expected_path, content)
                console.print(f"📝 Snapshot updated → {expected_path}")
            else:
                console.print(f"❌ Mismatch kept. Review: {expected_path} and {actual_path}")
                pytest.fail(f"Snapshot mismatch for {expected_path}", pytrace=False)

        return wrapper

    return decorator
