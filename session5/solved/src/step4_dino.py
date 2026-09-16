"""
step4_dino.py — ④ 공룡 게임: 반사로 점프하기 (MODEL_SPEC §4)

에피소드 = (속도 단계 k = 1..5, 선인장 j = 1..3), 시드 = 1000·k + j. 뇌는 휴지 상태에서 시작한다.
선인장은 t = 0 에 거리 d0 = d_on + 100 ms × v_k 에서 나타나 d(t) = d0 − v_k·t 로 접근한다.
각크기 θ(t) = 2·atan(h / (2·d(t))) ≥ θ_on 인 동안 LPLC2_L ∪ LPLC2_R 을 150 Hz 포아송으로 자극한다.
GF_L 또는 GF_R 의 첫 스파이크 t_s 로 점프 [t_s + t_motor, t_s + t_motor + T_jump] 를 정하고,
선인장이 x = 0 에 닿는 t_c = d0 / v_k 에 공중이면 통과, 아니면 충돌(no_jump / too_early / too_late).

산출물: outputs/04_dino.gif, outputs/04_speed_vs_pass.png, outputs/04_log.csv, outputs/04_summary.json
중간 결과: outputs/04_episodes/ep_k{k}_j{j}.npz — 에피소드가 하나 끝날 때마다 저장하고 04_log.csv 에 이어 쓴다.
          다시 실행하면 이미 있는 에피소드는 건너뛴다(끊겨도 이어서 간다).
실행:   python src/step4_dino.py
"""
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lif
lif.setup_matplotlib()
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
from matplotlib.patches import Rectangle

# ---------------- §4 상수 (고정) ----------------
H = 10.0                       # 선인장 높이(단위)
THETA_ON_DEG = 20.0            # looming 뉴런이 켜지는 각크기(도)
D_ON = H / (2.0 * math.tan(math.radians(THETA_ON_DEG) / 2.0))   # ≈ 28.36
SPEEDS = [0.05, 0.1, 0.25, 0.6, 2.0]    # v_k, 단위/ms, k = 1..5
K, M = 5, 3
BASE_LEVEL = 3
T_MOTOR = 10.0                 # ms, GF 스파이크 → 점프 시작
T_JUMP = 300.0                 # ms, 공중 체류
T_APPEAR = 100.0               # ms, d0 = d_on + 100 ms × v
T_EXTRA = 50.0                 # ms, 에피소드는 t_c + 50 ms 까지
STIM_HZ = lif.R_STIM
STIM_GROUPS = ["LPLC2_L", "LPLC2_R"]
GIF_EPISODES = [(BASE_LEVEL, 1), (K, 1)]
GIF_FRAME_MS, GIF_FPS = 10.0, 10

LOG_COLS = ["episode_id", "speed_level", "v_units_per_ms", "d0", "t_theta_on_ms", "t_gf_first_ms", "latency_ms",
            "t_collision_ms", "jumped", "passed", "fail_reason"]
EP_DIR = os.path.join(lif.OUT_DIR, "04_episodes")
LOG_PATH = os.path.join(lif.OUT_DIR, "04_log.csv")


def ep_id(k, j):
    return f"k{k}_j{j}"


def theta_deg(d):
    """각크기 θ = 2·atan(h/(2d)) (도). 선인장이 x = 0 에 닿은 뒤(d ≤ 0)는 접촉 상태로 보고 180°."""
    d = np.asarray(d, dtype=np.float64)
    out = np.full(d.shape, 180.0)
    pos = d > 0
    out[pos] = np.degrees(2.0 * np.arctan(H / (2.0 * d[pos])))
    return out


def judge(t_gf_first, t_c):
    """(jumped, passed, fail_reason, t_air0, t_air1)"""
    if t_gf_first is None:
        return 0, 0, "no_jump", None, None
    t_air0, t_air1 = t_gf_first + T_MOTOR, t_gf_first + T_MOTOR + T_JUMP
    if t_c < t_air0:
        return 1, 0, "too_late", t_air0, t_air1
    if t_c > t_air1:
        return 1, 0, "too_early", t_air0, t_air1
    return 1, 1, "", t_air0, t_air1


def nan_or(x):
    return np.nan if x is None else x


