#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Greger Update Agent (GUA) module for the Greger Client Module
"""

__author__ = "Eric Sandbling"
__license__ = 'MIT'
__status__ = 'Development'

# System modules
import os
import logging
import subprocess
from threading import Event
from threading import Thread

# Local Modules
from common import getLocalConfig
from gdb import GregerDatabase as greger

class GregerUpdateAgent(Thread):
    """
    Main class which holds the main sequence of the application.
    """

    is_active = False

    def __init__(self):
        '''
        Initialize the main class
        '''
        Thread.__init__(self)

        # Setup logging
        self.logPath = "root.GUA"
        self.log = logging.getLogger(self.logPath)
        localLog = logging.getLogger(self.logPath + ".__init__")
        localLog.debug("Initiating Greger Update Agent (GUA)...")

        # Stop execution handler
        self.stopExecution = Event()

        # Get local path
        self._location = os.path.abspath(__file__)
        self._location = self._location[:-15] # Trim gcm/__main__.py from path to get at location of application
        localLog.debug("Local path: " + self._location)

        self.log.info("Greger Update Agent (GUA) successfully initiated!")

    @property
    def localRevisionRecord(self):
        '''
        Get local revision record (.gcm)
        '''
        # Logging
        localLog = logging.getLogger(self.logPath + ".localRevisionRecord")
        localLog.debug("Getting local revision record (.gcm)...")

        # Local parameters
        revisionRecordPath = self._location + "/.gcm"

        localLog.debug("Attemption to get record from file...")
        try:
            with open(revisionRecordPath,"r") as f:
                localRecord = f.read()
                localLog.debug("Local revision record: " + str(localRecord))
        except Exception as e:
            self.log.warning("Failed to open file! - " + str(e))
            self.localRevisionRecord = 0
            localRecord = self.localRevisionRecord

        return localRecord

    @localRevisionRecord.setter
    def localRevisionRecord(self, newRevision):
        '''
        Set local revision record (.gcm)
        '''
        # Logging
        localLog = logging.getLogger(self.logPath + ".localRevisionRecord")
        localLog.debug("Setting local revision record (.gcm)...")

        # Local parameters
        revisionRecordPath = self._location + "/.gcm"

        localLog.debug("Attemption to write \"" + str(newRevision) + "\" to file...")
        with open(revisionRecordPath,"w") as f:
            f.write(str(newRevision))
        self.log.info("Local revision record set: " + str(newRevision))

    def getSoftwareInfo(self, rev='HEAD'):
        '''
        Retrieve information about a revision available on server.
        '''
        # Logging
        localLog = logging.getLogger(self.logPath + ".getSoftwareInfo")
        localLog.debug("Attempting to retrieve software revision info...")

        # Locally relevant parameters
        if 'guaSWSource' in greger.settings:
            guaSWServerURI = greger.settings['guaSWSource']['value']
        else:
            self.log.warning("Setting " + str(guaSWSource) + " not defined!")
            return
        moduleReturn = {
            'revision': "",
            'revision_SHA' : "",
            'revision_author' : "",
            'revision_date' : "",
            'revision_comment' : ""
            }

        # Get server revision info
        localLog.debug("Attempting to retrieve info from server... " + guaSWServerURI)
        pCmd  =       "svn proplist -v -R --revprop -r " + rev
        pCmd += " " + guaSWServerURI
        localLog.debug(pCmd)
        try:
            p = subprocess.Popen(pCmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()

            # Create list of output and remove extra white spaces
            outputList = output.splitlines()[1:]
            outputList = [elem.strip() for elem in outputList]

            # Get revision from output
            revStr = output.splitlines()[0]
            revStr = revStr.split()[-1]
            moduleReturn['revision'] = revStr[:-1]
            localLog.debug("Revision: " + revStr[:-1])

            # Get SHA
            shaStr = outputList[outputList.index('git-commit')+1]
            moduleReturn['revision_SHA'] = shaStr
            localLog.debug("Revision SHA: " + shaStr)

            # Get revision author
            authorStr = outputList[outputList.index('svn:author')+1]
            moduleReturn['revision_author'] = authorStr
            localLog.debug("Revision author: " + authorStr)

            # Get revision date
            dateStr = outputList[outputList.index('svn:date')+1]
            moduleReturn['revision_date'] = dateStr
            localLog.debug("Revision date: " + dateStr)

            # Get revision comment
            commentStr = outputList[outputList.index('svn:log')+1].strip()
            moduleReturn['revision_comment'] = commentStr
            localLog.debug("Revision Comment: " + commentStr)

            if err is not None:
                localLog.debug("Error message: " + str(err))

        except Exception as e:
            self.log.error("Oops! Something went wrong - " + str(e))

        return moduleReturn

    def getSoftware(self,swRev='HEAD'):
        '''
        Get software from server
        '''
        # Logging
        localLog = logging.getLogger(self.logPath + ".getSoftware")
        localLog.debug("Getting software revision " + str(swRev) + " from server...")

        # Locally relevant parameters
        targetRoot = self._location
        targetDir  = "gcm/"
        targetPath = targetRoot + targetDir
        if 'guaSWSource' in greger.settings:
            guaSWServerURI = greger.settings['guaSWSource']['value']
        else:
            self.log.warning("Setting " + str(guaSWSource) + " not defined!")
            return

        # Get software revision
        pCmd  =       "svn export --force -r " + str(swRev)
        pCmd += " " + guaSWServerURI
        pCmd += " " + targetPath
        pCmd += " " + '| grep -e "A " -e "U "'    # Filter output to Added an Updeted files
        pCmd += " " + "| awk '{print $2}'"        # Get files
        localLog.debug("Getting software files from server...")
        try:
            p = subprocess.Popen(pCmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            exportedFiles = output.splitlines()[1:]
            exportedFiles = [targetRoot + file for file in exportedFiles]

            self.log.info("Software files downloaded:")
            for file in exportedFiles:
                self.log.info("File: " + file)

            if err is not None:
                localLog.debug("Error message: " + str(err))
        except Exception as e:
            self.log.error("Oops! Something went wrong - " + str(e))

        # List files in directory
        self.log.debug("Getting all files in local directory...")
        allFiles = []
        # r=root, d=directories, f = files
        for r, d, f in os.walk(targetPath):
            for file in f:
                allFiles.append(os.path.join(r, file))
            for dir in d:
                allFiles.append(os.path.join(r, dir))
        self.log.debug("Files in directory:")
        for file in allFiles:
            self.log.debug("File: " + file)

        self.log.info("Identifying old files to remove...")
        diffFiles = list(set(allFiles) - set(exportedFiles))
        for file in diffFiles:
            self.log.info("Removing: " + file)
            try:
                if os.path.isfile(file):
                    os.unlink(file)
                elif os.path.isdir(file):
                    shutil.rmtree(file)
            except Exception as e:
                self.log.warning("Oops! Something went wrong! - " + str(e))

        # List files in directory
        self.log.debug("Re-getting all files in local directory...")
        allFiles = []
        # r=root, d=directories, f = files
        for r, d, f in os.walk(targetPath):
            for file in f:
                allFiles.append(os.path.join(r, file))
            for dir in d:
                allFiles.append(os.path.join(r, dir))
        self.log.debug("Files in directory:")
        for file in allFiles:
            self.log.debug("File: " + file)

    def run(self):
        '''
        Run Greger Update Agent.
        '''
        # Logging
        localLog = logging.getLogger(self.logPath + ".run")
        self.log.info("Starting Greger Update Agent (GUA)...")

        # Set start flag
        GregerUpdateAgent.is_active = True

        # Start checking for updates
        loopCount = 0
        while not self.stopExecution.is_set():
            loopCount += 1
            localLog.debug("Checking for updates (" + str(loopCount) + ")...")

            # Get local revision record
            localLog.debug("Getting local revision record...")
            localRevision = self.localRevisionRecord

            # Get server revision...
            localLog.debug("Getting latest software info...")
            latestRevisionInfo = self.getSoftwareInfo()

            if int(localRevision) == int(latestRevisionInfo['revision']):
                self.log.info("Local and server revisions match!")
            else:
                self.log.info("New revision found!")

                ### Do update!! ###

            if 'guaCheckUpdateDelay' in greger.settings:
                delayTime = greger.settings['guaCheckUpdateDelay']['value']
            else:
                delayTime = 10
                self.log.warning("Settings not defined! (using default=10)")

            # Wait update delay
            self.log.info("Waiting " + str(delayTime) + "s...")
            self.stopExecution.wait(delayTime)

        self.log.info("Greger Update Agent (GUA) execution stopped!")
        GregerUpdateAgent.is_active = False
