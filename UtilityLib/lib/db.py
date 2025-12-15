"""Database utilities for UtilityLib with SQL, NoSQL, and file-based support."""
from typing import Any, Optional, Dict, List, Union
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import os as OS
import weakref
import threading

from .path import EntityPath
from .file import EntityFile
from .obj import ObjDict


# Database Instance Cache
class DBCache:
  """Singleton cache for database instances with TTL support."""
  _instance = None
  _lock = threading.Lock()

  def __new__(cls):
    if cls._instance is None:
      with cls._lock:
        if cls._instance is None:
          cls._instance = super().__new__(cls)
          cls._instance._cache = {}
          cls._instance._timestamps = {}
          cls._instance.default_ttl = 120  # Default 2 minutes, can be overridden per instance
    return cls._instance

  def get(self, key: str, ttl: int = None):
    """Get cached instance if it exists and hasn't expired."""
    if ttl is None:
      ttl = self.default_ttl

    if key in self._cache:
      timestamp = self._timestamps.get(key)
      if timestamp and (datetime.now() - timestamp).total_seconds() < ttl:
        instance = self._cache[key]
        # Check if it's a weakref
        if isinstance(instance, weakref.ref):
          instance = instance()
          if instance is None:
            # Object was garbage collected
            del self._cache[key]
            del self._timestamps[key]
            return None
        return instance
      else:
        # Expired
        del self._cache[key]
        del self._timestamps[key]
    return None

  def set(self, key: str, instance, use_weakref: bool = False):
    """Cache an instance with current timestamp."""
    if use_weakref:
      self._cache[key] = weakref.ref(instance)
    else:
      self._cache[key] = instance
    self._timestamps[key] = datetime.now()

  def clear(self, key: str = None):
    """Clear specific key or entire cache."""
    if key:
      self._cache.pop(key, None)
      self._timestamps.pop(key, None)
    else:
      self._cache.clear()
      self._timestamps.clear()

  def cleanup_expired(self, ttl: int = None):
    """Remove all expired entries."""
    if ttl is None:
      ttl = self.default_ttl

    now = datetime.now()
    expired_keys = [
      key for key, timestamp in self._timestamps.items()
      if (now - timestamp).total_seconds() >= ttl
    ]
    for key in expired_keys:
      del self._cache[key]
      del self._timestamps[key]

  def keys(self):
    """Get all cache keys."""
    return list(self._cache.keys())

  def get_timestamp(self, key: str):
    """Get timestamp for a specific cache key."""
    return self._timestamps.get(key)



