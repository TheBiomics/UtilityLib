import pandas as PD
import os as OS

# import mysql.connector as SQLConnector

from .CommandUtility import CommandUtility

class DatabaseUtility(CommandUtility):
  def __init__(self, *args, **kwargs):
    self.__defaults = {
        "debug": True,
        "db_path": "scrapper.db",
        "engine": None,
        "is_connected": False,
      }
    self.__defaults.update(kwargs)
    super(DatabaseUtility, self).__init__(**self.__defaults)

  def connect_mysql(self, *args, **kwargs):
    # My SQL Connection
    self.__update_attr(*args, **kwargs)
    if self.engine is None and self.db_name is not None:
      from sqlalchemy import create_engine
      self.engine = create_engine("mysql+pymysql://" + self.db_user + ":" + self.db_password + "@" + self.db_host + "/" + self.db_name)
    return self.engine

  def connect_sqlite(self, *args, **kwargs):
    self.db_path = args[0] if len(args) > 0 else kwargs.get("db_path", getattr(self, "db_path"))

    if self.is_connected:
      return self.db_path

    if len(self.db_path) > 3:
      from sqlalchemy import create_engine
      if OS.name == "nt":
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo = self.debug)
      else:
        self.engine = create_engine(f"sqlite:////{self.db_path}", echo = self.debug)

      self.is_connected = True
      return self.db_path
    else:
      raise Exception("Failed to connect to SQLite DB.")

  def db_connect(self, *args, **kwargs):
    self.update_attributes(self, kwargs)
    return self.connect_sqlite(**kwargs)

  # Accessory functions using pandas
  def set_table_data(self, *args, **kwargs):
    """
      Function for pandas to update/insert table data using the initiated SQLite/MySQL engine
    """
    _data_entries = args[0] if len(args) > 0 else kwargs.get("data")
    _table = args[1] if len(args) > 1 else kwargs.get("table_name")
    _if_exists = args[2] if len(args) > 2 else kwargs.get("if_exists", "append")
    _db_engine = args[3] if len(args) > 3 else kwargs.get("engine", self.engine)
    _chunk_size = args[4] if len(args) > 4 else kwargs.get("chunk_size", 50)
    _method = args[5] if len(args) > 5 else kwargs.get("method", 'multi')
    _index = args[6] if len(args) > 6 else kwargs.get("index", False)

    if isinstance(_data_entries, PD.DataFrame):
      return _data_entries.to_sql(_table, _db_engine, if_exists=_if_exists, chunksize = _chunk_size, method = _method, index = _index)
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
        _res = PD.read_sql(f"SELECT * FROM {_table} ORDER BY {_id_column} DESC LIMIT 1;", _db_engine)
        _res[_id_column] = _res[_id_column].astype(int)
        if len(_res.index) != 0:
          _last_id = int(_res[_id_column].values[0])
    except:
      self.log_error(f"Error in get_last_id for {_table}.")

    return _last_id

  def __correct_table_type(self, *args, **kwargs):
    _data = args[0] if len(args) > 0 else kwargs.get("data")
    _column_details = args[1] if len(args) > 1 else kwargs.get("column_details")

    if all([isinstance(_data, PD.DataFrame), _column_details, isinstance(_column_details, dict)]):
      for _key, _type in _column_details.items():
        if _key in _data.columns:
          _data[_key] = _data[_key].astype(_type)

    return _data

  def __empty_table_with_columns(self, *args, **kwargs):
    _column_details = args[0] if len(args) > 0 else kwargs.get("column_details")
    if _column_details is not None and isinstance(_column_details, dict):
      _columns = list(_column_details.keys())
      return PD.DataFrame(columns=_columns)
    return None

  def get_table_data(self, *args, **kwargs):
    _table = args[0] if len(args) > 0 else kwargs.get("table_name")
    _where = args[1] if len(args) > 1 else kwargs.get("where")
    _db_engine = args[2] if len(args) > 2 else kwargs.get("engine", self.engine)

    _db_entries = self.__empty_table_with_columns(**kwargs)

    if _table is None:
      return _db_entries

    try:
      if _where and isinstance(_where, dict):
        _where_clause = ""
        for _key in _where.keys():
          if _where[_key] is not None:
            if len(_where_clause) > 5:
              _where_clause = f" {_where_clause} AND "

            _where_val_connector = "=" if isinstance(_where[_key], str) else "IN"
            _where_values = repr(_where[_key]) if isinstance(_where[_key], str) else f"({', '.join(map(repr, _where[_key]))})"
            _where_clause = f"{_where_clause}{_key} {_where_val_connector} {_where_values}"

        _db_entries = PD.read_sql(f"SELECT * FROM {_table} WHERE {_where_clause}", _db_engine)
      else:
        _db_entries = PD.read_sql_table(_table, _db_engine)
    except:
      self.log_info(f"Some error occurred while accessing table '{_table}'.")

    _db_entries = self.__correct_table_type(_db_entries, **kwargs)
    return _db_entries
