# TDR dongle bring-up (Rev A)

A careful first power-on for the Rev A boards. Work top to bottom and stop at the first thing that looks wrong.

You'll need: a multimeter, a current-limited USB supply or USB power meter, a Pi 5 (or any Linux machine with USB 3), and a few known Ethernet cables (good, one with an open pair, one with a short, known lengths).

## 0. Before soldering the connectors

JLCPCB assembles every SMD part. J1 (USB 3 plug) and J2 (RJ45 magjack) are hand-soldered.

- Inspect U1 (LAN7801) and U2 (88E1512) under magnification: no bridges on the 0.5 mm pins, parts square to their pads.
- Check pin 1 on U1, U2, U3 (buck) and U4 (EEPROM) against the silkscreen dot.
- Solder J2 (RJ45) first, then J1 (USB plug). J1's pins must sit flat on the 9 pads while its two shield legs drop into the slots.

## 1. Resistance checks (unpowered)

Measure to GND. None of these should be a dead short (under about 10 Ω):

| Net | Where to probe | Expect |
|---|---|---|
| VBUS / +5V | J1 VBUS pin, C1 | > 1 kΩ |
| +3V3 | C21, any 100 nF cap | > 100 Ω |
| LAN_1V2 | L2 output side | > 10 Ω (low-ish is normal for a core rail) |
| PHY rails | C44–C50 | not shorted |

## 2. First power

Use a current-limited supply (500 mA limit) or a USB power meter on a laptop/Pi port.

| Rail | Expected | Notes |
|---|---|---|
| +5V (VBUS) | 4.75–5.25 V | from the host |
| +3V3 | 3.25–3.35 V | TLV62569 buck (U3) |
| LAN_1V2 | ~1.2 V | LAN7801 internal switcher + L2 |
| LAN_2V5 | ~2.5 V | LAN7801 internal regulator |
| PHY_1V8 / PHY_1V0 | ~1.8 V / ~1.0 V | 88E1512 internal regulators |

Idle current should be a few hundred mA at most. If it's much higher, or anything gets hot, unplug and look for shorts.

## 3. USB enumeration

On the Pi 5:

```bash
lsusb                  # expect 0424:7801 (Microchip LAN7801)
dmesg | grep -i lan78  # lan78xx should bind and create an ethX interface
dmesg | grep -i phy    # expect a Marvell 88E1510-family PHY at MDIO address 0
```

- **No USB device:** check the 25 MHz crystal Y1, the VBUS path through FB1, and J1 soldering.
- **Shows as USB 2 only (480M in `lsusb -t`):** the USB 3 SuperSpeed pairs through J1 or U5 have a problem.

## 4. EEPROM (MAC address + RGMII config)

U4 (93AA66, 512 x 8) holds the LAN7801 config: MAC address, and settings that affect the RGMII clock and delays. A blank EEPROM leaves the driver on defaults with a random MAC, which is fine for first tests.

- Read it: `sudo ethtool -e ethX`
- Programming uses `ethtool -E ethX magic 0x78A5 offset <n> value <v>`. The exact byte layout is in the LAN7801 datasheet's EEPROM section. **TODO:** add a verified image and script to `software/` once tested on real boards.

## 5. Link test

```bash
sudo ip link set ethX up
ethtool ethX            # expect Speed: 1000Mb/s, Duplex: Full, Link detected: yes
iperf3 -c <server> -B <ethX-ip>
ip -s link show ethX    # RX errors / CRC should stay at 0
```

CRC errors or no traffic at 1000 Mb/s (while 100 Mb/s works) almost always means an **RGMII delay mismatch**. Try in this order:

1. PHY-side delays via the driver's phy-mode (`rgmii-id` / `rgmii-rxid` / `rgmii-txid`)
2. LAN7801-side delays via EEPROM
3. Check R9–R20 (22 Ω RGMII series resistors) are fitted and correct

## 6. Cable test (the point of all this)

Always unplug the far end of the cable first.

```bash
sudo ethtool --cable-test ethX       # per-pair status + fault distance
sudo ethtool --cable-test-tdr ethX   # raw TDR amplitude vs distance
```

Record results for:

| Cable | Expected | Result |
|---|---|---|
| 2 m known-good patch, far end open | all pairs "open" at ~2 m | |
| 10 m / 30 m known lengths, far end open | distance within about 1 m | |
| Cable with one pair cut | that pair "open" at cut distance | |
| Cable with a shorted pair | that pair "short" | |
| Good cable into a live switch | expect "unknown" or odd results (link partner) | |

Post results as an issue using the *Bring-up report* template.
