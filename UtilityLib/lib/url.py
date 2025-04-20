import requests
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

class EntityURL:
  """
  A versatile URL utility class for parsing, validating, and interacting with URLs.

  Features:
  ----------
  - Parse and retrieve URL components (scheme, netloc, path, etc.).
  - Check if a URL exists.
  - Save content of a URL to a file.
  - Estimate the size of the page.
  - Search for specific content within the page.
  """
  headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "*/*",  # Accept all content types
      }
  def __init__(self, url):
    self._URL = url
    self._original_url = url  # Store the original URL as a string
    self.parsed = urlparse(url)
    self._response = None  # Cache for the response

  @property
  def _ORIGINAL(self):
    """Access the originally passed URL as an EntityURL object."""
    return EntityURL(self._original_url)

  def reset(self):
    """Reset the URL to the originally passed URL."""
    self._URL = str(self._original_url)
    self.parsed = urlparse(self._URL)
    self._response = None  # Clear cached response as the URL has changed

  def _fetch_response(self):
    """Fetch and cache the response for the URL."""
    if self._response is None:
      try:
        response = requests.head(self._URL, headers=self.headers, allow_redirects=True)
        self._response = response
        if response.url != self._URL:  # If the URL was redirected
          self._URL = response.url
          self.parsed = urlparse(self._URL)
      except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        self._response = None

  @property
  def is_redirected(self):
    """Check if the URL was redirected."""
    self._fetch_response()
    return self._original_url != self._URL

  @property
  def status(self):
    """Get the status code of the URL."""
    self._fetch_response()
    return self._response.status_code if self._response else -1

  @property
  def exists(self):
    """
    Check if the URL exists or redirects.
    - Status codes < 300: Exists.
    - Status codes >= 500: Exists but server error.
    - Status codes between 300 and 404: Redirects or not found.
    """
    self._fetch_response()
    if not self._response:
      return False
    return self._response.status_code != 404

  def __str__(self):
    return self._URL

  @property
  def scheme(self):
    return self.parsed.scheme

  @property
  def netloc(self):
    """Get the host (netloc) of the URL."""
    return self.parsed.netloc

  @netloc.setter
  def netloc(self, new_host):
    """Set a new host (netloc) for the URL."""
    self.parsed = self.parsed._replace(netloc=new_host)
    self._URL = self.url

  # Alias `netloc` as `host`
  host = netloc

  @property
  def path(self):
    return self.parsed.path

  @property
  def params(self):
    return self.parsed.params

  @property
  def query(self):
    return self.parsed.query

  @property
  def fragment(self):
    return self.parsed.fragment

  @property
  def status(self):
    """Check if the URL is reachable."""
    try:
      response = requests.head(self._URL, allow_redirects=True)
      return response.status_code
    except requests.RequestException:
      return -1

  @property
  def exists(self):
    """
    Check if the URL exists or redirects.
    - Status codes < 300: Exists.
    - Status codes >= 500: Exists but server error.
    - Status codes between 300 and 404: Redirects or not found.
    """
    try:
      response = requests.head(self.url, allow_redirects=True)
      if response.status_code < 300 or response.status_code >= 500:
        return True
      return False
    except requests.RequestException:
      return False

  @property
  def url(self):
    """Reconstruct the URL from its components."""
    return urlunparse(self.parsed)

  def to_https(self):
    """Convert the scheme from http to https."""
    if self.scheme == 'http':
      self.parsed = self.parsed._replace(scheme='https')
      self._URL = self.url
    return self

  https = to_https
  force_https = to_https

  def __add__(self, modification):
    """
    Add query strings or path segments dynamically.
    - If `modification` is a dict, it updates query strings.
    - If `modification` is a string starting with '?', it replaces the query string.
    - If `modification` is a string, list, tuple, or set, it appends to the path.
    """
    if isinstance(modification, dict):
      # Update query string with the dictionary
      query_dict = parse_qs(self.parsed.query)
      query_dict.update(modification)
      new_query = urlencode(query_dict, doseq=True)
      self.parsed = self.parsed._replace(query=new_query)
    elif isinstance(modification, str):
      if modification.startswith('?'):
        # Replace the entire query string
        self.parsed = self.parsed._replace(query=modification.lstrip('?'))
      elif modification.startswith('#'):
        # Replace the fragment
        self.parsed = self.parsed._replace(fragment=modification.lstrip('#'))
      else:
        # Append to the path
        existing_path = self.parsed.path.rstrip('/')
        new_path = f"{existing_path}/{modification.lstrip('/')}"
        self.parsed = self.parsed._replace(path=new_path)
    elif isinstance(modification, (list, tuple, set)):
      # Append list/tuple/set elements as path segments
      existing_path = self.parsed.path.rstrip('/')
      new_path_segments = "/".join(map(str, modification))
      new_path = f"{existing_path}/{new_path_segments}"
      self.parsed = self.parsed._replace(path=new_path)
    self._URL = self.url
    return self

  def __sub__(self, modification):
    """
    Remove query strings or path segments dynamically.
    - If `modification` is a dict, it removes specific query parameters.
    - If `modification` is a string, it removes the matching path segment or fragment.
    """
    if isinstance(modification, dict):
      query_dict = parse_qs(self.parsed.query)
      for key in modification.keys():
        query_dict.pop(key, None)
      new_query = urlencode(query_dict, doseq=True)
      self.parsed = self.parsed._replace(query=new_query)
    elif isinstance(modification, str):
      if modification == '?':
        # Remove the QS
        self.parsed = self.parsed._replace(query='')
      if modification == '#':
        # Remove the fragment
        self.parsed = self.parsed._replace(fragment='')
      else:
        # Remove matching path segment
        existing_path = self.parsed.path.split('/')
        new_path = '/'.join([segment for segment in existing_path if segment != modification])
        self.parsed = self.parsed._replace(path=new_path)
    elif isinstance(modification, (list, tuple, set)):
      # Remove matching path segments
      existing_path = self.parsed.path.split('/')
      to_remove = set(map(str, modification))
      new_path = '/'.join([segment for segment in existing_path if segment not in to_remove])
      self.parsed = self.parsed._replace(path=new_path)
    self._URL = self.url
    return self

  def __truediv__(self, modification):
    """
    Replace the path part of the URL with the given value.
    - If `modification` is a string, it sets it as the new path.
    - If `modification` is a list, tuple, or set, it joins elements with '/'.
    - If `modification` is a dict, it converts to a query string and appends.
    """
    if isinstance(modification, str):
      # Replace the entire path with the string
      self.parsed = self.parsed._replace(path=modification.lstrip('/'))
    elif isinstance(modification, (list, tuple, set)):
      # Replace the path with a '/'-joined string
      new_path = "/".join(map(str, modification))
      self.parsed = self.parsed._replace(path=new_path)
    elif isinstance(modification, dict):
      # Convert dictionary to key/value pairs and append as path segments
      new_path = "/".join(f"{k}/{v}" for k, v in modification.items())
      self.parsed = self.parsed._replace(path=new_path)
    self._URL = self.url
    return self

  __floordiv__ = __truediv__

  def add_query(self, key, value):
    """Add a single query parameter."""
    return self + {key: value}

  def replace_fragment(self, fragment):
    """Replace the fragment."""
    return self + f"#{fragment}"

  def remove_fragment(self):
    """Remove the fragment."""
    return self - "#"

  @property
  def host_exists(self):
    """Check if the host (netloc) exists by resolving the domain."""
    import socket
    try:
      socket.gethostbyname(self.netloc)
      return True
    except socket.error:
      return False

  @property
  def is_www(self):
    """
    Verify if the host has a `www.` prefix.
    Returns:
      bool: True if `www.` is present, False otherwise.
    """
    return self.netloc.startswith('www.')

  def force_www(self):
    """
    Enforce the presence of `www.` in the host.
    - Adds `www.` if not present.
    """
    if not self.is_www:
      self.parsed = self.parsed._replace(netloc=f"www.{self.netloc}")
      self._URL = self.url
    return self
