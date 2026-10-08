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

LAYER = {"M1": (8, 0), "M2": (10, 0), "M3": (30, 0), "V1": (19, 0), "V2": (29, 0)}
SPACE = {"M1": 0.18, "M2": 0.21, "M3": 0.21, "V1": 0.22, "V2": 0.22}
VIA = {"V1": ("M1", "M2"), "V2": ("M2", "M3")}
CUT, CUT_SPACE, PAD = 0.19, 0.22, 0.30
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
        box = db.DBox(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
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
    # key: (pcell, parameters) - values from heichips26_FAIf.sch (R1/R2: rhigh w0.5 l50 b0; C1: cap_cmomi w50 l2)
    "rhigh": ("rhigh", {"w": "0.5u", "l": "50u", "b": 0, "Calculate": "R"}),
    "cmomi": ("cap_cmomi", {"w": "50u", "l": "2u", "mmin": 2, "mmax": 3, "feed": "double", "subblock": 0}),
}


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
    cells = {}
    for key, (name, params) in DIVIDER_PCELLS.items():
        pc = ly.create_cell(name, "SG13_dev", params)
        assert pc is not None, f"PCell {name} not available"
        cell = ly.cell(ly.convert_cell_to_static(pc.cell_index()))
        cell.flatten(True)
        cell.name = f"{prefix}{key}_{name}"
        cells[key] = cell
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
# The PTAT (x3) is not routed in this round: it moves next to the comparator first. Its iIREF3/4
# routes are planned as Metal2 trunks in the west channel (x 19/20) and a Metal3 entry at
# R2R + 19.2 (between bit 3 and the R2R's Metal3 feedback line) down onto IDACIREF.
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
    bars = r.pin_shapes("C1", 30)                     # Metal3 pins on the low and the high bar
    cb = r.placed["C1"][2]
    m3 = r.ly.find_layer(*LAYER["M3"])
    cx = r.placed["C1"][0].dbbox_per_layer(m3).transformed(r.placed["C1"][1])
    bar_h = 0.6                                       # cap_cmomi feed bar width (PCell)
    c_lo = db.DBox(cx.left, bars[0].center().y - bar_h / 2, cx.right, bars[0].center().y + bar_h / 2)
    c_hi = db.DBox(cx.left, bars[-1].center().y - bar_h / 2, cx.right, bars[-1].center().y + bar_h / 2)
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
    yl = c_lo.center().y
    r.wire("VGND", "M3", [(c_lo.left + 0.3, yl), (x_vgnd, yl)], c_lo.height())
    r.contact("VGND", "M3", db.DPoint(c_lo.left + 0.3, yl))
    r.via("VGND", "V2", x_vgnd, yl)
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
    yh = c_hi.center().y
    xv = cb.right + 1.0                               # via beyond the cap (no Metal2 fingers there)
    r.wire("iVREF", "M3", [(c_hi.right - 0.3, yh), (xv, yh)], bar_h)
    r.contact("iVREF", "M3", db.DPoint(c_hi.right - 0.3, yh))
    r.via("iVREF", "V2", xv, yh)
    r.wire("iVREF", "M2", [(xv, yh), (VREF_X, yh)])
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
    c = r.pin_shapes("C1", 30)
    add("VGND", "M3", c[0].center()); add("iVREF", "M3", c[-1].center())
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
