from .base import BaseUtility

class TimeUtility(BaseUtility):
  def __init__(self, *args, **kwargs):
    __defaults = {
        "duration": 3,
      }
    __defaults.update(kwargs)
    super().__init__(**__defaults)
    self.time_start()

  def time_get(self):
    self.require("time", "TIME")
    self.pinned_time = self.TIME.time()
    return self.pinned_time

  @property
  def time_stamp(self):
    return self.get_dt_stamp()

  timestamp = time_stamp

  @property
  def date_stamp(self):
    return self.get_dt_stamp(format='%Y%m%d')

  datestamp = date_stamp

  def get_dt_stamp(self, *args, **kwargs):
    _format = kwargs.get("format", args[0] if len(args) > 0 else '%Y%m%d%H%M%S')
    from datetime import datetime as DATE_PROVIDER
    return DATE_PROVIDER.today().strftime(_format)

  def time_string(self, *args, **kwargs):
    # https://stackoverflow.com/a/10981895/6213452
    _timestamp = args[0] if len(args) > 0 else kwargs.get("timestamp", self.time_get())

    if _timestamp:
      from datetime import datetime as DATE_PROVIDER
      return DATE_PROVIDER.utcfromtimestamp(float(_timestamp))

    self.require("time", "TIME")
    return self.TIME.ctime()

  def time_elapsed(self, *args, **kwargs):
    _from = args[0] if len(args) > 0 else kwargs.get("from", self.time_get())
    _human_readable = args[1] if len(args) > 1 else kwargs.get("human_readable", False)
    _seconds_elapsed = _from - self.start_time

    self.require("datetime", "DATETIME")
    _time_delta = self.DATETIME.timedelta(seconds=_seconds_elapsed)
    _res_time = str(_time_delta)

    if _human_readable:
      _res_time = self.time_string(_time_delta)

    return _res_time

  def time_start(self, *args, **kwargs):
    self.start_time = self.time_get()
    self.pinned_time = self.time_get()
    return self.start_time

  def time_end(self, *args, **kwargs):
    return self.time_get() - self.start_time

  def _sleep(self, *args, **kwargs):
    """Sleep for certain `duration|0` in seconds."""
    self.update_attributes(self, kwargs)
    self.duration = kwargs.get("duration", args[0] if len(args) > 0 else getattr(self, "duration"))
    self.require("time", "TIME")
    return self.TIME.sleep(self.duration)

  sleep = _sleep
  wait = _sleep
  time_break = _sleep
  time_pause = _sleep
  time_sleep = _sleep

  def sleep_ms(self, *args, **kwargs):
    """Sleep for certain `duration|0` in milliseconds."""
    self.duration = kwargs.get("duration", args[0] if len(args) > 0 else getattr(self, "duration"))
    kwargs['duration'] = float(self.duration) / 1000
    return self._sleep(*args, **kwargs)

  def sleep_random(self, *args, **kwargs):
    """Sleep for random seconds between `min|0` and `max|1`."""
    _min = kwargs.get("min", args[0] if len(args) > 0 else 0)
    _max = kwargs.get("max", args[1] if len(args) > 1 else 6)

    self.require("random", "RANDOM")
    _duration = self.RANDOM.uniform(float(_min), float(_max))
    kwargs['duration'] = _duration
    return self._sleep(**kwargs)
