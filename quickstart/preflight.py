"""Preflight checks for quickstart.

This module exposes lightweight helpers that verify whether required
binaries are available on the system PATH before any real work begins.
No subprocesses are executed at import time; every check is performed
lazily when the caller invokes the relevant function.
"""

from __future__ import annotations

import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def check_uv() -> Path | None:
    """Return the resolved path to the ``uv`` binary, or ``None`` if absent.

    The lookup uses :func:`shutil.which`, which searches the directories
    listed in the ``PATH`` environment variable.

    Returns
    -------
    Path
        Absolute path to the ``uv`` executable when it is found on PATH.
    None
        When ``uv`` cannot be located on PATH.

    Notes
    -----
    This function never executes ``uv`` — it only checks for its presence
    on the filesystem via PATH resolution.
    """
    found = shutil.which("uv")
    if found is None:
        return None
    return Path(found)


def check_git() -> Path | None:
    """Return the resolved path to the ``git`` binary, or ``None`` if absent.

    The lookup uses :func:`shutil.which`, which searches the directories
    listed in the ``PATH`` environment variable.

    Returns
    -------
    Path
        Absolute path to the ``git`` executable when it is found on PATH.
    None
        When ``git`` cannot be located on PATH.

    Notes
    -----
    This function never executes ``git`` — it only checks for its presence
    on the filesystem via PATH resolution.
    """
    found = shutil.which("git")
    if found is None:
        return None
    return Path(found)
