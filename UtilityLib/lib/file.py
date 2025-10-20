from .path import EntityPath
from typing import Any, Dict, List, Optional, Union
import json
import os
import shutil
import time
import toml
import yaml
import pandas as pd

class EntityFile(EntityPath):
  """EntityFile:
    Comprehensive file operations class handling various file types and operations.
  """

  # Default paths and settings
  default_backup_dir: str = "~/.utilitylib/backups"
  supported_formats: List[str] = ['json', 'yaml', 'toml', 'csv', 'xlsx', 'parquet', 'txt', 'xml', 'html']

  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  def __del__(self):
    """Cleanup when EntityFile is destroyed."""
    if hasattr(self, '_schedule_manager'):
      self.stop_monitoring()

  # ================================
  # File Permissions and Access Control
  # ================================

  def set_permissions(self, mode: int) -> bool:
    """Set file permissions."""
    if self.exists():
      os.chmod(str(self), mode)
      return True
    return False

  def get_permissions(self) -> str:
    """Get file permissions."""
    if self.exists():
      return oct(self.stat().st_mode)[-3:]
    return ""

  @property
  def is_readable(self) -> bool:
    """Check if file is readable."""
    return os.access(str(self), os.R_OK)

  @property
  def is_writable(self) -> bool:
    """Check if file is writable."""
    return os.access(str(self), os.W_OK)

  @property
  def is_executable(self) -> bool:
    """Check if file is executable."""
    return os.access(str(self), os.X_OK)

  has_R = is_readable
  has_W = is_writable
  has_X = is_executable

  # ================================
  # File Conversions
  # ================================

  def _toml_map_from_str(self, data: Any) -> Any:
    """Helper for TOML processing."""
    if isinstance(data, dict):
      return {k: self._toml_map_from_str(v) for k, v in data.items()}
    elif isinstance(data, list):
      return [self._toml_map_from_str(v) for v in data]
    elif data == "":
      return None
    return data

  def read_json(self, **kwargs) -> Any:
    """Read JSON file."""
    return json.loads(self.read_text(encoding=kwargs.get('encoding', 'utf-8')))

  def write_json(self, data: Any, indent: int = 2, **kwargs) -> bool:
    """Write data to JSON file."""
    self.write_text(json.dumps(data, indent=indent), encoding=kwargs.get('encoding', 'utf-8'))
    return True

  def read_yaml(self, **kwargs) -> Any:
    """Read YAML file."""
    return yaml.safe_load(self.read_text(encoding=kwargs.get('encoding', 'utf-8')))

  def write_yaml(self, data: Any, **kwargs) -> bool:
    """Write data to YAML file."""
    self.write_text(yaml.dump(data), encoding=kwargs.get('encoding', 'utf-8'))
    return True

  def read_toml(self, **kwargs):
    """Read TOML file."""
    _raw = toml.loads(self.read_text(encoding=kwargs.get('encoding', 'utf-8')))
    return self._toml_map_from_str(_raw)

  def write_toml(self, data: Dict[str, Any], **kwargs) -> bool:
    """Write data to TOML file."""
    self.parent().validate()
    self.write(toml.dumps(data), encoding=kwargs.get('encoding', 'utf-8'))
    return True

  def read_csv(self, **kwargs) -> Any:
    """Read CSV file using pandas."""
    return pd.read_csv(str(self), **kwargs)

  def write_csv(self, data: Any, **kwargs) -> bool:
    """Write data to CSV file."""
    self.parent().validate()
    data.to_csv(str(self), **kwargs)
    return True

  def read_excel(self, **kwargs) -> Any:
    """Read Excel file."""
    return pd.read_excel(str(self), **kwargs)

  def write_excel(self, data: Any, **kwargs) -> bool:
    """Write data to Excel file."""
    self.parent().validate()
    data.to_excel(str(self), **kwargs)
    return True

  def read_parquet(self, **kwargs) -> Any:
    """Read Parquet file."""
    return pd.read_parquet(str(self), **kwargs)

  def write_parquet(self, data: Any, **kwargs) -> bool:
    """Write data to Parquet file."""
    self.parent().validate()
    data.to_parquet(str(self), **kwargs)
    return True

  def parse_html(self, markup: str, parser: str = 'html.parser'):
    """Parse HTML using BeautifulSoup.

    Args:
        markup: HTML markup to parse
        parser: Parser to use ('html.parser', 'lxml', 'html5lib')

    Returns:
        BeautifulSoup object
    """
    try:
      from bs4 import BeautifulSoup
      return BeautifulSoup(markup, parser)
    except ImportError:
      raise ImportError("BeautifulSoup4 is required for HTML parsing. Install with: pip install beautifulsoup4")

  def read_html(self, **kwargs) -> Any:
    """Read and parse HTML file.

    Args:
        **kwargs: Additional arguments for parsing (parser, encoding, etc.)

    Returns:
        Parsed HTML content
    """
    parser   = kwargs.pop('parser', 'html.parser')
    encoding = kwargs.pop('encoding', 'utf-8')
    content  = self.read_text(encoding=encoding)
    return self.parse_html(content, parser=parser)

  def read_xml(self, **kwargs) -> Any:
    """Read and parse XML file.

    Args:
        **kwargs: Additional arguments for parsing

    Returns:
        Parsed XML content as dictionary
    """
    try:
      from lxml import etree as XMLTree
      tree = XMLTree.parse(str(self))
      root = tree.getroot()
      return self.xml_to_dict(root)
    except ImportError:
      raise ImportError("lxml is required for XML parsing. Install with: pip install lxml")

  def write_xml(self, content: str, encoding: str = 'utf-8', **kwargs) -> bool:
    """Write XML content to file.

    Args:
        content: XML content to write
        encoding: Text encoding
        **kwargs: Additional arguments

    Returns:
        True if successful
    """
    self.write_text(content, encoding=encoding, **kwargs)
    return True

  def xml_to_dict(self, data: Any) -> Dict[str, Any]:
    """Convert XML to dictionary.

    Args:
        data: XML data (string or ElementTree element)

    Returns:
        Dictionary representation of XML
    """
    try:
      import xmltodict
      from lxml import etree as XMLTree

      if not isinstance(data, str):
        data = XMLTree.tostring(data, encoding='utf8', method='xml').decode('utf8')

      return xmltodict.parse(data)
    except ImportError:
      raise ImportError("xmltodict and lxml are required for XML processing. Install with: pip install xmltodict lxml")

  # ================================
  # File Metadata Handling
  # ================================

  def get_metadata(self) -> Dict[str, Any]:
    """Get file metadata."""
    if not self.exists():
      return {}

    stat = self.stat()
    return {
      'size'       : stat.st_size,
      'created'    : time.ctime(stat.st_ctime),
      'modified'   : time.ctime(stat.st_mtime),
      'accessed'   : time.ctime(stat.st_atime),
      'permissions': oct(stat.st_mode)[-3:],
      'extension'  : self.suffix,
      'name'       : self.name,
      'path'       : str(self)
    }

  # ================================
  # File Validation and Integrity Checks
  # ================================

  def validate_integrity(self, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """Validate file integrity using hash."""
    return self.get_hash(algorithm) == expected_hash

  def compare(self, other: Union[str, 'EntityFile'], **kwargs) -> Optional[bool]:
    """
    Compare this file with another file.

    Args:
      other: Path to other file or EntityFile object to compare with
      **kwargs: Additional arguments for specific comparison types

    Returns:
      True|False if files are considered equal based on comparison_type
      None if either file does not exist
    """
    if isinstance(other, str):
      other = EntityFile(other)

    if not all([self.exists(), other.exists()]):
      return None

    return self.hash == other.hash

  # ================================
  # File Versioning and Backup
  # ================================

  def create_backup(self, backup_name: Optional[str] = None) -> EntityPath:
    """Create a backup of the file."""
    if not self.exists():
      raise FileNotFoundError(f"File {self} does not exist")

    if backup_name is None:
      timestamp = time.strftime("%Y%m%d_%H%M%S")
      backup_name = f"{self.stem}_backup_{timestamp}{self.suffix}"

    backup_path = self.backup_dir / backup_name
    backup_path.parent.validate()
    shutil.copy2(str(self), str(backup_path))
    return backup_path

  def list_backups(self) -> List[EntityPath]:
    """List all backups for this file."""
    pattern = f"{self.stem}_backup_*{self.suffix}"
    return list(self.backup_dir.search(pattern))

  # ================================
  # File Compression and Decompression
  # ================================

  def compress(self, archive_format: str = 'zip', **kwargs) -> EntityPath:
    """Compress file."""
    archive_path = self.with_suffix(f'.{archive_format}')
    self.parent().validate()

    if archive_format == 'zip':
      with shutil.ZipFile(archive_path, 'w') as zipf:
        zipf.write(str(self), self.name)
    elif archive_format == 'tar':
      with shutil.TarFile(archive_path, 'w') as tarf:
        tarf.add(str(self), self.name)

    return archive_path

  def decompress(self, extract_to: Optional[EntityPath] = None, **kwargs) -> EntityPath:
    """Decompress file."""
    if extract_to is None:
      extract_to = self.parent

    extract_to.validate()

    if self.suffix == '.zip':
      with shutil.ZipFile(str(self), 'r') as zipf:
        zipf.extractall(str(extract_to))
    elif self.suffix in ['.tar', '.tar.gz', '.tar.bz2']:
      with shutil.TarFile(str(self), 'r') as tarf:
        tarf.extractall(str(extract_to))

    return extract_to

  # ================================
  # File Monitoring and Change Detection
  # ================================

  def monitor_changes(self, callback: callable, interval: int = 1) -> Any:
    """Monitor file for changes using ScheduleManager."""
    if not callable(callback):
      raise ValueError("Callback must be callable")

    # Store last_modified in instance to avoid closure issues
    self._last_modified = self.stat().st_mtime if self.exists() else 0

    def check_changes():
      if self.exists():
        current_modified = self.stat().st_mtime
        if current_modified != self._last_modified:
          try:
            callback(self)
          except Exception as e:
            print(f"Error in file change callback: {e}")
          self._last_modified = current_modified

    # Use ScheduleManager for monitoring
    # Import ScheduleManager
    from .schedule import ScheduleManager

    # Create a ScheduleManager instance if not exists
    if not hasattr(self, '_schedule_manager'):
      self._schedule_manager = ScheduleManager(autostart=True)

    # Schedule the check function
    event = self._schedule_manager.add(
      check_changes,
      interval=interval,
      unit='seconds',
      name=f"file_monitor_{self.name}_{id(self)}"
    )

    return event  # Return the ScheduleEvent for control

  def stop_monitoring(self, event: Optional[Any] = None) -> bool:
    """Stop file monitoring."""
    if hasattr(self, '_schedule_manager'):
      if event:
        # Stop specific event
        event.stop()
      else:
        # Stop all monitoring for this file
        for ev_name, ev in self._schedule_manager.events.items():
          if f"file_monitor_{self.name}" in ev_name:
            ev.stop()
      return True
    return False

  def list_monitors(self) -> List[Any]:
    """List active file monitors for this file."""
    monitors = []
    if hasattr(self, '_schedule_manager'):
      for ev_name, ev in self._schedule_manager.events.items():
        if f"file_monitor_{self.name}" in ev_name:
          monitors.append(ev)
    return monitors
