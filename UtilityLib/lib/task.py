from .obj import ObjDict
from .time import EntityTime

class TaskManager():
  """
    Enhanced Task Manager for handling tasks, stages, and timings.

    TASKS.SUBTASK.STAGE = {"status": 1|0|-1, "start": <datetime>, "end": <datetime>}
    e.g.,
    project.downloading.init = {"status": 1, "start": <datetime>, "end": None}

    status
      -1:
      0:
      1:

  """

  _def_task = 'Main'
  _def_subtask = 'Stage'
  _def_step = 'First'

  _status_header = ['Task', 'Subtask', 'Step', 'Status', 'Start', 'End']
  last_status_df = None

  _tasks = ObjDict()
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._def_task = kwargs.get('task', args[0] if len(args) > 0 else self._def_task)
    self._def_subtask = kwargs.get('subtask', args[1] if len(args) > 1 else self._def_subtask)
    self._def_step = kwargs.get('step', args[2] if len(args) > 2 else self._def_step)

  def _get_task_params(self, *args, **kwargs):
    _step    = kwargs.get('step', args[0] if len(args) > 0 else self._def_step)
    _subtask = kwargs.get('subtask', args[1] if len(args) > 1 else self._def_subtask)
    _task    = kwargs.get('task', args[2] if len(args) > 2 else self._def_task)
    _status  = kwargs.get('status', args[3] if len(args) > 3 else None)

    return _step, _subtask, _task, _status

  def start_step(self, *args, **kwargs):
    """Start a specific stage for a task."""
    _step, _subtask, _task, _ = self._get_task_params(*args, **kwargs)

    self._tasks[_task][_subtask][_step]['status'] = 0
    self._tasks[_task][_subtask][_step]['start'] = EntityTime().timestamp
    self._tasks[_task][_subtask][_step]['last'] = EntityTime().timestamp

  def step_status(self, *args, **kwargs):
    """Update a specific stage for a task."""
    _step, _subtask, _task, _status = self._get_task_params(*args, **kwargs)
    self._tasks[_task][_subtask][_step]['last'] = EntityTime().timestamp
    if not _status is None:
      self._tasks[_task][_subtask][_step]['status'] = _status

  def end_step(self, *args, **kwargs):
    """Start a specific stage for a task."""
    _step, _subtask, _task, _ = self._get_task_params(*args, **kwargs)

    self._tasks[_task][_subtask][_step]["status"] = 1
    self._tasks[_task][_subtask][_step]['last'] = EntityTime().timestamp

  def get_status(self, *args, **kwargs):
    """Summarize progress across all tasks."""
    _status = []
    for _task, _subtask, _step, _step_details in self._iterate_tasks(*args, **kwargs):
      _s = _task, _subtask, _step, _step_details.status, _step_details.start, _step_details.end
      _status.append(_s)

    return _status

  def _iterate_tasks(self, task=None, subtask=None):
    _all_tasks = self._tasks.copy()
    for _task, _subtasks in _all_tasks.items():
      if not task is None and not _task == task:
        continue
      for _subtask, _subtask_details in _subtasks.items():
        if not subtask is None and not _subtask == subtask:
          continue
        for _step, _step_details in _subtask_details.items():
          yield _task, _subtask, _step, _step_details

  """Other Accessory Methods"""
  def get_status_df(self, *args, **kwargs):
    import pandas as PD
    _status = self.get_status(*args, **kwargs)
    self.last_status_df = PD.DataFrame(_status, columns=self._status_header)
    return self.last_status_df
