"""Tests for the uv-init step, git fallback, flag translation, and preflight."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from quickstart.cli import app
from quickstart.config import ProjectConfig, Template
from quickstart.steps.uv_init import GitInitStep, UvInitStep
from quickstart.subprocess_runner import CommandError

runner = CliRunner()


def _invoke(*args: str):
    return runner.invoke(app, list(args))


def _config(tmp_path, **overrides) -> ProjectConfig:
    defaults = dict(
        project_name="demo",
        target_path=tmp_path,
        template=Template.basic,
        python_version="3.11",
        uv=True,
        git=True,
    )
    return ProjectConfig(**(defaults | overrides))


# ===========================================================================
# Command construction (UvInitStep.description, computed at construction time)
# ===========================================================================


class TestUvCommandConstruction:
    def test_basic_template_has_no_lib_flag(self, tmp_path):
        step = UvInitStep(_config(tmp_path, template=Template.basic), path=tmp_path)
        assert "--lib" not in step.description

    def test_lib_template_inserts_lib_before_target_dir(self, tmp_path):
        step = UvInitStep(_config(tmp_path, template=Template.lib), path=tmp_path)
        parts = step.description.split()
        assert parts[:2] == ["uv", "init"]
        assert parts[2] == "--lib"
        assert parts[3] == str(tmp_path)

    @pytest.mark.parametrize("template", [Template.basic, Template.cli, Template.data])
    def test_non_lib_templates_have_no_lib_flag(self, tmp_path, template):
        step = UvInitStep(_config(tmp_path, template=template), path=tmp_path)
        assert "--lib" not in step.description

    def test_python_version_appended(self, tmp_path):
        step = UvInitStep(_config(tmp_path, python_version="3.12"), path=tmp_path)
        assert "--python 3.12" in step.description

    def test_vcs_none_appended_when_git_disabled(self, tmp_path):
        step = UvInitStep(_config(tmp_path, git=False), path=tmp_path)
        assert "--vcs none" in step.description

    def test_no_vcs_flag_when_git_enabled(self, tmp_path):
        step = UvInitStep(_config(tmp_path, git=True), path=tmp_path)
        assert "--vcs" not in step.description

    def test_description_starts_with_uv_init(self, tmp_path):
        step = UvInitStep(_config(tmp_path), path=tmp_path)
        assert step.description.startswith("uv init")


class TestGitFallbackDescription:
    def test_description_is_git_init_command(self, tmp_path):
        step = GitInitStep(_config(tmp_path, uv=False), path=tmp_path)
        assert step.description == f"git init {tmp_path}"


# ===========================================================================
# execute() -- real subprocess calls, always mocked
# ===========================================================================


class TestUvInitStepExecute:
    def test_calls_run_command_with_constructed_argv(self, tmp_path):
        config = _config(tmp_path, git=False, python_version="3.12")
        step = UvInitStep(config, path=tmp_path)
        with patch("quickstart.steps.uv_init.run_command") as mock_run:
            step.execute(config)
        args, kwargs = mock_run.call_args
        assert args[0] == ["uv", "init", str(tmp_path / "demo"), "--python", "3.12", "--vcs", "none"]
        assert kwargs["cwd"] == tmp_path / "demo"

    def test_command_error_propagates_uncaught(self, tmp_path):
        config = _config(tmp_path)
        step = UvInitStep(config, path=tmp_path)
        with patch(
            "quickstart.steps.uv_init.run_command",
            side_effect=CommandError(["uv", "init"], 1, "boom"),
        ):
            with pytest.raises(CommandError):
                step.execute(config)


class TestGitInitStepExecute:
    def test_calls_run_command_with_git_init(self, tmp_path):
        config = _config(tmp_path, uv=False)
        step = GitInitStep(config, path=tmp_path)
        with patch("quickstart.steps.uv_init.run_command") as mock_run:
            step.execute(config)
        args, kwargs = mock_run.call_args
        assert args[0] == ["git", "init", str(tmp_path / "demo")]
        assert kwargs["cwd"] == tmp_path / "demo"


# ===========================================================================
# CLI integration -- preflight, error surfacing, dry-run transparency
# ===========================================================================


class TestCLIIntegration:
    def test_dry_run_prints_exact_uv_command_and_executes_nothing(self, tmp_path):
        with patch("quickstart.cli.check_uv") as mock_check_uv, \
             patch("quickstart.steps.uv_init.run_command") as mock_run:
            result = _invoke("demo", "--path", str(tmp_path), "--dry-run")
        assert result.exit_code == 0
        # The description uses the raw config.target_path (never the fully
        # resolved parent/name directory) -- see UvInitStep's construction-
        # time comment: computing that requires resolve_target_path(), which
        # has a filesystem side effect the planner must never trigger.
        assert f"uv init {tmp_path}" in result.output
        mock_check_uv.assert_not_called()
        mock_run.assert_not_called()

    def test_no_uv_never_invokes_uv(self, tmp_path):
        with patch("quickstart.cli.check_git", return_value=tmp_path), \
             patch("quickstart.steps.uv_init.run_command") as mock_run:
            result = _invoke("demo", "--path", str(tmp_path), "--no-uv")
        assert result.exit_code == 0
        assert mock_run.call_args[0][0][0] == "git"

    def test_no_uv_no_git_invokes_neither(self, tmp_path):
        with patch("quickstart.steps.uv_init.run_command") as mock_run:
            result = _invoke("demo", "--path", str(tmp_path), "--no-uv", "--no-git")
        assert result.exit_code == 0
        mock_run.assert_not_called()

    def test_default_path_never_invokes_git_init_directly(self, tmp_path):
        with patch("quickstart.cli.check_uv", return_value=tmp_path), \
             patch("quickstart.steps.uv_init.run_command") as mock_run:
            result = _invoke("demo", "--path", str(tmp_path))
        assert result.exit_code == 0
        assert mock_run.call_args[0][0][0] == "uv"

    def test_missing_uv_fails_before_directory_created(self, tmp_path):
        with patch("quickstart.cli.check_uv", return_value=None):
            result = _invoke("demo", "--path", str(tmp_path))
        assert result.exit_code != 0
        assert "--no-uv" in result.output
        assert not (tmp_path / "demo").exists()

    def test_missing_git_fails_when_no_uv(self, tmp_path):
        with patch("quickstart.cli.check_git", return_value=None):
            result = _invoke("demo", "--path", str(tmp_path), "--no-uv")
        assert result.exit_code != 0
        assert "--no-git" in result.output
        assert not (tmp_path / "demo").exists()

    def test_failing_uv_init_surfaces_stderr_and_exits_nonzero(self, tmp_path):
        with patch("quickstart.cli.check_uv", return_value=tmp_path), \
             patch(
                 "quickstart.steps.uv_init.run_command",
                 side_effect=CommandError(["uv", "init"], 1, "network unreachable"),
             ):
            result = _invoke("demo", "--path", str(tmp_path))
        assert result.exit_code != 0
        assert "network unreachable" in result.output

    def test_dry_run_never_checks_uv_or_git_preflight(self, tmp_path):
        with patch("quickstart.cli.check_uv") as mock_uv, \
             patch("quickstart.cli.check_git") as mock_git:
            _invoke("demo", "--path", str(tmp_path), "--dry-run")
        mock_uv.assert_not_called()
        mock_git.assert_not_called()
