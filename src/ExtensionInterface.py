'''
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
This module is the interface between ExpController and extensions.
'''

import ctypes
import threading
from multiprocessing import Process, Event, Queue, Value, Pipe
from Queue import Full,Empty

import MsgLogger

try:
    import Extensions
    extensionClasses = Extensions.extensionClasses
except ImportError:
    extensionClasses = []   #empty list if no directory / package called Extensions
    print "Extensions module not found"
    

EVENT_QUEUE_IS_PIPE = False      #was implemented for performance test Pipe vs Queue. Queues have some latency (not constant)


def extProcessFnc(extensionClass, expConstants, _curFrameNr, consoleMsgQueue, eventQueue, bioDataQueue, requestBioData, requestEndExtention):
#     print "extProcessFnc start"
    #instantiate backend
    backend = ExtensionInterfaceBackend(expConstants, _curFrameNr, consoleMsgQueue, eventQueue, bioDataQueue, requestBioData, requestEndExtention)
    
    #instantiate extension class
    extInstnace = extensionClass(backend,expConstants)
    
    #run extension
    extInstnace.run()
    
#     print "extProcessFnc end"
    

class ExtensionInterfaceFrontend:
    """
    This is the frontend side and is instantiated by ExpController
    """
    def __init__(self, subjectId, experimentId, logDir, startTime, logFileNameBase, channelHeader, sampleFreq, nolog = False):
        
        #experiment variables, need to be updated by ExpController
        self._curFrameNr = Value(ctypes.c_int64,-1)   
        
        #experiment constants
        self.expConstants = ExperimentConstants(subjectId, experimentId, logDir, startTime, logFileNameBase, channelHeader, sampleFreq, nolog)
        self.extensionClass = None
        
        #instances for the current run
        self.consoleMsgQueue = Queue(maxsize=1000)    #not infinite size, better to detect errors
        
        if EVENT_QUEUE_IS_PIPE:
            print "EVENT_QUEUE_IS_PIPE"
            self.eventConnFrontend, self.eventConnBackend = Pipe()   
        else:
            self.eventQueue = Queue(maxsize=1000)    #not infinite size, better to detect errors
            
        self.bioDataQueue = Queue(maxsize=1000)    #not infinite size, better to detect errors 
        self.requestBioData = Event()
        self.requestEndExtention = Event()      #for ExpController to request for extension to end
        
        self.extProcess = None      #extension process
        self.consoleMsgThread = None
    
    def setCurrentFramenr(self,frameNr):
        self._curFrameNr.value = frameNr
    
    def checkEvents(self,curFrameNr):
        """
        returns a list of tuples with (frameNr, event strings), empty list if no events
        frameNr == -1 indicates a request from the extension to end the experiment
        to be used by ExpController to check on events
        Method updates curFrameNr so that curFameNr is always updated atomically with event check.
        This way the extension can determine at what frame nr the event will be detected.
        """
        ev = []

        with self._curFrameNr.get_lock():   #use _curFrameNr lock for not atomic operation
            if EVENT_QUEUE_IS_PIPE:
                if self.eventConnFrontend.poll():   #anything to receive?
                    ev.append( self.eventConnFrontend.recv() )
            else:
                try:
                    while True:     #loop ended by Quee.Empty exception
                        ev.append( self.eventQueue.get(False) )    #not blocking
                except Empty:
                    pass
            
            self._curFrameNr.value = curFrameNr
        
        return ev
    
    def putBioData(self, curFrameNr, bioDataTup):
        """
        To be used by ExpController to provide the current bio data to the extension.
        Bio data is only provided to the extension if the requestBioData was set by the extension: requestBioData(True)
        """
        if self.requestBioData.is_set():
            try:
                self.bioDataQueue.put((curFrameNr, bioDataTup))  #not blocking, ensure type str
            except Full:
                print "ExtensionInterface.putBioData: bioDataQueue full"
    
    def selectExtensionByName(self, extName):
        """
        Returns True on success
        """
        success = False
        
        self.extensionClass = None
        
        if extName == "None":
            success = True
        else:
            for c in extensionClasses:
                if c.extensionName == extName:
                    self.extensionClass = c    #just pass class, instance will be instantiated by extension process
                    success = True
                    break             
        return success
    
    def extensionStart(self):
        if self.extensionClass != None:     #any extension selected (not None)
            #start console msg handling thread
            if self.consoleMsgThread == None:   #thread not started yet
                self.consoleMsgThread = threading.Thread(target=self._consoleMsgLoop)
                self.consoleMsgThread.setDaemon(True)   #quit when main thread ends
                self.consoleMsgThread.start()
                
            self.requestEndExtention.clear()    #should be cleared already as new instance of ExtensionInterface is generated for every run
            
            #start extension process
            if EVENT_QUEUE_IS_PIPE:
                evQueue = self.eventConnBackend
            else:
                evQueue = self.eventQueue
            #all shared ressources have to be explicit arguments, not nested within a class or list
            self.extProcess = Process(target=extProcessFnc,args=(self.extensionClass, self.expConstants, self._curFrameNr, self.consoleMsgQueue, evQueue, self.bioDataQueue, 
                                                                 self.requestBioData, self.requestEndExtention))
            self.extProcess.start()

    def extensionEnd(self):
        self.requestEndExtention.set()
        
    def joinExtProcess(self,timeout=None):
        self.extProcess.join(timeout)

    def _consoleMsgLoop(self):
        while True:
            msg = self.consoleMsgQueue.get(block=True)
            MsgLogger.append(msg)
    
