// Placeholder module for a the FAIf analogue interface.
// LibreLane doesn't read this file; it uses the macro's final/vh/analogue_interface.vh.

module analogue_interface (
    input  logic [7:0]  adc_ref,    // ADC Reference
    input  logic        adc_hold,   // S&H enable SH_EN: 1 = track, 0 = hold
    output logic        adc_comp,   // ADC Comparitor output: 1 when V_dac > V_in

    input  logic [15:0] dac_out,     // DAC output

    input  logic [3:0]  sh_cap_en,  // spare 3.3 V outputs (former S&H hold-cap trim)

    inout wire         analog_0, analog_1, analog_2    // Analogue pins
);

`ifdef SIM
    // Behavioral model of the ADC path, simulation only. Polarities as in the
    // transistor netlists of the macro (checked with ngspice on 2026-10-09):
    // - the S&H tracks while adc_hold (SH_EN) is 1 and holds while it is 0;
    // - the comparator has INP = DAC and INN = S&H output, so adc_comp = 1
    //   when V_dac > V_in;
    // - the SAR DAC voltage rises with adc_ref (ideal, full scale VFS).
    localparam real VFS = 3.3;

    real vin  = 0.0;    // ADC input voltage on analog_0, set by the testbench
    real v_sh = 0.0;    // S&H output
    real v_dac;

    always @(adc_hold or vin)
        if (adc_hold)
            v_sh = vin;

    always @(adc_ref or v_sh) begin
        v_dac    = $itor(adc_ref) * VFS / 256.0;
        adc_comp = (v_dac > v_sh);
    end
`endif

endmodule
