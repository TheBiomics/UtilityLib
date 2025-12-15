from .base import BaseUtility
from ..lib.time import EntityTime

class TimeUtility(BaseUtility):
  DeltaTime = EntityTime.DeltaTime
  DateTime  = EntityTime.DateTime
  Timestamp = EntityTime.Timestamp
  EntityTime = EntityTime

  def __init__(self, *args, **kwargs):
    __defaults = {
        "duration": 3,
      }
    __defaults.update(kwargs)
    super().__init__(**__defaults)
    self.time_start()

  def now(self, format=None):
    """Get current time."""
    _now = self.DateTime.now()
    if format:
      _now = _now.strftime(format)
    return _now

  @property
  def time(self):
    """Time with custom format"""
    return self.now(format="%H:%M:%S")

  @property
  def time_ms(self):
    """Time format: 12:54:54.111"""
    return self.time_us[:-3]

  @property
  def time_us(self):
    """Time format: 12:54:54.111111"""
    return self.now(format="%H:%M:%S.%f")

  @property
  def date(self):
    """Date format: 2024-10-24"""
    return self.now(format="%Y-%m-%d")

  @property
  def datetime(self):
    """Datetime format: 2024-10-24 12:54:54"""
    return self.now(format="%Y-%m-%d %H:%M:%S")

  dt = datetime

  @property
  def day(self):
    return self.now().day

  @property
  def weekday(self):
    return self.now(format="%A")

  @property
  def week(self):
    return self.now().isocalendar()[1]

  day_name = weekday

  @property
  def month(self):
    return self.now().month

  @property
  def month_name(self):
    return self.now().strftime('%B')

  @property
  def year(self):
    return self.now().year

  @property
  def hour(self):
    return self.now().hour

  @property
  def minute(self):
    return self.now().minute

  @property
  def second(self):
    return self.now().second

  @property
  def ts_us(self):
    """Timestamp with microseconds e.g., 1729927233.803901"""
    return EntityTime().timestamp

  @property
  def time_stamp(self):
    """Timestamp in YYYYMMDDHHMMSS format."""
    return f"{self.year}{self.month:02}{self.day:02}{self.hour:02}{self.minute:02}{self.second:02}"

  timestamp = time_stamp

  def time_string(self, *args, **kwargs):
    # https://stackoverflow.com/a/10981895/6213452
    _timestamp = args[0] if len(args) > 0 else kwargs.get("timestamp", self.time_get())
    return EntityTime(_timestamp, **kwargs).string

  def time_elapsed(self, *args, **kwargs):
    _from = args[0] if len(args) > 0 else kwargs.get("from", self.time_get())
    _human_readable = args[1] if len(args) > 1 else kwargs.get("human_readable", False)
    _seconds_elapsed = _from - self.start_time

    _time_delta = EntityTime.DeltaTime.timedelta(seconds=_seconds_elapsed)
    _res_time = str(_time_delta)

    if _human_readable:
      _res_time = self.time_string(_time_delta)

    return _res_time

  def time_get(self, *args, **kwargs):
    self.pinned_time = EntityTime(**kwargs).timestamp
    return self.pinned_time

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
