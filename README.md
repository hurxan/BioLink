# BioLink
A tool for synchronized psycho-physiological and behavioural data acquisition.

BioLink enables the integrated acquisition, synchronization and labelling of stimulus events acquired from
observational data, using the stimulus presentation packages Presentation® or PsychoPy, with
physiological data acquired using a biosignalsplux research kit. The biosignalsplux kits include devices
and software. The devices are referred to as the “PLUX device” throughout this readme. BioLink bridges a
specific gap in the present range of biosignalsplux synchronization tools. Harmonized marking and labelling
of stimulus events and physiological data is accomplished by synchronizing the timestamps of stimulus
events with the physiological data in one timeline. The raw data is stored unprocessed and can be analysed
using any tool that supports the import of .txt files.
BioLink is a pure Python application, providing an easy to use graphical user interface (GTK3 based). It is
distributed under LGPLv3 license. For compatibility with PsychoPy, it is built using Python 2.7 32-Bit
edition.
BioLink has been tested on Windows® 7 and 10. It could be readily be adapted to run on other platforms,
provided that the data acquisition hardware (PLUX) supports these.

## Getting Started
The following steps show how to set up BioLink on a Windows® platform, using the binary release of BioLink downloadable from github.
* Download and install OpenSignals for Windows 32-bit from the biosignalsplux homepage: http://biosignalsplux.com/en/software
Note: You need the 32-bit installation irrespective of whether you are operating a 32-bit or a 64-bit version of Windows®. This is because BioLink runs on a 32-Bit Python installation. In order for BioLink to be able to access the hardware driver integrated in OpenSignals, these versions need to match.
Please ensure that OpenSignals is installed in its standard installation path (‘C:\Plux’).
* Download the binary release zip-file from https://github.com/BioLinkJ/BioLink/releases
* Unpack the zip file in the desired installation directory (recommendation: directly in C:\ or in your user directory).
* Pair PLUX device (before using it for the first time, also see OpenSignals Manual)
	* make sure the Bluetooth interface is turned on as well as the PLUX device.
	* click on the Bluetooth symbol in the task list (bottom right of screen) and choose “Add a Bluetooth device”.
	* select / add the device called “biosignalsplux” (PIN: 123).
* BioLink is started by launching (double-click) the file ‘start_BioLink.bat’ in the unpacked BioLink directory.
Launching BioLink for the very first time can take up to a few minutes, as all the Python source code will be compiled at first run.
Note: At first run, the message “Error loading '../settings.json': [Errno 2] No such file or directory: '../settings.json'” will be shown in the message area. This is normal and will only occur the very first time BioLink is run, as the settings are initialised with default values and saved to the ‘settings.json’ file.

## Further information and instruction
Please refer to the manual (BioLink_1.4_Manual.pdf) for further information.



