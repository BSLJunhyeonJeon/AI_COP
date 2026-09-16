"""viz_episode.py — 강사용: 게임 화면과 초파리 뇌 활동을 한 화면에서 동기화해 보여 주는 애니메이션.
MODEL_SPEC §4 규칙 그대로 에피소드를 시뮬레이션하면서 (1) 모든 스파이크 (2) GF 막전위 (3) 자극 on/off 를 기록하고,
위: 게임 장면 / 가운데: 래스터(LPLC2 표본·GF·하류 뉴런) / 아래: 전체 발화 수와 GF 막전위 를 시간 커서와 함께 그린다.
사용: python viz_episode.py <data_dir> <out_dir> [<annotations.tsv> <Completeness_783.csv>]
"""
import json, math, os, sys, time
import numpy as np, pandas as pd, scipy.sparse as sp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, Circle
from matplotlib.animation import PillowWriter

V_REST, V_TH, TAU_M, TAU_S, T_REF, T_DELAY, W_UNIT, DT = -52.0, -45.0, 20.0, 5.0, 2.2, 1.8, 0.275, 0.1
N = 138_639
H, THETA_ON, T_MOTOR, T_JUMP, R_STIM = 10.0, 20.0, 10.0, 300.0, 150.0
SPEEDS = [0.05, 0.1, 0.25, 0.6, 2.0]
D_ON = H / (2 * math.tan(math.radians(THETA_ON) / 2))

def load(data_dir):
    conn = pd.read_parquet(f"{data_dir}/connections.parquet")
    w = W_UNIT * conn["syn"].to_numpy(np.float64) * conn["sign"].to_numpy(np.float64)
    W = sp.csr_matrix((w, (conn["pre"].to_numpy(), conn["post"].to_numpy())), shape=(N, N))
    groups = json.load(open(f"{data_dir}/groups.json", encoding="utf-8"))
    return W, groups

def load_positions(annot_tsv, comp_csv):
    """뉴런 위치(FlyWire 복셀 좌표, 4x4x40 nm). soma 가 있으면 soma, 없으면 pos. 인덱스 순서 = Completeness 행 순서."""
    a = pd.read_csv(annot_tsv, sep="\t", low_memory=False, usecols=["root_id", "pos_x", "pos_y", "pos_z", "soma_x", "soma_y", "soma_z"])
    comp = pd.read_csv(comp_csv); comp.columns = ["root_id", "completed"]
    m = comp.merge(a.drop_duplicates("root_id"), on="root_id", how="left")
    x = m["soma_x"].fillna(m["pos_x"]).to_numpy(np.float64); y = m["soma_y"].fillna(m["pos_y"]).to_numpy(np.float64); z = m["soma_z"].fillna(m["pos_z"]).to_numpy(np.float64)
    return x, y, z

def theta_deg(d):
    return 2 * math.degrees(math.atan(H / (2 * d))) if d > 0 else 180.0

def run_episode(W, groups, k, j):
    """MODEL_SPEC §4 그대로. 반환: dict(스파이크 목록, GF 막전위, 게임 타임라인)."""
    v_k = SPEEDS[k - 1]; seed = 1000 * k + j
    d0 = D_ON + 100.0 * v_k; t_c = d0 / v_k; T = t_c + 50.0
    steps = int(round(T / DT)); delay = int(round(T_DELAY / DT))
    rng = np.random.default_rng(seed)
    lplc2 = np.array(groups["LPLC2_L"] + groups["LPLC2_R"]); gfL, gfR = groups["GF_L"][0], groups["GF_R"][0]
    a_m, a_s = math.exp(-DT / TAU_M), math.exp(-DT / TAU_S)
    v = np.full(N, V_REST); g = np.zeros(N); ref_until = np.zeros(N, dtype=np.int64)
    queue = [np.empty(0, dtype=np.int64) for _ in range(delay + 1)]
    p_stim = R_STIM * DT / 1000.0
    spikes = []            # (step, idx array)
    vgf = np.zeros((steps, 2)); stim_on = np.zeros(steps, dtype=bool); theta = np.zeros(steps); dist = np.zeros(steps)
    t_gf_first = None
    t0 = time.time()
    for s in range(steps):
        t = s * DT; d = d0 - v_k * t; dist[s] = d; th = theta_deg(d); theta[s] = th
        arrive = queue[s % (delay + 1)]
        if arrive.size:
            g += np.asarray(W[arrive].sum(axis=0)).ravel()
        active = ref_until <= s
        v = np.where(active, V_REST + (v - V_REST) * a_m + g * (1.0 - a_m), V_REST)
        g *= a_s
        spk = np.flatnonzero(active & (v >= V_TH))
        if th >= THETA_ON and d > 0:
            stim_on[s] = True
            forced = lplc2[rng.random(lplc2.size) < p_stim]
            spk = np.union1d(spk, forced)
        vgf[s] = (v[gfL], v[gfR])
        if spk.size:
            v[spk] = V_REST; ref_until[spk] = s + int(round(T_REF / DT))
            spikes.append((s, spk))
            if t_gf_first is None and (gfL in spk or gfR in spk):
                t_gf_first = t
        queue[(s + delay) % (delay + 1)] = spk
    wall = time.time() - t0
    # 게임 판정
    if t_gf_first is None:
        air = None; passed = False; reason = "no_jump"
    else:
        air = (t_gf_first + T_MOTOR, t_gf_first + T_MOTOR + T_JUMP)
        passed = air[0] <= t_c <= air[1]
        reason = "" if passed else ("too_late" if air[0] > t_c else "too_early")
    t_on = float(np.argmax(stim_on) * DT) if stim_on.any() else None
    return dict(k=k, j=j, v=v_k, d0=d0, t_c=t_c, T=T, steps=steps, spikes=spikes, vgf=vgf, stim_on=stim_on,
                theta=theta, dist=dist, t_gf_first=t_gf_first, t_on=t_on, air=air, passed=passed, reason=reason,
                wall=wall, gfL=gfL, gfR=gfR, lplc2=lplc2)

def fly_patch(ax, x, y, wing_phase, color="#1f4e9a"):
    """초파리 모양(우리가 그린 단순 도형): 몸통 타원 + 날개 두 장 + 눈."""
    body = Ellipse((x, y + 4), 6, 3.2, color=color, zorder=5); ax.add_patch(body)
    head = Circle((x + 3.2, y + 4.4), 1.3, color=color, zorder=5); ax.add_patch(head)
    ax.add_patch(Circle((x + 3.7, y + 4.9), 0.5, color="#c0392b", zorder=6))
    dy = 1.6 if wing_phase else 0.8
    for sx in (-1.2, 0.8):
        ax.add_patch(Ellipse((x + sx, y + 5.5 + dy * 0.6), 4.2, 1.4, angle=20 if wing_phase else 5, color="#9ecae1", alpha=0.85, zorder=4))

