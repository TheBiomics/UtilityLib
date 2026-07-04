"""
UtilityLib — One standpoint for everything.

Quick start:
    import UtilityLib as UL
    UL.ObjDict, UL.EntityPath, UL.EntityFile, UL.EntityURL, UL.EntityTime
    UL.ProjectManager, UL.UtilityManager, UL.PM2Manager
    UL.Git, UL.CMDLib, UL.SYS, UL.OS

    from UtilityLib import ProjectManager, EntityFile, ObjDict, EntityPath
    from UtilityLib import EU                    # easyUtility = ProjectManager
"""

from .__metadata__ import __version__, __description__, __build__, __name__

# ── stdlib re-exports (used by 10+ projects) ──────────────────
import os as OS
import sys as SYS

# ── Always-available core (no heavy deps) ─────────────────────
from .lib.obj import ObjDict
from .lib.path import EntityPath

# ── Lazy-loaded heavy / optional deps ─────────────────────────
def __getattr__(name: str):
    # Data structures
    if name == "EntityFile":
        from .lib.file import EntityFile; return EntityFile
    if name == "EntityURL":
        from .lib.url import EntityURL; return EntityURL
    if name == "EntityTime":
        from .lib.time import EntityTime; return EntityTime
    if name == "DeltaTime":
        from .lib.time import DeltaTime; return DeltaTime

    # Scheduling & parallel
    if name == "ScheduleManager":
        from .lib.schedule import ScheduleManager; return ScheduleManager
    if name == "ScheduleEvent":
        from .lib.schedule import ScheduleEvent; return ScheduleEvent
    if name == "ParallelExecutor":
        from .lib.parallel import ParallelExecutor; return ParallelExecutor
    if name == "ParallelManager":
        from .lib.parallel import ParallelManager; return ParallelManager
    if name == "TaskManager":
        from .lib.task import TaskManager; return TaskManager
    if name == "StepManager":
        from .lib.step import StepManager; return StepManager

    # System
    if name == "CMDLib":
        from .lib.cmd import CMDLib; return CMDLib
    if name == "DOMSchema":
        from .lib.dom import DOMSchema; return DOMSchema
    if name == "DOMNode":
        from .lib.dom import DOMNode; return DOMNode
    if name == "InsecureSession":
        from .lib.requests import InsecureSession; return InsecureSession
    if name == "SESSION":
        from .lib.requests import SESSION; return SESSION

    # Version control
    if name == "Git":
        from .lib.git import Git; return Git
    if name == "GitManager":
        from .lib.git import GitManager; return GitManager

    # DevOps
    if name == "PM2Manager":
        from .lib.pm2 import PM2Manager; return PM2Manager
    if name == "CloudflaredManager":
        from .lib.cloudflared import CloudflaredManager; return CloudflaredManager

    # Database (SQLAlchemy required)
    if name in ("EntityDB", "SQLiteDB", "SQLDB", "NoSQLDB", "FileDB"):
        from .lib import db; return getattr(db, name)

    # Crypto (cryptography required)
    if name in ("Crypt", "CryptData", "CryptGPG", "CryptGPGData", "CryptPass"):
        from .lib import crypt; return getattr(crypt, name)

    # Managers — heavy inheritance chain
    if name == "ProjectManager":
        from .project import ProjectManager; return ProjectManager
    if name in ("PM", "UM", "EU"):
        from .project import ProjectManager; return ProjectManager
    if name == "UtilityManager":
        from .utility import UtilityManager; return UtilityManager
    if name == "BrowserManager":
        from .browser import BrowserManager; return BrowserManager
    if name == "ChromeManager":
        from .browser import ChromeManager; return ChromeManager
    if name == "OfficeManager":
        from .office import OfficeManager; return OfficeManager
    if name == "CloudManager":
        from .cloud import CloudManager; return CloudManager
    if name == "WebManager":
        from .lib.web import WebManager; return WebManager

    # H5 plugin bundle — use importlib to avoid __getattr__ recursion
    if name == "h5_wall":
        import importlib
        return importlib.import_module(".h5_wall", package=__package__)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# ── Utility functions ─────────────────────────────────────────
def add_sys_path(*paths):
    """Add one or more paths to sys.path if not already there."""
    for _path in paths:
        _path_resolved = OS.path.abspath(OS.path.expanduser(_path))
        if _path_resolved not in SYS.path:
            SYS.path.insert(0, _path_resolved)

__all__ = [
    "__version__", "__description__", "__build__", "__name__",
    "OS", "SYS",
    "ObjDict", "EntityPath", "EntityFile", "EntityURL", "EntityTime", "DeltaTime",
    "CMDLib", "EntityDB", "SQLiteDB", "SQLDB", "NoSQLDB", "FileDB",
    "Crypt", "CryptData", "CryptGPG", "CryptGPGData", "CryptPass",
    "ScheduleManager", "ScheduleEvent", "ParallelExecutor", "ParallelManager",
    "TaskManager", "StepManager",
    "PM2Manager", "CloudflaredManager",
    "DOMSchema", "DOMNode",
    "Git", "GitManager",
    "ProjectManager", "UtilityManager", "BrowserManager", "ChromeManager",
    "OfficeManager", "CloudManager", "WebManager",
    "PM", "UM", "EU",
    "InsecureSession", "SESSION",
    "add_sys_path",
]
