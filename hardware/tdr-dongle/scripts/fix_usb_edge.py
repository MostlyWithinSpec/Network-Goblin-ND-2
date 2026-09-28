import pcbnew
lib = r"C:\path\to\ND2\tdr-dongle\ND2.pretty"
io = pcbnew.PCB_IO_KICAD_SEXPR()
fp = io.FootprintLoad(lib, "USB3_A_Plug_HongCheng_HC-USB3.0-C26")
n = 0
for g in list(fp.GraphicalItems()):
    if g.GetLayer() == pcbnew.Edge_Cuts:
        fp.Remove(g); n += 1
# mark board edge position on the fab layer instead (plug face must hang past the edge)
g = pcbnew.PCB_SHAPE(fp); g.SetShape(pcbnew.SHAPE_T_SEGMENT)
g.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(-6.0), pcbnew.FromMM(3.7))); g.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(6.0), pcbnew.FromMM(3.7)))
g.SetLayer(pcbnew.F_Fab); g.SetWidth(pcbnew.FromMM(0.1)); fp.Add(g)
io.FootprintSave(lib, fp)
print("removed edge items:", n)
