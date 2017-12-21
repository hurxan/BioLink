# -*- coding: utf-8 -*-
"""
BioLink - Tool for synchronized psycho-physiological and behavioural data acquisition
Copyright (C) 2017  Julian Schneider, Department of Internal Medicine, 
                    University Hospital Zurich, Zurich, Switzerland.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

-----------------------------------------------------------------
ExpController contains the core functionality for opening data acquisition
devices (Plux), record data from them and to reseive data from other extensions
or the serial interface.
"""

import numpy as np

import threading
from multiprocessing import Pipe
import time
import csv
#import winsound
import serial
import serial.tools.list_ports
import os
import json
from random import randint

import PluxInterface
import RealtimePlot
import MsgLogger
from ExtensionInterface import ExtensionInterfaceFrontend


#version str
versionStr = "V1.1"

#plux configuration
pluxMac = "00:07:80:79:6F:E0"   # MAC address of device
fs = 1000

maxDurationFrames = 3600 * fs   #init value: 1hr

#channel definition
MAX_CHANNEL_CNT = 8
MAX_SERIAL_EVENT_STR_LEN = 16      #should be > 7 for serial comments (#noconn)
MAX_EXTENSION_EVENT_STR_LEN = 32

channelHeader = ["ecg","eda","bvp"]
channelMask = 0x07  #only channels 1,2,3

bitsResolution = 16

#serial port
if os.name == 'nt':
    serialPort = "COM1"     #"\\\\.\\COM1"  #on Windows
else:
    serialPort = '/dev/ttyUSB0'    #on mac OS X / Linux
serialBaud = 115200

#plot
PLOT_RANGE_SEC = 10   #seconds
plotRefreshRate = 1 #per seconds


#global variables
pluxDevice = None
logRawFile = None
logRawCsvWriter = None
ser = None
isSerialOpen = threading.Event()
stopSerialReconnectThread = threading.Event()
# plotT = None
# plotEcg = None
# PlotEda = None
# plotEvent = None
nolog = False
endLogging = threading.Event()
notifyExpEndFnc = None    #function to notify gui that logging ended for whatever reason, the function should close serial and plux
deviceThread = None
logThread = None
serialReconnectThread = None
tmpEventStr = ""
startTime = None
logFileNameBase = None
extInterface = None

#to be set from other module
versionStr = ""     
logDir = "../log/"
subjectId = ""
experimentId = ""
useSerial = True
useLifePlot = True
reopenLifePlot = True
extensionName = "None"


#logged data
bioData = None     #np.array preallocated for max duration
serialEventData = None    #list of tuples with frame nr and event string (serial events)
extensionEventData = None   #list of tuples with frame nr and event string
frameCnt = 0


def pluxOpenDevice():
    """Raises exception on failure
    openes plux device unless device with same mac address is already open
    """
    global pluxDevice,pluxMac
    
    pluxCloseDevice()
    
    #weird effect: plot process needs to be ended to open plux again!!!
    closePlot()     #close old plot if any
    time.sleep(0.1) #dirty: quick sleep to wait for plot process to be cleaned up
    
    pluxDevice = PluxInterface.openDevice(pluxMac)    # MAC address of device
    props = pluxDevice.getProperties()
    MsgLogger.append('Plux Device: ' + str(props))
    MsgLogger.append("Plux Device Battery: " + pluxDevice.getBatteryStr())


def pluxStartDeviceLoop(pipeEnd):
    global pluxDevice
#     print pipeEnd
    pluxDevice.stopRequest.clear()
    pluxDevice.pipeConn = pipeEnd
    pluxDevice.start(fs, channelMask, bitsResolution)   # 1000 Hz, ports 1-8, 16 bits                
    pluxDevice.loop()   #blocks 
    print "Plux device loop terminated"
    pluxDevice.stop()
    pluxCloseDevice()
    
def pluxCloseDevice():
    global pluxDevice
    if pluxDevice:
        MsgLogger.append("Plux Device Battery: " + pluxDevice.getBatteryStr())
        pluxDevice.close()
        del pluxDevice
    pluxDevice = None
    
def configChannels(channelNames):
    """tuple of channel names for used channels, "" for unused channels
    """
    global channelHeader
    global channelMask
    
    channelHeader = []
    channelMask = 0
    index = 0
    
    for name in channelNames:
        if name != "":
            channelHeader.append(name)
            channelMask |= 0x01 << index
        
        index += 1

