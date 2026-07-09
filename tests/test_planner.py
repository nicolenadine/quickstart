"""Tests for planner module and runner."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock

import pytest

from quickstart.config import ProjectConfig, Template
from quickstart.runner import planner, run
from quickstart.steps import Plan, Step


@pytest.fixture()
def full_config(tmp_path) -> ProjectConfig:
    return ProjectConfig(
        project_name="testproject",
        target_path=tmp_path,
        template=Template.basic,
        docker=True,
        github_create=True,
        vscode_open=True,
        git=True,
    )


@pytest.fixture()
def minimal_config(tmp_path) -> ProjectConfig:
    return ProjectConfig(
        project_name="minimal",
        target_path=tmp_path,
        template=Template.basic,
        docker=False,
        github_create=False,
        vscode_open=False,
        git=False,
    )


def _mock_step(name: str, description: str = "") -> MagicMock:
    step = MagicMock(spec=Step)
    step.name = name
    step.description = description or f"Description for {name}"
    return step


class TestPlannerProducesOrderedPlan:
    def test_returns_plan_instance(self, full_config):
        assert isinstance(planner(full_config), Plan)

    def test_plan_non_empty(self, full_config):
        assert len(planner(full_config)) > 0

    def test_five_steps_when_all_flags_enabled(self, full_config):
        assert len(planner(full_config)) == 5

    def test_one_step_when_all_flags_disabled(self, minimal_config):
        assert len(planner(minimal_config)) == 1

    def test_first_step_is_scaffold(self, full_config):
        assert planner(full_config).steps[0].name == "scaffold"

    def test_scaffold_description_contains_project_name(self, full_config):
        assert full_config.project_name in planner(full_config).steps[0].description

    def test_scaffold_description_contains_template(self, full_config):
        assert full_config.template.value in planner(full_config).steps[0].description

    def test_full_plan_order(self, full_config):
        names = [s.name for s in planner(full_config)]
        assert names == ["scaffold", "git_init", "docker", "github_create", "vscode_open"]

    @pytest.mark.parametrize(
        "absent", ["git_init", "docker", "github_create", "vscode_open"]
    )
    def test_optional_step_absent_in_minimal(self, minimal_config, absent):
        assert absent not in [s.name for s in planner(minimal_config)]

    def test_git_step_present_when_git_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=True, docker=False, github_create=False, vscode_open=False,
        )
        assert "git_init" in [s.name for s in planner(config)]

    def test_docker_step_present_when_docker_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=True, github_create=False, vscode_open=False,
        )
        assert "docker" in [s.name for s in planner(config)]

    def test_github_step_present_when_github_create_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=True, vscode_open=False,
        )
        assert "github_create" in [s.name for s in planner(config)]

    def test_vscode_step_present_when_vscode_open_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=False, vscode_open=True,
        )
        assert "vscode_open" in [s.name for s in planner(config)]

    def test_github_description_mentions_public(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=True, vscode_open=False,
            public=True,
        )
        gh = next(s for s in planner(config) if s.name == "github_create")
        assert "public" in gh.description

    def test_github_description_mentions_private(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=True, vscode_open=False,
            private=True,
        )
        gh = next(s for s in planner(config) if s.name == "github_create")
        assert "private" in gh.description

    def test_every_step_satisfies_protocol(self, full_config):
        assert all(isinstance(s, Step) for s in planner(full_config))

    def test_every_step_has_description(self, full_config):
        assert all(s.description for s in planner(full_config))

    def test_template_reflected_in_scaffold_description(self, tmp_path):
        config = ProjectConfig(
            project_name="mylib", target_path=tmp_path, template=Template.lib,
            git=False, docker=False, github_create=False, vscode_open=False,
        )
        assert "lib" in planner(config).steps[0].description


class TestRunnerExecutesInOrder:
    def test_run_calls_execute_on_every_step(self, minimal_config):
        steps = [_mock_step(f"step_{i}") for i in range(3)]
        run(Plan(steps), minimal_config)
        for step in steps:
            step.execute.assert_called_once_with(minimal_config)

    def test_run_executes_steps_in_order(self, minimal_config):
        calls: list[str] = []
        steps = []
        for name in ("a", "b", "c"):
            step = _mock_step(name)
            step.execute.side_effect = lambda cfg, n=name: calls.append(n)
            steps.append(step)
        run(Plan(steps), minimal_config)
        assert calls == ["a", "b", "c"]

    def test_run_stops_on_first_failing_step(self, minimal_config):
        calls: list[str] = []
        good = _mock_step("good")
        good.execute.side_effect = lambda cfg: calls.append("good")
        failing = _mock_step("failing")
        failing.execute.side_effect = RuntimeError("boom")
        never = _mock_step("never")
        never.execute.side_effect = lambda cfg: calls.append("never")
        with pytest.raises(RuntimeError):
            run(Plan([good, failing, never]), minimal_config)
        assert calls == ["good"]
        never.execute.assert_not_called()

    def test_run_reraises_original_exception(self, minimal_config):
        failing = _mock_step("failing")
        sentinel = ValueError("specific failure")
        failing.execute.side_effect = sentinel
        with pytest.raises(ValueError) as exc_info:
            run(Plan([failing]), minimal_config)
        assert exc_info.value is sentinel

    def test_run_empty_plan_is_noop(self, minimal_config):
        run(Plan([]), minimal_config)


class TestNoSideEffects:
    def test_planner_creates_no_filesystem_entries(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            docker=True, github_create=True, vscode_open=True, git=True,
        )
        before = set(tmp_path.rglob("*"))
        planner(config)
        assert set(tmp_path.rglob("*")) == before

    def test_run_creates_no_filesystem_entries(self, full_config):
        plan = planner(full_config)
        before = set(full_config.target_path.rglob("*"))
        run(plan, full_config)
        assert set(full_config.target_path.rglob("*")) == before

    def test_planner_and_run_invoke_no_subprocess(self, full_config, monkeypatch):
        def _fail(*args, **kwargs):
            raise AssertionError("subprocess was invoked")

        monkeypatch.setattr(subprocess, "run", _fail)
        monkeypatch.setattr(subprocess, "Popen", _fail)
        monkeypatch.setattr(subprocess, "call", _fail)
        monkeypatch.setattr(subprocess, "check_call", _fail)
        monkeypatch.setattr(subprocess, "check_output", _fail)

        plan = planner(full_config)
        run(plan, full_config)

    def test_run_invokes_no_os_system(self, full_config, monkeypatch):
        import os

        def _fail(*args, **kwargs):
            raise AssertionError("os.system was invoked")

        monkeypatch.setattr(os, "system", _fail)
        run(planner(full_config), full_config)
