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
