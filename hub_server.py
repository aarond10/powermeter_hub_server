import db
from SocketServer import BaseServer
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from OpenSSL import SSL
import logging
import time
import socket
import urlparse

class SecureHTTPServer(HTTPServer):
  def __init__(self, server_address, HandlerClass):
    BaseServer.__init__(self, server_address, HandlerClass)
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    fpem = 'cert.pem'
    ctx.set_cipher_list('RC4-MD5')
    ctx.use_privatekey_file(fpem)
    ctx.use_certificate_file(fpem)
    self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                    self.socket_type))
    self.server_bind()
    self.server_activate()

  def shutdown_request(self, request):
    """We will shut down ourselves."""
    pass

class SecureHTTPRequestHandler(SimpleHTTPRequestHandler):
  def setup(self):
    self.connection = self.request
    self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
    self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

class FakeEfergyServer(SecureHTTPRequestHandler):
  """Pretends to be a sensornet.info server.

  The firmware in the hub that I have (v1.1 AU) *requires* HTTP/1.1 and 
  a graceful SSL shutdown handshake. SSL certificate fields may also be 
  checked but I've just copied all of those so I'm not sure.
  """
  protocol_version = 'HTTP/1.1'

  def do_GET(self):
    try:
      url = urlparse.urlparse(self.path)
      q = urlparse.parse_qs(url.query)

      code = 200
      content = ""
      if url.path == '/get_key.html':
	# This doesn't seem part of the normal flow of operations.
	# No arguments are provided and the same string is returned of
	# the form:  TT|<13 characters>
	# It gives me the same response regardless of host I query via
	# chrome so I suspect it's some sort of a salt for the key hashing.
	# Strangely, it sometimes happens mid-flow and I see different
	# strings of the form E1|<13 characters>
	content = "TT|a1bCDEFGHa1zZ\n"
      elif url.path == '/check_key.html':
	# q['h'][0] is some 128-bit hash of:
	#  1. q['p'][0] (the device type - E1 in my case)
	#  2. q['ts'][0] (uptime as 32-bit hex value)
	#  3. hostname (the MAC address of the device)
	# Queries with the same ts value (across reboots) have
	# the same hash.
	# The form is not known but we don't particularly care.
	# We only want to return success.
	content = "\n"

      self.send_response(code)
      self.send_header("Content-Type", "text/html; charset=UTF-8")
      self.send_header("Content-Length", len(content))
      self.end_headers()
      self.wfile.write(content)
      logging.error('GET: %s', (url, dict(self.headers)))
    except Exception, e:
      logging.error("Exception: %s", e)
    
    # Shutdown SSL before closing the connection. 
    self.close_connection = 1
    self.connection.shutdown()
    self.connection.close()

  def do_POST(self):
    url = urlparse.urlparse(self.path)
    q = urlparse.parse_qs(url.query)

    if url.path == '/h2' or url.path == '/h3':
      # Sensor data!
      # Headers look like this:
      #   x-uptime: <seconds since boot>
      #   x-hash: <unknown hash algorithm. 64-bit>
      #   x-version: 2.3.7
      #   x-pair: P
      #   x-mode: E1
      #   x-ts: <uptime seconds as 32-bit hex value>:<milliseconds in decimal?>
      #   content-type: application/eh-data
      # This is followed by a \r\n-terminated line for each connected sensor.
      # Data for each sensor looks like this:
      #   <SID>|1|<SensorType>|<Port>,<value to 2 decimal places>
      #   SID is a sensor id, a 6 digit integer. I've seen this be zero occasionally,
      #   which typically goes away after we respond with a 200 OK.
      #   SensorType is EFCT for CT transmitters, not sure about others - but I've seen my EFT
      #   sensor return 'EFMS1' in this field:
      #     <SID>|0|EFMS1|M,64.00&T,0.00&L,0.00|-62
      #   Port is P1, even on (my) multi-CT setup.
    
      hubVersion = url.path.strip('/')
      httpData = self.rfile.read(int(self.headers['content-length']))
      sensorLines = httpData.split('\r\n')
      for line in sensorLines:
            if len(line) == 0:
		continue
            data = line.split('|')
            SID = data[0]
            if SID == '0':
                continue
            portAndValue = data[3]
            value = float(portAndValue.split(',')[1])
            label = 'efergy_%s_%s' % (hubVersion, SID)
            print portAndValue.split(',')
            print "%s, %s, %s" % (url.path, time.time(), value)
            logging.info("%s, %s, %s, %s" % (SID, url.path, time.time(), value))
            db.LogData(label, value)
      
    self.send_response(200)
    self.send_header("Content-Type", "text/html; charset=UTF-8")
    self.end_headers()

    # Shutdown SSL before closing the connection. 
    self.close_connection = 1
    self.connection.shutdown()
    self.connection.close()

def run_server():
  server_address = ('', 8080) # (address, port)
  httpd = SecureHTTPServer(server_address, FakeEfergyServer)
  sa = httpd.socket.getsockname()
  print "Serving HTTPS on", sa[0], "port", sa[1], "..."
  httpd.serve_forever()


if __name__ == '__main__':
  logging.basicConfig()
  db.SetupDb('readings.db')
  run_server()
