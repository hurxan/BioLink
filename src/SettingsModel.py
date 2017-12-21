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
The SettingsModel class is used to safe and load the settings from the settings file,
so they are retained when the program is closed. There are setters for most settings
which check setting integrity.
"""

import json
import MsgLogger
from __builtin__ import False
from ExpController import MAX_CHANNEL_CNT
import os


if os.name == 'nt':
    DEFAULT_SERIAL_PORT = "COM1"     #"\\\\.\\COM1"  #on Windows
else:
    DEFAULT_SERIAL_PORT = '/dev/ttyUSB0'    #on mac OS X / Linux
    

class SettingsModel:
    ver = "0.4"
    
    def __init__(self):
        self.setToDefaultValues()
    

    def setToDefaultValues(self):
        #default values:
        #all settings entries have to be present here
        #if new settings are introduced, adding their default here is sufficient
        self.settingsDict = dict(serialPort = DEFAULT_SERIAL_PORT,
                        pluxMac = "xx:xx:xx:xx:xx:xx",
                        channelNames = ("ECG","EDA","BVP"),
                        experimentId = "test",
                        sampleRate = 1000,
                        maxDuration = 60,
                        useSerial = True,
                        useLifePlot = True,
                        reopenLifePlot = True,
                        extension = "None")

    def updateSettings(self, setDict):
        """
        setDict as dictionary
        defaults: {'channelNames': ('ECG', 'EDA', 'BVP'), 'pluxMac': "xx:xx:xx:xx:xx:xx", 
        'experimentId': 'test', 'serialPort': 'COM1'}
        """
        for k in setDict.iterkeys():
            if k in self.settingsDict:  #only update key if key already in dictionary -> cannot create new keys, only valid settings
                self.settingsDict[k] = setDict[k]
            else:
                print "Key '" + k + "' unknown"
    
        
    def getChannelNamesStr(self):
        s = ""
        i = 1
        firstCh = True
        
        for ch in self.settingsDict['channelNames']:
            if len(ch) > 0:     #empty string means channel not used
                if not firstCh:   #second cycle
                    s = s + ", "
                s = s + str(i) + ":" + ch
                firstCh = False
            i += 1
            
        return s
    
    def setChannelNamesStr(self,s):
        """returns True on success
        """
        success =  True
        chList = [""] * MAX_CHANNEL_CNT
        chStrs = s.split(',')
        
        #assign names to channels
        for ch in chStrs:
            try:
                nr,name = ch.split(':')
                nr = int(nr.strip())
                if nr+1 > MAX_CHANNEL_CNT:
                    success = False
                else:
                    name = name.strip()
                    if name == "":
                        success = False
                    else:
                        chList[nr-1] = name
            except:
                success = False
        
        #remove unused channels at end
        for i in range(MAX_CHANNEL_CNT-1,-1,-1):
            if chList[i] == "":
                chList.pop()
            else:
                break
            
        self.settingsDict['channelNames'] = tuple(chList)
                
        return success

    def setSampleRateStr(self,sampleRateStr):
        """returns True on success
        """
        success = False
        try:
            sampleRate = int(sampleRateStr)
            if sampleRate >= 100:
                if sampleRate <= 1000:
                    if sampleRate % 100 == 0:   #is multiple of 100
                        success = True
                    else:
                        sampleRate = (sampleRate + 50) / 100 * 100
                else:
                    sampleRate = 1000
            else:
                sampleRate = 100
                
            self.settingsDict['sampleRate'] = sampleRate
        except:
            pass
        
        return success
    
    def getSampleRateStr(self):
        return str(self.settingsDict['sampleRate'])
    
    def setMaxDurationStr(self,maxDurationStr):
        """returns True on success
        """
        success = False
        try:
            maxDur = int(maxDurationStr)
            if maxDur <= 480:
                if maxDur >= 1:
                    success = True
                else:
                    maxDur = 1
            else:
                maxDur = 480
                
            self.settingsDict['maxDuration'] = maxDur
        except:
            pass
        
        return success
            
    def getMaxDurationStr(self):
        return str(self.settingsDict['maxDuration'])

    def dumpSettings(self, f):
        """
        dump settings in json format to file f
        """
#         MsgLogger.append("Saving settings to '" + f.name + "'")
        setDict = {'ver': self.ver,
            'settings': self.settingsDict
            }
            
    #        print setDict
        
        json.dump(setDict, f, indent=2, )
        
        
    def loadSettings(self, f):
        """
        load settings in json format from file f
        """
        self.setToDefaultValues()
        
        setDict = json.load(f)
        if not ('ver' in setDict and setDict['ver'] == self.ver):
            MsgLogger.append("Version in '" + f.name + "' does not match class version. Using default values.") 
            return
            
        if 'settings' in setDict:
            self.updateSettings(setDict['settings'])
        else:
            print "Key 'settings' not found. Using default values"
            
            
settingsModel = SettingsModel()
    

if __name__ == "__main__":
    

    semo = SettingsModel()  
     

#     print semo.getChannelNamesStr()
#     print semo.setChannelNamesStr(" 1 :ECG,2: EDA, 3:BVP,7:sieben, 5:fünf ")
#     print semo.getChannelNamesStr()

#     print semo.setSampleRateStr('200')
    print semo.setMaxDurationStr('120')

    print semo.settingsDict

#     print semo.expParamDict
#     print semo.expType
#     print semo.candDefParamDict
#     print semo.candEvParamDict
#     
#     with open("test.json",'w') as f:
#         semo.dumpSettings(f)
#         
#     with open("test.json",'r') as f:
#         semo.loadSettings(f)
#         
#     print semo.expParamDict
#     print semo.expType
#     print semo.candDefParamDict
#     print semo.candEvParamDict
        