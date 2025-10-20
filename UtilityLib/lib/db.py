class BaseDB:
  """Abstract minimal DB base class.

  Subclasses should implement `connect()` and `close()`.
  """
  def connect(self, *args, **kwargs):
    raise NotImplementedError()

  def close(self):
    raise NotImplementedError()


class SQLiteDB(BaseDB):
  """SQLite wrapper using sqlite3 from the standard library.

  Accepts a path string or an `EntityFile`.
  """
  def __init__(self, db_path: str):
    self.db_path = str(db_path)
    self.conn: Optional[sqlite3.Connection] = None
    self.connect(db_path)

  def connect(self, db_path: str):
    import sqlite3
    db_path = str(db_path)
    # Create or open the SQLite database file
    self.conn = sqlite3.connect(db_path)
    return self.conn

  def execute(self, sql: str, params: Optional[tuple[Any, ...]] = None):
    if self.conn is None:
      raise RuntimeError("Not connected to SQLite database")
    cur = self.conn.cursor()
    cur.execute(sql, params or ())
    return cur

  def commit(self):
    if self.conn:
      self.conn.commit()

  def close(self):
    if self.conn:
      self.conn.close()
      self.conn = None


class SQLDB(BaseDB):
  """Generic SQL DB placeholder.

  Replace or extend this with SQLAlchemy engine logic or specific DB drivers.
  """
  def __init__(self, dsn: str | dict[str, Any]):
    self.dsn = dsn
    self.engine = None

  def connect(self):
    # Integrate SQLAlchemy or specific drivers here if required
    self.engine = self.dsn
    return self.engine

  def close(self):
    # Dispose engine if applicable
    self.engine = None


class EntityDB:
  """Factory that returns a DB instance based on `source`.

  Rules used:
    - If `source` is a path string that ends with .db/.sqlite/.sqlite3 -> return SQLiteDB
    - If `source` is a dict or looks like a DSN -> return SQLDB
    - If `source` is an `EntityFile` pointing to a sqlite path -> SQLiteDB
  """
  def __new__(cls, source: Any, **kwargs):
    if isinstance(source, (str)) and EntityFile(source).parent().exists():
      return SQLiteDB(source)

    # If a dict or looks like a DSN (contains '://' or '@'), return SQLDB
    if isinstance(source, dict) or '://' in path or '@' in path:
      return SQLDB(source)

    return None
