from pathlib import Path

class EntityPath(Path):
  _flavour = Path('.')._flavour
  prevent_delete = True
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  def __init__(self, *args, **kwargs):
    str.__init__(self)

  def __len__(self):
    return len(str(self))

  def __str__(self):
    return super().__str__()

  def _read_file(self, _method=None):
    """Read the text from the file.
      0|method: Custom method/function to read the file
    """
    if not self.is_file():
      raise ValueError(f"{self} is not a file.")
    if not _method is None:
      return _method(str(self))
    return super().read_text()

  read_text = _read_file
  read = _read_file

  def write_text(self, data):
    """Write the given text to the file."""
    if self.exists() and not self.is_file():
      raise ValueError(f"{self} is not a file.")
    return super().write_text(data)

  write = write_text

  def list_files(self):
    """List all files in the directory."""
    if not self.is_dir():
      raise ValueError(f"{self} is not a directory.")
    return [EntityPath(_f) for _f in self.iterdir() if _f.is_file()]

  _files = list_files
  files = list_files

  def list_dirs(self):
    """List all directories in the directory."""
    if not self.is_dir():
      raise ValueError(f"{self} is not a directory.")
    return [EntityPath(_d) for _d in self.iterdir() if _d.is_dir()]

  dirs = list_dirs
  _dirs = list_dirs
  folders = list_dirs

  def list_items(self):
    """List all items (files and directories) in the directory."""
    if not self.is_dir():
      raise ValueError(f"{self} is not a directory.")
    return [EntityPath(_i) for _i in self.iterdir()]

  items = list_items

  def delete(self):
    """Delete the file or directory."""
    if self.prevent_delete:
      raise ValueError(f"{self} has prevent_lock attribute to prevent accidental deletion so cannot be deleted.")

    if self.is_file():
      self.unlink()
    elif self.is_dir():
      for _item in self.iterdir():
        if _item.is_dir():
          EntityPath(_item).delete()
        else:
          _item.unlink()
      self.rmdir()
    else:
      raise ValueError(f"{self} is neither a file nor a directory.")

  def move(self, target):
    """Move the file or directory to a new location."""
    if self.prevent_delete:
      return
    import shutil as _SHUTIL
    _SHUTIL.move(str(self), str(target))
    return EntityPath(target)

  def copy(self, _destination):
    """Copy the file or directory to a new location."""
    import shutil as _SHUTIL

    _target_path = EntityPath(_destination)
    if not _target_path.parent().exists():
      _target_path.parent().mkdir(parents=True, exist_ok=True)
    if self.is_file():
      _SHUTIL.copy(str(self), str(_target_path))
    elif self.is_dir():
      _SHUTIL.copytree(str(self), str(_target_path))
    return _target_path

  def exists(self):
    """Check if the path exists."""
    return super().exists()

  def get_stem(self):
    """Return the stem of the file or directory (filename without extension)."""
    return self.stem

  def get_name(self):
    """Return the name of the file or directory."""
    return self.name

  def search(self, _pattern="**"):
    return self.glob(_pattern)

  def size(self, _unit=None):
    """Return the size of the file or directory."""
    if self.is_file():
      return self.stat().st_size
    elif self.is_dir():
      return sum(f.stat().st_size for f in self.rglob('*') if f.is_file())
    else:
      raise ValueError(f"{self} is neither a file nor a directory.")

  def parent(self, _level=0):
    """Return the parent directory."""
    return EntityPath(self.parents[_level])

  def full_path(self):
    """Return the absolute path."""
    return str(self.resolve())

  def rel_path(self, _path=None):
    """Return the relative path from the current working directory."""
    return str(self.relative_to(_path or Path.cwd()))

  def has(self, _file=None):
    """Case sensitive check if pattern (e.g., **/file.txt; *ile.tx*) exists"""
    return len(self.search(_file)) > 0

  contains = has
  has_file = has
  has_dir = has

  def lower(self):
    return str(self).lower()

  def upper(self):
    return str(self).upper()

  def __add__(self, _what=''):
    return self / _what
