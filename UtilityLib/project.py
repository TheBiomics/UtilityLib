from .utility import UtilityManager
import copy as COPY_Mod

class ObjDict(dict):
  def __init__(__self, *args, **kwargs):
    object.__setattr__(__self, "__parent", kwargs.pop("__parent", None))
    object.__setattr__(__self, "__key", kwargs.pop("__key", None))
    object.__setattr__(__self, "__frozen", False)
    for arg in args:
      if not arg:
        continue
      elif isinstance(arg, dict):
        for key, val in arg.items():
          __self[key] = __self._hook(val)
      elif isinstance(arg, tuple) and (not isinstance(arg[0], tuple)):
        __self[arg[0]] = __self._hook(arg[1])
      else:
        for key, val in iter(arg):
          __self[key] = __self._hook(val)

    for key, val in kwargs.items():
      __self[key] = __self._hook(val)

  def __setattr__(self, name, value):
    if hasattr(self.__class__, name):
      raise AttributeError(
        "'ObjDict' object attribute " "'{0}' is read-only".format(name)
      )
    else:
      self[name] = value

  def __setitem__(self, name, value):
    isFrozen = hasattr(self, "__frozen") and object.__getattribute__(
      self, "__frozen"
    )
    if isFrozen and name not in super(ObjDict, self).keys():
      raise KeyError(name)
    super(ObjDict, self).__setitem__(name, value)
    try:
      p = object.__getattribute__(self, "__parent")
      key = object.__getattribute__(self, "__key")
    except AttributeError:
      p = None
      key = None
    if p is not None:
      p[key] = self
      object.__delattr__(self, "__parent")
      object.__delattr__(self, "__key")

  def __add__(self, other):
    if not self.keys():
      return other
    else:
      self_type = type(self).__name__
      other_type = type(other).__name__
      msg = "unsupported operand type(s) for +: '{}' and '{}'"
      raise TypeError(msg.format(self_type, other_type))

  @classmethod
  def _hook(cls, item):
    if isinstance(item, dict):
      return cls(item)
    elif isinstance(item, (list, tuple)):
      return type(item)(cls._hook(elem) for elem in item)
    return item

  def __getattr__(self, item):
    return self.__getitem__(item)

  def __missing__(self, name):
    if object.__getattribute__(self, "__frozen"):
      raise KeyError(name)
    return self.__class__(__parent=self, __key=name)

  def __delattr__(self, name):
    del self[name]

  def to_dict(self):
    base = {}
    for key, value in self.items():
      if isinstance(value, type(self)):
        base[key] = value.to_dict()
      elif isinstance(value, (list, tuple)):
        base[key] = type(value)(
          item.to_dict() if isinstance(item, type(self)) else item
          for item in value
        )
      else:
        base[key] = value
    return base

  def copy(self):
    return COPY_Mod.copy(self)

  def deepcopy(self):
    return COPY_Mod.deepcopy(self)

  def __deepcopy__(self, memo):
    other = self.__class__()
    memo[id(self)] = other
    for key, value in self.items():
      other[COPY_Mod.deepcopy(key, memo)] = COPY_Mod.deepcopy(value, memo)
    return other

  def update(self, *args, **kwargs):
    other = {}
    if args:
      if len(args) > 1:
        raise TypeError()
      other.update(args[0])
    other.update(kwargs)
    for k, v in other.items():
      if (
        (k not in self)
        or (not isinstance(self[k], dict))
        or (not isinstance(v, dict))
      ):
        self[k] = v
      else:
        self[k].update(v)

  def __getnewargs__(self):
    return tuple(self.items())

  def __getstate__(self):
    return self

  def __setstate__(self, state):
    self.update(state)

  def __or__(self, other):
    if not isinstance(other, (ObjDict, dict)):
      return NotImplemented
    new = ObjDict(self)
    new.update(other)
    return new

  def __ror__(self, other):
    if not isinstance(other, (ObjDict, dict)):
      return NotImplemented
    new = ObjDict(other)
    new.update(self)
    return new

  def __ior__(self, other):
    self.update(other)
    return self

  def setdefault(self, key, default=None):
    if key in self:
      return self[key]
    else:
      self[key] = default
      return default

  def freeze(self, shouldFreeze=True):
    object.__setattr__(self, "__frozen", shouldFreeze)
    for key, val in self.items():
      if isinstance(val, ObjDict):
        val.freeze(shouldFreeze)

  def unfreeze(self):
    self.freeze(False)

# Backward compatibility
Dict = ObjDict
DotDict = ObjDict

class ProjectManager(UtilityManager):
  name = "project"
  version = 1
  subversion = 20240400
  path_config = None

  def __init__(self, *args, **kwargs):
    self.__defaults = {"debug": False, "config_key": "config"}
    self.__defaults.update(kwargs)
    super(ProjectManager, self).__init__(**self.__defaults)
    self.set_project_paths()
    self.load_config()

  def write_toml(self, *args, **kwargs):
    """Write configuration in readable format"""
    # import toml
    # _config = toml.dumps(self.config)

  def set_project_paths(self, *args, **kwargs):
    if not getattr(self, 'path_base'):
      self.path_base = self.OS.getcwd()

    _path_bases = args[0] if len(args) > 0 else kwargs.get("path_bases", self.path_base)

    # Consider first path for Linux and second path for Windows
    if isinstance(_path_bases, (str)):
      self.path_base = _path_bases
    elif isinstance(_path_bases, (list, tuple)):
      _path_bases = _path_bases * 2
      self.path_base = _path_bases[1] if self.is_windows else _path_bases[0]
    elif isinstance(_path_bases, (dict)):
      # Consider that order of the dict is preserved
      self.path_base = self.set_project_paths(path_bases=_path_bases.values())

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
    return f"{self.path_base.rstrip('/')}/{_relative_path.lstrip('/')}"

  def get_join(self, *args, **kwargs):
    _key = args[0] if len(args) > 0 else kwargs.get("key", None)
    _val = args[1] if len(args) > 1 else kwargs.get("val", None)
    _glue = args[2] if len(args) > 2 else kwargs.get("glue", "/")
    _def_prepend = args[3] if len(args) > 3 else kwargs.get("default", "")

    if not _key is None:
      _static_config = getattr(self, self.config_key)
      _def_prepend = _static_config.get(_key, "")

    return f"{_glue}".join([_def_prepend, _val])

  def get_file(self, *args, **kwargs):
    ...

  def get_dir(self, *args, **kwargs):
    ...
