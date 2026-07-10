"""Tests for CLI module."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from quickstart.cli import DockerVenvChoice, TemplateChoice, app
from quickstart.config import ProjectConfig, Template

runner = CliRunner()


def _invoke(*args: str):
    return runner.invoke(app, list(args))


def _combined(result) -> str:
    """Merge stdout and stderr into a single string for assertion convenience."""
    stderr = getattr(result, "stderr", "") or ""
    return (result.output or "") + stderr


# ---------------------------------------------------------------------------
# Cache the help output once so parametrised tests share a single invocation.
# ---------------------------------------------------------------------------

_HELP_OUTPUT: str | None = None


def _help_output() -> str:
    global _HELP_OUTPUT
    if _HELP_OUTPUT is None:
        _HELP_OUTPUT = _invoke("--help").output
    return _HELP_OUTPUT


# ===========================================================================
# Help output
# ===========================================================================


class TestHelpOutput:
    """The --help flag must exit 0 and list every supported option."""

    def test_help_exits_zero(self):
        assert _invoke("--help").exit_code == 0

    # ---- every option must appear verbatim --------------------------------

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
    def test_help_lists_option(self, option: str):
        assert option in _help_output(), (
            f"Option {option!r} not found in --help output"
        )

    # ---- PROJECT_NAME positional argument ---------------------------------

    def test_help_mentions_project_name_argument(self):
        # Typer renders the argument name in upper-case in the usage line.
        output = _help_output().upper()
        assert "PROJECT_NAME" in output or "PROJECT-NAME" in output

    # ---- template choices -------------------------------------------------

    @pytest.mark.parametrize("value", ["basic", "lib", "cli", "data"])
    def test_help_lists_template_choice(self, value: str):
        assert value in _help_output(), (
            f"Template choice {value!r} not found in --help output"
        )

    # ---- docker-venv choices ----------------------------------------------

    @pytest.mark.parametrize("value", ["ephemeral", "persistent"])
    def test_help_lists_docker_venv_choice(self, value: str):
        assert value in _help_output(), (
            f"docker-venv choice {value!r} not found in --help output"
        )


# ===========================================================================
# Invalid --template value
# ===========================================================================


class TestInvalidTemplateValue:
    """An unrecognised --template value must fail with a helpful message."""

    def test_invalid_template_exits_nonzero(self):
        result = _invoke("myproject", "--template", "notatemplate")
        assert result.exit_code != 0

    @pytest.mark.parametrize("choice", ["basic", "lib", "cli", "data"])
    def test_invalid_template_output_names_valid_choice(self, choice: str):
        result = _invoke("myproject", "--template", "notatemplate")
        assert choice in _combined(result), (
            f"Valid template choice {choice!r} not listed in error output"
        )

    def test_invalid_template_output_references_invalid_value(self):
        result = _invoke("myproject", "--template", "notatemplate")
        assert "notatemplate" in _combined(result)


# ===========================================================================
# Invalid --docker-venv value
# ===========================================================================


class TestInvalidDockerVenvValue:
    """An unrecognised --docker-venv value must fail with a helpful message."""

    def test_invalid_docker_venv_exits_nonzero(self):
        result = _invoke("myproject", "--docker-venv", "badmode")
        assert result.exit_code != 0

    @pytest.mark.parametrize("choice", ["ephemeral", "persistent"])
    def test_invalid_docker_venv_output_names_valid_choice(self, choice: str):
        result = _invoke("myproject", "--docker-venv", "badmode")
        assert choice in _combined(result), (
            f"Valid docker-venv choice {choice!r} not listed in error output"
        )

    def test_invalid_docker_venv_output_references_invalid_value(self):
        result = _invoke("myproject", "--docker-venv", "badmode")
        assert "badmode" in _combined(result)


# ===========================================================================
# --public / --private conflict
# ===========================================================================


class TestVisibilityConflict:
    """--public and --private together must fail with a conflict message."""

    def test_public_and_private_exits_nonzero(self):
        result = _invoke("myproject", "--public", "--private")
        assert result.exit_code != 0

    def test_public_and_private_reports_conflict_keyword(self):
        result = _invoke("myproject", "--public", "--private")
        combined = _combined(result).lower()
        assert "conflict" in combined or "mutually exclusive" in combined

    def test_public_and_private_message_mentions_public(self):
        result = _invoke("myproject", "--public", "--private")
        assert "public" in _combined(result).lower()

    def test_public_and_private_message_mentions_private(self):
        result = _invoke("myproject", "--public", "--private")
        assert "private" in _combined(result).lower()

    def test_public_alone_exits_zero(self, tmp_path):
        # --public without --private must NOT conflict.
        result = _invoke("myproject", "--path", str(tmp_path), "--public", "--dry-run")
        assert result.exit_code == 0

    def test_private_alone_exits_zero(self, tmp_path):
        # --private without --public must NOT conflict.
        result = _invoke("myproject", "--path", str(tmp_path), "--private", "--dry-run")
        assert result.exit_code == 0


# ===========================================================================
# Dry-run behaviour
# ===========================================================================


class TestDryRun:
    """--dry-run must exit 0, print an ordered step list, and touch nothing."""

    # ---- exit code --------------------------------------------------------

    def test_dry_run_exits_zero(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert result.exit_code == 0

    # ---- step descriptions present in output ------------------------------

    def test_dry_run_scaffold_step_contains_project_name(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert "demoproject" in result.output

    def test_dry_run_scaffold_step_contains_template(self, tmp_path):
        result = _invoke(
            "demoproject", "--path", str(tmp_path),
            "--template", "lib", "--dry-run",
        )
        assert "lib" in result.output

    def test_dry_run_git_step_present_by_default(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert "git" in result.output.lower()

    def test_dry_run_docker_step_present_by_default(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert "docker" in result.output.lower()

    def test_dry_run_vscode_step_present_by_default(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        lowered = result.output.lower()
        assert "vs code" in lowered or "vscode" in lowered

    def test_dry_run_github_step_present_when_gh_flag_given(self, tmp_path):
        result = _invoke(
            "demoproject", "--path", str(tmp_path), "--gh", "--dry-run"
        )
        assert "github" in result.output.lower()

    def test_dry_run_github_step_absent_when_gh_not_given(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert "github" not in result.output.lower()

    # ---- ordering ---------------------------------------------------------

    def test_dry_run_scaffold_before_git(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        scaffold_idx = next(
            (i for i, ln in enumerate(lines) if "demoproject" in ln), None
        )
        git_idx = next(
            (i for i, ln in enumerate(lines) if "git" in ln.lower()), None
        )
        assert scaffold_idx is not None, "scaffold step not found in output"
        assert git_idx is not None, "git step not found in output"
        assert scaffold_idx < git_idx

    def test_dry_run_git_before_docker(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        git_idx = next(
            (i for i, ln in enumerate(lines) if "git" in ln.lower()), None
        )
        docker_idx = next(
            (i for i, ln in enumerate(lines) if "docker" in ln.lower()), None
        )
        assert git_idx is not None, "git step not found in output"
        assert docker_idx is not None, "docker step not found in output"
        assert git_idx < docker_idx

    def test_dry_run_docker_before_vscode(self, tmp_path):
        result = _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        docker_idx = next(
            (i for i, ln in enumerate(lines) if "docker" in ln.lower()), None
        )
        vscode_idx = next(
            (i for i, ln in enumerate(lines)
             if "vs code" in ln.lower() or "vscode" in ln.lower()),
            None,
        )
        assert docker_idx is not None, "docker step not found in output"
        assert vscode_idx is not None, "vscode step not found in output"
        assert docker_idx < vscode_idx

    def test_dry_run_full_order_scaffold_git_docker_github_vscode(self, tmp_path):
        """All five steps must appear in the documented order."""
        result = _invoke(
            "demoproject", "--path", str(tmp_path), "--gh", "--dry-run"
        )
        lines = [ln.lower() for ln in result.output.splitlines() if ln.strip()]

        def idx_of(keyword: str) -> int:
            for i, ln in enumerate(lines):
                if keyword in ln:
                    return i
            raise AssertionError(f"keyword {keyword!r} not found in output lines")

        scaffold_i = idx_of("demoproject")
        git_i = idx_of("git")
        docker_i = idx_of("docker")
        github_i = idx_of("github")
        vscode_i = next(
            (i for i, ln in enumerate(lines) if "vs code" in ln or "vscode" in ln),
            None,
        )
        assert vscode_i is not None, "vscode step not found"
        assert scaffold_i < git_i < docker_i < github_i < vscode_i

    # ---- no output when all optional steps disabled -----------------------

    def test_dry_run_minimal_prints_only_one_line(self, tmp_path):
        result = _invoke(
            "minimal", "--path", str(tmp_path),
            "--no-git", "--no-docker", "--no-open", "--dry-run",
        )
        assert result.exit_code == 0
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 1, f"Expected 1 line, got {len(lines)}: {lines}"

    def test_dry_run_minimal_only_scaffold_step(self, tmp_path):
        result = _invoke(
            "minimal", "--path", str(tmp_path),
            "--no-git", "--no-docker", "--no-open", "--dry-run",
        )
        assert "minimal" in result.output

    # ---- no filesystem side-effects ---------------------------------------

    def test_dry_run_creates_no_new_filesystem_entries(self, tmp_path):
        before = set(tmp_path.rglob("*"))
        _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        after = set(tmp_path.rglob("*"))
        assert after == before, (
            f"Unexpected filesystem entries created: {after - before}"
        )

    def test_dry_run_creates_no_new_directories(self, tmp_path):
        before = {p for p in tmp_path.rglob("*") if p.is_dir()}
        _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        after = {p for p in tmp_path.rglob("*") if p.is_dir()}
        assert after == before, (
            f"Unexpected directories created: {after - before}"
        )

    def test_dry_run_creates_no_new_files(self, tmp_path):
        before = {p for p in tmp_path.rglob("*") if p.is_file()}
        _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        after = {p for p in tmp_path.rglob("*") if p.is_file()}
        assert after == before, (
            f"Unexpected files created: {after - before}"
        )

    def test_dry_run_does_not_create_project_directory(self, tmp_path):
        project_dir = tmp_path / "demoproject"
        _invoke("demoproject", "--path", str(tmp_path), "--dry-run")
        assert not project_dir.exists()


# ===========================================================================
# Default ProjectConfig values produced via CLI defaults
# ===========================================================================


class TestProjectConfigDefaults:
    """ProjectConfig.from_cli_inputs with all defaults must match the spec."""

    @pytest.fixture()
    def default_config(self, tmp_path) -> ProjectConfig:
        return ProjectConfig.from_cli_inputs(
            project_name="testproject",
            target_path=tmp_path,
        )

    def test_default_template_is_basic(self, default_config):
        assert default_config.template == Template.basic

    def test_default_template_value_string(self, default_config):
        assert default_config.template.value == "basic"

    def test_default_docker_is_enabled(self, default_config):
        assert default_config.docker is True

    def test_default_github_create_is_disabled(self, default_config):
        assert default_config.github_create is False

    def test_default_vscode_open_is_enabled(self, default_config):
        assert default_config.vscode_open is True

    def test_default_git_is_enabled(self, default_config):
        assert default_config.git is True

    def test_default_public_is_false(self, default_config):
        assert default_config.public is False

    def test_default_private_is_false(self, default_config):
        assert default_config.private is False

    def test_default_docker_venv_is_false(self, default_config):
        assert default_config.docker_venv is False

    def test_default_python_version(self, default_config):
        assert default_config.python_version == "3.11"


# ===========================================================================
# CLI-driven default config (via dry-run invocation)
# ===========================================================================


class TestCLIDefaultsViaDryRun:
    """Verify that default CLI behaviour (dry-run) reflects correct defaults."""

    def test_default_run_uses_basic_template(self, tmp_path):
        result = _invoke("myproject", "--path", str(tmp_path), "--dry-run")
        assert "basic" in result.output

    def test_default_run_includes_git_step(self, tmp_path):
        result = _invoke("myproject", "--path", str(tmp_path), "--dry-run")
        assert "git" in result.output.lower()

    def test_default_run_includes_docker_step(self, tmp_path):
        result = _invoke("myproject", "--path", str(tmp_path), "--dry-run")
        assert "docker" in result.output.lower()

    def test_default_run_includes_vscode_step(self, tmp_path):
        result = _invoke("myproject", "--path", str(tmp_path), "--dry-run")
        lowered = result.output.lower()
        assert "vs code" in lowered or "vscode" in lowered

    def test_default_run_excludes_github_step(self, tmp_path):
        result = _invoke("myproject", "--path", str(tmp_path), "--dry-run")
        assert "github" not in result.output.lower()


# ===========================================================================
# TemplateChoice and DockerVenvChoice enum integrity
# ===========================================================================


class TestChoiceEnums:
    """Enum members must have exactly the expected values."""

    @pytest.mark.parametrize(
        "member,expected",
        [
            (TemplateChoice.basic, "basic"),
            (TemplateChoice.lib, "lib"),
            (TemplateChoice.cli, "cli"),
            (TemplateChoice.data, "data"),
        ],
    )
    def test_template_choice_value(self, member, expected):
        assert member.value == expected

    def test_template_choice_has_exactly_four_members(self):
        assert len(TemplateChoice) == 4

    @pytest.mark.parametrize(
        "member,expected",
        [
            (DockerVenvChoice.ephemeral, "ephemeral"),
            (DockerVenvChoice.persistent, "persistent"),
        ],
    )
    def test_docker_venv_choice_value(self, member, expected):
        assert member.value == expected

    def test_docker_venv_choice_has_exactly_two_members(self):
        assert len(DockerVenvChoice) == 2

    def test_template_choice_is_str_subclass(self):
        assert isinstance(TemplateChoice.basic, str)

    def test_docker_venv_choice_is_str_subclass(self):
        assert isinstance(DockerVenvChoice.ephemeral, str)
