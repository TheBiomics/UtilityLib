Help on class CommandUtility in module UtilityLib.core.cmd:

class CommandUtility(UtilityLib.core.log.LoggingUtility)
    CommandUtility(*args, **kwargs)

    Method resolution order:
        CommandUtility
        UtilityLib.core.log.LoggingUtility
        UtilityLib.core.time.TimeUtility
        UtilityLib.BaseUtility
        builtins.object

    Methods defined here:

    __enter__(self)

    __exit__(self, *args, **kwargs)

    __init__(self, *args, **kwargs)
        Initialize self.  See help(type(self)) for accurate signature.

    call_cmd = cmd_call(self, *args, **kwargs)

    call_command = cmd_call(self, *args, **kwargs)

    cmd_call(self, *args, **kwargs)
        Call a command without capturing output.

        :param command: The command to run.
        :return: The return code of the command.

    cmd_call_echo = cmd_run_mock(self, *args, **kwargs)

    cmd_call_mock = cmd_run_mock(self, *args, **kwargs)

    cmd_dry_run = cmd_run_mock(self, *args, **kwargs)

    cmd_is_exe = is_executable(self, program)

    cmd_run(self, *args, **kwargs)
        Run a command and capture the output.

        :param command: The command to run.
        :param newlines: Whether to treat the output as text with newlines.
        :return: The output of the command.

    cmd_run_mock(self, *args, **kwargs)
        Mocks cmd_run/cmd_call

    cmd_which(self, program)

    contextual_directory(self, new_path)
        A context manager for changing the current working directory
        later switches back to the original directory.

    flatten_args(self, *args, **kwargs)

    get_cli_args(self, *args, **kwargs)
        @example

        _cli_settings = {
          ...
          "db_path": (['-db'], None, None, 'Provide path to the database for Sieve project.', {}),
          "path_base": (['-b'], "*", [OS.getcwd()], 'Provide base directory to run the process.', {}),
          ...
        }

    guess_nargs_from_default(self, *args, **kwargs)

    init_cli(self, *args, **kwargs)

    init_multiprocessing(self, *args, **kwargs)

    is_exe = is_executable(self, program)

    is_executable(self, program)

    process_queue(self, *args, **kwargs)
        Process tasks from the queue
        # Acquire semaphore to limit concurrency
        # Get task from the queue
        # Submit task to the executor

    queue_final_callback(self, callback=None, *args, **kwargs) -> None

    queue_task(self, func, *args, **kwargs) -> None
        Queue a function operation

        @example:
        def method_to_execute(self, *arg, **kwargs):
          # Example function to be cached
          return arg ** 2

        _.init_multiprocessing
        _.queue_task(method_to_execute, *args, **kwargs)
        _.process_queue
        _.queue_final_callback

    queue_timed_callback(self, callback=None, *args, **kwargs) -> None

    run_cmd = cmd_run(self, *args, **kwargs)

    run_command = cmd_run(self, *args, **kwargs)

    start_mp = init_multiprocessing(self, *args, **kwargs)

    sys_open_files(self)
        Returns list of open files or open file handles by system

    unregistered_arg_parser(self, *args, **kwargs)
        Processes uregistered arguments from commandline

        @accepts
        List/Tuple

        @return
        dict() with/out values

    which = cmd_which(self, program)

    ----------------------------------------------------------------------
    Readonly properties defined here:

    queue_done

    queue_failed
        Blocking

    queue_pending

    queue_running
        Blocking

    queue_task_status

    ----------------------------------------------------------------------
    Data and other attributes defined here:

    future_objects = []

    max_workers = 32

    num_cores = 8

    semaphore = None

    task_queue = None

    thread_pool = None

    ----------------------------------------------------------------------
    Methods inherited from UtilityLib.core.log.LoggingUtility:

    debug = log_debug(self, *args, **kwargs)

    emergency = log_critical(self, *args, **kwargs)

    error = log_error(self, *args, **kwargs)

    error_traceback(self, _error)

    info = log_info(self, *args, **kwargs)

    log_critical(self, *args, **kwargs)

    log_debug(self, *args, **kwargs)

    log_error(self, *args, **kwargs)

    log_fail = log_critical(self, *args, **kwargs)

    log_info(self, *args, **kwargs)

    log_success = log_info(self, *args, **kwargs)

    log_warning(self, *args, **kwargs)

    set_logging(self, *args, **kwargs)
        Logging Setup

    warning = log_warning(self, *args, **kwargs)

    ----------------------------------------------------------------------
    Data and other attributes inherited from UtilityLib.core.log.LoggingUtility:

    LogHandler = None

    log_file_name = 'UtilityLib.log'

    log_file_path = None

    log_level = 'DEBUG'

    log_to_console = True

    log_to_file = True

    log_type = 'info'

    ----------------------------------------------------------------------
    Methods inherited from UtilityLib.core.time.TimeUtility:

    get_dt_stamp(self, *args, **kwargs)

    sleep = _sleep(self, *args, **kwargs)

    sleep_ms(self, *args, **kwargs)
        Sleep for certain `duration|0` in milliseconds.

    sleep_random(self, *args, **kwargs)
        Sleep for random seconds between `min|0` and `max|1`.

    time_break = _sleep(self, *args, **kwargs)

    time_elapsed(self, *args, **kwargs)

    time_end(self, *args, **kwargs)

    time_get(self)

    time_pause = _sleep(self, *args, **kwargs)

    time_sleep = _sleep(self, *args, **kwargs)

    time_start(self, *args, **kwargs)

    time_string(self, *args, **kwargs)

    wait = _sleep(self, *args, **kwargs)

    ----------------------------------------------------------------------
    Readonly properties inherited from UtilityLib.core.time.TimeUtility:

    date_stamp

    datestamp

    time_stamp

    timestamp

    ----------------------------------------------------------------------
    Methods inherited from UtilityLib.BaseUtility:

    __call__(self, *args, **kwargs)

    __repr__(self)

    __str__ = __repr__(self)

    from_import = _import_module_from(self, *args, **kwargs)

    import_from = _import_module_from(self, *args, **kwargs)

    import_many = _import_multiple_modules(self, *args, **kwargs)

    import_module = _import_single_module(self, *args, **kwargs)

    import_path = require_path(self, *args, **kwargs)

    is_running(self, *args, **kwargs)

    module_from = _import_module_from(self, *args, **kwargs)

    require = _import_single_module(self, *args, **kwargs)

    require_from = _import_module_from(self, *args, **kwargs)

    require_global = _import_single_module(self, *args, **kwargs)

    require_many = _import_multiple_modules(self, *args, **kwargs)

    require_path(self, *args, **kwargs)
        Imports a module through a path by adding the module path to system path

        @extends require
        To import from a given path by adding the path to the system

        @params
        0|module_path:
        1|module:

    set_attributes = _setattrs(self, kw)

    set_cwd = _set_working_dir(self, *args, **kwargs)

    set_project_paths(self, *args, **kwargs)
        Set current working directory

    setattrs = _setattrs(self, kw)

    setcwd = _set_working_dir(self, *args, **kwargs)

    update_attributes(self, obj=None, kw: dict = {}, defaults: dict = {})
        Sets and updates object attributes from dict

    ----------------------------------------------------------------------
    Data descriptors inherited from UtilityLib.BaseUtility:

    __dict__
        dictionary for instance variables (if defined)

    __weakref__
        list of weak references to the object (if defined)

    path_base

    pwd

    ----------------------------------------------------------------------
    Data and other attributes inherited from UtilityLib.BaseUtility:

    OS = <module 'os' from '/opt/miniconda3/envs/aiml3/lib/python3.8/os.py...

    SYS = <module 'sys' (built-in)>

    SYSTEM = <module 'sys' (built-in)>

    __build__ = '20240521'

    __description__ = 'Python Helper for Repetitive Tasks with File and Da...

    is_linux = None

    name = 'UtilityLib'

    version = '2.16'

    version_info = '2.16.20240521'
