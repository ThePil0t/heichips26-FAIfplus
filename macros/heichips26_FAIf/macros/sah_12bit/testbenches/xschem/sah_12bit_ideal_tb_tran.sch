v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {Testbench sah_12bit - ideal source (infinite drive): pedestal, droop, feedthrough, acquisition, C_eff} 80 -1500 0 0 0.7 0.7 {}
T {VIN is an ideal 0-Ohm source directly on SH_IN, CLOAD = comparator gate. One run per (setup, VLEV):
  track (VLEV) -> hold: pedestal, droop at VIN = VLEV, VIN steps to VFAR in mid-hold: feedthrough, droop at VIN = VFAR (off-switch leakage)
  -> track (VFAR): acquisition of a large step (settling to 1/4 and 1/2 LSB of 12 bit, tail time constant tau), C_eff = Q(VIN)/dV
  -> hold: pedestal at VFAR.   VFAR = VDDA - 0.1 V for VLEV < VDDA/2, else 0.1 V (always a large step).
Run setups (lists in the NGSPICE block): hold cap size CW (CL = 25.2 um, M1-M3 MOM), switch multiplier MSW (= gate inverter MINV),
finger widths WNF/WPF, switch length LSW, dummy fractions KDN/KDP, SH_EN fall/rise time TF.  'make sim-xschem-pvt' runs only setup 15 (frozen switch, hold cap at -35 %: droop/leakage worst case).
Results: simulations/sah_12bit_ideal_tb_tran.txt, evaluated by ../../scripts/sizing/cs_sizing.py} 80 -1440 0 0 0.3 0.3 {}
C {code_shown.sym} 80 -1200 0 0 {name=PVT only_toplevel=true
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
C {code_shown.sym} 80 -940 0 0 {name=PARAMS only_toplevel=true
value="** ===== Stimulus timing and levels =====
.param TTRK1=1u
.param THLD=20u
.param TTRK2=1u
.param TF=1n
.param TPED=100n
.param TINR=100n
.param VLEV=0.5
.param VFAR=3.2
.param CLOAD=20f
** ===== sah_12bit sizes (um), set per run by the NGSPICE block =====
.param WNFP=0.6 WPFP=1.8 LSWP=0.45 MSWP=1 KDNP=0.5 KDPP=0.5 CWP=59.63 CLP=25.2
** derived edge times
.param TH1=\{TTRK1\}
.param TA=\{TTRK1+TF+THLD\}
.param TH2=\{TA+TF+TTRK2\}
.csparam th1=\{TH1\}
.csparam ta=\{TA\}
.csparam th2=\{TH2\}
.csparam thld=\{THLD\}
.csparam tf=\{TF\}
.csparam tped=\{TPED\}
.csparam tinr=\{TINR\}
.csparam tstop=\{TH2+TF+TPED+50n\}
"}
C {code_shown.sym} 620 -1200 0 0 {name=NGSPICE only_toplevel=true
value="
** gear + tight tolerances: pedestal and droop are uV effects; tiny gmin: droop comes from pA leakage
.options method=gear reltol=1e-6 vntol=1e-10 abstol=1e-16 chgtol=1e-20 gmin=1e-18
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
  set outtxt = sah_12bit_ideal_tb_tran.txt
  set outraw = sah_12bit_ideal_tb_tran.raw
  if $?pvt_tag
    set outtxt = \\"sah_12bit_ideal_tb_tran$pvt_tag$ext_txt\\"
    set outraw = \\"sah_12bit_ideal_tb_tran$pvt_tag$ext_raw\\"
  end

  ** ===== run setups (one column each) =====
  ** runs 1-14: today's switch (4/14 um) scaled and varied; 15/16: frozen sah_12bit switch at C -35 % / nominal (1.21 pF)
  **           1      2      3      4      5      6      7      8      9      10     11     12     13     14     15     16
  set cw_l = ( 13.35  48.95  48.95  48.95  194.91 48.95  48.95  194.91 48.95  48.95  48.95  48.95  48.95  48.95  39.16  59.63 )
  set ms_l = ( 1      1      1      1      1      2      4      4      1      1      1      1      1      1      1      1 )
  set wn_l = ( 4      4      4      4      4      4      4      4      2      4      4      4      4      4      0.6    0.6 )
  set wp_l = ( 14     14     14     14     14     14     14     14     7      14     14     14     10     20     1.8    1.8 )
  set ls_l = ( 0.6    0.6    0.6    0.6    0.6    0.6    0.6    0.6    0.6    0.45   0.6    0.6    0.6    0.6    0.45   0.45 )
  set kn_l = ( 0.5    0.5    0.5    0.5    0.5    0.5    0.5    0.5    0.5    0.5    0.4    0.6    0.5    0.5    0.5    0.5 )
  set kp_l = ( 0.5    0.5    0.5    0.5    0.5    0.5    0.5    0.5    0.5    0.5    0.4    0.6    0.5    0.5    0.5    0.5 )
  set tf_l = ( 1      0.1    1      5      1      1      1      1      1      1      1      1      1      1      1      1 )
  set runs = ( 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 )
  if $?pvt_temp
    set runs = ( 15 )
  end
  ** single setup (parallel runs): ngspice -D run_sel=<n> -D pvt_tag=_r<n>
  if $?run_sel
    set runs = ( $run_sel )
  end
  set vlevs = ( 0.1 0.3 0.5 0.7 0.9 1.1 1.3 1.5 1.7 1.9 2.1 2.3 2.5 2.7 2.9 3.1 )
  ** quick check: ngspice -D quick=1
  if $?quick
    set runs = ( 3 )
    set vlevs = ( 0.5 2.5 )
  end

  echo corner temp_C vdd_V run cw_um msw wnf_um wpf_um lsw_um kdn kdp tf_ns vlev_V vfar_V ceff_pF trk_uV ped_mV ped2_mV droop_mV_per_ms droop2_mV_per_ms ft_dB tset_q_ns tset_h_ns tau_ns > $outtxt
  foreach temp_c $temps
  foreach vdd $vdds
  foreach r $runs
  foreach vl $vlevs
    alterparam VDDA = $vdd
    alterparam CWP = $cw_l[$r]
    alterparam MSWP = $ms_l[$r]
    alterparam WNFP = $wn_l[$r]
    alterparam WPFP = $wp_l[$r]
    alterparam LSWP = $ls_l[$r]
    alterparam KDNP = $kn_l[$r]
    alterparam KDPP = $kp_l[$r]
    alterparam TF = $tf_l[$r]n
    alterparam VLEV = $vl
    let vlev = $vl
    if vlev < $vdd/2
      let vfar = $vdd - 0.1
    else
      let vfar = 0.1
    end
    alterparam VFAR = $&vfar
    reset
    option temp = $temp_c
    save v(sh_out) i(vin)
    tran 0.1n $&tstop 0 20n

    let vlev = $vl
    let vfar = 0.1
    if vlev < $vdd/2
      let vfar = $vdd - 0.1
    end
    let lsb = $vdd/4096
    ** first hold window: pedestal and droop at VIN = VLEV
    let tpre1 = th1 - 1n
    let tped1 = th1 + tf + tped
    let tstep = th1 + tf + thld/2
    let tdr1 = tstep - 1n
    meas tran vtrk find v(sh_out) at=$&tpre1
    meas tran vped find v(sh_out) at=$&tped1
    meas tran vdr1 find v(sh_out) at=$&tdr1
    let trk_uv = (vtrk - vlev)*1e6
    let ped_mv = (vped - vtrk)*1e3
    let droop = (vdr1 - vped)/(tdr1 - tped1)
    ** input step during hold: feedthrough (droop removed), then droop at VIN = VFAR
    let tft = tstep + tinr + tped
    let tend1 = ta - 1n
    meas tran vft find v(sh_out) at=$&tft
    meas tran vend1 find v(sh_out) at=$&tend1
    let ft_db = db(abs((vft - vdr1 - droop*(tft - tdr1))/(vfar - vlev)) + 1e-12)
    let droop2 = (vend1 - vft)/(tend1 - tft)
    ** second track window: acquisition of the large step and C_eff
    let tpre2 = th2 - 1n
    meas tran vfin find v(sh_out) at=$&tpre2
    let dv = abs(vfin - vend1)
    let err = abs(v(sh_out) - vfin)
    meas tran errmax max err from=$&ta to=$&tpre2
    let tolq = lsb/4
    let tolh = lsb/2
    let tset_q = 0
    let tset_h = 0
    if errmax > tolq
      meas tran tq when err=$&tolq fall=last from=$&ta to=$&tpre2
      let tset_q = (tq - ta)*1e9
    end
    if errmax > tolh
      meas tran tqh when err=$&tolh fall=last from=$&ta to=$&tpre2
      let tset_h = (tqh - ta)*1e9
    end
    let e2 = dv*1e-2
    let e3 = dv*1e-3
    meas tran t2 when err=$&e2 fall=last from=$&ta to=$&tpre2
    meas tran t3 when err=$&e3 fall=last from=$&ta to=$&tpre2
    let tau_ns = (t3 - t2)/ln(10)*1e9
    meas tran qin integ i(vin) from=$&ta to=$&tpre2
    let ceff = abs(qin)/dv*1e12
    ** second hold edge: pedestal at VFAR
    let tped2 = th2 + tf + tped
    meas tran vped2 find v(sh_out) at=$&tped2
    let ped2_mv = (vped2 - vfin)*1e3
    let droop_mvms = droop
    let droop2_mvms = droop2
    echo $pvt_corner $temp_c $vdd $r $cw_l[$r] $ms_l[$r] $wn_l[$r] $wp_l[$r] $ls_l[$r] $kn_l[$r] $kp_l[$r] $tf_l[$r] $vl $&vfar $&ceff $&trk_uv $&ped_mv $&ped2_mv $&droop_mvms $&droop2_mvms $&ft_db $&tset_q $&tset_h $&tau_ns >> $outtxt
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
C {vsource.sym} 120 -560 0 0 {name=VVDDA value=\{VDDA\} savecurrent=true}
C {lab_pin.sym} 120 -590 0 1 {name=lp1 sig_type=std_logic lab=VDDA}
C {gnd.sym} 120 -530 0 0 {name=lg2 lab=GND}
C {vsource.sym} 300 -560 0 0 {name=VSHEN value="pwl(0 \{VDDA\} \{TH1\} \{VDDA\} \{TH1+TF\} 0 \{TA\} 0 \{TA+TF\} \{VDDA\} \{TH2\} \{VDDA\} \{TH2+TF\} 0)" savecurrent=false}
C {lab_pin.sym} 300 -590 0 1 {name=lp3 sig_type=std_logic lab=sh_en}
C {gnd.sym} 300 -530 0 0 {name=lg4 lab=GND}
C {vsource.sym} 480 -560 0 0 {name=VIN value="pwl(0 \{VLEV\} \{TH1+TF+THLD/2\} \{VLEV\} \{TH1+TF+THLD/2+TINR\} \{VFAR\})" savecurrent=true}
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
