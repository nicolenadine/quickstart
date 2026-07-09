"""Tests for planner and runner."""

from __future__ import annotations

import os
import subprocess
from unittest.mock import MagicMock

import pytest

from quickstart.config import ProjectConfig, Template
from quickstart.runner import planner, run
from quickstart.steps import Plan, Step


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def full_config(tmp_path) -> ProjectConfig:
    """Config with every optional feature enabled."""
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
    """Config with every optional feature disabled."""
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
    """Build a MagicMock that satisfies the Step protocol."""
    step = MagicMock(spec=Step)
    step.name = name
    step.description = description or f"Description for {name}"
    return step


# ===========================================================================
# Planner – produces an ordered Plan
# ===========================================================================


class TestPlannerProducesOrderedPlan:
    """planner() must return a Plan whose steps are in the documented order."""

    # ---- return type -------------------------------------------------------

    def test_returns_plan_instance(self, full_config):
        assert isinstance(planner(full_config), Plan)

    def test_plan_is_non_empty(self, full_config):
        assert len(planner(full_config)) > 0

    # ---- step counts -------------------------------------------------------

    def test_five_steps_when_all_flags_enabled(self, full_config):
        assert len(planner(full_config)) == 5

    def test_one_step_when_all_optional_flags_disabled(self, minimal_config):
        assert len(planner(minimal_config)) == 1

    # ---- scaffold is always first -----------------------------------------

    def test_first_step_name_is_scaffold(self, full_config):
        assert planner(full_config).steps[0].name == "scaffold"

    def test_first_step_name_is_scaffold_in_minimal(self, minimal_config):
        assert planner(minimal_config).steps[0].name == "scaffold"

    def test_scaffold_description_contains_project_name(self, full_config):
        desc = planner(full_config).steps[0].description
        assert full_config.project_name in desc

    def test_scaffold_description_contains_template_value(self, full_config):
        desc = planner(full_config).steps[0].description
        assert full_config.template.value in desc

    def test_scaffold_description_contains_target_path(self, full_config):
        desc = planner(full_config).steps[0].description
        assert str(full_config.target_path) in desc

    # ---- full ordering ----------------------------------------------------

    def test_full_plan_step_order(self, full_config):
        names = [s.name for s in planner(full_config)]
        assert names == ["scaffold", "git_init", "docker", "github_create", "vscode_open"]

    # ---- optional steps absent in minimal ---------------------------------

    @pytest.mark.parametrize(
        "absent", ["git_init", "docker", "github_create", "vscode_open"]
    )
    def test_optional_step_absent_in_minimal_config(self, minimal_config, absent):
        names = [s.name for s in planner(minimal_config)]
        assert absent not in names

    # ---- individual flag → step mapping ------------------------------------

    def test_git_step_present_when_git_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=True, docker=False, github_create=False, vscode_open=False,
        )
        assert "git_init" in [s.name for s in planner(config)]

    def test_git_step_absent_when_git_false(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=False, vscode_open=False,
        )
        assert "git_init" not in [s.name for s in planner(config)]

    def test_docker_step_present_when_docker_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=True, github_create=False, vscode_open=False,
        )
        assert "docker" in [s.name for s in planner(config)]

    def test_docker_step_absent_when_docker_false(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=False, vscode_open=False,
        )
        assert "docker" not in [s.name for s in planner(config)]

    def test_github_step_present_when_github_create_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=True, vscode_open=False,
        )
        assert "github_create" in [s.name for s in planner(config)]

    def test_github_step_absent_when_github_create_false(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=False, vscode_open=False,
        )
        assert "github_create" not in [s.name for s in planner(config)]

    def test_vscode_step_present_when_vscode_open_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=False, vscode_open=True,
        )
        assert "vscode_open" in [s.name for s in planner(config)]

    def test_vscode_step_absent_when_vscode_open_false(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=False, vscode_open=False,
        )
        assert "vscode_open" not in [s.name for s in planner(config)]

    # ---- github visibility in description ----------------------------------

    def test_github_description_mentions_public_when_public_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=True, vscode_open=False,
            public=True,
        )
        gh = next(s for s in planner(config) if s.name == "github_create")
        assert "public" in gh.description

    def test_github_description_mentions_private_when_private_true(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=True, vscode_open=False,
            private=True,
        )
        gh = next(s for s in planner(config) if s.name == "github_create")
        assert "private" in gh.description

    def test_github_description_mentions_default_when_no_visibility(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            git=False, docker=False, github_create=True, vscode_open=False,
        )
        gh = next(s for s in planner(config) if s.name == "github_create")
        assert gh.description  # non-empty

    # ---- template reflected in scaffold description -------------------------

    @pytest.mark.parametrize("template", [Template.basic, Template.lib, Template.cli, Template.data])
    def test_scaffold_description_contains_correct_template(self, tmp_path, template):
        config = ProjectConfig(
            project_name="myproject", target_path=tmp_path, template=template,
            git=False, docker=False, github_create=False, vscode_open=False,
        )
        desc = planner(config).steps[0].description
        assert template.value in desc

    # ---- Step protocol compliance ------------------------------------------

    def test_every_step_satisfies_step_protocol(self, full_config):
        for step in planner(full_config):
            assert isinstance(step, Step), f"Step {step!r} does not satisfy the Step protocol"

    def test_every_step_has_non_empty_description(self, full_config):
        for step in planner(full_config):
            assert step.description, f"Step {step.name!r} has empty description"

    def test_every_step_has_non_empty_name(self, full_config):
        for step in planner(full_config):
            assert step.name, "A step has an empty name"

    # ---- Plan iteration ----------------------------------------------------

    def test_plan_is_iterable(self, full_config):
        steps = list(planner(full_config))
        assert len(steps) == 5

    def test_plan_steps_property_returns_copy(self, full_config):
        plan = planner(full_config)
        # Mutating the returned list must not change the Plan.
        copy = plan.steps
        copy.clear()
        assert len(plan) == 5