class BaseDB:
  """Abstract base for all database operations."""

  # Mapping of standard keys to their aliases
  PARAM_ALIASES = {
    'user'    : ['username', 'db_user'],
    'password': ['pwd', 'db_password'],
    'database': ['db_name', 'db'],
    'host'    : ['db_host'],
    'port'    : ['db_port'],
    'path'    : ['db_path'],
    'db_type' : ['driver'],
  }

  # Default cache settings
  DEFAULT_CACHE_ENABLED = True
  DEFAULT_CACHE_TTL     = 60

  @staticmethod
  def normalize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize common parameter names to standard keys.

    Args:
      params: Dictionary of connection parameters

    Returns:
      Dictionary with normalized parameter names
    """
    normalized = params.copy()

    # For each standard key, check if any alias exists and normalize it
    for standard_key, aliases in BaseDB.PARAM_ALIASES.items():
      # Skip if standard key already exists
      if standard_key in normalized:
        continue

      # Check each alias and use the first one found
      for alias in aliases:
        if alias in normalized:
          # Special case: don't use 'db' as database if it's Redis 'db' parameter
          if alias == 'db' and 'db_type' in params and params.get('db_type') == 'redis':
            continue
          normalized[standard_key] = normalized.pop(alias)
          break

    return normalized

  def connect(self, *args, **kwargs):
    raise NotImplementedError()

  def close(self):
    raise NotImplementedError()

  def execute(self, sql: str, params: Optional[Any] = None):
    raise NotImplementedError()

  def commit(self):
    raise NotImplementedError()

  def rollback(self):
    raise NotImplementedError()


class TypeSQL(BaseDB):
  db_group     = 'sql'
  _table_info  = None
  _engine      = None
  _db_schema   = ObjDict()
  Session      = None
  _db_cache    = None  # Override in child classes
  _cache_prefix = None  # Override in child classes (e.g., 'sqlite:', 'sqldb:')

  @property
  def engine(self):
    """Get the SQLAlchemy engine. Auto-connects if not connected."""
    if self._engine is None:
      self.connect()
    return self._engine

  @property
  def is_connected(self) -> bool:
    """Check if database is currently connected."""
    return self._engine is not None

  def setup_session(self):
    """Initialize sessionmaker for ORM usage. Call after engine is created."""
    if self._engine and self.Session is None:
      from sqlalchemy.orm import sessionmaker
      self.Session = sessionmaker(bind=self._engine)
    return self.Session

  @contextmanager
  def get_session(self):
    """Context manager for ORM session with automatic commit/rollback.

    Example:
      >>> db = SQLiteDB('data.db')
      >>> with db.get_session() as session:
      ...     user = User(name='Alice')
      ...     session.add(user)
      ...     # Auto-commits on success, auto-rollback on error
    """
    if self.Session is None:
      self.setup_session()

    session = self.Session()
    try:
      yield session
      session.commit()
    except Exception:
      session.rollback()
      raise
    finally:
      session.close()

  with_session = get_session

  def _set_table_info(self):
    """Reflect database metadata to get table information."""
    if self.engine is None:
      return
    try:
      from sqlalchemy import MetaData

      _md = MetaData()
      _md.reflect(bind=self.engine)
      self._table_info = ObjDict(_md.tables)
    except:
      pass

  @property
  def tables(self):
    """Get table information from database metadata."""
    if self._table_info is None:
      self._set_table_info()
    return self._table_info

  def table_exists(self, table_name: str) -> bool:
    """Check if a table exists in the database."""
    return table_name in self.tables

  def get_table_schema(self, table_name: str) -> List[Dict]:
    """Get table schema information."""
    if table_name not in self.tables:
      raise ValueError(f"Table '{table_name}' does not exist in the database.")

    if not table_name in self._db_schema:
      from sqlalchemy import inspect
      inspector = inspect(self.engine)
      columns = inspector.get_columns(table_name)
      self._db_schema[table_name] = columns
      return columns

    return self._db_schema[table_name]

  @property
  def db_schema(self) -> Dict[str, List[Dict]]:
    """Get schema information for all tables in the database."""
    for table_name in self.tables._keys:
      self._db_schema[table_name] = self.get_table_schema(table_name)
    return self._db_schema

  def execute(self, sql: str, params: Optional[Dict] = None):
    """Execute SQL statement using SQLAlchemy.

    Args:
      sql: SQL statement
      params: Query parameters (dict)

    Returns:
      SQLAlchemy Result object
    """
    if self._engine is None:
      raise RuntimeError("Not connected to database")

    from sqlalchemy import text
    with self._engine.connect() as conn:
      result = conn.execute(text(sql), params or {})
      conn.commit()
      return result

  def fetchone(self, sql: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Execute query and fetch one result as dict.

    Args:
      sql: SQL query string
      params: Query parameters

    Returns:
      Dictionary of row data or None
    """
    result = self.execute(sql, params)
    row = result.fetchone()
    return dict(row._mapping) if row else None

  def fetchall(self, sql: str, params: Optional[Dict] = None) -> List[Dict]:
    """Execute query and fetch all results as list of dicts.

    Args:
      sql: SQL query string
      params: Query parameters

    Returns:
      List of dictionaries
    """
    result = self.execute(sql, params)
    return [dict(row._mapping) for row in result.fetchall()]

  def commit(self):
    """Commit is handled automatically by SQLAlchemy connection context."""
    pass

  def rollback(self):
    """Rollback is handled automatically by SQLAlchemy connection context."""
    pass

  def create_tables(self, BaseModel):
    """Create all tables defined in BaseModel that don't exist yet."""
    BaseModel.metadata.create_all(self.engine)

  def drop_tables(self, BaseModel):
    """Drop all tables defined in BaseModel."""
    BaseModel.metadata.drop_all(self.engine)

  def sync_tables(self, BaseModel, safe=True):
    """Synchronize database schema with model definitions.

    This will:
    - Create missing tables
    - Add missing columns to existing tables
    - Optionally modify column types (if safe=False)

    WARNING: Does NOT drop columns or tables. Use with caution in production.

    Args:
      BaseModel: SQLAlchemy Base class with model definitions
      safe: If True, only adds missing columns. If False, also modifies existing columns.

    Example:
      >>> Base = get_base_model()
      >>> class User(Base):
      ...     __tablename__ = 'users'
      ...     name = Column(String(100))
      >>>
      >>> db = SQLiteDB('data.db')
      >>> db.sync_tables(Base)  # Creates/updates tables automatically
    """
    from sqlalchemy import inspect

    inspector = inspect(self.engine)
    metadata = BaseModel.metadata

    # Get existing tables in database
    existing_tables = inspector.get_table_names()

    # Create missing tables
    for table_name, table in metadata.tables.items():
      if table_name not in existing_tables:
        table.create(self.engine)
        print(f"Created table: {table_name}")
      else:
        # Table exists, check for missing columns
        existing_columns = {col['name'] for col in inspector.get_columns(table_name)}

        for column in table.columns:
          if column.name not in existing_columns:
            # Add missing column
            column_type = column.type.compile(self.engine.dialect)
            nullable = "NULL" if column.nullable else "NOT NULL"
            default = ""

            if column.default is not None:
              if hasattr(column.default, 'arg'):
                if callable(column.default.arg):
                  # Skip functions like datetime.utcnow
                  default = ""
                else:
                  default = f"DEFAULT {column.default.arg}"

            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column_type} {nullable} {default}"

            try:
              self.execute(alter_sql)
              print(f"Added column: {table_name}.{column.name}")
            except Exception as e:
              print(f"Warning: Could not add column {table_name}.{column.name}: {e}")

  def close(self):
    """Dispose of the SQLAlchemy engine."""
    if self._engine:
      self._engine.dispose()
      self._engine = None
      self.Session = None

  @classmethod
  def clear_cache(cls, cache_key: str = None):
    """Clear cached instances.

    Args:
      cache_key: Specific cache key to clear, or None to clear all instances of this class
    """
    if not cls._db_cache or not cls._cache_prefix:
      return

    if cache_key:
      cls._db_cache.clear(cache_key)
    else:
      # Clear all entries with this class's prefix
      keys_to_clear = [k for k in cls._db_cache.keys() if k.startswith(cls._cache_prefix)]
      for key in keys_to_clear:
        cls._db_cache.clear(key)

  @classmethod
  def cache_info(cls):
    """Get information about cached instances."""
    if not cls._db_cache or not cls._cache_prefix:
      return []

    cached_keys = [k for k in cls._db_cache.keys() if k.startswith(cls._cache_prefix)]
    info = []
    for key in cached_keys:
      timestamp = cls._db_cache.get_timestamp(key)
      if timestamp:
        age = (datetime.now() - timestamp).total_seconds()
        info.append({
          'key': key.replace(cls._cache_prefix, ''),
          'age_seconds': round(age, 2),
          'expires_in': round(BaseDB.DEFAULT_CACHE_TTL - age, 2)
        })
    return info

