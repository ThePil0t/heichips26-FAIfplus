# heichips26_FAIf: what is left before tapeout

> **[\*] = I can do this reliably myself and check the result with tools available here.** Through `nix-shell` I can run verilator, iverilog, cocotb, `ghdl synth`, yosys, LibreLane, xschem netlisting, KLayout DRC/LVS and `make precheck`.
> Unmarked points need a team or organizer decision, analog design judgement, hand-drawn layout, or verification I cannot do here.
> "[\*] after X" means I can do it once X has been decided or delivered.

## Context
This plan is based on a read-only audit of every branch on 2026-09-28. Six area agents read the repo and two reviewers re-checked their blocker findings. None of the blockers was refuted; a few details were corrected.

**Scope (decided):**
- **Architecture:** digital-on-top. LibreLane builds `heichips26_FAIf` and places one hand-drawn analog hard macro, `analogue_interface`, near `analog_0..2`.
- **ADC:** 8-bit SAR on `analog_0`.
- **DACs:** 2× 8-bit R-2R DACs on `analog_1` and `analog_2`.
- **S&H:** the trimmed sample-and-hold (`cap_en[3:0]`), with trim bits loaded through `load_config` (`uio_in[7]`).
- **No DDS.**

**Where things stand:**
- **`digital`** (checked out, tip 70de8ef): the RTL is small but working. `dac_reg` gives two 8-bit writes forming a 16-bit word; `sar` is 8 bits; the pinout matches the README. LibreLane now gets past GHDL and Yosys (148 cells, 41 flip-flops, +4.8 ns slack at 10 ns). It stops at floorplan with ORD-2013 because `analogue_interface` is an empty placeholder with no LEF. The Makefile fix from this session is not committed yet.
- **`benedikt`** (tip caafe19; `pascal` is fully merged into it): a complete mixed-signal top schematic, `schematic/xschem/heichips26_FAIf.sch`, with a `digital_logic` block.
  - Layouts exist for opamp, r2r_dac, comparator, PTAT and the three level translators.
  - Only r2r_dac has committed DRC reports (clean). There is no committed LVS result, no final view (GDS/LEF/vh/lib) and no PEX for any block.
  - Nothing has been committed since 2026-08-07.
- **`main`** (tip dd1486a): prelim `submission.yaml` with correct paths, but none of the RTL or analog work.
- **Precheck:** fails on every branch. There is no `final/` directory, and the local precheck rejects VAPWR.
- **Upstream template:** the fork is 18 commits behind. Upstream PR #18 adds a `uses-vapwr` key; there is also a new PDK pin.
- **Deadline:** not published. Issue #13 on HeiChips/heichips26-tapeout is open with the label `submission-pending`.

## Critical path
```
0 Ask organizers ──┐
1 Housekeeping ────┼─► 2 Interface spec ─┬─► 3 Digital RTL + verification ──────────┐
                   │                     └─► 4 Analog blocks ─► 5 Analog macro ──────┼─► 6 LibreLane integration ─► 7 Sign-off + submit
```
Workstreams 3 and 4 run in parallel. Workstream 5 (the analog macro layout) is the longest chain, so start it as early as possible.

---

## 0. Ask the organizers now (comment on issue #13)
[\*] I can draft the comment. Posting it is up to you.
- **VAPWR:** is it available in a small digital-on-top slot, and at what voltage? The whole analog chain uses HV devices and 1.2↔3.3 V level translators. If there is no 3.3 V supply, the blocks must be redesigned before any layout work.
- **VAPWR straps:** how must they be placed? The small_analog DEF defines only VPWR and VGND.
- **Power straps:** may Metal4 VPWR/VGND straps be interrupted by the macro halo? The README requires full-height straps.
- **Pad path:** what sits between `analog_0..2` and the bond pads (ESD cell, series R, capacitance, voltage limits)? This sets the DAC buffer load and the ADC source impedance.
- **Clock:** what clock and `ena` rate does the eFPGA provide? This sets the SAR bit period.
- **Other:** fill/NoMetFiller policy over analog blocks, the deadline, and PCB features (VAPWR supply, ADC signal source, DAC loads).