# ===========================================================================
# Runner – executes steps in order and stops on first failure
# ===========================================================================


class TestRunnerExecutesInOrder:
    """run() must call each step in order and re-raise the first exception."""

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

    def test_run_does_not_call_later_steps_after_failure(self, minimal_config):
        failing = _mock_step("failing")
        failing.execute.side_effect = ValueError("stop here")
        after1 = _mock_step("after1")
        after2 = _mock_step("after2")

        with pytest.raises(ValueError):
            run(Plan([failing, after1, after2]), minimal_config)

        after1.execute.assert_not_called()
        after2.execute.assert_not_called()

    def test_run_reraises_the_original_exception_object(self, minimal_config):
        failing = _mock_step("failing")
        sentinel = ValueError("specific failure")
        failing.execute.side_effect = sentinel

        with pytest.raises(ValueError) as exc_info:
            run(Plan([failing]), minimal_config)

        assert exc_info.value is sentinel

    def test_run_reraises_runtime_error_unchanged(self, minimal_config):
        step = _mock_step("boom")
        step.execute.side_effect = RuntimeError("runtime failure")
        with pytest.raises(RuntimeError, match="runtime failure"):
            run(Plan([step]), minimal_config)

    def test_run_empty_plan_is_noop(self, minimal_config):
        # Must not raise and must not call anything.
        run(Plan([]), minimal_config)  # no assertion needed; success is no exception

    def test_run_passes_config_to_each_step(self, minimal_config):
        steps = [_mock_step(f"s{i}") for i in range(3)]
        run(Plan(steps), minimal_config)
        for step in steps:
            args, _ = step.execute.call_args
            assert args[0] is minimal_config

    def test_run_calls_execute_exactly_once_per_step_on_success(self, minimal_config):
        steps = [_mock_step(f"s{i}") for i in range(4)]
        run(Plan(steps), minimal_config)
        for step in steps:
            assert step.execute.call_count == 1


# ===========================================================================
# No side effects – planner and runner must not touch the filesystem or shell
# ===========================================================================


