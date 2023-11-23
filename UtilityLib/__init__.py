__package__ = "UtilityLib"
__version__ = '2.8'
__subversion__ = "20231123"
__author__ = "Vishal Kumar Sahu"

from .TimeUtility import TimeUtility
from .DataUtility import DataUtility
from .CommandUtility import CommandUtility
from .DatabaseUtility import DatabaseUtility
from .LoggingUtility import LoggingUtility
from .FileSystemUtility import FileSystemUtility
from .UtilityManager import UtilityManager
from .ProjectManager import ProjectManager, ObjDict

__all__ = ["CommandUtility", "DataUtility", "FileSystemUtility", "UtilityManager", "easyUtility", "EU", "UM"]

@UtilityManager
def UM():
  ...

@UtilityManager
def EU():
  ...

@UtilityManager
def easyUtility():
  ...
