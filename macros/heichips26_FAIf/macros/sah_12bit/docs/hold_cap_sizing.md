# sah_12bit: hold-capacitor sizing for 12 bit

This document sizes the hold capacitor of the FAIf track & hold from first principles for 12-bit performance, and with it the sampling switch, because the two cannot be sized separately. It covers:
- an ideal source (infinite drive);
- the real case, with `op_amp_ver_2` as the input buffer;
- whether a capacitor trim array is worth having.

Plan: [`sah_12bit_sizing_PLAN.md`](../../../../../sah_12bit_sizing_PLAN.md). All numbers come from the testbenches in `../testbenches/xschem/`. They are evaluated by `../scripts/sizing/cs_sizing.py` (`make sizing`), which prints the tables below and writes the figures `sah12_*.png` to `../testbenches/xschem/plot_simulations/figures/`.

## Result

| | Value |
|---|---|
| Hold cap C1 | `cap_cmomi` w 54.29 × l 27.72 µm (33 × 60 unit cells; the sweeps used the same 1980 cells as 59.63 × 25.2 µm), Metal1–Metal3: **1.21 pF**, 1.5k µm². All 12-bit limits hold at **−35 %** cap spread |
| Switch | HV transmission gate: NMOS **0.6/0.45 µm**, PMOS **1.8/0.45 µm** (2 fingers each); dummies one finger; buffered 4-inverter gate drive |
| Binding limit | comparator kickback (555_comparator INN): 157 µV at C −35 %, against the 201 µV budget |
| Next limit | sampled noise of the `op_amp_ver_2` follower: 184 µV (27 °C) to 218 µV (125 °C, C −35 %) rms, almost independent of C. It uses most of the 12-bit noise budget |
| Pedestal nonlinearity | ≤ 50 µV at every PVT point and both cap-spread points (budget 201 µV) |
| Acquisition with the follower, 25 nA | 1.2 µs at tt 27 °C, ≤ 2.4 µs over PVT × cap spread, for inputs within 0.5–3.2 V. ≈ 0.9 µs at 100 nA (falling steps), 0.37 µs (rising) |
| Input bandwidth | follower slew rate ≥ 0.25 V/µs → a full-scale sine (0.5–3.2 V) is limited to ≈ 29 kHz, whatever C is |
| Hold time (droop ≤ ¼ LSB, C −35 %) | ≥ 7.6 µs up to 85 °C, ≥ 1.8 µs up to 125 °C. A 12-bit conversion holds for 13 SAR clocks, so the SAR clock must be ≥ 1.7 MHz (85 °C) or ≥ 7.3 MHz (125 °C) |
| Speed with an ideal source | charge injection limits the switch time constant to τ ≥ 1.5 ns, i.e. t_track ≥ 15 ns |
| Trim array | **not recommended**. A fixed C with spread margin is cheaper and adds no error (section 7) |

Two findings matter beyond the capacitor value:
- **Today's switch is far too wide.** `aswitch` (4/14 µm, "1 kΩ") is about 7× too wide for 12 bit with the follower as driver. Its pedestal nonlinearity is 3.2 mV, against a 0.2 mV budget.
- **Its dummies switch at the wrong moment.** The PMOS dummy turns on before the main PMOS turns off, and the NMOS gate sees the raw SH_EN slope. The buffered gate-driver chain of `sah_12bit` fixes both.

## 1. Budget

- **LSB:** full scale 3.3 V (the DAC reference), so **LSB = 806 µV**. Quantization noise q = LSB/√12 = **233 µV** rms.
- **Noise:** total S&H noise σ ≤ q, which costs ≤ 3 dB of SNR (about 0.5 bit). kT/C is given half of that power (σ_kTC ≤ 165 µV); the rest is for follower, comparator and DAC.
- **Deterministic errors:** each of these must stay ≤ **¼ LSB = 201 µV** at the worst input level, temperature (−40/27/125 °C) and corner: settling, the nonlinear part of the pedestal, droop over the hold time, comparator kickback and hold feedthrough.
- **Offset and gain:** the constant and linear parts of the pedestal and of the follower error are reported but not counted. They are calibratable and do not affect INL.
- **Capacitor spread ±35 %:** the `cap_cmomi` model has no process spread (typ = bcs = wcs) and no mismatch, so ±35 % is assumed as a lower bound until IHP data exist.
  - Accuracy limits must hold at C × 0.65, speed limits at C × 1.35.
  - About 0.05 pF of switch, comparator and routing parasitics is counted without spread.

## 2. What limits accuracy and speed

