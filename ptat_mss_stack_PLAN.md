# Plan: split the PTAT's `MSS[5:1]` stack into 5 single transistors so the LVS netlist works

## Context
`make klayout-lvs` stops at the schematic netlist. In `ptat_curr_gen.sch` the startup stack is one Xschem vector instance, `MSS[5:1]`: 5 diode-connected HV PMOS in series, 0.3/0.4 µm, each with bulk tied to source. In the LVS netlist mode, Xschem evaluates the PDK symbol's `drc="fet_drc @name …"` as Tcl. The bracket in `MSS[5:1]` is then read as a Tcl command (`invalid command name "5:1"`), and netlisting fails with error 10. The plain SPICE netlist works and shows the stack:

```
XMSS[5] wcs[4] wcs[4] CSSTARTUP CSSTARTUP sg13_hv_pmos w=0.3u l=0.4u ng=1 m=1   (D G S B)
XMSS[4] wcs[3] wcs[3] wcs[4]    wcs[4]    ...
XMSS[3] wcs[2] wcs[2] wcs[3]    wcs[3]    ...
XMSS[2] wcs[1] wcs[1] wcs[2]    wcs[2]    ...
XMSS[1] PCSVSS PCSVSS wcs[1]    wcs[1]    ...
```

Decision (answered): I edit the schematic with a script. It replaces the vector instance with 5 single instances `MSS5`…`MSS1` and the bus nets with plain nets `wcs4`…`wcs1`. The circuit stays identical, and the LVS netlist then has no bracketed names.

## Step 0 (me): save the plan
Copy this plan to `/home/benedikt/heichips26-FAIf/ptat_mss_stack_PLAN.md` and commit only that file. Do not push.

## Step 1 (me): run this script on `ptat_curr_gen.sch`
How the edit works:
- **MSS5 stays in place.** The original instance (at 690, −260) keeps its wires and gets the name `MSS5`. Its two bus labels become `CSSTARTUP` (top) and `wcs4` (bottom).
- **The other four are copies.** `MSS4`…`MSS1` are copies of the same small drawing: transistor, gate-drain tie, bulk-source tie, a stub at top and bottom, and two net labels. They go in a row in free space above the drawing (y = −800, x = 690…990; the drawing spans y −580…0), so they can't touch existing wires.
- **Connections run through net labels**, exactly as in the original.
- **Safety checks:** the script asserts that every line it changes exists exactly as expected. If one doesn't match, it stops without writing.

