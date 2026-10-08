# Plan: analog macro, DAC path (iVREF divider + routing + LVS reference)

## Context
Every analog cell is now clean in KLayout DRC and LVS (PTAT, opamp, R2R, translators, comparator, `sah_12bit`). The macro `analogue_interface` still only **places** the blocks:
- `scripts/build_analogue_interface.py` has no routing and no routing hook;
- R1, R2 and C1 are still dummy boxes;
- there is no LVS reference (no `schematic/`, no `lvs` target).

This round covers todo-plan items **D4** (iVREF divider) and **D5** (DAC part of the macro): the DAC path from the `dac_out` pins to `analog_1`/`analog_2`, with the bias and supplies those blocks need. The ADC path (x6/x4, opamp x8, S&H x10, comparator x1, x2/x9, spares) follows in a later round.

Your choices:
- DAC path only;
- I generate the reference schematic;
- routing is scripted in the builder;
- break point after the route design.

## Nets in this round (from `heichips26_FAIf.sch`, resolved by label instances, not wire `lab=`)
| Net | From → to | Pin geometry (macro coordinates) |
|---|---|---|
| `dac_out[k]`, k = 0..7 | west pin → x7 `LINk` | west pin: Metal3, x 0–1, y already aligned to the LIN label. LIN: Metal2 at x ≈ 4.16, y = 47.35 + LIN_x |
| `dac_out[8+k]` | west pin → x12 `LINk` | same, with y = 9.35 + LIN_x |
| 16 bit nets | x7 `nLOUTk` → x5 `nDk`; x12 → x11 | nLOUT: Metal2 at x ≈ 14.1. nD: Metal3 pads **inside** the R2R at x = 32.86 + 3.96·k, y = R2R_y + 16.5 |
| iIREF3, iIREF4 | PTAT `CSOUT3`/`CSOUT4` → x5/x11 `IDACIREF` | CSOUT: Metal2 pads inside the PTAT at (38.09 / 32.09, 152.38). IDACIREF: Metal3 inside the R2R at (79.03, R2R_y + 15.79) |
| iVREF | R1/R2/C1 node → x5/x11 `IDACVTAP` | IDACVTAP is the opamp IOAP pin inside the R2R at (90.51, R2R_y + 13.78). x4 joins in the ADC round |
| `analog_1`, `analog_2` | x5/x11 `ODACOUT` → south pins | ODACOUT: the opamp OOA bar, Metal3, reaching the R2R east edge at x 172.8, y = R2R_y + 15.7…16.9. South pins: Metal2 at x 264.54 / 269.34, y 0–2 |
| IDACDISABLE (x5, x11) | → VGND | inside the R2R at (73.93, R2R_y + 15.56) |
| VPWR, VAPWR, VGND | straps (Metal3, y 173–183) → x7/x12 supply bars, x5/x11 PDACVDD/PDACVSS rails, PTAT PCSVDD/PCSVSS, divider | translators (R90): vertical Metal3 bars at x ≈ 5.9 (VPWR), 9.85 (VGND), 12.25 (VAPWR). R2R: Metal3 rails at the top/bottom edge of the opamp area |

Watch out: several pins (nD, IDACIREF, IDACVTAP, IDACDISABLE) sit **inside** the R2R cell, and CSOUT3/4 sit inside the PTAT. Whether free tracks exist over them decides the routes (step 3).

## Step 0
Copy this plan to `macro_dac_routing_PLAN.md` at the repo root and commit only that file.

## Step 1: LVS reference schematic (generated)
- **Script:** new `analogue_interface/scripts/gen_reference_schematic.py`. It writes `analogue_interface/schematic/xschem/analogue_interface.sch` and `.sym`, plus an `xschemrc` with the library paths (as in the top `xschemrc`).
  - **Content:** the analog part of `heichips26_FAIf.sch`: x1–x12, R1, R2, C1 with their parameters. Not copied: x13 (digital logic) and the `conn_*` connectors.
  - **Added:** the 4 spare translators xcap0–3 (`digital_level_translator`), with LIN = `sh_cap_en[k]` and LOUT left unconnected (net `cap_out[k]`).
  - **Ports renamed to the macro ports:**

    | Top-level net | Macro port |
    |---|---|
    | `DAC0_OUT[k]` | `dac_out[k]` |
    | `DAC1_OUT[k]` | `dac_out[8+k]` |
    | `SAR_DAC[k]` | `adc_ref[k]` |
    | `SAR_SnH` | `adc_hold` |
    | `SAR_COMP` | `adc_comp` |

    `analog_0..2`, `VPWR`, `VAPWR` and `VGND` keep their names. Pin order is the LEF/`.vh` order.
  - **Stale labels:** the script resolves nets from the label instances. Two wire `lab=` values in the top schematic are stale: CSOUT4 is labelled iIREF3, and x13's right side is labelled SAR_DAC. The script must not trust wire labels.
