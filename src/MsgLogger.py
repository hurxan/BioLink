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
The MsgLogger utility is used to process error messages as well as
notification messages. The append and appendDateTime functions are
used to append messages to the message log. The internal message loop
(msgLoop) is run by a separate thread. There, all messages are written
to a log file and also forwarded to the graphical user interface.
A message forwarding function for the user interface has to be registered
(i.e. viewAppendFnc must be assigned). The viewAppendFnc is called to
forward messages and potentially has to handle synchronisation with
the main GUI event loop.
"""

import time
import threading
import Queue

msgLogQueue = Queue.Queue()
viewAppendFnc = None
logfilePath = None

#class MsgLogger(threading.Thread):
#    
#    def __init__(self,logfilePath):
#        super(MsgLogger, self).__init__()
#        self.stoprequest = threading.Event()
#        
#    
#        
#    def join(self, timeout=None):
#        self.stoprequest.set()
#        super(MsgLogger, self).join(timeout)

    

def msgLoop():
    global logfilePath
    global msgLogQueue
    
    logFile = open(logfilePath,'w')
    while True:
        try:
            msg = msgLogQueue.get(True, 0.1)    #blocking, 0.1 sec timeout
            msg = msg.encode('ascii', 'ignore')

            if isinstance(msg,str):
                msgAction(logFile,msg)
            elif isinstance(msg,int) and msg == -1:
                break
            else:
                msgAction(logFile,"MsgLog Error: invalid msg type, expected string.")
                #raise Exception("MsgLog Error: invalid msg type, expected string.")
            
        except Queue.Empty:
            continue

    logFile.close()

        


msgLoggerThread = None
# msgLogger = MsgLogger("log/log_" + time.strftime("%Y%m%d_%H%M") + ".txt")

def init(path='log/MsgLog.txt'):
    global msgLoggerThread
    global logfilePath
    
    logfilePath = path
    msgLoggerThread = threading.Thread(target=msgLoop)
    msgLoggerThread.start()
    
def msgAction(logFile,msg):
    print msg

    logFile.write(msg + "\n")
    
    if viewAppendFnc:
        viewAppendFnc(msg)

def append(msg):
    msgLogQueue.put(msg)
    
def appendDateTime():
    append(time.strftime("%H:%M %d/%m/%Y"))
    
def close():
    append(-1)
    msgLoggerThread.join()
    

   
if __name__ == "__main__":
    
    init()
    
    
    def appendFnc(msg):
        print 'append: ' + msg
    
    
    viewAppendFnc =appendFnc 
    append("Hello")
    appendDateTime()
#    msgLogger.appendMsg(1)
    close()
    