class ExtensionInterfaceBackend:
    """
    This is the backend side and is instantiated within the extension process. It is used by the extension class.
    """
    def __init__(self,expConstants, _curFrameNr, consoleMsgQueue, eventQueue, bioDataQueue, requestBioData, requestEndExtention):
        self.expConstants = expConstants
        self._curFrameNr = _curFrameNr
        self.consoleMsgQueue = consoleMsgQueue
        
        if EVENT_QUEUE_IS_PIPE:
            self.eventConnBackend = eventQueue
        else:
            self.eventQueue = eventQueue
            
        self.bioDataQueue = bioDataQueue
        self.requestBioData = requestBioData
        self.requestEndExtention = requestEndExtention      #for ExpController to request extension to end
        
    def getCurrentFramenr(self):
        cf = self._curFrameNr.value
        return cf
    
    def putEvent(self,eventStr,frameNr = None):
        """to log an event from the extension
        to be used by the extension
        frameNr to assign event to can be specified, if None frameNr is assinged the next frame (current + 1)
        returns the framenr the event will be recognized at by BioLink (ExpController), -1 on error
        
        The frame number at event generation is transmitted through the queue with the event str. 
        This way latencies of the queue have no effect on the event (time) detection.
        """        
        retval = -1
        with self._curFrameNr.get_lock():
            if frameNr == None:
                frameNr = self._curFrameNr.value + 1        #will be recognized on next frame
                
            if EVENT_QUEUE_IS_PIPE:
                self.eventConnBackend.send( (frameNr,str(eventStr)) )       #transmit tuple of frameNr and eventStr
                retval = frameNr 
            else:
                try:
                    #transmit tuple of frameNr and eventStr
                    self.eventQueue.put( (frameNr,str(eventStr)) ,False)  #not blocking, ensure type str
                    retval = frameNr
                except Full:
                    print "ExtensionInterface.putEvent: eventQueue full"
        
        return retval
    
    def setRequestBioData(self,request):
        if request:
            self.requestBioData.set()
        else:
            self.requestBioData.clear()
    
    def getBioData(self, block=True, timeout=10):
        """
        To be used by the extension. Should run in a separate data processing thread.
        Returns a tuple of (frameNr, (channel data tuple) ) or (None, None) if there was no new data within timeout [sec]
        """
        try:
            retval = self.bioDataQueue.get(block, timeout)
        except Empty:
            retval = (None, None)
            
        return retval
    
    def endExperiment(self):
        """
        For the extension to indicate that experiment is over, request to end experiment
        End experiment request is transmitted as event with frameNr == -1
        This way it is automatically synchronized with events and cannot arrive before events that were generated before.
        """
        self.putEvent("", frameNr=-1)
    
    def consoleMessage(self,msg):
        self.consoleMsgQueue.put(msg)
    
class ExperimentConstants:
    """
    This class is a wrapper for the experiment constants. It can only contain plain ctypes, no instances or lists.
    """
    def __init__(self,subjectId, experimentId, logDir, startTime, logFileNameBase, channelHeader, sampleFreq, nolog):
        self.subjectId = subjectId
        self.experimentId = experimentId
        self.logDir = logDir
        self.startTime = startTime
        self.logFileNameBase = logFileNameBase
        self.channelHeader = channelHeader
        self.sampleFreq = sampleFreq
        self.nolog = nolog

def enumerateExtensionNames():
    names = []
    for c in extensionClasses:
        names.append(c.extensionName) 
    
    return names
    
            
if __name__ == '__main__':
    pass
#     ec = enumerateExtensions()
#     
#     for c in ec:
#         print c.extensionName
#         
#        
#     ei = ExtensionInterface("t1", "test", "../log/", 0, "test_t1_")
#     ei.setCurrentFramenr(5)
#     
#     instance = ec[0](ei)
    
    
    
    