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

Floorplan v4 (2026-10-09). Cell 43.0 × 67.0 µm.
In `analogue_interface` it sits at (179.2, 45.5), between the input buffer `op_amp_ver_2` (x8, below) and the
comparator `555_comparator` (x1, at (180.63, 115.5), above). Cell coordinates below; add (179.2, 45.5) for the macro.

```
 y=67.0 ┌──── SH_OUT (x 12.23) ─ VSS (x 13.23) ── top-edge pins ── SH_IN run (Metal3, y 66.75) ────────────▶ SH_IN
        │            ║ │ ║ TG (mirrored)  │ T-switch room    │ driver I1..I4 (row) │ +2 inv │  (east edge, y 66.75)
        │            ║ │ ║ x 14.2–19.8    │ x ≈ 20–27        │ x 27.4–36.8         │ rsv    │
 y≈57.6 │            ║ │ ║ (SH_EN/VDD on Metal1 along the bottom of the head, under a Metal2 VSS plate at the spine)
        │ west strip ┌─┴PLUS───────────────────────────────────────────────────────MINUS┐
 SH_EN ▶│ SH_EN/VDD  │ C1 33 × 60 cells, GatPoly floor, M1–M3 fence + p-tap ring,       │
  VDD  ▶│ Metal1     │ Metal4 lid (x 11.68–41.66)                                        │
        │ risers     │                                                                   │
 y=0    └────────────└───────────────────────────────────────────────────────────────────┘
          x=0          x≈10.7 (fence)                                                      x=43.0
```

