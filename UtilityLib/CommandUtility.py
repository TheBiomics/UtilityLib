import os as OS
import shlex as SHELLX

import subprocess as SubProcess
import multiprocessing as MultiProcessing
from tqdm.auto import tqdm as ProgressBar

from .DataUtility import DataUtility

class CommandUtility(DataUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {
        "debug": False,
        "config": [],
        "ProgressBar": ProgressBar, # ProgressBar(iterable, position=0, leave=True)
        "PB": ProgressBar,
        "cpu_count": None,
        "processes": []
      }
    self.__defaults.update(kwargs)
    super(CommandUtility, self).__init__(**self.__defaults)

  def multiprocess_start(self, *args, **kwargs):
    _processes = args[0] if len(args) > 0 else kwargs.get("processes", getattr(self, "processes"))

    self.cpu_count = MultiProcessing.cpu_count()
    # Start job in chunks
    for _batch in self.chunks(_processes, round(self.cpu_count/5)):
      for _job in _batch:
        if not _job.is_alive():
          _job.start()
      for _job in _batch:
        _job.join()
      for _job in _batch:
        # Check if job is not yet exited
        _job.terminate()

  def multiprocess_add(self, *args, **kwargs):
    _target = args[0] if len(args) > 0 else kwargs.get("target")
    _args = args[1] if len(args) > 1 else kwargs.get("args")
    _kwargs = args[2] if len(args) > 2 else kwargs.get("kwargs", {})

    _process = MultiProcessing.Process(target=_target, args=_args, kwargs=_kwargs, daemon=True)
    self.processes.append(_process)
    return _process

  def cmd_is_exe(self, fpath):
    return OS.path.isfile(fpath) and OS.access(fpath, OS.X_OK)

  def cmd_which(self, program):
    fpath, fname = OS.path.split(program)
    if fpath:
      if self.is_exe(program):
        return program
    else:
      for path in OS.environ["PATH"].split(OS.pathsep):
        path = path.strip('"')
        exe_file = OS.path.join(path, program)
        if self.is_exe(exe_file):
          return exe_file
    return None

  def cmd_call(self, *args, **kwargs):
    _command = args[0] if len(args) > 0 else kwargs.get("command")

    if isinstance(_command, str):
      _command = _command.split()

    process = SubProcess.call(_command, shell=True)
    return process

  def cmd_run(self, *args, **kwargs):
    _command = args[0] if len(args) > 0 else kwargs.get("command")
    _newlines = args[1] if len(args) > 1 else kwargs.get("newlines", True)

    if _command is None:
      return None

    if isinstance(_command, str):
      _command = SHELLX.split(_command)

    _output = None

    _process = SubProcess.Popen(_command, stdout=SubProcess.PIPE, universal_newlines=_newlines)
    _output, _error = _process.communicate()

    return _output

  def flatten_args(self, *args, **kwargs):
    _args = args[0] if len(args) > 0 else kwargs.get("mapping", [])
    _flattened = {}
    if isinstance(_args, (dict)):
      _flattened = {_k: _v[0] if len(_v) == 1 else _v for _k, _v in _args.items()}
    return _flattened

  def unregistered_arg_parser(self, *args, **kwargs):
    """
      Processes uregistered arguments from commandline
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
    import argparse as ARGUMENT
    _version = args[0] if len(args) > 0 else kwargs.get("version", "unknown")
    self.cmd_arg_parser = ARGUMENT.ArgumentParser(prog=_version)
    self.cmd_arg_parser.add_argument('-v', '--version', action='version', version=_version)

  def get_cli_args_v2(self):
    """
      WIP
    """
    from absl import app
    from absl import flags
    from absl import logging

    flags.DEFINE_list(
        'fasta_paths', None, 'Paths to FASTA files, each containing a prediction '
        'target that will be folded one after another. If a FASTA file contains ')

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
