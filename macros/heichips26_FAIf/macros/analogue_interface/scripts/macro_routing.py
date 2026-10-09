# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
"""Routing of the analogue_interface macro (DAC path round).

Used by build_analogue_interface.py. Every route is derived from the pin labels of the placed
blocks, so a placement change moves the routes with it. The routes go into their own cell
(PREFIX + "routing"). check() reports clearance conflicts against the placed blocks and between
nets before the real DRC/LVS runs.

Layers: Metal2/Metal3 for signals (Metal1 only at the rhigh terminals), Via1/Via2 as 0.19 um
cuts with 0.30 um square pads on both metals (0.055 um enclosure on all sides).
"""
import klayout.db as db

LAYER = {"M1": (8, 0), "M2": (10, 0), "M3": (30, 0), "M4": (50, 0),
         "V1": (19, 0), "V2": (29, 0), "V3": (49, 0)}
SPACE = {"M1": 0.18, "M2": 0.21, "M3": 0.21, "M4": 0.21, "V1": 0.22, "V2": 0.22, "V3": 0.22}
VIA = {"V1": ("M1", "M2"), "V2": ("M2", "M3"), "V3": ("M3", "M4")}
# Metal4: vertical routes only, >= 10.5 um from the chip PDN Metal4 strap groups (LibreLane removes
# straps within PDN_HORIZONTAL_HALO = 10 um of a Metal4 obstruction) and off the S&H lid.
M4_BANDS = [(0.0, 161.88), (189.88, 211.88), (239.88, 261.88), (289.88, 300.0)]
CUT, CUT_SPACE, PAD = 0.19, 0.22, 0.30
GRID = 0.005
PAD_STACK = 0.40          # middle pads of via stacks (min metal area 0.144 um2)
W_SIG = 0.30          # signal wires
W_OUT = 1.20          # DAC outputs analog_1/2 (same as the opamp OOA bar)
W_SUP = 1.11          # supply trunks (same as the translator supply bars)
W_RAIL = 0.80         # supply rails in the row gaps


class Router:
    def __init__(self, ly, top, placed, prefix):
        self.ly, self.top = ly, top
        self.placed = {k: (c, db.DCplxTrans(t), b) for k, (c, t, b) in placed.items()}
        self.cell = ly.create_cell(prefix + "routing")
        top.insert(db.DCellInstArray(self.cell.cell_index(), db.DTrans()))
        self.shapes = []      # (net, layer, DBox)
        self.touch = []       # (net, layer, DPoint): intended contact to existing block metal

    # ---- pin lookup -----------------------------------------------------------------------
    def label(self, inst, text, layer):
        cell, trans, box = self.placed[inst]
        li = self.ly.find_layer(*layer)
        hits = []
        it = cell.begin_shapes_rec(li)
        while not it.at_end():
            s = it.shape()
            if s.is_text() and s.text_string == text:
                t = s.dtext.transformed(it.dtrans())
                hits.append((trans * db.DPoint(t.x, t.y)))
            it.next()
        assert len(hits) == 1, f"{inst}: label {text!r} on {layer}: {len(hits)} hits"
        return hits[0]

    def pinbox(self, inst, text, layer):
        """Bounding box of the pin shape (datatype 2, else drawing) under a block label."""
        p = self.label(inst, text, (layer[0], 25))
        cell, trans, _ = self.placed[inst]
        for dt in (2, 0):
            li = self.ly.find_layer(layer[0], dt)
            if li is None:
                continue
            reg = db.Region(cell.begin_shapes_rec(li)).transformed(trans.to_itrans(self.ly.dbu))
            probe = db.Region(db.DBox(p.x - 0.001, p.y - 0.001, p.x + 0.001, p.y + 0.001).to_itype(self.ly.dbu))
            hit = reg.merged().interacting(probe)
            if not hit.is_empty():
                return hit.bbox().to_dtype(self.ly.dbu)
        raise AssertionError(f"{inst}: no pin shape under {text!r}")

    # ---- drawing ----------------------------------------------------------------------------
    def rect(self, net, layer, x1, y1, x2, y2):
        g = lambda v: round(v / GRID) * GRID          # manufacturing grid
        box = db.DBox(g(min(x1, x2)), g(min(y1, y2)), g(max(x1, x2)), g(max(y1, y2)))
        self.cell.shapes(self.ly.layer(*LAYER[layer])).insert(box)
        self.shapes.append((net, layer, box))

    def wire(self, net, layer, pts, w=W_SIG):
        """Manhattan wire through pts, square ends extended by w/2."""
        h = w / 2
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            assert x1 == x2 or y1 == y2, f"{net}: non-Manhattan segment {(x1, y1)}-{(x2, y2)}"
            self.rect(net, layer, min(x1, x2) - h, min(y1, y2) - h, max(x1, x2) + h, max(y1, y2) + h)

    def via(self, net, kind, x, y, nx=1, ny=1):
        """nx x ny cut array centred at (x, y) with pads on both metals."""
        x, y = round(x / GRID) * GRID, round(y / GRID) * GRID
        pitch = CUT + CUT_SPACE
        sx, sy = (nx - 1) * pitch, (ny - 1) * pitch
        lo, hi = VIA[kind]
        for m in (lo, hi):
            self.rect(net, m, x - sx / 2 - PAD / 2, y - sy / 2 - PAD / 2, x + sx / 2 + PAD / 2, y + sy / 2 + PAD / 2)
        for i in range(nx):
            for j in range(ny):
                cx, cy = x - sx / 2 + i * pitch, y - sy / 2 + j * pitch
                self.rect(net, kind, cx - CUT / 2, cy - CUT / 2, cx + CUT / 2, cy + CUT / 2)

    def contact(self, net, layer, p):
        """Declare an intended contact with existing block metal at point p."""
        self.touch.append((net, layer, db.DPoint(p.x, p.y)))

    def pin_shapes(self, inst, layer, dt=2):
        """Pin shapes (layer/dt) of a placed block, in macro coordinates, sorted by (y, x)."""
        cell, trans, _ = self.placed[inst]
        li = self.ly.find_layer(layer, dt)
        reg = db.Region(cell.begin_shapes_rec(li)).transformed(trans.to_itrans(self.ly.dbu)).merged()
        boxes = [p.bbox().to_dtype(self.ly.dbu) for p in reg.each()]
        return sorted(boxes, key=lambda b: (b.center().y, b.center().x))

    def pin_shapes_named(self, label):
        """Pin shapes (Metal3) of all 8x translators carrying a supply label (x12, x7, x6)."""
        out = []
        for inst in ("x12", "x7", "x6"):
            out.append(self.pinbox(inst, label, (30, 0)))
        return out

    def metal_under(self, inst, layer, p):
        """Bounding box of the block metal (drawing) polygon that contains point p."""
        cell, trans, _ = self.placed[inst]
        li = self.ly.find_layer(*LAYER[layer])
        reg = db.Region(cell.begin_shapes_rec(li)).transformed(trans.to_itrans(self.ly.dbu)).merged()
        probe = db.Region(db.DBox(p.x - 0.001, p.y - 0.001, p.x + 0.001, p.y + 0.001).to_itype(self.ly.dbu))
        hit = reg.interacting(probe)
        assert not hit.is_empty(), f"{inst}: no {layer} at {p}"
        return hit.bbox().to_dtype(self.ly.dbu)

    # ---- checks -----------------------------------------------------------------------------
    def check(self, exclude_cells=()):
        """Clearance conflicts of the routes against the blocks and between nets."""
        ly, dbu = self.ly, self.ly.dbu
        out = []
        for layer, sp in SPACE.items():
            li = ly.find_layer(*LAYER[layer])
            exist = db.Region()
            if li is not None:
                for inst in self.top.each_inst():
                    if inst.cell_index == self.cell.cell_index() or ly.cell(inst.cell_index).name in exclude_cells:
                        continue
                    exist += db.Region(ly.cell(inst.cell_index).begin_shapes_rec(li)).transformed(inst.cplx_trans)
                exist += db.Region(self.top.shapes(li))
            exist.merge()
            nets = sorted({n for n, l, _ in self.shapes if l == layer})
            regs = {n: db.Region([b.to_itype(dbu) for m, l, b in self.shapes if m == n and l == layer]).merged()
                    for n in nets}
            for n in nets:
                touch = db.Region([db.DBox(p.x - 0.001, p.y - 0.001, p.x + 0.001, p.y + 0.001).to_itype(dbu)
                                   for m, l, p in self.touch if m == n and l == layer])
                allowed = exist.interacting(touch) if not touch.is_empty() else db.Region()
                bad = (regs[n].sized(int(round(sp / dbu))) & exist) - allowed
                for p in bad.each():
                    out.append(f"{layer} {n}: too close to block metal at {p.bbox().to_dtype(dbu)}")
            for i, a in enumerate(nets):
                for b in nets[i + 1:]:
                    bad = regs[a].sized(int(round(sp / dbu))) & regs[b]
                    for p in bad.each():
                        out.append(f"{layer} {a} vs {b}: too close at {p.bbox().to_dtype(dbu)}")
        return out


