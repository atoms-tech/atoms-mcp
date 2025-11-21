"""Unit tests for the parallel test orchestrator."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from cli_modules.test_orchestrator import (
    TestOrchestrator,
    TestStage,
)


pytestmark = pytest.mark.unit


def test_build_stage_plan_includes_foundation_paths():
    orchestrator = TestOrchestrator()
    stages = orchestrator.build_stage_plan()
    names = [stage.name for stage in stages]
    assert "foundation" in names
    assert "e2e" in names

    foundation = next(stage for stage in stages if stage.name == "foundation")
    assert any(path.endswith("test_workflow_execution.py") for path in foundation.paths)

    e2e_stage = next(stage for stage in stages if stage.name == "e2e")
    ignored = set(e2e_stage.ignore)
    assert any(path.endswith("test_workflow_execution.py") for path in ignored)


def test_run_stages_stops_after_failure(monkeypatch):
    orchestrator = TestOrchestrator()

    stage_foundation = TestStage(
        name="foundation",
        display_name="Foundation",
        description="",
        paths=["tests/unit/test_mock_clients.py"],
    )
    stage_tools = TestStage(
        name="tools",
        display_name="Tools",
        description="",
        paths=["tests/unit/tools/test_entity_core.py"],
        depends_on=["foundation"],
    )
    stage_integration = TestStage(
        name="integration",
        display_name="Integration",
        description="",
        paths=["tests/integration/test_mcp_server_integration.py"],
        depends_on=["tools"],
    )

    monkeypatch.setattr(
        TestOrchestrator,
        "build_stage_plan",
        lambda self: [stage_foundation, stage_tools, stage_integration],
    )

    call_count = {"runs": 0}

    def fake_run(cmd, cwd):
        call_count["runs"] += 1
        code = 0 if call_count["runs"] == 1 else 1
        return SimpleNamespace(returncode=code)

    monkeypatch.setattr("cli_modules.test_orchestrator.subprocess.run", fake_run)

    summary = orchestrator.run()

    assert summary.success is False
    statuses = [result.status for result in summary.stage_results]
    assert statuses == ["passed", "failed", "skipped"]
    assert "tools" in summary.stage_results[-1].reason


def test_parallel_mode_includes_worker_flag(monkeypatch):
    monkeypatch.setattr(
        TestOrchestrator,
        "_verify_parallel_support",
        lambda self: None,
    )

    orchestrator = TestOrchestrator(parallel=True, max_workers=4)

    sample_stage = TestStage(
        name="foundation",
        display_name="Foundation",
        description="",
        paths=["tests/unit/test_mock_clients.py"],
    )

    monkeypatch.setattr(
        TestOrchestrator,
        "build_stage_plan",
        lambda self: [sample_stage],
    )

    recorded = {"cmd": None}

    def fake_run(cmd, cwd):
        recorded["cmd"] = cmd
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("cli_modules.test_orchestrator.subprocess.run", fake_run)

    summary = orchestrator.run()
    assert summary.success is True
    assert recorded["cmd"] is not None
    assert "-n" in recorded["cmd"]
    assert "4" in recorded["cmd"]


def test_parallel_coverage_generates_combined_reports(monkeypatch):
    monkeypatch.setattr(
        TestOrchestrator,
        "_verify_parallel_support",
        lambda self: None,
    )

    orchestrator = TestOrchestrator(parallel=True, coverage=True)

    stage_one = TestStage(
        name="foundation",
        display_name="Foundation",
        description="",
        paths=["tests/unit/test_mock_clients.py"],
    )
    stage_two = TestStage(
        name="tools",
        display_name="Tools",
        description="",
        paths=["tests/unit/tools/test_entity_core.py"],
        depends_on=["foundation"],
    )

    monkeypatch.setattr(
        TestOrchestrator,
        "build_stage_plan",
        lambda self: [stage_one, stage_two],
    )

    commands = []

    def fake_run(cmd, cwd):
        commands.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("cli_modules.test_orchestrator.subprocess.run", fake_run)

    summary = orchestrator.run()
    assert summary.success is True

    pytest_cmds = [cmd for cmd in commands if cmd[:3] == ["python", "-m", "pytest"]]
    assert len(pytest_cmds) == 2
    assert "--cov=." in pytest_cmds[0]
    assert "--cov-append" not in pytest_cmds[0]
    assert "--cov=." in pytest_cmds[1]
    assert "--cov-append" in pytest_cmds[1]

    coverage_cmds = [cmd for cmd in commands if cmd[:3] == ["python", "-m", "coverage"]]
    coverage_actions = [" ".join(cmd[3:4]) for cmd in coverage_cmds]
    assert any("erase" in action for action in coverage_actions)
    assert any("combine" in action for action in coverage_actions)
