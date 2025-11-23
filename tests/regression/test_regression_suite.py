"""Regression test suite covering historic bug categories."""

from __future__ import annotations

import asyncio
import re
import time
import uuid
import weakref
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import pytest

from infrastructure.mocks import InMemoryDatabaseAdapter

pytestmark = pytest.mark.regression


class SearchIndex:
    """Minimal search index that preserves special characters."""

    def __init__(self) -> None:
        self.records: List[Dict[str, Any]] = []

    def add(self, record: Dict[str, Any]) -> None:
        self.records.append(record)

    def search(self, term: str) -> List[Dict[str, Any]]:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        return [rec for rec in self.records if pattern.search(rec.get("name", ""))]


class BatchProcessor:
    """Simulate batch creation with partial failure diagnostics."""

    async def process(self, payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for idx, payload in enumerate(payloads):
            if "document_id" not in payload:
                results.append({"success": False, "index": idx, "error": "Missing document_id"})
                continue
            results.append({"success": True, "id": uuid.uuid4().hex, **payload})
        return results


class OptimisticLocker:
    """Minimal optimistic locking helper used in concurrency tests."""

    def __init__(self, initial_value: str = "Req") -> None:
        self._version = 1
        self.value = initial_value

    def snapshot(self) -> int:
        return self._version

    def update(self, snapshot: int, new_value: str) -> Dict[str, Any]:
        if snapshot != self._version:
            return {"success": False, "error": "Concurrent update"}
        self._version += 1
        self.value = new_value
        return {"success": True, "version": self._version, "value": self.value}


def filter_visible_children(projects: List[Dict[str, Any]], parent_status: Dict[str, bool]) -> List[Dict[str, Any]]:
    return [
        project
        for project in projects
        if not project.get("is_deleted", False)
        and not parent_status.get(project.get("organization_id"), False)
    ]


class MemoryGuard:
    """Track asyncio Tasks and detect leaks."""

    def __init__(self) -> None:
        self._refs = weakref.WeakSet()

    def track(self, coro):
        task = asyncio.create_task(coro)
        self._refs.add(task)
        return task

    def pending(self) -> int:
        return sum(1 for task in self._refs if not task.done())


class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, limit: int = 3, window: float = 0.5) -> None:
        self.limit = limit
        self.window = window
        self._events: List[float] = []

    def allow(self, token: str | None) -> bool:
        now = time.monotonic()
        self._events = [ts for ts in self._events if now - ts < self.window]
        if not token:
            raise PermissionError("Missing token")
        if len(self._events) >= self.limit:
            return False
        self._events.append(now)
        return True

    def reset(self) -> None:
        self._events.clear()


class TokenManager:
    """Handle edge cases for token expiry and grace periods."""

    def __init__(self, grace_seconds: int = 5) -> None:
        self.grace_seconds = grace_seconds

    def is_valid(self, issued_at: float, ttl_seconds: int, now: float | None = None) -> bool:
        now = now or time.time()
        expires_at = issued_at + ttl_seconds
        return expires_at + self.grace_seconds >= now


@pytest.fixture
def db() -> InMemoryDatabaseAdapter:
    return InMemoryDatabaseAdapter()


@pytest.mark.asyncio
async def test_soft_delete_records_excluded_from_queries(db):
    record = await db.insert("documents", {"name": "Spec", "project_id": uuid.uuid4().hex})
    await db.update("documents", {"is_deleted": True}, {"id": record["id"]})

    results = await db.query("documents", filters={"is_deleted": False})
    assert all(item["id"] != record["id"] for item in results)


@pytest.mark.asyncio
async def test_soft_delete_records_visible_with_flag(db):
    record = await db.insert("documents", {"name": "Spec2", "project_id": uuid.uuid4().hex})
    await db.update("documents", {"is_deleted": True}, {"id": record["id"]})

    hidden = await db.query("documents", filters={"id": record["id"], "is_deleted": False})
    lookup = await db.query("documents", filters={"id": record["id"]})

    assert hidden == []
    assert lookup and lookup[0]["is_deleted"] is True


@pytest.mark.asyncio
async def test_soft_delete_cascade_preserves_parent(db):
    org = await db.insert("organizations", {"name": "Org"})
    project = await db.insert("projects", {"name": "Proj", "organization_id": org["id"]})
    await db.update("projects", {"is_deleted": True}, {"id": project["id"]})
    refreshed_org = await db.get_single("organizations", filters={"id": org["id"]})
    assert refreshed_org["is_deleted"] is False


def test_concurrent_update_conflict_detected():
    locker = OptimisticLocker()
    snapshot = locker.snapshot()

    first = locker.update(snapshot, "New Name")
    second = locker.update(snapshot, "Other Name")

    assert first["success"] is True
    assert second["success"] is False


def test_concurrent_update_retry_succeeds_on_fresh_snapshot():
    locker = OptimisticLocker()
    first_snapshot = locker.snapshot()
    locker.update(first_snapshot, "First")
    refreshed_snapshot = locker.snapshot()
    result = locker.update(refreshed_snapshot, "Retry")
    assert result["success"] is True
    assert result["value"] == "Retry"


