# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0
"""Generate the layout of sah_12bit (layout/sah_12bit.gds, top cell sah_12bit).

Devices come from the PDK PCells (SG13_dev, made static); taps, wells, wiring, the hold-cap
shield and the pins are drawn here. Run inside nix-shell from the macro folder:
    python3 scripts/layout/gen_sah_12bit_layout.py [out.gds]

Floorplan v4 (cell coordinates, um; the analog macro places the cell at (179.2, 45.5)):
- C1 (cap_cmomi 33 x 60 unit cells, M1-M3, PLUS pad west, MINUS pad east) in a closed VSS box:
  GatPoly floor, M1-M3 fence with via rows, p-tap ring under the fence, Metal4 lid. MINUS is tied
  to the fence. In the macro the lid's LEF obstruction keeps 10.5 um from the west Metal4 PDN strap
  group (PDN_HORIZONTAL_HALO = 10 um), so that group is not cut.
- SH_OUT spine: one straight Metal3 line from the top of the PLUS pad (through a gap in the Metal3
  fence) to the SH_OUT pin, between two VSS walls. The comparator's INN sits straight above it.
- Head on top of the cap, east of the spine: the transmission gate (one 4-finger strip per polarity,
  [SH_IN] D1 [SH_IN] M [SH_OUT] D2 [SH_OUT] M [SH_IN], drawn in a sub-cell and mirrored so its SH_OUT
  trunk goes straight west into the spine), free room for a later T-switch, then the gate driver
  I1..I4 as a row (mirrored, I4 next to the gate) and room for 2 more inverters.
- SH_IN leaves the gate on its east side and runs along the top edge to the SH_IN pin on the east
  edge; the macro route (by hand) continues on the right side of the S&H.
- SH_EN and VDD keep their west-edge pins. Both run up the west strip and east along the bottom of
  the head on Metal1, under a Metal2 VSS plate where they cross the spine.
- VSS is one pin (top edge, on the east spine wall): the driver ground (Metal2 rail) and the quiet
  ground of the cap, its shield and the gate's NMOS body meet only there.
"""
import os
import sys

PDK_ROOT = os.environ.get("PDK_ROOT", os.path.join(os.path.dirname(__file__), "../../../../../../IHP-Open-PDK"))
PDK = os.environ.get("PDK", "ihp-sg13cmos5l")
K = os.path.join(PDK_ROOT, PDK, "libs.tech/klayout")
sys.path.append(os.path.join(K, "python"))
sys.path.append(os.path.join(K, "python/pycell4klayout-api/source/python"))
import pya  # noqa: E402
import sg13cmos5l_pycell_lib  # noqa: E402,F401  (registers SG13_dev)

HERE = os.path.dirname(os.path.abspath(__file__))
MACRO = os.path.normpath(os.path.join(HERE, "..", ".."))
TOP = "sah_12bit"

LAYERS = {
    "Activ": (1, 0), "GatPoly": (5, 0), "Cont": (6, 0), "Metal1": (8, 0), "Metal2": (10, 0),
    "pSD": (14, 0), "Via1": (19, 0), "Via2": (29, 0), "Metal3": (30, 0), "Metal3.pin": (30, 2),
    "Metal3.text": (30, 25), "NWell": (31, 0), "ThickGateOx": (44, 0), "Via3": (49, 0),
    "Metal4": (50, 0), "NoMetFiller": (160, 0), "prBoundary": (189, 4),
}

CELL_W, CELL_H = 43.0, 67.0          # macro x 179.2-222.2, y 45.5-112.5

# Hold cap: cap_cmomi PCell origin; marker = origin + (-0.9 .. l+0.9, -0.32 .. w+0.32)
CAP_W, CAP_L = 54.29, 27.72          # um, 33 x 60 unit cells = 1213.8 fF
CAP_O = (12.81, 1.82)                # marker at macro (191.11, 47.0)
CAP_MARKER = (CAP_O[0] - 0.9, CAP_O[1] - 0.32, CAP_O[0] + 28.62, CAP_O[1] + 54.61)
# Shield box around the marker (distances outward from the marker edge)
FENCE = (0.30, 1.20)                 # M1/M2/M3 fence ring
POLY_OUT = 0.61                      # GatPoly floor edge
POLY_CONT = 0.46                     # centre of the poly contact row
TAP = (0.80, 1.10)                   # p-tap ring (Activ)
VIA_ROW = 0.75                       # centre of the Via1/Via2/Via3 rows
LID_X = 0.23                         # Metal4 lid: marker + 0.23 in x (29.98 um, Slt.c allows 30 um
LID_Y = FENCE[1]                     # without slits), over the fence in y

