#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
fblib - Library for Firebase database.

Library of functions adapted for the Greger Client Module (GCM).
"""

__author__ = "Eric Sandbling"
__status__ = 'Development'

# Modules goes here
import ow
import time, sys
import logging

# Firebase Python Admin SDK
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Local parameters
CLIENTS_ROOT = "clientModules"

class GDB(object):
    '''
    Class representing all Greger (Firebase RealTime) DataBase (GDB) actions
    available to the Greger Client Module (GCM).
    '''

    def __init__(self, config, location):
        '''
        Initialize class.
        '''
        # Logging
        self.logPath = "root.GDB"
        self.log = logging.getLogger(self.logPath)
        self.log.debug("Creating Class Log for Realtime Database (GDB).")

        # Define parameters
        self.config = config
        self._location = location
        self.settings = {}

        # Get settings from file
        self.log.debug("Getting configuration from file...")
        self.clientName = self.config.get("global", "client_module_name")
        self.clientRoot = CLIENTS_ROOT + "/" + self.clientName

        # Initialize Firebase connection
        self._initConnection()

    def _initConnection(self):
        '''
        Initiate Firebase Admin SDK connection and obtain Realtime Database
        reference (root)
        '''
        localLog = logging.getLogger(self.logPath + "._initConnection")

        # Initiate connection using Certificate
        localLog.debug("Attempting to initiate connection to Firebase Realtime Database...")
        try:
            self.cred = credentials.Certificate(self.config.get("firebase", "firebase_cert"))
            localLog.debug("Credentials successfully entered.")

            self.firebase_app = firebase_admin.initialize_app(self.cred, {
                'databaseURL':self.config.get("firebase", "firebase_app")})
            localLog.debug("Handle to Realtime Database successfully obtained.")

            self.dbRoot = db.reference()
            localLog.debug("Reference to Firebse Realtime Database obtained.")
            self.log.info("Firebase Admin Python SDK connection initiated.")

        except Exception as e:
            self.log.warning("Oops! Failed to initiate Firebase connection! - " + str(e))


        # Ensure client is defined
        localLog.debug("Ensuring this Greger Client Module (" + self.clientName + ") account is correct and updated...")
        self._setupAccount()

        # Retrieve Settings
        localLog.debug("Attempting to retrieve settings from account...")
        self.getSettings()

    def _setupAccount(self):
        '''
        Reset and/or setup Greger Client Module account with default values.
        '''
        localLog = logging.getLogger(self.logPath + "._setupAccount")

        # Does client exist?
        if self.dbRoot.child(self.clientRoot).get(shallow=True) is None:
            localLog.debug("GCM account is missing.")
            localLog.debug("Attempting to create GCM account using default account.")
            try:
                self.dbRoot.child(self.clientRoot).update(self.dbRoot.child(CLIENTS_ROOT + "/default").get())
                self.log.info("Greger Client Module Account successfully created from default!")
            except Exception as e:
                self.log.error("Oops! Failed to create Greger Client Module Account on server! - " + str(e))

        # Does settings exist?
        elif self.dbRoot.child(self.clientRoot + "/settings").get(shallow=True) is None:
            localLog.debug("GCM account exists, but are missing settings.")
            localLog.debug("Attempting to add settings using default settings...")
            try:
                self.dbRoot.child(self.clientRoot + "/settings").update(self.dbRoot.child(CLIENTS_ROOT + "/default/settings").get())
                self.log.info("Settings successfully added to Greger Client Module Account from default!")
            except Exception as e:
                self.log.error("Oops! Failed to add settings to Greger Client Module Account on server! - " + str(e))

        # Does all settings exist?
        else:
            localLog.debug("GCM account exists, with settings.")
            localLog.debug("Checking that all settings are present in GCM account...")
            localLog.debug("Attempting to retrieve settings...")
            try:
                defaultSettings = self.dbRoot.child(CLIENTS_ROOT + "/default/settings").get()
                gcmSettings = self.dbRoot.child(self.clientRoot + "/settings").get()

                localLog.debug("Settings retrieved. Reviewing all settings...")
                for setting in defaultSettings:
                    if setting not in gcmSettings:
                        localLog.debug("Setting " + str(setting) + " not present, attempting to add setting to account...")
                        try:
                            self.dbRoot.child(self.clientRoot + "/settings/" + setting).update(defaultSettings[setting])
                            self.log.info("Setting " + setting + " added to Greger Client Module account!")
                        except Exception as e:
                            self.log.error("Oops! Failed to write " + str(setting) + " to account! - " + str(e))
                    else:
                        localLog.debug("Setting " + str(setting) + " present!")

            except Exception as e:
                self.log.error("Oops! Failed to retrieve default settings! - " + str(e))

        # Update client root reference
        localLog.debug("Attempting to get db reference to GCM account...")
        self.dbGCMRoot = db.reference(self.clientRoot)
        localLog.debug("GCM account review complete!")

    def getSettings(self):
        '''
        Get GCM settings.
        '''
        localLog = logging.getLogger(self.logPath + ".getSettings")

        # Ensure CLient Module has an account and settings
        localLog.debug("Ensuring GCM has an account with settings.")
        if self.dbRoot.child(self.clientRoot).get(shallow=True) is None:
            if self.dbRoot.child(self.clientRoot + "/settings").get(shallow=True) is None:
                self._setupAccount()

        # Get new settings
        localLog.debug("Attempting to retrieve new/updated settings...")
        oldSettings = self.settings.copy()
        try:
            self.settings = self.dbGCMRoot.child("settings").get()
            localLog.debug("Settings successfully retrieved!")
        except Exception as e:
            self.log.error("Oops! Failed to retrieve settings. - " + str(e))

        # Checking settings for updates...
        if oldSettings == self.settings:
            self.log.info("Settings reviewed successfully!")
        else:
            localLog.debug("Checking settings for updates...")
            for setting in sorted(self.settings):
                if setting in oldSettings:
                    if oldSettings[setting] != self.settings[setting]:
                        self.log.info("Changed setting: " +
                            self.settings[setting]['name'] + " = " +
                            str(self.settings[setting]['value']))
                elif oldSettings == {}:
                    self.log.info("Setting detected: " +
                        self.settings[setting]['name'] + " = " +
                        str(self.settings[setting]['value']))
                else:
                    self.log.info("New setting: " +
                        self.settings[setting]['name'] + " = " +
                        str(self.settings[setting]['value']))

        localLog.debug("Settings retrieved successfully!")
        return self.settings

    def update(self, path, value):
        '''
        Update Greger Client Module account child with value at path.
        '''
        localLog = logging.getLogger(self.logPath + ".update")

        localLog.debug("Attempting to update GCM account child...")
        try:
            self.dbGCMRoot.child(path).update(value)
        except Exception as e:
            self.log.error("Oops! Failed to update child! - " + str(e))
