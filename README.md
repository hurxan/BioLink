# BioLink
A tool for synchronized psycho-physiological and behavioural data acquisition.

BioLink enables the integrated acquisition, synchronization and labelling of stimulus events acquired from
observational data using PsychoPy, with data acquired using a Biosginals Kit. The PLUX Bisognal Kits include devices
and software. The devices are referred to as the “PLUX device” throughout this readme. BioLink bridges a
specific gap in the present range of PLUX Biosignals synchronization tools. Harmonized marking and labelling
of stimulus events and physiological data is accomplished by synchronizing the timestamps of stimulus
events with the physiological data in one timeline. The raw data is stored unprocessed and can be analysed
using any tool that supports the import of .txt files.
BioLink is a pure Python application, providing an easy to use graphical user interface (GTK3 based). It is
distributed under LGPLv3 license.
For compatibility with PsychoPy, it is built using Python 2.7 32-Bit edition.
BioLink has been tested on Windows® 10.

## Getting Started
The following steps show how to set up BioLink on a Windows® platform, using the binary release of BioLink downloadable from github.
* Download the binary release zip-file from https://github.com/hurxan/BioLink/releases
* Unpack the zip file in the desired installation directory.
* Install Python 2.7 and PIP:
	* Python 2.7.9 (https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi)
	* PIP (https://bootstrap.pypa.io/pip/2.7/get-pip.py)
* Install PyGObject for Python 2.7 (https://sourceforge.net/projects/pygobjectwin32/)
* Install missing dependencies via PIP
* Pair PLUX device using its own USB dongle or via Bluetooth:
	* USB dongle connection is immediate and doesn't require any kind of setup.
	* Bluetooth pairing will require a PIN (123).
* BioLink is started by launching (double-click) the file ‘start.bat’ in the unpacked BioLink directory.
Launching BioLink for the very first time can take up to a few minutes, as all the Python source code will be compiled at first run.

## Further information and instruction
Please refer to the manual (BioLink_Manual.pdf) for further information.