# SH_OUT spine (centre on the PLUS pad = comparator INN in the macro) and its VSS walls
SPINE_X = CAP_MARKER[0] + 0.32       # 11.83
SPINE_W = 0.40
SPINE_GAP = (SPINE_X - 0.50, SPINE_X + 0.50)        # gap in the Metal3 fence top segment
WALL_W = (SPINE_X - 1.10, SPINE_X - 0.80)           # west VSS wall
WALL_E = (SPINE_X + 0.80, SPINE_X + 1.20)           # east VSS wall = VSS pin

# Transmission gate: sub-cell (strips at local x 0 .. 3.62), placed mirrored: cell x = TG_A - local x
TG_X = 0.0
TG_A = 17.82                         # strip end (local 3.62) at cell x 14.2, east of the spine walls
YN = 61.20                           # NMOS strip, W = 0.3 per finger
YP = YN + 1.54                       # PMOS strip, W = 0.9 per finger
WN, WP = 0.30, 0.90
GATES = [0.34, 1.17, 2.00, 2.83]     # gate poly x (left edge) in a strip, L = 0.45
SDX = [0.07, 0.90, 1.73, 2.56, 3.39]  # S/D strap x (left edge), 0.16 wide
STRIP_LEN = 3.62
SHIN_SD, SHOUT_SD = (0, 1, 4), (2, 3)
MAIN_G, DUMMY_G = (1, 3), (0, 2)
TRUNK_Y = (YN + 0.77, YN + 1.07)     # SH_OUT trunk between the strips, into the spine
SHIN_JOIN_X = TG_X - 1.0             # Metal3 joiner of the two SH_IN bars (east of the gate in the cell)
SPINE_LOCAL = TG_A - SPINE_X         # spine x in the gate's local coordinates
QVSS_LOCAL = TG_A - 13.6             # quiet-VSS via stack of the gate's p-tap (cell x 13.6)
VDD_TAP_LOCAL = TG_A - 22.9          # n-tap Metal1 reaches the VDD riser (cell x 22.6-22.9)

# Gate driver: drawn as a row in a sub-cell (inverters along x, PMOS row below, NMOS row above),
# placed mirrored so I4 sits next to the gate: cell (x, y) = (DRV_B - x, y + DRV_DY)
DRV = [(1.00, 1), (2.73, 1), (4.46, 2), (7.02, 2)]
DRV_YP, DRV_YN = 57.10, 59.90        # PMOS (W 1.2/finger) and NMOS (W 0.6/finger) Activ bottoms
DRV_GATE_Y = 59.10                   # gate contacts in the gap
DRV_B, DRV_DY = 37.1, 2.9            # driver TGO at cell x 27.4-36.8, y 58.2-64.8
GATE_M3_X = {"sw": 20.0, "sw_b": 20.8, "sw_d": 21.6}  # Metal3 risers between driver and gate
VDD_RISER = (22.6, 22.9)             # Metal1 VDD riser: driver VDD rail -> gate n-tap
BOT_SHEN = (57.86, 58.10)            # Metal1 runs along the bottom of the head (under the spine plate)
BOT_VDD = (58.34, 58.58)
# Metal2 VSS plate over the Metal1 runs where they cross the spine (merges with the fence's Metal2)
VSS_PLATE = (WALL_W[0] - 0.3, CAP_MARKER[3] + FENCE[0] + 0.2, WALL_E[1] + 0.3, BOT_VDD[1] + 0.1)
SHEN_X, VDD_X = 1.9, 0.9             # their Metal1 risers in the west strip
SH_IN_Y = (66.55, 66.95)             # SH_IN run along the top edge (Metal3)
VSS_RAIL_Y = (65.70, 66.20)          # driver VSS rail (Metal2) to the VSS pin