class TypeNoSQL(BaseDB):
  db_group = 'nosql'


"""SQL Based DB Implementations"""

class SQLiteDB(TypeSQL):
  """SQLite wrapper using SQLAlchemy with context manager.

  Example:
    >>> db = SQLiteDB('data.db')
    >>> db.execute("CREATE TABLE users (id INT, name TEXT)")
    >>> result = db.execute("INSERT INTO users VALUES (1, 'Alice')")
    >>> for row in db.execute("SELECT * FROM users").fetchall():
    ...     print(row['name'])
    >>> db.close()
  """
  _db_cache = DBCache()
  _cache_prefix = 'sqlite:'

  def __init__(self, *args, **kwargs):
    self.db_path = kwargs.get('db_path', EntityPath(args[0]).resolved() if args else 'UtilityLib.db')
    self._engine = None
    self.echo = kwargs.pop('echo', False)
    self.flag_db_cache = kwargs.pop('flag_db_cache', BaseDB.DEFAULT_CACHE_ENABLED)
    self.cache_ttl = kwargs.pop('cache_ttl', BaseDB.DEFAULT_CACHE_TTL)
    self.engine_kwargs = kwargs

    # Check cache first
    if self.flag_db_cache:
      cache_key = f"sqlite:{self.db_path}"
      cached_instance = self._db_cache.get(cache_key, ttl=self.cache_ttl)
      if cached_instance is not None:
        # Reuse cached connection
        self._engine = cached_instance._engine
        self.Session = cached_instance.Session
        return

    self.connect()

    # Cache this instance
    if self.flag_db_cache:
      self._db_cache.set(cache_key, self)

  def __repr__(self):
    return f"SQLiteDB('{self.db_path}')"

  def __str__(self):
    return str(self.db_path)

  def connect(self, db_path: str = None):
    from sqlalchemy import create_engine
    if db_path:
      self.db_path = EntityPath(db_path).resolved()

    # Ensure parent directory exists
    EntityPath(self.db_path).parent().validate()

    # Build URI based on OS
    if OS.name == "nt":
      uri = f"sqlite:///{self.db_path}"
    else:
      uri = f"sqlite:////{self.db_path}"

    self._engine = create_engine(uri, echo=self.echo, **self.engine_kwargs)
    return self._engine

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()
    return False

