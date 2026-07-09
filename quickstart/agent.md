## Files

__init__.py — Package initialization with version information
cli.py — CLI module for quickstart command-line interface
config.py — Configuration module for quickstart settings with template enum and validation
  Template (class) — 11-17 — Enum of permitted project template choices
  ConfigError (class) — 20-21 — Exception raised for invalid configuration combinations
  ProjectConfig (class) — 25-149 — Dataclass holding all settings needed to scaffold a new project
  from_cli_inputs (method) — 82-149 — Construct ProjectConfig from parsed CLI argument values
runner.py — Runner module for quickstart execution logic
steps/ — Step implementations for quickstart workflows
