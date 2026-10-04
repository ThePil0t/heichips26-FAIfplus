# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0
"""Plot the sample_and_hold_trim testbench results (ngspice raw files in ../simulations).

Usage: python3 plot_sample_and_hold_trim.py [tran] [pvt] [vs_notrim]
  tran       nominal sample_and_hold_trim_tb_tran         -> figures/sh_trim_tran_<n>_*.png
  pvt        nominal + all sample_and_hold_trim_tb_tran_<pvt tag>.raw overlaid
                                                            -> figures/sh_trim_tran_pvt_<n>_*.png
  vs_notrim  sample_and_hold_trim_tb_vs_notrim (trim vs. no-trim channels)
                                                            -> figures/sh_trim_vs_notrim_<n>_*.png
Without arguments the 'pvt' and 'vs_notrim' sets are plotted (if their raw files exist).
SHOW_PLOTS=1 additionally opens the figures.
"""
import glob
import os
import re
import sys

import numpy as np
import matplotlib

if not os.environ.get("SHOW_PLOTS"):
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, "..", "simulations")
FIG = os.path.join(HERE, "figures")
SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "meg": 1e6, "g": 1e9}


def read_raw(fn):
    """Return [(plotname, {vector: array})] for every plot in an ngspice binary raw file."""
    data = open(fn, "rb").read()
    plots, pos = [], 0
    while pos < len(data):
        hdr, names = {}, []
        while True:
            end = data.index(b"\n", pos)
            line = data[pos:end].decode(errors="replace")
            pos = end + 1
            if line.startswith("Variables:"):
                for _ in range(int(hdr["No. Variables"])):
                    end = data.index(b"\n", pos)
                    names.append(data[pos:end].decode().split()[1].lower())
                    pos = end + 1
                continue
            if line.startswith("Binary:"):
                break
            if ":" in line:
                k, v = line.split(":", 1)
                hdr[k.strip()] = v.strip()
        nv, npnt = int(hdr["No. Variables"]), int(hdr["No. Points"])
        dt = np.complex128 if "complex" in hdr.get("Flags", "") else np.float64
        arr = np.frombuffer(data, dtype=dt, count=nv * npnt, offset=pos).reshape(npnt, nv)
        pos += nv * npnt * np.dtype(dt).itemsize
        plots.append((hdr.get("Plotname", ""), {nm: np.real(arr[:, i]) for i, nm in enumerate(names)}))
        while pos < len(data) and data[pos:pos + 1] in (b"\n", b" "):
            pos += 1
    return [d for name, d in plots if name.lower().startswith("transient")]


def si(value):
    m = re.fullmatch(r"([-+0-9.eE]+)(meg|[fpnumkg])?", value.strip().lower())
    return float(m.group(1)) * SI.get(m.group(2), 1.0)


def timing(netlist):
    """Read the stimulus timing parameters from the generated netlist."""
    txt = open(netlist).read()
    p = {k: si(re.search(rf"^\.param {k}=(\S+)", txt, re.M | re.I).group(1)) for k in ("TTRK", "THLD", "TEDGE")}
    p["TPER"] = p["TTRK"] + p["THLD"] + 2 * p["TEDGE"]
    p["VDDA"] = si(re.search(r"^\.param VDDA=(\S+)", txt, re.M | re.I).group(1))
    return p


def windows(p):
    th = [p["TTRK"] + k * p["TPER"] for k in range(4)]                      # hold edges
    return dict(th=th,
                tstep=[t + p["TEDGE"] + p["THLD"] / 2 for t in th[:3]],      # input steps (mid-hold)
                ttrk=[t + p["TEDGE"] + p["THLD"] for t in th[:3]])           # track starts after hold k


LEV = ["0.5 V", "2.8 V", "1.65 V", "0.5 V"]


def win(t, a, b):
    return (t >= a) & (t <= b)


