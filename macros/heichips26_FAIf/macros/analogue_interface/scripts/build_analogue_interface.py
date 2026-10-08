#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
"""Build the dry-run version of the analogue_interface hard macro.

The existing block layouts are placed (not routed). Unfinished parts become
sized dummies, and bare pin shapes go on the macro edge. From one placement
and pin table the script writes:

  layout/analogue_interface.gds
  final/lef/analogue_interface.lef
  final/vh/analogue_interface.vh   (Verilog blackbox header)
  final/lib/analogue_interface.lib (timing-free Liberty)

See ../README.md for the floorplan and the size estimates.
"""

import os
import re

import klayout.db as db

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MACRO_DIR = os.path.dirname(SCRIPT_DIR)
BLOCKS_DIR = os.path.dirname(MACRO_DIR)  # macros/heichips26_FAIf/macros

TOP = "analogue_interface"
PREFIX = "heichips26_FAIf_"
DBU = 0.001
GRID = 0.005  # manufacturing grid
W, H = 300.0, 185.0
MIN_GAP = 3.0  # minimum spacing between placed blocks

# Planned placement of the macro in heichips26_FAIf (lower-left, orientation N).
# The analog pins sit directly above the die pins of heichips26_template_small_analog
# only for this location.
DIE_LOCATION = (190.0, 8.82)
DIE_ANALOG_PIN_X = {"analog_0": 450.24, "analog_1": 455.04, "analog_2": 459.84}

# Metal3 routing tracks of heichips26_template_small_analog.def (die coordinates): y = 0.42 * k
M3_TRACK_PITCH = 0.42

# GDS layers (layer, datatype)
METAL = {"Metal1": 8, "Metal2": 10, "Metal3": 30}
DT_DRAWING, DT_PIN, DT_TEXT = 0, 2, 25
PR_BOUNDARY = (189, 4)
TEXT = (63, 0)
STRIP_LAYERS = {126}  # TopMetal1 (r2r_dac carries a TopMetal1 text label)
FORBIDDEN_LAYERS = {49, 50, 125, 126, 133, 134}  # Via3, Metal4, TopVia1, TopMetal1, TopVia2, TopMetal2
# Exception: the Metal4 lid (VSS) over the hold cap of sah_12bit, with its Via3 rows. It must stay inside
# that instance, keep clear of the top-level Metal4 PDN straps and is covered by a Metal4 OBS in the LEF.
M4_ALLOWED_INST = "x10"
M4_OBS_HALO = 1.0
# Metal4 PDN strap groups over the macro (macro-local x), measured in final/gds/heichips26_FAIf.gds (2026-10-08):
# three 1 um straps on a 3 um pitch, groups every 50 um
M4_STRAP_GROUPS = [(172.38, 179.38), (222.38, 229.38), (272.38, 279.38)]
M4_MIN_SPACE = 0.6                 # lid to any strap: Mn.f (wide-metal spacing)
# LibreLane removes Metal4 PDN straps within PDN_HORIZONTAL_HALO (flow/librelane/config.yaml default, 10 um)
# of a Metal4 obstruction. The groups listed here must stay intact, so the lid's OBS keeps halo + 0.5 um.
PDN_HORIZONTAL_HALO = 10.0
M4_KEEP_GROUPS = [(172.38, 179.38)]

# Existing block layouts: key -> GDS path relative to BLOCKS_DIR
BLOCKS = {
    "lt8": "8x_inverting_digital_level_translator/layout/8x_inverting_digital_level_translator.gds",
    "r2r": "r2r_dac/layout/r2r_dac.gds",
    "ptat": "ptat_current_source/layout/ptat_curr_gen.gds",
    "dlt": "down_digital_translator/layout/down_digital_translator.gds",
    "lt": "digital_level_translator/layout/digital_level_translator.gds",
    "opamp": "opamp/layout/op_amp_ver_2.gds",
    "comp": "comparator/layout/555_comparator.gds",
    "sah": "sah_12bit/layout/sah_12bit.gds",
}

