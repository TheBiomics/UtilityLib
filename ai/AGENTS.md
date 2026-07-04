# AGENTS.md — UtilityLib AI Instructions

Guidelines for AI agents (Claude, Copilot, Cursor, etc.) working in this repository.

---

## Project Overview

**UtilityLib** is a Python "wrapper of wrappers" — a unified library that provides every common developer utility through a single import and a single class hierarchy. Instead of importing 15 different packages, you import one and get everything through a consistent, chainable API.

**Motto**: *"One standpoint for whatever a developer needs."*

- **Package**: `UtilityLib` (PyPI)
- **Python**: 3.8 – 3.14
- **Current version**: 2.21.5 → preparing 3.0.0
- **License**: MIT
- **Repo**: https://github.com/TheBiomics/UtilityLib

---

## Class Hierarchy (Inheritance Chain)

```
BaseUtility                 (core/base.py)  — module import, path mgmt, attributes
  └─ TimeUtility            (core/time.py)  — timestamps, date parsing
  └─ LoggingUtility         (core/log.py)   — log levels, file logging
  └─ CommandUtility         (core/cmd.py)   — shell commands, CLI parser
  └─ DatabaseUtility        (core/db.py)    — SQLite, SQLAlchemy, connections
  └─ FileSystemUtility      (core/file.py)  — read/write/compress/zip
       └─ DataUtility       (core/data.py)  — pandas, iteration, type checks
            └─ UtilityManager   (utility.py)  — presets, resource limits
                 └─ ProjectManager  (project.py)  — config, TOML, scheduling
                      └─ BrowserManager   (browser.py)  — Selenium/SeleniumWire
                      └─ CloudManager     (cloud.py)    — AWS/GCP/CPanel
                      └─ OfficeManager    (office.py)   — Excel/Word/PDF
```

**Key insight**: Every class inherits all methods from its parents. `ProjectManager` can do file ops, data processing, shell commands, AND project config — all in one object.

---

## Repository Layout

```
UtilityLib/                  # installable package (src layout)
  __init__.py                # lazy imports + __all__ (public API surface)
  __metadata__.py            # version from distribution metadata
  utility.py                 # UtilityManager
  project.py                 # ProjectManager
  browser.py                 # BrowserManager, ChromeManager, FireFoxManager, BrowserlessManager
  cloud.py                   # CloudManager, AWSManager, GCPManager
  office.py                  # OfficeManager
  core/                      # higher-level wrappers (inherit from each other)
    __init__.py
    base.py                  # BaseUtility — require(), path_base, update_attributes()
    time.py                  # TimeUtility — timestamp, date parsing
    log.py                   # LoggingUtility — log levels
    cmd.py                   # CommandUtility — cmd_run(), init_cli()
    db.py                    # DatabaseUtility — SQLite, SQLAlchemy
    file.py                  # FileSystemUtility — read/write/compress
    data.py                  # DataUtility — pandas, iteration, type checks
  lib/                       # standalone implementations (no cross-lib imports)
    __init__.py
    obj.py                   # ObjDict — dict with dot-notation access
    path.py                  # EntityPath — pathlib.Path subclass with extras
    file.py                  # EntityFile — file operations wrapper
    url.py                   # EntityURL — URL parsing and manipulation
    time.py                  # EntityTime — time operations
    cmd.py                   # CMDLib — CLI argument parser
    db.py                    # standalone DB utilities
    web.py                   # Flask-based web server
    git.py                   # Git, GitManager — git automation
    mail.py                  # SMTP email
    crypt.py                 # CryptData — encryption/hashing
    pm2.py                   # PM2Manager — YAML-driven process manager
    schedule.py              # ScheduleManager, ScheduleEvent
    task.py                  # TaskManager
    step.py                  # StepManager — itertools wrapper
    plot.py                  # Plot — matplotlib/seaborn wrapper
    requests.py              # InsecureSession — requests with SSL bypass
    dom.py                   # DOMSchema, DOMNode — Selenium DOM helpers
    parallel.py              # ParallelExecutor, ParallelManager
    cloudflared.py           # CloudflaredManager — tunnel config
    cloud/                   # cloud provider wrappers
      __init__.py
      aws.py                 # AWSLib
      gcp.py                 # GCPLib
      cpanel.py              # CPanelLib
  cli/                       # argparse CLI entry points
    __init__.py
    __main__.py              # module-level CLI dispatcher
    git.py                   # git CLI
    pm2.py                   # pm2-servers CLI
  docs/                      # markdown docs per module
  ai/                        # AI instructions (this file + README)
pyproject.toml               # package config + console_scripts
README.md
CITATION.cff
```

---

## Key Conventions

### 1. Lazy Imports (Critical)

