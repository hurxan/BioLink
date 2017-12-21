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
This file is the entry point to BioLink. 
Start this file with a python 2.7 interpreter to launch BioLink.

main was not integrated in BioLinkView because the module called as main gets called '__main__' instead of its original name
Therefore, a module variable like BioLinkView.view (class instance in this case) is not shared by __main__ as __main__ sees the variable as
__main__.view whereas other modules importing BioLinkView see it as BioLinkView.view.
With this separate module as main, BioLinkView gets imported also by main.py and therefore the global module variables are shared by all importing modules.
'''
import gi
import ExpController
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject
import time
import os

logDir = "../log/"
versionStr = "BioLink_V1.4"
wndTitle = versionStr.replace("_", " ")

import MsgLogger
import Controller
from BioLinkView import view

if __name__ == '__main__':
    
    if (not os.path.exists(logDir)):
        os.mkdir(logDir)            #ensure log dir exists

    GObject.threads_init()  #initialize use of threads with GTK+
    # Calling GObject.threads_init() is not needed for PyGObject 3.10.2+

    ExpController.logDir = logDir
    ExpController.versionStr = versionStr

    MsgLogger.init(logDir + "BioLink_MsgLog_" + time.strftime("%Y%m%d_%H%M") + ".txt")
    MsgLogger.viewAppendFnc = view.consoleAppend
    
    Controller.init()
    
    view.setWindowTitle(wndTitle)
    view.show()     
    Gtk.main()      #does not return until window is closed 
     
    MsgLogger.viewAppendFnc = None
    
    MsgLogger.close()