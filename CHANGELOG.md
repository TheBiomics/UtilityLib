# Changelog

All notable changes to UtilityLib are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Timestamps use `YYYYMMDDHHMMSS` format.

---

## [2.21.5] — 20260616

### Fixed
- **EntityPath `__str__` now always returns expanded path** — previously `str(EntityPath('~/...'))` returned the unexpanded `~`, breaking `gzip.open()`, `os.path.exists()`, and other stdlib functions that don't expand `~`. New code no longer needs the `.resolved()` workaround.

### Added
- **AI documentation** — comprehensive `ai/AGENTS.md` covering architecture, class hierarchy, module reference, conventions, and pitfalls
- **`ul` CLI command** — unified CLI entry point with subcommands: `version`, `info`, `config`, `path`, `json`, `toml`, `env`, `help`, plus passthrough for `pm2` and `git`
- **`ai/README.md`** — overview of the AI knowledgebase
- **`InsecureSession`** — HTTP session with SSL verification disabled for dev/testing
- **`CloudflaredManager`** — manage Cloudflare tunnels (start, stop, status)
- **`DOMSchema` / `DOMNode`** — DOM manipulation classes
- **`ScheduleManager` / `ScheduleEvent`** — event scheduling
- **`TaskManager` / `StepManager`** — task and step orchestration

### Changed
- **Improved `pyproject.toml` description** — now reflects the "one standpoint" motto
- **Added `ul` console script** to `[project.scripts]`

---

## [2.21.4] — 20251029

### Added
- `DOMSchema` and `DOMNode` classes for improved DOM manipulation
- `InsecureSession` for handling insecure HTTPS requests
- `BrowserManager` enhancements: persistent profiles, stealth mode, performance optimizations
- `EntityFile` improvements: read and iteration capabilities
- `EntityURL` improvements: better URL handling
- `EntityPath` compatibility fixes for Python versions
- New dependencies: `xmltodict`, `sqlalchemy`, `psutil`, `seaborn`, `openpyxl`, `schedule`, `humanize`, `cryptography`, `seleniumwire`, `selenium>=4.10.0`, `mechanicalsoup`, `blinker>=1.7.0`

---

## [2.21.0] — 20251128

- Published to PyPI
- DOI: 10.5281/zenodo.6563931

---

## [2.20.1] — Earlier

- PM2 process manager improvements
- Git library enhancements
- Parallelism and Selenium browser opening delay fixes

---

## [2.17] — Earlier

- Event Scheduler (`ScheduleManager`, `ScheduleEvent`)

## [2.16] — Earlier

- `EntityPath` — pathlib.Path subclass

## [2.12] — Earlier

- Various improvements

## [2.10] — Earlier

- Multi-processing support
- `add_method()` — extend classes at runtime
- Method caching for speed

## [2.9] — Earlier

- Various improvements

## [2.8] — Earlier

- Method aliases
- WHL build system setup

## [2.6] — 20221103

- `ProjectManager` — dot notation, pickling, persistent config
- `DataUtility` — quick data processing
- `require_from()` — import from external folders

## [2.5] — 20220905

- `from UtilityLib import EU` shortcut
- Various method additions

## [2.4] — 20220129

- Initial version