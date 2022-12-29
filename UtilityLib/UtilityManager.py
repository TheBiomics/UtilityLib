from .FileSystemUtility import FileSystemUtility

class UtilityManager(FileSystemUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    super(UtilityManager, self).__init__(**self.__defaults)
