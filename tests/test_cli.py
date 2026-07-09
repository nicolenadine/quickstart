"""Tests for CLI module."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from quickstart.cli import DockerVenvChoice, TemplateChoice, app
from quickstart.config import ProjectConfig, Template

runner = CliRunner(mix_stderr=False)


def _invoke(*args: str):
    return runner.invoke(app, list(args))


def _combined(result) -> str:
    stderr = getattr(result, "stderr", "") or ""
    return (result.output or "") + stderr


HELP = None


def _help_output() -> str:
    global HELP
    if HELP is None:
        HELP = _invoke("--help").output
    return HELP


class TestHelpOutput:
    def test_help_exits_zero(self):
        assert _invoke("--help").exit_code == 0

    @pytest.mark.parametrize(
        "option",
        [
            "--path",
            "--template",
            "--python",
            "--uv",
            "--git",
            "--gh",
            "--public",
            "--private",
            "--docker",
            "--docker-venv",
            "--open",
            "--dry-run",
        ],
    )
    def test_help_lists_option(self, option):
        assert option in _help_output()

    @pytest.mark.parametrize("value", ["basic", "lib", "cli", "data"])
    def test_help_lists_template_choice(self, value):
        assert value in _help_output()

    @pytest.mark.parametrize("value", ["ephemeral", "persistent"])
    def test_help_lists_docker_venv_choice(self, value):
        assert value in _help_output()


class TestInvalidTemplateValue:
    def test_invalid_template_exits_nonzero(self):
        assert _invoke("myproject", "--template", "notatemplate").exit_code != 0

    @pytest.mark.parametrize("choice", ["basic", "lib", "cli", "data"])
    def test_invalid_template_names_choice(self, choice):
        result = _invoke("myproject", "--template", "notatemplate")
        assert choice in _combined(result)


class TestInvalidDockerVenvValue:
    def test_invalid_docker_venv_exits_nonzero(self):
        assert _invoke("myproject", "--docker-venv", "badmode").exit_code != 0

    @pytest.mark.parametrize("choice", ["ephemeral", "persistent"])
    def test_invalid_docker_venv_names_choice(self, choice):
        result = _invoke("myproject", "--docker-venv", "badmode")
        assert choice in _combined(result)


class TestVisibilityConflict:
    def test_public_and_private_exits_nonzero(self):
        assert _invoke("myproject", "--public", "--private").exit_code != 0

    def test_public_and_private_reports_conflict(self):
        result = _invoke("myproject", "--public", "--private")
        combined = _combined(result).lower()
        assert "conflict" in combined or "mutually exclusive" in combined

    def test_public_and_private_mentions_public(self):
        assert "public" in _combined(_invoke("myproject", "--public", "--private")).lower()

    def test_public_and_private_mentions_private(self):
        assert "private" in _combined(_invoke("myproject", "--public", "--private")).lower()


class TestDryRun:
    def test_dry_run_exits_zero(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert result.exit_code == 0

    def test_dry_run_prints_scaffold_description(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert "demoproject" in result.output

    def test_dry_run_prints_git_step(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert "git" in result.output.lower()

    def test_dry_run_prints_docker_step(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert "docker" in result.output.lower()

    def test_dry_run_prints_vscode_step(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        lowered = result.output.lower()
        assert "vs code" in lowered or "vscode" in lowered

    def test_dry_run_scaffold_before_git(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        scaffold_idx = next((i for i, ln in enumerate(lines) if "demoproject" in ln), None)
        git_idx = next((i for i, ln in enumerate(lines) if "git" in ln.lower()), None)
        assert scaffold_idx is not None and git_idx is not None
        assert scaffold_idx < git_idx

    def test_dry_run_git_before_docker(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        git_idx = next((i for i, ln in enumerate(lines) if "git" in ln.lower()), None)
        docker_idx = next((i for i, ln in enumerate(lines) if "docker" in ln.lower()), None)
        assert git_idx is not None and docker_idx is not None
        assert git_idx < docker_idx

    def test_dry_run_creates_no_filesystem_entries(self, tmp_path):
        before = set(tmp_path.rglob("*"))
        _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert set(tmp_path.rglob("*")) == before

    def test_dry_run_creates_no_directories(self, tmp_path):
        before = {p for p in tmp_path.rglob("*") if p.is_dir()}
        _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert {p for p in tmp_path.rglob("*") if p.is_dir()} == before

    def test_dry_run_minimal_prints_only_scaffold(self, tmp_path):
        result = _invoke(
            "minimal", "--path", str(tmp_path),
            "--no-git", "--no-docker", "--no-open", "--dry-run",
        )
        assert result.exit_code == 0
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 1

    def test_dry_run_with_gh_includes_github_step(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--gh", "--dry-run")
        assert "github" in result.output.lower()


class TestProjectConfigDefaults:
    @pytest.fixture()
    def default_config(self, tmp_path) -> ProjectConfig:
        return ProjectConfig.from_cli_inputs(
            project_name="testproject",
            target_path=tmp_path,
        )

    def test_default_template_is_basic(self, default_config):
        assert default_config.template == Template.basic

    def test_default_docker_enabled(self, default_config):
        assert default_config.docker is True

    def test_default_github_create_disabled(self, default_config):
        assert default_config.github_create is False

    def test_default_vscode_open_enabled(self, default_config):
        assert default_config.vscode_open is True

    def test_default_git_enabled(self, default_config):
        assert default_config.git is True


class TestChoiceEnums:
    @pytest.mark.parametrize(
        "member,value",
        [
            (TemplateChoice.basic, "basic"),
            (TemplateChoice.lib, "lib"),
            (TemplateChoice.cli, "cli"),
            (TemplateChoice.data, "data"),
        ],
    )
    def test_template_choice_values(self, member, value):
        assert member.value == value

    def test_template_choice_member_count(self):
        assert len(TemplateChoice) == 4

    @pytest.mark.parametrize(
        "member,value",
        [
            (DockerVenvChoice.ephemeral, "ephemeral"),
            (DockerVenvChoice.persistent, "persistent"),
        ],
    )
    def test_docker_venv_choice_values(self, member, value):
        assert member.value == value

    def test_docker_venv_choice_member_count(self):
        assert len(DockerVenvChoice) == 2
