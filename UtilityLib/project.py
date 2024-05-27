from .utility import UtilityManager
from .lib import ObjDict
from .lib import EntityPath

class ProjectManager(UtilityManager):
  name = "project"
  version = 1
  subversion = 20240400
  path_config = None

  def __init__(self, *args, **kwargs):
    self.__defaults = {"config_key": "config"}
    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)
    self._set_base_path()
    self.load_config()

  def write_toml(self, *args, **kwargs):
    """Write configuration in readable format"""
    # import toml
    # _config = toml.dumps(self.config)

  def _set_base_path(self, *args, **kwargs):
    if getattr(self, 'path_base'):
      # It's set
      ...
    elif hasattr(self, 'path_bases'):
      self.set_project_paths(path_bases=getattr(self, 'path_bases'))
    else:
      self.path_base = EntityPath(self.OS.getcwd())

  def set_project_paths(self, *args, **kwargs):
    _path_bases = args[0] if len(args) > 0 else kwargs.get("path_bases", self.path_base)
    # Consider first path for Linux and second path for Windows
    if isinstance(_path_bases, (str)):
      self.path_base = EntityPath(_path_bases)
    elif isinstance(_path_bases, (list, tuple)):
      _path_bases = _path_bases * 2
      self.path_base = EntityPath(_path_bases[1] if self.is_windows else _path_bases[0])
    elif isinstance(_path_bases, (dict)):
      # Consider that order of the dict is preserved
      self.path_base = EntityPath(self.set_project_paths(path_bases=_path_bases.values()))

  def set_config_path(self, *args, **kwargs):
    self.update_attributes(self, kwargs, self.__defaults)
    self.path_config = (
      f"{self.path_base}/{self.name}.v{self.version}.{self.subversion}.config.gz"
    )

  def rebuild_config(self, *args, **kwargs):
    """Read config again"""
    setattr(self, self.config_key, self.ConfigManager(getattr(self, self.config_key, ObjDict())))

  def reset_config(self, *args, **kwargs):
    self.update_attributes(self, kwargs, self.__defaults)
    return self.load_config(**kwargs)

  def load_config(self, *args, **kwargs):
    if not getattr(self, 'path_config'):
      self.set_config_path()

    self.ConfigManager = ObjDict
    setattr(self, self.config_key, self.ConfigManager())
    if self.check_path(self.path_config):
      setattr(self, self.config_key, self.unpickle(self.path_config))

    self.rebuild_config()

  def save_config(self, *args, **kwargs):
    return self.update_config(*args, **kwargs)

  def update_config(self, *args, **kwargs):
    self.update_attributes(self, kwargs, self.__defaults)
    self.set_config_path()
    self.rebuild_config()

    _config = getattr(self, self.config_key, ObjDict())
    _config.last_updated = self.time_stamp()
    self.pickle(self.path_config, _config)

  def get_path(self, *args, **kwargs):
    _relative_path = args[0] if len(args) > 0 else kwargs.get("path", "")
    _fp = str(_relative_path).lstrip('/')
    if not self.path_base is None:
      _fp = self.path_base / _fp
    return _fp

  def get_join(self, *args, **kwargs):
    _key = args[0] if len(args) > 0 else kwargs.get("key", None)
    _val = args[1] if len(args) > 1 else kwargs.get("val", None)
    _glue = args[2] if len(args) > 2 else kwargs.get("glue", "/")
    _def_prepend = args[3] if len(args) > 3 else kwargs.get("default", "")

    if not _key is None:
      _static_config = getattr(self, self.config_key)
      _def_prepend = _static_config.get(_key, "")

    return f"{_glue}".join([_def_prepend, _val])

  def _apply_method_to_file(self, file_ref, operation, *args, **kwargs):
    """All operations are not op_file compatible due to variable number of arguments

      @params
      file_ref
      op
      *args: Passed to the method
      **kwargs: Passed on to the method

    """

    file_ref = kwargs.pop('file_ref', None) or file_ref
    operation = kwargs.pop('op', None) or operation

    _file_path = self.get_path(file_ref)
    _op = getattr(self, operation)

    return _op(_file_path, *args, **kwargs)

  file_op = _apply_method_to_file
  file_operation = _apply_method_to_file
  func_on_file = _apply_method_to_file
  file_func = _apply_method_to_file
  op_file = _apply_method_to_file

  def get_file(self, *args, **kwargs):
    ...

  def get_dir(self, *args, **kwargs):
    ...
