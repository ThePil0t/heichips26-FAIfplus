* NGSPICE file created from 555_comparator.ext - technology: ihp-sg13cmos5l

.subckt x555_comparator INN INP GNDA OUT VCCA PBIAS
X0 OUT a_3380_528# GNDA GNDA sg13_hv_nmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=0.45u
X1 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.85p pd=5.68u as=0.13787n ps=0.22884m w=2.5u l=0.45u
X2 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.272p pd=2.28u as=0 ps=0 w=0.8u l=1u
X3 a_422_188# INN a_1056_1862# VCCA sg13_hv_pmos ad=1.7p pd=10.68u as=1.7p ps=10.68u w=5u l=0.45u
X4 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.85p pd=5.68u as=0 ps=0 w=2.5u l=0.45u
X5 GNDA GNDA GNDA GNDA sg13_hv_nmos ad=0.408p pd=3.08u as=27.3426p ps=80.55u w=1.2u l=0.45u
X6 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.85p pd=5.68u as=0 ps=0 w=2.5u l=0.45u
X7 VCCA a_1964_278# a_3380_528# VCCA sg13_hv_pmos ad=0.204p pd=1.88u as=0.204p ps=1.88u w=0.6u l=0.45u
X8 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.272p pd=2.28u as=0 ps=0 w=0.8u l=1u
X9 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.85p pd=5.68u as=0 ps=0 w=2.5u l=0.45u
X10 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.85p pd=5.68u as=0 ps=0 w=2.5u l=0.45u
X11 a_1964_278# a_746_388# GNDA GNDA sg13_hv_nmos ad=0.816p pd=5.48u as=0.816p ps=5.48u w=2.4u l=0.45u
X12 a_1056_1862# INN a_422_188# VCCA sg13_hv_pmos ad=1.7p pd=10.68u as=1.7p ps=10.68u w=5u l=0.45u
X13 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.85p pd=5.68u as=0 ps=0 w=2.5u l=0.45u
X14 a_3380_528# a_1964_278# GNDA GNDA sg13_hv_nmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=0.45u
X15 VCCA a_3380_528# OUT VCCA sg13_hv_pmos ad=0.204p pd=1.88u as=0.204p ps=1.88u w=0.6u l=0.45u
X16 VCCA a_3380_528# OUT VCCA sg13_hv_pmos ad=0.204p pd=1.88u as=0.204p ps=1.88u w=0.6u l=0.45u
X17 VCCA PBIAS a_1056_1862# VCCA sg13_hv_pmos ad=0.272p pd=2.28u as=0.272p ps=2.28u w=0.8u l=1u
X18 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.85p pd=5.68u as=0 ps=0 w=2.5u l=0.45u
X19 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=0.45u
X20 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=0.85p pd=5.68u as=0 ps=0 w=2.5u l=0.45u
X21 a_1056_1862# INP a_746_388# VCCA sg13_hv_pmos ad=1.7p pd=10.68u as=1.7p ps=10.68u w=5u l=0.45u
X22 GNDA GNDA GNDA GNDA sg13_hv_nmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X23 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=0.45u
X24 a_422_188# a_422_188# GNDA GNDA sg13_hv_nmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X25 a_746_388# a_422_188# GNDA GNDA sg13_hv_nmos ad=0.136p pd=1.48u as=0.136p ps=1.48u w=0.4u l=1u
X26 OUT a_3380_528# GNDA GNDA sg13_hv_nmos ad=0.102p pd=1.28u as=0.102p ps=1.28u w=0.3u l=0.45u
X27 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=0.45u
X28 GNDA GNDA GNDA GNDA sg13_hv_nmos ad=0.136p pd=1.48u as=0 ps=0 w=0.4u l=1u
X29 VCCA PBIAS a_1964_278# VCCA sg13_hv_pmos ad=0.272p pd=2.28u as=0.272p ps=2.28u w=0.8u l=1u
X30 a_746_388# INP a_1056_1862# VCCA sg13_hv_pmos ad=1.7p pd=10.68u as=1.7p ps=10.68u w=5u l=0.45u
X31 VCCA VCCA VCCA VCCA sg13_hv_pmos ad=1.7p pd=10.68u as=0 ps=0 w=5u l=0.45u
X32 GNDA GNDA GNDA GNDA sg13_hv_nmos ad=0.408p pd=3.08u as=0 ps=0 w=1.2u l=0.45u
.ends

