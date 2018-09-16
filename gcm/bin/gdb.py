#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Greger Database (GDB) - Class module for GDB, representing the interface
to Greger Client Module (GCM).
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
from cfg import getLocalConfig
from cfg import setLogLevel

class GregerDatabase(object):
    '''
    Class representing all Greger (Firebase RealTime) DataBase (GDB) actions
    available to the Greger Client Module (GCM).
    '''

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

        # Initialize Firebase connection
        self._initConnection()

    def _initConnection(self):
        '''
        Initiate Firebase Admin SDK connection and obtain Realtime Database
        reference (root)
        '''
        # Logging
        localLog = logging.getLogger(self.logPath + "._initConnection")

        # Get Local Configuration Parameters
        localLog.debug("Getting configuration parameters from file...")
        config = getLocalConfig()

        # Locally relevant parameters
        gdbCert = config.get("greger_database", "cert")
        gdbURI = config.get("greger_database", "uri")
        gcmName = config.get("greger_client_module","name")
        localLog.debug("Parameter: (gdbCert) " + gdbCert)
        localLog.debug("Parameter: (gdbURI) " + gdbURI)
        localLog.debug("Parameter: (gcmName) " + gcmName)


        # Initiate connection using Certificate
        localLog.debug("Attempting to initiate connection to Firebase Realtime Database...")
        try:
            self.cred = credentials.Certificate(gdbCert)
            localLog.debug("Credentials successfully entered from " + gdbCert)

            self.firebase_app = firebase_admin.initialize_app(self.cred, {'databaseURL': gdbURI})
            localLog.debug("Handle to Realtime Database successfully obtained from " + gdbURI)

            self.dbRoot = db.reference()
            localLog.debug("Reference to Firebse Realtime Database obtained.")

            # successful message
            self.log.info("Connection to Greger DataBase (Firebase Admin Python SDK) successfully established!")

        except Exception as e:
            self.log.warning("Oops! Failed to initiate Firebase connection! - " + str(e))


        # Ensure client is defined
        localLog.debug("Ensuring account for " + gcmName + " is correct and updated...")
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

        # Locally relevant parameters
        clientsRoot = config.get("greger_database", "root")
        gcmPath = clientsRoot + "/" + config.get("greger_client_module","name")
        defaultPath = clientsRoot + "/" + "default"
        localLog.debug("Parameter: (clientsRoot) " + clientsRoot)
        localLog.debug("Parameter: (gcmPath) " + gcmPath)
        localLog.debug("Parameter: (defaultPath) " + defaultPath)

        # Does client exist?
        if self.dbRoot.child(gcmPath).get(shallow=True) is None:
            localLog.debug("GCM account is missing!")
            localLog.debug("Attempting to create GCM account using GDB default account.")
            try:
                self.dbRoot.child(gcmPath).update(self.dbRoot.child(defaultPath).get())
                self.log.info("Greger Client Module account successfully created from default!")
            except Exception as e:
                self.log.error("Oops! Failed to create Greger Client Module account on server! - " + str(e))

        # Does settings exist?
        localLog.debug("Checking the existense of the /settings child on the server account...")
        if self.dbRoot.child(gcmPath + "/settings").get(shallow=True) is None:
            localLog.debug("Child missing!")
            localLog.debug("Attempting to add settings using default settings...")
            try:
                self.dbRoot.child(gcmPath + "/settings").update(self.dbRoot.child(defaultPath + "/settings").get())
                self.log.info("Settings successfully added to Greger Client Module account from default!")
            except Exception as e:
                self.log.error("Oops! Failed to add settings to Greger Client Module account on server! - " + str(e))

        # Does all settings exist?
        else:
            localLog.debug("GCM account exists, with settings.")
            localLog.debug("Checking that all settings are present in GCM account...")
            localLog.debug("Attempting to retrieve settings...")
            try:
                defaultSettings = self.dbRoot.child(defaultPath + "/settings").get()
                gcmSettings = self.dbRoot.child(gcmPath + "/settings").get()

                localLog.debug("Settings retrieved. Reviewing all settings...")
                for setting in defaultSettings:
                    if setting not in gcmSettings:
                        localLog.debug("Setting " + str(setting) + " not present, attempting to add setting to account...")
                        try:
                            self.dbRoot.child(gcmPath + "/settings/" + setting).update(defaultSettings[setting])
                            self.log.info("Setting " + setting + " added to Greger Client Module account!")
                        except Exception as e:
                            self.log.error("Oops! Failed to write " + str(setting) + " to account! - " + str(e))
                    else:
                        localLog.debug("Setting " + str(setting) + " present!")

            except Exception as e:
                self.log.error("Oops! Failed to retrieve default settings! - " + str(e))

        # Does settings exist?
        localLog.debug("Checking the existense of the /about child on the server account...")
        if self.dbRoot.child(gcmPath + "/about").get(shallow=True) is None:
            localLog.debug("Child missing!")
            localLog.debug("Attempting to add about using default...")
            try:
                self.dbRoot.child(gcmPath + "/about").update(self.dbRoot.child(defaultPath + "/about").get())
                self.log.info("About successfully added to Greger Client Module Account from default!")
            except Exception as e:
                self.log.error("Oops! Failed to add /about to Greger Client Module Account on server! - " + str(e))

        # Update client root reference
        localLog.debug("Attempting to get db reference to GCM account...")
        self.dbGCMRoot = db.reference(gcmPath)
        localLog.debug("GCM account review complete!")

        self._accountReviewedOK = True

    def getSettings(self):
        '''
        Get GCM settings.
        '''
        localLog = logging.getLogger(self.logPath + ".getSettings")

        # Ensure CLient Module has an account and settings
        localLog.debug("Ensuring GCM has a reviewed account...")
        if not self._accountReviewedOK:
            localLog.debug("GCM not reviewed...")
            localLog.debug("Attempting to (re-)setup account for " + gcmName + "...")
            self._setupAccount()
        else:
            localLog.debug("GCM account OK!")

        # Get new settings
        localLog.debug("Attempting to retrieve new/updated settings...")
        oldSettings = self.settings.copy()
        try:
            self.settings = self.dbGCMRoot.child("settings").get()
            localLog.debug("Settings successfully retrieved!")
        except Exception as e:
            self.log.error("Oops! Failed to retrieve settings. - " + str(e))
            localLog.debug("Attempting to re-setup account for " + gcmName + "...")
            self._setupAccount()

        # Checking settings for updates...
        localLog.debug("Checking settings...")
        if oldSettings == self.settings:
            self.log.info("No new settings detected!")
        else:
            self.log.info("New/updated settings detected!")
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
            localLog.debug("All settings checked!")

        localLog.debug("Settings retrieved successfully!")

        # Update log level
        setLogLevel(self.settings['logLevel']['value'])

        return self.settings

    def getAbout(self):
        '''
        Get GCM about.
        '''
        localLog = logging.getLogger(self.logPath + ".getAbout")

        # Ensure CLient Module has an account and settings
        localLog.debug("Ensuring GCM has a reviewed account...")
        if not self._accountReviewedOK:
            localLog.debug("GCM not reviewed...")
            localLog.debug("Attempting to (re-)setup account for " + gcmName + "...")
            self._setupAccount()
        else:
            localLog.debug("GCM account OK!")

        # Get new settings
        localLog.debug("Attempting to retrieve new/updated \"about\"...")
        oldAbout = self.about.copy()
        try:
            self.about = self.dbGCMRoot.child("about").get()
            localLog.debug("\"About\" successfully retrieved!")
        except Exception as e:
            self.log.error("Oops! Failed to retrieve \"about\". - " + str(e))

        # Checking about for updates...
        localLog.debug("Checking \"about\" for updates...")
        if oldAbout == self.about:
            self.log.info("No new \"about\" detected!")
        else:
            self.log.info("New/updated \"about\" detected!")
            for parameter in sorted(self.about):
                if parameter in oldAbout:
                    if oldAbout[parameter] != self.about[parameter]:
                        self.log.info("Changed: " +
                            self.about[parameter]['name'] + " = " +
                            str(self.about[parameter]['value']))
                elif oldAbout == {}:
                    self.log.info("About: " +
                        self.about[parameter]['name'] + " = " +
                        str(self.about[parameter]['value']))
                else:
                    self.log.info("New: " +
                        self.about[parameter]['name'] + " = " +
                        str(self.about[parameter]['value']))
            localLog.debug("All \"about\" parameters checked!")

        localLog.debug("All \"about\" parameters retrieved successfully!")

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
