#!/usr/bin/env python3
"""Generate the ND-2 TDR proof dongle schematic (LAN7801 + Marvell 88E1512) for KiCad 10.

Label-based schematic: every pin gets a short stub wire ending in a net label or power
symbol, so connectivity is defined purely by net names (easy to review, easy to edit).
Re-run to regenerate; edits made by hand in KiCad will be overwritten.
Usage: python3 gen_dongle.py <kicad_symbol_lib_dir> <output_project_dir>
"""
import re, uuid, math, os, sys

LIBDIR = sys.argv[1] if len(sys.argv) > 1 else '_libcache'
PROJ = sys.argv[2] if len(sys.argv) > 2 else '.'
NAME = 'tdr-dongle'
ROOT_UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'nd2-tdr-dongle-root'))
_uc = [0]


def U():
    _uc[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, 'nd2-tdr-%d' % _uc[0]))


def fmt(v):
    v = round(v, 4)
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


# ---------------------------------------------------------------- s-expr helpers
def _balanced(s, i):
    d = 0; j = i; inq = False
    while True:
        c = s[j]
        if inq:
            if c == '\\':
                j += 2; continue
            if c == '"':
                inq = False
        else:
            if c == '"':
                inq = True
            elif c == '(':
                d += 1
            elif c == ')':
                d -= 1
                if d == 0:
                    return j + 1
        j += 1


def extract(s, name):
    i = s.find('(symbol "%s"' % name)
    assert i >= 0, name
    return s[i:_balanced(s, i)]


def blocks(s, head):
    out = []; k = 0
    while True:
        i = s.find(head, k)
        if i < 0:
            return out
        j = _balanced(s, i)
        out.append(s[i:j]); k = j


def parse_pins(symtext):
    pins = []
    for b in blocks(symtext, '(pin '):
        m = re.match(r'\(pin (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', b)
        num = re.search(r'\(number "([^"]*)"', b).group(1)
        nm = re.search(r'\(name "([^"]*)"', b).group(1)
        pins.append(dict(num=num, name=nm, type=m.group(1), x=float(m.group(3)),
                         y=float(m.group(4)), a=float(m.group(5))))
    return pins


LIBS = {}


def libsym(lib, name):
    key = '%s:%s' % (lib, name)
    if key not in LIBS:
        s = open(os.path.join(LIBDIR, lib + '.kicad_sym'), encoding='utf-8').read()
        t = extract(s, name)
        assert '(extends' not in t, key
        LIBS[key] = dict(text=t.replace('(symbol "%s"' % name, '(symbol "%s"' % key, 1), pins=parse_pins(t))
    return LIBS[key]