def serialOpen(exceptionOnError):
    """returns True on success
    """
    global ser,isSerialOpen
    
    try:
        ser = serial.Serial(serialPort,serialBaud,timeout=0)
        if ser:
            isSerialOpen.set()
            return True
    except:
        ser = None
        isSerialOpen.clear()
        
        if exceptionOnError:
            raise
        
        return False
        
def serialClose():
    global ser,isSerialOpen,tmpEventStr
    if ser:
        ser.close()
        ser = None
        tmpEventStr = ""
        isSerialOpen.clear()
        
def serialEnumPorts():
    l = list( serial.tools.list_ports.comports() )
    l.sort()
    return l

def _serialReconnectLoop():
    global stopSerialReconnectThread
    while not stopSerialReconnectThread.is_set():
        if not isSerialOpen.is_set():
            serialOpen(False)
        time.sleep(1)       #check every second

def serialStartReconnectThread():
    global stopSerialReconnectThread,serialReconnectThread
    stopSerialReconnectThread.clear()
    serialReconnectThread = threading.Thread(target=_serialReconnectLoop)
    serialReconnectThread.start()
    

def _serialAssembleEvent(buf,startSeq=None,endSeq="\n"):
    """assemble event string parts until \n received
    to be called iteratively with received buffers
    returns None unless a event is found in between startSeq and endSeq
    event string is returned not containing startSeq or endSeq
    """
    global tmpEventStr
    startIndex = 0
    startStrLen = 0
    retval = None
    
    tmpEventStr = tmpEventStr + buf
    print "tmpEventStr before: '" + repr(tmpEventStr) + "'" 
    
    if startSeq:
        startStrLen = len(startSeq)
        startIndex = tmpEventStr.find(startSeq)
        
    if startIndex >= 0:     #not -1, start found
        endIndex = tmpEventStr.find(endSeq,startIndex)
        print "startIndex", startIndex
        
        if endIndex >= 0:   #not -1, end found
            print "endIndex", endIndex
            retval = tmpEventStr[startIndex+startStrLen:endIndex]     #event string without start or end sequence
            if len(retval) > MAX_SERIAL_EVENT_STR_LEN:
                retval = retval[0:MAX_SERIAL_EVENT_STR_LEN-1]      #truncate string if too long
            tmpEventStr = tmpEventStr[endIndex+len(endSeq) :]        #remove current event but safe rest (if there was more in buf)
    print "tmpEventStr after: '" + repr(tmpEventStr) + "'" 
    
    return retval

def _serialHandleSpecialEvents(event):
    if event == "#END":
        stopExperiment()

def serialCheckEvent(curFrameNr):
    """detects serial events of the structure "test message\n". messages should always be terminated by '\n'
        supported commands:
        "#END\n"
        
        returns True on detected event
    """
    #assemble event strings, save start position, end event: call stopExperiment
    global ser,isSerialOpen,serialEventData
    
    retval = False
    
    if isSerialOpen.is_set():     #serial interface initialized
        if not serialCheckEvent.oldIsSerialOpen:
            MsgLogger.append("Serial port reconnected.")
            serialEventData.append((curFrameNr, "#reconn"))
            serialCheckEvent.oldIsSerialOpen = True
        try:
            buf = ser.read(50)      #read max 50 bytes
            if len(buf) > 0:    #anything new arrived
                while True:     #get all events available
                    event = _serialAssembleEvent(buf)
                    if event:   #not None
                        serialEventData.append((curFrameNr, event))
                        MsgLogger.append("Serial event at frame nr " + str(curFrameNr) + ": '" + event + "'")
                        _serialHandleSpecialEvents(event)
                        retval = True
                        buf = ""        #empty buf so it is not appended again in next loop cycle
                    else:
                        break   #break when no more events available
        except:
            MsgLogger.append("No connection to serial port.")
            #append comment to log, also when reconnected
            serialEventData.append((curFrameNr, "#noconn"))
            serialClose()
            serialCheckEvent.oldIsSerialOpen = False    #so reconnect can be detected
            
    return retval

serialCheckEvent.oldIsSerialOpen = True

def serialReceiveSubjectId():
    """ to be called in a loop until return value is not ""
        subject id should be transmitted in format:
        "#ID:test id\n" (start with "#ID:", end with "\n")
        
        can raise exception if serial is unplugged during read operation
    """
    global ser,isSerialOpen
    
    if isSerialOpen.is_set():
        buf = ser.read(20)  #read max 20 bytes
        
        if len(buf) > 0:
            sId = _serialAssembleEvent(buf,"#ID:","\n")
            if sId:
                return sId
         
    return ""
    
