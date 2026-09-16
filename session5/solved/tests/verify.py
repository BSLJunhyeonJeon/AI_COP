#!/usr/bin/env python3
"""
verify.py — 단계별 산출물 검사기 (읽기 전용. 에이전트는 이 파일을 수정하지 않는다)

사용:  python tests/verify.py --stage N      (N = 1..4)
       python tests/verify.py --all           (1~4 전부 + outputs/verify_all.txt 저장)

원칙: 에이전트의 코드를 import 하지 않는다. outputs/ 의 파일만 읽어 존재 → 형식 → 수치 순서로 검사한다.
기준치는 docs/TASK.md·docs/MODEL_SPEC.md 와 같고, 아래 상수 한 곳에 모아 둔다(강사 레퍼런스 실측으로 확정, 2026-09-16).
종료코드: 요청한 단계가 전부 PASS 면 0, 아니면 1.
"""
import argparse, json, math, os, sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # harness 루트 (tests/ 의 상위)
OUT = os.path.join(ROOT, "outputs")
DATA = os.path.join(ROOT, "data")
SRC = os.path.join(ROOT, "src")
MAIN_SCRIPT = {1: "step1_neuron.py", 2: "step2_reflex.py", 3: "step3_brain.py", 4: "step4_dino.py"}

# ---------------- 기준치 (한 곳) ----------------
TAU_M, T_REF, V_GAP = 20.0, 2.2, 7.0               # ms, ms, mV (임계값 − 휴지)
I_EXT_LIST = [0, 5, 7, 8, 10, 15, 20, 30]
ANALYTIC_MIN_I, ANALYTIC_TOL = 10, 0.05             # ①: I ≥ 10 mV 에서 ±5 %
RATE_MAX = 1000.0 / T_REF                           # 454.5 Hz
S2_SIM_MS, S2_RATIO_MAX = 500, 0.20                 # ②: J(on)/J(off) ≤ 0.2
S3_SIM_MS, S3_GF_MIN_HZ, S3_ACTIVE_MIN = 1000, 50.0, 200
S3_STIM_GROUPS, S3_STIM_HZ = {"LPLC2_L", "LPLC2_R"}, 150
S3_LPLC2_RATE_RANGE = (100.0, 200.0)                # 자극 뉴런 자신의 발화율은 150 Hz 근처여야 한다
N_NEURONS, N_CONN = 138_639, 2_700_513
S4_SPEEDS = [0.05, 0.1, 0.25, 0.6, 2.0]             # k = 1..5
S4_M, S4_BASE_LEVEL, S4_BASE_PASS_MIN, S4_MAX_FAIL_MIN = 3, 3, 0.8, 1
S4_H, S4_THETA_ON_DEG = 10.0, 20.0
S4_FAIL_REASONS = {"", "no_jump", "too_early", "too_late"}
GIF_MIN_FRAMES, GIF_MIN_W, GIF_MIN_H = 30, 640, 360   # ④ GIF: 두 에피소드 × 10 ms/프레임 ≈ 42 프레임
IMG_MIN_INK = 0.005                                  # 그림에 배경이 아닌 픽셀이 0.5 % 이상 (빈 그림 금지)

results = []   # (stage, ok, message)

def rec(stage, ok, msg):
    results.append((stage, ok, msg))
    print(f"[{'PASS' if ok else 'FAIL'}] ({stage}) {msg}")

def need_script(stage):
    name = MAIN_SCRIPT[stage]
    p = os.path.join(SRC, name)
    ok = os.path.isfile(p) and os.path.getsize(p) > 0
    rec(stage, ok, f"주 스크립트 존재: src/{name}" + ("" if ok else " — 없음 (이 이름으로 만들어야 한다)"))

def need_file(stage, name):
    p = os.path.join(OUT, name)
    ok = os.path.isfile(p) and os.path.getsize(p) > 0
    rec(stage, ok, f"파일 존재: outputs/{name}" + ("" if ok else " — 없거나 비어 있음"))
    return p if ok else None

