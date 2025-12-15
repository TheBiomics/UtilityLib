from .__metadata__ import __version__, __description__, __build__, __name__

import os as OS
import sys as SYS

from .lib.obj import ObjDict
from .lib.path import EntityPath
from .lib.url import EntityURL
from .lib.file import EntityFile
from .lib.schedule import ScheduleManager
from .lib.task import TaskManager
from .lib.step import StepManager
from .lib.cmd import CMDLib
from .lib.crypt import CryptData

from .project import ProjectManager
from .office import OfficeManager
from .utility import UtilityManager

from typing import Dict

__all__ = ["OfficeManager", "UtilityManager", "ProjectManager",
           "ObjDict", "EntityPath",]

# Convenient aliases
PM = ProjectManager