# ---------------------------------------------------------------- custom IC symbols
def gen_ic(name, ref, value, desc, datasheet, left, right, top, bottom, min_w=40.64):
    """left/right: 2.54 pitch lists of (num,name,type) or None (gap); top/bottom at 5.08 pitch."""
    def maxlen(lst):
        return max([len(p[1]) for p in lst if p] + [1])
    n_lr = max(len(left), len(right))
    H = math.ceil((22.86 + (n_lr - 1) * 2.54 + 5.08) / 5.08) * 5.08
    W = max(min_w, 10.16 + (max(len(top), len(bottom)) - 1) * 5.08, (maxlen(left) + maxlen(right)) * 1.27 + 12.7)
    W = math.ceil(W / 5.08) * 5.08
    x0, y0 = -W / 2, H / 2
    pins = []
    for i, p in enumerate(left):
        if p: pins.append((p, x0 - 2.54, y0 - 17.78 - i * 2.54, 0))
    for i, p in enumerate(right):
        if p: pins.append((p, -x0 + 2.54, y0 - 17.78 - i * 2.54, 180))
    tx0 = math.floor((-((len(top) - 1) * 5.08) / 2) / 2.54) * 2.54
    for i, p in enumerate(top):
        if p: pins.append((p, tx0 + i * 5.08, y0 + 2.54, 270))
    bx0 = math.floor((-((len(bottom) - 1) * 5.08) / 2) / 2.54) * 2.54
    for i, p in enumerate(bottom):
        if p: pins.append((p, bx0 + i * 5.08, -y0 - 2.54, 90))
    F = '(effects (font (size 1.27 1.27)))'
    pt = ['(pin %s line (at %s %s %s) (length 2.54) (name "%s" %s) (number "%s" %s))'
          % (typ, fmt(x), fmt(y), fmt(a), nm, F, num, F) for (num, nm, typ), x, y, a in pins]
    body = ('(symbol "{N}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)'
            ' (property "Reference" "{R}" (at {x0} {ry} 0) (effects (font (size 1.27 1.27)) (justify left)))'
            ' (property "Value" "{V}" (at {x0} {vy} 0) (effects (font (size 1.27 1.27)) (justify left)))'
            ' (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            ' (property "Datasheet" "{D}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            ' (property "Description" "{DS}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            ' (symbol "{N}_0_1" (rectangle (start {x0} {y0}) (end {x1} {y1}) (stroke (width 0.254) (type default)) (fill (type background))))'
            ' (symbol "{N}_1_1" {PINS}) (embedded_fonts no))').format(
        N=name, R=ref, V=value, D=datasheet, DS=desc, ry=fmt(-y0 - 7.62), vy=fmt(-y0 - 10.16),
        x0=fmt(x0), y0=fmt(y0), x1=fmt(-x0), y1=fmt(-y0), PINS=' '.join(pt))
    key = 'ND2:' + name
    LIBS[key] = dict(text=body.replace('(symbol "%s"' % name, '(symbol "%s"' % key, 1), pins=parse_pins(body), W=W, H=H)
    return body


P = lambda n, nm, t: (str(n), nm, t)
LAN_LEFT = [P(38, 'USB2_DP', 'bidirectional'), P(39, 'USB2_DM', 'bidirectional'), None,
            P(40, 'USB3_TXDP', 'output'), P(41, 'USB3_TXDM', 'output'), P(43, 'USB3_RXDP', 'input'), P(44, 'USB3_RXDM', 'input'), None,
            P(29, 'VBUS_DET', 'input'), P(47, 'RESET_N/PME_CLEAR', 'input'), P(46, 'TEST', 'input'), P(30, 'SUSPEND_N', 'output'), None,
            P(23, 'EECS/GPIO0', 'output'), P(24, 'EEDI/GPIO1', 'input'), P(25, 'EEDO/GPIO2', 'output'), P(26, 'EECLK/GPIO3', 'output'), None,
            P(52, 'XI', 'input'), P(53, 'XO', 'output'), None,
            P(49, 'USBRBIAS', 'passive'), P(1, 'REF_REXT', 'passive'), P(2, 'REF_FILT', 'passive'), None,
            P(35, 'GPIO4', 'bidirectional'), P(36, 'PME_MODE/GPIO5', 'bidirectional'), P(45, 'PME_N/GPIO6', 'bidirectional'),
            P(57, 'TDI/GPIO7', 'bidirectional'), P(58, 'TCK/GPIO8', 'bidirectional'), P(59, 'TMS/GPIO9', 'bidirectional'),
            P(60, 'TDO/GPIO10', 'bidirectional'), P(34, 'NC', 'no_connect')]
LAN_RIGHT = [P(10, 'TXC', 'output'), P(9, 'TX_CTL', 'output'), P(8, 'TXD0', 'output'), P(6, 'TXD1', 'output'),
             P(5, 'TXD2', 'output'), P(4, 'TXD3', 'output'), None,
             P(12, 'RXC', 'input'), P(13, 'RX_CTL', 'input'), P(14, 'RXD0', 'input'), P(15, 'RXD1', 'input'),
             P(16, 'RXD2', 'input'), P(17, 'RXD3', 'input'), None,
             P(56, 'MDC', 'output'), P(55, 'MDIO', 'bidirectional'), P(31, 'PHY_INT_N', 'input'), P(32, 'PHY_RESET_N', 'output'),
             P(33, 'DUPLEX', 'input'), None, P(19, 'CLK125', 'input'), P(61, 'REFCLK_25/GPIO11', 'bidirectional')]
LAN_TOP = [P(50, 'VDD33A', 'power_in'), P(64, 'VDD33_REG_IN', 'power_in'), P(21, 'VDD_SW_IN', 'power_in'),
           P(3, 'VDDVARIO', 'power_in'), P(7, 'VDDVARIO', 'power_in'), P(11, 'VDDVARIO', 'power_in'), P(18, 'VDDVARIO', 'power_in'),
           P(27, 'VDDVARIO', 'power_in'), P(48, 'VDDVARIO', 'power_in'), P(51, 'VDDVARIO', 'power_in'), None,
           P(20, 'VDD12_SW_OUT', 'power_out'), None, P(22, 'VDD12_SW_FB', 'passive'), P(28, 'VDD12CORE', 'power_in'),
           P(54, 'VDD12CORE', 'power_in'), P(37, 'VDD12A', 'power_in'), P(42, 'VDD12A', 'power_in'), P(62, 'VDD12A', 'power_in'),
           None, P(63, 'VDD25_REG_OUT', 'power_out')]
LAN_BOT = [P(65, 'VSS(EP)', 'power_in')]

PHY_LEFT = [P(28, 'MDIP[0]', 'bidirectional'), P(27, 'MDIN[0]', 'bidirectional'), P(24, 'MDIP[1]', 'bidirectional'),
            P(23, 'MDIN[1]', 'bidirectional'), P(22, 'MDIP[2]', 'bidirectional'), P(21, 'MDIN[2]', 'bidirectional'),
            P(18, 'MDIP[3]', 'bidirectional'), P(17, 'MDIN[3]', 'bidirectional'), None,
            P(14, 'LED[0]', 'output'), P(13, 'LED[1]', 'bidirectional'), P(12, 'LED[2]/INTn', 'output'), None,
            P(34, 'XTAL_IN', 'input'), P(33, 'XTAL_OUT', 'output'), None,
            P(30, 'RSET', 'passive'), P(29, 'TSTPT', 'output'), P(31, 'HSDACN', 'output'), P(32, 'HSDACP', 'output'), None,
            P(1, 'S_INP', 'input'), P(2, 'S_INN', 'input'), P(4, 'S_OUTP', 'output'), P(5, 'S_OUTN', 'output')]
PHY_RIGHT = [P(53, 'TX_CLK', 'input'), P(56, 'TX_CTRL', 'input'), P(50, 'TXD[0]', 'input'), P(51, 'TXD[1]', 'input'),
             P(54, 'TXD[2]', 'input'), P(55, 'TXD[3]', 'input'), None,
             P(46, 'RX_CLK', 'output'), P(43, 'RX_CTRL', 'output'), P(44, 'RXD[0]', 'output'), P(45, 'RXD[1]', 'output'),
             P(47, 'RXD[2]', 'output'), P(48, 'RXD[3]', 'output'), None,
             P(7, 'MDC', 'input'), P(8, 'MDIO', 'bidirectional'), P(16, 'RESETn', 'input'), P(15, 'CONFIG', 'input'),
             P(9, 'CLK125', 'output'), P(10, 'VDDO_SEL', 'input')]
PHY_TOP = [P(20, 'AVDD33', 'power_in'), P(25, 'AVDD33', 'power_in'), P(36, 'REG_IN', 'power_in'), P(11, 'VDDO', 'power_in'),
           P(49, 'VDDO', 'power_in'), P(52, 'VDDO', 'power_in'), None,
           P(39, 'AVDD18_OUT', 'power_out'), P(3, 'AVDD18', 'power_in'), P(19, 'AVDD18', 'power_in'), P(26, 'AVDD18', 'power_in'),
           P(38, 'AVDD18', 'power_in'), P(35, 'AVDDC18', 'power_in'), None,
           P(40, 'DVDD_OUT', 'power_out'), P(6, 'DVDD', 'power_in'), P(42, 'DVDD', 'power_in'), None,
           P(37, 'REGCAP1', 'passive'), P(41, 'REGCAP2', 'passive')]
PHY_BOT = [P(57, 'VSS(EP)', 'power_in')]

LAN_SYM = gen_ic('LAN7801', 'U', 'LAN7801', 'SuperSpeed USB 3.1 Gen 1 to 10/100/1000 Ethernet controller with RGMII, 64-SQFN 9x9',
                 'https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/DataSheets/LAN7801-Data-Sheet-DS00002123.pdf',
                 LAN_LEFT, LAN_RIGHT, LAN_TOP, LAN_BOT)
J2_SYM = gen_ic('HR911130C', 'J', 'HR911130C', 'HanRun 1 port RJ45 10/100/1000 magjack, 2 LEDs (green L, yellow R), THT',
                'https://www.lcsc.com/datasheet/C50933.pdf',
                [P(2, 'MDI0+', 'passive'), P(3, 'MDI0-', 'passive'), P(4, 'MDI1+', 'passive'), P(7, 'MDI1-', 'passive'),
                 P(5, 'MDI2+', 'passive'), P(6, 'MDI2-', 'passive'), P(8, 'MDI3+', 'passive'), P(9, 'MDI3-', 'passive'), None,
                 P(1, 'CT', 'passive'), P(10, 'CHS_GND', 'passive')],
                [P(11, 'LED_G+', 'passive'), P(12, 'LED_G-', 'passive'), None, P(14, 'LED_Y+', 'passive'), P(13, 'LED_Y-', 'passive')],
                [], [P('SH', 'SHIELD', 'passive')], min_w=30.48)
PHY_SYM = gen_ic('88E1512', 'U', '88E1512', 'Marvell Alaska 10/100/1000BASE-T PHY, RGMII/SGMII, VCT (TDR), 56-QFN 8x8',
                 'https://web.pa.msu.edu/hep/atlas/l1calo/htm/hardware/components/Enet_Phy/marvell_alaska_phy_88e151x_datasheet_jan18.pdf',
                 PHY_LEFT, PHY_RIGHT, PHY_TOP, PHY_BOT)

# ---------------------------------------------------------------- schematic model
ITEMS = []
USED = set()
PWR_N = [0]; FLG_N = [0]
POWER_NETS = {'GND': 'power:GND', '+3V3': 'power:+3V3', '+5V': 'power:+5V', 'VBUS': 'power:VBUS'}
NETS = {}
PARTS = {}


def G(v, g=2.54):
    return round(round(v / g) * g, 4)


def rot(px, py, r):
    a = math.radians(r)
    return px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)


