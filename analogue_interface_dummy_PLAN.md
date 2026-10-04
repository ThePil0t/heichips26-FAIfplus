# Plan: first `analogue_interface` hard macro (placement only) for the digital dry run

## Context
The digital-on-top LibreLane run of `heichips26_FAIf` stops at floorplan with `ORD-2013: LEF master analogue_interface not found`. The RTL instantiates an empty placeholder `analogue_interface`, and there is no hard macro yet. To dry-run the digital flow we need a first analog macro with:
- a realistic footprint;
- the analog blocks from `schematic/xschem/heichips26_FAIf.sch` placed sensibly;
- pins that match the RTL.

Rules from the request:
- **Nothing is routed.** Blocks are only placed. Pins are bare shapes on the macro edge.
- Existing GDS files are used as they are.
- Unfinished parts become sized dummies.

Decisions (answered):
- The S&H dummy is **sample_and_hold_trim**, so the macro gets 4 extra pins `sh_cap_en[3:0]`.
- Pin names **match the current RTL**.
- Scope is **macro only**. LibreLane integration and the dry run itself are a later step.

## Step 0: save the plan
Copy this plan unchanged to `/home/benedikt/heichips26-FAIf/analogue_interface_dummy_PLAN.md` and commit **only that file** on the current branch (`main`). Do not push.

## Location and files
Everything new goes in `macros/heichips26_FAIf/macros/analogue_interface/`, following the template `macros/heichips26_analog_project`:
- `Makefile`
  - `build-top` runs the build script, then `copy-gds` and `render-gds`; `clean` is also provided.
  - The `copy-gds`, `render-gds` and `klayout-drc` recipes are copied from `macros/heichips26_analog_project/Makefile`.
- `scripts/build_analogue_interface.py`: the single source of truth, a Python script using `klayout.db` (available in `nix-shell`).
- `scripts/lay2img.py`, `scripts/sak-drc.sh`: copied from the template, as every other FAIf block does.
- `layout/analogue_interface.gds`: generated.
- `final/gds|lef|vh|lib|render/`: generated. Here `vh` is the Verilog blackbox header, not VHDL.
- `README.md`: floorplan sketch, block table (source, status, estimate), pin table, planned location, known issues.

Nothing outside this directory changes. The top `VERILOG_FILES` glob (`rtl/*.sv`, `rtl/gen/*.v`) does not see the new files, so the current digital flow is not affected.

## Macro geometry
- Size **300 × 185 µm**, 1 nm dbu.
- Top cell `analogue_interface`, with `prBoundary` (189/4) at (0,0)–(300,185).
- **Planned die location (190, 5), orientation N.** The macro then covers die x 190–490 and y 5–190, inside the core (≈2.9–497.1 × 3.8–196.2). That leaves x < 180 (after the 10 µm macro halo) for the 148-cell digital logic and the west-edge IOs.
- Metal1–Metal3 only. No Via3/Metal4/TopMetal1, so top-level Metal4 PDN straps can cross the macro.

```
y=185 ┌─────────────────────────────────────────────────────────────────────┐
      │ VAPWR / VGND / VPWR pin straps (Metal3, x 2–298)                    │
  172 ├──────┬───────────────────────────────────┬──────────────────────────┤
      │ 4×LT │ PTAT x3 (153×35)                  │ (spare)                  │
      │ x9 LT│                                   │ x1 comp   R1/R2/C1 dummy │
  124 │ x2 ↓ │                                   │──────────────────────────│
      │LT8 x6│ R2R DAC x4 (SAR DAC)              │ S&H trim dummy x10       │
   86 │LT8 x7│ R2R DAC x5 (DAC0 → analog_1)      │ 110×58                   │
   48 │LT8x12│ R2R DAC x11 (DAC1 → analog_2)     │ opamp x8 (mirrored)      │
   10 │      │                                   │ analog_0 input above pins│
    0 └──────┴───────────────────────────────────┴───────────▲▲▲──────────┘
       west edge: digital pins (Metal3)          analog_0/1/2 (Metal2), x≈260–270
```

Signal-flow rationale:
- **Level translators (column A):** all of them sit at the west edge facing the digital logic, so the VPWR domain stays in one column.
- **DAC rows:** each 8× translator is rotated R90 next to its DAC row. Its LIN inputs face west and its nLOUT outputs face the DAC's nD inputs.
- **ADC front end (column C):** it sits next to the analog pins. The opamp is mirrored (MY) so its IOAP input is at x≈269, directly above analog_0..2.
- **Comparator:** INN/INP at y≈122, on the same height as the SAR DAC output (≈102).
- **Bias:** the PTAT row on top feeds the DACs and opamp below it.

## Placement table
Coordinates are macro-local in µm and give the lower-left of each block's transformed bbox. Gaps between blocks are ≥ 3 µm.

