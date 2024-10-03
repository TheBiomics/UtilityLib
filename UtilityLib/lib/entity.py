from pathlib import Path
import os as OS, time as TIME

class EntityPath(Path):
  _flavour = Path('.')._flavour
  force_delete = False

  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  def len(self):
    return len(str(self))

  __len__ = len

  def __str__(self):
    return super().__str__()

  def help(self):
    """
    Extension(s): Path.suffix, Path.suffixes
    Name: Path.name
    Stem: Path.stem (without suffixes)

    ## Noteable Methods
    Path.rglob(pattern, *, case_sensitive=None)
    Path.samefile(other_path)
    Path.symlink_to(target, target_is_directory=False)
    Path.write_bytes(data) # Write binary data
    Path.walk()
    Path.rename(target)
    Path.replace(target)
    Path.expanduser()
    Path.exists(*, follow_symlinks=True)
    Path.chmod(mode, *, follow_symlinks=True)
    Path.cwd()
    Path.with_name(new_name.ext) # Replaces the file name
    Path.with_stem(new_name) # Changes the file name (keeping extension)
    Path.with_suffix
    Path.match
    Path.parts
    """

  _is_gz = None

  @property
  def is_gz(self):
    if self._is_gz is None:
      self._is_gz = '.gz' in self.suffixes

    return self._is_gz

  is_compressed = is_gz

  @property
  def ext(self):
    return "".join(self.suffixes)

  _hash = None

  @property
  def hash(self):
    if self._hash is None:
      self._hash = self.get_hash()
    return self._hash

  def get_hash(self, algorithm='sha256'):
    """Compute the hash of the file or directory using the specified algorithm.

    :param algorithm: Hash algorithm to use ('md5', 'sha256', etc.)
    :return: The computed hash as a hexadecimal string
    """

    if self.is_file():
      self._hash = self._compute_file_hash(algorithm)
    elif self.is_dir():
      self._hash = self._compute_directory_hash(algorithm)
    else:
      self._hash = None
      raise ValueError(f"{self} is neither a file nor a directory.")

    return self._hash

  def _compute_file_hash(self, algorithm):
    """Helper method to compute the hash of a single file."""
    import hashlib as _HL
    _fn_hash = _HL.new(algorithm)

    # Read the file in _chunks to avoid memory issues with large files
    with self.open('rb') as _fh:
      for _chunk in iter(lambda: _fh.read(4096), b""):
        _fn_hash.update(_chunk)

    self._hash = _fn_hash.hexdigest()
    return self._hash

  def _compute_directory_hash(self, algorithm):
    """Helper method to compute the hash of a directory."""
    import hashlib as _HL
    _fn_hash = _HL.new(algorithm)

    for _file_path in sorted(self.files):
      # Update the hash with the file path relative to the directory
      _rel_path = str(_file_path.relative_to(self)).encode()
      _fn_hash.update(_rel_path)

      # Update the hash with the file content
      with _file_path.open('rb') as _fh:
        for _chunk in iter(lambda: _fh.read(4096), b""):
          _fn_hash.update(_chunk)

    # Update hash with directory names
    for _dir in sorted(self.dirs):
      _fn_hash.update(_dir.name.encode())

    self._hash = _fn_hash.hexdigest()
    return self._hash

  def _read_lines(self, num_lines=None):
    if not self.is_file():
      raise ValueError(f"{self} is not a file.")

    try:
      if num_lines is None:
        with self.open() as _f:
          for _line in _f:
              yield _line
      else:
        with self.open() as _f:
          for _ in range(int(num_lines)):
            yield next(_f).strip()

    except StopIteration:
      pass
    except Exception as _e:
      raise Exception(f'Some unknown error occurred.: {_e}')

  read_lines = _read_lines
  readlines = _read_lines
  readline = _read_lines

  def head(self, lines=1):
    """Return first few lines of a file"""
    return list(self._read_lines(lines))

  def tail(self, lines=1, buffer_size=4098):
    """Tail a file and get X lines from the end
    Source: https://stackoverflow.com/a/13790289
    """

    _fh = self.open()
    _res_lines = []
    _block_counter = -1

    import os as OS
    while len(_res_lines) < lines:
      try:
        _fh.seek(_block_counter * buffer_size, OS.SEEK_END)
      except IOError:
        # either file is too small, or too many lines requested
        _fh.seek(0)
        break

      _block_counter -= 1

    _res_lines = _fh.readlines()
    return _res_lines[-lines:]

  def _read_file(self, method=None):
    """Read the text from the file.
      0|method: Custom method/function to read the file
    """
    if not self.is_file():
      raise ValueError(f"{self} is not a file.")

    if not method is None and callable(method):
      return method(str(self))

    return super().read_text()

  read_text = _read_file
  read = _read_file

  @property
  def text(self):
    return self._read_file()

  def write_text(self, data, mode="a"):
    """Write the given text to the file."""
    if self.exists() and not self.is_file():
      raise ValueError(f"{self} is not a file.")

    with self.open(mode) as _f:
      _f.write(data)

    return self.exists()

  write = write_text

  def list_files(self, relative=True):
    """List all files in the directory."""
    if not self.is_dir():
      raise ValueError(f"{self} is not a directory.")

    _files = []
    for _f in self.iterdir():
      if _f.is_file():
        _fp = EntityPath(_f)
        if relative == True:
          _fp = _fp.rel_path() # Relative to cwd
        _files.append(_fp)

    return _files

  @property
  def files(self):
    return self.list_files()

  _files = files

  @property
  def dirs(self):
    return self.list_dirs()

  _dirs = dirs

  def list_dirs(self):
    """List all directories in the directory."""
    if not self.is_dir():
      raise ValueError(f"{self} is not a directory.")
    return [EntityPath(_d) for _d in self.iterdir() if _d.is_dir()]

  folders = list_dirs

  def list_items(self):
    """List all items (files and directories) in the directory."""
    if not self.is_dir():
      raise ValueError(f"{self} is not a directory.")

    return [EntityPath(_i) for _i in self.iterdir()]

  @property
  def items(self):
    return self.list_items()

  entities = items
  _all = items

  def delete(self, force_delete=None):
    self.force_delete = force_delete or self.force_delete

    """Delete the file or directory."""
    if not self.force_delete:
      raise ValueError(f"{self} is not safe to delete. pass force_delete=True enable accidental deletion.")

    if self.is_file():
      self.unlink()
      return self.exists()
    elif self.is_dir():
      for _item in self.iterdir():
        if _item.is_dir():
          EntityPath(_item).delete(force_delete=self.force_delete)
        else:
          _item.unlink()
      self.rmdir()
      return self.exists()
    elif not self.exists():
      # already deleted or didn't exist
      return self.exists()
    else:
      raise ValueError(f"{self} is neither a file nor a directory.")

  def validate(self):
    """Make directory/file if doesn't exist."""

    if self.exists():
      return self
    elif len(self.suffixes) > 0:
      self.touch()
    else:
      Path(str(self)).mkdir(parents=True, exist_ok=True)

    return self

  def move(self, destination):
    """Move the file or directory to a new location."""
    if self.force_delete:
      return

    destination = EntityPath(destination)

    # If destination parent directories are not present
    if not destination.parent().exists():
      destination.parent().mkdir(parents=True, exist_ok=True)

    import shutil as _SHUTIL
    _SHUTIL.move(str(self), str(destination))
    return EntityPath(destination)

  def copy(self, destination):
    """Copy the file or directory to a new location."""
    import shutil as _SHUTIL

    destination = EntityPath(destination)
    # If target parent directories are not present
    if not destination.parent().exists():
      destination.parent().mkdir(parents=True, exist_ok=True)

    if self.is_file():
      _SHUTIL.copy(str(self), str(destination))
    elif self.is_dir():
      _SHUTIL.copytree(str(self), str(destination))

    return destination

  def get_match(self, pattern="*txt"):
    if not '*' in pattern:
      pattern = f"*{pattern}*"

    _files = list(self.search(pattern))
    return _files[0] if len(_files) > 0 else None

  def exists(self):
    """Check if the path exists."""
    return super().exists()

  def get_stem(self):
    """Return the stem of the file or directory (filename without extension)."""
    return self.stem

  def get_name(self):
    """Return the name of the file or directory."""
    return self.name

  def search(self, pattern="**"):
    return self.glob(pattern)

  type_ext = search
  ext_type = search
  file_type = search

  def get_size(self, converter=None):
    """Return the size of the file or directory."""

    if self.is_file():
      self._size = self.stat().st_size
    elif self.is_dir():
      self._size = sum(f.stat().st_size for f in self.rglob('*') if f.is_file())
    else:
      raise ValueError(f"{self} is neither a file nor a directory.")

    if not converter is None and callable(converter):
      return converter(self._size)

    return self._size

  _size = None

  @property
  def size(self):
    if self._size is None:
      self._size = self.get_size()

    return self._size

  def parent(self, level=0):
    """Return the parent directory."""
    return EntityPath(self.parents[level])

  @property
  def full_path(self):
    """Return the absolute path."""
    return str(self.resolve())

  def rel_path(self, _path=None):
    """Return the relative path from the current working directory."""
    try:
      return (self).resolve().relative_to(_path or Path.cwd())
    except:
      return self

  def has(self, file=None):
    """Case sensitive check if pattern (e.g., **/file.txt; *ile.tx*) exists"""
    return len(list(self.search(file))) > 0

  contains = has
  has_file = has
  has_dir = has

  def lower(self):
    return str(self).lower()

  def upper(self):
    return str(self).upper()

  def __add__(self, what=''):
    return self / what

  _stats = None

  @property
  def stats(self):
    if self._stats is None:
      self.get_stats()
    return self._stats

  def get_stats(self):
    self._stats = OS.stat(str(self))
    return self._stats

  @property
  def permission(self):
    return oct(self.stats.st_mode)

  mode = permission

  @property
  def created(self):
    return TIME.ctime(self.stats.st_ctime)

  @property
  def accessed(self):
    return TIME.ctime(self.stats.st_atime)

  @property
  def updated(self):
    return TIME.ctime(self.stats.st_mtime)

  modified = updated
