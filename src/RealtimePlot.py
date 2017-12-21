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
This module is used for plotting the measured data life during the experiment.
"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation

import multiprocessing as mp
import Queue

import time
import sys

class PlotConfig:
    channelCnt = 1
    channelLabels = None
    xLabel = 'Sample Nr'
    xRange = 1000  #samples
    yMin = -2048
    yMax = 2048
    reopenPlotOnClose = True
    

#constants
dataQueueBufLen = 10000 #dataframes
refreshRate = 10     #per second

#global variables within plot process
plotCfg = None
fig = None
axArr = None
lineList = None
anim = None
dataQueue = None

#global variables local process
queueInp = None
proc = None
isPlotOpen = mp.Event()

# initialization function: plot the background of each frame
#def _initFnc():
#    global fig,axArr,lineList,dataQueue,anim
##    for i in range(channelCnt):
##        lineList[i].set_data([x for x in range(-xRange+1,1)], [0 for x in range(xRange)])
#    
#    lineList[0].set_data([x for x in range(-plotCfg.xRange+1,1)], [0 for x in range(plotCfg.xRange)])
#    return lineList[0]
    

# animation function.  This is called sequentially
def _animateFnc(i):
    global fig,axArr,lineList,dataQueue,anim
    
    dataReceived = False

    
    try:
        (time, data) = dataQueue.get_nowait()
        
        dataReceived = True     #get frame from queue successful, no exception raised
        
        timeList = []
        channelDataList = []
        for i in range(plotCfg.channelCnt):
            channelDataList.append( [] )    #initialize with channelCnt empty lists
        
        while True:     #until exception Queue.Empty is raised
            #process data
            timeList.append(time)
            for i in range(plotCfg.channelCnt):
                channelDataList[i].append(data[i])  #append frame data coming in tuple to list for each channel
        
            #try whether there is more data in queue
            (time, data) = dataQueue.get_nowait()      
        
    except Queue.Empty:
        pass
    
    if dataReceived:
#        print timeList, channelDataList[0]
#        sys.stdout.flush()  
        
        #now all new data in timeList and channelDataList
        x = lineList[0].get_xdata()                                 #xdata is the same for all lines
                #cut too old data points
                
        #find index of oldest x value to keep
        oldestFrameNr = timeList[-1] - plotCfg.xRange    #last element - xRange
        cutIndex = 0
        for x_val in x:
            if x_val < oldestFrameNr:
                cutIndex += 1       #increase cutIndex until oldest x value to keep found
            else:
                break
                
        newx = np.concatenate((x[cutIndex :], timeList) )      #so process only once
        
        for i in range(plotCfg.channelCnt):
            y = lineList[i].get_ydata()
            newy = np.concatenate((y[cutIndex :], channelDataList[i]) )
            
#            print newy[-1]
#            sys.stdout.flush()
            
            lineList[i].set_data(newx,newy)
            
            x_end = newx[0]+plotCfg.xRange 
#             if x_end < newx[-1]:
#                 print "plot right xlim too short"
            axArr[i].set_xlim(newx[0],x_end)

    return lineList, axArr  #return all lines and axes

def _init():
    global fig,axArr,lineList,anim

    plt.ioff()      #interactive mode off, so plt.show() blocks until plot window is closed
    
    lineList = []
#    initX = [x for x in range(- plotCfg.xRange+1,1)]
    initX = [0]
#    initY = [0 for x in range(plotCfg.xRange)]
    initY = [0]

    
    fig, axArr = plt.subplots(plotCfg.channelCnt,1,sharex=True)
    
    if plotCfg.channelCnt == 1:
        axArr = [axArr]     #make list from single object for compatibility
    
    for i in range(plotCfg.channelCnt):
#         axArr[i].set_xlim( (- plotCfg.xRange,0) )
        axArr[i].set_xlim( (0,plotCfg.xRange) )
        axArr[i].set_ylim( (plotCfg.yMin, plotCfg.yMax) )
        line, = axArr[i].plot(initX, initY, linewidth=1)
        lineList.append(line)
        if plotCfg.channelLabels:
            axArr[i].set_ylabel(plotCfg.channelLabels[i])
            
    plt.xlabel(plotCfg.xLabel)
    
    
    # call the animator.  blit=True means only re-draw the parts that have changed.
    anim = animation.FuncAnimation(fig, _animateFnc, #init_func=_initFnc,
                                   interval = (1000/refreshRate), blit=False)
    
                                   
    plt.tight_layout()

   
def _plotProcessFnc(queue,plotConfig,isPlotOpen):
#    print "Hello process"
#    sys.stdout.flush()
    
    #globals need to be reinitialized from parameters in new process...
    global dataQueue, plotCfg
    dataQueue = queue
    plotCfg = plotConfig
    
    
    while True:
        _init()
        plt.show()
        
        if plotConfig.reopenPlotOnClose and not dataQueue.empty():
            print "plot closed, reopening plot"
#             sys.stdout.flush()   # leads to crash when executed without console (pythonw.exe) 
        else:
            isPlotOpen.clear()
            break       #emulates do while loop
        
        
    
   
def startPlotProcess(plotConfig):
    global dataQueue, proc, isPlotOpen
    
    dataQueue = mp.Queue(dataQueueBufLen)    #buffers max dataQueueBufLen elements
    isPlotOpen.set()
    
    #plotting from a thread does not work, process needed
    proc = mp.Process(target=_plotProcessFnc, args = (dataQueue,plotConfig,isPlotOpen))
    proc.start()
    
def plotDataFrame(time,data):
    """time as int, data as tuple of channels
    """
    global dataQueue, isPlotOpen
    if isPlotOpen.is_set():
        tup = (time,data)
        try:
            dataQueue.put_nowait(tup)
        except Queue.Full:
            print "plotDataFrame: Queue full. Omiting data frame."

def joinPlotProcess():
    global proc
    proc.join()
    
def terminatePlotProcess():
    global proc
    if proc:
        proc.terminate()
        isPlotOpen.clear()
        proc = None
        

def dummyDataSenderLoop(channelCnt,yMax):
    fs = 100
    freq = 1
    
    for i in range(10*fs):
#        print i
        y = []
        for ch in range(channelCnt):
            curY = np.sin(2 * np.pi * i * freq/fs + (ch * np.pi * 0.5)) * yMax * 0.9
            y.append(curY)
        plotDataFrame(i,tuple(y))
        
        time.sleep(1.0/fs)
    
    
if __name__ == '__main__':    
    print "RealtimePlot test"  


    cfg = PlotConfig()
    cfg.channelCnt = 3
    cfg.channelLabels = ["ecg","eda","bvp"]
    
    startPlotProcess(cfg)    
       
    dummyDataSenderLoop(cfg.channelCnt,cfg.yMax)
    
    print "dummy data generation ended"
    time.sleep(5)
    
    proc.terminate()
    proc.join()

    