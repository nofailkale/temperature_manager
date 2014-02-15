"""temp_lib.py contains shared helper functions for temperature_manager"""

import os, sys, time, smtplib, socket, math
from functools import wraps

import config

import gspread

gmail_user = config.gmail_user
gmail_password = config.gmail_password

local_host = config.local_host
from_address = config.from_address
to_address = config.to_address
smtp_host = config.smtp_host
smtp_port = config.smtp_port
timeout = config.timeout

message = """From: {0} <{1}>
To: <{2}>
Subject: {3}

{4}

"""

def send_mail(script_name, subject, alert):
  """send_mail sends an email alert message via SMTP

  :param script_name: name of script sending alert
  :type  script_name: string 
  :param subject: subject of email message
  :type  subject: string
  :param alert: alert message body
  :type  alert: string
  """
  try:
    smtp = smtplib.SMTP(smtp_host, smtp_port, local_host, timeout)
    smtp.sendmail(from_address, to_address, message.format(script_name, from_address, to_address, subject, alert))
  except Exception, e:
    error = "Error while sending email:  %s %s\n" % (e.__class__, e)
    sys.stderr.write(error)

def check_python_version():
  """check_python_version require v2.6 or later for gspread API and support for timeouts in SMTP"""
  if sys.version_info < (2, 6):
    print "temperature_manager requires version 2.6 or later of Python.  Exiting."
    sys.exit(1)

def round_up_two(temp):
  """round_up_two rounds a given float up two decimal places

  :param temp: temperature value to round up
  :type  temp: float

  :returns: float rounded up to two decimal places
  :rtype: float
  """
  return math.ceil(temp*100)/100

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
  """retry retries calling the decorated function using an exponential backoff.

  http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
  original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

  :param ExceptionToCheck: the exception to check. may be a tuple of exceptions to check
  :type ExceptionToCheck: Exception or tuple
  :param tries: number of times to try (not retry) before giving up
  :type tries: int
  :param delay: initial delay between retries in seconds
  :type delay: int
  :param backoff: backoff multiplier e.g. value of 2 will double the delay each retry
  :type backoff: int
  :param logger: logger to use. If None, print
  :type logger: logging.Logger instance
  """
  def deco_retry(f):

    @wraps(f)
    def f_retry(*args, **kwargs):
      mtries, mdelay = tries, delay
      while mtries > 1:
        try:
          return f(*args, **kwargs)
        except ExceptionToCheck, e:
          msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
          if logger:
            logger.warning(msg)
          else:
            print msg
          time.sleep(mdelay)
          mtries -= 1
          mdelay *= backoff
      return f(*args, **kwargs)

    return f_retry  # true decorator

  return deco_retry

def alert_now(alert_file):
  """ alert_now creates an alert file (alert_file) to track time since the last alert was sent.

  :param alert_file: full path to the alert file to use
  :type  alert_file: string

  :returns: False if an alert has already been sent within the email_alert_threshold.  True otherwise.
  :rtype: bool
  """
  email_alert_threshold = config.hour_seconds
  if not os.path.exists(alert_file):
    try:
      file(alert_file, 'w').close()
      return True
    except IOError, e:
      error = "Error trying to open alert file:  %s %s\n" % (e.__class__, e)
      print error
      send_mail(script_name, script_name + " running on '" + local_host + "' could not open alert file", error)
  else:
    try:
      mtime = os.stat(alert_file).st_mtime
      now = time.time()
      time_diff = now - mtime
      if (time_diff >= email_alert_threshold):
        file(alert_file, 'w').close()
        return True
    except (OSError, IOError), e:
      error = "Error trying to stat alert file:  %s %s\n" % (e.__class__, e)
      print error
      send_mail(script_name, script_name + " running on '" + local_host + "' could not stat alert file", error)
  return False

@retry(Exception, tries=3, delay=30)
def get_gspread_client_login():
  """get_gspread_client_login creates a Google gspread client connection

  :returns: returns a Google gspread client connection
  :rtype: gspread.Client
  """
  try:
    gc = gspread.login(gmail_user,gmail_password)
  except Exception, e:
    error = "%s %s\n" % (e.__class__, e)
    print error
    raise
  return gc

# vim: tabstop=2: shiftwidth=2: expandtab:
