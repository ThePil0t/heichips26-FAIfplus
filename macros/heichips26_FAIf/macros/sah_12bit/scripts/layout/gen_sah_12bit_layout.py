# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0
"""Generate the layout of sah_12bit (layout/sah_12bit.gds, top cell sah_12bit).

Devices come from the PDK PCells (SG13_dev, made static); taps, wells, wiring, the hold-cap
shield and the pins are drawn here. Run inside nix-shell from the macro folder:
    python3 scripts/layout/gen_sah_12bit_layout.py [out.gds]

Floorplan (cell coordinates, um; the analog macro places the cell at (185.5, 46.0)):
- C1 (cap_cmomi 33 x 60 unit cells, M1-M3, PLUS pad west, MINUS pad east) in a closed VSS box:
  GatPoly floor, M1-M3 fence with via rows, p-tap ring under the fence, Metal4 lid. MINUS is tied
  to the fence. In the macro the cap sits between the Metal4 PDN strap groups (6.7 um clearance).
- Transmission gate (top left): one 4-finger strip per polarity, [SH_IN] D1 [SH_IN] M [SH_OUT] D2
  [SH_OUT] M [SH_IN]. The SH_OUT diffusions of both strips face each other; SH_IN and the main gates
  are wired on the outer sides, the dummy gates on the inner side.
- SH_OUT leaves the gate as an M2 line shielded by M1/M3 VSS planes and M2 VSS rails, and enters
  the PLUS pad through a gap in the fence. A branch goes up to the SH_OUT pin (top edge).
- Gate driver I1..I4 (one row, NMOS above PMOS) left of the gate; SH_EN and VDD on the west edge.
- SH_IN enters at the bottom-left corner, straight above the opamp's OOA exit, so its macro route
  is short and never runs along SH_EN.
- VSS is one pin (top edge): the driver ground and the quiet ground of the cap, its shield and the
  gate's NMOS body meet only there.
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

CELL_W, CELL_H = 81.5, 62.5

# Hold cap: cap_cmomi PCell origin; marker = origin + (-0.9 .. l+0.9, -0.32 .. w+0.32)
CAP_W, CAP_L = 54.29, 27.72          # um, 33 x 60 unit cells = 1213.8 fF
CAP_O = (51.52, 3.52)
CAP_MARKER = (CAP_O[0] - 0.9, CAP_O[1] - 0.32, CAP_O[0] + 28.62, CAP_O[1] + 54.61)
# Shield box around the marker (distances outward from the marker edge)
FENCE = (0.30, 1.20)                 # M1/M2/M3 fence ring
POLY_OUT = 0.61                      # GatPoly floor edge
POLY_CONT = 0.46                     # centre of the poly contact row
TAP = (0.80, 1.10)                   # p-tap ring (Activ)
VIA_ROW = 0.75                       # centre of the Via1/Via2/Via3 rows
LID_X = 0.23                         # Metal4 lid: marker + 0.23 in x (29.98 um, Slt.c allows 30 um
LID_Y = FENCE[1]                     # without slits), over the fence in y

# Transmission gate strips (Activ lower-left)
TG_X = 15.0
YN = 56.16                           # NMOS strip, W = 0.3 per finger
YP = 57.70                           # PMOS strip, W = 0.9 per finger
WN, WP = 0.30, 0.90
GATES = [0.34, 1.17, 2.00, 2.83]     # gate poly x (left edge) in a strip, L = 0.45
SDX = [0.07, 0.90, 1.73, 2.56, 3.39]  # S/D strap x (left edge), 0.16 wide
STRIP_LEN = 3.62
SHIN_SD, SHOUT_SD = (0, 1, 4), (2, 3)
MAIN_G, DUMMY_G = (1, 3), (0, 2)

# Coax (SH_OUT to the PLUS pad) centred on the trunk
TRUNK_Y = (56.93, 57.23)
COAX_Y = (56.23, 57.93)
COAX_X0 = 20.8
COAX_M3_END = 47.9                   # M3 cover ends here; from here on M3 VSS rails and the SH_OUT stub
SHOUT_V2_X = 48.95                   # SH_OUT goes up to M3 here and enters the PLUS pad on M3
BRANCH_X = (20.15, 20.45)            # SH_OUT branch to the pin (macro x 205.8 = comparator INN)
VSS_X = (20.95, 21.45)               # quiet VSS riser and the VSS pin (star point)

# Gate driver: inverters (x of Activ, ng); PMOS row below, NMOS row above
DRV = [(1.00, 1), (2.73, 1), (4.46, 2), (7.02, 2)]
DRV_YP, DRV_YN = 57.10, 59.90        # PMOS (W 1.2/finger) and NMOS (W 0.6/finger) Activ bottoms
DRV_GATE_Y = 59.10                   # gate contacts in the gap
SH_IN_X = 1.5                        # SH_IN pin (bottom edge, macro x 187.0)
SH_IN_Y = 44.0                       # SH_IN run towards the gate


class Gen:
    def __init__(self):
        self.ly = pya.Layout()
        self.ly.dbu = 0.001
        self.ly.technology_name = "sg13cmos5l"
        self.top = self.ly.create_cell(TOP)
        self.li = {k: self.ly.layer(*v) for k, v in LAYERS.items()}

    # ---- primitives ---------------------------------------------------------------------------
    def box(self, layer, x1, y1, x2, y2):
        self.top.shapes(self.li[layer]).insert(pya.DBox(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))

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
        self.top.insert(pya.DCellInstArray(cell.cell_index(), pya.DTrans(x, y)))

    def pin(self, name, x1, y1, x2, y2):
        self.box("Metal3", x1, y1, x2, y2)
        self.box("Metal3.pin", x1, y1, x2, y2)
        self.top.shapes(self.li["Metal3.text"]).insert(pya.DText(name, pya.DTrans((x1 + x2) / 2, (y1 + y2) / 2)))

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
        # M1/M2/M3 fence. The feed pads of the cap are solid on Metal3 only, so SH_OUT enters the
        # PLUS pad on Metal3 through a gap in the Metal3 fence (west side); M1 and M2 stay closed.
        gap = (COAX_Y[0] + 0.40, COAX_Y[1] - 0.40)          # between the coax VSS rails
        for m in ("Metal1", "Metal2"):
            self.ring(m, mk, *FENCE)
        x1, y1, x2, y2 = mk
        d0, d1 = FENCE
        self.box("Metal3", x1 - d1, y1 - d1, x2 + d1, y1 - d0)
        self.box("Metal3", x1 - d1, y2 + d0, x2 + d1, y2 + d1)
        self.box("Metal3", x2 + d0, y1 - d0, x2 + d1, y2 + d0)
        self.box("Metal3", x1 - d1, y1 - d0, x1 - d0, gap[0])
        self.box("Metal3", x1 - d1, gap[1], x1 - d0, y2 + d0)
        west_gap = lambda x, y: x < x1 and gap[0] - 0.6 < y < gap[1] + 0.6
        for x, y in self.ring_points(mk, VIA_ROW, 1.0):
            self.sq("Via1", x, y, 0.19)
            if not west_gap(x, y):
                self.sq("Via2", x, y, 0.19)
        # Metal4 lid: Via3 rows on the top and bottom fence and on the MINUS pad (Metal3)
        lid = (x1 - LID_X, y1 - LID_Y, x2 + LID_X, y2 + LID_Y)
        for x, y in self.ring_points(mk, VIA_ROW, 1.0):
            if lid[0] + 0.15 < x < lid[2] - 0.15 and (y < y1 or y > y2):
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

    # ---- transmission gate ---------------------------------------------------------------------
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
        # main gates: contacts on the outer side, M1 bar, Via1 -> M2 (to the driver, west)
        for i in MAIN_G:
            self.box("GatPoly", gx[i], edge_out, gx[i] + 0.45, out(0.53))
            self.cont(gx[i] + 0.225, out(0.38))
        self.box("Metal1", gx[1] + 0.07, out(0.225), gx[3] + 0.38, out(0.535))
        main_y = out(0.38)
        self.via(1, TG_X + 1.745, main_y)
        # dummy gates: contacts on the inner side, M1 bar, Via1 at its west end -> M2
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
        self.box("Metal2", sx[2] - 0.07, y0 if outer_up else y0, sx[3] + 0.23, y0 + 0.30 if outer_up else y0 + w)
        # SH_IN straps: extended outwards, Via1 pads, M2 bar (to the SH_IN riser, west)
        shin_y = out(1.20)
        for i in SHIN_SD:
            self.box("Metal1", sx[i], edge_out, sx[i] + 0.16, out(1.20))
            self.box("Metal1", sx[i] - 0.075, shin_y - 0.2, sx[i] + 0.235, shin_y + 0.2)
            self.sq("Via1", sx[i] + 0.08, shin_y, 0.19)
        self.box("Metal2", 11.80, shin_y - 0.2, TG_X + STRIP_LEN + 0.05, shin_y + 0.2)
        return main_y, dum_y, shin_y, out(2.05)

    def tgate(self):
        # PMOS: outer side up; NMOS: outer side down. SH_OUT diffusions face each other.
        p_main, p_dum, p_shin, p_tap = self.tg_strip(True, YP, True)
        n_main, n_dum, n_shin, n_tap = self.tg_strip(False, YN, False)
        # SH_OUT: join the two M2 bars and run the trunk east
        self.box("Metal2", TG_X + 2.075, YN, TG_X + 2.375, YP + 0.30)
        self.box("Metal2", TG_X + 2.075, TRUNK_Y[0], COAX_X0 + 0.1, TRUNK_Y[1])
        # n-tap (VDD) above the PMOS strip, p-tap (quiet VSS) below the NMOS strip
        self.tap_row(TG_X, TG_X + STRIP_LEN, p_tap - 0.15, p_tap + 0.15, ptap=False)
        self.box("Metal1", 13.60, p_tap - 0.20, TG_X + STRIP_LEN + 0.05, p_tap + 0.20)
        self.tap_row(TG_X, TG_X + STRIP_LEN, n_tap - 0.15, n_tap + 0.15, ptap=True)
        self.box("Metal1", TG_X, n_tap - 0.20, 19.80, n_tap + 0.20)
        self.box("Metal1", 19.40, n_tap - 0.20, 19.80, COAX_Y[0] + 0.3)
        # wells
        self.box("NWell", TG_X - 0.62, YP - 0.62, TG_X + STRIP_LEN + 0.62, p_tap + 0.15 + 0.62)
        self.box("ThickGateOx", TG_X - 0.70, n_tap - 0.45, TG_X + STRIP_LEN + 0.70, p_tap + 0.80)
        return dict(sw=n_main, sw_b_n=n_dum, sw_d=p_dum, sw_b_p=p_main, shin_p=p_shin, shin_n=n_shin, vdd_tap=p_tap)

    # ---- gate driver ---------------------------------------------------------------------------
    def driver(self):
        cells = {}
        outs = []
        for k, (x, ng) in enumerate(DRV):
            for pmos in (True, False):
                w = (1.2 if pmos else 0.6) * ng
                name = "pmosHV" if pmos else "nmosHV"
                key = (name, ng)
                if key not in cells:
                    cells[key] = self.pcell(name, {"w": f"{w:.1f}u", "l": "0.45u", "ng": str(ng), "m": "1"},
                                            f"sah12_drv_{name}_w{w:.1f}_ng{ng}".replace(".", "p"))
                self.place(cells[key], x, DRV_YP if pmos else DRV_YN)
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
        self.box("Metal1", 0.10, 55.90, 13.90, 56.40)
        self.tap_row(DRV[0][0], x_end, 61.30, 61.60, ptap=True)
        self.box("Metal1", 0.60, 61.20, 9.40, 62.20)
        self.box("pSD", DRV[0][0] - 0.18, DRV_YP - 0.40, x_end + 0.18, DRV_YP + 1.6)   # pSD.b
        self.box("NWell", DRV[0][0] - 0.62, 55.38, x_end + 0.62, DRV_YP + 1.2 + 0.62)
        self.box("ThickGateOx", 0.30, 55.30, x_end + 0.72, 61.90)
        return outs

    # ---- wiring --------------------------------------------------------------------------------
    def wiring(self, tg, outs):
        # SH_EN: west pin -> I1 gate
        self.box("Metal1", 0.10, DRV_GATE_Y - 0.13, DRV[0][0] + 0.72, DRV_GATE_Y + 0.13)
        self.stack(0.30, DRV_GATE_Y, 1, 3)
        self.pin("SH_EN", 0.0, DRV_GATE_Y - 0.25, 0.5, DRV_GATE_Y + 0.25)
        # VDD: west pin on the driver rail; rail -> TG n-tap
        self.stack(0.30, 56.15, 1, 3)
        self.pin("VDD", 0.0, 55.90, 0.5, 56.40)
        self.box("Metal1", 13.60, 55.90, 13.90, tg["vdd_tap"] + 0.20)
        # sw = I2 out -> TG NMOS main gates (M3 jog at the driver)
        o = outs[1]
        self.box("Metal1", o - 0.105, 57.30, o + 0.105, 57.49)
        self.stack(o, 57.395, 1, 3)
        self.box("Metal3", o - 0.15, tg["sw"] - 0.145, o + 0.15, 57.54)
        self.via(2, o, tg["sw"])
        self.box("Metal2", o - 0.15, tg["sw"] - 0.145, TG_X + 1.90, tg["sw"] + 0.145)
        # sw_b = I3 out -> TG PMOS main gates and TG NMOS dummy gates
        o = outs[2]
        y_b = 59.65
        self.box("Metal1", o - 0.105, y_b - 0.105, o + 0.105, y_b + 0.105)
        self.via(1, o, y_b)
        self.box("Metal2", o - 0.15, y_b - 0.145, 11.05, y_b + 0.145)
        self.via(2, 10.90, y_b)
        self.box("Metal3", 10.75, tg["sw_b_p"] - 0.145, 11.05, y_b + 0.145)
        self.via(2, 10.90, tg["sw_b_p"])
        self.box("Metal2", 10.75, tg["sw_b_p"] - 0.145, TG_X + 1.90, tg["sw_b_p"] + 0.145)
        self.via(2, 13.20, tg["sw_b_p"])
        self.via(2, 13.20, tg["sw_b_n"])
        self.box("Metal3", 13.05, tg["sw_b_n"] - 0.145, 13.35, tg["sw_b_p"] + 0.145)
        self.box("Metal2", 13.05, tg["sw_b_n"] - 0.145, TG_X + 0.14, tg["sw_b_n"] + 0.145)
        # sw_d = I4 out -> TG PMOS dummy gates
        o = outs[3]
        y_d = 60.20
        self.box("Metal1", o - 0.105, y_d - 0.105, o + 0.105, y_d + 0.105)
        self.via(1, o, y_d)
        self.box("Metal2", o - 0.15, y_d - 0.145, 10.15, y_d + 0.145)
        self.via(2, 10.00, y_d)
        self.box("Metal3", 9.85, tg["sw_d"] - 0.145, 10.15, y_d + 0.145)
        self.via(2, 10.00, tg["sw_d"])
        self.box("Metal2", 9.85, tg["sw_d"] - 0.145, TG_X + 0.14, tg["sw_d"] + 0.145)
        # SH_IN: bottom pin -> riser -> both strips
        self.pin("SH_IN", SH_IN_X - 0.2, 0.0, SH_IN_X + 0.2, 0.5)
        self.box("Metal3", SH_IN_X - 0.2, 0.0, SH_IN_X + 0.2, SH_IN_Y + 0.2)
        self.box("Metal3", SH_IN_X - 0.2, SH_IN_Y - 0.2, 12.20, SH_IN_Y + 0.2)
        self.box("Metal3", 11.80, SH_IN_Y - 0.2, 12.20, tg["shin_p"] + 0.2)
        self.via(2, 12.00, tg["shin_p"])
        self.via(2, 12.00, tg["shin_n"])
        # SH_OUT coax to the PLUS pad: M2 line, M2 VSS rails, M1/M3 VSS planes
        mk = CAP_MARKER
        x_end = mk[0] - FENCE[1] + 0.05
        self.box("Metal2", COAX_X0, TRUNK_Y[0], SHOUT_V2_X + 0.15, TRUNK_Y[1])
        self.via(2, SHOUT_V2_X, sum(TRUNK_Y) / 2)
        self.box("Metal3", SHOUT_V2_X - 0.15, TRUNK_Y[0], mk[0] + 0.10, TRUNK_Y[1])
        self.box("Metal1", 19.40, COAX_Y[0], x_end, COAX_Y[1])
        self.box("Metal3", COAX_X0, COAX_Y[0], COAX_M3_END, COAX_Y[1])
        for yr in ((COAX_Y[0], COAX_Y[0] + 0.40), (COAX_Y[1] - 0.40, COAX_Y[1])):
            self.box("Metal2", COAX_X0, yr[0], x_end, yr[1])
            self.box("Metal3", COAX_M3_END - 0.1, yr[0], x_end, yr[1])
            yc = (yr[0] + yr[1]) / 2
            x = COAX_X0 + 0.3
            while x < x_end - 0.3:
                self.sq("Via1", x, yc, 0.19)
                self.sq("Via2", x, yc, 0.19)
                x += 1.0
        # SH_OUT branch to the pin
        self.via(2, sum(BRANCH_X) / 2, sum(TRUNK_Y) / 2)
        self.box("Metal3", BRANCH_X[0], TRUNK_Y[0], BRANCH_X[1], CELL_H)
        self.pin("SH_OUT", BRANCH_X[0] - 0.05, CELL_H - 0.4, BRANCH_X[1] + 0.05, CELL_H)
        # VSS: driver rail (M2 along the top edge) and the quiet riser from the coax meet at the pin
        self.box("Metal2", 0.30, 61.90, VSS_X[1] + 0.15, 62.40)
        for x in (1.0, 3.0, 5.0, 7.0, 9.0):
            self.sq("Via1", x, 62.05, 0.19)
        self.box("Metal3", VSS_X[0], COAX_Y[1] - 0.3, VSS_X[1], CELL_H)
        self.sq("Via2", sum(VSS_X) / 2, 62.15, 0.19)
        self.pin("VSS", VSS_X[0], CELL_H - 0.4, VSS_X[1], CELL_H)

    def build(self, out):
        self.hold_cap()
        tg = self.tgate()
        outs = self.driver()
        self.wiring(tg, outs)
        mk = CAP_MARKER
        self.box("NoMetFiller", 14.0, mk[1] - LID_Y, mk[2] + FENCE[1], CELL_H)
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
