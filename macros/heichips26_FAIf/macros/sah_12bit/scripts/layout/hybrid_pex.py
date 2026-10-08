# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0
"""Build the post-layout netlist netlist/pex/sah_12bit_hybrid_pex.spice (.subckt sah_12bit_pex).

Neither extractor handles the hold cap correctly. Magic has no cap_cmomi device: it turns the
fingers into ~1.48 pF of wire coupling (the PDK model says 1.214 pF) and books their area as
junction area of an SH_OUT transistor. The KLayout LVS netlist has the right devices but no wires.
So the netlist is put together from:
- devices: frozen sizes, with the junction areas (as/ad/ps/pd) of the transmission gate taken
  from the KLayout LVS extraction (netlist/layout/sah_12bit_klayout.cir, run make klayout-lvs first);
- C1: the PDK cap_cmomi model, w/l kept as parameters CW/CL (for the +-35 % spread corners);
- wire parasitics: Magic C-coupled extraction of the layout without the cap and its shield box;
- cap environment (poly floor, Metal4 lid, fence, substrate) on SH_OUT-VSS: Magic C(shielded cap)
  - C(bare cap), scaled by C_model / C_Magic(bare cap).
Run inside nix-shell (PDK_ROOT/PDK set) from the macro folder:
    python3 scripts/layout/hybrid_pex.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

import klayout.db as db

HERE = os.path.dirname(os.path.abspath(__file__))
MACRO = os.path.normpath(os.path.join(HERE, "..", ".."))
GDS = os.path.join(MACRO, "layout", "sah_12bit.gds")
KLAY_CIR = os.path.join(MACRO, "netlist", "layout", "sah_12bit_klayout.cir")
OUT = os.path.join(MACRO, "netlist", "pex", "sah_12bit_hybrid_pex.spice")
C_MODEL = 1213.803e-15            # cap_cmomi model / PCell label for w=54.29u l=27.72u
SHIELD_X0 = 49.3                  # everything right of this belongs to the cap and its shield box
PLUS_XY, MINUS_XY = (50.92, 30.0), (79.84, 30.0)   # points on the PLUS and MINUS pads (Metal3)
SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3}


def num(v):
    m = re.fullmatch(r"([-+0-9.eE]+)([fpnum]?)", v)
    return float(m.group(1)) * SI.get(m.group(2), 1.0)


def variant(work, name, keep_cap, keep_devices, region):
    """Copy of the layout: region 'left' (x < SHIELD_X0) or 'right' or 'none' of the top-level shapes."""
    ly = db.Layout()
    ly.read(GDS)
    top = ly.cell("sah_12bit")
    for inst in list(top.each_inst()):
        is_cap = inst.cell.name.endswith("cap_cmomi")
        if (is_cap and not keep_cap) or (not is_cap and not keep_devices):
            inst.delete()
    right = db.Region(db.DBox(SHIELD_X0, -10, 200, 200).to_itype(ly.dbu))
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        if info.datatype == 25 and region == "left":
            continue                              # keep the pin labels
        r = db.Region(top.shapes(li))
        r = {"left": r - right, "right": r & right, "none": db.Region()}[region]
        top.shapes(li).clear()
        top.shapes(li).insert(r)
    if region != "left":                          # label the cap terminals
        t = ly.layer(30, 25)
        top.shapes(t).insert(db.DText("SH_OUT", db.DTrans(*PLUS_XY)))
        top.shapes(t).insert(db.DText("VSS", db.DTrans(*MINUS_XY)))
    for c in [c for c in ly.top_cells() if c.name != "sah_12bit"]:
        c.prune_cell()
    d = os.path.join(work, name)
    os.makedirs(d, exist_ok=True)
    ly.write(os.path.join(d, "sah_12bit.gds"))
    subprocess.run(["sh", os.path.join(MACRO, "scripts", "sak-pex.sh"), "-m", "2", "-w", d,
                    os.path.join(d, "sah_12bit.gds")], cwd=d, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return parse_magic(os.path.join(d, "sah_12bit.pex.spice"))


def parse_magic(path):
    devs, caps = [], []
    for line in open(path):
        tok = line.split()
        if not tok:
            continue
        if tok[0].startswith("X"):
            devs.append(tok[1:6])
        elif tok[0].startswith("C"):
            caps.append((tok[1], tok[2], num(tok[3])))
    return devs, caps


def cap_between(caps, a, b):
    return sum(c for n1, n2, c in caps if {n1, n2} == {a, b})


def klayout_junctions():
    """TG device name -> as/ad/ps/pd from the KLayout LVS netlist, oriented like the schematic (d = SH_IN side)."""
    text = open(KLAY_CIR).read().replace("\n+", " ")
    out = {}
    for line in text.splitlines():
        if not line.startswith("M"):
            continue
        tok = line.split()
        d, g, s, b, model = tok[1:6]
        p = dict(re.findall(r"(\w+)=(\S+)", line))
        pmos = "pmos" in model
        if {d, s} == {"SH_IN", "SH_OUT"}:
            name = "XMP1" if pmos else "XMN1"
            if d != "SH_IN":                       # schematic: d = SH_IN, s = SH_OUT
                p["AS"], p["AD"], p["PS"], p["PD"] = p["AD"], p["AS"], p["PD"], p["PS"]
        elif d == s == "SH_IN":
            name = "XMPD1" if pmos else "XMND1"
        elif d == s == "SH_OUT":
            name = "XMPD2" if pmos else "XMND2"
        else:
            continue
        out[name] = f"as={p['AS']} ad={p['AD']} ps={p['PS']} pd={p['PD']}"
    assert len(out) == 6, f"expected the 6 transmission-gate devices in {KLAY_CIR}, got {sorted(out)}"
    return out


def node_map(devs):
    """Magic node names of variant A -> schematic net names."""
    m = {n: n for n in ("SH_IN", "SH_OUT", "SH_EN", "VDD", "VSS")}
    for d, g, s, b, model in devs:
        pmos = "pmos" in model
        if {d, s} == {"SH_IN", "SH_OUT"}:
            m[g] = "sw_b" if pmos else "sw"
        elif d == s == "SH_OUT" and pmos:
            m[g] = "sw_d"
        elif g == "SH_EN":
            m[d if d not in ("VDD", "VSS") else s] = "sw_n"
    return m


def main():
    junc = klayout_junctions()
    work = tempfile.mkdtemp(prefix="sah12_hybrid_pex_")
    devs_a, caps_a = variant(work, "A_wires", keep_cap=False, keep_devices=True, region="left")
    _, caps_b = variant(work, "B_bare_cap", keep_cap=True, keep_devices=False, region="none")
    _, caps_c = variant(work, "C_shielded_cap", keep_cap=True, keep_devices=False, region="right")
    shutil.rmtree(work)
    c_bare = cap_between(caps_b, "SH_OUT", "VSS")
    c_shielded = cap_between(caps_c, "SH_OUT", "VSS")
    c_env = (c_shielded - c_bare) * C_MODEL / c_bare
    nm = node_map(devs_a)
    unknown = {n for n1, n2, _ in caps_a for n in (n1, n2) if n not in nm}
    assert not unknown, f"unmapped Magic nodes: {unknown}"

    lines = [
        "* sah_12bit post-layout netlist (hybrid), generated by scripts/layout/hybrid_pex.py",
        f"* Magic C(SH_OUT,VSS): bare cap {c_bare * 1e15:.1f} fF, shielded cap {c_shielded * 1e15:.1f} fF;"
        f" model C1 {C_MODEL * 1e15:.1f} fF -> cap environment {c_env * 1e15:.1f} fF",
        ".subckt sah_12bit_pex VDD SH_IN SH_OUT SH_EN VSS CW=54.29e-6 CL=27.72e-6",
        f"XMN1 SH_IN sw SH_OUT VSS sg13_hv_nmos w=0.6u l=0.45u ng=2 m=1 {junc['XMN1']}",
        f"XMP1 SH_IN sw_b SH_OUT VDD sg13_hv_pmos w=1.8u l=0.45u ng=2 m=1 {junc['XMP1']}",
        f"XMND1 SH_IN sw_b SH_IN VSS sg13_hv_nmos w=0.3u l=0.45u ng=1 m=1 {junc['XMND1']}",
        f"XMPD1 SH_IN sw_d SH_IN VDD sg13_hv_pmos w=0.9u l=0.45u ng=1 m=1 {junc['XMPD1']}",
        f"XMND2 SH_OUT sw_b SH_OUT VSS sg13_hv_nmos w=0.3u l=0.45u ng=1 m=1 {junc['XMND2']}",
        f"XMPD2 SH_OUT sw_d SH_OUT VDD sg13_hv_pmos w=0.9u l=0.45u ng=1 m=1 {junc['XMPD2']}",
        "XMPI1 sw_n SH_EN VDD VDD sg13_hv_pmos w=1.2u l=0.45u ng=1 m=1",
        "XMNI1 sw_n SH_EN VSS VSS sg13_hv_nmos w=0.6u l=0.45u ng=1 m=1",
        "XMPI2 sw sw_n VDD VDD sg13_hv_pmos w=1.2u l=0.45u ng=1 m=1",
        "XMNI2 sw sw_n VSS VSS sg13_hv_nmos w=0.6u l=0.45u ng=1 m=1",
        "XMPI3 sw_b sw VDD VDD sg13_hv_pmos w=1.2u l=0.45u ng=1 m=2",
        "XMNI3 sw_b sw VSS VSS sg13_hv_nmos w=0.6u l=0.45u ng=1 m=2",
        "XMPI4 sw_d sw_b VDD VDD sg13_hv_pmos w=1.2u l=0.45u ng=1 m=2",
        "XMNI4 sw_d sw_b VSS VSS sg13_hv_nmos w=0.6u l=0.45u ng=1 m=2",
        "XC1 SH_OUT VSS cap_cmomi w={CW} l={CL} mmin=1 mmax=3 feed=double subblock=0 m=1 mm_ok=1",
        "* wire parasitics (Magic, C-coupled, layout without the cap and its shield box)",
    ]
    for i, (n1, n2, c) in enumerate(caps_a):
        lines.append(f"Cw{i} {nm[n1]} {nm[n2]} {c * 1e15:.5f}f")
    lines += [f"Cenv SH_OUT VSS {c_env * 1e15:.3f}f", ".ends", ""]
    with open(OUT, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {OUT}")
    print(f"  C(SH_OUT,VSS) wires {cap_between(caps_a, 'SH_OUT', 'VSS') * 1e15:.2f} fF, cap environment {c_env * 1e15:.1f} fF")
    for a, b in (("SH_OUT", "SH_IN"), ("SH_OUT", "sw"), ("SH_OUT", "sw_b"), ("SH_OUT", "sw_d"), ("SH_OUT", "VDD")):
        c = sum(c for n1, n2, c in caps_a if {nm[n1], nm[n2]} == {a, b})
        print(f"  C({a},{b}) = {c * 1e15:.3f} fF")


if __name__ == "__main__":
    sys.exit(main())
