"""
DOM Schema Parser - Direct Selenium driver references

Example:
  schema = DOMSchema(driver)

  email = schema.first(placeholder='Email')
  email.send_keys('user@example.com')

  button = schema.first('sign in', tag='button')
  button.click()
"""

from collections import defaultdict
import platform, time, random, re
from typing import List, Dict, Optional, Any


class DOMNode:
  """DOM node with direct Selenium WebElement reference."""

  def __init__(self, webelement: Any, driver: Any, index: int = 0):
    """
    Create DOMNode from Selenium WebElement.

    Args:
      webelement: Selenium WebElement (cached reference)
      driver: Selenium WebDriver
      index: Element index for path reference
    """
    self._cached_webelement = webelement
    self._driver = driver
    self.index = index

    # Get all attributes in one JavaScript call (faster than multiple get_attribute calls)
    script = """
    var el = arguments[0];
    var result = {
      tag: el.tagName.toLowerCase(),
      text: el.textContent || '',
      attrs: {}
    };
    for (var i = 0; i < el.attributes.length; i++) {
      var attr = el.attributes[i];
      result.attrs[attr.name] = attr.value;
    }
    return result;
    """
    try:
      data = driver.execute_script(script, webelement)
      self.tag = data['tag']
      self.text = data['text'].strip()
      self.attrs = data['attrs']

      # Handle class as list for consistency
      if 'class' in self.attrs:
        self.attrs['class'] = self.attrs['class'].split()
    except Exception:
      # Fallback to slow method if JS fails
      self.tag = webelement.tag_name.lower()
      self.text = webelement.text.strip() if webelement.text else ""
      self.attrs = {}

  def get(self, key: str, default: Any = None) -> Any:
    """Get attribute value."""
    return self.attrs.get(key, default)

  @property
  def webelement(self) -> Any:
    """Get Selenium WebElement - returns cached driver reference."""
    if self._driver is None:
      raise ValueError("No driver available.")

    if self._cached_webelement is None:
      raise ValueError(f"No cached WebElement for {self.tag}. Recreate DOMSchema.")

    # Validate cached element is still accessible
    from selenium.common.exceptions import StaleElementReferenceException
    try:
      _ = self._cached_webelement.tag_name
      return self._cached_webelement
    except StaleElementReferenceException:
      raise ValueError(f"Element {self.tag} is stale. Recreate DOMSchema to refresh references.")

  def click(self, use_js: bool = False) -> None:
    """
    Click element.

    Args:
      use_js: Force JavaScript click (default: False)
    """
    if use_js:
      self._driver.execute_script("arguments[0].click();", self.webelement)
    else:
      try:
        self.webelement.click()
      except Exception:
        # Fallback to JavaScript click if regular click fails
        self._driver.execute_script("arguments[0].click();", self.webelement)

  def send_keys(self, *value, clear: bool = False) -> None:
    """
    Send keys to element.

    Args:
      *value: Keys to send
      clear: Clear element before sending keys using OS-independent method
    """
    if clear:
      self.clear()
    self.webelement.send_keys(*value)

  def clear(self) -> None:
    """Clear element using cross-platform select-all + delete."""
    from selenium.webdriver.common.keys import Keys
    import platform

    # Use Command on Mac, Control on Windows/Linux
    modifier = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
    self.webelement.send_keys(modifier + 'a')
    self.webelement.send_keys(Keys.BACKSPACE)

  def get_attribute(self, name: str) -> Optional[str]:
    """Get attribute from Selenium element."""
    return self.webelement.get_attribute(name)

  def is_displayed(self) -> bool:
    """Check if element is displayed."""
    return self.webelement.is_displayed()

  def is_enabled(self) -> bool:
    """Check if element is enabled."""
    return self.webelement.is_enabled()

  @property
  def flag_exists(self) -> bool:
    """
    Check if element is still present in the DOM.

    Returns:
      True if element is present and accessible, False otherwise
    """
    try:
      elem = self.webelement
      _ = elem.tag_name
      return True
    except Exception:
      return False

  def scroll_into_view(self) -> None:
    """Scroll element into view."""
    self._driver.execute_script("arguments[0].scrollIntoView(true);", self.webelement)

  def highlight(self, duration: float = 1.0) -> None:
    """Highlight element temporarily (useful for debugging)."""
    original_style = self.webelement.get_attribute('style')
    self._driver.execute_script(
      "arguments[0].setAttribute('style', arguments[1]);",
      self.webelement,
      "border: 2px solid red; background-color: yellow;"
    )
    time.sleep(duration)
    self._driver.execute_script(
      "arguments[0].setAttribute('style', arguments[1]);",
      self.webelement,
      original_style or ""
    )

  @property
  def innerHTML(self) -> str:
    """Get innerHTML of element."""
    return self._driver.execute_script("return arguments[0].innerHTML;", self.webelement)

  @property
  def outerHTML(self) -> str:
    """Get outerHTML of element."""
    return self._driver.execute_script("return arguments[0].outerHTML;", self.webelement)

  @property
  def soup(self):
    """Get BeautifulSoup object from innerHTML for scraping/parsing."""
    try:
      from bs4 import BeautifulSoup
      return BeautifulSoup(self.innerHTML, 'html.parser')
    except ImportError:
      raise ImportError("BeautifulSoup4 is required for soup property. Install: pip install beautifulsoup4")

  @property
  def info(self) -> Dict[str, Any]:
    """Get debug information about this node."""
    info = {
      'tag': self.tag,
      'attrs': self.attrs,
      'text': self.text,
      'index': self.index,
    }
    if self._driver:
      try:
        elem = self.webelement
        info['selenium_tag'] = elem.tag_name
        info['is_displayed'] = elem.is_displayed()
        info['is_enabled'] = elem.is_enabled()
      except Exception as e:
        info['selenium_error'] = str(e)
    return info

  def __repr__(self) -> str:
    return f"<DOMNode {self.tag} {self.attrs}>"

  def __str__(self) -> str:
    return f"<{self.tag} id='{self.get('id')}' class='{self.get('class')}'>"


