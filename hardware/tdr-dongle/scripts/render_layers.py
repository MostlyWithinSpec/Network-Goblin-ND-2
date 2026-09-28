import subprocess, sys
cli = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
P = r"C:\path\to\ND2\tdr-dongle"
pcb = sys.argv[1] if len(sys.argv) > 1 else P + r"\tdr-dongle.kicad_pcb"
for name, layers in [("top", "F.Cu,F.Fab,Edge.Cuts"), ("bot", "B.Cu,F.Fab,Edge.Cuts")]:
    r = subprocess.run([cli, "pcb", "export", "svg", "--layers", layers, "--mode-single", "--fit-page-to-board",
                        "--exclude-drawing-sheet", "-o", P + r"\_%s.svg" % name, pcb], capture_output=True, text=True)
    print(name, r.returncode, r.stderr[-200:])
