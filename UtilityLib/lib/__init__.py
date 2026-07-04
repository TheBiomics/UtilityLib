"""
UtilityLib.lib — standalone utility classes.

Import directly without loading the full UtilityLib chain:
    from UtilityLib.lib import ObjDict, EntityPath, EntityFile
    from UtilityLib.lib import Git, PM2Manager, ScheduleManager
"""

# These are always available (stdlib + lightweight)
from .obj import ObjDict
from .path import EntityPath
from .time import EntityTime, DeltaTime
from .cmd import CMDLib

__all__ = [
    "ObjDict", "EntityPath", "EntityTime", "DeltaTime", "CMDLib",
]
