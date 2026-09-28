# Fan out every SMD pad on the plane nets (GND -> In1, +3V3 -> In2) with a short stub + via.
# Tracks/vias are locked so Freerouting keeps them.
import pcbnew, math, sys
P = r"C:\path\to\ND2\tdr-dongle"
PCB = P + r"\tdr-dongle.kicad_pcb"
b = pcbnew.LoadBoard(PCB)
MM = pcbnew.FromMM
ToMM = pcbnew.ToMM
PLANE_NETS = {"GND", "+3V3"}
VIA_D, VIA_DRILL, CLR, STUB_W = 0.6, 0.3, 0.16, 0.25
OX, OY, BW, BH = 100.0, 100.0, 70.0, 30.0

# remove previous tracks/vias (routing is redone after fanout)
assert len(b.GetTracks()) == 0, 'run build_pcb.py first'

obst = []   # (x0, y0, x1, y1, netname) copper keepouts in mm (F.Cu relevant, vias hit all layers)
pads = []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        obst.append((ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()), pad.GetNetname(),
                     pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH))
        pads.append((fp, pad))

def circ_hits(cx, cy, r, net, allow_same=True):
    for (x0, y0, x1, y1, n, th) in obst:
        if allow_same and n == net and n:
            continue
        dx = max(x0 - cx, 0, cx - x1); dy = max(y0 - cy, 0, cy - y1)
        if dx * dx + dy * dy < r * r:
            return True
    if cx < OX + 0.6 or cx > OX + BW - 0.6 or cy < OY + 0.6 or cy > OY + BH - 0.6:
        return True
    return False

def seg_hits(ax, ay, bx, by, w, net, own):
    n = max(2, int(math.hypot(bx - ax, by - ay) / 0.05))
    for i in range(n + 1):
        t = i / n; x = ax + (bx - ax) * t; y = ay + (by - ay) * t
        for (x0, y0, x1, y1, nn, th), o in zip(obst, range(len(obst))):
            if nn == net and nn:
                continue
            dx = max(x0 - x, 0, x - x1); dy = max(y0 - y, 0, y - y1)
            if dx * dx + dy * dy < (w / 2 + CLR) ** 2:
                return True
    return False

added = 0; failed = []
vias = []
for fp, pad in pads:
    net = pad.GetNetname()
    if net not in PLANE_NETS or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
        continue
    if not pad.IsOnLayer(pcbnew.F_Cu):
        continue
    # exposed pads already carry thermal vias
    if fp.GetReference() in ("U1", "U2") and pad.GetNumber() in ("65", "57"):
        continue
    px, py = ToMM(pad.GetPosition().x), ToMM(pad.GetPosition().y)
    sx, sy = ToMM(pad.GetBoundingBox().GetWidth()) / 2, ToMM(pad.GetBoundingBox().GetHeight()) / 2
    fx, fy = ToMM(fp.GetPosition().x), ToMM(fp.GetPosition().y)
    # candidate directions: away from footprint centre first, then the rest
    vx, vy = px - fx, py - fy
    dirs = []
    if abs(vx) > 1e-3 or abs(vy) > 1e-3:
        if abs(vx) >= abs(vy): dirs.append((math.copysign(1, vx), 0))
        else: dirs.append((0, math.copysign(1, vy)))
    for d in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        if d not in dirs: dirs.append(d)
    done = False
    for dist_extra in (0.45, 0.6, 0.8, 1.0, 1.3):
        for dx, dy in dirs:
            half = sx if dx else sy
            cx = px + dx * (half + dist_extra); cy = py + dy * (half + dist_extra)
            if circ_hits(cx, cy, VIA_D / 2 + CLR, net):
                continue
            if any(math.hypot(cx - a, cy - c) < VIA_D + 0.3 for a, c in vias):
                continue
            ex, ey = px + dx * half, py + dy * half
            if seg_hits(ex, ey, cx, cy, STUB_W, net, pad):
                continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(MM(px), MM(py))); t.SetEnd(pcbnew.VECTOR2I(MM(cx), MM(cy)))
            t.SetWidth(MM(min(STUB_W, 2 * min(sx, sy)))); t.SetLayer(pcbnew.F_Cu); t.SetNet(pad.GetNet()); t.SetLocked(True); b.Add(t)
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(MM(cx), MM(cy))); v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_DRILL))
            v.SetNet(pad.GetNet()); v.SetLocked(True); b.Add(v); vias.append((cx, cy))
            obst.append((cx - VIA_D / 2, cy - VIA_D / 2, cx + VIA_D / 2, cy + VIA_D / 2, net, False))
            # stub copper as obstacle too
            obst.append((min(ex, cx) - 0.13, min(ey, cy) - 0.13, max(ex, cx) + 0.13, max(ey, cy) + 0.13, net, False))
            added += 1; done = True
            break
        if done:
            break
    if not done:
        failed.append("%s.%s" % (fp.GetReference(), pad.GetNumber()))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("fanout vias added:", added, "failed:", failed)