class SQLDB(TypeSQL):
  """SQLAlchemy ORM wrapper with session management.

  Example:
    >>> # URI string
    >>> db = SQLDB('postgresql://user:pass@localhost/mydb')
    >>>
    >>> # Connection params
    >>> db = SQLDB(db_type='postgresql', user='root', password='pass', database='mydb')
    >>>
    >>> # Existing engine
    >>> db = SQLDB(my_engine)
    >>>
    >>> # With session
    >>> db.create_tables(Base)
    >>> with db.get_session() as session:
    ...     user = User(name='Alice')
    ...     session.add(user)
    >>> db.close()
  """
  _db_cache = DBCache()
  _cache_prefix = 'sqldb:'

  def __init__(self, *args, **kwargs):
    """
    Args:
      *args: URI string or Engine (optional positional)
      **kwargs: Connection parameters (db_type, user, password, host, port, database, echo, flag_db_cache, cache_ttl, etc.)
    """
    self.db_uri        = None
    self._engine       = None
    self.Session       = None
    self.echo          = kwargs.pop('echo', False)
    self.flag_db_cache = kwargs.pop('flag_db_cache', BaseDB.DEFAULT_CACHE_ENABLED)
    self.cache_ttl     = kwargs.pop('cache_ttl', BaseDB.DEFAULT_CACHE_TTL)
    self.engine_kwargs = {}

    # Extract first arg if provided
    _first_arg = args[0] if args else None

    # Check if first arg is an Engine
    if _first_arg is not None:
      try:
        from sqlalchemy.engine import Engine
        if isinstance(_first_arg, Engine):
          self._engine = _first_arg
          from sqlalchemy.orm import sessionmaker
          self.Session = sessionmaker(bind=self._engine)
          if hasattr(self._engine, 'url'):
            self.db_uri = str(self._engine.url)
          return
      except ImportError:
        pass

    if self._engine is None:
      if _first_arg and isinstance(_first_arg, str):
        # First arg is URI
        self.db_uri = _first_arg
      elif kwargs:
        # Build URI from kwargs
        self.db_uri = self._build_uri_from_params(kwargs)
        # Extract engine-specific kwargs - exclude all standard keys and their aliases
        reserved_keys = set()
        for standard_key, aliases in BaseDB.PARAM_ALIASES.items():
          reserved_keys.add(standard_key)
          reserved_keys.update(aliases)
        self.engine_kwargs = {k: v for k, v in kwargs.items() if k not in reserved_keys}
      else:
        raise ValueError("Either URI, engine, or connection parameters must be provided")

      # Check cache before creating new engine
      if self.flag_db_cache and self.db_uri:
        cache_key = f"sqldb:{self.db_uri}"
        cached_instance = self._db_cache.get(cache_key, ttl=self.cache_ttl)
        if cached_instance is not None:
          # Reuse cached connection
          self._engine = cached_instance._engine
          self.Session = cached_instance.Session
          return

      self.connect()

      # Cache this instance
      if self.flag_db_cache and self.db_uri:
        self._db_cache.set(cache_key, self)

      if self.db_uri is None and hasattr(self._engine, 'url'):
        self.db_uri = str(self._engine.url)

  def __repr__(self):
    if self.db_uri:
      # Mask password in URI for security
      uri = self.db_uri
      if '@' in uri and '://' in uri:
        parts = uri.split('://')
        if len(parts) == 2:
          protocol = parts[0]
          rest = parts[1]
          if '@' in rest:
            creds, host_part = rest.split('@', 1)
            if ':' in creds:
              user = creds.split(':')[0]
              uri = f"{protocol}://{user}:***@{host_part}"
      return f"SQLDB('{uri}')"
    return "SQLDB(engine=<Engine>)"

  def __str__(self):
    if self.db_uri:
      # Extract database name from URI
      if '/' in self.db_uri:
        db_name = self.db_uri.split('/')[-1]
        if db_name:
          return db_name
      return self.db_uri
    return "<SQLDB>"

  @staticmethod
  def _build_uri_from_params(config: Dict[str, Any]) -> str:
    """Build database URI from connection parameters."""
    # Normalize parameters first
    config = BaseDB.normalize_params(config)

    driver = config.get('db_type', 'mysql')

    # Normalize driver names
    driver_map = {
      'mysql'   : 'mysql+pymysql',
      'postgres': 'postgresql',
      'pg'      : 'postgresql',
    }
    driver = driver_map.get(driver.lower(), driver)

    # Handle SQLite
    if driver == 'sqlite' or driver.startswith('sqlite'):
      db_path = config.get('database', config.get('path', 'data.db'))
      if OS.name == "nt":
        return f"sqlite:///{db_path}"
      else:
        return f"sqlite:////{db_path}"

    # Handle SQL databases - all parameters already normalized
    user     = config.get('user', '')
    password = config.get('password', '')
    host     = config.get('host', 'localhost')
    port     = config.get('port', '')
    database = config.get('database', '')

    auth     = f"{user}:{password}@" if user and password else f"{user}@" if user else ""
    port_str = f":{port}" if port else ""
    return f"{driver}://{auth}{host}{port_str}/{database}"

  def connect(self):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    self._engine = create_engine(self.db_uri, echo=self.echo, **self.engine_kwargs)
    self.Session = sessionmaker(bind=self._engine)
    return self._engine