def render(ep, out_path, XYZ, frame_ms=5.0, fps=8, hold_last=12):
    T = ep["T"]; n_frames = int(T // frame_ms) + 1
    # 래스터 행 구성: LPLC2 표본 12 + GF 2 + 하류 활성 뉴런 24
    counts = np.zeros(N, dtype=np.int64)
    for s, idx in ep["spikes"]:
        counts[idx] += 1
    lp_set = set(ep["lplc2"].tolist())
    lp_rows = [int(i) for i in ep["lplc2"][:12]]
    others = [int(i) for i in np.argsort(-counts) if int(i) not in lp_set and int(i) not in (ep["gfL"], ep["gfR"])][:24]
    rows = [("LPLC2", i) for i in lp_rows] + [("GF_L", ep["gfL"]), ("GF_R", ep["gfR"])] + [("하류", i) for i in others]
    row_of = {idx: r for r, (_, idx) in enumerate(rows)}
    ev_t, ev_r = [], []
    for s, idx in ep["spikes"]:
        for i in idx:
            r = row_of.get(int(i))
            if r is not None:
                ev_t.append(s * DT); ev_r.append(r)
    ev_t = np.array(ev_t); ev_r = np.array(ev_r)
    # 전체 발화 수 (1 ms 빈)
    nb = int(math.ceil(T)); pop = np.zeros(nb)
    for s, idx in ep["spikes"]:
        b = min(int(s * DT), nb - 1); pop[b] += idx.size
    tt = np.arange(ep["steps"]) * DT
    gfL_row, gfR_row = row_of[ep["gfL"]], row_of[ep["gfR"]]

    fig = plt.figure(figsize=(13.6, 13.6), dpi=75)
    gs = fig.add_gridspec(4, 2, height_ratios=[1.0, 2.3, 1.15, 0.8], width_ratios=[1.35, 1.0], hspace=0.38, wspace=0.22, left=0.09, right=0.98, top=0.95, bottom=0.05)
    ax_game = fig.add_subplot(gs[0, :]); ax_brain = fig.add_subplot(gs[1, :]); ax_ras = fig.add_subplot(gs[2, :]); ax_pop = fig.add_subplot(gs[3, 0]); ax_v = fig.add_subplot(gs[3, 1])
    # ---- 뇌 지도(정면 뷰) 배경: 한 번만 그린다 ----
    X, Y, Z = XYZ; ok = np.isfinite(X) & np.isfinite(Y)
    ax_brain.scatter(X[ok], -Y[ok], s=0.7, c="#c3c9d0", alpha=0.4, linewidths=0, rasterized=True)
    ax_brain.set_aspect("equal"); ax_brain.set_xticks([]); ax_brain.set_yticks([])
    for sp_ in ax_brain.spines.values(): sp_.set_visible(False)
    ax_brain.set_title("초파리 뇌 지도 · 정면 뷰 — 회색 점 = 뉴런 138,639개의 위치(FlyWire 좌표). 켜진 점 = 지난 5 ms 안에 발화한 뉴런 (주황 = 자극받는 LPLC2, 빨간 별 = 거대섬유 GF, 청록 = 하류 뉴런, 연한 파랑 = 직전 20 ms)", fontsize=9.5)
    sc_recent = ax_brain.scatter([], [], s=14, c="#5dade2", alpha=0.3, linewidths=0)
    sc_now = ax_brain.scatter([], [], s=34, c=[], linewidths=0)
    sc_gf = ax_brain.scatter([], [], s=320, c="#c0392b", marker="*", linewidths=0.6, edgecolors="k", zorder=6)
    step_idx = {st: idx for st, idx in ep["spikes"]}
    lp_mask = np.zeros(N, dtype=bool); lp_mask[ep["lplc2"]] = True
    def window(s0, s1):
        parts = [step_idx[q] for q in range(max(s0, 0), s1 + 1) if q in step_idx]
        return np.unique(np.concatenate(parts)) if parts else np.empty(0, dtype=np.int64)
    writer = PillowWriter(fps=fps)
    title = f"에피소드 k={ep['k']} (v={ep['v']} 단위/ms), j={ep['j']} — 게임 · 뇌 지도 · 래스터 · 전체 발화 · GF 막전위 (게임 시간 = 신경 시간)"
    with writer.saving(fig, out_path, dpi=75):
        for f in range(n_frames):
            t = min(f * frame_ms, T - DT); s = int(round(t / DT)); s = min(s, ep["steps"] - 1)
            for ax in (ax_game, ax_ras, ax_pop, ax_v):
                ax.clear()
            fig.suptitle(title, fontsize=12)
            # ---- 뇌 지도 ----
            now = window(s - int(frame_ms / DT) + 1, s); recent = window(s - int(20 / DT) + 1, s - int(frame_ms / DT))
            recent = recent[ok[recent]] if recent.size else recent; now = now[ok[now]] if now.size else now
            sc_recent.set_offsets(np.c_[X[recent], -Y[recent]] if recent.size else np.empty((0, 2)))
            if now.size:
                cols = np.where(lp_mask[now], "#e67e22", "#16a085")
                sc_now.set_offsets(np.c_[X[now], -Y[now]]); sc_now.set_color(cols)
            else:
                sc_now.set_offsets(np.empty((0, 2)))
            gf_now = [i for i in (ep["gfL"], ep["gfR"]) if i in set(now.tolist())]
            sc_gf.set_offsets(np.c_[X[gf_now], -Y[gf_now]] if gf_now else np.empty((0, 2)))
            # ---- 게임 ----
            d = ep["dist"][s]; th = ep["theta"][s]
            in_air = ep["air"] is not None and ep["air"][0] <= t <= ep["air"][1]
            y_fly = 0.0
            if in_air:
                u = (t - ep["air"][0]) / T_JUMP; y_fly = 22.0 * 4 * u * (1 - u)
            xmax = ep["d0"] + 8
            ax_game.set_xlim(-12, xmax); ax_game.set_ylim(-4, 34); ax_game.set_aspect("auto")
            ax_game.add_patch(Rectangle((-12, -4), xmax + 12, 4, color="#6b8e6b", zorder=1))
            if d > -3:
                ax_game.add_patch(Rectangle((d - 1.5, 0), 3, H, color="#2e8b57", zorder=3))
                ax_game.add_patch(Rectangle((d - 3.5, 3), 2, 4, color="#2e8b57", zorder=3)); ax_game.add_patch(Rectangle((d + 1.5, 4), 2, 4, color="#2e8b57", zorder=3))
            fly_patch(ax_game, 0, y_fly, wing_phase=(f % 2 == 0) if in_air else False)
            # 상태 텍스트
            if ep["t_on"] is None or t < ep["t_on"]:
                state, col = f"접근 중 — θ = {th:4.1f}° (< {THETA_ON:.0f}°, 자극 없음)", "#555"
            elif ep["t_gf_first"] is None or t < ep["t_gf_first"]:
                state, col = f"LOOMING — θ = {th:4.1f}° ≥ {THETA_ON:.0f}°, LPLC2 210개 150 Hz 자극 중", "#d35400"
            elif t < ep["air"][0]:
                state, col = f"GF 스파이크! ({ep['t_gf_first']:.1f} ms, 지연 {ep['t_gf_first']-ep['t_on']:.1f} ms) → {T_MOTOR:.0f} ms 뒤 점프", "#c0392b"
            elif t <= ep["air"][1]:
                state, col = "점프 중 (공중 300 ms)", "#1f4e9a"
            else:
                state, col = "착지", "#555"
            if t >= ep["t_c"]:
                res = "통과 ✓" if ep["passed"] else f"충돌 ✗ ({ep['reason']})"
                ax_game.text(xmax * 0.98, 30, res, ha="right", va="top", fontsize=16, fontweight="bold", color="#27ae60" if ep["passed"] else "#c0392b")
            ax_game.text(-11, 31.5, f"t = {t:6.1f} ms   선인장 거리 d = {max(d,0):6.1f}   충돌 예정 t_c = {ep['t_c']:.1f} ms", fontsize=10, va="top")
            ax_game.text(-11, 27.5, state, fontsize=11, va="top", color=col, fontweight="bold")
            ax_game.set_xticks([]); ax_game.set_yticks([])
            for sp_ in ax_game.spines.values(): sp_.set_visible(False)
            # ---- 래스터 ----
            m = ev_t <= t
            colors = np.where(ev_r[m] < 12, "#d35400", np.where(np.isin(ev_r[m], [gfL_row, gfR_row]), "#c0392b", "#34495e"))
            sizes = np.where(np.isin(ev_r[m], [gfL_row, gfR_row]), 60, 8)
            lws = np.where(np.isin(ev_r[m], [gfL_row, gfR_row]), 2.2, 1.2)
            ax_ras.scatter(ev_t[m], ev_r[m], s=sizes, marker="|", c=colors, linewidths=lws)
            if ep["t_on"] is not None:
                ax_ras.axvspan(ep["t_on"], min(t, ep["t_c"]) if t > ep["t_on"] else ep["t_on"], color="#f39c12", alpha=0.08, lw=0)
            ax_ras.axvline(t, color="k", lw=1); ax_ras.axvline(ep["t_c"], color="#c0392b", lw=1, ls="--")
            ax_ras.axhspan(gfL_row - 0.5, gfR_row + 0.5, color="#c0392b", alpha=0.08, lw=0)
            ax_ras.set_xlim(0, T); ax_ras.set_ylim(-0.5, len(rows) - 0.5)
            ax_ras.set_yticks([5.5, (gfL_row + gfR_row) / 2, 14 + 11.5]); ax_ras.set_yticklabels(["LPLC2 자극 뉴런\n(210개 중 12개)", "GF_L / GF_R", "하류 뉴런\n(활동 상위 24개)"], fontsize=9)
            ax_ras.set_ylabel("뉴런"); ax_ras.set_title("뇌 활동 래스터 (주황 = 자극 뉴런, 빨강 = 거대섬유 GF, 회색 = 하류 뉴런; 점선 = 충돌 시각)", fontsize=10)
            # ---- 전체 발화 수 ----
            b = int(t)
            ax_pop.fill_between(np.arange(b + 1), pop[:b + 1], color="#7f8c8d", step="mid")
            ax_pop.set_xlim(0, T); ax_pop.set_ylim(0, max(pop.max() * 1.1, 1)); ax_pop.axvline(t, color="k", lw=1)
            ax_pop.set_title("전체 뇌의 발화 수 (1 ms 마다)", fontsize=10); ax_pop.set_xlabel("시간 (ms)"); ax_pop.set_ylabel("스파이크/ms")
            # ---- GF 막전위 ----
            ax_v.plot(tt[:s + 1], ep["vgf"][:s + 1, 0], color="#c0392b", lw=1, label="GF_L")
            ax_v.plot(tt[:s + 1], ep["vgf"][:s + 1, 1], color="#e67e22", lw=1, label="GF_R", alpha=0.8)
            ax_v.axhline(V_TH, color="k", ls=":", lw=1); ax_v.text(T * 0.99, V_TH + 0.3, "임계값 −45 mV", ha="right", fontsize=8)
            ax_v.set_xlim(0, T); ax_v.set_ylim(-53.5, -43.5); ax_v.axvline(t, color="k", lw=1)
            ax_v.set_title("거대섬유(GF) 막전위", fontsize=10); ax_v.set_xlabel("시간 (ms)"); ax_v.set_ylabel("mV"); ax_v.legend(loc="lower right", fontsize=8)
            writer.grab_frame()
            if f == n_frames - 1:
                for _ in range(hold_last):
                    writer.grab_frame()
    plt.close(fig)
    return n_frames

if __name__ == "__main__":
    data_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    plt.rcParams["font.family"] = ["Noto Sans CJK JP", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    W, groups = load(data_dir)
    XYZ = load_positions(sys.argv[3], sys.argv[4]) if len(sys.argv) > 4 else (np.full(N, np.nan),) * 3
    for k in (3, 5):
        ep = run_episode(W, groups, k, 1)
        print(f"k={k}: v={ep['v']} d0={ep['d0']:.1f} t_c={ep['t_c']:.1f} t_on={ep['t_on']} t_gf_first={ep['t_gf_first']} air={ep['air']} passed={ep['passed']} {ep['reason']} | spikes {sum(i.size for _, i in ep['spikes'])} | sim wall {ep['wall']:.1f}s")
        p = os.path.join(out_dir, f"episode_k{k}_game_and_brain.gif")
        t0 = time.time(); nf = render(ep, p, XYZ); print(f"  rendered {nf} frames -> {p} ({time.time()-t0:.0f}s, {os.path.getsize(p)/1e6:.1f} MB)")
