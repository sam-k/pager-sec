# pager-sdr

## Motivation

Though largely replaced by smartphones today, pagers remain extremely common in niche fields, such as hospitals. Most pagers lack encryption/authentication and are vulnerable to attack. In this project, I use a software-defined radio (SDR) to intercept pages, parse the messages, and automate the task.

## Materials

This project uses the following hardware:
* [**SDR**](https://en.wikipedia.org/wiki/Software-defined_radio) with antenna, to intercept pages. I use the DVB-T+DAB+FM SDR, a USB 2.0 dongle that is available for cheap ($15–25) online. 
  * My SDR is based on the Realtek RTL2832U chipset and the Rafael Micro R820T tuner.
  * My SDR supports frequencies from 24 MHz to 1.766 GHz. You can check your SDR’s range based on its tuner on the [rtl-sdr wiki](https://osmocom.org/projects/rtl-sdr/wiki/Rtl-sdr).
* [**Raspberry Pi**](https://www.raspberrypi.org/) 3 Model B with 1 GB RAM, to automate the task. This and other RPi models are available online.

This project uses the following software stack:
* [**Gqrx**](https://gqrx.dk/), an open-source SDR receiver on Linux.
  * [Dependencies](https://ports.macports.org/port/gqrx/summary): gnuradio, gr-osmosdr, portaudio, qt5-qtbase, qt5-qtsvg, volk (and their dependencies)
* [**SoX**](http://sox.sourceforge.net/), a cross-platform tool for audio processing.
  * [Dependencies](https://ports.macports.org/port/sox/summary): flac, lame, libiconv, libid3tag, libmad, libmagic, libogg, libopus, libpng, libsndfile, libvorbis, opusfile, twolame, wavpack, zlib (and their dependencies)
* [**multimon-ng**](https://github.com/EliasOenal/multimon-ng), a digital decoder on Linux.
  * It is one of the few decoders that support FLEX and POCSAG, two common protocols for pagers.
* I am running [macOS Big Sur 11.1](https://developer.apple.com/documentation/macos-release-notes/macos-big-sur-11_1-release-notes) on my machine, and [Raspbian Buster](https://www.raspberrypi.org/blog/buster-the-new-version-of-raspbian/) on the RPi. All Linux software were installed on macOS through [MacPorts](https://www.macports.org/).

## Methods

To intercept and decode pages, open Gqrx and tune it to the chosen frequency, adjusting the gain and squelch settings as needed. Then click "UDP" to stream the audio over UDP to a remote host.

Listen to the UDP data (port 7355), resample the raw audio from 48 kHz to 22.05 kHz, then try to decode it using several protocols.
```
nc -lu 7355 \
| sox -t raw -esigned-integer -b16 -r 48000 - -esigned-integer -b16 -r 22050 -t raw - \
| multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -a FLEX -
```
The command is from the [Gqrx docs](https://gqrx.dk/doc/streaming-audio-over-udp). Protocols can be added or removed using the `-a` flag in `multimon-ng`. 

Longer messages are often fragmented and sent over several pages. This is not an issue for practical use—each pager receives only those pages intended for it—but, because we see all pages on a frequency, these fragments can arrive interrupted by other messages. We can reassemble these fragments by concatenating all the pages meant for a capcode and received in a certain timeframe.

Redirect the output to [collect.py](collect.py) to reassemble the message fragments in real time.
```
nc -lu 7355 \
| sox -t raw -esigned-integer -b16 -r 48000 - -esigned-integer -b16 -r 22050 -t raw - \
| multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -a FLEX - \
| ./collect.py
```

## Frequencies

All frequencies were tested from Durham, N.C.
* 929.577 MHz: Hospital services (FLEX)

## Readings

* Signal Identification Guide entries for [FLEX](https://www.sigidwiki.com/wiki/FLEX) and [POCSAG](https://www.sigidwiki.com/wiki/POCSAG), which can help you identify a frequency's protocol by its sound and waterfall.
* "[Motorola FLEX / P2000 decoding](http://jelmerbruijn.nl/motorola-flex-p2000-decoding/)," by Jelmer Brujin (2014)
  * Overview of FLEX's implementation, and a project to decode pages in the Dutch P2000 paging network.
* "[FLEX-TD Radio Paging System ARIB Standard](http://www.arib.or.jp/english/html/overview/doc/1-STD-43_A-E1.pdf)," by the Association of Radio Industries and Businesses (1996)
  * Called the "gold standard for FLEX implementations" by Johnston.
* "[Paging system design issues and overview of common paging protocols](https://user.eng.umd.edu/~leandros/papers/pagsys.pdf)," by Yianni Michalas and Leandros Tassiulas (1998)
* "[Motorola FLEX protocol references](https://embeddedartistry.com/blog/2019/09/16/motorola-flex-protocol-references/)," by Phillip Johnston in Embedded Artistry (2019)
  * A collection of additional resources about FLEX.