class DOMSchema:
  """Parse and query DOM using direct Selenium driver references."""

  HTML_TAGS = {
    'a', 'abbr', 'address', 'area', 'article', 'aside', 'audio',
    'b', 'base', 'bdi', 'bdo', 'blockquote', 'body', 'br', 'button',
    'canvas', 'caption', 'cite', 'code', 'col', 'colgroup',
    'data', 'datalist', 'dd', 'del', 'details', 'dfn', 'dialog', 'div', 'dl', 'dt',
    'em', 'embed',
    'fieldset', 'figcaption', 'figure', 'footer', 'form',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head', 'header', 'hgroup', 'hr', 'html',
    'i', 'iframe', 'img', 'input', 'ins',
    'kbd',
    'label', 'legend', 'li', 'link',
    'main', 'map', 'mark', 'meta', 'meter',
    'nav', 'noscript',
    'object', 'ol', 'optgroup', 'option', 'output',
    'p', 'param', 'picture', 'pre', 'progress',
    'q',
    'rp', 'rt', 'ruby',
    's', 'samp', 'script', 'section', 'select', 'small', 'source', 'span', 'strong', 'style', 'sub', 'summary', 'sup', 'svg',
    'table', 'tbody', 'td', 'template', 'textarea', 'tfoot', 'th', 'thead', 'time', 'title', 'tr', 'track',
    'u', 'ul',
    'var', 'video',
    'wbr'
  }

  def __init__(self, driver: Any):
    """
    Initialize and build DOM schema from Selenium driver.

    Args:
      driver: Selenium WebDriver
      wait_for_load: Wait for page to finish loading before building (default: True)

    Note: WebElements are cached as direct Selenium driver references.
          If DOM changes, recreate DOMSchema to refresh cached references.
    """
    if driver is None:
      raise ValueError("Must provide 'driver'")

    self.driver = driver
    self.nodes: List[DOMNode] = []
    self.by_tag: Dict[str, List[DOMNode]] = defaultdict(list)
    self.by_type: Dict[str, List[DOMNode]] = defaultdict(list)
    self.by_name: Dict[str, List[DOMNode]] = defaultdict(list)
    self.by_class: Dict[str, List[DOMNode]] = defaultdict(list)
    self.by_id: Dict[str, DOMNode] = {}
    self._build()

  def _build(self):
    """Walk DOM tree using Selenium, building indexes with cached WebElement references."""
    from selenium.webdriver.common.by import By

    try:
      # Get all elements from Selenium driver
      elements = self.driver.find_elements(By.XPATH, '//*')

      for idx, elem in enumerate(elements):
        try:
          # Create node with cached WebElement reference
          node = DOMNode(elem, self.driver, idx)

          # Build indexes
          self.nodes.append(node)
          self.by_tag[node.tag].append(node)

          if "type" in node.attrs:
            self.by_type[node.attrs["type"]].append(node)
          if "name" in node.attrs:
            self.by_name[node.attrs["name"]].append(node)
          if "class" in node.attrs:
            classes = node.attrs["class"] if isinstance(node.attrs["class"], list) else [node.attrs["class"]]
            for cls in classes:
              self.by_class[cls].append(node)
          if "id" in node.attrs:
            self.by_id[node.attrs["id"]] = node

        except Exception:
          # Skip elements that can't be accessed
          continue

    except Exception as e:
      raise ValueError(f"Failed to build DOM schema: {e}")

  def is_page_loading(self) -> bool:
    """Check if page is still loading."""
    try:
      return self.driver.execute_script("return document.readyState;") != "complete"
    except Exception:
      return False

  def wait_for_page_load(self, timeout: float = 30) -> bool:
    """
    Wait for page to finish loading.

    Args:
      timeout: Maximum time to wait in seconds (default: 30)

    Returns:
      True if page loaded, False if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
      if not self.is_page_loading():
        return True
      time.sleep(0.1)

    return False

  def select_node(self, *args, **kwargs) -> List[DOMNode]:
    """
    Select elements using various strategies.

    Query formats:
      - String: '#id', '.class', 'tag', 'text'
      - Dict: {'data-testid': 'value', 'class': 'btn'} for attribute matching
      - CSS Selector: Use css='selector' for native Selenium CSS selectors
    Kwargs: id, class_, name, type, text, tag, placeholder, pattern, css, etc.

    Examples:
      select_node('#login-btn')
      select_node('.button.primary')
      select_node('button', type='submit')
      select_node({'data-testid': 'LogoutIcon'})
      select_node(css='div > a.link[href*="test"]')  # Native CSS selector
    """
    _query = kwargs.pop('query', args[0] if len(args) > 0 else None)
    _css   = kwargs.pop('css', None)

    # If CSS selector provided, use Selenium's native CSS selector
    if _css:
      from selenium.webdriver.common.by import By
      try:
        elements = self.driver.find_elements(By.CSS_SELECTOR, _css)
        results = []
        for idx, elem in enumerate(elements):
          try:
            results.append(DOMNode(elem, self.driver, idx))
          except Exception:
            continue
        return results
      except Exception:
        return []

    # If _query is a dict, merge it into kwargs for attribute matching
    if isinstance(_query, dict):
      kwargs.update(_query)
      _query = None
    elif isinstance(_query, str):
      _query = _query.strip()

    # Extract parameters
    _id      = kwargs.pop('id', None)
    _class_  = kwargs.pop('class_', None)
    _cls     = kwargs.pop('cls', None)
    _name    = kwargs.pop('name', None)
    _text    = kwargs.pop('text', None)
    _pattern = kwargs.pop('pattern', None)
    _tag     = kwargs.pop('tag', None)
    _type    = kwargs.pop('type', None)

    use_full_index = True
    results = self.nodes

    # Parse string query
    if _query:
      if _query.startswith('#'):
        _id = _query[1:]
      elif _query.startswith('.'):
        _class_ = _query[1:]
      elif _query.lower() in self.HTML_TAGS:
        _tag = _query.lower()
      else:
        _text = _query

    if _id is not None:
      node = self.by_id.get(_id)
      return [node] if node else []

    _class_value = _class_ or _cls
    if _class_value is not None:
      use_full_index = False
      if '.' in _class_value:
        classes = _class_value.split('.')
        class_sets = [set(self.by_class.get(c, [])) for c in classes]
        if class_sets:
          class_nodes = set.intersection(*class_sets)
          results = [n for n in results if n in class_nodes]
      else:
        results = [n for n in results if _class_value in (n.attrs.get("class", []) if isinstance(n.attrs.get("class"), list) else [n.attrs.get("class")])]

    if _name is not None:
      if use_full_index:
        results = self.by_name.get(_name, [])
        use_full_index = False
      else:
        results = [n for n in results if n.get("name") == _name]

    if _type is not None:
      if use_full_index:
        results = self.by_type.get(_type, [])
        use_full_index = False
      else:
        results = [n for n in results if n.get("type") == _type]

    if _tag is not None:
      if use_full_index:
        results = self.by_tag.get(_tag, [])
        use_full_index = False
      else:
        results = [n for n in results if n.tag == _tag]

    if _text is not None or _pattern is not None:
      use_full_index = False

      # Determine if we're doing regex matching
      is_regex = False
      pattern_str = None

      if _pattern is not None:
        is_regex = True
        pattern_str = _pattern

      if is_regex and pattern_str is not None:
        # Regex matching
        try:
          pattern = re.compile(pattern_str, re.IGNORECASE)
          filtered = []
          for n in results:
            searchable_parts = [n.text]
            for attr in ['placeholder', 'title', 'value', 'alt', 'aria-label', 'data-testid']:
              if attr in n.attrs and n.attrs[attr]:
                searchable_parts.append(str(n.attrs[attr]))
            searchable_text = ' '.join(searchable_parts)

            if pattern.search(searchable_text):
              filtered.append(n)
          results = filtered
        except re.error as e:
          # Fallback to literal match if regex is invalid
          text_lower = pattern_str.lower()
          results = [n for n in results if text_lower in n.text.lower()]
      elif _text is not None:
        # Substring match in text and attribute values
        text_lower = _text.lower()
        filtered = []
        for n in results:
          searchable_parts = [n.text]
          for attr in ['placeholder', 'title', 'value', 'alt', 'aria-label', 'data-testid']:
            if attr in n.attrs and n.attrs[attr]:
              searchable_parts.append(str(n.attrs[attr]))
          searchable_text = ' '.join(searchable_parts).lower()

          if text_lower in searchable_text:
            filtered.append(n)

        results = filtered

    # Match any remaining kwargs as DOM attributes (data-testid, aria-label, etc.)
    if kwargs:
      filtered = []
      for n in results:
        matches = True
        for attr_key, attr_value in kwargs.items():
          node_attr_value = n.attrs.get(attr_key)
          if node_attr_value is None:
            matches = False
            break
          # Handle list values (e.g., class attribute)
          if isinstance(node_attr_value, list):
            if attr_value not in node_attr_value:
              matches = False
              break
          elif str(node_attr_value) != str(attr_value):
            matches = False
            break
        if matches:
          filtered.append(n)
      results = filtered

    return results

  def show(self, max_nodes: int = 50) -> None:
    """Display nodes."""
    for i, node in enumerate(self.nodes[:max_nodes]):
      attr_str = ", ".join([f"{k}={v}" for k, v in list(node.attrs.items())[:3]])
      text_preview = node.text[:30] + "..." if len(node.text) > 30 else node.text
      print(f"{i}: <{node.tag}> {attr_str} | {text_preview}")
    if len(self.nodes) > max_nodes:
      print(f"... and {len(self.nodes) - max_nodes} more nodes")

  def first(self, *args, **kwargs) -> Optional[DOMNode]:
    """Select first matching element."""
    results = self.select_node(*args, **kwargs)
    return results[0] if results else None

  @property
  def inputs(self) -> List[DOMNode]:
    """Get all input elements."""
    return self.by_tag.get("input", [])

  @property
  def buttons(self) -> List[DOMNode]:
    """Get all button elements."""
    buttons = self.by_tag.get("button", [])
    button_inputs = self.by_type.get("submit", []) + self.by_type.get("button", [])
    return buttons + button_inputs

  @property
  def passwords(self) -> List[DOMNode]:
    """Get all password inputs."""
    return self.by_type.get("password", [])

  @property
  def all(self) -> List[DOMNode]:
    """Get all nodes."""
    return self.nodes

  @property
  def summary(self) -> Dict[str, Any]:
    """Get summary statistics."""
    return {
      "total_nodes": len(self.nodes),
      "tags": {tag: len(nodes) for tag, nodes in self.by_tag.items()},
      "inputs": len(self.inputs),
      "buttons": len(self.buttons),
      "passwords": len(self.passwords),
    }

  @staticmethod
  def simulate_human_typing(*args, **kwargs):
    """
    Type text with human-like random delays.

    Args:
      element: DOMNode or Selenium WebElement
      text: Text to type
      min_delay: Min delay between chars (default: 0.05)
      max_delay: Max delay between chars (default: 0.2)
      pause_every: Pause after N chars (default: 4)
      pause_min: Min pause duration (default: 0.1)
      pause_max: Max pause duration (default: 0.3)
      clear_first: Clear field first (default: True)
    """
    _element = kwargs.pop('element', args[0] if len(args) > 0 else None)
    _text = kwargs.pop('text', args[1] if len(args) > 1 else None)
    _min_delay = kwargs.pop('min_delay', 0.05)
    _max_delay = kwargs.pop('max_delay', 0.2)
    _pause_every = kwargs.pop('pause_every', 4)
    _pause_min = kwargs.pop('pause_min', 0.1)
    _pause_max = kwargs.pop('pause_max', 0.3)
    _clear_first = kwargs.pop('clear_first', True)

    if _element is None or _text is None:
      raise ValueError("Both 'element' and 'text' arguments are required")

    if isinstance(_element, DOMNode):
      _element = _element.webelement

    if _clear_first:
      from selenium.webdriver.common.keys import Keys
      import platform
      _mod = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
      _element.send_keys(_mod + 'a')
      _element.send_keys(Keys.BACKSPACE)

    for i, char in enumerate(_text):
      _element.send_keys(char)
      time.sleep(random.uniform(_min_delay, _max_delay))
      if _pause_every > 0 and (i + 1) % _pause_every == 0:
        time.sleep(random.uniform(_pause_min, _pause_max))

  def __len__(self) -> int:
    return len(self.nodes)

  def __repr__(self) -> str:
    return f"<DOMSchema nodes={len(self.nodes)} tags={len(self.by_tag)}>"
