from functools import lru_cache as CacheMethod
from contextlib import contextmanager
from ..lib.obj import ObjDict
from ..lib.cmd import CMDLib
from ..lib.path import EntityPath
from .log import LoggingUtility

class CommandUtility(LoggingUtility):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  is_executable = CMDLib.is_exe
  cmd_is_exe    = CMDLib.which
  is_exe        = CMDLib.which
  cmd_which     = CMDLib.which
  which         = CMDLib.which

  def _format_command(self, *args, **kwargs):
    """
    Format the command with positional and keyword arguments.

    :param args: Positional arguments.
    :param kwargs: Keyword arguments.

    :return: List of command parts.
    """
    _command = [*args]

    for _key, _value in kwargs.items():
      _command = [*_command, f"{_key}"]
      if isinstance(_value, (dict)):
        _value = [self._format_command(**_value)]
      elif isinstance(_value, (str, int, float)):
        _value = [_value]

      _command = [*_command, *_value]

    return list(map(str, _command))

  def cmd_bg(self, *args, **kwargs):
    """
    Run a method in background using ThreadPoolExecutor.

    If the first argument is callable, it is used as the function to execute.
    Otherwise, self.cmd_run is used with all provided arguments.

    :param args: If first arg is callable, it's the function to run. Otherwise all args are passed to self.cmd_run.
    :param kwargs: Keyword arguments for the function.
    :return: A Future object representing the execution of the function.

    Usage:
      # Run an arbitrary function in background
      future = cmd_util.cmd_bg(some_function, arg1, arg2, kwarg1='value')

      # Run cmd_run in background (default)
      future = cmd_util.cmd_bg('echo', 'Hello')  # Equivalent to cmd_run('echo', 'Hello')
    """

    if not hasattr(self, 'thread_pool') or self.thread_pool is None:
      self.init_multiprocessing()

    # Determine if the first arg is a callable function
    if args and callable(args[0]):
      func = args[0]
      func_args = args[1:]
    else:
      func = self.cmd_run
      func_args = args

    func_name = getattr(func, '__name__', 'anonymous function')

    self.log_debug(f"CMD_010: Running function '{func_name}' in background")
    try:
      _future = self.thread_pool.submit(func, *func_args, **kwargs)
      self.future_objects.append(_future)
      return _future
    except Exception as e:
      self.log_error(f"CMD_011: Failed to run function '{func_name}' in background: {e}")
      return None

  func_bg = cmd_bg
  bg_func = cmd_bg

  command_background = cmd_bg
  bg_command = cmd_bg

  def cmd_call(self, *args, **kwargs):
    """
    Call a command without capturing output.

    :param command: The command to run.
    :return: The return code of the command.
    """
    _cmd_params = kwargs.pop('cmd_params', {
          "universal_newlines": kwargs.pop('newlines', True),
          "cwd": kwargs.pop('cwd', None),
          "check": kwargs.pop('check', None),
          "shell": kwargs.pop('shell', None),
          "capture_output": kwargs.pop('text', True),
          "text": kwargs.pop('newlines', None),
        })
    _cmd_params = {k: v for k, v in _cmd_params.items() if v is not None}
    _command = self._format_command(*args, **kwargs)
    _command_str = ' '.join(_command)

    self.require('subprocess', 'SubProcess')
    try:
      self.log_debug(f"CMD_007: Calling command: {_command_str}")
      _result = self.SubProcess.call(_command, **_cmd_params)
      return _result
    except Exception as _e:
      self.log_error(f"Command '{_command_str}' failed with error: {_e}")
      return None

  call_command = cmd_call
  call_cmd = cmd_call

  def cmd_run(self, *args, **kwargs):
    """
    Run a command and capture the output.

    # shell=True for commands such as git

    :param command: The command to run.
    :param newlines: Whether to treat the output as text with newlines.
    :return: The output of the command.
    """

    self.require('subprocess', 'SubProcess')

    _cmd_params = kwargs.pop('cmd_params', {
          "universal_newlines": kwargs.pop('newlines', True),
          "cwd"               : kwargs.pop('cwd', None),
          "check"             : kwargs.pop('check', None),
          "shell"             : kwargs.pop('shell', None),
          "capture_output"    : kwargs.pop('text', True),
          "text"              : kwargs.pop('newlines', None),
        })

    if not isinstance(_cmd_params, (dict)):
      _cmd_params = dict()
    else:
      _cmd_params = {_k: _v for _k, _v in _cmd_params.items() if _v is not None}

    _command = self._format_command(*args, **kwargs)
    _command_str = ' '.join(_command)

    try:
      self.log_debug(f"CMD_008: Running command: {_command_str}")
      _result = self.SubProcess.run(_command, **_cmd_params)
      self.log_debug(f"CMD_009: Command output: {_result.stdout}")
      return _result.stdout
    except self.SubProcess.CalledProcessError as _e:
      self.log_error(f"Command '{_command_str}' failed with error: {_e.stderr}")
      return None

  run_command = cmd_run
  run_cmd = cmd_run

  def cmd_run_mock(self, *args, **kwargs):
    """Mocks cmd_run/cmd_call"""
    return self.cmd_run('echo', *args, **kwargs)

  cmd_dry_run   = cmd_run_mock
  cmd_call_mock = cmd_run_mock
  cmd_call_echo = cmd_run_mock

  get_cli_args = CMDLib.get_registered_args

  # Multithreading
  max_workers = 32
  num_cores = 8
  thread_pool = None
  semaphore = None
  task_queue = None
  future_objects = []

  def _get_max_workers(self):
    # Get the number of CPU cores available
    self.num_cores = min(self.OS.cpu_count(), self.num_cores)
    # Adjust max_workers based on available CPU cores and workload
    self.max_workers = min(2 * self.num_cores, self.max_workers)  # Example: Limit to 2x CPU cores or 32 workers, whichever is lower
    return self.max_workers

  def init_multiprocessing(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    self.require('concurrent.futures', 'ConcurrentFutures')
    self.require('threading', 'Threading')
    self.require('queue', 'QueueProvider')
    self._get_max_workers()
    self.task_queue = self.QueueProvider.Queue()
    self.semaphore = self.Threading.Semaphore(self.max_workers - 1)
    self.thread_pool = self.ConcurrentFutures.ThreadPoolExecutor(max_workers=self.max_workers)
    self.log_debug(f"CMD_002:Starting with cores {self.num_cores} and max_workers {self.max_workers}.")

  start_mp = init_multiprocessing

  def __enter__(self):
    self.log_debug('CMD_004: Init multiprocessing.')
    self.init_multiprocessing()
    return self

  def __exit__(self, *args, **kwargs):
    self.log_debug('CMD_001: Shutting down the thread executor.')
    self.thread_pool.shutdown()

  @CacheMethod(maxsize=None)
  def _cache_wrapper(self, func, *arg, **kwarg):
    return func(*arg, **kwarg)

  def queue_task(self, func, *args, **kwargs) -> None:
    """Queue a function operation

@example:
def method_to_execute(self, *arg, **kwargs):
  # Example function to be cached
  return arg ** 2

_.init_multiprocessing
_.queue_task(method_to_execute, *args, **kwargs)
_.process_queue
_.queue_final_callback

"""
    self.task_queue.put((func, args, kwargs))

  def queue_timed_callback(self, callback=None, *args, **kwargs) -> None:
    _cb_interval = kwargs.pop("cb_interval", 300)
    if not callback is None and callable(callback):
      self.require('threading', 'Threading')
      self.log_debug(f'CMD_003: Delegating a callback in {_cb_interval}s.')
      self.Threading.Timer(_cb_interval, callback, args=args, kwargs=kwargs)

  _queue_schedule_ref = None
  def queue_final_callback(self, callback=None, *args, **kwargs) -> None:
    if callback is not None and callable(callback):
      from ..lib.schedule import ScheduleManager

      _cb_interval = kwargs.pop("cb_interval", 60)
      # Lazily create a ScheduleManager per CommandUtility instance and start it
      if not hasattr(self, "_schedule_mgr") or self._schedule_mgr is None:
        self._schedule_mgr = ScheduleManager()

      self._queue_schedule_ref = self._schedule_mgr.add(
        self._queue_final_cb_fn_bg_exe,
        interval=_cb_interval,
        unit="seconds",
        args=(callback, *args),
        **kwargs,
      )

  def _queue_final_cb_fn_bg_exe(self, callback, *args, **kwargs) -> None:
    _job_t, _job_d = self.queue_task_status.total, self.queue_task_status.done
    if any([_job_d < _job_t, not self.task_queue.empty()]):
      self.log_debug(f'CMD_004: Job Status: {_job_t-_job_d}/{_job_t} to be done. ~zZ')
    elif self._queue_schedule_ref is not None:
      self.log_debug(f'CMD_005: Job Status: All {self.queue_done} job(s) completed. Executing final callback...')
      callback(*args, **kwargs)
      self._queue_schedule_ref.stop()

  def process_queue(self, *args, **kwargs):
    """Process tasks from the queue
      # Acquire semaphore to limit concurrency
      # Get task from the queue
      # Submit task to the executor
    """

    while not self.task_queue.empty():
      try:
        with self.semaphore:
          _func, _args, _kwargs = self.task_queue.get()
          _ftr_obj = self.thread_pool.submit(_func, *_args, **_kwargs)
          self.future_objects.append(_ftr_obj)
      except Exception as e:
        self.log_error(f"Error processing the queue: {e}")

    self._shut_down_queue(*args, **kwargs)
    return True

  def _shut_down_queue(self, *args, **kwargs):
    _wait = kwargs.get("wait", args[0] if len(args) > 0 else False)
    self.log_debug(f'CMD_006: Setting queue wait = {_wait}.')

    if _wait:
      # Wait for all tasks to complete
      self.ConcurrentFutures.wait(self.future_objects)

    # Shutdown the ThreadPoolExecutor
    self.thread_pool.shutdown(wait=_wait)

  @property
  def queue_running(self) -> int:
    """Blocking"""
    return sum(map(lambda _fo: bool(_fo.running()), self.ConcurrentFutures.as_completed(self.future_objects)))

  @property
  def queue_failed(self) -> int:
    """Blocking"""
    return sum(map(lambda _fo: bool(_fo.exception()), self.ConcurrentFutures.as_completed(self.future_objects)))

  @property
  def queue_done(self) -> int:
    return self.queue_task_status.done

  @property
  def queue_pending(self) -> int:
    return self.queue_task_status.pending

  @property
  def queue_task_status(self) -> dict:
    _total = len(self.future_objects)
    _done = sum(map(lambda _fo: bool(_fo.done()), self.future_objects))

    return ObjDict({
      "total": _total,
      "done": _done,
      "pending": _total - _done, # _fo.done() - _fo.running()
    })

  sys_open_files = CMDLib.get_open_files
