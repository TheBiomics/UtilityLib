from .project import ProjectManager

from seleniumwire import webdriver as WebDriver # pip install selenium-wire webdriver-manager mechanicalsoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import ui, expected_conditions # WebDriverWait, Select

class BrowserManager(ProjectManager):
  headless = True
  delay = 6
  implicit_wait = 10
  maximized = True
  def __init__(self, *args, **kwargs):
    self.wd_ui = ui
    self.wd_by = By
    self.wd_ec = expected_conditions
    self.wd_keys = Keys
    self._ensure_requirements()
    self.set_selectors()
    super().__init__(**kwargs)

  def _ensure_requirements(self):
    _req_imports = ['seleniumwire', 'blinker==1.7.0', 'webdriver_manager', 'mechanicalsoup']
    _flag_reqs = {pkg: self._is_package_installed(pkg.split('==')[0]) for pkg in _req_imports}
    _not_installed = [pkg for pkg, _is_inst in _flag_reqs.items() if not _is_inst]
    if len(_not_installed) > 1:
      self.cmd_run('pip uninstall blinker', shell=True)
      self.cmd_run("pip install " + " ".join(_not_installed), shell=True)

  def set_selectors(self, *args, **kwargs):
    self.by_id             = By.ID
    self.by_name           = By.NAME
    self.by_xpath          = By.XPATH
    self.by_link_text      = By.LINK_TEXT
    self.by_link_text_part = By.PARTIAL_LINK_TEXT
    self.by_tag            = By.TAG_NAME
    self.by_class          = By.CLASS_NAME
    self.by_css            = By.CSS_SELECTOR

  def get_status_code(self):
      _last_pg_req = [_r for _r in self.wd_instance.requests if _r.url == self.wd_instance.current_url]
      _last_pg_req = _last_pg_req[0] if len(_last_pg_req) > 0 else None
      self.wd_instance.last_page_request = _last_pg_req
      return _last_pg_req.response.status_code

  def screenshot(self, *args, **kwargs):
    _screenshot_path = args[0] if len(args) > 0 else kwargs.get("screenshot_path", 'screenshot.png')
    self.wd_instance.save_screenshot(_screenshot_path)

    _original_w_h = self.wd_instance.get_window_size()
    _req_width    = self.wd_instance.execute_script('return document.body.parentNode.scrollWidth')
    _req_height   = self.wd_instance.execute_script('return document.body.parentNode.scrollHeight')
    self.wd_instance.set_window_size(max([_req_width, 1440]), _req_height)
    # self.wd_instance.save_screenshot(_screenshot_path)  # has scrollbar
    self.wd_instance.find_element(self.wd_by.TAG_NAME, 'body').screenshot(_screenshot_path)
    self.wd_instance.set_window_size(_original_w_h['width'], _original_w_h['height'])

  def fullpage_screenshot(self, *args, **kwargs):
    _screenshot_path = args[0] if len(args) > 0 else kwargs.get("screenshot_path", 'screenshot.png')
    try:
      total_width  = self.wd_instance.execute_script("return document.body.scrollWidth")
      total_height = self.wd_instance.execute_script("return document.body.scrollHeight")
      self.wd_instance.set_window_size(total_width, total_height)
      self.wd_instance.save_screenshot(_screenshot_path)
    except Exception as e:
      print(f"Error capturing full-page screenshot: {e}")

  def wait(self, *args, **kwargs):
    _type = args[0] if len(args) > 0 else kwargs.get("type", 'implicit')
    if _type == 'implicit':
      self.wd_instance.implicitly_wait(self.implicit_wait)
    else:
      self.time_pause(self.delay)
    # elem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.NAME, 'chart')))

  def browse_url(self, *args, **kwargs):
    _url = kwargs.get("url", args[0] if len(args) > 0 else None)
    _file_path = kwargs.get("file_path", args[1] if len(args) > 1 else None)
    _screenshot_path = kwargs.get("screenshot_path", args[2] if len(args) > 2 else None)
    _render_js = kwargs.get("render_js", args[3] if len(args) > 3 else None)

    self.wd_instance.get(_url)
    if _render_js:
      self.wait("implicit")

    _html = self.wd_instance.page_source
    # _html = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")

    if _screenshot_path:
      self.screenshot(_screenshot_path)

    if _file_path:
      self.write(_file_path, _html)

    return _html

  def add_option(self, option):
    """Add a browser-specific option dynamically."""
    self.options.add_argument(option)

  def set_page_load_timeout(self, timeout=30):
    self.wd_instance.set_page_load_timeout(timeout)

  def get_performance_logs(self):
    try:
      logs = self.wd_instance.get_log("performance")
      return logs
    except Exception as e:
      print(f"Error fetching performance logs: {e}")
      return []

  def toggle_headless(self, enable=True):
    if enable:
      self.options.add_argument("--headless")
    else:
      if "--headless" in self.options.arguments:
        self.options.arguments.remove("--headless")

  def init_browser(self, browser_type='chrome', *args, **kwargs):
    if hasattr(self, 'wd_instance') and self.wd_instance:
      return  # Browser instance already initialized

    sw_options = {
      'disable_encoding'        : True,
      'verify_ssl'              : False,
      'request_storage_base_dir': './sel-store-temp', # store large bodies
      # 'request_storage'         : 'memory',           # or memory/disk
      'request_storage_max_size': 50 * 1024 * 1024  # 50 MB
    }

    try:
      if browser_type.lower() == 'chrome':
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as ChromeService
        self.wd_instance = WebDriver.Chrome(
          options=self.options,
          service=ChromeService(executable_path=ChromeDriverManager().install()),
          seleniumwire_options=sw_options
        )
      elif browser_type.lower() == 'firefox':
        from webdriver_manager.firefox import GeckoDriverManager
        self.wd_instance = WebDriver.Firefox(
          service=FirefoxService(executable_path=GeckoDriverManager().install()),
          seleniumwire_options=sw_options
        )
      else:
        raise ValueError(f"Unsupported browser type: {browser_type}")
      if self.maximized:
        self.wd_instance.maximize_window()
    except Exception as e:
      print(f"Error initializing {browser_type} browser: {e}")

  def execute_js(self, script, *args):
    try:
      return self.wd_instance.execute_script(script, *args)
    except Exception as e:
      print(f"Error executing JavaScript: {e}")

  def set_proxy(self, proxy_url):
    from selenium.webdriver.common.proxy import Proxy, ProxyType
    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.http_proxy = proxy_url
    proxy.ssl_proxy = proxy_url
    self.options.proxy = proxy

  def set_implicit_wait(self, wait_time):
    self.implicit_wait = wait_time
    self.wd_instance.implicitly_wait(self.implicit_wait)

  def close_browser(self, *args, **kwargs):
    if hasattr(self, 'wd_instance') and getattr(self, 'wd_instance'):
      try:
        self.wd_instance.close()
        self.wd_instance.quit()
      except Exception as _e:
        print(f"Failed to close/quit browser:: {_e}")

  close = close_browser

  def __exit__(self, exc_type, exc_value, traceback):
    self.close_browser()

  def __del__(self):
    self.close_browser()