def run_episode(k, j, W, stim_idx, gf_ids, log):
    """에피소드 하나를 시뮬레이션하고 상세 dict 를 돌려준다. 저장본(npz)이 있으면 그것을 읽는다."""
    path = os.path.join(EP_DIR, f"ep_{ep_id(k, j)}.npz")
    if os.path.isfile(path):
        z = np.load(path, allow_pickle=False)
        detail = {key: (z[key].item() if z[key].ndim == 0 else z[key]) for key in z.files}
        log(f"[{ep_id(k, j)}] 저장된 결과 사용")
        return detail

    t0 = time.perf_counter()
    v = SPEEDS[k - 1]
    d0 = D_ON + T_APPEAR * v
    t_c = d0 / v
    sim_ms = t_c + T_EXTRA
    n_steps = int(round(sim_ms / lif.DT))
    t_ms = np.arange(n_steps) * lif.DT
    theta = theta_deg(d0 - v * t_ms)
    stim_on = theta >= THETA_ON_DEG
    t_theta_on = float(t_ms[np.argmax(stim_on)]) if stim_on.any() else None

    res = lif.simulate(W, lif.N_NEURONS, sim_ms, stim_idx=stim_idx, stim_on=stim_on, stim_rate_hz=STIM_HZ,
                       seed=1000 * k + j)
    gf_times = np.sort(res["spike_times_ms"][np.isin(res["spike_ids"], gf_ids)])
    t_gf_first = float(gf_times[0]) if gf_times.size else None
    jumped, passed, reason, t_air0, t_air1 = judge(t_gf_first, t_c)

    detail = dict(
        episode_id=ep_id(k, j), speed_level=k, cactus=j, seed=1000 * k + j, v=v, d0=d0, t_c=t_c, sim_ms=sim_ms,
        t_theta_on=nan_or(t_theta_on), t_gf_first=nan_or(t_gf_first),
        t_air0=nan_or(t_air0), t_air1=nan_or(t_air1),
        jumped=jumped, passed=passed, fail_reason=reason,
        gf_times=gf_times, n_spikes=int(res["counts"].sum()), n_active=int((res["counts"] > 0).sum()),
        wall_seconds=time.perf_counter() - t0,
    )
    os.makedirs(EP_DIR, exist_ok=True)
    np.savez(path, **detail)
    row = detail_to_row(detail)
    # 04_log.csv 에 이어 쓴다 (헤더는 파일이 없을 때만) — 끊겨도 진행 상황이 남는다
    pd.DataFrame([row], columns=LOG_COLS).to_csv(LOG_PATH, mode="a", header=not os.path.isfile(LOG_PATH), index=False)
    log(f"[{ep_id(k, j)}] v={v} d0={d0:.2f} t_c={t_c:.1f} ms, θ_on {row['t_theta_on_ms']} ms, "
        f"GF 첫 스파이크 {row['t_gf_first_ms']} ms → {'통과' if passed else '충돌 ' + reason}, "
        f"스파이크 {detail['n_spikes']}개, wall {detail['wall_seconds']:.1f} s")
    return detail


def detail_to_row(dd):
    t_on, t_gf = float(dd["t_theta_on"]), float(dd["t_gf_first"])
    return dict(
        episode_id=str(dd["episode_id"]), speed_level=int(dd["speed_level"]), v_units_per_ms=float(dd["v"]),
        d0=float(dd["d0"]), t_theta_on_ms=(None if math.isnan(t_on) else t_on),
        t_gf_first_ms=(None if math.isnan(t_gf) else t_gf),
        latency_ms=(None if (math.isnan(t_gf) or math.isnan(t_on)) else t_gf - t_on),
        t_collision_ms=float(dd["t_c"]), jumped=int(dd["jumped"]), passed=int(dd["passed"]),
        fail_reason=str(dd["fail_reason"]),
    )


