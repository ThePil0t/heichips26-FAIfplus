v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
B 2 2000 -1500 2900 -1100 {flags=graph
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
color="4 7 12 8"
node="sh_out_trim
sh_out_nmin
sh_out_nmax
vin_trim"
sim_type=tran
autoload=0}
B 2 2000 -1080 2900 -880 {flags=graph
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
color="8"
node="sh_en_trim"
sim_type=tran
autoload=0}
T {Testbench: cost of the capacitor trim - trimmed S&H vs. the same S&H without trim switches} 80 -3300 0 0 0.8 0.8 {}
T {Three channels with identical input buffer (op_amp_ver_2, unity gain), bias, stimulus and comparator load CLOAD:
  trim : sample_and_hold_trim, cap_en swept (codes list)
  nmin : same main switch + SH_EN inverter (asw_inv) with only C1 hard-wired   -> compare with trim at cap_en = 0
  nmax : same main switch + SH_EN inverter (asw_inv) with C1..C5 hard-wired    -> compare with trim at cap_en = 15
  The nmin/nmax cap sizes are copied from sample_and_hold_trim.sch, keep them in sync when the DUT changes.
Transient (same stimulus and measurements as sample_and_hold_trim_tb_tran), one active channel per run (EN_<ch>):
  cap_en=0 on trim and nmin, cap_en=15 on trim and nmax: pedestal, droop, feedthrough, tacq, trk_err
  -> simulations/sample_and_hold_trim_tb_vs_notrim.txt
AC at 1 MHz in hold mode: effective hold capacitance C(Vhold) per channel (includes switch parasitics, CLOAD removed)
  -> simulations/sample_and_hold_trim_tb_vs_notrim_chold.txt
PVT: nominal corner in the PVT block, 'make sim-xschem-pvt TB=sample_and_hold_trim_tb_vs_notrim' for the PVT points of the Makefile.} 80 -3240 0 0 0.3 0.3 {}
C {title.sym} 160 0 0 0 {name=l1 author="FAIf team"}
C {code_shown.sym} 80 -2900 0 0 {name=PVT only_toplevel=true
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
C {code_shown.sym} 900 -2900 0 0 {name=PARAMS only_toplevel=true
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
** analysis switches, set by the NGSPICE block:
** SHTRK=1 SH_EN pulses (transient), 0 SH_EN low (hold, C(V) AC); RBIAS hold-node bias resistor
.param SHTRK=1
.param RBIAS=1e18
** active channel of a transient run (1 = stimulated, 0 = static), set by the NGSPICE block
.param EN_TRIM=1 EN_NMIN=0 EN_NMAX=0
.param VLEV=1.65
** export to the control section
.csparam ttrk=\{TTRK\}
.csparam thld=\{THLD\}
.csparam tedge=\{TEDGE\}
.csparam tper=\{TPER\}
.csparam tstop=\{TTRK+3*TPER+TEDGE+THLD\}
.csparam cload_pf=\{CLOAD*1e12\}
"}
C {code_shown.sym} 3000 -3300 0 0 {name=NGSPICE only_toplevel=true
value="
** gear: no trapezoidal ringing; small gmin: the droop comes from pA leakage currents
** (no klu: with the floating trim-cap nodes at cap_en=0 it stalls at tiny time steps)
.options method=gear reltol=1e-4 abstol=1e-15 gmin=1e-18
.control
  ** ===== sweep lists =====
  ** trim codes for cap_en[3:0] of the 'trim' channel; code 0 is also run on the
  ** nmin reference, code 15 on the nmax reference (one active channel per transient run:
  ** simulating all channels at once is ~50x slower)
  set codes = ( 0 15 )
  ** temperature and supply sweep lists (process corner: see PVT block)
  set temps = ( 27 )
  set vdds = ( 3.3 )
  ** hold-node voltages for the hold-capacitance measurement
  set cv_levels = ( 0.5 1.65 2.8 )
  set chans = ( trim nmin nmax )
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
  set ext_cv = _chold.txt
  set ext_raw = .raw
  set outtxt = \\"@schname\\\\$pvt_tag$ext_txt\\"
  set outcv = \\"@schname\\\\$pvt_tag$ext_cv\\"
  set outraw = \\"@schname\\\\$pvt_tag$ext_raw\\"

  echo corner temp_C vdd_V code channel hold vin_V pedestal_mV droop_mV_per_ms feedthrough_dB tacq_us trk_err_mV > $outtxt
  echo corner temp_C vdd_V code channel vhold_V chold_pF > $outcv
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
    set runchans = ( trim )
    if $code = 0
      set runchans = ( trim nmin )
    end
    if $code = 15
      set runchans = ( trim nmax )
    end
    let tol = $vdd/256/2
    foreach ch $runchans
      ** transient of channel ch: SH_EN pulses, bias resistor effectively open
      alterparam SHTRK = 1
      alterparam RBIAS = 1e18
      alterparam EN_TRIM = 0
      alterparam EN_NMIN = 0
      alterparam EN_NMAX = 0
      alterparam EN_$ch = 1
      reset
      ** set the temperature after reset (reset restores the netlist temperature)
      option temp = $temp_c
      save v(vin_$ch) v(sh_en_$ch) v(sh_in_$ch) v(sh_out_$ch)
      tran 10n $&tstop
      write $outraw
      set appendwrite

      let k = 0
      while k < 4
        ** hold window k: SH_EN starts falling at th
        let th = ttrk + k*tper
        let tpre = th - 10n
        let tped = th + tedge + 100n
        let tdr = th + tedge + thld/2 - 10n
        let tend = th + tedge + thld - 10n
        meas tran vtrk find v(sh_out_$ch) at=$&tpre
        meas tran vped find v(sh_out_$ch) at=$&tped
        meas tran vdr find v(sh_out_$ch) at=$&tdr
        meas tran vend find v(sh_out_$ch) at=$&tend
        meas tran vlev find v(vin_$ch) at=$&tpre
        meas tran vin_dr find v(sh_in_$ch) at=$&tdr
        meas tran vin_end find v(sh_in_$ch) at=$&tend
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
          meas tran vfin find v(sh_out_$ch) at=$&tfin
          meas tran vin_fin find v(vin_$ch) at=$&tfin
          let err = abs(v(sh_out_$ch) - vfin)
          meas tran errmax max err from=$&ta to=$&tfin
          if errmax > tol
            meas tran tsettled when err=$&tol fall=last from=$&ta to=$&tfin
            let tacq_us = (tsettled - ta)*1e6
          else
            let tacq_us = 0
          end
          let trk_mv = (vfin - vin_fin)*1e3
          echo $pvt_corner $temp_c $vdd $code $ch $&k $&vlev $&ped_mv $&droop_mv_ms $&ft_db $&tacq_us $&trk_mv >> $outtxt
        else
          echo $pvt_corner $temp_c $vdd $code $ch $&k $&vlev $&ped_mv $&droop_mv_ms - - - >> $outtxt
        end
        let k = k + 1
      end
    end

    ** hold capacitance: SH_EN = 0 (hold), hold node biased to vhold through RBIAS,
    ** C = imag(Y)/(2 pi f) at 1 MHz (RBIAS does not enter), CLOAD subtracted
    foreach lev $cv_levels
      alterparam SHTRK = 0
      alterparam RBIAS = 1e9
      alterparam VLEV = $lev
      reset
      option temp = $temp_c
      ac lin 1 1e6 1e6
      foreach ch $chans
        let c_pf = imag(1/v(sh_out_$ch))/(2*pi*1e6)*1e12 - cload_pf
        echo $pvt_corner $temp_c $vdd $code $ch $lev $&c_pf >> $outcv
      end
    end
  end
  end
  end
  echo
  echo ===== Results: simulations/$outtxt and $outcv =====
  shell cat $outtxt
  shell cat $outcv
.endc
"}
C {launcher.sym} 2060 -1560 0 0 {name=h1
descr="Simulate"
tclcommand="xschem save; xschem netlist; xschem simulate"
}
C {launcher.sym} 2060 -1510 0 0 {name=h2
descr="Load waves"
tclcommand="xschem raw_read $netlist_dir/[file rootname [file tail [xschem get current_name]]].raw tran"
}
C {vsource.sym} 120 -1420 0 0 {name=VVDDA value=\{VDDA\} savecurrent=true}
C {lab_pin.sym} 120 -1450 0 0 {name=p1 sig_type=std_logic lab=VDDA}
C {gnd.sym} 120 -1390 0 0 {name=l2 lab=GND}
C {vsource.sym} 240 -1420 0 0 {name=VB value=\{VLEV\} savecurrent=false}
C {lab_pin.sym} 240 -1450 0 0 {name=p2 sig_type=std_logic lab=vb}
C {gnd.sym} 240 -1390 0 0 {name=l3 lab=GND}
C {vsource.sym} 360 -1420 0 0 {name=VTRIM0 value=\{CE0*VDDA\} savecurrent=false}
C {lab_pin.sym} 360 -1450 0 0 {name=p3 sig_type=std_logic lab=trim[0]}
C {gnd.sym} 360 -1390 0 0 {name=l4 lab=GND}
C {vsource.sym} 480 -1420 0 0 {name=VTRIM1 value=\{CE1*VDDA\} savecurrent=false}
C {lab_pin.sym} 480 -1450 0 0 {name=p4 sig_type=std_logic lab=trim[1]}
C {gnd.sym} 480 -1390 0 0 {name=l5 lab=GND}
C {vsource.sym} 600 -1420 0 0 {name=VTRIM2 value=\{CE2*VDDA\} savecurrent=false}
C {lab_pin.sym} 600 -1450 0 0 {name=p5 sig_type=std_logic lab=trim[2]}
C {gnd.sym} 600 -1390 0 0 {name=l6 lab=GND}
C {vsource.sym} 720 -1420 0 0 {name=VTRIM3 value=\{CE3*VDDA\} savecurrent=false}
C {lab_pin.sym} 720 -1450 0 0 {name=p6 sig_type=std_logic lab=trim[3]}
C {gnd.sym} 720 -1390 0 0 {name=l7 lab=GND}
C {vsource.sym} 120 -2150 0 0 {name=VIN_TRIM value="pwl(0 \{VLO\} \{T0\} \{VLO\} \{T0+TINR\} \{VLO+EN_TRIM*(VHI-VLO)\} \{T0+TPER\} \{VLO+EN_TRIM*(VHI-VLO)\} \{T0+TPER+TINR\} \{VLO+EN_TRIM*(VMID-VLO)\} \{T0+2*TPER\} \{VLO+EN_TRIM*(VMID-VLO)\} \{T0+2*TPER+TINR\} \{VLO\})" savecurrent=false}
C {lab_pin.sym} 120 -2180 0 0 {name=p7 sig_type=std_logic lab=vin_trim}
C {gnd.sym} 120 -2120 0 0 {name=l8 lab=GND}
C {vsource.sym} 120 -2030 0 0 {name=VSHEN_TRIM value="pulse(\{VDDA*SHTRK*EN_TRIM\} 0 \{TTRK\} \{TEDGE\} \{TEDGE\} \{THLD\} \{TPER\})" savecurrent=false}
C {lab_pin.sym} 120 -2060 0 0 {name=p8 sig_type=std_logic lab=sh_en_trim}
C {gnd.sym} 120 -2000 0 0 {name=l9 lab=GND}
T {channel 'trim'} 600 -1290 0 0 0.5 0.5 {}
C {isource.sym} 600 -1200 0 0 {name=IBIAS_TRIM value=\{IBIAS\}}
C {lab_pin.sym} 600 -1230 0 0 {name=p9 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 600 -1170 0 0 {name=p10 sig_type=std_logic lab=iref_trim}
C {op_amp_ver_2.sym} 760 -1100 0 0 {name=xbuf_trim}
C {lab_pin.sym} 770 -1150 0 1 {name=p11 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 730 -1030 0 0 {name=p12 sig_type=std_logic lab=iref_trim}
C {lab_pin.sym} 690 -1120 0 0 {name=p13 sig_type=std_logic lab=sh_in_trim}
C {lab_pin.sym} 860 -1100 0 1 {name=p14 sig_type=std_logic lab=sh_in_trim}
C {lab_pin.sym} 690 -1080 0 0 {name=p15 sig_type=std_logic lab=vin_trim}
C {lab_pin.sym} 770 -1050 0 1 {name=p16 sig_type=std_logic lab=GND}
C {lab_pin.sym} 730 -1170 0 0 {name=p17 sig_type=std_logic lab=GND}
C {sample_and_hold_trim.sym} 1060 -1100 0 0 {name=xsh_trim}
C {lab_pin.sym} 1140 -1180 0 1 {name=p18 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1010 -1130 0 0 {name=p19 sig_type=std_logic lab=sh_in_trim}
C {lab_pin.sym} 1210 -1130 0 1 {name=p20 sig_type=std_logic lab=sh_out_trim}
C {lab_pin.sym} 1080 -1050 0 0 {name=p21 sig_type=std_logic lab=sh_en_trim}
C {lab_pin.sym} 1140 -1050 0 0 {name=p22 sig_type=std_logic lab=GND}
C {lab_pin.sym} 1170 -1050 0 1 {name=p23 sig_type=std_logic lab=trim[3:0]}
C {capa.sym} 1700 -1100 0 0 {name=CLOAD_TRIM
m=1
value=\{CLOAD\}
footprint=1206
device="ceramic capacitor"}
C {lab_pin.sym} 1700 -1130 0 0 {name=p24 sig_type=std_logic lab=sh_out_trim}
C {gnd.sym} 1700 -1070 0 0 {name=l10 lab=GND}
N 1700 -1130 1880 -1130 {lab=sh_out_trim}
C {res.sym} 1790 -1100 0 0 {name=RB_TRIM
value=\{RBIAS\}
footprint=1206
device=resistor
m=1}
C {lab_pin.sym} 1790 -1070 0 1 {name=p25 sig_type=std_logic lab=vb}
C {isource.sym} 1880 -1100 2 0 {name=IAC_TRIM value="dc 0 ac 1"}
C {gnd.sym} 1880 -1070 0 0 {name=l11 lab=GND}
C {vsource.sym} 120 -1910 0 0 {name=VIN_NMIN value="pwl(0 \{VLO\} \{T0\} \{VLO\} \{T0+TINR\} \{VLO+EN_NMIN*(VHI-VLO)\} \{T0+TPER\} \{VLO+EN_NMIN*(VHI-VLO)\} \{T0+TPER+TINR\} \{VLO+EN_NMIN*(VMID-VLO)\} \{T0+2*TPER\} \{VLO+EN_NMIN*(VMID-VLO)\} \{T0+2*TPER+TINR\} \{VLO\})" savecurrent=false}
C {lab_pin.sym} 120 -1940 0 0 {name=p26 sig_type=std_logic lab=vin_nmin}
C {gnd.sym} 120 -1880 0 0 {name=l12 lab=GND}
C {vsource.sym} 120 -1790 0 0 {name=VSHEN_NMIN value="pulse(\{VDDA*SHTRK*EN_NMIN\} 0 \{TTRK\} \{TEDGE\} \{TEDGE\} \{THLD\} \{TPER\})" savecurrent=false}
C {lab_pin.sym} 120 -1820 0 0 {name=p27 sig_type=std_logic lab=sh_en_nmin}
C {gnd.sym} 120 -1760 0 0 {name=l13 lab=GND}
T {channel 'nmin'} 600 -940 0 0 0.5 0.5 {}
C {isource.sym} 600 -850 0 0 {name=IBIAS_NMIN value=\{IBIAS\}}
C {lab_pin.sym} 600 -880 0 0 {name=p28 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 600 -820 0 0 {name=p29 sig_type=std_logic lab=iref_nmin}
C {op_amp_ver_2.sym} 760 -750 0 0 {name=xbuf_nmin}
C {lab_pin.sym} 770 -800 0 1 {name=p30 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 730 -680 0 0 {name=p31 sig_type=std_logic lab=iref_nmin}
C {lab_pin.sym} 690 -770 0 0 {name=p32 sig_type=std_logic lab=sh_in_nmin}
C {lab_pin.sym} 860 -750 0 1 {name=p33 sig_type=std_logic lab=sh_in_nmin}
C {lab_pin.sym} 690 -730 0 0 {name=p34 sig_type=std_logic lab=vin_nmin}
C {lab_pin.sym} 770 -700 0 1 {name=p35 sig_type=std_logic lab=GND}
C {lab_pin.sym} 730 -820 0 0 {name=p36 sig_type=std_logic lab=GND}
C {/home/benedikt/heichips26-FAIf/macros/heichips26_FAIf/macros/asw_inv/schematic/xschem/asw_inv.sym} 1060 -750 0 0 {name=xsw_nmin}
C {lab_pin.sym} 990 -750 0 0 {name=p37 sig_type=std_logic lab=sh_in_nmin}
C {lab_pin.sym} 1130 -750 0 1 {name=p38 sig_type=std_logic lab=sh_out_nmin}
C {lab_pin.sym} 1060 -800 0 0 {name=p39 sig_type=std_logic lab=sh_en_nmin}
C {lab_pin.sym} 1110 -700 0 1 {name=p40 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1100 -700 0 0 {name=p41 sig_type=std_logic lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 1250 -710 0 0 {name=C1_NMIN
model=cap_cmomi
w=12.5e-6
l=25e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {lab_pin.sym} 1250 -740 0 1 {name=p42 sig_type=std_logic lab=sh_out_nmin}
C {gnd.sym} 1250 -680 0 0 {name=l14 lab=GND}
C {capa.sym} 1700 -750 0 0 {name=CLOAD_NMIN
m=1
value=\{CLOAD\}
footprint=1206
device="ceramic capacitor"}
C {lab_pin.sym} 1700 -780 0 0 {name=p43 sig_type=std_logic lab=sh_out_nmin}
C {gnd.sym} 1700 -720 0 0 {name=l15 lab=GND}
N 1700 -780 1880 -780 {lab=sh_out_nmin}
C {res.sym} 1790 -750 0 0 {name=RB_NMIN
value=\{RBIAS\}
footprint=1206
device=resistor
m=1}
C {lab_pin.sym} 1790 -720 0 1 {name=p44 sig_type=std_logic lab=vb}
C {isource.sym} 1880 -750 2 0 {name=IAC_NMIN value="dc 0 ac 1"}
C {gnd.sym} 1880 -720 0 0 {name=l16 lab=GND}
C {vsource.sym} 120 -1670 0 0 {name=VIN_NMAX value="pwl(0 \{VLO\} \{T0\} \{VLO\} \{T0+TINR\} \{VLO+EN_NMAX*(VHI-VLO)\} \{T0+TPER\} \{VLO+EN_NMAX*(VHI-VLO)\} \{T0+TPER+TINR\} \{VLO+EN_NMAX*(VMID-VLO)\} \{T0+2*TPER\} \{VLO+EN_NMAX*(VMID-VLO)\} \{T0+2*TPER+TINR\} \{VLO\})" savecurrent=false}
C {lab_pin.sym} 120 -1700 0 0 {name=p45 sig_type=std_logic lab=vin_nmax}
C {gnd.sym} 120 -1640 0 0 {name=l17 lab=GND}
C {vsource.sym} 120 -1550 0 0 {name=VSHEN_NMAX value="pulse(\{VDDA*SHTRK*EN_NMAX\} 0 \{TTRK\} \{TEDGE\} \{TEDGE\} \{THLD\} \{TPER\})" savecurrent=false}
C {lab_pin.sym} 120 -1580 0 0 {name=p46 sig_type=std_logic lab=sh_en_nmax}
C {gnd.sym} 120 -1520 0 0 {name=l18 lab=GND}
T {channel 'nmax'} 600 -590 0 0 0.5 0.5 {}
C {isource.sym} 600 -500 0 0 {name=IBIAS_NMAX value=\{IBIAS\}}
C {lab_pin.sym} 600 -530 0 0 {name=p47 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 600 -470 0 0 {name=p48 sig_type=std_logic lab=iref_nmax}
C {op_amp_ver_2.sym} 760 -400 0 0 {name=xbuf_nmax}
C {lab_pin.sym} 770 -450 0 1 {name=p49 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 730 -330 0 0 {name=p50 sig_type=std_logic lab=iref_nmax}
C {lab_pin.sym} 690 -420 0 0 {name=p51 sig_type=std_logic lab=sh_in_nmax}
C {lab_pin.sym} 860 -400 0 1 {name=p52 sig_type=std_logic lab=sh_in_nmax}
C {lab_pin.sym} 690 -380 0 0 {name=p53 sig_type=std_logic lab=vin_nmax}
C {lab_pin.sym} 770 -350 0 1 {name=p54 sig_type=std_logic lab=GND}
C {lab_pin.sym} 730 -470 0 0 {name=p55 sig_type=std_logic lab=GND}
C {/home/benedikt/heichips26-FAIf/macros/heichips26_FAIf/macros/asw_inv/schematic/xschem/asw_inv.sym} 1060 -400 0 0 {name=xsw_nmax}
C {lab_pin.sym} 990 -400 0 0 {name=p56 sig_type=std_logic lab=sh_in_nmax}
C {lab_pin.sym} 1130 -400 0 1 {name=p57 sig_type=std_logic lab=sh_out_nmax}
C {lab_pin.sym} 1060 -450 0 0 {name=p58 sig_type=std_logic lab=sh_en_nmax}
C {lab_pin.sym} 1110 -350 0 1 {name=p59 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1100 -350 0 0 {name=p60 sig_type=std_logic lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 1250 -360 0 0 {name=C1_NMAX
model=cap_cmomi
w=12.5e-6
l=25e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {lab_pin.sym} 1250 -390 0 1 {name=p61 sig_type=std_logic lab=sh_out_nmax}
C {gnd.sym} 1250 -330 0 0 {name=l19 lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 1330 -360 0 0 {name=C2_NMAX
model=cap_cmomi
w=12.5e-6
l=25e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {gnd.sym} 1330 -330 0 0 {name=l20 lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 1410 -360 0 0 {name=C3_NMAX
model=cap_cmomi
w=25e-6
l=25e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {gnd.sym} 1410 -330 0 0 {name=l21 lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 1490 -360 0 0 {name=C4_NMAX
model=cap_cmomi
w=50e-6
l=25e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {gnd.sym} 1490 -330 0 0 {name=l22 lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 1570 -360 0 0 {name=C5_NMAX
model=cap_cmomi
w=50e-6
l=25e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {gnd.sym} 1570 -330 0 0 {name=l23 lab=GND}
N 1250 -390 1570 -390 {lab=sh_out_nmax}
C {capa.sym} 1700 -400 0 0 {name=CLOAD_NMAX
m=1
value=\{CLOAD\}
footprint=1206
device="ceramic capacitor"}
C {lab_pin.sym} 1700 -430 0 0 {name=p62 sig_type=std_logic lab=sh_out_nmax}
C {gnd.sym} 1700 -370 0 0 {name=l24 lab=GND}
N 1700 -430 1880 -430 {lab=sh_out_nmax}
C {res.sym} 1790 -400 0 0 {name=RB_NMAX
value=\{RBIAS\}
footprint=1206
device=resistor
m=1}
C {lab_pin.sym} 1790 -370 0 1 {name=p63 sig_type=std_logic lab=vb}
C {isource.sym} 1880 -400 2 0 {name=IAC_NMAX value="dc 0 ac 1"}
C {gnd.sym} 1880 -370 0 0 {name=l25 lab=GND}
