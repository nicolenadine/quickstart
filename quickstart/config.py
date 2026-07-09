"""Configuration module for quickstart."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Template(str, Enum):
    """Permitted project template choices."""

    basic = "basic"
    lib = "lib"
    cli = "cli"
    data = "data"


class ConfigError(ValueError):
    """Raised when ProjectConfig receives an invalid combination of inputs."""


@dataclass
class ProjectConfig:
    """Holds every setting needed to scaffold a new project.

    Construct directly or via :meth:`from_cli_inputs` when working with
    values coming from the CLI argument parser.

    Raises
    ------
    ConfigError
        If both *public* and *private* visibility flags are ``True``.
    """

    # Core identity
    project_name: str
    target_path: Path

    # Template
    template: Template = Template.basic

    # Python interpreter
    python_version: str = "3.11"

    # Feature flags — defaults match the task specification
    docker: bool = True
    github_create: bool = False
    vscode_open: bool = True
    git: bool = True
    docker_venv: bool = False

    # Visibility (mutually exclusive; both False means no remote visibility opinion)
    public: bool = False
    private: bool = False

    def __post_init__(self) -> None:
        """Validate the configuration after construction."""
        # Coerce template to the enum so callers may pass raw strings.
        if not isinstance(self.template, Template):
            try:
                self.template = Template(self.template)
            except ValueError:
                allowed = ", ".join(t.value for t in Template)
                raise ConfigError(
                    f"Invalid template {self.template!r}. "
                    f"Allowed values are: {allowed}."
                ) from None

        if self.public and self.private:
            raise ConfigError(
                "Conflicting visibility options: --public and --private are "
                "mutually exclusive. Specify at most one."
            )

    # ------------------------------------------------------------------
    # Alternative constructor
    # ------------------------------------------------------------------

    @classmethod
    def from_cli_inputs(
        cls,
        *,
        project_name: str,
        target_path: Path,
        template: str = Template.basic.value,
        python_version: str = "3.11",
        docker: bool = True,
        github_create: bool = False,
        vscode_open: bool = True,
        git: bool = True,
        docker_venv: bool = False,
        public: bool = False,
        private: bool = False,
    ) -> "ProjectConfig":
        """Construct a :class:`ProjectConfig` from parsed CLI inputs.

        Parameters
        ----------
        project_name:
            Name of the project to scaffold.
        target_path:
            Filesystem path under which the project directory will live.
            No resolution or validation of the path is performed here.
        template:
            One of ``basic``, ``lib``, ``cli``, or ``data``.
        python_version:
            Python interpreter version string (e.g. ``"3.11"``).
        docker:
            Whether to add Docker support.
        github_create:
            Whether to create a remote GitHub repository.
        vscode_open:
            Whether to open the project in VS Code after creation.
        git:
            Whether to initialise a local Git repository.
        docker_venv:
            Whether to use a Docker-based virtual environment.
        public:
            Mark the GitHub repository as public (mutually exclusive with
            *private*).
        private:
            Mark the GitHub repository as private (mutually exclusive with
            *public*).

        Returns
        -------
        ProjectConfig

        Raises
        ------
        ConfigError
            If both *public* and *private* are ``True``, or if *template*
            is not one of the permitted values.
        """
        return cls(
            project_name=project_name,
            target_path=target_path,
            template=template,  # type: ignore[arg-type]  # coerced in __post_init__
            python_version=python_version,
            docker=docker,
            github_create=github_create,
            vscode_open=vscode_open,
            git=git,
            docker_venv=docker_venv,
            public=public,
            private=private,
        )
