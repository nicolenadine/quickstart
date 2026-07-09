"""Step that creates the resolved target project directory."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from quickstart.config import ProjectConfig
from quickstart.paths import PathsError, resolve_target_path, validate_project_name


class CreateProjectStep:
    """Create the resolved target project directory.

    Parameters
    ----------
    dry_run:
        When ``True`` the step prints the resolved absolute target path and
        creates no directory.  When ``False`` the directory is created.
    path:
        The raw value of the ``--path`` CLI option, or ``None`` to use the
        default workspace (``~/workspace``).
    """

    name: str = "create_project"
    description: str = "Create the target project directory"

    def __init__(self, dry_run: bool = False, path: Optional[Path] = None) -> None:
        self.dry_run = dry_run
        self.path = path

    def execute(self, config: ProjectConfig) -> None:
        """Validate the project name, resolve the target path, and create it.

        Parameters
        ----------
        config:
            The project configuration driving the current run.

        Raises
        ------
        typer.Exit
            With code 1 when the name is invalid, the ``--path`` parent does
            not exist, or the target directory already exists.
        """
        # Validate the project name.
        try:
            validate_project_name(config.project_name)
        except PathsError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from None

        # Resolve the absolute target path.
        try:
            target = resolve_target_path(config.project_name, self.path)
        except PathsError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from None

        if self.dry_run:
            typer.echo(str(target))
            return

        # Guard against an already-existing target directory.
        if target.exists():
            typer.echo(f"Project path already exists: {target}")
            typer.echo("Choose a different name or path.")
            raise typer.Exit(code=1)

        # Create the target directory.
        target.mkdir(parents=True, exist_ok=False)
