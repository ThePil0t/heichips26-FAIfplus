# Plan: LibreLane dry run of `heichips26_FAIf` with the `analogue_interface` macro

## Context
The digital-on-top flow stopped at floorplan with `ORD-2013: LEF master analogue_interface not found`. The macro now exists in `macros/heichips26_FAIf/macros/analogue_interface/final/`. It is not committed yet. This plan hooks the macro into LibreLane and lists the exact edits and commands, so you can run the dry run yourself.

Decisions:
- `sh_cap_en` is tied to `4'b0000` for now.
- **I** do Step 0 (commit the plan, your standing rule) and Step 1 (the pin fix in the macro I built).
- **You** do Steps 2–4: the RTL and config edits, and the LibreLane run.

About the Python file: `scripts/build_analogue_interface.py` generates the macro. It places the blocks and draws the pins, then writes GDS, LEF, the `.vh` Verilog header and the `.lib` from one table. LibreLane never runs it; it only reads `final/`. The script is touched in Step 1 only because the pin positions live in its table.

Facts checked in LibreLane 3.1.0.dev2 (the version in nix-shell):
- **Macro power comes from the RTL**, as in the template's `counter`. `Odb.SetPowerConnections` reads the `ifdef USE_POWER_PINS` connections on the instance and matches them to the macro's LEF `USE POWER/GROUND` pins. So `PDN_MACRO_CONNECTIONS` is not needed.
- **Macro power pins reach the grid:** the PDN macro grid connects Metal4 core straps to Metal3 macro pins (`add_pdn_connect -layers "Metal4 Metal3"`). The macro's power strips are Metal3, and it has no Metal4.
- **`GND_NETS` needs the same length as `VDD_NETS`:** `pdn_cfg.tcl` loops over the two lists in pairs.
- **The DEF template is applied in `strict` mode:** the design's pins must equal the template's. small_analog has the 43 digital pins plus `analog_0..2`, which matches the top ports. Power ports are not part of the synthesized netlist.
- **`ERROR_ON_DISCONNECTED_PINS` is true**, so every macro input must be driven. That is why `sh_cap_en` is tied off.
- **Output ports get buffers:** `DESIGN_REPAIR_BUFFER_OUTPUT_PORTS` is true. Making `analog_*` `inout` keeps buffers off them.
- **Metal3 tracks in the DEF template sit at y = 0.42·k µm.** With the macro at (190, 5), 15 of its 30 west pins are more than 0.1 µm off a track, and `dac_out[4]` misses the track entirely. Step 1 snaps them.

## Step 0 (me): save the plan
Copy this plan to `/home/benedikt/heichips26-FAIf/librelane_dry_run_PLAN.md` and commit only that file on `main`. Do not push.

## Step 1 (me): snap the macro's west pins to the Metal3 tracks
File: `macros/heichips26_FAIf/macros/analogue_interface/scripts/build_analogue_interface.py`. This and `final/` are still uncommitted; they stay uncommitted.

After the `DIE_ANALOG_PIN_X = …` line, add:
```python
# Metal3 routing tracks of heichips26_template_small_analog.def (die coordinates): y = 0.42 * k
M3_TRACK_PITCH = 0.42


def snap_to_m3_track(y):
    """Move a macro-local y onto the nearest Metal3 track for the planned DIE_LOCATION."""
    die_y = y + DIE_LOCATION[1]
    return round(round(die_y / M3_TRACK_PITCH) * M3_TRACK_PITCH - DIE_LOCATION[1], 3)
```
In `build_layout()`, in the `WEST_PINS` loop, replace
```python
        y = snap((trans * find_label(ly, cell, label, layer)).y)
```
with
```python
        y = snap_to_m3_track((trans * find_label(ly, cell, label, layer)).y)
```
Each pin moves by at most 0.21 µm. The analog pins (die x 450.24 = 938 × 0.48) already lie on the Metal2 tracks.

Then I rebuild and re-verify:
- run `make -C macros/heichips26_FAIf/macros/analogue_interface build-top` in nix-shell (all script asserts must pass);
- re-measure the GDS: for all 30 west pins, (y + 5.0) / 0.42 is an integer, and the pin labels sit on the pin shapes;
- reload LEF and lib in OpenROAD: 36 pins, no warnings;
- leave the README unchanged (it lists no pin y values).

## Step 2 (you): RTL edits
### `macros/heichips26_FAIf/rtl/heichips26_FAIf.sv`
Port list:
```systemverilog
`ifdef USE_POWER_PINS
    inout  wire VPWR,
    inout  wire VGND,
    inout  wire VAPWR,
`endif
    ...
    // Analogue pins (inout keeps LibreLane from buffering them)
    inout  wire analog_0, analog_1, analog_2
```
Instance:
```systemverilog
    analogue_interface analogue_interface_instance (
`ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VAPWR(VAPWR),
        .VGND(VGND),