def make_gif(details, path, log):
    """기본 속도·최고 속도 에피소드(j = 1)를 이어 붙인 GIF. 게임 시간 10 ms 마다 1 프레임, 10 fps."""
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    writer = PillowWriter(fps=GIF_FPS)
    n_frames = 0
    with writer.saving(fig, path, dpi=100):
        for dd in details:
            v, d0, t_c, sim_ms = float(dd["v"]), float(dd["d0"]), float(dd["t_c"]), float(dd["sim_ms"])
            k = int(dd["speed_level"])
            gf_times = np.asarray(dd["gf_times"], dtype=np.float64)
            t_air0, t_air1 = float(dd["t_air0"]), float(dd["t_air1"])
            passed, reason = int(dd["passed"]), str(dd["fail_reason"])
            x_max = d0 + 10.0
            for t in np.arange(0.0, sim_ms + 1e-9, GIF_FRAME_MS):
                ax.clear()
                d = d0 - v * t
                th = float(theta_deg(d))
                in_air = (not math.isnan(t_air0)) and (t_air0 <= t <= t_air1)
                s = (t - t_air0) / T_JUMP if in_air else 0.0
                y_dino = 25.0 * 4.0 * s * (1.0 - s) if in_air else 0.0
                n_gf = int((gf_times <= t).sum())
                gf_now = bool(((gf_times <= t) & (gf_times > t - GIF_FRAME_MS)).any())
                stim = th >= THETA_ON_DEG
                # 지면
                ax.axhline(0, color="k", lw=2)
                ax.axvline(0, color="gray", lw=0.6, ls=":")
                # 공룡(사각형, 공중이면 위로)
                ax.add_patch(Rectangle((-6, y_dino), 6, 10, color="C1" if gf_now else "C2"))
                ax.text(-3, y_dino + 11, "초파리", ha="center", fontsize=8)
                # 선인장(사각형, 위치 d(t) 에 따라 왼쪽으로 이동). 충돌이면 x = 0 에 멈춘 채 빨갛게 표시
                collided = t >= t_c and not passed
                ax.add_patch(Rectangle((max(d, 0.0) if collided else d, 0), 3, H, color="C3" if collided else "C0"))
                # 텍스트: 에피소드·t·θ·GF 스파이크·결과
                status = (f"에피소드 {dd['episode_id']}  (속도 단계 k={k}, v={v} 단위/ms, 시드 {int(dd['seed'])})\n"
                          f"t = {t:6.1f} ms   d = {max(d, 0):6.1f}   θ = {min(th, 180):6.1f}°   "
                          f"{'LPLC2 자극 ON' if stim else 'LPLC2 자극 off'}\n"
                          f"GF 스파이크 누적 {n_gf}개" + ("   ★ GF 발화!" if gf_now else "") +
                          (f"   점프 [{t_air0:.0f}, {t_air1:.0f}] ms" if not math.isnan(t_air0) else "   점프 없음"))
                if t >= t_c:
                    status += "\n결과: " + ("통과 (PASS)" if passed else f"충돌 (FAIL: {reason})")
                elif in_air:
                    status += "\n공중"
                ax.text(0.01, 0.98, status, transform=ax.transAxes, va="top", ha="left", fontsize=9,
                        bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9))
                ax.text(0.99, 0.02, f"충돌 시각 t_c = {t_c:.1f} ms", transform=ax.transAxes, va="bottom", ha="right",
                        fontsize=8, color="0.4")
                ax.set_xlim(-20, x_max)
                ax.set_ylim(-5, 45)
                ax.set_xlabel("거리 x (단위)")
                ax.set_yticks([])
                ax.set_title("④ 공룡 게임 — looming → LPLC2 → GF → 점프 (10배 슬로모션)", fontsize=10)
                writer.grab_frame()
                n_frames += 1
    plt.close(fig)
    log(f"GIF 저장: {path} ({n_frames} 프레임, {GIF_FPS} fps)")
    return n_frames


