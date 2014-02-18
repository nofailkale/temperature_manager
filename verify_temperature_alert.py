#!/usr/bin/python

""" 
  verify_temperature_alert.py is a watchdog program that sends email alerts 
  if temperature recording is not working 
"""

import os, sys, time, logging
from datetime import datetime

import config
from temp_lib import send_mail, check_python_version, get_gspread_client_login, \
    retry, get_logger

import gspread

check_python_version()

minimum_temperature = config.minimum_temperature
email_alert_threshold = config.hour_seconds

local_host = config.local_host

spreadsheet = config.spreadsheet

script_name = os.path.basename(__file__)

log = get_logger()

# retry decorator implemented because getting the time field from the last
# row of the spreadsheet fails too frequently
@retry(Exception, tries=3, delay=30)
def get_last_update():
  """get_last_update retrieves the time the spreadsheet was last updated

  :returns: the time from when the given spreadsheet was last updated
  :rtype: string
  """
  try:
    worksheet = gc.open(spreadsheet).worksheet(sheet_name)
    last_row = worksheet.row_count
    last_update = worksheet.cell(last_row, 1).value
    if not last_update:
      invalid_value = "Invalid value returned for the time when the spreadsheet was last updated"
      log.error(invalid_value)
      raise Exception(invalid_value)
  except Exception, e:
    error = "get_last_update error: %s %s" % (e.__class__, e)
    log.error(error)
    raise
  return last_update

log.info("BEGIN LOGGING")

try:
  log.info("Attempting to login to Google.")
  gc = get_gspread_client_login()
except Exception, e:
  error = "Google login error: %s %s" % (e.__class__, e)
  log.error(error)
  send_mail(script_name, script_name + " running on '" + local_host + "' could not authenticate for Google Docs access", error)
  sys.exit(3)

for sheet_name in config.sheets:
  try:
    last_update = get_last_update()
    log.info("Last update time for " + sheet_name + ": " + last_update)
  except Exception, e:
    error = "Error getting last update for sheet %s: %s %s" % (sheet_name, e.__class__, e)
    log.error("Couldn't get last update time for '" + sheet_name + "' trying next sheet if applicable : " + error)
    send_mail(script_name, script_name + " running on '" + local_host + "' could not access sheet '" + sheet_name + "' in Google spreadsheet", \
              "Could not retrieve data from the last row of the spreadsheet: " + error)
    continue

    last_update_seconds = ""
  try:
    log.info("Attempting to convert ISO 8601 string to epoch (local timezone)")
    last_update_seconds = time.mktime(datetime.strptime(last_update, "%Y-%m-%dT%H:%M:%S.%f").timetuple())
    log.info("Last update time in epoch: " + str(last_update_seconds))
  except ValueError, e:
    error = "Error converting string to epoch %s %s" % (e.__class__, e)
    log.error(error)
    send_mail(script_name, script_name + " running on '" + local_host + "' received unexpected last_update data", \
              "Received: '" + last_update + "' but expected time in ISO8601 format for sheet '" + \
              sheet_name + "' : " + error)
    continue

  now = time.time()
  time_diff = now - last_update_seconds
  if (time_diff >= email_alert_threshold):
    warning = "The sheet '" + sheet_name + "' for spreadsheet '" + spreadsheet + "' has not been updated recently " + last_update
    log.warning(warning)
    send_mail(script_name, "ALERT: " + script_name + " running on '" + local_host + "' detected Google spreadsheet not being updated", warning)

log.info("END LOGGING")

# vim: tabstop=2: shiftwidth=2: expandtab:
