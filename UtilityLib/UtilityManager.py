from .FileSystemUtility import FileSystemUtility

class UtilityManager(FileSystemUtility):
  def __init__(self, *args, **kwargs):
    super(UtilityManager, self).__init__(**kwargs)
    self.__defaults = {}
    self.update_attributes(self, kwargs, self.__defaults)