def prop(name, val, x, y, hide=False, ang=0, just=None):
    eff = '(font (size 1.27 1.27))'
    if just: eff += ' (justify %s)' % just
    if hide: eff += ' (hide yes)'
    return '(property "%s" "%s" (at %s %s %s) (effects %s))' % (name, val, fmt(x), fmt(y), ang, eff)


def sym_instance(lib_id, ref, value, x, y, r=0, fp='', dnp=False, props_pos=None, extra=None, val_just='left', val_ang=0):
    USED.add(lib_id)
    if lib_id not in LIBS:
        libsym(*lib_id.split(':', 1))
    rx, ry, vx, vy = props_pos or (x + 2.54, y - 1.27, x + 2.54, y + 1.27)
    is_pwr = ref.startswith('#')
    s = ['(symbol (lib_id "%s") (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom %s) (on_board %s) (dnp %s) (uuid "%s")'
         % (lib_id, fmt(x), fmt(y), r, 'no' if is_pwr else 'yes', 'no' if is_pwr else 'yes', 'yes' if dnp else 'no', U())]
    s.append(prop('Reference', ref, rx, ry, hide=is_pwr, just='left'))
    s.append(prop('Value', value, vx, vy, just=val_just, ang=val_ang))
    s.append(prop('Footprint', fp, x, y, hide=True))
    s.append(prop('Datasheet', '', x, y, hide=True))
    s.append(prop('Description', '', x, y, hide=True))
    for k, v in (extra or {}).items():
        s.append(prop(k, v, x, y, hide=True))
    s.append('(instances (project "%s" (path "/%s" (reference "%s") (unit 1))))' % (NAME, ROOT_UUID, ref))
    s.append(')')
    ITEMS.append(' '.join(s))


def wire(x1, y1, x2, y2):
    ITEMS.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))'
                 % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), U()))


def junction(x, y):
    ITEMS.append('(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))' % (fmt(x), fmt(y), U()))


def label(net, x, y, outdir):
    x, y = G(x, 1.27), G(y, 1.27)
    ang, just = {'L': (180, 'right bottom'), 'R': (0, 'left bottom'), 'U': (90, 'left bottom'), 'D': (270, 'right bottom')}[outdir]
    ITEMS.append('(label "%s" (at %s %s %d) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s"))'
                 % (net, fmt(x), fmt(y), ang, just, U()))


def noconn(x, y):
    ITEMS.append('(no_connect (at %s %s) (uuid "%s"))' % (fmt(x), fmt(y), U()))


def text(t, x, y, size=1.27):
    t = t.replace('"', "'").replace('\n', '\\n')
    ITEMS.append('(text "%s" (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)) (justify left top)) (uuid "%s"))'
                 % (t, fmt(x), fmt(y), size, size, U()))


def power_sym(net, x, y, outdir):
    x, y = G(x, 1.27), G(y, 1.27)
    PWR_N[0] += 1
    if net == 'GND':
        r = {'D': 0, 'U': 180, 'L': 270, 'R': 90}[outdir]
    else:
        r = {'U': 0, 'D': 180, 'L': 90, 'R': 270}[outdir]
    just = 'left'
    if outdir == 'U':
        vpos = (x - 1.27, y - 3.81) if net != 'GND' else (x - 1.27, y - 5.08)
    elif outdir == 'D':
        vpos = (x - 1.27, y + 5.08) if net == 'GND' else (x - 1.27, y + 5.08)
    elif outdir == 'L':
        vpos, just = (x - 3.81, y - 0.635), 'right'
    else:
        vpos = (x + 3.81, y - 0.635)
    sym_instance(POWER_NETS[net], '#PWR%03d' % PWR_N[0], net, x, y, r, props_pos=(x, y, vpos[0], vpos[1]), val_just=just,
                 val_ang=90 if r in (90, 270) else 0)