def load_json(stage, name):
    p = need_file(stage, name)
    if not p:
        return None
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        rec(stage, isinstance(d, dict), f"{name} 이 JSON 객체다")
        return d if isinstance(d, dict) else None
    except Exception as e:
        rec(stage, False, f"{name} JSON 파싱 실패: {e}")
        return None

def load_csv(stage, name, cols):
    p = need_file(stage, name)
    if not p:
        return None
    try:
        df = pd.read_csv(p)
    except Exception as e:
        rec(stage, False, f"{name} CSV 읽기 실패: {e}")
        return None
    missing = [c for c in cols if c not in df.columns]
    rec(stage, not missing, f"{name} 컬럼 확인" + (f" — 누락: {missing}" if missing else ""))
    return None if missing else df

def ink_fraction(im):
    """배경(가장 흔한 색)이 아닌 픽셀의 비율. 빈 그림이면 0 에 가깝다."""
    a = np.asarray(im.convert("L"))
    if a.size == 0:
        return 0.0
    vals, cnts = np.unique(a, return_counts=True)
    bg = vals[np.argmax(cnts)]
    return float(np.mean(np.abs(a.astype(int) - int(bg)) > 16))

def check_png(stage, name):
    p = need_file(stage, name)
    if not p:
        return
    try:
        from PIL import Image
        with Image.open(p) as im:
            w, h = im.size
            ink = ink_fraction(im)
        rec(stage, w >= 400 and h >= 300, f"{name} 크기 ≥ 400×300 (실제 {w}×{h})")
        rec(stage, ink >= IMG_MIN_INK, f"{name} 이 빈 그림이 아니다 (배경 아닌 픽셀 {ink*100:.1f} % ≥ {IMG_MIN_INK*100:.1f} %)")
    except Exception as e:
        rec(stage, False, f"{name} 이미지 열기 실패: {e}")

def check_summary_common(stage, d, name):
    ok_stage = isinstance(d.get("stage"), int) and d["stage"] == stage
    rec(stage, ok_stage, f"{name}: stage == {stage}")
    w = d.get("wall_seconds")
    rec(stage, isinstance(w, (int, float)) and w > 0, f"{name}: wall_seconds 기록됨 ({w})")

# ---------------- ① ----------------
def verify_stage1():
    s = 1
    need_script(s)
    check_png(s, "01_trace.png")
    df = load_csv(s, "01_fi_curve.csv", ["I_ext_mV", "n_spikes", "rate_hz", "rate_analytic_hz"])
    d = load_json(s, "01_summary.json")
    if df is not None:
        got = sorted(float(x) for x in df["I_ext_mV"])
        rec(s, got == [float(x) for x in I_EXT_LIST], f"I_ext 목록 = {I_EXT_LIST} (실제 {got})")
        df = df.sort_values("I_ext_mV")
        I = df["I_ext_mV"].to_numpy(float); r = df["rate_hz"].to_numpy(float)
        low = r[I <= V_GAP]
        rec(s, low.size > 0 and np.all(low == 0), f"I_ext ≤ 7 mV 에서 발화율 0 (실제 {low.tolist()})")
        rec(s, np.all(np.diff(r) >= -1e-9), "발화율이 I_ext 에 대해 단조 비감소")
        rec(s, np.all(r < RATE_MAX), f"모든 발화율 < {RATE_MAX:.1f} Hz (최대 {r.max():.1f})")
        errs = []
        for i, rate in zip(I, r):
            if i >= ANALYTIC_MIN_I:
                an = 1000.0 / (TAU_M * math.log(i / (i - V_GAP)) + T_REF)
                errs.append((i, rate, an, abs(rate - an) / an))
        ok = bool(errs) and all(e[3] <= ANALYTIC_TOL for e in errs)
        detail = ", ".join(f"I={e[0]:g}: {e[1]:.1f} vs {e[2]:.1f} ({e[3]*100:+.1f}%)" for e in errs)
        rec(s, ok, f"I_ext ≥ {ANALYTIC_MIN_I} mV 에서 해석해와 ±{ANALYTIC_TOL*100:.0f}% 이내 — {detail}")
    if d is not None:
        check_summary_common(s, d, "01_summary.json")
        rec(s, d.get("dt_ms") == 0.1, f"dt_ms == 0.1 (실제 {d.get('dt_ms')})")
        rec(s, d.get("sim_ms") == 1000, f"sim_ms == 1000 (실제 {d.get('sim_ms')})")
        rec(s, isinstance(d.get("I_ext_mV"), list) and sorted(float(x) for x in d["I_ext_mV"]) == [float(x) for x in I_EXT_LIST], "summary 의 I_ext_mV 목록 일치")
        rec(s, isinstance(d.get("rate_hz"), list) and len(d["rate_hz"]) == len(I_EXT_LIST), "summary 의 rate_hz 길이 8")

