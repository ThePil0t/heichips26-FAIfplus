# Plan: make the PTAT's DRC and LVS runnable from its Makefile

## Context
You want to run DRC and LVS on the PTAT (`macros/heichips26_FAIf/macros/ptat_current_source/`) with its Makefile. Three things stand in the way:
- **Wrong `TOP`:** the Makefile still has `TOP = inverter`, so every target needs `CELL=…`.
- **Name mismatch:** the layout cell and file are `ptat_curr_gen`, but the schematic is `ptat_curr_gen_mod1.sch`. The LVS targets use one name for the schematic file, the layout file and the top cell (netgen gets a single `TOPCELL`), so the two can't be compared.
- **Outdated layout:** the layout still implements the old circuit. It has CSOUT1–3 and CSSTARTUP; the schematic has CSOUT1–4 and PBIAS. LVS will report mismatches until the layout is updated; that is expected.

Decision: **rename the schematic to `ptat_curr_gen`**, the layout's name. Layout, macro build script and macro stay unchanged. The symbol needs a fix anyway: its second `CSOUT3` pin (line 51, x = 207.5, already labelled `CSOUT4` on the symbol) shorts iIREF3 and iIREF4 in the top schematic.

Current layout state: `layout/ptat_curr_gen.gds` has your nBuLay fix and the ThickGateOx tap fix (not committed). `layout/ptat_curr_gen_old.gds.old` is your untracked copy of the pre-tap-fix version; don't commit it.

## Step 0 (me): save the plan
Copy this plan to `/home/benedikt/heichips26-FAIf/ptat_drc_lvs_PLAN.md` and commit only that file. Do not push.

## Step 1 (me): rename the schematic and symbol, fix the pin
In `macros/heichips26_FAIf/macros/ptat_current_source/schematic/xschem/`:
```sh
git mv ptat_curr_gen_mod1.sch ptat_curr_gen.sch
git mv ptat_curr_gen_mod1.sym ptat_curr_gen.sym
```
In `ptat_curr_gen.sym`, line 51:
```
B 5 207.5 17.5 212.5 22.5 {name=CSOUT4 dir=out}
```
Before: `{name=CSOUT3 dir=out}`.

Update the two references `ptat_curr_gen_mod1.sym` → `ptat_curr_gen.sym`:
- `macros/heichips26_FAIf/schematic/xschem/heichips26_FAIf.sch`, line 304 (instance x3);
- `macros/heichips26_FAIf/macros/ptat_current_source/testbenches/xschem/tb_ptat_curr_gen.sch`, line 175 (instance x1).

The stale copies in `macros/heichips26_analog_project/` stay untouched; they are deleted in the cleanup (TAPEOUT_TODO_PLAN G3).

## Step 2 (me): PTAT Makefile
`macros/heichips26_FAIf/macros/ptat_current_source/Makefile`, line 7:
```make
TOP = ptat_curr_gen
```
No other Makefile change is needed:
- the LVS targets netlist `schematic/xschem/$(CELL).sch` with the PTAT's `xschemrc`;
- they compare it with `layout/$(CELL).gds`, using top cell `$(CELL)` on both sides.

## Step 3 (you): run DRC and LVS
```sh
cd /home/benedikt/heichips26-FAIf
nix-shell
export PDK_ROOT=$(pwd)/IHP-Open-PDK PDK=ihp-sg13cmos5l
cd macros/heichips26_FAIf/macros/ptat_current_source

make klayout-drc                     # DRC_LEVEL=macro by default
make klayout-drc DRC_LEVEL=regular   # full rule set
make magic-drc
make klayout-lvs
make magic-lvs
```
Reports go to `verification/drc/` and `verification/lvs/` (open the `.lyrdb` files in KLayout's Marker Browser). Netlists go to `netlist/schematic/` and `netlist/layout/`.

Expected results:
- **KLayout DRC:** clean at `macro` level; at `regular` level only the 4 density checks M2.j, M3.j, M4.j and TM1.c.
- **Magic DRC:** 4 × Sal.c/d at the resistor terminals (PDK resistor geometry).
- **LVS:** mismatch. The layout lacks CSOUT4 and PBIAS and has CSSTARTUP. The netgen report (`*.magic.lvs`) lists the unmatched devices and nets, which is the to-do list for the layout update.

## Verification of my steps
- Netlist the top schematic and the PTAT testbench with xschem (batch). There must be no "symbol not found", and in the top netlist x3's fourth current output must connect to `iIREF4` (no longer shorted to `iIREF3`).
- In the PTAT directory, `make -n klayout-lvs` and `make -n magic-lvs` show `schematic/xschem/ptat_curr_gen.sch`, `layout/ptat_curr_gen.gds` and `-c ptat_curr_gen`.
- `git status` shows only: the two renames, the symbol pin, the two reference lines and the Makefile line. The layout changes from before stay as they are.
