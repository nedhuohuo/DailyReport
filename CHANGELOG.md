# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-08

### Added
- Initial release of DailyReport skill
- Support for generating daily, weekly, and monthly reports from Git activity
- Slash commands: `/dr_init`, `/dr_daily`, `/dr_weekly`, `/dr_monthly`, `/dr_status`
- Python scripts for repository scanning (`dr_scan.py`) and analysis (`dr_analyze.py`)
- Obsidian-compatible Markdown output
- Configuration management via `~/.config/dailyreport/config.json`
- Multi-repository support with per-repo Git user binding
- Three detail levels: brief, standard, detailed
- Token-efficient reporting strategy (weekly/monthly summarize existing reports)

### Features
- **Repository Discovery**: Automatically scan workspace to find Git repositories
- **Git Activity Analysis**: Collect commits, diff stats, and branch activity
- **AI-Powered Summarization**: Generate human-readable reports from Git data
- **Obsidian Integration**: Output compatible with Obsidian vault structure
- **Incremental Updates**: Detect and add new repositories without losing existing config

### Technical
- SKILL.md with dual-trigger mechanism (keyword matching + slash commands)
- Python 3.11+ compatibility
- Read-only Git operations (safety-first design)
- Support for both Codex and Qoder AI tools

## [1.1.0] - 2026-04-08

### Added
- Plugin manifests for Claude Code (`.claude-plugin/plugin.json`) and Cursor (`.cursor-plugin/plugin.json`)
- Plugin-level command entrypoints for `dr_init`, `dr_daily`, `dr_weekly`, `dr_monthly`, and `dr_status`
- Codex installation guide under `.codex/INSTALL.md`

### Changed
- Moved the DailyReport skill to `skills/daily-report/`
- Updated slash-command documentation to use namespaced plugin commands such as `/daily-report:dr_daily`
- Clarified that Codex support is skill-based and slash-command menu support is not guaranteed

### Fixed
- Added `commands` array to `.claude-plugin/plugin.json` so Claude Code can discover slash commands from the plugin manifest
- Replaced non-standard `disable-model-invocation: true` frontmatter with `allowed-tools: Bash, Read, Write, Glob` in all five command files

## [0.1.0] - 2026-04-07

### Added
- Project initialization
- Basic skill structure with SKILL.md
- Initial script scaffolding
