import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.exceptions import InsecureRequestWarning
from urllib3.util.ssl_ import create_urllib3_context

class SSLAdapter(HTTPAdapter):
  def __init__(self, ssl_context=None, **kwargs):
    self.ssl_context = ssl_context
    super().__init__(**kwargs)

  def init_poolmanager(self, *args, **kwargs):
    kwargs['ssl_context'] = self.ssl_context
    return super().init_poolmanager(*args, **kwargs)

  def proxy_manager_for(self, *args, **kwargs):
    kwargs['ssl_context'] = self.ssl_context
    return super().proxy_manager_for(*args, **kwargs)

class InsecureSession:
  def __init__(self):
    self.initialise_session()

  def initialise_session(self):
    # Suppress only insecure HTTPS warning for QA runs
    urllib3.disable_warnings(InsecureRequestWarning)
    # Create a custom SSL context
    ssl_context = create_urllib3_context()
    ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')  # Lower the security level if needed
    ssl_context.check_hostname = False  # Disable hostname checking
    self.session = requests.Session()
    self.session.verify = False
    self.session.mount("https://", SSLAdapter(ssl_context=ssl_context))

  def get(self, url, **kwargs):
    try:
      return self.session.get(url, **kwargs)
    except requests.exceptions.SSLError:
      if url.startswith("https://"):
        url = url.replace("https://", "http://", 1)
        return self.session.get(url, **kwargs)
      raise

  def post(self, url, **kwargs):
    try:
      return self.session.post(url, **kwargs)
    except requests.exceptions.SSLError:
      if url.startswith("https://"):
        url = url.replace("https://", "http://", 1)
        return self.session.post(url, **kwargs)
      raise

  def put(self, url, **kwargs):
    try:
      return self.session.put(url, **kwargs)
    except requests.exceptions.SSLError:
      if url.startswith("https://"):
        url = url.replace("https://", "http://", 1)
        return self.session.put(url, **kwargs)
      raise

  def delete(self, url, **kwargs):
    try:
      return self.session.delete(url, **kwargs)
    except requests.exceptions.SSLError:
      if url.startswith("https://"):
        url = url.replace("https://", "http://", 1)
        return self.session.delete(url, **kwargs)
      raise

SESSION = InsecureSession()