# Dummies for parts without layout: key -> (cell suffix, width, height, label)
DUMMIES = {
    "rhigh": ("rhigh_w0p5_l50", 53.0, 2.0, "DUMMY rhigh w=0.5u l=50u 53x2um estimate"),
    "cmomi": ("cap_cmomi_w50_l2", 51.0, 8.0, "DUMMY cap_cmomi w=50u l=2u 51x8um estimate"),
}

# Placement: instance (schematic name), block or dummy key, orientation, lower-left of the
# transformed bbox (macro-local um), description
PLACEMENT = [
    ("x12", "lt8", "R90", 4.0, 9.35, "8x level translator for DAC1 (dac_out[15:8])"),
    ("x11", "r2r", "R0", 25.0, 10.0, "R2R DAC1 -> analog_2"),
    ("x7", "lt8", "R90", 4.0, 47.35, "8x level translator for DAC0 (dac_out[7:0])"),
    ("x5", "r2r", "R0", 25.0, 48.0, "R2R DAC0 -> analog_1"),
    ("x6", "lt8", "R90", 4.0, 85.35, "8x level translator for the SAR DAC (adc_ref)"),
    ("x4", "r2r", "R0", 25.0, 86.0, "R2R SAR DAC -> comparator"),
    ("x3", "ptat", "R0", 25.0, 124.0, "PTAT current source (bias)"),
    ("x2", "dlt", "MY", 4.0, 124.5, "down translator for adc_comp"),
    ("x9", "lt", "R0", 4.0, 132.4, "level translator for adc_hold"),
    ("xcap0", "lt", "R0", 4.0, 140.45, "level translator for sh_cap_en[0]"),
    ("xcap1", "lt", "R0", 4.0, 148.5, "level translator for sh_cap_en[1]"),
    ("xcap2", "lt", "R0", 4.0, 156.55, "level translator for sh_cap_en[2]"),
    ("xcap3", "lt", "R0", 4.0, 164.6, "level translator for sh_cap_en[3]"),
    ("x8", "opamp", "MY", 187.0, 10.0, "S&H input buffer, mirrored: IOAP above analog_0..2"),
    ("x10", "sah", "R0", 179.2, 45.5, "sample-and-hold sah_12bit: switches west of the hold cap"),
    ("x1", "comp", "R0", 180.63, 112.0, "SAR comparator: INN straight above the sah_12bit SH_OUT spine"),
    ("R1", "rhigh", "R0", 220.0, 113.0, "iVREF divider, upper resistor"),
    ("R2", "rhigh", "R0", 220.0, 118.0, "iVREF divider, lower resistor"),
    ("C1", "cmomi", "R0", 220.0, 124.0, "iVREF filter cap"),
]

# Orientation -> (rotation in multiples of 90 deg, mirror at x-axis before rotation)
ORIENT = {"R0": (0, False), "R90": (1, False), "R180": (2, False), "R270": (3, False),
          "MX": (0, True), "MY": (2, True)}

# Digital pins on the west edge (Metal3): pin name -> (instance, block label, label layer)
WEST_PIN_LEN, WEST_PIN_HEIGHT = 1.0, 0.4
WEST_PINS = {}
for _k in range(8):
    WEST_PINS[f"dac_out[{8 + _k}]"] = ("x12", f"LIN{_k}", (10, 25))
    WEST_PINS[f"dac_out[{_k}]"] = ("x7", f"LIN{_k}", (10, 25))
    WEST_PINS[f"adc_ref[{_k}]"] = ("x6", f"LIN{_k}", (10, 25))
for _k in range(4):
    WEST_PINS[f"sh_cap_en[{_k}]"] = (f"xcap{_k}", "LIN", (10, 25))
WEST_PINS["adc_hold"] = ("x9", "LIN", (10, 25))
WEST_PINS["adc_comp"] = ("x2", "DOUT", (8, 25))

# Analog pins on the south edge (Metal2)
SOUTH_PIN_WIDTH, SOUTH_PIN_HEIGHT = 1.0, 2.0