All non-trivial classes use lazy imports via `__getattr__` in `__init__.py`. This avoids loading heavy dependencies (pandas, selenium, etc.) at import time.

**Pattern** — add to `__init__.py`:
```python
# In __all__:
"NewClass",

# In __getattr__:
elif name == "NewClass":
    from .lib.new_module import NewClass
    return NewClass
```

Never add eager top-level imports for optional/heavy deps.

### 2. The `require()` Pattern

Every class inheriting from `BaseUtility` gets `self.require(module_name, as_name)` — it imports a module and sets it as an attribute on `self`. Results are cached via `@lru_cache`.

```python
self.require("pandas", "PD")      # → self.PD = import_module("pandas")
self.require("matplotlib.pyplot", "PLOT")
self.require_from("pathlib", "Path", "Path")  # from-import
```

### 3. Config Home

User configuration goes to `~/.UtilityLib/` by default. Every module that writes config must:
- Accept an explicit path override (constructor argument or env var)
- Fall back to `~/.UtilityLib/<config-name>`
- Create the directory with `mkdir(parents=True, exist_ok=True)` on first write

### 4. Path Handling

Use `pathlib.Path` and `EntityPath` for all path operations. `EntityPath` extends `pathlib.Path` with:
- `.walk_dirs`, `.walk_files` — iterators
- `.files`, `.dirs` — direct children
- `.tree` / `.tree_gen` — directory tree string
- `.search(glob)` — find matching files
- `.get_match(glob)` — single file match
- `.validate()` — ensure directory exists
- `.read()`, `.write()`, `.read_json()`, `.write_json()`, `.read_toml()`, `.write_toml()`

### 5. No Redundant Comments

Only add inline comments when the *why* is non-obvious. Don't add docstrings explaining what clear code already says. Do add docstrings for public API methods with complex argument patterns.

### 6. Import Style

```python
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# stdlib → third-party → local; all at top of file
```

### 7. Timestamp Format

All timestamps in code, docs, and commits use `YYYYMMDDHHMMSS` format (e.g., `20260604153000`). Use `EntityTime.timestamp` property or `datetime.now().strftime("%Y%m%d%H%M%S")`.

---

## Adding a New Module

### A new `lib/` module (standalone):

1. Create `UtilityLib/lib/<name>.py` with a single top-level class
2. Add lazy import in `UtilityLib/__init__.py` (`__all__` + `__getattr__`)
3. Add doc in `UtilityLib/docs/lib.<name>.md`
4. If it needs a CLI: add `UtilityLib/cli/<name>.py` using `CMDLib.init_cli()`

### A new `core/` module (inherits from chain):

1. Create `UtilityLib/core/<name>.py` inheriting from the appropriate parent in the chain
2. Add import in `UtilityLib/core/__init__.py`
3. Add doc in `UtilityLib/docs/core.<name>.md`

### A new CLI tool:

```python
from ..lib.cmd import CMDLib

def main():
    parser = CMDLib.init_cli(version="UtilityLib.X v1.0", description="…")
    parser.add_argument("--flag", help="…")
    args = parser.parse_args()
    # …
```

Wire in `pyproject.toml`:
```toml
[project.scripts]
my-tool = "UtilityLib.cli.my_module:main"
```

---

## Module Reference

### Core Modules

| Module | Class | Key Methods |
|--------|-------|-------------|
| `base.py` | `BaseUtility` | `require()`, `require_from()`, `update_attributes()`, `path_base` |
| `time.py` | `TimeUtility` | `timestamp`, `date_parse()`, `time_pause()` |
| `log.py` | `LoggingUtility` | `log_debug()`, `log_info()`, `log_error()`, `log_warning()` |
| `cmd.py` | `CommandUtility` | `cmd_run()`, `init_cli()`, `cmd_pipe()` |
| `db.py` | `DatabaseUtility` | `sqlite_connect()`, `sqlalchemy_engine()`, `db_query()` |
| `file.py` | `FileSystemUtility` | `read()`, `write()`, `read_json()`, `write_json()`, `compress()`, `decompress()`, `list_zip_files()` |
| `data.py` | `DataUtility` | `is_numeric()`, `is_array()`, `is_df()`, `unique()`, `loop()` (tqdm), `DF()`, `read_csv()`, `read_excel()`, `to_excel()`, `fix_column_names()`, `filter_digits()`, `filter_alpha()`, `recursive_map()` |

### Top-Level Classes

