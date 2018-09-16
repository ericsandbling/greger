#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
configlib - Configurations.

Library of functions adapted for the Greger Client Module (GCM).
"""

__author__ = "Eric Sandbling"
__status__ = 'Development'

from os import listdir
from os.path import isfile, join

import ConfigParser
import logging

_logLevelStr = {
    '0' : 'NOTSET',
    '10' : 'DEBUG',
    '20' : 'INFO',
    '30' : 'WARNING',
    '40' : 'ERROR',
    '50' : 'CRITICAL'
}

def getLocalConfig():
    '''
    Function to retrieve local configuration parameters from file.

    Returns config
    '''
    # Logging
    localLog = logging.getLogger("root.getLocalConfig")

    # Init config
    config = ConfigParser.RawConfigParser()

    # Get paths to configuration files
    cfgPath = "/etc/gcm/config"
    cfgFiles = [join(cfgPath,cfgFile) for cfgFile in listdir(cfgPath) if isfile(join(cfgPath,cfgFile))]

    # Load configuration files
    cfgFilesRead = config.read(cfgFiles)
    for file in cfgFilesRead:
        localLog.info("Loaded configuration file from: " + str(file))

    return config

def setLogLevel(logLevel, loggerName='root'):
    '''
    Update logger level.
    '''
    # Logging
    localLog = logging.getLogger("root.setLogLevel")

    oldLogLevel = logging.getLogger(loggerName).getEffectiveLevel()

    if logLevel != oldLogLevel:
        localLog.debug("New log level detected in settings!")
        localLog.debug("Attempting to update log level to " + _logLevelStr[str(logLevel)] + " for \"" + loggerName + "\"...")

        if str(logLevel) in _logLevelStr:
            logging.getLogger(loggerName).setLevel(logLevel)
            localLog.debug("Log level successfully updated!")
        else:
            localLog.warning("Could not determin log level! - " + str(logLevel))
            logging.getLogger(loggerName).setLevel(logging.DEBUG)
            localLog.debug("Setting log level to default (DEBUG).")

        newLogLevel = logging.getLogger(loggerName).getEffectiveLevel()
        localLog.info("Logger \"" + loggerName + "\" set to " + _logLevelStr[str(newLogLevel)] + "!")

    else:
        localLog.debug("Log level reviewed - No change!")
