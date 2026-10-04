// Placeholder module for a the FAIf analogue interface.

module analogue_interface (
    input  logic [7:0]  adc_ref,    // ADC Reference
    input  logic        adc_hold,   // ADC Hold
    output logic        adc_comp,   // ADC Comparitor output

    input  logic [15:0] dac_out,     // DAC output

    input  logic [3:0]  sh_cap_en,  // S&H hold-cap trim

    inout wire         analog_0, analog_1, analog_2    // Analogue pins
);

endmodule