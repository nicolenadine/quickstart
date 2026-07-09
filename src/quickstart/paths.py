"""Name validation and target-path resolution for quickstart."""

from __future__ import annotations

import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_WORKSPACE = Path("~/workspace")

_VALID_NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_\-]*$")

_ALLOWED_CHARS_MSG = (
    "Project name may only contain letters, digits, hyphens, and underscores, "
    "and must not start with a hyphen."
)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PathsError(ValueError):
    """Raised when name validation or path resolution fails."""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_project_name(name: str) -> str:
    """Validate *name* and return it unchanged if valid.

    Parameters
    ----------
    name:
        The raw PROJECT_NAME string supplied by the caller.

    Returns
    -------
    str
        The validated name, unchanged.

    Raises
    ------
    PathsError
        If *name* is empty, starts with a hyphen, contains a path separator,
        or contains any character outside ``[A-Za-z0-9_-]``.
    """
    if not name:
        raise PathsError(f"Project name must not be empty. {_ALLOWED_CHARS_MSG}")

    # Reject path separators explicitly (os.sep and the POSIX '/').
    separators = {os.sep, "/"}
    for sep in separators:
        if sep in name:
            raise PathsError(
                f"Project name must not contain path separators. {_ALLOWED_CHARS_MSG}"
            )

    if name.startswith("-"):
        raise PathsError(
            f"Project name must not start with a hyphen. {_ALLOWED_CHARS_MSG}"
        )

    if not _VALID_NAME_RE.match(name):
        raise PathsError(
            f"Invalid project name {name!r}. {_ALLOWED_CHARS_MSG}"
        )

    return name


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def resolve_target_path(name: str, path: Path | None = None) -> Path:
    """Resolve the absolute target directory for a new project.

    The target directory is ``<parent>/<name>`` where *parent* is determined
    as follows:

    * If *path* is ``None``, the parent defaults to ``~/workspace`` (expanded).
      This directory is created automatically when it does not yet exist.
    * If *path* is provided, its expanded value is used as the parent.  If
      that directory does not exist a :exc:`PathsError` is raised — no parent
      directories are created for an explicit *path*.

    The target directory itself (``<parent>/<name>``) is **never** created by
    this function.

    Parameters
    ----------
    name:
        A project name that has already been validated by
        :func:`validate_project_name`.
    path:
        The value of the ``--path`` CLI option, or ``None`` to use the
        default workspace.

    Returns
    -------
    Path
        Absolute, fully-resolved path of the form ``<parent>/<name>``.

    Raises
    ------
    PathsError
        If an explicit *path* is provided but does not exist on the
        filesystem.
    """
    if path is None:
        parent = _DEFAULT_WORKSPACE.expanduser().resolve()
        parent.mkdir(parents=True, exist_ok=True)
    else:
        parent = Path(os.path.expanduser(path)).resolve()
        if not parent.exists():
            raise PathsError(
                f"The specified --path directory does not exist: {parent}"
            )
        if not parent.is_dir():
            raise PathsError(
                f"The specified --path is not a directory: {parent}"
            )

    return parent / name