| Class | File | Purpose |
|-------|------|---------|
| `UtilityManager` | `utility.py` | Presets (`data`, `plot`, `ml`), `add_method()`, `set_resource_limits()` |
| `ProjectManager` | `project.py` | Config management (pickle/TOML), `path_base`, `schedule_event()`, `file_op()` |
| `BrowserManager` | `browser.py` | Selenium/SeleniumWire, `browse_url()`, `screenshot()`, `wait()`, `execute_js()` |
| `ChromeManager` | `browser.py` | Pre-configured Chrome |
| `FireFoxManager` | `browser.py` | Pre-configured Firefox |
| `BrowserlessManager` | `browser.py` | MechanicalSoup (no browser) |
| `CloudManager` | `cloud.py` | Base cloud ops |
| `OfficeManager` | `office.py` | Excel/Word/PDF |

### Lib Modules (Standalone)

| Class | File | Purpose |
|-------|------|---------|
| `ObjDict` | `lib/obj.py` | Dict with dot-notation access |
| `EntityPath` | `lib/path.py` | pathlib.Path subclass with walk/search/tree |
| `EntityFile` | `lib/file.py` | File read/write with encoding detection |
| `EntityURL` | `lib/url.py` | URL parsing, manipulation |
| `EntityTime` | `lib/time.py` | Time formatting, parsing |
| `CMDLib` | `lib/cmd.py` | CLI argument parser |
| `Git` / `GitManager` | `lib/git.py` | Git automation |
| `CryptData` | `lib/crypt.py` | Encryption/hashing |
| `PM2Manager` | `lib/pm2.py` | YAML-driven PM2 process manager |
| `ScheduleManager` | `lib/schedule.py` | Event scheduling |
| `TaskManager` | `lib/task.py` | Task management |
| `StepManager` | `lib/step.py` | itertools wrapper |
| `Plot` | `lib/plot.py` | matplotlib/seaborn wrapper |
| `InsecureSession` | `lib/requests.py` | requests with SSL bypass |
| `DOMSchema` / `DOMNode` | `lib/dom.py` | Selenium DOM helpers |
| `ParallelExecutor` / `ParallelManager` | `lib/parallel.py` | Threading/multiprocessing |
| `CloudflaredManager` | `lib/cloudflared.py` | Cloudflare Tunnel config |
| `FlaskApp` | `lib/web.py` | Flask web server wrapper |

---

## PM2Manager Details

- **Config**: `~/.UtilityLib/pm2-servers.yml` (override: `PM2_SERVERS_CONFIG` env var or `config_path` arg)
- **YAML schema**: `version: 1`, `projects: [...]` with `name`, `enabled`, `dir`, `port`, `command`, optional `tunnels` and `ssh`
- **CLI**: `pm2-servers` / `pm2s` → `UtilityLib/cli/pm2.py:main`
- **`port` is automatically exported as `PORT` env var** before running the command

### CLI Usage

```bash
pm2-servers SSH-MMM4          # start single project
pm2-servers --all              # start all enabled
pm2-servers --stop CSE-EF      # stop
pm2-servers --restart CSE-EF   # restart
pm2-servers --no-bg CSE-EF     # foreground (debug)
pm2-servers --list             # PM2 process list
pm2-servers --logs CSE-EF      # tail logs
pm2-servers --tunnel-config    # print tunnel ingress
pm2-servers --generate-ecosystem > ecosystem.config.js
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `PM2_SERVERS_CONFIG` | Override PM2 config path |
| `SHOW_PM2_STATUS` | Auto-show status after commands |
| `CHECK_PORT_COLLISIONS` | Validate port uniqueness |
| `LOG_LINES` | Default log tail lines |
| `NVM_DIR` | NVM directory for node-based projects |
| `ECOSYSTEM_DEFAULT_PATH` | Default ecosystem config output path |

---

## Common Pitfalls

1. **Don't break lazy imports** — adding eager imports for heavy deps slows startup for everyone
2. **Don't create circular imports** between `lib/` and `core/`
3. **`EntityPath` is a `pathlib.Path` subclass** — don't instantiate it in `lib/` code that has no dependency on it; use plain `Path`
4. **`pyyaml` is a core dependency** — no need to guard yaml imports
5. **Lazy imports break `isinstance` checks** across module reloads in notebooks — document this if relevant
6. **Don't use `print()` for logging** — use `self.log_info()` / `self.log_error()` etc.
7. **All timestamps must use `YYYYMMDDHHMMSS`** — never relative or partial

---

## Version 3.0.0 Roadmap

The next major release focuses on:

1. **Beautiful CLI** — a unified `ul` command with subcommands for all modules (like `hermes`)
2. **Plugin system** — allow third-party extensions
3. **Better type hints** — full mypy compatibility
4. **Async support** — `async` variants of browser, web, and request methods
5. **Improved docs** — auto-generated API docs
6. **Test suite** — pytest coverage for all modules

When working on v3 tasks, create feature branches from `release/3.0.0`.
