# heichips26_FAIf: open tasks to tapeout (as of 2026-10-04)

> **[\*]** = Claude can do this reliably and check the result with the tools in `nix-shell`: verilator, iverilog, cocotb, GHDL, yosys, LibreLane, xschem netlisting, KLayout/Magic DRC and LVS, `make precheck`.
> Unmarked tasks need a team or organizer decision, analog design judgement, hand-drawn layout, or verification that can't be done here.
> "[\*] after X" means Claude can do it once X has been decided or delivered.

This plan lists only what is still to do. It replaces the done/open bookkeeping in [TAPEOUT_PLAN.md](TAPEOUT_PLAN.md), which stays as background and history.

## Where we are
- **Repo:** `main` contains the digital RTL and all analog work (`digital` and `benedikt` merged on 2026-10-04).
- **Dry-run macro:** a placement-only `analogue_interface` hard macro exists in `macros/heichips26_FAIf/macros/analogue_interface/` (300 × 185 µm, nothing routed).
  - `scripts/build_analogue_interface.py` places the existing block layouts and writes GDS, LEF, Verilog blackbox `.vh` and `.lib`.
  - Dummies stand in for the trimmed S&H, R1, R2 and C1.
- **Full LibreLane flow** of `heichips26_FAIf` with this macro runs through (`RUN_2026-10-04_20-23-46`):
  - 0 routing DRC errors, LVS clean;
  - 0 power-grid, antenna and XOR errors;
  - setup slack +4.2 ns, hold slack +0.30 ns.
- **Only DRC is left, and all of it is inside the analog blocks:**
  - KLayout: 8 errors;
  - Magic: 1346, which Magic counts 3–4 times, so ≈340–450 unique.
- **Not committed yet:** the macro, the integration edits in `config.yaml`, `heichips26_FAIf.sv` and `analogue_interface.sv`, and the update of `TAPEOUT_PLAN.md`.

## Critical path
```
A Save state ─► B Decisions ─┬─► D Analog blocks ─► E Analog macro layout ──┐
                             ├─► C Digital RTL + verification ──────────────┼─► H Sign-off + submit
                             └─► F Integration (SDC, VAPWR, Makefile) ──────┘
G Housekeeping: any time before H
```
E is the longest chain: every block in D must be DRC/LVS clean before the macro can be signed off. Start the block fixes in D now; they do not wait for B, except for the S&H.

---

## A. Save the current state (first)
1. [\*] Commit the dry-run state on `main`:
   - `macros/heichips26_FAIf/macros/analogue_interface/`;
   - the edits to `flow/librelane/config.yaml`, `rtl/heichips26_FAIf.sv` and `rtl/analogue_interface.sv`;
   - the update of `TAPEOUT_PLAN.md` and this file.
2. [\*] In `build_analogue_interface.py`, set `DIE_LOCATION = (190.0, 8.82)`; it still says (190, 5). Rebuild the macro, rerun `make librelane-nodrc`, and commit.
3. [\*] Add the power pins (`VPWR`, `VAPWR`, `VGND` under `USE_POWER_PINS`) to the simulation stand-in `rtl/analogue_interface.sv`, so it matches the macro's `.vh`.

## B. Decisions (they block parts of C–F)
1. **S&H variant:** the trimmed `sample_and_hold_trim` (`cap_en[3:0]`, 0.23–2.9 pF) or `sah_12bit` (fixed 1.21 pF, no trim; recommended by `sah_12bit_sizing_PLAN.md`). This decides:
   - the S&H layout and its footprint (the macro reserves 110 × 58 µm for the trimmed version);
   - whether the macro needs 4 extra level translators and the `sh_cap_en[3:0]` pins;
   - whether the RTL needs the config register (C2).
2. **Macro pin names:** keep the current RTL names (`adc_ref`, `adc_hold`, `adc_comp`, `dac_out[15:0]`, `sh_cap_en`), or rename them to the spec in TAPEOUT_PLAN §2 (`sar_dac`, `sar_sh_en`, `sar_comp`, `dac0_out`, `dac1_out`).
   - [\*] after the decision: write the one-page interface spec (pin, direction, width, meaning, polarity, voltage domain) into the macro README.
   - A rename changes the generator, the `.vh` and the RTL instance together.
