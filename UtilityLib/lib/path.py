from pathlib import Path
import os as OS
from itertools import islice
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from .file import EntityFile

class EntityPath(Path):
  """
    An extension of Python's built-in `Path` class to simplify and enhance file and directory handling.

    Key Features:
    --------------
    1. **Extended Operators**: Implements custom operators (`//`, `%`, `-`, `+`) for intuitive path manipulation.
        - `//` (Floor division): Splits the path into segments based on integer or string input.
        - `%` (Modulo): Allows dynamic string formatting within paths.
        - `-` (Subtraction): Removes segments from the path, either by an index or up to a matching string.
        - `+` (Addition): Concatenates new path components easily.

    2. **Search and Match**: Provides methods for pattern matching and file type identification.
        - Methods like `search`, `has`, and `get_match` allow users to quickly find files or directories using flexible patterns.

    3. **File and Directory Operations**: Simplifies common filesystem tasks like reading, writing, moving, copying, and deleting files or directories.
        - Methods for safely deleting files (`delete` with `is_protected`).
        - List all files, directories, or both using `list_files`, `list_dirs`, or `list_items`.
        - Quick read/write utilities like `read_text`, `write_text`, `head`, and `tail` for file content manipulation.

    4. **Metadata and Stats**: Efficiently retrieve file or directory metadata.
        - Properties like `size`, `permission`, `created`, `updated`, and `hash` provide quick access to key attributes.
        - Comprehensive stat retrieval via `stats` for access, modification, and creation times.

    5. **Compression Detection**: Automatically detect if a file is compressed, based on file extension (`is_gz`).

    6. **Path Formatting**: Methods like `rel_path`, `parent`, and `full_path` make it easy to convert paths to relative, parent, or absolute forms.

    Additional Utilities:
    ---------------------
    - `validate`: Creates the file or directory if it doesn't exist.
    - `move` and `copy`: Move or copy files and directories to new locations with automatic parent directory creation if necessary.
    - `get_hash`: Calculate file or directory hash using common algorithms like `sha256` and `md5` for integrity checks.

    This class is designed to make filesystem operations more intuitive and reduce repetitive boilerplate code, improving readability and efficiency in path manipulation tasks.
  """

  _flavour = Path('.')._flavour

  def __new__(cls, *args, **kwargs) -> None:
    # Filter out None and empty arguments properly
    _valid_args = [
      str(arg)
      for arg in args
      if arg is not None and str(arg).strip()
    ] or ['.']
    _valid_args[0] = str(Path(_valid_args[0]).expanduser().resolve())
    return super().__new__(cls, *_valid_args, **kwargs)

  def len(self):
    return len(str(self))

  __len__ = len

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
    Path.is_absolute
    Path.resolve
    """
    help(self)

  _is_gz = None

  @property
  def is_gz(self):
    if self._is_gz is None:
      self._is_gz = '.gz' in self.suffixes

    return self._is_gz

  is_compressed = is_gz

  @property
  def has_gz(self):
    if self.is_gz:
      return True

    return (self + '.gz').exists()

  @property
  def ext(self):
    """None if current path is a directory."""
    if self.is_dir():
      return None

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

  def _read_lines(self, num_lines=None, strip_nl=False):
    if not self.is_file():
      raise ValueError(f"{self} is not a file.")

    try:
      if num_lines is None:
        with self.open() as _f:
          for _line in _f:
            yield _line.strip('\n') if strip_nl else _line
      else:
        with self.open() as _f:
          for _ in range(int(num_lines)):
            yield next(_f)

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

    while len(_res_lines) < lines:
      try:
        _fh.seek(_block_counter * buffer_size, OS.SEEK_END)
      except IOError:
        # either file is too small, or too many lines requested
        _fh.seek(0)
        break

      _block_counter -= 1

    _res_lines = _fh._read_lines()
    return _res_lines[-lines:]

  def _read_file(self, method=None, **kwargs):
    """Read the text from the file.
      0|method: Custom method/function to read the file
    """
    if not self.is_file():
      raise ValueError(f"{self} is not a file.")

    if callable(method):
      return method(str(self), **kwargs)

    return super().read_text(**kwargs)

  read_text = _read_file
  read = _read_file

  @property
  def text(self):
    return self._read_file()

  def write_text(self, data, mode="a", encoding="utf-8"):
    """Write the given text to the file."""
    self.parent().validate()  # Ensure directory exists
    if self.exists() and not self.is_file():
      raise ValueError(f"{self} is not a file.")

    with self.open(mode, encoding=encoding) as _f:
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
        # Lazy import to avoid circular imports
        from .file import EntityFile
        _fp = EntityFile(_f)
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


  _items = None
  def list_items(self):
    """List all items (files and directories) in the directory."""
    if not self.is_dir():
      raise ValueError(f"{self} is not a directory.")

    self._items = []
    for _i in self.iterdir():
      if _i.is_file():
        # Lazy import to avoid circular imports
        from .file import EntityFile
        self._items.append(EntityFile(_i))
      else:
        self._items.append(EntityPath(_i))
    return self._items

  @property
  def items(self):
    self.list_items()
    return self._items

  def __getitem__(self, idx):
    """Get item by index."""
    return self.items[idx]

  def __getitem__(self, idx):
    """Get item by index."""
    return self.items[idx]

  entities = items
  _all = items

  _discovered_dirs = []

  @property
  def list_sub_dirs(self):
    if not self._discovered_dirs:
      list(self._discover_dirs())
    return self._discovered_dirs

  list_subdirs = list_sub_dirs
  subdirs = list_sub_dirs

  @property
  def walk_dirs(self):
    return self._discover_dirs()

  def _discover_dirs(self, directory=None):
    """
    Recursively discovers directories and populates self._discovered_dirs.
    """
    if directory is None:
      directory = str(self)
    else:
      directory = str(directory)

    try:
      for dirpath, dirnames, filenames in OS.walk(directory):
        ep = EntityPath(dirpath)
        self._discovered_dirs.append(ep)
        yield ep
    except Exception as e:
      print(f"Exception: {e}")

  _discovered_files = None

  @property
  def list_sub_files(self):
    if not self._discovered_files:
      self._discovered_files = []
      list(self._discover_files())
    return self._discovered_files

  list_subfiles = list_sub_files
  subfiles = list_sub_files

  @property
  def walk_files(self):
    return self._discover_files()

  def _discover_files(self, *args, **kwargs):
    self._discovered_files = []
    try:
      for dirpath, dirnames, filenames in OS.walk(str(self)):
        for filename in filenames:
          # Lazy import to avoid circular imports
          from .file import EntityFile
          file_path = EntityFile(dirpath) / filename
          self._discovered_files.append(file_path)
          yield file_path
    except Exception as e:
      print(f"Exception: {e}")

  is_protected = True
  def delete(self, is_protected=None):
    self.is_protected = is_protected if not is_protected is None else self.is_protected

    """Delete the file or directory."""
    if self.is_protected:
      raise ValueError(f"{self} is not safe to delete. pass is_protected=False enable accidental deletion.")

    if self.is_file():
      self.unlink()
      return self.exists()
    elif self.is_dir():
      for _item in self.iterdir():
        if _item.is_dir():
          EntityPath(_item).delete(is_protected=self.is_protected)
        else:
          _item.unlink()
      self.rmdir()
      return self.exists()
    elif not self.exists():
      # Already deleted or didn't exist
      return self.exists()
    else:
      raise ValueError(f"{self} is neither a file nor a directory.")

  def validate(self):
    """Make directory/file if doesn't exist."""

    if self.exists():
      return self
    elif len(self.suffixes) > 0:
      # Assuming it is a file
      self.resolved().parent().mkdir(parents=True, exist_ok=True)
      self.touch()
    else:
      Path(str(self.resolved())).mkdir(parents=True, exist_ok=True)

    return self

  def move(self, destination):
    """Move the file or directory to a new location."""
    if self.is_protected:
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
    return str(self.expanduser().resolve())

  def resolved(self):
    """Return the absolute path."""
    return self.expanduser().resolve()

  def rel_path(self, _path=None):
    """Return the relative path from the current working directory."""
    try:
      return (self.full_path).relative_to(_path or Path.cwd())
    except:
      return self

  def has(self, file=None):
    """Case sensitive check if pattern (e.g., **/file.txt; *ile.tx*) exists"""
    return len(list(self.search(file))) > 0

  contains = has
  has_file = has
  has_dir = has

  def _has_extension(self, ext=None):
    if ext is None:
      return bool(self.suffix) and not self.is_dir()

    return ext in self.suffixes

  has_ext = _has_extension
  has_suffix = _has_extension

  def lower(self):
    return str(self).lower()

  def upper(self):
    return str(self).upper()

  _stats = None

  @property
  def stats(self):
    if self._stats is None:
      self.get_stats()

    _stats_dict = {k.replace('st_', ''): getattr(self._stats, k) for k in dir(self._stats) if k.startswith('st_')}
    return _stats_dict

  def get_stats(self):
    self._stats = OS.stat(str(self))
    return self._stats

  @property
  def permission(self):
    return oct(self.stats.st_mode)

  mode = permission

  @property
  def created(self):
    return self.stats.st_ctime

  @property
  def accessed(self):
    """Provides accessed time (timestamp) during run time"""
    self.get_stats()
    return self._stats.st_atime

  @property
  def updated(self):
    """Provides update time (timestamp) during run time"""
    self.get_stats()
    return self._stats.st_mtime

  modified = updated

  def __contains__(self, item):
    return item in self.parts

  def __add__(self, what=''):
    return EntityPath((self.full_path) + str(what))

  def __mod__(self, *args):
    """Modulo operand operation on EntityPath"""

    try:
      return EntityPath(self.full_path % args)
    except TypeError as _e:
      print(f"TypeError: Incorrect format argument passed: {_e}")
      return None
    except ValueError as _e:
      print(f"ValueError: Value mismatch in format: {_e}")
      return None
    except Exception as _e:
      print(f"Unexpected error occurred: {_e}")
      return None

  def __call__(self, *args, **kwargs):
    """ToDo: Call operator to perform open file or directory."""

  # def __iter__(self):
  #   """Iterates through entities in the directory"""
  #   for _item in self.items:
  #     yield _item

  def __floordiv__(self, what):
    """Flood Division (// operator) to return based on str or int"""
    if isinstance(what, (int, float)):
      what = int(what)
      try:
        _path_segments = self.parts[:what]
        _remainder_segments = self.parts[what:]
        return EntityPath(*_path_segments)
      except Exception as e:
        print(f"Error occurred during path division: {e}")
        return None
    elif isinstance(what, str):
      try:
        _guess_full_segment = [*filter(lambda _x: what in _x or what in _x, self.parts)]
        _idx = self.parts.index(_guess_full_segment[0]) # Consider first part only
        _rel_path = self.relative_to(*self.parts[:_idx])
        return EntityPath(_rel_path)
      except ValueError:
        print(f"Error: '{what}' not found in path.")
        return None
      except Exception as e:
        print(f"Error occurred while processing string input: {e}")
        return None
    else:
      raise TypeError("Unsupported operand type for //: must be 'int' or 'str'")

  def __sub__(self, what):
    """Subtraction operator (-) for removing segments from a path."""
    if isinstance(what, (int, float)):
      what = int(what)
      try:
        # If integer, remove the last `what` segments from the path
        if what > 0:
          _remaining_segments = self.parts[:-what]
          return EntityPath(*_remaining_segments)
        else:
          raise ValueError("Integer input must be greater than zero.")
      except Exception as e:
        print(f"Error during path subtraction with int: {e}")
        return None

    elif isinstance(what, (str, EntityPath)):
      what = str(what)
      try:
        # If string, remove all leading segments including the match
        _guess_full_segment = [*filter(lambda _x: what in _x or what in _x, self.parts)]
        _idx = self.parts.index(_guess_full_segment[0])
        _remaining_segments = self.parts[_idx + 1:]
        return EntityPath(*_remaining_segments)
      except ValueError:
        print(f"Error: '{what}' not found in path.")
        return None
      except Exception as e:
        print(f"Error during path subtraction with string: {e}")
        return None

    else:
      raise TypeError("Unsupported operand type for -: must be 'int' or 'str'")

  def __enter__(self):
    """
    Context manager entry:
    Temporarily changes the current working directory to the location of the path (parent for files, the directory itself for directories), and yields the opened file object for files or the path for directories.
    Usage:
      with EntityPath('file.txt') as f:
          # cwd changed to parent of file.txt
          for line in f:
              ...
      with EntityPath('dir/') as p:
          # cwd changed to dir/
          print('Current working directory:', p)
    """
    return self._CwdContext(self)

  def __exit__(self, exc_type, exc_val, exc_tb):
    pass

  class _CwdContext:
    """Context manager for temporarily changing the current working directory."""
    def __init__(self, path):
      self.path = path
      self._original_cwd = None

    def __enter__(self):
      self._original_cwd = OS.getcwd()
      if self.path.is_file():
        OS.chdir(str(self.path.parent()))
        self._context_file = self.path.open()
        return self._context_file
      elif self.path.is_dir():
        OS.chdir(str(self.path))
        return self.path
      else:
        return iter([])

    def __exit__(self, exc_type, exc_val, exc_tb):
      if hasattr(self, '_context_file'):
        self._context_file.close()
        del self._context_file
      if self._original_cwd:
        OS.chdir(self._original_cwd)



  space =  '    '
  branch = '│   '
  tee =    '├── '
  last =   '└── '

  def tree_gen(self, level: int = -1, limit_to_directories: bool = False):
    """Yield the tree structure lazily, line by line."""
    dir_path = Path(self)
    files = 0
    directories = 0

    def inner(dir_path: Path, prefix: str = "", level=-1):
      nonlocal files, directories
      if not level:
        return
      contents = (
        [d for d in dir_path.iterdir()]
        if not limit_to_directories
        else [d for d in dir_path.iterdir() if d.is_dir()]
      )
      pointers = [EntityPath.tee] * (len(contents) - 1) + [EntityPath.last]
      for pointer, path in zip(pointers, contents):
        if path.is_dir():
          directories += 1
          yield prefix + pointer + path.name
          extension = (
            EntityPath.branch
            if pointer == EntityPath.tee
            else EntityPath.space
          )
          yield from inner(path, prefix=prefix + extension, level=level - 1)
        elif not limit_to_directories:
          files += 1
          yield prefix + pointer + path.name

    yield dir_path.name
    yield from inner(dir_path, level=level)
    yield f"\n{directories} directories" + (f", {files} files" if files else "")

  def tree(self, level: int = -1, limit_to_directories: bool = False,
    length_limit: int = 1000, to_file: str = None ) -> str:
    """
    Return a visual tree structure of a directory.
    Optionally save the result to a file.
    """
    iterator = self.tree_gen(level=level, limit_to_directories=limit_to_directories)
    lines = list(islice(iterator, length_limit))

    # Check if more lines exist
    if next(iterator, None):
      lines.append(f"... length_limit, {length_limit}, reached")

    result = "\n".join(lines)

    if to_file:
      Path(to_file).write_text(result, encoding="utf-8")

    return result
