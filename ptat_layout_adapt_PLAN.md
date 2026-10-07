# Plan: adapt the PTAT layout to the current schematic (LVS clean)

## Context
`layout/ptat_curr_gen.gds` (DRC clean after the nBuLay and tap fixes) still implements the original circuit. LVS against the current schematic `ptat_curr_gen.sch` fails. Device-by-device comparison (Magic extraction vs. schematic netlist):

| Part | Layout | Schematic | Action |
|---|---|---|---|
| NMOS core + 16 dummies (10/2, 5/2, 2/2, 1/2 µm) | 18 | 18 | none, matches |
| PMOS mirror M3–M7, MS1, MS3 (0.4/1 µm) | 7, in a 3 × 9 PMOS array, middle row | 8 incl. **M8 → CSOUT4** | **layout:** add M8 as a **new** transistor in the array |
| PMOS dummies (0.4/1 µm, all terminals on PCSVDD) | 20 | 20 (MD17–36) | the array grows by one column so M8 keeps dummy neighbours: **+2 dummies** in layout and schematic (22) |
| Resistor R1 (`rhigh`, 30 µm × 21 bends) | 1 | 1 | none in the layout; schematic `lvs_format` fix (step 1) |
| Startup pull-down CSSTARTUP → PCSVSS | 480 × `nmosHV` 0.3/10 µm in series, gates on PCSVDD (x 42.6–152.8 µm, most of the cell) | MSS1–5: 5 diode-connected PMOS 0.3/0.4 µm, each body on its own source | **layout:** remove the chain, build the 5-PMOS stack |
| Startup gate: MS1 gate, MS3 source | on the PMOS gate line (PBIAS), which is correct | on an isolated net `net2`, so the startup can't reach the core | **schematic:** connect `net2` to PBIAS (exception, see step 1) |
| Pins | CSOUT1–3, **CSSTARTUP**, PCSVDD, PCSVSS | CSOUT1–4, **PBIAS**, PCSVDD, PCSVSS | **layout:** add CSOUT4 and PBIAS, remove the CSSTARTUP pin (the net stays) |

Every script below that edits the GDS or a schematic is shown to you before it runs; every step ends with a DRC/LVS check. Backups of the GDS and the schematic go to scratch first.

## Step 1 (schematic, small)
- **Startup gate:** connect `net2` (MS1 gate, MS3 source) to PBIAS. This is the one exception to "the layout follows the schematic": the layout is correct here, and the circuit needs it to start reliably.
- **Dummies:** add 4 PMOS dummies, all terminals on PCSVDD like MD17–36:
  - 2 × 0.4/1 µm for the new array column (step 2);
  - 2 × 0.3/0.4 µm at the ends of the startup stack (step 4).
- **R1:** delete the instance's own `lvs_format` override. It writes only 2 nodes; KLayout's LVS needs 3 ("Poly resistor should have 3 nodes"). The PDK symbol's default format adds the substrate node.
- Check: netlist exit code 0. Re-run `tb_ptat_curr_gen_startup.sch` (tt/ss/ff × −40/27/125 °C) to confirm startup still works with the corrected gate connection.

### ⏸ Break point
Show you the schematic diff and the testbench results (startup voltage and output currents per corner and temperature, compared with the previous run), then **wait for your go** before touching the layout.

## Step 2 (layout): M8 as a new transistor
- **Array:** grow the 3 × 9 PMOS array by one column to 3 × 10:
  - **Middle row:** the new transistor **M8** (`pmosHV` w = 0.4 µm, l = 1 µm, a copy of the existing device cell) goes directly next to the gate-line devices M3–M7/MS1, so it shares or extends their gate-line poly. The existing dummy at that end moves out by one pitch (1.2 µm), so M8 keeps a dummy neighbour.
  - **Top and bottom rows:** one new dummy each in the new column (the +2 dummies from step 1), wired like the other dummies (all terminals on PCSVDD).
  - **Side:** the left side is preferred (M8 next to the start of the gate-line strip), if the geometry analysis shows free space there; otherwise the right side.
- **N-well, guard ring, PCSVDD/dummy wiring:** extend them over the new column.
- **M8 connections:** source and body on PCSVDD, gate on the gate line, drain routed to a new **CSOUT4** pin (Metal2 label in the same style and row as CSOUT1–3).
- First a detailed geometry analysis of the array (poly, contacts, Metal1/Metal2, N-well, guard ring), then the edit script.

## Step 3 (layout): pins
- Add a **PBIAS** pin label on the gate-line net (Metal2 text + pin shape, same style as the CSOUT pins).
- Delete the **CSSTARTUP** pin label; the net stays.

## Step 4 (layout): replace the startup chain
- **Device cell:** build an `nmosHV`-style `pmosHV` cell with **w = 0.3 µm, l = 0.4 µm**.
  - Preferred: generate it with the PDK PCell library in batch KLayout. The earlier attempt didn't register `SG13_dev`; retry with `KLAYOUT_PATH=…/libs.tech/klayout/tech` so `pymacros/autorun.lym` runs.
  - Fallback: derive it from the existing `pmosHV` (0.4/1) cell geometry, adjusting the width and length.
- **Remove** the 480 `nmosHV` instances, plus their gate contact columns (`via_stack$13`, `$12`) and the chain wiring, but only what belongs to the chain. The NMOS core, dummies and guard rings stay.
- **Place MSS5 … MSS1** in series: CSSTARTUP → MSS5 → wcs4 → … → MSS1 → PCSVSS, each diode-connected (gate = drain). Each sits in **its own N-well** with an N-tap tied to its own source, because body = source. Spacing follows the HV N-well rules.
- **Dummies around the stack:** one dummy PMOS (w = 0.3 µm, l = 0.4 µm, like MSS) at each end of the 5-transistor row, i.e. 7 devices in a row: dummy, MSS5 … MSS1, dummy.
  - Each dummy has gate, source, drain and body tied together, sits in its own N-well and connects to PCSVDD, like the existing PMOS dummies.
  - The 2 dummies are added to the schematic as well (step 1). With the 2 from the array, that's 4 new PMOS dummies in total.
- **Location:** near the PMOS array (MS1/MS3), on the side facing the freed area. Route CSSTARTUP from MS1's drain and PCSVSS to the stack.
- The cell outline stays at 153.3 × 34.8 µm for now, so the macro floorplan doesn't change. Shrinking the cell (now possible, since the chain freed ≈ 110 µm of width) is a later, separate step.

## Verification (after each layout step, and at the end)
- Run, with reports to scratch first:
  - `make klayout-drc DRC_LEVEL=regular` (sign-off deck): no new errors beyond the 4 density checks the PTAT already has;
  - `make magic-drc`: only the known Sal.c/d at the resistor terminals;
  - `make klayout-lvs` and `make magic-lvs`: **match** at the end.
- Re-run the startup testbench (tt/ss/ff, −40/27/125 °C) with the final schematic.
- Then rebuild the analog macro (`make -C …/analogue_interface build-top`), run LibreLane and `make copy-final`, and run `make precheck`: KLayout DRC must stay at 0.
- Nothing is committed without your OK.
