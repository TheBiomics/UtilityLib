from .TimeUtility import TimeUtility

class DataUtility(TimeUtility):
  def __init__(self, *args, **kwargs):
    super(DataUtility, self).__init__(**kwargs)
    self.__defaults = {}
    self.update_attributes(self, kwargs, self.__defaults)

  def digit_only(self, *args, **kwargs):
    """
      @return digit parts of a given _data

      @params
      0|data: String type

      # Considering data is str
      # Float, int list etc are not tested or handled
    """
    _data = args[0] if len(args) > 0 else kwargs.get("data")
    return "".join([_s for _s in _data if _s.isdigit()])

  def DF(self, *args, **kwargs):
    _data = args[0] if len(args) > 0 else kwargs.get("data")
    if self.require("pandas", "PD"):
      return self.PD.DataFrame(_data)

  def re_compile(self, *args, **kwargs):
    _pattern = args[0] if len(args) > 0 else kwargs.get("pattern")
    _ignore_case = args[1] if len(args) > 1 else kwargs.get("ignore_case", True)
    if self.require("re", "REGEX"):
      _ignore_case = [self.REGEX.I] if _ignore_case else []
      return self.REGEX.compile(_pattern, *_ignore_case)
    else:
      return None

  def find_all(self, *args, **kwargs):
    """
    Finds all substrings in a given string
    """
    # Pop first element to extend re_compile method
    _string = args[0] if len(args) > 0 else kwargs.get("string", "")
    args = args[1:]
    _re_compiled = self.re_compile(*args, **kwargs)

    if _re_compiled is not None:
      return _re_compiled.findall(_string)
    return None

  def chunks(self, *args, **kwargs):
    """
    @function
    generator method to yield list values in chunks

    @arguments
    0|list: list or tuple
    1|size: chunk size to yield

    """
    _list = args[0] if len(args) > 0 else kwargs.get("list")
    _size = args[1] if len(args) > 1 else kwargs.get("size", 10)
    for _n in range(0, len(_list), _size):
      yield _list[_n:_n+_size]

  @staticmethod
  def flatten(_nested, _level=9999, _level_processed=0):
    """
      Flattens deep nested list/tuple of list/tuple
    """
    for _item in _nested:
      _level_processed += 1
      if _level > _level_processed and isinstance(_item, (list, tuple)):
        yield from DataUtility.flatten(_item, _level, _level_processed) # >v3
      else:
        yield _item

  def product(self, *args, **kwargs):
    """
      @generator
      Provides combinations of the given items
      NOTE: Single string will be converted to one item list
      "AUGC" will behave like ["A", "U", ...]
      ["AUGC"] will be treated as it is

      @params
      0|items (list): Object(s) to unpack using *
      1|repeat (1|int)

      @example
      combination(["AU", "GC"], 1)
      combination(["AUGC"], 8)
      combination(["A", "U", "G", "C"], 8)

    """
    _items = args[0] if len(args) > 0 else kwargs.get("items", [])
    _repeat = args[1] if len(args) > 1 else kwargs.get("repeat", 1)

    self.require("itertools", "IT")
    return self.IT.product(*_items, repeat=_repeat)

  def combinations(self, *args, **kwargs):
    """
      @returns combinations of a list.
    """
    _items = args[0] if len(args) > 0 else kwargs.get("items", [])
    _repeat = args[1] if len(args) > 1 else kwargs.get("repeat", 1)
    self.require("itertools", "IT")
    return self.IT.combinations(_items, _repeat)

  def get_parts(self, *args, **kwargs):
    _text = args[0] if len(args) > 0 else kwargs.get("text")
    _position = args[2] if len(args) > 2 else kwargs.get("position", -3)
    _delimiter = args[3] if len(args) > 3 else kwargs.get("delimiter", "/")

    _text = _text.split(_delimiter)
    return _text[_position]