3. **Organizer questions** (comment on issue #13; [\*] Claude drafts it, posting is up to you):
   - **VAPWR:** is it available in a small digital-on-top slot, and at 3.3 V? Is the precheck going to accept it (`uses-vapwr`, upstream PR #18)?
   - **VAPWR straps:** LibreLane currently creates VAPWR Metal4 straps only over the macro (x ≈ 218–468 µm). Is that enough, or must VAPWR straps span the whole slot?
   - **Metal4 over analog blocks:** may the top level route signals on Metal4 over the macro, or do we need a keep-out?
   - **Pad path:** what sits between `analog_0..2` and the bond pads (ESD, series R, capacitance, voltage limits)?
   - **Clock:** what clock and `ena` rate does the eFPGA provide?
   - **Other:** fill/NoMetFiller policy over analog blocks, the deadline, and PCB features (VAPWR supply, ADC source, DAC loads).
4. **PDK pin:** fix one PDK commit for everyone that contains `cap_cmomi`. [\*] Claude can check whether upstream pin `1ffc783` has it; the choice is the team's.

## C. Digital RTL and verification (`macros/heichips26_FAIf/`)
1. **`rtl/sar.vhdl`:**
   - [\*] add a 2-FF synchronizer on `comp`;
   - [\*] make `hold` a registered flip-flop; today it is a combinational decode of `mask_reg`;
   - [\*] latch the result at end of conversion and line up `tick` with valid data;
   - [\*] build the bit-period prescaler and acquisition phase as a mechanism (generic or config value);
   - [\*] after C3: fix the S&H polarity (`sar_sh_en = not hold`);
   - set the prescaler value; it needs the analog settling times from D.
2. [\*] after B1. **Config register:** when `load_config` (`uio_in[7]`) is 1, latch `ui_in` into `cfg`.
   - `cfg[3:0]` replaces the `4'b0000` tie-off on `sh_cap_en`. If B1 picks `sah_12bit`, remove `sh_cap_en` instead.
   - Update `_unused` and the README pinout.
3. **Polarity bugs:** confirm both in simulation: the S&H enable must be `not hold`, and the comparator output must be 1 when V_in ≥ V_dac. Fix the comparator by swapping INP/INN on x1 or inverting in the RTL.
4. **Testbenches:**
   - [\*] add `gcc` to `flake.nix` so `ghdl -e/-r` can run the VHDL testbenches;
   - [\*] fix `testbenches/vhdl/sar_tb.vhdl` (port `ref` → `ref_out`) and add asserts;
   - [\*] add a closed-loop system TB: `sar` + `sample_hold` + `r2r_dac` + `ana_comp` models with delays, sweeping a ramp or sine and checking ±1 LSB;
   - [\*] extend `testbenches/verilog/heichips26_FAIf_tb.sv` to cover the SAR, the config register and the DAC byte order;
   - [\*] rewrite `testbenches/cocotb/heichips26_FAIf_tb.py`, which is still the template counter test, for RTL and gate level;
   - [\*] add `sim-vhdl` and the `$(GEN_VERILOG)` prerequisites to the sim targets in the Makefile.
5. Optional: update the FPGA prototype (`fpga/design/boolean`) to the full top. [\*] Claude can check that it synthesizes, not test it on the board.

## D. Analog blocks (`macros/heichips26_FAIf/macros/*`)
For every block: schematic → testbenches → layout → DRC + LVS + antenna → PEX, on the PDK from B4.

[\*] For every block with a layout, Claude can:
- run `make klayout-drc`, `make magic-drc` and `make klayout-lvs` per block and commit the reports. This also shows which of the Magic errors from the dry run are real;
- replace absolute symbol paths with xschemrc library paths, checked by netlisting.

Fixing violations, layout and analog sims are for you.

| Block | Open tasks | DRC in the dry run |
|---|---|---|
| **S&H** (after B1): `sample_and_hold_trim` + `asw_inv` + `aswitch`, or `sah_12bit` | finish the testbenches (acquisition, droop, charge injection, trim steps if trimmed); draw all layouts (S&H, switches, MOM caps). [\*] Delete the template `inverter.gds` copied into `aswitch/layout/`. | dummy only |
| **Top schematic** `heichips26_FAIf.sch` | swap x10 (still `sample_and_hold.sym`) for the chosen S&H. If trimmed: add 4 × `digital_level_translator` for `cap_en[3:0]`, which runs at 3.3 V. | – |
| **PTAT** `ptat_current_source` | **remove the nBuLay ring (layer 32/0): it is forbidden in CMOS5L and blocks DRC sign-off.** Add CSOUT4 and PBIAS to the layout. [\*] Fix the symbol (CSOUT3 is declared twice, which shorts iIREF3/4) and the Makefile `TOP`. TBs: temperature, VDD, startup. | KLayout: 4 × nBuLay. Magic: 97 (Cnt.c 89, Cnt.a 4, Sal.c/d 4) |
| **Level translators**: 8x inverting (×3), single (×5), down (×1) | fix the tap placement: latch-up rules LU.a (P-diff to N-tap ≤ 20 µm) and LU.d, plus NW.d, pSD.e/f. Fix 4 × `Act.b` in the down translator. [\*] Fix `TOP` and remove the template files in the 8x macro. Delay sims across VPWR 1.08–1.65 V and corners. | Magic: 328 per 8x, 200 for the single ones, 15 in the down translator. KLayout: 4 × Act.b |
| **R2R DAC** (×3) | run LVS. Add the missing `IDACIREF` label. Check NW.d/LU.a. [\*] Remove the TopMetal1 text `ODACOUT` from the source GDS; the generator strips it already. INL/DNL/settling sims. | Magic: 11 each |
| **Opamp** `op_amp_ver_2` | [\*] re-run DRC/LVS and commit the reports; the caps are `lvs_ignore`. AC stability and CM-range TBs. | clean |
| **Comparator** `555_comparator` | [\*] rename cell, symbol and GDS cell; the name starts with a digit. Then DRC/LVS. Check LU.d/NW.d. Offset/delay TBs at the real PBIAS. | Magic: 17 |
| **iVREF divider**: R1, R2 (rhigh 0.5/50 µm) and C1 (cap_cmomi 50/2 µm) | draw them in the macro. The PDK PCell library does not load in batch KLayout, so place the PCells in the GUI. | dummy only |

Also for every block:
- replace the template READMEs and `cace/inverter.yaml` copies;
- run ss/ff corners at −40/27/125 °C, plus Monte Carlo for DAC and opamp offset.

## E. Analog macro `analogue_interface` (longest chain)
1. **Reference schematic:** create `macros/analogue_interface/schematic/xschem/analogue_interface.sch/.sym`. It is the analog half of `heichips26_FAIf.sch`:
   - x1–x12, R1, R2, C1 and the S&H from B1 (plus xcap0–3 if trimmed);
   - the pins from B2.

   It is the LVS reference for the macro.
2. **Layout:** start from the dry-run floorplan in `layout/analogue_interface.gds`, replace the dummies with the real layouts, then route. Keep these constraints:
   - **Location:** the macro sits at (190, 8.82) in `heichips26_FAIf`. `analog_0..2` stay on the south edge at macro x 260.24 / 265.04 / 269.84; the west-edge pins stay on the Metal3 track grid (die y = 0.42 · k).
   - **Height:** at most ≈187 µm. With `PDN_MULTILAYER: false`, the bottom cell row (y 3.78–7.56) is the only link between the Metal4 straps over the macro and the core grid.
   - **Layers:** Metal1–Metal3 only, TopMetal1 empty; Metal4 keep-out per B3.
   - **Power pins:** Metal3 strips for VPWR, VAPWR and VGND, declared `USE POWER`/`USE GROUND` in the LEF.
3. **Checks:** macro DRC (KLayout + Magic), LVS against E1, antenna, PEX; post-layout sims. [\*] Claude runs the checks; fixing violations is for you.
4. [\*] after E2. **Views:** regenerate GDS, LEF (with antenna data), `.vh` and `.lib` into `final/`. Either adapt the generator to read the routed layout, or use Magic's `lef write` and add the `USE POWER/GROUND` lines afterwards.
5. **Mixed-signal simulation:** replace the broken template top TB with a closed-loop test. Drive `digital_logic` through XSPICE (`macros/counter/scripts/spi2xspice.py`) or `d_cosim`:
   - a full ADC ramp and a sine;
   - a DAC sweep into a realistic pad load (B3);
   - repeat with PEX netlists.

## F. LibreLane integration (`flow/librelane/`)
1. [\*] **SDC** (`impl.sdc`, `signoff.sdc`):
   - false paths for `analog_*` and the macro I/O;
   - async `rst_n`;
   - extra STA hold corners at 1.35/1.5/1.65 V;
   - [\*] after B3: `CLOCK_PERIOD` matching the eFPGA clock.
2. [\*] after B3. **VAPWR straps and Metal4 keep-out:** set up as the organizers specify. The keep-out would be a Metal4 OBS in the macro LEF; that is only possible if the straps over the macro are not needed.
3. [\*] **Makefile:**
   - add a `build-analogue-interface` target that runs the macro's `build-top`, and call it from `build-macros`;
   - remove the `counter`/`inverter` references, so that `make all` works.

## G. Housekeeping (any time before H)
1. [\*] Apply the GHDL fix to `fpga/fpga.mk`. It still uses `ghdl -a` + `ghdl synth <entity>`; use `ghdl synth file.vhdl -e entity`, as the Makefile does.
2. [\*] Add `HeiChips/heichips26-template` as the `upstream` remote and merge it into `main`. This brings in `uses-vapwr` and the precheck update; the PDK pin follows B4.
3. [\*] Clean `main` (the leftovers came in with the `benedikt` merge):
   - delete the 52 `*:Zone.Identifier` files and the 15 committed `simulations/` outputs;
   - delete `*.orig.gds`, `*.bak.gds` and `magic_happy.gds`, after confirming the current GDS of each block;
   - delete the 96 `scripts/sizing/data/*.mat` copies (1.2 GB). They stay in the git history unless the history is rewritten; that is a separate team decision;
   - delete the stale duplicates in `macros/heichips26_analog_project/macros/*` (after a diff) and the `switch/` orphan. Keep the floorplan GDS files;
   - extend `.gitignore` to cover all of these.
4. Delete the template `counter`, `inverter` and `heichips26_digital_project`. Some analog TBs still use the inverter symbols, so check this together.
5. Delete the `pascal` branch, locally and on `origin`; it needs your OK.

## H. Sign-off and submission
1. [\*] `make build-top`: LibreLane, `copy-reports`, `copy-final`, `copy-netlist`.
   - All reports must be clean: KLayout and Magic DRC, LVS, antenna, STA, IR drop (including VAPWR).
   - Commit `final/{gds,lef,vh,lib,nl,pnl,spef}` and `verification/`.
   - Claude fixes violations on the digital side; violations inside the macro go back to D/E.
2. [\*] Gate-level simulation on `final/nl` with the cocotb suite and the analog behavioural model.
3. [\*] `submission.yaml`:
   - set `uses-vapwr` per B3;
   - draft a new `long-description` for you to review. It must describe the 8-bit SAR ADC, 2× 8-bit DAC, S&H, the eFPGA driver sequence and the test/PCB needs; the current one still lists 16-bit DAC/ADC and DDS and fails the precheck hash check.
4. [\*] README: the feature list still says 16-bit DAC/ADC; fix it, and fix the SPDX/licence headers. The macro READMEs need the specs from you.
5. [\*] `make precheck` passes locally; push to `main`.
   - You enable GitHub Actions on the fork; it has never run.
   - You post on issue #13.

## Definition of done
- `make sim-rtl-verilog`, `sim-vhdl`, `sim-rtl-cocotb` and `sim-gl-cocotb` pass, and the closed-loop ADC test is within ±1 LSB.
- The mixed-signal top sim converts a ramp and a sine correctly with PEX netlists.
- Every analog block and the `analogue_interface` macro have committed DRC-, LVS- and antenna-clean reports on the chosen PDK (KLayout and Magic).
- `make build-top` finishes with no DRC, LVS, antenna, power-grid or timing violations.
- `make precheck` passes locally and CI is green on `main`.
