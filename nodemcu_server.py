import db
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import logging
import urlparse

class NodeMCUServer(SimpleHTTPRequestHandler):
  """Act similar to the fake sensornet server we emulate for the sake of the
  efergy hub but this one uses regular HTTP and is designed for use with ESP8266
  devices flashed with NodeMCU. Use GET instead of POST because I'm lazy.
  """

  def do_GET(self):
    url = urlparse.urlparse(self.path)
    q = urlparse.parse_qs(url.query)

    if url.path == '/data':
      db.LogData(q['dev'][0], float(q['val'][0]))
      logging.info("%s, %s" % (q['dev'][0], q['val'][0]))
      self.send_response(200)
    else:
      self.send_response(404)

def run_server():
  server_address = ('', 8079) # (address, port)
  httpd = HTTPServer(server_address, NodeMCUServer)
  sa = httpd.socket.getsockname()
  print "Serving HTTP on", sa[0], "port", sa[1], "..."
  httpd.serve_forever()


if __name__ == '__main__':
  logging.basicConfig()
  db.SetupDb('readings.db')
  run_server()
