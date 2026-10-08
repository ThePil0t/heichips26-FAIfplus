# sah_12bit — track & hold sized for 12 bit

Single-ended track & hold for the FAIf SAR ADC, re-sized from first principles for 12-bit accuracy: hold cap 1.21 pF
(`cap_cmomi` w 54.29 × l 27.72 µm = 33 × 60 unit cells, sized for a ±35 % cap spread), HV transmission gate 0.6/1.8 µm at L = 0.45 µm. It replaces
`sample_and_hold` pin for pin: `SH_IN`, `SH_OUT`, `SH_EN` (1 = track, 0 = hold), `VDD`, `VSS`.

The cell contains:
- an HV transmission gate with dummy switches;
- a buffered gate-driver chain, so every dummy switches after its main device and the switch edges don't depend on the slope of `SH_EN`;
- a MOM hold capacitor (`cap_cmomi`, Metal1–Metal3).

The sizing, the limits behind it and whether a trim array is worth it are covered in [docs/hold_cap_sizing.md](docs/hold_cap_sizing.md).
The plan is in [`../../../../sah_12bit_sizing_PLAN.md`](../../../../sah_12bit_sizing_PLAN.md); the layout plan in [`../../../../sah_12bit_layout_PLAN.md`](../../../../sah_12bit_layout_PLAN.md).

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
| `layout/sah_12bit.gds` | the layout (top cell `sah_12bit`), generated, do not edit by hand |
| `scripts/layout/gen_sah_12bit_layout.py` | layout generator (PDK PCells + drawn wiring, taps, shield, pins) |
| `scripts/layout/hybrid_pex.py` | builds the post-layout netlist `netlist/pex/sah_12bit_hybrid_pex.spice` |

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

Layout, verification and post-layout simulation:

```sh
python3 scripts/layout/gen_sah_12bit_layout.py   # layout/sah_12bit.gds
make klayout-drc DRC_LEVEL=regular               # sign-off DRC: only the cell-level density rules remain
make magic-drc
make klayout-lvs                                 # sign-off LVS: match, C1 extracted as cap_cmomi
make magic-lvs                                   # differs only by C1 (Magic has no cap_cmomi extraction)
python3 scripts/layout/hybrid_pex.py             # post-layout netlist (after make klayout-lvs)
make sim-final-pex                               # final check with the post-layout netlist (PVT_FINAL)
make sim-pex-pvt TB=<testbench> PVT="..."         # any testbench that uses sah_12bit_param
```

Testbenches with many runs accept `ngspice -D run_sel=<n> -D pvt_tag=_r<n>`, so the run setups can be simulated in parallel.
Each testbench's header text lists its setups.

## Layout

Cell 81.5 × 62.5 µm. In `analogue_interface` it sits at (185.5, 46), between the input buffer `op_amp_ver_2` (x8, below) and the comparator `555_comparator` (x1, above).

```
 y=62.5 ┌ SH_OUT ─ VSS (top-edge pins at x 20.3 / 21.2) ───────────────────────────────────────────┐
 SH_EN ▶│ gate driver I1..I4 │ transmission gate │═ SH_OUT coax ═▶│PLUS│ C1 (33 × 60 cells)   │MINUS│
  VDD  ▶│ (NMOS row / PMOS)  │ PMOS / NMOS strip │ (M2 in M1/M3   │pad │ poly floor, M1–M3    │= VSS│
        │                    │                   │  VSS + rails)  │    │ fence, Metal4 lid    │     │
        │  SH_IN run (Metal3, shielded by distance from SH_EN/SH_OUT)                            │
 y=0    └ SH_IN (bottom-left, x 1.5) ─────────────────────────────────────────────────────────────┘
          x=0                                                     x≈50 ← straps at macro 222–229 | 272–279 →
```

**Pins** (Metal3, cell coordinates): `SH_IN` bottom edge x 1.5; `SH_EN` west edge y 59.1; `VDD` west edge y 56.15;
`SH_OUT` top edge x 20.3; `VSS` top edge x 21.2. In the macro, `SH_OUT` is straight below the comparator INN pad (x 205.8)
and `SH_IN` straight above the opamp's OOA exit (x 187).

**Hold cap and shield.**
- C1 is reshaped to 33 × 60 unit cells (w 54.29 µm × l 27.72 µm, marker 29.5 × 54.9 µm). It has exactly the same capacitance
  as the 30 × 66 cells (59.63 × 25.2 µm) used in the sizing study (1213.8 fF from the PCell/model formula), but it fits into the
  gap between two groups of top-level Metal4 PDN straps: 6.7 µm from the cap to the straps on both sides.
- Closed VSS box: a GatPoly floor under the whole cap, an M1–M3 fence with Via1/Via2 rows and a p-tap ring around it, and a
  **Metal4 lid** (29.98 µm wide: the slit rule Slt.c allows 30 µm without slits) tied down through Via3 on the fence and on the
  MINUS pad. The lid is 6.5 µm from the PDN straps. Metal4 is otherwise forbidden in the analog macro; this lid is the one
  exception, and the macro LEF obstructs Metal4 over it (+1 µm) so no top-level route can cross it.
