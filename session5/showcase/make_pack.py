"""make_pack.py — 재생기(player.py)가 읽는 데이터 팩을 미리 계산해 만든다 (강사용, 한 번만 실행).

들어가는 것:
  pack/meta.json            에피소드별 상수·결과, 프레임 간격, 뇌 지도 좌표 변환
  pack/episodes.npz         에피소드별 프레임 타임라인 + 프레임마다 켜진 뉴런의 픽셀 좌표 + GF 막전위 + 전체 발화 수
  pack/brain_bg.png         뉴런 138,639개 위치로 그린 뇌 지도 배경(정면 뷰)
  pack/fly3d/*.png          flybody 3D 초파리 자세 프레임(휴지·이륙·비행 날갯짓·착지)
  pack/fly2d_{0,1}.png      2D 게임용 초파리 스프라이트(날개 위상 2개)

사용:
  python make_pack.py <harness_data_dir> <annot_tsv> <completeness_csv> <flybody_xml> <out_pack_dir>
  (리눅스 서버에서는 MUJOCO_GL=osmesa 를 앞에 붙인다. 윈도우 데스크톱은 그대로 실행.)
계산 규칙은 viz_episode.run_episode (MODEL_SPEC §4 그대로) 를 그대로 쓴다.
"""
import json, math, os, sys, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)          # viz_episode.py / shorts_render.py 는 같은 폴더
import viz_episode as ve

FRAME_MS = 2.5            # 재생기 프레임 간격(게임 시간). 10배 슬로모션이면 초당 40 프레임
RECENT_MS = 15.0          # "직전" 창
BRAIN_W, BRAIN_H = 900, 520
EPISODES = [1, 2, 3, 4, 5]

def brain_background(X, Y, ok, out_png):
    """정면 뷰 배경. 반환: (sx, sy, ox, oy) — 픽셀 = (x*sx+ox, -y*sy+oy)"""
    xs, ys = X[ok], -Y[ok]
    x0, x1 = np.percentile(xs, [0.1, 99.9]); y0, y1 = np.percentile(ys, [0.1, 99.9])
    pad = 0.03
    x0, x1 = x0 - (x1 - x0) * pad, x1 + (x1 - x0) * pad; y0, y1 = y0 - (y1 - y0) * pad, y1 + (y1 - y0) * pad
    s = min(BRAIN_W / (x1 - x0), BRAIN_H / (y1 - y0))
    ox = (BRAIN_W - (x1 - x0) * s) / 2 - x0 * s; oy = (BRAIN_H - (y1 - y0) * s) / 2 + y1 * s   # 화면 y 는 아래로 증가
    px = xs * s + ox; py = -ys * s + oy
    img = np.zeros((BRAIN_H, BRAIN_W, 3), dtype=np.float32)
    ix = np.clip(px.astype(int), 0, BRAIN_W - 1); iy = np.clip(py.astype(int), 0, BRAIN_H - 1)
    np.add.at(img, (iy, ix), np.array([0.16, 0.18, 0.22], dtype=np.float32))
    img = np.clip(img, 0, 0.55) + np.array([0.055, 0.067, 0.086], dtype=np.float32)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out_png)
    return s, ox, oy

def fly3d_frames(fly_xml, out_dir):
    """flybody 자세 프레임. shorts_render.FlyAvatar 와 같은 자세 규칙."""
    import mujoco
    from shorts_render import FlyAvatar
    os.makedirs(out_dir, exist_ok=True)
    fly = FlyAvatar(fly_xml, size=400)
    frames = {"rest": [("rest", {})],
              "takeoff": [("takeoff", dict(u=u)) for u in np.linspace(0, 1, 6)],
              "flight": [("flight", dict(flap=p / 5.0, lift=0.0)) for p in range(5)],
              "landing": [("landing", dict(u=u)) for u in np.linspace(0, 1, 4)]}
    names = {}
    for kind, lst in frames.items():
        names[kind] = []
        for i, (phase, kw) in enumerate(lst):
            img = fly.render(fly.pose(phase, **kw)); fn = f"{kind}_{i}.png"
            Image.fromarray(img).save(os.path.join(out_dir, fn)); names[kind].append(fn)
    return names

def fly2d_sprites(out_dir):
    """2D 게임용 초파리 스프라이트 2장(RGBA). viz_episode.fly_patch 를 그대로 그린다."""
    for phase in (0, 1):
        fig = plt.figure(figsize=(2.4, 2.4), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-6, 6); ax.set_ylim(-1, 11); ax.axis("off")
        ve.fly_patch(ax, 0, 0, wing_phase=bool(phase), color="#5dade2")
        fig.savefig(os.path.join(out_dir, f"fly2d_{phase}.png"), transparent=True, dpi=100); plt.close(fig)

