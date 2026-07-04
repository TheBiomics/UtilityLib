from functools import lru_cache as CacheMethod
from contextlib import contextmanager
from ..lib.obj import ObjDict
from ..lib.cmd import CMDLib
from ..lib.path import EntityPath
from ..lib.parallel import ParallelExecutor
from .log import LoggingUtility

class CommandUtility(LoggingUtility):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self._executor = None

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

  @property
  def executor(self):
    """Get or create the ParallelExecutor instance"""
    if self._executor is None:
      self._executor = ParallelExecutor()
      self._executor.init()
    return self._executor

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
    # Determine if the first arg is a callable function
    if args and callable(args[0]):
      func = args[0]
      func_args = args[1:]
    else:
      func = self.cmd_run
      func_args = args

    return self.executor.submit(func, *func_args, **kwargs)

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

  # Multiprocessing properties (delegate to executor)
  @property
  def max_workers(self):
    return self.executor.max_workers

  @property
  def num_cores(self):
    return self.executor.num_cores

  @property
  def thread_pool(self):
    return self.executor.thread_pool

  @property
  def semaphore(self):
    return self.executor.semaphore

  @property
  def task_queue(self):
    return self.executor.task_queue

  @property
  def future_objects(self):
    return self.executor.future_objects

  def init_multiprocessing(self, *args, **kwargs):
    """Initialize multiprocessing (delegates to ParallelExecutor)"""
    return self.executor.init(*args, **kwargs)

  start_mp = init_multiprocessing

  def __enter__(self):
    self.log_debug('CMD_004: Init multiprocessing.')
    self.init_multiprocessing()
    return self

  def __exit__(self, *args, **kwargs):
    self.log_debug('CMD_001: Shutting down the thread executor.')
    self.executor.shutdown()

  @CacheMethod(maxsize=None)
  def _cache_wrapper(self, func, *arg, **kwarg):
    return func(*arg, **kwarg)

  def queue_task(self, func, *args, **kwargs) -> None:
    """Queue a function operation (delegates to ParallelExecutor)

@example:
def method_to_execute(self, *arg, **kwargs):
  # Example function to be cached
  return arg ** 2

_.init_multiprocessing
_.queue_task(method_to_execute, *args, **kwargs)
_.process_queue
_.queue_final_callback

"""
    return self.executor.queue_task(func, *args, **kwargs)

  def queue_timed_callback(self, callback=None, *args, **kwargs) -> None:
    """Schedule a timed callback (delegates to ParallelExecutor)"""
    return self.executor.queue_timed_callback(callback, *args, **kwargs)

  def queue_final_callback(self, callback=None, *args, **kwargs) -> None:
    """Schedule a final callback when all tasks complete (delegates to ParallelExecutor)"""
    return self.executor.queue_final_callback(callback, *args, **kwargs)

  def process_queue(self, *args, **kwargs):
    """Process tasks from the queue (delegates to ParallelExecutor)"""
    return self.executor.process_queue(*args, **kwargs)

  @property
  def queue_running(self) -> int:
    """Blocking"""
    return self.executor.queue_running

  @property
  def queue_failed(self) -> int:
    """Blocking"""
    return self.executor.queue_failed

  @property
  def queue_done(self) -> int:
    return self.executor.queue_done

  @property
  def queue_pending(self) -> int:
    return self.executor.queue_pending

  @property
  def queue_task_status(self) -> dict:
    return self.executor.queue_task_status

  sys_open_files = CMDLib.get_open_files