def main():
    t0 = time.perf_counter()
    os.makedirs(lif.OUT_DIR, exist_ok=True)
    log = lambda s: print(s, flush=True)

    groups = lif.load_groups()
    stim_idx = np.array(sorted(set(groups[STIM_GROUPS[0]]) | set(groups[STIM_GROUPS[1]])), dtype=np.int64)
    gf_ids = np.array([groups["GF_L"][0], groups["GF_R"][0]], dtype=np.int64)

    log("가중치 행렬 조립 중 ...")
    W, n_conn = lif.load_brain()
    log(f"W: {W.shape}, 연결 {n_conn}개")

    details = {}
    for k in range(1, K + 1):
        for j in range(1, M + 1):
            details[(k, j)] = run_episode(k, j, W, stim_idx, gf_ids, log)
    # 04_log.csv 는 마지막에 npz 전체로부터 다시 써서 항상 15행·정렬 상태로 맞춘다
    rows = [detail_to_row(details[(k, j)]) for k in range(1, K + 1) for j in range(1, M + 1)]
    df = pd.DataFrame(rows, columns=LOG_COLS)
    df.to_csv(LOG_PATH, index=False)

    # ---- 속도별 통과율 ----
    levels = []
    for k in range(1, K + 1):
        sub = df[df.speed_level == k]
        lat = pd.to_numeric(sub.latency_ms, errors="coerce").dropna()
        levels.append(dict(speed_level=k, v=SPEEDS[k - 1], n=int(len(sub)), passed=int(sub.passed.sum()),
                           pass_rate=float(sub.passed.mean()),
                           fail_reasons=sub.fail_reason.replace("", "pass").value_counts().to_dict(),
                           latency_ms_mean=(float(lat.mean()) if len(lat) else None)))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot([L["v"] for L in levels], [L["pass_rate"] for L in levels], "o-", color="C0", ms=8)
    for L in levels:
        ax.annotate(f"k={L['speed_level']}\n{L['passed']}/{L['n']}", (L["v"], L["pass_rate"]),
                    textcoords="offset points", xytext=(0, 10), ha="center", fontsize=8)
    ax.axvline(SPEEDS[BASE_LEVEL - 1], color="gray", ls=":", lw=0.8)
    ax.set_xscale("log")
    ax.set_xticks(SPEEDS)
    ax.set_xticklabels([f"{v:g}" for v in SPEEDS])
    ax.xaxis.set_minor_formatter(plt.NullFormatter())
    ax.set_ylim(-0.05, 1.2)
    ax.set_xlabel("선인장 속도 v (단위/ms, 로그축)")
    ax.set_ylabel("통과율")
    ax.set_title("④ 속도별 통과율 — 느리면 너무 일찍(too_early), 빠르면 늦음(too_late)", fontsize=10)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(lif.OUT_DIR, "04_speed_vs_pass.png"), dpi=100)
    plt.close(fig)

    # ---- GIF ----
    n_frames = make_gif([details[kj] for kj in GIF_EPISODES], os.path.join(lif.OUT_DIR, "04_dino.gif"), log)

    base, top = levels[BASE_LEVEL - 1], levels[K - 1]
    summary = dict(
        stage=4,
        constants=dict(h=H, theta_on_deg=THETA_ON_DEG, d_on=D_ON, speeds=SPEEDS, K=K, M=M, base_speed_level=BASE_LEVEL,
                       t_motor_ms=T_MOTOR, T_jump_ms=T_JUMP, t_appear_ms=T_APPEAR, t_extra_ms=T_EXTRA,
                       stim_rate_hz=STIM_HZ, stim_groups=STIM_GROUPS, seed_rule="1000*k + j",
                       d0_by_level=[D_ON + T_APPEAR * v for v in SPEEDS]),
        levels=levels, base_speed_level=BASE_LEVEL, base_pass_rate=base["pass_rate"],
        max_speed_fail_count=int(top["n"] - top["passed"]),
        gif=dict(episodes=[ep_id(*kj) for kj in GIF_EPISODES], n_frames=n_frames, fps=GIF_FPS, frame_ms=GIF_FRAME_MS),
        sim_ms_total=float(sum(float(d["sim_ms"]) for d in details.values())),
        wall_seconds_episodes_total=float(sum(float(d["wall_seconds"]) for d in details.values())),
        wall_seconds=time.perf_counter() - t0,
    )
    with open(os.path.join(lif.OUT_DIR, "04_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    log(df.to_string(index=False))
    log(f"기본 속도 통과율 {base['pass_rate']:.2f}, 최고 속도 실패 {summary['max_speed_fail_count']}개, "
        f"wall {summary['wall_seconds']:.1f} s")


if __name__ == "__main__":
    main()
