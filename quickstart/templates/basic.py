"""Basic template content provider for quickstart.

All functions in this module are **pure** — they accept parameters and return
strings.  They never write files, create directories, or perform any
filesystem operation.

Only plain Python string construction is used; no templating engine is
introduced.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# README.md
# ---------------------------------------------------------------------------

def readme_content(project_name: str, *, docker: bool = False) -> str:
    """Return the content for a ``README.md`` file.

    Parameters
    ----------
    project_name:
        Name of the project; used as the top-level Markdown heading.
    docker:
        When ``True``, an empty placeholder Docker-commands section is
        appended so a later milestone can populate it.  When ``False``,
        no Docker section appears in the output at all.

    Returns
    -------
    str
        Full README.md content.  The first line is exactly
        ``'# <project_name>'``.
    """
    lines: list[str] = [
        f"# {project_name}",
        "",
        f"A project scaffolded with quickstart.",
        "",
        "## Usage",
        "",
        "```bash",
        f"# Install dependencies",
        f"uv sync",
        "",
        f"# Run the project",
        f"python -m {project_name}",
        "```",
    ]

    if docker:
        lines += [
            "",
            "## Docker Commands",
            "",
        ]

    # Ensure the file ends with a single newline.
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# .env.example
# ---------------------------------------------------------------------------

def env_example_content() -> str:
    """Return the content for a ``.env.example`` file.

    Returns
    -------
    str
        A string containing a comment header line followed by placeholder
        environment variable entries.
    """
    lines: list[str] = [
        "# Environment variables for this project.",
        "# Copy this file to .env and fill in the values.",
        "",
        "# Application",
        "APP_ENV=development",
        "APP_DEBUG=false",
        "",
        "# Example secret (replace with a real value)",
        "SECRET_KEY=changeme",
    ]

    return "\n".join(lines) + "\n"


__all__ = ["readme_content", "env_example_content"]