def test_search_handles_special_characters():
    index = SearchIndex()
    index.add({"name": "Auth+Kit/Flow"})
    index.add({"name": "Plain"})

    matches = index.search("Auth+Kit/Flow")
    assert len(matches) == 1
    assert matches[0]["name"].startswith("Auth")


def test_search_handles_unicode_terms():
    index = SearchIndex()
    index.add({"name": "Διαδρομή"})
    assert index.search("Διαδρομή")


@pytest.mark.asyncio
async def test_batch_create_partial_failure_reports_indices():
    processor = BatchProcessor()
    payloads = [
        {"name": "Valid", "document_id": "doc-1"},
        {"name": "Broken"},
    ]
    results = await processor.process(payloads)
    assert results[1]["error"] == "Missing document_id"
    assert results[0]["success"] is True


@pytest.mark.asyncio
async def test_batch_create_continues_after_failure():
    processor = BatchProcessor()
    payloads = [
        {"name": "A", "document_id": "doc-1"},
        {"name": "B"},
        {"name": "C", "document_id": "doc-2"},
    ]
    results = await processor.process(payloads)
    assert sum(1 for r in results if r["success"]) == 2


@asynccontextmanager
async def transactional_log(log: List[str]):
    snapshot = list(log)
    try:
        yield
    except Exception:
        log[:] = snapshot
        raise


@pytest.mark.asyncio
async def test_transaction_rolls_back_on_nested_failure():
    log: List[str] = []
    try:
        async with transactional_log(log):
            log.append("step-1")
            async with transactional_log(log):
                log.append("step-2")
                raise RuntimeError("nested failure")
    except RuntimeError:
        pass

    assert log == []


@pytest.mark.asyncio
async def test_transaction_commits_when_nested_succeeds():
    log: List[str] = []
    async with transactional_log(log):
        log.append("outer")
        async with transactional_log(log):
            log.append("inner")

    assert log == ["outer", "inner"]


@pytest.mark.asyncio
async def test_memory_guard_releases_completed_tasks():
    guard = MemoryGuard()

    async def fast_job():
        await asyncio.sleep(0.01)
        return True

    task = guard.track(fast_job())
    await task
    assert guard.pending() == 0


@pytest.mark.asyncio
async def test_memory_guard_detects_growth():
    guard = MemoryGuard()

    async def slow_job():
        await asyncio.sleep(0.1)

    task = guard.track(slow_job())
    assert guard.pending() == 1
    task.cancel()


def test_rate_limit_bypass_prevented_without_token():
    limiter = RateLimiter()
    with pytest.raises(PermissionError):
        limiter.allow(None)


def test_rate_limit_resets_after_window():
    limiter = RateLimiter(limit=1, window=0.01)
    assert limiter.allow("token") is True
    time.sleep(0.02)
    assert limiter.allow("token") is True


def test_token_expiry_grace_period_allows_buffer():
    manager = TokenManager(grace_seconds=10)
    issued = time.time() - 100
    ttl = 90
    now = issued + ttl + manager.grace_seconds - 1
    assert manager.is_valid(issued, ttl, now=now)


def test_token_expiry_zero_ttl_rejected():
    manager = TokenManager(grace_seconds=0)
    issued = time.time()
    assert manager.is_valid(issued, 0, now=issued + 1) is False


@pytest.mark.asyncio
async def test_unicode_names_round_trip_in_db(db):
    record = await db.insert("documents", {"name": "測試", "project_id": uuid.uuid4().hex})
    fetched = await db.get_single("documents", filters={"id": record["id"]})
    assert fetched["name"] == "測試"


@pytest.mark.asyncio
async def test_unicode_search_results_returned(db):
    await db.insert("documents", {"name": "スペック", "project_id": uuid.uuid4().hex})
    results = await db.query("documents")
    assert any(item["name"] == "スペック" for item in results)


def test_special_character_search_returns_match():
    index = SearchIndex()
    index.add({"name": "Feature: Login"})
    matches = index.search("Feature: Login")
    assert matches


@pytest.mark.asyncio
async def test_batch_failure_returns_actionable_errors():
    processor = BatchProcessor()
    payloads = [{"name": "Only"}]
    result = await processor.process(payloads)
    assert result[0]["error"].startswith("Missing")


@pytest.mark.asyncio
async def test_soft_delete_filter_chain_with_relationships(db):
    parent = await db.insert("organizations", {"name": "Parent"})
    await db.insert("projects", {"name": "Child", "organization_id": parent["id"]})
    await db.update("organizations", {"is_deleted": True}, {"id": parent["id"]})
    projects = await db.query("projects", filters={"organization_id": parent["id"]})
    parent_record = await db.get_single("organizations", filters={"id": parent["id"]})
    visible = filter_visible_children(projects, {parent_record["id"]: parent_record["is_deleted"]})
    assert visible == []