```python
#!/usr/bin/env python3
"""Split the vector instance MSS[5:1] in ptat_curr_gen.sch into MSS5..MSS1 (nets wcs4..wcs1)."""
import re, sys

path = sys.argv[1]
lines = open(path).read().split("\n")

# --- the drawing of the original stack (all must exist exactly once) -------------------
WIRES = [  # (text of the wire line without its lab attribute, side)
    ("N 710 -220 710 -200", "bot"), ("N 660 -260 670 -260", "bot"), ("N 660 -260 660 -220", "bot"),
    ("N 660 -220 710 -220", "bot"), ("N 710 -230 710 -220", "bot"),
    ("N 710 -300 710 -290", "top"), ("N 710 -260 720 -260", "top"), ("N 720 -300 720 -260", "top"),
    ("N 710 -300 720 -300", "top"), ("N 710 -310 710 -300", "top"),
]
OLD_LAB = {"top": "CSSTARTUP,wcs[4:1]", "bot": "wcs[4:1],PCSVSS"}
LBL_TOP = "C {lab_wire.sym} 710 -310 0 1 {name=p8 sig_type=std_logic lab=CSSTARTUP,wcs[4:1]}"
LBL_BOT = "C {lab_wire.sym} 710 -200 0 1 {name=p11 sig_type=std_logic lab=wcs[4:1],PCSVSS}"
INST_HEAD = "C {sg13g2_pr/sg13_hv_pmos.sym} 690 -260 0 0 {name=MSS[5:1]"
INST_BODY = ["l=0.4u", "w=0.3u", "ng=1", "m=1", "model=sg13_hv_pmos", "spiceprefix=X", "}"]

def find_one(text):
    idx = [i for i, l in enumerate(lines) if l == text]
    assert len(idx) == 1, f"expected exactly one line {text!r}, found {len(idx)}"
    return idx[0]

wire_idx = {}
for w, side in WIRES:
    full = f"{w} {{lab={OLD_LAB[side]}}}"
    wire_idx[w] = find_one(full)
i_top, i_bot, i_inst = find_one(LBL_TOP), find_one(LBL_BOT), find_one(INST_HEAD)
assert lines[i_inst + 1:i_inst + 1 + len(INST_BODY)] == INST_BODY, "unexpected MSS[5:1] attributes"

# nets per transistor: top = source/bulk, bottom = drain/gate
NETS = {5: ("CSSTARTUP", "wcs4"), 4: ("wcs4", "wcs3"), 3: ("wcs3", "wcs2"),
        2: ("wcs2", "wcs1"), 1: ("wcs1", "PCSVSS")}

def shift(x, y, dx, dy):
    return x + dx, y + dy

def wire_line(w, side, k, dx, dy):
    _, x1, y1, x2, y2 = w.split()
    x1, y1 = shift(int(x1), int(y1), dx, dy); x2, y2 = shift(int(x2), int(y2), dx, dy)
    return f"N {x1} {y1} {x2} {y2} {{lab={NETS[k][0] if side == 'top' else NETS[k][1]}}}"

# --- 1. turn the original into MSS5 --------------------------------------------------------
for w, side in WIRES:
    lines[wire_idx[w]] = wire_line(w, side, 5, 0, 0)
lines[i_top] = "C {lab_wire.sym} 710 -310 0 1 {name=p8 sig_type=std_logic lab=CSSTARTUP}"
lines[i_bot] = "C {lab_wire.sym} 710 -200 0 1 {name=p11 sig_type=std_logic lab=wcs4}"
lines[i_inst] = "C {sg13g2_pr/sg13_hv_pmos.sym} 690 -260 0 0 {name=MSS5"

# --- 2. add MSS4..MSS1 as copies above the drawing ------------------------------------------
new_wires, new_comps = [], []
for n, k in enumerate((4, 3, 2, 1)):
    dx, dy = 100 * n, -540
    new_wires += [wire_line(w, side, k, dx, dy) for w, side in WIRES]
    new_comps.append(f"C {{lab_wire.sym}} {710 + dx} {-310 + dy} 0 1 {{name=p_mss{k}_s sig_type=std_logic lab={NETS[k][0]}}}")
    new_comps.append(f"C {{lab_wire.sym}} {710 + dx} {-200 + dy} 0 1 {{name=p_mss{k}_d sig_type=std_logic lab={NETS[k][1]}}}")
    new_comps.append(f"C {{sg13g2_pr/sg13_hv_pmos.sym}} {690 + dx} {-260 + dy} 0 0 {{name=MSS{k}")
    new_comps += INST_BODY

# keep Xschem's file order: new wires after the last wire line, new components at the end
last_wire = max(i for i, l in enumerate(lines) if l.startswith("N "))
lines[last_wire + 1:last_wire + 1] = new_wires
while lines and lines[-1] == "":
    lines.pop()
lines += new_comps + [""]
open(path, "w").write("\n".join(lines))
print("MSS[5:1] split into MSS5..MSS1; added", len(new_wires), "wires and", len(new_comps), "component lines")
```

How it is run (from the PTAT schematic folder, inside `nix-shell`; any Python 3 works):
```sh
python3 split_mss_stack.py ptat_curr_gen.sch
```
The script itself lives in my scratch folder, not in the repo.

## Verification (me)
1. **Netlist unchanged:** netlist `ptat_curr_gen.sch` as plain SPICE before and after (Xschem batch, output to scratch), then compare.
   - After renaming `XMSS[k]`→`XMSSk` and `wcs[k]`→`wcsk` in the "before" netlist, both netlists must contain exactly the same device lines.
   - The connections must be the 5-stack shown above.
2. **LVS netlists work:** run the Makefile's exact `klayout-lvs-netlist` and `magic-lvs-netlist` Xschem commands with the output dir set to scratch. Both must finish without the `fet_drc` error, and the CDL must contain `XMSS5`…`XMSS1`.
3. **Top level and testbench:** the top schematic `heichips26_FAIf.sch` and `tb_ptat_curr_gen.sch` still netlist without errors.
4. **Git:** `git diff` of `ptat_curr_gen.sch` shows only the changed lines of the original stack and the added block.

## Then (you): DRC/LVS as in the previous plan
```sh
cd macros/heichips26_FAIf/macros/ptat_current_source
make klayout-lvs
make magic-lvs
```
The LVS mismatch caused by the outdated layout (CSOUT4/PBIAS missing, CSSTARTUP extra) is still expected. In the layout, check whether the startup stack exists as 5 PMOS in series, each with its own N-well (bulk tied to its own source). The LVS report will show it.
