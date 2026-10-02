v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
B 2 1500 -1300 2400 -900 {flags=graph
y1=-140
y2=5
ypos1=0
ypos2=2
divy=5
subdivy=1
unity=1
x1=3
x2=9
divx=6
subdivx=8
xlabmag=1.0
ylabmag=1.0
dataset=-1
unitx=1
logx=1
logy=0
linewidth_mult=2
color=4
node="\\"sh_out [dB]; sh_out db20()\\""
sim_type=ac
autoload=0}
T {Testbench for AC analysis - Sample & Hold with capacitor trim} 80 -2000 0 0 0.8 0.8 {}
T {The S&H alone, driven by an ideal source (dc VLEV, ac 1 V) and loaded by CLOAD (comparator input).
RB (1 GOhm to VLEV) sets the DC level of the hold node in hold mode; it does not matter above a few kHz.
For every trim code, input/hold level and mode (written to simulations/sample_and_hold_trim_tb_ac.txt):
  track (SH_EN high): -3 dB bandwidth f3db and transfer at 1 MHz  (switch on-resistance with the hold capacitance)
  hold  (SH_EN low) : isolation sh_out/sh_in at 1 MHz, 10 MHz and 100 MHz (off-state feedthrough)
Trim codes: cap_en = 0 (smallest hold capacitance) and 15 (largest). Add more codes in the 'codes' list of the NGSPICE block.
PVT: nominal corner in the PVT block, temperature/supply lists in the NGSPICE block.
'make sim-xschem-pvt TB=sample_and_hold_trim_tb_ac' runs the PVT points of the Makefile (PVT variable), outputs get a _<corner>_<temp>C_<vdd>V suffix.} 80 -1940 0 0 0.3 0.3 {}
C {title.sym} 160 0 0 0 {name=l1 author="FAIf team"}
C {code_shown.sym} 80 -1650 0 0 {name=PVT only_toplevel=true
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
C {code_shown.sym} 900 -1650 0 0 {name=PARAMS only_toplevel=true
value="** ===== Stimulus and load =====
** input / hold-node DC level, set per run by the NGSPICE block
.param VLEV=1.65
** SH_EN: 1 = track, 0 = hold, set per run by the NGSPICE block
.param SHTRK=1
** comparator input load and hold-node bias resistor
.param CLOAD=20f
.param RBIAS=1e9
** trim bits cap_en[3:0], set per run by the NGSPICE block
.param CE0=0 CE1=0 CE2=0 CE3=0
"}
C {code_shown.sym} 2500 -2000 0 0 {name=NGSPICE only_toplevel=true
value="
** same solver settings as the transient testbenches
.options method=gear reltol=1e-4 abstol=1e-15 gmin=1e-18
.control
  ** ===== sweep lists =====
  ** trim codes for cap_en[3:0]: 0 = smallest, 15 = largest hold capacitance
  set codes = ( 0 15 )
  ** DC level of the input (track) / of the hold node (hold)
  set levels = ( 0.5 1.65 2.8 )
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
  set ext_txt = .txt
  set ext_raw = .raw
  ** output names: <tb><pvt_tag>.<ext>, the tag only exists for PVT runs
  if $?pvt_tag
    set outtxt = \\"@schname\\\\$pvt_tag$ext_txt\\"
    set outraw = \\"@schname\\\\$pvt_tag$ext_raw\\"
  else
    set outtxt = \\"@schname\\\\$ext_txt\\"
    set outraw = \\"@schname\\\\$ext_raw\\"
  end

  echo corner temp_C vdd_V code mode vin_V f3db_MHz gain_1MHz_dB iso_1MHz_dB iso_10MHz_dB iso_100MHz_dB > $outtxt
  unset appendwrite
  foreach temp_c $temps
  foreach vdd $vdds
  foreach code $codes
    ** split the trim code into the cap_en bits
    let b0 = $code - 2*floor($code/2)
    let b1 = floor($code/2) - 2*floor($code/4)
    let b2 = floor($code/4) - 2*floor($code/8)
    let b3 = floor($code/8) - 2*floor($code/16)
    foreach lev $levels
    ** shtrk = 1: SH_EN high (track), 0: SH_EN low (hold)
    foreach shtrk 1 0
      alterparam VDDA = $vdd
      alterparam CE0 = $&b0
      alterparam CE1 = $&b1
      alterparam CE2 = $&b2
      alterparam CE3 = $&b3
      alterparam VLEV = $lev
      alterparam SHTRK = $shtrk
      reset
      ** set the temperature after reset (reset restores the netlist temperature)
      option temp = $temp_c
      save v(sh_in) v(sh_out)
      ac dec 20 1k 1G
      write $outraw
      set appendwrite
      ** transfer sh_out/sh_in in dB (sh_in is the ideal 1 V AC source)
      let tf_db = vdb(sh_out)
      meas ac a1m find tf_db at=1e6
      if $shtrk = 1
        meas ac amin min tf_db
        if amin < -3
          meas ac f3db when tf_db=-3 fall=1
          let f3db_mhz = f3db/1e6
          echo $pvt_corner $temp_c $vdd $code track $lev $&f3db_mhz $&a1m - - - >> $outtxt
        else
          ** no -3 dB point below 1 GHz
          echo $pvt_corner $temp_c $vdd $code track $lev over_1000 $&a1m - - - >> $outtxt
        end
      else
        meas ac a10m find tf_db at=1e7
        meas ac a100m find tf_db at=1e8
        echo $pvt_corner $temp_c $vdd $code hold $lev - - $&a1m $&a10m $&a100m >> $outtxt
      end
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
C {launcher.sym} 1560 -1400 0 0 {name=h1
descr="Simulate"
tclcommand="xschem save; xschem netlist; xschem simulate"
}
C {launcher.sym} 1560 -1350 0 0 {name=h2
descr="Load waves"
tclcommand="xschem raw_read $netlist_dir/[file rootname [file tail [xschem get current_name]]].raw ac"
}
C {vsource.sym} 120 -1000 0 0 {name=VVDDA value=\{VDDA\} savecurrent=false}
C {lab_pin.sym} 120 -1030 0 0 {name=p1 sig_type=std_logic lab=VDDA}
C {gnd.sym} 120 -970 0 0 {name=l2 lab=GND}
C {vsource.sym} 120 -860 0 0 {name=VIN value="dc \{VLEV\} ac 1" savecurrent=false}
C {lab_pin.sym} 120 -890 0 0 {name=p2 sig_type=std_logic lab=sh_in}
C {gnd.sym} 120 -830 0 0 {name=l3 lab=GND}
C {vsource.sym} 120 -720 0 0 {name=VSHEN value=\{VDDA*SHTRK\} savecurrent=false}
C {lab_pin.sym} 120 -750 0 0 {name=p3 sig_type=std_logic lab=sh_en}
C {gnd.sym} 120 -690 0 0 {name=l4 lab=GND}
C {vsource.sym} 120 -580 0 0 {name=VB value=\{VLEV\} savecurrent=false}
C {lab_pin.sym} 120 -610 0 0 {name=p4 sig_type=std_logic lab=vb}
C {gnd.sym} 120 -550 0 0 {name=l5 lab=GND}
C {vsource.sym} 300 -580 0 0 {name=VTRIM0 value=\{CE0*VDDA\} savecurrent=false}
C {lab_pin.sym} 300 -610 0 0 {name=p5 sig_type=std_logic lab=trim[0]}
C {gnd.sym} 300 -550 0 0 {name=l6 lab=GND}
C {vsource.sym} 420 -580 0 0 {name=VTRIM1 value=\{CE1*VDDA\} savecurrent=false}
C {lab_pin.sym} 420 -610 0 0 {name=p6 sig_type=std_logic lab=trim[1]}
C {gnd.sym} 420 -550 0 0 {name=l7 lab=GND}
C {vsource.sym} 540 -580 0 0 {name=VTRIM2 value=\{CE2*VDDA\} savecurrent=false}
C {lab_pin.sym} 540 -610 0 0 {name=p7 sig_type=std_logic lab=trim[2]}
C {gnd.sym} 540 -550 0 0 {name=l8 lab=GND}
C {vsource.sym} 660 -580 0 0 {name=VTRIM3 value=\{CE3*VDDA\} savecurrent=false}
C {lab_pin.sym} 660 -610 0 0 {name=p8 sig_type=std_logic lab=trim[3]}
C {gnd.sym} 660 -550 0 0 {name=l9 lab=GND}
C {sample_and_hold_trim.sym} 1060 -800 0 0 {name=xsh}
C {lab_pin.sym} 1140 -880 0 1 {name=p9 sig_type=std_logic lab=VDDA}
C {lab_pin.sym} 1010 -830 0 0 {name=p10 sig_type=std_logic lab=sh_in}
C {lab_pin.sym} 1210 -830 0 1 {name=p11 sig_type=std_logic lab=sh_out}
C {lab_pin.sym} 1080 -750 0 0 {name=p12 sig_type=std_logic lab=sh_en}
C {lab_pin.sym} 1140 -750 0 0 {name=p13 sig_type=std_logic lab=GND}
C {lab_pin.sym} 1170 -750 0 1 {name=p14 sig_type=std_logic lab=trim[3:0]}
N 1210 -830 1400 -830 {lab=sh_out}
C {capa.sym} 1300 -800 0 0 {name=CLOAD
m=1
value=\{CLOAD\}
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 1300 -770 0 0 {name=l10 lab=GND}
C {res.sym} 1400 -800 0 0 {name=RB
value=\{RBIAS\}
footprint=1206
device=resistor
m=1}
C {lab_pin.sym} 1400 -770 0 1 {name=p15 sig_type=std_logic lab=vb}
