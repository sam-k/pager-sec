# pager-sec

### Timeline

:checkered_flag: This independent research project was **started** on Jan. 27, 2021, under the guidance of [Dr. Tyler Bletsch](http://people.duke.edu/~tkb13/) at Duke University.

:construction: Per guidance from Duke University’s [Office of Counsel](https://ogc.duke.edu/), the interception and decoding steps of this project were **suspended** on March 26, 2021.

:white_check_mark: This project was **finished** on April 21, 2021.



### Table of Contents
1. [Motivation](#motivation)
2. [Materials](#materials)
3. [Part 1: Hacking Pagers](#part-1-hacking-pagers)
    1. [Finding Frequencies](#finding-frequencies)
    2. [Interception](#interception)
    3. [Alternative: Generating Data](#alternative-generating-data)
    4. [Processing](#processing)
4. [Part 2: Fixing Pagers](#part-2-fixing-pagers)
5. [Conclusion](#conclusion)
6. [Poster](#poster)
7. [Additional Readings](#additional-readings)



## Motivation

Though largely replaced by smartphones today, pagers remain extremely common in niche fields, such as hospitals, where pagers are favored for their low cost, long battery life, wide range and reliable connectivity—crucial in a setting where many walls are shielded to block X-ray radiation. An estimated [80% of all U.S. clinicians](https://www.journalofhospitalmedicine.com/jhospmed/article/141692/hospital-medicine/hospital-based-clinicians-use-technology-patient-care) still carry pagers, not to mention the nurses, paramedics and other health-care personnel who also rely on pagers.

However, most pagers lack even the most basic security. Most data is transmitted unencrypted despite carrying, in many cases, protected health information (PHI)—including patient names, medical histories and test results, all in real time. This poses significant risk to patient confidentiality, especially when the pages contain information about patient locations or stigmatized illnesses. It may even violate the [HIPAA Security Rule](https://www.law.cornell.edu/cfr/text/45/164.306). Still, it remains common practice in many hospitals.

In this project, I illustrate this **dangerous yet neglected security flaw** by:

1. Demonstrating the ease of intercepting and decoding pages; then
2. Building a simple proof of concept for pager security.



## Materials

This project uses the following hardware:

- [**SDR**](https://en.wikipedia.org/wiki/Software-defined_radio) with antenna, to intercept pages. I use the DVB-T+DAB+FM SDR, a USB 2.0 dongle that is available for cheap ($15–25) online.
    - My SDR is based on the Realtek RTL2832U chipset and the Rafael Micro R820T tuner.
    - My SDR supports frequencies from 24 MHz to 1.766 GHz. You can check your SDR’s range based on its tuner on the [rtl-sdr wiki](https://osmocom.org/projects/rtl-sdr/wiki/Rtl-sdr).
- [**Arduino Nano**](https://store.arduino.cc/usa/arduino-nano), to build the proof of concept. This and other Arduino models are available online.
    - My Arduino uses the ATmega328P microcontroller.

This project uses the following software stack:

- [**Ncat**](https://nmap.org/ncat/) 7.80, a networking utility for reading and writing data across networks.
- [**Gqrx**](https://gqrx.dk/) 2.14.4, an open-source SDR receiver on Linux.
    - [Dependencies](https://ports.macports.org/port/gqrx/summary): gnuradio, gr-osmosdr, portaudio, qt5-qtbase, qt5-qtsvg, volk (and their dependencies)
- [**SoX**](http://sox.sourceforge.net/) 14.4.2, a cross-platform tool for audio processing.
    - [Dependencies](https://ports.macports.org/port/sox/summary): flac, lame, libiconv, libid3tag, libmad, libmagic, libogg, libopus, libpng, libsndfile, libvorbis, opusfile, twolame, wavpack, zlib (and their dependencies)
- [**multimon-ng**](https://github.com/EliasOenal/multimon-ng) 1.1.8, a digital decoder on Linux.
    - It is one of the few decoders that support FLEX and POCSAG, two common paging protocols.
- [**Crypto**](https://rweather.github.io/arduinolibs/crypto.html) 0.2.0, a cryptography library for Arduino.
- I am running [macOS Big Sur 11.1](https://developer.apple.com/documentation/macos-release-notes/macos-big-sur-11_1-release-notes) on my machine. All Linux software were installed on macOS through [MacPorts](https://www.macports.org/).



## Part 1: Hacking Pagers

### Finding Frequencies

Most U.S. pagers use either [**FLEX**](https://www.sigidwiki.com/wiki/FLEX) or [**POCSAG**](https://www.sigidwiki.com/wiki/POCSAG) as their paging protocols. You can identify a pager frequency’s protocol by its characteristic sounds and waterfall shape, which can be found in its [Signal Identification Guide](https://www.sigidwiki.com/wiki/Signal_Identification_Guide) entry. The wiki entries also contain each protocol’s usual frequency ranges.

All frequencies were tested from Durham, N.C., United States. Only 929.577 MHz could be positively identified, as the interception and decoding of pages were suspended afterward. The other frequencies are only suspected to follow the FLEX protocol, based on their sound and waterfalls.

- 929.142 MHz: ??? (FLEX)
- 929.577 MHz: Hospital services in North and South Carolina (FLEX)
- 931.161 MHz: ??? (FLEX)

I used the FLEX frequency **929.577 MHz**. Fortunately, the frequency had relatively busy traffic, with roughly about 50 pages a minute.

<p align="center"><img width="700" src="https://i.imgur.com/via8jLN.png"></p>


### Interception

To intercept and decode pages, open **Gqrx** and tune it to the chosen frequency, adjusting the gain and squelch settings as needed. Then click "UDP" to stream the audio over UDP to a remote host.

<p align="center"><img width="400" src="https://i.imgur.com/C9sVgwN.png"></p>

Listen to the UDP data (port 7355), resample the raw audio from 48 kHz to 22.05 kHz, then try to decode it using several common paging protocols. This command is adapted from that in the [Gqrx docs](https://gqrx.dk/doc/streaming-audio-over-udp). Protocols can be added or removed using the `-a` flag in **multimon-ng**, and we can display the timestamp for each message with the `--timestamp` flag.

```
ncat -lu 7355 \
| sox -t raw -esigned-integer -b16 -r 48000 - -esigned-integer -b16 -r 22050 -t raw - \
| multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -a FLEX -
```

<p align="center"><img width="700" src="https://i.imgur.com/iEzyeCq.png"></p>

From what I’ve observed, the messages seem to fall into one of several formats:

1. For binary pages, a series of nine 8-digit hexadecimal numbers.
2. For tone/numeric pages, a number or an extension to call.
3. For alphanumeric pages,
    1. A short message that appears manually typed.
    2. A long message with a structured header (From/Subject fields), often followed by a confidentiality notice.
    3. An automated alert.
    4. A long series of base-64 characters, terminating in four (or fewer) A’s.

For each decoded FLEX message, multimon-ng prints a lot of associated metadata. I deciphered its syntax using the [ARIB Standard](http://www.arib.or.jp/english/html/overview/doc/1-STD-43_A-E1.pdf) for FLEX and the relevant [source code](https://github.com/EliasOenal/multimon-ng/blob/master/demod_flex.c). Here is a typical (but not real) message that you might see:

```
FLEX|3200/4|08.103.C|0004783821|LS|5|ALN|3.0.K|PT IN 413 DOE, JANE 37F DILAUDID 0.5MG 1HR AGO STILL C/O PAIN, INCREASE DOSE?
```

1. Protocol name: FLEX
2. Transmission mode
    1. Speed (1600/3200/6400): 3200 bits per second
    2. FSK level (2/4): 4-level
3. Frame information
    1. Cycle number (0 to 14): 8
    2. Frame number (0 to 127): 103
    3. Phase (A for 1600 bps, A/C for 3200 bps, A/B/C/D for 6400 bps): C
4. Capcode, left-padded with zeroes: 4783821
5. Address type
    1. Long/short (L/S): Long
    2. Group/single (G/S): Single
6. Page enum (2 for tone, 3 for numeric, 5 for alphanumeric, 6 for binary): Alphanumeric
7. Page type (TON for tone, NUM for numeric, ALN for alphanumeric, BIN for binary): Alphanumeric
8. (Only for alphanumeric) Message fragment information
    1. Fragment indicator (3 for first fragment, 0,1,2,4,… for next fragments): First fragment
    2. Message continued flag (0 if end of message, 1 if more to follow): End of message
    3. Fragment flag (K if only 1 fragment, F if more to follow, C if last fragment): First and only fragment of message
9. Message: Patient Jane Doe in Rm. 413, a 37-year-old female, was given 0.5 mg of Dilaudid (hydromorphone) 1 hour ago, yet she is still complaining of pain. Should we increase her dose?


### Alternative: Generating Data

If you wish not to intercept real pages, you can also auto-generate artificial data. The script [**generate.py**](generate.py) follows the multimon-ng output format above to generate fake pages.


### Processing

Longer messages are often fragmented and transmitted over several pages. This is not an issue for practical use—each pager receives only those pages intended for it—but, because we see all pages on a frequency, these fragments can arrive interrupted by other messages. We can reassemble these fragments by concatenating all the pages meant for a capcode and received in a certain timeframe.

Redirect the output to [**collect.py**](collect.py) to reassemble the message fragments in real time.

```
ncat -lu 7355 \
| sox -t raw -esigned-integer -b16 -r 48000 - -esigned-integer -b16 -r 22050 -t raw - \
| multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -a FLEX - \
| ./collect.py
```

<p align="center"><img width="700" src="https://i.imgur.com/otHM4YC.png"></p>



## Part 2: Fixing Pagers

Cryptographically, pagers are limited by the following:

- Small memory, which may make computationally or resource-intensive protocols (e.g., [RSA](https://en.wikipedia.org/wiki/RSA_(cryptosystem))) infeasible
    - RSA implementations for the Arduino do exist, but they are far too weak for practical use—one [proof of concept](https://www.sciencedirect.com/science/article/pii/S1877050914009466) uses 8-bit keys, while the NIST recommends at least 2,048-bit keys.
- One-way communication, which make many common encryption protocols (e.g., [Diffie–Hellman](https://en.wikipedia.org/wiki/Diffie–Hellman_key_exchange)) impossible
    - This does mean one-way pagers cannot be used for location-tracking—as [pager advocates](https://www.washingtonpost.com/news/the-switch/wp/2014/08/11/why-one-of-cybersecuritys-thought-leaders-uses-a-pager-instead-of-a-smart-phone/) like to tout—but that is a trivially small benefit in exchange for total lack of data privacy.

To show even limited hardware can support encryption, we modeled pagers with Arduino Nano, which is the smallest Arduino available and has even less memory than pagers. It has only 32 KB of flash memory and 2 KB of SRAM, compared to the Motorola Advisor pager, which has 8×32 KB of SRAM.

I also used [**ChaCha20–Poly1305**](https://blog.cloudflare.com/it-takes-two-to-chacha-poly/), a lightweight symmetric-key protocol for authenticated encryption with additional data (AEAD). The stream cipher ChaCha, with 20 rounds of encryption, is as secure as the more popular [AES](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) while offering better performance. The message authentication code (MAC) protocol Poly1305 allows verifying the integrity of a message—i.e., it detects when the contents of a message have been changed. The implementation details are as follows:

- Each pager is assigned a unique, randomly generated pre-shared key (PSK), which is also known to the central paging system. In this way, if the PSK is somehow compromised, only communications to that one pager are compromised.
- The frame information of a message is used as the “additional data” (AD), which is unencrypted and used for authentication only. By checking that the frame information, incremented with every message, is as expected, we can prevent [replay attacks](https://en.wikipedia.org/wiki/Replay_attack), where an attacker simply records and replays an encrypted message.
- This implementation uses 256-bit keys, 96-bit initialization vectors (IVs) and 128-bit authentication tags.
- Due to memory constraints, this implementation is limited to 300-byte messages and 32-byte ADs.

This proof of concept does not require any changes in hardware, since modifying or replacing pagers can be costly for hospitals. Instead, it is designed to be only a software upgrade.

I simulated the paging system with the Python script [**encrypt.py**](encrypt.py), which encrypts a message with a hardcoded PSK. And I simulated the pager with the Arduino script [**Decrypt.ino**](Decrypt/Decrypt.ino).

<p align="center"><img width="600" src="https://i.imgur.com/08TtVT2.png"></p>



## Conclusion

Pagers used by hospitals are **easy to attack**. With cheap hardware and free software, anyone can intercept pages to access sensitive data.

Pagers are also **easy to defend**. Even limited hardware can support authenticated encryption for one-way communication. After all the decades in which hospitals have been using pagers, there is little excuse for this huge lapse in security.



## Poster

<p align="center"><img width="100%" src="https://i.imgur.com/d9J7HXy.png"></p>



## Additional Readings

- Signal Identification Guide entries for [FLEX](https://www.sigidwiki.com/wiki/FLEX) and [POCSAG](https://www.sigidwiki.com/wiki/POCSAG), which can help you identify a frequency’s protocol by its sound and waterfall.
- “[FLEX-TD Radio Paging System ARIB Standard](http://www.arib.or.jp/english/html/overview/doc/1-STD-43_A-E1.pdf),” by the Association of Radio Industries and Businesses (1996)
  - Called the “gold standard for FLEX implementations” by Johnston.
- “[Motorola FLEX / P2000 decoding](http://jelmerbruijn.nl/motorola-flex-p2000-decoding/),” by Jelmer Brujin (2014)
  - Overview of FLEX’s implementation, and a project to decode pages in the Dutch P2000 paging network.
- “[Paging system design issues and overview of common paging protocols](https://user.eng.umd.edu/~leandros/papers/pagsys.pdf),” by Yianni Michalas and Leandros Tassiulas (1998)
  - A review of common paging protocols, including FLEX, POCSAG and ERMES.
- “[Motorola FLEX protocol references](https://embeddedartistry.com/blog/2019/09/16/motorola-flex-protocol-references/),” by Phillip Johnston in Embedded Artistry (2019)
  - A collection of additional resources about FLEX.
