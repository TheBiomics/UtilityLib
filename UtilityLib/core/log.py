from .time import TimeUtility
import logging as _Logging
from ..lib.entity import EntityPath

class _ColoredFormatter(_Logging.Formatter):
  BLACK = '\x1b[30m'
  BLUE = '\x1b[34m'
  CYAN = '\x1b[36m'
  GREEN = '\x1b[32m'
  MAGENTA = '\x1b[35m'
  RED = '\x1b[31m'
  RESET = '\x1b[39m'
  WHITE = '\x1b[37m'
  YELLOW = '\x1b[33m'
  RESET_ALL = '\x1b[0m'
  INVERT_START = '\033[7m'
  INVERT_END = '\033[27m'

  COLORS = {
    'DEBUG': 'BLUE',
    'INFO': 'WHITE',
    'WARNING': 'YELLOW',
    'ERROR': 'RED',
    'CRITICAL': 'MAGENTA',
  }

  def format(self, record):
    _log_color = getattr(self, self.COLORS.get(record.levelname, 'WHITE'), self.WHITE)
    _log_msg = super().format(record)
    _format = f"{_log_color}{_log_msg}{self.RESET_ALL}"
    _invert_format = f"{self.INVERT_START}{_log_color}{_log_msg}{self.RESET_ALL}{self.INVERT_END}"
    return _format

class LoggingUtility(TimeUtility):
  log_type = "info"
  log_file_name = "UtilityLib.log"
  log_file_path = None
  log_to_file = True
  log_to_console = True
  def __init__(self, *args, **kwargs):
    __defaults = {
        "last_message": None,
        "log_table_name": "ul_watchdog",
      }

    __defaults.update(kwargs)
    super().__init__(**__defaults)

    self.set_logging(**__defaults)
    # self._set_file_log_handler()

  LogHandler = None
  log_level = 'DEBUG'

  def _set_console_log_handler(self, *args, **kwargs):
    """Set Console Log Handler"""
    if not self.log_to_console is True:
      return

    _log_level = _Logging.DEBUG
    if isinstance(self.log_level, (str)):
      self.log_level = self.log_level.upper()
      _log_level = getattr(_Logging, self.log_level, _log_level)
    elif isinstance(self.log_level, (int)):
      _log_level = self.log_level

    _ch = _Logging.StreamHandler()
    _ch.setLevel(_log_level)
    _fmt = _ColoredFormatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    _ch.setFormatter(_fmt)

    self.LogHandler.addHandler(_ch)

  def _set_file_log_handler(self, *args, **kwargs):
    """Set File Log Handler and Log Everything"""
    if not self.log_to_file is True:
      return

    if not self.log_file_path is None:
      _fh = _Logging.FileHandler(self.log_file_path)
      _fh.setLevel(_Logging.DEBUG)

      _fmt = _Logging.Formatter('|%(asctime)s\t|%(name)s\t|%(levelname)s\t|%(message)s')
      _fh.setFormatter(_fmt)
      self.LogHandler.addHandler(_fh)

  def set_logging(self, *args, **kwargs):
    """Logging Setup"""

    if self.log_file_path is None:
      self.log_file_path = EntityPath(self.log_file_name)

    if not any([self.log_to_console, self.log_to_file]):
      return

    self.LogHandler = _Logging.getLogger(self.name)
    self.LogHandler.setLevel(_Logging.DEBUG)

    if self.LogHandler.hasHandlers:
      for _h in list(self.LogHandler.handlers):
        self.LogHandler.removeHandler(_h)

    self._set_console_log_handler()
    self._set_file_log_handler()

  def __log(self, *args, **kwargs):
    _log_type = kwargs.pop('log_type', args[1] if len(args) > 1 else self.log_type)
    _message = kwargs.pop('text', args[0] if len(args) > 0 else "EMPTY MESSAGE")

    if self.LogHandler is None:
      self.set_logging()

    if not self.LogHandler is None:
      _lh = getattr(self.LogHandler, _log_type)
      if _lh:
        _lh(_message)
      else:
        print(_message)

  def log_debug(self, *args, **kwargs):
    kwargs.update({"log_type": "debug"})
    return self.__log(*args, **kwargs)

  debug = log_debug

  def log_info(self, *args, **kwargs):
    kwargs.update({"log_type": "info"})
    return self.__log(*args, **kwargs)

  info = log_info
  log_success = log_info

  def log_warning(self, *args, **kwargs):
    kwargs.update({"log_type": "warning"})
    return self.__log(*args, **kwargs)

  warning = log_warning

  def log_error(self, *args, **kwargs):
    kwargs.update({"log_type": "error"})
    return self.__log(*args, **kwargs)

  error = log_error

  def log_critical(self, *args, **kwargs):
    kwargs.update({"log_type": "critical"})
    return self.__log(*args, **kwargs)

  log_fail = log_critical
  emergency = log_critical
