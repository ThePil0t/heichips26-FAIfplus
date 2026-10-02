# Generates sample_and_hold_trim_tb_vs_notrim.sch (xschem 3.4.8 format)
# Usage: python3 gen_tb_vs_notrim.py [output.sch]   (default: ../sample_and_hold_trim_tb_vs_notrim.sch)
# Edits made in xschem are lost on regeneration, port them to this script.
import os
import sys
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "sample_and_hold_trim_tb_vs_notrim.sch")
L = []; n = {"p": 0, "l": 0}
def lab(x, y, net, flip=0, rot=0):
    n["p"] += 1; L.append(f"C {{lab_pin.sym}} {x} {y} {rot} {flip} {{name=p{n['p']} sig_type=std_logic lab={net}}}")
def gnd(x, y):
    n["l"] += 1; L.append(f"C {{gnd.sym}} {x} {y} 0 0 {{name=l{n['l']+1} lab=GND}}")
def vsrc(x, y, name, val, net, cur="false"):
    L.append(f"C {{vsource.sym}} {x} {y} 0 0 {{name={name} value={val} savecurrent={cur}}}"); lab(x, y-30, net); gnd(x, y+30)
CAPS = [("12.5e-6", "C1"), ("12.5e-6", "C2"), ("25e-6", "C3"), ("50e-6", "C4"), ("50e-6", "C5")]
def cap(x, y, name, w, top, label=True):
    L.append(f"""C {{sg13cmos5l_pr/cap_cmomi.sym}} {x} {y} 0 0 {{name={name}
model=cap_cmomi
w={w}
l=25e-6
mmin=1
mmax=3
feed=double
subblock=0
m=1
mm_ok=1
spiceprefix=X
}}""")
    if label:
        lab(x, y-30, top, flip=1)
    gnd(x, y+30)

# ---- shared sources -------------------------------------------------------
vsrc(120, -1420, "VVDDA", r"\{VDDA\}", "VDDA", cur="true")
vsrc(240, -1420, "VB", r"\{VLEV\}", "vb")
for i in range(4):
    vsrc(360 + 120*i, -1420, f"VTRIM{i}", rf"\{{CE{i}*VDDA\}}", f"trim[{i}]")

# ---- three channels -------------------------------------------------------
for idx, (ch, Y) in enumerate((("trim", -1100), ("nmin", -750), ("nmax", -400))):
    sin, sout, iref, vin, shen = f"sh_in_{ch}", f"sh_out_{ch}", f"iref_{ch}", f"vin_{ch}", f"sh_en_{ch}"
    EN = f"EN_{ch.upper()}"
    lv = lambda x: rf"\{{VLO+{EN}*({x}-VLO)\}}"
    # per-channel stimulus: EN_<ch>=0 makes the channel static (constant input, SH_EN low)
    # long pwl/pulse values: stimulus sources in their own column above the channels
    vsrc(120, -2150 + 240*idx, f"VIN_{ch.upper()}", '"pwl(0 ' + " ".join([r"\{VLO\}", r"\{T0\}", r"\{VLO\}", r"\{T0+TINR\}", lv("VHI"), r"\{T0+TPER\}", lv("VHI"), r"\{T0+TPER+TINR\}", lv("VMID"), r"\{T0+2*TPER\}", lv("VMID"), r"\{T0+2*TPER+TINR\}", r"\{VLO\}"]) + ')"', vin)
    vsrc(120, -2030 + 240*idx, f"VSHEN_{ch.upper()}", '"pulse(' + rf"\{{VDDA*SHTRK*{EN}\}}" + r' 0 \{TTRK\} \{TEDGE\} \{TEDGE\} \{THLD\} \{TPER\})"', shen)
    L.append(f"T {{channel '{ch}'}} 600 {Y-190} 0 0 0.5 0.5 {{}}")
    # opamp bias + unity-gain buffer, identical in every channel
    L.append(f"C {{isource.sym}} 600 {Y-100} 0 0 {{name=IBIAS_{ch.upper()} value=\\{{IBIAS\\}}}}")
    lab(600, Y-130, "VDDA"); lab(600, Y-70, iref)
    L.append(f"C {{op_amp_ver_2.sym}} 760 {Y} 0 0 {{name=xbuf_{ch}}}")
    lab(770, Y-50, "VDDA", flip=1); lab(730, Y+70, iref); lab(690, Y-20, sin); lab(860, Y, sin, flip=1)
    lab(690, Y+20, vin); lab(770, Y+50, "GND", flip=1); lab(730, Y-70, "GND")
    if ch == "trim":
        L.append(f"C {{sample_and_hold_trim.sym}} 1060 {Y} 0 0 {{name=xsh_trim}}")
        lab(1140, Y-80, "VDDA", flip=1); lab(1010, Y-30, sin); lab(1210, Y-30, sout, flip=1)
        lab(1080, Y+50, shen); lab(1140, Y+50, "GND"); lab(1170, Y+50, "trim[3:0]", flip=1)
    else:
        # same main switch + SH_EN inverter as inside sample_and_hold_trim (asw_inv)
        L.append(f"C {{/home/benedikt/heichips26-FAIf/macros/heichips26_FAIf/macros/asw_inv/schematic/xschem/asw_inv.sym}} 1060 {Y} 0 0 {{name=xsw_{ch}}}")
        lab(990, Y, sin); lab(1130, Y, sout, flip=1); lab(1060, Y-50, shen)
        lab(1110, Y+50, "VDDA", flip=1); lab(1100, Y+50, "GND")
        caps = CAPS[:1] if ch == "nmin" else CAPS
        for j, (w, cname) in enumerate(caps):
            cap(1250 + 80*j, Y+40, f"{cname}_{ch.upper()}", w, sout, label=(j == 0))
        if len(caps) > 1:
            L.append(f"N 1250 {Y+10} {1250 + 80*(len(caps)-1)} {Y+10} {{lab={sout}}}")
    # comparator load, weak DC bias for the C(V) AC analysis, AC test current
    L.append(f"""C {{capa.sym}} 1700 {Y} 0 0 {{name=CLOAD_{ch.upper()}
m=1
value=\\{{CLOAD\\}}
footprint=1206
device="ceramic capacitor"}}""")
    lab(1700, Y-30, sout); gnd(1700, Y+30)
    L.append(f"N 1700 {Y-30} 1880 {Y-30} {{lab={sout}}}")
    L.append(f"""C {{res.sym}} 1790 {Y} 0 0 {{name=RB_{ch.upper()}
value=\\{{RBIAS\\}}
footprint=1206
device=resistor
m=1}}""")
    lab(1790, Y+30, "vb", flip=1)
    # rotated: the current flows from GND (bottom) into the hold node (top)
    L.append(f'C {{isource.sym}} 1880 {Y} 2 0 {{name=IAC_{ch.upper()} value="dc 0 ac 1"}}')
    gnd(1880, Y+30)

