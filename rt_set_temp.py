#!/usr/bin/python

"""
  rt_set_temp.py is a basic CGI based web interface for setting the
  temperature on a Radio Thermostat thermostat
"""

import sys, time, cgi, cgitb

import config

import radiotherm
thermostat_module = __import__("radiotherm.thermostat",fromlist=[config.thermostat_model])
thermostat_model = getattr(thermostat_module,config.thermostat_model)

html_output = """<html>
<head>
<title>Thermostat Manager</title>
<style type="text/css">
p,form {{
  font-family: comic sans ms, tahoma;
  font-size: 12.5pt;
  background-color: #424242;
  padding: .5em;
}}
</style>
</head>
<body>
<h1>Thermostat Manager ({0})</h1>
<form action='/cgi-bin/rt_set_temp.py' method='post'>
Update temperature setting: <input type='text' name='new_temperature'>
<input type='submit' value='Submit' />
</form>
<p>
Current temperature: {1} F<br />
Temperature currently holding at: {2} F<br />
</p>
</body>
</html>
"""

def print_error(error):
  """print_error outputs error data for debug purposes"""
  print "<h3>Error Encountered:</h3>\n"
  print str(error)

def set_heat_setting(new_temperature):
  """set_heat_setting attempts to update the thermostat with a new temperature"""
  try:
    #print_error("Setting new temperature to " + new_temperature)
    thermostat_model(config.thermostat_address).t_heat = float(new_temperature)
  except Exception, e:
    error = "%s %s\n" % (e.__class__, e)
    print_error(error)
    sys.exit(5)

print "Content-type:text/html\n"

try:
  tstat = thermostat_model(config.thermostat_address).tstat
  current_temp = float(tstat['raw']['temp'])
  heat_setting = float(tstat['raw']['t_heat'])
except Exception, e:
  error = "%s %s\n" % (e.__class__, e)
  print_error(error)
  sys.exit(4)

cgitb.enable()
form = cgi.FieldStorage()
new_temperature = form.getvalue('new_temperature')

if new_temperature:
  set_heat_setting(new_temperature)

print html_output.format(config.thermostat_model, str(current_temp), str(heat_setting))

# vim: tabstop=2: shiftwidth=2: expandtab:
