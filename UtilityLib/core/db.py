from .cmd import CommandUtility
from ..lib.obj import ObjDict
from ..lib.path import EntityPath
from ..lib.db import EntityDB, SQLiteDB, SQLDB

class DatabaseUtility(CommandUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {
        "db_path"    : None,
        "engine"     : None,
        "_db_instance": None,
      }
    self.__defaults.update(kwargs)
    super().__init__(**self.__defaults)

  @property
  def tables(self):
    """Get table metadata from database engine."""
    return self._db_instance.tables if self._db_instance else {}

  @property
  def DB_Instance(self):
    """Get current database instance."""
    return self._db_instance

  def connect_mysql(self, *args, **kwargs):
    """Connect to MySQL/PostgreSQL database using EntityDB.

    :param args: Positional arguments for EntityDB
    :param kwargs: Keyword arguments (user, password, database, host, port, db_type, etc.)
    :return: SQLAlchemy engine
    """
    if self._db_instance is None or not isinstance(self._db_instance, SQLDB):
      self._db_instance = SQLDB(*args, **kwargs)
      if hasattr(self._db_instance, 'engine'):
        self.engine = self._db_instance.engine
    return self.engine

  def connect_sqlite(self, *args, **kwargs):
    """Wrapper method for lib.SQLiteDB

    :param args: Arguments passed to SQLiteDB
    :param kwargs: Keyword arguments passed to SQLiteDB
    :return: SQLAlchemy engine
    """
    if self._db_instance is None or not isinstance(self._db_instance, SQLiteDB):
      self._db_instance = SQLiteDB(*args, **kwargs)
      if hasattr(self._db_instance, 'engine'):
        self.engine = self._db_instance.engine
    return self.engine

  def connect_db(self, *args, **kwargs):
    """Connect to database using EntityDB.

    :param args: Positional arguments for EntityDB
    :param kwargs: Keyword arguments (user, password, database, host, port, db_type, etc.)
    :return: SQLAlchemy engine
    """
    if not args or not kwargs:
      kwargs['db_path'] = self.db_path

    if self._db_instance is None:
      self._db_instance = EntityDB(*args, **kwargs)
      if hasattr(self._db_instance, 'engine'):
        self.engine = self._db_instance.engine
    return self.engine

  db_connect = connect_db

  # Accessory functions using pandas
  def set_table_data(self, *args, **kwargs):
    """
      Function for pandas to update/insert table data using the initiated SQLite/MySQL engine
      [Ref](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html)

      @params
      3|if_exists: append|replace
    """
    _data_entries = args[0] if len(args) > 0 else kwargs.get("data")
    _table = args[1] if len(args) > 1 else kwargs.get("table_name")

    _db_engine = args[2] if len(args) > 2 else kwargs.get("engine", self.engine)

    _pandas_options = {
      "if_exists": args[3] if len(args) > 3 else kwargs.get("if_exists", "append"),
      "chunksize": args[4] if len(args) > 4 else kwargs.get("chunksize", 50),
      "method": args[5] if len(args) > 5 else kwargs.get("method", 'multi'),
      "index": args[6] if len(args) > 6 else kwargs.get("index"),
      "index_label": args[7] if len(args) > 7 else kwargs.get("index_label"),
    }

    _pandas_options = {k: v for k, v in _pandas_options.items() if v}
    if isinstance(_data_entries, self.PD.DataFrame):
      return _data_entries.to_sql(_table, _db_engine, **_pandas_options)
    else:
      raise Exception("[Error] Requires dataframe. Got some other data type.")

  def get_last_id(self, *args, **kwargs):
    """
      @default
      table_name*
      id_column = "primary_id"
      engine: self.engine
      default: 0 (Default Last ID in case none found.)

      @returns
      max value from the provided `id_column`

      *required
    """
    _table = args[0] if len(args) > 0 else kwargs.get("table_name")
    _id_column = args[1] if len(args) > 1 else kwargs.get("id_column", "primary_id")
    _db_engine = args[2] if len(args) > 2 else kwargs.get("engine", self.engine)
    _last_id = args[3] if len(args) > 3 else kwargs.get("default", 0)
    try:
      if all([_table, _id_column]):
        _res = self.PD.read_sql(f"SELECT * FROM {_table} ORDER BY {_id_column} DESC LIMIT 1;", _db_engine)
        _res[_id_column] = _res[_id_column].astype(int)
        if len(_res.index) != 0:
          _last_id = int(_res[_id_column].values[0])
    except:
      self.log_error(f"Error in get_last_id for {_table}.")

    return _last_id

  def __correct_table_type(self, *args, **kwargs):
    _data = args[0] if len(args) > 0 else kwargs.get("data")
    _column_details = args[1] if len(args) > 1 else kwargs.get("column_details")

    self.require('pandas', 'PD')
    if all([isinstance(_data, self.PD.DataFrame), _column_details, isinstance(_column_details, dict)]):
      for _key, _type in _column_details.items():
        if _key in _data.columns:
          _data[_key] = _data[_key].astype(_type)

    return _data

  def __empty_table_with_columns(self, *args, **kwargs):
    _column_details = args[0] if len(args) > 0 else kwargs.get("column_details")
    if _column_details is not None and isinstance(_column_details, dict):
      _columns = list(_column_details.keys())
      return self.PD.DataFrame(columns=_columns)
    return None

  def get_table_data(self, *args, **kwargs):
    """Get SQLite or SQL Table Data

    * Use where dict object for where query
    * Read whole table, use chunksize for generator object for large tables)

    :param table_name|0: Default First Table
    :param where|1: Where Clause
    :param engine|2: Pass database Engine (Default self.engine)
    :param chunksize: See `pandas.read_sql_table`

    Returns:
      DataFrame|None: Pandas DataFrame
    """
    _table = kwargs.pop("table_name", args[0] if len(args) > 0 else None)
    _where = kwargs.pop("where", args[1] if len(args) > 1 else None)
    _db_engine = kwargs.pop("engine", args[2] if len(args) > 2 else self.engine)

    _db_entries = self.__empty_table_with_columns(**kwargs)

    if _table is None and len(self.tables) > 0:
      _table = self.tables[0]

    try:
      self.require('pandas', 'PD')
      if _where and isinstance(_where, dict):
        _where_clause = ""
        for _key in _where.keys():
          if _where[_key] is not None:
            if len(_where_clause) > 5:
              _where_clause = f" {_where_clause} AND "

            _where_val_connector = "=" if isinstance(_where[_key], str) else "IN"
            _where_values = repr(_where[_key]) if isinstance(_where[_key], str) else f"({', '.join(map(repr, _where[_key]))})"
            _where_clause = f"{_where_clause}{_key} {_where_val_connector} {_where_values}"

        _db_entries = self.PD.read_sql(f"SELECT * FROM {_table} WHERE {_where_clause}", _db_engine, **kwargs)
      else:
        _db_entries = self.PD.read_sql_table(_table, _db_engine, **kwargs)
    except Exception as _e:
      self.log_info(f"Some error occurred while accessing table '{_table}': {_e}")

    _db_entries = self.__correct_table_type(_db_entries, **kwargs)
    return _db_entries

  def insert(self, *args, **kwargs):
    """
      @usage
      CLASS.insert("table_name", {
        'col_1': '5vr3',
        'col_2': 'DB12070',
        ...
        'col_N': None})
    """

    _table = kwargs.get("table", args[0] if len(args) > 0 else None)
    _values = kwargs.get("values", args[1] if len(args) > 1 else None) # dict

    _table_obj = self.tables.get(_table)

    if _values:
      return self.query(_table_obj.insert(), _values)

    return False

  def _query_database(self, *args, **kwargs):
    """Manual query to database

    :param query|0: sql statement
    :param query_params|1: Query parameters

    :returns: Result Iterator
    """
    self.query_last = kwargs.get("query", args[0] if len(args) > 0 else None)
    self.query_params = kwargs.get("query_params", args[1] if len(args) > 1 else None)

    from sqlalchemy import text as SQLText
    with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as _con:
      self.query_last_result = _con.execute(SQLText(self.query_last), self.query_params)

    return self.query_last_result

  sql_query = _query_database
  query_db = _query_database
  query_datbase = _query_database
