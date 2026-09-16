"""shorts_render.py — 강사용: 세로(9:16) 쇼츠 영상. 전뇌 시뮬레이션 결과를 재생하면서
위: 2D 게임 화면(+ 오른쪽 위 구석에 flybody 3D 초파리 아바타, 동기화) / 가운데: 뇌 지도 / 아래: GF 막전위·전체 발화.
계산은 viz_episode.run_episode (MODEL_SPEC §4 그대로), 3D 초파리는 flybody(Apache-2.0) 를 MuJoCo 로 키프레임 렌더.
사용: MUJOCO_GL=osmesa python shorts_render.py <data_dir> <annot_tsv> <comp_csv> <flybody_xml> <out_dir>
"""
import math, os, sys, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.animation import FFMpegWriter, PillowWriter
import mujoco
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import viz_episode as ve

# ---------------- 재생 설정 ----------------
FPS = 30
GAME_MS_PER_FRAME = 1000.0 / FPS / 10.0      # 10배 슬로모션 → 프레임당 3.33 ms
SLOWMO = 10
PREROLL_MS = 60.0                            # θ_on(100 ms) 40 ms 전부터 보여 준다
HOLD_END_S = 1.0
EPISODES = [int(x) for x in os.environ.get("EPISODES", "1,2,3,4,5").split(",")]
W_PX, H_PX = 1080, 1920
PIP_PX = 400

# ---------------- flybody 아바타 ----------------
class FlyAvatar:
    def __init__(self, xml_path, size=PIP_PX):
        self.m = mujoco.MjModel.from_xml_path(xml_path); self.d = mujoco.MjData(self.m)
        self.base = self.m.key_qpos[0].copy()
        self.r = mujoco.Renderer(self.m, height=size, width=size)
        self.cam = mujoco.MjvCamera(); self.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.d.qpos[:] = self.base; mujoco.mj_forward(self.m, self.d)
        self.rest_lookat = self.d.xpos[self._bid("thorax")].copy() + np.array([0.0, 0.0, 0.16])
        self.cache_key = None; self.cache_img = None
    def _bid(self, n): return mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, n)
    def _adr(self, n): return self.m.jnt_qposadr[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, n)]
    def _set(self, q, n, deg): q[self._adr(n)] = math.radians(deg)
    def pose(self, phase, u=0.0, flap=0.0, lift=0.0, shake=0.0):
        """phase: rest / takeoff(u 0→1) / flight(flap 0..1 위상, lift cm) / landing(u 0→1) / hit(shake)"""
        q = self.base.copy()
        def legs(fem, tib, only=None):
            for s in ("left", "right"):
                for L in ("T1", "T2", "T3"):
                    if only and L != only: continue
                    self._set(q, f"femur_{L}_{s}", fem); self._set(q, f"tibia_{L}_{s}", tib)
        def wings(yaw, roll):
            self._set(q, "wing_yaw_left", yaw); self._set(q, "wing_yaw_right", -yaw)
            self._set(q, "wing_roll_left", roll); self._set(q, "wing_roll_right", roll)
        if phase == "takeoff":          # 가운데 다리(T2) 펴기 + 날개 열기 시작
            legs(20 * (1 - u) + 5 * u, 40 * u + 60 * u * u, only="T2"); wings(60 * u, 15 * u)
            q[2] += 0.02 * u
        elif phase == "flight":         # 다리 접고 날갯짓
            legs(100, -70); wings(52 + 33 * math.sin(2 * math.pi * flap), 20 * math.sin(2 * math.pi * flap + 1.0))
            q[2] += lift
        elif phase == "landing":
            legs(100 * (1 - u), -70 * (1 - u)); wings(50 * (1 - u), 10 * (1 - u))
        elif phase == "hit":
            q[0] += shake
        return q
    def render(self, q):
        key = tuple(np.round(q, 3))
        if key == self.cache_key:
            return self.cache_img
        self.d.qpos[:] = q; mujoco.mj_forward(self.m, self.d)
        self.cam.lookat[:] = self.rest_lookat; self.cam.distance = 0.82; self.cam.azimuth = 145; self.cam.elevation = -8
        self.r.update_scene(self.d, camera=self.cam); img = self.r.render().copy()
        self.cache_key, self.cache_img = key, img
        return img

def avatar_state(ep, t, frame_idx):
    """게임 타임라인 → 아바타 자세 파라미터"""
    air = ep["air"]; tgf = ep["t_gf_first"]
    if tgf is not None and air is not None:
        if tgf <= t < air[0]:
            return "takeoff", dict(u=(t - tgf) / ve.T_MOTOR)
        if air[0] <= t <= air[1]:
            u = (t - air[0]) / ve.T_JUMP
            return "flight", dict(flap=(frame_idx % 5) / 5.0, lift=0.30 * 4 * u * (1 - u))
        if air[1] < t <= air[1] + 40:
            return "landing", dict(u=(t - air[1]) / 40.0)
    if (not ep["passed"]) and ep["t_c"] <= t <= ep["t_c"] + 60 and not (air and air[0] <= t <= air[1]):
        return "hit", dict(shake=0.03 * math.sin(frame_idx * 2.5))
    return "rest", {}

# ---------------- 프레임 합성 ----------------
def main():
    data_dir, annot_tsv, comp_csv, fly_xml, out_dir = sys.argv[1:6]
    os.makedirs(out_dir, exist_ok=True)
    plt.rcParams["font.family"] = ["Noto Sans CJK JP", "DejaVu Sans"]; plt.rcParams["axes.unicode_minus"] = False
    W, groups = ve.load(data_dir)
    X, Y, Z = ve.load_positions(annot_tsv, comp_csv); ok = np.isfinite(X) & np.isfinite(Y)
    fly = FlyAvatar(fly_xml)
    eps = {}
    for k in EPISODES:
        t0 = time.time(); eps[k] = ve.run_episode(W, groups, k, 1)
        e = eps[k]; print(f"k={k}: T={e['T']:.0f} ms t_gf={e['t_gf_first']} passed={e['passed']} {e['reason']} spikes={sum(i.size for _, i in e['spikes'])} ({time.time()-t0:.1f}s)", flush=True)

    fig = plt.figure(figsize=(W_PX / 100, H_PX / 100), dpi=100); fig.patch.set_facecolor("#0e1116")
    ax_game = fig.add_axes([0.02, 0.625, 0.96, 0.300]); ax_pip = fig.add_axes([0.611, 0.7135, 0.370, 0.2083])
    ax_brain = fig.add_axes([0.02, 0.310, 0.96, 0.300]); ax_v = fig.add_axes([0.10, 0.170, 0.87, 0.120]); ax_pop = fig.add_axes([0.10, 0.040, 0.87, 0.105])
    for ax in (ax_game, ax_brain, ax_v, ax_pop, ax_pip):
        ax.set_facecolor("#0e1116")
    # 뇌 지도 배경 (한 번)
    ax_brain.scatter(X[ok], -Y[ok], s=0.7, c="#3a4250", alpha=0.9, linewidths=0, rasterized=True)
    ax_brain.set_aspect("equal"); ax_brain.set_xticks([]); ax_brain.set_yticks([])
    for sp_ in ax_brain.spines.values(): sp_.set_visible(False)
    sc_recent = ax_brain.scatter([], [], s=16, c="#2e86c1", alpha=0.35, linewidths=0)
    sc_now = ax_brain.scatter([], [], s=38, c=[], linewidths=0)
    sc_gf = ax_brain.scatter([], [], s=420, c="#ff3b30", marker="*", linewidths=0.8, edgecolors="white", zorder=6)
    brain_title = fig.text(0.5, 0.612, "", ha="center", va="top", fontsize=15, color="#d5dbe3")
    header = fig.text(0.5, 0.985, "초파리 뇌(뉴런 138,639개)가 공룡 게임을 한다", ha="center", va="top", fontsize=30, color="white", fontweight="bold")
    sub = fig.text(0.5, 0.950, "", ha="center", va="top", fontsize=16, color="#b8c1cc")
    foot = fig.text(0.5, 0.008, "FlyWire v783 커넥톰 (CC BY 4.0) · Shiu 2024 LIF 모델 · flybody 3D 초파리 (Apache-2.0) · 전뇌 시뮬레이션 결과 재생", ha="center", va="bottom", fontsize=11, color="#7f8a96")
    pip_img = ax_pip.imshow(np.zeros((PIP_PX, PIP_PX, 3), dtype=np.uint8)); ax_pip.set_xticks([]); ax_pip.set_yticks([])
    for sp_ in ax_pip.spines.values(): sp_.set_edgecolor("#5d6d7e"); sp_.set_linewidth(2)
    pip_label = ax_pip.text(0.5, 0.03, "flybody 3D 초파리 (동기화)", transform=ax_pip.transAxes, ha="center", va="bottom", fontsize=11, color="white", bbox=dict(boxstyle="round,pad=0.25", fc="#00000088", ec="none"))

    mp4 = os.path.join(out_dir, os.environ.get("OUT_NAME", "fly_brain_dino_shorts.mp4"))
    writer = FFMpegWriter(fps=FPS, codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium"])
    frame_idx = 0; t_start = time.time(); marks = []
    all_axes = (ax_game, ax_pip, ax_brain, ax_v, ax_pop)
    def card(lines, n_frames, extra=None):
        nonlocal frame_idx
        for ax in all_axes: ax.set_visible(False)
        brain_title.set_visible(False); sub.set_visible(False)
        arts = []
        y = 0.62
        for txt, size, col in lines:
            arts.append(fig.text(0.5, y, txt, ha="center", va="center", fontsize=size, color=col, fontweight="bold" if size >= 30 else "normal", wrap=True)); y -= 0.055 if size < 30 else 0.075
        if extra: arts += extra()
        for _ in range(n_frames):
            writer.grab_frame(); frame_idx += 1
        for a in arts: a.remove()
        for ax in all_axes: ax.set_visible(True)
        brain_title.set_visible(True); sub.set_visible(True)
    with writer.saving(fig, mp4, dpi=100):
        card([("초파리 뇌 전체를 컴퓨터에 넣었다", 34, "white"), ("뉴런 138,639개 · 연결 2,700,513개 (FlyWire 커넥톰)", 20, "#b8c1cc"), ("다가오는 물체를 피하는 반사 회로로", 24, "#d5dbe3"), ("공룡 점프 게임을 시켜 보았다", 24, "#d5dbe3"), ("같은 뇌, 다섯 가지 속도", 22, "#ff9f1a")], int(2.2 * FPS))
        for k in EPISODES:
            ep = eps[k]; T = ep["T"]; marks.append((k, frame_idx / FPS))
            step_idx = {st: idx for st, idx in ep["spikes"]}
            lp_mask = np.zeros(ve.N, dtype=bool); lp_mask[ep["lplc2"]] = True
            def window(s0, s1):
                parts = [step_idx[q] for q in range(max(s0, 0), s1 + 1) if q in step_idx]
                return np.unique(np.concatenate(parts)) if parts else np.empty(0, dtype=np.int64)
            nb = int(math.ceil(T)); pop = np.zeros(nb)
            for s, idx in ep["spikes"]:
                pop[min(int(s * ve.DT), nb - 1)] += idx.size
            tt = np.arange(ep["steps"]) * ve.DT
            n_frames = int((T - PREROLL_MS) / GAME_MS_PER_FRAME) + 1
            sub.set_text(f"속도 단계 {k}/5 (v = {ep['v']} 단위/ms)  ·  화면은 실제 계산의 1/{SLOWMO} 속도")
            brain_title.set_text("뇌 지도(정면) — 켜진 점 = 지금 발화한 뉴런  ·  주황 LPLC2(다가오는 물체 감지)  ·  빨간 별 = 거대섬유 GF  ·  청록 = 하류")
            gf_latched_until = -1
            for f in range(n_frames + int(HOLD_END_S * FPS)):
                t = min(PREROLL_MS + f * GAME_MS_PER_FRAME, T - ve.DT); s = min(int(round(t / ve.DT)), ep["steps"] - 1)
                # ---- 뇌 지도 ----
                now = window(s - int(GAME_MS_PER_FRAME / ve.DT) + 1, s); recent = window(s - int(20 / ve.DT) + 1, s - int(GAME_MS_PER_FRAME / ve.DT))
                now = now[ok[now]] if now.size else now; recent = recent[ok[recent]] if recent.size else recent
                sc_recent.set_offsets(np.c_[X[recent], -Y[recent]] if recent.size else np.empty((0, 2)))
                if now.size:
                    sc_now.set_offsets(np.c_[X[now], -Y[now]]); sc_now.set_color(np.where(lp_mask[now], "#ff9f1a", "#1abc9c"))
                else:
                    sc_now.set_offsets(np.empty((0, 2)))
                now_set = set(now.tolist()); gf_now = [i for i in (ep["gfL"], ep["gfR"]) if i in now_set]
                sc_gf.set_offsets(np.c_[X[gf_now], -Y[gf_now]] if gf_now else np.empty((0, 2)))
                # ---- 게임 ----
                ax_game.clear(); ax_game.set_facecolor("#0e1116")
                d = ep["dist"][s]; th = ep["theta"][s]
                in_air = ep["air"] is not None and ep["air"][0] <= t <= ep["air"][1]
                y_fly = 0.0
                if in_air:
                    u = (t - ep["air"][0]) / ve.T_JUMP; y_fly = 22.0 * 4 * u * (1 - u)
                xmax = 90.0
                ax_game.set_xlim(-14, xmax); ax_game.set_ylim(-5, 40)
                ax_game.add_patch(Rectangle((-14, -5), xmax + 14, 5, color="#3d5a3d", zorder=1))
                if -3 < d < xmax + 4:
                    ax_game.add_patch(Rectangle((d - 1.5, 0), 3, ve.H, color="#2ecc71", zorder=3))
                    ax_game.add_patch(Rectangle((d - 3.5, 3), 2, 4, color="#2ecc71", zorder=3)); ax_game.add_patch(Rectangle((d + 1.5, 4), 2, 4, color="#2ecc71", zorder=3))
                ve.fly_patch(ax_game, 0, y_fly, wing_phase=(f % 2 == 0) if in_air else False, color="#5dade2")
                if ep["t_gf_first"] is not None and t >= ep["t_gf_first"] and gf_latched_until < 0:
                    gf_latched_until = f + 9
                if ep["t_on"] is None or t < ep["t_on"]:
                    state, col = f"접근 중 — 각크기 θ = {th:4.1f}° (아직 20° 미만, 뇌는 조용)", "#aab4be"
                elif f <= gf_latched_until and ep["t_gf_first"] is not None and t >= ep["t_gf_first"]:
                    state, col = f"GF 스파이크! 자극 후 {ep['t_gf_first']-ep['t_on']:.1f} ms → 10 ms 뒤 점프", "#ff3b30"
                elif ep["t_gf_first"] is None or t < ep["t_gf_first"]:
                    state, col = f"LOOMING — θ = {th:4.1f}° ≥ 20°, 시각 뉴런 LPLC2 210개 발화 중", "#ff9f1a"
                elif in_air:
                    state, col = "점프 중 (공중 300 ms)", "#5dade2"
                elif ep["air"] is not None and t > ep["air"][1]:
                    state, col = "착지", "#aab4be"
                else:
                    state, col = "", "#aab4be"
                ax_game.text(-13, 38.5, f"t = {t:6.1f} ms   선인장까지 {max(d,0):6.1f}   충돌 예정 {ep['t_c']:.0f} ms", fontsize=13, va="top", color="#d5dbe3")
                ax_game.text(-13, 33.5, state, fontsize=15, va="top", color=col, fontweight="bold")
                if t >= ep["t_c"]:
                    res = "통과" if ep["passed"] else {"too_late": "충돌 — 너무 빨라서 늦음", "too_early": "충돌 — 너무 일찍 뛰어 착지", "no_jump": "충돌 — 점프 없음"}[ep["reason"]]
                    ax_game.text(-13, 26.5, res, fontsize=22, va="top", fontweight="bold", color="#2ecc71" if ep["passed"] else "#ff3b30")
                ax_game.set_xticks([]); ax_game.set_yticks([])
                for sp_ in ax_game.spines.values(): sp_.set_visible(False)
                # ---- 3D 아바타 ----
                phase, kw = avatar_state(ep, t, f)
                pip_img.set_data(fly.render(fly.pose(phase, **kw)))
                # ---- GF 막전위 ----
                ax_v.clear(); ax_v.set_facecolor("#0e1116")
                ax_v.plot(tt[:s + 1], ep["vgf"][:s + 1, 0], color="#ff3b30", lw=1.2, label="GF_L"); ax_v.plot(tt[:s + 1], ep["vgf"][:s + 1, 1], color="#ff9f1a", lw=1.2, label="GF_R", alpha=0.9)
                ax_v.axhline(ve.V_TH, color="#d5dbe3", ls=":", lw=1); ax_v.axvline(t, color="white", lw=1); ax_v.axvline(ep["t_c"], color="#ff3b30", lw=1, ls="--", alpha=0.7)
                ax_v.set_xlim(PREROLL_MS, T); ax_v.set_ylim(-53.5, -43.5)
                ax_v.set_title("거대섬유 GF 막전위 (점선 = 발화 임계값 −45 mV, 빨간 점선 = 충돌 시각)", fontsize=13, color="#d5dbe3", loc="left")
                ax_v.tick_params(colors="#aab4be", labelsize=10); ax_v.set_ylabel("mV", color="#aab4be"); ax_v.legend(loc="lower right", fontsize=9, facecolor="#1c2229", labelcolor="white", edgecolor="none")
                for sp_ in ax_v.spines.values(): sp_.set_color("#3a4250")
                # ---- 전체 발화 ----
                ax_pop.clear(); ax_pop.set_facecolor("#0e1116")
                b = int(t); ax_pop.fill_between(np.arange(b + 1), pop[:b + 1], color="#5d6d7e", step="mid")
                ax_pop.set_xlim(PREROLL_MS, T); ax_pop.set_ylim(0, max(pop.max() * 1.1, 1)); ax_pop.axvline(t, color="white", lw=1)
                ax_pop.set_title("뇌 전체의 발화 수 (1 ms 마다)", fontsize=13, color="#d5dbe3", loc="left"); ax_pop.set_xlabel("시간 (ms)", color="#aab4be")
                ax_pop.tick_params(colors="#aab4be", labelsize=10)
                for sp_ in ax_pop.spines.values(): sp_.set_color("#3a4250")
                writer.grab_frame(); frame_idx += 1
                if frame_idx % 60 == 0:
                    print(f"  frame {frame_idx} (k={k}, t={t:.0f} ms) {time.time()-t_start:.0f}s", flush=True)
        # ---- 아웃트로: 속도별 결과 ----
        marks.append(("outro", frame_idx / FPS))
        def bars():
            axb = fig.add_axes([0.15, 0.20, 0.70, 0.16]); axb.set_facecolor("#0e1116")
            ks = EPISODES; rates = [1.0 if eps[k]["passed"] else 0.0 for k in ks]
            axb.bar([str(eps[k]["v"]) for k in ks], [r if r else 0.07 for r in rates], color=["#2ecc71" if r else "#ff3b30" for r in rates])
            for i, k in enumerate(ks):
                axb.text(i, (1.0 if rates[i] else 0.07) + 0.04, "통과" if rates[i] else {"too_late": "늦음", "too_early": "너무 이름", "no_jump": "점프 없음"}[eps[k]["reason"]], ha="center", va="bottom", color="#d5dbe3", fontsize=12)
            axb.set_ylim(0, 1.15); axb.set_yticks([0, 1]); axb.set_yticklabels(["충돌", "통과"], color="#d5dbe3", fontsize=13)
            axb.set_xlabel("선인장 속도 (단위/ms)", color="#d5dbe3", fontsize=13); axb.tick_params(colors="#d5dbe3", labelsize=13)
            for sp_ in axb.spines.values(): sp_.set_color("#3a4250")
            return [axb]
        card([("결과", 34, "white"), ("느리면 너무 일찍 뛰어 착지 후 부딪히고", 22, "#d5dbe3"), ("빠르면 반사 6 ms + 근육 10 ms 예산으로 늦는다", 22, "#d5dbe3"), ("커넥톰은 반사를 재현하지,", 26, "#ff9f1a"), ("속도를 학습하진 못한다", 26, "#ff9f1a")], int(3.0 * FPS), extra=bars)
    print("episode start times (s):", marks)
    print(f"done: {mp4} frames={frame_idx} ({time.time()-t_start:.0f}s) size={os.path.getsize(mp4)/1e6:.1f} MB")

if __name__ == "__main__":
    main()
