* NGSPICE file created from digital_level_translator.ext - technology: ihp-sg13cmos5l

.subckt nmos a_100_15# a_74_n21# sub a_0_0#
X0 a_100_15# a_74_n21# a_0_0# sub sg13_lv_nmos ad=0.1005p pd=1.34u as=0.1005p ps=1.34u w=0.15u l=0.13u
.ends

.subckt nmosHV a_68_n36# sub a_158_0# a_0_0#
X0 a_158_0# a_68_n36# a_0_0# sub sg13_hv_nmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=0.45u
.ends

.subckt nmosHV$1 a_68_n36# sub a_158_0# a_0_0#
X0 a_158_0# a_68_n36# a_0_0# sub sg13_hv_nmos ad=0.34p pd=2.68u as=0.34p ps=2.68u w=1u l=0.45u
.ends

.subckt pmos$1 a_68_n36# w_n62_n62# a_94_0# a_0_0#
X0 a_94_0# a_68_n36# a_0_0# w_n62_n62# sg13_lv_pmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=0.13u
.ends

.subckt pmosHV a_68_n36# w_n124_n124# a_158_0# a_0_0#
X0 a_158_0# a_68_n36# a_0_0# w_n124_n124# sg13_hv_pmos ad=0.204p pd=1.88u as=0.204p ps=1.88u w=0.6u l=0.45u
.ends

.subckt pmosHV$1 a_68_n36# w_n124_n124# a_158_0# a_0_0#
X0 a_158_0# a_68_n36# a_0_0# w_n124_n124# sg13_hv_pmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=0.45u
.ends

.subckt digital_level_translator LOUT LIN PLAVDD PLVSS PLDVDD
Xnmos_0 a_513_360# LIN PLVSS PLVSS nmos
Xnmos_1 m2_484_621# a_513_360# PLVSS PLVSS nmos
XnmosHV_0 a_2381_738# PLVSS LOUT PLVSS nmosHV
XnmosHV_1 a_2381_738# PLVSS LOUT PLVSS nmosHV
XnmosHV$1_0 m2_484_621# PLVSS a_2381_738# PLVSS nmosHV$1
XnmosHV$1_1 a_513_360# PLVSS a_1362_738# PLVSS nmosHV$1
XnmosHV_2 a_2381_738# PLVSS LOUT PLVSS nmosHV
XnmosHV_3 a_2381_738# PLVSS LOUT PLVSS nmosHV
Xpmos$1_0 LIN w_377_958# PLDVDD a_513_360# pmos$1
Xpmos$1_1 a_513_360# w_377_958# PLDVDD m2_484_621# pmos$1
XpmosHV_0 a_2381_738# w_1101_1020# PLAVDD LOUT pmosHV
XpmosHV_1 a_2381_738# w_1101_1020# PLAVDD LOUT pmosHV
XpmosHV_2 a_2381_738# w_1101_1020# PLAVDD LOUT pmosHV
XpmosHV$1_0 a_1362_738# w_1101_1020# PLAVDD a_2381_738# pmosHV$1
XpmosHV_3 a_2381_738# w_1101_1020# PLAVDD LOUT pmosHV
XpmosHV$1_1 a_2381_738# w_1101_1020# PLAVDD a_1362_738# pmosHV$1
.ends