def pwr_flag(x, y):
    x, y = G(x, 1.27), G(y, 1.27)
    FLG_N[0] += 1
    sym_instance('power:PWR_FLAG', '#FLG%02d' % FLG_N[0], 'PWR_FLAG', x, y, 0, props_pos=(x, y, x + 1.27, y - 5.08))


def terminate(net, x, y, outdir):
    if net in POWER_NETS:
        power_sym(net, x, y, outdir)
    else:
        label(net, x, y, outdir)


def outdir_of(angle_world):
    a = int(round(angle_world)) % 360
    return {0: 'L', 180: 'R', 90: 'D', 270: 'U'}[a]


DV = {'L': (-1, 0), 'R': (1, 0), 'U': (0, -1), 'D': (0, 1)}


def place(lib_id, ref, value, x, y, conns, r=0, fp='', dnp=False, stub=2.54, group=False, props_pos=None, extra=None):
    """conns: {pin_number: net | 'NC'}; every pin must be assigned (library no_connect pins may be omitted)."""
    sym = LIBS[lib_id] if lib_id in LIBS else libsym(*lib_id.split(':', 1))
    x, y = G(x), G(y)
    sym_instance(lib_id, ref, value, x, y, r, fp, dnp, props_pos, extra=extra)
    PARTS[ref] = (lib_id, value, fp, dnp, extra or {})
    pins = sym['pins']
    nums = set(p['num'] for p in pins)
    for k in conns:
        assert k in nums, (ref, k)
    done = {}
    groups = {}
    for p in pins:
        net = conns.get(p['num'])
        if net is None:
            if p['type'] == 'no_connect':
                continue
            raise SystemExit('unassigned pin %s.%s (%s)' % (ref, p['num'], p['name']))
        px, py = rot(p['x'], p['y'], r)
        wx, wy = x + px, y - py
        key = (round(wx, 3), round(wy, 3))
        if net != 'NC':
            NETS.setdefault(net, []).append((ref, p['num'], p['name']))
        if key in done:
            assert done[key] == net, (ref, p['num'])
            continue
        done[key] = net
        if net == 'NC':
            noconn(wx, wy); continue
        od = outdir_of(p['a'] + r)
        dx, dy = DV[od]
        ex, ey = wx + dx * stub, wy + dy * stub
        wire(wx, wy, ex, ey)
        if group and od in 'UD':
            groups.setdefault((od, net, round(ey, 3)), []).append((ex, ey))
        else:
            terminate(net, ex, ey, od)
    # join adjacent same-net top/bottom stubs with a bus wire and one terminator
    for (od, net, _), pts in groups.items():
        pts.sort()
        runs = [[pts[0]]]
        for q in pts[1:]:
            if q[0] - runs[-1][-1][0] <= 5.09:
                runs[-1].append(q)
            else:
                runs.append([q])
        for run in runs:
            dx, dy = DV[od]
            fx, fy = run[0]
            if len(run) == 1:
                terminate(net, fx, fy, od); continue
            for a, b in zip(run, run[1:]):
                wire(a[0], a[1], b[0], b[1])
            for q in run[:-1]:
                junction(q[0], q[1])
            wire(fx, fy, fx + dx * 2.54, fy + dy * 2.54)
            terminate(net, fx + dx * 2.54, fy + dy * 2.54, od)


FP_R = 'Resistor_SMD:R_0402_1005Metric'
FP_C = 'Capacitor_SMD:C_0402_1005Metric'
FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
FP_C0805 = 'Capacitor_SMD:C_0805_2012Metric'
REFN = {'R': 0, 'C': 0}

# LCSC part numbers (checked on lcsc.com 2026-09-25). value -> (LCSC, MPN, Manufacturer)
LCSC_R = {
    '22R': ('C25092', '0402WGF220JTCE', 'UNI-ROYAL'), '10k': ('C25744', '0402WGF1002TCE', 'UNI-ROYAL'),
    '12k': ('C25752', '0402WGF1202TCE', 'UNI-ROYAL'), '2k': ('C4109', '0402WGF2001TCE', 'UNI-ROYAL'),
    '4.99k': ('C25903', '0402WGF4991TCE', 'UNI-ROYAL'), '453k': ('C27009', '0402WGF4533TCE', 'UNI-ROYAL'),
    '100k': ('C25741', '0402WGF1003TCE', 'UNI-ROYAL'), '1.5k': ('C25867', '0402WGF1501TCE', 'UNI-ROYAL'),
    '330R': ('C25104', '0402WGF3300TCE', 'UNI-ROYAL'), '0R': ('C17168', '0402WGF0000TCE', 'UNI-ROYAL'),
}
LCSC_C = {
    '100nF': ('C1525', 'CL05B104KO5NNNC', 'Samsung'), '1uF': ('C52923', 'CL05A105KA5NQNC', 'Samsung'),
    '10uF': ('C15850', 'CL21A106KAYNNNE', 'Samsung'), '22uF': ('C45783', 'CL21A226MAQNNNE', 'Samsung'),
    '15pF': ('C1548', '0402CG150J500NT', 'FH'), '220nF': ('C16772', 'CL05B224KO5NNNC', 'Samsung'),
}


def lcsc(entry):
    c, mpn, mfr = entry
    return {'LCSC': c, 'MPN': mpn, 'Manufacturer': mfr}


def R(value, n1, n2, x, y, fp=FP_R, dnp=False):
    REFN['R'] += 1; ref = 'R%d' % REFN['R']
    place('Device:R', ref, value, x, y, {'1': n1, '2': n2}, fp=fp, dnp=dnp, extra=lcsc(LCSC_R[value]))
    return ref


def C(value, n1, n2, x, y, fp=None):
    REFN['C'] += 1; ref = 'C%d' % REFN['C']
    if fp is None:
        fp = FP_C0805 if value in ('10uF', '22uF') else FP_C
    place('Device:C', ref, value, x, y, {'1': n1, '2': n2}, fp=fp, extra=lcsc(LCSC_C[value]))
    return ref


