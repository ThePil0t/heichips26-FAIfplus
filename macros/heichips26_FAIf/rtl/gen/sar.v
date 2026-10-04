module sar
  (input  clk,
   input  rst_n,
   input  clear,
   input  ena,
   input  start,
   output done,
   output tick,
   output [7:0] value,
   output hold,
   output [7:0] ref_out,
   input  comp);
  wire [7:0] value_reg;
  wire [7:0] value_next;
  wire [8:0] mask_reg;
  wire [8:0] mask_next;
  wire n6;
  wire n18;
  localparam [8:0] n20 = 9'b000000000;
  wire [7:0] n21;
  wire [7:0] n23;
  wire [8:0] n24;
  wire [8:0] n25;
  wire [7:0] n26;
  wire [8:0] n28;
  wire n29;
  wire [7:0] n30;
  wire [7:0] n31;
  wire [7:0] n32;
  wire [7:0] n33;
  wire [7:0] n34;
  wire [7:0] n35;
  wire [7:0] n36;
  wire [8:0] n37;
  wire [7:0] n39;
  wire [8:0] n40;
  wire [7:0] n43;
  wire [8:0] n45;
  wire n50;
  wire n51;
  wire n54;
  wire n55;
  wire n57;
  wire n58;
  wire n59;
  wire n63;
  wire n64;
  reg [7:0] n66;
  reg [8:0] n67;
  assign done = n51; //(module output)
  assign tick = n59; //(module output)
  assign value = value_reg; //(module output)
  assign hold = n64; //(module output)
  assign ref_out = value_reg; //(module output)
  /*# rtl/sar.vhdl:76:10 */
  assign value_reg = n66; // (signal)
  /*# rtl/sar.vhdl:76:21 */
  assign value_next = n43; // (signal)
  /*# rtl/sar.vhdl:81:10 */
  assign mask_reg = n67; // (signal)
  /*# rtl/sar.vhdl:81:20 */
  assign mask_next = n45; // (signal)
  /*# rtl/sar.vhdl:91:14 */
  assign n6 = ~rst_n;
  /*# rtl/sar.vhdl:115:19 */
  assign n18 = mask_reg == 9'b000000000;
  /*# rtl/sar.vhdl:81:20 */
  assign n21 = n20[7:0]; // extract
  /*# rtl/sar.vhdl:116:9 */
  assign n23 = start ? 8'b00000000 : value_reg;
  /*# rtl/sar.vhdl:116:9 */
  assign n24 = {1'b1, n21};
  /*# rtl/sar.vhdl:116:9 */
  assign n25 = start ? n24 : mask_reg;
  /*# rtl/sar.vhdl:122:36 */
  assign n26 = mask_reg[8:1]; // extract
  /*# rtl/sar.vhdl:122:26 */
  assign n28 = {1'b0, n26};
  /*# rtl/sar.vhdl:123:17 */
  assign n29 = ~comp;
  /*# rtl/sar.vhdl:125:51 */
  assign n30 = mask_reg[7:0]; // extract
  /*# rtl/sar.vhdl:125:39 */
  assign n31 = ~n30;
  /*# rtl/sar.vhdl:125:35 */
  assign n32 = value_reg & n31;
  /*# rtl/sar.vhdl:123:9 */
  assign n33 = n29 ? n32 : value_reg;
  /*# rtl/sar.vhdl:128:45 */
  assign n34 = mask_reg[8:1]; // extract
  /*# rtl/sar.vhdl:128:34 */
  assign n35 = n33 | n34;
  /*# rtl/sar.vhdl:115:7 */
  assign n36 = n18 ? n23 : n35;
  /*# rtl/sar.vhdl:115:7 */
  assign n37 = n18 ? n25 : n28;
  /*# rtl/sar.vhdl:114:5 */
  assign n39 = ena ? n36 : value_reg;
  /*# rtl/sar.vhdl:114:5 */
  assign n40 = ena ? n37 : mask_reg;
  /*# rtl/sar.vhdl:111:5 */
  assign n43 = clear ? 8'b00000000 : n39;
  /*# rtl/sar.vhdl:111:5 */
  assign n45 = clear ? 9'b000000000 : n40;
  /*# rtl/sar.vhdl:134:29 */
  assign n50 = mask_reg == 9'b000000000;
  /*# rtl/sar.vhdl:134:15 */
  assign n51 = n50 ? 1'b1 : 1'b0;
  /*# rtl/sar.vhdl:136:42 */
  assign n54 = mask_reg[0]; // extract
  /*# rtl/sar.vhdl:136:30 */
  assign n55 = n54 & ena;
  /*# rtl/sar.vhdl:136:66 */
  assign n57 = mask_next == 9'b000000000;
  /*# rtl/sar.vhdl:136:52 */
  assign n58 = n57 & n55;
  /*# rtl/sar.vhdl:136:15 */
  assign n59 = n58 ? 1'b1 : 1'b0;
  /*# rtl/sar.vhdl:139:29 */
  assign n63 = mask_reg != 9'b000000000;
  /*# rtl/sar.vhdl:139:15 */
  assign n64 = n63 ? 1'b1 : 1'b0;
  /*# rtl/sar.vhdl:94:5 */
  always @(posedge clk or posedge n6)
    if (n6)
      n66 <= 8'b00000000;
    else
      n66 <= value_next;
  /*# rtl/sar.vhdl:94:5 */
  always @(posedge clk or posedge n6)
    if (n6)
      n67 <= 9'b000000000;
    else
      n67 <= mask_next;
endmodule

