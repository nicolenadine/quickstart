## Files

__init__.py — Package initialization with version information
cli.py — CLI module with Typer application for quickstart project scaffolding
  TemplateChoice (class) — 22-28 — Enum of valid template choices exposed to argument parser
  DockerVenvChoice (class) — 31-35 — Enum of valid docker-venv modes exposed to argument parser
  quickstart (function) — 39-143 — Typer command for scaffolding new projects with configurable options
config.py — Configuration module for quickstart settings with template enum and validation
  Template (class) — 11-17 — Enum of permitted project template choices
  ConfigError (class) — 20-21 — Exception raised for invalid configuration combinations
  ProjectConfig (class) — 25-149 — Dataclass holding all settings needed to scaffold a new project
  from_cli_inputs (method) — 82-149 — Construct ProjectConfig from parsed CLI argument values
runner.py — Runner module for quickstart execution logic with planner and executor
  _NoOpStep (class) — 13-32 — Placeholder step performing no side effects during scaffolding
  planner (function) — 39-115 — Assemble ordered plan from config with deterministic step selection
  run (function) — 122-142 — Execute plan steps in order, halting on first failure
steps/ — Step implementations for quickstart workflows
