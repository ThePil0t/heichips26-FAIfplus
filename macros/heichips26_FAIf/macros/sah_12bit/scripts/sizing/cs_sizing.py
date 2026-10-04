# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0
"""Hold-capacitor sizing of sah_12bit for 12-bit accuracy.

Reads the result tables of the sah_12bit testbenches, evaluates every error mechanism
against the 12-bit budget and plots the trade-offs.

Usage (inside nix-shell, from the macro folder):
    python3 scripts/sizing/cs_sizing.py [--data DIR] [--fig DIR]
  --data  folder with the result tables (default: testbenches/xschem/plot_simulations/data,
          the archived copies; testbenches/xschem/simulations holds the latest runs)
  --fig   output folder for the figures (default: testbenches/xschem/plot_simulations/figures)

Result tables (one per testbench, written by the NGSPICE block of the testbench):
  sah_12bit_ideal_tb_tran.txt     ideal source: pedestal, droop, feedthrough, acquisition, C_eff
  sah_12bit_ideal_tb_tran_v1.txt  same, first cell version (unbuffered gate drive), for comparison
  sah_12bit_ideal_tb_tran_pvt.txt same, nominal setup at the PVT points (droop vs temperature)
  sah_12bit_ideal_tb_dc.txt       switch on-resistance vs input level
  sah_12bit_ideal_tb_noise.txt    sampled noise with an ideal source (kT/C check)
  sah_12bit_opamp_tb_ac.txt       follower loop gain with the hold cap as load
  sah_12bit_opamp_tb_noise.txt    sampled noise with the follower as driver
  sah_12bit_opamp_tb_dc.txt       follower static error
  sah_12bit_opamp_tb_tran.txt     acquisition with the follower
  sah_12bit_opamp_tb_ped*.txt     pedestal vs input level with the follower (switch sizing)
  sah_12bit_kickback_tb_tran.txt  comparator kickback during a conversion
  sah_12bit_trim_tb_tran.txt      trimmed vs fixed hold cap
"""
import argparse
import glob
import math
import os

import numpy as np
import matplotlib

if not os.environ.get("SHOW_PLOTS"):
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
MACRO = os.path.normpath(os.path.join(HERE, "..", ".."))
PLOT = os.path.join(MACRO, "testbenches", "xschem", "plot_simulations")

# ----------------------------------------------------------------------------- 12-bit budget
KB = 1.380649e-23
VFS = 3.3                      # ADC full scale = DAC reference = VDDA
NBIT = 12
LSB = VFS / 2**NBIT            # 806 uV
QN = LSB / math.sqrt(12)       # quantization noise, 233 uV rms
SIG_KTC = QN / math.sqrt(2)    # kT/C gets half of the noise power, 165 uV rms
DET = LSB / 4                  # every deterministic error <= 1/4 LSB, 201 uV
N_TAU = math.log(4 * 2**NBIT)  # settling to 1/4 LSB of a full-scale step: 9.7 tau
# hold-cap spread: the cap_cmomi model has no process spread, so +-35 % is assumed as a lower bound.
# Accuracy limits must hold at C_nom*(1-CSPREAD), speed limits at C_nom*(1+CSPREAD); the parasitics
# CPAR (switch junctions, comparator gate, routing) do not spread.
CSPREAD = 0.35
CPAR = 0.05e-12
CW_NOM = 59.63                 # chosen hold cap: cap_cmomi 59.63 x 25.2 um (M1-M3)
CW_LO, CW_HI = 39.16, 80.1     # the same at -35 % / +35 % (whole 0.89 um rows)


def cmom(cw_um, cl_um=25.2, nlay=3):
    """cap_cmomi main capacitance (F), same equation as the PDK Verilog-A model."""
    dens = {2: 0.55, 3: 0.82, 4: 1.09}[nlay]
    ax = max(math.floor(cl_um / 0.84 + 1e-6), 1)
    ay = max(math.floor(cw_um / 0.89 + 1e-6) - 1, 1)
    return dens * ax * ay * 0.84 * 0.89 * 1e-15


def c_ktc(temp_c, sigma=SIG_KTC):
    return KB * (temp_c + 273.15) / sigma**2


def c_nom_required(c_eff_min):
    """drawn nominal C that still gives c_eff_min at -CSPREAD"""
    return max(c_eff_min - CPAR, 0) / (1 - CSPREAD)


# ----------------------------------------------------------------------------- table helpers
def load(path):
    """ngspice result table -> list of dicts (numbers converted where possible)."""
    if not os.path.exists(path):
        return []
    lines = [l.split() for l in open(path) if l.strip()]
    hdr = lines[0]
    out = []
    for r in lines[1:]:
        if len(r) != len(hdr) or r[0] == hdr[0]:
            continue
        d = {}
        for k, v in zip(hdr, r):
            try:
                d[k] = float(v)
            except ValueError:
                d[k] = v
        out.append(d)
    return out


def load_glob(folder, pattern):
    rows = []
    for f in sorted(glob.glob(os.path.join(folder, pattern))):
        rows += load(f)
    return rows


