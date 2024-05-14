from functools import lru_cache as CacheMethod
from tqdm.auto import tqdm as TQDMProgressBar
from .time import TimeUtility

class CommandUtility(TimeUtility):
  ProgressBar = TQDMProgressBar
  PB = ProgressBar
  TQDM = ProgressBar
  def __init__(self, *args, **kwargs):
    self.__defaults = {
        "debug": False,
        "config": [],
        "cpu_count": None,
        "processes": []
      }
    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)

  def cmd_is_exe(self, program):
    return self.cmd_which(program) is not None

  is_exe = cmd_is_exe

  def cmd_which(self, program):
    return self.SHUTIL.which(program)

  which = cmd_which

  def cmd_call(self, *args, **kwargs):
    _command = args[0] if len(args) > 0 else kwargs.get("command")

    self.require('subprocess', 'SubProcess')

    if isinstance(_command, str):
      _command = _command.split()

    process = self.SubProcess.call(_command, shell=True)
    return process

  def cmd_run(self, *args, **kwargs):
    _command = args[0] if len(args) > 0 else kwargs.get("command")
    _newlines = args[1] if len(args) > 1 else kwargs.get("newlines", True)

    if _command is None:
      return None

    if self.require('shlex', 'SHELLX') and isinstance(_command, str):
      _command = self.SHELLX.split(_command)

    _output = None

    self.require('subprocess', 'SubProcess')

    _process = self.SubProcess.Popen(_command, stdout=self.SubProcess.PIPE, universal_newlines=_newlines)
    _output, _error = _process.communicate()

    return _output

  def flatten_args(self, *args, **kwargs):
    _args = args[0] if len(args) > 0 else kwargs.get("mapping", [])
    _flattened = {}
    if isinstance(_args, (dict)):
      _flattened = {_k: _v[0] if len(_v) == 1 else _v for _k, _v in _args.items()}
    return _flattened

  def unregistered_arg_parser(self, *args, **kwargs):
    """Processes uregistered arguments from commandline

      @accepts
      List/Tuple

      @return
      dict() with/out values
    """
    _un_args = args[0] if len(args) > 0 else kwargs.get("unregistered_args", [])

    _arg_aggregator = {}
    _key = None
    for _ua in _un_args:

      if _ua.startswith(("-", "--")):
        _key = _ua.strip("-")
        _key, _attached_value = _key.split("=", 1) if "=" in _key else (_key, "")

        if not _key in _arg_aggregator.keys():
          _arg_aggregator[_key] = []

        _arg_aggregator[_key].append(_attached_value) if len(_attached_value) > 0 else None

      elif _key and _key in _arg_aggregator.keys():
        _arg_aggregator[_key].append(_ua)

    return self.flatten_args(_arg_aggregator)

  def guess_nargs_from_default(self, *args, **kwargs):
    _default = args[0] if len(args) > 0 else kwargs.get("default")
    if _default is None:
      return None
    elif isinstance(_default, (str)):
      return "*"
    elif isinstance(_default, (list, tuple, set, dict)):
      return

  def init_cli(self, *args, **kwargs):
    self.require('argparse', 'ArgParser')

    _version = args[0] if len(args) > 0 else kwargs.get("version", "unknown")
    self.cmd_arg_parser = self.ArgParser.ArgumentParser(prog=_version)
    self.cmd_arg_parser.add_argument('-v', '--version', action='version', version=_version)

  def get_cli_args(self, *args, **kwargs):
    """
      @example

      _cli_settings = {
        ...
        "db_path": (['-db'], None, None, 'Provide path to the database for Sieve project.', {}),
        "path_base": (['-b'], "*", [OS.getcwd()], 'Provide base directory to run the process.', {}),
        ...
      }
    """

    if not hasattr(self, "cmd_arg_parser"):
      self.init_cli(**kwargs)

    _cli_args = args[0] if len(args) > 0 else kwargs.get("cli_args", {})

    for _arg_key, _arg_value in _cli_args.items():

      _keys = _arg_value[0]
      _keys.append(f"--{_arg_key}")

      _keys = [_k if "-" in _k else f"-{_k}" for _k in _keys] # Add atleast one - to the argument identifier

      _cmd_keys = _arg_value[0]
      _nargs = _arg_value[1]
      _default = _arg_value[2]
      _help = _arg_value[3]

      if not '%(default)s' in _help:
        _help = f"{_help} (Default: %(default)s)"

      _kws = _arg_value[4]
      _kws.update({
        "nargs": _nargs,
        "default": _default,
        "help": _help,
      })

      self.cmd_arg_parser.add_argument(*list(_cmd_keys), **_kws)

    _reg_args, _unreg_args = self.cmd_arg_parser.parse_known_args()
    _reg_args = vars(_reg_args)
    _params = self.unregistered_arg_parser(_unreg_args)
    _params.update(_reg_args)
    return _params

  # Multithreading
  max_workers = None
  thread_executor = None
  semaphore = None
  task_queue = None
  future_objects = []

  def _get_max_workers(self):
    # Get the number of CPU cores available
    _num_cores = self.OS.cpu_count()
    # Adjust max_workers based on available CPU cores and workload
    self.max_workers = min(2 * _num_cores, 32)  # Example: Limit to 2x CPU cores or 32 workers, whichever is lower
    return self.max_workers

  def init_multiprocessing(self):
    self.require('concurrent.futures', 'ConcurrentTasks')
    self.require('threading', 'Threading')
    self.require('queue', 'QueueProvider')
    self._get_max_workers()
    self.task_queue = self.QueueProvider.Queue()
    self.semaphore = self.Threading.Semaphore(self.max_workers)
    self.thread_executor = self.ConcurrentTasks.ThreadPoolExecutor(max_workers=self.max_workers)

  def __enter__(self):
    self.init_multiprocessing()
    return self

  def __exit__(self, *args, **kwargs):
    self.thread_executor.shutdown()

  @CacheMethod(maxsize=None)
  def _cache_wrapper(self, func, *arg, **kwarg):
    return func(*arg, **kwarg)

  def queue_task(self, func, *args, **kwargs):
    """Queue a function operation

@example:
def method_to_execute(self, *arg, **kwargs):
  # Example function to be cached
  return arg ** 2

_cu = CommandUtility()
_cu.init_multiprocessing()
_cu.queue_task(method_to_execute, *args, **kwargs)

"""
    self.task_queue.put((func, args, kwargs))

  def process_queue(self, wait=False):
    # Process tasks from the queue
    while not self.task_queue.empty():
      # Acquire semaphore to limit concurrency
      try:
        with self.semaphore:
          # Get task from the queue
          _func, _args, _kwargs = self.task_queue.get()
          # Submit task to the executor
          _ftr_obj = self.thread_executor.submit(_func, *_args, **_kwargs)
          self.future_objects.append(_ftr_obj)
      except Exception as e:
        # Handle exceptions raised during file operation
        print(f"Error processing the queue: {e}")

    if wait:
      self._wait_for_completion()

  def _wait_for_completion(self):
    # Wait for all tasks to complete
    self.ConcurrentTasks.wait(self.future_objects)
    # Shutdown the ThreadPoolExecutor
    self.thread_executor.shutdown(wait=True)

  def queue_task_status(self):
    self.config.jobs.done = sum(1 for _ftr in self.future_objects if _ftr.done())
    self.config.jobs.pending = sum(1 for _ftr in self.future_objects if not _ftr.done() and not _ftr.running())
    self.config.jobs.running = sum(1 for _ftr in self.future_objects if not _ftr.done() and _ftr.running())
    return self.config.jobs

  def sys_open_files(self):
    import psutil as PC
    _p = PC.Process()
    return _p.open_files()