# ================================================================================================
# iVREF divider devices (PDK PCells, made static)
# ================================================================================================
DIVIDER_PCELLS = {
    # key: (pcell, parameters) - values from heichips26_FAIf.sch
    "rhigh": ("rhigh", {"w": "0.5u", "l": "50u", "b": 0, "Calculate": "R"}),     # R1, R2
}
# iVREF filter: one block "cvref" = MOS cap C2 (sg13_hv_nmos, G = iVREF, S/D/B = VGND) with the
# MOM cap C1 (cap_cmomi Metal1/Metal2) on top of its gate. Metal3 over the block stays free.
CAP_MOS = {"w": "33.5u", "l": "48u", "ng": "1"}                                # C2: W 33.5 (y) x L 48 (x)
CAP_MOM = {"w": "31.5u", "l": "46u", "mmin": 1, "mmax": 2, "feed": "double", "subblock": 0}  # C1
MOS_W, MOS_L = 33.5, 48.0
MOM_W, MOM_L = 31.5, 46.0
MOM_OX, MOM_OY = 1.4, 1.0        # MOM origin in the MOS frame (inside the S/D Metal1 columns)
GATE_Y = MOS_W + 0.74            # gate contact row (poly band above the channel)
TIE_Y = -0.62                    # source/drain tie strip below the channel (Metal1)
# connection points in the cell frame (Metal2): VGND bottom-left, iVREF top-right
CAP_VGND = (MOM_OX - 0.65, TIE_Y)
CAP_IVREF = (MOM_OX + MOM_L + 0.39, GATE_Y)
RING = (-1.2, -1.8, MOS_L + 1.55, MOS_W + 2.5)   # p-tap ring (VGND) around the MOS cap: Activ outer box
RING_W = 0.3


def make_divider_cells(ly, prefix):
    """Generate the divider devices with the PDK PCell library, as flat static cells."""
    import os
    import sys
    k = os.path.join(os.environ["PDK_ROOT"], os.environ["PDK"], "libs.tech", "klayout", "python")
    for p in (k, os.path.join(k, "pycell4klayout-api", "source", "python")):
        if p not in sys.path:
            sys.path.append(p)
    import pya  # noqa: F401  (the PDK library registers through pya)
    import sg13cmos5l_pycell_lib  # noqa: F401
    tech = ly.technology_name
    ly.technology_name = "sg13cmos5l"
    def pcell(name, params):
        pc = ly.create_cell(name, "SG13_dev", params)
        assert pc is not None, f"PCell {name} not available"
        cell = ly.cell(ly.convert_cell_to_static(pc.cell_index()))
        cell.flatten(True)
        return cell

    cells = {}
    for key, (name, params) in DIVIDER_PCELLS.items():
        cell = pcell(name, params)
        cell.name = f"{prefix}{key}_{name}"
        cells[key] = cell

    # combined iVREF cap: MOS cap with the MOM cap on top, gate band, S/D tie, connection stubs
    cap = ly.create_cell(f"{prefix}cvref_cap")
    mos, mom = pcell("nmosHV", CAP_MOS), pcell("cap_cmomi", CAP_MOM)
    cap.insert(db.DCellInstArray(mos.cell_index(), db.DTrans()))
    cap.insert(db.DCellInstArray(mom.cell_index(), db.DTrans(MOM_OX, MOM_OY)))
    cap.flatten(True)                 # prunes the two device cells
    L_ = lambda k: ly.layer(*LAYER[k]) if k in LAYER else ly.layer(*k)
    box = lambda layer, x1, y1, x2, y2: cap.shapes(L_(layer)).insert(db.DBox(x1, y1, x2, y2))
    # gate: poly band above the channel, contact row, Metal1 strip (iVREF)
    box((5, 0), 0.34, MOS_W + 0.1, MOS_L + 0.34, MOS_W + 1.3)
    x = 0.8
    while x + 0.16 < MOS_L - 0.2:
        box((6, 0), x, GATE_Y - 0.08, x + 0.16, GATE_Y + 0.08)
        x += 0.36
    box("M1", 0.6, GATE_Y - 0.18, MOS_L, GATE_Y + 0.18)
    # source/drain: both Metal1 columns down to a tie strip below the channel (VGND)
    box("M1", 0.07, TIE_Y - 0.18, MOS_L + 0.61, TIE_Y + 0.18)
    box("M1", 0.07, TIE_Y, 0.23, 0.0)
    box("M1", MOS_L + 0.45, TIE_Y, MOS_L + 0.61, 0.0)
    # VGND: tie strip -> Via1 -> Metal2 up onto the MOM's west comb spine
    x0 = MOM_OX - 0.9
    box("M2", x0, TIE_Y - 0.18, x0 + 0.5, MOM_OY + 2.0)
    box("V1", CAP_VGND[0] - 0.095, TIE_Y - 0.095, CAP_VGND[0] + 0.095, TIE_Y + 0.095)
    # iVREF: gate strip -> Via1 -> Metal2 down onto the MOM's east comb spine
    x1 = MOM_OX + MOM_L + 0.2         # on the east comb spine, clear of the west comb's finger ends
    box("M2", x1, MOM_OY + MOM_W - 3.0, x1 + 0.38, GATE_Y + 0.18)
    box("V1", CAP_IVREF[0] - 0.095, GATE_Y - 0.095, CAP_IVREF[0] + 0.095, GATE_Y + 0.095)
    # p-tap ring (substrate tie, VGND) around the MOS cap (latch-up LU.b), tied to the S/D strip
    rx1, ry1, rx2, ry2 = RING
    w = RING_W
    for (a, b, c, d) in ((rx1, ry1, rx2, ry1 + w), (rx1, ry2 - w, rx2, ry2),
                         (rx1, ry1, rx1 + w, ry2), (rx2 - w, ry1, rx2, ry2)):
        box((1, 0), a, b, c, d)
        box("M1", a, b, c, d)
        for lay in ((14, 0), (40, 0)):
            box(lay, a - 0.03, b - 0.03, c + 0.03, d + 0.03)
    def cont_line(a, b_, c, horiz):
        n = int((b_ - a - 0.16) / 0.36) + 1
        for i in range(n):
            q = a + i * 0.36
            if horiz:
                box((6, 0), q, c - 0.08, q + 0.16, c + 0.08)
            else:
                box((6, 0), c - 0.08, q, c + 0.08, q + 0.16)
    cont_line(rx1 + 0.07, rx2 - 0.07, ry1 + w / 2, True)
    cont_line(rx1 + 0.07, rx2 - 0.07, ry2 - w / 2, True)
    cont_line(ry1 + w + 0.2, ry2 - w - 0.2, rx1 + w / 2, False)
    cont_line(ry1 + w + 0.2, ry2 - w - 0.2, rx2 - w / 2, False)
    box("M1", 0.07, ry1, 0.23, TIE_Y)                     # ring -> S/D tie strip
    box("M1", MOS_L + 0.45, ry1, MOS_L + 0.61, TIE_Y)
    cells["cvref"] = cap
    for c in list(ly.each_cell()):           # drop the library proxies left behind
        if c.is_library_cell() and c.parent_cells() == 0:
            ly.delete_cell(c.cell_index())
    ly.technology_name = tech
    return cells


