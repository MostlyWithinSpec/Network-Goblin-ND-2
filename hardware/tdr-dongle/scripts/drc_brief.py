import json, collections, subprocess, sys, os
P = r"C:\path\to\ND2\tdr-dongle"
pcb = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else P + r"\tdr-dongle.kicad_pcb"
cli = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
out = P + r"\drc.json"
if os.path.exists(out): os.remove(out)
r = subprocess.run([cli, "pcb", "drc", "--format", "json", "--severity-all", "--schematic-parity", "--refill-zones", "-o", out, pcb], capture_output=True, text=True)
d = json.load(open(out))
v = d["violations"]
print(collections.Counter((x["type"], x["severity"]) for x in v), "unconnected", len(d["unconnected_items"]), "parity", len(d["schematic_parity"]))
seen = collections.Counter()
for x in v:
    seen[x["type"]] += 1
    if seen[x["type"]] > 6: continue
    print(x["type"], "|", x["description"][:80], "|", [(i["description"][:50], round(i["pos"]["x"] - 100, 2), round(i["pos"]["y"] - 100, 2)) for i in x["items"]])
for x in d["unconnected_items"]:
    print("UNCONN", [(i["description"][:50], round(i["pos"]["x"] - 100, 2), round(i["pos"]["y"] - 100, 2)) for i in x["items"]])
