# ND-2 TDR dongle - PCB builder (run inside KiCad 10 python: pcbnew available)
# Builds tdr-dongle.kicad_pcb from the schematic netlist: 4-layer JLC stackup, rules,
# net classes, outline, placement, inner planes. Routing is done separately.
import pcbnew, os, re, math

PROJ = r"C:\path\to\ND2\tdr-dongle"
NET = os.path.join(PROJ, "tdr-dongle.net")
OUT = os.path.join(PROJ, "tdr-dongle.kicad_pcb")
KIFP = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
OX, OY = 100.0, 100.0           # board origin offset (mm)
BW, BH = 70.0, 30.0             # board size (mm)

def V(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
MM = pcbnew.FromMM

# ---------------------------------------------------------------- netlist
s = open(NET, encoding="utf-8").read()
comps = {}
csec = s[s.find("(components"):s.find("(libparts")]
for blk in csec.split("(comp\n")[1:]:
    ref = re.search(r'\(ref "([^"]+)"\)', blk).group(1)
    comps[ref] = dict(
        value=re.search(r'\(value "([^"]*)"\)', blk).group(1),
        fp=re.search(r'\(footprint "([^"]*)"\)', blk).group(1),
        uuid=re.findall(r'\(tstamps "([^"]+)"\)', blk)[-1],
        lcsc=(re.search(r'\(name "LCSC"\) "([^"]*)"', blk) or [None, ""])[1],
        fields=[(a, b) for a, b in re.findall(r'\(field\s*\(name "([^"]+)"\) "([^"]*)"\)', blk) if a not in ('Footprint', 'Datasheet', 'Description')],
        dnp='(property\n\t\t\t\t(name "dnp")' in blk)
padnet = {}
nsec = s[s.find("(nets"):]
netnames = []
for blk in re.split(r'\n\t\t\(net\n', nsec)[1:]:
    name = re.search(r'\(name "([^"]*)"\)', blk).group(1)
    netnames.append(name)
    for ref, pin in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', blk):
        padnet[(ref, pin)] = name

# ---------------------------------------------------------------- board + stackup
board = pcbnew.CreateEmptyBoard()
board.SetCopperLayerCount(4)
ds = board.GetDesignSettings()
ds.SetBoardThickness(MM(1.6))
lset = board.GetEnabledLayers()
board.SetEnabledLayers(lset)
board.SetLayerName(pcbnew.In1_Cu, "In1.Cu")
board.SetLayerName(pcbnew.In2_Cu, "In2.Cu")
board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)

# design rules (JLCPCB 4-layer capable, kept conservative)
ds.m_TrackMinWidth = MM(0.1)
ds.m_MinClearance = MM(0.127)
ds.m_ViasMinSize = MM(0.5)
ds.m_MinThroughDrill = MM(0.25)
ds.m_CopperEdgeClearance = MM(0.3)
ds.m_HoleClearance = MM(0.2)
ds.m_HoleToHoleMin = MM(0.25)
ds.m_SilkClearance = MM(0.0)

# net classes
ns = ds.m_NetSettings
def netclass(name, width, clearance, via=0.6, drill=0.3, dp_w=None, dp_gap=None):
    nc = pcbnew.NETCLASS(name)
    nc.SetTrackWidth(MM(width)); nc.SetClearance(MM(clearance))
    nc.SetViaDiameter(MM(via)); nc.SetViaDrill(MM(drill))
    if dp_w: nc.SetDiffPairWidth(MM(dp_w)); nc.SetDiffPairGap(MM(dp_gap))
    return nc
dflt = ns.GetDefaultNetclass()
dflt.SetTrackWidth(MM(0.15)); dflt.SetClearance(MM(0.127)); dflt.SetViaDiameter(MM(0.6)); dflt.SetViaDrill(MM(0.3))
classes = {
    "Power": netclass("Power", 0.3, 0.127),
    "USB": netclass("USB", 0.25, 0.127, dp_w=0.25, dp_gap=0.15),
    "MDI": netclass("MDI", 0.2, 0.127, dp_w=0.2, dp_gap=0.15),
}
for k, nc in classes.items():
    ns.SetNetclass(k, nc)
pat = {
    "Power": ["VBUS", "+5V", "/BUCK_SW", "/LAN_SW", "/LAN_1V2", "/LAN_2V5", "/PHY_1V8", "/PHY_1V0", "/PHY_REGCAP1", "/PHY_REGCAP2"],
    "USB": ["/USB_*", "/LAN_USB3_*"],
    "MDI": ["/MDI?_*"],
}
for k, pats in pat.items():
    for p in pats:
        ns.SetNetclassPatternAssignment(p, k)

