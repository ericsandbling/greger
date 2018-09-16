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

# Local Modules
from configlib import getLocalConfig

class GDB(object):
    '''
    Class representing all Greger (Firebase RealTime) DataBase (GDB) actions
    available to the Greger Client Module (GCM).
    '''

    # def __init__(self, config, location):
    def __init__(self):
        '''
        Initialize class.
        '''
        # Logging
        self.logPath = "root.GDB"
        self.log = logging.getLogger(self.logPath)
        localLog = logging.getLogger(self.logPath + ".__init__")
        localLog.debug("Starting Greger (Firebase RealTime) Database...")

        # Define parameters
        self.settings = {}
        self.about = {}

        # Get Local Configuration Parameters
        # localLog.debug("Getting configuration parameters from file...")

        # config = getLocalConfig()
        # self.GDBConfig = {}

        # self.GDBConfig.update({'gcmName' : config.get("greger_client_module", "name")})
        # self.GDBConfig.update({'gcmLocation' : config.get("greger_client_module", "location")})
        #
        # self.GDBConfig.update({'gdbRoot' : config.get("greger_database", "root") + "/" + self.GDBConfig['gcmName']})
        # self.GDBConfig.update({'gdbPath' : config.get("greger_database", "path")})
        # self.GDBConfig.update({'gdbCert' : config.get("greger_database", "cert")})

        # for parameter in self.GDBConfig:
        #     localLog.debug("Parameter: " + parameter + " = " + self.GDBConfig[parameter])

        # Initialize Firebase connection
        self._initConnection()

    def _initConnection(self):
        '''
        Initiate Firebase Admin SDK connection and obtain Realtime Database
        reference (root)
        '''
        localLog = logging.getLogger(self.logPath + "._initConnection")

        # Get Local Configuration Parameters
        localLog.debug("Getting configuration parameters from file...")
        config = getLocalConfig()

        # Initiate connection using Certificate
        localLog.debug("Attempting to initiate connection to Firebase Realtime Database...")
        try:
            gdbCert = config.get("greger_database", "cert")
            self.cred = credentials.Certificate(gdbCert)
            localLog.debug("Credentials successfully entered from " + gdbCert)

            gdbURI = config.get("greger_database", "uri")
            self.firebase_app = firebase_admin.initialize_app(self.cred, {'databaseURL': gdbURI})
            localLog.debug("Handle to Realtime Database successfully obtained from " + gdbURI)

            self.dbRoot = db.reference()
            localLog.debug("Reference to Firebse Realtime Database obtained.")

            # successful message
            self.log.info("Connection to Greger DataBase (Firebase Admin Python SDK) successfully established!")

        except Exception as e:
            self.log.warning("Oops! Failed to initiate Firebase connection! - " + str(e))


        # Ensure client is defined
        localLog.debug("Ensuring account for " + config.get("greger_client_module","name") + " is correct and updated...")
        self._setupAccount()

        # Retrieve Settings
        localLog.debug("Attempting to retrieve settings from account...")
        self.getSettings()

        localLog.debug("Attempting to retrieve about from account...")
        self.getAbout()

    def _setupAccount(self):
        '''
        Reset and/or setup Greger Client Module account with default values.
        '''
        localLog = logging.getLogger(self.logPath + "._setupAccount")

        # Get Local Configuration Parameters
        localLog.debug("Getting configuration parameters from file...")
        config = getLocalConfig()
        self.gdbRootPath = config.get("greger_database", "root") + "/" + config.get("greger_client_module","name")

        # Does client exist?
        if self.dbRoot.child(self.gdbRootPath).get(shallow=True) is None:
            localLog.debug("GCM account is missing.")
            localLog.debug("Attempting to create GCM account using default account.")
            try:
                self.dbRoot.child(self.GDBConfig['gdbRoot']).update(self.dbRoot.child(CLIENTS_ROOT + "/default").get())
                self.log.info("Greger Client Module Account successfully created from default!")
            except Exception as e:
                self.log.error("Oops! Failed to create Greger Client Module Account on server! - " + str(e))

        # Does settings exist?
        localLog.debug("Checking the existense of the /settings child on the server account...")
        if self.dbRoot.child(self.GDBConfig['gdbRoot'] + "/settings").get(shallow=True) is None:
            localLog.debug("Child missing!")
            localLog.debug("Attempting to add settings using default settings...")
            try:
                self.dbRoot.child(self.GDBConfig['gdbRoot'] + "/settings").update(self.dbRoot.child(CLIENTS_ROOT + "/default/settings").get())
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
                gcmSettings = self.dbRoot.child(self.GDBConfig['gdbRoot'] + "/settings").get()

                localLog.debug("Settings retrieved. Reviewing all settings...")
                for setting in defaultSettings:
                    if setting not in gcmSettings:
                        localLog.debug("Setting " + str(setting) + " not present, attempting to add setting to account...")
                        try:
                            self.dbRoot.child(self.GDBConfig['gdbRoot'] + "/settings/" + setting).update(defaultSettings[setting])
                            self.log.info("Setting " + setting + " added to Greger Client Module account!")
                        except Exception as e:
                            self.log.error("Oops! Failed to write " + str(setting) + " to account! - " + str(e))
                    else:
                        localLog.debug("Setting " + str(setting) + " present!")

            except Exception as e:
                self.log.error("Oops! Failed to retrieve default settings! - " + str(e))

        # Does settings exist?
        localLog.debug("Checking the existense of the /about child on the server account...")
        if self.dbRoot.child(self.GDBConfig['gdbRoot'] + "/about").get(shallow=True) is None:
            localLog.debug("Child missing!")
            localLog.debug("Attempting to add about using default...")
            try:
                self.dbRoot.child(self.GDBConfig['gdbRoot'] + "/about").update(self.dbRoot.child(CLIENTS_ROOT + "/default/about").get())
                self.log.info("About successfully added to Greger Client Module Account from default!")
            except Exception as e:
                self.log.error("Oops! Failed to add /about to Greger Client Module Account on server! - " + str(e))

        # Update client root reference
        localLog.debug("Attempting to get db reference to GCM account...")
        self.dbGCMRoot = db.reference(self.GDBConfig['gdbRoot'])
        localLog.debug("GCM account review complete!")

    def getSettings(self):
        '''
        Get GCM settings.
        '''
        localLog = logging.getLogger(self.logPath + ".getSettings")

        # Ensure CLient Module has an account and settings
        localLog.debug("Ensuring GCM has an account with settings.")
        if self.dbRoot.child(self.GDBConfig['gdbRoot']).get(shallow=True) is None:
            if self.dbRoot.child(self.GDBConfig['gdbRoot'] + "/settings").get(shallow=True) is None:
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
            self.log.info("No new settings detected!")
        else:
            self.log.info("New/updated settings detected!")
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

    def getAbout(self):
        '''
        Get GCM about.
        '''
        localLog = logging.getLogger(self.logPath + ".getAbout")

        # Ensure CLient Module has an account and settings
        localLog.debug("Ensuring GCM has an account with about.")
        if self.dbRoot.child(self.GDBConfig['gdbRoot']).get(shallow=True) is None:
            if self.dbRoot.child(self.GDBConfig['gdbRoot'] + "/about").get(shallow=True) is None:
                self._setupAccount()

        # Get new settings
        localLog.debug("Attempting to retrieve new/updated about...")
        oldAbout = self.about.copy()
        try:
            self.about = self.dbGCMRoot.child("about").get()
            localLog.debug("About successfully retrieved!")
        except Exception as e:
            self.log.error("Oops! Failed to retrieve settings. - " + str(e))

        # Checking about for updates...
        if oldAbout == self.about:
            self.log.info("No new about detected!")
        else:
            self.log.info("New/updated about detected!")
            localLog.debug("Checking about for updates...")
            for child in sorted(self.about):
                if child in oldAbout:
                    if oldAbout[child] != self.about[child]:
                        self.log.info("Changed: " +
                            self.about[child]['name'] + " = " +
                            str(self.about[child]['value']))
                elif oldAbout == {}:
                    self.log.info("About: " +
                        self.about[child]['name'] + " = " +
                        str(self.about[child]['value']))
                else:
                    self.log.info("New: " +
                        self.about[child]['name'] + " = " +
                        str(self.about[child]['value']))

        localLog.debug("About retrieved successfully!")

        return self.about

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