def nonlin(x, y, lo, hi):
    """best-fit line over [lo, hi]: (offset, gain, max |residual|)"""
    x, y = np.asarray(x), np.asarray(y)
    m = (x >= lo - 1e-9) & (x <= hi + 1e-9)
    if m.sum() < 3:
        return float("nan"), float("nan"), float("nan")
    b, a = np.polyfit(x[m], y[m], 1)
    return a, b, float(np.max(np.abs(y[m] - (a + b * x[m]))))


def group(rows, *keys):
    """rows grouped by the values of keys (scalar key for a single key)"""
    g = {}
    for r in rows:
        k = tuple(r[k] for k in keys)
        g.setdefault(k[0] if len(keys) == 1 else k, []).append(r)
    return g


def savefig(fig, name):
    os.makedirs(ARGS.fig, exist_ok=True)
    p = os.path.join(ARGS.fig, name)
    fig.tight_layout()
    fig.savefig(p, dpi=130)
    plt.close(fig)
    print("  figure:", os.path.relpath(p, MACRO))


def hline(ax, y, txt):
    ax.axhline(y, color="k", ls="--", lw=0.8)
    ax.text(ax.get_xlim()[0], y, " " + txt, va="bottom", fontsize=8)


# ----------------------------------------------------------------------------- sections
def budget():
    print("== 12-bit budget (FS = %.1f V)" % VFS)
    print(f"  LSB = {LSB*1e6:.1f} uV, quantization noise q = {QN*1e6:.1f} uV rms, 1/4 LSB = {DET*1e6:.1f} uV")
    print(f"  kT/C share sigma <= {SIG_KTC*1e6:.1f} uV -> C >= {c_ktc(27)*1e12:.3f} pF (27 C), {c_ktc(125)*1e12:.3f} pF (125 C)")
    print(f"  settling to 1/4 LSB of a full-scale step: {N_TAU:.2f} tau")
    print(f"  hold-cap spread +-{CSPREAD*100:.0f} % (assumed, no PDK spread), unscaled parasitics {CPAR*1e12:.2f} pF;"
          f" chosen C_nom = {cmom(CW_NOM)*1e12:.3f} pF ({CW_NOM} x 25.2 um) -> {cmom(CW_LO)*1e12:.3f} / {cmom(CW_HI)*1e12:.3f} pF at -/+35 %")


def ideal_ron(d):
    rows = load(os.path.join(d, "sah_12bit_ideal_tb_dc.txt"))
    if not rows:
        return
    print("== Switch on-resistance (ideal source, track)")
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for (run, wn, wp, ls, t, corner), rr in sorted(group(rows, "run", "wnf_um", "wpf_um", "lsw_um", "temp_C", "corner").items()):
        v = [r["vin_V"] for r in rr]
        ron = [r["ron_ohm"] for r in rr]
        if run in (1, 3) or (corner != "tt"):
            ax.plot(v, ron, label=f"{wn:g}/{wp:g}/{ls:g} um, {corner} {t:g} C")
        print(f"  WNF/WPF/L = {wn:g}/{wp:g}/{ls:g} um, {corner} {t:5g} C: Ron max {max(ron):7.0f} Ohm, Ron*W_N = {max(ron)*wn/1e3:5.2f} kOhm*um")
    ax.set_xlabel("V(SH_IN) [V]")
    ax.set_ylabel("Ron [Ohm]")
    ax.set_title("sah_12bit transmission gate on-resistance")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)
    savefig(fig, "sah12_1_ron.png")


def ideal_noise(d):
    rows = load(os.path.join(d, "sah_12bit_ideal_tb_noise.txt"))
    if not rows:
        return
    print("== Sampled noise, ideal source (kT/C check)")
    for r in rows:
        ktc = math.sqrt(KB * (r["temp_C"] + 273.15) / (r["ceff_pF"] * 1e-12)) * 1e6
        if isinstance(r.get("vn_uV"), float):
            print(f"  {r['temp_C']:5g} C  C_eff {r['ceff_pF']:.3f} pF  vin {r['vlev_V']:.2f} V: noise {r['vn_uV']:6.1f} uV, kT/C {ktc:6.1f} uV, ratio {r['vn_uV']/ktc:.3f}")


