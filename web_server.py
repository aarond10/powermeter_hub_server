from SocketServer import BaseServer
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import json
import logging
import time
import socket
import sqlite3
import urlparse

db = sqlite3.connect('readings.db')

class MyWebServer(SimpleHTTPRequestHandler):
  STATIC = '/static/'
  POWER_FACTOR = 0.6
  MAINS_VOLTAGE = 230

  def do_GET(self):
    url = urlparse.urlparse(self.path)
    q = urlparse.parse_qs(url.query)

    code = 200
    content = ""
    if url.path[:len(self.STATIC)] == self.STATIC:
      try:
	path = 'static/%s' % url.path[len(self.STATIC):]
	if path.find('../') != -1:
	  raise ValueError('Invalid path escaping detected.')
	data = open(path).read()
	self.send_response(200)
	self.end_headers()
	self.wfile.write(data)
      except Exception, e:
	self.send_response(500)
	self.end_headers()
	self.wfile.write('Error: %s' % e)
    elif url.path == '/':
      self.send_response(200)
      self.end_headers()
      self.wfile.write(open('static/index.html').read())
    elif url.path == '/data.csv':
      self.send_response(200)
      self.end_headers()
      self.wfile.write('Timestamp,Raw Value\n')

      global db
      cur = db.cursor()
      data = cur.execute('SELECT * from readings').fetchall()
      for timestamp, amps in data:
        self.wfile.write('%s,%s,0.02\n' % (
            timestamp, amps * self.MAINS_VOLTAGE * self.POWER_FACTOR / 1000000))
    else:
      self.send_response(404)
      self.end_headers()
      self.wfile.write('File not found')
	
    
def run_server():
  server_address = ('', 8081) # (address, port)
  httpd = HTTPServer(server_address, MyWebServer)
  sa = httpd.socket.getsockname()
  print "Serving HTTP on", sa[0], "port", sa[1], "..."
  httpd.serve_forever()


if __name__ == '__main__':
  logging.basicConfig()
  run_server()
