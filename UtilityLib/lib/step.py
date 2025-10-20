import itertools as IT

class StepManager(dict):
  """StepManager: To manage different stages of execution
    _SM = StepManager()

    // Example Inputs
    StepManager(['Stage-1', 'Stage-2', 'Stage-3'], Stage_1=0, Stage_2=1, Stage_3=2)
    StepManager({'Stage-1': 0, 'Stage-2': 1, 'Stage-3': 2})
    StepManager([('Stage-1', 1), ('Stage-2', 5), ('Stage-3', 0)])

    _SM.next, _SM.current, _SM.prev, _SM.is_first, _SM.is_last
    next(_SM),
    _SM.current = 'Stage-2'

  """

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    # Handle stages_list from various types
    _arg_0 = args[0] if args else None
    if args and isinstance(_arg_0, (list, tuple, dict)):
      if isinstance(_arg_0, dict):
        self.stages_list = list(_arg_0.keys())
        self.priorities = dict(_arg_0)
      elif isinstance(_arg_0, (list, tuple)) and _arg_0 and isinstance(_arg_0[0], (tuple, list)):
        self.stages_list = [t[0] for t in _arg_0]
        self.priorities = dict(_arg_0)
      else:
        self.stages_list = list(_arg_0)
        self.priorities = {}
    else:
      self.stages_list = list(args)
      self.priorities = {arg: i for i, arg in enumerate(args)}
      self.stages_list += list(kwargs.keys())
      self.priorities.update(kwargs)

    for stage in self.stages_list:
      if stage not in self.priorities:
        self.priorities[stage] = 0

    self.original_stages_list = self.stages_list.copy()
    self.stages_list = sorted(self.stages_list, key=lambda s: (-self.priorities[s], self.original_stages_list.index(s)))

    self._current = self.stages_list[0] if self.stages_list else None
    self._set_position()

    self._cycle = IT.cycle(self.stages_list)
    _current_index = self.stages_list.index(self._current)
    for _ in range(_current_index):
      next(self._cycle)

  def _set_position(self):
    self._is_first = self._current == self.stages_list[0]
    self._is_last = self._current == self.stages_list[-1]

  @property
  def is_first(self):
    return self._is_first

  @property
  def is_last(self):
    return self._is_last

  @property
  def current(self):
    return self._current

  @current.setter
  def current(self, stage_key):
    if stage_key in self.stages_list:
      self._current = stage_key
      self._set_position()
    else:
      raise ValueError(f"Stage {stage_key} does not exist.")

  step = current
  stage = current

  def get_stage(self):
    return self._current

  def set_stage(self, *args, **kwargs):
    _stage_key = kwargs.get('stage_key', args[0] if len(args) > 0 else self._current)
    self.current = _stage_key

  def next_stage(self, cycle=False):
    _current_index = self.stages_list.index(self._current)
    if _current_index < (len(self.stages_list) - 1):
      self.current = self.stages_list[_current_index + 1]
    elif cycle is True:
      self.current = self.stages_list[0]
    return self.get_stage()

  __next__ = next_stage

  @property
  def next(self):
    self.next_stage()
    return self.get_stage()

  def previous_stage(self, cycle=False):
    _current_index = self.stages_list.index(self._current)
    if _current_index > 0:
      self.current = self.stages_list[_current_index - 1]
    elif cycle is True:
      self.current = self.stages_list[-1]
    return self.get_stage()

  @property
  def prev(self):
    self.previous_stage()
    return self.get_stage()

  previous = prev

  @property
  def next(self):
    self.next_stage()
    return self.get_stage()

  def reset(self):
    self.current = self.stages_list[0]

  def update_priority(self, stage, new_priority):
    if stage in self.stages_list:
      self.priorities[stage] = new_priority
      self.stages_list = sorted(self.stages_list, key=lambda s: (-self.priorities[s], self.original_stages_list.index(s)))
      self._set_position()
      self._cycle = IT.cycle(self.stages_list)
      _current_index = self.stages_list.index(self._current)
      for _ in range(_current_index):
        next(self._cycle)

  def __iter__(self):
    for _step in self.stages_list:
      self.set_stage(_step)
      yield _step

  def __next__(self):
    self.current = next(self._cycle)
    return self.current

  def __repr__(self):
    return f"{self.current}"

  def __str__(self):
    return self._current
