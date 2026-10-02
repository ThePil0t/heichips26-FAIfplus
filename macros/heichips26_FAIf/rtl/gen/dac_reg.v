module dac_reg
  (input  clk,
   input  reset_n,
   input  [7:0] dac_in,
   input  dac_sel,
   input  dac_load,
   output [15:0] dac_out);
  wire [15:0] dac_rg;
  wire [7:0] dac_lsb;
  wire n2;
  wire [15:0] n4;
  wire [7:0] n6;
  wire n7;
  wire [15:0] n16;
  reg [15:0] n17;
  wire [7:0] n18;
  reg [7:0] n19;
  assign dac_out = dac_rg; //(module output)
  /*# rtl/dac_reg.vhdl:53:12 */
  assign dac_rg = n17; // (signal)
  /*# rtl/dac_reg.vhdl:54:12 */
  assign dac_lsb = n19; // (signal)
  /*# rtl/dac_reg.vhdl:61:16 */
  assign n2 = ~reset_n;
  /*# rtl/dac_reg.vhdl:69:30 */
  assign n4 = {dac_in, dac_lsb};
  /*# rtl/dac_reg.vhdl:68:11 */
  assign n6 = dac_sel ? dac_lsb : dac_in;
  /*# rtl/dac_reg.vhdl:66:9 */
  assign n7 = dac_sel & dac_load;
  /*# rtl/dac_reg.vhdl:65:5 */
  assign n16 = n7 ? n4 : dac_rg;
  /*# rtl/dac_reg.vhdl:65:5 */
  always @(posedge clk or posedge n2)
    if (n2)
      n17 <= 16'b0000000000000000;
    else
      n17 <= n16;
  /*# rtl/dac_reg.vhdl:65:5 */
  assign n18 = dac_load ? n6 : dac_lsb;
  /*# rtl/dac_reg.vhdl:65:5 */
  always @(posedge clk or posedge n2)
    if (n2)
      n19 <= 8'b00000000;
    else
      n19 <= n18;
endmodule

