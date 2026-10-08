v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {Testbench sah_12bit - final check of the frozen cell with the op_amp_ver_2 follower and the 555_comparator (PDK cap model)} 80 -1500 0 0 0.7 0.7 {}
T {sah_12bit_param at the frozen sah_12bit sizes (check_param_equiv.py verifies both netlists match), PDK cap_cmomi model (also in the
opamp Miller caps), real comparator load. Hold-cap spread (the PDK model has none, +-35 % assumed): cap corner wcs -> CW -35 %,
bcs -> CW +35 %, typ -> nominal (whole 0.89 um rows). PVT list: PVT_FINAL in the Makefile.
One run per step: track at VLEV -> hold: pedestal; VIN steps to VFAR 1 us into the hold (follower slews while the switch is open)
-> follower slew rate (20-80 %) on the step -> droop from 5 us after the step to the end of the hold (includes the open-switch leakage at full Vds) -> track: acquisition of the
full step, settling time to 1/4 and 1/2 LSB (12 bit), static error -> hold: pedestal at VFAR.
'make sim-xschem-pvt TB=sah_12bit_final_tb_tran PVT="$(PVT_FINAL)"' (make sim-all does this). Results: simulations/sah_12bit_final_tb_tran*.txt} 80 -1440 0 0 0.3 0.3 {}
C {code_shown.sym} 80 -1250 0 0 {name=PVT only_toplevel=true
format="tcleval( @value )"
value="** ===== PVT setup =====
** Process corner (one per run): mos_tt / mos_ss / mos_ff / mos_sf / mos_fs,
** MOM caps: cap_typ / cap_bcs / cap_wcs (the cap_cmomi model has no corner spread yet).
** 'make sim-xschem-pvt' replaces mos_tt and cap_typ for every PVT point, keep these tokens.
.lib cornerMOShv.lib mos_tt
.lib cornerMOSlv.lib mos_tt
.lib cornerCAP.lib cap_typ
.param VDDA=3.3
.temp 27
"}
C {code_shown.sym} 80 -1000 0 0 {name=PARAMS only_toplevel=true
value="** ===== stimulus =====
.param TTRK1=5u
.param THLD=40u
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
** frozen sah_12bit sizes (um); CWP is set from the cap corner in the NGSPICE block
.param WNFP=0.6 WPFP=1.8 LSWP=0.45 KDNP=0.5 KDPP=0.5 CWP=54.29 CLP=27.72
** opamp bias (PTAT CSOUT in the top level), comparator bias, DAC level at the comparator INP
.param IBIAS=25n
.param IBCOMP=100n
.param VDAC=1.65
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
  set outtxt = sah_12bit_final_tb_tran.txt
  set outraw = sah_12bit_final_tb_tran.raw
  if $?pvt_tag
    set outtxt = \\"sah_12bit_final_tb_tran$pvt_tag$ext_txt\\"
    set outraw = \\"sah_12bit_final_tb_tran$pvt_tag$ext_raw\\"
  end
  ** hold-cap spread: cap corner of the PVT point -> drawn cap width
  set cwf = 54.29
  if $?pvt_cap
    strcmp capw $pvt_cap wcs
    if $capw = 0
      set cwf = 35.6
    end
    strcmp capb $pvt_cap bcs
    if $capb = 0
      set cwf = 72.98
    end
  end
  set v1_l = ( 0.5 2.8 1.6 3.2 )
  set v2_l = ( 2.8 0.5 1.7 0.45 )
  set steps = ( 1 2 3 4 )
  if $?run_sel
    set steps = ( $run_sel )
  end
  echo corner temp_C vdd_V cw_um vlev_V vfar_V ped_mV ped2_mV droop_mV_per_ms sr_V_per_us tset_q_us tset_h_us err_final_mV > $outtxt
  foreach temp_c $temps
  foreach vdd $vdds
  foreach st $steps
    alterparam VDDA = $vdd
    alterparam CWP = $cwf
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
    ** follower slew rate on the input step (20 % -> 80 %, switch open)
    let vlv = $v1_l[$st]
    let vfv = $v2_l[$st]
    let v20 = vlv + 0.2*(vfv - vlv)
    let v80 = vlv + 0.8*(vfv - vlv)
    let tst = th1 + 1u
    meas tran t20 when v(ooa)=$&v20 cross=1 from=$&tst
    meas tran t80 when v(ooa)=$&v80 cross=1 from=$&tst
    let sr = 0.6*abs(vfv - vlv)/(t80 - t20)*1e-6
    let td1 = th1 + 6u
    let td2 = ta - 1n
    meas tran vd1 find v(sh_out) at=$&td1
    meas tran vd2 find v(sh_out) at=$&td2
    let droop = (vd2 - vd1)/(td2 - td1)
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
    echo $pvt_corner $temp_c $vdd $cwf $v1_l[$st] $v2_l[$st] $&ped_mv $&ped2_mv $&droop $&sr $&tset_q $&tset_h $&errf >> $outtxt
    destroy all
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
C {sah_12bit_param.sym} 1400 -560 0 0 {name=x2 WNF=\{WNFP*1e-6\} WPF=\{WPFP*1e-6\} LSW=\{LSWP*1e-6\} MSW=1 KDN=\{KDNP\} KDP=\{KDPP\} MINV=1 CW=\{CWP*1e-6\} CL=\{CLP*1e-6\}}
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