**Pins** (Metal3, cell coordinates):
- `SH_IN`: east edge, y 66.75 (macro (222.2, 112.25)). The macro route to the opamp is done by hand on the east side of the S&H (corridor macro x 222.2–232), far from the DAC routes on the west.
- `SH_EN`: west edge, y 38.37 (macro 83.9).
- `VDD`: west edge, y 46.0 (macro 91.5).
- `SH_OUT`: top edge, x 12.23 (macro 191.43, straight below the comparator INN).
- `VSS`: top edge, x 13.23 (macro 192.43, below the comparator's GNDA).

**Hold cap and shield.**
- **Shape:** C1 is reshaped to 33 × 60 unit cells (w 54.29 µm × l 27.72 µm, marker 29.5 × 54.9 µm). This gives exactly the same capacitance as the 30 × 66 cells (59.63 × 25.2 µm) of the sizing study: 1213.8 fF from the PCell/model formula.
- **Shield box:** closed VSS box made of
  - a GatPoly floor under the whole cap;
  - an M1–M3 fence with Via1/Via2 rows and a p-tap ring around the cap;
  - a **Metal4 lid** tied down through Via3 on the top and bottom fence and on the MINUS pad. It is 29.98 µm wide, because the slit rule Slt.c allows 30 µm without slits.
- **Metal4 exception and strap clearance:** Metal4 is otherwise forbidden in the analog macro, and the macro LEF obstructs Metal4 over the lid + 1 µm. LibreLane removes Metal4 PDN straps within `PDN_HORIZONTAL_HALO` = 10 µm of an obstruction. The obstruction keeps 10.5 µm from the west strap group (macro x 172.38–179.38), so that group stays intact; the east group is cut over the S&H.
- **Shield net = VSS**, the same node as the MINUS plate:
  - shield-to-PLUS coupling only adds hold capacitance against the reference;
  - ground noise is common to the shield and MINUS;
  - VAPWR would inject supply ripple, VPWR would add digital noise, and a floating shield does not shield.
- **SH_OUT spine:** the cap's feed pads are solid on Metal3 only. The spine therefore leaves the top of the PLUS pad on Metal3 through a gap in the Metal3 fence, with no Via3 on that gap, and runs straight to the pin between two VSS walls. The gate's SH_OUT trunk joins it from the east.
- **LVS constraint:** no other `.pin` shape may lie inside the cap marker; the KLayout LVS needs exactly two.

**Switch head** (on top of the cap, east of the SH_OUT spine):
- **Transmission gate:** one 4-finger strip per polarity, `[SH_IN] D1 [SH_IN] M [SH_OUT] D2 [SH_OUT] M [SH_IN]`, placed mirrored so its SH_OUT trunk runs straight west into the spine (no stub, no tap line).
  - The hold node therefore has two shared inner diffusions per polarity.
  - Extracted hold-node junctions: PMOS 0.68 µm² / 5.1 µm, NMOS 0.23 µm² / 2.7 µm. The sizing sims used the model defaults, 1.22 µm² / 9.9 µm and 0.41 µm² / 5.1 µm.
- **T-switch room:** ≈ 7 × 8 µm between the gate and the driver, on the SH_IN side. A series switch and a shunt fit there without moving the spine, the cap or the comparator.
- **Gate driver I1..I4:** a row, mirrored, east of the T-switch room, with room for 2 more inverters (shunt phase) at its east end. Its outputs reach the gate's east side on Metal2 (with short Metal3 risers where two lines would meet); none crosses the spine.
- **SH_EN and VDD** come in on the west edge (same pins as v2b), rise in the west strip on Metal1 and run east along the bottom of the head, under a Metal2 VSS plate where they cross the spine.
- **SH_IN:** from the gate's SH_IN joiner up to the top edge and east to the pin on Metal3, above the gate and the driver. SH_IN, SH_OUT, SH_EN and the gate lines don't cross anywhere.

**Grounds.** The driver ground (its VSS rail, Metal2 along the top edge to the east spine wall) and the quiet ground meet only at the `VSS` pin. The quiet ground is the cap MINUS, the shield box, the spine walls, the Metal2 plate and the gate's NMOS body tap. This keeps the driver's current at the sampling edge out of the hold-cap reference.

### Verification (2026-10-09, floorplan v4)

| Check | Result |
|---|---|
| KLayout DRC, regular (sign-off) | only the cell-level global density rules AFil.g, M1.j, M2.j, TM1.c |
| Magic DRC | 0 |
| KLayout LVS (sign-off) | match; C1 extracted as `cap_cmomi` between SH_OUT and VSS |
| Magic + Netgen LVS | 14 vs 15 devices: Magic cannot extract `cap_cmomi`. Without C1 in the netlist: "Circuits match uniquely" (only `mm_ok` property notes) |
| Macro `analogue_interface`, KLayout DRC regular | only the global density rules; builder routing check (DAC path) OK |
| Chip (LibreLane, RUN_2026-10-09_01-12-07) | KLayout DRC 0, LVS clean, antenna 0, setup/hold met, no power-grid violations, IR drop unchanged. Magic DRC (not run in the earlier chip runs) reports 1248 latch-up/well/tap findings in other blocks, none in the S&H |
| Metal4 PDN straps | west group (macro x 172.38–179.38) intact over the whole macro; east group (222.38–229.38) cut over the S&H; no top-level route near the lid |

### Post-layout results (v4)

Neither extractor handles the MOM cap on its own. Magic has no `cap_cmomi` device: it reads the fingers as 1.48 pF of wire coupling and books their area as junction area. `scripts/layout/hybrid_pex.py` therefore combines:
- the PDK C1 model;
- the KLayout junction areas;
- the Magic wire parasitics of the layout without the cap and its shield box.

See the script header for details. `make sim-final-pex` runs the final check with this netlist. The results are archived in `testbenches/xschem/plot_simulations/data/*_pex*.txt`.

| Quantity | Post-layout v4 | v2b (7c28bb3) | Sizing / schematic |
|---|---|---|---|
| Extra C on SH_OUT to VSS | 3 fF wiring + 196 fF cap environment (poly floor, lid, fence) | same | CPAR = 0.05 pF |
| C(SH_IN, SH_OUT) | 0.35 fF, mostly the facing S/D straps of the gate itself | 0.35 fF | device model only |
| Hold feedthrough | −72 dB (nominal C), −69 dB (C −35 %), from the unchanged C(SH_IN, SH_OUT) | same | −116 dB |
| Pedestal nonlinearity, PVT × cap spread (budget 201 µV) | ≤ 72 µV (worst ff −40 °C, C −35 %) | ≤ 66 µV | ≤ 50 µV |
| Leakage droop at 125 °C (step 1.6 → 1.7 V) | 9.9–18.1 mV/ms | same | 12.7–23.1 mV/ms |
| Acquisition 0.5–3.2 V to ¼ LSB | +2…5 % (worst ss 125 °C +35 %: 1.82 µs) | same | 1.78 µs |
| Comparator kickback at tt 27 °C (budget 201 µV) | 125 µV at C −35 %, 89 µV nominal | 126 / 88 µV | 157 / 103 µV |

**Hold feedthrough is the one figure the layout makes worse than the schematic.** The coupling sits mostly in the switch's own S/D straps, which face each other across the main gates; moving the routing doesn't remove it (checked in v1; the v2b and v4 floorplans barely change it).
- An input that moves by the full scale during the hold shifts the held value by 0.8 mV (nominal C) to 1.2 mV (C −35 %).
- That is about 1–1.5 LSB at 12 bit and about 0.1 LSB for the 8-bit ADC, and negligible for slowly varying inputs.
- If 12 bit at high input slew is needed later, a T-switch (series–shunt–series) is the circuit fix. The room between the gate and the driver is kept free for it.

The `droop` column of `sah_12bit_final_tb_tran` starts 5 µs after the input step, while the 25 nA follower is still slewing (≈ 9 µs for 2.3 V). Post-layout it therefore contains the feedthrough of the rest of the step; use the 1.6 → 1.7 V step for the leakage droop.