graph = lambda y1, y2, nodes, colors, ylo, yhi: f"""B 2 2000 {y1} 2900 {y2} {{flags=graph
y1={ylo}
y2={yhi}
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
color="{colors}"
node="{nodes}"
sim_type=tran
autoload=0}}"""

control = r"""
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
  set ext_txt = .txt
  set ext_cv = _chold.txt
  set ext_raw = .raw
  ** output names: <tb><pvt_tag>.<ext>, the tag only exists for PVT runs
  if $?pvt_tag
    set outtxt = \\"@schname\\\\$pvt_tag$ext_txt\\"
    set outcv = \\"@schname\\\\$pvt_tag$ext_cv\\"
    set outraw = \\"@schname\\\\$pvt_tag$ext_raw\\"
  else
    set outtxt = \\"@schname\\\\$ext_txt\\"
    set outcv = \\"@schname\\\\$ext_cv\\"
    set outraw = \\"@schname\\\\$ext_raw\\"
  end

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
      ** after reset only the netlist .save (i(vvdda)) is active: save the hold nodes explicitly
      save v(sh_out_trim) v(sh_out_nmin) v(sh_out_nmax)
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
"""

head = r"""v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
""" + graph(-1500, -1100, r"sh_out_trim\nsh_out_nmin\nsh_out_nmax\nvin_trim", "4 7 12 8", 0, 3.3).replace(r"\n", "\n") + "\n" + \
graph(-1080, -880, "sh_en_trim", "8", 0, 3.3) + "\n" + \
r"""T {Testbench: cost of the capacitor trim - trimmed S&H vs. the same S&H without trim switches} 80 -3300 0 0 0.8 0.8 {}
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
value=\"""" .replace('value=\\"', 'value="') + control.replace('"', '\\"').replace('\\\\\\"', '\\\\"') + r""""}
C {launcher.sym} 2060 -1560 0 0 {name=h1
descr="Simulate"
tclcommand="xschem save; xschem netlist; xschem simulate"
}
C {launcher.sym} 2060 -1510 0 0 {name=h2
descr="Load waves"
tclcommand="xschem raw_read $netlist_dir/[file rootname [file tail [xschem get current_name]]].raw tran"
}
"""
open(out, "w").write(head + "\n".join(L) + "\n")
print("written", out)