def ic_props(lib_id, x, y):
    W, H = LIBS[lib_id]['W'], LIBS[lib_id]['H']
    return (x - W / 2, y - H / 2 - 22, x - W / 2, y - H / 2 - 19.5)


# ================================================================ BUILD
PITCH = 10.16


class Row:
    """hands out x positions along a row at a fixed pitch"""
    def __init__(self, x, y, pitch=PITCH):
        self.x, self.y, self.p = x, y, pitch

    def __call__(self, extra=0):
        self.x += extra
        pos = (self.x, self.y)
        self.x += self.p
        return pos


# ---------------- Block A: USB upstream, ESD, 5V, 3V3 buck
text('USB 3.0 UPSTREAM + POWER', 20, 20, 2)
for i, net in enumerate(['VBUS', '+5V', '+3V3', 'GND']):
    fx = 76.2 + i * 20.32
    wire(fx, 35.56, fx + 5.08, 35.56)
    pwr_flag(fx + 5.08, 35.56)
    power_sym(net, fx, 35.56, 'D' if net == 'GND' else 'U')
place('Connector:USB3_A', 'J1', 'HC-USB3.0-C26', 40.64, 60.96,
      {'1': 'VBUS', '2': 'USB_DM', '3': 'USB_DP', '4': 'GND', '5': 'USB_SSRX_N', '6': 'USB_SSRX_P', '7': 'GND',
       '8': 'USB_SSTX_N', '9': 'USB_SSTX_P', 'SH': 'GND'}, stub=5.08, group=True, props_pos=(30.48, 45.72, 30.48, 43.18),
      fp='ND2:USB3_A_Plug_HongCheng_HC-USB3.0-C26', extra=lcsc(('C7501854', 'HC-USB3.0-C26', 'Hong Cheng')))
text('J1 = USB 3.0 Type-A PLUG (male, PCB edge or cable).\nSSRX = host receive (our TX), SSTX = host transmit (our RX).', 20, 96)
r = Row(88.9, 60.96)
place('Device:FerriteBead', 'FB1', '600R', *r(), conns={'1': 'VBUS', '2': '+5V'}, fp='Inductor_SMD:L_0805_2012Metric',
      extra=dict(lcsc(('C21519', 'MPZ2012S601AT000', 'TDK')), Spec='600R @ 100 MHz, 2 A'))
C('10uF', '+5V', 'GND', *r())
C('100nF', '+5V', 'GND', *r())

place('Power_Protection:TPD4EUSB30', 'U5', 'TPD4EUSB30', 45.72, 124.46,
      {'1': 'USB_SSTX_P', '2': 'USB_SSTX_N', '3': 'GND', '8': 'GND', '4': 'USB_SSRX_P', '5': 'USB_SSRX_N',
       '6': 'NC', '7': 'NC', '9': 'NC', '10': 'NC'}, fp='Package_SON:USON-10_2.5x1.0mm_P0.5mm',
      props_pos=(50.8, 109.22, 50.8, 106.68), extra=lcsc(('C90627', 'TPD4EUSB30DQAR', 'TI')))
r = Row(96.52, 124.46)
C('100nF', 'LAN_USB3_TXP', 'USB_SSRX_P', *r())
C('100nF', 'LAN_USB3_TXN', 'USB_SSRX_N', *r())
text('USB 3 TX AC-coupling caps\n(device side), place near U1', 88.9, 138)
place('Power_Protection:PRTR5V0U2X', 'U6', 'PRTR5V0U2X', 45.72, 167.64,
      {'1': 'GND', '2': 'USB_DP', '3': 'USB_DM', '4': '+5V'}, fp='Package_TO_SOT_SMD:SOT-143',
      props_pos=(50.8, 153.67, 50.8, 151.13), extra=lcsc(('C12333', 'PRTR5V0U2X,215', 'Nexperia')))

text('3V3 BUCK (TLV62569, 2 A)   Vout = 0.6 x (1 + 453k / 100k) = 3.32 V', 20, 184, 1.5)
place('Regulator_Switching:TLV62568DBV', 'U3', 'TLV62569DBV', 45.72, 210.82,
      {'1': '+5V', '4': '+5V', '2': 'GND', '3': 'BUCK_SW', '5': 'BUCK_FB'}, fp='Package_TO_SOT_SMD:SOT-23-5',
      props_pos=(40.64, 200.66, 40.64, 198.12), extra=lcsc(('C141836', 'TLV62569DBVR', 'TI')))
r = Row(76.2, 210.82)
place('Device:L', 'L1', '2.2uH', *r(), conns={'1': 'BUCK_SW', '2': '+3V3'}, fp='ND2:L_4.0x4.0mm_SMNR4020',
      extra=dict(lcsc(('C135262', 'SMNR4020-2.2UH', 'Shun Xiang Nuo')), Spec='2.2 uH, 3.4 A, 46 mR'))
C('10uF', '+5V', 'GND', *r())
C('22uF', '+3V3', 'GND', *r())
C('22uF', '+3V3', 'GND', *r())
R('453k', '+3V3', 'BUCK_FB', *r())
R('100k', 'BUCK_FB', 'GND', *r())

