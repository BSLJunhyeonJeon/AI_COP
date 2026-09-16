"""
lif.py — 공용 LIF 뉴런/네트워크 시뮬레이터 (docs/MODEL_SPEC.md §1~§3 구현)

①~④ 모든 단계가 이 모듈의 `simulate()` 하나를 쓴다. 뉴런 파라미터는 전부 여기(§1)에 있고 바꾸지 않는다.

이산화(exponential Euler), 매 스텝 순서 (MODEL_SPEC §2):
    1) 지연 큐에서 이번 스텝에 도착하는 스파이크의 입력을 g 에 더한다
    2) 막전위 갱신 (불응 중인 뉴런은 v = v_rest 로 고정)
    3) 시냅스 감쇠 g ← g·a_s
    4) 발화 판정: 불응이 아니고 v ≥ v_th 이면 스파이크, v = v_rest, 불응 타이머 = t_ref
    5) 이번 스텝의 스파이크를 지연 큐에 넣는다 (18 스텝 뒤 도착)

자극 뉴런(포아송)은 막전위와 무관하게 스스로 발화한다: 매 스텝 u < r_stim·dt 이면 스파이크.
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
import pandas as pd
import scipy.sparse as sp

# ---------------- §1 파라미터 (고정) ----------------
V_REST = -52.0      # mV, 휴지 전위 = 리셋 전위
V_TH = -45.0        # mV, 발화 임계값
TAU_M = 20.0        # ms, 막 시간상수
TAU_SYN = 5.0       # ms, 시냅스 시간상수
T_REF = 2.2         # ms, 불응기
T_DELAY = 1.8       # ms, 시냅스 지연(전역 고정)
W_UNIT = 0.275      # mV, 시냅스 1개의 크기
DT = 0.1            # ms, 적분 간격
R_STIM = 150.0      # Hz, 자극 뉴런의 포아송 발화율(기본)
SEED = 0

N_NEURONS = 138_639
DELAY_STEPS = int(round(T_DELAY / DT))   # 18
REF_STEPS = int(round(T_REF / DT))       # 22
A_M = float(np.exp(-DT / TAU_M))
A_S = float(np.exp(-DT / TAU_SYN))

# 작업 루트 기준 상대경로 (이 파일 = src/lif.py)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "outputs")

_EMPTY = np.empty(0, dtype=np.int64)


# ---------------- §3 전뇌 조립 ----------------
def load_groups() -> dict:
    with open(os.path.join(DATA_DIR, "groups.json"), encoding="utf-8") as f:
        return json.load(f)


def load_connections() -> pd.DataFrame:
    return pd.read_parquet(os.path.join(DATA_DIR, "connections.parquet"))


def build_weight_matrix(pre, post, syn, sign, n: int = N_NEURONS) -> sp.csr_matrix:
    """W[pre, post] = w_unit × syn × sign (mV). 행 = 프리시냅스 뉴런."""
    w = W_UNIT * np.asarray(syn, dtype=np.float64) * np.asarray(sign, dtype=np.float64)
    W = sp.csr_matrix((w, (np.asarray(pre, dtype=np.int64), np.asarray(post, dtype=np.int64))), shape=(n, n))
    W.sort_indices()
    return W


def load_brain():
    """전뇌 가중치 행렬 W (CSR, N×N) 와 연결 수를 돌려준다."""
    conn = load_connections()
    W = build_weight_matrix(conn["pre"].to_numpy(), conn["post"].to_numpy(),
                            conn["syn"].to_numpy(), conn["sign"].to_numpy())
    return W, int(len(conn))


def _row_sum(indptr, indices, data, idx, n):
    """W[idx].sum(axis=0) 과 같다. 발화한 행(idx)의 항목만 모아 열 방향으로 합친다 (밀집 행렬 없음)."""
    starts = indptr[idx]
    lens = indptr[idx + 1] - starts
    total = int(lens.sum())
    if total == 0:
        return None
    # 각 행의 항목 위치를 하나의 인덱스 배열로 펼친다
    offs = np.repeat(starts - (np.cumsum(lens) - lens), lens) + np.arange(total)
    return np.bincount(indices[offs], weights=data[offs], minlength=n)


# ---------------- §2 시뮬레이션 ----------------
def simulate(W, n: int, sim_ms: float, *,
             stim_idx=None, stim_on=None, stim_rate_hz: float = R_STIM, seed: int = SEED,
             I_ext: float = 0.0, record_v_idx=None, progress_every: int = 0, log=print) -> dict:
    """
    W          : scipy.sparse CSR (n×n), W[pre, post] mV. None 이면 시냅스 없음(①).
    n          : 뉴런 수
    sim_ms     : 시뮬레이션 길이(ms)
    stim_idx   : 포아송 자극 대상 뉴런 인덱스 배열 (None 이면 자극 없음)
    stim_on    : None(항상 켜짐) 또는 길이 n_steps 의 bool 배열(스텝별 자극 켜짐 여부, ④용)
    I_ext      : 상수 입력(mV, ①에서만 사용)
    record_v_idx: 막전위를 기록할 뉴런 인덱스 목록 (None 이면 기록 안 함)
    반환: dict(spike_steps, spike_ids, counts, rates_hz, v_trace, t_ms, n_steps, wall_seconds)
    """
    t0 = time.perf_counter()
    n_steps = int(round(sim_ms / DT))
    rng = np.random.default_rng(seed)

    v = np.full(n, V_REST, dtype=np.float64)
    g = np.zeros(n, dtype=np.float64)
    ref_left = np.zeros(n, dtype=np.int64)          # 남은 불응 스텝 수 (>0 이면 불응 중)
    one_minus_am = 1.0 - A_M

    if W is not None:
        W = sp.csr_matrix(W)
        indptr, indices, data = W.indptr.astype(np.int64), W.indices.astype(np.int64), W.data.astype(np.float64)
    else:
        indptr = indices = data = None

    if stim_idx is not None:
        stim_idx = np.asarray(stim_idx, dtype=np.int64)
        if stim_idx.size == 0:
            stim_idx = None
    p_stim = stim_rate_hz * DT / 1000.0                 # 150 Hz → 0.015

    # 지연 큐: 크기 DELAY_STEPS+1 의 링 버퍼. 스텝 t 에 읽고(t%Q) 나서 쓴다((t+D)%Q).
    Q = DELAY_STEPS + 1
    queue = [_EMPTY] * Q

    rec = None
    if record_v_idx is not None:
        record_v_idx = np.asarray(record_v_idx, dtype=np.int64)
        rec = np.empty((n_steps, record_v_idx.size), dtype=np.float64)

    spike_steps, spike_ids = [], []
    counts = np.zeros(n, dtype=np.int64)

    for t in range(n_steps):
        # 1) 지연 큐 도착분을 g 에 더한다
        arrivals = queue[t % Q]
        if arrivals.size and indptr is not None:
            inc = _row_sum(indptr, indices, data, arrivals, n)
            if inc is not None:
                g += inc

        # 2) 막전위 갱신 (v_rest + (v−v_rest)·a_m + (g+I)(1−a_m) 와 대수적으로 같은 형태)
        refr = ref_left > 0
        v += (V_REST - v + g + I_ext) * one_minus_am
        v[refr] = V_REST
        if rec is not None:
            rec[t] = v[record_v_idx]

        # 3) 시냅스 감쇠
        g *= A_S

        # 4) 발화 판정
        spk = (v >= V_TH) & ~refr
        if stim_idx is not None and (stim_on is None or stim_on[t]):
            # 자극 뉴런은 막전위와 무관하게 포아송으로 스스로 발화한다
            u = rng.random(stim_idx.size)
            spk[stim_idx] = False
            spk[stim_idx[u < p_stim]] = True
        idx = np.flatnonzero(spk)
        if idx.size:
            v[idx] = V_REST
            ref_left[idx] = REF_STEPS
            counts[idx] += 1
            spike_steps.append(np.full(idx.size, t, dtype=np.int64))
            spike_ids.append(idx)
        ref_left[refr] -= 1

        # 5) 지연 큐에 넣는다 (18 스텝 뒤 도착)
        queue[(t + DELAY_STEPS) % Q] = idx

        if progress_every and (t + 1) % progress_every == 0:
            log(f"  step {t + 1}/{n_steps} ({(t + 1) * DT:.0f} ms)  누적 스파이크 {int(counts.sum())}  "
                f"경과 {time.perf_counter() - t0:.1f}s")

    spike_steps = np.concatenate(spike_steps) if spike_steps else _EMPTY.copy()
    spike_ids = np.concatenate(spike_ids) if spike_ids else _EMPTY.copy()
    return dict(
        spike_steps=spike_steps, spike_ids=spike_ids, spike_times_ms=spike_steps * DT,
        counts=counts, rates_hz=counts / (sim_ms / 1000.0),
        v_trace=rec, t_ms=np.arange(n_steps) * DT, n_steps=n_steps,
        wall_seconds=time.perf_counter() - t0,
    )


def setup_matplotlib():
    """그림의 한국어 라벨용 폰트 설정 (있는 폰트만 쓴다, 없으면 기본 폰트 유지)."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager
    names = {f.name for f in font_manager.fontManager.ttflist}
    for cand in ("Malgun Gothic", "NanumGothic", "Noto Sans CJK KR", "AppleGothic"):
        if cand in names:
            matplotlib.rcParams["font.family"] = cand
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


def analytic_rate_hz(I_ext: float) -> float:
    """상수 입력 I_ext(mV) 에 대한 LIF 발화율 해석해 (MODEL_SPEC §5-①)."""
    gap = V_TH - V_REST
    if I_ext <= gap:
        return 0.0
    return 1000.0 / (TAU_M * np.log(I_ext / (I_ext - gap)) + T_REF)