def pedestal_table(rows, label):
    """per setup: C_eff, pedestal NL (full range / buffer range), tau, settling"""
    res = []
    for run, rr in sorted(group(rows, "run").items()):
        x = [r["vlev_V"] for r in rr]
        y = [r["ped_mV"] for r in rr]
        o, g, nlf = nonlin(x, y, 0.1, 3.1)
        _, _, nlb = nonlin(x, y, 0.45, 3.1)
        r0 = rr[0]
        res.append(dict(run=run, cw=r0["cw_um"], msw=r0["msw"], wn=r0["wnf_um"], wp=r0["wpf_um"], ls=r0["lsw_um"],
                        kdn=r0.get("kdn", 0.5), kdp=r0.get("kdp", 0.5), tf=r0["tf_ns"],
                        ceff=np.mean([r["ceff_pF"] for r in rr]), nlf=nlf, nlb=nlb, off=o, gain=g,
                        tau=max(r["tau_ns"] for r in rr), tset=max(r["tset_q_ns"] for r in rr), x=x, y=y))
    print(f"== Pedestal with an ideal source ({label})")
    print("  run  C_eff  WNF/WPF  L    MSW KDN/KDP TF  | NL 0.1-3.1V  NL 0.45-3.1V [mV] | dV_NL*tau [ps*V] | tau / t_set(1/4 LSB) [ns]")
    for s in res:
        print(f"  {s['run']:3.0f} {s['ceff']:6.3f} {s['wn']:4g}/{s['wp']:<4g} {s['ls']:4g} {s['msw']:3g} {s['kdn']:.2f}/{s['kdp']:.2f} {s['tf']:3g} |"
              f" {s['nlf']:8.3f} {s['nlb']:10.3f}       | {s['nlf']*1e-3*s['tau']*1e-9*1e12:8.2f}         | {s['tau']:6.3f} / {s['tset']:6.2f}")
    return res


def ideal_pedestal(d):
    v2 = pedestal_table(load(os.path.join(d, "sah_12bit_ideal_tb_tran.txt")), "buffered gate drive")
    v1 = pedestal_table(load(os.path.join(d, "sah_12bit_ideal_tb_tran_v1.txt")), "v1: gate drive straight from SH_EN")
    if not v2:
        return
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    for s in v1:
        if s["run"] in (3,):
            axs[0].plot(s["x"], s["y"], "o--", ms=3, label=f"v1 {s['wn']:g}/{s['wp']:g} um, {s['ceff']:.2f} pF")
    for s in v2:
        if s["run"] in (1, 3, 5, 9, 13):
            axs[0].plot(s["x"], s["y"], "o-", ms=3, label=f"{s['wn']:g}/{s['wp']:g} um, {s['ceff']:.2f} pF")
    axs[0].set_xlabel("V_in [V]")
    axs[0].set_ylabel("pedestal [mV]")
    axs[0].set_title("Pedestal, ideal source")
    axs[0].grid(True, alpha=0.3)
    axs[0].legend(fontsize=7)
    # speed-accuracy: pedestal NL vs switch time constant. Same switch shape (WPF/WNF = 3.5, KD = 0.5, L = 0.6 um)
    # scaled in width or in C collapses onto one curve NL(tau); fit NL = k * tau^-n
    shape = [t for t in v2 if t["wp"] / t["wn"] == 3.5 and t["kdn"] == 0.5 and t["kdp"] == 0.5 and t["ls"] == 0.6 and t["tf"] == 1]
    lt = np.log([t["tau"] for t in shape])
    ln = np.log([t["nlf"] for t in shape])
    n_exp, lk = np.polyfit(lt, ln, 1)
    k = math.exp(lk)
    tau_min = (DET * 1e3 / k) ** (1 / n_exp)
    IDEAL["tau_min_ns"] = tau_min
    IDEAL["t_trk_ns"] = N_TAU * tau_min
    print(f"  fit (WPF/WNF = 3.5, KD = 0.5, L = 0.6 um): NL = {k:.3f} mV * (tau/ns)^{n_exp:.2f}")
    print(f"  -> 1/4 LSB needs tau >= {tau_min:.2f} ns, i.e. t_track >= {N_TAU*tau_min:.1f} ns for a full-scale step (ideal source)")
    for s_ in v2:
        axs[1].loglog(s_["tau"], s_["nlf"], "o")
        axs[1].annotate(f"{s_['wn']:g}/{s_['wp']:g},{s_['ceff']:.1f}p,m{s_['msw']:g}", (s_["tau"], s_["nlf"]), fontsize=6)
    t = np.logspace(-1, 1.5, 20)
    axs[1].loglog(t, k * t**n_exp, "k:", lw=0.8, label=f"fit NL = {k:.2f} mV (tau/ns)^{n_exp:.2f}")
    axs[1].axhline(DET * 1e3, color="k", ls="--", lw=0.8, label="1/4 LSB")
    axs[1].set_xlabel("switch time constant tau [ns]")
    axs[1].set_ylabel("pedestal NL 0.1-3.1 V [mV]")
    axs[1].set_title("Speed vs charge injection (ideal source)")
    axs[1].grid(True, which="both", alpha=0.3)
    axs[1].legend(fontsize=7)
    savefig(fig, "sah12_2_pedestal_ideal.png")


