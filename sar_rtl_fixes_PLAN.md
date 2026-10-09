# Plan: SAR / top RTL fixes, config register, testbenches (todo C1–C4)

## Context
The digital side of the ADC was written before the analog blocks were final. Reading the transistor netlists of the current macro (`macros/analogue_interface/netlist/schematic/analogue_interface_klayout.cdl`) against `rtl/sar.vhdl` and `rtl/heichips26_FAIf.sv` shows two polarity bugs that make the ADC unusable and two timing weaknesses at the digital/analog boundary. This round fixes them, adds the config register (C2), and adds testbenches that close the loop with a model of the real analog polarities. Nothing here touches the analog macro, so it doesn't collide with the routing session.

**Your choices:** fixes 1, 2, 3 and 4; **no** comparator synchronizer (the SAR keeps 1 clock cycle per bit, settling time comes from the clock rate); config register C2 included.

## Why each fix is needed

| # | Finding (evidence) | Effect if not fixed |
|---|---|---|
| 1 | **Comparator polarity.** `555_comparator`: PMOS input pair, mirror diode on the INN side, output on the INP side, then two inverters: OUT = 1 when V(INP) > V(INN). In the macro INP = DAC (`iSAR_DAC`), INN = S&H output (`iSAR_AN`). The down translator x2 is two inverters (non-inverting). So `adc_comp = 1` means V_dac > V_in, but the SAR keeps a bit when `comp = 1`. | The SAR keeps exactly the bits that are too high: e.g. 2 bits, input at code 1 → 11, input at code 2 → 00. Can't be repaired in software. |
| 2 | **S&H polarity.** `sah_12bit`: SH_EN = 1 closes the switch (track). The old `sample_and_hold` was the same (SH_EN on the `aswitch` NMOS gate). x9 doesn't invert; the SAR drives `hold = 1` during the conversion. | The S&H tracks during the conversion and holds a stale value while idle. |
| 3 | **`tick` one cycle before the data.** `tick` is high while the LSB is still being decided; `value` still shows the trial LSB = 1 then. `tick` is also a combinational path from input pins to `uio_out[4]`. | Reading `uo_out` on `tick` gives LSB = 1 always (≈ half the conversions off by 1 LSB); possible glitches on `uio_out[4]`. |
| 4 | **`hold` combinational** (`OR` of the one-hot `mask_reg`, which shifts every edge). | A sub-ns glitch low can reach SH_EN and briefly reopen the S&H during the hold; not guaranteed to be filtered by x9. |

