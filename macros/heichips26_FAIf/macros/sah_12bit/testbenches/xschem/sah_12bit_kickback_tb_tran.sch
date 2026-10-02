v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {Testbench sah_12bit - comparator kickback onto the held voltage during a 12-bit conversion} 80 -1500 0 0 0.7 0.7 {}
T {x1 drives the real 555_comparator (INN = sh_out), x2 is an identical S&H loaded with CREF (~ comparator gate) as droop reference.
VDAC (comparator INP) follows sar.vhdl: previous result VPREV during track, 0 in the first hold cycle, then the 12 trial values of the
binary search for the held level VH (ideal decisions), one per TBIT. kick_k = change of v(sh_out) minus change of v(sh_ref) since the
hold edge, at the end of DAC slot k. Reported: max |kick| over the 12 decisions and the kick at the LSB decision.
Results: simulations/sah_12bit_kickback_tb_tran.txt} 80 -1440 0 0 0.3 0.3 {}
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
value="** ===== timing, levels, loads =====
.param TTRK=2u
.param TH=\{TTRK\}
.param TF=1n
.param TD=20n
.param TR=20n
.param TBIT=2u
.param VH=1.65
.param VPREV=1.65
.param CREF=15f
.param IBCOMP=100n
.param VT1=0 VT2=0 VT3=0 VT4=0 VT5=0 VT6=0 VT7=0 VT8=0 VT9=0 VT10=0 VT11=0 VT12=0
.csparam th=\{TH\}
.csparam td=\{TD\}
.csparam tf=\{TF\}
.csparam tbit=\{TBIT\}
.csparam tstop=\{TH+TD+13*TBIT+10n\}
** ===== sah_12bit sizes (um) =====
.param WNFP=0.6 WPFP=1.8 LSWP=0.45 MSWP=1 KDNP=0.5 KDPP=0.5 CWP=59.63 CLP=25.2
"}
C {code_shown.sym} 700 -1250 0 0 {name=NGSPICE only_toplevel=true
value="
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
  set outtxt = sah_12bit_kickback_tb_tran.txt
  set outraw = sah_12bit_kickback_tb_tran.raw
  if $?pvt_tag
    set outtxt = \\"sah_12bit_kickback_tb_tran$pvt_tag$ext_txt\\"
    set outraw = \\"sah_12bit_kickback_tb_tran$pvt_tag$ext_raw\\"
  end
  ** 0.26 / 1 / 2 / 4 pF and the chosen 1.21 pF at -35 % / nominal / +35 %
  set cws = ( 13.35 48.95 97.9 194.91 39.16 59.63 80.1 )
  set vhs = ( 0.5 1.2 1.65 2.3 2.9 )
  ** previous result during track: 0 = same level as VH (slow input), bottom, top of the range
  set vps = ( 0 0.1 3.2 )
  if $?pvt_temp
    set cws = ( 59.63 )
  end
  if $?run_sel
    set rsel = $run_sel
    set cw_all = ( 13.35 48.95 97.9 194.91 39.16 59.63 80.1 )
    set cws = ( $cw_all[$rsel] )
  end
  echo corner temp_C vdd_V cw_um vh_V vprev_V kick_max_uV kick_last_uV > $outtxt
  foreach temp_c $temps
  foreach vdd $vdds
  foreach cw $cws
  foreach vhl $vhs
  foreach vp $vps
    let lsb = $vdd/4096
    ** held level 0.3 LSB above a code edge, so no trial lands exactly on it
    let vh = $vhl + 0.3*lsb
    let vpv = $vp
    if vpv = 0
      let vpv = vh
    end
    alterparam VDDA = $vdd
    alterparam CWP = $cw
    alterparam VH = $&vh
    alterparam VPREV = $&vpv
    let d = 0
    let tr = d + 2048
    let vt = tr*lsb
    alterparam VT1 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 1024
    let vt = tr*lsb
    alterparam VT2 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 512
    let vt = tr*lsb
    alterparam VT3 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 256
    let vt = tr*lsb
    alterparam VT4 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 128
    let vt = tr*lsb
    alterparam VT5 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 64
    let vt = tr*lsb
    alterparam VT6 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 32
    let vt = tr*lsb
    alterparam VT7 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 16
    let vt = tr*lsb
    alterparam VT8 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 8
    let vt = tr*lsb
    alterparam VT9 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 4
    let vt = tr*lsb
    alterparam VT10 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 2
    let vt = tr*lsb
    alterparam VT11 = $&vt
    if vt <= vh
      let d = tr
    end
    let tr = d + 1
    let vt = tr*lsb
    alterparam VT12 = $&vt
    if vt <= vh
      let d = tr
    end
    reset
    option temp = $temp_c
    save v(sh_out) v(sh_ref) v(vdac)
    tran 1n $&tstop 0 20n
    let t0 = th + tf + 10n
    meas tran a0r find v(sh_out) at=$&t0
    meas tran b0r find v(sh_ref) at=$&t0
    let k_mx = 0
    let k_last = 0
    let tm = th + td + 1*tbit - 20n
    meas tran a0 find v(sh_out) at=$&tm
    meas tran b0 find v(sh_ref) at=$&tm
    let kick = ((a0 - a0r) - (b0 - b0r))*1e6

    let k_last = kick
    let tm = th + td + 2*tbit - 20n
    meas tran a1 find v(sh_out) at=$&tm
    meas tran b1 find v(sh_ref) at=$&tm
    let kick = ((a1 - a0r) - (b1 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 3*tbit - 20n
    meas tran a2 find v(sh_out) at=$&tm
    meas tran b2 find v(sh_ref) at=$&tm
    let kick = ((a2 - a0r) - (b2 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 4*tbit - 20n
    meas tran a3 find v(sh_out) at=$&tm
    meas tran b3 find v(sh_ref) at=$&tm
    let kick = ((a3 - a0r) - (b3 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 5*tbit - 20n
    meas tran a4 find v(sh_out) at=$&tm
    meas tran b4 find v(sh_ref) at=$&tm
    let kick = ((a4 - a0r) - (b4 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 6*tbit - 20n
    meas tran a5 find v(sh_out) at=$&tm
    meas tran b5 find v(sh_ref) at=$&tm
    let kick = ((a5 - a0r) - (b5 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 7*tbit - 20n
    meas tran a6 find v(sh_out) at=$&tm
    meas tran b6 find v(sh_ref) at=$&tm
    let kick = ((a6 - a0r) - (b6 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 8*tbit - 20n
    meas tran a7 find v(sh_out) at=$&tm
    meas tran b7 find v(sh_ref) at=$&tm
    let kick = ((a7 - a0r) - (b7 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 9*tbit - 20n
    meas tran a8 find v(sh_out) at=$&tm
    meas tran b8 find v(sh_ref) at=$&tm
    let kick = ((a8 - a0r) - (b8 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 10*tbit - 20n
    meas tran a9 find v(sh_out) at=$&tm
    meas tran b9 find v(sh_ref) at=$&tm
    let kick = ((a9 - a0r) - (b9 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 11*tbit - 20n
    meas tran a10 find v(sh_out) at=$&tm
    meas tran b10 find v(sh_ref) at=$&tm
    let kick = ((a10 - a0r) - (b10 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 12*tbit - 20n
    meas tran a11 find v(sh_out) at=$&tm
    meas tran b11 find v(sh_ref) at=$&tm
    let kick = ((a11 - a0r) - (b11 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    let tm = th + td + 13*tbit - 20n
    meas tran a12 find v(sh_out) at=$&tm
    meas tran b12 find v(sh_ref) at=$&tm
    let kick = ((a12 - a0r) - (b12 - b0r))*1e6

    if k_mx < abs(kick)
      let k_mx = abs(kick)
    end
    let k_last = kick
    echo $pvt_corner $temp_c $vdd $cw $vhl $&vpv $&k_mx $&k_last >> $outtxt
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
C {vsource.sym} 300 -560 0 0 {name=VIN value=\{VH\} savecurrent=false}
C {lab_pin.sym} 300 -590 0 1 {name=lp3 sig_type=std_logic lab=vin}
C {gnd.sym} 300 -530 0 0 {name=lg4 lab=GND}
C {vsource.sym} 480 -560 0 0 {name=VSHEN value="pwl(0 \{VDDA\} \{TH\} \{VDDA\} \{TH+TF\} 0)" savecurrent=false}
C {lab_pin.sym} 480 -590 0 1 {name=lp5 sig_type=std_logic lab=sh_en}
C {gnd.sym} 480 -530 0 0 {name=lg6 lab=GND}
C {vsource.sym} 660 -560 0 0 {name=VDACS value="pwl(0 \{VPREV\} \{TH+TD\} \{VPREV\} \{TH+TD+TR\} 0 \{TH+TD+1*TBIT\} 0 \{TH+TD+1*TBIT+TR\} \{VT1\} \{TH+TD+2*TBIT\} \{VT1\} \{TH+TD+2*TBIT+TR\} \{VT2\} \{TH+TD+3*TBIT\} \{VT2\} \{TH+TD+3*TBIT+TR\} \{VT3\} \{TH+TD+4*TBIT\} \{VT3\} \{TH+TD+4*TBIT+TR\} \{VT4\} \{TH+TD+5*TBIT\} \{VT4\} \{TH+TD+5*TBIT+TR\} \{VT5\} \{TH+TD+6*TBIT\} \{VT5\} \{TH+TD+6*TBIT+TR\} \{VT6\} \{TH+TD+7*TBIT\} \{VT6\} \{TH+TD+7*TBIT+TR\} \{VT7\} \{TH+TD+8*TBIT\} \{VT7\} \{TH+TD+8*TBIT+TR\} \{VT8\} \{TH+TD+9*TBIT\} \{VT8\} \{TH+TD+9*TBIT+TR\} \{VT9\} \{TH+TD+10*TBIT\} \{VT9\} \{TH+TD+10*TBIT+TR\} \{VT10\} \{TH+TD+11*TBIT\} \{VT10\} \{TH+TD+11*TBIT+TR\} \{VT11\} \{TH+TD+12*TBIT\} \{VT11\} \{TH+TD+12*TBIT+TR\} \{VT12\})" savecurrent=false}
C {lab_pin.sym} 660 -590 0 1 {name=lp7 sig_type=std_logic lab=vdac}
C {gnd.sym} 660 -530 0 0 {name=lg8 lab=GND}
C {sah_12bit_param.sym} 1000 -560 0 0 {name=x1 WNF=\{WNFP*1e-6\} WPF=\{WPFP*1e-6\} LSW=\{LSWP*1e-6\} MSW=\{MSWP\} KDN=\{KDNP\} KDP=\{KDPP\} MINV=\{MSWP\} CW=\{CWP*1e-6\} CL=\{CLP*1e-6\}}
C {lab_pin.sym} 1080 -640 0 1 {name=lp9 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 950 -590 0 0 {name=lp10 sig_type=std_logic lab=vin}
C {lab_pin.sym} 1150 -590 0 1 {name=lp11 sig_type=std_logic lab=sh_out}
C {lab_pin.sym} 1020 -510 0 0 {name=lp12 sig_type=std_logic lab=sh_en}
C {gnd.sym} 1080 -510 0 0 {name=lg13 lab=GND}
C {555_comparator.sym} 1400 -560 0 0 {name=x3}
C {lab_pin.sym} 1440 -630 0 1 {name=lp14 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1420 -640 0 0 {name=lp15 sig_type=std_logic lab=pbias}
C {lab_pin.sym} 1550 -560 0 1 {name=lp16 sig_type=std_logic lab=cout}
C {lab_pin.sym} 1380 -580 0 0 {name=lp17 sig_type=std_logic lab=sh_out}
C {lab_pin.sym} 1380 -540 0 0 {name=lp18 sig_type=std_logic lab=vdac}
C {gnd.sym} 1440 -490 0 0 {name=lg19 lab=GND}
C {sg13cmos5l_pr/sg13_hv_pmos.sym} 1700 -560 0 0 {name=MPB
l=1u
w=0.8u
ng=1
m=1
mm_ok=1
model=sg13_hv_pmos
spiceprefix=X
}
C {lab_pin.sym} 1720 -530 0 1 {name=lp20 sig_type=std_logic lab=pbias}
C {lab_pin.sym} 1680 -560 0 0 {name=lp21 sig_type=std_logic lab=pbias}
C {lab_pin.sym} 1720 -590 0 1 {name=lp22 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1720 -560 0 1 {name=lp23 sig_type=std_logic lab=VDDA}
C {isource.sym} 1720 -460 0 0 {name=IBC value=\{IBCOMP\}}
C {lab_pin.sym} 1720 -490 0 1 {name=lp24 sig_type=std_logic lab=pbias}
C {gnd.sym} 1720 -430 0 0 {name=lg25 lab=GND}
C {sah_12bit_param.sym} 1000 -260 0 0 {name=x2 WNF=\{WNFP*1e-6\} WPF=\{WPFP*1e-6\} LSW=\{LSWP*1e-6\} MSW=\{MSWP\} KDN=\{KDNP\} KDP=\{KDPP\} MINV=\{MSWP\} CW=\{CWP*1e-6\} CL=\{CLP*1e-6\}}
C {lab_pin.sym} 1080 -340 0 1 {name=lp26 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 950 -290 0 0 {name=lp27 sig_type=std_logic lab=vin}
C {lab_pin.sym} 1150 -290 0 1 {name=lp28 sig_type=std_logic lab=sh_ref}
C {lab_pin.sym} 1020 -210 0 0 {name=lp29 sig_type=std_logic lab=sh_en}
C {gnd.sym} 1080 -210 0 0 {name=lg30 lab=GND}
C {capa.sym} 1250 -260 0 0 {name=CREF
m=1
value=\{CREF\}
footprint=1206
device="ceramic capacitor"}
C {lab_pin.sym} 1250 -290 0 1 {name=lp31 sig_type=std_logic lab=sh_ref}
C {gnd.sym} 1250 -230 0 0 {name=lg32 lab=GND}
C {title.sym} 160 0 0 0 {name=l0 author="FAIf team"}
