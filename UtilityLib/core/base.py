from . import __version__, __description__, __build__, __name__
import importlib as MODULE_IMPORTER
import os as _OS
import sys as _SYSTEM
from functools import lru_cache as CacheMethod

class BaseUtility:
  __name__= __name__
  __version__= __version__
  __build__= __build__
  __description__= __description__
  name = __name__
  version = __version__
  version_info = f"{__version__}.{__build__}"

  OS = _OS
  SYS = _SYSTEM
  SYSTEM = _SYSTEM
  os_type = None
  is_windows = None
  is_linux = None
  path_base = None

  _imported_modules = []

  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    self._set_os_type(**self.__defaults)
    self.update_attributes(self, self.__defaults)

  def is_running(self, *args, **kwargs):
    _file = args[0] if len(args) > 0 else kwargs.get("file", "UtilityLib-Processes-v2.txt")
    _dir = args[1] if len(args) > 1 else kwargs.get("dir", 'Documents/PyProcessConfig')

    _path_user_settings = self.OS.path.join(self.OS.path.expanduser('~'), _dir)
    _path_file_pid = f"{_path_user_settings}/{_file}"

    if not self.OS.path.exists(_path_user_settings):
      self.OS.makedirs(_path_user_settings)

    _current_pid = self.OS.getpid()

    # Import psutil
    from psutil import pid_exists, Process

    if self.OS.path.exists(_path_file_pid):
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

  def _setattrs(self, kw):
    """set multiple attributes from dict"""

    [setattr(self, _k, kw[_k]) for _k in kw.keys()]

  set_attributes = _setattrs
  setattrs = _setattrs

  def update_attributes(self, obj=None, kw: dict={}, defaults: dict={}):
    """Sets and updates object attributes from dict
    """
    if obj is None:
      obj = self

    [setattr(obj, _k, defaults[_k]) for _k in defaults.keys() if not hasattr(obj, _k)]
    [setattr(obj, _k, kw[_k]) for _k in kw.keys()]

  def __call__(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    return self

  def __repr__(self):
    return f"{self.name}: Use help() function to see the list of all methods."

  __str__ = __repr__

  def _set_os_type(self, *args, **kwargs):
    if self.OS.name == "nt":
      self.is_windows = True
      self.is_linux = False
      self.os_type = 'windows'
    else:
      self.is_linux = True
      self.is_windows = False
      self.os_type = 'linux'

  set_system_type = _set_os_type

  def _import_module_from(self, *args, **kwargs):
    """Executes "from Package import Module"

    @coverage
    from PIL import Image as PImage <=> import PIL.Image as PImage
    from pathlib import Path as PATH <=> import pathlib; PATH = getattr(pathlib, 'Path')

    @params
    0|package:
    1|module:
    2|as:
    """

    _package = args[0] if len(args) > 0 else kwargs.get("package")
    _module = args[1] if len(args) > 1 else kwargs.get("module")
    _as = args[2] if len(args) > 2 else kwargs.get("as")

    _module_instance = None

    if not _package:
      return None

    try:
      _pkg = MODULE_IMPORTER.import_module(_package)
      if hasattr(_pkg, _module):
        _module_instance = getattr(_pkg, _module)
      else:
        _import_stmt = f"{_package}.{_module}" # "import PIL.Image <=> from PIL import Image"
        _module_instance = MODULE_IMPORTER.import_module(_import_stmt)

    except:
      ...

    if not _module_instance:
      return False

    self._imported_modules.append((_as, ))
    setattr(self, _as, _module_instance)
    return True

  require_from = _import_module_from
  module_from = _import_module_from
  import_from = _import_module_from
  from_import = _import_module_from

  def require_path(self, *args, **kwargs):
    """Imports a module through a path by adding the module path to system path

    @extends require
    To import from a given path by adding the path to the system

    @params
    0|module_path:
    1|module:
    """
    _module_path = args.pop(0) if len(args) > 0 else kwargs.get("module_path", "")
    self.require("sys", "SYSTEM")
    self.SYSTEM.path.append(_module_path)
    self.require(*args, **kwargs)
    return self

  def _import_multiple_modules(self, *args, **kwargs):
    """@extends require
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
        _res = self._import_single_module(*_rm, **kwargs)
      self._enabled_modules.append(_res)

    return all(self._enabled_modules)

  import_many = _import_multiple_modules
  require_many = _import_multiple_modules

  @CacheMethod(maxsize=None)
  def _import_single_module(self, *args, **kwargs):
    """"Import module in the run time from the utility.

      @usage
      require(module_name, import_as, alternate_if_not_available)

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

    self.set_logging()

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

  import_module = _import_single_module
  require = _import_single_module