# ================================================================================================
# DAC path (round 1): x12 -> x11 -> analog_2 and x7 -> x5 -> analog_1, bias, divider, supplies
# ================================================================================================
DAC_PAIRS = [
    # translator, R2R, dac_out base bit, output pin
    ("x12", "x11", 8, "analog_2"),
    ("x7", "x5", 0, "analog_1"),
]
# The PTAT (x3, now east of the comparator) is routed in the ADC round. IDACIREF of each R2R can be
# entered on Metal3 at R2R + 19.2 (between bit 3 and the R2R's Metal3 feedback line) from the west.
DIS_X = 61.9            # IDACDISABLE drop column (between nD7 and the opamp's UNBUF_DAC Metal3)
DIS_DY = 0.8            # IDACDISABLE track above the R2R bottom (onto the POAVSS rail)
VREF_X = 173.6          # iVREF trunk (Metal2), just east of the R2R column
VTAP_DY = 2.5           # IDACVTAP exit track above the R2R bottom (above the opamp POAVSS rail)
VTAP_EXIT_DX = 33.0     # exit column east of IDACVTAP: past the POAVSS rail end, before the output stage
VTAP_GAP = 0.8          # iVREF run below the R2R bottom edge (in the row gap)
OUT_ROUTE = {           # DAC outputs (Metal3, W_OUT): x of the down-leg, y of the south-channel run.
    # analog_1 stays >= 4 um from the S&H SH_IN route (Metal3 at x 186.2, y 26.3-44) and clear of the
    # S&H west edge (x 179.2 above y 45.5); analog_2 goes down first, west of analog_1.
    "analog_2": dict(x_down=175.6, y_south=4.5),
    "analog_1": dict(x_down=178.3, y_south=7.0),
}
TRUNK = {"VPWR": "PLDVDD", "VGND": "PLVSS", "VAPWR": "PLAVDD"}   # 8x translator supply bar per net
RAIL_X1 = 100.0         # supply rails run east to here; tabs at x 95-100 reach the R2R opamp rails
DIVIDER_X = 118.0       # west end of the divider devices (placement in the builder)


def route_dac_path(r, pins):
    """Draw the DAC-path routes. pins: macro pins {name: (LEF layer, DBox)}."""
    for tr, dac, base, out in DAC_PAIRS:
        y0 = r.placed[dac][2].bottom

        # dac_out[k]: Metal3 stub from the west pin to LINk, Via2 down onto the LIN Metal2 pad
        for k in range(8):
            name = f"dac_out[{base + k}]"
            wp = pins[name][1]
            yw = wp.center().y
            lin = r.label(tr, f"LIN{k}", (10, 25))
            r.wire(name, "M3", [(wp.left + 0.2, yw), (lin.x, yw), (lin.x, lin.y)])
            r.via(name, "V2", lin.x, lin.y)
            r.contact(name, "M3", db.DPoint(wp.left + 0.2, yw))
            r.contact(name, "M2", lin)

        # bits: nLOUTk -> nDk. Metal3 east along the nLOUT row; bits above the nD row drop on
        # Metal2 onto the pad stack, bits below go up on Metal3 (staircase, no crossings).
        for k in range(8):
            net = f"{dac}_nd{k}"
            nl = r.label(tr, f"nLOUT{k}", (10, 25))
            nd = r.pinbox(dac, f"nD{k}", (30, 0)).center()
            r.via(net, "V2", nl.x, nl.y)
            r.contact(net, "M2", nl)
            if nl.y > nd.y:
                r.wire(net, "M3", [(nl.x, nl.y), (nd.x, nl.y)])
                r.via(net, "V2", nd.x, nl.y)
                r.wire(net, "M2", [(nd.x, nl.y), (nd.x, nd.y)])
                r.contact(net, "M2", nd)
            else:
                r.wire(net, "M3", [(nl.x, nl.y), (nd.x, nl.y), (nd.x, nd.y)])
                r.contact(net, "M3", nd)

        # IDACDISABLE -> VGND: west on Metal3, down the drop column, east onto the POAVSS rail
        dp = r.label(dac, "IDACDISABLE", (30, 25))
        rail = r.metal_under(dac, "M3", r.label(dac, "PDACVSS", (30, 25)))
        yd = y0 + DIS_DY
        r.wire("VGND", "M3", [(dp.x, dp.y), (DIS_X, dp.y), (DIS_X, yd), (rail.left + 0.5, yd)])
        r.contact("VGND", "M3", dp)
        r.contact("VGND", "M3", db.DPoint(rail.left + 0.5, yd))

        # DAC output: from the OOA bar at the R2R east edge down to the south pin
        ob = r.metal_under(dac, "M3", r.label(dac, "ODACOUT", (30, 25)))
        yo = ob.center().y
        sp = pins[out][1]
        c = OUT_ROUTE[out]
        pts = [(ob.right - 0.6, yo), (c["x_down"], yo), (c["x_down"], c["y_south"]), (sp.center().x, c["y_south"])]
        r.wire(out, "M3", pts, W_OUT)
        r.contact(out, "M3", db.DPoint(ob.right - 0.6, yo))
        r.via(out, "V2", sp.center().x, c["y_south"], 2, 2)
        r.wire(out, "M2", [(sp.center().x, c["y_south"]), (sp.center().x, sp.top - 0.5)], sp.width())
        r.contact(out, "M2", db.DPoint(sp.center().x, sp.top - 0.5))

    # iVREF into IDACVTAP of all three DACs (one net; x4 included): IDACVTAP is boxed in by the opamp
    # on Metal3 except towards the south, so drop to just above the POAVSS rail, run east under the
    # opamp to a gap between the rail end and the output stage, leave the R2R through its bottom edge
    # and run along the row gap to the trunk.
    for dac in ("x11", "x5", "x4"):
        y0 = r.placed[dac][2].bottom
        vt = r.label(dac, "IDACVTAP", (30, 25))
        xe, ya, yg = vt.x + VTAP_EXIT_DX, y0 + VTAP_DY, y0 - VTAP_GAP
        r.wire("iVREF", "M3", [(vt.x, vt.y), (vt.x, ya), (xe, ya), (xe, yg), (VREF_X, yg)])
        r.contact("iVREF", "M3", vt)
        r.via("iVREF", "V2", VREF_X, yg)

    route_supplies(r, pins)
    route_divider(r, pins)


