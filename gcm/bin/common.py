#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration and settings library for the Greger Client Module software.
"""

__author__ = "Eric Sandbling"
__status__ = 'Development'

import os, sys
from os import listdir
from os.path import isfile, join

import ConfigParser
import logging
from logging.handlers import RotatingFileHandler

#### Update tools ####
def restart_program():
    """
    Restarts the current program.

    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function.
    """
    # Logging
    localLog = logging.getLogger("root")
    localLog.info("Restarting application...")

    python = sys.executable
    localLog.info("Path to restart: " + python)
    for arg in sys.argv:
        localLog.info("Arg: " + arg)

    os.execl(python, python, * sys.argv)

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

    enableConsolLogger = False

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
    rotatingFileHandler = RotatingFileHandler(
    logPath + sysLog,
    mode='a+',
    maxBytes=int(logMaxBytes),
    backupCount=int(logBackupCount),
    encoding=None,
    delay=0)
    if enableConsolLogger:
        consoleHandler = logging.StreamHandler()

    # Create formatter
    fmt = '%(asctime)s %(name)s [%(levelname)s] : %(message)s'
    formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')

    # Add formatter to logging handlers
    rotatingFileHandler.setFormatter(formatter)
    if enableConsolLogger:
        consoleHandler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(rotatingFileHandler)
    if enableConsolLogger:
        logger.addHandler(consoleHandler)

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