# ---------------- Block B: LAN7801
text('LAN7801   USB 3 -> RGMII MAC', 150, 20, 2)
place('ND2:LAN7801', 'U1', 'LAN7801-I/9JX', 215.9, 134.62, {
    '38': 'USB_DP', '39': 'USB_DM', '40': 'LAN_USB3_TXP', '41': 'LAN_USB3_TXN', '43': 'USB_SSTX_P', '44': 'USB_SSTX_N',
    '29': '+3V3', '47': 'LAN_RESET_N', '46': 'GND', '30': 'NC',
    '23': 'EE_CS', '24': 'EE_DO', '25': 'EE_DI', '26': 'EE_CLK',
    '52': 'LAN_XI', '53': 'LAN_XO', '49': 'LAN_USBRBIAS', '1': 'LAN_REF_REXT', '2': 'LAN_REF_FILT',
    '35': 'NC', '36': 'NC', '45': 'NC', '57': 'NC', '58': 'NC', '59': 'NC', '60': 'NC',
    '10': 'LAN_TXC', '9': 'LAN_TX_CTL', '8': 'LAN_TXD0', '6': 'LAN_TXD1', '5': 'LAN_TXD2', '4': 'LAN_TXD3',
    '12': 'RGMII_RXC', '13': 'RGMII_RX_CTL', '14': 'RGMII_RXD0', '15': 'RGMII_RXD1', '16': 'RGMII_RXD2', '17': 'RGMII_RXD3',
    '56': 'MDC', '55': 'MDIO', '31': 'PHY_INT_N', '32': 'PHY_RESET_N', '33': '+3V3', '19': 'LAN_CLK125', '61': 'NC',
    '50': '+3V3', '64': '+3V3', '21': '+3V3', '3': '+3V3', '7': '+3V3', '11': '+3V3', '18': '+3V3', '27': '+3V3',
    '48': '+3V3', '51': '+3V3',
    '20': 'LAN_SW', '22': 'LAN_1V2', '28': 'LAN_1V2', '54': 'LAN_1V2', '37': 'LAN_1V2', '42': 'LAN_1V2', '62': 'LAN_1V2',
    '63': 'LAN_2V5', '65': 'GND'}, group=True, props_pos=ic_props('ND2:LAN7801', 215.9, 134.62),
    fp='ND2:LAN7801_QFN-64-1EP_9x9mm_P0.5mm_EP6.1mm', extra=lcsc(('C633491', 'LAN7801-I/9JX', 'Microchip')))

Y0 = 231.14
text('LAN7801 support: crystal, bias resistors, reset, CLK125, EEPROM', 150, Y0 - 26, 1.5)
place('Device:Crystal_GND24', 'Y1', '25MHz', 162.56, Y0, {'1': 'LAN_XI', '3': 'LAN_XO', '2': 'GND', '4': 'GND'},
      fp='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', props_pos=(158.75, Y0 - 5.08, 158.75, Y0 - 7.62),
      extra=dict(lcsc(('C9006', 'X322525MOB4SI', 'YXC')), Spec='25.000 MHz, CL 12 pF, +/-10 ppm'))
r = Row(187.96, Y0)
C('15pF', 'LAN_XI', 'GND', *r())
C('15pF', 'LAN_XO', 'GND', *r())
R('12k', 'LAN_USBRBIAS', 'GND', *r())
R('2k', 'LAN_REF_REXT', 'GND', *r())
C('1uF', 'LAN_REF_FILT', 'GND', *r())
R('10k', '+3V3', 'LAN_RESET_N', *r())
C('100nF', 'LAN_RESET_N', 'GND', *r())
R('10k', 'LAN_CLK125', 'GND', *r())
R('0R', 'LAN_CLK125', 'PHY_CLK125', *r(), dnp=True)
place('Memory_EEPROM:93AAxxC', 'U4', '93AA66/SN', 294.64, Y0 + 2.54,
      {'1': 'EE_CS', '2': 'EE_CLK', '3': 'EE_DI', '4': 'EE_DO', '5': 'GND', '6': 'GND', '8': '+3V3'},
      fp='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', props_pos=(299.72, Y0 - 7.62, 299.72, Y0 - 10.16),
      extra=lcsc(('C615340', '93AA66/SN', 'Microchip')))
r = Row(325.12, Y0)
C('100nF', '+3V3', 'GND', *r())
R('10k', 'EE_DO', '+3V3', *r())
text('R3 12k, R4 2k: 1 %.   U4 93AA66A = 512 x 8 Microwire EEPROM (x8 only): MAC address + HW_CFG'
     '\n(RGMII hybrid mode: MAC TXC + RXC internal delay ON, CLK125_EN = 1, REFCLK25_EN = 0).', 150, Y0 + 20)

Y1 = Y0 + 50.8
text('LAN7801 1V2 switcher, 2V5 LDO cap, 1V2 decoupling', 150, Y1 - 26, 1.5)
r = Row(162.56, Y1)
place('Device:L', 'L2', '3.3uH', *r(), conns={'1': 'LAN_SW', '2': 'LAN_1V2'}, fp='ND2:L_3.0x3.0mm_SMNR3015',
      extra=dict(lcsc(('C135239', 'SMNR3015-3R3MT', 'Shun Xiang Nuo')), Spec='3.3 uH, 1.32 A, 104 mR'))
C('22uF', 'LAN_1V2', 'GND', *r())
C('1uF', 'LAN_1V2', 'GND', *r())
for i in range(5):
    C('100nF', 'LAN_1V2', 'GND', *r())
C('1uF', 'LAN_2V5', 'GND', *r(5.08))
fx, fy = r(5.08)
pwr_flag(fx, fy); label('LAN_1V2', fx, fy, 'R')

Y1b = Y1 + 45.72
text('LAN7801 3V3 decoupling: 10uF at VDD_SW_IN, 1uF at VDD33_REG_IN, 100nF per VDDVARIO / VDD33A pin', 150, Y1b - 26, 1.5)
r = Row(162.56, Y1b)
C('10uF', '+3V3', 'GND', *r())
C('1uF', '+3V3', 'GND', *r())
for i in range(9):
    C('100nF', '+3V3', 'GND', *r())

YR = Y1b + 45.72
text('RGMII 22R series terminations (start value): TX group next to U1, RX group next to U2. Length-match all 12 lines.', 150, YR - 26, 1.5)
r = Row(162.56, YR)
for a, b in [('LAN_TXC', 'RGMII_TXC'), ('LAN_TX_CTL', 'RGMII_TX_CTL'), ('LAN_TXD0', 'RGMII_TXD0'), ('LAN_TXD1', 'RGMII_TXD1'),
             ('LAN_TXD2', 'RGMII_TXD2'), ('LAN_TXD3', 'RGMII_TXD3')]:
    R('22R', a, b, *r())
r.x += 5.08
for a, b in [('PHY_RXC', 'RGMII_RXC'), ('PHY_RX_CTL', 'RGMII_RX_CTL'), ('PHY_RXD0', 'RGMII_RXD0'), ('PHY_RXD1', 'RGMII_RXD1'),
             ('PHY_RXD2', 'RGMII_RXD2'), ('PHY_RXD3', 'RGMII_RXD3')]:
    R('22R', a, b, *r())
