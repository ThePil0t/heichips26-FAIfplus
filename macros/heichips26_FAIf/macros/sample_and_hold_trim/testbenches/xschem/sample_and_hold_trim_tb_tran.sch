v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
B 2 1500 -1340 2400 -940 {flags=graph
y1=0
y2=3.3
ypos1=0
ypos2=2
divy=5
subdivy=1
unity=1
x1=0
x2=0.00016
divx=8
subdivx=1
xlabmag=1.0
ylabmag=1.0
dataset=-1
unitx=1
logx=0
logy=0
linewidth_mult=2
color="4 7 12"
node="vin
sh_in
sh_out"
sim_type=tran
autoload=0}
B 2 1500 -920 2400 -720 {flags=graph
y1=0
y2=3.3
ypos1=0
ypos2=2
divy=2
subdivy=1
unity=1
x1=0
x2=0.00016
divx=8
subdivx=1
xlabmag=1.0
ylabmag=1.0
dataset=-1
unitx=1
logx=0
logy=0
linewidth_mult=2
color="8"
node="sh_en"
sim_type=tran
autoload=0}
T {Testbench for transient analysis - Sample & Hold with capacitor trim} 80 -2400 0 0 0.8 0.8 {}
T {The S&H is driven by the op_amp_ver_2 unity-gain buffer and loaded by CLOAD (comparator input), as in heichips26_FAIf.sch.
Stimulus: 4 track/hold cycles. The input level changes in the middle of every hold window (VLO -> VHI -> VMID -> VLO).
Measured for every hold window k = 0..3 (written to simulations/sample_and_hold_trim_tb_tran.txt):
  pedestal     = V(sh_out) 100 ns after the hold edge - V(sh_out) just before it (charge injection + clock feedthrough)
  droop        = slope of V(sh_out) in the first half of the hold window (leakage)
  feedthrough  = change of V(sh_out) when the input steps during hold, droop removed, relative to the input step
  tacq         = time after SH_EN rises until V(sh_out) stays within 1/2 LSB (8 bit, VDDA/256) of its final value
  trk_err      = V(sh_out) - V(vin) at the end of the track window (buffer offset + residual settling error)
Trim codes: cap_en = 0 (smallest hold capacitance) and 15 (largest). Add more codes in the 'codes' list of the NGSPICE block.
PVT: nominal corner in the PVT block, temperature/supply lists in the NGSPICE block.
'make sim-xschem-pvt TB=sample_and_hold_trim_tb_tran' runs the PVT points of the Makefile (PVT variable), outputs get a _<corner>_<temp>C_<vdd>V suffix.} 80 -2340 0 0 0.3 0.3 {}
N 860 -480 940 -480 {lab=sh_in}
N 940 -510 940 -480 {lab=sh_in}
N 940 -510 1010 -510 {lab=sh_in}
N 1210 -510 1300 -510 {lab=sh_out}
C {title.sym} 160 0 0 0 {name=l1 author="FAIf team"}
C {code_shown.sym} 80 -2000 0 0 {name=PVT only_toplevel=true
format="tcleval( @value )"
value="** ===== PVT setup =====
** Process corner (one per run): mos_tt / mos_ss / mos_ff / mos_sf / mos_fs,
** MOM caps: cap_typ / cap_bcs / cap_wcs (the cap_cmomi model has no corner spread yet).
** 'make sim-xschem-pvt' replaces mos_tt and cap_typ for every PVT point, keep these tokens.
.lib cornerMOShv.lib mos_tt
.lib cornerMOSlv.lib mos_tt
.lib cornerCAP.lib cap_typ
** Default supply and temperature. To sweep them, edit the 'vdds' and
** 'temps' lists in the NGSPICE block (they override these defaults).
.param VDDA=3.3
.temp 27
"}
C {code_shown.sym} 900 -2000 0 0 {name=PARAMS only_toplevel=true
value="** ===== Stimulus and load =====
** track window, hold window, SH_EN edge time, input step ramp time
.param TTRK=20u
.param THLD=20u
.param TEDGE=5n
.param TINR=100n
.param TPER=\{TTRK+THLD+2*TEDGE\}
** input steps in the middle of each hold window
.param T0=\{TTRK+TEDGE+THLD/2\}
** input levels
.param VLO=0.5
.param VMID=1.65
.param VHI=2.8
** opamp bias current (PTAT CSOUT) and comparator input load
.param IBIAS=25n
.param CLOAD=20f
** trim bits cap_en[3:0], set per run by the NGSPICE block
.param CE0=0 CE1=0 CE2=0 CE3=0
** export timing to the control section
.csparam ttrk=\{TTRK\}
.csparam thld=\{THLD\}
.csparam tedge=\{TEDGE\}
.csparam tper=\{TPER\}
.csparam tstop=\{TTRK+3*TPER+TEDGE+THLD\}
"}
C {code_shown.sym} 2500 -2400 0 0 {name=NGSPICE only_toplevel=true
value="
** gear: no trapezoidal ringing; small gmin: the droop comes from pA leakage currents
** (no klu: with the floating trim-cap nodes at cap_en=0 it stalls at tiny time steps)
.options method=gear reltol=1e-4 abstol=1e-15 gmin=1e-18
.control
  ** ===== sweep lists =====
  ** trim codes for cap_en[3:0]: 0 = smallest, 15 = largest hold capacitance
  set codes = ( 0 15 )
  ** temperature and supply sweep lists (process corner: see PVT block)
  set temps = ( 27 )
  set vdds = ( 3.3 )
  ** 'make sim-xschem-pvt' passes the PVT point with ngspice -D and adds a
  ** _<corner>_<temp>C_<vdd>V suffix to the output files
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
  if $?pvt_tag
  else
    set pvt_tag = ''
  end
  set ext_txt = .txt
  set ext_raw = .raw
  set outtxt = \\"@schname\\\\$pvt_tag$ext_txt\\"
  set outraw = \\"@schname\\\\$pvt_tag$ext_raw\\"

  echo corner temp_C vdd_V code hold vin_V pedestal_mV droop_mV_per_ms feedthrough_dB tacq_us trk_err_mV > $outtxt
  unset appendwrite
  foreach temp_c $temps
  foreach vdd $vdds
  foreach code $codes
    ** split the trim code into the cap_en bits
    let b0 = $code - 2*floor($code/2)
    let b1 = floor($code/2) - 2*floor($code/4)
    let b2 = floor($code/4) - 2*floor($code/8)
    let b3 = floor($code/8) - 2*floor($code/16)
    alterparam VDDA = $vdd
    alterparam CE0 = $&b0
    alterparam CE1 = $&b1
    alterparam CE2 = $&b2
    alterparam CE3 = $&b3
    reset
    ** set the temperature after reset (reset restores the netlist temperature)
    option temp = $temp_c
    ** top-level signals and the trim capacitor nodes inside the S&H
    save v(vin) v(sh_in) v(sh_out) v(sh_en) i(vvdda) v(x2.net2) v(x2.net3) v(x2.net4) v(x2.net5)
    tran 10n $&tstop
    write $outraw
    set appendwrite

    let tol = $vdd/256/2
    let k = 0
    while k < 4
      ** hold window k: SH_EN starts falling at th
      let th = ttrk + k*tper
      let tpre = th - 10n
      let tped = th + tedge + 100n
      let tdr = th + tedge + thld/2 - 10n
      let tend = th + tedge + thld - 10n
      meas tran vtrk find v(sh_out) at=$&tpre
      meas tran vped find v(sh_out) at=$&tped
      meas tran vdr find v(sh_out) at=$&tdr
      meas tran vend find v(sh_out) at=$&tend
      meas tran vlev find v(vin) at=$&tpre
      meas tran vin_dr find v(sh_in) at=$&tdr
      meas tran vin_end find v(sh_in) at=$&tend
      let ped_mv = (vped - vtrk)*1e3
      let droop = (vdr - vped)/(tdr - tped)
      let droop_mv_ms = droop
      if k < 3
        ** feedthrough of the input step during hold, droop removed
        let dvin = vin_end - vin_dr
        let dvout = (vend - vdr) - droop*(tend - tdr)
        let ft_db = db(abs(dvout/dvin) + 1e-12)
        ** acquisition of the new level in the following track window
        let ta = th + tedge + thld
        let tfin = th + tper - 10n
        meas tran vfin find v(sh_out) at=$&tfin
        meas tran vin_fin find v(vin) at=$&tfin
        let err = abs(v(sh_out) - vfin)
        meas tran errmax max err from=$&ta to=$&tfin
        if errmax > tol
          meas tran tsettled when err=$&tol fall=last from=$&ta to=$&tfin
          let tacq_us = (tsettled - ta)*1e6
        else
          let tacq_us = 0
        end
        let trk_mv = (vfin - vin_fin)*1e3
        echo $pvt_corner $temp_c $vdd $code $&k $&vlev $&ped_mv $&droop_mv_ms $&ft_db $&tacq_us $&trk_mv >> $outtxt
      else
        echo $pvt_corner $temp_c $vdd $code $&k $&vlev $&ped_mv $&droop_mv_ms - - - >> $outtxt
      end
      let k = k + 1
    end
  end
  end
  end
  echo
  echo ===== Results: simulations/$outtxt =====
  shell cat $outtxt
.endc
"}
C {launcher.sym} 1560 -1450 0 0 {name=h1
descr="Simulate"
tclcommand="xschem save; xschem netlist; xschem simulate"
}
C {launcher.sym} 1560 -1400 0 0 {name=h2
descr="Load waves"
tclcommand="xschem raw_read $netlist_dir/[file rootname [file tail [xschem get current_name]]].raw tran"
}
C {vsource.sym} 120 -720 0 0 {name=VVDDA value=\{VDDA\} savecurrent=true}
C {lab_pin.sym} 120 -750 0 0 {name=p1 sig_type=std_logic lab=VDDA}
C {gnd.sym} 120 -690 0 0 {name=l2 lab=GND}
C {vsource.sym} 120 -1100 0 0 {name=VIN value="pwl(0 \{VLO\} \{T0\} \{VLO\} \{T0+TINR\} \{VHI\} \{T0+TPER\} \{VHI\} \{T0+TPER+TINR\} \{VMID\} \{T0+2*TPER\} \{VMID\} \{T0+2*TPER+TINR\} \{VLO\})" savecurrent=false}
C {lab_pin.sym} 120 -1130 0 0 {name=p2 sig_type=std_logic lab=vin}
C {gnd.sym} 120 -1070 0 0 {name=l3 lab=GND}
C {vsource.sym} 120 -980 0 0 {name=VSHEN value="pulse(\{VDDA\} 0 \{TTRK\} \{TEDGE\} \{TEDGE\} \{THLD\} \{TPER\})" savecurrent=false}
C {lab_pin.sym} 120 -1010 0 0 {name=p3 sig_type=std_logic lab=sh_en}
C {gnd.sym} 120 -950 0 0 {name=l4 lab=GND}
C {vsource.sym} 300 -320 0 0 {name=VTRIM0 value=\{CE0*VDDA\} savecurrent=false}
C {lab_pin.sym} 300 -350 0 0 {name=p4 sig_type=std_logic lab=trim[0]}
C {gnd.sym} 300 -290 0 0 {name=l5 lab=GND}
C {vsource.sym} 420 -320 0 0 {name=VTRIM1 value=\{CE1*VDDA\} savecurrent=false}
C {lab_pin.sym} 420 -350 0 0 {name=p5 sig_type=std_logic lab=trim[1]}
C {gnd.sym} 420 -290 0 0 {name=l6 lab=GND}
C {vsource.sym} 540 -320 0 0 {name=VTRIM2 value=\{CE2*VDDA\} savecurrent=false}
C {lab_pin.sym} 540 -350 0 0 {name=p6 sig_type=std_logic lab=trim[2]}
C {gnd.sym} 540 -290 0 0 {name=l7 lab=GND}
C {vsource.sym} 660 -320 0 0 {name=VTRIM3 value=\{CE3*VDDA\} savecurrent=false}
C {lab_pin.sym} 660 -350 0 0 {name=p7 sig_type=std_logic lab=trim[3]}
C {gnd.sym} 660 -290 0 0 {name=l8 lab=GND}
C {isource.sym} 560 -580 0 0 {name=IBIAS value=\{IBIAS\}}
C {lab_pin.sym} 560 -610 0 0 {name=p8 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 560 -550 0 0 {name=p9 sig_type=std_logic lab=iref}
C {op_amp_ver_2.sym} 760 -480 0 0 {name=x1}
C {lab_pin.sym} 770 -530 0 0 {name=p10 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 730 -410 0 0 {name=p11 sig_type=std_logic lab=iref}
C {lab_pin.sym} 690 -500 0 0 {name=p12 sig_type=std_logic lab=sh_in}
C {lab_pin.sym} 690 -460 0 0 {name=p13 sig_type=std_logic lab=vin}
C {lab_pin.sym} 770 -430 0 1 {name=p14 sig_type=std_logic lab=GND}
C {lab_pin.sym} 730 -550 0 0 {name=p15 sig_type=std_logic lab=GND}
C {sample_and_hold_trim.sym} 1060 -480 0 0 {name=x2}
C {lab_pin.sym} 1140 -560 0 1 {name=p16 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1080 -430 0 0 {name=p17 sig_type=std_logic lab=sh_en}
C {lab_pin.sym} 1140 -430 0 0 {name=p18 sig_type=std_logic lab=GND}
C {lab_pin.sym} 1170 -430 0 1 {name=p19 sig_type=std_logic lab=trim[3:0]}
C {capa.sym} 1300 -480 0 0 {name=CLOAD
m=1
value=\{CLOAD\}
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 1300 -450 0 0 {name=l9 lab=GND}
C {lab_pin.sym} 1300 -510 0 1 {name=p20 sig_type=std_logic lab=sh_out}
C {lab_pin.sym} 940 -480 0 1 {name=p21 sig_type=std_logic lab=sh_in}