serialReceiveSubjectId.iterCnt = 0

def _serialTest():
    while True:
        event = serialCheckEvent()
        if event != '-':
            print "Event: " + event
        
        time.sleep(0.1)
        
def extensionStart():
    global extInterface
    
    #init ExtensionInterface and open extension
    extInterface = ExtensionInterfaceFrontend(subjectId, experimentId, logDir, startTime, logFileNameBase, channelHeader, fs, nolog)
    if extInterface.selectExtensionByName(extensionName):
        extInterface.extensionStart()
    else:
        MsgLogger.append("Error opening extension '" + extensionName  + "'.")
        
def extensionEnd():
    global extInterface
    
    if extInterface:
        extInterface.extensionEnd()
        extInterface = None
        
def extensionCheckEvent(curFrameNr):
    """
    logs events from the currently selected extension
    and updates current frame nr in ExtensionInterface
    Multiple events during one call (frame) possible!
    """
    global extInterface, extensionEventData
    
    if extInterface:
        eventList = extInterface.checkEvents(curFrameNr)
        if len(eventList) > 0:
            for frameNr,e in eventList:
                if frameNr < 0:
                    stopExperiment()    #frameNr == -1 is used to indicate an experiment end request
                else:
                    if len(e) > MAX_EXTENSION_EVENT_STR_LEN:
                        e = e[0:MAX_EXTENSION_EVENT_STR_LEN-1]      #truncate string if too long
                        
                    extensionEventData.append((frameNr, e))     #the list is not necessarily sorted for frameNr. needs to be sorted after experiment ended!
                    
                    MsgLogger.append("Extension event at frame nr " + str(frameNr) + ": '" + e + "'")
#                 print "Real frame: " + str(curFrameNr)
 
def setMaxDuration(minutes):
    """to be called after setting fs
    """
    global maxDurationFrames
    maxDurationFrames = minutes * 60 * fs
        
def _expEnded():    #save log, etc.
    global stopSerialReconnectThread,tmpEventStr,notifyExpEndFnc,deviceThread
    
    stopSerialReconnectThread.set()
    tmpEventStr = ""
    
    _safeLog()
    
    deviceThread.join(timeout=5)
    
    if notifyExpEndFnc:     #not None
        notifyExpEndFnc()
    
def _safeLog(appendToFileName=""):
    global serialEventData,bioData,extensionEventData,channelHeader
    
    if not nolog:
        npzPath = logFileNameBase + appendToFileName + ".npz"
        jsonPath = logFileNameBase + appendToFileName + ".json"
        
        logChannelHeader = np.array(channelHeader)
        bioData = bioData[:frameCnt]      #shorten data array to actual size (delete pending zeros)
        serialEventDataArr = np.array( serialEventData, np.dtype( [('frame_nr',np.uint32),('event_str','S' + str(MAX_SERIAL_EVENT_STR_LEN))] ) )      #generate event array
        
        extensionEventData.sort(key = lambda l:l[0])    #sort according to first tuple entry of every list entry ( frameNr )
        extensionEventDataArr = np.array( extensionEventData, np.dtype( [('frame_nr',np.uint32),('event_str','S' + str(MAX_EXTENSION_EVENT_STR_LEN))] ) )      #generate event array
        
        np.savez_compressed(npzPath, channelHeader = logChannelHeader, bioData = bioData, serialEventData = serialEventDataArr, extensionEventData = extensionEventDataArr)
        MsgLogger.append("Data saved to '" + npzPath + "'")
        
        #construct header
        dateStr = time.strftime("%d/%m/%Y %H:%M",startTime)
        duration_sec = float(frameCnt)/fs
        hdrDict = {'version':versionStr,'dateStr':dateStr,'experimentId':experimentId,'subjectId':subjectId,'fs':fs,
                   'frameCnt':frameCnt,'duration_sec':duration_sec, 'channels':channelHeader, 'pluxMac':pluxMac,
                   'extension':extensionName}
        with open(jsonPath,'w') as f:
            json.dump(hdrDict, f, indent=2, )
    
    
