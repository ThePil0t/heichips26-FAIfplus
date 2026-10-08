* NGSPICE file created from ptat_curr_gen.ext - technology: ihp-sg13cmos5l

.subckt ptat_curr_gen CSOUT4 PBIAS PCSVDD CSOUT1 CSOUT2 CSOUT3 PCSVSS
X0 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=76.2832p ps=0.15327m w=0.4u l=1u
X1 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X2 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=0.68p pd=4.68u as=0.25442n ps=0.5791m w=2u l=2u
X3 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=0.34p pd=2.68u as=0 ps=0 w=1u l=2u
X4 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X5 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X6 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=2u
X7 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=3.4p pd=20.68u as=0 ps=0 w=10u l=2u
X8 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X9 PCSVDD PBIAS PBIAS PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X10 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=0.34p pd=2.68u as=0 ps=0 w=1u l=2u
X11 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=0.34p pd=2.68u as=0 ps=0 w=1u l=2u
X12 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=2u
X13 PCSVSS a_1378_1075# PCSVSS rhigh l=0.68478m w=0.5u
X14 PCSVDD PBIAS CSOUT3 PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X15 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X16 PCSVDD PBIAS w_8420_5504# PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X17 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=0.34p pd=2.68u as=0 ps=0 w=1u l=2u
X18 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X19 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X20 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=2u
X21 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X22 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=0.68p pd=4.68u as=0 ps=0 w=2u l=2u
X23 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X24 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X25 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X26 a_1296_1177# a_1296_1177# PCSVSS PCSVSS sg13_hv_nmos ad=0.68p pd=4.68u as=0.68p ps=4.68u w=2u l=2u
X27 w_8420_4776# w_8420_4776# w_8420_5504# w_8420_5504# sg13_hv_pmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=3u
X28 w_8420_3320# w_8420_3320# w_8420_4048# w_8420_4048# sg13_hv_pmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=3u
X29 w_8420_3320# w_8420_2592# w_8420_2592# w_8420_3320# sg13_hv_pmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=3u
X30 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X31 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X32 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X33 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=2u
X34 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.102p pd=1.28u as=0 ps=0 w=0.3u l=3u
X35 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X36 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X37 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X38 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=0.34p pd=2.68u as=0 ps=0 w=1u l=2u
X39 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.102p pd=1.28u as=0 ps=0 w=0.3u l=3u
X40 PCSVDD PBIAS CSOUT4 PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X41 PCSVDD PBIAS CSOUT1 PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X42 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=0.34p pd=2.68u as=0 ps=0 w=1u l=2u
X43 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=2u
X44 PBIAS a_1296_1177# a_1378_1075# PCSVSS sg13_hv_nmos ad=3.4p pd=20.68u as=3.4p ps=20.68u w=10u l=2u
X45 PCSVDD PBIAS a_1296_1177# PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X46 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=3.4p pd=20.68u as=0 ps=0 w=10u l=2u
X47 w_8420_4776# w_8420_4048# w_8420_4048# w_8420_4776# sg13_hv_pmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=3u
X48 PCSVDD PBIAS CSOUT2 PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X49 PBIAS w_8420_5504# PCSVSS PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X50 PCSVSS PCSVSS w_8420_2592# w_8420_2592# sg13_hv_pmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=3u
X51 PCSVSS PCSVSS PCSVSS PCSVSS sg13_hv_nmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=2u
X52 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X53 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X54 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X55 PCSVDD PCSVDD PCSVDD PCSVDD sg13_hv_pmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
.ends

