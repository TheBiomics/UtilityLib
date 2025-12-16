from .__metadata__ import __version__, __description__, __build__, __name__

import os as OS
import sys as SYS

# Core imports (no heavy dependencies)
from .lib.obj import ObjDict
from .lib.path import EntityPath

from typing import Dict

__all__ = [
  "ObjDict", "EntityPath",
  "EntityURL", "EntityFile",
  "ScheduleManager", "TaskManager", "StepManager",
  "CMDLib", "CryptData",
  "ProjectManager", "OfficeManager", "UtilityManager",
]

# Lazy imports to avoid loading heavy dependencies unless needed
def __getattr__(name):
  if name == "EntityURL":
    from .lib.url import EntityURL
    return EntityURL
  elif name == "EntityFile":
    from .lib.file import EntityFile
    return EntityFile
  elif name == "ScheduleManager":
    from .lib.schedule import ScheduleManager
    return ScheduleManager
  elif name == "TaskManager":
    from .lib.task import TaskManager
    return TaskManager
  elif name == "StepManager":
    from .lib.step import StepManager
    return StepManager
  elif name == "CMDLib":
    from .lib.cmd import CMDLib
    return CMDLib
  elif name == "CryptData":
    from .lib.crypt import CryptData
    return CryptData
  elif name == "ProjectManager":
    from .project import ProjectManager
    return ProjectManager
  elif name == "OfficeManager":
    from .office import OfficeManager
    return OfficeManager
  elif name == "UtilityManager":
    from .utility import UtilityManager
    return UtilityManager
  elif name == "PM":
    from .project import ProjectManager
    return ProjectManager
  raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