### Exact RTL change for fixes 2 + 4 (logic function unchanged)
Today (output logic of `rtl/sar.vhdl`):
```vhdl
hold <= '1' when mask_reg /= MASK_ZERO else '0';
done <= '1' when mask_reg  = MASK_ZERO else '0';
```
New:
```vhdl
-- REG process
if rst_n = '0' then
  mask_reg  <= (others => '0');
  sh_en_reg <= '1';                       -- after reset: idle = track (= hold '0' today)
elsif rising_edge(clk) then
  mask_reg  <= mask_next;
  if mask_next = MASK_ZERO then sh_en_reg <= '1'; else sh_en_reg <= '0'; end if;
end if;
-- output logic
sh_en <= sh_en_reg;                       -- replaces port hold (sh_en = not hold)
done  <= sh_en_reg;                       -- done was always = not hold
```
- `mask_reg` and `sh_en_reg` load from the same `mask_next` at the same edge, so after every edge `sh_en_reg = (mask_reg = 0)` = today's `not hold`; reset gives the same value.
- The next-state process `NSL` is not touched: `value_next`, `mask_next`, `ref_out` and the conversion sequence stay as they are.
- Hardware: +1 flip-flop; the 9-input compare moves from behind the mask register to in front of the new flip-flop; no gate between the flip-flop and the macro pin `adc_hold` (fix 2's inversion is folded in).

### Timing impact of fixes 3 and 4 (no added delay)
- **Fix 4:** the new flip-flop is loaded with the *next* value, `mask_next /= 0`, so it switches at the **same clock edge** as `mask_reg` today. Cycle timing is identical. At the output, today's path is clk→Q + 9-input OR; the new path is clk→Q only, so SH_EN switches **earlier** by the OR delay (≈ 0.1–0.2 ns). The flip-flop stores SH_EN polarity directly (`sh_en_reg <= '1' when mask_next = MASK_ZERO`), so fix 2 adds no inverter either.
- **Fix 3:** the final value is still written at the same edge as today, and `done` still rises at that edge. Only `tick` moves one cycle later, to the edge where the data is actually valid. Conversion time is unchanged: 1 start cycle + NBITS cycles.

## Steps (after your go)
0. Copy this plan to `sar_rtl_fixes_PLAN.md` at the repo root and commit only that file.
1. **C3 check in simulation** (scratchpad testbench, nothing in the repo): ngspice DC sweep of the `555_comparator` subcircuit (INP swept around INN) and of the `sah_12bit` switch (SH_EN 0 / 3.3 V). If the result disagrees with the netlist reading, stop and report.
2. **Reference copy:** save the current `rtl/sar.vhdl` as `testbenches/vhdl/sar_ref.vhdl` (entity renamed `sar_ref`), unchanged otherwise. It is the golden model for the equivalence checks.
3. **`rtl/sar.vhdl`** (keeps its documented meaning: comp = 1 → keep the bit):
   - `sh_en` output from a flip-flop loaded with `mask_next = MASK_ZERO` (1 = track; replaces `hold`); `done` from the same next-state logic;
   - `result` register loaded with `value_next` at the last decision; `tick` registered, so `tick` and the final `value` appear in the same cycle; `value` shows the latched result, not the conversion in progress; `ref_out` (DAC) unchanged;
   - `clear` also clears `result`; header, description and revision line updated.
4. **`rtl/heichips26_FAIf.sv`:**
   - comparator polarity at the macro boundary: `.comp(~adc_comp)`, with a comment on the netlist evidence;
   - macro pin `adc_hold` driven by the SAR's `sh_en` (a flip-flop output, no gate in between);
   - **C2 config register:** `cfg` loads `ui_in` when `load_config` (`uio_in[7]`) = 1, reset to 0; `cfg[3:0]` → `sh_cap_en`; `cfg[7:4]` listed in `_unused`.
5. `make gen-verilog` regenerates `rtl/gen/sar.v`.
6. **C4 testbenches:**
   - `flake.nix`: add `gcc` (this GHDL uses the LLVM backend, which needs it for `-e/-r`);
   - `rtl/analogue_interface.sv`: behavioral model under `ifdef SIM` with the **real** polarities (comp = 1 when V_dac > V_in; the S&H tracks while its enable is 1), `real vin` set by the testbench. LibreLane doesn't read this file (it uses the macro `.vh`), so synthesis is unaffected;
   - `testbenches/vhdl/sar_tb.vhdl`: port names fixed, ideal comparator model, all 256 codes, plus the **equivalence checks** below;
   - `testbenches/verilog/heichips26_FAIf_tb.sv`: existing DAC checks kept, plus config register and a closed-loop ADC sweep through the top (catches fixes 1 and 2 end to end);
   - `testbenches/cocotb/heichips26_FAIf_tb.py`: replace the template counter test with tests for `heichips26_FAIf` (reset, DAC byte order, config register, ADC sweep); GL mode uses `final/nl` plus the model;
   - `Makefile`: `sim-vhdl` target; `$(GEN_VERILOG)` as prerequisite of the lint/sim targets.
7. Update `TAPEOUT_TODO_PLAN.md` (C1–C4 status) and the README pinout (`uio_in[7]` load_config, `ui_in` → cfg, cfg bit meaning, `tick`/`value` timing).

## How fixes 3 and 4 are checked for errors (no change in behavior or timing)
- **Cycle-accurate equivalence in `sar_tb.vhdl`:** old `sar_ref` and new `sar` run side by side on the same clock and stimuli: all 256 input codes, plus random `start`/`clear`/`ena` sequences (start during a conversion, clear mid-conversion, ena toggling). Checked every cycle, just before each rising edge:
  - `new.sh_en = not old.hold` (fix 4 changes no cycle);
  - `new.done = old.done`, `new.ref_out = old.ref_out` (DAC sequence and conversion length unchanged);
  - `new.tick` = `old.tick` delayed by exactly 1 cycle, and on `new.tick` `new.value` = old `value` after the final edge = expected code (fix 3);
  - `new.value` is stable between two ticks.
- **Glitch-free `sh_en` by construction:** after synthesis (`yosys` on `rtl/gen/sar.v`), check that the `sh_en` output is driven directly by a flip-flop Q with no logic in between. After the next `make build-top`, the same check on `final/nl` (only buffers allowed between the flip-flop and the macro pin `adc_hold`).
- **Timing:** the macro pin is unconstrained (no timing arcs in the macro `.lib`), so the normal STA reports don't list it. Measure the clk → `analogue_interface_instance/adc_hold` arrival with OpenSTA `report_checks -unconstrained -to …` on the post-PnR netlist + SPEF of the current run (`RUN_2026-10-09_01-12-07`, step 55 `stapostpnr`) as baseline, and again on the next `make build-top` run. The new arrival must be ≤ the baseline at all three corners, i.e. no added delay.

## Verification
- ngspice polarity check (step 1) matches the netlist reading.
- `make lint-verilog` (Verilator) clean.
- `make sim-vhdl`: all 256 codes exact with the ideal model; all equivalence checks above pass.
- `make sim-rtl-verilog` and `make sim-rtl-cocotb` pass, including the closed-loop ADC sweep through the top with the real analog polarities.
- `sim-gl-cocotb` and the netlist/STA checks wait for the next `make build-top` (G1/G2); the current `final/nl` predates these changes.
- Nothing is committed except the plan file (step 0) without your OK.