def opamp_pedestal(d):
    rows = load_glob(d, "sah_12bit_opamp_tb_ped*.txt")
    if not rows:
        return []
    print("== Pedestal with the op_amp_ver_2 follower as driver (switch sizing)")
    print("  corner T IBIAS  C        WNF/WPF  L    KDN/KDP | ped 0.45 / 1.65 / 3.2 V [mV] | NL 0.45-3.2V [mV] (budget %.3f)" % (DET * 1e3))
    res = []
    keys = ("cw_um", "wnf_um", "wpf_um", "lsw_um", "kdn", "kdp", "temp_C", "ibias", "corner")
    for k, rr in sorted(group(rows, *keys).items()):
        cw, wn, wp, ls, kdn, kdp, t, ib, corner = k
        x = [r["vlev_V"] for r in rr]
        y = [r["ped_mV"] for r in rr]
        o, g, nlb = nonlin(x, y, 0.45, 3.2)
        c = cmom(cw) * 1e12
        at = lambda v: ([b for a, b in zip(x, y) if abs(a - v) < 1e-6] or [float("nan")])[0]
        print(f"  {corner} {t:4g} {ib*1e9:4.0f}n {c:5.2f} pF  {wn:4g}/{wp:<4g} {ls:4g} {kdn:.2f}/{kdp:.2f} |"
              f" {at(0.45):6.3f} {at(1.65):6.3f} {at(3.2):6.3f} | {nlb:6.3f} {'ok' if nlb <= DET*1e3 else 'FAIL'}")
        res.append(dict(t=t, c=c, wn=wn, wp=wp, ls=ls, kdn=kdn, kdp=kdp, x=x, y=y, nl=nlb, corner=corner, ib=ib))
    # NL vs C for the selected switch shape (0.6 um NMOS, KD = 0.5, L = 0.45 um) at tt 27 C -> C limit
    sel = [r for r in res if r["wn"] == 0.6 and r["kdn"] == 0.5 and r["kdp"] == 0.5 and r["ls"] == 0.45
           and r["t"] == 27 and r["corner"] == "tt" and r["wp"] == 2.1]
    if len(sel) >= 3:
        n_exp, lk = np.polyfit(np.log([r["c"] for r in sel]), np.log([r["nl"] for r in sel]), 1)
        cmin = math.exp((math.log(DET * 1e3) - lk) / n_exp) * 1e-12
        print(f"  NL vs C (0.6/2.1 um, KD 0.5): NL = {math.exp(lk):.3f} mV * (C/pF)^{n_exp:.2f} -> 1/4 LSB at C = {cmin*1e12:.2f} pF")
        LIMITS["pedestal NL, follower (27 C, 0.6/2.1 um fit)"] = (cmin + CPAR, "fit over 0.5 ... 2 pF; 0.6/1.8 um is lower")
    worst = [r for r in res if r["c"] > 0.9 and r["c"] < 1.1 and r["wn"] == 0.6 and r["kdn"] == 0.5 and r["kdp"] == 0.5]
    for wp in sorted(set(r["wp"] for r in worst)):
        w = max((r for r in worst if r["wp"] == wp), key=lambda r: r["nl"])
        print(f"  worst over PVT, 1 pF, 0.6/{wp:g} um: NL {w['nl']:.3f} mV at {w['corner']} {w['t']:g} C")
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for s in res:
        if s["t"] == 27 and s["corner"] == "tt":
            ax.plot(s["x"], s["y"], "o-", ms=3, label=f"{s['wn']:g}/{s['wp']:g}/{s['ls']:g} um kd {s['kdn']:g}/{s['kdp']:g}, {s['c']:.2f} pF")
    ax.set_xlabel("V_in [V]")
    ax.set_ylabel("pedestal [mV]")
    ax.set_title("Pedestal with the op_amp_ver_2 follower")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=6)
    savefig(fig, "sah12_3_pedestal_opamp.png")
    return res


def opamp_ac(d):
    rows = load(os.path.join(d, "sah_12bit_opamp_tb_ac.txt"))
    if not rows:
        return
    print("== Follower loop gain with the hold cap as load (track)")
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    for (ib, vl), rr in sorted(group(rows, "ibias", "vlev_V").items()):
        rr = [r for r in rr if r["cw_um"] > 0]
        c = [cmom(r["cw_um"]) * 1e12 for r in rr]
        axs[0].semilogx(c, [r["pm_deg"] for r in rr], "o-", ms=3, label=f"{ib*1e9:g} nA, {vl:g} V")
        axs[1].semilogx(c, [r["ugf_Hz"] / 1e6 for r in rr], "o-", ms=3, label=f"{ib*1e9:g} nA, {vl:g} V")
        worst = min(rr, key=lambda r: r["pm_deg"])
        print(f"  IBIAS {ib*1e9:4g} nA, VIN {vl:4g} V: UGF {min(r['ugf_Hz'] for r in rr)/1e3:6.0f}-{max(r['ugf_Hz'] for r in rr)/1e3:6.0f} kHz,"
              f" A0 {rr[0]['a0_dB']:5.1f} dB, PM {max(r['pm_deg'] for r in rr):4.1f} deg (0.25 pF) .. {worst['pm_deg']:4.1f} deg ({cmom(worst['cw_um'])*1e12:.1f} pF)")
    axs[0].set_xlabel("hold cap [pF]")
    axs[0].set_ylabel("phase margin [deg]")
    axs[0].grid(True, which="both", alpha=0.3)
    axs[0].legend(fontsize=6)
    axs[1].set_xlabel("hold cap [pF]")
    axs[1].set_ylabel("unity-gain frequency [MHz]")
    axs[1].grid(True, which="both", alpha=0.3)
    savefig(fig, "sah12_4_opamp_loopgain.png")


