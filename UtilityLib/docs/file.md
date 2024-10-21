Help on class FileSystemUtility in module UtilityLib.core.file:

class FileSystemUtility(UtilityLib.core.db.DatabaseUtility)
    FileSystemUtility(*args, **kwargs)

    Method resolution order:
        FileSystemUtility
        UtilityLib.core.db.DatabaseUtility
        UtilityLib.core.cmd.CommandUtility
        UtilityLib.core.log.LoggingUtility
        UtilityLib.core.time.TimeUtility
        UtilityLib.BaseUtility
        builtins.object

    Methods defined here:

    __init__(self, *args, **kwargs)
        Initialize self.  See help(type(self)) for accurate signature.

    add_tgz_files = _add_files_to_tar_gzip(self, *args, **kwargs)

    backup(self, *args, **kwargs)

    change_ext(self, *args, **kwargs)

    check_path(self, *args, **kwargs)
        Checks if path(s) exists or not

        @param
        0|path: String, path, or list of paths

        @return boolean
        True|False

    compress_dir = _compress_dir(self, *args, **kwargs)

    compress_gz = _compress_file_to_gzip(self, *args, **kwargs)

    compress_to_gzip = _compress_file_to_gzip(self, *args, **kwargs)

    compress_zip = _compress_dir(self, *args, **kwargs)

    conv_xml_to_dict = xml_to_dict(self, *args, **kwargs)

    convert_bytes(self, *args, **kwargs)
        Converts bytes to ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")... etc

        :params _bytes|0: float

    convert_xml_to_dict = xml_to_dict(self, *args, **kwargs)

    copy = _copy_from_to(self, *args, **kwargs)

    copy_file = _copy_from_to(self, *args, **kwargs)

    copy_to = _copy_from_to(self, *args, **kwargs)

    count_file_lines(self, *args, **kwargs)
        Quickly counts lines in a file or gz file
        @stats: counts lines in a 7GB gz file in 2min

    create_copy = _copy_from_to(self, *args, **kwargs)

    create_dir(self, *args, **kwargs) -> dict

    delete_file = delete_path(self, *args, **kwargs)

    delete_files(self, *args, **kwargs)
        Deletes multiple files or paths

    delete_path(self, *args, **kwargs)
        Deletes a file or directory

        @params
        0|path (str): File path
        1|flag_files_only (boolean): To keep directory structure but delete all the files

        @ToDo:
        Instead of deletion, move the entity to temporary directory to avoid any accidental loss of data

    dict_to_csv(self, *args, **kwargs)

    dir_exists = check_path(self, *args, **kwargs)

    download_content(self, *args, **kwargs)

    exists = check_path(self, *args, **kwargs)

    ext = file_ext(self, *args, **kwargs)

    ext_files = _walk_files_by_extension(self, *args, **kwargs)

    extract_zip = _uncompress_archive(self, *args, **kwargs)

    file_dir(self, *args, **kwargs)
        Returns parent directory path from the filepath

    file_exists = check_path(self, *args, **kwargs)

    file_ext(self, *args, **kwargs)
        Returns file fxtension

        @params
        0|file_path
        1|num_ext=1: Number of extension with a dot

    file_extension = file_ext(self, *args, **kwargs)

    file_name = filename(self, *args, **kwargs)

    filename(self, *args, **kwargs)
        @function
        Returns file_name from path <path>/<file_name>.<extn>.<ext2>.<ext1>

        @params
        0|file_path
        1|with_ext=default False
        2|with_dir=default False
        3|num_ext=default 1 or -1 to guess extensions

        @ToDo
        num_ext=-1 to guess extensions

    find_dirs = _search_dir_filter(self, *args, **kwargs)

    find_file_types = _walk_files_by_extension(self, *args, **kwargs)

    find_files = _search_file_filter(self, *args, **kwargs)

    from_JSON = read_json(self, *args, **kwargs)

    from_html = read_html(self, *args, **kwargs)

    from_json = read_json(self, *args, **kwargs)

    from_text = read_text(self, *args, **kwargs)

    get_existing(self, *args, **kwargs)
        Returns first existing path from the given list

        @extends check_path

    get_ext = file_ext(self, *args, **kwargs)

    get_extension = file_ext(self, *args, **kwargs)

    get_file(self, *args, **kwargs)
        @function
        downloads a url content and returns content of the file
        uses urlretrieve as fallback

        @return
        str|list
        None

        @params
        0|url (str):
        1|destination (None|str|path):
        2|return_text (bool):
        3|overwrite (False|bool): forces to download the content if file already exists
        4|form_values (None|dict): values to be submitted while downloading file from url USING GET METHOD
        5|headers: headers to set for downloading files
        6|method ("get"|"post"): method of downloading file

        @update
        * v20220905
          - Removed json parameter to use form_values instead of json

    get_file_content(self, *args, **kwargs)
        @extends get_file

        @function
        returns content of a file

    get_file_size(self, *args, **kwargs)
        Returns file size(s)

        :params file_path|0: string or iterable

        :returns: [(file_path, file_size, size_unit), ]

    get_file_types = _walk_files_by_extension(self, *args, **kwargs)

    get_open_file_descriptors(self, *args, **kwargs)

    get_pickle = read_pickle(self, *args, **kwargs)

    gz = _compress_file_to_gzip(self, *args, **kwargs)

    gzip = _compress_file_to_gzip(self, *args, **kwargs)

    html = read_html(self, *args, **kwargs)

    list_tgz_files(self, *args, **kwargs)

    list_tgz_items(self, *args, **kwargs)
        @bug: Doesn't renew file in loop due to path_tgz
        Workaround to assign path_tgz at the beginning of every loop.

    list_zip_files(self, *args, **kwargs)

    list_zip_items(self, *args, **kwargs)

    move(self, *args, **kwargs)
        Copies source and deletes using .delete_path

    parse_html(self, *args, **kwargs)

    parse_jsonl_gz(self, *args, **kwargs)

    parse_latex(self, *args, **kwargs)

    path_exists = check_path(self, *args, **kwargs)

    pickle = write_pickle(self, *args, **kwargs)

    pkl = write_pickle(self, *args, **kwargs)

    read(self, *args, **kwargs)
        @ToDo:
        - Guess type of file and return type based on the path, extension with exceptions
        @Temporarily resolves to read_text

    read_gz_file(self, *args, **kwargs)
        Reads gzipped files only (not tar.gz, tgz or a compressed file) line by line (fasta, txt, jsonl, csv, and tsv etc...)
        Can advance the counter to skip set of lines

    read_html(self, *args, **kwargs)

    read_json(self, *args, **kwargs)

    read_pickle(self, *args, **kwargs)
        @function
        reads pickle file

        @params
        0|source (str|path): File path
        1|default (any): default value to return if file not found
        2|flag_compressed (boolean): If file is gz compressed (other compressions are not implemented)

        @return
        None: if some error occurs
        python object after reading the pkl file

    read_text(self, *args, **kwargs)
        @ToDo
          * implement yield|generator to handle larger files
          * check if file extension is gz, try reading it as gz
          * `str.splitlines(keepends=False)`

    read_tgz_file(self, *args, **kwargs)

    read_xml(self, *args, **kwargs)

    read_zipfile(self, *args, **kwargs)

    rename(self, *args, **kwargs)

    save_json = write_json(self, *args, **kwargs)

    save_pickle = write_pickle(self, *args, **kwargs)

    save_xml = write_xml(self, *args, **kwargs)

    search = _search_file_filter(self, *args, **kwargs)

    search_dirs = _search_dir_filter(self, *args, **kwargs)

    search_file_types = _walk_files_by_extension(self, *args, **kwargs)

    search_files = _search_file_filter(self, *args, **kwargs)

    split_file(self, *args, **kwargs)
        WIP: Split file in smaller files

    text = read_text(self, *args, **kwargs)

    tgz = _compress_dir_to_tgz(self, *args, **kwargs)

    to_gz = _compress_file_to_gzip(self, *args, **kwargs)

    to_pickle = write_pickle(self, *args, **kwargs)

    to_pkl = write_pickle(self, *args, **kwargs)

    to_tgz = _compress_dir_to_tgz(self, *args, **kwargs)

    uncompress = _uncompress_archive(self, *args, **kwargs)

    unpickle = read_pickle(self, *args, **kwargs)

    unzip = _uncompress_archive(self, *args, **kwargs)

    validate_dir(self, *args, **kwargs)

    validate_path = validate_dir(self, *args, **kwargs)

    validate_subdir(self, *args, **kwargs)

    write(self, *args, **kwargs)
        @params
          0|destination:
          1|content
          2|append (boolean)
          3|encoding
          4|mode
          5|position: Write position by moving cursor

        @return
          check_path(destination)

    write_json(self, *args, **kwargs)
        @function
        Writes dict content as JSON

        @returns
        True|False if file path exists

    write_pickle(self, *args, **kwargs)
        @function
        Writes python object as pickle file

        @params
        0|destination (str|path)
        1|content (any): Python object for pickling

        @returns
        True|False if file path exists

        @update
          Uses GZip for compression
          File extension pkl.gz used against df.gz|pd.gz pickled files

    write_xml(self, *args, **kwargs)
        @function
        Writes XML string to file

        @returns
        True|False if file path exists

    xml_to_dict(self, *args, **kwargs)
        Converts XML to dict

        @returns
        dict of the converted xml

    zip(self, *args, **kwargs)

    ----------------------------------------------------------------------
    Methods inherited from UtilityLib.core.db.DatabaseUtility:

    connect_mysql(self, *args, **kwargs)

    connect_sqlite(self, *args, **kwargs)
        Connects with SQLite Database

        :param db_path|0: Path to SQLite Database File (Optionally to be created)
        :returns: str|None

    db_connect = connect_sqlite(self, *args, **kwargs)

    get_last_id(self, *args, **kwargs)
        @default
        table_name*
        id_column = "primary_id"
        engine: self.engine
        default: 0 (Default Last ID in case none found.)

        @returns
        max value from the provided `id_column`

        *required

    get_table_data(self, *args, **kwargs)
        Get SQLite or SQL Table Data

        * Use where dict object for where query
        * Read whole table, use chunksize for generator object for large tables)

        :param table_name|0: Default First Table
        :param where|1: Where Clause
        :param engine|2: Pass database Engine (Default self.engine)
        :param chunksize: See `pandas.read_sql_table`

        Returns:
          DataFrame|None: Pandas DataFrame

    insert(self, *args, **kwargs)
        @usage
        CLASS.insert("table_name", {
          'col_1': '5vr3',
          'col_2': 'DB12070',
          ...
          'col_N': None})

    query_datbase = _query_database(self, *args, **kwargs)

    query_db = _query_database(self, *args, **kwargs)

    set_table_data(self, *args, **kwargs)
        Function for pandas to update/insert table data using the initiated SQLite/MySQL engine
        [Ref](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html)

        @params
        3|if_exists: append|replace

    set_table_info(self, *args, **kwargs)

    sql_query = _query_database(self, *args, **kwargs)

    ----------------------------------------------------------------------
    Readonly properties inherited from UtilityLib.core.db.DatabaseUtility:

    tables

    ----------------------------------------------------------------------
    Methods inherited from UtilityLib.core.cmd.CommandUtility:

    __enter__(self)

    __exit__(self, *args, **kwargs)

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
    Readonly properties inherited from UtilityLib.core.cmd.CommandUtility:

    queue_done

    queue_failed
        Blocking

    queue_pending

    queue_running
        Blocking

    queue_task_status

    ----------------------------------------------------------------------
    Data and other attributes inherited from UtilityLib.core.cmd.CommandUtility:

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
