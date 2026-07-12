"""Step that writes template-driven files into the project directory."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from quickstart.config import ProjectConfig
from quickstart.paths import PathsError, resolve_target_path
from quickstart.templates import registry


class TemplateFilesStep:
    """Write README.md, .env.example, and .gitignore from the selected template.

    Files written
    -------------
    README.md
        Always overwritten with content from the template's
        ``readme_content`` function.  This replaces the stub that ``uv init``
        places there.
    .env.example
        Written from the template's ``env_example_content`` function only when
        the file does not yet exist.  A pre-existing ``.env.example`` is never
        overwritten.
    .gitignore
        A ``.env`` line is ensured to appear exactly once.  If ``.gitignore``
        does not exist it is created with a single ``.env`` line.  If it
        already exists, ``.env`` is appended only when no ``.env`` line is
        already present.  All existing content is preserved.

    Parameters
    ----------
    path:
        The raw value of the ``--path`` CLI option, or ``None`` to use the
        default workspace -- the same value :class:`CreateProjectStep`
        receives, so both resolve to the same real target directory.
    """

    name: str = "template_files"
    description: str = (
        "Write template files: README.md, .env.example, .gitignore"
    )

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path

    def execute(self, config: ProjectConfig) -> None:
        """Resolve the project directory and write template-driven files.

        Parameters
        ----------
        config:
            The project configuration driving the current run.

        Raises
        ------
        typer.Exit
            With code 1 when the target path cannot be resolved.
        """
        try:
            target = resolve_target_path(config.project_name, self.path)
        except PathsError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from None

        # Look up the content provider for the selected template.
        provider = registry[config.template.value]

        # --- README.md (always overwrite) -----------------------------------
        readme = target / "README.md"
        readme.write_text(
            provider.readme_content(config.project_name, docker=config.docker),
            encoding="utf-8",
        )

        # --- .env.example (only if absent) ----------------------------------
        env_example = target / ".env.example"
        if not env_example.exists():
            env_example.write_text(
                provider.env_example_content(),
                encoding="utf-8",
            )

        # --- .gitignore (ensure a '.env' line exists exactly once) ----------
        gitignore = target / ".gitignore"
        if gitignore.exists():
            existing = gitignore.read_text(encoding="utf-8")
            # Check whether any line is exactly '.env'.
            lines = existing.splitlines()
            if ".env" not in lines:
                # Append '.env', ensuring we start on a new line.
                if existing and not existing.endswith("\n"):
                    existing += "\n"
                existing += ".env\n"
                gitignore.write_text(existing, encoding="utf-8")
        else:
            gitignore.write_text(".env\n", encoding="utf-8")