| Mechanism | Scales with | Ideal source | With `op_amp_ver_2` |
|---|---|---|---|
| kT/C noise | 1/C | C ≥ 0.20 pF (125 °C) | same, but swamped by the follower noise |
| Follower noise sampled on C | follower bandwidth (its Miller caps) | – | 175–244 µV, nearly C-independent → C_eff ≥ 0.46 pF at 125 °C |
| Charge injection, nonlinear part | switch W, gate drive, source impedance; at fixed τ independent of C | NL ∝ τ^-2 → τ ≥ 1.5 ns | small switch: ≤ 50 µV over PVT |
| Comparator kickback | Q_kb/C | – | **binding**: 0.14 fC → C_eff ≥ 0.71 pF |
| Droop (junction leakage) | I_leak·t_hold/C | < 1 pA at 27 °C, 20–90 pA at 125 °C | same; limits the hold time and therefore the SAR clock at high temperature |
| Hold feedthrough | C_ds,off/C | < −116 dB | not limiting |
| Settling (acquisition) | Ron·C (ideal) or the follower | 9.7·Ron·C | follower-limited, weak C dependence |
| Follower stability with C as load | output pole gm_out/C | – | phase margin 64–76° up to 16 pF: **no limit** |
| Follower slew rate | I_tail/Cc | – | limits the input bandwidth, not C |
| Follower static error | loop gain | – | offset 0.12–2.3 mV, gain error ≈ 20 ppm, nonlinearity ≤ 86 µV |

## 3. Case A: ideal source (infinite drive strength)

Testbenches `sah_12bit_ideal_tb_{dc,tran,noise}`. VIN is a 0 Ω source directly at SH_IN; the comparator gate is modelled as 20 fF.

- **kT/C.** The `.noise` result matches kT/C_eff within 1–4 % at 1 and 4 pF. At 0.3 pF the match is within 5–11 %, because C_eff from the AC admittance includes the switch channel capacitance.
- **Ron** (figure `sah12_1_ron.png`):
  - Today's switch: 480–950 Ω at 27 °C, up to 1.2 kΩ at 125 °C. Ron·W_N ≈ 3.8 kΩ·µm at L = 0.6 µm and 2.6 kΩ·µm at L = 0.45 µm.
  - Frozen 0.6/1.8 µm switch: ≤ 4.6 kΩ (27 °C) and ≤ 5.5 kΩ (125 °C). Its tail time constant at 1.21 pF is 3.4 ns.
- **The pedestal fix** (figure `sah12_2_pedestal_ideal.png`):
  - With today's switch the pedestal is 1.4–18 mV, with a 6–8 mV bow at 1 pF, and it depends strongly on the SH_EN edge time.
  - The PMOS dummy is driven by SH_EN and turns on *before* the main PMOS (driven by the inverted SH_EN) turns off, so it cancels nothing.
  - The buffered driver chain SH_EN → I1 → I2 (sw) → I3 (sw_b) → I4 (sw_d) switches the main NMOS first, then the main PMOS and the NMOS dummies, then the PMOS dummies. This reduced the pedestal by 3–50× and made it independent of the SH_EN slope: 2.4 vs 1.9 mV at 0.1 V for 5 ns vs 1 ns edges, where the old cell changed by 6 mV.
- **Speed versus charge injection.**
  - Scaling the switch with C at a constant time constant gives the same pedestal: 1.59 mV at 4 pF with a 4× switch, vs 1.57 mV at 1 pF with a 1× switch. So with an ideal source the injection error is set by the **track time, not by C**.
  - For one switch shape (WP/WN = 3.5, half-size dummies) the nonlinear pedestal follows NL ≈ 0.46 mV·(τ/ns)^-2.
  - ¼ LSB therefore needs **τ ≥ 1.5 ns**, i.e. **t_track ≥ 15 ns** for a full-scale step (9.7 τ).
  - C itself is then only bounded by kT/C (0.2 pF), by kickback and by droop.
  - The frozen small switch is far below this limit (NL 7–16 µV, τ = 2.3–3.4 ns).
- **Droop** (figure `sah12_9_leakage.png`, frozen switch, C −35 %):
  - The hold-node leakage is below 1 pA at 27 °C, 1–22 pA at 85 °C and 23–92 pA at 125 °C, highest at ff and 3.63 V.
  - An operating-point breakdown at 125 °C shows the source: the p+/n-well junctions of the main PMOS (16–21 pA) and of the hold-side PMOS dummy (12 pA), reverse-biased by VDD − V_hold. The off-channel adds 4–5 pA when the input sits at the opposite rail; the NMOS side contributes ≤ 3 pA.
  - Held for ¼ LSB, this allows t_hold ≥ 7.6 µs up to 85 °C and ≥ 1.8 µs up to 125 °C.
  - The PDK `cap_cmomi` model adds a 1 TΩ GLEAK from each terminal to ground (up to 3.3 pA). That is a model artifact, so the sweeps use `cap_cmomi_lf.spice` (same capacitance equations, no RF branches, no GLEAK), and the final check subtracts it.
