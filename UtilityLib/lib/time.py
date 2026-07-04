from datetime import datetime as _DT
import re as _Rx

try:
  import pandas as PD
except ImportError:
  PD = None


class DeltaTime:
  """Extended timedelta with human-readable formatting.

  Falls back to datetime.timedelta if pandas is not installed.

  Usage:
    DeltaTime(hours=5)
    DeltaTime('5 hours')
    DeltaTime(seconds=3600).diff  # -> "1 hour"
  """
  def __init__(self, *args, **kwargs):
    if PD is not None:
      self._td = PD.Timedelta(*args, **kwargs)
    else:
      from datetime import timedelta
      self._td = timedelta(*args, **kwargs)

  def __getattr__(self, name):
    return getattr(self._td, name)

  @property
  def humanize(self):
    """Human-readable relative time (requires humanize package)."""
    try:
      import humanize
      return humanize.naturaltime(self._td)
    except ImportError:
      return str(self._td)

  @property
  def diff(self):
    """Human-readable duration string like '2 hours and 30 minutes'."""
    _seconds = int(round(self._td.total_seconds()))
    _days, _seconds = divmod(_seconds, 86400)
    _hours, _seconds = divmod(_seconds, 3600)
    _minutes, _seconds = divmod(_seconds, 60)

    _string = []
    if _days:
      _string.append(f"{_days} day{'s' if abs(_days) > 1 else ''}")
    if _hours:
      _string.append(f"{_hours} hour{'s' if abs(_hours) > 1 else ''}")
    if _minutes:
      _string.append(f"{_minutes} minute{'s' if abs(_minutes) > 1 else ''}")
    if _seconds:
      _string.append(f"{_seconds} second{'s' if abs(_seconds) > 1 else ''}")

    if len(_string) == 0:
      return "0 seconds"
    elif len(_string) == 1:
      return _string[0]
    elif len(_string) == 2:
      return f"{_string[0]} and {_string[1]}"
    else:
      return f"{', '.join(_string[:-1])}, and {_string[-1]}"


class EntityTime:
  """EntityTime: manage time and provide utility methods.

  Usage:
    _et = EntityTime()                    # now
    _et = EntityTime('+6 hours')          # offset
    _et = EntityTime('20240101120000')    # from timestamp string
    _et = EntityTime(1704067200)          # from unix timestamp
  """
  DeltaTime = DeltaTime
  DateTime = _DT
  format = '%Y%m%d%H%M%S'

  if PD is not None:
    Timestamp = PD.Timestamp
  else:
    Timestamp = _DT

  def __init__(self, *args, **kwargs):
    self._datetime = _DT.now()
    self.format = kwargs.get('format', self.format)

    if len(args) == 1 and isinstance(args[0], EntityTime):
      raise ValueError('Cyclic call.')
    elif len(args) == 1 and isinstance(args[0], str):
      if _Rx.fullmatch(r'^([+-]\d+)\s+(hour|hours|minute|minutes|day|days)$', args[0]):
        self._apply_shift(args[0])
      elif "%" in args[0]:
        self.format = args[0]
      else:
        try:
          self._datetime = _DT.strptime(args[0], self.format)
        except Exception as _e:
          raise _e
    elif len(args) == 1 and isinstance(args[0], (int, float)):
      self._datetime = _DT.fromtimestamp(args[0])
    elif len(args) >= 3:
      self._datetime = _DT(args[0], args[1], args[2]) + DeltaTime(seconds=args[3] if len(args) > 3 else 0)

  @property
  def date(self):
    return self._datetime.date()

  @property
  def time(self):
    return self._datetime.time()

  @property
  def string(self):
    return str(self._datetime.ctime())

  def get_format(self, *args, **kwargs):
    return self._datetime.strftime(*args, **kwargs)

  def get_isoformat(self, *args, **kwargs):
    return self._datetime.isoformat(*args, **kwargs)

  @property
  def current(self):
    return EntityTime()

  @property
  def _ts(self):
    return self._datetime.timestamp()

  timestamp = _ts
  stamp = _ts
  ts = _ts

  def __call__(self, *args, **kwargs):
    return EntityTime(*args, **kwargs)

  def _apply_shift(self, time_shift=None):
    if time_shift is None:
      return
    _unit_match = _Rx.match(r'([+-]\d+)\s+(hour|hours|minute|minutes|day|days)', time_shift)
    if _unit_match:
      _time_val = int(_unit_match.group(1))
      _time_unit = _unit_match.group(2)
      if _time_unit in ['hour', 'hours']:
        delta = DeltaTime(hours=_time_val)
      elif _time_unit in ['minute', 'minutes']:
        delta = DeltaTime(minutes=_time_val)
      elif _time_unit in ['day', 'days']:
        delta = DeltaTime(days=_time_val)
      else:
        raise ValueError(f"Unsupported time unit '{_time_unit}'")
      self._datetime += delta

  def __sub__(self, other):
    if isinstance(other, (str, float, int)):
      other = EntityTime(other)
    return DeltaTime(self._datetime - other._datetime)

  def __rsub__(self, other):
    if isinstance(other, (str, float, int)):
      other = EntityTime(other)
    return DeltaTime(other._datetime - self._datetime)

  def __iter__(self):
    return [self._datetime]

  def __repr__(self):
    return f"{self.string}"

  def __str__(self):
    return f"{self.string}"
