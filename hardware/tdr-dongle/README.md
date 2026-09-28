# ND-2 TDR Proof Dongle — Rev A

![Top copper](../../docs/images/tdr-dongle-top.png)

A small USB 3 → Gigabit Ethernet dongle that is just the ND-2 test-port circuit:
**Microchip LAN7801** (USB 3 to RGMII MAC) + **Marvell 88E1512** (GbE PHY with VCT/TDR) + HanRun 1G magjack.
Plug it into a Pi 5 / CM5 IO board and prove `ethtool --cable-test` / `--cable-test-tdr` before building the CM5 carrier.

**Status:** ERC and DRC clean, schematic/PCB parity clean, ordered from JLCPCB in Sept 2026. **Not yet tested on real hardware.** Bring-up plan: [docs/bring-up.md](../../docs/bring-up.md).

## Files

| File | What it is |
| --- | --- |
| `tdr-dongle.kicad_sch` | Schematic (KiCad 10, one A2 sheet, label-based wiring) |
| `ND2.kicad_sym` + `sym-lib-table` | Project symbols: `ND2:LAN7801`, `ND2:88E1512`, `ND2:HR911130C` |
| `ND2.pretty` + `fp-lib-table` | Project footprints (from LCSC/EasyEDA, cleaned up — see below) |
| `bom_jlcpcb.csv` | Grouped BOM in JLCPCB format (Comment, Designator, Footprint, LCSC Part #) |
| `bom.csv` | One line per part with MPN + LCSC |
| `netlist_report.txt` | Every net and the pins on it |
| `tdr-dongle.kicad_pcb` | PCB: 70 x 30 mm, 4-layer |
| `tdr-dongle.kicad_pro` | KiCad project (design rules, net classes) |
| `tdr-dongle.net` | KiCad netlist export |
| `fab/` | Fabrication package: Gerber zip, JLC BOM + CPL, layer PDF, schematic PDF, STEP, renders |
| `scripts/` | Python scripts that generated the schematic and PCB (see [scripts/README.md](scripts/README.md)) |

## Parts (LCSC, checked 2026-09-25)

| Ref | Part | LCSC | Footprint | Notes |
| --- | --- | --- | --- | --- |
| U1 | LAN7801-I/9JX | C633491 | ND2:LAN7801_QFN-64-1EP_9x9mm_P0.5mm_EP6.1mm | Only ~13 in stock at LCSC |
| U2 | 88E1512-A0-NNP2C000 | C845579 | ND2:88E1512_QFN-56-1EP_8x8mm_P0.5mm_EP4.4mm | Only ~13 in stock at LCSC |
| U3 | TLV62569DBVR | C141836 | SOT-23-5 | 3V3 buck |
| U4 | 93AA66/SN | C615340 | SOIC-8 | ORG pin (6) tied to GND = 512 x 8 |
| U5 | TPD4EUSB30DQAR | C90627 | USON-10 | USB 3 ESD |
| U6 | PRTR5V0U2X,215 | C12333 | SOT-143 | USB 2 ESD |
| J1 | HC-USB3.0-C26 (USB 3 Type-A plug, SMD) | C7501854 | ND2:USB3_A_Plug_HongCheng_HC-USB3.0-C26 | Flash-drive style plug at the board edge |
| J2 | HanRun HR911130C (1G magjack, 2 LEDs) | C50933 | ND2:RJ45_HanRun_HR911130C_Horizontal | Replaces the Pulse JK0654219NL (0 stock) |
| Y1, Y2 | X322525MOB4SI 25 MHz, CL 12 pF | C9006 | Crystal_SMD_3225-4Pin | Load caps changed to 15 pF |
| L1 | SMNR4020-2.2UH (3.4 A) | C135262 | ND2:L_4.0x4.0mm_SMNR4020 | Buck inductor |
| L2 | SMNR3015-3R3MT (1.32 A) | C135239 | ND2:L_3.0x3.0mm_SMNR3015 | LAN7801 1V2 switcher |
| FB1 | MPZ2012S601AT000 (600 Ω, 2 A) | C21519 | L_0805 | VBUS filter |
| Caps | 100 nF C1525 · 1 µF C52923 · 220 nF C16772 · 15 pF C1548 (0402) · 10 µF C15850 · 22 µF C45783 (0805) | | | |
| Resistors (0402, UNI-ROYAL) | 22R C25092 · 330R C25104 · 0R C17168 · 1.5k C25867 · 2k C4109 · 4.99k C25903 · 10k C25744 · 12k C25752 · 100k C25741 · 453k C27009 | | | |

## Changes from the first draft

- **Magjack → HanRun HR911130C.** The Pulse part had no stock. The HR911130C has one **common** center tap (pin 1 → one 100 nF to GND) and an internal Bob-Smith termination on pin 10 (tied to GND). LEDs: 11/12 green (anode/cathode), 14/13 yellow (anode/cathode).
- **EEPROM → 93AA66/SN** (the x8-only 93AA66A wasn't stocked in SOIC). ORG pin tied low selects 512 x 8.
- **Crystals → 12 pF load** (YXC, 70k in stock); load caps now 15 pF.
- **Real footprints** for U1, U2, J1, J2, L1, L2, taken from LCSC/EasyEDA and fixed up:
  - LAN7801 pads resized to Microchip's recommended land pattern (0.30 × 0.85 mm pads, 6.1 mm exposed pad), plus 5 × 5 thermal vias (0.33 mm) and a split paste stencil.
  - 88E1512 exposed pad 4.4 mm (datasheet D2/E2 = 4.37 mm), 3 × 3 thermal vias numbered to the pad, split paste.
  - HR911130C / USB plug pads renumbered to match the symbols; the RJ45 plastic posts made non-plated.

## Known issues and Rev B ideas

1. **Stock on U1 / U2** — about 13 of each at LCSC right now. Enough for a few prototypes; for more, JLCPCB global sourcing or Mouser/Digi-Key.
2. **J1 plug** hangs over the board edge and was left off the JLC assembly (hand-soldered). Rev B: USB-C receptacle + cable.
3. RGMII series resistors (22 Ω) are a starting value; tune after the first boards.
4. Optional: low-capacitance TVS on the MDI pairs, test points on RGMII/MDIO.

## Bring-up plan

1. Power only: check +5V, +3V3, LAN_1V2, LAN_2V5, PHY_1V8, PHY_1V0.
2. Plug into a Pi 5: `lsusb` should show 0424:7801. Program the EEPROM with MAC + HW_CFG (hybrid RGMII delay, CLK125_EN).
3. `dmesg` should show lan78xx attaching the Marvell 88E1510-family PHY at address 0.
4. Link test: clean 1 Gb/s link, iperf3, watch for CRC errors (wrong RGMII delay).
5. TDR: `ethtool --cable-test ethX` and `ethtool --cable-test-tdr ethX` on known cables (open, short, known lengths).

## PCB and fab package (Rev A)

- Board: 70 x 30 mm, 4-layer 1.6 mm (JLC04161H-7628). F.Cu signals, In1 = GND plane, In2 = +3V3 plane, B.Cu signals.
- Rules: 0.1 mm min track (Freerouting necks to ~0.11 at the QFN pins), 0.127 mm clearance, 0.6/0.3 mm vias.
- Routing: plane fan-out by script (scripts/fanout.py), the rest by Freerouting 2.4.1, and 2 nets fixed by hand (scripts/fix_last2.py).
- DRC: 0 errors, 0 warnings, 0 unconnected, schematic parity clean (KiCad 10.0.5).

`fab/` holds:
- `tdr-dongle_gerbers_JLC.zip`: Gerbers + Excellon drills. Upload this to JLCPCB and pick 4 layers, 1.6 mm, JLC04161H-7628.
- `tdr-dongle_BOM_JLC.csv`: the BOM (R7 is DNP and left out).
- `tdr-dongle_CPL_JLC.csv`: pick and place (89 parts, all top side, origin at the board's lower-left corner).
- `tdr-dongle_layers.pdf`, `tdr-dongle_schematic.pdf`, `tdr-dongle.step`, and top/bottom renders for review.

Caveats:
- USB3 and MDI pairs were autorouted. They are **not** length-matched or impedance-controlled. That is fine for a proof dongle but not final.
- Check part rotations in JLC's CPL preview, especially J1, J2, U1, U2 and the crystals.
- LAN7801 and 88E1512 LCSC stock was low (~13 each) when checked.