def opamp_noise(d):
    rows = load(os.path.join(d, "sah_12bit_opamp_tb_noise.txt"))
    if not rows:
        return
    print("== Sampled noise with the follower (track, 1 Hz ... 1 GHz)")
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for (t, ib), rr in sorted(group(rows, "temp_C", "ibias").items()):
        c = [cmom(r["cw_um"]) * 1e12 for r in rr]
        ax.semilogx(c, [r["vn_1Hz_uV"] for r in rr], "o-", ms=3, label=f"follower + switch, {ib*1e9:g} nA, {t:g} C")
        for r, cc in zip(rr, c):
            ktc = math.sqrt(KB * (t + 273.15) / (cc * 1e-12)) * 1e6
            tot = math.sqrt(r["vn_1Hz_uV"]**2 + (QN * 1e6)**2)
            print(f"  {t:4g} C {ib*1e9:4g} nA {cc:5.2f} pF: {r['vn_1Hz_uV']:6.1f} uV (from 1 kHz {r['vn_1kHz_uV']:6.1f}), kT/C alone {ktc:5.1f} uV"
                  f" -> with quantization {tot:6.1f} uV = {20*math.log10(tot/(QN*1e6)):.2f} dB SNR loss")
    # smallest simulated C for which follower + switch noise stays below the quantization noise at the hottest corner
    hot = max(r["temp_C"] for r in rows)
    pts = sorted((cmom(r["cw_um"]), r["vn_1Hz_uV"]) for r in rows if r["temp_C"] == hot and r["ibias"] == 25e-9)
    cmin = None
    for (c1, v1), (c2, v2) in zip(pts, pts[1:]):
        if v1 > QN * 1e6 >= v2:   # log-log interpolation of the crossing
            cmin = math.exp(math.log(c1) + (math.log(QN * 1e6) - math.log(v1)) * (math.log(c2) - math.log(c1)) / (math.log(v2) - math.log(v1)))
    if pts and pts[0][1] <= QN * 1e6:
        cmin = pts[0][0]
    if cmin:
        LIMITS["noise (follower + kT/C <= q, %g C, 25 nA)" % hot] = (cmin + CPAR, "follower noise dominates; kT/C alone needs %.2f pF" % (c_ktc(hot) * 1e12))
    cc = np.logspace(-1, 1, 30)
    ax.semilogx(cc, np.sqrt(KB * 300 / (cc * 1e-12)) * 1e6, "k:", label="kT/C (27 C)")
    ax.axhline(QN * 1e6, color="k", ls="--", lw=0.8, label="quantization noise (12 bit)")
    ax.axhline(SIG_KTC * 1e6, color="gray", ls="--", lw=0.8, label="kT/C share of the budget")
    ax.set_xlabel("hold cap [pF]")
    ax.set_ylabel("sampled noise [uV rms]")
    ax.set_title("Noise frozen on the hold cap")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=6)
    savefig(fig, "sah12_5_noise.png")


def opamp_dc(d):
    rows = load(os.path.join(d, "sah_12bit_opamp_tb_dc.txt"))
    if not rows:
        return
    print("== Follower static error through the closed switch")
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for (t, ib), rr in sorted(group(rows, "temp_C", "ibias").items()):
        x = [r["vin_V"] for r in rr]
        y = [r["err_mV"] for r in rr]
        o, g, nl = nonlin(x, y, 0.5, 3.1)
        ax.plot(x, y, label=f"{ib*1e9:g} nA, {t:g} C")
        print(f"  {t:5g} C {ib*1e9:4g} nA: offset {o:6.3f} mV, gain error {g*1e3:6.1f} ppm, NL 0.5-3.1 V {nl*1e3:5.1f} uV")
    ax.set_ylim(-1, 3)
    ax.set_xlabel("V_in [V]")
    ax.set_ylabel("V(sh_out) - V_in [mV]")
    ax.set_title("Follower + switch static error (track)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)
    savefig(fig, "sah12_6_follower_dc.png")


def opamp_tran(d):
    rows = load(os.path.join(d, "sah_12bit_opamp_tb_tran.txt"))
    if not rows:
        return
    print("== Acquisition with the follower (cap recharged from the previous sample)")
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for (ib, v1, v2), rr in sorted(group(rows, "ibias", "vlev_V", "vfar_V").items()):
        c = [cmom(r["cw_um"]) * 1e12 for r in rr]
        ax.plot(c, [r["tset_q_us"] for r in rr], "o-", ms=3, label=f"{ib*1e9:g} nA, {v1:g} -> {v2:g} V")
        for r, cc in zip(rr, c):
            ACQ[(ib, r["cw_um"])] = max(ACQ.get((ib, r["cw_um"]), 0), r["tset_q_us"])
            print(f"  {ib*1e9:4g} nA {cc:5.2f} pF {v1:4g}->{v2:<4g} V: t_acq(1/4 LSB) {r['tset_q_us']:6.3f} us, (1/2 LSB) {r['tset_h_us']:6.3f} us,"
                  f" static error {r['err_final_mV']:6.3f} mV, pedestal {r['ped_mV']:6.3f} / {r['ped2_mV']:6.3f} mV")
    ax.set_xlabel("hold cap [pF]")
    ax.set_ylabel("t_acq to 1/4 LSB [us]")
    ax.set_title("Acquisition time with op_amp_ver_2")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=6)
    savefig(fig, "sah12_7_acquisition_opamp.png")


