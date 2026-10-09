# heichips26_FAIf: open tasks to tapeout (as of 2026-10-09)

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
  - The full `upstream` template is merged into `main` (2026-10-09, `04242e0`). We keep our own PDK pin (IHP-Open-PDK `90f04ea` + ihp-sg13cmos5l `0d622ea`); upstream's single-repo PDK `1ffc783` is not taken.
- **Analog macro:** `analogue_interface` (300 × 185 µm at (190, 8.82)), built by `macros/analogue_interface/scripts/build_analogue_interface.py` with routes from `scripts/macro_routing.py`.
  - All blocks are real layouts, no dummies left. The iVREF divider R1/R2/C1 is generated from PDK PCells.
  - **DAC path routed** (2026-10-08, `68865bc`, see `macro_dac_routing_PLAN.md`), except the PTAT (iIREF3/4, PTAT supplies), which moves to the ADC round.
  - Macro KLayout DRC (macro deck) clean. Macro LVS against the generated reference schematic is informational until the ADC path is routed.
  - ADC path not routed yet.
- **LibreLane** runs the full flow with this macro: routing, LVS, power grid, antenna and timing are clean.
- **Done since 2026-10-08:**
  - every analog block KLayout DRC and LVS clean (`9d92ed1`);
  - `sah_12bit` layout (floorplan v2b) placed in the macro;
  - macro reference schematic, iVREF divider and DAC-path routing (D4, D5);
  - template projects `heichips26_analog_project` and `heichips26_digital_project` deleted, upstream merged (H2, parts of H3/H4).
- **Done 2026-10-04 to 2026-10-07:**
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
2. **Set in the working tree** (2026-10-09, by the macro routing session, not committed yet): `ERROR_ON_MAGIC_DRC: false` in `flow/librelane/config.yaml`.
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
1. **S&H variant: resolved (2026-10-07) → `sah_12bit`** (fixed 1.21 pF, no trim; see `sah_12bit_sizing_PLAN.md`).
   - It is pin-compatible with the old `sample_and_hold` (VDD, SH_IN, SH_OUT, SH_EN, VSS) and self-contained (no `aswitch`).
   - **Done:** x10 in the top schematic now uses `sah_12bit.sym`, and its folder is on the top xschemrc library path. The top schematic and its testbench netlist cleanly.
   - **`sh_cap_en[3:0]` stays:** the macro pins and the 4 level translators xcap0–3 remain as **spare 3.3 V outputs** for a later trim (e.g. comparator or opamp offset). The RTL tie-off to `0000` stays until the config register (C2) exists.
   - ~~The analog dummy macro stays unchanged for now.~~ **Done:** the real `sah_12bit` layout replaced the S&H dummy in the macro.
   - `sample_and_hold`, `sample_and_hold_trim`, `asw_inv` and `aswitch` become unused (keep for reference or delete in H).
2. **Macro pin names:** keep the current RTL names (`adc_ref`, `adc_hold`, `adc_comp`, `dac_out[15:0]`, `sh_cap_en`), or rename them to TAPEOUT_PLAN §2. A rename changes the generator, the `.vh` and the RTL instance together. [\*] After the decision: write the interface spec into the macro README.
3. ~~PDK pin with `cap_cmomi`~~: **resolved.** MOM caps are fine per the organizer, and our PDK has `cap_cmomi`.

## C. Digital RTL and verification (`macros/heichips26_FAIf/`)
See `sar_rtl_fixes_PLAN.md` for the reasons and the exact changes of C1–C4 (2026-10-09).
1. **`rtl/sar.vhdl`:**
   - ~~[\*] add a 2-FF synchronizer on `comp`~~ **not done, by decision:** the SAR keeps 1 clock per bit; the clock period has to cover DAC + comparator settling (the RP2350 can slow the clock);
   - **Done:** `hold` replaced by the registered `sh_en` (loaded from `mask_next`, same clock edge, no gate to the macro pin); `done` from the same flip-flop;
   - **Done:** result register, `tick` registered: `tick` and the final value appear in the same cycle (the old SAR showed the trial LSB at `tick` in 128 of 256 conversions);
   - **Done:** S&H polarity (see C3);
   - optional, not done: a bit-period prescaler and acquisition phase.
2. **Done:** config register `cfg` (loads `ui_in` while `load_config` = `uio_in[7]` is 1); `cfg[3:0]` → `sh_cap_en`, `cfg[7:4]` unused. README pinout and interface behavior updated.
3. **Done, polarity bugs confirmed with ngspice** on the macro netlist and fixed in `rtl/heichips26_FAIf.sv`: the comparator gives 1 when V_dac > V_in (now `.comp(~adc_comp)`); the S&H tracks when SH_EN = 1 and x9 doesn't invert (macro pin `adc_hold` now driven by `sh_en`).
4. **Testbenches, done:**
   - `gcc`, `zlib` and `LIBRARY_PATH` in `flake.nix` for `ghdl -e/-r`;
   - `testbenches/vhdl/sar_tb.vhdl` (`make sim-vhdl`): all 256 codes exact, plus cycle-by-cycle equivalence with `sar_ref.vhdl` (the old SAR) over 20 000 random cycles;
   - analog behavioral model in `rtl/analogue_interface.sv` (`ifdef SIM`, real polarities);
   - Verilog TB: config register and a closed-loop ADC sweep through the top, with the input changed during each conversion;
   - cocotb TB rewritten for `heichips26_FAIf`: reset, DAC byte order, config register, ADC sweep, clear (RTL: 5/5 pass);
   - Makefile: `sim-vhdl`, `$(GEN_VERILOG)` prerequisites.
   - **Done on `RUN_2026-10-09_13-18-52`** (first run with the new RTL): `sim-gl-cocotb` 5/5 pass. clk → `adc_hold` max arrival (OpenSTA `report_checks -unconstrained`, final netlist + SPEF) typ 0.559 / slow 0.879 / fast 0.373 ns, against the old RTL's 1.469 / 2.331 / 0.969 ns (`RUN_2026-10-09_01-12-07`, path flip-flop → hold-fix delay cell → nor4 → buf → inv). New path: flip-flop → one inverter → pin. Deviation from the plan's "only buffers": the std-cell library has no flip-flop with asynchronous set, so the reset-to-1 `sh_en` flip-flop is a reset-to-0 flip-flop plus an inverter; a single-input inverter can't glitch. Repeat both checks on the sign-off run (G1/G2).
5. Optional: FPGA prototype of the full top.

## D. DAC path first (`analog_1` = DAC0, `analog_2` = DAC1)
The chain per DAC: digital pins `dac_out[7:0]` / `dac_out[15:8]` → 8x level translator (x7 / x12) → R2R DAC with its output buffer (x5 / x11) → `analog_1` / `analog_2`. The DACs need the PTAT currents iIREF3 / iIREF4 (CSOUT3 / CSOUT4) and the reference `iVREF` from the R1/R2/C1 divider.

| Step | Block | Open tasks |
|---|---|---|
| D1 | **R2R DAC** `r2r_dac` (x5, x11; also x4 for the ADC) | **Done:** KLayout + Magic DRC and LVS reports committed (`9d92ed1`); `IDACIREF` label added (LVS extracts it as a port). **Open:** check the Magic NW.d/LU.a entries (11 per DAC). [\*] Remove the TopMetal1 text `ODACOUT` from the source GDS (not verified; the GDS still has 2 `ODACOUT` texts). Sims: INL/DNL, settling into the pad load (B3). |
| D2 | **8x level translator** (x7, x12; also x6 for the ADC) | [\*] KLayout DRC and LVS reports (KLayout is sign-off): the macro README lists the cell as clean, but `verification/drc/` and `verification/lvs/` are empty, so the reports still have to be committed. [\*] Fix the Makefile `TOP` and remove the template files. Delay sims across VPWR 1.08–1.65 V and corners. *If time allows:* fix the tap placement for Magic's latch-up rules (LU.a, LU.d), NW.d and pSD.e/f; 328 Magic errors per instance, not required for sign-off. |
| D3 | **PTAT** `ptat_current_source` | **Done:** layout updated to the fixed schematic (CSOUT1–4 and PBIAS outputs), DRC and LVS clean (`2a4c16f`, `9d92ed1`). **Open: re-simulate** post-layout: the fix changed the mirror (XM5 is now an output, so XM3 : XM4 went from 1 : 2 to 1 : 1). Check the output currents, temperature, VDD and startup. |
| D4 | ~~**iVREF divider** R1, R2 (rhigh 0.5/50 µm), C1 (cap_cmomi 50/2 µm)~~ | **Done:** generated from the PDK PCells in the macro builder, R90 at x 118–169, y 156–167. |
| D5 | **Macro, DAC part** | **Done** (`68865bc`): reference schematic (full macro, see E); routes `dac_out` pins → x7/x12 → x5/x11 → `analog_1/2`, iVREF, IDACDISABLE, VAPWR/VPWR/VGND; macro KLayout DRC clean, metal-only connectivity check passed. **Moved to the ADC round:** iIREF3/4 and the PTAT supplies (the PTAT moved next to the comparator). |
| D6 | **DAC verification** | DAC sweep into the pad load from A3 (R_pad 100 Ω, C_pad 5 pF, external 10 pF ∥ 1 MΩ until the organizer answers), then repeat with PEX. |

## E. ADC path (after D)
| Block | Open tasks |
|---|---|
| **S&H `sah_12bit`** | **Layout done (2026-10-09, floorplan v4):** cell 43.0 × 67.0 µm at (179.2, 45.5); hold cap 33 × 60 cells (1.214 pF) in a VSS shield box with a Metal4 lid, 10.5 µm from the west PDN strap group (not cut). Switch on top of the cap east of the SH_OUT spine, T-switch room and gate driver east of it; SH_IN pin on the east edge (macro (222.2, 112.25)), routed by hand through the corridor x 222.2–232, away from the DAC routes. SH_OUT is one straight spine from the cap to the comparator INN; comparator and PTAT moved to y 115.5. Cell KLayout DRC (density only), Magic DRC 0, KLayout LVS match; post-layout final check and kickback within budget; chip run clean. Open: hold feedthrough −72 dB post-layout (≈ 1 LSB at 12 bit for a full-scale input change during the hold; fine for 8 bit; T-switch later if needed); macro routing of SH_IN/SH_OUT/SH_EN/iSAR_DAC (routes in the macro README). |
| ~~**Spare translators** for `sh_cap_en`~~ | **Done:** xcap0–3 are in the macro reference schematic (generated by `gen_reference_schematic.py`). |
| ~~**Xschem start-up**~~ | **Done:** `make xschem` in `macros/heichips26_FAIf/` opens the top schematic from its own folder. |
| **Opamp** `op_amp_ver_2` (x8) | **Done:** DRC/LVS re-run and reports committed (`9d92ed1`). **Open:** AC stability and CM-range TBs. |
| **Comparator** `555_comparator` (x1) | **Done:** DRC/LVS clean. **Open:** [\*] rename cell, symbol and GDS cell (leading digit), then DRC/LVS again. Check Magic LU.d/NW.d (17). Offset/delay TBs at the real PBIAS. |
| **Single level translators** (x9, xcap0–3) | tap placement for Magic's latch-up rules (200 errors together). |
| **Macro, ADC part** | **Done:** E1, the full macro reference schematic `macros/analogue_interface/schematic/xschem/analogue_interface.sch/.sym` (x1–x12, R1, R2, C1, xcap0–3, S&H, pins), plus `make klayout-lvs`. **Open:** route the rest: x6/x4, opamp x8, S&H x10, comparator x1, x2/x9, xcap0–3, and the PTAT x3 (iIREF1–4, PBIAS, supplies). Then the full macro LVS must match. |

**Macro constraints (both paths):**
- **Location:** at (190, 8.82). `analog_0..2` stay on the south edge at macro x 260.24 / 265.04 / 269.84; west-edge pins stay on the Metal3 track grid (die y = 0.42 · k).
- **Height:** ≤ ≈187 µm. The bottom cell row links the Metal4 straps over the macro to the core grid.
- **Layers:** Metal1–Metal3 only, TopMetal1 empty, Metal4 keep-out per the organizer answer. **Exception:** the Metal4 lid (VSS) over the `sah_12bit` hold cap, obstructed in the macro LEF. Its obstruction keeps ≥ 10.5 µm from the west PDN strap group, because LibreLane cuts straps within `PDN_HORIZONTAL_HALO` = 10 µm; the build script checks this.
- **Power pins:** Metal3 strips, LEF `USE POWER/GROUND`.

**After routing:**
- [\*] regenerate the macro views: GDS, LEF with antenna data, `.vh`, `.lib`;
- macro DRC, LVS, antenna and PEX;
- the mixed-signal top simulation (XSPICE or `d_cosim`): ADC ramp and sine, DAC sweep, also with PEX.

For every block, also: replace the template READMEs and `cace` copies, and run ss/ff corners at −40/27/125 °C, plus Monte Carlo for DAC and opamp offset.

## F. LibreLane integration (`flow/librelane/`)
1. **SDC, done (2026-10-09)** in `impl.sdc` and `signoff.sdc`: false paths from/to `analog_0..2` and from `rst_n`, with the reasons as comments. The macro pins get no constraint: OpenSTA doesn't treat them as endpoints (a false path there only adds warnings). Checked on `RUN_2026-10-09_13-18-52`: worst setup/hold slack and TNS identical with the old and new SDC in all three corners, no warnings. **Open:** extra hold corners at 1.35/1.5/1.65 V (the PDK has these libraries), only if VPWR is above 1.32 V: ask the organizer. `CLOCK_PERIOD: 10` (100 MHz) stays, as confirmed by the organizer.
2. ~~VAPWR straps~~: **resolved**, no change needed (organizer answer). The Metal4 keep-out over the macro is still open (A4).
3. **Makefile, done (2026-10-09):** `build-macros` → `build-analogue-interface`; `lint-verilog-all` lints only the top; `counter` targets removed. `clean-macros` deliberately doesn't clean the analog macro (its `final/` views and DRC/LVS reports are committed sign-off data). `make -n all` resolves; `build-fpga` inside `make all` still needs H1.

## G. Sign-off and submission
1. [\*] `make build-top`. All reports must be clean: KLayout DRC (sign-off), LVS, antenna, STA, IR drop including VAPWR; Magic as far as possible. Commit `final/` and `verification/`.
2. [\*] Gate-level simulation on `final/nl` with the cocotb suite.
3. **Done (2026-10-09):** new `long-description` in `submission.yaml` (pins, digital interface, driver sequence, timing, test/PCB needs). **Open:** add the maximum ADC clock, the ADC input range, the DAC output range and the maximum DAC load once the D6/E simulations give them.
4. **Done (2026-10-09):** README feature list (2× 8-bit R-2R DAC, 8-bit SAR ADC with S&H, VAPWR) and the `XXX` SPDX placeholders in the top RTL and the two top testbenches ("HeiChips 2026 FAIf team"). The template `counter` files still have them (H4).
5. `make precheck` passes locally, Actions are green on the fork; post on issue #13. **Trial run 2026-10-09** on the in-progress `final/` of `RUN_2026-10-09_13-18-52` (new RTL, macro routing unfinished): "Precheck successfully completed", KLayout DRC clean, Magic 1248 errors as warning only. Magic's GDS reader also warns that cells in the opamp layout are placed twice on top of each other (`pmosHV`, `via_stack`; it ignores the extra copy). **Open:** the final run after the macro routing; push to the fork and the issue post need your OK.

## H. Housekeeping (any time before G)
1. [\*] GHDL fix in `fpga/fpga.mk` (`ghdl synth file.vhdl -e entity`).
2. ~~[\*] Merge the full `upstream` template into `main`~~ **Done** (2026-10-09, `04242e0`). Merged with rename detection off, so template updates didn't land in our cells. Our PDK pin, `submission.yaml` and the template deletions were kept; `.spiceinit` gained the `sg13cmos5l_io` source path (not `cap_cmomf.osdi`, which our PDK lacks).
3. [\*] Clean `main`:
   - **Done** (2026-10-09, `860a34f`): deleted the whole template project `macros/heichips26_analog_project` (with its stale `macros/*` copies and 44 of the `*.mat` files);
   - delete the remaining 26 `*:Zone.Identifier` files and the 8 committed `simulations/` outputs;
   - delete `*.orig.gds`, `*.bak.gds`, `magic_happy.gds` (3 left) and local leftovers such as `ptat_curr_gen_old.gds.old`;
   - delete the remaining 52 `*.mat` copies (they stay in the git history unless it's rewritten);
   - delete the `switch/` orphan;
   - extend `.gitignore` to cover all of these.
4. **Done** (2026-10-09, `860a34f`): deleted the template `heichips26_digital_project`. **Open:** delete the template `counter` and `inverter` in `macros/heichips26_FAIf/macros/` (some analog TBs use the inverter symbols; check together).
5. Delete the `pascal` branch locally and on `origin` (needs your OK).

## Definition of done
- `make sim-rtl-verilog`, `sim-vhdl`, `sim-rtl-cocotb` and `sim-gl-cocotb` pass; the closed-loop ADC test is within ±1 LSB.
- The mixed-signal top sim converts a ramp and a sine and sweeps both DACs correctly, with PEX netlists.
- Every analog block and the macro have committed DRC-, LVS- and antenna-clean reports.
- `make build-top` finishes with no DRC, LVS, antenna, power-grid or timing violations.
- `make precheck` passes locally and CI is green.
