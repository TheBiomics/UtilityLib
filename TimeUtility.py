import time as TIME

from .BaseUtility import BaseUtility

class TimeUtility(BaseUtility):
  def __init__(self, *args, **kwargs):
    super(TimeUtility, self).__init__(**kwargs)
    self.__defaults = {
        "debug": False,
        "duration": 3,
      }
    self.update_attributes(self, kwargs, self.__defaults)
    self.time_start()

  def time_get(self):
    self.pinned_time = TIME.time()
    return self.pinned_time

  def time_stamp(self):
    from datetime import datetime as DATE_PROVIDER
    return DATE_PROVIDER.today().strftime('%Y%m%d%H%M%S')

  def time_to_string(self, *args, **kwargs):
    # https://stackoverflow.com/a/10981895/6213452
    _time = args[0] if len(args) > 0 else kwargs.get("time")

    # days = td.days
    # hours, remainder = divmod(td.seconds, 3600)
    # minutes, seconds = divmod(remainder, 60)
    # # If you want to take into account fractions of a second
    # seconds += td.microseconds / 1e6

    if _time:
      return _time

  def time_elapsed(self, *args, **kwargs):
    _from = args[0] if len(args) > 0 else kwargs.get("from", self.time_get())
    _human_readable = args[1] if len(args) > 1 else kwargs.get("human_readable", False)
    _seconds_elapsed = _from - self.start_time

    self.require("datetime", "DATETIME")
    _time_delta = self.DATETIME.timedelta(seconds=_seconds_elapsed)
    _res_time = str(_time_delta)

    if _human_readable:
      _res_time = self.time_to_string(_time_delta)

    return _res_time

  def time_start(self, *args, **kwargs):
    self.start_time = self.time_get()
    self.pinned_time = self.time_get()
    return self.start_time

  def time_end(self, *args, **kwargs):
    return self.time_get() - self.start_time

  def time_sleep(self, *args, **kwargs):
    return self.time_pause(*args, **kwargs)

  def time_pause(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    _duration = args[0] if len(args) > 0 else kwargs.get("duration", getattr(self, "duration"))
    TIME.sleep(_duration)
