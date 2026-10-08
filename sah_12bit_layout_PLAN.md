# Plan: layout of `sah_12bit` (shielded hold cap, placed between opamp x8 and comparator x1)

## Context
`sah_12bit` (fixed 1.214 pF MOM hold cap, HV transmission gate with dummies, 4-stage gate driver) has no layout yet. It is the S&H of the ADC path (TAPEOUT_TODO_PLAN §E). In the macro it sits between:
- the buffer **opamp x8**: its output OOA drives SH_IN and leaves the opamp's west edge at macro (187, 26.3);
- the **comparator x1**: SH_OUT drives INN, an M3 pad at macro (197.8, 121.7), which can be reached straight from the south.

Goals:
- a DRC/LVS-clean cell with a **shielded hold cap**;
- pins placed so that the SH_OUT and SH_IN routes stay short;
- the real cell placed in `analogue_interface` instead of the 110 × 58 µm dummy.

Another Claude session is working in the same tree, so I stage files by explicit path only and leave its files alone (see step 6 for the builder).

**Decided with you (2026-10-08):**
- Reshape the cap to the **same C**, so it fits between the Metal4 PDN strap groups with **≈ 6 µm** clearance.
- Add a **Metal4 shield** over the cap, as an exception that applies to sah_12bit only.
- Also update the macro builder.

## Facts the plan relies on
- **Metal4 over the S&H area:** the only Metal4 there today are LibreLane PDN straps. They run in groups of three 1 µm straps at macro x **222.38–229.38** and **272.38–279.38**, from the last run.
  - `RT_MAX_LAYER: Metal4` allows signal routing on Metal4, and the macro LEF does not block Metal4. So an OBS is needed.
- **How the cap PCell sets C:** C = 0.82 fF/µm² × nx·0.84 × ny·0.89 µm. C depends only on nx·ny (the ngspice model uses the same formula).
  - Today: 30 × 66 = 1980 cells = 1213.8 fF, marker 27.0 × 60.3 µm.
  - **New: 33 × 60 = 1980 cells**, so **identical C**. The parameters are `l = 27.72u` and `w = 54.29u`, giving a marker of **29.52 × 54.93 µm**.
  - Centred in the gap 229.38–272.38: marker at x 236.12–265.64, which is **6.7 µm** from the straps. The shield and fence edge sit **≈ 5.8 µm** from the straps.
- **What the cap looks like:** both terminals are on every layer M1–M3 (alternating bars); PLUS pad on the west edge, MINUS pad on the east edge, both on M3.
  - Because of this, M1–M3 can't shield the top; a top shield needs Metal4.
  - The PCell already paints Recog.mom 99/39 and NoMetFiller 160/0.
- **KLayout LVS of the cap:** the device is recognised from the marker plus **exactly 2 `.pin` shapes** inside it.
  - l and w are measured from the marker bbox and are not compared (non-primary parameters), so a drawn Metal4 shape over the cap doesn't affect extraction.
  - No other `.pin` may lie inside the marker. This is the opamp's LVS failure; don't repeat it.
- **Magic** can't extract `cap_cmomi`. Magic LVS will therefore show C1 as missing; that is the one accepted difference, and KLayout LVS is the sign-off.
- **Generator:** PDK PCells in batch through `klayout.db`, as in PTAT step 5:
  - `sys.path` gets `libs.tech/klayout/python` and `pycell4klayout-api/source/python`;
  - `import sg13cmos5l_pycell_lib`;
  - **`ly.technology_name = "sg13cmos5l"`**;
  - `create_cell(name, "SG13_dev", {...})`, then `convert_cell_to_static`;
  - run it with nix-shell `python3`, not `klayout -b`.
  - The PTAT scripts were lost with the scratchpad, so **this generator is committed** in the cell folder.
- **Team layout conventions:**
  - tap rings 0.30 µm Activ with Cont on a 0.36 pitch and full Metal1;
  - p-tap = Activ + pSD + Substrate, n-tap = Activ in NWell;
  - ThickGateOx over HV devices and taps;
  - pins as `.pin` (dt 2) + `.text` (dt 25) on Metal3.

## Layout design and what to watch
**1. Shielding: a closed VSS box around C1.**
- **Bottom:** a GatPoly plane over field oxide under the whole marker (+0.5 µm). It has no Activ under it, so it forms no device, and it is contacted to the M1 fence outside the marker. A p-tap ring under the fence ties the local substrate. (The DRC deck has no maximum poly width or slit rules; density is checked only globally or in 800 µm windows.)
- **Sides:**
  - a fence of M1 + M2 + M3 rings with Via1/Via2 stacks at minimum pitch, ≈ 0.3 µm outside the marker;
  - the MINUS pad side merges into the fence;
  - the only opening is where SH_OUT reaches the PLUS pad on M3. M1 below and M3 above the stripline stay closed.
