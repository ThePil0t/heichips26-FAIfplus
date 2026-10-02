v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {Testbench sah_12bit - pedestal vs input level with the op_amp_ver_2 follower as driver (switch sizing)} 80 -1500 0 0 0.7 0.7 {}
T {Track at VLEV (settled from the operating point) -> hold edge -> pedestal = v(sh_out) TPED after the edge - v(sh_out) just before.
The channel charge splits between the hold cap and the follower output, whose high-frequency impedance (class-AB output, Miller caps)
sets the split - so the dummy fractions KDN/KDP that cancel it differ from the ideal-source case (sah_12bit_ideal_tb_tran).
One run per (setup, VLEV); setups = switch widths, dummy fractions, length, hold cap. Parallel: -D run_sel=<setup> -D pvt_tag=_r<n>.
Results: simulations/sah_12bit_opamp_tb_ped.txt} 80 -1440 0 0 0.3 0.3 {}
C {code_shown.sym} 80 -1250 0 0 {name=PVT only_toplevel=true
format="tcleval( @value )"
value="** ===== PVT setup =====
** Process corner (one per run): mos_tt / mos_ss / mos_ff / mos_sf / mos_fs.
** 'make sim-xschem-pvt' replaces mos_tt for every PVT point, keep this token.
.lib cornerMOShv.lib mos_tt
.lib cornerMOSlv.lib mos_tt
** MOM caps: low-frequency equivalent of cap_cmomi (same C equations, no RF branches, no GLEAK),
** see ../cap_cmomi_lf.spice. The PDK cap model has no corner spread (cap_typ = cap_bcs = cap_wcs).
.include ../cap_cmomi_lf.spice
.param VDDA=3.3
.temp 27
"}
C {code_shown.sym} 80 -1000 0 0 {name=PARAMS only_toplevel=true
value="** ===== stimulus =====
.param TTRK1=2u
.param TF=1n
.param TPED=200n
.param VLEV=1.65
.param TH1=\{TTRK1\}
.csparam th1=\{TH1\}
.csparam tf=\{TF\}
.csparam tped=\{TPED\}
.csparam tstop=\{TH1+TF+TPED+20n\}
** opamp bias (PTAT CSOUT in the top level), comparator bias, DAC level at the comparator INP
.param IBIAS=25n
.param IBCOMP=100n
.param VDAC=1.65
.param SHEN=1
** ===== sah_12bit sizes (um), set per run by the NGSPICE block =====
.param WNFP=0.6 WPFP=1.8 LSWP=0.45 MSWP=1 KDNP=0.5 KDPP=0.5 CWP=59.63 CLP=25.2
** follower feedback
VFB ooa fb 0
"}
C {code_shown.sym} 700 -1250 0 0 {name=NGSPICE only_toplevel=true
value="
** reltol 1e-5 / abstol 1e-15: the 25 nA opamp does not converge with tighter settings (pedestal accuracy ~10 uV)
.options method=gear reltol=1e-5 vntol=1e-9 abstol=1e-15 chgtol=1e-18 gmin=1e-18
.control
  set temps = ( 27 )
  set vdds = ( 3.3 )
  if $?pvt_temp
    set temps = ( $pvt_temp )
  end
  if $?pvt_vdd
    set vdds = ( $pvt_vdd )
  end
  if $?pvt_corner
  else
    set pvt_corner = tt
  end
  set ext_txt = .txt
  set ext_raw = .raw
  set outtxt = sah_12bit_opamp_tb_ped.txt
  set outraw = sah_12bit_opamp_tb_ped.raw
  if $?pvt_tag
    set outtxt = \\"sah_12bit_opamp_tb_ped$pvt_tag$ext_txt\\"
    set outraw = \\"sah_12bit_opamp_tb_ped$pvt_tag$ext_raw\\"
  end
  ** ===== run setups (one column each) =====
  set cw_l = ( 48.95 48.95 )
  set wn_l = ( 0.6 0.6 )
  set wp_l = ( 1.5 1.8 )
  set kn_l = ( 0.5 0.5 )
  set kp_l = ( 0.5 0.5 )
  set ls_l = ( 0.45 0.45 )
  set runs = ( 1 2 )
  if $?pvt_temp
    set runs = ( 2 )
  end
  if $?run_sel
    set runs = ( $run_sel )
  end
  set ib = 25n
  if $?ibias
    set ib = $ibias
  end
  set vlevs = ( 0.45 0.65 0.85 1.05 1.25 1.45 1.65 1.85 2.05 2.25 2.45 2.65 2.85 3.05 3.2 )
  echo corner temp_C vdd_V ibias run cw_um wnf_um wpf_um lsw_um kdn kdp vlev_V ped_mV > $outtxt
  foreach temp_c $temps
  foreach vdd $vdds
  foreach r $runs
  foreach vl $vlevs
    alterparam VDDA = $vdd
    alterparam IBIAS = $ib
    alterparam CWP = $cw_l[$r]
    alterparam WNFP = $wn_l[$r]
    alterparam WPFP = $wp_l[$r]
    alterparam KDNP = $kn_l[$r]
    alterparam KDPP = $kp_l[$r]
    alterparam LSWP = $ls_l[$r]
    alterparam VLEV = $vl
    alterparam VDAC = $vl
    reset
    option temp = $temp_c
    save v(sh_out)
    tran 1n $&tstop 0 10n
    let tpre1 = th1 - 1n
    let tped1 = th1 + tf + tped
    meas tran vtrk find v(sh_out) at=$&tpre1
    meas tran vped find v(sh_out) at=$&tped1
    let ped_mv = (vped - vtrk)*1e3
    echo $pvt_corner $temp_c $vdd $ib $r $cw_l[$r] $wn_l[$r] $wp_l[$r] $ls_l[$r] $kn_l[$r] $kp_l[$r] $vl $&ped_mv >> $outtxt
    destroy all
  end
  end
  end
  end
  echo
  echo ===== Results: simulations/$outtxt =====
  shell cat $outtxt
.endc
"}
C {launcher.sym} 2400 -1500 0 0 {name=h1
descr="Simulate"
tclcommand="xschem save; xschem netlist; xschem simulate"
}
C {launcher.sym} 2400 -1450 0 0 {name=h2
descr="Load waves"
tclcommand="xschem raw_read $netlist_dir/[file rootname [file tail [xschem get current_name]]].raw tran"
}
C {vsource.sym} 120 -560 0 0 {name=VVDDA value=\{VDDA\} savecurrent=false}
C {lab_pin.sym} 120 -590 0 1 {name=lp1 sig_type=std_logic lab=VDDA}
C {gnd.sym} 120 -530 0 0 {name=lg2 lab=GND}
C {vsource.sym} 300 -560 0 0 {name=VIN value=\{VLEV\} savecurrent=false}
C {lab_pin.sym} 300 -590 0 1 {name=lp3 sig_type=std_logic lab=vin}
C {gnd.sym} 300 -530 0 0 {name=lg4 lab=GND}
C {vsource.sym} 480 -560 0 0 {name=VSHEN value="pwl(0 \{VDDA\} \{TH1\} \{VDDA\} \{TH1+TF\} 0)" savecurrent=false}
C {lab_pin.sym} 480 -590 0 1 {name=lp5 sig_type=std_logic lab=sh_en}
C {gnd.sym} 480 -530 0 0 {name=lg6 lab=GND}
C {vsource.sym} 660 -560 0 0 {name=VDACS value=\{VDAC\} savecurrent=false}
C {lab_pin.sym} 660 -590 0 1 {name=lp7 sig_type=std_logic lab=vdac}
C {gnd.sym} 660 -530 0 0 {name=lg8 lab=GND}
C {isource.sym} 840 -560 0 0 {name=IBIAS value=\{IBIAS\}}
C {lab_pin.sym} 840 -590 0 1 {name=lp9 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 840 -530 0 1 {name=lp10 sig_type=std_logic lab=iref}
C {op_amp_ver_2.sym} 1100 -560 0 0 {name=x1}
C {lab_pin.sym} 1110 -610 0 1 {name=lp11 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1070 -490 0 0 {name=lp12 sig_type=std_logic lab=iref}
C {lab_pin.sym} 1030 -580 0 0 {name=lp13 sig_type=std_logic lab=fb}
C {lab_pin.sym} 1200 -560 0 1 {name=lp14 sig_type=std_logic lab=ooa}
C {lab_pin.sym} 1030 -540 0 0 {name=lp15 sig_type=std_logic lab=vin}
C {gnd.sym} 1110 -510 0 0 {name=lg16 lab=GND}
C {gnd.sym} 1070 -630 0 0 {name=lg17 lab=GND}
C {sah_12bit_param.sym} 1400 -560 0 0 {name=x2 WNF=\{WNFP*1e-6\} WPF=\{WPFP*1e-6\} LSW=\{LSWP*1e-6\} MSW=\{MSWP\} KDN=\{KDNP\} KDP=\{KDPP\} MINV=\{MSWP\} CW=\{CWP*1e-6\} CL=\{CLP*1e-6\}}
C {lab_pin.sym} 1480 -640 0 1 {name=lp18 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1350 -590 0 0 {name=lp19 sig_type=std_logic lab=ooa}
C {lab_pin.sym} 1550 -590 0 1 {name=lp20 sig_type=std_logic lab=sh_out}
C {lab_pin.sym} 1420 -510 0 0 {name=lp21 sig_type=std_logic lab=sh_en}
C {gnd.sym} 1480 -510 0 0 {name=lg22 lab=GND}
C {555_comparator.sym} 1800 -560 0 0 {name=x3}
C {lab_pin.sym} 1840 -630 0 1 {name=lp23 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1820 -640 0 0 {name=lp24 sig_type=std_logic lab=pbias}
C {lab_pin.sym} 1950 -560 0 1 {name=lp25 sig_type=std_logic lab=cout}
C {lab_pin.sym} 1780 -580 0 0 {name=lp26 sig_type=std_logic lab=sh_out}
C {lab_pin.sym} 1780 -540 0 0 {name=lp27 sig_type=std_logic lab=vdac}
C {gnd.sym} 1840 -490 0 0 {name=lg28 lab=GND}
C {sg13cmos5l_pr/sg13_hv_pmos.sym} 2100 -560 0 0 {name=MPB
l=1u
w=0.8u
ng=1
m=1
mm_ok=1
model=sg13_hv_pmos
spiceprefix=X
}
C {lab_pin.sym} 2120 -530 0 1 {name=lp29 sig_type=std_logic lab=pbias}
C {lab_pin.sym} 2080 -560 0 0 {name=lp30 sig_type=std_logic lab=pbias}
C {lab_pin.sym} 2120 -590 0 1 {name=lp31 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 2120 -560 0 1 {name=lp32 sig_type=std_logic lab=VDDA}
C {isource.sym} 2120 -460 0 0 {name=IBC value=\{IBCOMP\}}
C {lab_pin.sym} 2120 -490 0 1 {name=lp33 sig_type=std_logic lab=pbias}
C {gnd.sym} 2120 -430 0 0 {name=lg34 lab=GND}
C {title.sym} 160 0 0 0 {name=l0 author="FAIf team"}
