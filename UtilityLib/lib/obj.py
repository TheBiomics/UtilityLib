import copy as COPY_Mod

class ObjDict(dict):
  def __init__(self, *args, **kwargs):
    object.__setattr__(self, "__parent", kwargs.pop("__parent", None))
    object.__setattr__(self, "__key", kwargs.pop("__key", None))
    object.__setattr__(self, "__frozen", False)

    for arg in args:
      if not arg:
        continue
      elif isinstance(arg, dict):
        for key, val in arg.items():
          self[key] = self._hook(val)
      elif isinstance(arg, tuple) and (not isinstance(arg[0], tuple)):
        self[arg[0]] = self._hook(arg[1])
      else:
        for key, val in iter(arg):
          self[key] = self._hook(val)

    for key, val in kwargs.items():
      self[key] = self._hook(val)

  def __setattr__(self, name, value):
    if hasattr(self.__class__, name):
      raise AttributeError(f"'ObjDict' object attribute '{name}' is read-only.")
    else:
      self[name] = value

  def __setitem__(self, name, value):
    try:
      _is_frozen = hasattr(self, "__frozen") and object.__getattribute__(self, "__frozen")
    except Exception as _e:
      _is_frozen = False

    if _is_frozen and name not in super().keys():
      raise KeyError(name)

    super().__setitem__(name, value)

    try:
      _p = object.__getattribute__(self, "__parent")
      _key = object.__getattribute__(self, "__key")
    except AttributeError:
      _p = None
      _key = None

    if _p is not None:
      _p[_key] = self
      object.__delattr__(self, "__parent")
      object.__delattr__(self, "__key")

  @property
  def _keys(self):
    """Return keys excluding those starting with an underscore.
    dict.keys avoids recursion as the class creates keys while iterating in case key is missing.
    """
    return [_k for _k in dict.keys(self) if not _k.startswith('_')]

  def __iter__(self):
    """Iterate over keys, excluding private ones."""
    return iter(self._keys)

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

  def __getattr__(self, key):
    if key not in self:
      self[key] = ObjDict()
    return self[key]

  def __getitem__(self, key):
    if key not in self:
      self[key] = ObjDict()
    return super().__getitem__(key)

  def __missing__(self, name):
    try:
      _is_frozen = hasattr(self, "__frozen") and object.__getattribute__(self, "__frozen")
    except Exception as _e:
      _is_frozen = False

    # if _is_frozen:
    if object.__getattribute__(self, "__frozen"):
      raise KeyError(name)

    return self.__class__(__parent=self, __key=name)

  def __delattr__(self, name):
    del self[name]

  def __eq__(self, other):
    """Compare with another dict or ObjDict, ignoring private keys."""
    if not isinstance(other, (dict, ObjDict)):
      return False
    return dict(self.items()) == dict(other.items() if hasattr(other, 'items') else other)

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
    _other = {}
    if args:
      if len(args) > 1:
        raise TypeError()
      _other.update(args[0])
    _other.update(kwargs)
    for _k, _v in _other.items():
      if (
        (_k not in self)
        or (not isinstance(self[_k], dict))
        or (not isinstance(_v, dict))
      ):
        self[_k] = _v
      else:
        self[_k].update(_v)

  def __getnewargs__(self):
    return tuple(self.items())

  def __getstate__(self):
    return self.__dict__.copy()

  def __setstate__(self, state):
    self.update(state)

  def __or__(self, other):
    if not isinstance(other, (ObjDict, dict)):
      return NotImplemented
    _new = ObjDict(self)
    _new.update(other)
    return _new

  __and__ = __or__
  __ror__ = __or__
  __ior__ = __or__

  def setdefault(self, key, default=None):
    if key in self:
      return self[key]

    self[key] = default
    return default

  def freeze(self, shouldFreeze=True):
    object.__setattr__(self, "__frozen", shouldFreeze)
    for key, val in self.items():
      if isinstance(val, ObjDict):
        val.freeze(shouldFreeze)

  def unfreeze(self):
    self.freeze(False)

  class _FrozenContext:
    def __init__(self, obj_dict):
      self.obj_dict = obj_dict
      self.was_frozen = object.__getattribute__(obj_dict, "__frozen")

    def __enter__(self):
      self.obj_dict.freeze(True)
      return self.obj_dict

    def __exit__(self, exc_type, exc_val, exc_tb):
      self.obj_dict.freeze(self.was_frozen)

  def frozen(self):
    """Context manager for temporarily freezing the ObjDict."""
    return self._FrozenContext(self)

  def items(self):
    """Return items, excluding those with keys starting with an underscore."""
    return ((_k, self.get(_k)) for _k in self._keys)

  def values(self):
    """Return values, excluding those associated with keys starting with an underscore."""
    return (self.get(_k) for _k in self._keys)

  def __repr__(self):
    """Custom representation of the dictionary, excluding private keys."""
    _item_string = ",\n".join([f"  {_k}: {_v}" for _k, _v in self.items()])
    return f"{self.__class__.__name__}(\n{_item_string}\n)"

  def flatten(self, separator='.', prefix=''):
    """Flatten nested ObjDict into a single level dict with dotted keys."""
    result = {}
    for key, value in self.items():
      new_key = f"{prefix}{separator}{key}" if prefix else key
      if isinstance(value, ObjDict):
        result.update(value.flatten(separator, new_key))
      else:
        result[new_key] = value
    return result

  def to_json(self, **kwargs):
    """Convert to JSON string."""
    import json
    return json.dumps(self.to_dict(), **kwargs)

  @classmethod
  def from_json(cls, json_str, **kwargs):
    """Create ObjDict from JSON string."""
    import json
    data = json.loads(json_str, **kwargs)
    return cls(data)

  def save_json(self, path, **kwargs):
    """Save to JSON file."""
    import json
    with open(path, 'w') as f:
      json.dump(self.to_dict(), f, **kwargs)

  @classmethod
  def load_json(cls, path, **kwargs):
    """Load from JSON file."""
    import json
    with open(path, 'r') as f:
      data = json.load(f, **kwargs)
    return cls(data)

# Backward compatibility
Dict = ObjDict
DotDict = ObjDict
