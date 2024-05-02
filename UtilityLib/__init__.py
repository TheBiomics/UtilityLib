from .__metadata__ import __version__, __description__, __build__, __name__

from .office import OfficeManager
from .utility import UtilityManager
from .project import ProjectManager, ObjDict

__all__ = ["OfficeManager", "UtilityManager", "ProjectManager", "ObjDict"]

@ProjectManager
def _ProjectManager():
  ...

UM = easyUtility = EU = PM = _ProjectManager