- **Top: Metal4 shield** over the marker plus the fence, tied down by a Via3 row on the M3 fence all round. **Its net is VSS**: the cap's MINUS branch, not the driver ground.
  - Why VSS: MINUS is VSS, so shield-to-PLUS coupling only adds hold C to the same reference. Ground noise is common to the shield and MINUS and doesn't appear across C1.
  - VAPWR would inject supply ripple, a VPWR connection would add digital noise, and a floating shield doesn't shield.
  - Side effects: about +2–4 % C from the poly and Metal4 shields. That helps kickback, and PEX will capture it.
- **Fill keep-out:** NoMetFiller over the box, the switch and the SH_OUT stripline.

**2. The hold node (SH_OUT): short, shielded, small junction area.**
- **TG as shared strips:** one strip per polarity from a 4-finger PCell, `[SH_IN] D1 [SH_IN] M [SH_OUT] D2 [SH_OUT] M [SH_IN]`.
  - NMOS: w = 1.2u, ng = 4, gates sw_b / sw / sw_b / sw.
  - PMOS: w = 3.6u, ng = 4, gates sw_d / sw_b / sw_d / sw_b.
  - SH_OUT then has 2 inner diffusions per polarity instead of 3. PMOS junction leakage dominates droop at 125 °C, so this helps.
  - Each dummy is still exactly one finger of the main device.
  - If the PCell joins the gate polys of the 4 fingers, build the strip from single-finger geometry.
- **SH_OUT path:**
  - in the cell: TG → PLUS pad as an M2 stripline between M1 VSS and M3 VSS, ≤ ~25 µm. It crosses under the strap group at x 222–229, where the M3 VSS shields it;
  - in the macro: a straight M3 hop from the top-edge pin to INN (≈ 3 µm gap + 9.7 µm inside the comparator).
- **Hold feedthrough budget:** the coupling SH_IN ↔ SH_OUT must stay ≤ **0.05 fF** in total (¼ LSB / FS at C −35 %). SH_IN and SH_OUT therefore never run side by side. SH_IN enters the TG from the west, SH_OUT leaves to the east and north, and VSS separates them everywhere.
- **SH_EN and gate lines:** SH_EN, sw, sw_b and sw_d do not run along SH_OUT. Any routing coupling to SH_OUT would add charge injection that the dummies don't cancel. Gate contacts go on the driver side, and the gate lines are kept short.

**3. Gate driver**
- I1, I2 are single devices; I3, I4 are drawn as ng = 2 (shared drain), checked against m = 2 in LVS.
- The driver sits directly next to the TG on the side away from the cap, so sw → sw_b → sw_d keep their delay order.
- The driver VSS/VDD and the cap/shield VSS are **separate branches that meet only at the VSS pin** (Kelvin). Driver ground bounce at the sampling edge must not appear across C1.

**4. Wells and taps:** p-tap ring around the NMOS, n-tap ring (VDD) in the PMOS NWell, ThickGateOx over all of it, and HV well spacings. These also cover the KLayout latch-up rules (Magic LU is best effort).

**5. Floorplan (macro coordinates; cell ≈ 80 × 62 µm inside the old 110 × 58 reservation; height checked against the neighbours)**
```
 y≈108 ┌─ SH_OUT pin (M3, x≈197.8 under INN) ── VSS rail (gap at SH_OUT) ────────────────────┐
       │ TG (under INN) ══ SH_OUT stripline ══▶ │PLUS│ C1 33×60, M4 lid, poly floor │MINUS=fence│
       │ gate driver I1..I4                      │pad │ marker x 236.1–265.6          │           │
 SH_EN ▶ SH_IN ▶ (west edge, see below)          │    │ (6.7 µm to the straps)        │           │
 y≈45.5└──────────────── VDD rail (faces the opamp POAVDD rail) ───────────────────────────────┘
        x≈188 ── strap-free 179.4–222.4 ──┤straps 222.4–229.4├── strap-free 229.4–272.4 ──┤272.4 straps
```
- **Neighbour gaps:** opamp top 42.29 + 3 µm `MIN_GAP` gives the bottom ≥ 45.3. The comparator bottom 112 and R1 at 113, each minus 3 µm, give the top ≤ 109.
- **SH_IN and SH_EN pins** on the west or south edge, chosen so that SH_IN (from OOA, coming from the south) and SH_EN (from x9, coming from the north) need not run in parallel or cross in the macro channel at x 173–187. The exact pin y is fixed in the floorplan preview (step 3).

**6. Macro routing rules (for §E routing, recorded in the macro README):**
- SH_OUT is a direct M3 hop to INN.
- iSAR_DAC enters INP from the west at y ≈ 122.4 and never runs along the S&H top edge.
- SH_EN never runs along SH_IN or SH_OUT without a VSS track between them.
- No M1–M3 routing over the S&H (the LEF already blocks it); Metal4 OBS over the shield.

## Steps
0. **Save the plan.** Copy this plan unchanged to `sah_12bit_layout_PLAN.md` at the repo root and commit only that file on `main`, with the message "Add sah_12bit_layout_PLAN.md". Don't push; nothing else starts before this commit.
1. **Reshape C1, same C:**
   - in `schematic/xschem/sah_12bit.sch`, change C1 to `w=54.29e-6 l=27.72e-6` and update the header text;
   - `testbenches/xschem/sah_12bit_param.sym` template: `CW=54.29e-6 CL=27.72e-6`;
   - `sah_12bit_final_tb_tran.sch`: `CWP=54.29 CLP=27.72` and `set cwf = 54.29`, with the ±35 % row mapping re-checked for 61 rows;
   - README: the cap dimensions.
   - The archived sweep TBs keep their old CW lists. The C values are identical by the model formula; the README says so.
   - **Check:**
     - `scripts/sizing/check_param_equiv.py` passes;
     - the PCell label reads C = 1213.8 fF;
     - one `sim-final` point (tt / typ / 27 °C) reproduces the archived pedestal and t_acq.
2. **Generator `scripts/layout/gen_sah_12bit_layout.py`** (klayout.db + SG13_dev PCells, made static). It:
   - builds the devices from §2–§4, C1 (`cap_cmomi` w=54.29u, l=27.72u, mmin=1, mmax=3, double feed), the shield box from §1, routing, rails and pins (SH_IN, SH_OUT, SH_EN, VDD, VSS on Metal3);
   - names the top cell `sah_12bit` and writes `layout/sah_12bit.gds`;
   - prints the bbox, marker, shield box and pin positions;
   - writes its output to scratch first.
3. **Floorplan preview (non-blocking report).** In scratch, put the opamp, the new S&H and the comparator at the proposed macro positions and draw the strap positions. Render a PNG (`lay2img.py`) and post it with a distance table:
   - SH_OUT and SH_IN route lengths;
   - clearance from the cap and from the shield to the straps;
   - the gaps to the neighbours.
   I continue unless you object.
4. **DRC and LVS until clean** (from `sah_12bit/`, nix-shell, `PDK_ROOT`/`PDK`/`PDKPATH`/`STD_CELL_LIBRARY` exported):
   - `make klayout-drc DRC_LEVEL=regular`: density rules only;
   - `make magic-drc`: clean as far as possible;
   - `make klayout-lvs`: **match**;
   - `make magic-lvs`: match except the known C1 difference.
5. **PEX and post-layout sims.**
   - Run `make klayout-pex` and/or `magic-pex`. Check that C1 is counted once: total SH_OUT–VSS C ≈ 1.21 pF + parasitics, not 2.4 pF and not 0.05 pF.
   - From the PEX, read the coupling from SH_OUT to SH_IN (≤ 0.05 fF), to SH_EN, and to sw/sw_b/sw_d.
   - Add `sah_12bit_pex.sym` and PEX variants of `final_tb_tran` (tt 27 °C, ss 125 °C, ff −40 °C) and of `kickback_tb_tran`. Compare them with the schematic results: pedestal NL, droop at 125 °C, hold feedthrough, kickback.
   - Replace the CPAR = 0.05 pF estimate in `docs/hold_cap_sizing.md` with the extracted value.
6. **Builder `analogue_interface/scripts/build_analogue_interface.py`.** First check `git status` / `git diff` on the folder. If there are uncommitted edits from the other session, stop and ask. Then:
   - `BLOCKS["sah"] = "sah_12bit/layout/sah_12bit.gds"`, remove the `sh_trim` dummy, and set the x10 placement so that the cap marker lands at x 236.12 and the S&H stays within y 45.3–109;
   - **Metal4 exception:** Via3/Metal4 are allowed only inside x10's shield box; the check stays for everything else;
   - **LEF:** a `LAYER Metal4` OBS over the shield box + 1 µm;
   - assert ≥ 5.5 µm from the shield to the strap groups, using constants that name the run they come from;
   - update the README: placement table, the Metal4 exception, the routing rules from §6;
   - `make layout` (or `build-top`) and the macro KLayout DRC.
