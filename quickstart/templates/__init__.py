"""Templates package for quickstart.

Exposes a registry mapping every valid :class:`~quickstart.config.Template`
name to its content provider callable module.  In this milestone all template
names resolve to the same :mod:`quickstart.templates.basic` provider — variant-
specific content is left for a later milestone.
"""

from __future__ import annotations

from quickstart.config import Template
from quickstart.templates import basic

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
# Maps each template name (string value of the Template enum) to the module
# that provides content functions for that template.  Every name currently
# resolves to the basic provider; this mapping is the extension point for
# future variant-specific implementations.

registry: dict[str, object] = {t.value: basic for t in Template}

__all__ = ["registry", "basic"]