# nets
nets = {}
for n in netnames:
    ni = pcbnew.NETINFO_ITEM(board, n)
    board.Add(ni)
    nets[n] = ni

# ---------------------------------------------------------------- placement table (x, y, rot) board-relative mm
P = {
 # USB / power (left)
 "J1": (3.7, 15.0, 270), "U5": (9.5, 15.0, 0), "U6": (6.5, 5.5, 0),
 "C3": (13.2, 12.2, 0), "C4": (13.2, 13.4, 0),
 "FB1": (2.0, 25.8, 90), "C1": (4.6, 25.8, 90), "C2": (4.6, 22.6, 0),
 "U3": (8.6, 26.3, 0), "C5": (8.6, 22.6, 0), "L1": (13.5, 27.3, 0),
 "R1": (6.6, 29.2, 0), "R2": (8.6, 29.2, 0), "C6": (19.3, 27.9, 90), "C7": (21.8, 27.9, 90),
 # LAN7801 (rotated 180: USB side faces J1, RGMII side faces U2)
 "U1": (20.0, 15.0, 180),
 "U4": (13.0, 4.5, 0), "C12": (17.4, 3.5, 90), "C14": (17.4, 6.5, 90), "C13": (19.6, 6.2, 90),
 "L2": (22.5, 6.6, 90), "C21": (25.4, 6.2, 90),
 "C15": (14.5, 9.3, 0), "C23": (16.5, 9.3, 0), "C16": (26.5, 9.3, 0), "R8": (11.0, 8.4, 0),
 "R6": (27.5, 11.5, 0), "C24": (24.5, 9.3, 0), "R7": (29.8, 11.5, 0), "C27": (28.5, 9.3, 0),
 "C28": (21.0, 2.0, 0), "C29": (23.0, 2.0, 0), "C30": (25.0, 2.0, 0), "C31": (27.0, 2.0, 0),
 "C17": (13.2, 16.2, 0), "C25": (13.2, 17.4, 0), "R5": (13.2, 18.6, 0), "C11": (13.2, 19.8, 0),
 "R3": (16.2, 20.65, 0), "C18": (13.2, 21.0, 0), "C26": (13.2, 22.2, 0), "C20": (23.2, 20.65, 0), "R4": (26.0, 20.65, 0),
 "C19": (21.5, 21.75, 0), "C22": (23.5, 21.75, 0), "C10": (26.0, 21.75, 0),
 "Y1": (18.4, 23.4, 0), "C8": (15.3, 23.4, 90), "C9": (21.6, 25.3, 0),
 # RGMII series resistors
 "R9": (27.5, 13.0, 0), "R10": (27.5, 14.1, 0), "R11": (27.5, 15.2, 0), "R12": (27.5, 16.3, 0), "R13": (27.5, 17.4, 0), "R14": (27.5, 18.5, 0),
 "R15": (33.0, 10.8, 0), "R16": (33.0, 11.9, 0), "R17": (33.0, 13.0, 0), "R18": (33.0, 14.1, 0), "R19": (33.0, 15.2, 0), "R20": (33.0, 16.3, 0),
 "R21": (30.2, 21.0, 0), "R22": (30.2, 22.1, 0), "R23": (30.2, 23.2, 0),
 # 88E1512
 "U2": (40.0, 15.0, 0),
 "Y2": (41.5, 5.5, 0), "C32": (38.4, 5.5, 90), "C33": (44.6, 5.5, 90),
 "C49": (34.6, 9.3, 0), "C43": (36.6, 9.3, 0), "C34": (38.6, 9.3, 0), "R24": (44.6, 9.3, 0),
 "C42": (33.5, 2.2, 0), "C48": (33.5, 5.0, 0), "C35": (33.5, 7.6, 0),
 "C38": (45.6, 13.0, 0), "C45": (45.6, 16.0, 0),
 "C44": (35.6, 20.1, 0), "C50": (37.6, 20.1, 0), "C36": (45.4, 20.1, 0),
 "C46": (35.6, 22.0, 0), "C47": (37.6, 22.0, 0), "C37": (43.6, 22.0, 0), "C39": (45.6, 22.0, 0),
 "C40": (35.6, 24.0, 0), "C41": (37.6, 24.0, 0),
 # RJ45 (front faces +x, flush with right edge + 0.5 mm overhang)
 "J2": (70.5 - 12.79, 15.0, 270),
 "C51": (50.0, 25.3, 0), "R25": (62.0, 25.0, 0), "R26": (62.0, 5.0, 0),
}

