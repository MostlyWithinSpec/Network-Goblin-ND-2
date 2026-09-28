#!/usr/bin/env python3
"""nd2-cabletest: friendly front end for Linux PHY cable diagnostics.

Runs `ethtool --cable-test` on an interface (e.g. the ND-2 TDR dongle) and prints
a per-pair summary with the fault distance, if any.

Needs: Linux with a PHY driver that supports cable test (Marvell 88E151x does),
ethtool 5.8 or newer, and root (sudo).

Usage:
    sudo ./nd2-cabletest.py eth1
    sudo ./nd2-cabletest.py eth1 --json      # machine-readable output
    sudo ./nd2-cabletest.py eth1 --tdr       # also dump the raw TDR trace

Status: written ahead of the Rev A hardware, not yet tested on a real dongle.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys

PAIRS = {"A": "1-2 (orange)", "B": "3-6 (green)", "C": "4-5 (blue)", "D": "7-8 (brown)"}
FRIENDLY = {
    "OK": "OK",
    "Open Circuit": "OPEN",
    "Short within Pair": "SHORT (within pair)",
    "Short to another pair": "SHORT (to another pair)",
    "Unspecified": "UNKNOWN",
}


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        sys.exit("ethtool not found. Install it (e.g. `sudo apt install ethtool`).")
    return r.returncode, r.stdout, r.stderr


def link_up(iface):
    try:
        with open(f"/sys/class/net/{iface}/carrier") as f:
            return f.read().strip() == "1"
    except OSError:
        return False


def parse_cable_test(text):
    """Parse ethtool's text output into {pair: {"status": str, "fault_m": float|None}}."""
    res = {}
    for line in text.splitlines():
        m = re.match(r"\s*Pair ([A-D]) code (.+?)\s*$", line)
        if m:
            res.setdefault(m.group(1), {"status": m.group(2), "fault_m": None})["status"] = m.group(2)
            continue
        m = re.match(r"\s*Pair ([A-D]), fault length: ([\d.]+)m", line)
        if m:
            res.setdefault(m.group(1), {"status": "?", "fault_m": None})["fault_m"] = float(m.group(2))
    return res


def main():
    ap = argparse.ArgumentParser(description="ND-2 cable test")
    ap.add_argument("iface", help="network interface, e.g. eth1")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a table")
    ap.add_argument("--tdr", action="store_true", help="also print the raw TDR amplitude trace")
    ap.add_argument("--force", action="store_true", help="run even if a link partner is detected")
    a = ap.parse_args()

    if not shutil.which("ethtool"):
        sys.exit("ethtool not found. Install it (e.g. `sudo apt install ethtool`).")
    if link_up(a.iface) and not a.force:
        sys.exit(f"{a.iface} has an active link. Unplug the far end of the cable first "
                 "(results are unreliable with a live link partner), or pass --force.")

    rc, out, err = run(["ethtool", "--cable-test", a.iface])
    if rc != 0:
        sys.exit(f"cable test failed: {err.strip() or out.strip()}\n"
                 "(Does this PHY/driver support cable test? Are you root?)")
    res = parse_cable_test(out)

    if a.json:
        print(json.dumps({"iface": a.iface, "pairs": res}, indent=2))
    else:
        print(f"Cable test on {a.iface}\n")
        print(f"{'Pair':<6}{'Pins':<16}{'Result':<26}Fault at")
        for p in "ABCD":
            r = res.get(p)
            if not r:
                print(f"{p:<6}{PAIRS[p]:<16}{'no data':<26}-")
                continue
            status = FRIENDLY.get(r["status"], r["status"])
            dist = f"{r['fault_m']:.1f} m" if r["fault_m"] is not None else "-"
            print(f"{p:<6}{PAIRS[p]:<16}{status:<26}{dist}")
        opens = [r["fault_m"] for r in res.values() if r["status"] == "Open Circuit" and r["fault_m"]]
        if len(opens) == 4 and max(opens) - min(opens) < 1.5:
            print(f"\nAll pairs open at about {sum(opens) / 4:.1f} m: that's probably the cable length "
                  "(far end unplugged), not a fault.")
        print("\nPair letters follow the PHY's MDI pairs (T568B colours shown). Distances are ±1 m or so.")

    if a.tdr:
        rc, out, err = run(["ethtool", "--cable-test-tdr", a.iface])
        print("\nRaw TDR trace:\n" + (out if rc == 0 else err))


if __name__ == "__main__":
    main()
