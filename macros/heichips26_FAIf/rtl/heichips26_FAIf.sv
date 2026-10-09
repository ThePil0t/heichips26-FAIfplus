// SPDX-FileCopyrightText: © 2026 XXX Authors
// SPDX-License-Identifier: Apache-2.0

// Adapted from the Tiny Tapeout template

`default_nettype none

module heichips26_FAIf (
`ifdef USE_POWER_PINS
    inout  wire VPWR,
    inout  wire VGND,
    inout  wire VAPWR,
`endif
    
    input  logic [7:0] ui_in,    // Dedicated inputs
    output logic [7:0] uo_out,   // Dedicated outputs
    input  logic [7:0] uio_in,   // IOs: Input path
    output logic [7:0] uio_out,  // IOs: Output path
    output logic [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  logic       ena,      // always 1 when the design is powered, so you can ignore it
    input  logic       clk,      // clock
    input  logic       rst_n,     // reset_n - low to reset

    // Analogue dedicated outputs (inout keeps LibreLane from buffering them)
    inout wire analog_0, analog_1, analog_2
);

    logic [7:0] cfg;

    // List all unused inputs to prevent warnings
    wire _unused = &{ena, uio_in[4:3], cfg[7:4]};
    assign uio_out[7:5] = '0;
    assign uio_out[2:0] = '0;


    logic adc_clear, adc_ena, adc_start;
    logic adc_done, adc_tick;
    logic adc_sh_en;
    logic [7:0] adc_value;
    logic [7:0] adc_ref_out;
    logic adc_comp;

    logic [7:0] dac_in;
    logic dac_sel, dac_load;
    logic [15:0] dac_out;

    logic load_config;

    // Config register: loads ui_in while load_config is 1.
    // cfg[3:0] drives the spare 3.3 V outputs sh_cap_en, cfg[7:4] is unused.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cfg <= '0;
        else if (load_config)
            cfg <= ui_in;
    end

    // Instanciate the DAC Register
    dac_reg dac_reg_instance (
        .clk(clk),
        .reset_n(rst_n),
        .dac_in(dac_in),
        .dac_sel(dac_sel),
        .dac_load(dac_load),
        .dac_out(dac_out)
    );

    // The comparator in the macro gives adc_comp = 1 when V_dac > V_in
    // (INP = DAC, INN = S&H output; the down translator doesn't invert).
    // The SAR keeps a bit on comp = 1, i.e. it needs V_in >= V_dac: invert.
    sar sar_instance (
        .clk(clk),
        .rst_n(rst_n),
        .clear(adc_clear),
        .ena(adc_ena),
        .start(adc_start),
        .done(adc_done),
        .tick(adc_tick),
        .value(adc_value),
        .sh_en(adc_sh_en),
        .ref_out(adc_ref_out),
        .comp(~adc_comp)
    );

    analogue_interface analogue_interface_instance (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VAPWR(VAPWR),
        .VGND(VGND),
    `endif
        .adc_ref(adc_ref_out),
        // The macro pin adc_hold is the S&H enable SH_EN (x9 doesn't invert):
        // 1 = track, 0 = hold. Driven straight from the SAR's sh_en flip-flop.
        .adc_hold(adc_sh_en),
        .adc_comp(adc_comp),
        .dac_out(dac_out),
        .sh_cap_en(cfg[3:0]),
        .analog_0(analog_0),
        .analog_1(analog_1),
        .analog_2(analog_2)
    );

    assign adc_clear = uio_in[0];
    assign adc_ena = uio_in[1];
    assign adc_start = uio_in[2];
    
    assign uio_out[3] = adc_done;
    assign uio_out[4] = adc_tick;
    assign uo_out = adc_value;
    
    assign dac_in = ui_in;
    assign dac_sel = uio_in[5];
    assign dac_load = uio_in[6];
    assign load_config = uio_in[7];

    assign uio_oe  = 8'b00011000;

endmodule
