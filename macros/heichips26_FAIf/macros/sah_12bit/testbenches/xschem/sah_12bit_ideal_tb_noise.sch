v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {Testbench sah_12bit - sampled thermal noise (kT/C check), ideal source} 80 -1500 0 0 0.7 0.7 {}
T {SH_EN = VDDA (track), ideal VIN (ac 1) at VLEV. .noise of v(sh_out) integrated from 1 Hz to 100 GHz is the noise that is
frozen on the hold cap at the sampling instant; cs_sizing.py compares it with kT/C_eff (C_eff from the 1 Hz admittance of SH_OUT).
Results: simulations/sah_12bit_ideal_tb_noise.txt, evaluated by ../../scripts/sizing/cs_sizing.py} 80 -1440 0 0 0.3 0.3 {}
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
value="** ===== level, comparator-gate load and sah_12bit sizes (um) =====
.param VLEV=1.65
.param CLOAD=20f
.param WNFP=0.6 WPFP=1.8 LSWP=0.45 MSWP=1 KDNP=0.5 KDPP=0.5 CWP=59.63 CLP=25.2
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
  set outtxt = sah_12bit_ideal_tb_noise.txt
  set outraw = sah_12bit_ideal_tb_noise.raw
  if $?pvt_tag
    set outtxt = \\"sah_12bit_ideal_tb_noise$pvt_tag$ext_txt\\"
    set outraw = \\"sah_12bit_ideal_tb_noise$pvt_tag$ext_raw\\"
  end
  set temps = ( 27 125 )
  if $?pvt_temp
    set temps = ( $pvt_temp )
  end
  ** noise in V^2/Hz and V^2 (fixed units)
  set sqrnoise
  set cws = ( 13.35 48.95 194.91 )
  set vlevs = ( 0.5 1.65 2.8 )
  echo corner temp_C vdd_V cw_um vlev_V ceff_pF vn_uV > $outtxt
  foreach temp_c $temps
  foreach vdd $vdds
  foreach cw $cws
  foreach vl $vlevs
    alterparam VDDA = $vdd
    alterparam CWP = $cw
    alterparam VLEV = $vl
    reset
    option temp = $temp_c
    ** C_eff of the hold node: 1 Hz current from the ideal source (I = j*w*C_eff*1V, Ron negligible)
    save all
    ac dec 1 1 1
    let ceff = abs(imag(i(vin)))/(2*pi)*1e12
    set ceff_s = $&ceff
    ** sampled noise = total output noise of v(sh_out) in track
    save all
    noise v(sh_out) vin dec 20 1 100g
    setplot noise2
    let vn = sqrt(v(onoise_total))*1e6
    echo $pvt_corner $temp_c $vdd $cw $vl $ceff_s $&vn >> $outtxt
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
C {vsource.sym} 480 -560 0 0 {name=VIN value="\{VLEV\} ac 1" savecurrent=true}
C {lab_pin.sym} 480 -590 0 1 {name=lp5 sig_type=std_logic lab=vin}
C {gnd.sym} 480 -530 0 0 {name=lg6 lab=GND}
C {sah_12bit_param.sym} 800 -560 0 0 {name=x1 WNF=\{WNFP*1e-6\} WPF=\{WPFP*1e-6\} LSW=\{LSWP*1e-6\} MSW=\{MSWP\} KDN=\{KDNP\} KDP=\{KDPP\} MINV=\{MSWP\} CW=\{CWP*1e-6\} CL=\{CLP*1e-6\}}
C {lab_pin.sym} 880 -640 0 1 {name=lp7 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 750 -590 0 0 {name=lp8 sig_type=std_logic lab=vin}
C {lab_pin.sym} 950 -590 0 1 {name=lp9 sig_type=std_logic lab=sh_out}
C {lab_pin.sym} 820 -510 0 0 {name=lp10 sig_type=std_logic lab=sh_en}
C {gnd.sym} 880 -510 0 0 {name=lg11 lab=GND}
C {capa.sym} 1050 -560 0 0 {name=CLOAD
m=1
value=\{CLOAD\}
footprint=1206
device="ceramic capacitor"}
C {lab_pin.sym} 1050 -590 0 1 {name=lp12 sig_type=std_logic lab=sh_out}
C {gnd.sym} 1050 -530 0 0 {name=lg13 lab=GND}
C {title.sym} 160 0 0 0 {name=l0 author="FAIf team"}
