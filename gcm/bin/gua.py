#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Greger Update Agent (GUA) module for the Greger Client Module
"""

__author__ = "Eric Sandbling"
__license__ = 'MIT'
__status__ = 'Development'

# System modules
import os, sys
import logging
import subprocess
from threading import Event
from threading import Thread
from threading import enumerate

# Local Modules
from common import getLocalConfig
from common import restart_program
from gdb import GregerDatabase
# from gcm import GregerClientModule

class GregerUpdateAgent(Thread):
    """
    Main class which holds the main sequence of the application.
    """

    def __init__(self, ready=None):
        '''
        Initialize the main class
        '''
        Thread.__init__(self)
        self.ready = ready

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
        revisionRecordPath = os.path.join(self._location, ".gcm")

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
        localLog.debug("Setting local revision record (.gcm) to " + str(newRevision) + "...")

        # Local parameters
        revisionRecordPath = os.path.join(self._location, ".gcm")

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
        if 'guaSWSource' in GregerDatabase.settings:
            guaSWServerURI = GregerDatabase.settings['guaSWSource']['value']
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

    def updateSoftware(self, swRev='HEAD'):
        '''
        Get and updating software from server
        '''
        # Logging
        localLog = logging.getLogger(self.logPath + ".updateSoftware")
        localLog.debug("Getting software revision " + str(swRev) + " from server and updating local client...")

        # Locally relevant parameters
        localLog.debug("Retrieving relevant parameters from server...")
        targetRoot = self._location
        targetDir  = "gcm"
        targetPath = os.path.join(targetRoot + targetDir)
        if 'guaSWSource' in GregerDatabase.settings:
            guaSWServerURI = GregerDatabase.settings['guaSWSource']['value']
            localLog.debug("Parameter: (guaSWSource) " + guaSWServerURI)
        else:
            self.log.warning("Setting " + str(guaSWSource) + " not defined!")
            return

        # Get software files from server
        localLog.debug("Getting software files from server...")

        # Compile download command
        pCmd  =       "svn export --force -r " + str(swRev)
        pCmd += " " + guaSWServerURI
        pCmd += " " + targetPath
        localLog.debug(pCmd)

        # Execute command
        try:
            p = subprocess.Popen(pCmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()

            if err is not None:
                localLog.debug("Error message: " + str(err))
            else:
                localLog.debug("Download successful!")
                # Print output
                for line in output.splitlines():
                    localLog.debug("Line: " + line)

        except Exception as e:
            self.log.error("Oops! Something went wrong - " + str(e))

        # Read revision text
        localLog.debug("Reading downloaded revision from \"" + output.splitlines()[-1] + "\"...")
        revText = output.splitlines()[-1].split()[-1][:-1]
        localLog.debug("Downloaded Revision: " + revText)

        # Update local revision record
        self.localRevisionRecord = revText

        # Get downloaded files text
        localLog.debug("Listing downloaded files...")
        downloadedFiles = []
        for row in output.splitlines()[:-1]:
            file = os.path.join(targetRoot, [t.strip() for t in row.split()][1])
            downloadedFiles.append(file)
            localLog.debug("File: " + file)

        # List files in directory
        self.log.debug("Getting all files in local directory (after update)...")
        allFiles = []
        # r=root, d=directories, f = files
        for r, d, f in os.walk(targetPath):
            for file in f:
                allFiles.append(os.path.join(r, file))
                self.log.debug("File: " + os.path.join(r, file))
            for dir in d:
                allFiles.append(os.path.join(r, dir))
                self.log.debug("Dir:  " + os.path.join(r, file))

        self.log.info("Identifying old files to remove (<new_files> - <all_files>)...")
        diffFiles = list(set(allFiles) - set(downloadedFiles))
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
                self.log.debug("File: " + os.path.join(r, file))
            for dir in d:
                allFiles.append(os.path.join(r, dir))
                self.log.debug("Dir:  " + os.path.join(r, file))

    def run(self):
        '''
        Run Greger Update Agent.
        '''
        # Logging
        localLog = logging.getLogger(self.logPath + ".run")
        self.log.info("Starting Greger Update Agent (GUA)...")

        # Wait for Greger Client Module to start...
        localLog.debug("Wait for Greger Client Module to start...")
        self.ready.wait()

        # List all active threads!
        gcmThread = None
        for thr in enumerate():
            localLog.debug(thr.name + " " + thr.__class__.__name__ +" active!")
            if thr.__class__.__name__ == "GregerClientModule":
                gcmThread = thr
                localLog.debug("Greger Client Module thread found! " + gcmThread.name)

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

                # Tell GCM to stop all treads (except GUA)...
                self.log.warning("Attempting to stop all exection!")
                gcmThread.stopAll(GUA=True)

                # Do update!!
                self.updateSoftware()

                # Restart Application
                localLog.debug("Attemption to restart application...")
                restart_program()

            if 'guaCheckUpdateDelay' in GregerDatabase.settings:
                delayTime = GregerDatabase.settings['guaCheckUpdateDelay']['value']
            else:
                delayTime = 10
                self.log.warning("Settings not defined! (using default=10)")

            # Wait update delay
            self.log.info("Waiting " + str(delayTime) + "s...")
            self.stopExecution.wait(delayTime)

        self.log.info("Greger Update Agent (GUA) execution stopped!")
