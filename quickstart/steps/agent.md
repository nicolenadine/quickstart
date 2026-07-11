## Files

__init__.py — Protocol and Plan classes for ordered step execution in quickstart
  Step (class) — 11-40 — Protocol defining machine-friendly name, description, and execute method for plan steps
  Plan (class) — 43-71 — Ordered sequence container for Step objects with iteration support
create_project.py — Step that creates and validates the resolved target project directory
  CreateProjectStep (class) — 14-73 — Creates target project directory after name validation and path resolution
uv_init.py — Steps for initialising projects via uv init or git init with config-driven command construction
  _build_uv_init_command (function) — 15-31 — Constructs uv init argument list from project config and target path
  UvInitStep (class) — 34-69 — Runs uv init with config flags translated to uv arguments
  GitInitStep (class) — 72-103 — Runs git init directly when uv is disabled but git version control is enabled
