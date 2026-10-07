* NGSPICE file created from down_digital_translator.ext - technology: ihp-sg13cmos5l

.subckt nmosHV a_68_n36# sub a_158_0# a_0_0#
X0 a_158_0# a_68_n36# a_0_0# sub sg13_hv_nmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=0.45u
.ends

.subckt pmosHV a_68_n36# w_n124_n124# a_158_0# a_0_0#
X0 a_158_0# a_68_n36# a_0_0# w_n124_n124# sg13_hv_pmos ad=0.204p pd=1.88u as=0.204p ps=1.88u w=0.6u l=0.45u
.ends

.subckt down_digital_translator PDIGVDD DIN PDIGVSS DOUT
XnmosHV_0 DIN PDIGVSS PDIGVSS a_560_122# nmosHV
XnmosHV_1 a_560_122# PDIGVSS PDIGVSS DOUT nmosHV
XpmosHV_0 DIN PDIGVDD a_560_122# PDIGVDD pmosHV
XpmosHV_1 a_560_122# PDIGVDD DOUT PDIGVDD pmosHV
.ends

