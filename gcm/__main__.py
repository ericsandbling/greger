#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Greger Client Module 1-wire Client - RPi client for publishing 1-wire data to
Google Firebase.
Usage:
Options:
"""

__author__ = "Eric Sandbling"
__license__ = 'MIT'
__status__ = 'Development'

# ToDo:
# =====
# 1. Add Logging
# 2. Find a way to read "changes" on the 1wire network

import os, sys, argparse
import getpass
import time
from threading import Timer
import logging

# Layout and formating libraries
import ConfigParser

# Project specific libraries
import ow

# Custom libraries
import bin.owlib as owlib
import bin.fblib as fblib

# logging
# create logger
logger = logging.getLogger("gcm")
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

class Main(object):
    """
    Main class which holds the main sequence of the application.
    """
    def __init__(self):
        '''
        Initialize the main class
        '''
        # Setup logging
        self.log = logging.getLogger("gcm.Main")
        self.log.info("==== STARTING Greger Client Module APPLICATION ===")

        # Get Command Line Arguments
        self.log.debug("Getting commandline arguments...")
        self._getCommandLineArguments()

        # Get variables for self
        self._location = os.path.abspath(__file__)
        self._location = self._location[:-11]        # Trim __main__.py from path
        self._username = getpass.getuser()

        # Get configuration parameters
        self.log.debug("Getting configuration parameters from file...")
        self.config = ConfigParser.RawConfigParser()
        cfgPath = self._location + "config.cfg"
        self.config.read(cfgPath)
        self.log.info("Loaded configuration file from: "+ cfgPath)

        # Initiate firebase connection
        self.log.debug("Initiating Firebase Realtime Database connection...")
        self.firebaseConnection = fblib.RTDB(self.config, self._location)

        # Get initial settings from database
        self.log.debug("Getting initial settings from database...")
        self._updateSettings()
        # self.settings = self.firebaseConnection.getSettings()

        # Init OW devices and update settings
        self.log.debug("Initiating 1-Wire Server connection...")
        self.owDevices = owlib.owDevices(self.settings)

        # Start execution timer
        self.log.debug("Initiating End Execution Timer...")
        self.execute = True
        self.stopTime = 0
        self.pauseExecution = False
        if self.runTime != 0:
            self._executionTimer = Timer(float(self.runTime), self._stop)
            self._executionTimer.start()
            self.log.info("End Execution Timer started with runTime: " + str(self.runTime) + " second(s).")
        else:
            self.log.info("End Execution Timer disabled! (infinite run time enabled)")

        # Start main loop
        self.log.debug("Attempting to start main loop...")
        self.mainLoop()

    def whereami(self):
        """
        Display our current path.
        """
        print(self._location)

    def whoami(self):
        """
        Display the user who executes this program.
        """
        print self._username

    def _getCommandLineArguments(self):
        '''
        Parse and get commandline arguments.
        '''
        # Get command line arguments
        parser = argparse.ArgumentParser()

        # Run Time (optional)
        parser.add_argument(
            '-rt','--runTime',
            type=int,
            # dest='runTime',
            default=15,
            help='Run-time of the application in seconds. 0 = Infinite runtime.')

        # Get arguments from parser
        # parser.set_defaults(printOn=True)
        self.args = parser.parse_args()

        # Depacking some parameters
        self.runTime = self.args.runTime

        # Log
        infoMsg = "Application start conditions: gcm "
        infoMsg += "-rt: " +  str(self.args.runTime) + " "
        self.log.info(infoMsg)

    def _stop(self):
        '''
        Set flags to stop execution
        '''
        self.execute = False
        self.stopTime = time.time()
        self.log.info("End Execution Timer hit, main loop execution flag set to False.")

    def _updateSettings(self):
        '''
        Update all settings.
        '''
        # Log
        # self.logUpdateSettings = logging.getLogger("gcm.Main._updateSettings")
        localLog = logging.getLogger("gcm.Main._updateSettings")
        localLog.debug("Updating GCM settings...")

        # Retrieve updated settings from database
        localLog.debug("Retrieving updated settings from database...")
        try:
            # Get updated settings
            self.settings = self.firebaseConnection.getSettings()
            localLog.debug("New/modified settings successfully retrieved from database.")
        except Exception as e:
            self.log.warning("Oops! Failed to get data! - " + str(e))

        # Update log settings
        if self.settings['logLevel']['value'] <= 1:
            logger.setLevel(logging.DEBUG)
        elif self.settings['logLevel']['value'] == 2:
            logger.setLevel(logging.INFO)
        elif self.settings['logLevel']['value'] == 3:
            logger.setLevel(logging.WARNING)
        elif self.settings['logLevel']['value'] == 4:
            logger.setLevel(logging.ERROR)
        elif self.settings['logLevel']['value'] == 5:
            logger.setLevel(logging.CRITICAL)
        else:
            logger.setLevel(logging.DEBUG)
            localLog.debug("Could not determin log level! - " + str(self.settings['logLevel']['value']))

        # Check if execution is paused
        localLog.debug("Checking if execution is pasued from database...")
        if self.settings['deviceReadingsEnable']['value']:
            self.pauseExecution = False
            localLog.debug("Execution is paused!")
        else:
            self.pauseExecution = True
            localLog.debug("Execution is not paused.")

        # # Update owDevices settings
        # localLog.debug("Updating new/changed 1-Wire Server settings...")
        # self.owDevices.settings = self.settings

    def mainLoop(self):
        '''
        Main loop of the program.
        '''
        # Logging
        localLog = logging.getLogger("gcm.Main.mainLoop")
        self.log.info("Starting main loop...")

        # Main loop
        while self.execute:
            # Update new/modified settings
            self._updateSettings()

            # Update owDevices settings
            localLog.debug("Updating new/changed 1-Wire Server settings...")
            self.owDevices.settings = self.settings

            # Check if execution is paused
            if self.pauseExecution:
                time.sleep(5)
                continue

            # Read ow devices
            localLog.debug("Attempting to read 1-Wire Devices...")
            owDeviceReading = self.owDevices.readAll()
            localLog.debug("Retrieving timeseries...")
            timeseries = self.owDevices.timeseries

            # Publish current to firebase
            localLog.debug("Attempting to publish current 1-Wire Device reading to database...")
            try:
                self.firebaseConnection.update('current', owDeviceReading)
                self.log.info("Current 1-Wire Device reading published to Firebse Realtime DataBase.")
            except Exception as e:
                self.log.warning("Oops! Failed to update data! - " + str(e))

            # Publish timeseries to firebsae
            localLog.debug("Attempting to publish timeseries to database...")
            # Update each device time-series
            for device in timeseries:
                for sensor in timeseries[device]:
                    updatePath = 'timeseries/' + device + "/" + sensor
                    try:
                        self.firebaseConnection.update(updatePath, self.owDevices.timeseries[device][sensor])
                        localLog.debug(updatePath + " updated with latest timeseries.")
                    except Exception as e:
                        self.log.warning("Oops! Failed to update data! - " + str(e))
            # Print message
            self.log.info("Timeseries published to Firebase Realtime Database.")

        # Print END message
        self.log.info("Execution ended! (Stopped at:" +
            time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.stopTime)) + ")")

if __name__ == '__main__':
    try:
        APP = Main()
    except KeyboardInterrupt:
        print 'Interrupted!'
        try:
            sys.exit("\n=== APPLICATION END ===")
        except SystemExit:
            print "\n=== APPLICATION END ==="
            os._exit(0)

    print "\n=== APPLICATION END ==="
