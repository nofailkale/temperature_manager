#!/usr/bin/python

"""
  rt_temperature_tracker.py collects, records and alerts on temperature data
  produced by Radio Thermostat Wi-Fi thermostats
"""

import os, sys, glob, time, datetime, urllib2

import config
from temp_lib import send_mail, check_python_version, get_gspread_client_login, \
    retry, alert_now, get_logger

import radiotherm
# Dynamically load thermostat model class from config
thermostat_module = __import__("radiotherm.thermostat",fromlist=[config.thermostat_model])
thermostat_model = getattr(thermostat_module,config.thermostat_model)

import gspread

check_python_version()

local_host = config.local_host

minimum_temperature = config.minimum_temperature

spreadsheet = config.spreadsheet

log = get_logger()

path_name, script_name = os.path.split(os.path.abspath(__file__))
alert_file = os.path.abspath(path_name) + "/alert_sent_temperature_tracker"

# retry connecting to thermostat because "No route to host" and "Connection
# refused" urllib2.URLError exceptions are common.  Also handle retry 
# for invalid temperature.
@retry(Exception, tries=3, delay=60)
def get_current_temp():
  """get_current_temp retrieves the current temperature from the thermostat

  :returns: current temperature from the thermostat
  :rtype: float
  """
  try:
    # Get temperature in one call to thermostat without getting the model and
    # making multiple tstat calls as is done through traditional radiotherm
    # library initialization
    tstat = thermostat_model(config.thermostat_address).tstat
    current_temp = float(tstat['raw']['temp'])
    if not is_temp_valid(current_temp):
      invalid_temp = "Value for given temperature invalid: " + str(current_temp)
      log.error(invalid_temp)
      raise Exception(invalid_temp)
  except Exception, e:
    error = "get_current_temp error: %s %s" % (e.__class__, e)
    log.error(error)
    raise
  return current_temp

def is_temp_valid(temp):
  """is_temp_valid tests to make sure a given temperature is within a
  reasonable indoor range.  These thermostats commonly return '-1' for
  the current temperature.

  :param temp: temperature value
  :type  temp: float
  
  :returns: True if the temp is within the range 30-100.  Otherwise return False.
  :rtype: bool
  """
  if 30 < temp < 100:
    return True
  else:
    return False

log.info("BEGIN LOGGING")

current_temp = None
try:
  current_temp = get_current_temp()
  log.info("Current temp returned: " + str(current_temp))
  spreadsheet_data = [datetime.datetime.now().isoformat(), current_temp]
  log.info("Spreadsheet input generated: " + str(spreadsheet_data))
except Exception, e:
  error = "Error getting current temperature %s %s" % (e.__class__, e)
  log.error(error)
  if alert_now(alert_file):
    send_mail(script_name, script_name + " running on '" + local_host + "' could not retrieve data properly from thermostat(" + config.thermostat_address + ")", error)
  sys.exit(1)

if (current_temp <= minimum_temperature):
  error = "The current temperature is " + str(current_temp) + " degrees.  The alert threshold is " + str(minimum_temperature) + " degrees."
  log.error(error)
  if alert_now(alert_file):
    send_mail(script_name, "CRITICAL ALERT from " + script_name + ": Temperature reading passed alert threshold", error)

try:
  log.info("Attempting to login to Google.")
  gc = get_gspread_client_login()
except Exception, e:
  error = "Google login error: %s %s" % (e.__class__, e)
  log.error(error)
  send_mail(script_name, script_name + " running on '" + local_host + "' could not authenticate for Google Docs access", error)
  sys.exit(3)

try:
  log.info("Opening worksheet to append data")
  worksheet = gc.open(spreadsheet).worksheet(config.rt_worksheet)
  worksheet.append_row(spreadsheet_data)
except Exception, e:
  error = "Error working with spreadsheet: %s %s" % (e.__class__, e)
  log.error(error)
  if alert_now(alert_file):
    send_mail(script_name, script_name + " running on '" + local_host + "' could not update Google spreadsheet", error)
  sys.exit(4)

log.info("END LOGGING")

# vim: tabstop=2: shiftwidth=2: expandtab:
