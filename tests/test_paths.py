"""Tests for name validation, path resolution, and directory-creation behavior.

Covers:
- validate_project_name: valid names, all invalid-name edge cases, allowed-chars message
- resolve_target_path: default workspace (mocked), explicit --path (exists / missing)
- CreateProjectStep.execute: dry-run, non-dry-run create, already-existing target,
  invalid name, missing explicit --path parent
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from quickstart.config import ProjectConfig
from quickstart.paths import (
    _ALLOWED_CHARS_MSG,
    PathsError,
    resolve_target_path,
    validate_project_name,
)
from quickstart.steps.create_project import CreateProjectStep


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(name: str, target_path: Path) -> ProjectConfig:
    """Create a minimal ProjectConfig with the given name and target_path."""
    return ProjectConfig(project_name=name, target_path=target_path)


# ---------------------------------------------------------------------------
# validate_project_name — valid names
# ---------------------------------------------------------------------------


class TestValidateProjectNameValid:
    """Valid names are returned unchanged."""

    def test_simple_alpha(self):
        assert validate_project_name("myproject") == "myproject"

    def test_alpha_with_digits(self):
        assert validate_project_name("project42") == "project42"

    def test_with_underscore(self):
        assert validate_project_name("my_project") == "my_project"

    def test_with_hyphen(self):
        assert validate_project_name("my-project") == "my-project"

    def test_single_char(self):
        assert validate_project_name("a") == "a"

    def test_starts_with_digit(self):
        # The regex allows [A-Za-z0-9_] as the first character.
        assert validate_project_name("9lives") == "9lives"

    def test_starts_with_underscore(self):
        assert validate_project_name("_hidden") == "_hidden"

    def test_mixed_case(self):
        assert validate_project_name("MyProject") == "MyProject"

    def test_all_caps(self):
        assert validate_project_name("MYPROJECT") == "MYPROJECT"


# ---------------------------------------------------------------------------
# validate_project_name — invalid names
# ---------------------------------------------------------------------------


class TestValidateProjectNameInvalid:
    """Invalid names raise PathsError containing the allowed-characters message."""

    def _assert_raises_with_allowed_chars_msg(self, name: str) -> None:
        with pytest.raises(PathsError) as exc_info:
            validate_project_name(name)
        assert _ALLOWED_CHARS_MSG in str(exc_info.value)

    # Empty string -------------------------------------------------------

    def test_empty_string_raises_paths_error(self):
        with pytest.raises(PathsError):
            validate_project_name("")

    def test_empty_string_message_contains_allowed_chars(self):
        self._assert_raises_with_allowed_chars_msg("")

    # Path traversal: ../evil --------------------------------------------

    def test_dotdot_slash_raises_paths_error(self):
        with pytest.raises(PathsError):
            validate_project_name("../evil")

    def test_dotdot_slash_message_contains_allowed_chars(self):
        self._assert_raises_with_allowed_chars_msg("../evil")

    # Space in name ------------------------------------------------------

    def test_has_space_raises_paths_error(self):
        with pytest.raises(PathsError):
            validate_project_name("has space")

    def test_has_space_message_contains_allowed_chars(self):
        self._assert_raises_with_allowed_chars_msg("has space")

    # Starts with hyphen (flag-like) -------------------------------------

    def test_leading_hyphen_raises_paths_error(self):
        with pytest.raises(PathsError):
            validate_project_name("-flag")

    def test_leading_hyphen_message_contains_allowed_chars(self):
        self._assert_raises_with_allowed_chars_msg("-flag")

    # Other characters outside the allowed set ---------------------------

    def test_dot_in_name_raises(self):
        self._assert_raises_with_allowed_chars_msg("my.project")

    def test_at_sign_raises(self):
        self._assert_raises_with_allowed_chars_msg("my@project")

    def test_slash_only_raises(self):
        self._assert_raises_with_allowed_chars_msg("/")

    def test_absolute_path_raises(self):
        self._assert_raises_with_allowed_chars_msg("/etc/passwd")


# ---------------------------------------------------------------------------
# resolve_target_path — explicit --path
# ---------------------------------------------------------------------------


class TestResolveTargetPathExplicitPath:
    """When an explicit --path is supplied it must exist; the target is <path>/<name>."""

    def test_resolves_to_absolute_path(self, tmp_path: Path):
        target = resolve_target_path("myproject", tmp_path)
        assert target.is_absolute()

    def test_target_is_parent_slash_name(self, tmp_path: Path):
        target = resolve_target_path("myproject", tmp_path)
        assert target == tmp_path.resolve() / "myproject"

    def test_target_not_created_by_resolve(self, tmp_path: Path):
        target = resolve_target_path("myproject", tmp_path)
        assert not target.exists()

    def test_missing_explicit_path_raises_paths_error(self, tmp_path: Path):
        missing = tmp_path / "does_not_exist"
        with pytest.raises(PathsError):
            resolve_target_path("myproject", missing)

    def test_missing_explicit_path_error_mentions_the_path(self, tmp_path: Path):
        missing = tmp_path / "no_such_dir"
        with pytest.raises(PathsError) as exc_info:
            resolve_target_path("myproject", missing)
        assert str(missing.resolve()) in str(exc_info.value)

    def test_explicit_path_that_is_a_file_raises(self, tmp_path: Path):
        file_path = tmp_path / "afile.txt"
        file_path.write_text("hello")
        with pytest.raises(PathsError):
            resolve_target_path("myproject", file_path)

    def test_name_appended_correctly(self, tmp_path: Path):
        target = resolve_target_path("cool_lib", tmp_path)
        assert target.name == "cool_lib"
        assert target.parent == tmp_path.resolve()

    def test_different_names_produce_different_targets(self, tmp_path: Path):
        t1 = resolve_target_path("alpha", tmp_path)
        t2 = resolve_target_path("beta", tmp_path)
        assert t1 != t2


# ---------------------------------------------------------------------------
# resolve_target_path — default workspace (no explicit --path)
# ---------------------------------------------------------------------------


class TestResolveTargetPathDefaultWorkspace:
    """When path=None the default workspace is used and auto-created."""

    def test_default_resolves_to_absolute(self, tmp_path: Path):
        fake_workspace = tmp_path / "workspace"
        with patch("quickstart.paths._DEFAULT_WORKSPACE", Path(str(fake_workspace))):
            target = resolve_target_path("myproject")
        assert target.is_absolute()

    def test_default_workspace_is_created_when_missing(self, tmp_path: Path):
        fake_workspace = tmp_path / "workspace"
        assert not fake_workspace.exists()
        with patch("quickstart.paths._DEFAULT_WORKSPACE", Path(str(fake_workspace))):
            resolve_target_path("myproject")
        assert fake_workspace.exists()

    def test_default_target_is_workspace_slash_name(self, tmp_path: Path):
        fake_workspace = tmp_path / "workspace"
        with patch("quickstart.paths._DEFAULT_WORKSPACE", Path(str(fake_workspace))):
            target = resolve_target_path("myproject")
        assert target == fake_workspace.resolve() / "myproject"

    def test_default_target_itself_not_created(self, tmp_path: Path):
        fake_workspace = tmp_path / "workspace"
        with patch("quickstart.paths._DEFAULT_WORKSPACE", Path(str(fake_workspace))):
            target = resolve_target_path("myproject")
        assert not target.exists()

    def test_default_workspace_already_existing_is_fine(self, tmp_path: Path):
        fake_workspace = tmp_path / "workspace"
        fake_workspace.mkdir()
        with patch("quickstart.paths._DEFAULT_WORKSPACE", Path(str(fake_workspace))):
            # Should not raise even though the directory already exists.
            target = resolve_target_path("myproject")
        assert target == fake_workspace.resolve() / "myproject"


# ---------------------------------------------------------------------------
# CreateProjectStep — dry-run behaviour
# ---------------------------------------------------------------------------


class TestCreateProjectStepDryRun:
    """dry_run=True prints the resolved absolute path and creates no directory."""

    def test_dry_run_prints_resolved_path(self, tmp_path: Path, capsys):
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=True, path=tmp_path)
        step.execute(config)
        captured = capsys.readouterr()
        expected = str(tmp_path.resolve() / "myproject")
        assert expected in captured.out

    def test_dry_run_printed_path_is_absolute(self, tmp_path: Path, capsys):
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=True, path=tmp_path)
        step.execute(config)
        captured = capsys.readouterr()
        printed = captured.out.strip()
        assert Path(printed).is_absolute()

    def test_dry_run_does_not_create_target_directory(self, tmp_path: Path):
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=True, path=tmp_path)
        step.execute(config)
        assert not (tmp_path / "myproject").exists()

    def test_dry_run_completes_without_raising(self, tmp_path: Path):
        """dry_run=True must not raise typer.Exit."""
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=True, path=tmp_path)
        # Should complete without raising.
        step.execute(config)

    def test_dry_run_printed_path_ends_with_project_name(self, tmp_path: Path, capsys):
        config = _make_config("coolproject", tmp_path)
        step = CreateProjectStep(dry_run=True, path=tmp_path)
        step.execute(config)
        captured = capsys.readouterr()
        assert captured.out.strip().endswith("coolproject")


# ---------------------------------------------------------------------------
# CreateProjectStep — non-dry-run: directory creation
# ---------------------------------------------------------------------------


class TestCreateProjectStepCreate:
    """non-dry-run creates the target directory and exits successfully."""

    def test_creates_target_directory(self, tmp_path: Path):
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        step.execute(config)
        assert (tmp_path / "myproject").is_dir()

    def test_target_directory_name_matches_project_name(self, tmp_path: Path):
        config = _make_config("cool_lib", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        step.execute(config)
        assert (tmp_path / "cool_lib").is_dir()

    def test_does_not_print_anything_on_success(self, tmp_path: Path, capsys):
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        step.execute(config)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_no_exit_raised_on_success(self, tmp_path: Path):
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        # Must complete without raising typer.Exit.
        step.execute(config)

    def test_uses_tmp_parent_not_real_home(self, tmp_path: Path):
        """The parent used is the supplied tmp_path, not ~/workspace."""
        config = _make_config("safeproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        step.execute(config)
        home_workspace = Path("~/workspace").expanduser() / "safeproject"
        # We only assert our tmp directory was used; we never touch ~/workspace.
        assert (tmp_path / "safeproject").is_dir()
        # The real home workspace must NOT have been created by this test.
        assert not home_workspace.exists() or home_workspace.parent != tmp_path

    def test_created_directory_is_empty(self, tmp_path: Path):
        config = _make_config("newproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        step.execute(config)
        created = tmp_path / "newproject"
        assert list(created.iterdir()) == []


# ---------------------------------------------------------------------------
# CreateProjectStep — invalid project name
# ---------------------------------------------------------------------------


class TestCreateProjectStepInvalidName:
    """Invalid names cause Exit(code=1) with the allowed-characters message on stderr."""

    @pytest.mark.parametrize("bad_name", ["../evil", "has space", "-flag", ""])
    def test_invalid_name_exits_with_code_1(self, bad_name: str, tmp_path: Path):
        config = _make_config(bad_name, tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit) as exc_info:
            step.execute(config)
        assert exc_info.value.exit_code == 1

    @pytest.mark.parametrize("bad_name", ["../evil", "has space", "-flag", ""])
    def test_invalid_name_prints_allowed_chars_message_to_stderr(
        self, bad_name: str, tmp_path: Path, capsys
    ):
        config = _make_config(bad_name, tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit):
            step.execute(config)
        captured = capsys.readouterr()
        assert _ALLOWED_CHARS_MSG in captured.err

    @pytest.mark.parametrize("bad_name", ["../evil", "has space", "-flag", ""])
    def test_invalid_name_creates_no_directory(
        self, bad_name: str, tmp_path: Path
    ):
        config = _make_config(bad_name, tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        before = set(tmp_path.iterdir())
        with pytest.raises(typer.Exit):
            step.execute(config)
        after = set(tmp_path.iterdir())
        assert before == after

    @pytest.mark.parametrize("bad_name", ["../evil", "has space", "-flag", ""])
    def test_invalid_name_dry_run_also_exits_with_code_1(
        self, bad_name: str, tmp_path: Path
    ):
        config = _make_config(bad_name, tmp_path)
        step = CreateProjectStep(dry_run=True, path=tmp_path)
        with pytest.raises(typer.Exit) as exc_info:
            step.execute(config)
        assert exc_info.value.exit_code == 1


# ---------------------------------------------------------------------------
# CreateProjectStep — missing explicit --path parent
# ---------------------------------------------------------------------------


class TestCreateProjectStepMissingParent:
    """A --path parent that does not exist fails non-zero and creates nothing."""

    def test_missing_path_exits_with_code_1(self, tmp_path: Path):
        missing_parent = tmp_path / "no_such_dir"
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=missing_parent)
        with pytest.raises(typer.Exit) as exc_info:
            step.execute(config)
        assert exc_info.value.exit_code == 1

    def test_missing_path_does_not_create_the_parent(self, tmp_path: Path):
        missing_parent = tmp_path / "no_such_dir"
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=missing_parent)
        with pytest.raises(typer.Exit):
            step.execute(config)
        assert not missing_parent.exists()

    def test_missing_path_does_not_create_the_target(self, tmp_path: Path):
        missing_parent = tmp_path / "no_such_dir"
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=missing_parent)
        with pytest.raises(typer.Exit):
            step.execute(config)
        assert not (missing_parent / "myproject").exists()

    def test_missing_path_prints_error_to_stderr(self, tmp_path: Path, capsys):
        missing_parent = tmp_path / "no_such_dir"
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=missing_parent)
        with pytest.raises(typer.Exit):
            step.execute(config)
        captured = capsys.readouterr()
        assert captured.err.strip() != ""

    def test_missing_path_dry_run_exits_with_code_1(self, tmp_path: Path):
        missing_parent = tmp_path / "no_such_dir"
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=True, path=missing_parent)
        with pytest.raises(typer.Exit) as exc_info:
            step.execute(config)
        assert exc_info.value.exit_code == 1

    def test_missing_path_nothing_added_to_tmp(self, tmp_path: Path):
        missing_parent = tmp_path / "no_such_dir"
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=missing_parent)
        before = set(tmp_path.iterdir())
        with pytest.raises(typer.Exit):
            step.execute(config)
        after = set(tmp_path.iterdir())
        assert before == after


# ---------------------------------------------------------------------------
# CreateProjectStep — already-existing target
# ---------------------------------------------------------------------------


class TestCreateProjectStepAlreadyExists:
    """An already-existing target prints the two-line message, exits non-zero,
    and leaves the existing directory contents unchanged."""

    def _pre_create_target(self, tmp_path: Path, name: str) -> Path:
        """Create the target directory with a sentinel file inside."""
        target = tmp_path / name
        target.mkdir()
        sentinel = target / "existing_file.txt"
        sentinel.write_text("do not remove me")
        return target

    def test_already_existing_exits_with_code_1(self, tmp_path: Path):
        self._pre_create_target(tmp_path, "myproject")
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit) as exc_info:
            step.execute(config)
        assert exc_info.value.exit_code == 1

    def test_already_existing_prints_project_path_already_exists_line(
        self, tmp_path: Path, capsys
    ):
        target = self._pre_create_target(tmp_path, "myproject")
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit):
            step.execute(config)
        captured = capsys.readouterr()
        assert f"Project path already exists: {target}" in captured.out

    def test_already_existing_prints_choose_different_name_line(
        self, tmp_path: Path, capsys
    ):
        self._pre_create_target(tmp_path, "myproject")
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit):
            step.execute(config)
        captured = capsys.readouterr()
        assert "Choose a different name or path." in captured.out

    def test_already_existing_prints_exactly_two_stdout_lines(
        self, tmp_path: Path, capsys
    ):
        self._pre_create_target(tmp_path, "myproject")
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit):
            step.execute(config)
        captured = capsys.readouterr()
        non_empty_lines = [ln for ln in captured.out.splitlines() if ln.strip()]
        assert len(non_empty_lines) == 2

    def test_already_existing_sentinel_file_still_present(self, tmp_path: Path):
        target = self._pre_create_target(tmp_path, "myproject")
        sentinel = target / "existing_file.txt"
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit):
            step.execute(config)
        assert sentinel.exists()

    def test_already_existing_sentinel_file_content_unchanged(self, tmp_path: Path):
        target = self._pre_create_target(tmp_path, "myproject")
        sentinel = target / "existing_file.txt"
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit):
            step.execute(config)
        assert sentinel.read_text() == "do not remove me"

    def test_already_existing_does_not_add_files_to_directory(self, tmp_path: Path):
        target = self._pre_create_target(tmp_path, "myproject")
        files_before = set(target.iterdir())
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit):
            step.execute(config)
        files_after = set(target.iterdir())
        assert files_before == files_after

    def test_already_existing_no_stderr_output(self, tmp_path: Path, capsys):
        """The two-line message goes to stdout, not stderr."""
        self._pre_create_target(tmp_path, "myproject")
        config = _make_config("myproject", tmp_path)
        step = CreateProjectStep(dry_run=False, path=tmp_path)
        with pytest.raises(typer.Exit):
            step.execute(config)
        captured = capsys.readouterr()
        assert captured.err == ""