- Shield net = **VSS**, the same node as the MINUS plate: shield-to-PLUS coupling only adds hold capacitance against the
  reference, and ground noise is common to the shield and MINUS. VAPWR would inject supply ripple, VPWR digital noise, and a
  floating shield does not shield.
- The cap's feed pads are solid on Metal3 only, so SH_OUT enters the PLUS pad on Metal3 through a gap in the Metal3 fence;
  no Via3 sits on that gap. No other `.pin` shape may lie inside the cap marker (the KLayout LVS needs exactly two).

**Transmission gate.** One 4-finger strip per polarity, `[SH_IN] D1 [SH_IN] M [SH_OUT] D2 [SH_OUT] M [SH_IN]`, so the hold node
has two shared inner diffusions per polarity. Extracted hold-node junctions: PMOS 0.68 µm² / 5.1 µm, NMOS 0.23 µm² / 2.7 µm,
against 1.22 µm² / 9.9 µm and 0.41 µm² / 5.1 µm with the model defaults used in the sizing sims. The SH_OUT diffusions of the
two strips face each other; SH_IN and the main gates are wired on the outer sides, the dummy gates on the inner side.

**Grounds.** The driver ground and the quiet ground (cap MINUS, shield, coax, the gate's NMOS body tap) meet only at the
`VSS` pin, so the driver's current at the sampling edge does not flow through the hold-cap reference.

### Verification (2026-10-08)

| Check | Result |
|---|---|
| KLayout DRC, regular (sign-off) | only the cell-level density rules AFil.g, M1.j–M4.j, TM1.c |
| Magic DRC | 0 |
| KLayout LVS (sign-off) | match; C1 extracted as `cap_cmomi` between SH_OUT and VSS |
| Magic + Netgen LVS | 14 vs 15 devices: Magic cannot extract `cap_cmomi`. Without C1 in the netlist: "Circuits match uniquely" (only `mm_ok` property notes) |
| Macro `analogue_interface`, KLayout DRC regular | only the global density rules |
| Chip (LibreLane, RUN_2026-10-08_14-05-39) | KLayout DRC 0, LVS clean, antenna 0, setup/hold met, IR drop unchanged; no top-level Metal4 within 5.5 µm of the lid |

LibreLane's PDN generator trims the Metal4 straps closest to the lid obstruction (within ≈ 9 µm): over the S&H only the
outer straps of the two groups remain. All power nets stay connected and the IR drop is unchanged.

### Post-layout results

Neither extractor handles the MOM cap on its own (Magic has no `cap_cmomi` device; it reads the fingers as 1.48 pF of wire
coupling and books their area as junction area). `scripts/layout/hybrid_pex.py` therefore combines the PDK C1 model, the
KLayout junction areas and the Magic wire parasitics of the layout without the cap (see the script header).

| Quantity | Post-layout | Sizing assumption |
|---|---|---|
| Extra C on SH_OUT to VSS | 14 fF wiring + 196 fF cap environment (poly floor, lid, fence) = 0.21 pF | CPAR = 0.05 pF |
| C(SH_IN, SH_OUT) | 0.36 fF (0.19 fF from the facing S/D straps of the gate itself) | device model only |
| Hold feedthrough | −72 dB (nominal C), −69 dB (C −35 %) | −116 dB (schematic) |
| Pedestal nonlinearity, PVT × cap spread | ≤ 86 µV (worst ff −40 °C, C −35 %), budget 201 µV | ≤ 50 µV |
| Leakage droop, 125 °C (step 1.6 → 1.7 V) | 9.8–17.9 mV/ms | 12.7–23.1 mV/ms |
| Acquisition 0.5–3.2 V to ¼ LSB | +2…5 % (worst ss 125 °C +35 %: 1.82 µs) | 1.78 µs |
| Comparator kickback, tt 27 °C | 125 µV at C −35 %, 88 µV nominal (budget 201 µV) | 157 µV / 103 µV |

**Hold feedthrough is the one figure the layout made worse.** The coupling sits mostly in the switch's own S/D straps,
which face each other across the main gates; moving routing does not remove it (checked). An input that moves by the full
scale during the hold shifts the held value by 0.8 mV (nominal C) to 1.2 mV (C −35 %): about 1–1.5 LSB at 12 bit, about 0.1 LSB
for the 8-bit ADC, negligible for slowly varying inputs. If 12 bit at high input slew is needed later, a T-switch
(series–shunt–series) is the circuit fix.

The `droop` column of `sah_12bit_final_tb_tran` starts 5 µs after the input step, while the 25 nA follower is still slewing
(≈ 9 µs for 2.3 V). Post-layout it therefore contains the feedthrough of the rest of the step; use the 1.6 → 1.7 V step for
the leakage droop.
