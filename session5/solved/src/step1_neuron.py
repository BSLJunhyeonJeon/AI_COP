"""
step1_neuron.py — ① 뉴런 1개: LIF 가 어떻게 발화하는가

상수 입력 I_ext = 0, 5, 7, 8, 10, 15, 20, 30 mV 각각에 대해 1000 ms 를 돌려 스파이크 수와 발화율을 재고
해석해와 나란히 CSV 로 저장한다. I_ext = 0, 10, 30 의 v(t) 처음 200 ms 를 그림으로 저장한다.

산출물: outputs/01_trace.png, outputs/01_fi_curve.csv, outputs/01_summary.json
실행:   python src/step1_neuron.py
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lif
lif.setup_matplotlib()
import matplotlib.pyplot as plt

I_EXT_LIST = [0, 5, 7, 8, 10, 15, 20, 30]     # mV
SIM_MS = 1000.0
TRACE_I = [0, 10, 30]
TRACE_MS = 200.0


def main():
    t0 = time.perf_counter()
    os.makedirs(lif.OUT_DIR, exist_ok=True)

    rows, traces = [], {}
    for I in I_EXT_LIST:
        res = lif.simulate(None, 1, SIM_MS, I_ext=float(I), record_v_idx=[0] if I in TRACE_I else None)
        n_spk = int(res["counts"][0])
        rate = n_spk / (SIM_MS / 1000.0)
        rows.append(dict(I_ext_mV=I, n_spikes=n_spk, rate_hz=rate, rate_analytic_hz=lif.analytic_rate_hz(I)))
        if I in TRACE_I:
            traces[I] = (res["t_ms"], res["v_trace"][:, 0], res["spike_times_ms"])
        print(f"I_ext = {I:>2} mV: 스파이크 {n_spk:>3}개, 발화율 {rate:6.1f} Hz (해석해 {rows[-1]['rate_analytic_hz']:6.1f} Hz)")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(lif.OUT_DIR, "01_fi_curve.csv"), index=False)

    # v(t) 그림: I_ext = 0, 10, 30 의 처음 200 ms
    fig, axes = plt.subplots(len(TRACE_I), 1, figsize=(9, 7), sharex=True)
    n_show = int(TRACE_MS / lif.DT)
    for ax, I in zip(axes, TRACE_I):
        t, v, spk = traces[I]
        ax.plot(t[:n_show], v[:n_show], lw=1.0, color="C0")
        spk = spk[spk < TRACE_MS]
        ax.vlines(spk, lif.V_TH, lif.V_TH + 15, color="C3", lw=1.0, label=f"스파이크 {len(spk)}개 / {TRACE_MS:.0f} ms")
        ax.axhline(lif.V_TH, color="gray", ls="--", lw=0.8, label="v_th = -45 mV")
        ax.axhline(lif.V_REST, color="gray", ls=":", lw=0.8, label="v_rest = -52 mV")
        ax.set_ylabel("v (mV)")
        ax.set_title(f"I_ext = {I} mV  (측정 {df.loc[df.I_ext_mV == I, 'rate_hz'].iloc[0]:.1f} Hz, "
                     f"해석해 {df.loc[df.I_ext_mV == I, 'rate_analytic_hz'].iloc[0]:.1f} Hz)", fontsize=10)
        ax.legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("t (ms)")
    fig.suptitle("① LIF 뉴런 1개 — 막전위 v(t), 처음 200 ms")
    fig.tight_layout()
    fig.savefig(os.path.join(lif.OUT_DIR, "01_trace.png"), dpi=100)
    plt.close(fig)

    summary = dict(
        stage=1, dt_ms=lif.DT, sim_ms=int(SIM_MS),
        I_ext_mV=I_EXT_LIST, rate_hz=[float(r) for r in df["rate_hz"]],
        rate_analytic_hz=[float(r) for r in df["rate_analytic_hz"]],
        wall_seconds=time.perf_counter() - t0,
    )
    with open(os.path.join(lif.OUT_DIR, "01_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"완료: wall {summary['wall_seconds']:.2f} s")


if __name__ == "__main__":
    main()