- **Makefile** (macro): add `klayout-lvs-netlist` and `klayout-lvs` (KLayout is sign-off), modelled on the cell Makefiles. Copy `sak-lvs.sh` into the macro's `scripts/`.
- **Checks:**
  - the Xschem netlist exits with code 0;
  - a small compare script confirms the generated netlist has the same instance → net mapping as the top netlist's analog part, after the port renames.
- You can review the generated schematic in xschem afterwards. It's not a break point.

## Step 2: real iVREF divider (D4)
- **Builder:** replace the R1/R2/C1 dummies with PDK PCells.
  - **R1, R2:** `rhigh`, w 0.5, l 50 µm, b 0.
  - **C1:** `cap_cmomi`, w 50, l 2 µm, values as in the schematic.
  - Generate them with `sg13cmos5l_pycell_lib` (same mechanism as the PTAT stack cells) and convert them to static cells with the macro prefix.
- **Placement:** choose it in step 3, near the IDACVTAP pins of x5/x11 if a free area allows, otherwise keep (220, 113–132).
- **C1 rule** (from the S&H plan): KLayout recognizes the cap from its marker plus **exactly 2 `.pin` shapes**. No other `.pin` may lie inside the marker.

## Step 3: route design (analysis, no build yet)
- **Occupancy maps:** for each placed block (R2R, 8x translator, PTAT, divider) and for the channels, map Metal1–Metal3 and Via1/Via2, with metal spacing bloated (M1 0.18, M2/M3 0.21), and find free tracks:
  - **West channel** x 17.1–25 (between translators and R2Rs), y 9–124;
  - **Gaps between rows** y 42.3–48 and 80.3–86;
  - **East channel** x 172.8–185.5 (R2R east edge to opamp/S&H);
  - **South channel** y 2–10 under x11 and x8;
  - **Over the R2R's left part:** nD, IDACIREF, IDACVTAP, IDACDISABLE;
  - **Over the PTAT:** CSOUT3/4.
- **Route concept:**
  - **dac_out:** short Metal3 stubs from each west pin plus Via2 onto LINk.
  - **16 bit nets:** Metal2/Metal3 through the west channel into the nD pads, assigned so tracks don't cross on the same layer.
  - **iIREF3/4:** out of the PTAT on Metal3, down the west channel, then in to IDACIREF.
  - **iVREF:** from the divider to both IDACVTAP pins.
  - **IDACDISABLE:** to the nearest VGND.
  - **analog_1/2:** from ODACOUT at the R2R east edge, down the east channel, along the south channel on Metal3 (≥ 1 µm wide), with Via2 onto the Metal2 south pins. analog_0 stays free for its later vertical hop to x8.
  - **Supplies:** vertical trunks from the strap band down to the blocks. A trunk changes to Metal2 where it crosses a strap of another net. Horizontal rails run in the row gaps for the R2R top and bottom rails and for the PTAT.
- **If an internal pin can't be reached** on a free track, the fallback is to bring that pin to the cell edge inside `r2r_dac.gds` or `ptat_curr_gen.gds`, then rerun that cell's DRC and LVS.
- **Output:** a route table (net, layer, polyline, width, vias) and a macro render with the routes overlaid.

### ⏸ Break point
Show you the route picture and table. Wait for your go before changing the builder.

## Step 4: implement in the builder
- **Routing module:** in `build_analogue_interface.py`, add a data-driven `ROUTES` table plus helpers `wire(layer, points, width)` and `via(x, y, lower, upper)`.
  - Via sizes and enclosures follow the PDK rules (Via1/Via2 0.19 µm), the same as the existing `via_stack` cells.
  - Routes go into their own subcell `heichips26_FAIf_routing`.
- **Existing asserts** stay: Metal1–Metal3 only (Metal4 only for the x10 lid), prefix, bbox and pins.
- **New asserts:**
  - every route ends on its target pin shape;
  - no route over x10 (S&H obstruction).
- **README:** a routing section, and the PTAT size corrected (48.58 × 34.8 µm). The macro LEF/`.vh`/`.lib` stay as they are; the LEF already obstructs Metal1–Metal3 over the whole macro.

## Verification
- **`make layout`:** the builder asserts pass.
- **`make klayout-drc DRC_LEVEL=macro`** and the regular sign-off deck: no new errors, only the known global density rules.
- **Connectivity check:** extract the macro netlist with KLayout (`run_lvs.py --net_only`). A script then checks that each DAC-round net connects exactly its intended pins and that no two nets are shorted. The full macro LVS can't pass yet because the ADC nets are unrouted.
- **Macro LVS** against `analogue_interface.sch`: run it and record the remaining mismatches, which must be **only** the ADC-round nets. That becomes the pass gate for the next round.
- **Rebuild:** you run `make build-top` / LibreLane / `copy-final` / precheck later. Nothing is committed without your OK, except the plan file in step 0.
- **Next:** D6, the DAC sims into the pad load, also with Magic PEX of the routed DAC part.
