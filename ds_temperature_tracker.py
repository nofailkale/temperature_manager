#!/usr/bin/python

"""ds_temperature_tracker.py collects, records and alets on temperature data"""

import os, sys, glob, time, datetime

import config
from temp_lib import send_mail, check_python_version, round_up_two, \
get_gspread_client_login, alert_now, get_logger

import gspread

check_python_version()

local_host = config.local_host

minimum_temperature = config.minimum_temperature
email_alert_threshold = config.hour_seconds

spreadsheet = config.spreadsheet

log = get_logger()

path_name, script_name = os.path.split(os.path.abspath(__file__))
alert_file = os.path.abspath(path_name) + "/alert_sent_temperature_alert"

base_dir = '/sys/bus/w1/devices/'

def read_temp_raw():
  """read_temp_raw retrieves temperature data from DS18B20 sensor

  :returns: raw temperature data
  :rtype: list
  """
  try:
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'
    f = open(device_file, 'r')
    try:
      lines = f.readlines()
      return lines
    finally:
      f.close()
  except (IndexError, IOError), e:
    error = "read_temp_raw encountered an error: %s %s" % (e.__class__, e)
    log.error(error)
    if alert_now(alert_file):
      send_mail(script_name, script_name + " running on '" + local_host + "' could not read raw temperature data", error)
    sys.exit(2)

def read_temp(scale="F"):
  """ read_temp parses raw temperature data output
  
  :param: temperature scale type "F" or "C"
  :type: string

  :returns: temperature data in fahrenheit or celsius
  :rtype: float
  """
  lines = read_temp_raw()
  count = 0
  max_loops = 10
  while (lines[0].strip()[-3:] != 'YES'):
    time.sleep(0.2)
    lines = read_temp_raw()
    count = count + 1
    if (count == max_loops):
      error = "The 'read_temp' function made " + str(max_loops) + " attempts to read output and failed: " + lines
      log.error(error)
      if alert_now(alert_file):
        send_mail(script_name, script_name + " running on '" + local_host + "' could not read temperature data output", error)
      sys.exit(3)
  equals_pos = lines[1].find('t=')
  if equals_pos != -1:
    temp_string = lines[1][equals_pos+2:]
    temp_c = float(temp_string) / 1000.0
    if (scale == "C"):
      return round_up_two(temp_c)
    else:
      temp_f = temp_c * 9.0 / 5.0 + 32.0
      return round_up_two(temp_f)

log.info("BEGIN LOGGING")

current_temp = read_temp(config.temperature_scale) or "No valid data"
if isinstance(current_temp, float):
  if (current_temp <= minimum_temperature):
    if alert_now(alert_file):
      error = "The temperature has dipped to " + str(current_temp) + " degrees.  Please investigate."
      log.error(error)
      send_mail(script_name, "CRITICAL ALERT from " + script_name + ": Temperature reading passed alert threshold", error)
  spreadsheet_data = [datetime.datetime.now().isoformat(), current_temp]
else:
  if alert_now(alert_file):
    error = "Data must be of type float. '" + str(current_temp) + "' returned."
    log.error(error)
    send_mail(script_name, script_name + " running on '" + local_host + "' did not receive valid data from read_temp() ", error)
  sys.exit(5)

try:
  log.info("Attempting to login to Google.")
  gc = get_gspread_client_login()
except Exception, e:
  error = "Google login error: %s %s" % (e.__class__, e)
  log.error(error)
  send_mail(script_name, script_name + " running on '" + local_host + "' could not authenticate for Google Docs access", error)
  sys.exit(6)

try:
  log.info("Attempting to append data to worksheet: " + str(spreadsheet_data))
  worksheet = gc.open(spreadsheet).worksheet(config.ds_worksheet)
  worksheet.append_row(spreadsheet_data)
except Exception, e:
  error = "Error appending data to worksheet: %s %s" % (e.__class__, e)
  log.error(error)
  if alert_now(alert_file):
    send_mail(script_name, script_name + " running on '" + local_host + "' could not update Google spreadsheet", error)
  sys.exit(7)

log.info("END LOGGING")

# vim: tabstop=2: shiftwidth=2: expandtab:
