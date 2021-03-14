# pager-sdr

:construction: Pending review, the interception and decoding steps of this project have been **paused**.

## Motivation

Though largely replaced by smartphones today, pagers remain extremely common in niche fields, such as hospitals, where pagers are favored for their low cost, long battery life, wide range and reliable connectivity—crucial in a setting where many walls are shielded to block X-ray radiation. An estimated [80% of all U.S. clinicians](https://www.journalofhospitalmedicine.com/jhospmed/article/141692/hospital-medicine/hospital-based-clinicians-use-technology-patient-care) still carry pagers, not to mention the nurses, paramedics and other health-care personnel who also rely on pagers.

However, most pagers have zero security. The one-way pagers cannot support end-to-end encryption, and most data is transmitted unencrypted, yet paging communications often include protected health information (PHI)—including patient names, medical histories and test results, all in real time. This poses significant risk to patient confidentiality and may violate the [HIPAA Security Rule](https://www.law.cornell.edu/cfr/text/45/164.306). Still, it remains common practice in many hospitals.

In this project, I demonstrate the security issues in medical pagers by using a software-defined radio (SDR) to intercept pages, parse the messages, and automate the task. I also provide security recommendations to remedy these issues.

## Materials

This project uses the following hardware:
* [**SDR**](https://en.wikipedia.org/wiki/Software-defined_radio) with antenna, to intercept pages. I use the DVB-T+DAB+FM SDR, a USB 2.0 dongle that is available for cheap ($15–25) online. 
  * My SDR is based on the Realtek RTL2832U chipset and the Rafael Micro R820T tuner.
  * My SDR supports frequencies from 24 MHz to 1.766 GHz. You can check your SDR’s range based on its tuner on the [rtl-sdr wiki](https://osmocom.org/projects/rtl-sdr/wiki/Rtl-sdr).
* [**Raspberry Pi**](https://www.raspberrypi.org/) 3 Model B with 1 GB RAM, to automate the task. This and other RPi models are available online.

This project uses the following software stack:
* [**Gqrx**](https://gqrx.dk/) 2.14.4, an open-source SDR receiver on Linux.
  * [Dependencies](https://ports.macports.org/port/gqrx/summary): gnuradio, gr-osmosdr, portaudio, qt5-qtbase, qt5-qtsvg, volk (and their dependencies)
* [**SoX**](http://sox.sourceforge.net/) 14.4.2, a cross-platform tool for audio processing.
  * [Dependencies](https://ports.macports.org/port/sox/summary): flac, lame, libiconv, libid3tag, libmad, libmagic, libogg, libopus, libpng, libsndfile, libvorbis, opusfile, twolame, wavpack, zlib (and their dependencies)
* [**multimon-ng**](https://github.com/EliasOenal/multimon-ng) 1.1.8, a digital decoder on Linux.
  * It is one of the few decoders that support FLEX and POCSAG, two common paging protocols.
* I am running [macOS Big Sur 11.1](https://developer.apple.com/documentation/macos-release-notes/macos-big-sur-11_1-release-notes) on my machine, and [Raspbian Buster](https://www.raspberrypi.org/blog/buster-the-new-version-of-raspbian/) on the RPi. All Linux software were installed on macOS through [MacPorts](https://www.macports.org/).

## Methods

### Interception

To intercept and decode pages, open Gqrx and tune it to the chosen frequency, adjusting the gain and squelch settings as needed. Then click "UDP" to stream the audio over UDP to a remote host.

<p align="center"><img width="400" src="https://i.imgur.com/YSquBIJ.png"></p>

Listen to the UDP data (port 7355), resample the raw audio from 48 kHz to 22.05 kHz, then try to decode it using several common paging protocols. This command is adapted from that in the [Gqrx docs](https://gqrx.dk/doc/streaming-audio-over-udp). Protocols can be added or removed using the `-a` flag in `multimon-ng`, and we can display the timestamp for each message with the `--timestamp` flag.
```
nc -lu 7355 \
| sox -t raw -esigned-integer -b16 -r 48000 - -esigned-integer -b16 -r 22050 -t raw - \
| multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -a FLEX -
```

<p align="center"><img width="650" src="https://i.imgur.com/iEzyeCq.png"></p>

From what I’ve observed, the messages seem to fall into one of several formats:
1. For binary pages, a series of nine 8-digit hexadecimal numbers.
2. For tone/numeric pages, a number or an extension to call.
3. For alphanumeric pages,
   * A short message that appears manually typed.
   * A long message with a structured header (From/Subject fields), often followed by a confidentiality notice.
   * An automated alert.
   * A long series of base-64 characters, terminating in four (or fewer) A’s.

For each decoded FLEX message, multimon-ng prints a lot of associated metadata. I deciphered its syntax using the [ARIB Standard](http://www.arib.or.jp/english/html/overview/doc/1-STD-43_A-E1.pdf) for FLEX and the relevant [source code](https://github.com/EliasOenal/multimon-ng/blob/master/demod_flex.c). Here is a typical (but not real) message that you might see:

```
FLEX|3200/4|08.103.C|0004783821|LS|5|ALN|3.0.K|PT IN 413 DOE, JANE 37F AMS 85%RA 61 20 204/66 104 LKN 1315
```

1. Protocol name: FLEX
2. Transmission mode
   * Speed (1600/3200/6400): 3200 bits per second
   * FSK level (2/4): 4-level
3. Frame information
   * Cycle number (0 to 14): 8
   * Frame number (0 to 127): 103
   * Phase (A for 1600 bps, A/C for 3200 bps, A/B/C/D for 6400 bps): C
4. Capcode, left-padded with zeroes: 4783821
5. Address type
   * Long/short (L/S): Long
   * Group/single (G/S): Single
6. Page enum (2 for tone, 3 for numeric, 5 for alphanumeric, 6 for binary): Alphanumeric
7. Page type (TON for tone, NUM for numeric, ALN for alphanumeric, BIN for binary): Alphanumeric
8. (Only for alphanumeric) Message fragment information
   * Fragment indicator (3 for first fragment, 0,1,2,4,… for next fragments): First fragment
   * Message continued flag (0 if end of message, 1 if more to follow): End of message
   * Fragment flag (K if only 1 fragment, F if more to follow, C if last fragment): First and only fragment of message
9. Message: Patient Jane Doe in Rm. 413, a 37-year-old female, has altered mental status. Her blood oxygen saturation is 85% of room air, her pulse is 61 beats per minute, her respiratory rate is 20 breaths per minute, her blood pressure is 204/66, and her temperature is 104 °F. Her last known normal time was 1:15 p.m.

### Alternative: Generating Data

If you wish not to intercept real pages, you can also auto-generate artificial data. The script [generate.py](generate.py) follows the multimon-ng output format above to generate fake pages.

### Processing

Longer messages are often fragmented and transmitted over several pages. This is not an issue for practical use—each pager receives only those pages intended for it—but, because we see all pages on a frequency, these fragments can arrive interrupted by other messages. We can reassemble these fragments by concatenating all the pages meant for a capcode and received in a certain timeframe.

Redirect the output to [collect.py](collect.py) to reassemble the message fragments in real time.
```
nc -lu 7355 \
| sox -t raw -esigned-integer -b16 -r 48000 - -esigned-integer -b16 -r 22050 -t raw - \
| multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -a FLEX - \
| ./collect.py
```

<p align="center"><img width="650" src="https://i.imgur.com/otHM4YC.png"></p>

## Frequencies

All frequencies were tested from Durham, N.C., United States.
* 929.142 MHz: ??? (FLEX)
* 929.577 MHz: Hospital services in North and South Carolina (FLEX)
* 931.161 MHz: ??? (FLEX)

## Readings

* Signal Identification Guide entries for [FLEX](https://www.sigidwiki.com/wiki/FLEX) and [POCSAG](https://www.sigidwiki.com/wiki/POCSAG), which can help you identify a frequency’s protocol by its sound and waterfall.
* “[FLEX-TD Radio Paging System ARIB Standard](http://www.arib.or.jp/english/html/overview/doc/1-STD-43_A-E1.pdf),” by the Association of Radio Industries and Businesses (1996)
  * Called the “gold standard for FLEX implementations” by Johnston.
* “[Motorola FLEX / P2000 decoding](http://jelmerbruijn.nl/motorola-flex-p2000-decoding/),” by Jelmer Brujin (2014)
  * Overview of FLEX’s implementation, and a project to decode pages in the Dutch P2000 paging network.
* “[Paging system design issues and overview of common paging protocols](https://user.eng.umd.edu/~leandros/papers/pagsys.pdf),” by Yianni Michalas and Leandros Tassiulas (1998)
  * A review of common paging protocols, including FLEX, POCSAG and ERMES.
* “[Motorola FLEX protocol references](https://embeddedartistry.com/blog/2019/09/16/motorola-flex-protocol-references/),” by Phillip Johnston in Embedded Artistry (2019)
  * A collection of additional resources about FLEX.