- **Hold feedthrough** is below −116 dB.

## 4. Case B: `op_amp_ver_2` follower as the buffer

Testbenches `sah_12bit_opamp_tb_{ac,noise,dc,tran,ped}`, with the real `555_comparator` on SH_OUT and IBIAS = 25 nA (50/100 nA for comparison).

- **Stability** (figure `sah12_4_opamp_loopgain.png`): UGF 0.4–0.6 MHz, DC loop gain 104–141 dB, phase margin 85° unloaded and still 64–76° with 16 pF. The hold cap does not destabilize the follower, contrary to the hand estimate in the plan.
- **Noise** (figure `sah12_5_noise.png`):
  - The follower noise frozen on C is 175–210 µV at 27 °C and 202–244 µV at 125 °C. It barely depends on C between 0.26 and 4 pF, or on the bias; the 1/f part (1 Hz–1 kHz) is about 60 µV.
  - At 1.21 pF: 184 µV (27 °C) and 212 µV (125 °C); at −35 %: 218 µV.
  - Together with quantization this is a 2.1–2.7 dB SNR loss (0.35–0.45 bit), leaving only about 90 µV rms for comparator and DAC noise at 125 °C.
  - More noise margin would need a lower-bandwidth follower (larger Miller caps), not a larger hold cap.
- **Static error** (figure `sah12_6_follower_dc.png`):
  - offset 0.12–0.15 mV at −40/27 °C, up to 2.3 mV at 125 °C and 100 nA;
  - gain error ≈ 20 ppm, nonlinearity ≤ 86 µV over 0.5–3.1 V;
  - the follower output floor (≈ 0.39 V) sets the lower end of the input range.
- **Acquisition** (figure `sah12_7_acquisition_opamp.png`):
  - The previous sample is replaced through the class-AB output's local Miller loop, so the settling to ¼ LSB is set by the follower, not by Ron·C.
  - t_acq to ¼ LSB, worst of the 0.5→2.8 V and 2.8→0.5 V steps, tt 27 °C:

    | IBIAS | C −35 % (0.79 pF) | 1.21 pF | C +35 % (1.64 pF) |
    |---|---|---|---|
    | 25 nA | 1.15 µs | 1.21 µs | 1.28 µs |
    | 50 nA | 0.94 µs | 1.00 µs | 1.05 µs |
    | 100 nA | 0.84 µs | 0.90 µs | 0.95 µs |

  - Rising steps settle faster with more bias (0.34–0.39 µs at 100 nA); falling steps toward 0.5 V do not.
- **Switch sizing with the follower** (figure `sah12_3_pedestal_opamp.png`).
  - The follower's high-frequency output impedance changes how the channel charge splits, compared with an ideal source.
  - Ron·C (3.4 ns) is negligible against the µs-class acquisition, so the switch can be made small. The nonlinear pedestal at 1 pF falls steeply with switch width:

    | Switch | Nonlinearity at 1 pF |
    |---|---|
    | 4/14 µm (today) | 3.2 mV |
    | 2/7 µm | 0.9 mV |
    | 1/3.5 µm | 0.2 mV |
    | 0.6/1.8 µm (frozen) | 0.045 mV |

  - Moving the dummy fractions away from one finger (KD = 0.5) made it worse.
  - Over 9 PVT points the frozen 0.6/1.8 µm switch stays ≤ 0.049 mV at 1 pF.
- **Comparator kickback** (testbench `sah_12bit_kickback_tb_tran`, figure `sah12_8_kickback.png`):
  - The DAC drives INP as in `sar.vhdl`: the previous result during track, 0 in the first hold cycle, then the 12 binary-search trials.
  - The held voltage moves by up to 0.14 fC/C: 466 µV at 0.26 pF, 157 µV at 0.79 pF (= 1.21 pF −35 %), 103 µV at 1.21 pF, 62 µV at 2 pF.
  - It is worst when the previous result was far from the new sample.

## 5. Choosing C (with ±35 % spread)

