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
This module contains the view class, that draws the main window and contains
all button handler methods.
'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject

import MsgLogger
import Controller


class Handler: 
    def __init__(self, view):
        self.view = view
#         self.controller = controller
        
    def onDeleteWindow(self, *args):
#         self.controller.saveSettings()      #has to be in here because afterwards
#                                             #window is going to be destroyed and
#                                             #controller has to read out settings
        return Controller.onDeleteWindow()      #return True stops window from being destroyed
    
    def onStartClicked(self, button):
        Controller.startExperiment()
        
    def onEndClicked(self, button):
        Controller.endExperiment()
        
    def onFindPortsClicked(self, button):
        Controller.findSerialPorts()
        
    def onFindDevicesClicked(self, button):
        Controller.findPluxDevices()
        
    def onMenuSettingsReset(self, *args):
        Controller.resetSettings()
        
    def onMenuConvertLog(self, *args):
        Controller.convertLogToTxt()
        
    def onMenuPlotBioLinkData(self, *args):
        Controller.plotBioLinkData()


class BioLinkView:
    
    def __init__(self):
        self.handler = Handler(self)
        self.builder = Gtk.Builder()
        self.builder.add_from_file("BioLink_wnd.glade")
        self.builder.connect_signals(self.handler)
        
        self.tvConsole = self.builder.get_object("tvConsole")
        self.tbufConsole = self.tvConsole.get_buffer()
        
        #get objects
        self.window = self.builder.get_object("main_wnd")
        
        #text entrys
        self.teSerialPort = self.builder.get_object("teSerialPort")
        self.tePluxMac = self.builder.get_object("tePluxMac")
        self.teChannelNames = self.builder.get_object("teChannelNames")
        self.teExperimentId = self.builder.get_object("teExperimentId")
        self.teSubjectId = self.builder.get_object("teSubjectId")        
        self.teSampleRate = self.builder.get_object("teSampleRate")
        self.teMaxDuration = self.builder.get_object("teMaxDuration")
        
        #buttons
        self.btStart = self.builder.get_object("btStart")
        self.btEnd = self.builder.get_object("btEnd")
        self.btFindSerial = self.builder.get_object("btFindSerial")
        self.btFindPlux = self.builder.get_object("btFindPlux")
        
        #check boxes
        self.cbUseSerial = self.builder.get_object("cbUseSerial")
        self.cbUseLifePlot = self.builder.get_object("cbUseLifePlot")
        self.cbReopenLifePlot = self.builder.get_object("cbReopenLifePlot")
        
        #combo box: select extension
        self.cbExtension = self.builder.get_object("cbExtension")   
        
        self.freezeObjects = [self.teSerialPort,self.tePluxMac,self.teChannelNames,self.teExperimentId,self.teSubjectId,
                              self.btFindSerial,self.btFindPlux, self.teSampleRate, self.teMaxDuration,self.cbUseSerial,
                              self.cbUseLifePlot, self.cbReopenLifePlot, self.cbExtension]
        
        
        #set tooltips for fields with cheats
        self.teSubjectId.set_tooltip_text("Subject ID\nTESTING: enter 'nolog' to not save a log")
        self.tePluxMac.set_tooltip_text("MAC address of format: xx:xx:xx:xx:xx:xx\nTESTING: enter 'dummy' for dummy data")
        
        #test
#         self.teSerialPort.set_text("Com 1")
#         self.tePluxMac.set_text("plux mac")
#         self.teChannelNames.set_text("1: ECG, 2: EDA, 3: BVP")
#         self.teSubjectId.set_text("VP1")
#         self.btEnd.set_sensitive(False)
#         self.teExperimentId.set_text("IOWA")

    def initExtensionComboBox(self,extNameList):
        for e in extNameList:
            self.cbExtension.append_text(e)
        self.cbExtension.set_active(0)        
        
    def consoleAppendInternal(self, msg):
        #append text to console and scroll to apended line
            
        enditer = self.tbufConsole.get_end_iter()
        
        self.tbufConsole.insert(enditer, str(msg) + "\n")
        
        self.firstConsoleMsg = False
        
        GLib.idle_add(self.consoleScrollInternal)       #append scrolling command to Gtk event queue, has to be done after the insertion was done by the Gtk.main thread
        return False
    
    def consoleScrollInternal(self):
        self.tvConsole.scroll_to_iter(self.tbufConsole.get_end_iter() , 0.0, False, 0, 0)
        return False
    
    def consoleAppend(self, msg):
        #append to console thread safe
        GLib.idle_add(self.consoleAppendInternal, msg)
        
    def freezeSettings(self, bFreeze):  #true =  freeze, false = unfreeze
        if bFreeze:
            bSens = False
        else:
            bSens = True
            
        for obj in self.freezeObjects:
            obj.set_sensitive(bSens)
            
    def setWindowTitle(self,title):
        self.window.set_title(title)
    
    def show(self):
        self.window.show_all()
        

view = BioLinkView()

    
    
    
