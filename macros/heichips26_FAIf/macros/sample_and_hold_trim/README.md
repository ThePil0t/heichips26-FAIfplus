# sample_and_hold_trim (ihp-sg13cmos5l)

Sample & hold with a 4-bit trimmable hold capacitor for the FAIf SAR ADC input. It runs from the analog supply (3.3 V, HV devices). The input `SH_IN` is driven by the `op_amp_ver_2` unity-gain buffer, and the output `SH_OUT` goes to the comparator, as in `../../schematic/xschem/heichips26_FAIf.sch`.

Status: schematic and testbenches only. There is no layout, DRC/LVS or PEX yet.

## Circuit

- Main switch: `aswitch` transmission gate (HV NMOS 4u/0.6u, PMOS 14u/0.6u, half-size dummies), with an inverter that generates `sw_b` from `SH_EN`.
- Fixed hold capacitor C1, plus four trim capacitors that `asw_inv` switches connect to `SH_OUT`.

| Pin | Dir | Function |
|---|---|---|
| `SH_IN` | in | Analog input (from the input buffer) |
| `SH_OUT` | out | Held voltage (to the comparator) |
| `SH_EN` | in | 1 = track, 0 = hold (3.3 V logic) |
| `cap_en[3:0]` | in | Trim bits, 1 = capacitor connected (3.3 V logic) |
| `VDD`, `VSS` | inout | Analog supply (VAPWR) and ground |

| Capacitor | cap_cmomi W × L (Metal1–3) | C (model, 1 MHz) | Enabled by |
|---|---|---|---|
| C1 | 12.5 × 25 µm | 0.231 pF | always |
| C2 | 12.5 × 25 µm | 0.231 pF | `cap_en[0]` |
| C3 | 25 × 25 µm | 0.480 pF | `cap_en[1]` |
| C4 | 50 × 25 µm | 0.978 pF | `cap_en[2]` |
| C5 | 50 × 25 µm | 0.978 pF | `cap_en[3]` |

The trim weights are 1:1:2:4:4 relative to C1, so the steps are not binary. With the switch parasitics included, the effective hold capacitance (TT, 27 °C) is:

| `cap_en` | Effective hold capacitance |
|---|---|
| 0 | 0.34–0.44 pF |
| 15 | 3.08–3.27 pF |

## Testbenches (`testbenches/xschem`)

| Testbench | What it measures |
|---|---|
| `sample_and_hold_trim_tb_tran` | Buffer + S&H + comparator load, 4 track/hold cycles (input 0.5 → 2.8 → 1.65 → 0.5 V, stepped in the middle of the hold). Per hold window: pedestal, droop, feedthrough, acquisition time to ½ LSB (8 bit) and tracking error, for `cap_en` = 0 and 15. |
| `sample_and_hold_trim_tb_vs_notrim` | Cost of the trim. Compares the trimmed S&H with the same switch and C1 only (`nmin`, vs. `cap_en`=0), and with C1–C5 hard-wired (`nmax`, vs. `cap_en`=15). Same transient measurements, plus the effective hold capacitance C(V) from an AC analysis. |

```sh
make sim-xschem                                         # sample_and_hold_trim_tb_tran, nominal TT / 27 C / 3.3 V
make sim-xschem TB=sample_and_hold_trim_tb_vs_notrim
make sim-xschem-pvt TB=<testbench>                      # every point of the PVT list
make sim-xschem-pvt TB=<testbench> PVT="ss:wcs:125:2.97 tt:typ:27:3.3"
make sim-all                                            # all of the above
python3 testbenches/xschem/plot_simulations/plot_sample_and_hold_trim.py [tran] [pvt] [vs_notrim]
```

- Results go to `testbenches/xschem/simulations/<testbench>[_<corner>_<temp>C_<vdd>V].{txt,raw}`. PVT runs also write `<testbench>_pvt.txt`. The folder is git-ignored.
- Figures go to `testbenches/xschem/plot_simulations/figures/`. Note that `make clean` also empties this folder.
- Default PVT points: SS/125 °C, FF/−40 °C and FF/125 °C, each at VDDA = 2.97 V and 3.63 V. A point is written `<mos corner>:<cap corner>:<temp>:<VDDA>`. `sim-xschem-pvt` replaces the `mos_tt` / `cap_typ` tokens of the PVT block and passes temperature, supply and file suffix with `ngspice -D`.
- Trim codes, temperatures and supplies can also be listed directly in the `codes` / `temps` / `vdds` lists of the NGSPICE block.

Solver settings: `method=gear reltol=1e-4 abstol=1e-15 gmin=1e-18`. A small `gmin` is needed because the droop is caused by pA leakage. `klu` is not used, because it stalls on the floating trim-capacitor nodes.

## Known limitations

- The `cap_cmomi` MOM-capacitor model is not yet validated on cmos5l silicon and has no corner or mismatch spread.
- Disabled trim capacitors are left floating. Their voltage depends on the history, which affects the droop at small `cap_en` codes. The design is intentionally left as is for now.
- All results are schematic-level (no layout parasitics). The opamp bias is an ideal 25 nA (the real one is PTAT).

The generic layout, DRC/LVS/PEX and view-export targets come from the HeiChips template (`make help`).
