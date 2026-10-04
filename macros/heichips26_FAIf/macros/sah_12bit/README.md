# sah_12bit — track & hold sized for 12 bit

Single-ended track & hold for the FAIf SAR ADC, re-sized from first principles for 12-bit accuracy: hold cap 1.21 pF
(`cap_cmomi` 59.63 × 25.2 µm, sized for a ±35 % cap spread), HV transmission gate 0.6/1.8 µm at L = 0.45 µm. It replaces
`sample_and_hold` pin for pin: `SH_IN`, `SH_OUT`, `SH_EN` (1 = track, 0 = hold), `VDD`, `VSS`.

The cell contains:
- an HV transmission gate with dummy switches;
- a buffered gate-driver chain, so every dummy switches after its main device and the switch edges don't depend on the slope of `SH_EN`;
- a MOM hold capacitor (`cap_cmomi`, Metal1–Metal3).

The sizing, the limits behind it and whether a trim array is worth it are covered in [docs/hold_cap_sizing.md](docs/hold_cap_sizing.md).
The plan is in [`../../../../sah_12bit_sizing_PLAN.md`](../../../../sah_12bit_sizing_PLAN.md).

## Files

| Path | Content |
|---|---|
| `schematic/xschem/sah_12bit.sch/.sym` | the cell, frozen sizes |
| `testbenches/xschem/sah_12bit_param.sch/.sym` | the same cell with size parameters, used by the sizing sweeps |
| `testbenches/xschem/cap_cmomi_lf.spice` | low-frequency `cap_cmomi` equivalent for the sweeps; same C equations, no RF branches, no GLEAK artifact |
| `testbenches/xschem/sah_12bit_ideal_tb_*.sch` | ideal-source testbenches: Ron, kT/C, pedestal/droop/feedthrough/acquisition |
| `testbenches/xschem/sah_12bit_opamp_tb_*.sch` | `op_amp_ver_2` follower as driver: loop gain, noise, static error, acquisition, pedestal |
| `testbenches/xschem/sah_12bit_kickback_tb_tran.sch` | `555_comparator` kickback during a 12-bit conversion |
| `testbenches/xschem/sah_12bit_trim_tb_tran.sch` | trimmed vs fixed hold cap |
| `testbenches/xschem/sah_12bit_final_tb_tran.sch` | final check of the frozen cell with the PDK cap model (PVT) |
| `testbenches/xschem/plot_simulations/data/` | archived result tables used by the sizing script |
| `scripts/sizing/cs_sizing.py` | evaluates all results against the 12-bit budget, writes `plot_simulations/figures/sah12_*.png` |
| `scripts/sizing/check_param_equiv.py` | checks that `sah_12bit_param` at its defaults is device-for-device the frozen cell |

## Running

Run these in the repository root's `nix-shell`, with `export PDK_ROOT=$PWD/IHP-Open-PDK PDK=ihp-sg13cmos5l`, from this folder:

```sh
make sim-xschem TB=sah_12bit_ideal_tb_tran        # one testbench, nominal
make sim-xschem-pvt TB=sah_12bit_ideal_tb_tran    # at the PVT points of the Makefile (PVT=...)
make sim-final                                    # final check: PVT x cap-spread points (PVT_FINAL)
python3 scripts/sizing/check_param_equiv.py      # param copy == frozen cell
make sizing                                       # evaluate plot_simulations/data -> figures
python3 scripts/sizing/cs_sizing.py --data testbenches/xschem/simulations   # evaluate the latest runs
```

Testbenches with many runs accept `ngspice -D run_sel=<n> -D pvt_tag=_r<n>`, so the run setups can be simulated in parallel.
Each testbench's header text lists its setups.
