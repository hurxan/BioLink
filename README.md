# BioLink
<div id="top"></div>

<!-- PROJECT SHIELDS -->

<div align="center">

  [![Contributors][contributors-shield]][contributors-url]
  [![Forks][forks-shield]][forks-url]
  [![Stargazers][stars-shield]][stars-url]
  [![Issues][issues-shield]][issues-url]
  
</div>

<br />
<div align="center">
<h3 align="center">BioLink</h3>
  <p align="center">
    A tool for synchronized psycho-physiological and behavioural data acquisition.
    <br />
    <a href="https://github.com/hurxan/BioLink/blob/master/Manual.pdf"><strong>See the manual »</strong></a>
    <br />
    <br />
    <a href="https://github.com/hurxan/BioLink/issues">Report Bug</a>
    ·
    <a href="https://github.com/hurxan/BioLink/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

BioLink enables the integrated acquisition, synchronization and labelling of stimulus events acquired from
observational data using PsychoPy, with data acquired using a Biosginals Kit. <br/>
The PLUX Bisognal Kits include devices and software. The devices are referred to as the “PLUX device” throughout this readme. <br/>
BioLink bridges a specific gap in the present range of PLUX Biosignals synchronization tools. Harmonized marking and labelling
of stimulus events and physiological data is accomplished by synchronizing the timestamps of stimulus
events with the physiological data in one timeline. <br/>
The raw data is stored unprocessed and can be analysed using any tool that supports the import of .txt files. <br/>
BioLink is a pure Python application, providing an easy to use graphical user interface (GTK3 based). It is distributed under LGPLv3 license. <br/>
For compatibility with PsychoPy, it is built using Python 2.7 32-Bit edition.

<p align="right">(<a href="#top">back to top</a>)</p>


### Built With

* [Python 2.7](https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi)
* [PyGObject](https://sourceforge.net/projects/pygobjectwin32/)

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

### Important

BioLink has been tested on Windows® 10.

### Prerequisites

* Python 2.7
* PIP
* OpenSignals API for Python 2.7 (included inside the project)
* PyGObject


### Installation

The following steps show how to set up BioLink on a Windows® platform, using the binary release of BioLink downloadable from github.
1. Clone the repo
   ```sh
   git clone https://github.com/hurxan/BioLink.git
   ```
2. Unpack the zip file in the desired installation directory.
3. Install Python 2.7 and PIP:
	* [Python 2.7.9](https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi)
	* [PIP](https://bootstrap.pypa.io/pip/2.7/get-pip.py)
4. Install PyGObject for Python 2.7 (https://sourceforge.net/projects/pygobjectwin32/)
5. Install missing dependencies via PIP
6. Pair PLUX device using its own USB dongle or via Bluetooth:
	* USB dongle connection is immediate and doesn't require any kind of setup.
	* Bluetooth pairing will require a PIN (123).
7. BioLink is started by launching (double-click) the file ‘start.bat’ in the unpacked BioLink directory.

Launching BioLink for the very first time can take up to a few minutes, as all the Python source code will be compiled at first run.

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- USAGE EXAMPLES -->
## Usage

For more details about the usage of the software, please refer to the [BioLink Manual](https://github.com/hurxan/BioLink/blob/master/Manual.pdf)

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributions are highly appreciated.

If you have a suggestion that would make this better, please fork the repo and create a pull request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

Andrei Senyuva - hurcanandrei.senyuva@unipd.it

[Project Link](https://github.com/hurxan/BioLink)

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Original Project by BioLinkJ](https://github.com/BioLinkJ/BioLink)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/hurxan/BioLink.svg?style=for-the-badge
[contributors-url]: https://github.com/hurxan/BioLink/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/hurxan/BioLink.svg?style=for-the-badge
[forks-url]: https://github.com/hurxan/BioLink/network/members
[stars-shield]: https://img.shields.io/github/stars/hurxan/BioLink.svg?style=for-the-badge
[stars-url]: https://github.com/hurxan/BioLink/stargazers
[issues-shield]: https://img.shields.io/github/issues/hurxan/BioLink.svg?style=for-the-badge
[issues-url]: https://github.com/hurxan/BioLink/issues
[product-screenshot]: images/screenshot.png
