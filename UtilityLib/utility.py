from .core import FileSystemUtility

class UtilityManager(FileSystemUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)

  def preset(self, *args, **kwargs):
    """Presets of Libraries for Different Purposes

@return Returns true|false

@params
0|purpose: data, plot, data_plot

    """
    _purpose = args[0] if len(args) > 0 else kwargs.get("data") # plot
    _purpose = str(_purpose).lower()

    # Get data libraries
    _res = []

    if 'ml' in _purpose:
      # LOAD ML Libraries
      ...

    if 'data' in _purpose:
      _res.append(self.require('pandas', 'PD'))

    if 'plot' in _purpose:
      _res.append(self.require('matplotlib.pyplot', "PLOT"))
      _res.append(self.require('seaborn', "SNS"))
      # Plot default config for publication?
      self.PLOT.rcParams.update({'font.size': 24, 'font.family': 'Times New Roman'})

    return all(_res)

  def add_method(self, *args, **kwargs):
    """Add/overwrite a new method to the class

@params
0|method_obj: def/method object
1|cls: class object

@example
class CLS:
  ...

def _new_method(self, *args, **kw):
  ...

__UL__.add_method(_new_method)
__UL__.add_method(_new_method, CLS)
"""
    _method_obj = args[0] if len(args) > 0 else kwargs.get("method_obj") # plot
    _cls = args[1] if len(args) > 1 else kwargs.get("cls", self) # plot

    self.require('types', 'TYPES')
    _obj = self.TYPES.MethodType(_method_obj, _cls)
    setattr(_cls, _method_obj.__name__, _obj)

    return hasattr(_cls, _method_obj.__name__)

  set_method = add_method
