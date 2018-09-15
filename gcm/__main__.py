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
from gcm import GCM

# Create root logger
logger = logging.getLogger("root")
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

# Create logging handlers
consoleHandler = logging.StreamHandler()

# Set default logging level
consoleHandler.setLevel(logging.DEBUG)
# consoleHandler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s %(name)s [%(levelname)s] : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Add formatter to logging handlers
consoleHandler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(consoleHandler)

if __name__ == '__main__':
    try:
        APP = GCM()
    except KeyboardInterrupt:
        print 'Interrupted!'
        try:
            sys.exit("\n=== APPLICATION END (sys) ===")
        except SystemExit:
            print "\n=== APPLICATION END (os) ==="
            os._exit(0)

    print "\n=== APPLICATION END (-) ==="