def droop(d):
    rows = load_glob(d, "sah_12bit_ideal_tb_tran_pvt*.txt")
    if not rows:
        return
    print("== Droop / hold-node leakage vs PVT (ideal source, GLEAK artifact not in the model)")
    print("  corner T  | worst |droop| at VIN = VLEV [mV/ms] -> I_leak [pA] -> max t_hold for 1/4 LSB [us]")
    out = []
    # input levels above VDDA - 0.1 V forward-bias the PMOS junctions (not a valid operating point)
    rows = [r for r in rows if r["vlev_V"] <= r["vdd_V"] - 0.1 + 1e-9]
    for (corner, t, vdd), rr in sorted(group(rows, "corner", "temp_C", "vdd_V").items()):
        dr = max(abs(r["droop_mV_per_ms"]) for r in rr)
        dr2 = max(abs(r["droop2_mV_per_ms"]) for r in rr)
        c = np.mean([r["ceff_pF"] for r in rr])
        il = max(dr, dr2) * c   # mV/ms * pF = pA
        th = DET * 1e3 / max(dr, dr2, 1e-9) * 1e3   # us
        out.append((corner, t, vdd, dr, dr2, il, th))
        print(f"  {corner} {t:4g} C {vdd:4g} V | {dr:8.3f} (VIN = VFAR: {dr2:8.3f}) mV/ms at {c:.2f} pF -> {il:7.2f} pA -> t_hold <= {th:9.1f} us"
              f" -> SAR clock >= {13/th:6.2f} MHz (13 hold cycles)")
    w = min(out, key=lambda o: o[6])
    HOLD["t_hold_max_us"] = w[6]
    HOLD["where"] = f"{w[0]} {w[1]:g} C, C_eff {np.mean([r['ceff_pF'] for r in rows]):.2f} pF (-35 %)"
    for tmax in sorted(set(o[1] for o in out)):
        ww = min((o for o in out if o[1] == tmax), key=lambda o: o[6])
        HOLD.setdefault("by_temp", {})[tmax] = (ww[6], ww[0], ww[2])
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for corner in sorted(set(o[0] for o in out)):
        oo = sorted((o for o in out if o[0] == corner), key=lambda o: o[1])
        ax.semilogy([o[1] for o in oo], [max(o[5], 1e-3) for o in oo], "o-", label=corner)
    ax.set_xlabel("temperature [C]")
    ax.set_ylabel("hold-node leakage [pA]")
    ax.set_title("sah_12bit hold-node leakage (frozen switch, C -35 %)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7)
    savefig(fig, "sah12_9_leakage.png")
    return out


def kickback(d):
    rows = load(os.path.join(d, "sah_12bit_kickback_tb_tran.txt"))
    if not rows:
        return
    print("== Comparator kickback onto the held voltage (12 decisions)")
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for cw, rr in sorted(group(rows, "cw_um").items()):
        c = cmom(cw) * 1e12
        km = max(abs(r["kick_max_uV"]) for r in rr)
        kl = max(abs(r["kick_last_uV"]) for r in rr)
        print(f"  {c:5.2f} pF: max |kick| over the decisions {km:7.1f} uV, at the LSB decision {kl:7.1f} uV (budget {DET*1e6:.0f} uV)")
        ax.plot(c, km, "o", color="C0")
        ax.plot(c, kl, "s", color="C1")
    q = max(max(abs(r["kick_max_uV"]) for r in rr) * 1e-6 * (cmom(cw) + CPAR) for cw, rr in group(rows, "cw_um").items())
    LIMITS["kickback"] = (q / DET, f"worst kicked charge {q*1e15:.3f} fC (all levels, previous DAC level 0.1/same/3.2 V)")
    g = group(rows, "cw_um")
    for cw, tag in ((CW_LO, "-35 %"), (CW_NOM, "nominal"), (CW_HI, "+35 %")):
        if cw in g:
            km = max(abs(r["kick_max_uV"]) for r in g[cw])
            KICK[tag] = km
            print(f"  chosen C at {tag}: {cmom(cw)*1e12:.2f} pF -> max kick {km:.0f} uV = {km/(DET*1e6)*100:.0f} % of 1/4 LSB")
    for cw, ls in ((CW_LO, ":"), (CW_NOM, "-"), (CW_HI, ":")):
        ax.axvline(cmom(cw) * 1e12, color="gray", ls=ls, lw=0.8)
    ax.plot([], [], "o", color="C0", label="max over the 12 decisions")
    ax.plot([], [], "s", color="C1", label="at the LSB decision")
    ax.axhline(DET * 1e6, color="k", ls="--", lw=0.8, label="1/4 LSB")
    ax.set_xlabel("hold cap [pF]")
    ax.set_ylabel("kickback error [uV]")
    ax.set_title("555_comparator kickback")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)
    savefig(fig, "sah12_8_kickback.png")