| Inst | Part | Source (`macros/heichips26_FAIf/macros/…`) | Orient | x, y | Size |
|---|---|---|---|---|---|
| x12, x7, x6 | 8x inverting level translator | `8x_inverting_digital_level_translator/layout/8x_inverting_digital_level_translator.gds` | R90 | (4, 9.35), (4, 47.35), (4, 85.35) | 13.145 × 33.61 |
| x11, x5, x4 | R2R DAC (includes its output opamp) | `r2r_dac/layout/r2r_dac.gds` | R0 | (25, 10), (25, 48), (25, 86) | 147.82 × 32.315 |
| x3 | PTAT | `ptat_current_source/layout/ptat_curr_gen.gds` | R0 | (25, 124) | 153.29 × 34.80 |
| x2 | down translator (adc_comp) | `down_digital_translator/layout/down_digital_translator.gds` | MY | (4, 124.5) | 3.24 × 4.90 |
| x9 | level translator (adc_hold) | `digital_level_translator/layout/digital_level_translator.gds` | R0 | (4, 132.4) | 12.12 × 5.05 |
| xcap0–3 | level translator (sh_cap_en[0..3]), **new** | same GDS as x9 | R0 | (4, 140.45 / 148.5 / 156.55 / 164.6) | 12.12 × 5.05 |
| x8 | opamp (S&H input buffer) | `opamp/layout/op_amp_ver_2.gds` | MY | (187, 10) | 105.66 × 32.29 |
| x10 | **DUMMY** sample_and_hold_trim (+ 5 aswitch/asw_inv) | – | – | (185, 48) | 110 × 58 (est.) |
| x1 | comparator | `comparator/layout/555_comparator.gds` | R0 | (187, 112) | 21.80 × 19.81 |
| R1, R2 | **DUMMY** rhigh w=0.5 l=50 | – | – | (220, 113), (220, 118) | 53 × 2 (est.) |
| C1 | **DUMMY** cap_cmomi w=50 l=2 | – | – | (220, 124) | 51 × 8 (est.) |

How the dummy sizes were estimated:
- **S&H trim:** the MOM caps are 3750 µm² drawn (C4 and C5 are 50×25 each, C3 25×25, C1 and C2 12.5×25 each). They go in two ≈27 µm rows, with the 5 HV switch cells and the inverter next to C1–C3, plus ≈25 % for feeds and spacing. That gives ≈6400 µm², drawn as 110 × 58.
- **R1, R2:** rhigh body 0.5 × 50 µm plus contact heads, laid horizontal.
- **C1:** cap_cmomi 2 × 50 µm of finger area plus feed pads, laid horizontal.

The PDK PCell library (`SG13_dev`) does not register in batch klayout, so real PCells are not used.

The xcap0–3 translators are not in the top schematic. They are needed because the trimmed S&H's `cap_en` runs at 3.3 V, while TAPEOUT_PLAN §2 puts every digital-side pin in the 1.2 V domain.

## Build script (`build_analogue_interface.py`)
1. Read each source GDS once (they use 5 nm dbu). Copy its cell tree into the 1 nm target layout with `Cell.copy_tree`, then assert that the copied bbox in µm equals the source bbox. If copy_tree does not rescale, use the fallback: `src.transform(ICplxTrans(5)); src.dbu = 0.001` before copying.
2. Rename every copied cell to `heichips26_FAIf_<blockkey>_<orig>`, mapping characters outside `[A-Za-z0-9_]` to `_`. Block top cells become `heichips26_FAIf_<orig>`, which also fixes the leading digit in `555_comparator`.
   - Blocks used several times are copied once and instantiated several times: r2r ×3, LT8 ×3, single LT ×5.
