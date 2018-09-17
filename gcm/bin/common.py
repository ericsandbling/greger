#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration and settings library for the Greger Client Module software.
"""

__author__ = "Eric Sandbling"
__status__ = 'Development'

from os import listdir
from os.path import isfile, join

import ConfigParser
import logging
from logging.handlers import RotatingFileHandler

#### Configuration Methods ####

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

#### Logging Methods ####

_logLevelStr = {
    '0' : 'NOTSET',
    '10' : 'DEBUG',
    '20' : 'INFO',
    '30' : 'WARNING',
    '40' : 'ERROR',
    '50' : 'CRITICAL'
}

def createLogger():
    '''
    Create common root logger.
    '''
    # Get Local Configuration Parameters
    config = getLocalConfig()

    # Locally relevant parameters
    logPath = config.get("log", "path")
    sysLog = config.get("log", "syslog")

    logMaxBytes = config.get("log", "maxbytes")
    logBackupCount = config.get("log", "backupcount")

    # Create root logger
    logger = logging.getLogger("root")

    # Set logger default level
    logger.setLevel(logging.DEBUG)
    # logger.setLevel(logging.INFO)

    # Create logging handlers
    consoleHandler = logging.StreamHandler()
    # fileHandler = logging.FileHandler(logFile, mode='w')
    rotatingFileHandler = RotatingFileHandler(
        logPath + sysLog,
        mode='a',
        maxBytes=int(logMaxBytes),
        backupCount=int(logBackupCount),
        encoding=None,
        delay=0)

    # Set default logging level
    # consoleHandler.setLevel(logging.DEBUG)
    # consoleHandler.setLevel(logging.INFO)

    # Create formatter
    fmt = '%(asctime)s %(name)s [%(levelname)s] : %(message)s'
    formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')

    # Add formatter to logging handlers
    consoleHandler.setFormatter(formatter)
    # fileHandler.setFormatter(formatter)
    rotatingFileHandler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(consoleHandler)
    # logger.addHandler(fileHandler)
    logger.addHandler(rotatingFileHandler)

    logger.debug("Logger created successfully!")

    return logger


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