class NoSQLDB(TypeNoSQL):
  """NoSQL wrapper for MongoDB and Redis.

  Example:
    >>> # MongoDB
    >>> db = NoSQLDB('mongodb', {'host': 'localhost', 'port': 27017, 'database': 'mydb'})
    >>> db.insert_one('users', {'name': 'Alice', 'age': 30})
    >>> users = db.find('users', {'age': {'$gt': 25}})
    >>>
    >>> # Redis
    >>> db = NoSQLDB('redis', {'host': 'localhost', 'port': 6379, 'db': 0})
    >>> db.set('key', 'value')
    >>> value = db.get('key')
  """

  def __init__(self, db_type: str, connection_params: Dict[str, Any], **kwargs):
    self.db_type = db_type.lower()
    self.connection_params = connection_params
    self.kwargs = kwargs
    self._engine = None
    self.db = None
    self.connect()

  @property
  def engine(self):
    """Get the NoSQL database engine/client."""
    return self._engine

  def __repr__(self):
    return f"NoSQLDB('{self.db_type}', {self.connection_params})"

  def __str__(self):
    if self.db_type == 'mongodb':
      return self.connection_params.get('database', self.db.name if self.db else '<mongodb>')
    elif self.db_type == 'redis':
      db_num = self.connection_params.get('db', 0)
      return f"redis:db{db_num}"
    return f"<{self.db_type}>"

  def connect(self):
    if self.db_type == 'mongodb':
      return self._connect_mongodb()
    elif self.db_type == 'redis':
      return self._connect_redis()
    raise ValueError(f"Unsupported NoSQL type: {self.db_type}")

  def _connect_mongodb(self):
    try:
      from pymongo import MongoClient
    except ImportError:
      raise ImportError("Install pymongo: pip install pymongo")

    # Normalize parameters
    params = BaseDB.normalize_params(self.connection_params)

    # Check if URI is provided
    if 'uri' in params:
      uri = params['uri']
      self._engine = MongoClient(uri, **self.kwargs)
      # Extract database name from URI
      from urllib.parse import urlparse
      parsed = urlparse(uri)
      database = parsed.path.lstrip('/') if parsed.path else 'test'
      self.db = self._engine[database]
      return self.db

    # Build URI from connection params (all normalized)
    host = params.get('host', 'localhost')
    port = params.get('port', 27017)
    database = params.get('database', 'test')
    username = params.get('user')
    password = params.get('password')

    if username and password:
      connection_string = f"mongodb://{username}:{password}@{host}:{port}/"
    else:
      connection_string = f"mongodb://{host}:{port}/"

    self._engine = MongoClient(connection_string, **self.kwargs)
    self.db = self._engine[database]
    return self.db

  def _connect_redis(self):
    try:
      import redis
    except ImportError:
      raise ImportError("Install redis: pip install redis")

    # Check if URI is provided
    if 'uri' in self.connection_params:
      uri = self.connection_params['uri']
      self._engine = redis.from_url(uri, decode_responses=True, **self.kwargs)
      self.db = self._engine
      return self.db

    # Build from connection params
    self._engine = redis.Redis(
      host=self.connection_params.get('host', 'localhost'),
      port=self.connection_params.get('port', 6379),
      db=self.connection_params.get('db', 0),
      password=self.connection_params.get('password'),
      decode_responses=True,
      **self.kwargs
    )
    self.db = self._engine
    return self.db

  def execute(self, operation: str, *args, **kwargs):
    if self.db is None:
      raise RuntimeError(f"Not connected to {self.db_type}")

    if self.db_type == 'mongodb':
      collection_name = kwargs.pop('collection', args[0] if args else None)
      if not collection_name:
        raise ValueError("MongoDB operations require collection name")
      collection = self.db[collection_name]
      method = getattr(collection, operation)
      return method(*args[1:] if args else [], **kwargs)

    elif self.db_type == 'redis':
      method = getattr(self.db, operation)
      return method(*args, **kwargs)

  def find(self, collection: str, query: Dict = None, **kwargs) -> List[Dict]:
    if self.db_type != 'mongodb':
      raise NotImplementedError(f"find() not supported for {self.db_type}")
    return list(self.db[collection].find(query or {}, **kwargs))

  def find_one(self, collection: str, query: Dict = None, **kwargs) -> Optional[Dict]:
    if self.db_type != 'mongodb':
      raise NotImplementedError(f"find_one() not supported for {self.db_type}")
    return self.db[collection].find_one(query or {}, **kwargs)

  def insert_one(self, collection: str, document: Dict, **kwargs):
    if self.db_type != 'mongodb':
      raise NotImplementedError(f"insert_one() not supported for {self.db_type}")
    return self.db[collection].insert_one(document, **kwargs)

  def insert_many(self, collection: str, documents: List[Dict], **kwargs):
    """Insert multiple documents into MongoDB collection"""
    if self.db_type != 'mongodb':
      raise NotImplementedError(f"insert_many() not supported for {self.db_type}")

    return self.db[collection].insert_many(documents, **kwargs)

  def update_one(self, collection: str, query: Dict, update: Dict, **kwargs):
    if self.db_type != 'mongodb':
      raise NotImplementedError(f"update_one() not supported for {self.db_type}")
    return self.db[collection].update_one(query, update, **kwargs)

  def delete_one(self, collection: str, query: Dict, **kwargs):
    if self.db_type != 'mongodb':
      raise NotImplementedError(f"delete_one() not supported for {self.db_type}")
    return self.db[collection].delete_one(query, **kwargs)

  def get(self, key: str):
    if self.db_type != 'redis':
      raise NotImplementedError(f"get() not supported for {self.db_type}")
    return self._engine.get(key)

  def set(self, key: str, value: Any, **kwargs):
    if self.db_type != 'redis':
      raise NotImplementedError(f"set() not supported for {self.db_type}")
    return self._engine.set(key, value, **kwargs)

  def delete(self, *keys):
    if self.db_type != 'redis':
      raise NotImplementedError(f"delete() not supported for {self.db_type}")
    return self._engine.delete(*keys)

  def commit(self):
    pass

  def rollback(self):
    pass

  def close(self):
    if self._engine:
      self._engine.close()
      self._engine = None
      self.db = None

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()
    return False

