"""Runner module for quickstart."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from quickstart.config import ProjectConfig
from quickstart.steps import Plan, Step
from quickstart.steps.uv_init import GitInitStep, UvInitStep


# ---------------------------------------------------------------------------
# Concrete no-op step implementations used by the planner
# ---------------------------------------------------------------------------

class _NoOpStep:
    """A placeholder step that performs no side effects.

    Used during this milestone to establish plan ordering and printing
    without invoking any real operations.

    Parameters
    ----------
    name:
        Short machine-friendly identifier for the step.
    description:
        Human-readable sentence describing what the step will eventually do.
    """

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    def execute(self, config: ProjectConfig) -> None:  # noqa: ARG002
        """No-op: this placeholder step intentionally does nothing."""


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

def planner(config: ProjectConfig, path: Optional[Path] = None) -> Plan:
    """Assemble an ordered :class:`~quickstart.steps.Plan` from *config*.

    The steps are chosen and ordered deterministically based on the feature
    flags present in *config*.

    The fixed ordering is:

    1. ``scaffold``      – always present; creates the project skeleton.
    2. ``uv_init``        – present when ``config.uv`` is ``True``; owns local
       Git initialisation itself (via ``--vcs none`` when ``config.git`` is
       ``False``), so ``git_init`` never also appears alongside it.
       ``git_init`` – present when ``config.uv`` is ``False`` and
       ``config.git`` is ``True`` (direct ``git init`` fallback).
    3. ``docker``        – present when ``config.docker`` is ``True``.
    4. ``github_create`` – present when ``config.github_create`` is ``True``.
    5. ``vscode_open``   – present when ``config.vscode_open`` is ``True``.

    Parameters
    ----------
    config:
        Project configuration driving the plan.
    path:
        The raw value of the ``--path`` CLI option, or ``None`` to use the
        default workspace -- forwarded to ``uv_init``/``git_init`` so they
        resolve the same real target directory as ``CreateProjectStep``.

    Returns
    -------
    Plan
        An ordered plan ready to be passed to :func:`run`.
    """
    steps: list[Step] = []

    # Step 1 – always scaffold the project structure.
    steps.append(
        _NoOpStep(
            name="scaffold",
            description=(
                f"Scaffold {config.template.value!r} project "
                f"{config.project_name!r} at {config.target_path}"
            ),
        )
    )

    # Step 2 – initialise the project via uv, or fall back to a direct git
    # init when uv is disabled. uv owns local Git itself on the default
    # path, so these are mutually exclusive, never both present.
    if config.uv:
        steps.append(UvInitStep(config, path=path))
    elif config.git:
        steps.append(GitInitStep(config, path=path))

    # Step 3 – add Docker support when requested.
    if config.docker:
        steps.append(
            _NoOpStep(
                name="docker",
                description="Add Docker support files",
            )
        )

    # Step 4 – create a remote GitHub repository when requested.
    if config.github_create:
        visibility = "public" if config.public else ("private" if config.private else "default")
        steps.append(
            _NoOpStep(
                name="github_create",
                description=f"Create a {visibility} GitHub repository",
            )
        )

    # Step 5 – open the project in VS Code when requested.
    if config.vscode_open:
        steps.append(
            _NoOpStep(
                name="vscode_open",
                description="Open the project in VS Code",
            )
        )

    return Plan(steps)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run(plan: Plan, config: ProjectConfig) -> None:
    """Execute *plan* steps in order, halting on the first failure.

    Each step's :meth:`~quickstart.steps.Step.execute` method is called
    with *config*.  If any step raises an exception the runner re-raises it
    immediately without executing subsequent steps.

    Parameters
    ----------
    plan:
        The ordered plan to execute.
    config:
        Project configuration forwarded to every step.

    Raises
    ------
    Exception
        The exception raised by the first failing step, unchanged.
    """
    for step in plan:
        step.execute(config)
