import asyncio

from pytest_verify import verify_snapshot


# ──────────────────────────────────────────────
# Simple async snapshot
# ──────────────────────────────────────────────
@verify_snapshot()
async def test_async_simple_snapshot():
    await asyncio.sleep(0.01)
    return {"message": "hello", "ok": True}


# ──────────────────────────────────────────────
# Async returning nested JSON
# ──────────────────────────────────────────────
@verify_snapshot()
async def test_async_nested_json_snapshot():
    await asyncio.sleep(0.01)
    return {
        "user": {"id": 1, "name": "Ayoub"},
        "scores": [99.5, 100.0, 97.2],
        "meta": {"timestamp": "2025-10-25T12:00:00Z"},
    }


# ──────────────────────────────────────────────
# Async with ignored dynamic field
# ──────────────────────────────────────────────
@verify_snapshot(ignore_fields=["$.meta.timestamp"])
async def test_async_ignore_field_snapshot():
    return {
        "user": {"id": 10, "name": "Mohamed"},
        "meta": {"timestamp": f"2025-10-25T{int(asyncio.get_event_loop().time())}Z"},
    }


# ──────────────────────────────────────────────
# 4️⃣ Async with numeric tolerance
# ──────────────────────────────────────────────
@verify_snapshot(abs_tol=0.05, rel_tol=0.01)
async def test_async_numeric_tolerance_snapshot():
    return {"value": 3.1416}


# ──────────────────────────────────────────────
# 5️⃣ Async returning coroutine (double await safety)
# ──────────────────────────────────────────────
async def _inner_async():
    await asyncio.sleep(0.01)
    return {"nested": True, "value": 5}


@verify_snapshot()
async def test_async_returning_coroutine_snapshot():
    # This returns a coroutine instead of a dict directly
    return _inner_async()


# ──────────────────────────────────────────────
# 6️⃣ Mixed sync + async coexistence (regression guard)
# ──────────────────────────────────────────────
@verify_snapshot()
def test_sync_and_async_coexistence():
    # Normal sync test to ensure async logic doesn't break sync behavior
    return {"type": "sync", "ok": True}
