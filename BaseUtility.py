import importlib as MODULE_IMPORTER
import os as OS

class BaseUtility:
  def __init__(self, *args, **kwargs):
    self.__defaults = {
      "imported_module_list": [],
    }
    self.set_system_type(**kwargs)
    self.update_attributes(self, kwargs, self.__defaults)

  def update_attributes(self, object=None, kw=dict(), defaults=dict()):
    """
      Sets attribute (dict) values and defaults
    """
    if object is not None:
      [setattr(object, _k, defaults[_k]) for _k in defaults.keys() if not hasattr(object, _k)]
      [setattr(object, _k, kw[_k]) for _k in kw.keys()]

  def set_system_type(self, *args, **kwargs):
    self.is_windows = False
    self.is_linux = False
    if OS.name == "nt":
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

    _module_path = args[0] if len(args) > 0 else kwargs.get("module_path", [])
    args = args[1:]
    self.require("sys", "SYSTEM")
    self.SYSTEM.path.append(_module_path)
    # the mock-0.3.1 dir contains testcase.py, testutils.py & mock.py
    self.SYSTEM.path.append(_module_path)
    self.require(*args, **kwargs)

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

    _results = []
    for _rm in _modules:
      _res = False
      if len(_rm) > 0 and isinstance(_rm, (tuple, list)):
        _res = self.require(*_rm, **kwargs)
      _results.append(_res)

    return _results

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
    setattr(self, _as, _module_instance)
    return True