class FileDB(TypeNoSQL):
  """File-based database with CSV, JSON, JSONL support using EntityFile.

  Example:
    >>> db = FileDB('data.csv')
    >>> db.insert([{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}])
    >>> users = db.find({'name': 'Alice'})
    >>> db.update({'id': 1}, {'name': 'Alice Smith'})
    >>> db.delete({'id': 2})
    >>> db.close()
  """

  def __init__(self, file_path: str, file_type: str = None, **kwargs):
    self.file = EntityFile(file_path)
    self.file_type = file_type or self._detect_file_type()
    self.encoding = kwargs.get('encoding', 'utf-8')
    self.cache_enabled = kwargs.get('cache', True)
    self._cache = None
    self._modified = False
    self.connect()

  def __repr__(self):
    return f"FileDB('{self.file.path}', file_type='{self.file_type}')"

  def __str__(self):
    return str(self.file.name)

  def _detect_file_type(self) -> str:
    ext = self.file.ext.lower() if self.file.ext else ''
    if ext in ['.csv', '.tsv']:
      return 'csv'
    elif ext == '.json':
      return 'json'
    elif ext == '.jsonl':
      return 'jsonl'
    raise ValueError(f"Unsupported extension: {ext}")

  def connect(self):
    if not self.file.exists():
      self.file.validate()
      self._cache = []
      self._save_cache()
    if self.cache_enabled:
      self._cache = self._load_file()
    return self

  def _load_file(self) -> List[Dict]:
    import json
    import csv

    if not self.file.exists():
      return []

    if self.file_type == 'csv':
      content = self.file.read_text()
      if not content.strip():
        return []
      reader = csv.DictReader(content.splitlines())
      return [dict(row) for row in reader]

    elif self.file_type == 'json':
      content = self.file.read_text()
      if not content.strip():
        return []
      data = json.loads(content)
      if isinstance(data, dict):
        return [data]
      return data if isinstance(data, list) else []

    elif self.file_type == 'jsonl':
      data = []
      for line in self.file.readlines():
        line = line.strip()
        if line:
          data.append(json.loads(line))
      return data

  def _save_cache(self):
    import json
    import csv
    from io import StringIO

    if self.file_type == 'csv':
      if not self._cache:
        self.file.write_text('', mode='w')
        return
      keys = set()
      for record in self._cache:
        keys.update(record.keys())
      keys = sorted(keys)
      output = StringIO()
      writer = csv.DictWriter(output, fieldnames=keys)
      writer.writeheader()
      writer.writerows(self._cache)
      self.file.write_text(output.getvalue(), mode='w')

    elif self.file_type == 'json':
      content = json.dumps(self._cache, indent=2, ensure_ascii=False)
      self.file.write_text(content, mode='w')

    elif self.file_type == 'jsonl':
      lines = [json.dumps(rec, ensure_ascii=False) for rec in self._cache]
      content = '\n'.join(lines) + '\n' if lines else ''
      self.file.write_text(content, mode='w')

    self._modified = False

  def execute(self, operation: str, *args, **kwargs):
    ops = {'find': self.find, 'insert': self.insert, 'update': self.update,
           'delete': self.delete, 'count': self.count}
    if operation not in ops:
      raise ValueError(f"Unsupported operation: {operation}")
    return ops[operation](*args, **kwargs)

  def find(self, query: Dict = None, limit: int = None) -> List[Dict]:
    if not self.cache_enabled:
      self._cache = self._load_file()

    if not query:
      results = self._cache
    else:
      results = [r for r in self._cache if all(r.get(k) == v for k, v in query.items())]

    return results[:limit] if limit else results

  def find_one(self, query: Dict = None) -> Optional[Dict]:
    results = self.find(query, limit=1)
    return results[0] if results else None

  def insert(self, record: Union[Dict, List[Dict]]):
    if not self.cache_enabled:
      self._cache = self._load_file()

    if isinstance(record, dict):
      self._cache.append(record)
    elif isinstance(record, list):
      self._cache.extend(record)
    else:
      raise ValueError("Record must be dict or list")

    self._modified = True
    return len(self._cache)

  def update(self, query: Dict, update: Dict) -> int:
    if not self.cache_enabled:
      self._cache = self._load_file()

    count = 0
    for record in self._cache:
      if all(record.get(k) == v for k, v in query.items()):
        record.update(update)
        count += 1

    if count > 0:
      self._modified = True
    return count

  def delete(self, query: Dict) -> int:
    if not self.cache_enabled:
      self._cache = self._load_file()

    original_length = len(self._cache)
    self._cache = [r for r in self._cache if not all(r.get(k) == v for k, v in query.items())]
    deleted = original_length - len(self._cache)
    if deleted > 0:
      self._modified = True
    return deleted

  def count(self, query: Dict = None) -> int:
    return len(self.find(query))

  def commit(self):
    if self._modified and self._cache is not None:
      self._save_cache()

  def rollback(self):
    self._cache = self._load_file()
    self._modified = False

  def close(self):
    if self._modified:
      self.commit()
    self._cache = None

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_type:
      self.rollback()
    else:
      self.commit()
    self.close()
    return False

  def to_dataframe(self):
    try:
      import pandas as pd
      return pd.DataFrame(self._cache or [])
    except ImportError:
      raise ImportError("Install pandas: pip install pandas")

  def to_dict_list(self) -> List[Dict]:
    return self._cache.copy() if self._cache else []