r.x += 5.08
R('1.5k', '+3V3', 'MDIO', *r())
R('10k', '+3V3', 'PHY_INT_N', *r())
R('10k', 'PHY_RESET_N', 'GND', *r())
text('MDIO 1.5k pull-up.  PHY_INT_N pull-up.  PHY_RESET_N pull-down holds the PHY in reset until the LAN7801 releases it.', 150, YR + 20)

# ---------------- Block C: 88E1512
text('MARVELL 88E1512   GbE PHY with VCT / TDR', 380, 20, 2)
place('ND2:88E1512', 'U2', '88E1512-A0-NNP2C000', 444.5, 134.62, {
    '28': 'MDI0_P', '27': 'MDI0_N', '24': 'MDI1_P', '23': 'MDI1_N', '22': 'MDI2_P', '21': 'MDI2_N', '18': 'MDI3_P', '17': 'MDI3_N',
    '14': 'PHY_LED0', '13': 'PHY_LED1', '12': 'PHY_INT_N',
    '34': 'PHY_XI', '33': 'PHY_XO', '30': 'PHY_RSET', '29': 'NC', '31': 'NC', '32': 'NC', '1': 'NC', '2': 'NC', '4': 'NC', '5': 'NC',
    '53': 'RGMII_TXC', '56': 'RGMII_TX_CTL', '50': 'RGMII_TXD0', '51': 'RGMII_TXD1', '54': 'RGMII_TXD2', '55': 'RGMII_TXD3',
    '46': 'PHY_RXC', '43': 'PHY_RX_CTL', '44': 'PHY_RXD0', '45': 'PHY_RXD1', '47': 'PHY_RXD2', '48': 'PHY_RXD3',
    '7': 'MDC', '8': 'MDIO', '16': 'PHY_RESET_N', '15': 'GND', '9': 'PHY_CLK125', '10': 'GND',
    '20': '+3V3', '25': '+3V3', '36': '+3V3', '11': '+3V3', '49': '+3V3', '52': '+3V3',
    '39': 'PHY_1V8', '3': 'PHY_1V8', '19': 'PHY_1V8', '26': 'PHY_1V8', '38': 'PHY_1V8', '35': 'PHY_1V8',
    '40': 'PHY_1V0', '6': 'PHY_1V0', '42': 'PHY_1V0', '37': 'PHY_REGCAP1', '41': 'PHY_REGCAP2', '57': 'GND'},
    group=True, props_pos=ic_props('ND2:88E1512', 444.5, 134.62), fp='ND2:88E1512_QFN-56-1EP_8x8mm_P0.5mm_EP4.4mm',
    extra=lcsc(('C845579', '88E1512-A0-NNP2C000', 'Marvell')))

Y2 = Y0
text('88E1512 support: crystal, RSET, regulator cap, 3V3 decoupling', 375, Y2 - 26, 1.5)
place('Device:Crystal_GND24', 'Y2', '25MHz', 386.08, Y2, {'1': 'PHY_XI', '3': 'PHY_XO', '2': 'GND', '4': 'GND'},
      fp='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', props_pos=(382.27, Y2 - 5.08, 382.27, Y2 - 7.62),
      extra=dict(lcsc(('C9006', 'X322525MOB4SI', 'YXC')), Spec='25.000 MHz, CL 12 pF, +/-10 ppm'))
r = Row(411.48, Y2)
C('15pF', 'PHY_XI', 'GND', *r())
C('15pF', 'PHY_XO', 'GND', *r())
R('4.99k', 'PHY_RSET', 'GND', *r())
C('220nF', 'PHY_REGCAP1', 'PHY_REGCAP2', *r())
C('10uF', '+3V3', 'GND', *r(5.08))
for i in range(6):
    C('100nF', '+3V3', 'GND', *r())

Y3 = Y1
text('88E1512 regulator outputs: PHY_1V8 (AVDD18 x4 + AVDDC18), PHY_1V0 (DVDD x2)', 375, Y3 - 26, 1.5)
r = Row(386.08, Y3)
C('10uF', 'PHY_1V8', 'GND', *r())
for i in range(5):
    C('100nF', 'PHY_1V8', 'GND', *r())
C('10uF', 'PHY_1V0', 'GND', *r(5.08))
for i in range(2):
    C('100nF', 'PHY_1V0', 'GND', *r())
text('R24 4.99k 1 %.   XTAL_IN is in the 1.8 V AVDDC18 domain (not 3.3 V tolerant): own crystal,'
     '\n  never drive it from LAN7801 REFCLK_25.'
     '\nCONFIG = VSS -> PHYAD = 0, VDDO level 3.3 V.   VDDO_SEL = VSS (3.3 V I/O).'
     '\nInternal switched-cap regulators make PHY_1V8 / PHY_1V0; 220nF REGCAP1-REGCAP2 right at the pins.'
     '\nPHY_CLK125 reaches LAN7801 CLK125 only if R7 (0R, DNP) is fitted;'
     '\n  default: LAN7801 generates CLK125 internally (HW_CFG.CLK125_EN).', 375, Y3 + 20)
text('MDI0..3 -> magjack pairs 1/2, 3/6, 4/5, 7/8 (Auto-MDIX handles swaps).'
     '\nHR911130C: common center tap (pin 1) -> 100nF to GND, no bias (voltage-mode PHY). Pin 10 = internal Bob-Smith 1nF/2kV to chassis.'
     '\nLEDs are active-low (88E1512 default). LED0 / LED1 functions set in register 3_16.'
     '\nLED[2]/INTn -> LAN7801 PHY_INT_N needs LED[2] set to interrupt mode (reg 3_18),'
     '\n  otherwise lan78xx simply polls the PHY.', 375, Y3 + 52)

