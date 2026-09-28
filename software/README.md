# ND-2 software

| Folder | What it is | Status |
|---|---|---|
| [`cabletest/`](cabletest/) | `nd2-cabletest.py`: per-pair cable test summary using `ethtool --cable-test` | Written, waiting for hardware |
| *(planned)* `eeprom/` | LAN7801 EEPROM image + script (MAC address, RGMII config) | After bring-up |
| *(planned)* `gui/` | Touch UI for the ND-2 handheld (LVGL on Linux DRM) | Stage 4 |

## nd2-cabletest

```bash
sudo apt install ethtool
sudo python3 software/cabletest/nd2-cabletest.py eth1
```

Example output (illustrative):

```
Cable test on eth1

Pair  Pins            Result                    Fault at
A     1-2 (orange)    OPEN                      12.4 m
B     3-6 (green)     OPEN                      12.6 m
C     4-5 (blue)      OPEN                      12.3 m
D     7-8 (brown)     OPEN                      12.5 m

All pairs open at about 12.5 m: that's probably the cable length (far end unplugged), not a fault.
```

It works with any Linux NIC whose PHY driver supports cable test, not just the ND-2 dongle.
