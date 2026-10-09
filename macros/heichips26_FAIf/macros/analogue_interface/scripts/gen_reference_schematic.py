#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
"""Generate the LVS reference schematic of the analog macro.

Writes schematic/xschem/analogue_interface.sch/.sym and an xschemrc. The schematic holds the
analog part of the top schematic (x1..x12, R1, R2, C1, same symbols, positions and parameters)
plus the 4 spare level translators xcap0..3 of the macro. Every instance pin gets a net label;
the nets come from an Xschem netlist of the top schematic (Xschem is the authority, the saved
wire labels of the top schematic are partly stale) and are renamed to the macro ports.

Needs PDK_ROOT and PDK in the environment and xschem on the PATH (nix-shell).
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MACRO_DIR = os.path.dirname(HERE)                       # .../macros/analogue_interface
MACROS = os.path.dirname(MACRO_DIR)                     # .../macros
TOP_DIR = os.path.join(os.path.dirname(MACROS), "schematic", "xschem")
TOP_SCH = os.path.join(TOP_DIR, "heichips26_FAIf.sch")
OUT_DIR = os.path.join(MACRO_DIR, "schematic", "xschem")
NAME = "analogue_interface"

KEEP = ["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9", "x10", "x11", "x12", "R1", "R2", "C1", "C2"]
SPARES = 4

# macro ports in .vh/LEF order: (name, xschem pin symbol, symbol pin direction)
PORTS = [
    ("VPWR", "iopin", "inout"), ("VAPWR", "iopin", "inout"), ("VGND", "iopin", "inout"),
    ("adc_ref[7:0]", "ipin", "in"), ("adc_hold", "ipin", "in"), ("adc_comp", "opin", "out"),
    ("dac_out[15:0]", "ipin", "in"), ("sh_cap_en[3:0]", "ipin", "in"),
    ("analog_0", "iopin", "inout"), ("analog_1", "iopin", "inout"), ("analog_2", "iopin", "inout"),
]

LIB_DIRS = [
    "8x_inverting_digital_level_translator/schematic/xschem",
    "8x_inverting_digital_level_translator/macros/inverting_digital_level_translator/schematic/xschem",
    "comparator/schematic/xschem", "down_digital_translator/schematic/xschem",
    "opamp/schematic/xschem", "ptat_current_source/schematic/xschem", "r2r_dac/schematic/xschem",
    "digital_level_translator/schematic/xschem", "sah_12bit/schematic/xschem",
]


def rename(net):
    """Top-level net name -> macro net name."""
    m = re.fullmatch(r"DAC0_OUT\[(\d)\]", net)
    if m:
        return f"dac_out[{int(m.group(1))}]"
    m = re.fullmatch(r"DAC1_OUT\[(\d)\]", net)
    if m:
        return f"dac_out[{8 + int(m.group(1))}]"
    m = re.fullmatch(r"SAR_DAC\[(\d)\]", net)
    if m:
        return f"adc_ref[{int(m.group(1))}]"
    return {"SAR_SnH": "adc_hold", "SAR_COMP": "adc_comp"}.get(net, net)


def read_blocks(path):
    """Split an xschem file into top-level records ('C', text), keeping multi-line attribute blocks."""
    text = open(path).read()
    recs, i = [], 0
    while i < len(text):
        j = i
        depth = 0
        while j < len(text):
            ch = text[j]
            if ch == "\\":
                j += 2
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            elif ch == "\n" and depth == 0:
                break
            j += 1
        recs.append(text[i:j])
        i = j + 1
    return [r for r in recs if r.strip()]


def find_symbol(ref):
    cands = [os.path.join(MACROS, d, ref) for d in LIB_DIRS]
    cands.append(os.path.join(os.environ["PDK_ROOT"], os.environ["PDK"], "libs.tech", "xschem", ref))
    for c in cands:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(ref)


def symbol_pins(ref):
    """[(pin name, x, y)] in @pinlist order (B 5 order, or sim_pinnumber if given)."""
    pins = []
    for line in open(find_symbol(ref)):
        m = re.match(r"B 5 (\S+) (\S+) (\S+) (\S+) \{(.*)\}", line)
        if m:
            x = (float(m.group(1)) + float(m.group(3))) / 2
            y = (float(m.group(2)) + float(m.group(4))) / 2
            name = re.search(r"name=(\S+)", m.group(5)).group(1)
            num = re.search(r"sim_pinnumber=(\d+)", m.group(5))
            pins.append((int(num.group(1)) if num else len(pins) + 1, name, x, y))
    return [(n, x, y) for _, n, x, y in sorted(pins)]


def place(x, y, rot, flip, px, py):
    """xschem ROTATION(): symbol point -> schematic point."""
    xf = -px if flip else px
    rx, ry = [(xf, py), (-py, xf), (-xf, -py), (py, -xf)][rot]
    return x + rx, y + ry


def top_netlist():
    tmp = tempfile.mkdtemp()
    subprocess.run(["xschem", "--rcfile", "xschemrc", "-n", "-s", "-q", "--no_x", "-o", tmp,
                    "-N", "top.spice", "heichips26_FAIf.sch"], cwd=TOP_DIR, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    lines, cur = [], ""
    for line in open(os.path.join(tmp, "top.spice")):
        line = line.rstrip("\n")
        if line.startswith(".subckt"):
            break
        if line.startswith("+"):
            cur += " " + line[1:].strip()
        else:
            if cur:
                lines.append(cur)
            cur = line
    lines.append(cur)
    return lines


def main():
    recs = read_blocks(TOP_SCH)
    inst = {}
    for r in recs:
        m = re.match(r"C \{([^}]*)\} (\S+) (\S+) (\d) (\d) \{name=([^\s}]+)", r)
        if m and m.group(6) in KEEP:
            inst[m.group(6)] = (m.group(1), float(m.group(2)), float(m.group(3)),
                                int(m.group(4)), int(m.group(5)), r)
    assert sorted(inst) == sorted(KEEP), sorted(inst)

    # nets from the top netlist (instance -> nodes in @pinlist order)
    nodes = {}
    for line in top_netlist():
        tok = line.split()
        if not tok:
            continue
        name = tok[0][1:] if tok[0][0] in "Xx" and tok[0][1:] in KEEP and tok[0] not in KEEP else tok[0]
        if name in inst:
            nodes[name] = tok[1:]
    assert sorted(nodes) == sorted(KEEP), sorted(nodes)

    # readable names for the auto nets: translator outputs and the S&H links
    auto = {}
    for t, pre in (("x6", "sar_nd"), ("x7", "dac0_nd"), ("x12", "dac1_nd")):
        for (pin, _, _), net in zip(symbol_pins(inst[t][0]), nodes[t]):
            m = re.fullmatch(r"nLOUT(\d)", pin)
            if m:
                auto[net] = f"{pre}{m.group(1)}"
    for (pin, _, _), net in zip(symbol_pins(inst["x10"][0]), nodes["x10"]):
        if pin in ("SH_IN", "SH_EN"):
            auto[net] = pin.lower()

    out = ["v {xschem version=3.4.8RC file_version=1.3}", "G {}", "K {}", "V {}", "S {}", "E {}",
           "T {Generated by scripts/gen_reference_schematic.py from heichips26_FAIf.sch - do not edit.\n"
           "LVS reference of the analog macro: analog part of the top schematic plus spares xcap0..3.} "
           "100 -2400 0 0 0.6 0.6 {}"]
    lab = 0
    pin_nets = {}

    def label(x, y, net, left):
        nonlocal lab
        lab += 1
        out.append(f"C {{lab_pin.sym}} {x:g} {y:g} 0 {0 if left else 1} "
                   f"{{name=l{lab} sig_type=std_logic lab={net}}}")

    for n in KEEP:
        sym, x, y, rot, flip, rec = inst[n]
        out.append(rec)
        pins = symbol_pins(sym)
        cx = sum(place(x, y, rot, flip, px, py)[0] for _, px, py in pins) / len(pins)
        for (pin, px, py), net in zip(pins, nodes[n]):
            net = auto.get(net, rename(net))
            sx, sy = place(x, y, rot, flip, px, py)
            label(sx, sy, net, sx <= cx)
            pin_nets[(n, pin)] = net

    # spare translators (sh_cap_en outputs, unconnected in this design)
    sym = "digital_level_translator.sym"
    for k in range(SPARES):
        x, y = 1970 + 300 * k, 200
        out.append(f"C {{{sym}}} {x} {y} 0 0 {{name=xcap{k}}}")
        nets = {"PLAVDD": "VAPWR", "PLDVDD": "VPWR", "PLVSS": "VGND",
                "LIN": f"sh_cap_en[{k}]", "LOUT": f"cap_out{k}"}
        for pin, px, py in symbol_pins(sym):
            sx, sy = place(x, y, 0, 0, px, py)
            label(sx, sy, nets[pin], px < 80)

    # macro ports
    for i, (pname, psym, _) in enumerate(PORTS):
        out.append(f"C {{{psym}.sym}} -300 {-2200 + 40 * i} 0 0 {{name=p{i} lab={pname}}}")

    os.makedirs(OUT_DIR, exist_ok=True)
    open(os.path.join(OUT_DIR, NAME + ".sch"), "w").write("\n".join(out) + "\n")

    # symbol: inputs on the left, outputs/inouts on the right, pins in PORTS order
    sym_lines = ["v {xschem version=3.4.8RC file_version=1.3}", "G {}",
                 'K {type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=x1"\n}',
                 "V {}", "S {}", "E {}"]
    left = [p for p in PORTS if p[2] == "in"]
    right = [p for p in PORTS if p[2] != "in"]
    h = 20 * (max(len(left), len(right)) + 1)
    sym_lines.append(f"P 4 5 -100 -20 100 -20 100 {h} -100 {h} -100 -20 {{}}")
    sym_lines.append(f"T {{@symname}} -60 {h + 10} 0 0 0.3 0.3 {{}}")
    sym_lines.append(f"T {{@name}} -60 -40 0 0 0.3 0.3 {{}}")
    ypos = {}
    for side, plist, x0 in (("l", left, -120), ("r", right, 120)):
        for i, p in enumerate(plist):
            ypos[p[0]] = (x0, 20 * i)
    for pname, _, d in PORTS:
        x0, yy = ypos[pname]
        xl = -100 if x0 < 0 else 100
        sym_lines.append(f"L 4 {x0} {yy} {xl} {yy} {{}}")
        sym_lines.append(f"B 5 {x0 - 2.5} {yy - 2.5} {x0 + 2.5} {yy + 2.5} {{name={pname} dir={d}}}")
        tx = xl + 5 if x0 < 0 else xl - 5
        sym_lines.append(f"T {{{pname}}} {tx} {yy - 6} 0 {0 if x0 < 0 else 1} 0.2 0.2 {{}}")
    open(os.path.join(OUT_DIR, NAME + ".sym"), "w").write("\n".join(sym_lines) + "\n")

    # xschemrc: PDK + all block libraries
    rc = ["# Generated by scripts/gen_reference_schematic.py",
          "if {![info exists PDK]} {", "  source $env(PDK_ROOT)/$env(PDK)/libs.tech/xschem/xschemrc", "}",
          "set xschem_execute_scripts yes",
          "append XSCHEM_LIBRARY_PATH :[file dirname [info script]]"]
    rc += [f"append XSCHEM_LIBRARY_PATH :[file normalize [file join [file dirname [info script]] ../../../{d}]]"
           for d in LIB_DIRS]
    open(os.path.join(OUT_DIR, "xschemrc"), "w").write("\n".join(rc) + "\n")

    # mapping file for the compare step
    with open(os.path.join(OUT_DIR, NAME + ".pins.txt"), "w") as f:
        for (n, pin), net in sorted(pin_nets.items()):
            f.write(f"{n} {pin} {net}\n")
    print(f"wrote {OUT_DIR}/{NAME}.sch/.sym/xschemrc ({len(KEEP)} instances + {SPARES} spares, {lab} labels)")


if __name__ == "__main__":
    sys.exit(main())
