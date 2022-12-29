from .TimeUtility import TimeUtility

class DataUtility(TimeUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    super(DataUtility, self).__init__(**self.__defaults)

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
    _escape = args[1] if len(args) > 1 else kwargs.get("escape", False)

    if self.require("re", "REGEX"):
      _pattern = self.REGEX.escape(_pattern) if _escape else _pattern
      _ignore_case = [self.REGEX.I] if _ignore_case else []
      return self.REGEX.compile(_pattern, *_ignore_case)
    else:
      return None

  @staticmethod
  def filter(*args, **kwargs):
    """
      @status: WIP

      @method
      Recursively filter

      @params
      0|data: List/Tuple/Set/Dict(values)/str
      1|what: What char to strip
    """
    _data = args[0] if len(args) > 0 else kwargs.get("data")
    _what = args[1] if len(args) > 1 else kwargs.get("what")
    _result = []
    if isinstance(_data, (str)):
      ...
    elif isinstance(_data, (list, tuple, set)):
      # Filter for a key word
      for _i in _data:
        if _what in _i:
          _result.append(_i)
    elif isinstance(_data, (dict)):
      for _key, _value in _data:
        ...
    return _result

  @staticmethod
  def strip(*args, **kwargs):
    """
      @method
      Recursively strips string in a array

      @params
      0|data: List/Tuple/Set/Dict(values)/str
      1|char: What char to strip
    """
    _data = args[0] if len(args) > 0 else kwargs.get("data")
    _char = args[1] if len(args) > 1 else kwargs.get("char")

    if isinstance(_data, (str)):
      _data = _data.strip(_char) if _char and len(_char) > 0 else _data.strip()
    elif isinstance(_data, (list, tuple, set)):
      _data = [DataUtility.strip(_t, _char) for _t in _data]
    elif isinstance(_data, (dict)):
      for _key, _value in _data:
        _data[_key] = DataUtility.strip(_value, _char)

    return _data

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

  def slice(self, *args, **kwargs):
    """
    @function (similar to chunks)
    generator method to yield list values in chunks

    @arguments
    0|obj: DF, str, dict, obj or tuple
    1|size: chunk size to yield

    """
    _obj = args[0] if len(args) > 0 else kwargs.get("obj")

    from itertools import islice
    return islice(_obj, *args[1:])

  def chunks(self, *args, **kwargs):
    """
    @function
    generator method to yield list values in chunks

    @arguments
    0|obj: DF, str, dict, obj or tuple
    1|size: chunk size to yield

    """
    _obj = args[0] if len(args) > 0 else kwargs.get("obj")
    _size = args[1] if len(args) > 1 else kwargs.get("size", 10)
    for _n in range(0, len(_obj), _size):
      yield _obj[_n:_n+_size]

  @staticmethod
  def flatten(_nested, _level=99, _level_processed=0):
    """
      Flattens deep nested list/tuple of list/tuple
    """
    _collector = []
    if isinstance(_nested, (list, tuple, set)):
      for _item in _nested:
        _level_processed += 1
        if _level > _level_processed and isinstance(_item, (list, tuple, set)):
          _collector.extend(DataUtility.flatten(_item, _level, _level_processed)) # >v3
        else:
          _collector.append(_item)
    else:
      _collector = _nested
    return _collector

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


  def common_substrings(self, *args, **kwargs):
    """
      Returns all common substrings in two given strings

      @params
      0|text1
      1|text2
      2|min_len
      @return
      list

    """
    _text1 = args[0] if len(args) > 0 else kwargs.get("text1")
    _text2 = args[1] if len(args) > 1 else kwargs.get("text2")
    _min_len = args[2] if len(args) > 2 else kwargs.get("min_len", 1)

    # DiffMatcher not working as expected
    # from difflib import SequenceMatcher
    # _seq_match = SequenceMatcher(None, _text1, _text2)
    # _match_blocks = _seq_match.get_matching_blocks()
    # _results = [_text1[_b.a: _b.a + _b.size] for _b in _match_blocks if _b.size >= _min_len]

    from itertools import combinations

    _t1_combs = [_text1[x:y] for x, y in combinations(range(len(_text1) + 1), r=2)]
    _t2_combs = [_text2[x:y] for x, y in combinations(range(len(_text2) + 1), r=2)]

    _count_2 = [(_c, _s) for _c, _s in zip(_t2_combs, [_text1.count(_t) for _t in _t2_combs]) if _s > 0 and len(_c) > _min_len]
    _count_1 = [(_c, _s) for _c, _s in zip(_t1_combs, [_text2.count(_t) for _t in _t1_combs]) if _s > 0 and len(_c) > _min_len]

    self.common_substrings__values = _count_1 + _count_2

    return [_ss for _ss, _c in _count_2 + _count_1]

  def common_substring(self, *args, **kwargs):
    """
      returns largest common substring from CLASS.common_substrings

      @params
      0|text1
      1|text2
      2|min_len

    """
    _results = self.common_substrings(*args, **kwargs)
    _result = max(_results, key=len) if len(_results) > 0 else ""
    return _result

  def clean_key(self, *args, **kwargs):
    """
      Cleans a string to be used a key

      @params
      0|text:
      1|keep:

      @ToDo:
      - Remove special characts
      - remove bracket content flag
      - preserve or replace space with dash or underscore???

    """
    _text = args[0] if len(args) > 0 else kwargs.get("text", "")
    _keep = args[1] if len(args) > 1 else kwargs.get("keep", " ")

    # Compile or get the existing object
    self.re_underscore = self.re_underscore if hasattr(self, "re_underscore") else self.re_compile("_")
    self.re_bracket = self.re_bracket if hasattr(self, "re_bracket") else self.re_compile("\(.*?\)|\[.*?\]")
    self.re_space = self.re_space if hasattr(self, "re_space") else self.re_compile("\s+")

    # _text = _text.lower()
    _text = self.re_bracket.sub(" ", _text)
    _text = self.re_underscore.sub(" ", _text)
    _text = self.re_space.sub(" ", _text.strip())
    return _text

  def text_to_slug(self, *args, **kwargs):
    _text = args[0] if len(args) > 0 else kwargs.get("text")
    _keep = args[1] if len(args) > 1 else kwargs.get("keep", ["-"])
    _replace_with = args[1] if len(args) > 1 else kwargs.get("replace_with", "-")
    _replacements = args[2] if len(args) > 2 else kwargs.get("keep", ["-"])

    if isinstance(_text, (str)):
      _text = "".join([_c if _c.isalnum() or _c in _keep else _replace_with for _c in _text])
      if isinstance(_replacements, (dict)):
        for _k, _v in _replacements.items():
          _text = _text.replace(_k, _v)

    return _text
