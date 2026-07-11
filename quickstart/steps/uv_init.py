"""Step that initialises a new project via uv, with a direct git-init fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from quickstart.config import ProjectConfig, Template
from quickstart.paths import PathsError, resolve_target_path
from quickstart.subprocess_runner import run_command


def _build_uv_init_command(config: ProjectConfig, target: Path | str) -> list[str]:
    """Build the ``uv init`` argument list for *config*, targeting *target*.

    *target* may be the raw, unresolved ``config.target_path`` (used for the
    step's static description, computed at construction time) or the real
    resolved directory (used by :meth:`UvInitStep.execute`) -- flag order and
    presence are identical either way.
    """
    command = ["uv", "init"]
    if config.template == Template.lib:
        command.append("--lib")
    command.append(str(target))
    if config.python_version:
        command += ["--python", config.python_version]
    if not config.git:
        command += ["--vcs", "none"]
    return command


class UvInitStep:
    """Initialise the project via ``uv init``, translating config flags to uv args.

    Parameters
    ----------
    config:
        Project configuration driving the command construction.
    path:
        The raw value of the ``--path`` CLI option, or ``None`` to use the
        default workspace -- the same value :class:`CreateProjectStep`
        receives, so both resolve to the same real target directory.
    """

    name: str = "uv_init"

    def __init__(self, config: ProjectConfig, path: Optional[Path] = None) -> None:
        self.path = path
        # Static description, computed once here at construction time: the
        # CLI's dry-run loop only ever prints step.description -- it never
        # calls execute() on plan steps -- so this must already be the exact
        # command. Uses config.target_path (never None, no filesystem
        # access) rather than the fully resolved directory, since resolving
        # that requires resolve_target_path(), which creates the default
        # ~/workspace parent as a side effect when no --path is given, and
        # the planner must never touch the filesystem at construction time.
        self.description = " ".join(_build_uv_init_command(config, config.target_path))

    def execute(self, config: ProjectConfig) -> None:
        """Resolve the real target directory and run ``uv init`` against it."""
        try:
            target = resolve_target_path(config.project_name, self.path)
        except PathsError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from None
        command = _build_uv_init_command(config, target)
        run_command(command, cwd=target)


class GitInitStep:
    """Initialise a local Git repository directly, when uv is disabled.

    Only ever planned when ``config.uv`` is ``False`` and ``config.git`` is
    ``True`` -- on the default uv-enabled path, uv itself owns local Git
    initialisation (via ``--vcs none`` or its own default), and ``git init``
    is never invoked directly.

    Parameters
    ----------
    config:
        Project configuration driving the description.
    path:
        The raw value of the ``--path`` CLI option, or ``None`` to use the
        default workspace -- the same value :class:`CreateProjectStep`
        receives, so both resolve to the same real target directory.
    """

    name: str = "git_init"

    def __init__(self, config: ProjectConfig, path: Optional[Path] = None) -> None:
        self.path = path
        self.description = f"git init {config.target_path}"

    def execute(self, config: ProjectConfig) -> None:
        """Resolve the real target directory and run ``git init`` against it."""
        try:
            target = resolve_target_path(config.project_name, self.path)
        except PathsError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from None
        run_command(["git", "init", str(target)], cwd=target)