def route_supplies(r, pins):
    """Translator supply bars extended to Metal3 trunks up to the straps; rails to the R2R/PTAT."""
    bars = {net: r.pin_shapes_named(TRUNK[net]) for net in TRUNK}
    xs = {net: (min(b.left for b in bars[net]), max(b.right for b in bars[net])) for net in TRUNK}
    strap = {net: pins[net][1] for net in TRUNK}
    xc = {net: (x1 + x2) / 2 for net, (x1, x2) in xs.items()}

    # trunks (Metal3) - VGND starts low to feed the rail under x11
    lo = {"VPWR": min(b.bottom for b in bars["VPWR"]), "VAPWR": min(b.bottom for b in bars["VAPWR"]),
          "VGND": r.placed["x11"][2].bottom - 2.6}
    for net in TRUNK:
        x1, x2 = xs[net]
        for b in bars[net]:
            r.contact(net, "M3", b.center())
        if net == "VPWR":
            r.rect(net, "M3", x1, lo[net], x2, strap[net].top)
            r.contact(net, "M3", db.DPoint(xc[net], strap[net].center().y))
            continue
        # VGND/VAPWR cross the lower straps on Metal2
        top3 = strap["VPWR"].bottom - 1.0
        r.rect(net, "M3", x1, lo[net], x2, top3)
        r.via(net, "V2", xc[net], top3 - 0.3, 2, 1)
        r.wire(net, "M2", [(xc[net], top3 - 0.3), (xc[net], strap[net].center().y)], x2 - x1)
        r.via(net, "V2", xc[net], strap[net].center().y, 2, 2)
        r.contact(net, "M3", db.DPoint(xc[net], strap[net].center().y))

    def rail(net, y, x_end, hop):
        """Metal3 rail from a trunk east to x_end; VGND hops under the VAPWR trunk on Metal2."""
        x0 = xc[net]
        if hop:
            xh = xs["VAPWR"][1] + 0.8
            r.via(net, "V2", x0, y)
            r.wire(net, "M2", [(x0, y), (xh, y)], W_RAIL)
            r.via(net, "V2", xh, y)
            x0 = xh
        r.wire(net, "M3", [(x0, y), (x_end, y)], W_RAIL)

    def tab(net, inst, label, y):
        """Short Metal3 tab from a rail at y onto the R2R opamp rail (PDACVDD/PDACVSS)."""
        m = r.metal_under(inst, "M3", r.label(inst, label, (30, 25)))
        x1 = RAIL_X1 - 4.0
        y1, y2 = (m.center().y, y) if y > m.center().y else (y, m.center().y)
        r.rect(net, "M3", x1, y1, RAIL_X1, y2)
        r.contact(net, "M3", db.DPoint((x1 + RAIL_X1) / 2, m.center().y))

    b11, b5, b4 = (r.placed[i][2] for i in ("x11", "x5", "x4"))
    # under x11: VGND onto its PDACVSS
    y = b11.bottom - 2.2
    rail("VGND", y, RAIL_X1, hop=False)
    tab("VGND", "x11", "PDACVSS", y)
    # gap x11/x5: VAPWR onto x11 PDACVDD, VGND onto x5 PDACVSS
    y = b11.top + 1.7
    rail("VAPWR", y, RAIL_X1, hop=False)
    tab("VAPWR", "x11", "PDACVDD", y)
    y = b5.bottom - 1.8
    rail("VGND", y, RAIL_X1, hop=True)
    tab("VGND", "x5", "PDACVSS", y)
    # gap x5/x4: VAPWR onto x5 PDACVDD, VGND onto x4 PDACVSS (y ~83.9 stays free for SH_EN)
    y = b5.top + 1.5
    rail("VAPWR", y, RAIL_X1, hop=False)
    tab("VAPWR", "x5", "PDACVDD", y)
    y = b4.bottom - 1.2
    rail("VGND", y, RAIL_X1, hop=True)
    tab("VGND", "x4", "PDACVSS", y)
    # above x4: VAPWR onto its PDACVDD (the PTAT supplies follow when the PTAT has moved)
    y = b4.top + 1.7
    rail("VAPWR", y, RAIL_X1, hop=False)
    tab("VAPWR", "x4", "PDACVDD", y)


def route_divider(r, pins):
    """R1 (VAPWR-iVREF), R2 (iVREF-VGND), C1 (iVREF-VGND) and the iVREF trunk."""
    pads1 = sorted(r.pin_shapes("R1", 8), key=lambda b: b.center().x)
    pads2 = sorted(r.pin_shapes("R2", 8), key=lambda b: b.center().x)
    ccell, ctr, cb = r.placed["C1"]
    cap_vgnd = ctr * db.DPoint(*CAP_VGND)
    cap_ivref = ctr * db.DPoint(*CAP_IVREF)
    x_vgnd, x_vapwr = DIVIDER_X - 3.0, DIVIDER_X - 1.0
    # west ends: R1 -> VAPWR riser, R2 and C1 low bar -> VGND riser
    p = pads1[0].center()
    r.via("VAPWR", "V1", p.x, p.y)
    r.contact("VAPWR", "M1", p)
    r.wire("VAPWR", "M2", [(p.x, p.y), (x_vapwr, p.y), (x_vapwr, pins["VAPWR"][1].center().y)])
    r.via("VAPWR", "V2", x_vapwr, pins["VAPWR"][1].center().y, 1, 2)
    r.contact("VAPWR", "M3", db.DPoint(x_vapwr, pins["VAPWR"][1].center().y))
    p = pads2[0].center()
    r.via("VGND", "V1", p.x, p.y)
    r.contact("VGND", "M1", p)
    r.wire("VGND", "M2", [(p.x, p.y), (x_vgnd, p.y)])
    yl = cap_vgnd.y
    r.wire("VGND", "M2", [(cap_vgnd.x, yl), (x_vgnd, yl)])
    r.contact("VGND", "M2", cap_vgnd)
    r.wire("VGND", "M2", [(x_vgnd, yl), (x_vgnd, pins["VGND"][1].center().y)])
    r.via("VGND", "V2", x_vgnd, pins["VGND"][1].center().y, 1, 2)
    r.contact("VGND", "M3", db.DPoint(x_vgnd, pins["VGND"][1].center().y))
    # east ends: R1, R2 and C1 high bar -> iVREF trunk
    top = pads1[-1].center().y
    for pad in (pads1[-1], pads2[-1]):
        p = pad.center()
        r.via("iVREF", "V1", p.x, p.y)
        r.contact("iVREF", "M1", p)
        r.wire("iVREF", "M2", [(p.x, p.y), (VREF_X, p.y)])
    r.wire("iVREF", "M2", [(cap_ivref.x, cap_ivref.y), (VREF_X, cap_ivref.y)])
    r.contact("iVREF", "M2", cap_ivref)
    y_low = r.placed["x11"][2].bottom - VTAP_GAP
    r.wire("iVREF", "M2", [(VREF_X, top), (VREF_X, y_low)])


