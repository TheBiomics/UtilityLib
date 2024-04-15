from .__metadata__ import __version__, __description__, __build__, __name__
from .time import TimeUtility
from .data import DataUtility
from .cmd import CommandUtility
from .db import DatabaseUtility
from .log import LoggingUtility
from .file import FileSystemUtility
from .utility import UtilityManager
from .project import ProjectManager, ObjDict

__all__ = ["TimeUtility", "DataUtility", "CommandUtility", "DatabaseUtility", "LoggingUtility", "FileSystemUtility", "UtilityManager", "ProjectManager", "ObjDict"]

@UtilityManager
def _UtilityManager():
  ...

UM = _UtilityManager

@ProjectManager
def _ProjectManager():
  ...

easyUtility = _ProjectManager
EU = _ProjectManager
PM = _ProjectManager
