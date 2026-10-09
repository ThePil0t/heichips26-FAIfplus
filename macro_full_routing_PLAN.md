# Plan: iVREF cap + full macro routing (ADC path, PTAT, level translators, rest)

## Context
The DAC path is routed (commits 68865bc/19a663a). The S&H (`sah_12bit` v4, your manual fix in 3351c4e), the comparator x1 and the PTAT x3 (MX, east of x1) are placed but unrouted. You asked for:
1. a much larger iVREF filter cap, extended down to the DAC, on Metal1/Metal2, with a MOS cap underneath;
2. then all remaining routing: ADC path, PTAT, level translators, and the rest.

As before:
- this plan is the **suggestion** for the cap;
- the route design gets its own **break point** before the builder changes.

## Step 0
Commit this plan as `macro_full_routing_PLAN.md` (plan file only).

## Step 1: iVREF cap (suggestion)

**Today:** C1 is a `cap_cmomi` w 50 / l 2 µm on Metal2/Metal3 at x 118–169, y 156–159.5, only ≈ 45 fF.

**Proposed:** one combined cap block "C1/C2" filling the free area between x4 and R2: x 118–169.2, y ≈ 121.3–159.5. That's 3 µm from x4 (top 118.3) and from R2 (bottom 162.5).

| Part | Device | Size | Value | Terminals |
|---|---|---|---|---|
| C1 (MOM, top) | `cap_cmomi`, **mmin 1, mmax 2** (Metal1/Metal2), feed double | w ≈ 32 µm (rows) × l ≈ 48 µm (finger length), R0 | ≈ 0.82 pF (PCell: 0.825 pF at 32 × 50) | c0 = iVREF, c1 = VGND |
| C2 (MOS cap, underneath) | `sg13_hv_nmos` (thick oxide, 6.9 nm → ≈ 5 fF/µm²) | W ≈ 48 µm, L ≈ 34 µm, ng 1 | ≈ 8 pF (inversion at iVREF ≈ 1.65 V) | G = iVREF, S = D = B = VGND |

Total ≈ 9 pF instead of 45 fF. τ with the 74 kΩ divider source ≈ 0.7 µs.

**Why HV NMOS:** the PDK's `moscap_n` is thin-oxide (1.2 V class) and iVREF is 1.65 V. The HV NMOS is rated for 3.3 V.

**Layout:**
- C2's gate covers the area, with source/drain strips (Metal1) along the bottom and top edges. The gate poly is contacted at the left and right ends, outside the MOM.
- C1's fingers (Metal1/Metal2) sit over the gate, between the source/drain strips, at Metal1 spacing.
- **Metal3 over the cap stays free for routing** (iIREF/PBIAS lines from the PTAT run west over it).
- A p-tap ring (VGND) goes around C2.
- Both are generated from the PDK PCells in **one block cell**, so the builder's 3 µm block-gap check isn't violated by the overlap. The gate contacts, ring and terminal stubs are drawn by the script.

**Schematic** (`heichips26_FAIf.sch`, the LVS source):
- change C1 to w 32u, l 48u, mmin 1, mmax 2;
- add **C2** = `sg13_hv_nmos` (w 48u, l 34u), G = iVREF, S/D/B = VGND;
- then `make reference-schematic`. The generator's instance list gets C2.

Exact W/L/w/l follow from DRC; the values above are the targets.

## Step 2: implement the cap
- `macro_routing.make_divider_cells`: replace the C1 PCell by the combined cap cell.
- `PLACEMENT` "C1" row: new size and position.
- `route_divider`: VGND (west riser at x 115) and iVREF (east, to the trunk at x 173.6) connect both caps.
- **Checks:** builder checks, KLayout DRC (macro and regular), cell-level KLayout LVS of the cap block against a 2-device netlist, and the startup testbench unchanged in function.

## Step 3: route design for everything left (analysis, then ⏸ break point)

| Net group | From → to | Plan |
|---|---|---|
| `adc_ref[7:0]`, SAR bits | west pins → x6 LIN; x6 nLOUT → x4 nD | same pattern as the DAC pairs |
| x4 IDACDISABLE | → VGND | same as x11/x5 |
| iSAR_DAC | x4 ODACOUT (172.82, 102.3) → x1 INP (191.53, 125.87) | Metal3 x 173.4–173.8 up to y 125.87, then east into INP (README rule) |
| SH_IN | x8 OOA (west end, 187.01, 26.3) → S&H east pin (222.2, 112.25) | Metal3 0.4 µm in the corridor x 222.2–232, nothing alongside (README rules) |
| SH_OUT / VSS hop | S&H top (191.43 / 192.43, 112.5) → INN (191.43, 125.2) / GNDA | straight Metal3 hops up (README) |
| SH_EN | x9 LOUT → S&H west (179.2, 83.9) | LOUT Metal2 east to x ≥ 13.6, Metal3 to x 22.5, Metal2 down x 22.5, Metal3 east at y 83.9 (README) |
| S&H VDD | west (179.2, 91.5) → VAPWR | short hop into the east channel, then a supply path to be designed |
| analog_0 | south pin (259.74–260.74) → x8 IOAP | Metal2/Metal3 up into the opamp |
| x8 IOADISABLE, supplies | → VGND / VAPWR | rails along the opamp edges to the straps |
| iSAR_COMP | x1 OUT (SE corner) → x2 DIN (west) | east and north around the comparator, then west above the blocks (README rule) |
| `adc_comp`, `adc_hold`, `sh_cap_en[3:0]` | west pins → x2 DOUT / x9 LIN / xcap LIN | Metal2 stubs: LIN sits under my VPWR trunk |
| x2, x9, xcap0–3 supplies | Metal1 supply pins → VPWR/VAPWR/VGND trunks at x 5.35–12.81 | short Metal1/Metal2 taps |
| PTAT x3 | CSOUT1 → x8 IOAIREF; CSOUT2/3/4 → IDACIREF of x4/x5/x11 (Metal3 entry at R2R + 19.2 from the west); PBIAS → x1 PBIAS; PCSVDD/PCSVSS | Metal3 west over the cap and the top area, trunks down the west channel (x 19–21, Metal2); CSOUT1 down the east side; PBIAS straight to x1's top |
| xcap LOUT | unconnected (spares) | nothing |

**Break-point output:** a route picture and table, plus the clearance and connectivity pre-check on a scratch copy. You review it, and I wait for your go.

## Step 4: implement in the builder
- **`macro_routing.py`:** add `route_adc_path()` and `route_ptat()`; extend `dac_probes` to all nets.
- **README routing section:** the generated routing replaces "routed by hand" for SH_IN.

## Verification
- **Builder checks:** `make layout`, with clearance and connectivity checks over **all** nets.
- **KLayout DRC:** macro level and the regular deck, density rules only.
- **Macro KLayout LVS** against the regenerated reference: must now **match** (sign-off for the macro). Magic is informational.
- **Rebuild:** you run `make build-top`, LibreLane, `copy-final` and precheck. Commits only with your OK, except the plan file.
