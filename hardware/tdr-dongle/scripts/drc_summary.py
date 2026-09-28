import subprocess, json, os, collections, sys
proj = r"C:\path\to\ND2\tdr-dongle"
cli = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
pcb = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else os.path.join(proj, "tdr-dongle.kicad_pcb")
skip = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else set()
out = os.path.join(proj, "drc.json")
r = subprocess.run([cli, "pcb", "drc", "--format", "json", "--severity-all", "--schematic-parity", "-o", out, pcb],
                   capture_output=True, text=True)
print(r.returncode, r.stdout.strip()[-300:], r.stderr.strip()[-500:])
if os.path.exists(out) and os.path.getmtime(out) < __import__("time").time() - 60: print("STALE REPORT"); sys.exit(1)
d = json.load(open(out))
v = d.get("violations", [])
print("violations:", collections.Counter((x["type"], x["severity"]) for x in v))
print("unconnected:", len(d.get("unconnected_items", [])), " parity:", len(d.get("schematic_parity", [])))
for x in v:
    if x["type"] in skip:
        continue
    print(x["type"], "|", x["description"][:70], "|",
          [(i["description"][:55], round(i["pos"]["x"] - 100, 2), round(i["pos"]["y"] - 100, 2)) for i in x["items"]])
for x in d.get("schematic_parity", [])[:20]:
    print("PARITY", x["description"][:100], [i["description"][:60] for i in x["items"]])
