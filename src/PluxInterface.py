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
This module provides the interface class to communicate with Plux devices.
"""
import sys
sys.path.append(r"C:\Plux\OpenSignals (r)evolution\code\modules\WIN32")     #path of plux library
import plux     #@UnresolvedImport
import threading
import time
import math



class Device(plux.MemoryDev):
    """
        one end of a pipe has to be assinged to pipeConn
        tuples are sent through the pipe for every data frame received from the
        device. Tuples: (frame_nr, data_from_all_channels)
        reception from device
    """
    pipeConn = None
    stopRequest = threading.Event()

    # callbacks override
    def onRawFrame(self, nSeq, data):
        tup = (nSeq, data)
        if self.pipeConn:    #not None
            self.pipeConn.send(tup)        
        
            if self.stopRequest.isSet():
                return True
            else:
                return False
        else:
            print "onRawFrame: ending because no pipe registered"
            return True     #ends aquisition
            
        return False
        
    def endAquisition(self):
        """ends aquisition, leads loop() method to end
        """
        self.stopRequest.set()
        
    def getBatteryStr(self):
        bat = self.getBattery()
        if bat == -1.0:
            bat = "charging"
        else:
            bat = "%.0f %%" % bat
        return bat
      
# pluxDevice.start(fs, channelMask, bitsResolution)   # 1000 Hz, ports 1-8, 16 bits                
#     pluxDevice.loop()   #blocks 
#     print "Plux device loop terminated"
#     pluxDevice.stop()  
# pluxDevice.close()

class DummyDevice():
    pipeConn = None
    stopRequest = threading.Event()
    
    def getProperties(self):
        return "Dummy device for testing."           
    
    def start(self, fs, channelMask, bitsResolution):
        self.period = 1.0/fs
        self.channelCnt = bin(channelMask).count("1")     #count '1' in string representation
        self.bitsResolution = bitsResolution
        
        self.sampleNr = 0
        self.dataMax = 2**self.bitsResolution - 1
        
    def loop(self):
        period2pi = self.period * 2 * math.pi
        dataMean = self.dataMax / 2
        dataAmplitude = self.dataMax / 2
        tNext = time.clock() + self.period
        
        if self.pipeConn:    #not None
            while not self.stopRequest.is_set():
    #             self.timerEvent.wait(1.0)    #timeout: 1s
                time.sleep(self.period) #usually sleeps too long
                
                while tNext < time.clock():   #catch up missed frame to keep overall speed
                    data = int(math.sin(self.sampleNr*period2pi) * dataAmplitude + dataMean)
                    dataTup = tuple([ data ] * self.channelCnt)
                    tup = (self.sampleNr,dataTup)
                    
                    self.pipeConn.send(tup)
                    
                    self.sampleNr += 1
                    tNext += self.period
        else:
            print "DummyDevice.loop: ending because no pipe registered"
    
    def stop(self):
        pass
        
    def close(self):
        pass
    
    def endAquisition(self):
        """ends aquisition, leads loop() method to end
        """
        self.stopRequest.set()
    
    def getBatteryStr(self):
        bat = "150 %"
        return bat
     

def enumDevices():
    """ returns ((path string, descpription string),(...))
    """
    return plux.BaseDev.findDevices()

def openDevice(addr):
    """
    returns class instance for opened device
    returns dummy device if addr == "dummy"
    """
    if addr != "dummy":
        return Device(addr)
    else:
        return DummyDevice()    
    
    
if __name__ == '__main__':
    def tick():
        print "tick"
    
    threading.Timer(1.0,tick).start()
#     print enumDevices()
#     pluxDevice = Device("00:07:80:79:6F:E0")    # MAC address of device
#     props = pluxDevice.getProperties()
#     print 'Properties:', props
#     
#     pluxDevice.start(1000, 0x07, 16)
#     pluxDevice.loop()
#     pluxDevice.stop()
#     pluxDevice.close()
#     pluxDevice = None
#     
#     pluxDevice = Device("00:07:80:79:6F:E0")    # MAC address of device
#     props = pluxDevice.getProperties()
#     print 'Properties:', props
    
    