## 1. Housekeeping and branch consolidation
1. [\*] Commit the Makefile GHDL fix on `digital`: the `GEN_VERILOG` prerequisites and `ghdl synth file.vhdl -e entity`. Apply the same fix to `fpga/fpga.mk`.
2. [\*] Add `HeiChips/heichips26-template` as the `upstream` remote and merge it into `main`. This brings in `uses-vapwr` and the precheck update. The PDK pin stays as it is until point 3 is decided.
3. Fix one PDK commit for everyone. It must contain `cap_cmomi`, which the MOM caps in the S&H and DAC need. Check the new upstream pin `1ffc783`. [\*] I can check whether `1ffc783` has `cap_cmomi`; the choice itself is the team's.
4. Clean `benedikt` before merging:
   - [\*] delete the 52 `*:Zone.Identifier` files, the committed `simulations/` outputs, `*.orig.gds` and `magic_happy.gds`;
   - [\*] delete the per-macro copies of `scripts/sizing/data/*.mat` (96 copies, about 1 GB);
   - [\*] extend `.gitignore` to cover these;
   - [\*] delete the stale duplicates in `macros/heichips26_analog_project/macros/*` (after a diff; the FAIf copies are newer or identical) and the `switch/` orphan. Keep the floorplan GDS files for the analog macro;
   - delete the template `counter`/`inverter` macros and `heichips26_digital_project`. Some analog TBs still use inverter symbols, so this has to be checked together with you.
5. [\*] Merge in this order: `digital` → `main`, then the cleaned `benedikt` → `main`. `git merge-tree` shows no textual conflicts. Keep main's `submission.yaml` and the digital RTL, config and Makefile. After each merge I'll run lint and synth to check. Deleting the `pascal` branch on the remote needs your OK.

## 2. Freeze the digital↔analog interface, a one-page spec in the macro README
[\*] I can write the draft. The polarity rows must be confirmed by the analog team.
Every signal on the digital side is in the 1.2 V (VPWR) domain. The level translators live **inside** the analog macro.

| Macro pin | Dir | Width | Meaning |
|---|---|---|---|
| `sar_dac` | in | 8 | SAR trial code (`sar.ref_out`) |
| `sar_sh_en` | in | 1 | 1 = track, 0 = hold. **The RTL must drive `not hold`.** |
| `sar_comp` | out | 1 | 1 when V_in ≥ V_dac. **Fix the polarity:** swap INP/INN on x1 or invert in RTL. |
| `dac0_out` / `dac1_out` | in | 8 / 8 | `dac_out[7:0]` → analog_1, `dac_out[15:8]` → analog_2 |
| `sh_cap_en` | in | 4 | S&H trim, from the config register |
| `analog_0..2` | inout | 3 | ADC in, DAC0 out, DAC1 out |
| `VPWR`, `VAPWR`, `VGND` | power | – | under `USE_POWER_PINS` |

The two polarity bugs were found by reading transistor-level schematics. Confirm them in simulation, in workstreams 3 and 4.

## 3. Digital RTL and verification (`macros/heichips26_FAIf/`)
1. [\*] after 2. **`rtl/analogue_interface.sv`:** replace the empty placeholder with a blackbox or `.vh` stub carrying the pins above. Take it out of the LibreLane `VERILOG_FILES` glob; keep a behavioural model for simulation only. Declare `analog_*` as `inout`, and add power pins to the instance in `rtl/heichips26_FAIf.sv`.
2. **`rtl/sar.vhdl`:**
   - [\*] add a 2-FF synchronizer on `comp`;
   - [\*] make `hold` a registered flip-flop instead of a combinational decode, so no glitches reach the S&H switch;
   - [\*] latch the result at end of conversion and line up `tick` with valid data;
   - [\*] invert the S&H polarity (`sar_sh_en = not hold`), once confirmed;
   - [\*] build the bit-period prescaler and acquisition phase as a mechanism (generic or config value);
   - the actual prescaler value needs the analog settling times from workstream 4.
