"""Steps subpackage for quickstart."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from quickstart.config import ProjectConfig


@runtime_checkable
class Step(Protocol):
    """Protocol that every plan step must satisfy.

    Attributes
    ----------
    name:
        Short machine-friendly identifier for the step (e.g. ``"scaffold"``)
    description:
        Human-readable sentence shown to the user when the step is printed
        or executed.
    """

    name: str
    description: str

    def execute(self, config: ProjectConfig) -> None:
        """Carry out the step against *config*.

        Parameters
        ----------
        config:
            The project configuration driving the current run.

        Raises
        ------
        Exception
            Any exception raised here is treated by the runner as a step
            failure, which halts execution immediately.
        """
        ...


class Plan:
    """An ordered sequence of :class:`Step` objects.

    Steps are stored and executed in the order they were supplied at
    construction time.

    Parameters
    ----------
    steps:
        Ordered list of steps that make up the plan.
    """

    def __init__(self, steps: list[Step]) -> None:
        self._steps: list[Step] = list(steps)

    @property
    def steps(self) -> list[Step]:
        """Return the ordered list of steps (read-only copy)."""
        return list(self._steps)

    def __len__(self) -> int:
        return len(self._steps)

    def __iter__(self):
        return iter(self._steps)

    def __repr__(self) -> str:  # pragma: no cover
        names = ", ".join(s.name for s in self._steps)
        return f"Plan([{names}])"