# ---------------- ② ----------------
def verify_stage2():
    s = 2
    need_script(s)
    check_png(s, "02_reflex.png")
    d = load_json(s, "02_summary.json")
    if d is None:
        return
    check_summary_common(s, d, "02_summary.json")
    rec(s, d.get("sim_ms") == S2_SIM_MS, f"sim_ms == {S2_SIM_MS} (실제 {d.get('sim_ms')})")
    sp = d.get("spikes", {})
    ok_shape = all(k in sp and all(n in sp[k] for n in "VIGJ") for k in ("off", "on"))
    rec(s, ok_shape, "spikes.off / spikes.on 에 V, I, G, J 가 모두 있다")
    if not ok_shape:
        return
    off, on = sp["off"], sp["on"]
    rec(s, off["V"] > 0 and on["V"] > 0, f"두 조건 모두 V 가 자극됨 (off V={off['V']}, on V={on['V']})")
    rec(s, off["I"] == 0, f"억제 꺼짐 조건에서 I 스파이크 0 (실제 {off['I']})")
    rec(s, on["I"] > 0, f"억제 켜짐 조건에서 I 가 자극됨 (실제 {on['I']})")
    rec(s, off["J"] >= 1, f"억제 꺼짐: J 스파이크 ≥ 1 (실제 {off['J']})")
    if off["J"] >= 1:
        ratio = on["J"] / off["J"]
        rec(s, ratio <= S2_RATIO_MAX, f"억제 켜짐: J(on)/J(off) = {on['J']}/{off['J']} = {ratio:.3f} ≤ {S2_RATIO_MAX}")
        rep = d.get("ratio_J_on_over_off")
        rec(s, isinstance(rep, (int, float)) and abs(rep - ratio) < 1e-6, f"ratio_J_on_over_off 값이 spikes 와 일치 (기록 {rep})")