3. [\*] **Config register:** when `load_config` (`uio_in[7]`) is 1, latch `ui_in` into `cfg`, with `cfg[3:0]` = `sh_cap_en` and the rest reserved (for example the prescaler). Add it to `_unused` and update the README pinout.
4. **Testbenches:**
   - [\*] add `gcc` to `flake.nix`, so that `ghdl -e/-r` can run VHDL testbenches;
   - [\*] fix `testbenches/vhdl/sar_tb.vhdl` (port `ref` → `ref_out`) and add asserts;
   - [\*] add a closed-loop system TB (`sar` + `sample_hold` + `r2r_dac` + `ana_comp` models with delays) that sweeps a ramp or sine and checks ±1 LSB;
   - [\*] extend `testbenches/verilog/heichips26_FAIf_tb.sv` to cover the SAR, config and DAC byte order;
   - [\*] rewrite `testbenches/cocotb/heichips26_FAIf_tb.py`, which is still the template counter test, for RTL and gate level (GL);
   - [\*] add `sim-vhdl` and `$(GEN_VERILOG)` prerequisites to the sim targets.
5. Optional: update the FPGA prototype (`fpga/design/boolean`) to the full top. [\*] I can check that it synthesizes; I can't test it on the board.

## 4. Analog blocks (on `benedikt`, `macros/heichips26_FAIf/macros/*`)
For every block used in the top, finish schematic → testbench → layout → DRC + LVS + antenna → PEX, all on the chosen PDK. Existing DRC results predate the PDK bump and must be re-run.

Checks I can do for every block with existing layouts:
- [\*] run `make klayout-drc` / `magic-drc` / `klayout-lvs` and commit the reports. Fixing any violations found is design work and stays with you;
- [\*] replace absolute symbol paths with xschemrc library paths, checked by netlisting.

| Block | State | To do |
|---|---|---|
| sample_and_hold_trim + asw_inv + aswitch | schematic WIP; `cap_en` not wired, missing from the .sym; aswitch's GDS is the template inverter | finish the schematic, TBs (acquisition, droop, charge injection, trim steps) and all three layouts. [\*] I can add the `cap_en[3:0]` pin to the .sym and delete the copied inverter.gds. |
| ptat_current_source | symbol declares CSOUT3 twice (shorts iIREF3/4); layout has old pins | [\*] fix the symbol pin to CSOUT4 (checked by netlisting) and set Makefile TOP. The layout (CSOUT4, PBIAS) and the temperature/VDD/startup TBs are for you. |
| r2r_dac (×3) | DRC clean, no LVS; IDACIREF label missing; TopMetal1 text | [\*] remove the TopMetal1 text and run LVS. The IDACIREF label placement and the INL/DNL/settling sims are for you. |
| opamp | layout exists; "LVS clean" only in a commit message; caps `lvs_ignore` | [\*] re-run DRC/LVS and commit. The AC stability and CM-range TBs are for you. |
| comparator | layout exists, no DRC/LVS; cell name starts with a digit (`555_…`) | [\*] rename cell, symbol and GDS cell, then run DRC/LVS. The offset/delay TBs at the real PBIAS are for you. |
| level translators (×3 types) | layouts exist, unverified; the 8x has template leftovers and the wrong TOP | [\*] fix TOP, remove the template files, run DRC/LVS. The delay sims across VPWR 1.08–1.65 V and corners are for you. |

Also for every block:
- replace the template READMEs and `cace/inverter.yaml` copies;
- run ss/ff corners at −40/27/125 °C, plus Monte Carlo for DAC and opamp offset.

## 5. Assemble the analog hard macro `analogue_interface` (longest chain)
1. **Reference schematic:** create `macros/analogue_interface/schematic/xschem/analogue_interface.sch/.sym`. It is the analog half of `heichips26_FAIf.sch`: x1–x12, R1, R2, C1, the trimmed S&H, and the pins from workstream 2. It is the LVS reference. Keep the full top schematic, with `digital_logic`, only as a simulation TB.
2. **Mixed-signal sim:** replace the template top TB, which is broken, with a closed-loop test. Drive `digital_logic` through XSPICE (`macros/counter/scripts/spi2xspice.py`) or `d_cosim`, run a full ADC ramp and sine, and do a DAC sweep into a realistic pad load. Repeat with PEX.
3. **Floorplan and area budget:** the slot is 500 × 200 µm. Measured blocks: r2r 148×32 µm (×3), opamp 106×32, PTAT 153×35, comparator 22×20, plus the MOM caps. Put the analog pins at the south edge, near x = 450–460 µm (small_analog DEF). [\*] I can compute the area budget.
4. **Layout** (hand-drawn in KLayout): Metal1–Metal3 only, TopMetal1 empty, a Metal4 strap and keep-out plan agreed with the organizers, `prBoundary`, and pins named exactly as in workstream 2.
   - [\*] convert the block GDS files from 5 nm to 1 nm dbu;
   - [\*] prefix every sub-cell name with `heichips26_FAIf_`.
