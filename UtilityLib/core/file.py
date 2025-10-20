from .db import DatabaseUtility
from ..lib.path import EntityPath
from ..lib.file import EntityFile

class FileSystemUtility(DatabaseUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {}
    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)
    self.require('shutil', 'SHUTIL')
    self.require('json', 'JSON')

  def _backup_file(self, *args, **kwargs):
    _path_file = kwargs.get('path_file', args[0] if len(args) > 0 else None)
    _path_backup = kwargs.get('path_backup', args[1] if len(args) > 1 else None)
    _flag_compress = kwargs.get('flag_compress', args[2] if len(args) > 2 else True)

    _path_file = EntityPath(_path_file)

    if _path_file is None or not _path_file.is_file():
      return

    _file_stamped_name = _path_file.name + f'.{self.timestamp}.bkup'

    if not isinstance(_path_backup, (EntityPath, str)):
      _path_backup = _path_file.parent()

    if _path_backup.exists() and _path_backup.is_dir():
      _path_backup = _path_backup / _file_stamped_name
    elif _path_backup.suffix.startswith('.'):
      _path_backup.parent().validate()
    else:
      _path_backup.validate()
      _path_backup = _path_backup / _file_stamped_name

    _path_file.copy(_path_backup)

    if _flag_compress:
      return self.gz(_path_backup, flag_move=True)

    return _path_backup

  backup = _backup_file
  create_file_backup = _backup_file
  backup_file = _backup_file

  def get_file_backups(self, *args, **kwargs):
    _path_file = kwargs.get('path_file', args[0] if len(args) > 0 else None)
    _path_file = EntityPath(_path_file)
    _path_backup = kwargs.get('path_backup', args[1] if len(args) > 1 else _path_file if _path_file.is_dir() else _path_file.parent())
    _path_backup = EntityPath(_path_backup)

    return _path_backup.search(f"{_path_file.name}*bkup*")

  def clean_file_backups(self, *args, **kwargs):
    _all = kwargs.get('all', False)
    _all_backups = self.get_file_backups(*args, **kwargs)
    _res = None

    try:
      if not _all:
        _first, _bkups = next(_all_backups), _all_backups
      else:
        _bkups = _all_backups
      _res = [_bkup.delete(is_protected = False) for _bkup in _bkups]
    except Exception as _e:
      self.log_debug(_e)

    return _res

  def get_file_backup(self, *args, **kwargs):
    """Get latest file backup"""
    *_backups, = self.get_file_backups(*args, **kwargs)
    sorted(_backups, key=lambda _x: self.get_parts(_x, -2, '.'), reverse=True)
    return _backups[0] if len(_backups) > 0 else None

  def rename(self, *args, **kwargs):
    _old_name = args[0] if len(args) > 0 else kwargs.get("from")
    _new_name = args[1] if len(args) > 1 else kwargs.get("to")
    return self.OS.rename(_old_name, _new_name)

  def _compress_dir(self, *args, **kwargs):
    """Archive/compress a directory
    @params
    0|source: eg /mnt/data/downloads/xyz-files
    1|format: eg /mnt/data/downloads/xyz-files(.tar.gz|.zip|.tar) || "zip", "tar", "gztar", "bztar", or "xztar"
    2|destination: eg /mnt/data/downloads/xyz-files.tgz
    3|flag_move (False): Deletes the original file
    """

    _source = args[0] if len(args) > 0 else kwargs.get("source")
    _format = args[1] if len(args) > 1 else kwargs.get("format", "zip")
    _destination = args[2] if len(args) > 2 else kwargs.get("destination", f"{_source}.{_format}")
    _flag_move = args[3] if len(args) > 3 else kwargs.get("flag_move", False)

    _format_map = {
        "tar.gz": 'gztar',
        "tar.bz": 'bztar',
        "tar.xz": 'xztar',
        "tgz": 'gztar',
        "tbz": 'bztar',
        "txz": 'xztar',
        "zip": 'zip',
        "tar": 'tar',
    }

    _shutil_format = _format_map.get(_format, 'gztar')

    _kwargs = {
      "base_name": self.file_name(_destination, with_dir=True, num_ext=1),
      "root_dir": self.file_dir(_source),
      "base_dir": self.file_name(_source),
      "format": _shutil_format,
    }
    _result = self.SHUTIL.make_archive(**_kwargs)

    if _flag_move:
      self.delete_path(_source)

    return _result;

  compress_dir = _compress_dir
  compress_zip = _compress_dir

  def _compress_dir_to_tgz(self, *args, **kwargs):
    """@extends _compress_dir

    Compresses a directory to tar.gz
    """
    _format = args[1] if len(args) > 1 else kwargs.get("format", "tgz")
    kwargs['format'] = 'tgz'
    if (len(args) > 1):
      args = list(args)
      args[1] = _format

    return self._compress_dir(*args, **kwargs)

  to_tgz = _compress_dir_to_tgz
  tgz = _compress_dir_to_tgz

  def zip(self, *args, **kwargs):
    _format = args[1] if len(args) > 1 else kwargs.get("format", "zip")
    kwargs['format'] = 'zip'
    if (len(args) > 1):
      args = list(args)
      args[1] = _format

    self._compress_dir(*args, **kwargs)

  def _compress_file_to_gzip(self, *args, **kwargs):
    """Compress a file to gz

    :param path_file|0:
    :param flag_move|1: Default False

    """
    _path_file = kwargs.get("path_file", args[0] if len(args) > 0 else None)
    _path_destination = kwargs.get("path_destination", args[1] if len(args) > 1 else False)
    self.require("gzip", "GZip")

    _path_file = EntityPath(_path_file)
    if not _path_file.exists():
      return None

    if not _path_destination:
      _path_destination = _path_file + '.gz'

    _path_destination = EntityPath(_path_destination)

    if _path_destination.exists():
      self.log_warning(f"{_path_destination} already exists. Cannot overwrite.")
      return None

    with open(_path_file, 'rb') as _f_in, self.GZip.open(_path_destination, 'wb') as _f_out:
      _f_out.writelines(_f_in)

    return _path_destination

  compress_gz      = _compress_file_to_gzip
  to_gz            = _compress_file_to_gzip
  gz               = _compress_file_to_gzip
  gzip             = _compress_file_to_gzip
  compress_to_gzip = _compress_file_to_gzip

  def _add_files_to_tar_gzip(self, *args, **kwargs):
    """Adds files to tarball with gz compression
      Note: Directory architecture is not maintained for now.

      @params
      :param path_tgz|0:
      :param files_path|1:
      :param mode|2: (default: w:gz)
    """
    self.path_tgz = kwargs.get("path_tgz", args[0] if len(args) > 0 else getattr('path_tgz', None))
    _file_paths = kwargs.get("files_path", args[1] if len(args) > 1 else [])
    _mode = kwargs.get("mode", args[2] if len(args) > 2 else "w:gz")

    if isinstance(_file_paths, (str, EntityPath)):
      _file_paths = [_file_paths]

    if isinstance(_file_paths, (list, tuple, set)):
      _file_paths = {self.file_name(_f, with_ext=True): _f for _f in _file_paths if self.check_path(_f)}

    if isinstance(_file_paths, (dict)):
      self.require("tarfile", "TarFileManager")
      if not self.exists(self.path_tgz):
        _tar = self.TarFileManager.open(self.path_tgz, _mode)
        _tar.close()

      _tar = self.TarFileManager.open(self.path_tgz, 'r:gz')
      _tmp_tgz = f"{self.path_tgz}.tmp.tgz"

      _tmp_tarh = self.TarFileManager.open(_tmp_tgz, _mode)

      _tar.extractall()
      for _mem in _tar.members:
        _tmp_tarh.add(_mem.path)
        self.delete_file(_mem.path)

      # @TODO Same file name in different path will be overridden
      for _name, _path in _file_paths.items():
        if self.check_path(_path):
          _tmp_tarh.add(_path, arcname=_name)

      _tmp_tarh.close()
      _tar.close()

      self.delete_file(self.path_tgz)
      self.rename(_tmp_tgz, self.path_tgz)

  add_tgz_files = _add_files_to_tar_gzip

  def list_tgz_items(self, *args, **kwargs):
    """

    @bug: Doesn't renew file in loop due to path_tgz
    Workaround to assign path_tgz at the beginning of every loop.

    """
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

    _processor_line = _processor_line if callable(_processor_line) else None

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

  def _get_fh_blocks(self, file_handle, size=65536):
    """Yields blocks from file handle"""
    while True:
      _b = file_handle.read(size)
      if not _b: break
      yield _b

  def count_file_lines(self, *args, **kwargs):
    """Quickly counts lines in a file or gz file
    @stats: counts lines in a 7GB gz file in 2min
    """
    _file_path = kwargs.get('path_file', args[0] if len(args) > 0 else None)
    _read_method = kwargs.get('read_method', open)

    # To bypass Pathlib open method call
    _file_path = str(_file_path.resolve())

    # Fall back
    _args = [_file_path, "r"]
    _kwargs = {
      "encoding": "utf-8",
      "errors": "ignore",
    }

    # If gz compressed
    if str(_file_path).endswith('.gz'):
      self.require('gzip', 'GZip')
      _read_method = self.GZip.open
      _args = [_file_path, "rt"]
      _kwargs = {}

    _num_lines = None
    with _read_method(*_args, **_kwargs) as _fh:
      _num_lines = sum(_bl.count("\n") for _bl in self._get_fh_blocks(_fh))

    return _num_lines

  def _uncompress_archive(self, *args, **kwargs):
    """Unpack archive like .zip, .gz, .tar

    Programs attempted:
      SHUTIL
      ZipFile
      7z Commandline

    :param source|0: eg /mnt/data/drive/downloads/files-1.tar.gz
    :param destination|1: /mnt/data/drive/downloads

    :return: bool
    """
    _source = kwargs.get("source", args[0] if len(args) > 0 else None)

    if _source is None:
      return None

    _source = EntityPath(_source)
    _destination = kwargs.get("destination", args[1] if len(args) > 1 else _source.parent() / _source.stem)

    _destination = EntityPath(_destination)

    if _destination.exists():
      self.log_warning(f'{_destination} already exists.')

    if _source.exists():
        try:
          if _source.has_suffix('.zip'):
            """Extracts ZIP Files Only"""
            self.require("zipfile", "ZipHandler")
            with self.ZipHandler.ZipFile(str(_source), 'r') as zipObj:
              zipObj.extractall(_destination)
          else:
            self.SHUTIL.unpack_archive(_source, _destination)
        except Exception as _e:
          # https://stackoverflow.com/a/59327542 ZIP compression 9
          self.log_debug(f'Error occurred: {_e}')
          self.log_debug(f'Trying with 7z')
          self.require('subprocess', 'SubProcess')
          self.SubProcess.Popen(["7z", "e", f"{_source}", f"-o{_destination}", "-y"])

    if _destination.exists():
      self.log_info(f"Extracted {_source} content in {_destination}.")
    else:
      self.log_error(f'Failed to extract {_source}.')

    return _destination.exists()

  extract_zip = _uncompress_archive
  unzip = _uncompress_archive
  uncompress = _uncompress_archive

  def _recursive_list_dir_items(self, *args, **kwargs):
    _path = kwargs.get('path', args[0] if len(args) > 0 else None)
    _path_details = kwargs.get('path_details', args[1] if len(args) > 1 else self.path_base / f'path-details.{self.timestamp[:10]}.tsv')

    if not _path or not _path.exists():
      return

    if not _path_details.exists():
      _head = ("file_dir",
          "file_name",
          "file_created",
          "file_modified",
          "file_accessed",
          "file_size")

      _head = "\t".join(_head)
      _head = _head + "\n"
      (_path_details).write_text(_head)

    if _path.is_file():
      _data = (str(_path.parent().full_path),
          str(_path.name),
          str(_path.stats.st_ctime),
          str(_path.stats.st_mtime),
          str(_path.stats.st_atime),
          str(_path.size))

      _data = "\t".join(_data)
      _data = _data + "\n"
      (_path_details).write_text(_data)

    elif _path.is_dir():
      for _item in _path.items:
        self._recursive_list_dir_items(_item, _path_details)
    else:
      self.log_error(f'{_path} is neither a dir or file.')

  def _dir_file_inventory(self, *args, **kwargs):
    _path = kwargs.get('path', args[0] if len(args) > 0 else self.path_base)

    _path = EntityPath(_path)
    _ustamp = str(self.timestamp)[:10]

    _path_details = kwargs.get('path_details', args[1] if len(args) > 1 else _path.with_suffix(f'.items-{_ustamp}.tsv'))
    _level = kwargs.get('level', args[2] if len(args) > 2 else -1) # -1 for all, 0 for one recursion
    _flag_sqlite = kwargs.get('flag_sqlite', args[3] if len(args) > 3 else False)

    if not _path or not _path.exists():
      return

    _path_details_gz = _path.with_suffix(f'.items-{_ustamp}.tsv.gz')

    if _path_details.exists():
      self.log_warning('Deleting existing details file.')

    if _path_details_gz.exists():
      _path_details_gz.move(_path_details_gz.with_suffix(f".{_path_details_gz.suffix}.bak"))

    self._recursive_list_dir_items(_path, _path_details, level=_level)

    self.gz(_path_details, flag_move=True)

    # Get dataframe from the
    _item_details = self.read_tsv(_path_details_gz)

    """SQLite Takes More Space Than File"""
    if _flag_sqlite:
      self.conect_sqlite(self.config.details_file.with_suffix('.db'))
      _item_details.to_sql(self.config.details_file.stem, self.engine, index=False)

    return _path_details_gz, _item_details

  dir_details = _dir_file_inventory
  get_item_details = _dir_file_inventory
  file_stats = _dir_file_inventory

  def list_zip_items(self, *args, **kwargs):
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
    _text = args[0] if len(args) > 0 else kwargs.get("text")
    try:
      from pylatexenc.latex2text import LatexNodes2Text
      _text = LatexNodes2Text().latex_to_text(_text)
    except Exception as e:
      self.log_error("LaTeX parsing failed.")
    return _text

  def parse_html(self, *args, **kwargs):
    """Parse HTML using BeautifulSoup

      :param 0|markup (str): HTML markup to parse
      :param 1|parser (str): Parser to use, default is 'html.parser; 'html.parser', 'lxml', 'html5lib''
    """
    _markup = kwargs.get("markup", args[0] if len(args) > 0 else '')
    _parser = kwargs.get("parser", 'html.parser')

    from bs4 import BeautifulSoup
    _html = BeautifulSoup(_markup, _parser)
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
    _source = args[0] if len(args) > 0 else kwargs.get("source")
    _default = args[1] if len(args) > 1 else kwargs.get("default", None)
    _flag_compressed = args[2] if len(args) > 2 else kwargs.get("flag_compressed", True)

    _source = EntityPath(_source)

    if _source.exists() and self.require('pickle', "PICKLE"):
      if _flag_compressed and self.require("gzip", "GZip"):
        with self.GZip.open(str(_source.resolve()), 'rb') as _fh:
          _default = self.PICKLE.load(_fh)
      else:
        with open(str(_source.resolve()), 'rb+') as _fp:
          _default = self.PICKLE.load(_fp)
    else:
      self.log_error(f"Either path {_source} doesn't exists or required module or pickle path is not found!")

    return _default

  unpickle = read_pickle
  get_pickle = read_pickle

  def get_html(self, *args, **kwargs):
    _content = self.get_file_content(*args, **kwargs)
    return self.parse_html(_content, **kwargs)

  def read_html(self, *args, **kwargs):
    """Read and parse HTML file - DELEGATED TO EntityFile
    """
    _source = args[0] if len(args) > 0 else kwargs.get("source")
    return EntityFile(_source).read_html(**kwargs)

  # added v2.8
  html      = read_html
  from_html = read_html

  def read_xml(self, *args, **kwargs):
    """Read and parse XML file - DELEGATED TO EntityFile
    """
    _source = kwargs.get("source", args[0] if len(args) > 0 else None)
    return EntityFile(_source).read_xml(**kwargs)

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
    """Read JSON file - DELEGATED TO EntityFile"""
    _file_path = args[0] if len(args) > 0 else kwargs.get("file_path")
    return EntityFile(_file_path).read_json(**kwargs)

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

    _destination = kwargs.get("destination", args[0] if len(args) > 0 else None)
    _content = kwargs.get("content", args[1] if len(args) > 1 else None)

    self.require('pickle', "PICKLE", "pickle")
    self.require("gzip", "GZip")

    try:
      with self.GZip.open(_destination,'wb') as _fh:
        self.PICKLE.dump(_content, _fh)
    except Exception as _e:
      self.log_error(f"Error: {_e}")

    return self.exists(_destination)

  save_pickle = write_pickle
  pickle = write_pickle
  to_pickle = write_pickle
  to_pkl = write_pickle
  pkl = write_pickle

  def write_json(self, *args, **kwargs):
    """Write dict content as JSON

      @returns
      True|False if file path exists
    """
    _destination = args[0] if len(args) > 0 else kwargs.get("destination")
    _content = args[1] if len(args) > 1 else kwargs.get("content", dict())
    return EntityFile(_destination).write_json(_content, **kwargs)

  save_json = write_json

  def write_xml(self, *args, **kwargs):
    """Write XML content to file

      @returns
      True|False if file path exists

    """

    _destination = kwargs.get("destination", args[0] if len(args) > 0 else None)
    _content = kwargs.get("content", args[1] if len(args) > 1 else None)
    _encoding = kwargs.pop("encoding", args[2] if len(args) > 2 else 'utf-8')
    kwargs['encoding'] = _encoding

    return EntityFile(_destination).write_xml(_content, **kwargs)

  save_xml = write_xml

  def xml_to_dict(self, *args, **kwargs):
    """Converts XML to dict

      @returns
      dict of the converted xml
    """
    _data = kwargs.get("data", args[0] if len(args) > 0 else "")
    _res = {}

    try:
      self.require("xmltodict", "XMLTODICT")
      from lxml import etree as XMLTree

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
      self.log_debug(f"FILE_01: Source or Destination is not specified.")
      return False

    self.validate_dir(self.OS.path.dirname(_destination))

    self.log_debug(f"FILE_02: Copying... {_source} to {_destination}.")
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

  def convert_bytes(self, *args, **kwargs):
    """Converts bytes to ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")... etc

    :params _bytes|0: float
    """
    _bytes = kwargs.get('bytes', args[0] if len(args) > 0 else 0)
    _bytes = float(_bytes)

    import math

    if _bytes == 0:
      return "0B"
    size_name = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    i = int(math.floor(math.log(_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(_bytes/p, 2)
    return (s, size_name[i])

  def get_file_size(self, *args, **kwargs):
    """Returns file size(s)

    :params file_path|0: string or iterable

    :returns: [(file_path, file_size, size_unit), ]
    """
    _file_path = kwargs.get('file_path', args[0] if len(args) > 0 else [])

    _sizes = []
    _flag_is_single = False
    if isinstance(_file_path, (str, EntityPath)):
      _flag_is_single = True
      _file_path = [_file_path]

    if self.is_iterable(_file_path):
      for _fp in _file_path:
        _fp = EntityPath(_fp)
        if _fp.exists():
          _sizes.append((_fp, *_fp.get_size(self.convert_bytes)))

    return _sizes[0] if _flag_is_single else _sizes

  session          = None
  session_request  = None
  session_response = None
  def set_request_session(self, *args, **kwargs):
    """Sets session for requests

    Returns:
      session:
    """
    _headers = kwargs.get("headers", args[1] if len(args) > 1 else {})

    _default_headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    _default_headers.update(_headers)

    self.require("requests", "REQUESTS")
    self.session_request = self.REQUESTS.Session()
    self.session_request.headers.update(_default_headers)
    return self.session_request

  def _GET_URL_CONTENT(self, *args, **kwargs):
    """
      @function
      downloads a url content and returns content of the file
      uses urlretrieve as fallback

      @params
      :param url|0: (str)
      :param destination|1: (None|str|path)
      :param return_text|2: (bool)
      :param overwrite|3: (False|bool)= forces to download the content if file already exists
      :param form_values|4: (None|dict)= values to be submitted while downloading file from url USING GET METHOD
      :param headers: headers to set for downloading files
      :param method: ("get"|"post")= method of downloading file

      @returns
      :return: bool

      @update
      * v20220905
        - Removed json parameter to use form_values instead of json
      @ToDo:
      * Use wget library for the purpose
    """
    _url          = kwargs.get("url", args[0] if len(args) > 0 else None)
    _destination  = kwargs.get("destination", args[1] if len(args) > 1 else None)
    _return_text  = kwargs.get("return_text", args[2] if len(args) > 2 else False)
    _overwrite    = kwargs.get("overwrite", args[3] if len(args) > 3 else False)
    _form_values  = kwargs.get("form_values", args[4] if len(args) > 4 else None)
    _headers      = kwargs.get("headers", {})
    _method: str  = kwargs.get("method", "get")
    _request_args = kwargs.get("request_args", {})

    _default_request_args = {
        "stream"         : True,
        "allow_redirects": True,
        "headers"        : _headers,
      }

    _default_request_args.update(_request_args)

    if not _overwrite and self.check_path(_destination):
      self.log_warning(f"{_url} exists at {_destination}.")
      return True

    if not _destination:
      # Return text if writing destination not provided
      _return_text = True

    try:
      self.session = self.set_request_session(headers=_headers)
      self.log_info(f"Downloading content from {_url}.")

      if str(_method).lower() == "post":
        if _form_values:
          _default_request_args.update({"json": _form_values})
        self.session_response = self.session.post(_url, **_default_request_args)
      else:
        if _form_values:
          _default_request_args.update({"data": _form_values})

        self.session_response = self.session.get(_url, **_default_request_args)

      if _destination:
        kwargs.pop("content", None)
        kwargs.pop("destination", None)
        self.write(_destination, self.session_response.content, **kwargs)
      if _return_text:
        return self.session_response.text
    except:
      self.log_warning(f"Normal procedure failed. Trying alternate method 'urlretrieve'.")
      self.download_content(_url, _destination)

    return self.check_path(_destination)

  get_file = _GET_URL_CONTENT
  get_url_file = _GET_URL_CONTENT
  get_url = _GET_URL_CONTENT

  def _search_dir_filter(self, *args, **kwargs):
    """Search directories using pattern

    """
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

  def _walk_files_by_extension(self, *args, **kwargs):
    """Search files using extension(s) as suffix

    @params
    0|source
    1|ext: string, tuple, list or set containing extensions

    @returns
    files matches  as list found using os.walk
    """
    _source = kwargs.get("source", args[0] if len(args) > 0 else getattr(self, "source", self.OS.getcwd()))
    _ext = kwargs.get("ext", args[1] if len(args) > 1 else getattr(self, "ext", ()))
    _matches = []

    if not all((_source, len(_ext) > 0)):
      return _matches

    for _root, _dir_names, _file_names in self.OS.walk(_source):
      for filename in _file_names:
        if filename.endswith(_ext):
          _matches.append(self.OS.path.join(_root, filename))

    return _matches

  get_file_types = _walk_files_by_extension
  find_file_types = _walk_files_by_extension
  search_file_types = _walk_files_by_extension
  ext_files = _walk_files_by_extension

  def _search_path_pattern(self, *args, **kwargs) -> list:
    """Internal Function to Search Paths based on pattern

    """
    _results = []
    _source = args[0] if len(args) > 0 else kwargs.get("source", getattr(self, "source"))
    _pattern = args[1] if len(args) > 1 else kwargs.get("pattern", "*")

    if not _source or not _pattern:
      return _results

    _source = EntityPath(_source)

    if isinstance(_pattern, (str)):
      _pattern = [_pattern]

    for _p in _pattern:
      if "*" not in _p:
        _p = f"*{_p}*"
      _results.extend(list(_source.search(_p)))

    return _results

  def create_dir(self, *args, **kwargs) -> dict:
    _path = kwargs.get("path", args[0] if len(args) > 0 else None)

    _dir_created = {}
    if _path is None:
      pass
    if isinstance(_path, (EntityPath)):
      _path.validate()
      _dir_created[_path] = _path.exists()
    else:
      if isinstance(_path, str):
        _path = [_path]

      for _d in _path:
        if len(_d) > 1 and not self.OS.path.exists(_d):
          self.log_debug(f"FILE_03: Path does not exist. Creating {_d}...")
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
    # DEPRECATED
    raise Exception('DEPRECATED')

  def validate_dir(self, *args, **kwargs):
    _path = args[0] if len(args) > 0 else kwargs.get("path")
    _path = EntityPath(_path)

    try:
      _path.validate()
    except Exception as _e:
      self.log_error(_e)

    return _path

  validate_path = validate_dir

  def change_ext(self, *args, **kwargs):
    _path = kwargs.get("path", args[0] if len(args) > 0 else None)
    _to = kwargs.get("to", args[1] if len(args) > 1 else None)
    _from = kwargs.get("from", args[2] if len(args) > 2 else None)
    _num_ext = kwargs.get("num_ext", args[3] if len(args) > 3 else 1)

    _path = str(_path)
    _current_ext = self.ext(_path, _num_ext)

    if _from is not None:
      if _current_ext == _from:
        _f_wo_ext = self.file_name(_path, with_dir = True, num_ext = _num_ext)
      else:
        self.log_error("Method change_ext: From and Current extensions are not same.")
        return _path
    else:
      _f_wo_ext = self.file_name(_path, with_dir = True, num_ext = _num_ext)

    return ".".join((_f_wo_ext, _to))

  def get_open_file_descriptors(self, *args, **kwargs):
    self.require('psutil', 'PC')
    self.processes = self.PC.Process()
    return self.processes.num_fds()

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
    _file_path = kwargs.get("file_path", args[0] if len(args) > 0 else None)
    _with_ext = kwargs.get("with_ext", args[1] if len(args) > 1 else False)
    _with_dir = kwargs.get("with_dir", args[2] if len(args) > 2 else False)
    _num_ext = kwargs.get("num_ext", args[3] if len(args) > 3 else 1)

    if not _file_path:
      return None

    _file_path = EntityPath(_file_path)
    _result = _file_path.resolve()

    if _with_dir is False:
      _result = _file_path.name

    _result = str(_result)

    if _with_ext is True:
      return _result

    _result = _result.rsplit(".", _num_ext)

    if len(_result):
      return _result[0]

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