class TestNoSideEffects:
    """Neither the planner nor the runner must invoke subprocesses or I/O."""

    # ---- filesystem --------------------------------------------------------

    def test_planner_creates_no_filesystem_entries(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            docker=True, github_create=True, vscode_open=True, git=True,
        )
        before = set(tmp_path.rglob("*"))
        planner(config)
        assert set(tmp_path.rglob("*")) == before

    def test_planner_creates_no_directories(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            docker=True, github_create=True, vscode_open=True, git=True,
        )
        before = {p for p in tmp_path.rglob("*") if p.is_dir()}
        planner(config)
        assert {p for p in tmp_path.rglob("*") if p.is_dir()} == before

    def test_planner_creates_no_files(self, tmp_path):
        config = ProjectConfig(
            project_name="p", target_path=tmp_path,
            docker=True, github_create=True, vscode_open=True, git=True,
        )
        before = {p for p in tmp_path.rglob("*") if p.is_file()}
        planner(config)
        assert {p for p in tmp_path.rglob("*") if p.is_file()} == before

    def test_run_creates_no_filesystem_entries(self, full_config):
        plan = planner(full_config)
        before = set(full_config.target_path.rglob("*"))
        run(plan, full_config)
        assert set(full_config.target_path.rglob("*")) == before

    def test_run_creates_no_directories(self, full_config):
        plan = planner(full_config)
        before = {p for p in full_config.target_path.rglob("*") if p.is_dir()}
        run(plan, full_config)
        assert {p for p in full_config.target_path.rglob("*") if p.is_dir()} == before

    def test_run_creates_no_files(self, full_config):
        plan = planner(full_config)
        before = {p for p in full_config.target_path.rglob("*") if p.is_file()}
        run(plan, full_config)
        assert {p for p in full_config.target_path.rglob("*") if p.is_file()} == before

    # ---- subprocess --------------------------------------------------------

    def test_planner_does_not_invoke_subprocess_run(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.run was invoked during planner()")
        monkeypatch.setattr(subprocess, "run", _fail)
        planner(full_config)  # must not raise AssertionError

    def test_planner_does_not_invoke_subprocess_popen(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.Popen was invoked during planner()")
        monkeypatch.setattr(subprocess, "Popen", _fail)
        planner(full_config)

    def test_planner_does_not_invoke_subprocess_call(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.call was invoked during planner()")
        monkeypatch.setattr(subprocess, "call", _fail)
        planner(full_config)

    def test_planner_does_not_invoke_subprocess_check_call(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.check_call was invoked during planner()")
        monkeypatch.setattr(subprocess, "check_call", _fail)
        planner(full_config)

    def test_planner_does_not_invoke_subprocess_check_output(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.check_output was invoked during planner()")
        monkeypatch.setattr(subprocess, "check_output", _fail)
        planner(full_config)

    def test_run_does_not_invoke_subprocess_run(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.run was invoked during run()")
        monkeypatch.setattr(subprocess, "run", _fail)
        run(planner(full_config), full_config)

    def test_run_does_not_invoke_subprocess_popen(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.Popen was invoked during run()")
        monkeypatch.setattr(subprocess, "Popen", _fail)
        run(planner(full_config), full_config)

    def test_run_does_not_invoke_subprocess_call(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.call was invoked during run()")
        monkeypatch.setattr(subprocess, "call", _fail)
        run(planner(full_config), full_config)

    def test_run_does_not_invoke_subprocess_check_call(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.check_call was invoked during run()")
        monkeypatch.setattr(subprocess, "check_call", _fail)
        run(planner(full_config), full_config)

    def test_run_does_not_invoke_subprocess_check_output(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("subprocess.check_output was invoked during run()")
        monkeypatch.setattr(subprocess, "check_output", _fail)
        run(planner(full_config), full_config)

    # ---- os.system ---------------------------------------------------------

    def test_planner_does_not_invoke_os_system(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("os.system was invoked during planner()")
        monkeypatch.setattr(os, "system", _fail)
        planner(full_config)

    def test_run_does_not_invoke_os_system(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("os.system was invoked during run()")
        monkeypatch.setattr(os, "system", _fail)
        run(planner(full_config), full_config)

    # ---- os.mkdir / os.makedirs -------------------------------------------

    def test_planner_does_not_invoke_os_mkdir(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("os.mkdir was invoked during planner()")
        monkeypatch.setattr(os, "mkdir", _fail)
        planner(full_config)

    def test_run_does_not_invoke_os_mkdir(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("os.mkdir was invoked during run()")
        monkeypatch.setattr(os, "mkdir", _fail)
        run(planner(full_config), full_config)

    def test_planner_does_not_invoke_os_makedirs(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("os.makedirs was invoked during planner()")
        monkeypatch.setattr(os, "makedirs", _fail)
        planner(full_config)

    def test_run_does_not_invoke_os_makedirs(self, full_config, monkeypatch):
        def _fail(*a, **kw):
            raise AssertionError("os.makedirs was invoked during run()")
        monkeypatch.setattr(os, "makedirs", _fail)
        run(planner(full_config), full_config)
