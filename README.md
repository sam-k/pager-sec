# pager-sdr

Though largely replaced by smartphones today, pagers remain extremely common in niche fields, such as hospitals. Most pagers lack encryption/authentication and are vulnerable to attack. In this project, I use a software-defined radio (SDR) to intercept pages, parse the messages, and automate the task.

## Materials

This project uses the following hardware:
* [**SDR**](https://en.wikipedia.org/wiki/Software-defined_radio) with antenna, to intercept pages. I use the DVB-T+DAB+FM SDR, a USB 2.0 dongle that is available for cheap ($15–25) online. 
  * My SDR is based on the Realtek RTL2832U chipset and the Rafael Micro R820T tuner.
  * My SDR supports frequencies from 24 MHz to 1.766 GHz. You can check your SDR’s range based on its tuner on the [rtl-sdr wiki](https://osmocom.org/projects/rtl-sdr/wiki/Rtl-sdr).
* [**Raspberry Pi**](https://www.raspberrypi.org/) 3 Model B with 1 GB RAM, to automate the task. This and other RPi models are available online.

This project uses the following software stack:
* [**Gqrx**](https://gqrx.dk/), an open-source SDR receiver on Linux.
* [**SoX**](http://sox.sourceforge.net/), a cross-platform tool for audio processing.
* [**multimon-ng**](https://github.com/EliasOenal/multimon-ng), a digital decoder on Linux.
  * It is one of the few decoders that support FLEX and POCSAG, two common protocols for pagers.
* I am running macOS Big Sur 11.1 on my machine, and Raspbian Buster on the RPi. All Linux software were installed on  through [MacPorts](https://www.macports.org/).
