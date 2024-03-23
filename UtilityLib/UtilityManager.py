from .FileSystemUtility import FileSystemUtility

class UtilityManager(FileSystemUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    super(UtilityManager, self).__init__(**self.__defaults)

  def preset(self, *args, **kwargs):
    """Presets of Libraries for Different Purposes

@return Returns true|false

@params
0|purpose: data, plot, data_plot

    """
    _purpose = args[0] if len(args) > 0 else kwargs.get("data") # plot

    # Get data libraries
    _res = []

    if 'data' in _purpose:
      _res.append(self.require('pandas', 'PD'))

    if 'plot' in _purpose:
      _res.append(self.require('matplotlib.pyplot', "PLOT"))
      _res.append(self.require('seaborn', "SNS"))
      # Plot default config for publication?
      self.PLOT.rcParams.update({'font.size': 24, 'font.family': 'Times New Roman'})

    return all(_res)
