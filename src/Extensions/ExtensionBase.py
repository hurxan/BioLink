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

'''

import threading

import csv
import time

class ExtensionBase:
    '''
    Base class for extensions.
    Methods starting with '_' should not be called by child classes.
    '''
    #to be set by chlid class
    logColumnHeader = []        #list of log column headers
    logAutomaticHeader = True   #if true, the header is written automatically before extMainLoop is called
    extensionName = "base"
    
    def __init__(self, extensionInterfaceBackend, extConstnats):
        self.eib = extensionInterfaceBackend
        self.extConstants = extConstnats

        self.logfile = None
        self.logCsvWriter = None
        
        self.dataProcessingEndRequest = threading.Event()
        self.dataProcessingThread = None
        
        self.mainTrheadRunning = threading.Event()
        
    def _requestEndExtentionLoop(self):
        while self.mainTrheadRunning.is_set():      #terminates when main thread is done
            if self.eib.requestEndExtention.wait(1):     #waits infinitely for event, 1 second timeout
                self.onExtEndRequest()
                break
                
        #thread must terminate properly, if terminated while in self.eib.requestEndExtention.wait() the event gets corrupted and cannot be set anymore
#         print "_requestEndExtentionLoop end"
      
    def run(self):
        self.mainTrheadRunning.set()
        
        #run tread to notice requestEndExtention event
        endExtentionThread = threading.Thread(target=self._requestEndExtentionLoop)
        endExtentionThread.start()
        
        #prepare logfile, write header
        self._logOpen()
        if self.logAutomaticHeader:
            self.logHeader()
        
        try:
            self.extMainLoop()
        except Exception as e:
            self.eib.consoleMessage(self.extensionName + ": Exception in extMainLoop: " + str(e))
        
        #close logfile
        self._logClose()
        
        self.mainTrheadRunning.clear()
        endExtentionThread.join(10)
        
    def extMainLoop(self):
        """
        Main loop of extension.
        To be overridden by extension.
        Method should not end until extension is finished or self.eib.requestEndExperiment.is_set() is True
        """
        print "extMainLoop: Please override method in your extension class."
        
    def _logOpen(self):
        if not self.extConstants.nolog:
            fileName = self.extConstants.logDir + self.extConstants.logFileNameBase + "_" + self.extensionName + ".txt"
            try:
                self.logfile = open(fileName,"wb")
                self.logCsvWriter = csv.writer(self.logfile,delimiter='\t')
            except:
                self.eib.consoleMessage("Error creating logfile: '" + fileName + "'")
                self.logfile = None
        else:
            self.logfile = None

    def logHeader(self,extensionHeaderLines=None):
        """
        if self.logAutomaticHeader == False this method has to be called in extMainLoop before writing to the logfile.
        optional: extensionHeaderLines is a list of lines to append to header with settings of the extension
        """
        def logWriteHdrLine(line):
            self.logfile.write("# " + line + "\r\n")
        
        if self.logfile:
            logWriteHdrLine("BioLink extension " + self.extensionName)
            logWriteHdrLine("Date: " + time.strftime("%d/%m/%Y %H:%M", self.extConstants.startTime))
            logWriteHdrLine("Experiment ID: " + self.extConstants.experimentId)
            logWriteHdrLine("Subject ID: " + self.extConstants.subjectId)
            if extensionHeaderLines != None:
                logWriteHdrLine("----------------------------------")
                for l in extensionHeaderLines:
                    logWriteHdrLine(l)
            logWriteHdrLine("----------------------------------")
            logWriteHdrLine("Columns:")
            
            columnHdr = ""
            for h in self.logColumnHeader:
                columnHdr = columnHdr + h + "\t"
            columnHdr = columnHdr[:-1]  #delete last '\t'
            logWriteHdrLine(columnHdr)
        else:
            print "logHeader: no logfile open"
        
    def logAppendLine(self,dataList):
        """
        Method to be used by extension to write a log row.
        dataList is the list of data elements, should contain as many elements as self.logColumnHeader
        """
        if self.logfile:
            if len(dataList) > len(self.logColumnHeader):
                print "logAppendLine: dataList longer than column count."
                dataList = dataList[:len(self.logColumnHeader)]  #truncate
                                         
            self.logCsvWriter.writerow(dataList)
    
    def _logClose(self):
        if self.logfile:
            self.logfile.close()
            self.logfile = None
            self.logCsvWriter = None      
        
    def _bioDataProcessingLoop(self):
        while not self.dataProcessingEndRequest.is_set():
            (frameNr, bioDataTup) = self.eib.getBioData(block=True,timeout=10)
            if frameNr != None:     #not None, there is new data
                self.onBioDataFrame(frameNr, bioDataTup)
            else:
                if not self.dataProcessingEndRequest.is_set():
                    print "ExtensionBase._bioDataProcessingLoop: no data"
                
    def startBioDataProcessing(self):
        self.eib.setRequestBioData(True)
        self.dataProcessingEndRequest.clear()
        self.dataProcessingThread = threading.Thread(target=self._bioDataProcessingLoop)
        self.dataProcessingThread.setDaemon(True)  #closed if last process that is running
        self.dataProcessingThread.start()
    
    def stopBioDataProcessing(self):
        self.eib.setRequestBioData(False)
        self.dataProcessingEndRequest.set()
        
    def onBioDataFrame(self,frameNr,bioDataTup):
        """
        To be overridden by extension.
        Called by pluxDataProcessing thread for every frame; must not block. 
        bioDataTup contains as many values as there are channels active (see self.extConstants.pluxChannelHeader)
        """
        print "onBioDataFrame: Please override method in your extension class."
    
    def onExtEndRequest(self):
        """
        To be overridden by extension.
        Can be used to react on requestEndExtention event.
        """
        print "onExtEndRequest: Please override method in your extension class."

if __name__ == '__main__':
    from ExtensionInterface import ExtensionInterfaceFrontend,ExtensionInterfaceBackend
    
#     ei = ExtensionInterface("t1", "test", "../log/", 0, "test_t1_")
#     eb = ExtensionBase(ei,'eb')
#     eb.start()
#     eb.endWait(10)
        
        