| Mechanism | C_eff,min | Drawn C_nom required (−35 %, +0.05 pF unscaled) | Margin of 1.21 pF at −35 % |
|---|---|---|---|
| Comparator kickback | 0.71 pF | **1.02 pF** | ×1.18 (simulated: 157 µV = 78 % of the budget) |
| Follower + switch noise ≤ q (125 °C, 25 nA) | 0.46 pF | 0.64 pF | ×1.81 |
| Pedestal nonlinearity (follower drive) | 0.21 pF | 0.25 pF | ×3.95 |
| kT/C share of the noise budget (125 °C) | 0.20 pF | 0.24 pF | ×4.14 |

- **Choice: 1.21 pF.** At −35 % (0.79 pF drawn + 0.05 pF) every accuracy limit holds. At +35 % (1.64 pF) the follower acquisition grows only from 1.21 to 1.28 µs (tt) and the follower stays stable.
- **Cost:** 1.5k µm² instead of 1.23k µm² for today's C1.
- **Without the spread rule,** about 0.75 pF would be enough.
- **A larger C would not buy much.** Noise is follower-limited, and droop scales only with 1/C, so even 2× C would leave the 125 °C hold-time limit at a few µs.

## 6. Final check: frozen cell, PDK cap model, PVT × cap spread

Testbench `sah_12bit_final_tb_tran`, run with `make sim-final` (`PVT_FINAL` in the Makefile; figure `sah12_10_final_check.png`).
- **Setup:** follower (25 nA) → `sah_12bit` → `555_comparator`, all with the PDK `cap_cmomi` model.
- **Steps:** 0.5↔2.8 V, 1.6→1.7 V and 3.2→0.45 V.
- **Cap spread:** set by the cap corner (wcs = −35 %, bcs = +35 %).
- **Netlist equivalence:** `scripts/sizing/check_param_equiv.py` confirms that the parametrized copy used here is device-for-device identical to the frozen schematic.

| Corner | C | T | VDDA | Pedestal NL | Droop (GLEAK removed) → t_hold | Slew rate | t_acq, 0.5–3.2 V | t_acq, step to 0.45 V |
|---|---|---|---|---|---|---|---|---|
| tt | 1.21 pF | 27 °C | 3.3 V | 34 µV | 0.09 mV/ms → 2.4 ms | 0.260 V/µs | 1.22 µs | 2.4 µs |
| tt | 0.79 pF | 125 °C | 3.3 V | 46 µV | 29 mV/ms → 6.9 µs | 0.253 V/µs | 1.40 µs | 1.2 µs |
| tt | 0.79 pF | −40 °C | 3.3 V | 41 µV | 0.17 mV/ms → 1.2 ms | 0.269 V/µs | 2.37 µs | 10.4 µs |
| tt | 1.64 pF | 125 °C | 3.3 V | 27 µV | 14 mV/ms → 14 µs | 0.253 V/µs | 1.59 µs | 1.3 µs |
| ss | 0.79 pF | 125 °C | 2.97 V | 50 µV | 25 mV/ms → 8.0 µs | 0.248 V/µs | 1.61 µs | 2.3 µs |
| ss | 1.64 pF | 125 °C | 2.97 V | 22 µV | 12 mV/ms → 16 µs | 0.248 V/µs | 1.79 µs | 2.5 µs |
| ff | 0.79 pF | −40 °C | 3.63 V | 28 µV | 1.4 mV/ms → 141 µs | 0.280 V/µs | 0.92 µs | 1.2 µs |
| ff | 0.79 pF | 125 °C | 3.63 V | 37 µV | 54 mV/ms → 3.8 µs | 0.260 V/µs | 1.28 µs | 0.75 µs |
| sf | 0.79 pF | 27 °C | 3.3 V | 50 µV | 0.41 mV/ms → 0.49 ms | 0.259 V/µs | 1.80 µs | 4.6 µs |
| fs | 0.79 pF | 27 °C | 3.3 V | 41 µV | 0.19 mV/ms → 1.0 ms | 0.260 V/µs | 1.13 µs | 1.3 µs |

- **Pedestal:** passes everywhere with ≥ 4× margin.
- **Static error:** 0.15–0.5 mV, and up to 1.6 mV at ff 125 °C (offset, calibratable).
- **Steps ending at 0.45 V settle slowly at −40 °C/sf.** The follower is close to its output floor there, so the specified input range for full-speed 12-bit operation is **0.5–3.2 V**.
- **Droop:** this check (input at the opposite rail during hold, PDK model with GLEAK removed) agrees with section 3. The 125 °C hold time is a few µs.

## 7. Should the hold cap be trimmed?