`endif
        .adc_ref(adc_ref_out),
        .adc_hold(adc_hold),
        .adc_comp(adc_comp),
        .dac_out(dac_out),
        .sh_cap_en(4'b0000),  // TODO: drive from the config register (TAPEOUT_PLAN §3.3)
        .analog_0(analog_0),
        .analog_1(analog_1),
        .analog_2(analog_2)
    );
```
### `macros/heichips26_FAIf/rtl/analogue_interface.sv`
This file is only the lint and simulation stand-in, and LibreLane will no longer read it. Its ports must match the macro, or `make lint-verilog` and `sim-rtl-verilog` fail on the new pins:
```systemverilog
// Placeholder module for the FAIf analogue interface.
// Lint/simulation stand-in only: LibreLane uses the hard macro in
// macros/analogue_interface/final/ and does not read this file.

module analogue_interface (
`ifdef USE_POWER_PINS
    inout  wire         VPWR,
    inout  wire         VAPWR,
    inout  wire         VGND,
`endif
    input  logic [7:0]  adc_ref,    // ADC Reference
    input  logic        adc_hold,   // ADC Hold
    output logic        adc_comp,   // ADC Comparitor output

    input  logic [15:0] dac_out,    // DAC output

    input  logic [3:0]  sh_cap_en,  // S&H hold-cap trim

    inout  wire         analog_0, analog_1, analog_2    // Analogue pins
);

endmodule
```
The Verilog testbench connects `analog_*` to plain wires, so `inout` needs no TB change.

## Step 3 (you): `macros/heichips26_FAIf/flow/librelane/config.yaml`
1. **Synthesis sources**: drop the placeholder from synthesis. The macro's `.vh` (Verilog header) comes in through `MACROS`.
   ```yaml
   VERILOG_FILES:
     - dir::../../rtl/heichips26_FAIf.sv
     - dir::../../rtl/gen/*.v
   ```
2. **Floorplan**: use the template with the analog pins.
   ```yaml
   DIE_AREA: [0, 0, 500, 200]
   FP_DEF_TEMPLATE: dir::heichips26_template_small_analog.def
   ```
3. **Power and analog nets**: add next to the PDN settings.
   ```yaml
   # Second supply for the analog macro (3.3 V)
   VDD_NETS: [VPWR, VAPWR]
   GND_NETS: [VGND, VGND]

   # Keep the resizer off the analog nets
   RSZ_DONT_TOUCH_RX: "^analog_"
   ```
4. **Macro**: replace the empty `MACROS:` with:
   ```yaml
   MACROS:
     analogue_interface:
       gds:
         - dir::../../macros/analogue_interface/final/gds/analogue_interface.gds
       lef:
         - dir::../../macros/analogue_interface/final/lef/analogue_interface.lef
       vh:
         - dir::../../macros/analogue_interface/final/vh/analogue_interface.vh
       lib:
         "*":
           - dir::../../macros/analogue_interface/final/lib/analogue_interface.lib
       instances:
         analogue_interface_instance:
           location: [190, 5]
           orientation: N
   ```

## Step 4 (you): commands
```sh
cd /home/benedikt/heichips26-FAIf
nix-shell
export PDK_ROOT=$(pwd)/IHP-Open-PDK
export PDK=ihp-sg13cmos5l
cd macros/heichips26_FAIf

# a) RTL still lints with the updated placeholder
make lint-verilog

# b) first pass without DRC: the macro has 12 known block-internal DRC errors
make librelane-nodrc

# c) look at the result
make librelane-openroad      # or: make librelane-klayout

# d) full run with DRC (expected to stop at KLayout/Magic DRC on the macro's block errors)
make librelane
```
Each run writes to `flow/librelane/runs/RUN_<date>/`. Check `flow.log`, `error.log` and `warning.log` there.

## What to check in the run
| Step dir (in `runs/RUN_…/`) | Expected |
|---|---|
| `*-openroad-floorplan` | no ORD-2013 |
| `*-odb-applydeftemplate` | 46 pins matched, strict mode passes |
| `*-odb-setpowerconnections` | "Connecting power net VPWR / VAPWR / VGND to analogue_interface_instance/…" |
| `*-odb-manualmacroplacement` | macro at (190, 5), N |
| `*-openroad-generatepdn` | no PDN errors; in the GUI, Metal4 VPWR/VGND/VAPWR straps cross the macro, with Via3 onto its Metal3 power strips |
| `*-openroad-detailedrouting` | 0 DRC; `analog_0..2` are short Metal2 stubs from the die pins to the macro pins |
| `*-checker-disconnectedpins` | passes |
| `*-netgen-lvs` | clean, with the macro as a blackbox |
| `*-klayout-drc`, `*-magic-drc` (step d only) | the macro's known errors: nBuLay in the PTAT, Act.b in the down translator |

## Possible failures and what they mean
- **PDN error or floating VAPWR:** the core straps did not get vias onto the macro's power strips. In the GUI, check whether Metal4 straps cross the macro at all.
- **Pin access errors on `analogue_interface_instance` pins:** the macro was placed somewhere other than (190, 5). The pins are only on-track for that location.
- **Synthesis error that `analogue_interface` is defined twice:** `analogue_interface.sv` is still in `VERILOG_FILES`.
- **Not tested by this run:** `make precheck`. It still rejects VAPWR (TAPEOUT_PLAN §0), so that remains an organizer question.

Send me the `error.log` or the last lines of `flow.log` if a step fails, and I'll go through it with you.