def drv(x, y):
    """Driver row coordinates -> cell coordinates."""
    return DRV_B - x, y + DRV_DY


def tgx(x):
    """Gate local x -> cell x."""
    return TG_A - x


class Gen:
    def __init__(self):
        self.ly = pya.Layout()
        self.ly.dbu = 0.001
        self.ly.technology_name = "sg13cmos5l"
        self.top = self.ly.create_cell(TOP)
        self.tgt = self.top
        self.li = {k: self.ly.layer(*v) for k, v in LAYERS.items()}

    # ---- primitives (draw into self.tgt) --------------------------------------------------------
    def box(self, layer, x1, y1, x2, y2):
        self.tgt.shapes(self.li[layer]).insert(pya.DBox(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))

    def sq(self, layer, xc, yc, a):
        self.box(layer, xc - a / 2, yc - a / 2, xc + a / 2, yc + a / 2)

    def cont(self, xc, yc):
        self.sq("Cont", xc, yc, 0.16)

    def via(self, n, xc, yc):
        """Via n (1: M1-M2, 2: M2-M3, 3: M3-M4) with 0.05 um landing pads on both metals."""
        self.sq(f"Via{n}", xc, yc, 0.19)
        for m in (n, n + 1):
            self.sq(f"Metal{m}", xc, yc, 0.29)

    def stack(self, xc, yc, n0, n1):
        for n in range(n0, n1):
            self.via(n, xc, yc)
        for m in range(n0 + 1, n1):     # inner landing pads need the Mn.d minimum area
            self.sq(f"Metal{m}", xc, yc, 0.40)

    def pcell(self, name, params, cname):
        pc = self.ly.create_cell(name, "SG13_dev", params)
        assert pc is not None, f"PCell {name} not found (technology/library not registered)"
        cell = self.ly.cell(self.ly.convert_cell_to_static(pc.cell_index()))
        self.ly.delete_cell(pc.cell_index())   # drop the library proxy, keep the static copy
        cell.name = cname
        return cell

    def place(self, cell, x, y):
        self.tgt.insert(pya.DCellInstArray(cell.cell_index(), pya.DTrans(x, y)))

    def pin(self, name, x1, y1, x2, y2):
        self.box("Metal3", x1, y1, x2, y2)
        self.box("Metal3.pin", x1, y1, x2, y2)
        self.tgt.shapes(self.li["Metal3.text"]).insert(pya.DText(name, pya.DTrans((x1 + x2) / 2, (y1 + y2) / 2)))

    def ring(self, layer, bx, d0, d1):
        """Rectangular ring between distances d0 and d1 outside box bx."""
        x1, y1, x2, y2 = bx
        self.box(layer, x1 - d1, y1 - d1, x2 + d1, y1 - d0)
        self.box(layer, x1 - d1, y2 + d0, x2 + d1, y2 + d1)
        self.box(layer, x1 - d1, y1 - d0, x1 - d0, y2 + d0)
        self.box(layer, x2 + d0, y1 - d0, x2 + d1, y2 + d0)

    def ring_points(self, bx, d, pitch, skip=None):
        """Points on the centre line of a ring at distance d outside bx, every pitch um."""
        x1, y1, x2, y2 = bx[0] - d, bx[1] - d, bx[2] + d, bx[3] + d
        pts = []
        for ya in (y1, y2):
            n = int((x2 - x1) / pitch)
            pts += [(x1 + (x2 - x1 - n * pitch) / 2 + i * pitch, ya) for i in range(n + 1)]
        for xa in (x1, x2):
            n = int((y2 - y1) / pitch)
            pts += [(xa, y1 + (y2 - y1 - n * pitch) / 2 + i * pitch) for i in range(1, n)]
        if skip:
            pts = [p for p in pts if not skip(*p)]
        return pts

    def tap_row(self, x1, x2, y1, y2, ptap):
        """Tap stripe: Activ + contacts (+ pSD for a p-tap); Metal1 is drawn by the caller."""
        self.box("Activ", x1, y1, x2, y2)
        if ptap:
            self.box("pSD", x1 - 0.03, y1 - 0.03, x2 + 0.03, y2 + 0.03)
        n = int((x2 - x1 - 0.14 - 0.16) / 0.36)
        x0 = (x1 + x2) / 2 - n * 0.36 / 2
        for i in range(n + 1):
            self.cont(round(x0 + i * 0.36, 3), (y1 + y2) / 2)

    # ---- hold cap with its shield box --------------------------------------------------------------
    def hold_cap(self):
        cap = self.pcell("cap_cmomi", {"w": f"{CAP_W}u", "l": f"{CAP_L}u", "mmin": 1, "mmax": 3,
                                        "feed": "double", "subblock": 0}, "sah12_cap_cmomi")
        self.place(cap, *CAP_O)
        mk = CAP_MARKER
        # GatPoly floor (no Activ under it, so no device) and its contacts to the M1 fence
        self.box("GatPoly", mk[0] - POLY_OUT, mk[1] - POLY_OUT, mk[2] + POLY_OUT, mk[3] + POLY_OUT)
        for x, y in self.ring_points(mk, POLY_CONT, 1.0):
            self.cont(x, y)
        # p-tap ring under the fence
        self.ring("Activ", mk, *TAP)
        self.ring("pSD", mk, TAP[0] - 0.03, TAP[1] + 0.03)
        for x, y in self.ring_points(mk, (TAP[0] + TAP[1]) / 2, 0.5):
            self.cont(x, y)
        # M1/M2/M3 fence. The feed pads of the cap are solid on Metal3 only, so SH_OUT leaves the
        # top of the PLUS pad on Metal3 through a gap in the Metal3 fence; M1 and M2 stay closed.
        for m in ("Metal1", "Metal2"):
            self.ring(m, mk, *FENCE)
        x1, y1, x2, y2 = mk
        d0, d1 = FENCE
        self.box("Metal3", x1 - d1, y1 - d1, x2 + d1, y1 - d0)
        self.box("Metal3", x1 - d1, y2 + d0, SPINE_GAP[0], y2 + d1)
        self.box("Metal3", SPINE_GAP[1], y2 + d0, x2 + d1, y2 + d1)
        self.box("Metal3", x1 - d1, y1 - d0, x1 - d0, y2 + d0)
        self.box("Metal3", x2 + d0, y1 - d0, x2 + d1, y2 + d0)
        at_gap = lambda x, y: y > y2 and SPINE_GAP[0] - 0.35 < x < SPINE_GAP[1] + 0.35
        for x, y in self.ring_points(mk, VIA_ROW, 1.0):
            self.sq("Via1", x, y, 0.19)
            if not at_gap(x, y):
                self.sq("Via2", x, y, 0.19)
        # Metal4 lid: Via3 rows on the top and bottom fence (not on the spine gap) and on the MINUS pad
        lid = (x1 - LID_X, y1 - LID_Y, x2 + LID_X, y2 + LID_Y)
        for x, y in self.ring_points(mk, VIA_ROW, 1.0):
            if lid[0] + 0.15 < x < lid[2] - 0.15 and (y < y1 or y > y2) and not at_gap(x, y):
                self.sq("Via3", x, y, 0.19)
        minus_x = CAP_O[0] + CAP_L + 0.60                   # centre of the MINUS pad
        y = CAP_O[1] + 1.0
        while y < CAP_O[1] + CAP_W - 0.5:
            self.sq("Via3", minus_x, y, 0.19)
            y += 1.0
        self.box("Metal4", *lid)
        # MINUS pad tied to the fence by Metal3 bridges
        for i in range(11):
            yc = CAP_O[1] + 2.0 + i * 5.0
            self.box("Metal3", minus_x, yc - 0.5, x2 + d0 + 0.1, yc + 0.5)

    # ---- transmission gate (sub-cell, local coordinates; placed mirrored) ----------------------
    def tg_strip(self, pmos, y0, outer_up):
        w = WP if pmos else WN
        name = "pmosHV" if pmos else "nmosHV"
        cell = self.pcell(name, {"w": f"{4 * w:.2f}u", "l": "0.45u", "ng": "4", "m": "1"},
                          f"sah12_tg_{name}_w{4 * w:.1f}_ng4".replace(".", "p"))
        self.place(cell, TG_X, y0)
        s = 1 if outer_up else -1
        edge_out = y0 + w if outer_up else y0          # Activ edge on the outer side
        edge_in = y0 if outer_up else y0 + w
        out = lambda d: edge_out + s * d               # distance d beyond the outer edge
        inn = lambda d: edge_in - s * d                # distance d beyond the inner edge
        gx = [TG_X + g for g in GATES]
        sx = [TG_X + x for x in SDX]
        # main gates: contacts on the outer side, M1 bar, Via1 -> M2 (to the driver)
        for i in MAIN_G:
            self.box("GatPoly", gx[i], edge_out, gx[i] + 0.45, out(0.53))
            self.cont(gx[i] + 0.225, out(0.38))
        self.box("Metal1", gx[1] + 0.07, out(0.225), gx[3] + 0.38, out(0.535))
        main_y = out(0.38)
        self.via(1, TG_X + 1.745, main_y)
        # dummy gates: contacts on the inner side, M1 bar, Via1 at its end -> M2
        for i in DUMMY_G:
            self.box("GatPoly", gx[i], edge_in, gx[i] + 0.45, inn(0.485))
            self.cont(gx[i] + 0.225, inn(0.335))
        dum_y = inn(0.335)
        self.box("Metal1", TG_X - 0.15, dum_y - 0.155, gx[2] + 0.38, dum_y + 0.155)
        self.via(1, TG_X - 0.005, dum_y)
        # SH_OUT straps: Via1 on the Activ, M2 bar
        sh_out_y = edge_in + s * 0.15
        for i in SHOUT_SD:
            self.box("Metal1", sx[i] - 0.075, y0, sx[i] + 0.235, y0 + w)   # 0.31 wide: M1.d
            self.sq("Via1", sx[i] + 0.08, sh_out_y, 0.19)
        self.box("Metal2", sx[2] - 0.07, y0, sx[3] + 0.23, y0 + 0.30 if outer_up else y0 + w)
        # SH_IN straps: extended outwards, Via1 pads, M2 bar (to the SH_IN joiner)
        shin_y = out(1.20)
        for i in SHIN_SD:
            self.box("Metal1", sx[i], edge_out, sx[i] + 0.16, out(1.20))
            self.box("Metal1", sx[i] - 0.075, shin_y - 0.2, sx[i] + 0.235, shin_y + 0.2)
            self.sq("Via1", sx[i] + 0.08, shin_y, 0.19)
        self.box("Metal2", SHIN_JOIN_X - 0.25, shin_y - 0.2, TG_X + STRIP_LEN + 0.05, shin_y + 0.2)
        return main_y, dum_y, shin_y, out(2.05)

    def tgate(self):
        cell = self.ly.create_cell("sah12_tgate")
        self.tgt = cell
        # PMOS: outer side up; NMOS: outer side down. SH_OUT diffusions face each other.
        p_main, p_dum, p_shin, p_tap = self.tg_strip(True, YP, True)
        n_main, n_dum, n_shin, n_tap = self.tg_strip(False, YN, False)
        # SH_OUT: join the two M2 bars, trunk into the spine (after mirroring: west)
        self.box("Metal2", TG_X + 2.075, YN, TG_X + 2.375, YP + 0.30)
        self.box("Metal2", TG_X + 2.075, TRUNK_Y[0], SPINE_LOCAL + 0.15, TRUNK_Y[1])
        self.via(2, SPINE_LOCAL, sum(TRUNK_Y) / 2)
        # SH_IN: Metal3 joiner of the two SH_IN bars
        self.box("Metal3", SHIN_JOIN_X - 0.2, n_shin - 0.2, SHIN_JOIN_X + 0.2, p_shin + 0.2)
        self.via(2, SHIN_JOIN_X, n_shin)
        self.via(2, SHIN_JOIN_X, p_shin)
        # n-tap (VDD) above the PMOS strip, Metal1 out to the VDD riser
        self.tap_row(TG_X, TG_X + STRIP_LEN, p_tap - 0.15, p_tap + 0.15, ptap=False)
        self.box("Metal1", VDD_TAP_LOCAL, p_tap - 0.20, TG_X + STRIP_LEN + 0.05, p_tap + 0.20)
        # p-tap (quiet VSS) below the NMOS strip, via stack up to the east spine wall
        self.tap_row(TG_X, TG_X + STRIP_LEN, n_tap - 0.15, n_tap + 0.15, ptap=True)
        self.box("Metal1", TG_X, n_tap - 0.20, QVSS_LOCAL + 0.2, n_tap + 0.20)
        self.stack(QVSS_LOCAL, n_tap, 1, 3)
        self.box("Metal3", QVSS_LOCAL - 0.2, n_tap - 0.2, TG_A - WALL_E[0] + 0.05, n_tap + 0.2)
        # wells
        self.box("NWell", TG_X - 0.62, YP - 0.62, TG_X + STRIP_LEN + 0.62, p_tap + 0.15 + 0.62)
        self.box("ThickGateOx", TG_X - 0.70, n_tap - 0.45, TG_X + STRIP_LEN + 0.70, p_tap + 0.80)
        self.tgt = self.top
        self.top.insert(pya.DCellInstArray(cell.cell_index(), pya.DTrans(pya.DTrans.M90, TG_A, 0.0)))
        return dict(sw=n_main, sw_b_n=n_dum, sw_d=p_dum, sw_b_p=p_main, shin_p=p_shin, shin_n=n_shin, vdd_tap=p_tap)

    # ---- gate driver (sub-cell, drawn as a row, placed mirrored) --------------------------------
    def driver(self):
        cell = self.ly.create_cell("sah12_driver")
        self.tgt = cell
        pcells = {}
        outs = []
        for k, (x, ng) in enumerate(DRV):
            for pmos in (True, False):
                w = (1.2 if pmos else 0.6) * ng
                name = "pmosHV" if pmos else "nmosHV"
                key = (name, ng)
                if key not in pcells:
                    pcells[key] = self.pcell(name, {"w": f"{w:.1f}u", "l": "0.45u", "ng": str(ng), "m": "1"},
                                             f"sah12_drv_{name}_w{w:.1f}_ng{ng}".replace(".", "p"))
                self.place(pcells[key], x, DRV_YP if pmos else DRV_YN)
            gates = [x + 0.34] + ([x + 1.17] if ng == 2 else [])
            for g in gates:   # one poly from the PMOS through the gap to the NMOS
                self.box("GatPoly", g, DRV_YP + 1.2, g + 0.45, DRV_YN)
            if ng == 2:
                self.box("GatPoly", x + 0.34, DRV_GATE_Y - 0.2, x + 1.62, DRV_GATE_Y + 0.2)
            self.cont(x + 0.565, DRV_GATE_Y)
            self.box("Metal1", x + 0.41, DRV_GATE_Y - 0.155, x + 0.72, DRV_GATE_Y + 0.155)
            # output: drain straps joined across the gap
            self.box("Metal1", x + 0.90, DRV_YP, x + 1.06, DRV_YN + 0.6)
            outs.append(x + 0.98)
            # sources to the rails
            for sxs in ([x + 0.07] + ([x + 1.73] if ng == 2 else [])):
                self.box("Metal1", sxs, DRV_YP - 0.70, sxs + 0.16, DRV_YP)
                self.box("Metal1", sxs, DRV_YN + 0.6, sxs + 0.16, DRV_YN + 1.30)
            # input hop from the previous output
            if k > 0:
                self.box("Metal1", outs[k - 1] - 0.08, DRV_GATE_Y - 0.13, x + 0.72, DRV_GATE_Y + 0.13)
        x_end = DRV[-1][0] + 1.96
        # taps and rails: n-tap + VDD rail below, p-tap + VSS rail above
        self.tap_row(DRV[0][0], x_end, 56.00, 56.30, ptap=False)
        self.box("Metal1", 0.60, 55.90, 9.40, 56.40)
        self.tap_row(DRV[0][0], x_end, 61.30, 61.60, ptap=True)
        self.box("Metal1", 0.60, 61.20, 9.40, 61.70)
        self.box("pSD", DRV[0][0] - 0.18, DRV_YP - 0.40, x_end + 0.18, DRV_YP + 1.6)   # pSD.b
        self.box("NWell", DRV[0][0] - 0.62, 55.38, x_end + 0.62, DRV_YP + 1.2 + 0.62)
        self.box("ThickGateOx", 0.30, 55.30, x_end + 0.72, 61.90)
        self.tgt = self.top
        self.top.insert(pya.DCellInstArray(cell.cell_index(), pya.DTrans(pya.DTrans.M90, DRV_B, DRV_DY)))
        return outs

    # ---- wiring --------------------------------------------------------------------------------
    def wiring(self, tg, outs):
        mk = CAP_MARKER
        # SH_EN: west pin -> Metal1 riser in the west strip -> Metal1 run along the bottom of the head
        #   (under the spine plate) -> Metal2 up at the east end of the driver -> I1 gate pad
        gx, gy = drv(DRV[0][0] + 0.565, DRV_GATE_Y)
        sy = 38.37
        self.pin("SH_EN", 0.0, sy - 0.25, 0.5, sy + 0.25)
        self.via(2, 0.30, sy)
        self.box("Metal2", 0.155, sy - 0.145, SHEN_X + 0.145, sy + 0.145)
        self.via(1, SHEN_X, sy)
        self.box("Metal1", SHEN_X - 0.12, sy - 0.145, SHEN_X + 0.12, BOT_SHEN[1])
        x_e = gx + 1.9
        self.box("Metal1", SHEN_X - 0.12, BOT_SHEN[0], x_e + 0.145, BOT_SHEN[1])
        vye = sum(BOT_SHEN) / 2 + 0.05                # keeps the Metal2 pad 0.25 um from the fence (Mn.b)
        self.via(1, x_e, vye)
        self.box("Metal1", x_e - 0.145, BOT_SHEN[0], x_e + 0.145, vye + 0.145)
        self.box("Metal2", x_e - 0.145, vye - 0.145, x_e + 0.145, gy + 0.145)
        self.box("Metal2", gx - 0.145, gy - 0.145, x_e + 0.145, gy + 0.145)
        self.via(1, gx, gy)
        # VDD: west pin -> Metal1 riser -> Metal1 run along the bottom -> VDD riser -> gate n-tap,
        #   and the driver VDD rail
        vy = 46.0
        self.pin("VDD", 0.0, vy - 0.25, 0.5, vy + 0.25)
        self.via(2, 0.30, vy)
        self.box("Metal2", 0.155, vy - 0.145, VDD_X + 0.145, vy + 0.145)
        self.via(1, VDD_X, vy)
        self.box("Metal1", VDD_X - 0.12, vy - 0.145, VDD_X + 0.12, BOT_VDD[1])
        self.box("Metal1", VDD_X - 0.12, BOT_VDD[0], VDD_RISER[1], BOT_VDD[1])
        rail_y = (55.90 + DRV_DY, 56.40 + DRV_DY)
        self.box("Metal1", VDD_RISER[0], BOT_VDD[0], VDD_RISER[1], tg["vdd_tap"] + 0.20)
        self.box("Metal1", VDD_RISER[0], rail_y[0], DRV_B - 9.40 + 0.1, rail_y[1])
        # Metal2 VSS plate between the Metal1 runs and the spine (merges with the fence's Metal2)
        self.box("Metal2", *VSS_PLATE)
        # driver outputs -> M2 -> Metal3 risers -> M2 entries into the gate (gate vias at tgx())
        # tap heights on the output straps; sw_b above sw_d so their Metal2 runs don't meet the entries
        taps = {"sw": (outs[1], 57.395), "sw_b": (outs[2], 60.20), "sw_d": (outs[3], 59.65)}
        entries = {"sw": [(tg["sw"], tgx(1.745))], "sw_b": [(tg["sw_b_p"], tgx(1.745)), (tg["sw_b_n"], tgx(-0.005))],
                   "sw_d": [(tg["sw_d"], tgx(-0.005))]}
        for net, (ox, oy) in taps.items():
            px, py = drv(ox, oy)
            self.via(1, px, py)
            if all(abs(ye - py) < 0.5 for ye, _ in entries[net]):   # same track: one Metal2 run, no riser
                for ye, xe in entries[net]:
                    self.box("Metal2", xe - 0.145, min(ye, py) - 0.145, px + 0.145, max(ye, py) + 0.145)
                continue
            m3 = GATE_M3_X[net]
            self.box("Metal2", m3 - 0.15, py - 0.145, px + 0.145, py + 0.145)
            self.via(2, m3, py)
            ys = [y for y, _ in entries[net]] + [py]
            self.box("Metal3", m3 - 0.15, min(ys) - 0.145, m3 + 0.15, max(ys) + 0.145)
            for ye, xe in entries[net]:
                self.via(2, m3, ye)
                self.box("Metal2", xe - 0.145, ye - 0.145, m3 + 0.15, ye + 0.145)
        # SH_IN: gate joiner -> up -> along the top edge -> east pin
        jx = tgx(SHIN_JOIN_X)
        self.box("Metal3", jx - 0.2, tg["shin_p"], jx + 0.2, SH_IN_Y[1])
        self.box("Metal3", jx - 0.2, SH_IN_Y[0], CELL_W, SH_IN_Y[1])
        self.pin("SH_IN", CELL_W - 0.5, SH_IN_Y[0], CELL_W, SH_IN_Y[1])
        # SH_OUT spine: from inside the PLUS pad top through the fence gap to the pin
        self.box("Metal3", SPINE_X - SPINE_W / 2, mk[3] - 0.23, SPINE_X + SPINE_W / 2, CELL_H)
        self.pin("SH_OUT", SPINE_X - SPINE_W / 2, CELL_H - 0.4, SPINE_X + SPINE_W / 2, CELL_H)
        # VSS walls along the spine (quiet VSS, on the fence top segment)
        wall_y0 = mk[3] + FENCE[0] + 0.3
        self.box("Metal3", WALL_W[0], wall_y0, WALL_W[1], CELL_H)
        self.box("Metal3", WALL_E[0], wall_y0, WALL_E[1], CELL_H)
        # VSS: driver VSS rail (Metal1, extended up) -> Metal2 rail west -> east spine wall at the pin
        vx_l = DRV_B - 9.40                         # west end of the driver's VSS rail
        self.box("Metal1", vx_l, 61.20 + DRV_DY, vx_l + 0.5, VSS_RAIL_Y[1])
        self.sq("Via1", vx_l + 0.25, sum(VSS_RAIL_Y) / 2, 0.19)
        self.box("Metal2", WALL_E[0], VSS_RAIL_Y[0], vx_l + 0.5, VSS_RAIL_Y[1])
        self.sq("Via2", sum(WALL_E) / 2, sum(VSS_RAIL_Y) / 2, 0.19)
        self.pin("VSS", WALL_E[0], CELL_H - 0.4, WALL_E[1], CELL_H)

    def build(self, out):
        self.hold_cap()
        tg = self.tgate()
        outs = self.driver()
        self.wiring(tg, outs)
        mk = CAP_MARKER
        self.box("NoMetFiller", 0.0, 0.0, CELL_W, CELL_H)
        self.box("prBoundary", 0.0, 0.0, CELL_W, CELL_H)
        assert self.top.dbbox() == pya.DBox(0, 0, CELL_W, CELL_H), self.top.dbbox()
        opt = pya.SaveLayoutOptions()
        opt.write_context_info = False
        self.ly.write(out, opt)
        lid = (mk[0] - LID_X, mk[1] - LID_Y, mk[2] + LID_X, mk[3] + LID_Y)
        print(f"Wrote {out}: cell {CELL_W} x {CELL_H} um")
        print(f"  cap marker {mk}, Metal4 lid {lid}")
        for s in self.top.shapes(self.li["Metal3.text"]).each():
            print(f"  pin {s.text_string:7s} at ({s.dtext.x:.3f}, {s.dtext.y:.3f})")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MACRO, "layout", f"{TOP}.gds")
    Gen().build(out)
