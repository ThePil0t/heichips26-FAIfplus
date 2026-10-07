# heichips26_FAIf: open tasks to tapeout (as of 2026-10-07)

> **[\*]** = Claude can do this reliably and check the result with the tools in `nix-shell`: verilator, iverilog, cocotb, GHDL, yosys, LibreLane, xschem netlisting, KLayout/Magic DRC and LVS, `make precheck`.
> Unmarked tasks need a team or organizer decision, analog design judgement, hand-drawn layout, or verification that can't be done here.
> "[\*] after X" means Claude can do it once X has been decided or delivered.

This plan lists only what is still to do. [TAPEOUT_PLAN.md](TAPEOUT_PLAN.md) stays as background and history.

**Scope stays as decided:** 8-bit SAR ADC, 2× 8-bit R-2R DAC, trimmed S&H. **The two DACs have priority:** the DAC path is finished first (section D), the ADC path after it (section E). The organizer needs the final design by the end of the week (of 2026-10-05).

## Where we are
- **Precheck:**
  - `submission.yaml` has `uses-vapwr: true`, and the VAPWR-capable precheck comes from the `upstream` template.
  - `final/` holds the views of the latest LibreLane run (`RUN_2026-10-07_12-53-17`): **0 KLayout DRC errors**. Magic shows 1248 errors (≈310–420 unique), but the precheck only warns about Magic.
  - The fork `ThePil0t/heichips26-FAIfplus` (remote `fork`) runs the precheck in GitHub Actions.
- **Analog macro:** a placement-only `analogue_interface` (300 × 185 µm at (190, 8.82), nothing routed) built by `macros/analogue_interface/scripts/build_analogue_interface.py` from the existing block layouts. Dummies stand in for the trimmed S&H, R1, R2 and C1.
- **LibreLane** runs the full flow with this macro: routing, LVS, power grid, antenna and timing are clean.
- **Done since 2026-10-04:**
  - **PTAT:**
    - nBuLay removed, tap contacts moved off the ThickGateOx edge (KLayout clean, Magic only 4 × Sal.c/d at the PDK resistor);
    - schematic renamed to `ptat_curr_gen`, symbol pin CSOUT4 fixed (no more iIREF3/iIREF4 short);
    - PBIAS/CSOUT3 wiring fixed (PBIAS = mirror gate line, CSOUT1–4 each with its own mirror PMOS);
    - `MSS[5:1]` split into `MSS1`–`MSS5` so the LVS netlist works;
    - Makefile `TOP` fixed.
  - **Down translator:** N-well tap spacing fixed (Act.b, pSD.e, NW.e1), DRC and LVS clean.
  - **8x level translator:** the sub-cell folder is now on the Xschem library path. That was also the cause of the top-level netlist error (exit code 10).
  - **Organizer questions:** sent.

## Critical path
```
D DAC path (blocks → macro routing → DAC sims) ──┐
E ADC path (S&H decision → blocks → routing) ────┼─► G Sign-off + submit
C Digital RTL + verification ────────────────────┤
F Integration (SDC, VAPWR, Makefile) ────────────┘
H Housekeeping: any time before G
```

---

## A. Small loose ends and open points
1. [\*] Add the power pins (`VPWR`, `VAPWR`, `VGND` under `USE_POWER_PINS`) to the simulation stand-in `rtl/analogue_interface.sv`, so it matches the macro's `.vh`.
2. **Open, not changed yet:** add `ERROR_ON_MAGIC_DRC: false` to `flow/librelane/config.yaml`.
   - The organizer confirmed that KLayout DRC is the sign-off deck; Magic can even be disabled in the precheck.
   - With the flag on, every full run ends with "deferred errors" and LibreLane doesn't update `flow/final/` (workaround: copy the run's `final/` by hand).
   - If set, watch the Magic count in the run summary instead.
3. **Open: analog pad path** (question to the organizer drafted 2026-10-07). Until the answer arrives, the DAC and ADC sims use this **assumed pad path per analog pin**:
   - series resistance **R_pad = 100 Ω** (on-chip routing plus ESD series resistor);
   - pad capacitance **C_pad = 5 pF** to VGND (pad, ESD diodes, bond wire, package);
   - for the DAC outputs also an external load of **10 pF ∥ 1 MΩ** (PCB trace plus probe).

   Replace these values once the organizer answers.
4. **Open, not asked yet:**
   - Metal4 over the analog macro (signal routing allowed, or keep-out?);
   - fill over the analog blocks;
   - PCB: VAPWR supply, access to the analog pins.

