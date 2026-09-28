import pcbnew, os
lib = r"C:\path\to\ND2\tdr-dongle\ND2.pretty"

import sys
for name in sys.argv[1:]:
    io = pcbnew.PCB_IO_KICAD_SEXPR()
    fp = io.FootprintLoad(lib, name)
    xs0, ys0, xs1, ys1 = [], [], [], []
    for p in fp.Pads():
        b = p.GetBoundingBox()
        xs0.append(b.GetLeft()); ys0.append(b.GetTop()); xs1.append(b.GetRight()); ys1.append(b.GetBottom())
    for g in list(fp.GraphicalItems()):
        if g.GetLayer() == pcbnew.F_CrtYd:
            b = g.GetBoundingBox()
            xs0.append(b.GetLeft()); ys0.append(b.GetTop()); xs1.append(b.GetRight()); ys1.append(b.GetBottom())
            fp.Remove(g)
    m = pcbnew.FromMM(0.25)
    x0, y0, x1, y1 = min(xs0) - m, min(ys0) - m, max(xs1) + m, max(ys1) + m
    g = pcbnew.PCB_SHAPE(fp); g.SetShape(pcbnew.SHAPE_T_RECT)
    g.SetStart(pcbnew.VECTOR2I(x0, y0)); g.SetEnd(pcbnew.VECTOR2I(x1, y1))
    g.SetLayer(pcbnew.F_CrtYd); g.SetWidth(pcbnew.FromMM(0.05)); fp.Add(g)
    io.FootprintSave(lib, fp)
    print(name, [round(pcbnew.ToMM(v), 2) for v in (x0, y0, x1, y1)])