# ================================================================================================
# Connectivity check (metal-only extraction): every probe of a net on one island, nets distinct
# ================================================================================================
def dac_probes(r, pins):
    """(net, layer, point) for every pin of the DAC-path nets."""
    P = []
    add = lambda n, l, p: P.append((n, l, db.DPoint(p.x, p.y)))
    for tr, dac, base, out in DAC_PAIRS:
        for k in range(8):
            name = f"dac_out[{base + k}]"
            add(name, "M3", pins[name][1].center())
            add(name, "M2", r.label(tr, f"LIN{k}", (10, 25)))
            add(f"{dac}_nd{k}", "M2", r.label(tr, f"nLOUT{k}", (10, 25)))
            add(f"{dac}_nd{k}", "M3", r.pinbox(dac, f"nD{k}", (30, 0)).center())
        add(out, "M3", r.label(dac, "ODACOUT", (30, 25)))
        add(out, "M2", pins[out][1].center())
        add("VGND", "M3", r.label(dac, "IDACDISABLE", (30, 25)))
    for dac in ("x11", "x5", "x4"):
        add("iVREF", "M3", r.label(dac, "IDACVTAP", (30, 25)))
        add("VAPWR", "M3", r.label(dac, "PDACVDD", (30, 25)))
        add("VGND", "M3", r.label(dac, "PDACVSS", (30, 25)))
    for tr in ("x12", "x7", "x6"):
        for net, lab in TRUNK.items():
            add(net, "M3", r.pinbox(tr, lab, (30, 0)).center())
    for net in TRUNK:
        add(net, "M3", pins[net][1].center())
    p1 = sorted(r.pin_shapes("R1", 8), key=lambda b: b.center().x)
    p2 = sorted(r.pin_shapes("R2", 8), key=lambda b: b.center().x)
    add("VAPWR", "M1", p1[0].center()); add("iVREF", "M1", p1[-1].center())
    add("VGND", "M1", p2[0].center()); add("iVREF", "M1", p2[-1].center())
    ctr = r.placed["C1"][1]
    add("VGND", "M2", ctr * db.DPoint(*CAP_VGND)); add("iVREF", "M2", ctr * db.DPoint(*CAP_IVREF))
    return P


def connectivity(ly, top, probes):
    """Metal-only net extraction of the macro; returns a list of problems (empty = OK)."""
    l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly, top, []))
    lay = {k: l2n.make_layer(ly.layer(*v), k) for k, v in LAYER.items()}
    for k in ("M1", "M2", "M3"):
        l2n.connect(lay[k])
    for v, (lo, hi) in VIA.items():
        l2n.connect(lay[v])
        l2n.connect(lay[lo], lay[v])
        l2n.connect(lay[v], lay[hi])
    l2n.extract_netlist()
    island = {}
    out = []
    for net, layer, p in probes:
        n = l2n.probe_net(lay[layer], p)
        if n is None:
            out.append(f"{net}: no {layer} at {p}")
            continue
        island.setdefault(net, set()).add(n.cluster_id)
    for net, ids in island.items():
        if len(ids) > 1:
            out.append(f"{net}: split over {len(ids)} metal islands")
    owner = {}
    for net, ids in island.items():
        for i in ids:
            if i in owner and owner[i] != net:
                out.append(f"short: {owner[i]} and {net} on one metal island")
            owner[i] = net
    return out


# ================================================================================================
# Round 2: SAR DAC, ADC front end, PTAT, small translators, east supplies
# ================================================================================================
SAR_PAIR = ("x6", "x4", "adc_ref[{}]")
IREF_DY = 19.2                       # IDACIREF entry track above an R2R's bottom (from the west)
IREF_ROUTE = [                       # PTAT output, net, R2R, westward track y, west-channel drop x
    ("CSOUT4", "iIREF4", "x11", 136.5, 19.0),
    ("CSOUT2", "iIREF2", "x4", 141.5, 21.0),
    ("CSOUT3", "iIREF3", "x5", 143.0, 20.0),
]
COMP_GAP_X = 203.9                   # gap between comparator x1 and PTAT x3
PBIAS_Y = 139.0
COMP_OUT_Y = 152.0                   # iSAR_COMP westward track
SH_EN_Y = 155.0                      # SH_EN eastward track
SH_EN_M4_X = 245.0                   # SH_EN Metal4 drop east of the S&H/PTAT
SH_IN_X = 227.0                      # SH_IN Metal2 riser in the corridor east of the S&H
SH_IN_Y = 43.9                       # SH_IN run between the opamp top and the S&H bottom
VAPWR_E_X, VGND_E_X = 262.0, 297.0   # east supply trunks (Metal3)
IREF1_X, IREF1_Y = 295.0, 117.3      # iIREF1: east down-leg, run below the PTAT outputs
W_SUP_E = 1.0


def stack(r, net, x, y, lo, hi):
    """Via stack from metal lo to metal hi at (x, y)."""
    order = ["M1", "M2", "M3", "M4"]
    vias = {("M1", "M2"): "V1", ("M2", "M3"): "V2", ("M3", "M4"): "V3"}
    for a, b in zip(order[order.index(lo):order.index(hi)], order[order.index(lo) + 1:order.index(hi) + 1]):
        r.via(net, vias[(a, b)], x, y)
    h = PAD_STACK / 2
    for m in order[order.index(lo) + 1:order.index(hi)]:
        r.rect(net, m, x - h, y - h, x + h, y + h)


