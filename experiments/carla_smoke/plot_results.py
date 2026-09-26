#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def read_frames(path):
    with path.open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.asarray([float(r[k]) if r[k] else np.nan for r in rows]) for k in rows[0]}


def main():
    p = argparse.ArgumentParser(); p.add_argument("root", type=Path); a = p.parse_args()
    names = ["single60", "three60", "obstacle40", "stability600"]
    labels = ["1 view / 60 s", "3 views / 60 s", "Obstacle / 40 s", "3 views / 600 s"]
    summaries = [json.loads((a.root / n / "summary.json").read_text()) for n in names]
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10, "axes.spines.top":False, "axes.spines.right":False})
    fig, axes = plt.subplots(1,2,figsize=(11,4.2),layout="constrained")
    x = np.arange(4)
    axes[0].bar(x-.16,[s['loop_ms']['p95'] for s in summaries],width=.32,label="P95",color="#3274a1")
    axes[0].bar(x+.16,[s['loop_ms']['p99'] for s in summaries],width=.32,label="P99",color="#e1812c")
    axes[0].axhline(50,color="#b53e3e",ls="--",label="50 ms cycle budget")
    axes[0].set_xticks(x,labels,rotation=15,ha="right"); axes[0].set_ylabel("Active loop time (ms)");axes[0].legend(fontsize=8)
    axes[0].set_title("Control + RPC + aligned sensor processing")
    axes[1].bar(x,[s['rtf'] for s in summaries],color="#439775")
    axes[1].set_xticks(x,labels,rotation=15,ha="right");axes[1].set_ylabel("Simulation time / wall-clock time")
    axes[1].set_ylim(0,1.1);axes[1].axhline(1,color="gray",ls="--");axes[1].set_title("20 Hz wall-clock pacing")
    for i,s in enumerate(summaries):axes[1].text(i,s['rtf']+.025,"%.4f"%s['rtf'],ha="center",fontsize=9)
    fig.suptitle("CARLA 0.9.15 on sheng: infrastructure smoke test",fontsize=13)
    fig.savefig(a.root/'performance.png',dpi=180);fig.savefig(a.root/'performance.pdf');plt.close(fig)
    d=read_frames(a.root/'obstacle40'/'frames.csv')
    fig,axes=plt.subplots(3,1,figsize=(9,7),sharex=True,layout="constrained")
    axes[0].plot(d['sim_seconds'],d['speed_mps'],color="#3274a1");axes[0].set_ylabel("Speed (m/s)")
    axes[1].plot(d['sim_seconds'],d['range_m'],color="#439775");axes[1].set_ylabel("LiDAR front range (m)");axes[1].set_ylim(0,52)
    axes[2].plot(d['sim_seconds'],d['brake'],label="Brake",color="#b53e3e");axes[2].plot(d['sim_seconds'],d['throttle'],label="Throttle",color="#e1812c")
    axes[2].set_ylabel("Control command");axes[2].set_xlabel("Simulation time (s)");axes[2].legend()
    for ax in axes:ax.axvline(20,color="gray",ls="--");ax.axvspan(0,20,color="gray",alpha=.07)
    axes[0].set_title("Sensor feedback: approach, brake, stop, resume after obstacle removal")
    axes[0].text(20.3,axes[0].get_ylim()[1]*.86,"Obstacle removed",fontsize=9)
    fig.savefig(a.root/'obstacle_response.png',dpi=180);fig.savefig(a.root/'obstacle_response.pdf');plt.close(fig)


if __name__ == '__main__':main()
