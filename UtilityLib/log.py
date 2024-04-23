from .db import DatabaseUtility

class LoggingUtility(DatabaseUtility):
  _terminal_bg_colors = {
      "black": 40,
      "red": 41,
      "green": 42,
      "yellow": 43,
      "blue": 44,
      "magenta": 45,
      "cyan": 46,
      "white": 47,
    }

  _terminal_fg_colors = {
      "black": 30,
      "red": 31,
      "green": 32,
      "yellow": 33,
      "blue": 34,
      "magenta": 35,
      "cyan": 36,
      "white": 37,
    }

  _terminal_text_styles = {
      "regular": 0,
      "bold": 1,
      "low_intensity": 2,
      "italic": 3,
      "underline": 4,
      "blink": 5,
      "reverse": 6,
      "background": 7,
      "invisible": 8,
    }

  print_log = True
  step_log = False
  step_pause = False

  def __init__(self, *args, **kwargs):
    self.__defaults = {
        "log_type": "info",
        "last_message": None,
        "log_file_path": ".",
        "log_file_name": "app-process.log",
        "log_table_name": "db_watchdog",
        "log_status": {
            "success": LoggingUtility._highlight_terminal_text("[SUCCESS]", "black", 'green'),
            "info": LoggingUtility._highlight_terminal_text("[INFO]", "black", 'cyan'),
            "debug": LoggingUtility._highlight_terminal_text("[DEBUG]", "black", 'magenta', text_style="italic"),
            "warning": LoggingUtility._highlight_terminal_text("[WARNING]", "black", 'yellow'),
            "fail": LoggingUtility._highlight_terminal_text("[FAIL]", "black", 'red', text_style="blink"),
            "error": LoggingUtility._highlight_terminal_text("[ERROR]", "black", 'red'),
          },
      }

    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)
    self.set_logging(**self.__defaults)
    self.require_many([("pandas", "PD"), ("textwrap", "TextWrapper")])

  @staticmethod
  def _highlight_terminal_text(text, bg_color="blue", fg_color="white", text_style="regular", placeholder_size=11):
    bg_color_code = LoggingUtility._terminal_bg_colors.get(bg_color, 4)
    fg_color_code = LoggingUtility._terminal_fg_colors.get(fg_color, 37)
    text_style_code = LoggingUtility._terminal_text_styles.get(text_style, 0)
    placeholder_size_fs = f">{placeholder_size}"

    if False:
      return f"\033[0m\033[0;{fg_color_code}m\033[{text_style_code};{bg_color_code}m{text:>10}\033[0m"

    return f"\033[{text_style_code};{fg_color_code}m{text:>10}\033[0m"

  def __log(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    _wrap_message = kwargs.get("log_wrap", True)
    _db_log = []
    _log_type = kwargs.get('log_type', self.log_type)

    for _message in args:
      if self.print_log == True:
        _print_msg = f"{self.log_status[_log_type]} [{self.time_elapsed()}] {str(_message)}"
        if _wrap_message:
          _print_msg = self.TextWrapper.fill(_print_msg, width=80, subsequent_indent=" "*11)

        _log = getattr(self.LOGGER, _log_type, 'info')
        _log(_print_msg)

      _db_log.append({
        "type": _log_type,
        "message": str(_message),
        "time": self.time_get()
      })

    _db_log_df = self.DF(_db_log)

    if getattr(self, 'engine'):
      _db_log_df.to_sql(self.log_table_name, self.engine, if_exists='append', index=False)
    else:
      _log_file = f"{self.log_file_path.strip('/')}/{self.log_file_name}"
      if self.exists(_log_file):
        _db_log_df.to_csv(_log_file, mode='a', header=False)

    if getattr(self, 'step_pause', False):
      input("Step pause enabled. Press enter to continue...")
      self.update_attributes(self, {"step": False})

  def log_info(self, *args, **kwargs):
    kwargs.update({"log_type": "info"})
    return self.__log(*args, **kwargs)

  def log_debug(self, *args, **kwargs):
    kwargs.update({"log_type": "debug"})
    return self.__log(*args, **kwargs)

  def log_warning(self, *args, **kwargs):
    kwargs.update({"log_type": "warning"})
    return self.__log(*args, **kwargs)

  def log_error(self, *args, **kwargs):
    kwargs.update({"log_type": "error"})
    return self.__log(*args, **kwargs)

  def log_success(self, *args, **kwargs):
    kwargs.update({"log_type": "success"})
    return self.__log(*args, **kwargs)

  def log_fail(self, *args, **kwargs):
    kwargs.update({"log_type": "fail"})
    return self.__log(*args, **kwargs)