Testbench `sah_12bit_trim_tb_tran` compares two cells, each driven by its own follower:
- `sah_12bit` with a 0.5 pF base cap plus a binary trim array (0.13/0.26/0.50/0.99 pF, each behind an `asw_inv` switch as in `sample_and_hold_trim`);
- `sah_12bit` with a fixed cap of the same total value.

| | 27 °C | 125 °C |
|---|---|---|
| Hold-node leakage, trimmed / fixed | ×26 … ×57 (1.7–3.8 vs 0.03–0.14 mV/ms) | ×29 … ×58 (570–1315 vs 10–45 mV/ms) |
| Pedestal shift trimmed vs fixed | ≤ 0.07 mV | ≤ 0.23 mV |
| Acquisition, trimmed − fixed | +16 … +24 ns | +24 … +67 ns |

**Verdict: no trim array.**
- **C is not a ratio here.** The hold cap is not part of a capacitive DAC, so its value does not enter the transfer function. A wrong C only scales the 1/C errors (kickback, droop, kT/C, pedestal). Trimming corrects no error; it only moves the accuracy/speed point.
- **Margin is cheap.** The process spread (±35 % assumed) is covered by sizing for −35 %. That costs only area (+0.3k µm² here), because the follower-limited acquisition hardly depends on C.
- **The array adds the dominant error.** Its switches hang their junctions and dummies on the hold node. With the existing `asw_inv` (4/14 µm) cells this raises the leakage by 26–58×, and at 125 °C leakage already limits the hold time. Minimal-size trim switches would still at least double it.
- **It cannot be set.** Re-centering C would need an on-chip way to measure C, and this system has none. The existing `sample_and_hold_trim` codes are also non-monotonic (C4 = C5).
- **Better alternative:** if a speed/accuracy setting is wanted (the eFPGA clock is still open), make the SAR track time programmable (the prescaler already in TAPEOUT_PLAN). That gives the same flexibility with no analog cost.
- **If a trim is kept anyway:** put the switches at the cap's bottom plate (NMOS to VSS), so they are not on the hold node, and use binary weights.

## 8. Caveats and open points

- **Cap spread:** ±35 % is an assumption. The `cap_cmomi` model is transferred from SG13G2, is not validated on cmos5l silicon, and has no spread, mismatch, TC or VC.
- **High-temperature hold time.** At 125 °C 12-bit accuracy needs a short hold (≤ 1.8 µs, i.e. SAR clock ≥ 7.3 MHz). The 100 nA comparator and the R-2R DAC settling at that speed were not checked. If they cannot keep up, the options are:
  - restrict 12-bit operation to ≤ 85 °C (hold ≤ 7.6 µs);
  - raise C (the hold time scales with C);
  - reduce the PMOS junction area on the hold node.
- **Bias:** the follower bias was an ideal 25 nA source. The PTAT block (`iIREF1`) was not simulated, and its spread changes acquisition time and noise.
- **Comparator and DAC noise** were not simulated. The budget leaves them only about 90 µV rms at 125 °C.
- **Layout (done 2026-10-09, floorplan v4, see the README):** the post-layout netlist adds about 0.2 pF on SH_OUT (shield box 196 fF, wiring 3 fF) instead of the CPAR = 0.05 pF assumed here. That helps kickback (125 µV at C −35 %) and kT/C, and slows acquisition by 2–5 %. Pedestal nonlinearity stays ≤ 72 µV, and the leakage droop drops by 15–22 % because the hold-node junctions are smaller. Hold feedthrough rises to −72 dB (−69 dB at C −35 %), because of the switch's own S/D strap coupling (0.35 fF in total).
- **Input range:** 0.5–3.2 V for full-speed 12-bit operation.
- **Offset:** the follower offset at 125 °C reaches 1.6–2.3 mV (calibratable, not INL).
- **Integration:** `sah_12bit` is pin-compatible with `sample_and_hold` but not yet instantiated in the top level.

## 9. Reproducing

```sh
nix-shell                                     # repository root
export PDK_ROOT=$PWD/IHP-Open-PDK PDK=ihp-sg13cmos5l
cd macros/heichips26_FAIf/macros/sah_12bit
make sim-all                                  # all testbenches (a few hours on 16 cores)
python3 scripts/sizing/check_param_equiv.py   # param copy == frozen cell
make sizing                                   # tables in plot_simulations/data -> printout + figures
```

The archived tables in `plot_simulations/data/` are the ones behind this document. The `*_sw4x14.txt` and `*_v1.txt` files hold the runs with today's switch and the first cell version, for comparison.
