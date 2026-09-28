import pcbnew
lib = r"C:\path\to\ND2\tdr-dongle\ND2.pretty"
io = pcbnew.PCB_IO_KICAD_SEXPR()
fp = io.FootprintLoad(lib, "RJ45_HanRun_HR911130C_Horizontal")
n = 0
for g in list(fp.GraphicalItems()):
    if g.GetLayer() == pcbnew.F_SilkS and pcbnew.ToMM(g.GetBoundingBox().GetTop()) < -11.3:
        fp.Remove(g); n += 1
g = pcbnew.PCB_SHAPE(fp); g.SetShape(pcbnew.SHAPE_T_SEGMENT)
g.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(-8.0), pcbnew.FromMM(-11.8))); g.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(8.0), pcbnew.FromMM(-11.8)))
g.SetLayer(pcbnew.F_Fab); g.SetWidth(pcbnew.FromMM(0.1)); fp.Add(g)
io.FootprintSave(lib, fp)
print("removed silk items:", n)