class EntityDB:
  """Factory returning appropriate DB instance based on path, engine, or settings.

  Parameters:
    *args: File path (str or EntityPath) or URI string (optional positional)
    engine: Existing SQLAlchemy Engine (keyword-only)
    **kwargs: Connection parameters (db_type, user, password, host, port, database, etc.)

  Examples:
    >>> # Path-based (auto-detected from extension)
    >>> db = EntityDB('data.db')
    >>> db = EntityDB('data.csv')
    >>> db = EntityDB(_path / 'test.db')  # Works with Path-like objects ✅

    >>> # URI string
    >>> db = EntityDB('postgresql://user:pass@localhost:5432/mydb')
    >>> db = EntityDB('mongodb://localhost:27017/mydb')

    >>> # Existing SQLAlchemy engine
    >>> db = EntityDB(engine=existing_engine)

    >>> # Connection parameters with db_type
    >>> db = EntityDB(db_type='mysql', user='root', password='pass', database='mydb')
    >>> db = EntityDB(db_type='mongodb', host='localhost', port=27017, database='mydb')

    >>> # No arguments - fallback to UtilityLib.db
    >>> db = EntityDB()
  """

  file_db_ext = {'.csv', '.json', '.jsonl', '.tsv'}
  sql_db_ext = {'.db', '.sqlite', '.sqlite3', '.db3'}

  @staticmethod
  def _is_sqlite_path(path: str) -> bool:
    if not isinstance(path, str):
      return False
    p = EntityPath(path)
    if p.suffix.lower() in {'.db', '.sqlite', '.sqlite3', '.db3'}:
      return True
    if '://' not in path and ('/' in path or '\\' in path):
      return True
    return False

  def __new__(cls, *args, **kwargs):
    # Extract first arg if provided
    _first_arg = args[0] if args else None

    if _first_arg is not None:
      try:
        from sqlalchemy.engine import Engine
        if isinstance(_first_arg, Engine):
          return SQLDB(_first_arg, **kwargs)
      except ImportError:
        pass

      # First arg is string or EntityPath
      if isinstance(_first_arg, (str, EntityPath)):
        path = str(_first_arg)

        # File extensions
        if any(path.endswith(ext) for ext in cls.file_db_ext):
          return FileDB(path, **kwargs)

        if any(path.endswith(ext) for ext in cls.sql_db_ext):
          return SQLiteDB(path, **kwargs)

        # URI strings
        if '://' in path:
          if path.startswith(('mongodb://', 'mongodb+srv://')):
            return NoSQLDB('mongodb', {'uri': path}, **kwargs)

          if path.startswith('redis://'):
            return NoSQLDB('redis', {'uri': path}, **kwargs)

          # Other SQL URIs e.g., postgresql, mysql
          return SQLDB(path, **kwargs)

    # Case 3: Connection params in kwargs
    db_type = kwargs.get('db_type') or kwargs.get('driver', '').lower()

    if db_type in ['mongodb', 'mongo', 'redis']:
      nosql_type = 'mongodb' if db_type in ['mongodb', 'mongo'] else 'redis'
      connection_params = {k: v for k, v in kwargs.items() if k not in ['db_type', 'nosql_type', 'driver']}
      return NoSQLDB(nosql_type, connection_params)

    if db_type in ['sqlite', 'sqlite3']:
      db_path = kwargs.get('database', kwargs.get('db_path', kwargs.get('path', 'data.db')))
      return SQLiteDB(db_path)

    if 'engine' in kwargs or db_type:
      return SQLDB(*args, **kwargs)

    # Case 4: Fallback to UtilityLib.db
    return SQLiteDB('UtilityLib.db')


