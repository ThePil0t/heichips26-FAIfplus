* NGSPICE file created from sah_12bit.ext - technology: ihp-sg13cmos5l

.subckt sah_12bit SH_EN VDD SH_IN SH_OUT VSS
X0 SH_OUT a_3074_12451# SH_OUT VDD sg13_hv_pmos ad=0.171p pd=1.28u as=0.38703n ps=3.69626m w=0.9u l=0.45u
X1 a_2908_12512# a_2908_12134# VSS VSS sg13_hv_nmos ad=0.114p pd=0.98u as=0.204p ps=1.88u w=0.6u l=0.45u
X2 VSS a_2908_12512# a_3074_12451# VSS sg13_hv_nmos ad=0.204p pd=1.88u as=0.114p ps=0.98u w=0.6u l=0.45u
X3 a_3074_12451# a_2908_12512# VSS VSS sg13_hv_nmos ad=0.114p pd=0.98u as=0.204p ps=1.88u w=0.6u l=0.45u
X4 SH_OUT a_2908_12512# SH_OUT VSS sg13_hv_nmos ad=57f pd=0.68u as=0 ps=0 w=0.3u l=0.45u
X5 VDD a_6716_11964# a_2908_12134# VDD sg13_hv_pmos ad=0.408p pd=3.08u as=0.408p ps=3.08u w=1.2u l=0.45u
X6 VSS SH_EN a_6716_11964# VSS sg13_hv_nmos ad=0.204p pd=1.88u as=0.204p ps=1.88u w=0.6u l=0.45u
X7 VSS a_2908_12134# a_2908_12512# VSS sg13_hv_nmos ad=0.204p pd=1.88u as=0.114p ps=0.98u w=0.6u l=0.45u
X8 a_2908_12512# a_2908_12134# VDD VDD sg13_hv_pmos ad=0.228p pd=1.58u as=0.408p ps=3.08u w=1.2u l=0.45u
X9 a_3074_12451# a_2908_12512# VDD VDD sg13_hv_pmos ad=0.228p pd=1.58u as=0.408p ps=3.08u w=1.2u l=0.45u
X10 VDD a_2908_12512# a_3074_12451# VDD sg13_hv_pmos ad=0.408p pd=3.08u as=0.228p ps=1.58u w=1.2u l=0.45u
X11 SH_OUT a_2908_12512# SH_IN VDD sg13_hv_pmos ad=0.171p pd=1.28u as=0.306p ps=2.48u w=0.9u l=0.45u
X12 SH_IN a_2908_12512# SH_OUT VDD sg13_hv_pmos ad=0.171p pd=1.28u as=0.171p ps=1.28u w=0.9u l=0.45u
X13 SH_IN a_3074_12451# SH_IN VDD sg13_hv_pmos ad=0.171p pd=1.28u as=2.28p ps=27.72u w=0.9u l=0.45u
X14 VSS a_6716_11964# a_2908_12134# VSS sg13_hv_nmos ad=0.204p pd=1.88u as=0.204p ps=1.88u w=0.6u l=0.45u
X15 VDD SH_EN a_6716_11964# VDD sg13_hv_pmos ad=0.408p pd=3.08u as=0.408p ps=3.08u w=1.2u l=0.45u
X16 SH_OUT a_2908_12134# SH_IN VSS sg13_hv_nmos ad=57f pd=0.68u as=0.102p ps=1.28u w=0.3u l=0.45u
X17 VDD a_2908_12134# a_2908_12512# VDD sg13_hv_pmos ad=0.408p pd=3.08u as=0.228p ps=1.58u w=1.2u l=0.45u
X18 SH_IN a_2908_12134# SH_OUT VSS sg13_hv_nmos ad=57f pd=0.68u as=57f ps=0.68u w=0.3u l=0.45u
X19 SH_IN a_2908_12512# SH_IN VSS sg13_hv_nmos ad=57f pd=0.68u as=0 ps=0 w=0.3u l=0.45u
.ends

