"""CLI module for quickstart."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from quickstart.config import ConfigError, ProjectConfig
from quickstart.runner import planner, run
from quickstart.steps.create_project import CreateProjectStep


app = typer.Typer(
    name="quickstart",
    help="Scaffold a new project from a template.",
    add_completion=False,
)


class TemplateChoice(str, Enum):
    """Valid template choices exposed to the Typer argument parser."""

    basic = "basic"
    lib = "lib"
    cli = "cli"
    data = "data"


class DockerVenvChoice(str, Enum):
    """Valid docker-venv choices exposed to the Typer argument parser."""

    ephemeral = "ephemeral"
    persistent = "persistent"


@app.command()
def quickstart(
    project_name: str = typer.Argument(
        ...,
        help="Name of the project to scaffold.",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        help="Directory under which the project folder will be created.",
    ),
    template: TemplateChoice = typer.Option(
        TemplateChoice.basic,
        "--template",
        help="Project template to use.",
    ),
    python: str = typer.Option(
        "3.11",
        "--python",
        help="Python interpreter version (e.g. 3.11).",
    ),
    uv: bool = typer.Option(
        False,
        "--uv/--no-uv",
        help="Use uv for environment management.",
    ),
    git: bool = typer.Option(
        True,
        "--git/--no-git",
        help="Initialise a local Git repository.",
    ),
    gh: bool = typer.Option(
        False,
        "--gh/--no-gh",
        help="Create a remote GitHub repository.",
    ),
    public: bool = typer.Option(
        False,
        "--public",
        is_flag=True,
        help="Mark the GitHub repository as public (mutually exclusive with --private).",
    ),
    private: bool = typer.Option(
        False,
        "--private",
        is_flag=True,
        help="Mark the GitHub repository as private (mutually exclusive with --public).",
    ),
    docker: bool = typer.Option(
        True,
        "--docker/--no-docker",
        help="Add Docker support files.",
    ),
    docker_venv: Optional[DockerVenvChoice] = typer.Option(
        None,
        "--docker-venv",
        help="Docker virtual-environment mode: ephemeral or persistent.",
    ),
    open_: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open the project in VS Code after creation.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        is_flag=True,
        help="Print planned steps without executing them.",
    ),
) -> None:
    """Scaffold a new PROJECT_NAME project."""
    # Resolve the base path: default to the current working directory.
    target_path: Path = path if path is not None else Path(".")

    # Determine docker_venv flag from the optional docker-venv choice.
    use_docker_venv: bool = docker_venv is not None

    # Build the configuration, letting ConfigError surface visibility conflicts.
    try:
        config = ProjectConfig.from_cli_inputs(
            project_name=project_name,
            target_path=target_path,
            template=template.value,
            python_version=python,
            docker=docker,
            github_create=gh,
            vscode_open=open_,
            git=git,
            docker_venv=use_docker_venv,
            public=public,
            private=private,
        )
    except ConfigError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    # Build the create-project step (carries dry_run and the raw --path value).
    create_step = CreateProjectStep(dry_run=dry_run, path=path)

    # Build the ordered plan.
    plan = planner(config)

    if dry_run:
        create_step.execute(config)
        for step in plan:
            typer.echo(step.description)
        raise typer.Exit(code=0)

    # Create the project directory before executing the remaining plan.
    create_step.execute(config)

    # Execute the plan via the runner (steps are no-op placeholders at this stage).
    run(plan, config)
