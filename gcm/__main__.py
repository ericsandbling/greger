#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Applicatopn root
"""

__author__ = "Eric Sandbling"
__license__ = 'MIT'
__status__ = 'Development'

import os, sys
import getpass
import logging

# Custom libraries
from bin.gcm import GregerClientModule
import bin.common as lib

if __name__ == '__main__':

    username = getpass.getuser()
    print "Greger Client Module Application started by: " + username

    logger = lib.createLogger()
    logger.info("Starting application....")
    logger.info("Application started by: " + username)
    try:
        GCM = GregerClientModule()
        GCM.start()
        GCM.join()

    except KeyboardInterrupt:
        print 'Interrupted!'
        logger.info("Interrupted!")
        try:
            sys.exit("\n=== APPLICATION END (sys) ===")
        except SystemExit:
            os._exit(0)