def plot_set(runs, labels, sig, p, prefix, title_of_col, colors=None):
    """Four figures (overview, pedestal, droop/feedthrough, acquisition).
    runs[row][curve] -> vector dict; sig[row][curve] -> (vin, sh_in, sh_out) names; one subplot row per row."""
    w = windows(p)
    lsb = p["VDDA"] / 256
    rows = len(runs)
    os.makedirs(FIG, exist_ok=True)
    kw = dict(dpi=90)

    fig, axs = plt.subplots(rows, 1, figsize=(15, 3.5 * rows), squeeze=False)
    for r in range(rows):
        ax = axs[r][0]
        for c, d in enumerate(runs[r]):
            if d is None:
                continue
            t = d["time"] * 1e6
            ax.plot(t, d[sig[r][c][2]], color=None if colors is None else colors[c], label=f"sh_out {labels[r][c]}")
        c0, d0 = next((c, d) for c, d in enumerate(runs[r]) if d is not None)
        ax.plot(d0["time"] * 1e6, d0[sig[r][c0][0]], "k:", lw=1, label="vin")
        ax.set_title(f"Overview, {title_of_col[r]}")
        ax.set_ylabel("V")
        ax.set_xlabel("time [us]")
        ax.grid(alpha=.3)
        ax.legend(fontsize=7, ncol=3)
    fig.tight_layout()
    fig.savefig(f"{FIG}/{prefix}_1_overview.png", **kw)

    fig, axs = plt.subplots(rows, 4, figsize=(18, 3.6 * rows), squeeze=False)
    for r in range(rows):
        for k in range(4):
            ax = axs[r][k]
            for c, d in enumerate(runs[r]):
                if d is None:
                    continue
                t, v = d["time"], d[sig[r][c][2]]
                m = win(t, w["th"][k] - 0.1e-6, w["th"][k] + 0.4e-6)
                ref = np.interp(w["th"][k] - 10e-9, t, v)
                ax.plot((t[m] - w["th"][k]) * 1e9, (v[m] - ref) * 1e3, label=labels[r][c])
            ax.axvline(100, ls=":", c="gray")
            ax.axhspan(-lsb / 2e-3, lsb / 2e-3, color="g", alpha=.08)
            ax.set_title(f"Pedestal, hold {k}, vin={LEV[k]}\n{title_of_col[r]}", fontsize=9)
            ax.set_xlabel("time after hold edge [ns]")
            ax.set_ylabel("sh_out - v(before) [mV]")
            ax.grid(alpha=.3)
        axs[r][0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(f"{FIG}/{prefix}_2_pedestal.png", **kw)

    fig, axs = plt.subplots(rows, 4, figsize=(18, 3.6 * rows), squeeze=False)
    for r in range(rows):
        for k in range(4):
            ax = axs[r][k]
            for c, d in enumerate(runs[r]):
                if d is None:
                    continue
                t, v = d["time"], d[sig[r][c][2]]
                a = w["th"][k] + p["TEDGE"] + 100e-9
                m = win(t, a, w["th"][k] + p["TEDGE"] + p["THLD"] - 10e-9)
                ax.plot((t[m] - w["th"][k]) * 1e6, (v[m] - np.interp(a, t, v)) * 1e3, label=labels[r][c])
            if k < 3:
                ax.axvline((w["tstep"][k] - w["th"][k]) * 1e6, ls=":", c="r")
            ax.set_title(f"Droop/feedthrough, hold {k}, vin={LEV[k]}\n{title_of_col[r]}", fontsize=9)
            ax.set_xlabel("time after hold edge [us]")
            ax.set_ylabel("sh_out - v(100 ns) [mV]")
            ax.grid(alpha=.3)
        axs[r][0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(f"{FIG}/{prefix}_3_droop_feedthrough.png", **kw)

    fig, axs = plt.subplots(rows, 3, figsize=(16, 3.6 * rows), squeeze=False)
    for r in range(rows):
        for k in range(3):
            ax = axs[r][k]
            for c, d in enumerate(runs[r]):
                if d is None:
                    continue
                t, v = d["time"], d[sig[r][c][2]]
                m = win(t, w["ttrk"][k] - 20e-9, w["ttrk"][k] + 0.6e-6)
                vfin = np.interp(w["th"][k] + p["TPER"] - 10e-9, t, v)
                ax.plot((t[m] - w["ttrk"][k]) * 1e9, (v[m] - vfin) * 1e3, label=labels[r][c])
            ax.axhspan(-lsb / 2e-3, lsb / 2e-3, color="g", alpha=.15)
            ax.set_ylim(-20, 20)
            ax.set_title(f"Acquisition after hold {k}: {LEV[k]} -> {LEV[k + 1]}\n{title_of_col[r]}", fontsize=9)
            ax.set_xlabel("time after SH_EN rises [ns]")
            ax.set_ylabel("sh_out - final [mV] (green: +-1/2 LSB)")
            ax.grid(alpha=.3)
        axs[r][0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(f"{FIG}/{prefix}_4_acquisition.png", **kw)
    print(f"saved {FIG}/{prefix}_[1-4]_*.png")


def tran():
    tb = "sample_and_hold_trim_tb_tran"
    runs = read_raw(f"{SIM}/{tb}.raw")
    p = timing(f"{SIM}/{tb}.spice")
    s = ("v(vin)", "v(sh_in)", "v(sh_out)")
    plot_set([runs], [["cap_en=0", "cap_en=15"]], [[s, s]], p, "sh_trim_tran", ["nominal (tt, 27 C, 3.3 V)"])


def pvt():
    tb = "sample_and_hold_trim_tb_tran"
    files = [(f"{SIM}/{tb}.raw", "tt 27C 3.3V")]
    for f in sorted(glob.glob(f"{SIM}/{tb}_*.raw")):
        tag = os.path.basename(f)[len(tb) + 1:-4]
        corner, temp, vdd = tag.split("_")
        files.append((f, f"{corner} {temp.replace('m', '-')} {vdd.replace('p', '.')}"))
    if len(files) < 2:
        print("pvt: no PVT raw files found, run 'make sim-xschem-pvt' first")
        return
    data = [read_raw(f) for f, _ in files]
    p = timing(f"{SIM}/{tb}.spice")
    s = ("v(vin)", "v(sh_in)", "v(sh_out)")
    runs = [[d[i] if len(d) > i else None for d in data] for i in (0, 1)]
    labels = [[lbl for _, lbl in files]] * 2
    plot_set(runs, labels, [[s] * len(files)] * 2, p, "sh_trim_tran_pvt", ["cap_en=0", "cap_en=15"])


def vs_notrim():
    tb = "sample_and_hold_trim_tb_vs_notrim"
    if not os.path.exists(f"{SIM}/{tb}.raw"):
        print("vs_notrim: no raw file found, run 'make sim-xschem TB=sample_and_hold_trim_tb_vs_notrim' first")
        return
    # one active channel per transient run: trim(code 0), nmin, trim(code 15), nmax
    by = {"trim": [], "nmin": [], "nmax": []}
    for d in read_raw(f"{SIM}/{tb}.raw"):
        by[next(ch for ch in by if f"v(sh_out_{ch})" in d)].append(d)
    p = timing(f"{SIM}/{tb}.spice")
    sig = lambda ch: (f"v(vin_{ch})", f"v(sh_in_{ch})", f"v(sh_out_{ch})")
    plot_set([[by["trim"][0], by["nmin"][0]], [by["trim"][1], by["nmax"][0]]],
             [["trim cap_en=0", "no trim, C1 only (nmin)"], ["trim cap_en=15", "no trim, C1..C5 (nmax)"]],
             [[sig("trim"), sig("nmin")], [sig("trim"), sig("nmax")]], p, "sh_trim_vs_notrim",
             ["minimum capacitance", "maximum capacitance"])
    # effective hold capacitance vs. hold voltage
    rows = [l.split() for l in open(f"{SIM}/{tb}_chold.txt").read().splitlines()[1:]]
    fig, axs = plt.subplots(1, 2, figsize=(12, 4))
    for ax, code, ref in ((axs[0], "0", "nmin"), (axs[1], "15", "nmax")):
        for ch, lbl in (("trim", f"trim cap_en={code}"), (ref, f"no trim ({ref})")):
            pts = [(float(r[5]), float(r[6])) for r in rows if r[3] == code and r[4] == ch]
            ax.plot(*zip(*pts), "o-", label=lbl)
        ax.set_xlabel("hold voltage [V]")
        ax.set_ylabel("effective hold capacitance [pF]")
        ax.grid(alpha=.3)
        ax.legend()
    axs[0].set_title("Minimum capacitance")
    axs[1].set_title("Maximum capacitance")
    fig.tight_layout()
    fig.savefig(f"{FIG}/sh_trim_vs_notrim_5_chold.png", dpi=90)
    print(f"saved {FIG}/sh_trim_vs_notrim_5_chold.png")


if __name__ == "__main__":
    todo = sys.argv[1:] or ["pvt", "vs_notrim"]
    for name in todo:
        {"tran": tran, "pvt": pvt, "vs_notrim": vs_notrim}[name]()
    if os.environ.get("SHOW_PLOTS"):
        plt.show()
