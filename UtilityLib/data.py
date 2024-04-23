from .time import TimeUtility
from functools import lru_cache as CacheMethod

class DataUtility(TimeUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)

  # DataFrame Functions
  ## Pandas
  def df_reset_columns(self, *args, **kwargs):
    """
      @return reset column multiindex additionally set group index as a column

      @params
      0|df: DataFrame
      1|key: DataFrame.groupby().key

      # Considering data is str
      # Float, int list etc are not tested or handled
    """

    _df = args[0] if len(args) > 0 else kwargs.get("df")
    _key = args[1] if len(args) > 1 else kwargs.get("key")

    _joined_cols = ["__".join(_idx) for _idx in _df.columns if isinstance(_idx, tuple)]
    _df.columns = _joined_cols if len(_joined_cols) == len(_df.columns) else _df.columns
    if _key and (not _key in _df.columns) and (not 'index' in _df.columns):
        _df = _df.reset_index()
    return _df

  def _json_file_to_df(self, *args, **kwargs):
    """JSON structure to DataFrame converter

    0|json: JSON file path (string)/object (dict)
    1|map: Dot notation of keys to parse (parsable using UL.deepkey) i.e., column to key map e.g. entity|0|metadata|header

    @return
    Pandas DataFrame object

    """
    _json = args[0] if len(args) > 0 else kwargs.get("json")
    _map = args[1] if len(args) > 1 else kwargs.get("map", None)

    if isinstance(_json, (str)):
      _json = self.read_json(_json)

    _result = []
    for _json_el in _json:
      _row = {}
      if _map and isinstance(_map, (dict)):
        # If column map is provided
        for _key, _dotkey in _map.items():
          _row[_key] = self.get_deep_key(_json_el, _dotkey)
      else:
        # If column map is not provided
        for _key, _value in _json.items():
          _row[_key] = _value

      _result.append(_row)

    return self.DF(_result)

  json_to_df = _json_file_to_df

  def pd_categorical(self, df, col_name, sort=True):
      """
      Arguments:
        0|df: pandas DataFrame
        1|col_name: Column Name
        2|sort: boolean

      Returns:
        (categorical_df, mapping)

      Example:
        _df_cat, _mapping = _PM.pd_categorical(df, 'gender', True)

      """
      df_copy = df.copy()
      if sort:
          df_copy = df_copy.sort_values(col_name)

      column_mapping = {}
      if not df_copy[col_name].dtype.name == 'category':
          df_copy[col_name] = df_copy[col_name].astype('category')
          column_mapping = dict(zip( df_copy[col_name].cat.codes, df_copy[col_name]))
          column_mapping_inverse = zip(column_mapping.values(), column_mapping.keys())
          column_mapping_inverse = dict(column_mapping_inverse)
          df_copy[col_name] = df_copy[col_name].map(column_mapping_inverse)

      column_mapping_df = self.DF({
              'key': column_mapping.keys(),
              'values': column_mapping.values(),
          })

      return (df_copy, column_mapping_df)

  def pd_excel_writer(self, *args, **kwargs):
    _excel = args[0] if len(args) > 0 else kwargs.get("excel")
    _options = args[4] if len(args) > 4 else kwargs.get("pyxl_options", dict())

    _options.update({
      "engine": kwargs.get("engine", "openpyxl"),
      "mode": kwargs.get("mode", "a"),
      "if_sheet_exists": kwargs.get("sheet_exists", "replace"),
    })

    if isinstance(_excel, (str, )): # str or path?
      self.require('pandas', 'PD')
      if not self.exists(_excel):
        del _options['mode']
        del _options['if_sheet_exists']

      return self.PD.ExcelWriter(_excel, **_options)

  def from_excel(self, *args, **kwargs):
    """
    Arguments:
      0|excel: Either openpyxl writer or path to excel
      1|sheet: Name of the sheet

    Returns:
      pandas.DataFrame

    Example:
      _PM.from_excel(<path.xlsx>, _df, 'sheet_name', **excel_options, **pyxl_options)

    """

    _excel = args[0] if len(args) > 0 else kwargs.get("excel")
    _sheet = args[1] if len(args) > 1 else kwargs.get("sheet")
    kwargs['sheet'] = _sheet

    self.require('pandas', 'PD')
    _excel = self.PD.read_excel(_excel, **kwargs)

    return _excel

  def pd_excel(self, *args, **kwargs):
    """
    Arguments:
      0|excel: Either openpyxl writer or path to excel
      1|df: Pandas DataFrame to be written
      2|sheet: Name of the sheet
      3|excel_options: Options for PD.to_excel e.g., {'index': False, 'float_format': "%.4f"}
      4|pyxl_options: Options (like engine, mode) for PD.ExcelWriter

    Returns:
      openpyxl
      openpyxl.sheets => Contains sheets
      openpyxl.books => contains books

    Example:
      _PM.pd_excel(<path.xlsx>, _df, 'sheet_name', **excel_options, **pyxl_options)

    """

    _excel_writer = args[0] if len(args) > 0 else kwargs.get("excel")
    _df = args[1] if len(args) > 1 else kwargs.get("df")
    _sheet = args[2] if len(args) > 2 else kwargs.get("sheet", 'DataFrame')
    _excel_options = args[3] if len(args) > 3 else kwargs.get("excel_options", {'index': False})

    if isinstance(_excel_writer, (str, )):
      _excel_writer = self.pd_excel_writer(_excel_writer, **kwargs)

    _df.copy().to_excel(_excel_writer, sheet_name=_sheet, **_excel_options)
    hasattr(_excel_writer, 'save') and _excel_writer.save()
    _excel_writer.close()
    _excel_writer.handles = None
    return _excel_writer

  def DF(self, *args, **kwargs):
    _data = args[0] if len(args) > 0 else kwargs.get("data")
    if self.require("pandas", "PD"):
      return self.PD.DataFrame(_data, **kwargs)

  def _csv_file_to_DF(self, *args, **kwargs):
    """Read comma separated value file and convert to Pandas DataFrame"""
    _file = args[0] if len(args) > 0 else kwargs.get("file")
    if self.require("pandas", "PD"):
      return self.PD.read_csv(_file, **kwargs)

  pd_csv = _csv_file_to_DF
  read_csv = _csv_file_to_DF

  def _tsv_file_to_DF(self, *args, **kwargs):
    """Read tab delimited value file and convert to Pandas DataFrame"""
    kwargs['sep'] = "\t"
    return self.pd_csv(*args, **kwargs)

  read_tsv = _tsv_file_to_DF
  pd_tsv = _tsv_file_to_DF

  # Helpers

  def preprocess_output(self, *args, **kwargs):
    """
      @ToDo: Test and QA
    """
    _value = args[0] if len(args) > 0 else kwargs.get("value")
    _callback = args[1] if len(args) > 1 else kwargs.get("callback")
    if _callback and _value:
      return _callback(_value)

    return _value

  def parse_digits(self, *args, **kwargs):
    """Digit parts of a given data

      @params
      0|data: String type

      # Considering data is str
      # Float, int list etc are not tested or handled
    """
    _data = args[0] if len(args) > 0 else kwargs.get("data")
    return "".join([_s for _s in str(_data) if _s.isdigit()])

  digits = parse_digits
  digit_only = parse_digits
  parseInt = parse_digits
  parse_int = parse_digits

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

  slices = chunks
  sliced = chunks

  @staticmethod
  def is_iterable(*args, **kwargs):
    """
      Checks for iterables except str

      @usage
      .flatten(list|tuple, 2)
    """
    _obj = args[0] if len(args) > 0 else kwargs.get("obj")
    return hasattr(_obj, '__iter__') and not isinstance(_obj, str)

  @staticmethod
  def flatten(_nested, _level=99, _depth=0):
    """Flattens nested iterables except str

      @usage
      .flatten(list|tuple, 2)
    """
    _collector = []
    _depth += 1
    if all([DataUtility.is_iterable(_nested), not _level <= _depth]):
      for _item in _nested:
        _val = DataUtility.flatten(_item, _level, _depth)
        _collector.extend(_val) if DataUtility.is_iterable(_val) else _collector.append(_val)
    else:
      _collector = _nested
    return _collector

  def product(self, *args, **kwargs):
    """@generator Provides combinations of the given items
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
    _position = args[1] if len(args) > 1 else kwargs.get("position", -3)
    _delimiter = args[2] if len(args) > 2 else kwargs.get("delimiter", "/")

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


  def get_deep_key(self, *args, **kwargs):
    """Get method to access nested key

      @params
      0|obj: dictionary
      1|keys: string, pipe separated string, list, tuple, set
      2|default:
      3|sep: '|'

      @example
      get_deep_key(_dict, (key, subkey, subsubkey), _default)

      @return
      matched key value or default
    """
    _obj = args[0] if len(args) > 0 else kwargs.get("obj", {})
    _keys = args[1] if len(args) > 1 else kwargs.get("keys", ())
    _default = args[2] if len(args) > 2 else kwargs.get("default")
    _sep = args[3] if len(args) > 3 else kwargs.get("sep", "|")

    _instance_list = (tuple, set, list)
    _instance_dict = (dict)
    _instance_singluar = (str, int)

    _keys = _keys if isinstance(_keys, _instance_list) else _keys.split(_sep)

    for _k in _keys:
      # hasattr(, 'get') & str|int=> _dict key, int => list, tuple, or set
      if isinstance(_obj, _instance_dict) and hasattr(_obj, 'get') and isinstance(_k, _instance_singluar):
        _obj = _obj.get(_k, _default)
      elif(isinstance(_obj, _instance_list) and (isinstance(_k, (int)) or _k.isnumeric())):
        _k = int(_k)
        if len(_obj) > _k:
          _obj = _obj[_k]

    return _obj

  dotkey_value = get_deep_key

  def clean_key(self, *args, **kwargs):
    """Cleans a string to be used a key

      @params
      0|text:
      1|keep:

      @ToDo:
      - Remove special characters
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

  def expand_ranges(self, *args, **kwargs):
    # 33-51,103-203
    _ranges = args[0] if len(args) > 0 else kwargs.get("ranges", "")
    _expanded = self.flatten(map(
        lambda _l: [*range(int(_l[0]), int(_l[1]) + 1, 1)],
        map(lambda _x: _x.split("-"), _ranges.split(","))
    ))
    return _expanded

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

  def print_csv(self, *args, **kwargs):
      _args = [str(_a) for _a in self.flatten(args)]
      _return = kwargs.get('return', False)
      _str = ",".join(_args)
      if _return:
        return _str
      print(_str)