io = pcbnew.PCB_IO_KICAD_SEXPR()
missing = [r for r in comps if r not in P]
assert not missing, missing
for ref, c in sorted(comps.items()):
    lib, name = c["fp"].split(":")
    path = os.path.join(PROJ, "ND2.pretty") if lib == "ND2" else os.path.join(KIFP, lib + ".pretty")
    fp = io.FootprintLoad(path, name)
    assert fp is not None, (ref, c["fp"])
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    # drop any Edge.Cuts graphics carried by the footprint (USB plug)
    for g in list(fp.GraphicalItems()):
        if g.GetLayer() == pcbnew.Edge_Cuts:
            fp.Remove(g)
    board.Add(fp)
    fp.SetReference(ref); fp.SetValue(c["value"])
    fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
    fp.SetSheetname("tdr-dongle"); fp.SetSheetfile("tdr-dongle.kicad_sch")
    for fname, fval in c["fields"]:
        fp.SetField(fname, fval)
        f = fp.GetField(fname)
        if f is not None:
            f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
    if c["dnp"]:
        fp.SetDNP(True); fp.SetExcludedFromPosFiles(True)
    x, y, rot = P[ref]
    fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(rot)
    # reference on fab layer only (keeps silkscreen clean on a dense 0402 board)
    rt = fp.Reference()
    rt.SetLayer(pcbnew.F_Fab); rt.SetTextSize(pcbnew.VECTOR2I(MM(0.5), MM(0.5))); rt.SetTextThickness(MM(0.08))
    rt.SetPosition(fp.GetPosition())
    fp.Value().SetVisible(False)
    for pad in fp.Pads():
        n = padnet.get((ref, pad.GetNumber()))
        if n:
            pad.SetNet(nets[n])

# ---------------------------------------------------------------- outline (1 mm corner radius)
def seg(a, b):
    g = pcbnew.PCB_SHAPE(board); g.SetShape(pcbnew.SHAPE_T_SEGMENT)
    g.SetStart(V(*a)); g.SetEnd(V(*b)); g.SetLayer(pcbnew.Edge_Cuts); g.SetWidth(MM(0.1)); board.Add(g)
def arc(c, st, ang):
    g = pcbnew.PCB_SHAPE(board); g.SetShape(pcbnew.SHAPE_T_ARC)
    g.SetCenter(V(*c)); g.SetStart(V(*st)); g.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True)
    g.SetLayer(pcbnew.Edge_Cuts); g.SetWidth(MM(0.1)); board.Add(g)
r = 1.0
seg((r, 0), (BW - r, 0)); seg((BW, r), (BW, BH - r)); seg((BW - r, BH), (r, BH)); seg((0, BH - r), (0, r))
arc((BW - r, r), (BW - r, 0), 90); arc((BW - r, BH - r), (BW, BH - r), 90)
arc((r, BH - r), (r, BH), 90); arc((r, r), (0, r), 90)

# ---------------------------------------------------------------- inner planes
def zone(layer, netname, prio=0, clearance=0.2):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(nets[netname])
    ol = z.Outline(); ol.NewOutline()
    for (x, y) in [(0, 0), (BW, 0), (BW, BH), (0, BH)]:
        ol.Append(MM(OX + x), MM(OY + y))
    z.SetLocalClearance(MM(clearance)); z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.3))
    z.SetAssignedPriority(prio); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName("%s_%s" % (board.GetLayerName(layer), netname))
    board.Add(z)
    return z
zone(pcbnew.In1_Cu, "GND")
zone(pcbnew.In2_Cu, "+3V3")

# silkscreen title
t = pcbnew.PCB_TEXT(board); t.SetText("ND-2 TDR DONGLE  Rev A"); t.SetLayer(pcbnew.F_SilkS)
t.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0))); t.SetTextThickness(MM(0.15)); t.SetPosition(V(51.0, 27.8))
board.Add(t)
t2 = pcbnew.PCB_TEXT(board); t2.SetText("Network Goblin"); t2.SetLayer(pcbnew.B_SilkS)
t2.SetTextSize(pcbnew.VECTOR2I(MM(1.5), MM(1.5))); t2.SetTextThickness(MM(0.2)); t2.SetPosition(V(35.0, 15.0)); t2.SetMirrored(True)
board.Add(t2)

board.BuildConnectivity()
pcbnew.SaveBoard(OUT, board)
print("saved", OUT, "footprints", len(board.GetFootprints()), "nets", board.GetNetCount())