### Organizer answers (2026-10-07)
- **VAPWR:** always available, 3.3 V. The precheck fix is in the upstream template (already used). `heichips26_template_small_analog.def` is the right template (already used).
- **Power straps:** positions don't matter. The HeiChips top runs horizontal VPWR/VGND/VAPWR straps over the project and connects to all vertical straps where they cross. Our VAPWR straps only over the macro are fine.
- **Clock:** the RP2350 supplies the clock and can run as slowly as needed. Implement for 100 MHz (as now). `ena` must not be used (it isn't).
- **DRC:** KLayout DRC is the sign-off deck. Fixing the Magic violations is still best but not required.
- **Caps:** MOM caps (`cap_cmomi`) are fine; MIM caps aren't available in CMOS5L. Our PDK has `cap_cmomi`.

## B. Decisions
1. **S&H variant** (blocks the ADC path only): the trimmed `sample_and_hold_trim` (`cap_en[3:0]`) or `sah_12bit` (fixed 1.21 pF, no trim; recommended by `sah_12bit_sizing_PLAN.md`). The macro reserves 110 × 58 µm for the trimmed version.
2. **Macro pin names:** keep the current RTL names (`adc_ref`, `adc_hold`, `adc_comp`, `dac_out[15:0]`, `sh_cap_en`), or rename them to TAPEOUT_PLAN §2. A rename changes the generator, the `.vh` and the RTL instance together. [\*] After the decision: write the interface spec into the macro README.
3. ~~PDK pin with `cap_cmomi`~~: **resolved.** MOM caps are fine per the organizer, and our PDK has `cap_cmomi`.

## C. Digital RTL and verification (`macros/heichips26_FAIf/`)
1. **`rtl/sar.vhdl`:**
   - [\*] add a 2-FF synchronizer on `comp`;
   - [\*] make `hold` a registered flip-flop; today it is a combinational decode of `mask_reg`;
   - [\*] latch the result at end of conversion and line up `tick` with valid data;
   - [\*] build the bit-period prescaler and acquisition phase as a mechanism;
   - [\*] after C3: fix the S&H polarity (`sar_sh_en = not hold`);
   - set the prescaler value; it needs the analog settling times.
2. [\*] after B1. **Config register:** when `load_config` (`uio_in[7]`) is 1, latch `ui_in` into `cfg`; `cfg[3:0]` replaces the `4'b0000` tie-off on `sh_cap_en`, or `sh_cap_en` is removed if B1 picks `sah_12bit`. Update `_unused` and the README pinout.
3. **Polarity bugs:** confirm both in simulation. The S&H enable must be `not hold`, and the comparator output must be 1 when V_in ≥ V_dac.
4. **Testbenches:**
   - [\*] add `gcc` to `flake.nix` for `ghdl -e/-r`;
   - [\*] fix `testbenches/vhdl/sar_tb.vhdl` (`ref` → `ref_out`) and add asserts;
   - [\*] add a closed-loop SAR system TB (±1 LSB);
   - [\*] extend the Verilog TB (SAR, config register, DAC byte order);
   - [\*] rewrite the cocotb TB, which is still the template counter test, for RTL and gate level;
   - [\*] add the `sim-vhdl` and `$(GEN_VERILOG)` prerequisites in the Makefile.
5. Optional: FPGA prototype of the full top.

## D. DAC path first (`analog_1` = DAC0, `analog_2` = DAC1)
The chain per DAC: digital pins `dac_out[7:0]` / `dac_out[15:8]` → 8x level translator (x7 / x12) → R2R DAC with its output buffer (x5 / x11) → `analog_1` / `analog_2`. The DACs need the PTAT currents iIREF3 / iIREF4 (CSOUT3 / CSOUT4) and the reference `iVREF` from the R1/R2/C1 divider.

| Step | Block | Open tasks |
|---|---|---|
| D1 | **R2R DAC** `r2r_dac` (x5, x11; also x4 for the ADC) | [\*] run DRC (KLayout + Magic) and LVS, and commit the reports. Add the missing `IDACIREF` label. Check the Magic NW.d/LU.a entries (11 per DAC). [\*] Remove the TopMetal1 text `ODACOUT` from the source GDS. Sims: INL/DNL, settling into the pad load (B3). |
| D2 | **8x level translator** (x7, x12; also x6 for the ADC) | fix the tap placement for Magic's latch-up rules (LU.a: P-diff to N-tap ≤ 20 µm; LU.d), plus NW.d and pSD.e/f; 328 Magic errors per instance. [\*] Fix the Makefile `TOP` and remove the template files. [\*] DRC/LVS reports. Delay sims across VPWR 1.08–1.65 V and corners. |
| D3 | **PTAT** `ptat_current_source` | update the layout to the fixed schematic: add the CSOUT4 output (DAC1's bias) and the PBIAS output; remove CSSTARTUP or add it to the schematic. Then LVS clean. **Re-simulate:** the fix changed the mirror (XM5 is now an output, so XM3 : XM4 went from 1 : 2 to 1 : 1). Check the output currents, temperature, VDD and startup. |
| D4 | **iVREF divider** R1, R2 (rhigh 0.5/50 µm), C1 (cap_cmomi 50/2 µm) | draw them in the macro (PDK PCells via the KLayout GUI). |
| D5 | **Macro, DAC part** | E1 reference schematic (at least the DAC part). Route in the macro: `dac_out` pins → x7/x12 → x5/x11 → `analog_1/2`; iIREF3/4, iVREF, VAPWR/VPWR/VGND. Macro DRC/LVS of the routed part. |
| D6 | **DAC verification** | DAC sweep into a realistic pad load, then repeat with PEX. |

## E. ADC path (after D)
| Block | Open tasks |
|---|---|
| **S&H** (after B1) | finish the testbenches; draw all layouts (S&H, switches, MOM caps). [\*] Delete the template `inverter.gds` in `aswitch/layout/`. |
| **Top schematic** `heichips26_FAIf.sch` | swap x10 (still `sample_and_hold.sym`) for the chosen S&H. If trimmed: add 4 × `digital_level_translator` for `cap_en[3:0]`. |
| **Opamp** `op_amp_ver_2` (x8) | [\*] re-run DRC/LVS and commit the reports. AC stability and CM-range TBs. |
| **Comparator** `555_comparator` (x1) | [\*] rename cell, symbol and GDS cell (leading digit), then DRC/LVS. Check Magic LU.d/NW.d (17). Offset/delay TBs at the real PBIAS. |
| **Single level translators** (x9, xcap0–3) | tap placement for Magic's latch-up rules (200 errors together). |
| **Macro, ADC part** | finish E1 and route the rest. The full macro reference schematic is `macros/analogue_interface/schematic/xschem/analogue_interface.sch/.sym`: x1–x12, R1, R2, C1, the S&H and the pins from B2. |

**Macro constraints (both paths):**
- **Location:** at (190, 8.82). `analog_0..2` stay on the south edge at macro x 260.24 / 265.04 / 269.84; west-edge pins stay on the Metal3 track grid (die y = 0.42 · k).
- **Height:** ≤ ≈187 µm. The bottom cell row links the Metal4 straps over the macro to the core grid.
- **Layers:** Metal1–Metal3 only, TopMetal1 empty, Metal4 keep-out per the organizer answer.
- **Power pins:** Metal3 strips, LEF `USE POWER/GROUND`.

**After routing:**
- [\*] regenerate the macro views: GDS, LEF with antenna data, `.vh`, `.lib`;
- macro DRC, LVS, antenna and PEX;
- the mixed-signal top simulation (XSPICE or `d_cosim`): ADC ramp and sine, DAC sweep, also with PEX.

For every block, also: replace the template READMEs and `cace` copies, and run ss/ff corners at −40/27/125 °C, plus Monte Carlo for DAC and opamp offset.

## F. LibreLane integration (`flow/librelane/`)
1. [\*] **SDC:** false paths for `analog_*` and the macro I/O; async `rst_n`; extra hold corners at 1.35/1.5/1.65 V; [\*] after the organizer answer: `CLOCK_PERIOD` matching the eFPGA clock.
2. [\*] after the organizer answer. **VAPWR straps and Metal4 keep-out** as specified.
3. [\*] **Makefile:** add a `build-analogue-interface` target to `build-macros`; remove the `counter`/`inverter` references so `make all` works.

## G. Sign-off and submission
1. [\*] `make build-top`. All reports must be clean (KLayout DRC, LVS, antenna, STA, IR drop including VAPWR; Magic as far as possible). Commit `final/` and `verification/`.
2. [\*] Gate-level simulation on `final/nl` with the cocotb suite.
3. [\*] `submission.yaml`: draft a new `long-description` for you to review. It must describe the 8-bit SAR ADC, 2× DAC, S&H, the eFPGA driver sequence and the test/PCB needs; the current one still lists 16-bit DAC/ADC and DDS.
4. [\*] README: fix the feature list (still 16-bit DAC/ADC) and the SPDX headers.
5. `make precheck` passes locally, Actions are green on the fork; post on issue #13.

## H. Housekeeping (any time before G)
1. [\*] GHDL fix in `fpga/fpga.mk` (`ghdl synth file.vhdl -e entity`).
2. [\*] Merge the full `upstream` template into `main`; so far only `.github/precheck` was taken from it.
3. [\*] Clean `main`:
   - delete the 52 `*:Zone.Identifier` files and the 15 committed `simulations/` outputs;
   - delete `*.orig.gds`, `*.bak.gds`, `magic_happy.gds` and local leftovers such as `ptat_curr_gen_old.gds.old`;
   - delete the 96 `*.mat` copies (1.2 GB; they stay in the git history unless it's rewritten);
   - delete the stale `macros/heichips26_analog_project/macros/*` copies and the `switch/` orphan;
   - extend `.gitignore` to cover all of these.
4. Delete the template `counter`, `inverter` and `heichips26_digital_project` (some analog TBs use the inverter symbols; check together).
5. Delete the `pascal` branch locally and on `origin` (needs your OK).

## Definition of done
- `make sim-rtl-verilog`, `sim-vhdl`, `sim-rtl-cocotb` and `sim-gl-cocotb` pass; the closed-loop ADC test is within ±1 LSB.
- The mixed-signal top sim converts a ramp and a sine and sweeps both DACs correctly, with PEX netlists.
- Every analog block and the macro have committed DRC-, LVS- and antenna-clean reports.
- `make build-top` finishes with no DRC, LVS, antenna, power-grid or timing violations.
- `make precheck` passes locally and CI is green.
