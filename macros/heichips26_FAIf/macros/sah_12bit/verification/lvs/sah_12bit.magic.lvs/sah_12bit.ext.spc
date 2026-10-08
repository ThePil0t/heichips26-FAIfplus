* NGSPICE file created from sah_12bit.ext - technology: ihp-sg13cmos5l

.subckt sah_12bit SH_EN VDD SH_IN SH_OUT VSS
X0 a_264_8832# a_264_8320# VSS VSS sg13_hv_nmos ad=0.114p pd=0.98u as=0.204p ps=1.88u w=0.6u l=0.45u
X1 a_264_8320# a_264_7974# VSS VSS sg13_hv_nmos ad=0.204p pd=1.88u as=0.204p ps=1.88u w=0.6u l=0.45u
X2 SH_OUT a_264_8832# SH_IN VDD sg13_hv_pmos ad=0.171p pd=1.28u as=0.171p ps=1.28u w=0.9u l=0.45u
X3 SH_OUT a_264_8320# SH_IN VSS sg13_hv_nmos ad=57f pd=0.68u as=57f ps=0.68u w=0.3u l=0.45u
X4 SH_IN a_300_8922# SH_IN VDD sg13_hv_pmos ad=0.306p pd=2.48u as=2.28p ps=27.72u w=0.9u l=0.45u
X5 VDD a_264_8832# a_300_8922# VDD sg13_hv_pmos ad=0.408p pd=3.08u as=0.228p ps=1.58u w=1.2u l=0.45u
X6 SH_OUT a_300_8922# SH_OUT VDD sg13_hv_pmos ad=0.171p pd=1.28u as=0.38703n ps=3.69626m w=0.9u l=0.45u
X7 SH_IN a_264_8832# SH_OUT VDD sg13_hv_pmos ad=0.306p pd=2.48u as=0.171p ps=1.28u w=0.9u l=0.45u
X8 a_300_8922# a_264_8832# VDD VDD sg13_hv_pmos ad=0.228p pd=1.58u as=0.408p ps=3.08u w=1.2u l=0.45u
X9 a_264_7974# SH_EN VDD VDD sg13_hv_pmos ad=0.408p pd=3.08u as=0.408p ps=3.08u w=1.2u l=0.45u
X10 SH_IN a_264_8832# SH_IN VSS sg13_hv_nmos ad=0.102p pd=1.28u as=0 ps=0 w=0.3u l=0.45u
X11 VSS a_264_8832# a_300_8922# VSS sg13_hv_nmos ad=0.204p pd=1.88u as=0.114p ps=0.98u w=0.6u l=0.45u
X12 VDD a_264_8320# a_264_8832# VDD sg13_hv_pmos ad=0.408p pd=3.08u as=0.228p ps=1.58u w=1.2u l=0.45u
X13 a_300_8922# a_264_8832# VSS VSS sg13_hv_nmos ad=0.114p pd=0.98u as=0.204p ps=1.88u w=0.6u l=0.45u
X14 a_264_7974# SH_EN VSS VSS sg13_hv_nmos ad=0.204p pd=1.88u as=0.204p ps=1.88u w=0.6u l=0.45u
X15 a_264_8832# a_264_8320# VDD VDD sg13_hv_pmos ad=0.228p pd=1.58u as=0.408p ps=3.08u w=1.2u l=0.45u
X16 a_264_8320# a_264_7974# VDD VDD sg13_hv_pmos ad=0.408p pd=3.08u as=0.408p ps=3.08u w=1.2u l=0.45u
X17 SH_OUT a_264_8832# SH_OUT VSS sg13_hv_nmos ad=57f pd=0.68u as=0 ps=0 w=0.3u l=0.45u
X18 SH_IN a_264_8320# SH_OUT VSS sg13_hv_nmos ad=0.102p pd=1.28u as=57f ps=0.68u w=0.3u l=0.45u
X19 VSS a_264_8320# a_264_8832# VSS sg13_hv_nmos ad=0.204p pd=1.88u as=0.114p ps=0.98u w=0.6u l=0.45u
.ends

