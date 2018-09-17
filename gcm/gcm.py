#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Greger Client Module - RPi client for publishing 1-wire data to Greger Database
(GDB).
"""

__author__ = "Eric Sandbling"
__license__ = 'MIT'
__status__ = 'Development'

import os, sys, argparse
import time
from threading import Timer
import logging
import ConfigParser

# Custom libraries
from bin.owd import owDevices
import bin.gdb as gdb
import bin.gua as gua
from bin.common import getLocalConfig

class GregerClientModule(object):
    """
    Main class which holds the main sequence of the application.
    """
    def __init__(self):
        '''
        Initialize the main class
        '''
        # Setup logging
        self.logPath = "root.GCM"
        self.log = logging.getLogger(self.logPath)
        localLog = logging.getLogger(self.logPath + ".__init__")
        localLog.debug("Initiating Greger Client Module...")

        # Get Command Line Arguments
        localLog.debug("Getting command line arguments...")
        self._getCommandLineArguments()

        # Get variables for self
        self._location = os.path.abspath(__file__)
        self._location = self._location[:-11]        # Trim __main__.py from path

        # Initiate firebase connection and get settings from server
        localLog.debug("Attempting to initiate Greger Database (GDB)...")
        self.GregerDatabase = gdb.GregerDatabase()
        localLog.debug("Attempting to start Greger Database (GDB)...")
        self.GregerDatabase.start()

        # Initialize Greger Update Agent
        localLog.debug("Attempting to initiate Greger Update Agent (GUA)...")
        self.GregerUpdateAgent = gua.GregerUpdateAgent()
        localLog.debug("Attempting to start Greger Update Agent (GUA)...")
        self.GregerUpdateAgent.start()

        # Init owDevices and update settings
        localLog.debug("Attempting to initiate 1-Wire Server connection...")
        self.owDevices = owDevices()

        # Start execution timer
        localLog.debug("Attempting to initiate Execution Timer...")
        self._startExecution()

        # Start main loop
        localLog.debug("Greger Client Module initiated successfully!")
        localLog.debug("Initiating Main...")
        self.main()

    def whereami(self):
        """
        Display our current path.
        """
        print(self._location)

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

    def _startExecution(self):
        '''
        Start execution timer.
        '''
        # Log
        localLog = logging.getLogger(self.logPath + "._startExecution")
        localLog.debug("Initiating Execution Timer...")

        # Execution Timer parameters
        self.execute = True
        self.stopTime = 0
        self.pauseExecution = False

        # Start Execution Timer
        if self.runTime != 0:
            self._executionTimer = Timer(float(self.runTime), self._stopExecution)
            self._executionTimer.start()
            localLog.debug("Execution Timer started successfully!")
            self.log.info("End Execution Timer started with runTime: " + str(self.runTime) + " second(s).")
        else:
            localLog.debug("Execution Timer disabled! runTime=" + self.runTime)
            self.log.info("End Execution Timer disabled! (infinite run time enabled)")

    def _stopExecution(self):
        '''
        Set flags to stop execution
        '''
        # Log
        localLog = logging.getLogger(self.logPath + "._stopExecution")
        localLog.debug("Attempting to stop all execution...")

        # Set stop flag for main method
        self.execute = False
        self.stopTime = time.time()
        self.log.info("End Execution Timer hit, main loop execution flag set to False.")

        # Stop Greger Update Agent (GUA)
        localLog.debug("Attempting to stop Greger Update Agent (GUA)...")
        try:
            self.GregerUpdateAgent.stopExecution.set()
        except Exception as e:
            localLog.error("Oops! Failed to stop Greger Update Agent - " + str(e))

        # Stop Greger Database (GDB)
        localLog.debug("Attempting to stop Greger Database (GDB)...")
        try:
            self.GregerDatabase.stopExecution.set()
        except Exception as e:
            localLog.error("Oops! Failed to stop Greger Update Agent - " + str(e))


    def _updateSettings(self):
        '''
        Update all settings.
        '''
        # Log
        localLog = logging.getLogger(self.logPath + "._updateSettings")
        localLog.debug("Updating GCM settings...")

        # Retrieve updated settings from database
        localLog.debug("Retrieving updated settings from database...")
        oldSettings = self.settings.copy()
        try:
            # Get updated settings
            self.settings = self.GregerDatabase.getSettings()
            localLog.debug("New/modified settings successfully retrieved from database.")
        except Exception as e:
            self.log.warning("Oops! Failed to get data! - " + str(e))

        if oldSettings != self.settings:
            # Check if execution is paused
            localLog.debug("Checking if execution is pasued from database...")
            if self.settings['deviceReadingsEnable']['value']:
                self.pauseExecution = False
                localLog.debug("Execution is paused!")
            else:
                self.pauseExecution = True
                localLog.debug("Execution is not paused.")

            # Update Greger Update Agent settings
            localLog.debug("Updating new/changed GUA settings...")
            self.GregerUpdateAgent.settings = self.settings

            # Update owDevices settings
            localLog.debug("Updating new/changed owDevices settings...")
            self.owDevices.settings = self.settings

        else:
            localLog.debug("No new settings detected!")

    def main(self):
        '''
        Main loop of the program.
        '''
        # Logging
        localLog = logging.getLogger(self.logPath + ".main")
        self.log.info("Starting main loop...")

        # Main loop
        while self.execute:
            # Update new/modified settings
            # self._updateSettings()

            # Check if execution is paused
            # if self.pauseExecution:
            if not self.GregerDatabase.settings['gcmEnableOWD']['value']:
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
                self.GregerDatabase.update('current', owDeviceReading)
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
                        self.GregerDatabase.update(updatePath, self.owDevices.timeseries[device][sensor])
                        localLog.debug(updatePath + " updated with latest timeseries.")
                    except Exception as e:
                        self.log.warning("Oops! Failed to update data! - " + str(e))
            # Print message
            self.log.info("Timeseries published to Firebase Realtime Database.")

        # Print END message
        self.log.info("Execution ended! (Stopped at: " +
            time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.stopTime)) + ")")
