#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Applicatopn root
"""

__author__ = "Eric Sandbling"
__license__ = 'MIT'
__status__ = 'Development'

import os, sys
import logging

# Custom libraries
from bin.gcm import GregerClientModule
import bin.common as lib

if __name__ == '__main__':

    logger = lib.createLogger()
    logger.info("Starting application....")
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