3. Delete all TopMetal1 (126/*) shapes. Only r2r_dac has any: the text `ODACOUT` on 126/25. Then assert that no shapes remain on Via3 (49), Metal4 (50), TopMetal1 (126) or TopMetal2 (134).
4. Dummies are cells `heichips26_FAIf_dummy_<name>`. Each holds a 189/4 outline box and a TEXT (63/0) label such as `DUMMY sample_and_hold_trim 110x58um (estimate)`. No mask layers.
5. Place each instance so its transformed bbox lower-left lands on (x, y) from the table. Assert that everything lies inside (0,0)–(300,185), with ≥ 3 µm pairwise spacing and no overlap.
6. Pins. Each pin is drawn on its layer three times, on the drawing, pin and text datatypes (e.g. 30/0 + 30/2 + 30/25), as in the template floorplan GDS.
   - **West edge, Metal3**, rect x 0–1.0, height 0.4. Each pin's y comes from the matching block label, transformed:

| Pins | Matching block label |
|---|---|
| `dac_out[15:8]` | LIN0–7 of x12 |
| `dac_out[7:0]` | LIN0–7 of x7 |
| `adc_ref[7:0]` | LIN0–7 of x6 |
| `adc_hold` | LIN of x9 |
| `sh_cap_en[3:0]` | LIN of xcap0–3 |
| `adc_comp` | DOUT of x2 |

   - **South edge, Metal2**, 1.0 µm wide, y 0–2:
     - `analog_0` at x 259.74–260.74, `analog_1` at x 264.54–265.54, `analog_2` at x 269.34–270.34;
     - that is die x 450.24 / 455.04 / 459.84 minus 190, from `heichips26_template_small_analog`.
   - **Power, Metal3 straps** at x 2–298, 2 µm wide: `VPWR` y 173–175, `VGND` y 177–179, `VAPWR` y 181–183.
7. Write `layout/analogue_interface.gds` without PCell context info.
8. Write `final/lef/analogue_interface.lef` directly from the same pin table. Magic's `lef write` would drop `USE POWER/GROUND`, as the template LEF shows.
   - `CLASS BLOCK`, `SIZE 300 BY 185`.
   - `DIRECTION INPUT` for adc_ref, adc_hold, dac_out and sh_cap_en; `OUTPUT` for adc_comp; `INOUT` for analog_* (USE SIGNAL).
   - VPWR and VAPWR are `USE POWER`; VGND is `USE GROUND`.
   - OBS on Metal1, Metal2 and Metal3 covers the full macro, minus the pin shapes bloated by 0.5 µm. The script computes this with a KLayout `Region` boolean and writes it as RECTs.
   - No OBS on Metal4.
9. Write `final/vh/analogue_interface.vh`. `.vh` is a **Verilog header** (plain Verilog, not VHDL), the blackbox view LibreLane's `MACROS` entry expects, like the template's `counter.vh`. It contains:
   - a blackbox module with real directions (`input [7:0] adc_ref`, `input adc_hold`, `output adc_comp`, `input [15:0] dac_out`, `input [3:0] sh_cap_en`, `inout analog_0..2`);
   - `VPWR`, `VAPWR` and `VGND` under `` `ifdef USE_POWER_PINS ``.
10. Write `final/lib/analogue_interface.lib`, a timing-free Liberty:
    - `voltage_map`: VPWR 1.2, VAPWR 3.3, VGND 0;
    - `pg_pin`s and bus types bus4/bus8/bus16;
    - pin directions and a small input capacitance;
    - `area` 55500, `is_macro_cell`, `dont_touch`;
    - no arcs.

## Verification
All checks run in `nix-shell` from the repo root:
1. `make -C macros/heichips26_FAIf/macros/analogue_interface build-top` runs clean, and every assert in the script passes.
2. Re-measure `final/gds/analogue_interface.gds`:
   - one top cell, bbox 300 × 185;
   - every pin label is present at the expected position;
   - the layer list contains nothing above Metal3;
   - all cell names start with `heichips26_FAIf_` (except the top cell).
3. Open the `final/render` PNG and check the floorplan by eye against the sketch.
4. Load the views together in OpenROAD/OpenSTA (a small Tcl script): the PDK tech LEF + the macro LEF, `read_liberty` on the lib, and `read_verilog` on the vh plus a 3-line wrapper that instantiates it. There must be no errors. Lint the vh with `verilator --lint-only`.
5. As information only: `make klayout-drc DRC_LEVEL=macro` on the macro. Report the violation counts. Violations inside the unverified blocks or density violations are expected; nothing is fixed.

## Known issues to record in the README (not fixed here)
- **PTAT:** the GDS predates `ptat_curr_gen_mod1`. It has CSSTARTUP, but no CSOUT4 and no PBIAS. The symbol also declares CSOUT3 twice.
- **No LVS or DRC results:** none of the blocks has LVS; only r2r_dac has DRC. In r2r_dac the `IDACIREF` label is missing.
- **Translators:** xcap0–3 and the trimmed S&H are not in the top schematic yet, which still uses `sample_and_hold.sym`.
- **sh_cap_en is undriven in the RTL:** `heichips26_FAIf.sv` does not connect `sh_cap_en` yet. Until the config register exists, the dry run will see 4 unconnected macro inputs.
- **Location-dependent analog pins:** analog_0..2 line up with the die pins only at location (190, 5).
- **Metal4 open:** Metal4 is not obstructed, so top-level signal routes may cross the analog blocks. The keep-out plan is still open (TAPEOUT_PLAN §5.4).

## Next step (out of scope)
LibreLane integration for the dry run:
- `FP_DEF_TEMPLATE: heichips26_template_small_analog.def`;
- a `MACROS: analogue_interface` entry with the final views, instance at [190, 5] N;
- VDD/GND nets and `PDN_MACRO_CONNECTIONS` including VAPWR;
- the placeholder `rtl/analogue_interface.sv` taken out of synthesis;
- `sh_cap_en` wired in the RTL.

The macro work is left uncommitted for your review unless you ask for a commit.
