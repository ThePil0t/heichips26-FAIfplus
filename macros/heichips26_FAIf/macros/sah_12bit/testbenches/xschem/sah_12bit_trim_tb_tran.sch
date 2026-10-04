v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {Testbench sah_12bit - does a hold-cap trim array cost accuracy? (trimmed vs fixed C of the same value)} 80 -1700 0 0 0.7 0.7 {}
T {Both S&Hs are driven by their own op_amp_ver_2 follower from the same VIN and loaded with CLOAD (comparator gate).
xF: sah_12bit with a fixed hold cap = total C of the code.  xT: sah_12bit with the base cap (27 rows, 0.50 pF) plus 4 trim
branches on SH_OUT, each an asw_inv switch (the existing trim switch cell) in series with a cap_cmomi of 7/14/27/54 rows
(0.13/0.26/0.50/0.99 pF, binary), enabled by cap_en[3:0] at VDDA. Range 0.50 ... 2.37 pF.
Stimulus as in sample_and_hold_trim_tb_tran: 4 track/hold cycles, VIN steps in mid-hold VLO -> VHI -> VMID -> VLO.
Per hold window k and output: pedestal, droop (first half of hold), acquisition time to 1/4 LSB (12 bit) in the next track window.
Results: simulations/sah_12bit_trim_tb_tran.txt (column out = F or T)} 80 -1640 0 0 0.3 0.3 {}
C {code_shown.sym} 80 -1400 0 0 {name=PVT only_toplevel=true
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
C {code_shown.sym} 80 -1150 0 0 {name=PARAMS only_toplevel=true
value="** ===== stimulus (as sample_and_hold_trim_tb_tran, 12-bit timing) =====
.param TTRK=10u
.param THLD=20u
.param TEDGE=1n
.param TINR=100n
.param TPER=\{TTRK+THLD+2*TEDGE\}
.param T0=\{TTRK+TEDGE+THLD/2\}
.param VLO=0.5
.param VMID=1.65
.param VHI=2.8
.param IBIAS=25n
.param CLOAD=20f
** trim code bits and the fixed-C width for the same total capacitance
.param CE0=0 CE1=0 CE2=0 CE3=0
.param CWF=24.92
** sah_12bit switch (um)
.param WNFP=0.6 WPFP=1.8 LSWP=0.45 KDNP=0.5 KDPP=0.5
.csparam ttrk=\{TTRK\}
.csparam thld=\{THLD\}
.csparam tedge=\{TEDGE\}
.csparam tper=\{TPER\}
.csparam tstop=\{TTRK+3*TPER+TEDGE+THLD\}
** follower feedback
VFBF ooaf fbf 0
VFBT ooat fbt 0
"}
C {code_shown.sym} 700 -1400 0 0 {name=NGSPICE only_toplevel=true
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
  set outtxt = sah_12bit_trim_tb_tran.txt
  set outraw = sah_12bit_trim_tb_tran.raw
  if $?pvt_tag
    set outtxt = \\"sah_12bit_trim_tb_tran$pvt_tag$ext_txt\\"
    set outraw = \\"sah_12bit_trim_tb_tran$pvt_tag$ext_raw\\"
  end
  set codes = ( 0 1 2 4 8 15 )
  set temps = ( 27 125 )
  if $?pvt_temp
    set temps = ( $pvt_temp )
  end
  if $?run_sel
    set rsel = $run_sel
    set code_all = ( 0 1 2 4 8 15 )
    set codes = ( $code_all[$rsel] )
  end
  echo corner temp_C vdd_V code ctrim_pF out hold vin_V ped_mV droop_mV_per_ms tacq_us > $outtxt
  foreach temp_c $temps
  foreach vdd $vdds
  foreach code $codes
    let b0 = $code - 2*floor($code/2)
    let b1 = floor($code/2) - 2*floor($code/4)
    let b2 = floor($code/4) - 2*floor($code/8)
    let b3 = floor($code/8) - 2*floor($code/16)
    let rows = 27 + 7*b0 + 14*b1 + 27*b2 + 54*b3
    let cwf = (rows + 1)*0.89
    let ctrim = rows*30*0.84*0.89*0.82e-3
    alterparam VDDA = $vdd
    alterparam CE0 = $&b0
    alterparam CE1 = $&b1
    alterparam CE2 = $&b2
    alterparam CE3 = $&b3
    alterparam CWF = $&cwf
    reset
    option temp = $temp_c
    save v(vin) v(sh_outf) v(sh_outt)
    tran 10n $&tstop 0 50n
    let tol = $vdd/4096/4
    foreach o f t
      let k = 0
      while k < 4
        let th = ttrk + k*tper
        let tpre = th - 10n
        let tped = th + tedge + 200n
        let tdr = th + tedge + thld/2 - 10n
        meas tran vtrk find v(sh_out$o) at=$&tpre
        meas tran vped find v(sh_out$o) at=$&tped
        meas tran vdr find v(sh_out$o) at=$&tdr
        meas tran vlev find v(vin) at=$&tpre
        let ped_mv = (vped - vtrk)*1e3
        let droop = (vdr - vped)/(tdr - tped)
        let tacq_us = -1
        if k < 3
          let ta = th + tedge + thld
          let tfin = th + tper - 10n
          meas tran vfin find v(sh_out$o) at=$&tfin
          let err = abs(v(sh_out$o) - vfin)
          meas tran errmax max err from=$&ta to=$&tfin
          let tacq_us = 0
          if errmax > tol
            meas tran tsettled when err=$&tol fall=last from=$&ta to=$&tfin
            let tacq_us = (tsettled - ta)*1e6
          end
        end
        echo $pvt_corner $temp_c $vdd $code $&ctrim $o $&k $&vlev $&ped_mv $&droop $&tacq_us >> $outtxt
        let k = k + 1
      end
    end
    destroy all
  end
  end
  end
  echo
  echo ===== Results: simulations/$outtxt =====
  shell cat $outtxt
.endc
"}
C {launcher.sym} 2600 -1700 0 0 {name=h1
descr="Simulate"
tclcommand="xschem save; xschem netlist; xschem simulate"
}
C {launcher.sym} 2600 -1650 0 0 {name=h2
descr="Load waves"
tclcommand="xschem raw_read $netlist_dir/[file rootname [file tail [xschem get current_name]]].raw tran"
}
C {vsource.sym} 120 -760 0 0 {name=VVDDA value=\{VDDA\} savecurrent=false}
C {lab_pin.sym} 120 -790 0 1 {name=lp1 sig_type=std_logic lab=VDDA}
C {gnd.sym} 120 -730 0 0 {name=lg2 lab=GND}
C {vsource.sym} 300 -760 0 0 {name=VIN value="pwl(0 \{VLO\} \{T0\} \{VLO\} \{T0+TINR\} \{VHI\} \{T0+TPER\} \{VHI\} \{T0+TPER+TINR\} \{VMID\} \{T0+2*TPER\} \{VMID\} \{T0+2*TPER+TINR\} \{VLO\})" savecurrent=false}
C {lab_pin.sym} 300 -790 0 1 {name=lp3 sig_type=std_logic lab=vin}
C {gnd.sym} 300 -730 0 0 {name=lg4 lab=GND}
C {vsource.sym} 480 -760 0 0 {name=VSHEN value="pulse(\{VDDA\} 0 \{TTRK\} \{TEDGE\} \{TEDGE\} \{THLD\} \{TPER\})" savecurrent=false}
C {lab_pin.sym} 480 -790 0 1 {name=lp5 sig_type=std_logic lab=sh_en}
C {gnd.sym} 480 -730 0 0 {name=lg6 lab=GND}
C {vsource.sym} 660 -760 0 0 {name=VTRIM0 value=\{CE0*VDDA\} savecurrent=false}
C {lab_pin.sym} 660 -790 0 1 {name=lp7 sig_type=std_logic lab=en0}
C {gnd.sym} 660 -730 0 0 {name=lg8 lab=GND}
C {vsource.sym} 820 -760 0 0 {name=VTRIM1 value=\{CE1*VDDA\} savecurrent=false}
C {lab_pin.sym} 820 -790 0 1 {name=lp9 sig_type=std_logic lab=en1}
C {gnd.sym} 820 -730 0 0 {name=lg10 lab=GND}
C {vsource.sym} 980 -760 0 0 {name=VTRIM2 value=\{CE2*VDDA\} savecurrent=false}
C {lab_pin.sym} 980 -790 0 1 {name=lp11 sig_type=std_logic lab=en2}
C {gnd.sym} 980 -730 0 0 {name=lg12 lab=GND}
C {vsource.sym} 1140 -760 0 0 {name=VTRIM3 value=\{CE3*VDDA\} savecurrent=false}
C {lab_pin.sym} 1140 -790 0 1 {name=lp13 sig_type=std_logic lab=en3}
C {gnd.sym} 1140 -730 0 0 {name=lg14 lab=GND}
C {isource.sym} 120 -460 0 0 {name=IBIASF value=\{IBIAS\}}
C {lab_pin.sym} 120 -490 0 1 {name=lp15 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 120 -430 0 1 {name=lp16 sig_type=std_logic lab=ireff}
C {isource.sym} 300 -460 0 0 {name=IBIAST value=\{IBIAS\}}
C {lab_pin.sym} 300 -490 0 1 {name=lp17 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 300 -430 0 1 {name=lp18 sig_type=std_logic lab=ireft}
C {op_amp_ver_2.sym} 700 -460 0 0 {name=x1}
C {lab_pin.sym} 710 -510 0 1 {name=lp19 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 670 -390 0 0 {name=lp20 sig_type=std_logic lab=ireff}
C {lab_pin.sym} 630 -480 0 0 {name=lp21 sig_type=std_logic lab=fbf}
C {lab_pin.sym} 800 -460 0 1 {name=lp22 sig_type=std_logic lab=ooaf}
C {lab_pin.sym} 630 -440 0 0 {name=lp23 sig_type=std_logic lab=vin}
C {gnd.sym} 710 -410 0 0 {name=lg24 lab=GND}
C {gnd.sym} 670 -530 0 0 {name=lg25 lab=GND}
C {sah_12bit_param.sym} 1000 -460 0 0 {name=xF WNF=\{WNFP*1e-6\} WPF=\{WPFP*1e-6\} LSW=\{LSWP*1e-6\} MSW=1 KDN=\{KDNP\} KDP=\{KDPP\} MINV=1 CL=25.2e-6 CW=\{CWF*1e-6\}}
C {lab_pin.sym} 1080 -540 0 1 {name=lp26 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 950 -490 0 0 {name=lp27 sig_type=std_logic lab=ooaf}
C {lab_pin.sym} 1150 -490 0 1 {name=lp28 sig_type=std_logic lab=sh_outf}
C {lab_pin.sym} 1020 -410 0 0 {name=lp29 sig_type=std_logic lab=sh_en}
C {gnd.sym} 1080 -410 0 0 {name=lg30 lab=GND}
C {capa.sym} 1250 -460 0 0 {name=CLOADF
m=1
value=\{CLOAD\}
footprint=1206
device="ceramic capacitor"}
C {lab_pin.sym} 1250 -490 0 1 {name=lp31 sig_type=std_logic lab=sh_outf}
C {gnd.sym} 1250 -430 0 0 {name=lg32 lab=GND}
C {op_amp_ver_2.sym} 700 -160 0 0 {name=x2}
C {lab_pin.sym} 710 -210 0 1 {name=lp33 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 670 -90 0 0 {name=lp34 sig_type=std_logic lab=ireft}
C {lab_pin.sym} 630 -180 0 0 {name=lp35 sig_type=std_logic lab=fbt}
C {lab_pin.sym} 800 -160 0 1 {name=lp36 sig_type=std_logic lab=ooat}
C {lab_pin.sym} 630 -140 0 0 {name=lp37 sig_type=std_logic lab=vin}
C {gnd.sym} 710 -110 0 0 {name=lg38 lab=GND}
C {gnd.sym} 670 -230 0 0 {name=lg39 lab=GND}
C {sah_12bit_param.sym} 1000 -160 0 0 {name=xT WNF=\{WNFP*1e-6\} WPF=\{WPFP*1e-6\} LSW=\{LSWP*1e-6\} MSW=1 KDN=\{KDNP\} KDP=\{KDPP\} MINV=1 CL=25.2e-6 CW=24.92e-6}
C {lab_pin.sym} 1080 -240 0 1 {name=lp40 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 950 -190 0 0 {name=lp41 sig_type=std_logic lab=ooat}
C {lab_pin.sym} 1150 -190 0 1 {name=lp42 sig_type=std_logic lab=sh_outt}
C {lab_pin.sym} 1020 -110 0 0 {name=lp43 sig_type=std_logic lab=sh_en}
C {gnd.sym} 1080 -110 0 0 {name=lg44 lab=GND}
C {capa.sym} 1250 -160 0 0 {name=CLOADT
m=1
value=\{CLOAD\}
footprint=1206
device="ceramic capacitor"}
C {lab_pin.sym} 1250 -190 0 1 {name=lp45 sig_type=std_logic lab=sh_outt}
C {gnd.sym} 1250 -130 0 0 {name=lg46 lab=GND}
C {asw_inv.sym} 1450 -160 0 0 {name=xsw0}
C {lab_pin.sym} 1380 -160 0 0 {name=lp47 sig_type=std_logic lab=sh_outt}
C {lab_pin.sym} 1520 -160 0 1 {name=lp48 sig_type=std_logic lab=nt0}
C {lab_pin.sym} 1450 -210 0 0 {name=lp49 sig_type=std_logic lab=en0}
C {lab_pin.sym} 1500 -110 0 1 {name=lp50 sig_type=std_logic lab=VDDA}
C {gnd.sym} 1490 -110 0 0 {name=lg51 lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 1560 -100 0 0 {name=CT0
model=cap_cmomi
w=7.12e-6
l=25.2e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {lab_pin.sym} 1560 -130 0 1 {name=lp52 sig_type=std_logic lab=nt0}
C {gnd.sym} 1560 -70 0 0 {name=lg53 lab=GND}
C {asw_inv.sym} 1710 -160 0 0 {name=xsw1}
C {lab_pin.sym} 1640 -160 0 0 {name=lp54 sig_type=std_logic lab=sh_outt}
C {lab_pin.sym} 1780 -160 0 1 {name=lp55 sig_type=std_logic lab=nt1}
C {lab_pin.sym} 1710 -210 0 0 {name=lp56 sig_type=std_logic lab=en1}
C {lab_pin.sym} 1760 -110 0 1 {name=lp57 sig_type=std_logic lab=VDDA}
C {gnd.sym} 1750 -110 0 0 {name=lg58 lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 1820 -100 0 0 {name=CT1
model=cap_cmomi
w=13.35e-6
l=25.2e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {lab_pin.sym} 1820 -130 0 1 {name=lp59 sig_type=std_logic lab=nt1}
C {gnd.sym} 1820 -70 0 0 {name=lg60 lab=GND}
C {asw_inv.sym} 1970 -160 0 0 {name=xsw2}
C {lab_pin.sym} 1900 -160 0 0 {name=lp61 sig_type=std_logic lab=sh_outt}
C {lab_pin.sym} 2040 -160 0 1 {name=lp62 sig_type=std_logic lab=nt2}
C {lab_pin.sym} 1970 -210 0 0 {name=lp63 sig_type=std_logic lab=en2}
C {lab_pin.sym} 2020 -110 0 1 {name=lp64 sig_type=std_logic lab=VDDA}
C {gnd.sym} 2010 -110 0 0 {name=lg65 lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 2080 -100 0 0 {name=CT2
model=cap_cmomi
w=24.92e-6
l=25.2e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {lab_pin.sym} 2080 -130 0 1 {name=lp66 sig_type=std_logic lab=nt2}
C {gnd.sym} 2080 -70 0 0 {name=lg67 lab=GND}
C {asw_inv.sym} 2230 -160 0 0 {name=xsw3}
C {lab_pin.sym} 2160 -160 0 0 {name=lp68 sig_type=std_logic lab=sh_outt}
C {lab_pin.sym} 2300 -160 0 1 {name=lp69 sig_type=std_logic lab=nt3}
C {lab_pin.sym} 2230 -210 0 0 {name=lp70 sig_type=std_logic lab=en3}
C {lab_pin.sym} 2280 -110 0 1 {name=lp71 sig_type=std_logic lab=VDDA}
C {gnd.sym} 2270 -110 0 0 {name=lg72 lab=GND}
C {sg13cmos5l_pr/cap_cmomi.sym} 2340 -100 0 0 {name=CT3
model=cap_cmomi
w=48.95e-6
l=25.2e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}
C {lab_pin.sym} 2340 -130 0 1 {name=lp73 sig_type=std_logic lab=nt3}
C {gnd.sym} 2340 -70 0 0 {name=lg74 lab=GND}
C {title.sym} 160 0 0 0 {name=l0 author="FAIf team"}
