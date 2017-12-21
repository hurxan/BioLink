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
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject


from Extensions.ExtensionBase import ExtensionBase

class ExtensionTemplate(ExtensionBase):
    """
    Template Extension
    """
    
    #to be set by chlid class
    logColumnHeader = ["frameNr", "event"]        #list of log column headers
    extensionName = "template"
    
    def onDialogResponse(self,dialog,responseId):
        if responseId == Gtk.ResponseType.OK:
            event = "OK"
        elif responseId == Gtk.ResponseType.CANCEL:
            event = "cancel"
        elif responseId == Gtk.ResponseType.DELETE_EVENT:
            event = "delete"
            self.eib.endExperiment()
        else:
            event = str(responseId)
            
        forceFrameNr = None
        if event == "cancel":
            forceFrameNr = 123
            
        frameNr = self.eib.putEvent(event, frameNr=forceFrameNr)
        self.logAppendLine([frameNr, event])
#         print "event detected at frame nr " + str(frameNr) + ": '" + event + "'"
#         self.extensionInterface.putEvent("test")    #test concatenation of 2 events on the same frame
    
    def extMainLoop(self):
        self.baseMsg = "This Dialog is displayed by the BioLink template extension."
        self.dialog = Gtk.MessageDialog(type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK_CANCEL, text=self.baseMsg, title="template extension")
        self.dialog.connect("response",self.onDialogResponse)
        self._updateDialogMsg("")
        self.dialog.show()
        
        self.lastFrameNr = -1
        
        self.startBioDataProcessing()    
           
        Gtk.main()
        
    def _endTemplateExt(self):
        self.stopBioDataProcessing()
        self.dialog.destroy()
        Gtk.main_quit()     #end Gtk main loop of extension process
        
    def _updateDialogMsg(self,msg):
        if self.dialog.is_visible():    #only if dialog still open
            self.dialog.format_secondary_text(msg)
        
    def onBioDataFrame(self,frameNr,bioDataTup):
        """
        To be overridden by extension.
        Called by bioDataProcessing thread for every frame; must not block. 
        bioDataTup contains as many values as there are channels active (see self.extensionInterface.channelHeader)
        """
        if self.lastFrameNr == frameNr:
            print "Frame transmitted twice:", frameNr, bioDataTup
            self.lastFrameNr = frameNr
            
        if frameNr % (self.extConstants.sampleFreq/4) == 0:       #every 0.25 second
#             print "onBioDataFrame:", frameNr
            
            dataStr = "Frame: " + str(frameNr) + "  Bio Data:"
            for i in range(len(self.extConstants.channelHeader)):
                dataStr = dataStr + "  " + self.extConstants.channelHeader[i] + ": " + str(bioDataTup[i])
            
            GLib.idle_add(self._updateDialogMsg,dataStr)
            
    def onExtEndRequest(self):
        """
        To be overridden by extension.
        Can be used to react on requestEndExtention event.
        """
        GLib.idle_add(self._endTemplateExt)
            
            
if __name__ == '__main__':
    from ExtensionInterface import ExtensionInterfaceFrontend
    import time
   
    
    eif = ExtensionInterfaceFrontend("t1", "test", "test_log/", time.localtime() , "test_t1_", ["ecg","eda","bvp"], 1000)
#     ei.extensionInstance = ExtensionTemplate(ei)
    print eif.selectExtensionByName("template")
    eif.extensionStart()
    
    print "started"
    
    time.sleep(10)
    eif.extensionEnd()
    print "ended"
    
        