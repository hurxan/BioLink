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
This helper utility prevents Microsoft Windows systems from suspending during experiments.
'''

import ctypes

ES_CONTINUOUS        = 0x80000000
ES_AWAYMODE_REQUIRED = 0x00000040
ES_SYSTEM_REQUIRED   = 0x00000001
ES_DISPLAY_REQUIRED  = 0x00000002

def preventSleep():
    try:
        print "preventSleep"
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)  #@UndefinedVariableError
    except Exception as e:
        print "preventSleep Error: " + str(e)
        

def allowSleep():
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)   #@UndefinedVariableError
    except Exception as e:
        print "allowSleep Error: " + str(e)