def route_rest(r, pins):
    straps = {n: pins[n][1] for n in ("VPWR", "VGND", "VAPWR")}
    sy = {n: b.center().y for n, b in straps.items()}

    def strap_drop(net, x, y_from, layer_from="M3"):
        """Riser from (x, y_from) up to the strap of net; crosses lower straps on Metal2."""
        if layer_from == "M3":
            top3 = straps["VPWR"].bottom - 1.0
            r.wire(net, "M3", [(x, y_from), (x, top3)], W_SUP_E)
            r.via(net, "V2", x, top3 - 0.3, 2, 1)
            y_from = top3 - 0.3
        r.wire(net, "M2", [(x, y_from), (x, sy[net])], W_SUP_E)
        r.via(net, "V2", x, sy[net], 2, 2)
        r.contact(net, "M3", db.DPoint(x, sy[net]))

    # ---- SAR DAC: adc_ref stubs, x6 -> x4 bits, x4 IDACDISABLE -------------------------------
    tr, dac, fmt = SAR_PAIR
    y0 = r.placed[dac][2].bottom
    for k in range(8):
        name = fmt.format(k)
        wp = pins[name][1]
        lin = r.label(tr, f"LIN{k}", (10, 25))
        r.wire(name, "M3", [(wp.left + 0.2, wp.center().y), (lin.x, wp.center().y), (lin.x, lin.y)])
        r.via(name, "V2", lin.x, lin.y)
        r.contact(name, "M3", db.DPoint(wp.left + 0.2, wp.center().y))
        r.contact(name, "M2", lin)
        net = f"{dac}_nd{k}"
        nl = r.label(tr, f"nLOUT{k}", (10, 25))
        nd = r.pinbox(dac, f"nD{k}", (30, 0)).center()
        r.via(net, "V2", nl.x, nl.y)
        r.contact(net, "M2", nl)
        if nl.y > nd.y:
            r.wire(net, "M3", [(nl.x, nl.y), (nd.x, nl.y)])
            r.via(net, "V2", nd.x, nl.y)
            r.wire(net, "M2", [(nd.x, nl.y), (nd.x, nd.y)])
            r.contact(net, "M2", nd)
        else:
            r.wire(net, "M3", [(nl.x, nl.y), (nd.x, nl.y), (nd.x, nd.y)])
            r.contact(net, "M3", nd)
    dp = r.label(dac, "IDACDISABLE", (30, 25))
    rail = r.metal_under(dac, "M3", r.label(dac, "PDACVSS", (30, 25)))
    r.wire("VGND", "M3", [(dp.x, dp.y), (DIS_X, dp.y), (DIS_X, y0 + DIS_DY), (rail.left + 0.5, y0 + DIS_DY)])
    r.contact("VGND", "M3", dp)
    r.contact("VGND", "M3", db.DPoint(rail.left + 0.5, y0 + DIS_DY))

    # ---- iSAR_DAC: x4 ODACOUT -> comparator INP (Metal3 x 173.4-173.8, then east) -------------
    ob = r.metal_under("x4", "M3", r.label("x4", "ODACOUT", (30, 25)))
    inp = r.label("x1", "INP", (30, 25))
    r.wire("iSAR_DAC", "M3", [(ob.right - 0.6, ob.center().y), (VREF_X, ob.center().y), (VREF_X, inp.y), (inp.x, inp.y)], 0.4)
    r.contact("iSAR_DAC", "M3", db.DPoint(ob.right - 0.6, ob.center().y))
    r.contact("iSAR_DAC", "M3", inp)

    # ---- S&H: SH_OUT straight up into INN, VSS hop onto the comparator GNDA --------------------
    so, inn = r.label("x10", "SH_OUT", (30, 25)), r.label("x1", "INN", (30, 25))
    r.wire("iSAR_AN", "M3", [(so.x, so.y), (inn.x, inn.y)], 0.4)
    r.contact("iSAR_AN", "M3", so); r.contact("iSAR_AN", "M3", inn)
    vs, gn = r.label("x10", "VSS", (30, 25)), r.label("x1", "GNDA", (8, 25))
    gb = r.pinbox("x1", "GNDA", (8, 0))
    r.wire("VGND", "M3", [(vs.x, vs.y), (vs.x, gb.center().y)], 0.4)
    r.contact("VGND", "M3", vs)
    stack(r, "VGND", vs.x, gb.center().y, "M1", "M3")
    r.contact("VGND", "M1", db.DPoint(vs.x, gb.center().y))
    # comparator GNDA (and with it the S&H VSS) -> VGND strap: Metal2 west of the comparator
    xg = 176.5
    stack(r, "VGND", gb.left + 0.4, gb.center().y, "M1", "M2")
    r.contact("VGND", "M1", db.DPoint(gb.left + 0.4, gb.center().y))
    r.wire("VGND", "M2", [(gb.left + 0.4, gb.center().y), (xg, gb.center().y), (xg, sy["VGND"])], 0.6)
    r.via("VGND", "V2", xg, sy["VGND"], 1, 2)
    r.contact("VGND", "M3", db.DPoint(xg, sy["VGND"]))
    # comparator VCCA -> VAPWR strap (Metal2 riser)
    vb = r.pinbox("x1", "VCCA", (8, 0))
    xv = vb.right - 0.6
    stack(r, "VAPWR", xv, vb.center().y, "M1", "M2")
    r.contact("VAPWR", "M1", db.DPoint(xv, vb.center().y))
    r.wire("VAPWR", "M2", [(xv, vb.center().y), (xv, sy["VAPWR"])], 0.6)
    r.via("VAPWR", "V2", xv, sy["VAPWR"], 1, 2)
    r.contact("VAPWR", "M3", db.DPoint(xv, sy["VAPWR"]))

    # ---- SH_IN: opamp OOA (west end) -> along the S&H bottom -> corridor -> S&H east pin -------
    oo = r.metal_under("x8", "M3", r.label("x8", "OOA", (30, 25)))
    si = r.label("x10", "SH_IN", (30, 25))
    x_w = oo.left - 1.4
    r.wire("sh_in", "M3", [(oo.left + 0.3, oo.center().y), (x_w, oo.center().y), (x_w, SH_IN_Y), (SH_IN_X, SH_IN_Y)], 0.4)
    r.contact("sh_in", "M3", db.DPoint(oo.left + 0.3, oo.center().y))
    r.via("sh_in", "V2", SH_IN_X, SH_IN_Y)
    r.wire("sh_in", "M2", [(SH_IN_X, SH_IN_Y), (SH_IN_X, si.y)], 0.4)
    r.via("sh_in", "V2", SH_IN_X, si.y)
    r.wire("sh_in", "M3", [(SH_IN_X, si.y), (si.x, si.y)], 0.4)
    r.contact("sh_in", "M3", si)
    # opamp unity-gain loop: OOA bar east end -> IOAM
    am = r.label("x8", "IOAM", (30, 25))
    r.wire("sh_in", "M3", [(oo.right - 0.3, oo.center().y), (am.x, oo.center().y), (am.x, am.y)])
    r.contact("sh_in", "M3", db.DPoint(oo.right - 0.3, oo.center().y)); r.contact("sh_in", "M3", am)

    # ---- analog_0 -> opamp IOAP: south out of the opamp (like IDACVTAP), Metal2 to the pin -----
    ap = r.label("x8", "IOAP", (30, 25))
    y8 = r.placed["x8"][2].bottom
    xe = ap.x - VTAP_EXIT_DX
    a0 = pins["analog_0"][1]
    r.wire("analog_0", "M3", [(ap.x, ap.y), (ap.x, y8 + VTAP_DY), (xe, y8 + VTAP_DY), (xe, y8 - VTAP_GAP)])
    r.contact("analog_0", "M3", ap)
    r.via("analog_0", "V2", xe, y8 - VTAP_GAP)
    ya = a0.top + 0.6
    r.wire("analog_0", "M2", [(xe, y8 - VTAP_GAP), (xe, ya), (a0.center().x, ya), (a0.center().x, a0.top - 0.5)])
    r.contact("analog_0", "M2", db.DPoint(a0.center().x, a0.top - 0.5))

    # ---- east supplies: VAPWR trunk (S&H VDD, PTAT PCSVDD, opamp POAVDD), VGND trunk ------------
    pv = r.metal_under("x8", "M3", r.label("x8", "POAVDD", (30, 25)))
    r.rect("VAPWR", "M3", VAPWR_E_X - W_SUP_E / 2, pv.center().y, VAPWR_E_X + W_SUP_E / 2, straps["VPWR"].bottom - 1.0)
    r.contact("VAPWR", "M3", db.DPoint(VAPWR_E_X, pv.center().y))
    strap_drop("VAPWR", VAPWR_E_X, straps["VPWR"].bottom - 1.0)
    vd = r.label("x10", "VDD", (30, 25))
    r.wire("VAPWR", "M3", [(vd.x, vd.y), (VAPWR_E_X, vd.y)], 0.5)
    r.contact("VAPWR", "M3", vd)
    pc = r.pinbox("x3", "PCSVDD", (10, 0))
    r.wire("VAPWR", "M2", [(pc.right - 0.5, pc.center().y), (VAPWR_E_X, pc.center().y)], 0.5)
    r.contact("VAPWR", "M2", db.DPoint(pc.right - 0.5, pc.center().y))
    r.via("VAPWR", "V2", VAPWR_E_X, pc.center().y)
    pg = r.metal_under("x8", "M3", r.label("x8", "POAVSS", (30, 25)))
    yb = pg.bottom - 1.2
    r.rect("VGND", "M3", VGND_E_X - W_SUP_E / 2, yb - 0.4, VGND_E_X + W_SUP_E / 2, straps["VPWR"].bottom - 1.0)
    strap_drop("VGND", VGND_E_X, straps["VPWR"].bottom - 1.0)
    r.wire("VGND", "M3", [(VGND_E_X, yb), (pg.right - 2.0, yb)], 0.8)
    r.rect("VGND", "M3", pg.right - 4.0, yb, pg.right - 2.0, pg.center().y)
    r.contact("VGND", "M3", db.DPoint(pg.right - 3.0, pg.center().y))
    dis = r.label("x8", "IOADISABLE", (30, 25))
    r.wire("VGND", "M3", [(dis.x, dis.y), (VGND_E_X, dis.y)])
    r.contact("VGND", "M3", dis)
    ps = r.pinbox("x3", "PCSVSS", (10, 0))
    xs = ps.right - 1.0
    r.wire("VGND", "M2", [(xs, ps.center().y), (xs, sy["VGND"])], W_SUP_E)
    r.contact("VGND", "M2", db.DPoint(xs, ps.center().y))
    r.via("VGND", "V2", xs, sy["VGND"], 2, 2)
    r.contact("VGND", "M3", db.DPoint(xs, sy["VGND"]))

    # ---- PTAT outputs --------------------------------------------------------------------------
    # iIREF1 -> opamp IOAIREF: down below the outputs, east (Metal2 outside the PTAT), down the east edge
    c1 = r.label("x3", "CSOUT1", (10, 25))
    ai = r.label("x8", "IOAIREF", (30, 25))
    xo = r.placed["x3"][2].right + 0.6
    r.via("iIREF1", "V2", c1.x, c1.y); r.contact("iIREF1", "M2", c1)
    r.wire("iIREF1", "M3", [(c1.x, c1.y), (c1.x, IREF1_Y), (xo, IREF1_Y)])
    r.via("iIREF1", "V2", xo, IREF1_Y)
    r.wire("iIREF1", "M2", [(xo, IREF1_Y), (IREF1_X, IREF1_Y)])
    r.via("iIREF1", "V2", IREF1_X, IREF1_Y)
    yi = y8 + IREF_DY
    r.wire("iIREF1", "M3", [(IREF1_X, IREF1_Y), (IREF1_X, yi), (ai.x, yi), (ai.x, ai.y)])
    r.contact("iIREF1", "M3", ai)
    # PBIAS -> comparator PBIAS (Metal2 pin at its top): up, west, Metal2 drop
    pb, cb_ = r.label("x3", "PBIAS", (10, 25)), r.label("x1", "PBIAS", (10, 25))
    r.via("iPBIAS", "V2", pb.x, pb.y); r.contact("iPBIAS", "M2", pb)
    r.wire("iPBIAS", "M3", [(pb.x, pb.y), (pb.x, PBIAS_Y), (cb_.x, PBIAS_Y)])
    r.via("iPBIAS", "V2", cb_.x, PBIAS_Y)
    r.wire("iPBIAS", "M2", [(cb_.x, PBIAS_Y), (cb_.x, cb_.y)])
    r.contact("iPBIAS", "M2", cb_)
    # iIREF2/3/4 -> IDACIREF of x4/x5/x11: up, west over the top area, Metal2 drop in the west channel
    for cs_lab, net, dac_, yw, xd in IREF_ROUTE:
        cs = r.label("x3", cs_lab, (10, 25))
        r.via(net, "V2", cs.x, cs.y); r.contact(net, "M2", cs)
        r.wire(net, "M3", [(cs.x, cs.y), (cs.x, yw), (xd, yw)])
        r.via(net, "V2", xd, yw)
        yh = r.placed[dac_][2].bottom + IREF_DY
        r.wire(net, "M2", [(xd, yw), (xd, yh)])
        r.via(net, "V2", xd, yh)
        ip = r.label(dac_, "IDACIREF", (30, 25))
        r.wire(net, "M3", [(xd, yh), (ip.x, yh), (ip.x, ip.y)])
        r.contact(net, "M3", ip)

    # ---- iSAR_COMP: comparator OUT -> east gap -> north -> west -> x2 DIN -----------------------
    co = r.pinbox("x1", "OUT", (8, 0)).center()
    di = r.label("x2", "DIN", (8, 25))
    stack(r, "iSAR_COMP", co.x, co.y, "M1", "M2"); r.contact("iSAR_COMP", "M1", co)
    r.wire("iSAR_COMP", "M2", [(co.x, co.y), (COMP_GAP_X, co.y), (COMP_GAP_X, COMP_OUT_Y)])
    r.via("iSAR_COMP", "V2", COMP_GAP_X, COMP_OUT_Y)
    xc2 = 22.0
    r.wire("iSAR_COMP", "M3", [(COMP_GAP_X, COMP_OUT_Y), (xc2, COMP_OUT_Y)])
    r.via("iSAR_COMP", "V2", xc2, COMP_OUT_Y)
    r.wire("iSAR_COMP", "M2", [(xc2, COMP_OUT_Y), (xc2, di.y)])
    r.via("iSAR_COMP", "V2", xc2, di.y)
    xh = TRUNK_X_HOP = 13.6
    r.wire("iSAR_COMP", "M3", [(xc2, di.y), (xh, di.y)])
    r.via("iSAR_COMP", "V2", xh, di.y)
    r.wire("iSAR_COMP", "M2", [(xh, di.y), (di.x, di.y)])
    r.via("iSAR_COMP", "V1", di.x, di.y); r.contact("iSAR_COMP", "M1", di)
    # x2 DOUT -> adc_comp west pin (Metal2 under nothing), x2 supplies onto the trunks
    do_ = r.label("x2", "DOUT", (8, 25))
    wp = pins["adc_comp"][1]
    r.via("adc_comp", "V2", wp.left + 0.5, wp.center().y)
    r.contact("adc_comp", "M3", db.DPoint(wp.left + 0.5, wp.center().y))
    r.wire("adc_comp", "M2", [(wp.left + 0.5, wp.center().y), (do_.x, wp.center().y), (do_.x, do_.y)])
    r.via("adc_comp", "V1", do_.x, do_.y); r.contact("adc_comp", "M1", do_)
    bars = {net: r.pinbox("x12", lab, (30, 0)) for net, lab in TRUNK.items()}
    tx = {net: b.center().x for net, b in bars.items()}

    def tap(inst, lab, net):
        """Metal1 supply pin of a small translator -> via stack onto the supply trunk above it."""
        pbx = r.pinbox(inst, lab, (8, 0))
        y = pbx.center().y
        x1 = min(pbx.left + 0.2, tx[net]); x2 = max(pbx.right - 0.2, tx[net])
        r.wire(net, "M1", [(x1, y), (x2, y)], 0.3)
        r.contact(net, "M1", pbx.center())
        stack(r, net, tx[net], y, "M1", "M3")
        r.contact(net, "M3", db.DPoint(tx[net], y))
    tap("x2", "PDIGVDD", "VPWR"); tap("x2", "PDIGVSS", "VGND")

    # ---- x9 (adc_hold -> SH_EN) and the spare translators xcap0-3 -------------------------------
    for inst, pin in (("x9", "adc_hold"), ("xcap0", "sh_cap_en[0]"), ("xcap1", "sh_cap_en[1]"),
                      ("xcap2", "sh_cap_en[2]"), ("xcap3", "sh_cap_en[3]")):
        lin = r.label(inst, "LIN", (10, 25))
        wp = pins[pin][1]
        r.via(pin, "V2", wp.left + 0.5, wp.center().y)
        r.contact(pin, "M3", db.DPoint(wp.left + 0.5, wp.center().y))
        r.wire(pin, "M2", [(wp.left + 0.5, wp.center().y), (lin.x, wp.center().y), (lin.x, lin.y)])
        r.contact(pin, "M2", lin)
        tap(inst, "PLAVDD", "VAPWR"); tap(inst, "PLDVDD", "VPWR"); tap(inst, "PLVSS", "VGND")
    lo = r.label("x9", "LOUT", (10, 25))
    sh = r.label("x10", "SH_EN", (30, 25))
    xs1, xs2 = TRUNK_X_HOP, 23.5
    r.wire("sh_en", "M2", [(lo.x, lo.y), (xs1, lo.y)]); r.contact("sh_en", "M2", lo)
    r.via("sh_en", "V2", xs1, lo.y)
    r.wire("sh_en", "M3", [(xs1, lo.y), (xs2, lo.y)])
    r.via("sh_en", "V2", xs2, lo.y)
    r.wire("sh_en", "M2", [(xs2, lo.y), (xs2, SH_EN_Y)])
    r.via("sh_en", "V2", xs2, SH_EN_Y)
    r.wire("sh_en", "M3", [(xs2, SH_EN_Y), (SH_EN_M4_X, SH_EN_Y)])
    r.via("sh_en", "V3", SH_EN_M4_X, SH_EN_Y)
    r.wire("sh_en", "M4", [(SH_EN_M4_X, SH_EN_Y), (SH_EN_M4_X, sh.y)])
    r.via("sh_en", "V3", SH_EN_M4_X, sh.y)
    r.wire("sh_en", "M3", [(SH_EN_M4_X, sh.y), (sh.x, sh.y)])
    r.contact("sh_en", "M3", sh)


