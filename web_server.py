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
        if path[-3:] == ".js":
          self.send_header('Content-Type', 'application/javascript')
	self.end_headers()
	self.wfile.write(data)
      except IOError, e:
        self.send_response(404)
	self.end_headers()
      except Exception, e:
	self.send_response(500)
	self.end_headers()
	self.wfile.write('Error: %s' % e)
    elif url.path == '/':
      self.send_response(200)
      self.end_headers()
      self.wfile.write(open('static/index.html').read())
    elif url.path == '/data/labels.json':
      self.send_response(200)
      self.send_header('Content-Type', 'application/json')
      self.end_headers()
      global db
      cur = db.cursor()
      data = cur.execute('SELECT label_id, label from labels').fetchall()
      labels = [{'id': v[0], 'name': v[1]} for v in data]
      self.wfile.write(json.dumps(labels))
    elif url.path[:len('/data/')] == '/data/':
      label = url.path[len('/data/'):]
      self.send_response(200)
      self.end_headers()
      self.wfile.write('Timestamp,Raw Value\n')

      duration = q.get('duration', ['7d'])[0]
      if duration[-1] == 'w':
        duration = int(duration[:-1])*86400*7
      elif duration[-1] == 'd':
        duration = int(duration[:-1])*86400
      elif duration[-1] == 'h':
        duration = int(duration[:-1])*3600
      elif duration[-1] == 'm':
        duration = int(duration[:-1])*60
      else:
        duration = int(duration)

      sample_interval = max(1, duration / 256)
      start_time = time.time() - duration

      logging.error('label: %s, start_time: %s, sample_interval; %s, duration: %s',
          label, start_time, sample_interval, duration)

      global db
      cur = db.cursor()
      data = cur.execute('SELECT timestamp, sum(value)/count(*) from readings '
          'where label_id=(select label_id from labels where label=?) '
          'and timestamp > ? group by cast(timestamp / ? as int)',
          (label, start_time, sample_interval)).fetchall()
      if label.startswith('efergy_h2'):
        # Adjust for power factor.
        for timestamp, amps in data:
          self.wfile.write('%s,%s,0.02\n' % (
            timestamp, amps * self.MAINS_VOLTAGE * self.POWER_FACTOR / 1000000))
      elif label.startswith('efergy_h3'):
        # Raw data is returned in tens of watts.
        for timestamp, amps in data:
          self.wfile.write('%s,%s,0.02\n' % (timestamp, amps / 10 ))
      else:
        # Just write raw values.
        for timestamp, val in data:
          self.wfile.write('%s,%s,0.02\n' % (timestamp, val))
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
