import importlib as MODULE_IMPORTER
from os import getpid
import os as OS

class BaseUtility:
  name = "UtilityLib"
  def __init__(self, *args, **kwargs):
    self.__defaults = {
      "_imported_modules": [],
    }
    self.__defaults.update(kwargs)
    self.set_system_type(**self.__defaults)
    self.update_attributes(self, self.__defaults)

  def is_running(self, *args, **kwargs):
    _file = args[0] if len(args) > 0 else kwargs.get("file", "process-v2.txt")
    _dir = args[1] if len(args) > 1 else kwargs.get("dir", 'Documents/PyProcessConfig')

    _path_user_settings = OS.path.join(OS.path.expanduser('~'), _dir)
    _path_file_pid = f"{_path_user_settings}/{_file}"

    if not OS.path.exists(_path_user_settings):
      OS.makedirs(_path_user_settings)

    _current_pid = getpid()

    from psutil import pid_exists, Process

    if OS.path.exists(_path_file_pid):
      with open(_path_file_pid) as f:
        pid = f.read()
        pid = int(pid) if pid.isnumeric() else None
      if pid is not None and pid_exists(pid) and Process(pid).cmdline() == Process(_current_pid).cmdline():
        return True

    with open(_path_file_pid, 'w') as f:
      f.write(str(_current_pid))

    return False

  def set_logging(self, *args, **kwargs):
    import logging
    import warnings
    self.LOGGER = logging.getLogger(self.name + "Logs")
    logging.captureWarnings(True)
    self.WARNINGS = warnings
    self.LOGGER.setLevel(logging.INFO)
    self.LOGGER_WARNING = logging.getLogger('py.warnings')

  def update_attributes(self, object=None, kw=dict(), defaults=dict()):
    """
      Sets attribute (dict) values and defaults
    """
    if object is None:
      object = self

    if isinstance(kw.get('path_bases'), (list, tuple)):
      self.set_directories(**kw)

    [setattr(object, _k, defaults[_k]) for _k in defaults.keys() if not hasattr(object, _k)]
    [setattr(object, _k, kw[_k]) for _k in kw.keys()]

  def set_directories(self, *args, **kwargs):
    _path_bases = args[0] if len(args) > 0 else kwargs.get("path_bases", self.OS.getcwd())
    # Consider first path is for Linux and second path is for Windows
    if isinstance(_path_bases, (str)):
      self.path_base = _path_bases
    elif isinstance(_path_bases, (list, tuple)):
      _path_bases = _path_bases * 2
      self.path_base = _path_bases[1] if self.is_windows else _path_bases[0]
    elif isinstance(_path_bases, (dict)):
      # ToDo: first linux, then windows
      self.path_base = self.set_directories(path_bases=_path_bases.values())

  def __call__(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    return self

  def __str__(self):
    return "@ToDo: implement str magic."

  def preprocess_output(self, *args, **kwargs):
    """
      @ToDo: Test and QA
    """
    _value = args[0] if len(args) > 0 else kwargs.get("value")
    _callback = args[1] if len(args) > 1 else kwargs.get("callback")
    if _callback and _value:
      return _callback(_value)

    return _value

  def set_system_type(self, *args, **kwargs):
    self.is_windows = False
    self.is_linux = False
    self.OS = OS
    if self.OS.name == "nt":
      self.is_windows = True
    else:
      self.is_linux = True

  def require_from(self, *args, **kwargs):
    """
    @extends require
    To import from a given path by adding the path to the system

    @params
    0|path:
    1|module:
    """

    _module_path = args[0] if len(args) > 0 else kwargs.get("module_path", "")
    self.require("sys", "SYSTEM")
    self.SYSTEM.path.append(_module_path)
    args = args[1:]
    self.require(*args, **kwargs)
    return self

  def require_many(self, *args, **kwargs):
    """
    @extends require
    for multiple imports in single call

    @params
    0|modules: array of tuples|list

    @return
    list containing success status (True|False) of the provided list

    """
    _modules = args[0] if len(args) > 0 else kwargs.get("modules", [])

    self._enabled_modules = []
    for _rm in _modules:
      _res = False
      if len(_rm) > 0 and isinstance(_rm, (tuple, list)):
        _res = self.require(*_rm, **kwargs)
      self._enabled_modules.append(_res)

    return all(self._enabled_modules)

  def require(self, *args, **kwargs):
    """"
      Help providing module through the utility.

      @usage
      require(module_name, provide_as, alternate_if_not_available)

      @params
      0|module (str):
      1|as (str|None):
      2|alternate (str|None):

      @return
      True: if module/alternate is imported
      False: If no module could be imported
    """
    _module = args[0] if len(args) > 0 else kwargs.get("module")
    _as = args[1] if len(args) > 1 else kwargs.get("as")
    _alternate = args[2] if len(args) > 2 else kwargs.get("alternate", False)

    if _as is None:
      _as = _module

    if hasattr(self, _as) and getattr(self, _as, None) is not None:
      return True

    _module_instance = None
    try:
      __i = MODULE_IMPORTER.import_module(_module)
      # self.log_info(f"Imported {_module}")
      _module_instance = __i
    except:
      # self.log_error(f"`{_module} as {_as}` could not be imported.")
      try:
        if _alternate and isinstance(_alternate, (str)):
          # self.log_warning(f"{_module} could not be imported. Trying to import {_alternate}.")
          __i = MODULE_IMPORTER.import_module(_alternate)
          _module_instance = __i
      except:
        _error_message = f"{_module} as {_as} or its alternate {_alternate} could not be imported."
        print(_error_message)
        # self.log_error(_error_message)

    if _module_instance is None:
      return False

    # To understand most imported modules
    self._imported_modules.append((_as, ))
    setattr(self, _as, _module_instance)
    return True