# ---------------- ③ ----------------
def verify_stage3():
    s = 3
    need_script(s)
    check_png(s, "03_raster.png")
    df = load_csv(s, "03_rates.csv", ["index", "group", "rate_stim_hz", "rate_ctrl_hz"])
    d = load_json(s, "03_summary.json")
    try:
        with open(os.path.join(DATA, "groups.json"), encoding="utf-8") as f:
            groups = json.load(f)
    except Exception as e:
        rec(s, False, f"data/groups.json 을 읽을 수 없음: {e}"); return
    gfL, gfR = groups["GF_L"][0], groups["GF_R"][0]
    lplc2 = set(groups["LPLC2_L"]) | set(groups["LPLC2_R"])
    if d is not None:
        check_summary_common(s, d, "03_summary.json")
        rec(s, d.get("sim_ms") == S3_SIM_MS, f"sim_ms == {S3_SIM_MS} (실제 {d.get('sim_ms')})")
        rec(s, set(d.get("stim_groups", [])) == S3_STIM_GROUPS, f"stim_groups == {sorted(S3_STIM_GROUPS)} (실제 {d.get('stim_groups')})")
        rec(s, d.get("stim_rate_hz") == S3_STIM_HZ, f"stim_rate_hz == {S3_STIM_HZ} (실제 {d.get('stim_rate_hz')})")
        gf = d.get("gf", {})
        for side in ("GF_L", "GF_R"):
            g = gf.get(side, {})
            st, ct = g.get("stim_hz"), g.get("ctrl_hz")
            rec(s, isinstance(st, (int, float)) and st >= S3_GF_MIN_HZ, f"{side} 자극 시 발화율 ≥ {S3_GF_MIN_HZ:g} Hz (실제 {st})")
            rec(s, ct == 0, f"{side} 무자극 시 발화율 == 0 (실제 {ct})")
        rec(s, d.get("n_active_ctrl") == 0, f"무자극 시 발화 뉴런 수 == 0 (실제 {d.get('n_active_ctrl')})")
        na = d.get("n_active_stim")
        rec(s, isinstance(na, int) and na >= S3_ACTIVE_MIN, f"자극 시 발화 뉴런 수 ≥ {S3_ACTIVE_MIN} (실제 {na})")
        rec(s, d.get("n_neurons") == N_NEURONS, f"n_neurons == {N_NEURONS} (실제 {d.get('n_neurons')})")
        rec(s, d.get("n_connections") == N_CONN, f"n_connections == {N_CONN} (실제 {d.get('n_connections')})")
    if df is not None:
        idx = df["index"].astype(int)
        have = set(idx.tolist())
        all_group = set(i for v in groups.values() for i in v)
        rec(s, all_group <= have, f"groups.json 의 뉴런 {len(all_group)}개가 모두 03_rates.csv 에 있다 (누락 {len(all_group - have)})")
        rec(s, not idx.duplicated().any(), "03_rates.csv 의 index 중복 없음")
        rec(s, bool((df["rate_ctrl_hz"] == 0).all()), "03_rates.csv 의 rate_ctrl_hz 가 전부 0")
        n_pos = int((df["rate_stim_hz"] > 0).sum())
        if d is not None and isinstance(d.get("n_active_stim"), int):
            rec(s, n_pos == d["n_active_stim"], f"csv 에서 rate_stim_hz > 0 인 행 수({n_pos}) == summary 의 n_active_stim({d['n_active_stim']})")
        for name, gi in (("GF_L", gfL), ("GF_R", gfR)):
            row = df[idx == gi]
            v = float(row["rate_stim_hz"].iloc[0]) if len(row) else None
            rec(s, v is not None and v >= S3_GF_MIN_HZ, f"csv 의 {name}(index {gi}) rate_stim_hz ≥ {S3_GF_MIN_HZ:g} (실제 {v})")
        lp = df[idx.isin(lplc2)]["rate_stim_hz"]
        m = float(lp.mean()) if len(lp) else float("nan")
        rec(s, len(lp) == len(lplc2) and S3_LPLC2_RATE_RANGE[0] <= m <= S3_LPLC2_RATE_RANGE[1],
            f"LPLC2 자극 뉴런({len(lp)}/{len(lplc2)}개)의 평균 발화율이 150 Hz 근처 ({m:.1f} Hz, 허용 {S3_LPLC2_RATE_RANGE})")

