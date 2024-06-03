class StepManager(dict):
  """StepManager: To manage different stages of execution
    _a = StepManager(_dict_map, )
    _a.next()
    _a.current()
  """

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.stages_list = kwargs.get('stages_list', args[0] if len(args) > 0 else list(kwargs.values()))
    _def_stage = self.stages_list[0] if len(self.stages_list) else None
    self._current = kwargs.get('current', args[1] if len(args) > 1 else _def_stage)
    self._set_position()

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

  def next_stage(self):
    _current_index = self.stages_list.index(self._current)
    if _current_index < (len(self.stages_list) - 1):
      self.current = self.stages_list[_current_index + 1]
    return self.get_stage()

  __next__ = next_stage

  @property
  def next(self):
    self.next_stage()
    return self.get_stage()

  def previous_stage(self):
    _current_index = self.stages_list.index(self._current)
    if _current_index > 0:
        self.current = self.stages_list[_current_index - 1]
    return self.get_stage()

  @property
  def prev(self):
    self.previous_stage()
    return self.get_stage()

  previous = prev

  def reset(self):
    self.current = self.stages_list[0]

  def __iter__(self):
    for _step in self.stages_list:
      self.set_stage(_step)
      yield _step

  def __repr__(self):
    return f"{self.current}"

  def __str__(self):
    return self._current