def main():
    data_dir, annot_tsv, comp_csv, fly_xml, out = sys.argv[1:6]
    os.makedirs(out, exist_ok=True)
    W, groups = ve.load(data_dir)
    X, Y, Z = ve.load_positions(annot_tsv, comp_csv); ok = np.isfinite(X) & np.isfinite(Y)
    sx, ox, oy = brain_background(X, Y, ok, os.path.join(out, "brain_bg.png"))
    PX = np.where(ok, X * sx + ox, -1).astype(np.int16); PY = np.where(ok, Y * sx + oy, -1).astype(np.int16)  # y: -(-Y)=Y → 화면 아래로
    # 주의: brain_background 에서 ys = -Y, py = -ys*s + oy = Y*s + oy
    fly_names = fly3d_frames(fly_xml, os.path.join(out, "fly3d")); fly2d_sprites(out)
    lp_all = np.array(groups["LPLC2_L"] + groups["LPLC2_R"]); gfL, gfR = groups["GF_L"][0], groups["GF_R"][0]
    cls = np.zeros(ve.N, dtype=np.int8); cls[lp_all] = 1; cls[gfL] = 2; cls[gfR] = 2     # 0 하류, 1 LPLC2, 2 GF
    arrays = {}; meta = {"frame_ms": FRAME_MS, "recent_ms": RECENT_MS, "brain_size": [BRAIN_W, BRAIN_H], "episodes": {},
              "constants": {"h": ve.H, "theta_on_deg": ve.THETA_ON, "t_motor_ms": ve.T_MOTOR, "T_jump_ms": ve.T_JUMP, "r_stim_hz": ve.R_STIM,
                            "speeds": ve.SPEEDS, "d_on": ve.D_ON, "v_rest": ve.V_REST, "v_th": ve.V_TH},
              "fly3d": fly_names, "n_neurons": ve.N}
    for k in EPISODES:
        t0 = time.time(); ep = ve.run_episode(W, groups, k, 1)
        step_idx = {st: idx for st, idx in ep["spikes"]}
        n_f = int(ep["T"] // FRAME_MS) + 1
        fr_t = np.arange(n_f) * FRAME_MS
        s_of = np.minimum(np.round(fr_t / ve.DT).astype(int), ep["steps"] - 1)
        d = ep["dist"][s_of]; th = ep["theta"][s_of]
        now_off = [0]; now_x = []; now_y = []; now_c = []; rec_off = [0]; rec_x = []; rec_y = []
        w_now = int(FRAME_MS / ve.DT); w_rec = int(RECENT_MS / ve.DT)
        def window(s0, s1):
            parts = [step_idx[q] for q in range(max(s0, 0), s1 + 1) if q in step_idx]
            return np.unique(np.concatenate(parts)) if parts else np.empty(0, dtype=np.int64)
        for s in s_of:
            now = window(s - w_now + 1, s); now = now[ok[now]] if now.size else now
            rec = window(s - w_rec + 1, s - w_now); rec = rec[ok[rec]] if rec.size else rec
            now_x.append(PX[now]); now_y.append(PY[now]); now_c.append(cls[now]); now_off.append(now_off[-1] + now.size)
            rec_x.append(PX[rec]); rec_y.append(PY[rec]); rec_off.append(rec_off[-1] + rec.size)
        cat = lambda L, dt: (np.concatenate(L).astype(dt) if L and sum(len(a) for a in L) else np.zeros(0, dtype=dt))
        nb = int(math.ceil(ep["T"])); pop = np.zeros(nb, dtype=np.int32)
        for s, idx in ep["spikes"]:
            pop[min(int(s * ve.DT), nb - 1)] += idx.size
        p = f"k{k}_"
        arrays.update({p + "t": fr_t.astype(np.float32), p + "d": d.astype(np.float32), p + "theta": th.astype(np.float32),
                       p + "now_x": cat(now_x, np.int16), p + "now_y": cat(now_y, np.int16), p + "now_c": cat(now_c, np.int8), p + "now_off": np.array(now_off, dtype=np.int32),
                       p + "rec_x": cat(rec_x, np.int16), p + "rec_y": cat(rec_y, np.int16), p + "rec_off": np.array(rec_off, dtype=np.int32),
                       p + "vgf": ep["vgf"].astype(np.float32), p + "pop": pop})
        meta["episodes"][str(k)] = {"k": k, "v": ep["v"], "d0": ep["d0"], "t_c": ep["t_c"], "T": ep["T"], "t_on": ep["t_on"], "t_gf_first": ep["t_gf_first"],
                                    "air": list(ep["air"]) if ep["air"] else None, "passed": bool(ep["passed"]), "reason": ep["reason"],
                                    "n_spikes": int(sum(i.size for _, i in ep["spikes"])), "n_frames": n_f, "dt_ms": ve.DT}
        print(f"k={k}: frames {n_f}, now {now_off[-1]:,}, recent {rec_off[-1]:,}, passed={ep['passed']} {ep['reason']} ({time.time()-t0:.1f}s)", flush=True)
    np.savez_compressed(os.path.join(out, "episodes.npz"), **arrays)
    with open(os.path.join(out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    tot = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fs in os.walk(out) for fn in fs)
    print(f"pack done: {out}  ({tot/1e6:.1f} MB)")

if __name__ == "__main__":
    main()
