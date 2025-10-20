
"""
  CMDLib: Command line interface/CLI like Utilities
"""

import shutil as SHUTIL
import sys as SYS
import subprocess as SUBPROCESS
import os as OS
from pathlib import Path
from typing import Union
import psutil as PC

class _MetaCMDLib(type):
  @property
  def cpu(cls):
    total = cls.get_cpu_total()
    available_percent = cls.get_cpu_available()
    available = total * (available_percent / 100)
    return {
      'total': total,
      'available': available,
    }

  @property
  def threads(cls):
    total = cls.get_threads_total()
    available_percent = cls.get_threads_available()
    available = total * (available_percent / 100)
    return {
      'total': total,
      'available': available,
    }

  @property
  def memory(cls):
    return {
      'total': cls.get_memory_total(),
      'available': cls.get_memory_available(),
    }

  @property
  def swap(cls):
    return {
      'total': cls.get_swap_total(),
      'available': cls.get_swap_available(),
    }

  @property
  def load(cls):
    """CPU load percentage (0-100). Use > 80 to check if system is busy."""
    return PC.cpu_percent(interval=0.1)

  @property
  def disk(cls):
    """Disk usage for root filesystem."""
    usage = PC.disk_usage('/')
    return {
      'total': usage.total,
      'used': usage.used,
      'free': usage.free,
      'percent': usage.percent,
    }

  @property
  def uptime(cls):
    """System uptime in seconds."""
    import time
    return time.time() - PC.boot_time()

  @property
  def processes(cls):
    """Number of running processes."""
    return len(PC.pids())