# Power pins: Metal3 straps across the top band (name -> y bottom, y top)
POWER_X = (2.0, 298.0)
POWER_PINS = {"VPWR": (173.0, 175.0), "VGND": (177.0, 179.0), "VAPWR": (181.0, 183.0)}
POWER_USE = {"VPWR": "POWER", "VAPWR": "POWER", "VGND": "GROUND"}

# Port list in Verilog/LEF order: name, direction, width (0 = scalar)
PORTS = [
    ("adc_ref", "input", 8),
    ("adc_hold", "input", 0),
    ("adc_comp", "output", 0),
    ("dac_out", "input", 16),
    ("sh_cap_en", "input", 4),
    ("analog_0", "inout", 0),
    ("analog_1", "inout", 0),
    ("analog_2", "inout", 0),
]
LEF_DIRECTION = {"input": "INPUT", "output": "OUTPUT", "inout": "INOUT"}


def snap(v):
    return round(v / GRID) * GRID


def snap_to_m3_track(y):
    """Move a macro-local y onto the nearest Metal3 track for the planned DIE_LOCATION."""
    die_y = y + DIE_LOCATION[1]
    return round(round(die_y / M3_TRACK_PITCH) * M3_TRACK_PITCH - DIE_LOCATION[1], 3)


def sanitize(name):
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def import_block(ly, key, rel_path):
    """Copy a block's cell tree into ly (rescaled to DBU) and prefix all cell names."""
    src = db.Layout()
    src.read(os.path.join(BLOCKS_DIR, rel_path))
    tops = src.top_cells()
    assert len(tops) == 1, f"{rel_path}: expected one top cell, got {[c.name for c in tops]}"
    src_top = tops[0]
    cell = ly.create_cell(PREFIX + sanitize(src_top.name))
    for ci in cell.copy_tree(src_top):
        sub = ly.cell(ci)
        sub.name = f"{PREFIX}{key}_{sanitize(sub.name)}"
    a, b = src_top.dbbox(), cell.dbbox()
    assert abs(a.width() - b.width()) < 1e-6 and abs(a.height() - b.height()) < 1e-6, \
        f"{rel_path}: size changed on import ({a} -> {b})"
    return cell


def make_dummy(ly, suffix, w, h, label):
    cell = ly.create_cell(f"{PREFIX}dummy_{suffix}")
    cell.shapes(ly.layer(*PR_BOUNDARY)).insert(db.DBox(0, 0, w, h))
    cell.shapes(ly.layer(*TEXT)).insert(db.DText(label, db.DTrans(w / 2, h / 2)))
    return cell


def find_label(ly, cell, text, layer):
    li = ly.find_layer(*layer)
    assert li is not None, f"{cell.name}: no layer {layer}"
    hits = []
    it = cell.begin_shapes_rec(li)
    while not it.at_end():
        shape = it.shape()
        if shape.is_text() and shape.text_string == text:
            t = shape.dtext.transformed(it.dtrans())
            hits.append(db.DPoint(t.x, t.y))
        it.next()
    assert len(hits) == 1, f"{cell.name}: expected one label {text!r} on {layer}, found {len(hits)}"
    return hits[0]


def separation(a, b):
    return max(b.left - a.right, a.left - b.right, b.bottom - a.top, a.bottom - b.top)


