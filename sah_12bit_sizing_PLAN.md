# Plan: hold-capacitor sizing for 12 bit in a new macro `sah_12bit`

## Context
The hold capacitor in `sample_and_hold` (fixed C1 ≈ 978 fF) and `sample_and_hold_trim` (0.23–2.9 pF, 4-bit array) was picked by hand. This plan sizes it from first principles for **12-bit performance only**:
- identify the limits on accuracy and speed;
- size first with an ideal source (infinite drive), then with `op_amp_ver_2` as the unity-gain buffer;
- size it untrimmed;
- decide whether a trim capability is worth it.

All changes go into a **new macro `sah_12bit`**. The existing `sample_and_hold`, `sample_and_hold_trim`, `aswitch`, opamp, comparator and top level stay untouched. Speed is an **output**: C is sized for accuracy, and the study reports the reachable track time, hold time and fs.

**Facts the sizing relies on**
- **Process and supply:** PDK `ihp-sg13cmos5l`. The only capacitor is the MOM `cap_cmomi`: 0.82 fF/µm² of active area for M1–M3, about 0.78 fF/µm² drawn. It has no mismatch, corner, TC or VC model, and adds a `GLEAK`=1e-12 S leak to substrate on each terminal. All devices are HV at 3.3 V. FS = 3.3 V, the same as the DAC reference.
- **Topology:** `op_amp_ver_2` follower → HV transmission gate (N 4/0.6, P 14/0.6, half-size dummies, ≈1 kΩ) → C to VSS → `555_comparator` INN (HV PMOS, 2×5/0.45). Sampling is single-ended on the top plate. The hold cap is **not** part of a ratio (it is not a CDAC), so its value does not enter the transfer function.
- **Opamp at 25 nA:**
  - Slew rate ≈ 0.24–0.4 V/µs, with Cc = 2×422 fF and a class-AB output.
  - Output swing 0.39–3.3 V.
  - GBW, gain and PM were never simulated; my estimate is a GBW of 0.5–1 MHz.
- **Existing trim TB data (27 °C):**
  - At 0.23 pF: pedestal 3.7–9.4 mV, droop up to 101 mV/ms (≈ 23 pA).
  - At 2.9 pF: droop ≈ 21 mV/ms (≈ 61 pA), because the trim switches add leakage.

## 12-bit error budget
- **LSB and noise:** LSB = 3.3 V / 4096 = 806 µV. Quantization noise q = LSB/√12 = 233 µV.
- **Total noise:** σ ≤ q. kT/C gets half of the noise power, so σ_kTC ≤ 165 µV; the rest goes to the opamp, comparator and DAC.
- **Deterministic errors:** each of the following must stay ≤ ¼ LSB = 201 µV in the worst case over Vin, temperature (−40/27/125 °C) and corners tt/ss/ff/sf/fs:
  - settling;
  - the nonlinear part of the pedestal;
  - droop over t_hold;
  - comparator kickback;
  - hold feedthrough.
- **Offset and gain:** the constant and linear parts of the pedestal and of the opamp gain error are reported separately. They are calibratable and not counted as INL.

## Limits and first-cut numbers (hand estimates; simulations replace them)
**A. Ideal source (infinite drive)**

| Mechanism | Scaling law | 12-bit first cut |
|---|---|---|
| kT/C noise | C ≥ 2kT/q² | ≥ 0.15 pF at 27 °C, ≥ 0.20 pF at 125 °C |
| Charge injection, nonlinear part (switch scaled with C) | ΔV·τ ≈ k_res·L²/(2µ) ≈ k_res·3.4 ps·V (HV, L = 0.5 µm). This is set by the **track time**, not by C | τ ≥ k_res·17 ns, so t_trk ≥ k_res·164 ns |
| Charge injection with today's switch | ∝ 1/C | ≈ 1–2 pF (from the existing TB data) |
| Droop | C ≥ I_leak·t_hold / (¼ LSB) | ≈ 0.11 pF per µs of hold (23 pA, 27 °C); higher at 125 °C |
| Comparator kickback | C ≥ Q_kb / (¼ LSB) | to be simulated |
| Hold feedthrough | C_ds,off / C, must be < −84 dB | already −118 dB at 0.23 pF |
| Settling | t_trk = 9.7·Ron·(C + C_par) | sets the switch W |
| Tracking distortion and aperture | Ron(Vin) variation × C × 2πf_in; gate fall time × Vin/VDD; jitter | limits f_in, not C; jitter must be ≤ 1.3 ns at 25 kHz |
| Area | 0.78 fF/µm² | about 2.6k µm² for 2 pF |