def trim(d):
    rows = load(os.path.join(d, "sah_12bit_trim_tb_tran.txt"))
    if not rows:
        return
    print("== Trim array vs fixed hold cap of the same value (F = fixed, T = trimmed)")
    print("  T    code C_tot  | pedestal F/T @0.5,2.8,1.65 V [mV] | |droop| max F/T [mV/ms] | t_acq max F/T [us]")
    for (t, code), rr in sorted(group(rows, "temp_C", "code").items()):
        f = [r for r in rr if r["out"] == "f"]
        tt = [r for r in rr if r["out"] == "t"]
        pf = " ".join(f"{r['ped_mV']:6.3f}" for r in f[:3])
        pt = " ".join(f"{r['ped_mV']:6.3f}" for r in tt[:3])
        df = max(abs(r["droop_mV_per_ms"]) for r in f)
        dt = max(abs(r["droop_mV_per_ms"]) for r in tt)
        af = max(r["tacq_us"] for r in f)
        at = max(r["tacq_us"] for r in tt)
        print(f"  {t:4g} {code:4g} {rr[0]['ctrim_pF']:5.2f} | {pf} / {pt} | {df:7.3f} / {dt:7.3f} | {af:6.3f} / {at:6.3f}")
        TRIM.setdefault(t, []).append(dict(code=code, c=rr[0]["ctrim_pF"], leak_ratio=dt / max(df, 1e-9),
                                           dped=max(abs(a["ped_mV"] - b["ped_mV"]) for a, b in zip(f, tt)), dacq=at - af))
    for t, lst in sorted(TRIM.items()):
        print(f"  {t:4g} C: trimmed/fixed leakage x{min(l['leak_ratio'] for l in lst):.1f} ... x{max(l['leak_ratio'] for l in lst):.1f},"
              f" pedestal shift up to {max(l['dped'] for l in lst):.3f} mV, acquisition {min(l['dacq'] for l in lst)*1e3:+.0f} ... {max(l['dacq'] for l in lst)*1e3:+.0f} ns")


IDEAL = {}


LIMITS = {}
TRIM = {}
ACQ = {}
HOLD = {}
KICK = {}
FINAL = {}


def final_check(d):
    rows = load_glob(d, "sah_12bit_final_tb_tran_pvt*.txt")
    if not rows:
        return
    print("== Final check: sah_12bit (frozen sizes), op_amp_ver_2 (25 nA), 555_comparator, PDK cap model, PVT x cap spread")
    print("  (droop: measured with the PDK model, which adds a 1 TOhm GLEAK from SH_OUT to ground; 'real' = GLEAK removed)")
    print("  corner  C [pF]  T    VDDA | pedestal NL (8 lv) | |droop| real [mV/ms] -> t_hold(1/4 LSB) | SR [V/us] | t_acq 0.5-3.2 V [us] | static err [mV]")
    pts = []
    for (corner, cw, t, vdd), rr in sorted(group(rows, "corner", "cw_um", "temp_C", "vdd_V").items()):
        x = [r["vlev_V"] for r in rr] + [r["vfar_V"] for r in rr]
        y = [r["ped_mV"] for r in rr] + [r["ped2_mV"] for r in rr]
        o, g, nl = nonlin(x, y, 0.4, 3.25)
        ce = cmom(cw) + CPAR
        # GLEAK current V/1T pulls the held level (VLEV) down: remove it from the measured slope
        dr = max(abs(r["droop_mV_per_ms"] + r["vlev_V"] * 1e-12 / ce) for r in rr)
        th = DET * 1e3 / max(dr, 1e-9) * 1e3
        # slew rate from the large steps only; settling inside 0.5 ... 3.2 V and separately for the step that ends
        # at 0.45 V, right above the follower output floor (~0.39 V)
        sr = min(r["sr_V_per_us"] for r in rr if abs(r["vfar_V"] - r["vlev_V"]) >= 1)
        ta = max(r["tset_q_us"] for r in rr if min(r["vlev_V"], r["vfar_V"]) >= 0.5)
        ta_floor = max([r["tset_q_us"] for r in rr if min(r["vlev_V"], r["vfar_V"]) < 0.5] or [float("nan")])
        ef = [r["err_final_mV"] for r in rr]
        pts.append(dict(corner=corner, c=cmom(cw) * 1e12, t=t, vdd=vdd, nl=nl, th=th, sr=sr, ta=ta, taf=ta_floor))
        print(f"  {corner:3s} {cmom(cw)*1e12:6.3f} {t:5g} {vdd:5g} | {nl*1e3:6.1f} uV {'ok' if nl <= DET*1e3 else 'FAIL'}"
              f"   | {dr:8.3f} -> {th:9.1f} us | {sr:5.3f} | {ta:6.3f} ({ta_floor:6.2f} to 0.45 V) | {min(ef):6.3f} .. {max(ef):6.3f}")
    w_nl = max(pts, key=lambda p: p["nl"])
    w_ta = max(pts, key=lambda p: p["ta"])
    w_th = min(pts, key=lambda p: p["th"])
    w_sr = min(pts, key=lambda p: p["sr"])
    w_tf = max(pts, key=lambda p: p["taf"])
    FINAL.update(nl=w_nl, ta=w_ta, th=w_th, sr=w_sr, taf=w_tf)
    print(f"  worst: pedestal NL {w_nl['nl']*1e3:.1f} uV ({w_nl['corner']} {w_nl['c']:.2f} pF {w_nl['t']:g} C, budget {DET*1e6:.0f} uV),"
          f" t_acq {w_ta['ta']:.2f} us ({w_ta['corner']} {w_ta['c']:.2f} pF {w_ta['t']:g} C),"
          f" t_hold <= {w_th['th']:.0f} us ({w_th['corner']} {w_th['c']:.2f} pF {w_th['t']:g} C), SR >= {w_sr['sr']:.3f} V/us")
    print(f"  steps ending at 0.45 V (follower near its output floor): t_acq up to {w_tf['taf']:.1f} us ({w_tf['corner']} {w_tf['c']:.2f} pF {w_tf['t']:g} C)")
    a_fs = (3.2 - 0.5) / 2
    print(f"  input bandwidth: full-scale sine (0.5 ... 3.2 V) <= SR/(2 pi A) = {w_sr['sr']*1e6/(2*math.pi*a_fs)/1e3:.0f} kHz")
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    lab = [f"{p['corner']} {p['c']:.2f}p {p['t']:g}C" for p in pts]
    axs[0].bar(range(len(pts)), [p["nl"] * 1e3 for p in pts])
    axs[0].axhline(DET * 1e6, color="k", ls="--", lw=0.8, label="1/4 LSB")
    axs[0].set_ylabel("pedestal NL [uV]")
    axs[1].bar(range(len(pts)), [p["ta"] for p in pts], color="C1")
    axs[1].set_ylabel("t_acq to 1/4 LSB, steps in 0.5-3.2 V [us]")
    for ax in axs:
        ax.set_xticks(range(len(pts)))
        ax.set_xticklabels(lab, rotation=60, ha="right", fontsize=7)
        ax.grid(True, axis="y", alpha=0.3)
    axs[0].legend(fontsize=7)
    axs[0].set_title("Final check: pedestal nonlinearity")
    axs[1].set_title("Final check: acquisition (follower, 25 nA)")
    savefig(fig, "sah12_10_final_check.png")


