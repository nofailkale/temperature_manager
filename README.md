temperature_manager
=================

# About

temperature_manager can be used to record and graph temperature data with 
Google Docs and Google Apps Script.  The software can also send email alerts
based on temperature monitoring events.

temperature_manager currently interfaces with Raspberry Pis connected to 
DS18B20 temperature sensors as well as Radio Thermostat Wi-Fi based
thermostats.

Details on building, configuring and using this software can be found at [website](http://technotes.nofailkale.com/2013/12/temperature-monitoring-tracking-and.html)

# Code

## config_example

Common configuration file. Copy the file to config.py and update the settings
for your deployment.

## ds_temperature_tracker.py

Intended to run out of cron to collect, record and alert on temperature data
produced by DS18B20 temperature sensors

## temp_lib.py

Contains shared helper functions for temperature_manager.

## test_for_temp_guage.sh

Test if your DS18B20 temperature sensor is operational

## verify_temperature_alert.py

Intended to run out of cron as a watchdog program that sends email alerts 
if temperature data recording is not working.

## rt_set_temp.py

A basic CGI based web interface for setting the temperature on a Radio
Thermostat thermostat.  This is useful if you'd like to avoid connecting
your thermostats over unencrypted HTTP to the vendor's cloud services.

## rt_temperature_tracker.py

Intended to run out of cron to collect, record and alert on temperature data
produced by Radio Thermostat thermostats

## Google Integration

For Google Docs and Apps Script integration code, see the project's [website](http://technotes.nofailkale.com/2013/12/temperature-monitoring-tracking-and.html)

# Credits

Base temperature reading code for the DS18B20 was derived from [Adafruit's Raspberry Pi Lesson 11. DS18B20](http://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing/software)  by Simon Monk
