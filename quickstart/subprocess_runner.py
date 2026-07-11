"""Subprocess runner primitives for quickstart.

This module provides a single public helper, :func:`run_command`, that
executes an external process, captures its output, and raises a typed
exception on failure.  Nothing in this module executes a subprocess at
import time.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# Typed exception
# ---------------------------------------------------------------------------


class CommandError(Exception):
    """Raised when an external command exits with a non-zero status code.

    Attributes
    ----------
    command:
        The argument list that was executed.
    returncode:
        The process exit code (always non-zero when this exception is raised).
    stderr:
        Text captured from the process's standard error stream.
    """

    def __init__(
        self,
        command: Sequence[str],
        returncode: int,
        stderr: str,
    ) -> None:
        self.command: Sequence[str] = command
        self.returncode: int = returncode
        self.stderr: str = stderr
        cmd_str = " ".join(command)
        super().__init__(
            f"Command {cmd_str!r} failed with exit code {returncode}.\n"
            f"stderr:\n{stderr}"
        )


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------


def run_command(
    command: Sequence[str],
    cwd: Path,
) -> tuple[str, str]:
    """Run *command* inside *cwd*, capturing stdout and stderr.

    The command is executed synchronously.  Both stdout and stderr are
    captured and decoded as UTF-8 (with replacement for undecodable bytes).

    Parameters
    ----------
    command:
        Argument list to execute (e.g. ``["git", "init"]``).  The first
        element is the program; subsequent elements are its arguments.
    cwd:
        Working directory in which the command is executed.  The directory
        must already exist.

    Returns
    -------
    tuple[str, str]
        A ``(stdout, stderr)`` pair containing the captured output of the
        process.  Both strings may be empty.

    Raises
    ------
    CommandError
        If the process exits with a non-zero return code.  The exception
        carries the original *command*, the ``returncode``, and the captured
        ``stderr``.
    FileNotFoundError
        If the executable named by *command[0]* cannot be found on PATH.
    """
    result = subprocess.run(
        list(command),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")

    if result.returncode != 0:
        raise CommandError(
            command=list(command),
            returncode=result.returncode,
            stderr=stderr,
        )

    return stdout, stderr