def summary():
    print("== Hold capacitance per mechanism (12 bit), with the +-35 % cap spread")
    LIMITS.setdefault("kT/C share of the noise budget (125 C)", (c_ktc(125), "sigma_kTC <= q/sqrt(2)"))
    c_lo = cmom(CW_LO) + CPAR
    print(f"  {'mechanism':48s} C_eff,min   C_nom,req   margin at -35 % ({c_lo*1e12:.2f} pF eff.)")
    for k, (c, note) in sorted(LIMITS.items(), key=lambda kv: -kv[1][0]):
        print(f"  {k:48s} {c*1e12:6.3f} pF   {c_nom_required(c)*1e12:6.3f} pF   x{c_lo/c:5.2f}   ({note})")
    print(f"  chosen C_nom = {cmom(CW_NOM)*1e12:.3f} pF drawn ({CW_NOM} x 25.2 um, {CW_NOM*25.2:.0f} um2)")
    if "-35 %" in KICK:
        print(f"  kickback simulated at -35 %: {KICK['-35 %']:.0f} uV (budget {DET*1e6:.0f} uV)")
    for ib in sorted(set(k[0] for k in ACQ)):
        if (ib, CW_HI) in ACQ:
            print(f"  speed at +35 % ({cmom(CW_HI)*1e12:.2f} pF), follower {ib*1e9:g} nA: t_acq(1/4 LSB) <= {ACQ[(ib, CW_HI)]:.2f} us"
                  f" (nominal {ACQ.get((ib, CW_NOM), float('nan')):.2f} us)")
    if HOLD:
        print(f"  droop (C -35 %): t_hold for 1/4 LSB; a 12-bit conversion holds 13 SAR clocks")
        for tmax, (th, corner, vdd) in sorted(HOLD["by_temp"].items()):
            print(f"    up to {tmax:4g} C: t_hold <= {th:8.1f} us (worst {corner} {vdd:g} V) -> SAR clock >= {13/th:6.2f} MHz")
    if IDEAL:
        print(f"  ideal source: switch tau >= {IDEAL['tau_min_ns']:.2f} ns (charge-injection NL), t_track >= {IDEAL['t_trk_ns']:.1f} ns")


def main():
    budget()
    d = ARGS.data
    print("data:", os.path.relpath(d, MACRO))
    ideal_ron(d)
    ideal_noise(d)
    ideal_pedestal(d)
    opamp_ac(d)
    opamp_noise(d)
    opamp_dc(d)
    opamp_tran(d)
    opamp_pedestal(d)
    droop(d)
    kickback(d)
    trim(d)
    final_check(d)
    summary()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(PLOT, "data"))
    ap.add_argument("--fig", default=os.path.join(PLOT, "figures"))
    ARGS = ap.parse_args()
    main()
