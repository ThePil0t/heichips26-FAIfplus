v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {Testbench sah_12bit - acquisition, pedestal and static error with the op_amp_ver_2 follower as driver} 80 -1500 0 0 0.7 0.7 {}
T {One run per (step, hold cap, opamp bias): track at VLEV -> hold (pedestal from the real source impedance), VIN steps to VFAR 1 us
into the hold window, so the follower output has slewed and settled before the next track -> track: the hold cap is recharged
from VLEV to VFAR through the switch by the follower (class-AB output, local Miller loop, then the main loop): settling time to
1/4 and 1/2 LSB (12 bit) of the final value, final static error v(sh_out) - VFAR -> hold: pedestal at VFAR.
Results: simulations/sah_12bit_opamp_tb_tran.txt} 80 -1440 0 0 0.3 0.3 {}
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
.param TTRK1=5u
.param THLD=30u
.param TTRK2=20u
.param TF=1n
.param TPED=200n
.param TINR=100n
.param VLEV=0.5
.param VFAR=2.8
.param TH1=\{TTRK1\}
.param TA=\{TTRK1+TF+THLD\}
.param TH2=\{TA+TF+TTRK2\}
.csparam th1=\{TH1\}
.csparam ta=\{TA\}
.csparam th2=\{TH2\}
.csparam tf=\{TF\}
.csparam tped=\{TPED\}
.csparam tstop=\{TH2+TF+TPED+50n\}
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
  set outtxt = sah_12bit_opamp_tb_tran.txt
  set outraw = sah_12bit_opamp_tb_tran.raw
  if $?pvt_tag
    set outtxt = \\"sah_12bit_opamp_tb_tran$pvt_tag$ext_txt\\"
    set outraw = \\"sah_12bit_opamp_tb_tran$pvt_tag$ext_raw\\"
  end
  ** sah_12bit switch for these runs (frozen sizes unless overridden with ngspice -D sw_wnf/sw_wpf/sw_msw)
  set wnf = 0.6
  set wpf = 1.8
  set msw = 1
  if $?sw_wnf
    set wnf = $sw_wnf
  end
  if $?sw_wpf
    set wpf = $sw_wpf
  end
  if $?sw_msw
    set msw = $sw_msw
  end
  ** ===== steps (VLEV -> VFAR), hold caps, opamp bias =====
  set v1_l = ( 0.5 2.8 1.6 1.65 )
  set v2_l = ( 2.8 0.5 1.7 1.66 )
  set steps = ( 1 2 3 4 )
  set ibs = ( 25n 50n 100n )
  ** 0.26 / 1 / 2 / 4 pF and the chosen 1.21 pF at -35 % / nominal / +35 %
  set cws = ( 13.35 48.95 97.9 194.91 39.16 59.63 80.1 )
  if $?pvt_temp
    set ibs = ( 25n )
    set cws = ( 59.63 )
  end
  if $?quick
    set steps = ( 1 )
    set ibs = ( 25n )
    set cws = ( 48.95 )
  end
  ** parallel runs: ngspice -D run_sel=<1..21> -D pvt_tag=_r<n> -> one (bias, cap) pair each
  if $?run_sel
    set rsel = $run_sel
    set ib_r = ( 25n 25n 25n 25n 25n 25n 25n 50n 50n 50n 50n 50n 50n 50n 100n 100n 100n 100n 100n 100n 100n )
    set cw_r = ( 13.35 48.95 97.9 194.91 39.16 59.63 80.1 13.35 48.95 97.9 194.91 39.16 59.63 80.1 13.35 48.95 97.9 194.91 39.16 59.63 80.1 )
    set ibs = ( $ib_r[$rsel] )
    set cws = ( $cw_r[$rsel] )
  end
  echo corner temp_C vdd_V ibias cw_um vlev_V vfar_V ped_mV ped2_mV tset_q_us tset_h_us err_final_mV > $outtxt
  foreach temp_c $temps
  foreach vdd $vdds
  foreach ib $ibs
  foreach cw $cws
  foreach st $steps
    alterparam VDDA = $vdd
    alterparam IBIAS = $ib
    alterparam CWP = $cw
    alterparam WNFP = $wnf
    alterparam WPFP = $wpf
    alterparam MSWP = $msw
    alterparam VLEV = $v1_l[$st]
    alterparam VFAR = $v2_l[$st]
    reset
    option temp = $temp_c
    save v(sh_out) v(ooa) v(vin)
    tran 1n $&tstop 0 20n
    let lsb = $vdd/4096
    let tpre1 = th1 - 1n
    let tped1 = th1 + tf + tped
    meas tran vtrk find v(sh_out) at=$&tpre1
    meas tran vped find v(sh_out) at=$&tped1
    let ped_mv = (vped - vtrk)*1e3
    let tpre2 = th2 - 1n
    meas tran vfin find v(sh_out) at=$&tpre2
    meas tran vinf find v(vin) at=$&tpre2
    let err = abs(v(sh_out) - vfin)
    meas tran errmax max err from=$&ta to=$&tpre2
    let tolq = lsb/4
    let tolh = lsb/2
    let tset_q = 0
    let tset_h = 0
    if errmax > tolq
      meas tran tq when err=$&tolq fall=last from=$&ta to=$&tpre2
      let tset_q = (tq - ta)*1e6
    end
    if errmax > tolh
      meas tran tqh when err=$&tolh fall=last from=$&ta to=$&tpre2
      let tset_h = (tqh - ta)*1e6
    end
    let errf = (vfin - vinf)*1e3
    let tped2 = th2 + tf + tped
    meas tran vped2 find v(sh_out) at=$&tped2
    let ped2_mv = (vped2 - vfin)*1e3
    echo $pvt_corner $temp_c $vdd $ib $cw $v1_l[$st] $v2_l[$st] $&ped_mv $&ped2_mv $&tset_q $&tset_h $&errf >> $outtxt
    destroy all
  end
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
C {vsource.sym} 300 -560 0 0 {name=VIN value="pwl(0 \{VLEV\} \{TH1+1u\} \{VLEV\} \{TH1+1u+TINR\} \{VFAR\})" savecurrent=false}
C {lab_pin.sym} 300 -590 0 1 {name=lp3 sig_type=std_logic lab=vin}
C {gnd.sym} 300 -530 0 0 {name=lg4 lab=GND}
C {vsource.sym} 480 -560 0 0 {name=VSHEN value="pwl(0 \{VDDA\} \{TH1\} \{VDDA\} \{TH1+TF\} 0 \{TA\} 0 \{TA+TF\} \{VDDA\} \{TH2\} \{VDDA\} \{TH2+TF\} 0)" savecurrent=false}
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
