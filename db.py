"""Module for logging time series data to sqlite."""
import logging
import time
import sqlite3

def SetupDb(path):
  global db
  db = sqlite3.connect(path)
  db.cursor().execute(
      'CREATE TABLE IF NOT EXISTS labels '
      '(label_id INTEGER PRIMARY KEY AUTOINCREMENT, label STRING UNIQUE)')
  db.cursor().execute(
      'CREATE INDEX IF NOT EXISTS labels_label_index ON labels(label)')
  db.cursor().execute(
      'CREATE TABLE IF NOT EXISTS readings '
      '(label_id INTEGER, timestamp INTEGER, value REAL)')
  db.cursor().execute(
      'CREATE INDEX IF NOT EXISTS readings_timestamp ON readings(timestamp)')
  db.cursor().execute(
      'CREATE INDEX IF NOT EXISTS readings_label_id ON readings(label_id)')

def LogData(label, value, timestamp=-1):
  """Log an event/value pair.

  Args:
    label: (str) The type of data being logged.
    value: (float) The value to be logged.
    timestamp: (int) Optional timestamp (seconds since epoch).
  Returns:
    None
  """
  global db
  if timestamp == -1:
    timestamp = int(time.time())
  if label not in LogData._labels:
    #... Fetch or insert into DB.
    cursor = db.cursor()
    result = cursor.execute('SELECT label_id FROM labels WHERE label=?', (label,)).fetchone()
    if result:
      LogData._labels[label] = result[0]
    else:
      cursor.execute('INSERT INTO labels(label) VALUES (?)', (label,))
      LogData._labels[label] = cursor.lastrowid
      db.commit()
  label_id = LogData._labels[label]

  db.execute('INSERT INTO readings(label_id, timestamp, value) VALUES '
             '(?,?,?)', (label_id, int(timestamp), value))
  db.commit()
  logging.info("%s: %s (%d), %d" % (
      time.strftime("%Y%m%d-%H%M%S", time.localtime(timestamp)), 
      label, label_id, value))

# Cache of label to ID mappings.
LogData._labels = {}
