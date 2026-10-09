module sar
  (input  clk,
   input  rst_n,
   input  clear,
   input  ena,
   input  start,
   output done,
   output tick,
   output [7:0] value,
   output sh_en,
   output [7:0] ref_out,
   input  comp);
  wire [7:0] value_reg;
  wire [7:0] value_next;
  wire [8:0] mask_reg;
  wire [8:0] mask_next;
  wire sh_en_reg;
  wire [7:0] result_reg;
  wire tick_next;
  wire tick_reg;
  wire n6;
  wire n9;
  wire n12;
  wire [7:0] n13;
  wire [7:0] n15;
  wire n35;
  localparam [8:0] n37 = 9'b000000000;
  wire [7:0] n38;
  wire [7:0] n40;
  wire [8:0] n41;
  wire [8:0] n42;
  wire [7:0] n43;
  wire [8:0] n45;
  wire n46;
  wire [7:0] n47;
  wire [7:0] n48;
  wire [7:0] n49;
  wire [7:0] n50;
  wire [7:0] n51;
  wire [7:0] n52;
  wire [7:0] n53;
  wire [8:0] n54;
  wire [7:0] n56;
  wire [8:0] n57;
  wire [7:0] n60;
  wire [8:0] n62;
  wire n66;
  wire n67;
  wire n69;
  wire n70;
  wire n71;
  reg [7:0] n73;
  reg [8:0] n74;
  reg n75;
  reg [7:0] n76;
  reg n77;
  assign done = sh_en_reg; //(module output)
  assign tick = tick_reg; //(module output)
  assign value = result_reg; //(module output)
  assign sh_en = sh_en_reg; //(module output)
  assign ref_out = value_reg; //(module output)
  /*# rtl/sar.vhdl:88:10 */
  assign value_reg = n73; // (signal)
  /*# rtl/sar.vhdl:88:21 */
  assign value_next = n60; // (signal)
  /*# rtl/sar.vhdl:93:10 */
  assign mask_reg = n74; // (signal)
  /*# rtl/sar.vhdl:93:20 */
  assign mask_next = n62; // (signal)
  /*# rtl/sar.vhdl:96:10 */
  assign sh_en_reg = n75; // (signal)
  /*# rtl/sar.vhdl:98:10 */
  assign result_reg = n76; // (signal)
  /*# rtl/sar.vhdl:99:10 */
  assign tick_next = n71; // (signal)
  /*# rtl/sar.vhdl:99:21 */
  assign tick_reg = n77; // (signal)
  /*# rtl/sar.vhdl:108:14 */
  assign n6 = ~rst_n;
  /*# rtl/sar.vhdl:118:20 */
  assign n9 = mask_next == 9'b000000000;
  /*# rtl/sar.vhdl:118:7 */
  assign n12 = n9 ? 1'b1 : 1'b0;
  /*# rtl/sar.vhdl:125:7 */
  assign n13 = tick_next ? value_next : result_reg;
  /*# rtl/sar.vhdl:123:7 */
  assign n15 = clear ? 8'b00000000 : n13;
  /*# rtl/sar.vhdl:147:19 */
  assign n35 = mask_reg == 9'b000000000;
  /*# rtl/sar.vhdl:93:20 */
  assign n38 = n37[7:0]; // extract
  /*# rtl/sar.vhdl:148:9 */
  assign n40 = start ? 8'b00000000 : value_reg;
  /*# rtl/sar.vhdl:148:9 */
  assign n41 = {1'b1, n38};
  /*# rtl/sar.vhdl:148:9 */
  assign n42 = start ? n41 : mask_reg;
  /*# rtl/sar.vhdl:154:36 */
  assign n43 = mask_reg[8:1]; // extract
  /*# rtl/sar.vhdl:154:26 */
  assign n45 = {1'b0, n43};
  /*# rtl/sar.vhdl:155:17 */
  assign n46 = ~comp;
  /*# rtl/sar.vhdl:157:51 */
  assign n47 = mask_reg[7:0]; // extract
  /*# rtl/sar.vhdl:157:39 */
  assign n48 = ~n47;
  /*# rtl/sar.vhdl:157:35 */
  assign n49 = value_reg & n48;
  /*# rtl/sar.vhdl:155:9 */
  assign n50 = n46 ? n49 : value_reg;
  /*# rtl/sar.vhdl:160:45 */
  assign n51 = mask_reg[8:1]; // extract
  /*# rtl/sar.vhdl:160:34 */
  assign n52 = n50 | n51;
  /*# rtl/sar.vhdl:147:7 */
  assign n53 = n35 ? n40 : n52;
  /*# rtl/sar.vhdl:147:7 */
  assign n54 = n35 ? n42 : n45;
  /*# rtl/sar.vhdl:146:5 */
  assign n56 = ena ? n53 : value_reg;
  /*# rtl/sar.vhdl:146:5 */
  assign n57 = ena ? n54 : mask_reg;
  /*# rtl/sar.vhdl:143:5 */
  assign n60 = clear ? 8'b00000000 : n56;
  /*# rtl/sar.vhdl:143:5 */
  assign n62 = clear ? 9'b000000000 : n57;
  /*# rtl/sar.vhdl:166:47 */
  assign n66 = mask_reg[0]; // extract
  /*# rtl/sar.vhdl:166:35 */
  assign n67 = n66 & ena;
  /*# rtl/sar.vhdl:166:71 */
  assign n69 = mask_next == 9'b000000000;
  /*# rtl/sar.vhdl:166:57 */
  assign n70 = n69 & n67;
  /*# rtl/sar.vhdl:166:20 */
  assign n71 = n70 ? 1'b1 : 1'b0;
  /*# rtl/sar.vhdl:114:5 */
  always @(posedge clk or posedge n6)
    if (n6)
      n73 <= 8'b00000000;
    else
      n73 <= value_next;
  /*# rtl/sar.vhdl:114:5 */
  always @(posedge clk or posedge n6)
    if (n6)
      n74 <= 9'b000000000;
    else
      n74 <= mask_next;
  /*# rtl/sar.vhdl:114:5 */
  always @(posedge clk or posedge n6)
    if (n6)
      n75 <= 1'b1;
    else
      n75 <= n12;
  /*# rtl/sar.vhdl:114:5 */
  always @(posedge clk or posedge n6)
    if (n6)
      n76 <= 8'b00000000;
    else
      n76 <= n15;
  /*# rtl/sar.vhdl:114:5 */
  always @(posedge clk or posedge n6)
    if (n6)
      n77 <= 1'b0;
    else
      n77 <= tick_next;
endmodule