def build_layout():
    ly = db.Layout()
    ly.dbu = DBU
    top = ly.create_cell(TOP)

    cells = {key: import_block(ly, key, path) for key, path in BLOCKS.items()}
    cells.update({key: make_dummy(ly, *spec) for key, spec in DUMMIES.items()})

    # TopMetal1 must stay empty
    for li in ly.layer_indexes():
        if ly.get_info(li).layer in STRIP_LAYERS:
            ly.clear_layer(li)

    # Place the blocks
    placed = {}
    l_text = ly.layer(*TEXT)
    for inst, key, orient, x, y, desc in PLACEMENT:
        cell = cells[key]
        rot, mirror = ORIENT[orient]
        bbox = cell.dbbox().transformed(db.DTrans(rot, mirror, 0, 0))
        trans = db.DTrans(rot, mirror, snap(x - bbox.left), snap(y - bbox.bottom))
        top.insert(db.DCellInstArray(cell.cell_index(), trans))
        box = cell.dbbox().transformed(trans)
        placed[inst] = (cell, trans, box)
        top.shapes(l_text).insert(db.DText(f"{inst} {desc}", db.DTrans(box.center().x, box.center().y)))

    # Placement checks: inside the macro, below the power band, spaced
    band_bottom = min(y0 for y0, _ in POWER_PINS.values())
    insts = list(placed)
    for i, a in enumerate(insts):
        box = placed[a][2]
        assert box.left >= 0 and box.bottom >= SOUTH_PIN_HEIGHT and box.right <= W, f"{a} outside macro: {box}"
        assert box.top <= band_bottom - MIN_GAP, f"{a} too close to the power straps: {box}"
        for b in insts[i + 1:]:
            sep = separation(box, placed[b][2])
            assert sep >= MIN_GAP - 1e-6, f"{a} and {b} only {sep:.3f} um apart"

    # Pins: name -> (LEF layer, DBox)
    pins = {}
    for name, (inst, label, layer) in WEST_PINS.items():
        cell, trans, _ = placed[inst]
        y = snap_to_m3_track((trans * find_label(ly, cell, label, layer)).y)
        pins[name] = ("Metal3", db.DBox(0, y - WEST_PIN_HEIGHT / 2, WEST_PIN_LEN, y + WEST_PIN_HEIGHT / 2))
    for name, die_x in DIE_ANALOG_PIN_X.items():
        x = snap(die_x - DIE_LOCATION[0])
        pins[name] = ("Metal2", db.DBox(x - SOUTH_PIN_WIDTH / 2, 0, x + SOUTH_PIN_WIDTH / 2, SOUTH_PIN_HEIGHT))
    for name, (y0, y1) in POWER_PINS.items():
        pins[name] = ("Metal3", db.DBox(POWER_X[0], y0, POWER_X[1], y1))

    names = list(pins)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if pins[a][0] == pins[b][0]:
                assert separation(pins[a][1], pins[b][1]) >= 0.21, f"pins {a} and {b} too close"
        for inst, (_, _, box) in placed.items():
            assert separation(pins[a][1], box) > 0, f"pin {a} overlaps {inst}"

    for name, (layer, box) in pins.items():
        num = METAL[layer]
        top.shapes(ly.layer(num, DT_DRAWING)).insert(box)
        top.shapes(ly.layer(num, DT_PIN)).insert(box)
        top.shapes(ly.layer(num, DT_TEXT)).insert(db.DText(name, db.DTrans(box.center().x, box.center().y)))

    top.shapes(ly.layer(*PR_BOUNDARY)).insert(db.DBox(0, 0, W, H))

    # Final checks: nothing above Metal3 except the sah_12bit hold-cap lid, unique names, one top cell
    m4_cell, m4_trans, m4_inst_box = placed[M4_ALLOWED_INST]
    m4_box = m4_cell.dbbox_per_layer(ly.layer(50, 0)).transformed(m4_trans)
    assert not m4_box.empty() and m4_inst_box.contains(m4_box.p1) and m4_inst_box.contains(m4_box.p2)
    m4_obs = m4_box.enlarged(M4_OBS_HALO, M4_OBS_HALO)
    for x0, x1 in M4_STRAP_GROUPS:
        clearance = max(x0 - m4_box.right, m4_box.left - x1)
        assert clearance >= M4_MIN_SPACE, f"Metal4 lid {m4_box} only {clearance:.2f} um from the strap group {x0}-{x1}"
    for x0, x1 in M4_KEEP_GROUPS:
        clearance = max(x0 - m4_obs.right, m4_obs.left - x1)
        assert clearance >= PDN_HORIZONTAL_HALO + 0.5, \
            f"Metal4 OBS {m4_obs} only {clearance:.2f} um from the strap group {x0}-{x1}: LibreLane would cut it"
    for li in ly.layer_indexes():
        if ly.get_info(li).layer in FORBIDDEN_LAYERS:
            used = top.dbbox_per_layer(li)
            if ly.get_info(li).layer in (49, 50) and not used.empty():
                tol = m4_box.enlarged(0.001, 0.001)   # same box after a float transform
                assert tol.contains(used.p1) and tol.contains(used.p2), \
                    f"{ly.get_info(li)} outside the {M4_ALLOWED_INST} lid: {used}"
                continue
            assert used.empty(), f"shapes left on forbidden layer {ly.get_info(li)}"
    cell_names = [c.name for c in ly.each_cell()]
    assert len(cell_names) == len(set(cell_names)), "duplicate cell names"
    assert all(n == TOP or n.startswith(PREFIX) for n in cell_names), "unprefixed cell name"
    assert [c.name for c in ly.top_cells()] == [TOP]
    assert top.dbbox() == db.DBox(0, 0, W, H), f"macro bbox {top.dbbox()} != (0,0;{W},{H})"

    gds = os.path.join(MACRO_DIR, "layout", f"{TOP}.gds")
    opt = db.SaveLayoutOptions()
    opt.format = "GDS2"
    opt.write_context_info = False
    ly.write(gds, opt)
    print(f"Wrote {gds} ({len(cell_names)} cells)")
    for inst, (cell, trans, box) in placed.items():
        print(f"  {inst:6s} {cell.name:55s} {str(trans):24s} ({box.left:7.3f},{box.bottom:7.3f})-({box.right:7.3f},{box.top:7.3f})")
    print(f"  Metal4 lid of {M4_ALLOWED_INST}: {m4_box}")
    return pins, m4_obs


