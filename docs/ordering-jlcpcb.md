# Ordering the TDR dongle from JLCPCB

Files are in [`hardware/tdr-dongle/fab/`](../hardware/tdr-dongle/fab/).

## PCB settings

| Option | Setting | Why |
|---|---|---|
| Gerber upload | `tdr-dongle_gerbers_JLC.zip` | |
| Layers | 4 | GND and +3V3 planes on the inner layers |
| Dimensions | 70 x 30 mm | auto-detected |
| PCB thickness | 1.6 mm | |
| Stackup | JLC04161H-7628, or "Specify Stackup: No" (it's the default) | the board was designed for it |
| Surface finish | HASL (leaded) or ENIG | ENIG is flatter for the 0.5 mm QFNs, but HASL works fine for machine assembly |
| Outer / inner copper | 1 oz / 0.5 oz | |
| Via covering | Plugged | |
| Min via hole / diameter | 0.3 mm / (0.4–0.45 mm) | vias are 0.3 / 0.6 mm |
| Min track | standard | 0.1 mm at the QFN pins, fine for JLC 4-layer |
| Mark on PCB | Remove Mark | |
| Confirm production file | Yes (recommended) | review JLC's processed files before they build |

## Assembly settings

| Option | Setting |
|---|---|
| PCBA type | **Economic**, top side |
| Assembly quantity | **2** (of 5 bare boards), plenty for a proof board |
| BOM | `tdr-dongle_BOM_JLC.csv` |
| CPL | `tdr-dongle_CPL_JLC.csv` |
| Do not place | **J1 (USB plug) and J2 (RJ45)**: through-hole/edge parts push the order to Standard assembly. Hand-solder them. |

In the placement preview, check pin 1 on U1, U2, U3 and U4, and the orientation of Y1, Y2, U5 and U6.

## Hand-soldered parts to buy separately

| Ref | Part | LCSC | Notes |
|---|---|---|---|
| J1 | HC-USB3.0-C26 USB 3 Type-A plug (SMD) | C7501854 | Generic "USB 3.0 A male SMT 9-pin" plugs can work if the 9 pins are **one row at 1.0 mm pitch** and the 2 shield legs are about **11.7 mm** apart |
| J2 | HanRun HR911130C 1G magjack | C50933 | Exact part only; other magjacks don't share its pinout |

## Cost notes (Sept 2026, 5 PCBs / 2 assembled, US shipping)

- The first quote (Standard, 5 assembled, ENIG, connectors placed) was about **$294**.
- Economic, 2 assembled, connectors not placed, HASL: about **$160 + shipping/customs**.
- The biggest costs are the parts themselves (LAN7801 and 88E1512) and the ~$3 loading fee per *extended* part. Rev B will switch passives to JLC basic parts.
