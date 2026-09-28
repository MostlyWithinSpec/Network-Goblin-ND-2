# plot region of F.Cu/B.Cu to svg with a viewbox crop (x0 y0 x1 y1 in board mm)
import subprocess, sys, re
cli = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
P = r"C:\path\to\ND2\tdr-dongle"
pcb = P + r"\tdr-dongle.kicad_pcb"
layers = sys.argv[1]; name = sys.argv[2]
r = subprocess.run([cli, "pcb", "export", "svg", "--layers", layers, "--mode-single", "--exclude-drawing-sheet",
                    "-o", P + r"\_%s.svg" % name, pcb], capture_output=True, text=True)
print(r.returncode, r.stderr[-200:])