k_res is the remaining fraction of the nonlinear charge injection after CMOS and dummy cancellation. It comes from simulation.

**B. With op_amp_ver_2 as the buffer (additional limits)**
- **Slew rate:** SR ≈ I_tail/Cc. A full-scale input step takes 7–12 µs, and a full-scale sine is limited to about 26 kHz. This does not depend on C.
- **Recharging C at the start of track:** this goes through the class-AB output's local Miller loop, τ ≈ C/gm_out,large-signal. The existing results are 12 ns at 0.23 pF and about 200 ns at 2.9 pF.
- **Small-signal settling:** 9.7/(2π·GBW), i.e. about 1.5–3 µs.
- **Stability:** the output pole gm_out,q/(2πC) must stay above about 2×GBW. This sets an upper limit on C, estimated in the 5–10 pF range.
- **Opamp noise sampled on C:** about α·kT/Cc ≈ 70–120 µV rms. This uses up much of the 12-bit noise budget, so the simulation must verify it.
- **Gain nonlinearity:** the measured tracking error varies by 40 µV, which is fine (budget 201 µV).
- **Swing floor at 0.39 V:** this reduces the usable full scale, and the report states it.

## New macro `macros/heichips26_FAIf/macros/sah_12bit/`
- **Skeleton:** copy from `sample_and_hold/`, i.e. the Makefile, README.md, `scripts/` (sak-*, lay2img, check_pex_ports), and `schematic/xschem/xschemrc` and `testbenches/xschem/xschemrc`.
  - Set `TOP = sah_12bit`.
  - In the xschemrc files, add library paths to `../../../opamp/schematic/xschem` and `../../../comparator/schematic/xschem`. The TBs need these.
  - Leave out the template inverter TBs and CACE yaml.
- **`schematic/xschem/sah_12bit.sch` and `.sym`:**
  - The pins match `sample_and_hold.sym` (SH_IN, SH_OUT, SH_EN, VDD, VSS) so the cell can drop into the top level later.
  - The transmission gate, its dummies and the gate inverter are placed **directly in this cell** with the new sizes. `aswitch` keeps its current sizes, because `asw_inv`, `sample_and_hold` and an opamp TB also use it.
  - The hold cap is `cap_cmomi` (M1–M3).
  - During the study the sizes are parameters (`wn`, `wp`, `cw`, `cl`), and they are frozen at the end.
- **`testbenches/xschem/`:** the testbenches listed under Steps.
- **`scripts/sizing/cs_sizing.py`:** numpy and matplotlib, both available in nix-shell; pygmid and scipy are not.
- **`docs/hold_cap_sizing.md`:** the report.

## Steps
0. **Save this plan first.** Copy this plan unchanged to `sah_12bit_sizing_PLAN.md` at the repo root, next to `TAPEOUT_PLAN.md`. Commit only that file on branch `benedikt`, with the message "Add sah_12bit_sizing_PLAN.md". The untracked `rtl/gen/` stays out of the commit. Nothing is pushed unless you ask. No other work starts before this commit.
1. **Set up the macro.** Create the skeleton, plus a first `sah_12bit.sch` and `.sym` with the parametrized transmission gate and cap.
2. **Analytic sizing script, `cs_sizing.py`.**
   - It encodes the budget and the scaling laws above.
   - It reads the `.txt` results from steps 3–5.
   - It outputs:
     - C_min for each mechanism;
     - the switch W;
     - t_trk, t_hold and fs versus C, for the ideal source and for the opamp.