def rest_probes(r, pins):
    P = []
    add = lambda n, l, p: P.append((n, l, db.DPoint(p.x, p.y)))
    tr, dac, fmt = SAR_PAIR
    for k in range(8):
        add(fmt.format(k), "M3", pins[fmt.format(k)][1].center()); add(fmt.format(k), "M2", r.label(tr, f"LIN{k}", (10, 25)))
        add(f"{dac}_nd{k}", "M2", r.label(tr, f"nLOUT{k}", (10, 25))); add(f"{dac}_nd{k}", "M3", r.pinbox(dac, f"nD{k}", (30, 0)).center())
    add("VGND", "M3", r.label(dac, "IDACDISABLE", (30, 25)))
    add("iSAR_DAC", "M3", r.label("x4", "ODACOUT", (30, 25))); add("iSAR_DAC", "M3", r.label("x1", "INP", (30, 25)))
    add("iSAR_AN", "M3", r.label("x10", "SH_OUT", (30, 25))); add("iSAR_AN", "M3", r.label("x1", "INN", (30, 25)))
    add("sh_in", "M3", r.label("x8", "OOA", (30, 25))); add("sh_in", "M3", r.label("x10", "SH_IN", (30, 25)))
    add("sh_in", "M3", r.label("x8", "IOAM", (30, 25)))
    add("analog_0", "M3", r.label("x8", "IOAP", (30, 25))); add("analog_0", "M2", pins["analog_0"][1].center())
    add("iIREF1", "M2", r.label("x3", "CSOUT1", (10, 25))); add("iIREF1", "M3", r.label("x8", "IOAIREF", (30, 25)))
    add("iPBIAS", "M2", r.label("x3", "PBIAS", (10, 25))); add("iPBIAS", "M2", r.label("x1", "PBIAS", (10, 25)))
    for cs_lab, net, dac_, yw, xd in IREF_ROUTE:
        add(net, "M2", r.label("x3", cs_lab, (10, 25))); add(net, "M3", r.label(dac_, "IDACIREF", (30, 25)))
    add("iSAR_COMP", "M1", r.pinbox("x1", "OUT", (8, 0)).center()); add("iSAR_COMP", "M1", r.label("x2", "DIN", (8, 25)))
    add("adc_comp", "M1", r.label("x2", "DOUT", (8, 25))); add("adc_comp", "M3", pins["adc_comp"][1].center())
    add("sh_en", "M2", r.label("x9", "LOUT", (10, 25))); add("sh_en", "M3", r.label("x10", "SH_EN", (30, 25)))
    for inst, pin in (("x9", "adc_hold"), ("xcap0", "sh_cap_en[0]"), ("xcap1", "sh_cap_en[1]"),
                      ("xcap2", "sh_cap_en[2]"), ("xcap3", "sh_cap_en[3]")):
        add(pin, "M3", pins[pin][1].center()); add(pin, "M2", r.label(inst, "LIN", (10, 25)))
        add("VAPWR", "M1", r.pinbox(inst, "PLAVDD", (8, 0)).center()); add("VPWR", "M1", r.pinbox(inst, "PLDVDD", (8, 0)).center())
        add("VGND", "M1", r.pinbox(inst, "PLVSS", (8, 0)).center())
    add("VPWR", "M1", r.pinbox("x2", "PDIGVDD", (8, 0)).center()); add("VGND", "M1", r.pinbox("x2", "PDIGVSS", (8, 0)).center())
    add("VGND", "M3", r.label("x10", "VSS", (30, 25))); add("VGND", "M1", r.pinbox("x1", "GNDA", (8, 0)).center())
    add("VAPWR", "M1", r.pinbox("x1", "VCCA", (8, 0)).center()); add("VAPWR", "M3", r.label("x10", "VDD", (30, 25)))
    add("VAPWR", "M2", r.pinbox("x3", "PCSVDD", (10, 0)).center()); add("VGND", "M2", r.pinbox("x3", "PCSVSS", (10, 0)).center())
    add("VAPWR", "M3", r.label("x8", "POAVDD", (30, 25))); add("VGND", "M3", r.label("x8", "POAVSS", (30, 25)))
    add("VGND", "M3", r.label("x8", "IOADISABLE", (30, 25)))
    for n in ("VPWR", "VGND", "VAPWR"):
        add(n, "M3", pins[n][1].center())
    return P