def pin_names(name, width):
    return [name] if width == 0 else [f"{name}[{i}]" for i in range(width)]


def obs_rects(pins, layer):
    """Full macro area minus the pin shapes on this layer (bloated by 0.5 um), as rectangles."""
    to_dbu = lambda v: int(round(v / DBU))
    region = db.Region(db.Box(0, 0, to_dbu(W), to_dbu(H)))
    holes = db.Region()
    for lay, box in pins.values():
        if lay == layer:
            holes.insert(db.Box(to_dbu(box.left), to_dbu(box.bottom), to_dbu(box.right), to_dbu(box.top)))
    region -= holes.sized(to_dbu(0.5))
    rects = []
    for poly in region.each_merged():
        for part in poly.decompose_trapezoids(db.Polygon.TD_htrapezoids):
            assert part.is_box(), "OBS piece is not a rectangle"
            rects.append(part.bbox())
    return sorted([[v * DBU for v in (r.left, r.bottom, r.right, r.top)] for r in rects], key=lambda r: (r[1], r[0]))


def write_lef(pins, m4_obs):
    path = os.path.join(MACRO_DIR, "final", "lef", f"{TOP}.lef")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rect = lambda r: f"RECT {r[0]:.3f} {r[1]:.3f} {r[2]:.3f} {r[3]:.3f} ;"
    lines = [
        "VERSION 5.7 ;",
        '  DIVIDERCHAR "/" ;',
        '  BUSBITCHARS "[]" ;',
        f"MACRO {TOP}",
        "  CLASS BLOCK ;",
        f"  FOREIGN {TOP} ;",
        "  ORIGIN 0.000 0.000 ;",
        f"  SIZE {W:.3f} BY {H:.3f} ;",
    ]

    def pin(name, direction, use):
        layer, box = pins[name]
        lines.extend([
            f"  PIN {name}",
            f"    DIRECTION {direction} ;",
            f"    USE {use} ;",
            "    PORT",
            f"      LAYER {layer} ;",
            f"        {rect([box.left, box.bottom, box.right, box.top])}",
            "    END",
            f"  END {name}",
        ])

    for name, direction, width in PORTS:
        for bit in pin_names(name, width):
            pin(bit, LEF_DIRECTION[direction], "SIGNAL")
    for name in POWER_PINS:
        pin(name, "INOUT", POWER_USE[name])

    lines.append("  OBS")
    for layer in METAL:
        lines.append(f"    LAYER {layer} ;")
        lines.extend(f"      {rect(r)}" for r in obs_rects(pins, layer))
    lines.append("    LAYER Metal4 ;")     # keeps top-level routing off the hold-cap lid
    lines.append(f"      {rect([m4_obs.left, m4_obs.bottom, m4_obs.right, m4_obs.top])}")
    lines += ["  END", f"END {TOP}", "", "END LIBRARY", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {path}")


def write_vh():
    path = os.path.join(MACRO_DIR, "final", "vh", f"{TOP}.vh")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [
        "// Blackbox of the analogue_interface hard macro (dry-run version: placed blocks and dummies, not routed).",
        "// Generated by scripts/build_analogue_interface.py.",
        "",
        f"module {TOP} (",
        "`ifdef USE_POWER_PINS",
    ]
    lines += ["    inout  wire VPWR,", "    inout  wire VAPWR,", "    inout  wire VGND,", "`endif"]
    ports = []
    for name, direction, width in PORTS:
        rng = f"[{width - 1}:0] " if width else ""
        ports.append(f"    {direction:6s} wire {rng}{name}")
    lines.append(",\n".join(ports))
    lines += [");", "endmodule", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {path}")


def write_lib():
    path = os.path.join(MACRO_DIR, "final", "lib", f"{TOP}.lib")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [
        f"library ({TOP}) {{",
        '  comment : "Timing-free view of the dry-run analogue_interface macro (no timing arcs)";',
        "  delay_model : table_lookup;",
        "  capacitive_load_unit (1, pf);",
        '  current_unit : "1mA";',
        '  leakage_power_unit : "1nW";',
        '  pulling_resistance_unit : "1kohm";',
        '  time_unit : "1ns";',
        '  voltage_unit : "1V";',
        "  nom_process : 1.0;",
        "  nom_temperature : 25.0;",
        "  nom_voltage : 1.2;",
        "  input_threshold_pct_fall : 50.0;",
        "  input_threshold_pct_rise : 50.0;",
        "  output_threshold_pct_fall : 50.0;",
        "  output_threshold_pct_rise : 50.0;",
        "  slew_lower_threshold_pct_fall : 20.0;",
        "  slew_lower_threshold_pct_rise : 20.0;",
        "  slew_upper_threshold_pct_fall : 80.0;",
        "  slew_upper_threshold_pct_rise : 80.0;",
        "  voltage_map (VPWR, 1.2);",
        "  voltage_map (VAPWR, 3.3);",
        "  voltage_map (VGND, 0.0);",
    ]
    for width in sorted({w for _, _, w in PORTS if w}):
        lines += [
            f"  type (bus{width}) {{",
            "    base_type : array;",
            "    data_type : bit;",
            f"    bit_width : {width};",
            f"    bit_from : {width - 1};",
            "    bit_to : 0;",
            "    downto : true;",
            "  }",
        ]
    lines += [
        f"  cell ({TOP}) {{",
        f"    area : {W * H:.1f};",
        "    is_macro_cell : true;",
        "    dont_touch : true;",
        "    dont_use : true;",
        "    pg_pin (VPWR) { pg_type : primary_power; voltage_name : VPWR; }",
        "    pg_pin (VAPWR) { pg_type : primary_power; voltage_name : VAPWR; }",
        "    pg_pin (VGND) { pg_type : primary_ground; voltage_name : VGND; }",
    ]
    for name, direction, width in PORTS:
        power = "VAPWR" if direction == "inout" else "VPWR"
        body = [f"direction : {direction};"]
        if direction != "output":
            body.append("capacitance : 0.005;")
        body += [f"related_power_pin : {power};", "related_ground_pin : VGND;"]
        if width:
            lines.append(f"    bus ({name}) {{")
            lines.append(f"      bus_type : bus{width};")
        else:
            lines.append(f"    pin ({name}) {{")
        lines += [f"      {b}" for b in body]
        lines.append("    }")
    lines += ["  }", "}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {path}")


if __name__ == "__main__":
    pins, m4_obs = build_layout()
    write_lef(pins, m4_obs)
    write_vh()
    write_lib()
