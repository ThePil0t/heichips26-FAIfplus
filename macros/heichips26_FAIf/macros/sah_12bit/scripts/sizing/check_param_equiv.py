# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0
"""Check that sah_12bit_param (testbenches/xschem, used by the sizing and final testbenches) at its
default parameters is the same circuit as the frozen cell schematic/xschem/sah_12bit.sch.

Both schematics are netlisted with xschem, the {expressions} of the param cell are evaluated with the
.subckt defaults, and every device is compared (nodes, model, w, l, ng, m).
Run inside nix-shell with PDK_ROOT/PDK set, from the macro folder:
    python3 scripts/sizing/check_param_equiv.py
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MACRO = os.path.normpath(os.path.join(HERE, "..", ".."))
CELLS = [("schematic/xschem", "sah_12bit"), ("testbenches/xschem", "sah_12bit_param")]
SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3}


def netlist(folder, cell, out):
    subprocess.run(["xschem", "-r", "-x", "-q", "--rcfile", "xschemrc", "--command",
                    f"set top_is_subckt 1; set netlist_dir {out}; xschem netlist", f"{cell}.sch"],
                   cwd=os.path.join(MACRO, folder), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return open(os.path.join(out, f"{cell}.spice")).read()


def num(v):
    m = re.fullmatch(r"([-+0-9.eE]+)([fpnum]?)", v)
    return float(m.group(1)) * SI.get(m.group(2), 1.0)


def sym_defaults(folder, cell):
    """parameter defaults from the symbol template (the standalone netlist has none on its .subckt line)"""
    t = open(os.path.join(MACRO, folder, f"{cell}.sym")).read()
    m = re.search(r'template="([^"]*)"', t)
    return {k: num(v) for k, v in re.findall(r"(\w+)=(\S+)", m.group(1)) if k != "name"}


def devices(text, params=None):
    lines = [l for l in text.splitlines()]
    # join continuation lines
    joined = []
    for l in lines:
        if l.startswith("+") and joined:
            joined[-1] += " " + l[1:]
        else:
            joined.append(l)
    params, devs = dict(params or {}), {}
    for l in joined:
        if l.lower().startswith(".subckt"):
            for k, v in re.findall(r"(\w+)=(\S+)", l):
                params[k] = num(v)
        elif l[:1] in "XxMmCc" and not l.startswith("*"):
            tok = l.split()
            kv = dict(re.findall(r"(\w+)=(\S+)", l))
            pos = [t for t in tok[1:] if "=" not in t]
            vals = {}
            for k in ("w", "l", "ng", "m"):
                if k in kv:
                    v = kv[k]
                    if v.startswith("{"):
                        expr = v.strip("{}")
                        v = eval(expr, {}, dict(params))
                    else:
                        v = num(v)
                    vals[k] = round(float(v), 15)
            devs[tok[0]] = (tuple(pos[:-1]), pos[-1], vals)
    return devs


def main():
    with tempfile.TemporaryDirectory() as d:
        frozen = devices(netlist(*CELLS[0], d))
        param = devices(netlist(*CELLS[1], d), sym_defaults(*CELLS[1]))
    ok = True
    for name in sorted(set(frozen) | set(param)):
        a, b = frozen.get(name), param.get(name)
        if a != b:
            ok = False
            print(f"MISMATCH {name}:\n  frozen {a}\n  param  {b}")
    print(f"{len(frozen)} devices compared:", "sah_12bit_param at its defaults == sah_12bit" if ok else "DIFFERENT")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
