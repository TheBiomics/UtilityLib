# UtilityLib

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/utilitylib?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLUE&right_color=BLACK&left_text=All)](https://pepy.tech/projects/utilitylib)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/utilitylib?period=monthly&units=INTERNATIONAL_SYSTEM&left_color=BLUE&right_color=BLACK&left_text=This+Month)](https://pepy.tech/projects/utilitylib)

**One standpoint for everything.**

A unified Python utility library of wrappers — file, data, web, cloud, browser, email, encryption, process management, and more — all through one consistent, chainable API.

```python
from UtilityLib import ProjectManager

proj = ProjectManager(path_base="./my-project")
proj.config.database = "sqlite:///data.db"
df = proj.read_csv("data.csv")
proj.to_excel("output.xlsx", df, "Results")
```

## Installation

```bash
pip install UtilityLib
```

With all optional dependencies:

```bash
pip install UtilityLib[all]
```

## Quick Start

```python
# One import, everything available
from UtilityLib import ObjDict, EntityPath, EntityFile, EntityURL
from UtilityLib import ProjectManager, BrowserManager, PM2Manager

# Dict with dot notation
config = ObjDict({"db": {"host": "localhost"}})
print(config.db.host)  # "localhost"

# Path with superpowers
path = EntityPath("~/Documents")
print(path.tree)       # directory tree
print(path.search("*.pdf"))  # find PDFs

# File operations
ef = EntityFile("data.json")
data = ef.read_json()

# Project manager (inherits EVERYTHING above)
proj = ProjectManager(path_base=".")
proj.config.api_key = "secret"
proj.save_config()

# Execute shell commands
proj.cmd_run("ls -la")
```

## Available Classes

| Category | Classes | Module |
|----------|---------|--------|
| **Core** | `ObjDict`, `EntityPath`, `EntityFile`, `EntityURL`, `EntityTime`, `DeltaTime` | `lib/obj`, `lib/path`, `lib/file`, `lib/url`, `lib/time` |
| **Project** | `ProjectManager` | `project` |
| **Utility** | `UtilityManager` | `utility` |
| **Command** | `CMDLib` | `lib/cmd` |
| **Version Control** | `Git`, `GitManager` | `lib/git` |
| **DevOps** | `PM2Manager`, `CloudflaredManager` | `lib/pm2`, `lib/cloudflared` |
| **Database** | `SQLiteDB`, `SQLDB`, `NoSQLDB`, `FileDB`, `EntityDB` | `lib/db` |
| **Browser** | `BrowserManager`, `ChromeManager`, `FireFoxManager`, `BrowserlessManager` | `browser` |
| **Cloud** | `CloudManager`, `AWSManager`, `GCPManager` | `cloud` |
| **Office** | `OfficeManager` | `office` |
| **Parallel** | `ParallelExecutor`, `ParallelManager` | `lib/parallel` |
| **Task** | `TaskManager`, `StepManager` | `lib/task`, `lib/step` |
| **Schedule** | `ScheduleManager`, `ScheduleEvent` | `lib/schedule` |
| **Crypto** | `Crypt`, `CryptData`, `CryptGPG`, `CryptGPGData`, `CryptPass`, `CryptPassData` | `lib/crypt` |
| **DOM** | `DOMSchema`, `DOMNode` | `lib/dom` |
| **Web** | `WebManager`, `InsecureSession` | `lib/web`, `lib/requests` |
| **Email** | `MailEntity` | `lib/mail` |
| **Plot** | `Plot` | `lib/plot` |

> **Note:** Cloud (`AWSLib`, `CPanelLib`, `GCPLib`), Email (`MailEntity`), and Plot (`Plot`) are stub modules — class definitions only, not yet implemented.

## CLI

```bash
ul info              # show library info
ul path ~/Documents  # inspect a path
ul json data.json    # pretty-print JSON
ul pm2 --list        # PM2 process manager
ul git --help        # Git automation
```

## Architecture

```
BaseUtility → TimeUtility → LoggingUtility → CommandUtility → DatabaseUtility
  → FileSystemUtility → DataUtility → UtilityManager → ProjectManager
                                                      → BrowserManager
                                                      → CloudManager
```

Each class inherits all methods from its parents. `ProjectManager` can do file ops, data processing, shell commands, AND project config — all in one object.

## Config Home

`~/.UtilityLib/` — all persistent configuration, logs, and data files.

## License

MIT © Vishal Kumar Sahu

## Citation

```bibtex
@software{utilitylib,
  title = {UtilityLib: Reusable and Optimised Python Classes},
  author = {Sahu, Vishal Kumar and Ranjan, Amit and Basu, Soumya},
  doi = {10.5281/zenodo.6563931},
  url = {https://github.com/TheBiomics/UtilityLib}
}
```