from warnings import warn as WARN
from .log import LoggingUtility

class FileSystemUtility(LoggingUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)
    self.require('shutil', 'SHUTIL')
    self.require('json', 'JSON')

  def backup(self, *args, **kwargs):
    _file = args[0] if len(args) > 0 else kwargs.get("file")
    _ext = self.ext(_file)
    _copy_name = self.change_ext(self.time_stamp() + f".{_ext}")
    return self.copy(_file, _copy_name)

  def rename(self, *args, **kwargs):
    _old_name = args[0] if len(args) > 0 else kwargs.get("from")
    _new_name = args[1] if len(args) > 1 else kwargs.get("to")
    return self.OS.rename(_old_name, _new_name)

  def compress_gz(self, *args, **kwargs):
    """Compress a file to gz

    @params
    0|path_file
    1|flag_move (False): Deletes the original file

    """
    self.path_file = args[0] if len(args) > 0 else kwargs.get("path_file")
    self.flag_move = args[1] if len(args) > 1 else kwargs.get("flag_move", False)
    self.require("gzip", "GZip")
    with open(self.path_file, 'rb') as _f_in, self.GZip.open(f"{self.path_file}.gz", 'wb') as _f_out:
      _f_out.writelines(_f_in)

    if self.flag_move == True:
      # delete file to simulate moving a file to gz compression
      self.delete_path(self.path_file)

  to_gz = compress_gz
  gz = compress_gz
  gzip = compress_gz
  compress_to_gzip = compress_gz

  def add_tgz_files(self, *args, **kwargs):
    """
      Adds files to tarball with gz compression
      Note: Directory architecture is not maintained for now.
    """
    self.update_attributes(self, kwargs)
    self.path_tgz = args[0] if len(args) > 0 else kwargs.get("path_tgz")
    _file_paths = args[1] if len(args) > 1 else kwargs.get("files_path", [])
    _mode = args[2] if len(args) > 2 else kwargs.get("mode", "w:gz")

    if isinstance(_file_paths, (str)):
      _file_paths = [_file_paths]

    if isinstance(_file_paths, (list, tuple, set)):
      _file_paths = {self.file_name(_f, with_ext=True): _f for _f in _file_paths if self.check_path(_f)}

    if isinstance(_file_paths, (dict)):
      self.require("tarfile", "TarFileManager")
      _tar = self.TarFileManager.open(self.path_tgz, _mode)
      # @TODO Same file name in different path will be overridden
      for _name, _path in _file_paths.items():
        if self.check_path(_path):
          _tar.add(_path, arcname=_name)

      _tar.close()

  def list_tgz_items(self, *args, **kwargs):
    """

    @bug: Doesn't renew file in loop due to path_tgz
    Workaround to assign path_tgz at the beginning of every loop.

    """
    self.update_attributes(self, kwargs)
    if not hasattr(self, "path_tgz"):
      self.path_tgz = args[0] if len(args) > 0 else kwargs.get("path_tgz")

    _info_type = args[1] if len(args) > 1 else kwargs.get("info_type", "names") # names|info
    _flag_filter = args[2] if len(args) > 2 else kwargs.get("flag_filter", False)

    self.require("tarfile", "TarFileManager")
    self.tgz_obj = self.TarFileManager.open(self.path_tgz, "r:gz") # File is left open

    if _info_type == "names" and _flag_filter == False:
      self.tgz_items = self.tgz_obj.getnames()
    else:
      self.tgz_items = self.tgz_obj.getmembers()
    return self.tgz_items

  def list_tgz_files(self, *args, **kwargs):
    _info_type = args[1] if len(args) > 1 else kwargs.get("info_type", "names")
    kwargs.update({"flag_filter": True})
    self.list_tgz_items(*args, **kwargs)
    self.tgz_files = [_f if not "names" in _info_type else _f.name for _f in self.tgz_items if _f.isfile()]
    return self.tgz_files

  def read_tgz_file(self, *args, **kwargs):
    if not hasattr(self, "tgz_files") or not hasattr(self, "tgz_obj"):
      self.list_tgz_files(*args, **kwargs)
    _filename = args[3] if len(args) > 3 else kwargs.get("filename")
    _encoding = args[4] if len(args) > 4 else kwargs.get("encoding", "utf-8")

    _file_content = None
    if _filename in self.tgz_files:
      _file = self.tgz_obj.extractfile(_filename)
      _file_content = _file.read()
      try:
        _file_content = _file_content.decode()
      except:
        # Don't raise error for image/media file types ["png", "jpg", "htaccess", "gif", "woff2", "ttf", "mp4"]
        if self.ext(_filename) in ["png", "jpg", "htaccess", "gif", "woff2", "ttf", "mp4"]:
          self.log_warning(f"Cannot decode a media file with extension {self.ext(_filename)}.")
        else:
          self.log_error(f"Could not decode the content from file with extension {self.ext(_filename)} returning {type(_file_content)}.")

    return _file_content

  def read_gz_file(self, *args, **kwargs):
    """
      Reads gzipped files only (not tar.gz, tgz or a compressed file) line by line (fasta, txt, jsonl, csv, and tsv etc...)
      Can advance the counter to skip set of lines
    """
    _default_args = {
      "skip_rows": 0,
      "row_size": 100,
    }
    _default_args.update(kwargs)
    self.update_attributes(self, _default_args)

    _file = args[0] if len(args) > 0 else kwargs.get("file")
    _processor_line = args[1] if len(args) > 1 else kwargs.get("processor_line")
    self.count_lines = self.count_lines if hasattr(self, "count_lines") else self.skip_rows

    self.require("gzip", "GZip")
    _result = True
    with self.GZip.open(_file, 'rt') as _fh:
      if not self.row_size:
        _result = _fh.readlines()
      else:
        self.require('itertools', "IterTools")
        for _line in self.IterTools.islice(_fh, self.skip_rows, self.skip_rows + self.row_size):
          # _fh.buffer.fileobj.tell() # https://stackoverflow.com/a/62589283/16963281
          self.count_lines = self.count_lines + 1
          yield _processor_line(_line) if _processor_line else _line

    return _result

  def extract_zip(self, *args, **kwargs):
    _source = args[0] if len(args) > 0 else kwargs.get("source")
    _destination = args[1] if len(args) > 1 else kwargs.get("destination")

    self.validate_dir(_destination)

    if self.check_path(_source):
      self.SHUTIL.unpack_archive(_source, _destination)
      self.log_info(f"Extracted {_source} content in {_destination}.")
      return True

      # Extracts ZIP Files Only
      # with ZipFile(str(_source), 'r') as zipObj:
      #   zipObj.extractall(des_dir)

    return self.check_path(_destination)

  def list_zip_items(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    self.path_zip = args[0] if len(args) > 0 else kwargs.get("path_zip", getattr(self, "path_zip"))

    _info_type = args[1] if len(args) > 1 else kwargs.get("info_type", "info") # names|info
    _flag_filter = args[2] if len(args) > 2 else kwargs.get("flag_filter", False)

    self.require("zipfile", "ZipHandler")

    self.zip_obj = self.ZipHandler.ZipFile(self.path_zip)
    if _info_type == "names" and _flag_filter == False:
      self.zip_items = self.zip_obj.namelist()
    else:
      self.zip_items = self.zip_obj.infolist()

    return self.zip_items

  def list_zip_files(self, *args, **kwargs):
    _info_type = args[1] if len(args) > 1 else kwargs.get("info_type", "info")
    kwargs.update({"flag_filter": True})
    self.list_zip_items(*args, **kwargs)
    self.zip_files = [_f if not "names" in _info_type else _f.filename for _f in self.zip_items if not _f.is_dir()]
    return self.zip_files

  def read_zipfile(self, *args, **kwargs):
    if not hasattr(self, "zip_files") or not hasattr(self, "zip_obj"):
      self.list_zip_files(*args, **kwargs)
    _filename = args[3] if len(args) > 3 else kwargs.get("filename", "utf-8")
    _encoding = args[4] if len(args) > 4 else kwargs.get("encoding", "utf-8")

    # Count Lines: https://stackoverflow.com/a/9631635/6213452

    if not self.path_zip or not _filename:
      return None

    # self.require('io', 'IO')

    _content = None
    if _filename in self.zip_files:
      _content = self.zip_obj.read(_filename)
      try:
        _content = _content.decode()
      except:
        self.log_error("Could not decode the content, returning as it is.")
        pass
      # with self.zip_obj.open(_filename) as _zipfile:
      #   for _line in self.IO.TextIOWrapper(_zipfile, _encoding):
      #     yield _line.strip("\n")
    return _content

  def parse_jsonl_gz(self, *args, **kwargs):
    kwargs.update({"processor_line": self.JSON.loads})
    return self.read_gz_file(*args, **kwargs)

  def parse_latex(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    _text = args[0] if len(args) > 0 else kwargs.get("text")
    try:
      from pylatexenc.latex2text import LatexNodes2Text
      _text = LatexNodes2Text().latex_to_text(_text)
    except Exception as e:
      self.log_error("LaTeX parsing failed.")
    return _text

  def parse_html(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    _text = args[0] if len(args) > 0 else kwargs.get("text")

    from bs4 import BeautifulSoup
    _html = BeautifulSoup(_text, "html.parser")
    return _html

  def read_pickle(self, *args, **kwargs):
    """
      @function
      reads pickle file

      @params
      0|source (str|path): File path
      1|default (any): default value to return if file not found
      2|flag_compressed (boolean): If file is gz compressed (other compressions are not implemented)

      @return
      None: if some error occurs
      python object after reading the pkl file
    """
    self.update_attributes(self, kwargs)
    _source = args[0] if len(args) > 0 else kwargs.get("source")
    _default = args[1] if len(args) > 1 else kwargs.get("default", None)
    _flag_compressed = args[2] if len(args) > 2 else kwargs.get("flag_compressed", True)

    if self.check_path(_source) and self.require('cPickle', "PICKLE", "pickle"):
      if _flag_compressed and self.require("gzip", "GZip"):
        with self.GZip.open(_source, 'rb') as _fh:
          _default = self.PICKLE.load(_fh)
      else:
        with open(_source, 'rb+') as _fp:
          _default = self.PICKLE.load(_fp)
    else:
      self.log_error("Required module or pickle path is not found!")

    return _default

  unpickle = read_pickle
  get_pickle = read_pickle

  def read_html(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    _source = args[0] if len(args) > 0 else kwargs.get("source")
    _read = self.read_text(_source)
    _file_content = None
    if isinstance(_read, (list, tuple, set)):
      _file_content = "".join(_read)
    return self.parse_html(_file_content, **kwargs)

  # added v2.8
  html = read_html
  from_html = read_html

  def read_xml(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    _source = args[0] if len(args) > 0 else kwargs.get("source")
    _content = ""

    from lxml import etree as XMLTree
    if self.check_path(_source):
      _tree = XMLTree.parse(_source)
      _content = _tree.getroot()
    _content = self.xml_to_dict(_content)
    return _content

  def read(self, *args, **kwargs):
    """
      @ToDo:
      - Guess type of file and return type based on the path, extension with exceptions
      @Temporarily resolves to read_text
    """
    return self.read_text(*args, **kwargs)

  def read_text(self, *args, **kwargs):
    """
    @ToDo
      * implement yield|generator to handle larger files
      * check if file extension is gz, try reading it as gz
      * `str.splitlines(keepends=False)`
    """

    self.update_attributes(self, kwargs)
    _file_path = args[0] if len(args) > 0 else kwargs.get("file_path")
    _return_type = args[1] if len(args) > 1 else kwargs.get("return_type", list) # tuple, set
    _callback = args[2] if len(args) > 2 else kwargs.get("callback", self.strip) # "".join
    _content = None

    if self.OS.path.isdir(_file_path):
      self.log_error(f"{_file_path} is a directory not a file.")
      return None

    if self.ext(_file_path) == "gz":
      _content = self.read_gz_file(_file_path, None, row_size=None)
    else:
      with open(_file_path, 'r', encoding='UTF8') as _fh:
        _content = _fh.readlines()

    if not isinstance(_content, (str)) and (isinstance(_return_type, (str)) or _return_type == str):
      _content = "".join(_content)
    else:
      _content = _return_type(_content)

    if _callback is not None:
      _content = _callback(_content)

    return _content

  # added v2.8
  text = read_text
  from_text = read_text

  def read_json(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    _file_path = args[0] if len(args) > 0 else kwargs.get("file_path")
    _res_dict = {}

    if self.check_path(_file_path):
      _content = self.read_text(_file_path, str)
      self.require("ast", "AbsSynTree")
      try:
        _res_dict = self.JSON.loads(_content)
      except:
        _res_dict = self.AbsSynTree.literal_eval(_content)

    return _res_dict

  # added v2.8
  from_json = read_json
  from_JSON = read_json

  def write(self, *args, **kwargs):
    """
      @params
        0|destination:
        1|content
        2|append (boolean)
        3|encoding
        4|mode
        5|position: Write position by moving cursor

      @return
        check_path(destination)
    """
    self.update_attributes(self, kwargs)
    _destination = args[0] if len(args) > 0 else kwargs.get("destination")
    _content = args[1] if len(args) > 1 else kwargs.get("content", "")
    _append = args[2] if len(args) > 2 else kwargs.get("append", False)
    _encoding = args[3] if len(args) > 3 else kwargs.get("encoding", "utf-8")
    _mode = args[4] if len(args) > 4 else kwargs.get("mode", "w+")
    _position = args[5] if len(args) > 5 else kwargs.get("position", 0)

    if _append is True:
      # Change any mode to a
      _mode = _mode[:0] + 'a' + _mode[1:]

    # Create dir if doesn't exist
    if self.OS.path.isdir(_destination):
      raise Exception(f"{_destination} already exists as a directory. Cannot write as a file.")

    _parent_path = self.validate_dir(self.OS.path.dirname(_destination))
    _file_name = self.filename(_destination, True)
    self.log_info(f"Writing {_file_name} to {_parent_path}.")

    if isinstance(_content, (bytes, bytearray)):
      _encoding = None
      _mode = "wb" if "b" not in _mode else _mode

    _write_args = {
      "encoding": _encoding
    }

    with open(_destination, _mode, **_write_args) as _fh:
      if _mode.startswith("w"):
        _fh.seek(_position)

      if isinstance(_content, (bytes, bytearray, str)):
        _fh.write(_content)
      elif isinstance(_content, (list, tuple, set)):
        _fh.write("\n".join(_content))

    return self.check_path(_destination)

  def write_pickle(self, *args, **kwargs):
    """
      @function
      Writes python object as pickle file

      @params
      0|destination (str|path)
      1|content (any): Python object for pickling

      @returns
      True|False if file path exists

      @update
        Uses GZip for compression
        File extension pkl.gz used against df.gz|pd.gz pickled files
    """

    self.update_attributes(self, kwargs)
    if self.require('cPickle', "PICKLE", "pickle") and self.require("gzip", "GZip"):
      _destination = args[0] if len(args) > 0 else kwargs.get("destination")
      _content = args[1] if len(args) > 1 else kwargs.get("content")

      with self.GZip.open(_destination,'wb') as _fh:
        self.PICKLE.dump(_content, _fh)
    else:
      self.log_error("Either pickle/gzip module was not loaded or some other error occurred.")
    return self.exists(_destination)

  save_pickle = write_pickle
  pickle = write_pickle
  to_pickle = write_pickle
  to_pkl = write_pickle
  pkl = write_pickle

  def write_json(self, *args, **kwargs):
    """@function
      Writes dict content as JSON

      @returns
      True|False if file path exists
    """
    self.update_attributes(self, kwargs)
    _destination = args[0] if len(args) > 0 else kwargs.get("destination")
    _content = args[1] if len(args) > 1 else kwargs.get("content", dict())
    if isinstance(_content, (dict)):
      _json_data = self.JSON.dumps(_content, ensure_ascii=False)
      self.write(_destination, _json_data)
    return self.check_path(_destination)

  save_json = write_json

  def write_xml(self, *args, **kwargs):
    """@function
      Writes XML string to file

      @returns
      True|False if file path exists
    """
    self.update_attributes(self, kwargs)
    _destination = args[0] if len(args) > 0 else kwargs.get("destination")
    _content = args[1] if len(args) > 1 else kwargs.get("content")
    self.write(_destination, _content, **kwargs)
    return self.check_path(_destination)

  save_xml = write_xml

  def xml_to_dict(self, *args, **kwargs):
    """Converts XML to dict

      @returns
      dict of the converted xml
    """
    self.update_attributes(self, kwargs)
    _data = args[0] if len(args) > 0 else kwargs.get("data")
    _res = {}

    self.require("xmltodict", "XMLTODICT")
    from lxml import etree as XMLTree

    try:
      if not isinstance(_data, (str)):
        _data = XMLTree.tostring(_data, encoding='utf8', method='xml')
      _res = self.JSON.loads(self.JSON.dumps(self.XMLTODICT.parse(_data)))
    except:
      self.log_info(f"Failed to convert XML to DICT. Some error occurred.")
    return _res

  conv_xml_to_dict = xml_to_dict
  convert_xml_to_dict = xml_to_dict

  def dict_to_csv(self, *args, **kwargs):
    _destination = args[0] if len(args) > 0 else kwargs.get("destination")
    _data = args[1] if len(args) > 1 else kwargs.get("data")

    if isinstance(_data, list) and isinstance(_data[0], dict):
      _keys = _data[0].keys()
      self.require("csv", "CSV")
      with open(_destination, 'w+', newline='', encoding="utf8") as _ofh:
        _dict_writer = self.CSV.DictWriter(_ofh, _keys)
        _dict_writer.writeheader()
        _dict_writer.writerows(_data)
    return self.check_path(_destination)

  def move(self, *args, **kwargs):
    """Copies source and deletes using .delete_path
    """
    _source = args[0] if len(args) > 0 else kwargs.get("source")
    # _destination = args[1] if len(args) > 1 else kwargs.get("destination")
    if self.copy(*args, **kwargs):
      return self.delete_path(_source)
    else:
      return False

  def _copy_from_to(self, *args, **kwargs):
    """Copy file from source to destination
    @params
    0|source: path or string
    1|destination: path or string

    @usage
    REF._copy_from_to(_source, _destination)

    """
    _source = args[0] if len(args) > 0 else kwargs.get("source")
    _destination = args[1] if len(args) > 1 else kwargs.get("destination")

    if not all([_source, _destination]):
      self.log_info(f"Source or Destination is not specified.")
      return False

    self.validate_dir(self.OS.path.dirname(_destination))

    self.log_info(f"Copying... {_source} to {_destination}.")
    self.SHUTIL.copyfile(_source, _destination)
    return self.check_path(_destination)

  # Alias Added: 20240330
  copy = _copy_from_to
  copy_file = _copy_from_to
  copy_to = _copy_from_to
  create_copy = _copy_from_to

  def delete_path(self, *args, **kwargs):
    """Deletes a file or directory

      @params
      0|path (str): File path
      1|flag_files_only (boolean): To keep directory structure but delete all the files

      @ToDo:
      Instead of deletion, move the entity to temporary directory to avoid any accidental loss of data
    """
    _path = args[0] if len(args) > 0 else kwargs.get("path")
    _flag_files_only = args[1] if len(args) > 1 else kwargs.get("flag_files_only", False)

    if _path is None or not self.check_path(_path):
      return True

    if self.OS.path.isfile(_path):
      self.OS.remove(_path)

    elif self.OS.path.isdir(_path) and not _flag_files_only:
      self.SHUTIL.rmtree(_path)

    return not self.check_path(_path)

  # Alias Added: 20240330
  delete_file = delete_path

  def delete_files(self, *args, **kwargs):
    """Deletes multiple files or paths"""

    _paths = args[0] if len(args) > 0 else kwargs.get("paths")
    _deleted_files = []

    if isinstance(_paths, (str)) and self.exists(_paths):
      _paths = [_paths]

    if not isinstance(_paths, (list, tuple, set, dict)):
      return True

    for _path in _paths:
      _deleted_files.append(self.delete_path(_path, True))

    return _deleted_files

  def get_file_content(self, *args, **kwargs):
    """@extends get_file

      @function
      returns content of a file

    """

    kwargs.update({"return_text": True})
    return self.get_file(*args, **kwargs)

  def download_content(self, *args, **kwargs):
    _url = args[0] if len(args) > 0 else kwargs.get("url")
    _destination = args[1] if len(args) > 1 else kwargs.get("destination", None)

    if _destination:
      self.validate_dir(self.file_dir(_destination))

    self.require("urllib.request", "URLLib")

    try:
      self.URLLib.urlretrieve(_url, _destination)
    except:
      self.log_error(f"{_url} has some error. Couldn't download the content.")

    return self.check_path(_destination)

  def get_file(self, *args, **kwargs):
    """
      @function
      downloads a url content and returns content of the file
      uses urlretrieve as fallback

      @return
      str|list
      None

      @params
      0|url (str):
      1|destination (None|str|path):
      2|return_text (bool):
      3|overwrite (False|bool): forces to download the content if file already exists
      4|form_values (None|dict): values to be submitted while downloading file from url USING GET METHOD
      5|headers: headers to set for downloading files
      6|method ("get"|"post"): method of downloading file

      @update
      * v20220905
        - Removed json parameter to use form_values instead of json
    """
    _url = args[0] if len(args) > 0 else kwargs.get("url")
    _destination = args[1] if len(args) > 1 else kwargs.get("destination", None)
    _return_text = args[2] if len(args) > 2 else kwargs.get("return_text", False)
    _overwrite = args[3] if len(args) > 3 else kwargs.get("overwrite", False)
    _form_values = args[4] if len(args) > 4 else kwargs.get("form_values", None)
    _headers = args[5] if len(args) > 5 else kwargs.get("headers", {})
    _method = args[6] if len(args) > 6 else kwargs.get("method", "get")

    _default_headers = {'User-agent': 'Mozilla/5.0'}
    _default_headers.update(_headers)

    if not _overwrite and self.check_path(_destination):
      self.log_warning(f"{_url} exists at {_destination}.")
      return True

    if not _destination:
      # Return text if writing destination not provided
      _return_text = True

    try:
      self.require("requests", "REQUESTS")
      _session = self.REQUESTS.Session()
      _session.headers.update(_default_headers)
      self.log_info(f"Downloading content from {_url}.")

      if _method == "post":
        _response = _session.post(_url, stream=True, json=_form_values, allow_redirects=True)
      else:
        _response = _session.get(_url, stream=True, data=_form_values, allow_redirects=True)

      if _destination:
        kwargs.pop("content", None)
        kwargs.pop("destination", None)
        self.write(_destination, _response.content, **kwargs)
      if _return_text:
        return _response.text
    except:
      self.log_warning(f"Normal procedure failed. Trying alternate method 'urlretrieve'.")
      self.download_content(_url, _destination)

    return self.check_path(_destination)

  def _search_dir_filter(self, *args, **kwargs):
    """Search directories using pattern

    """
    self.update_attributes(self, kwargs)
    _source = args[0] if len(args) > 0 else kwargs.get("dir", getattr(self, "dir"))
    _pattern = args[1] if len(args) > 1 else kwargs.get("pattern", "/*/")
    return self._search_path_pattern(_source, _pattern)

  search_dirs = _search_dir_filter
  find_dirs = _search_dir_filter

  def _search_file_filter(self, *args, **kwargs):
    """Search files using pattern

    """
    _source = args[0] if len(args) > 0 else kwargs.get("dir", getattr(self, "dir"))
    _pattern = args[1] if len(args) > 1 else kwargs.get("pattern", ["*"])

    return self._search_path_pattern(_source, _pattern)

  # added v2.8
  search_files = _search_file_filter
  find_files = _search_file_filter
  search = _search_file_filter

  def get_file_types(self, *args, **kwargs):
    """Search files using extension

    """
    _source = args[0] if len(args) > 0 else kwargs.get("source", getattr(self, "source", self.OS.getcwd()))
    _ext = args[1] if len(args) > 1 else kwargs.get("ext", getattr(self, "ext", ()))
    _matches = []

    if not all((_source, len(_ext) > 0)):
      return _matches

    for _root, _dir_names, _file_names in self.OS.walk(_source):
      for filename in _file_names:
        if filename.endswith(_ext):
          _matches.append(self.OS.path.join(_root, filename))
    return _matches

  def _search_path_pattern(self, *args, **kwargs):
    """Internal Function to Search Paths based on pattern

    """
    self.update_attributes(self, kwargs)
    _results = []
    _source = args[0] if len(args) > 0 else kwargs.get("source", getattr(self, "source"))
    _pattern = args[1] if len(args) > 1 else kwargs.get("pattern", "*")

    if not _source or not _pattern:
      return _results

    if isinstance(_pattern, (str)):
      _pattern = [_pattern]

    self._import_module_from('pathlib', 'Path', 'PATH')

    for _p in _pattern:
      if "*" not in _p:
        _p = f"*{_p}*"
      _results.extend([str(f) for f in self.PATH(_source).expanduser().glob(_p)])

    return _results

  def create_dir(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    _dir_paths = args[0] if len(args) > 0 else kwargs.get("dirs")

    if isinstance(_dir_paths, str):
      _dir_paths = [_dir_paths]

    _dir_created = {}
    for _d in _dir_paths:
      if len(_d) > 1 and not self.OS.path.exists(_d):
        self.log_info(f"Path does not exist. Creating {_d}...")
        _res = self.OS.makedirs(_d)
        _dir_created[_d] = _res
      else:
        self.log_warning(f"Either {_d} already exists or some other error occurred while creating the file.")

    return _dir_created

  def get_existing(self, *args, **kwargs):
    """Returns first existing path from the given list

      @extends check_path
    """
    _path = args[0] if len(args) > 0 else kwargs.get("path")
    if isinstance(_path, (str)):
      _path = [_path]

    if isinstance(_path, (list, dict, tuple, set)):
      for _p in _path:
        if self.check_path(_p):
          return _p
    return False

  def check_path(self, *args, **kwargs):
    """Checks if path(s) exists or not

      @param
      0|path: String, path, or list of paths

      @return boolean
      True|False
    """
    self.update_attributes(self, kwargs)
    _path = args[0] if len(args) > 0 else kwargs.get("path")
    _result = False

    if isinstance(_path, (list, dict, tuple, set)):
      _result = list()
      for _p in _path:
        _r = _p if self.check_path(_p) else False
        _result.append(_r)
    else:
      _result = self.OS.path.exists(_path) if _path else _result

    return _result

  exists = check_path
  path_exists = check_path
  dir_exists = check_path
  file_exists = check_path

  def validate_subdir(self, *args, **kwargs):
    _base = args[0] if len(args) > 0 else kwargs.get("base")
    _sub = args[0] if len(args) > 0 else kwargs.get("sub")
    _rgx = self.re_compile(r"[/\\]")
    # Check if sub_dir contains any slash so that it is not directory name, append it's parent path
    if _rgx.search(str(_sub)) == None:
      return self.validate_dir(f"{_base}{self.OS.sep}{_sub}")
    else:
      return self.validate_dir(_sub)

  def validate_dir(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    _dir = args[0] if len(args) > 0 else kwargs.get("dir")
    if not self.check_path(_dir):
      _res = self.create_dir(_dir, **kwargs)
      if _dir in _res.keys():
        self.log_info(f"Directory created.")
      else:
        self.log_info(f"Failed to create directory {_dir}.")
    return _dir

  def change_ext(self, *args, **kwargs):
    _fp = args[0] if len(args) > 0 else kwargs.get("path")
    _to = args[1] if len(args) > 1 else kwargs.get("to")
    _from = args[2] if len(args) > 2 else kwargs.get("from")
    _num_ext = args[3] if len(args) > 3 else kwargs.get("num_ext", 1)

    _current_ext = self.ext(_fp, _num_ext)

    if _from is not None:
      if _current_ext == _from:
        _f_wo_ext = self.file_name(_fp, with_dir = True, num_ext = _num_ext)
      else:
        WARN("From and Current extensions are not same.")
        return _fp
    else:
      _f_wo_ext = self.file_name(_fp, with_dir = True, num_ext = _num_ext)

    return ".".join((_f_wo_ext, _to))

  def file_dir(self, *args, **kwargs):
    """Returns parent directory path from the filepath
    """
    _fpath = args[0] if len(args) > 0 else kwargs.get("path")
    _validate = args[1] if len(args) > 1 else kwargs.get("validate", False)
    if _fpath:
      _fpath = self.OS.path.dirname(_fpath)

    if _validate and not self.OS.path.isdir(_fpath):
      return None

    return _fpath

  def filename(self, *args, **kwargs):
    """
      @function
      Returns file_name from path <path>/<file_name>.<extn>.<ext2>.<ext1>

      @params
      0|file_path
      1|with_ext=default False
      2|with_dir=default False
      3|num_ext=default 1 or -1 to guess extensions

      @ToDo
      num_ext=-1 to guess extensions
    """
    _file_path = args[0] if len(args) > 0 else kwargs.get("file_path")
    _with_ext = args[1] if len(args) > 1 else kwargs.get("with_ext", False)
    _with_dir = args[2] if len(args) > 2 else kwargs.get("with_dir", False)
    _num_ext = args[3] if len(args) > 3 else kwargs.get("num_ext", 1)

    if not _file_path:
      return None

    if _with_dir is False:
      _file_path = self.OS.path.basename(_file_path)

    if _with_ext is True:
      return str(_file_path)

    _file_path = _file_path.rsplit(".", _num_ext)

    if len(_file_path):
      return _file_path[0]

    return None

  file_name = filename

  def file_ext(self, *args, **kwargs):
    """Returns file fxtension

      @params
      0|file_path
      1|num_ext=1: Number of extension with a dot
    """
    _file_path = args[0] if len(args) > 0 else kwargs.get("file_path")
    _num_ext = args[1] if len(args) > 1 else kwargs.get("num_ext", 1)
    _delimiter = args[2] if len(args) > 2 else kwargs.get("delimiter", ".")

    _file_path = self.OS.path.basename(_file_path)
    _file_path = _file_path.rsplit(_delimiter, _num_ext) # str.removesuffix
    _file_path = f"{_delimiter}".join(_file_path[-_num_ext:])
    return _file_path

  get_extension = file_ext
  get_ext = file_ext
  file_extension = file_ext
  ext = file_ext

  def split_file(self, *args, **kwargs):
    """WIP: Split file in smaller files"""
    _file_path = args[0] if len(args) > 0 else kwargs.get("file_path")
    _sdf_id_delimiter = args[2] if len(args) > 2 else kwargs.get("id_delimiter")
