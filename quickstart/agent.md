## Files

__init__.py — Quickstart CLI package
cli.py — Command-line interface for project scaffolding with template and feature configuration
  TemplateChoice (class) — 25-31 — Enum of valid template options (basic, lib, cli, data)
  DockerVenvChoice (class) — 34-38 — Enum of Docker virtual-environment modes (ephemeral, persistent)
  quickstart (function) — 42-181 — Main CLI command that orchestrates project creation with preflight checks and plan execution
config.py — Project configuration dataclass with validation and CLI input constructor
  Template (class) — 11-17 — Enum of permitted template choices
  ConfigError (class) — 20-21 — Exception raised for invalid configuration combinations
  ProjectConfig (class) — 25-155 — Holds all settings for project scaffolding with mutual-exclusivity validation
paths.py — Name validation and target-path resolution utilities
  validate_project_name (function) — 36-76 — Validates project name against allowed character set and format rules
  resolve_target_path (function) — 84-133 — Resolves absolute target directory using ~/workspace default or explicit path
preflight.py — Lightweight PATH-based availability checks for uv and git binaries
  check_uv (function) — 20-41 — Returns resolved path to uv executable or None if absent
  check_git (function) — 44-65 — Returns resolved path to git executable or None if absent
runner.py — Plan assembly and execution engine for project scaffolding steps
  _NoOpStep (class) — 18-37 — Placeholder step performing no side effects, used to establish plan ordering and printing
  planner (function) — 44-136 — Assembles ordered step plan from config with fixed ordering (scaffold, init, template_files, docker, github_create, vscode_open)
  run (function) — 143-163 — Executes plan steps in sequence, halting on first failure
subprocess_runner.py — Subprocess execution wrapper with output capture and typed exception handling
  CommandError (class) — 21-47 — Exception carrying command, return code, and stderr for failed subprocess execution
  run_command (function) — 55-105 — Executes command in working directory, capturing stdout/stderr or raising CommandError
steps/ — Protocol and Step implementations for ordered step execution in quickstart