7. **Chip-level check.** Run LibreLane once and confirm:
   - the straps are unchanged and ≥ 5.5 µm from the shield;
   - no Metal4 routing over the shield;
   - KLayout DRC 0, LVS clean.

   `make copy-final` and `make precheck` only after your OK, because `final/` is shared with the other session.
8. **Docs:**
   - sah_12bit README: a layout section covering the floorplan, the shield and its net, the pins, the Magic LVS caveat and the Metal4 exception;
   - `TAPEOUT_TODO_PLAN.md` §E: the S&H row, plus the Metal4 exception in "Macro constraints" (one small edit; Metal4 over the macro, A4, is still open with the organizer).
9. **No commits without your OK** (apart from step 0). Then I propose one commit with `sah_12bit/` + `analogue_interface/` on `main`.

## Verification (end to end)
- **KLayout DRC** (regular, sign-off): density only. **KLayout LVS:** match, with C1 extracted as `cap_cmomi` and 2 ports.
- **Magic:** DRC as clean as possible; LVS differs only by C1.
- **PEX:**
  - C1 counted once;
  - coupling SH_IN ↔ SH_OUT ≤ 0.05 fF;
  - post-layout pedestal nonlinearity ≤ 201 µV;
  - droop at 125 °C reported against 13 SAR cycles;
  - kickback ≤ 201 µV with the extracted C at −35 %.
- **Macro:** the builder's asserts pass, macro DRC passes, and the LEF has the Metal4 OBS.
- **Chip:** the LibreLane run has KLayout DRC 0, and the straps and routing keep off the shield.

---

## Status as of 2026-10-08 (commit 7b33d78)

### Done
- Steps 0–8 are done. Results are in `sah_12bit/README.md` ("Layout").
- **Cell checks:** KLayout DRC regular shows only density rules; Magic DRC 0; KLayout LVS matches. Magic LVS differs only by C1.
- **Macro:** DRC shows global density only.
- **Chip:** run `RUN_2026-10-08_14-05-39` has KLayout DRC 0, LVS clean, antenna 0, timing met and unchanged IR drop.

### Deviations from the plan
- **Metal4 lid:** marker + 0.23 µm in x, so 29.98 µm wide. Slt.c allows at most 30 µm of metal without slits.
  - The lid is tied down through Via3 on the top and bottom fence and on the MINUS pad, not all around.
  - It sits 6.5 µm from the PDN straps.
- **SH_OUT entry:** the cap's feed pads are solid on Metal3 only, so SH_OUT enters the PLUS pad on Metal3. The gap is in the Metal3 fence; there is no Via3 there.
- **SH_IN pin:** at the bottom-left corner, straight above the opamp's OOA exit, instead of on the west edge.
- **Comparator x1:** moved from (187, 112) to (195, 112), so INN sits straight above the SH_OUT pin.
- **Post-layout netlist:** Magic PEX can't be used for the hold node, because it has no `cap_cmomi` device. `scripts/layout/hybrid_pex.py` combines:
  - the PDK C1 model;
  - the KLayout junction areas;
  - the Magic wire parasitics of the layout without the cap;
  - the cap-environment delta.
- **PDN straps:** LibreLane's pdngen trims the Metal4 straps within ≈ 9 µm of the lid's LEF obstruction. The power grid stays connected and the IR drop is unchanged.

### Open
- **Hold feedthrough:** −72 dB post-layout (−69 dB at C −35 %), from 0.36 fF SH_IN–SH_OUT coupling, mostly the switch's own S/D straps.
  - That is ≈ 1 LSB at 12 bit for a full-scale input change during the hold, and fine for 8 bit.
  - The circuit fix, if needed, is a T-switch.
- **Final TB "droop" column:** contaminated by feedthrough, because its window starts while the follower is still slewing. Read leakage droop from the 1.6 → 1.7 V step.
- **Macro routing:** SH_IN, SH_OUT, SH_EN, VDD, VSS. The rules are in the `analogue_interface` README.
- **Waiting for OK:** `make copy-final` and `make precheck` with the new chip run, because `final/` is shared.