def UTCNow():
  """Get current UTC time (compatible with Python 3.12+)"""
  return datetime.now(timezone.utc)


# Base Model for SQLAlchemy ORM

try:
  from sqlalchemy import Column, Integer, DateTime
  from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

  class TimestampMixin:
    # give timestamps a high sort_order so they end up after regular columns
    created_ts: Mapped[datetime] = mapped_column(DateTime, default=UTCNow, nullable=False, sort_order=1000)
    updated_ts: Mapped[datetime] = mapped_column(DateTime, default=UTCNow, onupdate=UTCNow, nullable=False, sort_order=1001)
    deleted_ts: Mapped[datetime] = mapped_column(DateTime, nullable=True, sort_order=1002)


  class BaseModel(DeclarativeBase, TimestampMixin):
    """Base model with common columns using SQLAlchemy 2.0 DeclarativeBase.

    All models extending this base will have:
    - id: Primary key with autoincrement (first column)
    - TimestampMixin

    Example:
      >>> from UtilityLib.lib.db import BaseModel
      >>> from sqlalchemy import Column, String
      >>>
      >>> class User(BaseModel):
      ...     __tablename__ = 'users'
      ...     name = Column(String(100), nullable=False)
      ...     email = Column(String(100), unique=True)
      >>>
      >>> # Column order: id, name, email, created_ts, updated_ts, deleted_ts
      >>> # Create all tables using `BaseModel.metadata.create_all(engine)`
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, sort_order=-100)


except ImportError:
  # If SQLAlchemy is not installed, BaseModel will be None
  print("Warning: SQLAlchemy not installed. BaseModel is unavailable. pip install sqlalchemy")
  BaseModel = None