5. **Checks:** macro DRC, LVS, antenna and PEX; post-layout sims. [\*] I can run the checks; fixing violations is for you.
6. [\*] after 5.4. **Views:** export GDS, LEF (pins, OBS, antenna data, VPWR/VAPWR `USE POWER`, VGND `USE GROUND`), a blackbox `.vh` and a timing-free `.lib` into `final/`. Base the targets on the template's `heichips26_analog_project` Makefile.

## 6. LibreLane integration (`flow/librelane/config.yaml`, SDC)
- [\*] **DEF template:** `FP_DEF_TEMPLATE: dir::heichips26_template_small_analog.def`. This is the only template with `analog_0..2`; the current one has none.
- [\*] **Dry run with a dummy macro:** use an empty GDS/LEF with the final pin list, so the whole flow up to DRC/LVS/precheck can be tested now, before the analog layout is finished. This finds integration problems early.
- [\*] after 5. **Macro:** add `MACROS: analogue_interface {gds, lef, vh, lib, instances: {analogue_interface_instance: {location, orientation}}}`. Model it on `origin/main:macros/heichips26_digital_project/flow/librelane/config.yaml:54-76`.
- [\*] after 0. **Power:** `VDD_NETS [VPWR, VAPWR]`, `GND_NETS [VGND]`, plus `PDN_MACRO_CONNECTIONS` for both supplies. VAPWR gets full-height Metal4 straps, placed as the organizers specify.
- [\*] **Analog nets:** keep buffers off `analog_*`. Set `RSZ_DONT_TOUCH_RX` or the list, and use `inout` ports so the `DESIGN_REPAIR_BUFFER_*_PORTS` repair step leaves them alone.
- [\*] **SDC** (`impl.sdc`, `signoff.sdc`): false paths for the analog pins and the macro I/O; async `rst_n`; extra STA hold corners at 1.35/1.5/1.65 V. [\*] after 0: `CLOCK_PERIOD` matching the eFPGA clock.
- [\*] **Makefile:** replace `build-counter` with an analog-macro build and remove the counter/inverter references so `make all` works.

## 7. Sign-off and submission
1. [\*] Run `make build-top`, which covers LibreLane, `copy-reports`, `copy-final` and `copy-netlist`. The DRC (KLayout and Magic), LVS, antenna, STA and IR-drop reports (including VAPWR) must all be clean. Commit `final/{gds,lef,vh,lib,nl,pnl,spef}` and `verification/`. I fix violations on the digital side; violations inside the analog macro go back to workstream 5.
2. [\*] Run gate-level (GL) simulation on `final/nl` with the cocotb suite and the analog behavioural model.
3. [\*] Update `submission.yaml` (main's version):
   - `uses-vapwr` set according to the answer from 0;
   - a draft `long-description` that replaces the template text (it fails the precheck's hash check): 8-bit SAR ADC and 2× 8-bit DAC with trimmed S&H, the eFPGA driver sequence, and test and PCB needs. You review the draft.
4. [\*] Update the README feature list, which still says 16-bit DAC/ADC and DDS; fix the SPDX/licence headers. Writing macro READMEs needs the specs from you.
5. [\*] Run `make precheck` locally until it passes and push to `main`. You enable GitHub Actions on the fork (repo settings, it has never run) and post on issue #13.

## Verification (definition of done)
- `make sim-rtl-verilog`, `sim-vhdl`, `sim-rtl-cocotb` and `sim-gl-cocotb` all pass, and the closed-loop ADC test is within ±1 LSB.
- The XSPICE mixed-signal top sim converts a ramp and a sine correctly, with PEX netlists.
- Every analog block and the `analogue_interface` macro have committed DRC-clean, LVS-clean and antenna-clean reports on the chosen PDK.
- `make build-top` finishes with no DRC, LVS, antenna or timing violations.
- `make precheck` passes locally and CI is green on `main`.
