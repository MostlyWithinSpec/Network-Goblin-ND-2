# ND-2 roadmap

The plan is to prove the risky part first (the TDR test port), then build outward.

## Stage 1: TDR proof dongle, Rev A *(in progress)*

LAN7801 + 88E1512 + magjack on a small 4-layer USB 3 dongle.

- [x] Schematic (ERC clean), LCSC parts, footprints
- [x] PCB layout and routing (DRC clean, schematic parity clean)
- [x] Fab package (Gerbers, BOM, CPL) and JLCPCB order
- [ ] Boards arrive, hand-solder J1 (USB plug) and J2 (RJ45)
- [ ] Bring-up: power rails, USB enumeration, EEPROM, link ([bring-up.md](bring-up.md))
- [ ] Prove `ethtool --cable-test` and `--cable-test-tdr` on known-good and known-bad cables
- [ ] Write up results: accuracy vs. real cable lengths, open/short detection per pair

**Exit criteria:** a stable 1 Gb/s link with no CRC errors, and cable-test results that match reality on a set of test cables.

## Stage 2: TDR dongle, Rev B (a product in its own right)

If Rev A works, the dongle is already useful on its own: plug it into any Pi 5 or Linux laptop and you have a TDR cable tester. Rev B makes it something people can build or buy:

- USB-C receptacle + cable instead of the hard USB-A plug
- All-SMD connectors so the whole board fits JLCPCB Economic assembly
- Swap passives to JLC "basic" parts to cut assembly fees
- Length-matched, impedance-controlled USB 3 and MDI pairs
- Low-capacitance TVS on the MDI pairs
- 3D-printed case
- Packaged `nd2-cabletest` software (Debian package / pip)
- Possible small batches on Tindie

## Stage 3: ND-2 carrier board

The full handheld from [spec.md](spec.md):

- CM5 carrier with the proven test-port circuit copied in
- CM5 native gigabit port as the uplink
- USB 3 hub + 2x USB-A, M.2 2230, microSD, HDMI
- DSI touchscreen
- USB-C PD input, 2S Li-ion with BQ25798 charger and fuel gauge
- Case

## Stage 4: software

- Touch GUI (LVGL on Linux DRM, sharing its look with ND-1)
- Modes: cable test, link/speed test, capture, inline tap (bridge), iperf3, scan
- Report export (HTML/PDF) for cable-test results

## Ideas parked for later

- Remote wiremap unit, for split-pair detection
- Relay-based fail-open bypass for the inline tap
- PoE detection / measurement on the test port
