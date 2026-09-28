# import the Freerouting session, refill zones, save
import pcbnew, os
P = r"C:\path\to\ND2\tdr-dongle"
R = P + r"\route"
b = pcbnew.LoadBoard(P + r"\tdr-dongle.kicad_pcb")
print("tracks before", len(b.GetTracks()))
for t in []:
    b.Remove(t)
print("ses import", pcbnew.ImportSpecctraSES(b, R + r"\tdr-dongle.ses"))
print("tracks", len(b.GetTracks()))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(P + r"\tdr-dongle.kicad_pcb", b)
print("saved")
