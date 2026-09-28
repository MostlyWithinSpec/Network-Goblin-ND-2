# Build the JLCPCB fab package into ..\export
import pcbnew, subprocess, os, shutil, csv, zipfile, glob
P = r"C:\path\to\ND2\tdr-dongle"
PCB = P + r"\tdr-dongle.kicad_pcb"
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
EX = P + r"\export"; G = EX + r"\gerbers"
if os.path.isdir(EX): shutil.rmtree(EX)
os.makedirs(G)
# origin = board lower-left corner (drill/aux origin)
b = pcbnew.LoadBoard(PCB)
b.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I(pcbnew.FromMM(100), pcbnew.FromMM(130)))
pcbnew.SaveBoard(PCB, b)
def run(args):
    r = subprocess.run([CLI] + args, capture_output=True, text=True)
    print(" ".join(args[:3]), "->", r.returncode, (r.stdout + r.stderr).strip()[-400:], flush=True)
layers = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
run(["pcb", "export", "gerbers", "-l", layers, "--subtract-soldermask", "--use-drill-file-origin", "-o", G + "\\", PCB])
run(["pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm", "--excellon-separate-th",
     "--drill-origin", "plot", "--generate-map", "--map-format", "gerberx2", "-o", G + "\\", PCB])
zp = EX + r"\tdr-dongle_gerbers_JLC.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(G)):
        z.write(os.path.join(G, f), f)
print("zip:", sorted(os.listdir(G)))
# CPL
raw = EX + r"\_pos_raw.csv"
run(["pcb", "export", "pos", "--side", "both", "--format", "csv", "--units", "mm", "--use-drill-file-origin",
     "--exclude-dnp", "-o", raw, PCB])
rows = list(csv.DictReader(open(raw)))
with open(EX + r"\tdr-dongle_CPL_JLC.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in rows:
        w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm", "Top" if r["Side"] == "top" else "Bottom", r["Rot"]])
os.remove(raw)
print("CPL rows:", len(rows), sorted(set(r["Side"] for r in rows)))
shutil.copy(P + r"\bom_jlcpcb.csv", EX + r"\tdr-dongle_BOM_JLC.csv")
# review docs
run(["pcb", "export", "pdf", "-l", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,Edge.Cuts", "--mode-multipage",
     "--include-border-title", "-o", EX + r"\tdr-dongle_layers.pdf", PCB])
run(["pcb", "export", "step", "--subst-models", "-f", "-o", EX + r"\tdr-dongle.step", PCB])
shutil.copy(P + r"\tdr-dongle.pdf", EX + r"\tdr-dongle_schematic.pdf")
print("export:", os.listdir(EX))
