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
This module contains functions used to export or display recorded data from
previous experiments.
'''

from __future__ import division     #so integer division results in float

import numpy as np
import json
import csv
from matplotlib import pyplot as plt
from matplotlib.backend_bases import MouseEvent
import matplotlib.animation as animation
import multiprocessing as mp
import os
import MsgLogger

plotProc = None

class BioLinkRawDataPlot():
    vLineX = 0.0
    vLineXold = 0.0 #so animation function can detect change
    axVLines = []
    
    def __init__(self,windowName,channelHeader,fs,data,serialEventData,extEventData):
        channelCnt = len(channelHeader)
        frameCnt = data.shape[0]
        self.fs = fs
        xLabel = "time [s]"
        
        durationSec = frameCnt/fs
#         print "durationSec:", durationSec
        
        xData = np.arange(0.0,durationSec,1.0/fs)
        
        
        plt.ioff()      #interactive mode off, so plt.show() blocks until plot window is closed
        
        self.fig, self.axArr = plt.subplots(channelCnt+1,1,sharex=True)   #one plot more for events
        self.fig.canvas.set_window_title(windowName)
         
        for i in range(channelCnt):
            self.axArr[i].plot(xData,data[:,i])
            self.axArr[i].set_ylabel(channelHeader[i])
            self.axVLines.append( self.axArr[i].axvline(self.vLineX,color='g',linestyle='dashed') )
        
        
        self._drawEvents(serialEventData, 'b')   #blue        #TODO: legend
        self._drawEvents(extEventData,'k')       #black
        self.axVLines.append( self.axArr[-1].axvline(self.vLineX,color='g',linestyle='dashed') )
        self.axArr[-1].set_ylabel('Experiment\nEvents')
                 
        plt.xlabel(xLabel)                                      
        plt.tight_layout()
        plt.xlim(0,xData[-1])
        
        plt.connect('button_press_event', self.onMouseClick)
        
#         plt.connect('motion_notify_event', self.onMouseMove)
#         self.cursorAni = animation.FuncAnimation(self.fig, self._updateCursor, frames=None,
#                                     interval=100, blit=False)      #blit=True is much faster but zoom does not work anymore

    def _drawEvents(self,eventData, color='k'):
        vlineYtop = 1.0
        textPosY = vlineYtop + 0.2
        eventTimeList = []
        for ev in eventData:    #ev are tuples of shape (framenr, text)
            evTime = ev[0]/self.fs
            eventTimeList.append(evTime)
            
            self.axArr[-1].text(evTime,textPosY,ev[1], rotation=70, rotation_mode='anchor', color=color, horizontalalignment='left',verticalalignment='center', clip_on=True)

        self.axArr[-1].vlines(eventTimeList,0.0,vlineYtop,colors=color,linewidths=2)
        self.axArr[-1].set_ylim( (0.0, 4.0) )
        
    def show(self):
        plt.show()      #blocks until plot is closed
                
    def onMouseClick(self,event):
        if isinstance(event,MouseEvent):
#             print "onMouseClick:", event
            if event.xdata != self.vLineX:
                self.vLineX = event.xdata       #is None when mouse not on any axes, makes line vanish automatically
                
                #updating and drawing lines replaced by animation function
                for vLine in self.axVLines:
                    vLine.set_xdata(self.vLineX)

                self.fig.canvas.draw()

def _plotProcessFnc(windowName, pluxChannelHeader, fs, bioData, serialEventData, extEventData):
#     print "_plotProcessFnc"
    rawPlot = BioLinkRawDataPlot(windowName, pluxChannelHeader, fs, bioData, serialEventData, extEventData)
    rawPlot.show()

def plotBioLinkData(targetBaseName):
    global plotProc
#     print "plotBioLinkData:",targetBaseName

    success = True

    try:
        data = np.load(targetBaseName + '.npz')
        bioData = data['bioData']
        serialEventData = data['serialEventData']
        extEventData = data['extensionEventData']
        channelHeader = data['channelHeader']
    except Exception as e:
        MsgLogger.append("Error opening '.npz' file: " + str(e) )
        success = False
    
    
    
    try:
        with open(targetBaseName + '.json','r') as f:
            headerDict = json.load(f)
            if 'fs' in headerDict:
                fs = headerDict['fs']
            else:
                success = False
                MsgLogger.append("Error reading fs from '.json' file.")
    except Exception as e:
        MsgLogger.append("Error opening '.json' file: " + str(e) )
        success = False
        
    if success:
        windowName = os.path.basename(targetBaseName) + '.npz'
        plotProc = mp.Process(target=_plotProcessFnc, args = (windowName, channelHeader, fs, bioData, serialEventData, extEventData))
        plotProc.daemon=True
        plotProc.start()

        
def terminatePlotProcess():
    global plotProc
    if plotProc:
        plotProc.terminate()

def exportTxt(targetBaseName,destinationName):
    """targetBaseName to find 'basename.npz' and 'basename.json'
    destinationName should end in .txt
    
    If multiple event arrived on one were logged on the same frame, the strings are concatenated by semicolons (;).
    """
    
    data = np.load(targetBaseName + '.npz')
    bioData = data['bioData']
    serialEventData = data['serialEventData']
    extEventData = data['extensionEventData']
    channelHeader = data['channelHeader']
    
    totalFrameCnt = bioData.shape[0]
    totalSerialEventCnt = serialEventData.shape[0]   
    totalExtEventCnt = extEventData.shape[0]
    
    exportTxt.header = ""
    
    def appendHeaderLine(line):
        exportTxt.header = exportTxt.header + "# " + line + os.linesep
    
    try:
        with open(targetBaseName + '.json','r') as f:
            headerDict = json.load(f)
            if 'version' in headerDict:
                appendHeaderLine(str(headerDict['version']))
                
            if 'dateStr' in headerDict:
                appendHeaderLine("Date: " + str(headerDict['dateStr']))
                
            if 'experimentId' in headerDict:
                appendHeaderLine("Experiment ID: " + str(headerDict['experimentId']))
                
            if 'subjectId' in headerDict:
                appendHeaderLine("Subject ID: " + str(headerDict['subjectId']))
                
            if 'duration_sec' in headerDict:
                appendHeaderLine("Duration [sec]: " + str(headerDict['duration_sec']))
                
            if 'frameCnt' in headerDict:
                appendHeaderLine("Total data frames: " + str(headerDict['frameCnt']))
                
            if 'extension' in headerDict:
                appendHeaderLine("Extension: " + str(headerDict['extension']))
                
            appendHeaderLine("----------------------------------")
            if 'fs' in headerDict:
                appendHeaderLine("SampleRate: " + str(headerDict['fs']))
                
            if 'pluxMac' in headerDict:
                appendHeaderLine("Plux Device MAC: " + str(headerDict['pluxMac']))
            
    except Exception as e:
        MsgLogger.append("Error opening '.json' file: " + str(e) )
        
    appendHeaderLine("Columns:")
    
    columnHdr = ""
    for h in channelHeader:
        columnHdr = columnHdr + "\t" + h
    columnHdr = columnHdr + '\tSerialEvent' + "\tExtensionEvent"
    appendHeaderLine(columnHdr)
        
    with open(destinationName,'wb') as f:
        f.write(exportTxt.header)
        csvWriter = csv.writer(f,delimiter='\t')
        
        serialEventIndex = 0
        extEventIndex = 0
        
        for i in range(totalFrameCnt):
            logRow = [i] + bioData[i].tolist()
            
            serEventStr = ""
            while serialEventIndex < totalSerialEventCnt and serialEventData[serialEventIndex][0] == i:
                if serEventStr != "":
                    serEventStr = serEventStr + ";"     #separate different events for same frame nr with ';'
                serEventStr = serEventStr + serialEventData[serialEventIndex][1]
                serialEventIndex += 1
                    
            if serEventStr != "":
                logRow.append( serEventStr.replace(" ", "_") )
            else:
                logRow.append('-')
            
            
            extEventStr = ""
            while extEventIndex < totalExtEventCnt and extEventData[extEventIndex][0] == i:     #concatenate all extEvents with this frame nr
                if extEventStr != "":
                    extEventStr = extEventStr + ";"     #separate different events for same frame nr with ';'
                extEventStr = extEventStr + extEventData[extEventIndex][1]
                extEventIndex += 1
                
            if extEventStr != "":
                logRow.append( extEventStr.replace(" ", "_") )
            else:
                logRow.append('-')
                
            csvWriter.writerow(logRow)
            
        if serialEventIndex != serialEventData.shape[0]:
            MsgLogger.append( "Some events occured after the latest sample in the data set.: " + str( serialEventData[serialEventIndex] ) )   
    
    
if __name__ == '__main__':
#     exportTxt("../log/test_t1_20160713_1439","../log/test_t1_20160713_1439.txt")
    plotBioLinkData("../log/test_NA_20160721_1605")

        
    
    