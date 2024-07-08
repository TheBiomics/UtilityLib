from flask import Flask, jsonify as FlaskJSON
from flask import request as _Request
import signal as Signal
import threading as Threader

class WebManager():
  webapp_name = 'UL-Web-Server'
  webapp_host = '127.0.0.1'
  webapp_port = '5007'
  webapp_debug = True
  webapp = None
  Request = _Request
  allowed_methods = ['GET', 'POST']

  def __init__(self, *args, **kwargs):
    self.webapp = Flask(self.webapp_name)
    self.webapp.config['CORS_HEADERS'] = 'Content-Type'

    _defaults = {
      "endpoints": {
            '/': self.demo_welcome,
            'test': self.demo_test,
          }
    }
    _defaults.update(kwargs)
    [setattr(self, _k, _defaults[_k]) for _k in _defaults.keys()]

  response_status = 200
  def send_api_data(self, *args, **kwargs):
    """Return API Data to the Query"""
    _data_dict = {
      "status": self.response_status,
    }
    _data_dict.update(kwargs)
    _response = FlaskJSON(**_data_dict)
    _response.headers.add('Access-Control-Allow-Origin', '*')
    # _response.headers.add('Access-Control-Allow-Headers', 'Origin, Content-Type, Accept')
    return _response

  def add_endpoint(self, _endpoint, _handler):
    self.webapp.route(_endpoint, methods=self.allowed_methods)(_handler)

  server_thread = None
  def serve(self, *args, **kwargs):
    _host = kwargs.get('host', args[0] if len(args) > 0 else self.webapp_host)
    _port = kwargs.get('port', args[1] if len(args) > 1 else self.webapp_port)
    _debug = kwargs.get('debug', args[2] if len(args) > 2 else self.webapp_debug)
    _reloader = kwargs.get('reloader', args[3] if len(args) > 3 else False)

    def _webserver_listen():
      self.webapp.run(host=_host, port=_port, debug=_debug, use_reloader=_reloader)

    _existing_threads = [t.name for t in Threader.enumerate()]
    if not self.webapp_name in _existing_threads:
      self.server_thread = Threader.Thread(target=_webserver_listen, name=self.webapp_name)
      self.server_thread.setDaemon(True)
      self.server_thread.start()
      print(f'Server Started at {_host}:{_port}')
    else:
      self.log_info('Not starting thread as already started.')

  def _shutdown(self):
    """WIP"""

  def setup_signal_handlers(self) -> None:
    Signal.signal(Signal.SIGINT, self._handle_signal)
    Signal.signal(Signal.SIGTERM, self._handle_signal)

  def _handle_signal(self, signum, frame):
    return self._shutdown()

  def demo_welcome(self):
    return self.send_api_data(screen='Welcome', get_args=self.getGet(), post_values=self.getPost())

  def demo_test(self):
    return self.send_api_data(screen='Test', get_args=self.getGet(), post_values=self.getPost())

  def get_endpoint_map(self):
    return self.endpoints or {}

  def run_server(self, *args, **kwargs) -> None:
    _ep_methods = self.get_endpoint_map() or {}
    for _ep, _h in _ep_methods.items():
      if not _ep.startswith('/'):
        _ep = f"/{_ep}"
      self.add_endpoint(_ep, _h)

    self.setup_signal_handlers()
    self.serve()

  @property
  def is_post(self):
    return self.Request.method == 'POST'

  @property
  def is_get(self):
    return self.Request.method == 'GET'

  def getPost(self, key=None, default=None):
    _values = self.Request.values
    if not key:
      return _values
    return _values.get(key, default)

  def getGet(self, key=None, default=None):
    _values = self.Request.args
    if not key:
      return _values
    return _values.get(key, default)