def _expControlLoop(pipeConn):
    global bioData,serialEventData,frameCnt,endLogging
    
    try:
        while not endLogging.is_set():
            if pipeConn.poll(5):     #block 5 sec max
                (curFrameNr, dataTup) = pipeConn.recv()      #curFrameNr is 0 based
                
                if curFrameNr >= maxDurationFrames:
                    break       #end experiment after max duration
    
                serEv = serialCheckEvent(curFrameNr)
                extensionCheckEvent(curFrameNr)
                
                bioData[curFrameNr] = dataTup
                frameCnt = curFrameNr + 1
                
                if extInterface:    #not None, sometimes gets initialized after first run
                    extInterface.putBioData(curFrameNr, dataTup)
                
    #             logRaw(frameCnt, data, serEv)
                if useLifePlot:
                    RealtimePlot.plotDataFrame(float(curFrameNr)/fs, dataTup)
                
#                 #report every sec or on event on console
#                 if curFrameNr % fs == 0:
#                     print "frame #", curFrameNr, "\tecg:", dataTup[0], "\teda:", dataTup[1], "\tbvp:", dataTup[2]
#                 if serEv:
#                     print "frame #", curFrameNr, "\tecg:", dataTup[0], "\teda:", dataTup[1], "\tbvp:", dataTup[2], "\tserial-event:", serialEventData[-1][1]     #string of last serialEventData element
#              
            else:
                MsgLogger.append("Error: no data from Plux device thread. Connection to Plux device lost.")
                break
    except Exception as e:      #all exceptions caught here. this ensures that _expEnded is called in any case and the log is saved
        MsgLogger.append("Error in _expControlLoop. Ending experiment.")
        print e

    pluxDevice.endAquisition() 
    _expEnded()
        
def startExperiment(subjectIdStr):
    global bioData,serialEventData,frameQueue,endLogging,frameCnt,deviceThread,logThread,tmpEventStr,startTime,subjectId,logFileNameBase,extensionEventData,nolog
    
    #check plux opened?
    if pluxDevice == None:
        raise Exception("Error in startExperiment: Plux not opened.")
    
    subjectId = subjectIdStr
    if subjectId == 'nolog':
        nolog = True
    else:
        nolog = False
    
    #init log arrays
    channelCnt = len(channelHeader)
    bioData = np.zeros((maxDurationFrames,channelCnt),np.uint16)
    serialEventData = []
    extensionEventData = []
    frameCnt = 0
    tmpEventStr = ""

    #prepare interface
    loggerConn, pluxConn = Pipe()
    endLogging.clear()
    serialCheckEvent.oldIsSerialOpen = True     #assume serial is connected, produces message and #noconn event with first frame otherwise
    
    #init plot
    cfg = RealtimePlot.PlotConfig()
    cfg.channelCnt = channelCnt
    cfg.channelLabels = channelHeader  
    cfg.xLabel = "Seconds"
    cfg.xRange = PLOT_RANGE_SEC    #display last 10 seconds
    cfg.yMin = 0
    cfg.yMax = 2**bitsResolution
    cfg.reopenPlotOnClose = reopenLifePlot
    
    deviceThread = threading.Thread(target=pluxStartDeviceLoop,args=(pluxConn,))
    logThread = threading.Thread(target=_expControlLoop,args=(loggerConn,))
    
    #init logging
    startTime = time.localtime()
    logFileNameBase = logDir + experimentId + "_" + subjectId + "_" + time.strftime("%Y%m%d_%H%M",startTime)
    
    
    #start
    deviceThread.start()
    if useLifePlot:
        RealtimePlot.startPlotProcess(cfg)
    logThread.start()
    if useSerial:
        serialStartReconnectThread()
        
    
def stopExperiment():
    """Clean way to stop experiment.
    """
    endLogging.set()
    
def forceStopExperiment():
    """In case of any failure in the experiment process, this function forces everything to stop and saves the log.
    Finally, the notify function is called.
    This function should not be needed normally! It should not be called less than 11 seconds after stopExperiment was called.
    """
    global stopSerialReconnectThread,tmpEventStr,notifyExpEndFnc,deviceThread
    
    endLogging.set()
    pluxDevice.endAquisition()
    stopSerialReconnectThread.set()
    
    tmpEventStr = ""
    
    _safeLog("_forcedsave")
    
    pluxCloseDevice()
    
    if notifyExpEndFnc:     #not None
        notifyExpEndFnc()
    
def closePlot():
    RealtimePlot.terminatePlotProcess()