class ChromeManager(BrowserManager):
  headless = True
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    if not hasattr(self, 'options'):
      from selenium.webdriver.chrome.options import Options as ChromeOptions
      self.options = ChromeOptions()  # Ensure options are initialized
    self._set_default_options()

  def _set_default_options(self):
    self.options.add_argument("--window-size=1920,1200")

    if self.headless:
      self.options.add_argument("--headless")

  def init_browser(self, *args, **kwargs):
    super().init_browser('chrome')

class FireFoxManager(BrowserManager):
  headless = True

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    if not hasattr(self, 'options') or not self.options:
      self.options = FirefoxOptions()
    self._set_default_options()

  def _set_default_options(self):
    self.options.add_argument("--width=1920")
    self.options.add_argument("--height=1080")
    if self.headless:
      self.options.add_argument("--headless")

  def init_browser(self, *args, **kwargs):
    if hasattr(self, 'wd_instance') and self.wd_instance:
        return  # Already initialized
    try:
      from webdriver_manager.firefox import GeckoDriverManager
      from selenium.webdriver.firefox.service import Service as FirefoxService
      self.wd_instance = WebDriver.Firefox(
        options=self.options,
        service=FirefoxService(executable_path=GeckoDriverManager().install())
      )
      if self.maximized:
        self.wd_instance.maximize_window()
    except Exception as e:
      print(f"Error initializing Firefox browser: {e}")

class BrowserlessManager(ProjectManager):
  browser = None
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.require("mechanicalsoup", 'MechSoup')
    self.browser = self.MechSoup.StatefulBrowser(raise_on_404=False)

  def browse_url(self, *args, **kwargs):
    _url = kwargs.get("url", args[0] if len(args) > 0 else None)
    _file_path = kwargs.get("file_path", args[1] if len(args) > 1 else None)

    self.browser.open(_url)

    _html = self.browser.page

    if not None is _file_path:
      self.write(_file_path, str(_html))

    return _html
