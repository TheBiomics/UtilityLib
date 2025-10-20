from .core import DataUtility

class UtilityManager(DataUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)

  def preset(self, *args, **kwargs):
    """Presets of Libraries for Different Purposes

@params
0|preset: data, plot, or multiple phrases

    """
    _preset = kwargs.get("preset", args[0] if len(args) > 0 else "")
    _preset = str(_preset).lower()

    # Get data libraries
    _res = []

    if 'ml' in _preset:
      # LOAD ML Libraries
      ...

    if 'data' in _preset:
      _res.append(self.require('pandas', 'PD'))

    if 'plot' in _preset:
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

  # Alter CPU Usage or Memory Limit
  def set_resource_limits(self, *args, **kwargs):
    """Init Background Alerts for
      CPU and Memory Limits
    """
    self.require('psutil', 'PSYS')
    _cpu = self.PSYS.cpu_percent(interval=1)
    _mem = self.PSYS.virtual_memory().percent

    _cpu_limit = kwargs.get('cpu_limit', 80)
    _mem_limit = kwargs.get('memory_limit', 80)

    if _cpu > _cpu_limit:
      self.PSYS.Process().cpu_affinity([0])
      self.PSYS.Process().nice(19)

    if _mem > _mem_limit:
      self.PSYS.Process().memory_limit(_mem_limit)

    if _cpu > _cpu_limit:
      self.PSYS.Process().cpu_affinity([0])
      self.PSYS.Process().nice(19)
