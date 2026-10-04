v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {Testbench sah_12bit - switch on-resistance Ron(Vin) in track mode} 80 -1500 0 0 0.7 0.7 {}
T {SH_EN = VDDA (track). VIN sweeps SH_IN from 0 to VDDA, EFORCE holds SH_OUT at VIN + 1 mV (code block),
Ron = 1 mV / |I(EFORCE)|. Run setups: switch finger widths WNF/WPF and length LSW (MSW = 1), temperature list.
Results: simulations/sah_12bit_ideal_tb_dc.txt (columns per run: vin_V ron_ohm), evaluated by ../../scripts/sizing/cs_sizing.py} 80 -1440 0 0 0.3 0.3 {}
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
value="** ===== sah_12bit sizes (um), set per run by the NGSPICE block =====
.param WNFP=0.6 WPFP=1.8 LSWP=0.45 MSWP=1 KDNP=0.5 KDPP=0.5 CWP=59.63 CLP=25.2
** SH_OUT forced to SH_IN + 1 mV (VFORCE in series measures the switch current)
EFORCE sh_out_e 0 vol='V(vin)+1m'
"}
C {code_shown.sym} 620 -1250 0 0 {name=NGSPICE only_toplevel=true
value="
.options method=gear reltol=1e-6 abstol=1e-16 gmin=1e-18
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
  set outtxt = sah_12bit_ideal_tb_dc.txt
  set outraw = sah_12bit_ideal_tb_dc.raw
  if $?pvt_tag
    set outtxt = \\"sah_12bit_ideal_tb_dc$pvt_tag$ext_txt\\"
    set outraw = \\"sah_12bit_ideal_tb_dc$pvt_tag$ext_raw\\"
  end
  ** ===== run setups (one column each): today's switch at L = 0.6 / 0.45 um, half and double width, frozen sah_12bit =====
  **           1      2      3      4      5
  set wn_l = ( 4      4      2      8      0.6 )
  set wp_l = ( 14     14     7      28     1.8 )
  set ls_l = ( 0.6    0.45   0.6    0.6    0.45 )
  set runs = ( 1 2 3 4 5 )
  if $?pvt_temp
    set runs = ( 5 )
  end
  set temps = ( -40 27 125 )
  if $?pvt_temp
    set temps = ( $pvt_temp )
  end
  echo corner temp_C vdd_V run wnf_um wpf_um lsw_um vin_V ron_ohm > $outtxt
  foreach temp_c $temps
  foreach vdd $vdds
  foreach r $runs
    alterparam VDDA = $vdd
    alterparam WNFP = $wn_l[$r]
    alterparam WPFP = $wp_l[$r]
    alterparam LSWP = $ls_l[$r]
    reset
    option temp = $temp_c
    let vmax = $vdd - 0.001
    dc VIN 0 $&vmax 0.025
    let ron = 1e-3/abs(i(vforce))
    let n = length(ron)
    let k = 0
    while k < n
      let vk = v(vin)[k]
      let rk = ron[k]
      echo $pvt_corner $temp_c $vdd $r $wn_l[$r] $wp_l[$r] $ls_l[$r] $&vk $&rk >> $outtxt
      let k = k + 1
    end
    destroy all
  end
  end
  end
  echo
  echo ===== Results: simulations/$outtxt =====
.endc
"}
C {launcher.sym} 1700 -1500 0 0 {name=h1
descr="Simulate"
tclcommand="xschem save; xschem netlist; xschem simulate"
}
C {launcher.sym} 1700 -1450 0 0 {name=h2
descr="Load waves"
tclcommand="xschem raw_read $netlist_dir/[file rootname [file tail [xschem get current_name]]].raw tran"
}
C {vsource.sym} 120 -560 0 0 {name=VVDDA value=\{VDDA\} savecurrent=false}
C {lab_pin.sym} 120 -590 0 1 {name=lp1 sig_type=std_logic lab=VDDA}
C {gnd.sym} 120 -530 0 0 {name=lg2 lab=GND}
C {vsource.sym} 300 -560 0 0 {name=VSHEN value=\{VDDA\} savecurrent=false}
C {lab_pin.sym} 300 -590 0 1 {name=lp3 sig_type=std_logic lab=sh_en}
C {gnd.sym} 300 -530 0 0 {name=lg4 lab=GND}
C {vsource.sym} 480 -560 0 0 {name=VIN value=0 savecurrent=false}
C {lab_pin.sym} 480 -590 0 1 {name=lp5 sig_type=std_logic lab=vin}
C {gnd.sym} 480 -530 0 0 {name=lg6 lab=GND}
C {vsource.sym} 1100 -560 0 0 {name=VFORCE value=0 savecurrent=false}
C {lab_pin.sym} 1100 -590 0 1 {name=lp7 sig_type=std_logic lab=sh_out_f}
C {lab_pin.sym} 1100 -530 0 1 {name=lp8 sig_type=std_logic lab=sh_out_e}
C {sah_12bit_param.sym} 800 -560 0 0 {name=x1 WNF=\{WNFP*1e-6\} WPF=\{WPFP*1e-6\} LSW=\{LSWP*1e-6\} MSW=\{MSWP\} KDN=\{KDNP\} KDP=\{KDPP\} MINV=\{MSWP\} CW=\{CWP*1e-6\} CL=\{CLP*1e-6\}}
C {lab_pin.sym} 880 -640 0 1 {name=lp9 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 750 -590 0 0 {name=lp10 sig_type=std_logic lab=vin}
C {lab_pin.sym} 950 -590 0 1 {name=lp11 sig_type=std_logic lab=sh_out_f}
C {lab_pin.sym} 820 -510 0 0 {name=lp12 sig_type=std_logic lab=sh_en}
C {gnd.sym} 880 -510 0 0 {name=lg13 lab=GND}
C {title.sym} 160 0 0 0 {name=l0 author="FAIf team"}
