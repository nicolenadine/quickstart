## Files

__init__.py — Package initialization with version information
cli.py — CLI module with Typer application for quickstart project scaffolding
  TemplateChoice (class) — 23-29 — Enum of valid template choices exposed to argument parser
  DockerVenvChoice (class) — 32-36 — Enum of valid docker-venv choices exposed to argument parser
  quickstart (function) — 40-151 — Typer command for scaffolding new projects with configurable options
config.py — Configuration module for quickstart settings with template enum and validation
  Template (class) — 11-17 — Enum of permitted project template choices
  ConfigError (class) — 20-21 — Exception raised for invalid configuration combinations
  ProjectConfig (class) — 25-149 — Dataclass holding all settings needed to scaffold a new project
  from_cli_inputs (method) — 82-149 — Construct ProjectConfig from parsed CLI argument values
paths.py — Name validation and target-path resolution for project creation
  PathsError (class) — 27-28 — Exception for validation and path resolution failures
  validate_project_name (function) — 36-76 — Validates project name characters and format
  resolve_target_path (function) — 84-133 — Resolves absolute target directory with parent handling
preflight.py — Lightweight helpers that verify required binaries are available on system PATH
  check_uv (function) — 20-41 — Return resolved path to uv binary or None if absent
  check_git (function) — 44-65 — Return resolved path to git binary or None if absent
runner.py — Runner module for quickstart execution logic with planner and executor
  _NoOpStep (class) — 13-32 — Placeholder step performing no side effects during scaffolding
  planner (function) — 39-115 — Assemble ordered plan from config with deterministic step selection
  run (function) — 122-142 — Execute plan steps in order, halting on first failure
steps/ — Step implementations for quickstart workflows
subprocess_runner.py — Subprocess runner primitives for executing external commands with output capture
  CommandError (class) — 21-47 — Exception raised when external command exits with non-zero status
  run_command (function) — 55-105 — Run command inside working directory, capturing stdout and stderr