class CMDLib(metaclass=_MetaCMDLib):
  @staticmethod
  def which(cmd):
    return SHUTIL.which(cmd)

  @staticmethod
  def is_exe(cmd):
    """
    Check if a command is executable.

    This checks:
    - If the command is found in PATH (using shutil.which).
    - If the executable file has execute permissions (using os.access).

    :param cmd: Command name or path.
    :return: True if executable and has permissions, False otherwise.
    """
    path = SHUTIL.which(cmd)
    if path:
      return OS.access(path, OS.X_OK)
    return False

  @staticmethod
  def get_args(callback: callable = None):
    """Method to parse various formats of command line arguments

    Returns args (list) and kwargs (dict)
    Supports:
      --key value
      --key=value
      -k value
      -k=value
      -abc (multiple flags)
      positional arguments
      negative numbers as values (e.g., -n -5)
      repeated keys (collected into lists)
      multiple values per key (e.g., --key val1 val2 val3)
    """
    args = SYS.argv[1:]
    parsed = {}
    positional = []
    i = 0
    while i < len(args):
      arg = args[i]
      if arg.startswith('--'):
        key = arg[2:]
        values = []
        if '=' in key:
          key, val = key.split('=', 1)
          values.append(val)
        else:
          # Collect all following non-flag args as values
          while i + 1 < len(args) and not args[i + 1].startswith('-'):
            i += 1
            values.append(args[i])
        if values:
          if len(values) == 1:
            value = values[0]
          else:
            value = values
        else:
          value = True
        if key in parsed:
          if not isinstance(parsed[key], list):
            parsed[key] = [parsed[key]]
          if isinstance(value, list):
            parsed[key].extend(value)
          else:
            parsed[key].append(value)
        else:
          parsed[key] = value
      elif arg.startswith('-'):
        flags = arg[1:]
        if len(flags) == 1:
          key = flags
          values = []
          # Collect all following non-flag args as values
          while i + 1 < len(args) and not args[i + 1].startswith('-'):
            i += 1
            values.append(args[i])
          if values:
            if len(values) == 1:
              value = values[0]
            else:
              value = values
          else:
            value = True
          if key in parsed:
            if not isinstance(parsed[key], list):
              parsed[key] = [parsed[key]]
            if isinstance(value, list):
              parsed[key].extend(value)
            else:
              parsed[key].append(value)
          else:
            parsed[key] = value
        else:
          # Multiple flags like -abc
          for flag in flags:
            if flag in parsed:
              if not isinstance(parsed[flag], list):
                parsed[flag] = [parsed[flag]]
              parsed[flag].append(True)
            else:
              parsed[flag] = True
      else:
        positional.append(arg)
      i += 1

    callback_result = None
    if callback and callable(callback):
      callback_result = callback(*positional, **parsed)

    return positional, parsed, callback_result

  @staticmethod
  def run(cmd, capture_output=False, check=False, timeout=None, cwd=None, env=None, shell=None):
    """
    Run a command and optionally capture its output.

    This method provides efficient command execution with configurable subprocess parameters.
    It avoids shell=True by default for better security and performance, but allows it if needed.

    :param cmd: Command to run (string or list). If list, shell=False is used for efficiency.
    :param capture_output: If True, capture stdout and stderr.
    :param check: If True, raise CalledProcessError on non-zero exit code.
    :param timeout: Timeout in seconds; raises TimeoutExpired if exceeded.
    :param cwd: Working directory for the command.
    :param env: Environment variables dict; if None, inherits from parent.
    :param shell: If True, run via shell (less efficient, use with caution).
    :return: If capture_output=True, returns stdout (str). Else, returns returncode (int).
    :raises: subprocess.CalledProcessError if check=True and command fails.
    :raises: subprocess.TimeoutExpired if timeout is exceeded.

    Examples:
        # Simple command
        result = CMDLib.run(['echo', 'hello'])

        # Capture output
        output = CMDLib.run(['ls', '-l'], capture_output=True)

        # With timeout and check
        CMDLib.run(['sleep', '10'], timeout=5, check=True)
    """
    # Determine shell usage: default to False for lists, True for strings if not specified
    if shell is None:
      shell = isinstance(cmd, str)

    # Prepare kwargs for subprocess.run
    kwargs = {
      'capture_output': capture_output,
      'text'          : True,
      'check'         : check,
      'timeout'       : timeout,
      'cwd'           : cwd,
      'env'           : env,
      'shell'         : shell,
    }
    # Remove None values to avoid passing them
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    result = SUBPROCESS.run(cmd, **kwargs)

    if capture_output:
      return result.stdout
    return result.returncode

  @staticmethod
  def call(cmd):
    """Call a command in the shell and return the exit code."""
    return SYS.call(cmd, shell=True)

  @staticmethod
  def get_open_files():
    """Returns list of open files or open file handles by system"""
    _p = PC.Process()
    return _p.open_files()

  """System and Memory Statistics"""

  @staticmethod
  def get_system_stats():
    """
    Get comprehensive system statistics including CPU, memory, and swap.

    :return: Dict with keys: cpu_total, cpu_percent, memory_total, memory_available, memory_percent, swap_total, swap_free, swap_percent, processes
    """
    vm = PC.virtual_memory()
    sm = PC.swap_memory()
    return {
      'cpu_total': PC.cpu_count(logical=True),
      'cpu_percent': PC.cpu_percent(interval=0.1),
      'memory_total': vm.total,
      'memory_available': vm.available,
      'memory_percent': vm.percent,
      'swap_total': sm.total,
      'swap_free': sm.free,
      'swap_percent': sm.percent,
      'processes': len(PC.pids()),
    }

  @staticmethod
  def get_cpu_total():
    """Get total CPU count (logical cores)."""
    return PC.cpu_count(logical=True)

  @staticmethod
  def get_cpu_available():
    """Get available CPU percentage (100 - current usage)."""
    return 100 - PC.cpu_percent(interval=0.1)

  @staticmethod
  def get_threads_total():
    """Get total threads (approximated as logical CPUs)."""
    return PC.cpu_count(logical=True)

  @staticmethod
  def get_threads_available():
    """Get available threads percentage (approximated as 100 - CPU usage)."""
    return 100 - PC.cpu_percent(interval=0.1)

  @staticmethod
  def get_memory_total():
    """Get total RAM in bytes."""
    return PC.virtual_memory().total

  @staticmethod
  def get_memory_available():
    """Get available RAM in bytes."""
    return PC.virtual_memory().available

  @staticmethod
  def get_swap_total():
    """Get total swap memory in bytes."""
    return PC.swap_memory().total

  @staticmethod
  def get_swap_available():
    """Get available swap memory in bytes."""
    return PC.swap_memory().free

  @staticmethod
  def get_processes(limit=10):
    """
    Get list of top processes by CPU usage.

    :param limit: Number of top processes to return.
    :return: List of dicts with 'pid', 'name', 'cpu_percent'.
    """
    processes = []
    for proc in PC.process_iter():
      try:
        cpu_percent = proc.cpu_percent(interval=0.1)
        processes.append({
          'pid': proc.pid,
          'name': proc.name(),
          'cpu_percent': cpu_percent,
        })
      except (PC.NoSuchProcess, PC.AccessDenied):
        continue
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return processes[:limit]

  @staticmethod
  def kill(pid):
    """
    Terminate/kill a process by PID.

    :param pid: Process ID.
    :return: True if terminated, False if process not found.
    """
    try:
      proc = PC.Process(pid)
      proc.terminate()
      return True
    except PC.NoSuchProcess:
      return False