# ---------------- Block D: magjack
text('TEST PORT   RJ45 1G MAGJACK', 510, 20, 2)
place('ND2:HR911130C', 'J2', 'HR911130C', 551.18, 111.76, {
    '2': 'MDI0_P', '3': 'MDI0_N', '4': 'MDI1_P', '7': 'MDI1_N', '5': 'MDI2_P', '6': 'MDI2_N', '8': 'MDI3_P', '9': 'MDI3_N',
    '1': 'MDI_CT', '10': 'GND', '11': 'LED_A0', '12': 'PHY_LED0', '14': 'LED_A1', '13': 'PHY_LED1', 'SH': 'GND'},
    fp='ND2:RJ45_HanRun_HR911130C_Horizontal', props_pos=ic_props('ND2:HR911130C', 551.18, 111.76),
    extra=lcsc(('C50933', 'HR911130C', 'HanRun')))
r = Row(520.7, 182.88)
C('100nF', 'MDI_CT', 'GND', *r())
R('330R', '+3V3', 'LED_A0', *r(5.08))
R('330R', '+3V3', 'LED_A1', *r())

# ---------------- title notes
text('ND-2 TDR PROOF DONGLE  -  Rev A', 20, 250, 3)
text('First spin: generated from tools/gen_dongle.py, ERC clean, NOT yet reviewed by a human.'
     '\n'
     '\nPurpose: prove LAN7801 + 88E1512 bring-up and Linux'
     '\n  ethtool --cable-test / --cable-test-tdr before building the CM5 carrier.'
     '\nBus powered from USB 3 VBUS (VBUS_DET tied to 3V3). Expected load ~0.6 A at 3V3.'
     '\nRGMII delay in exactly ONE place: LAN7801 hybrid mode (MAC adds TXC + RXC delay,'
     '\n  set in EEPROM) + PHY in plain RGMII (phy-mode "rgmii", no PHY delays).'
     '\nLayout: 90R diff USB 3 / USB 2, 100R diff MDI pairs, 50R single-ended RGMII,'
     '\n  RGMII < 50 mm and matched +/-2.5 mm, crystals tight to their ICs.'
     '\nFootprints: LCSC/EasyEDA land patterns in ND2.pretty (QFN pads + EP per datasheet, thermal vias added).'
     '\nOptional: low-cap TVS on the MDI pairs.', 20, 262, 1.5)

# ================================================================ WRITE
lib_text = '\n'.join(LIBS[k]['text'] for k in sorted(USED))
out = ['(kicad_sch (version 20250610) (generator "nd2-gen") (generator_version "10.0") (uuid "%s") (paper "A2")' % ROOT_UUID,
       '(title_block (title "ND-2 TDR Proof Dongle") (date "2026-09-25") (rev "A") (company "Network Goblin")'
       ' (comment 1 "LAN7801 USB3-to-RGMII + Marvell 88E1512 PHY (VCT/TDR) + 1G magjack")'
       ' (comment 2 "First spin - generated, not yet reviewed"))',
       '(lib_symbols', lib_text, ')']
out += ITEMS
out.append('(sheet_instances (path "/" (page "1")))')
out.append('(embedded_fonts no)')
out.append(')')
os.makedirs(PROJ, exist_ok=True)
open(os.path.join(PROJ, NAME + '.kicad_sch'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
open(os.path.join(PROJ, 'ND2.kicad_sym'), 'w', encoding='utf-8').write(
    '(kicad_symbol_lib (version 20251024) (generator "nd2-gen") (generator_version "10.0")\n%s\n%s\n%s\n)\n' % (LAN_SYM, PHY_SYM, J2_SYM))
open(os.path.join(PROJ, 'sym-lib-table'), 'w').write(
    '(sym_lib_table\n  (version 7)\n  (lib (name "ND2")(type "KiCad")(uri "${KIPRJMOD}/ND2.kicad_sym")(options "")(descr "ND-2 custom symbols"))\n)\n')
pro = os.path.join(PROJ, NAME + '.kicad_pro')
if not os.path.exists(pro):
    open(pro, 'w').write('{\n  "meta": {\n    "filename": "%s.kicad_pro",\n    "version": 1\n  }\n}\n' % NAME)

with open(os.path.join(PROJ, 'netlist_report.txt'), 'w') as f:
    f.write('ND-2 TDR dongle - generated net list (net: ref.pin(name) ...)\n\n')
    for net in sorted(NETS):
        f.write('%-14s %s\n' % (net, '  '.join('%s.%s(%s)' % rp for rp in NETS[net])))
with open(os.path.join(PROJ, 'bom.csv'), 'w') as f:
    f.write('Ref,Value,Footprint,DNP,MPN,LCSC\n')
    def keyf(r):
        m = re.match(r'([A-Z#]+)(\d+)', r); return (m.group(1), int(m.group(2)))
    for ref in sorted(PARTS, key=keyf):
        lib, val, fp, dnp, ex = PARTS[ref]
        f.write('%s,"%s",%s,%s,"%s",%s\n' % (ref, val, fp, 'DNP' if dnp else '', ex.get('MPN', ''), ex.get('LCSC', '')))
# JLCPCB-style grouped BOM
groups = {}
for ref, (lib, val, fp, dnp, ex) in PARTS.items():
    if dnp:
        continue
    groups.setdefault((val, fp.split(':')[-1], ex.get('LCSC', '')), []).append(ref)
with open(os.path.join(PROJ, 'bom_jlcpcb.csv'), 'w') as f:
    f.write('Comment,Designator,Footprint,LCSC Part #,Quantity\n')
    for (val, fp, lc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
        refs.sort(key=lambda r: (re.match(r'[A-Z]+', r).group(0), int(re.search(r'\d+', r).group(0))))
        f.write('"%s","%s",%s,%s,%d\n' % (val, ','.join(refs), fp, lc, len(refs)))
open(os.path.join(PROJ, 'fp-lib-table'), 'w').write(
    '(fp_lib_table\n  (version 7)\n  (lib (name "ND2")(type "KiCad")(uri "${KIPRJMOD}/ND2.pretty")(options "")(descr "ND-2 footprints (from LCSC/EasyEDA)"))\n)\n')
missing = [r for r, v in PARTS.items() if not v[4].get('LCSC')]
print('parts without LCSC:', missing)
single = [n for n, v in NETS.items() if len(v) < 2]
print('parts', len(PARTS), 'nets', len(NETS), 'single-pin nets', single)
