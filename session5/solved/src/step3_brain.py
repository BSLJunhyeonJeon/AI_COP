"""
step3_brain.py — ③ 전뇌 장착: 같은 식, 138,639개 뉴런

data/connections.parquet 로 희소 가중치 행렬 W 를 만들고(MODEL_SPEC §3),
(a) LPLC2_L ∪ LPLC2_R 을 150 Hz 포아송으로 1000 ms 자극, (b) 무자극 1000 ms 를 돌린다(둘 다 시드 0).
모든 뉴런의 스파이크 수를 세고 GF_L, GF_R 의 발화율을 기록한다.

산출물: outputs/03_raster.png, outputs/03_rates.csv, outputs/03_summary.json
중간 결과: outputs/03_spikes_{stim,ctrl}.npz (있으면 그 조건은 다시 돌리지 않고 이어서 간다)
실행:   python src/step3_brain.py
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

SIM_MS = 1000.0
STIM_GROUPS = ["LPLC2_L", "LPLC2_R"]
N_STIM_SHOW, N_TOP_SHOW = 20, 20


def run_condition(name, W, stim_idx, log):
    """조건 하나를 돌리거나, 저장된 중간 결과가 있으면 그것을 읽는다."""
    cache = os.path.join(lif.OUT_DIR, f"03_spikes_{name}.npz")
    if os.path.isfile(cache):
        z = np.load(cache)
        log(f"[{name}] 저장된 결과 사용: {cache}")
        return dict(spike_steps=z["spike_steps"], spike_ids=z["spike_ids"], counts=z["counts"],
                    wall_seconds=float(z["wall_seconds"]))
    log(f"[{name}] 시뮬레이션 시작: {SIM_MS:.0f} ms, 자극 뉴런 {0 if stim_idx is None else len(stim_idx)}개")
    res = lif.simulate(W, lif.N_NEURONS, SIM_MS, stim_idx=stim_idx, stim_rate_hz=lif.R_STIM, seed=lif.SEED,
                       progress_every=1000, log=log)
    np.savez(cache, spike_steps=res["spike_steps"], spike_ids=res["spike_ids"], counts=res["counts"],
             wall_seconds=res["wall_seconds"])
    log(f"[{name}] 끝: 총 스파이크 {int(res['counts'].sum())}, 발화 뉴런 {int((res['counts'] > 0).sum())}, "
        f"wall {res['wall_seconds']:.1f} s")
    return res


def main():
    t0 = time.perf_counter()
    os.makedirs(lif.OUT_DIR, exist_ok=True)
    log = lambda s: print(s, flush=True)

    groups = lif.load_groups()
    stim_idx = np.array(sorted(set(groups[STIM_GROUPS[0]]) | set(groups[STIM_GROUPS[1]])), dtype=np.int64)
    gf = {"GF_L": int(groups["GF_L"][0]), "GF_R": int(groups["GF_R"][0])}

    log("가중치 행렬 조립 중 ...")
    W, n_conn = lif.load_brain()
    log(f"W: {W.shape}, 연결 {n_conn}개, nnz {W.nnz}, 조립 {time.perf_counter() - t0:.1f} s")

    res_stim = run_condition("stim", W, stim_idx, log)
    res_ctrl = run_condition("ctrl", W, None, log)
    sec = SIM_MS / 1000.0
    rate_stim = res_stim["counts"] / sec
    rate_ctrl = res_ctrl["counts"] / sec

    # ---- 03_rates.csv: (a)에서 발화한 뉴런 전부 + groups.json 의 모든 뉴런 ----
    group_of = {}
    for gname, members in groups.items():
        for i in members:
            group_of.setdefault(int(i), []).append(gname)
    rows_idx = np.array(sorted(set(np.flatnonzero(res_stim["counts"] > 0).tolist()) | set(group_of)), dtype=np.int64)
    df = pd.DataFrame(dict(
        index=rows_idx,
        group=[";".join(group_of.get(int(i), [])) for i in rows_idx],
        rate_stim_hz=rate_stim[rows_idx],
        rate_ctrl_hz=rate_ctrl[rows_idx],
    ))
    df.to_csv(os.path.join(lif.OUT_DIR, "03_rates.csv"), index=False)

    # ---- 03_raster.png: 자극 뉴런 20개, GF_L·GF_R, 그 외 발화율 상위 20개 ----
    stim_set = set(stim_idx.tolist())
    order = np.argsort(-rate_stim, kind="stable")
    others = [int(i) for i in order if int(i) not in stim_set and int(i) not in gf.values() and rate_stim[i] > 0][:N_TOP_SHOW]
    rows = ([("LPLC2", int(i)) for i in stim_idx[:N_STIM_SHOW]] +
            [("GF_L", gf["GF_L"]), ("GF_R", gf["GF_R"])] +
            [("기타", i) for i in others])
    st, si = res_stim["spike_steps"] * lif.DT, res_stim["spike_ids"]
    fig, ax = plt.subplots(figsize=(12, 8))
    labels = []
    for r, (kind, i) in enumerate(rows):
        ts = st[si == i]
        is_gf = kind.startswith("GF")
        ax.vlines(ts, r - 0.45, r + 0.45, color="C3" if is_gf else ("C0" if kind == "LPLC2" else "C2"),
                  lw=1.6 if is_gf else 0.6)
        lab = f"{kind} #{i} ({rate_stim[i]:.0f} Hz)"
        labels.append(lab)
        if is_gf:
            ax.axhspan(r - 0.5, r + 0.5, color="C3", alpha=0.12)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels, fontsize=7)
    for tl, (kind, _) in zip(ax.get_yticklabels(), rows):
        if kind.startswith("GF"):
            tl.set_color("C3"); tl.set_fontweight("bold")
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.invert_yaxis()
    ax.set_xlim(0, SIM_MS)
    ax.set_xlabel("t (ms)")
    ax.set_title(f"③ 전뇌 래스터 (LPLC2 {len(stim_idx)}개 150 Hz 자극, {SIM_MS:.0f} ms) — "
                 f"GF_L {rate_stim[gf['GF_L']]:.0f} Hz, GF_R {rate_stim[gf['GF_R']]:.0f} Hz, "
                 f"발화 뉴런 {int((res_stim['counts'] > 0).sum())}개", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(lif.OUT_DIR, "03_raster.png"), dpi=100)
    plt.close(fig)

    # ---- 03_summary.json ----
    first_gf = st[np.isin(si, list(gf.values()))]
    summary = dict(
        stage=3, sim_ms=int(SIM_MS), seed=lif.SEED,
        stim_groups=STIM_GROUPS, stim_rate_hz=int(lif.R_STIM), n_stim_neurons=int(len(stim_idx)),
        gf={k: dict(stim_hz=float(rate_stim[i]), ctrl_hz=float(rate_ctrl[i])) for k, i in gf.items()},
        gf_first_spike_ms=(float(first_gf.min()) if first_gf.size else None),
        n_active_stim=int((res_stim["counts"] > 0).sum()),
        n_active_ctrl=int((res_ctrl["counts"] > 0).sum()),
        n_spikes_stim=int(res_stim["counts"].sum()),
        n_spikes_ctrl=int(res_ctrl["counts"].sum()),
        lplc2_mean_rate_hz=float(rate_stim[stim_idx].mean()),
        n_neurons=int(lif.N_NEURONS), n_connections=int(n_conn),
        sim_wall_seconds=dict(stim=res_stim["wall_seconds"], ctrl=res_ctrl["wall_seconds"]),
        wall_seconds=time.perf_counter() - t0,
    )
    with open(os.path.join(lif.OUT_DIR, "03_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    log(json.dumps({k: summary[k] for k in ("gf", "gf_first_spike_ms", "n_active_stim", "n_active_ctrl",
                                              "n_spikes_stim", "lplc2_mean_rate_hz", "wall_seconds")},
                   ensure_ascii=False))


if __name__ == "__main__":
    main()