3. **Ideal-drive characterization, `sah_12bit_ideal_tb_{dc,tran,noise}.sch`.** These follow the pattern of `sample_and_hold_trim_tb_tran.sch` (a control block with `foreach`, `alterparam` and `meas`, writing a `.txt`). The source is ideal (0 Ω).
   - DC: Ron(Vin).
   - Transient sweeps: Vin 0.1–3.2 V (16 points) × ideal C {0.25, 0.5, 1, 2, 4 pF} × switch scale × gate fall time {0.1, 1, 5 ns} × temperature × corner.
   - Transient outputs:
     - Q_inj(Vin) = ΔV·C, split into offset, gain and nonlinear residual; the residual gives k_res.
     - I_leak(Vin, T), with the GLEAK artifact separated out.
     - Full-scale step acquisition time to ¼ LSB.
     - Hold feedthrough.
   - `.noise`: check kT/C.
4. **Buffer characterization, `sah_12bit_opamp_tb_{ac,noise,dc,tran}.sch`.** The chain is op_amp_ver_2 follower → sah_12bit → real `555_comparator`.
   - `.ac` loop gain with a loop-break probe, for C from 0.25 to 16 pF: GBW and PM, which give the upper limit on C.
   - `.noise` integrated at SH_OUT in track mode.
   - DC sweep: follower INL.
   - Transient: acquisition for a full-scale step and for a small step, and the pedestal with the real source impedance.
   - IBIAS sweep {25, 50, 100 nA}: shows how much bias would buy, without changing the opamp schematic.
5. **Comparator kickback, `sah_12bit_kickback_tb_tran.sch`.** Drive INP with a 12-step SAR binary-search staircase. Measure the disturbance on C per decision and its dependence on the decision history.
6. **Choose the sizes.** C = max over all mechanisms with margin, limited from above by the opamp's stability. Then:
   - pick the switch W from the settling budget;
   - freeze them in `sah_12bit.sch`;
   - report the reachable fs for the ideal source and for the opamp, at 25 nA and at the swept biases.
7. **Trim evaluation, `sah_12bit_trim_cmp_tb_tran.sch`.** This instantiates the existing `sample_and_hold_trim.sym` read-only, next to `sah_12bit` with the same total C.
   - Run all 16 codes at −40/27/125 °C.
   - Compare:
     - the nonlinear pedestal;
     - droop and leakage;
     - the two-time-constant settling tail (trim-switch Ron × C_trim, then charge redistribution after hold);
     - memory from floating disabled caps.
   - The MOM spread is not modelled, so sweep the cap size by ±15 % by hand.
   - **Current assessment, to be confirmed by simulation:** in a voltage-mode S&H, trimming C corrects no error. It only moves the speed/accuracy point, and process spread can be covered by margin. Meanwhile the array more than doubles the leakage, adds a settling tail and nonlinear junction capacitance, and its codes are non-monotonic (C4 = C5).
   - **Expected recommendation:** use a fixed C. If speed/accuracy flexibility is wanted, make the SAR acquisition time programmable (the prescaler already planned in TAPEOUT_PLAN). If a trim is kept, put the switches at the bottom plate (NMOS to VSS) and use binary weights.
8. **Report, `sah_12bit/docs/hold_cap_sizing.md`.** It contains the budget table with the simulated values, the chosen C and W, the speed results, and the trim verdict. The plots go to `testbenches/xschem/plot_simulations/figures/`.

## Reused
- `sample_and_hold_trim/testbenches/xschem/sample_and_hold_trim_tb_tran.sch`, for its measurement definitions and stimulus pattern.
- `plot_simulations/ngspice2python.py`, for parsing `.raw` files.
- `op_amp_ver_2.sym` and `555_comparator.sym`, as symbols only.
- `sample_and_hold_trim.sym`, used read-only for the trim comparison.

## Verification
- **Running the sims:** start `nix-shell`, then `export PDK_ROOT=$PWD/IHP-Open-PDK PDK=ihp-sg13cmos5l`, then `make sim-xschem TB=<tb>` in `sah_12bit/`.
- **Cross-checks:**
  - The `.noise` result must match kT/C within 5 %.
  - ΔV·C must collapse onto one Q_inj(Vin) curve across the C sweep.
  - `sah_12bit`, set to today's switch sizes at 0.23 pF and 2.9 pF, must reproduce the existing trim TB numbers.
- **Final check:** a closed-loop transient of opamp → `sah_12bit` → comparator with the frozen sizes, at tt/ss/ff and −40/27/125 °C. Every deterministic error must be ≤ ¼ LSB, and the noise must fit the budget.
- **Out of scope** (can be done later on request): swapping `sah_12bit` into the top level, and layout.