if __name__ == '__main__':
   
    subjectId = "test"
    startTime = time.localtime()
     
    channelCnt = len(channelHeader)
    bioData = np.zeros((maxDurationFrames,channelCnt),np.uint16)
    serialEventData = []
    frameCnt = 0
     
    #pseudosamples
    for i in range(10):
        data = ( randint(0,65000),randint(0,65000),randint(0,65000) ) 
        bioData[i] = data
        frameCnt += 1
         
    serialEventData.append((2,"event 1"))
    serialEventData.append((5,"event 2"))
     
    _safeLog()
    
    
    
#     d = _pluxDataDtype()
#     print d
#     a = np.zeros(5,d)
#     a[0] = (1,2,3)
#     b = np.zeros((5,3),np.uint16)
#     b[0] = (1,2,3)
#     print a
#     print a[0]
#     print a[0][0]
#     print a.dtype.names
#     print b
    
#     startStr = None
#     endStr = "\n"
#     print _serialAssembleEvent("haha", startStr, endStr)
#     print _serialAssembleEvent("#T", startStr, endStr)
#     print _serialAssembleEvent("h", startStr, endStr)
#     print _serialAssembleEvent("a", startStr, endStr)
#     print _serialAssembleEvent("l", startStr, endStr)
#     print _serialAssembleEvent("l", startStr, endStr)
#     print _serialAssembleEvent("o\n#Tw", startStr, endStr)
#      
#     print _serialAssembleEvent("", startStr, endStr)
#     print _serialAssembleEvent("", startStr, endStr)
#     print _serialAssembleEvent("elt\n", startStr, endStr)
    
#     try:
#         pluxOpenDevice()
#     except:
#         pass
#     print pluxDevice
    
#    parent_conn, child_conn = Pipe()
    
#     print serialEnumPorts()
#     
#     channelCnt = len(channelHeader)
#     bioData = np.zeros((maxDurationFrames,channelCnt),np.uint16)
#     serialEventData = []
#     
#     bioData[1]=(1,2,3)
#     
#     print bioData
#     print bioData.shape

#     loggerConn, pluxConn = Pipe()
#     logThread = threading.Thread(target=_expControlLoop,args=(loggerConn,))
#     
#     logThread.run()
#     
#     time.sleep(1)
# 
#     
#     print loggerConn
#     print "pluxconn:",pluxConn
    
    
#    testPlot()
       
#    serialOpen()
#    _serialTest()
       
#     if checkSettingsConsistency():          
#         try:
#             #init
#             pluxOpenDevice(child_conn)
#             serialOpen(True)
#         
#             cfg = RealtimePlot.PlotConfig()
#             cfg.channelCnt = len(channelHeader)
#             cfg.channelLabels = channelHeader  
#             cfg.xLabel = "Sample Nr (10 sec total)"
#             cfg.xRange = 10 * fs    #display last 10 seconds
#             cfg.yMin = 0
#             cfg.yMax = 2**bitsResolution
#             
#             deviceThread = threading.Thread(target=pluxStartDeviceLoop)
#             
#             #get subject id
#             print "-" * 40
#             print "Hello this is Plux_Logger " + versionStr
#             print "Listening on port '" + serialPort + "' for events from Presentation."
#             print "Valid events are any chars. Typically: 's' for start, 'k' for klick, 'e' for end."
#             print "Receiving the end event ends this logging session."
#             print "To end otherwize, press <ctrl-c>."
#             print "Enter subject id 'nolog' to not write a log file and use visualization only"
#             print
#             print "Please attach the sensors to plux channel like this:"
#             print "ch1 - ECG, ch2 - EDA, ch3 - BVP"
#             print "-" * 40
#             if not ser:
#                 print "!!!Serial port could not be opened!!!"
#             subjectId = raw_input("Please input subject id: ")
#             
#             if subjectId == 'nolog':
#                 print "!!!Not writing a log file!!!"
#                 nolog = True
#             else:
#                 initLogRaw(subjectId)
#             
#             #start logging
#             deviceThread.start()
#             RealtimePlot.startPlotProcess(cfg)
#             
#             _expControlLoop(parent_conn)
#             
#             deviceThread.join()     #wait for device thread to end    
#             
#             print "Logging session ended. Closing plot in 5 seconds."
#             time.sleep(5)
#             RealtimePlot.terminatePlotProcess()  
#     
#         except Exception as e:
#             print e
#             time.sleep(5)
#         finally:
#             pluxCloseDevice()   #otherwize it stays occupied by python process
#             closeLogRaw()
#             serialClose()
            
