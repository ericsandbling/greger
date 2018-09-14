#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
owlib - Library for 1-wire devices.

Ligrary of function adapted for the Greger Client Module (GCM).
"""

__author__ = "Eric Sandbling"
__status__ = 'Development'

# Modules goes here
import ow
import time, sys
import logging

# logger
module_logger = logging.getLogger("gcm.owlib")
# module_logger.setLevel(logging.DEBUG)

# Functions for each sensor type goes here.
def _ds18b20(sensor,ndigits=1):
    '''Return available sensor values.'''
    data = {
        'temperature': round(float(sensor.temperature),ndigits)
    }
    return data

def _ds2438(sensor,ndigits=1):
    '''Return available sensor values.'''
    data = {
        'temperature': round(float(sensor.temperature),ndigits),
        'humidity': round(float(sensor.humidity),ndigits)
    }
    return data

# Sensor library listing all defined sensors
_sensorLib = {
    'ds18b20': _ds18b20,
    'ds2438': _ds2438
}

class owDevices(object):
    '''
    Class representing all devices on the 1-1wire.
    '''
    def __init__(self, settings):
        '''
        Initialize class
        '''
        # Logging
        self.log = logging.getLogger("gcm.owlib.owDevices")
        self.log.debug("Creating Class Log for 1-Wire Devices (owDevices).")

        # Input data
        self.settings = settings

        # Device readings
        self.deviceReading = {}

        # Time series measurements
        # ========================
        self._timeBucket            = {}            # Dict
        self._timeBucketTime        = 0             # Epoch
        self._timeBucketTypeDefault = 's'           # Char
        self._timeBucketEmptyTime   = time.time()   # Epoch
        self._timeBucketTypeLibrary = {
            'h' : 'hour',
            'm' : 'minute',
            's' : 'second'
        }
        # Output variable
        self.timeseries = {}

        # Start message
        self.log.info("1-Wire Devices initiated!")

    def _initOW(self):
        ow.init('localhost:4304')
        ow.Sensor('/').useCache(False)
        self.deviceList = ow.Sensor('/').sensorList()

    def _flushOW(self):
        ow.finish()

    def _timeToEmptyBucket(self):
        '''
        Calculate if it is time to empty the Timeseries Bucket.
        '''
        localLog = logging.getLogger("gcm.owlib.owDevices._timeToEmptyBucket")

        # Initialize local variable
        answer = False
        dDay    = time.localtime().tm_wday - time.localtime(self._timeBucketTime).tm_wday
        dHour   = time.localtime().tm_hour - time.localtime(self._timeBucketTime).tm_hour
        dMin    = time.localtime().tm_min - time.localtime(self._timeBucketTime).tm_min
        dSec    = time.localtime().tm_sec - time.localtime(self._timeBucketTime).tm_sec
        # dt   = 0
        methodName = "TIMESERIES"

        # Evaluate if enough time has passed to empty the bucket
        localLog.debug("Evaluate if enough time has passed to empty the bucket")
        if str(self.settings['timeseriesBucketType']['value']).lower() == 'h':
            answer = abs(dDay) > 0 or dHour > int(self.settings['timeseriesBucketSize']['value'])

        elif str(self.settings['timeseriesBucketType']['value']).lower() == 'm':
            answer = abs(dDay) > 0 or abs(dHour) > 0 or dMin > int(self.settings['timeseriesBucketSize']['value'])

        elif str(self.settings['timeseriesBucketType']['value']).lower() == 's':
            answer = abs(dDay) > 0 or abs(dHour) > 0 or abs(dMin) > 0 or dSec > int(self.settings['timeseriesBucketSize']['value'])

        else:
            self._disableTimeseries()

        # Reset timeBucket empty time if first reading ever
        if self._timeBucketEmptyTime == 0:
            self._timeBucketEmptyTime = time.time()

        # Print result to consol
        self.log.info(
            "Time to empty bucket: " + str(answer).upper() +
            " (empty@" + time.strftime("%H:%M:%S",time.localtime(self._timeBucketEmptyTime)) +
            " (+" + str(int(self.settings['timeseriesBucketSize']['value'])) + str(self.settings['timeseriesBucketType']['value']) + ")" +
            " dDay=" + str(dDay) +
            " dHour=" + str(dHour) +
            " dMin=" + str(dMin) +
            " dSec=" + str(dSec) + ")"
            )

        return answer

    def _disableTimeseries(self):
        '''
        Disable time-series collection.
        '''
        self.log.info("Timeseries Bucket type could not be determined! - " +
            str(self.settings['timeseriesBucketType']['value']))

        self.log.info("Turing off timeseries!!")
        self.settings['timeseriesEnable']['value'] = False

    def _emptyBucket(self):
        '''
        Empty timeseries timeBucket.
        '''
        localLog = logging.getLogger("gcm.owlib.owDevices._emptyBucket")

        # Empty each device in bucket to timeseries
        for deviceId in self._timeBucket:
            # Get console message
            infoMsg = "Emptying:"
            infoMsg += " " + str(deviceId) + " - "

            # Ensure device is in timeseries
            if deviceId not in self.timeseries:
                self.timeseries.update({deviceId:{}})

            # Get device values
            firstSensor = True
            for sensor in self._timeBucket[deviceId]:
                # Calculate sensor valuse
                sensorValues = self._timeBucket[deviceId][sensor].values()
                sensorMax = max(sensorValues)
                sensorMin = min(sensorValues)
                sensorMean = float(sum(sensorValues)) / max(len(sensorValues), 1)
                sensorMean = round(sensorMean, int(self.settings['sensorResolution']['value']))

                # Update consol message
                if not firstSensor:
                    infoMsg += " "
                    firstSensor = False
                infoMsg += str(sensor[0]) + ": "
                infoMsg += time.strftime("%H:%M:%S",time.localtime(self._timeBucketTime))
                infoMsg += " [" + str(sensorMin) + " "
                infoMsg += str(sensorMean) + " "
                infoMsg += str(sensorMax) + "]"

                # Average sensor times
                newValues = { str(int(self._timeBucketTime)) : {
                    'max': sensorMax,
                    'min' : sensorMin,
                    'mean' : sensorMean
                    }}

                # Ensure sensor is in timeseries
                if sensor not in self.timeseries[deviceId]:
                    self.timeseries[deviceId].update({sensor:{}})

                # Update timeseries
                self.timeseries[deviceId][sensor].update(newValues)

            # Print complete consol message
            self.log.info(infoMsg)

        # Reset timeBucket and bucket empty time
        self._timeBucket = {}
        self._timeBucketEmptyTime = time.time()

    def _setBucketTime(self):
        '''
        Set timeseries bucket time.
        '''
        localLog = logging.getLogger("gcm.owlib.owDevices._setBucketTime")

        # Get current time as a list
        timeStruct = [
            time.localtime().tm_year,      # 0 : (for example, 1993)
            time.localtime().tm_mon,       # 1 : range [1, 12]
            time.localtime().tm_mday,      # 2 : range [1, 31]
            time.localtime().tm_hour,      # 3 : range [0, 23]
            time.localtime().tm_min,       # 4 : range [0, 59]
            time.localtime().tm_sec,       # 5 : range [0, 61]
            time.localtime().tm_wday,      # 6 : range [0, 6], Monday is 0
            time.localtime().tm_yday,      # 7 : range [1, 366]
            time.localtime().tm_isdst      # 8 : 0, 1 or -1; -1 == unknown
            ]

        # Reset timeStruct to match timeBucket
        bucketSizeOutOfBounds = False
        if str(self.settings['timeseriesBucketType']['value']).lower() == 'h':
            # Is bucket size within bounds
            if int(self.settings['timeseriesBucketSize']['value']) > 23:
                self.settings['timeseriesBucketSize']['value'] = 23
                bucketSizeOutOfBounds = True

            # Set hour to start of timeBucket and min/sec to zero
            timeStruct[3] -= timeStruct[3] % timeBucketSize
            timeStruct[4] = 0
            timeStruct[5] = 0

        elif str(self.settings['timeseriesBucketType']['value']).lower() == 'm':
            # Is bucket size within bounds
            if int(self.settings['timeseriesBucketSize']['value']) > 59:
                self.settings['timeseriesBucketSize']['value'] = 59
                bucketSizeOutOfBounds = True

            # Set minutes to start of timeBucket and sec to zero
            timeStruct[4] -= timeStruct[4] % int(self.settings['timeseriesBucketSize']['value'])
            timeStruct[5] = 0

        elif str(self.settings['timeseriesBucketType']['value']).lower() == 's':
            # Is bucket size within bounds
            if int(self.settings['timeseriesBucketSize']['value']) > 61:
                self.settings['timeseriesBucketSize']['value'] = 61
                bucketSizeOutOfBounds = True

            # Set sec to start of timeBucket
            timeStruct[5] -= timeStruct[5] % int(self.settings['timeseriesBucketSize']['value'])

        else:
            self._disableTimeseries()

        # Get consol message
        if bucketSizeOutOfBounds:
            selg.log.warning(
                "Bucket size out of bounds! - reset to: " +
                int(self.settings['timeseriesBucketSize']['value']) +
                self._timeBucketTypeLibrary[self.settings['timeseriesBucketType']['value']])
        else:
            # Update time bucket time
            self._timeBucketTime = time.mktime(tuple(timeStruct))
            self.log.info("Bucket time set to: " + time.strftime('%H:%M:%S',time.localtime(self._timeBucketTime)))

    def readAll(self):
        '''
        Scan 1-Wire devices and update cuurent reading
        '''
        localLog = logging.getLogger("gcm.owlib.owDevices.readAll")

        # Init local variables
        warningMsg = ''
        infoMsg = ''
        methodName = "OW-SCAN"

        # Initialize timeBucket
        localLog.debug("Reviewing Time Bucket..")
        if bool(self.settings['timeseriesEnable']['value']):
            # Set timeBucket time if timeBucket is empty
            if not self._timeBucket:
                localLog.debug("Time Bucket is empty, setting new time.")
                self._setBucketTime()

            # Empty timeBucket
            if self._timeBucket and self._timeToEmptyBucket():
                localLog.debug("Time to empty bucket!")
                self._emptyBucket()
                self._setBucketTime()

        # Update 1-Wire server
        localLog.debug("Updating 1-Wire server (initOW).")
        self._initOW()

        # Init local copy of old device reading
        oldDeviceReading = self.deviceReading.copy()

        # Inactivate all devices in old reading
        for deviceId in oldDeviceReading:
            oldDeviceReading[deviceId].update({'isActive':False})

        # Init local new reading
        newDeviceReading = oldDeviceReading.copy()

        # Read all devices
        for owDevice in self.deviceList:
            try:
                # Disable cache
                owDevice.useCache(False)

                # Get device and sensor data from OW
                newSensorData = self.getSensor(owDevice, ndigits=int(self.settings['sensorResolution']['value']))

                # Get time
                t = time.time()
                sft = time.strftime('%Y-%m-%d %H:%M:%S')

                # Update consol message
                infoMsg = "Device (" + str(owDevice.type) + "): "
                infoMsg += str(owDevice.id)

                # New device?
                if owDevice.id not in oldDeviceReading:
                    # Add standard (OW) properties
                    newDeviceReading[owDevice.id] = {
                        'type': owDevice.type,
                        'family': owDevice.family,
                        'lastModified' : t,
                        'isActive': True
                        }

                    # Add formated time (optional)
                    if self.settings['strftime']['value']:
                        newDeviceReading[owDevice.id].update({
                            'strftime': sft})

                    # Add sensor readings to device reading
                    newDeviceReading[owDevice.id].update(newSensorData)

                    # Update consol message
                    infoMsg += " - NEW ("

                    # Add device to timeBucket
                    if self.settings['timeseriesEnable']['value']:
                        self._timeBucket.update({owDevice.id: { } })

                    # Check all device sensors
                    firstSensor = True
                    for sensor in newSensorData:
                        if self.settings['timeseriesEnable']['value']:
                            # Add to timeBucket (timeseries)
                            self._timeBucket[owDevice.id].update({sensor : {
                                    str(t): newSensorData[sensor]
                                    }})

                        # Update consol message
                        if not firstSensor:
                            infoMsg += " "
                        firstSensor = False
                        infoMsg += str(sensor) + " (" + str(sensor[0]) + "):"
                        infoMsg += str(newSensorData[sensor])

                    # Clear variables
                    newSensorData.clear()

                # Device already detected
                else:
                    # Print to console
                    infoMsg += " - ACTIVE ("

                    # Set device to active
                    newDeviceReading[owDevice.id]['isActive'] = True

                    # Get old device reading and reset variables
                    oldSensorData = oldDeviceReading[owDevice.id].copy()
                    modified = False
                    changeMsg = ''

                    # Check all device sensors for new values
                    for sensor in newSensorData:
                        # New value available?
                        if newSensorData[sensor] != oldSensorData[sensor]:
                            if self.settings['timeseriesEnable']['value']:
                                # Update timeBucket (timeseries)
                                if owDevice.id not in self._timeBucket:
                                    self._timeBucket.update({owDevice.id:{}})
                                if sensor not in self._timeBucket[owDevice.id]:
                                    self._timeBucket[owDevice.id].update({sensor:{}})

                                self._timeBucket[owDevice.id][sensor].update({
                                        str(t): newSensorData[sensor]
                                        })

                            # Update sensor reading time
                            newDeviceReading[owDevice.id].update({
                                'lastModified': t})
                            if self.settings['strftime']['value']:
                                newDeviceReading[owDevice.id].update({
                                    'strftime': sft})

                            # Set variable values
                            modified = True
                            changeMsg += ' ' + sensor[0] + ': '
                            changeMsg += str(oldSensorData[sensor]) + "->" + str(newSensorData[sensor])

                    # Print to consol
                    if modified:
                        infoMsg += "Changed " + changeMsg
                    else:
                        infoMsg += "Unchanged"

                    # Always update sensor values
                    newDeviceReading[owDevice.id].update(newSensorData)
                    newSensorData.clear()
                    oldSensorData.clear()

            except Exception as e:
                self.log.warning("Oops! Failed to read device! - " + str(e))
                continue

            # Print to console
            self.log.info(infoMsg + ")")

        # List all inactive devices
        for deviceId in newDeviceReading:
            if newDeviceReading[deviceId]['isActive'] == False:
                self.log.info(
                    "Device (" + oldDeviceReading[deviceId]['type'] + "): " +
                    str(deviceId) + " - InActive!")

        # Update self
        self.deviceReading = newDeviceReading.copy()

        # Flush OW server
        self._flushOW()

        # Return new device readings
        return self.deviceReading

    def getSensor(self, sensor, ndigits=1):
        '''
        Get 1-wire device sensor output.
        '''
        func = _sensorLib.get(sensor.type.lower(), "No sensor values found!")
        return func(sensor, ndigits)
