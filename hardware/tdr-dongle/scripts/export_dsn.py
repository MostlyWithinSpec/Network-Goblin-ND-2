import pcbnew, sys
P = r"C:\path\to\ND2\tdr-dongle"
b = pcbnew.LoadBoard(P + r"\tdr-dongle.kicad_pcb")
ok = pcbnew.ExportSpecctraDSN(b, P + r"\route\tdr-dongle.dsn")
print("dsn", ok)