# ---------------- ④ ----------------
def verify_stage4():
    s = 4
    need_script(s)
    check_png(s, "04_speed_vs_pass.png")
    gif = need_file(s, "04_dino.gif")
    if gif:
        try:
            from PIL import Image
            with Image.open(gif) as im:
                n = getattr(im, "n_frames", 1); w, h = im.size
                rec(s, n >= GIF_MIN_FRAMES, f"04_dino.gif 프레임 수 ≥ {GIF_MIN_FRAMES} (실제 {n})")
                rec(s, w >= GIF_MIN_W and h >= GIF_MIN_H, f"04_dino.gif 프레임 크기 ≥ {GIF_MIN_W}×{GIF_MIN_H} (실제 {w}×{h})")
                picks = sorted(set([0, n // 4, n // 2, (3 * n) // 4, n - 1]))
                frames = []
                for i in picks:
                    im.seek(i); frames.append(np.asarray(im.convert("L"), dtype=int))
                inks = [ink_fraction(Image.fromarray(f.astype(np.uint8))) for f in frames]
                rec(s, min(inks) >= IMG_MIN_INK, f"04_dino.gif 프레임이 비어 있지 않다 (배경 아닌 픽셀 최소 {min(inks)*100:.1f} %)")
                diffs = [float(np.mean(np.abs(frames[i] - frames[i + 1]) > 16)) for i in range(len(frames) - 1)]
                rec(s, max(diffs) > 0.001, f"04_dino.gif 장면이 움직인다 (프레임 간 달라진 픽셀 최대 {max(diffs)*100:.2f} %)")
        except Exception as e:
            rec(s, False, f"04_dino.gif 검사 실패: {e}")
    cols = ["episode_id", "speed_level", "v_units_per_ms", "d0", "t_theta_on_ms", "t_gf_first_ms", "latency_ms",
            "t_collision_ms", "jumped", "passed", "fail_reason"]
    df = load_csv(s, "04_log.csv", cols)
    d = load_json(s, "04_summary.json")
    d_on = S4_H / (2.0 * math.tan(math.radians(S4_THETA_ON_DEG) / 2.0))
    if df is not None:
        n_expected = len(S4_SPEEDS) * S4_M
        rec(s, len(df) == n_expected, f"에피소드 수 == {n_expected} (실제 {len(df)})")
        lv = df["speed_level"].astype(int)
        counts = lv.value_counts().to_dict()
        rec(s, all(counts.get(k, 0) == S4_M for k in range(1, len(S4_SPEEDS) + 1)), f"속도 단계 1..5 각각 {S4_M}개 (실제 {dict(sorted(counts.items()))})")
        v_ok = True
        for k, v in enumerate(S4_SPEEDS, start=1):
            vv = df.loc[lv == k, "v_units_per_ms"].astype(float)
            if len(vv) and not np.allclose(vv, v, rtol=1e-6, atol=1e-9):
                v_ok = False
        rec(s, v_ok, f"단계별 속도 == {S4_SPEEDS}")
        d0_ok = True
        for k, v in enumerate(S4_SPEEDS, start=1):
            dd = df.loc[lv == k, "d0"].astype(float)
            if len(dd) and not np.allclose(dd, d_on + 100.0 * v, rtol=1e-3):
                d0_ok = False
        rec(s, d0_ok, f"d0 == d_on + 100 ms × v (d_on = {d_on:.2f})")
        tc = df["t_collision_ms"].astype(float); expect_tc = df["d0"].astype(float) / df["v_units_per_ms"].astype(float)
        rec(s, bool(np.allclose(tc, expect_tc, rtol=1e-3)), "t_collision_ms == d0 / v")
        ton = df["t_theta_on_ms"].astype(float)
        rec(s, bool(np.all(np.abs(ton - 100.0) <= 1.0)), f"t_theta_on_ms ≈ 100 ms (실제 {ton.min():.1f}~{ton.max():.1f})")
        pj = df["passed"].astype(int); jm = df["jumped"].astype(int)
        rec(s, set(pj.unique()) <= {0, 1} and set(jm.unique()) <= {0, 1}, "jumped / passed 가 0 또는 1")
        fr = df["fail_reason"].fillna("").astype(str)
        rec(s, set(fr.unique()) <= S4_FAIL_REASONS, f"fail_reason 값이 {sorted(S4_FAIL_REASONS)} 안 (실제 {sorted(fr.unique())})")
        rec(s, bool(((pj == 1) == (fr == "")).all()), "passed == 1 인 행만 fail_reason 이 빈칸")
        lat = pd.to_numeric(df["latency_ms"], errors="coerce")
        rec(s, lat.notna().sum() >= 1 and bool((lat.dropna() > 0).all()), f"latency_ms 기록 {int(lat.notna().sum())}개, 모두 > 0 (범위 {lat.min():.1f}~{lat.max():.1f} ms)")
        rec(s, bool(((jm == 1) == lat.notna()).all()), "jumped == 1 인 행에만 latency_ms 가 있다")
        base = df[lv == S4_BASE_LEVEL]
        base_rate = float(base["passed"].astype(int).mean()) if len(base) else 0.0
        rec(s, base_rate >= S4_BASE_PASS_MIN, f"기본 속도(k={S4_BASE_LEVEL}) 통과율 {base_rate:.2f} ≥ {S4_BASE_PASS_MIN}")
        top = df[lv == len(S4_SPEEDS)]
        fails = int((top["passed"].astype(int) == 0).sum())
        rec(s, fails >= S4_MAX_FAIL_MIN, f"최고 속도(k={len(S4_SPEEDS)}) 실패 {fails}개 ≥ {S4_MAX_FAIL_MIN}")
        if d is not None:
            check_summary_common(s, d, "04_summary.json")
            rec(s, isinstance(d.get("constants"), dict) and len(d["constants"]) > 0, "constants 기록됨")
            levels = d.get("levels")
            ok_levels = isinstance(levels, list) and len(levels) == len(S4_SPEEDS)
            if ok_levels:
                for L in levels:
                    k = int(L.get("speed_level", -1)); sub = df[lv == k]
                    if len(sub) == 0 or L.get("n") != len(sub) or L.get("passed") != int(sub["passed"].astype(int).sum()) \
                            or abs(float(L.get("pass_rate", -1)) - float(sub["passed"].astype(int).mean())) > 1e-6:
                        ok_levels = False
            rec(s, ok_levels, "summary.levels 가 04_log.csv 와 일치(n, passed, pass_rate)")
            rec(s, d.get("base_speed_level") == S4_BASE_LEVEL, f"base_speed_level == {S4_BASE_LEVEL}")
            rec(s, isinstance(d.get("base_pass_rate"), (int, float)) and abs(d["base_pass_rate"] - base_rate) < 1e-6, f"base_pass_rate == {base_rate:.2f}")
            rec(s, d.get("max_speed_fail_count") == fails, f"max_speed_fail_count == {fails}")

STAGES = {1: verify_stage1, 2: verify_stage2, 3: verify_stage3, 4: verify_stage4}

def main():
    ap = argparse.ArgumentParser(description="session5 harness 산출물 검사기")
    ap.add_argument("--stage", type=int, choices=[1, 2, 3, 4])
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if not a.stage and not a.all:
        ap.error("--stage N 또는 --all 을 지정하세요")
    todo = [1, 2, 3, 4] if a.all else [a.stage]
    print(f"harness 루트: {ROOT}")
    for st in todo:
        print(f"\n===== 단계 {st} =====")
        try:
            STAGES[st]()
        except Exception as e:
            rec(st, False, f"검사 중 예외: {type(e).__name__}: {e}")
    print("\n===== 요약 =====")
    all_ok = True
    for st in todo:
        rs = [r for r in results if r[0] == st]
        n_ok = sum(1 for r in rs if r[1]); ok = n_ok == len(rs) and len(rs) > 0
        all_ok &= ok
        print(f"단계 {st}: {'PASS' if ok else 'FAIL'} ({n_ok}/{len(rs)} 항목 통과)")
    print(f"\n전체: {'PASS' if all_ok else 'FAIL'}")
    if a.all:
        try:
            os.makedirs(OUT, exist_ok=True)
            with open(os.path.join(OUT, "verify_all.txt"), "w", encoding="utf-8") as f:
                for st in todo:
                    f.write(f"===== 단계 {st} =====\n")
                    for r in results:
                        if r[0] == st:
                            f.write(f"[{'PASS' if r[1] else 'FAIL'}] {r[2]}\n")
                f.write(f"\n전체: {'PASS' if all_ok else 'FAIL'}\n")
            print("→ outputs/verify_all.txt 에 저장했습니다.")
        except Exception as e:
            print(f"(verify_all.txt 저장 실패: {e})")
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
