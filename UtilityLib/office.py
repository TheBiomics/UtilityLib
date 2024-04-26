from .utility import UtilityManager

class OfficeManager(UtilityManager):
  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)
