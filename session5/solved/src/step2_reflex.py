"""
step2_reflex.py — ② 3뉴런 반사궁: 흥분과 억제의 부호

뉴런 4개(0 = V 시각, 1 = I 억제, 2 = G 거대섬유, 3 = J 점프 운동)를
V→G (syn 50, +1), I→G (syn 150, −1), G→J (syn 250, +1) 로 잇는다.
"억제 꺼짐": V 만 150 Hz 포아송 500 ms.  "억제 켜짐": V 와 I 를 함께 150 Hz 포아송 500 ms.
두 조건 모두 시드 0. 시냅스 지연 1.8 ms(18 스텝) 큐는 lif.simulate 가 처리한다.

산출물: outputs/02_reflex.png, outputs/02_summary.json
실행:   python src/step2_reflex.py
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lif
lif.setup_matplotlib()
import matplotlib.pyplot as plt

NAMES = ["V", "I", "G", "J"]
V, I, G, J = 0, 1, 2, 3
SIM_MS = 500.0
# (pre, post, syn, sign)
CONNECTIONS = [(V, G, 50, +1), (I, G, 150, -1), (G, J, 250, +1)]


def main():
    t0 = time.perf_counter()
    os.makedirs(lif.OUT_DIR, exist_ok=True)

    pre, post, syn, sign = (np.array(c) for c in zip(*CONNECTIONS))
    W = lif.build_weight_matrix(pre, post, syn, sign, n=4)
    print("가중치(mV):", {f"{NAMES[p]}→{NAMES[q]}": float(W[p, q]) for p, q, _, _ in CONNECTIONS})

    conds = {"off": [V], "on": [V, I]}
    results = {}
    for name, stim in conds.items():
        res = lif.simulate(W, 4, SIM_MS, stim_idx=stim, seed=lif.SEED)
        results[name] = res
        print(f"억제 {'켜짐' if name == 'on' else '꺼짐'}: " +
              ", ".join(f"{NAMES[k]}={int(res['counts'][k])}" for k in range(4)))

    spikes = {name: {NAMES[k]: int(results[name]["counts"][k]) for k in range(4)} for name in conds}
    j_off, j_on = spikes["off"]["J"], spikes["on"]["J"]
    ratio = (j_on / j_off) if j_off > 0 else None

    # 래스터: 두 조건 × 4 뉴런 × 500 ms
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    titles = {"off": "억제 꺼짐 (V 만 자극)", "on": "억제 켜짐 (V + I 자극)"}
    colors = {"V": "C0", "I": "C3", "G": "C2", "J": "C1"}
    for ax, name in zip(axes, conds):
        res = results[name]
        for k in range(4):
            ts = res["spike_times_ms"][res["spike_ids"] == k]
            ax.vlines(ts, k - 0.4, k + 0.4, color=colors[NAMES[k]], lw=1.0)
        ax.set_yticks(range(4))
        ax.set_yticklabels([f"{NAMES[k]} ({spikes[name][NAMES[k]]}개)" for k in range(4)])
        ax.set_ylim(-0.7, 3.7)
        ax.invert_yaxis()
        ax.set_title(titles[name], fontsize=10)
        ax.set_xlim(0, SIM_MS)
    axes[-1].set_xlabel("t (ms)")
    fig.suptitle("② 3뉴런 반사궁 래스터 — V→G 흥분, I→G 억제, G→J 흥분 (지연 1.8 ms)")
    fig.tight_layout()
    fig.savefig(os.path.join(lif.OUT_DIR, "02_reflex.png"), dpi=100)
    plt.close(fig)

    summary = dict(
        stage=2, sim_ms=int(SIM_MS), seed=lif.SEED, stim_rate_hz=lif.R_STIM,
        connections=[dict(pre=NAMES[p], post=NAMES[q], syn=int(s), sign=int(g), w_mV=float(lif.W_UNIT * s * g))
                     for p, q, s, g in CONNECTIONS],
        spikes=spikes, ratio_J_on_over_off=ratio,
        wall_seconds=time.perf_counter() - t0,
    )
    with open(os.path.join(lif.OUT_DIR, "02_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"J(on)/J(off) = {j_on}/{j_off} = {ratio}, wall {summary['wall_seconds']:.2f} s")


if __name__ == "__main__":
    main()
