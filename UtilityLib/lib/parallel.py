"""
ParallelExecutor - Unified interface for threading, multiprocessing, and parallel execution

Provides:
- ThreadPoolExecutor for background task execution
- Semaphore-based concurrency control
- Queue-based task management with priority support
- Status tracking and monitoring
- Scheduled callbacks
- Decorators for parallel execution
"""

from functools import lru_cache as CacheMethod, wraps
from contextlib import contextmanager
from collections import deque
import logging as _logging
import concurrent.futures as ConcurrentFutures
import threading as Threading
import queue as QueueProvider
from .obj import ObjDict


class ParallelExecutor:
  """
  Manages parallel execution using threads, multiprocessing, and task queues.

  Features:
  - Background function execution
  - Queue-based task processing
  - Concurrency control via semaphores
  - Future tracking and status monitoring
  - Scheduled callbacks

  Usage:
    # Basic usage
    executor = ParallelExecutor(max_workers=16)
    future = executor.submit(my_function, arg1, arg2)

    # Queue-based processing
    executor.queue_task(process_item, item1)
    executor.queue_task(process_item, item2)
    executor.process_queue()

    # Context manager
    with ParallelExecutor() as executor:
      executor.queue_task(task1)
      executor.queue_task(task2)
      executor.process_queue(wait=True)
  """

  def __init__(self, max_workers=32, num_cores=8, *args, **kwargs):

    self.max_workers = max_workers
    self.num_cores = num_cores
    self.ConcurrentFutures = ConcurrentFutures
    self.Threading = Threading
    self.QueueProvider = QueueProvider
    self.thread_pool = None
    self.semaphore = None
    self.task_queue = None
    self._task_deque = deque()  # For position-based queue management
    self.future_objects = []
    self._task_metadata = []  # Track task names and metadata
    self._tasks_by_id = {}  # Map task_id to task data
    self._task_counter = 0  # Auto-incrementing task ID
    self._skipped_tasks = set()  # Track skipped task IDs
    self._schedule_mgr = None
    self._queue_schedule_ref = None
    self._system_resources = None  # Cache system resource info

    # Auto-initialize if requested
    if kwargs.get('auto_init', False):
      self.init()

  def get_system_resources(self, refresh=False):
    """
    Get comprehensive system resource information.

    :param refresh: Force refresh of cached data
    :return: ObjDict with system resource details

    Usage:
      resources = executor.get_system_resources()
      print(f"CPUs: {resources.cpu_count}, GPUs: {resources.gpu_count}")
      print(f"CPU Usage: {resources.cpu_usage_percent}%")
      print(f"Available workers: {resources.recommended_workers}")
    """
    if self._system_resources is not None and not refresh:
      return self._system_resources

    import os
    resources = {}

    # CPU Information
    try:
      resources['cpu_count_logical'] = os.cpu_count() or 1
      # Try to get physical cores
      try:
        import psutil
        resources['cpu_count_physical'] = psutil.cpu_count(logical=False) or resources['cpu_count_logical']
        resources['cpu_usage_percent'] = psutil.cpu_percent(interval=0.1)
        resources['cpu_usage_per_core'] = psutil.cpu_percent(interval=0.1, percpu=True)

        # Memory info
        mem = psutil.virtual_memory()
        resources['memory_total_gb'] = mem.total / (1024**3)
        resources['memory_available_gb'] = mem.available / (1024**3)
        resources['memory_usage_percent'] = mem.percent
        resources['memory_used_gb'] = mem.used / (1024**3)

        # Thread count
        resources['thread_count'] = len(psutil.Process().threads())
      except ImportError:
        resources['cpu_count_physical'] = resources['cpu_count_logical']
        resources['cpu_usage_percent'] = 0
        resources['cpu_usage_per_core'] = []
        resources['memory_total_gb'] = 0
        resources['memory_available_gb'] = 0
        resources['memory_usage_percent'] = 0
        resources['memory_used_gb'] = 0
        resources['thread_count'] = 1
    except Exception as e:
      _logging.error(f"PARALLEL_023: Error getting CPU info: {e}")
      resources['cpu_count_logical'] = 1
      resources['cpu_count_physical'] = 1
      resources['cpu_usage_percent'] = 0

    # GPU Information
    resources['gpu_count'] = 0
    resources['gpu_available'] = False
    resources['gpu_devices'] = []

    try:
      import torch
      if torch.cuda.is_available():
        resources['gpu_count'] = torch.cuda.device_count()
        resources['gpu_available'] = True
        resources['gpu_devices'] = [
          {
            'id': i,
            'name': torch.cuda.get_device_name(i),
            'memory_total_gb': torch.cuda.get_device_properties(i).total_memory / (1024**3),
            'memory_allocated_gb': torch.cuda.memory_allocated(i) / (1024**3),
            'memory_free_gb': (torch.cuda.get_device_properties(i).total_memory -
                              torch.cuda.memory_allocated(i)) / (1024**3)
          }
          for i in range(resources['gpu_count'])
        ]
    except ImportError:
      # Try pynvml for NVIDIA GPUs
      try:
        import pynvml
        pynvml.nvmlInit()
        resources['gpu_count'] = pynvml.nvmlDeviceGetCount()
        resources['gpu_available'] = resources['gpu_count'] > 0
        resources['gpu_devices'] = [
          {
            'id': i,
            'name': pynvml.nvmlDeviceGetName(pynvml.nvmlDeviceGetHandleByIndex(i)).decode('utf-8'),
            'memory_total_gb': pynvml.nvmlDeviceGetMemoryInfo(
              pynvml.nvmlDeviceGetHandleByIndex(i)).total / (1024**3),
            'memory_used_gb': pynvml.nvmlDeviceGetMemoryInfo(
              pynvml.nvmlDeviceGetHandleByIndex(i)).used / (1024**3),
            'memory_free_gb': pynvml.nvmlDeviceGetMemoryInfo(
              pynvml.nvmlDeviceGetHandleByIndex(i)).free / (1024**3)
          }
          for i in range(resources['gpu_count'])
        ]
        pynvml.nvmlShutdown()
      except (ImportError, Exception):
        pass

    # Calculate recommended workers based on system state
    cpu_available_percent = 100 - resources['cpu_usage_percent']
    cpu_available_cores = int((cpu_available_percent / 100) * resources['cpu_count_logical'])

    # Recommended workers: 2x available cores, but at least 2 and at most max_workers
    recommended = max(2, min(2 * max(1, cpu_available_cores), self.max_workers))
    resources['recommended_workers'] = recommended
    resources['busy_cores_estimate'] = resources['cpu_count_logical'] - cpu_available_cores
    resources['available_cores_estimate'] = cpu_available_cores

    # System load (if available)
    try:
      import psutil
      resources['system_load_1min'] = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
      resources['system_load_5min'] = psutil.getloadavg()[1] if hasattr(psutil, 'getloadavg') else 0
      resources['system_load_15min'] = psutil.getloadavg()[2] if hasattr(psutil, 'getloadavg') else 0
    except (ImportError, AttributeError):
      resources['system_load_1min'] = 0
      resources['system_load_5min'] = 0
      resources['system_load_15min'] = 0

    resources['timestamp'] = __import__('time').time()

    self._system_resources = ObjDict(resources)
    return self._system_resources

  def _get_max_workers(self):
    """Calculate optimal max_workers based on CPU cores and system load"""
    resources = self.get_system_resources()

    # Get the number of CPU cores available
    self.num_cores = min(resources.cpu_count_logical, self.num_cores)

    # Adjust max_workers based on available CPU cores and current usage
    if resources.cpu_usage_percent < 50:
      # System is under light load, use more workers
      optimal_workers = min(2 * self.num_cores, self.max_workers)
    elif resources.cpu_usage_percent < 80:
      # System is under moderate load
      optimal_workers = min(self.num_cores, self.max_workers)
    else:
      # System is under heavy load, be conservative
      optimal_workers = min(max(2, self.num_cores // 2), self.max_workers)

    self.max_workers = optimal_workers
    _logging.debug(f"PARALLEL_024: Adjusted max_workers to {self.max_workers} based on system load ({resources.cpu_usage_percent}% CPU usage)")
    return self.max_workers

  def init(self, *args, **kwargs):
    """Initialize the parallel execution environment"""
    self._get_max_workers()
    self.task_queue = self.QueueProvider.Queue()
    self.semaphore = self.Threading.Semaphore(self.max_workers - 1)
    self.thread_pool = self.ConcurrentFutures.ThreadPoolExecutor(max_workers=self.max_workers)

    _logging.debug(f"PARALLEL_001: Initialized with {self.num_cores} cores and {self.max_workers} max_workers")
    return self

  init_multiprocessing = init
  start_mp = init

  def submit(self, func, *args, **kwargs):
    """
    Submit a function for background execution using ThreadPoolExecutor.

    :param func: The function to execute
    :param args: Positional arguments for the function
    :param kwargs: Keyword arguments for the function
    :return: A Future object representing the execution

    Usage:
      future = executor.submit(some_function, arg1, arg2, kwarg1='value')
      result = future.result()  # Block until complete
    """
    if not hasattr(self, 'thread_pool') or self.thread_pool is None:
      self.init()

    func_name = getattr(func, '__name__', 'anonymous function')

    _logging.debug(f"PARALLEL_002: Submitting function '{func_name}' for background execution")
    try:
      _future = self.thread_pool.submit(func, *args, **kwargs)
      self.future_objects.append(_future)
      return _future
    except Exception as e:
      _logging.error(f"PARALLEL_003: Failed to submit function '{func_name}': {e}")
      return None

  run_bg = submit
  bg_func = submit
  func_bg = submit

  def queue(self, func, *args, position=None, name=None, **kwargs):
    """
    Queue a function for later execution with optional position control.

    Tasks are not executed immediately but stored in the queue.
    Call startAll() or process_queue() to execute all queued tasks.

    :param func: The function to queue
    :param args: Positional arguments for the function
    :param position: Queue position (None=append, 0=first, -1=last, int=specific position)
    :param name: Optional task name (defaults to function name)
    :param kwargs: Keyword arguments for the function
    :return: Task ID (int) for tracking, removal, or updates

    Usage:
      task_id1 = executor.queue(task1)                    # Append to end
      task_id2 = executor.queue(task2, position=0)        # Insert at beginning (highest priority)
      task_id3 = executor.queue(task3, position=-1)       # Append to end (same as no position)
      task_id4 = executor.queue(task4, position=2)        # Insert at specific position

      # Later you can reference by task_id
      executor.remove_task(task_id1)
      executor.skip_task(task_id2)
    """
    if self.task_queue is None:
      self.init()

    # Generate unique task ID
    task_id = self._task_counter
    self._task_counter += 1

    func_name = name or getattr(func, '__name__', 'anonymous')
    task_data = {
      'id': task_id,
      'func': func,
      'args': args,
      'kwargs': kwargs,
      'name': func_name,
      'position': None,  # Will be set when inserted
      'status': 'queued',
      'future': None
    }

    # Store in lookup dict
    self._tasks_by_id[task_id] = task_data

    # Handle position-based insertion
    if position is None:
      # Default: append to end
      self._task_deque.append(task_id)
      insert_pos = len(self._task_deque) - 1
    elif position == -1:
      # Explicit append to end
      self._task_deque.append(task_id)
      insert_pos = len(self._task_deque) - 1
    elif position == 0:
      # Insert at beginning (highest priority)
      self._task_deque.appendleft(task_id)
      insert_pos = 0
    else:
      # Insert at specific position
      temp_deque = deque()
      insert_pos = min(abs(position), len(self._task_deque))

      # Move items to temp
      for _ in range(insert_pos):
        if self._task_deque:
          temp_deque.append(self._task_deque.popleft())

      # Insert new task
      self._task_deque.appendleft(task_id)

      # Restore items from temp
      while temp_deque:
        self._task_deque.appendleft(temp_deque.pop())

    task_data['position'] = insert_pos
    _logging.debug(f"PARALLEL_004: Queued task '{func_name}' (ID={task_id}) at position {insert_pos}")
    return task_id

  def queue_task(self, func, *args, **kwargs):
    """
      Queue a function for later execution (legacy method).

      For position control, use queue() instead.

      :param func: The function to queue
      :param args: Positional arguments for the function
      :param kwargs: Keyword arguments for the function
      :return: Task ID
    """
    return self.queue(func, *args, **kwargs)

  def remove_task(self, task_id):
    """
    Remove a task from the queue by ID.

    :param task_id: The task ID returned from queue()
    :return: True if removed, False if not found or already running

    Usage:
      task_id = executor.queue(some_func)
      executor.remove_task(task_id)
    """
    if task_id not in self._tasks_by_id:
      _logging.debug(f"PARALLEL_014: Task {task_id} not found")
      return False

    task = self._tasks_by_id[task_id]

    if task['status'] != 'queued':
      _logging.debug(f"PARALLEL_015: Cannot remove task {task_id} - status: {task['status']}")
      return False

    # Remove from deque
    try:
      self._task_deque.remove(task_id)
      task['status'] = 'removed'
      _logging.debug(f"PARALLEL_016: Removed task {task_id} ({task['name']})")
      return True
    except ValueError:
      return False

  def skip_task(self, task_id):
    """
    Mark a task to be skipped during execution.

    :param task_id: The task ID returned from queue()
    :return: True if marked for skip, False if not found

    Usage:
      task_id = executor.queue(some_func)
      executor.skip_task(task_id)
      executor.startAll()  # This task will be skipped
    """
    if task_id not in self._tasks_by_id:
      return False

    self._skipped_tasks.add(task_id)
    self._tasks_by_id[task_id]['status'] = 'skipped'
    _logging.debug(f"PARALLEL_017: Marked task {task_id} for skipping")
    return True

  def unskip_task(self, task_id):
    """
    Unmark a task that was set to be skipped.

    :param task_id: The task ID to unskip
    :return: True if unmarked, False if not found
    """
    if task_id in self._skipped_tasks:
      self._skipped_tasks.remove(task_id)
      if task_id in self._tasks_by_id:
        self._tasks_by_id[task_id]['status'] = 'queued'
      _logging.debug(f"PARALLEL_018: Unmarked task {task_id} from skipping")
      return True
    return False

  def update_task(self, task_id, func=None, args=None, kwargs=None, name=None):
    """
    Update a queued task's parameters.

    :param task_id: The task ID to update
    :param func: New function (optional)
    :param args: New args tuple (optional)
    :param kwargs: New kwargs dict (optional)
    :param name: New task name (optional)
    :return: True if updated, False if not found or already running

    Usage:
      task_id = executor.queue(old_func, arg1)
      executor.update_task(task_id, func=new_func, args=(arg2,))
    """
    if task_id not in self._tasks_by_id:
      return False

    task = self._tasks_by_id[task_id]

    if task['status'] != 'queued':
      _logging.debug(f"PARALLEL_019: Cannot update task {task_id} - status: {task['status']}")
      return False

    if func is not None:
      task['func'] = func
    if args is not None:
      task['args'] = args
    if kwargs is not None:
      task['kwargs'] = kwargs
    if name is not None:
      task['name'] = name

    _logging.debug(f"PARALLEL_020: Updated task {task_id}")
    return True

  def get_task(self, task_id):
    """
    Get task information by ID.

    :param task_id: The task ID
    :return: ObjDict with task info, or None if not found

    Usage:
      task_id = executor.queue(func)
      info = executor.get_task(task_id)
      print(f"Task: {info.name}, Status: {info.status}")
    """
    if task_id not in self._tasks_by_id:
      return None

    task = self._tasks_by_id[task_id]
    return ObjDict({
      'id': task['id'],
      'name': task['name'],
      'status': task['status'],
      'position': task['position'],
      'has_future': task['future'] is not None,
      'done': task['future'].done() if task['future'] else False,
      'running': task['future'].running() if task['future'] else False,
    })

  def list_tasks(self, status=None):
    """
    List all tasks, optionally filtered by status.

    :param status: Filter by status ('queued', 'running', 'done', 'skipped', 'removed')
    :return: List of task IDs

    Usage:
      queued = executor.list_tasks(status='queued')
      all_tasks = executor.list_tasks()
    """
    if status is None:
      return list(self._tasks_by_id.keys())

    return [tid for tid, task in self._tasks_by_id.items() if task['status'] == status]

  def queue_timed_callback(self, callback=None, *args, **kwargs):
    """
    Schedule a callback to run after a specified interval.

    :param callback: The callback function to execute
    :param cb_interval: Time in seconds before executing callback (default: 300)
    :param args: Positional arguments for the callback
    :param kwargs: Keyword arguments for the callback
    """
    _cb_interval = kwargs.pop("cb_interval", 300)
    if callback is not None and callable(callback):
      _logging.debug(f'PARALLEL_005: Scheduling timed callback in {_cb_interval}s')
      Threading.Timer(_cb_interval, callback, args=args, kwargs=kwargs).start()

  def queue_final_callback(self, callback=None, *args, **kwargs):
    """
    Schedule a callback to run after all queued tasks complete.

    Uses ScheduleManager to periodically check if all tasks are done.
    Executes callback when queue is empty and all futures are complete.

    :param callback: The callback function to execute when all tasks complete
    :param cb_interval: Interval in seconds to check task status (default: 60)
    :param args: Positional arguments for the callback
    :param kwargs: Keyword arguments for the callback
    """
    if callback is not None and callable(callback):
      from .schedule import ScheduleManager

      _cb_interval = kwargs.pop("cb_interval", 60)

      # Lazily create a ScheduleManager per ParallelExecutor instance
      if not hasattr(self, "_schedule_mgr") or self._schedule_mgr is None:
        self._schedule_mgr = ScheduleManager()

      self._queue_schedule_ref = self._schedule_mgr.add(
        self._queue_final_cb_fn_bg_exe,
        interval=_cb_interval,
        unit="seconds",
        args=(callback, *args),
        **kwargs,
      )

      _logging.debug(f'PARALLEL_006: Scheduled final callback (check interval: {_cb_interval}s)')

  def _queue_final_cb_fn_bg_exe(self, callback, *args, **kwargs):
    """Internal method to check if all tasks are done and execute final callback"""
    _job_t, _job_d = self.queue_status.total, self.queue_status.done

    if any([_job_d < _job_t, len(self._task_deque) > 0]):
      _logging.debug(f'PARALLEL_007: Job Status: {_job_t - _job_d}/{_job_t} remaining')
    elif self._queue_schedule_ref is not None:
      _logging.debug(f'PARALLEL_008: All {self.queue_done} job(s) completed. Executing final callback...')
      callback(*args, **kwargs)
      self._queue_schedule_ref.stop()

  def process_queue(self, wait=False, *args, **kwargs):
    """
    Process all queued tasks using the thread pool.

    Acquires semaphore to limit concurrency, submits tasks from queue
    to the executor, and tracks futures. Skipped tasks are not executed.

    :param wait: If True, blocks until all tasks complete (default: False)
    :return: True when processing is initiated

    Usage:
      executor.queue_task(task1)
      executor.queue_task(task2)
      executor.process_queue(wait=True)  # Blocks until all tasks complete
    """
    if self.task_queue is None:
      self.init()

    _tasks_processed = 0
    _tasks_skipped = 0
    while self._task_deque:
      try:
        with self.semaphore:
          task_id = self._task_deque.popleft()

          # Skip if task was marked for skipping
          if task_id in self._skipped_tasks:
            _tasks_skipped += 1
            _logging.debug(f"PARALLEL_021: Skipping task {task_id}")
            continue

          # Get task data
          if task_id not in self._tasks_by_id:
            _logging.error(f"PARALLEL_022: Task {task_id} not found in registry")
            continue

          task = self._tasks_by_id[task_id]
          _func = task['func']
          _args = task['args']
          _kwargs = task['kwargs']

          # Submit to thread pool
          _ftr_obj = self.thread_pool.submit(_func, *_args, **_kwargs)
          self.future_objects.append(_ftr_obj)

          # Update task status
          task['status'] = 'running'
          task['future'] = _ftr_obj

          # Track task metadata
          self._task_metadata.append({
            'id': task_id,
            'func': task['name'],
            'future': _ftr_obj,
            'started': True
          })
          _tasks_processed += 1
      except Exception as e:
        _logging.error(f"PARALLEL_009: Error processing queue: {e}")

    _logging.debug(f"PARALLEL_010: Processed {_tasks_processed} tasks, skipped {_tasks_skipped}")
    self._shutdown(wait=wait, *args, **kwargs)
    return True

  def startAll(self, wait=False):
    """
    Start processing all queued tasks (fluent API).

    :param wait: If True, blocks until all tasks complete (default: False)
    :return: Self for method chaining

    Usage:
      executor.queue(task1).queue(task2).startAll(wait=True)
    """
    self.process_queue(wait=wait)
    return self

  start_all = startAll  # Alias for snake_case preference

  @property
  def queue_task_status(self):
    """Alias for queue_status (legacy compatibility)."""
    return self.queue_status

  def _shutdown(self, wait=False, *args, **kwargs):
    """Internal method to shutdown the executor"""
    _logging.debug(f'PARALLEL_011: Shutting down executor (wait={wait})')

    if wait and self.future_objects:
      # Wait for all tasks to complete
      self.ConcurrentFutures.wait(self.future_objects)

    # Shutdown the ThreadPoolExecutor
    if self.thread_pool is not None:
      self.thread_pool.shutdown(wait=wait)

  def shutdown(self, wait=True):
    """
    Shutdown the parallel executor.

    :param wait: If True, blocks until all pending futures complete (default: True)
    """
    self._shutdown(wait=wait)

  # Context manager support
  def __enter__(self):
    """Enter context: initialize multiprocessing"""
    _logging.debug('PARALLEL_012: Entering context, initializing executor')
    self.init()
    return self

  def __exit__(self, *args, **kwargs):
    """Exit context: shutdown executor"""
    _logging.debug('PARALLEL_013: Exiting context, shutting down executor')
    if self.thread_pool is not None:
      self.thread_pool.shutdown()

  # Status properties
  @property
  def queue_running(self):
    """Number of currently running tasks (blocking)"""
    if not self.future_objects:
      return 0
    return sum(map(lambda _fo: bool(_fo.running()),
                   self.ConcurrentFutures.as_completed(self.future_objects)))

  @property
  def queue_failed(self):
    """Number of tasks that failed with exceptions (blocking)"""
    if not self.future_objects:
      return 0
    return sum(map(lambda _fo: bool(_fo.exception()),
                   self.ConcurrentFutures.as_completed(self.future_objects)))

  @property
  def queue_done(self):
    """Number of completed tasks"""
    return self.queue_status.done

  @property
  def queue_pending(self):
    """Number of pending tasks"""
    return self.queue_status.pending

  @property
  def queue_status(self):
    """
    Get detailed status of all tasks.

    :return: ObjDict with keys: total, done, pending, queued, running, failed
    """
    _total = len(self.future_objects)
    _done = sum(map(lambda _fo: bool(_fo.done()), self.future_objects))
    _queued = len(self._task_deque)
    _running = sum(map(lambda _fo: bool(_fo.running()), self.future_objects))
    _failed = sum(map(lambda _fo: bool(_fo.exception()) if _fo.done() else False, self.future_objects))

    return ObjDict({
      "total"  : _total + _queued,
      "done"   : _done,
      "pending": _total - _done,
      "queued" : _queued,
      "running": _running,
      "failed" : _failed,
      "success": _done - _failed,
    })

  @property
  def status(self):
    """
    Get comprehensive status of executor and all tasks including system resources.

    :return: ObjDict with executor status, task breakdown, and system resources

    Usage:
      status = executor.status
      print(f"Total: {status.total}, Done: {status.done}, Running: {status.running}")
      print(f"CPUs: {status.system.cpu_count_logical}, Usage: {status.system.cpu_usage_percent}%")
    """
    task_status = self.queue_status

    # Add task details
    task_details = []
    for idx, metadata in enumerate(self._task_metadata):
      future = metadata.get('future')
      task_details.append({
        'id': idx,
        'name': metadata.get('func', 'unknown'),
        'done': future.done() if future else False,
        'running': future.running() if future else False,
        'failed': bool(future.exception()) if future and future.done() else False,
      })

    # Get current system resources
    system_resources = self.get_system_resources(refresh=True)

    return ObjDict({
      **task_status,
      'tasks': task_details,
      'has_queued': len(self._task_deque) > 0,
      'all_done': task_status.done == task_status.total and len(self._task_deque) == 0,
      'system': system_resources,
      'max_workers': self.max_workers,
    })

  def print_system_resources(self):
    """
    Print a formatted summary of system resources.

    Usage:
      executor = ParallelManager()
      executor.print_system_resources()
    """
    res = self.get_system_resources(refresh=True)

    print("\n" + "="*70)
    print("System Resources")
    print("="*70)

    print(f"\nCPU Information:")
    print(f"  Logical Cores:  {res.cpu_count_logical}")
    print(f"  Physical Cores: {res.cpu_count_physical}")
    print(f"  CPU Usage:      {res.cpu_usage_percent:.1f}%")
    print(f"  Available Est:  {res.available_cores_estimate} cores")
    print(f"  Busy Est:       {res.busy_cores_estimate} cores")

    if res.system_load_1min > 0:
      print(f"\nSystem Load:")
      print(f"  1 min:  {res.system_load_1min:.2f}")
      print(f"  5 min:  {res.system_load_5min:.2f}")
      print(f"  15 min: {res.system_load_15min:.2f}")

    if res.memory_total_gb > 0:
      print(f"\nMemory:")
      print(f"  Total:     {res.memory_total_gb:.1f} GB")
      print(f"  Available: {res.memory_available_gb:.1f} GB")
      print(f"  Used:      {res.memory_used_gb:.1f} GB ({res.memory_usage_percent:.1f}%)")

    if res.gpu_available:
      print(f"\nGPU Information:")
      print(f"  GPU Count: {res.gpu_count}")
      for gpu in res.gpu_devices:
        print(f"\n  GPU {gpu['id']}: {gpu.get('name', 'Unknown')}")
        if 'memory_total_gb' in gpu:
          used = gpu.get('memory_used_gb', gpu.get('memory_allocated_gb', 0))
          free = gpu.get('memory_free_gb', gpu['memory_total_gb'] - used)
          print(f"    Total Memory: {gpu['memory_total_gb']:.1f} GB")
          print(f"    Used Memory:  {used:.1f} GB")
          print(f"    Free Memory:  {free:.1f} GB")
    else:
      print(f"\nGPU: Not available")

    print(f"\nParallel Execution:")
    print(f"  Current Workers:     {self.max_workers}")
    print(f"  Recommended Workers: {res.recommended_workers}")
    print(f"  Active Threads:      {res.thread_count}")

    print("="*70 + "\n")

  @CacheMethod(maxsize=None)
  def _cache_wrapper(self, func, *args, **kwargs):
    """Cache wrapper for memoization of function results"""
    return func(*args, **kwargs)

  def map(self, func, *iterables, timeout=None, chunksize=1):
    """
    Map a function across iterables using the thread pool.

    :param func: The function to apply
    :param iterables: Iterables to map over
    :param timeout: Timeout for each function call
    :param chunksize: Size of chunks for processing
    :return: Iterator of results
    """
    if self.thread_pool is None:
      self.init()

    return self.thread_pool.map(func, *iterables, timeout=timeout, chunksize=chunksize)

  def wait_all(self, timeout=None, return_when='ALL_COMPLETED'):
    """
    Wait for all futures to complete.

    :param timeout: Maximum time to wait in seconds
    :param return_when: When to return ('ALL_COMPLETED', 'FIRST_COMPLETED', 'FIRST_EXCEPTION')
    :return: Named tuple with 'done' and 'not_done' sets
    """
    if not self.future_objects:
      return None

    return self.ConcurrentFutures.wait(
      self.future_objects,
      timeout=timeout,
      return_when=return_when
    )

  def as_completed(self, timeout=None):
    """
    Iterator over futures as they complete.

    :param timeout: Maximum time to wait
    :return: Iterator yielding futures as they complete
    """
    if not self.future_objects:
      return []

    return self.ConcurrentFutures.as_completed(self.future_objects, timeout=timeout)

  # ---------------------------------------------------------------------------
  # Decorators as Class Methods
  # ---------------------------------------------------------------------------

  def parallel(self, func=None):
    """
    Decorator to run a function in the background using this executor.

    :param func: The function to decorate
    :return: Decorated function that returns a Future

    Usage:
      executor = ParallelManager()

      @executor.parallel
      def long_task(x, y):
        return x + y

      future = long_task(1, 2)
      result = future.result()
    """
    def decorator(fn):
      @wraps(fn)
      def wrapper(*args, **kwargs):
        return self.submit(fn, *args, **kwargs)
      return wrapper

    if func is None:
      return decorator
    else:
      return decorator(func)

  def background(self, func):
    """
    Decorator to run a function in the background (fire-and-forget).

    Usage:
      executor = ParallelManager()

      @executor.background
      def send_notification(msg):
        pass

      send_notification('Done!')  # Returns immediately
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
      self.submit(func, *args, **kwargs)
    return wrapper

  def retry(self, max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):
    """
    Decorator to retry a function on failure.

    :param max_attempts: Maximum number of retry attempts
    :param delay: Initial delay between retries in seconds
    :param backoff: Multiplier for delay on each retry
    :param exceptions: Tuple of exceptions to catch and retry

    Usage:
      executor = ParallelManager()

      @executor.retry(max_attempts=5, delay=0.5)
      def flaky_api_call():
        pass
    """
    def decorator(func):
      @wraps(func)
      def wrapper(*args, **kwargs):
        attempt = 1
        current_delay = delay

        while attempt <= max_attempts:
          try:
            return func(*args, **kwargs)
          except exceptions as e:
            if attempt == max_attempts:
              raise

            import time
            time.sleep(current_delay)
            current_delay *= backoff
            attempt += 1

      return wrapper
    return decorator

  def throttle(self, calls_per_second=10):
    """
    Decorator to throttle function calls to a maximum rate.

    :param calls_per_second: Maximum calls allowed per second

    Usage:
      executor = ParallelManager()

      @executor.throttle(calls_per_second=5)
      def rate_limited_api():
        pass
    """
    import time
    import threading

    min_interval = 1.0 / calls_per_second
    lock = threading.Lock()
    last_called = [0.0]

    def decorator(func):
      @wraps(func)
      def wrapper(*args, **kwargs):
        with lock:
          elapsed = time.time() - last_called[0]
          left_to_wait = min_interval - elapsed

          if left_to_wait > 0:
            time.sleep(left_to_wait)

          last_called[0] = time.time()
          return func(*args, **kwargs)

      return wrapper
    return decorator


# Convenience aliases
ParallelManager = ParallelExecutor  # For the user's preferred naming
WorkerPool = ParallelExecutor
TaskExecutor = ParallelExecutor
