v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {sah_12bit - single-ended track & hold for 12 bit (HV transmission gate, dummies, MOM hold cap)} 40 -1160 0 0 0.6 0.6 {}
T {SH_EN = 1: track, SH_EN = 0: hold. Hold cap C1 = cap_cmomi 59.63 x 25.2 um, M1-M3: 1.214 pF nominal
(sized for a +-35 % cap spread, + ~0.05 pF switch/comparator parasitics). Switch: main NMOS 0.6/0.45 um and main PMOS
1.8/0.45 um (2 fingers each); dummies = one finger of the main device. Sized for the op_amp_ver_2 follower as driver.
Gate-driver chain SH_EN -> I1 -> I2 (sw) -> I3 (sw_b) -> I4 (sw_d): the main NMOS turns off first (sw), then the main PMOS and the
NMOS dummies (sw_b), then the PMOS dummies (sw_d). So every dummy switches after its main device, and the edges at the switch
gates are sharp and independent of the SH_EN slope.
Parametrized copy for the sweeps: ../../testbenches/xschem/sah_12bit_param.sch. Sizing: ../../docs/hold_cap_sizing.md} 40 -1100 0 0 0.3 0.3 {}
T {main switch} 380 -920 0 0 0.4 0.4 {}
C {sg13cmos5l_pr/sg13_hv_nmos.sym} 400 -740 0 0 {name=MN1
l=0.45u
w=0.6u
ng=2
m=1
mm_ok=1
model=sg13_hv_nmos
spiceprefix=X
}
C {lab_pin.sym} 420 -770 0 1 {name=l1 sig_type=std_logic lab=SH_IN}
C {lab_pin.sym} 420 -710 0 1 {name=l2 sig_type=std_logic lab=SH_OUT}
C {lab_pin.sym} 380 -740 0 0 {name=l3 sig_type=std_logic lab=sw}
C {lab_pin.sym} 420 -740 0 1 {name=l4 sig_type=std_logic lab=VSS}
C {sg13cmos5l_pr/sg13_hv_pmos.sym} 400 -860 0 0 {name=MP1
l=0.45u
w=1.8u
ng=2
m=1
mm_ok=1
model=sg13_hv_pmos
spiceprefix=X
}
C {lab_pin.sym} 420 -830 0 1 {name=l5 sig_type=std_logic lab=SH_IN}
C {lab_pin.sym} 420 -890 0 1 {name=l6 sig_type=std_logic lab=SH_OUT}
C {lab_pin.sym} 380 -860 0 0 {name=l7 sig_type=std_logic lab=sw_b}
C {lab_pin.sym} 420 -860 0 1 {name=l8 sig_type=std_logic lab=VDD}
T {dummies SH_IN side} 680 -920 0 0 0.4 0.4 {}
C {sg13cmos5l_pr/sg13_hv_nmos.sym} 700 -740 0 0 {name=MND1
l=0.45u
w=0.3u
ng=1
m=1
mm_ok=1
model=sg13_hv_nmos
spiceprefix=X
}
C {lab_pin.sym} 720 -770 0 1 {name=l9 sig_type=std_logic lab=SH_IN}
C {lab_pin.sym} 720 -710 0 1 {name=l10 sig_type=std_logic lab=SH_IN}
C {lab_pin.sym} 680 -740 0 0 {name=l11 sig_type=std_logic lab=sw_b}
C {lab_pin.sym} 720 -740 0 1 {name=l12 sig_type=std_logic lab=VSS}
C {sg13cmos5l_pr/sg13_hv_pmos.sym} 700 -860 0 0 {name=MPD1
l=0.45u
w=0.9u
ng=1
m=1
mm_ok=1
model=sg13_hv_pmos
spiceprefix=X
}
C {lab_pin.sym} 720 -830 0 1 {name=l13 sig_type=std_logic lab=SH_IN}
C {lab_pin.sym} 720 -890 0 1 {name=l14 sig_type=std_logic lab=SH_IN}
C {lab_pin.sym} 680 -860 0 0 {name=l15 sig_type=std_logic lab=sw_d}
C {lab_pin.sym} 720 -860 0 1 {name=l16 sig_type=std_logic lab=VDD}
T {dummies SH_OUT side} 980 -920 0 0 0.4 0.4 {}
C {sg13cmos5l_pr/sg13_hv_nmos.sym} 1000 -740 0 0 {name=MND2
l=0.45u
w=0.3u
ng=1
m=1
mm_ok=1
model=sg13_hv_nmos
spiceprefix=X
}
C {lab_pin.sym} 1020 -770 0 1 {name=l17 sig_type=std_logic lab=SH_OUT}
C {lab_pin.sym} 1020 -710 0 1 {name=l18 sig_type=std_logic lab=SH_OUT}
C {lab_pin.sym} 980 -740 0 0 {name=l19 sig_type=std_logic lab=sw_b}
C {lab_pin.sym} 1020 -740 0 1 {name=l20 sig_type=std_logic lab=VSS}
C {sg13cmos5l_pr/sg13_hv_pmos.sym} 1000 -860 0 0 {name=MPD2
l=0.45u
w=0.9u
ng=1
m=1
mm_ok=1
model=sg13_hv_pmos
spiceprefix=X
}
C {lab_pin.sym} 1020 -830 0 1 {name=l21 sig_type=std_logic lab=SH_OUT}
C {lab_pin.sym} 1020 -890 0 1 {name=l22 sig_type=std_logic lab=SH_OUT}
C {lab_pin.sym} 980 -860 0 0 {name=l23 sig_type=std_logic lab=sw_d}
C {lab_pin.sym} 1020 -860 0 1 {name=l24 sig_type=std_logic lab=VDD}
T {gate-driver chain} 380 -560 0 0 0.4 0.4 {}
C {sg13cmos5l_pr/sg13_hv_pmos.sym} 400 -460 0 0 {name=MPI1
l=0.45u
w=1.2u
ng=1
m=1
mm_ok=1
model=sg13_hv_pmos
spiceprefix=X
}
C {lab_pin.sym} 420 -430 0 1 {name=l25 sig_type=std_logic lab=sw_n}
C {lab_pin.sym} 420 -490 0 1 {name=l26 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 380 -460 0 0 {name=l27 sig_type=std_logic lab=SH_EN}
C {lab_pin.sym} 420 -460 0 1 {name=l28 sig_type=std_logic lab=VDD}
C {sg13cmos5l_pr/sg13_hv_nmos.sym} 400 -320 0 0 {name=MNI1
l=0.45u
w=0.6u
ng=1
m=1
mm_ok=1
model=sg13_hv_nmos
spiceprefix=X
}
C {lab_pin.sym} 420 -350 0 1 {name=l29 sig_type=std_logic lab=sw_n}
C {lab_pin.sym} 420 -290 0 1 {name=l30 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 380 -320 0 0 {name=l31 sig_type=std_logic lab=SH_EN}
C {lab_pin.sym} 420 -320 0 1 {name=l32 sig_type=std_logic lab=VSS}
C {sg13cmos5l_pr/sg13_hv_pmos.sym} 600 -460 0 0 {name=MPI2
l=0.45u
w=1.2u
ng=1
m=1
mm_ok=1
model=sg13_hv_pmos
spiceprefix=X
}
C {lab_pin.sym} 620 -430 0 1 {name=l33 sig_type=std_logic lab=sw}
C {lab_pin.sym} 620 -490 0 1 {name=l34 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 580 -460 0 0 {name=l35 sig_type=std_logic lab=sw_n}
C {lab_pin.sym} 620 -460 0 1 {name=l36 sig_type=std_logic lab=VDD}
C {sg13cmos5l_pr/sg13_hv_nmos.sym} 600 -320 0 0 {name=MNI2
l=0.45u
w=0.6u
ng=1
m=1
mm_ok=1
model=sg13_hv_nmos
spiceprefix=X
}
C {lab_pin.sym} 620 -350 0 1 {name=l37 sig_type=std_logic lab=sw}
C {lab_pin.sym} 620 -290 0 1 {name=l38 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 580 -320 0 0 {name=l39 sig_type=std_logic lab=sw_n}
C {lab_pin.sym} 620 -320 0 1 {name=l40 sig_type=std_logic lab=VSS}
C {sg13cmos5l_pr/sg13_hv_pmos.sym} 800 -460 0 0 {name=MPI3
l=0.45u
w=1.2u
ng=1
m=2
mm_ok=1
model=sg13_hv_pmos
spiceprefix=X
}
C {lab_pin.sym} 820 -430 0 1 {name=l41 sig_type=std_logic lab=sw_b}
C {lab_pin.sym} 820 -490 0 1 {name=l42 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 780 -460 0 0 {name=l43 sig_type=std_logic lab=sw}
C {lab_pin.sym} 820 -460 0 1 {name=l44 sig_type=std_logic lab=VDD}
C {sg13cmos5l_pr/sg13_hv_nmos.sym} 800 -320 0 0 {name=MNI3
l=0.45u
w=0.6u
ng=1
m=2
mm_ok=1
model=sg13_hv_nmos
spiceprefix=X
}
C {lab_pin.sym} 820 -350 0 1 {name=l45 sig_type=std_logic lab=sw_b}
C {lab_pin.sym} 820 -290 0 1 {name=l46 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 780 -320 0 0 {name=l47 sig_type=std_logic lab=sw}
C {lab_pin.sym} 820 -320 0 1 {name=l48 sig_type=std_logic lab=VSS}
C {sg13cmos5l_pr/sg13_hv_pmos.sym} 1000 -460 0 0 {name=MPI4
l=0.45u
w=1.2u
ng=1
m=2
mm_ok=1
model=sg13_hv_pmos
spiceprefix=X
}
C {lab_pin.sym} 1020 -430 0 1 {name=l49 sig_type=std_logic lab=sw_d}
C {lab_pin.sym} 1020 -490 0 1 {name=l50 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 980 -460 0 0 {name=l51 sig_type=std_logic lab=sw_b}
C {lab_pin.sym} 1020 -460 0 1 {name=l52 sig_type=std_logic lab=VDD}
C {sg13cmos5l_pr/sg13_hv_nmos.sym} 1000 -320 0 0 {name=MNI4
l=0.45u
w=0.6u
ng=1
m=2
mm_ok=1
model=sg13_hv_nmos
spiceprefix=X
}
C {lab_pin.sym} 1020 -350 0 1 {name=l53 sig_type=std_logic lab=sw_d}
C {lab_pin.sym} 1020 -290 0 1 {name=l54 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 980 -320 0 0 {name=l55 sig_type=std_logic lab=sw_b}
C {lab_pin.sym} 1020 -320 0 1 {name=l56 sig_type=std_logic lab=VSS}
T {hold capacitor} 1260 -560 0 0 0.4 0.4 {}
C {sg13cmos5l_pr/cap_cmomi.sym} 1300 -400 0 0 {name=C1
model=cap_cmomi
w=59.63e-6
l=25.2e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {lab_pin.sym} 1300 -430 0 1 {name=l57 sig_type=std_logic lab=SH_OUT}
C {lab_pin.sym} 1300 -370 0 1 {name=l58 sig_type=std_logic lab=VSS}
C {ipin.sym} 80 -900 0 0 {name=p1 lab=SH_IN}
C {ipin.sym} 80 -860 0 0 {name=p2 lab=SH_EN}
C {opin.sym} 200 -900 0 0 {name=p3 lab=SH_OUT}
C {iopin.sym} 80 -820 2 0 {name=p4 lab=VDD}
C {iopin.sym} 80 -780 2 0 {name=p5 lab=VSS}
C {title.sym} 160 0 0 0 {name=l0 author="FAIf team"}
