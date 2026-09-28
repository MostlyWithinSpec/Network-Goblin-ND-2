# Hand-fix the two connections Freerouting left open (LAN_SW, C24.1 +3V3) by re-routing LAN_CLK125.
import pcbnew, shutil
P = r"C:\path\to\ND2\tdr-dongle"
PCB = P + r"\tdr-dongle.kicad_pcb"
shutil.copy(PCB, P + r"\route\before_fix_last2.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
MM = pcbnew.FromMM; T = pcbnew.ToMM
O = 100.0
def pt(x, y): return pcbnew.VECTOR2I(MM(x + O), MM(y + O))
def close(a, x, y): return abs(T(a.x) - O - x) < 0.02 and abs(T(a.y) - O - y) < 0.02
net = lambda n: b.FindNet(n)
# remove old CLK125 via + short segments that occupy the LAN_SW corridor
rm = []
for t in b.GetTracks():
    if t.GetNetname() != "/LAN_CLK125": continue
    s, e = t.GetStart(), t.GetEnd()
    ends = [(22.75, 9.92, 22.26, 9.43), (22.26, 9.43, 22.26, 9.14), (22.26, 9.14, 22.26, 7.56), (22.26, 9.14, 22.26, 9.14)]
    for (ax, ay, bx, by) in ends:
        if (close(s, ax, ay) and close(e, bx, by)) or (close(e, ax, ay) and close(s, bx, by)):
            rm.append(t); break
print("removing", len(rm))
for t in rm: b.Remove(t)
def trk(pts, w, n, layer=pcbnew.F_Cu):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(pt(*a)); t.SetEnd(pt(*c)); t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(net(n)); b.Add(t)
def via(x, y, n):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pt(x, y)); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(net(n)); b.Add(v)
# new CLK125 path
trk([(22.75, 9.92), (22.68, 9.8), (22.68, 9.2), (22.95, 8.85)], 0.15, "/LAN_CLK125")
via(22.95, 8.85, "/LAN_CLK125")
trk([(22.95, 8.85), (22.95, 8.2), (22.31, 7.56), (22.26, 7.56)], 0.15, "/LAN_CLK125", pcbnew.B_Cu)
# LAN_SW: U1.20 straight up into L2.1
trk([(22.25, 10.55), (22.33, 10.3), (22.33, 7.8)], 0.25, "/LAN_SW")
# C24.1 -> +3V3 via
trk([(24.02, 9.3), (23.25, 9.67)], 0.2, "+3V3")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("saved")
