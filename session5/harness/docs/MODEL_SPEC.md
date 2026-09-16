# MODEL_SPEC — 모델·게임 규칙·출력 규격 (고정)

이 문서의 값은 바꾸지 않는다. 결과가 이상하면 값이 아니라 구현을 의심한다.
출처: Shiu et al. 2024 (Nature) 전뇌 LIF 모델과 그 numpy 재구현(flypoke)의 파라미터.

---

## 1. 뉴런·시냅스 파라미터

| 기호 | 뜻 | 값 |
|---|---|---|
| v_rest | 휴지 전위 = 리셋 전위 | −52 mV |
| v_th | 발화 임계값 | −45 mV |
| τ_m | 막 시간상수 | 20 ms |
| τ_syn | 시냅스 시간상수 | 5 ms |
| t_ref | 불응기 | 2.2 ms |
| t_delay | 시냅스 지연(전역 고정) | 1.8 ms |
| w_unit | 시냅스 1개의 크기 | 0.275 mV |
| w_ij | 뉴런 j → i 연결 가중치 | w_unit × syn_ij × sign_ij (mV) |
| dt | 적분 간격 | 0.1 ms |
| r_stim | 자극 뉴런의 포아송 발화율(기본) | 150 Hz |
| seed | 난수 시드 | 0 (④는 에피소드별 규칙, §4) |

모든 뉴런은 같은 파라미터를 쓴다. 뉴런별 차이는 오직 연결(w_ij)뿐이다.

## 2. 방정식과 이산화

연속 식:

    τ_m · dv/dt = (v_rest − v) + g + I_ext
    τ_syn · dg/dt = −g
    프리시냅스 뉴런 j 가 t 에 발화 → t + t_delay 에 g_i += w_ij
    v ≥ v_th → 스파이크, v = v_rest, t_ref 동안 정지(입력 무시)

g 는 전압 단위(mV)로 둔다(Shiu 원문의 단순화). I_ext 는 ①에서만 쓰는 상수 입력(mV)이고 나머지 단계에서는 0.

이산화(exponential Euler). 상수 a_m = exp(−dt/τ_m), a_s = exp(−dt/τ_syn). 매 스텝 순서:

    1) 지연 큐에서 이번 스텝에 도착하는 스파이크의 입력을 g 에 더한다     g += Σ_j w_ij · s_j(t − t_delay)
    2) 막전위 갱신 (불응 중인 뉴런은 v = v_rest 로 고정)                   v ← v_rest + (v − v_rest)·a_m + (g + I_ext)·(1 − a_m)
    3) 시냅스 감쇠                                                          g ← g · a_s
    4) 발화 판정: 불응이 아니고 v ≥ v_th 이면 스파이크 기록, v = v_rest, 불응 타이머 = t_ref
    5) 이번 스텝의 스파이크를 지연 큐에 넣는다(t_delay = 18 스텝 뒤 도착)

상수 입력만 있을 때(g = 0) 이 식은 정확해(exact)이므로 ①의 해석해와 맞아야 한다.

자극(포아송): 자극 대상 뉴런은 막전위 계산 결과와 무관하게 스스로 발화한다. 매 스텝 각 자극 뉴런에 대해 난수 u ∈ [0,1) 를 뽑아 u < r_stim · dt (150 Hz 면 0.015) 이면 그 스텝에 스파이크. 자극이 켜진 동안 그 뉴런의 스파이크는 이 추첨으로만 정한다(막전위가 임계값을 넘어도 따로 세지 않는다). 스파이크 뒤 리셋·불응은 똑같이 적용하고, 이 스파이크는 다른 스파이크와 똑같이 지연 큐를 거쳐 전파된다. 난수 생성기는 `numpy.random.default_rng(seed)` 하나를 쓴다.

## 3. 전뇌 조립

    N = 138_639                                       # 뉴런 수, 인덱스 0 ~ 138_638
    conn = pd.read_parquet("data/connections.parquet")   # 컬럼 pre, post, syn, sign
    w = 0.275 * conn.syn.values * conn.sign.values    # mV, 부호 포함
    W = scipy.sparse.csr_matrix((w, (conn.pre.values, conn.post.values)), shape=(N, N))   # W[pre, post]

스텝마다 발화한 뉴런 인덱스 `idx`(보통 수십~수백 개)에 대해 입력은 `W[idx].sum(axis=0)` (길이 N). 밀집 N×N 행렬을 만들지 않는다(N² = 192억).

발화율(Hz) = 스파이크 수 / 시뮬레이션 길이(s). 자극 뉴런 자신의 스파이크도 센다.

## 4. 공룡 게임 규칙 (④)

게임 시간 = 신경 시간(ms). 실시간 엔진은 없다. 에피소드를 통째로 시뮬레이션하고 결과를 GIF 로 그린다.

에피소드 = (속도 단계 k, 선인장 j) 하나. 뇌는 휴지 상태(v = v_rest, g = 0)에서 시작한다. 시드 = 1000·k + j (k = 1..K, j = 1..M).

| 기호 | 뜻 | 값 |
|---|---|---|
| h | 선인장 높이 | 10 (단위) |
| θ_on | looming 뉴런이 켜지는 각크기 | 20° |
| d_on | θ = θ_on 이 되는 거리 = h / (2·tan(θ_on/2)) | ≈ 28.4 |
| d0 | 선인장이 나타나는 거리 = d_on + 100 ms × v_k | 속도별로 다름 |
| v_k | 속도 단계(단위/ms), k = 1..5 | 0.05, 0.1, 0.25, 0.6, 2.0 |
| 기본 속도 | 통과율 기준이 되는 단계 | k = 3 (v = 0.25) |
| K, M | 속도 단계 수, 단계당 선인장 수 | 5, 3 |
| t_motor | GF 스파이크 → 점프 시작 지연 | 10 ms |
| T_jump | 공중에 머무는 시간 | 300 ms |

규칙:

1. 공룡은 x = 0 에 고정. 선인장은 t = 0 에 거리 d0 에서 나타나 d(t) = d0 − v_k·t 로 접근한다. 각크기 θ(t) = 2·atan(h / (2·d(t))). d(t) ≤ 0 (접촉 이후)은 θ = 180° 로 두어 자극을 켠 채로 둔다(판정은 t_c 에서 이미 끝났으므로 결과에 영향 없음).
2. θ(t) ≥ θ_on 인 동안 `LPLC2_L` 과 `LPLC2_R` 의 모든 뉴런을 150 Hz 포아송으로 자극한다. 그 외에는 자극 없음. (실제 LPLC2 는 팽창 속도에 반응하지만 수업용 단순화다.)
3. `GF_L` 또는 `GF_R` 의 첫 스파이크 시각을 t_s 라 한다. 공룡은 [t_s + t_motor, t_s + t_motor + T_jump] 동안 공중에 있다. 점프는 에피소드당 한 번뿐이다 — 공중일 때는 물론 착지한 뒤에 나오는 GF 스파이크도 무시한다(재점프 없음). 그래야 "느린 물체엔 너무 일찍 뛴다" 가 결과로 드러난다.
4. 선인장이 x = 0 에 닿는 시각 t_c = d0 / v_k 에 공룡이 공중이면 통과, 아니면 충돌. 실패 이유는 셋 중 하나: `no_jump`(GF 발화 없음), `too_early`(착지 후 충돌), `too_late`(점프 시작 전 충돌).
5. 에피소드는 t_c + 50 ms 까지만 시뮬레이션한다.
6. 게임은 충돌해도 끝내지 않는다. 모든 에피소드를 돌려 속도별 통과율을 낸다.

메시지: looming 발화 거리와 반사 지연이 고정이라, 느린 물체엔 너무 일찍 뛰고 빠른 물체엔 늦는다. 통과율 그래프는 나온 대로 둔다 — 좋게 보이게 상수를 조정하지 않는다.

참고(강사 레퍼런스 실측, 2026-09-16): LPLC2 자극 시작 → GF 첫 스파이크까지 5.7~6.5 ms(시드 5개). 따라서 점프 시작은 θ_on 뒤 약 16 ms 이고, 각 속도의 충돌까지 남은 시간은 d_on / v_k = 568, 284, 114, 47, 14 ms 다.

## 5. 출력 파일 규격 (verify 가 이 규격을 본다)

파일 이름은 정확히 아래와 같아야 한다. 모든 `0N_summary.json` 은 최소한 `"stage"`(정수)와 `"wall_seconds"`(실수)를 갖는다. 이어서 실행해 일부만 다시 계산했다면 `wall_seconds` 는 이번 실행의 시간이고, 전체 계산 시간은 `wall_seconds_total` 같은 별도 키에 남긴다. 아래 규격 파일 외에 이어가기용 중간 파일(예: `.npz`)과 실행 로그를 `outputs/` 에 두어도 된다 — 규격 파일 이름과 겹치지만 않으면 된다.

### ① `outputs/01_trace.png`, `outputs/01_fi_curve.csv`, `outputs/01_summary.json`

- I_ext 목록(mV): 0, 5, 7, 8, 10, 15, 20, 30. 각각 1000 ms 시뮬레이션, g 는 0(시냅스 입력 없음).
- `01_fi_curve.csv` 컬럼: `I_ext_mV`, `n_spikes`, `rate_hz`, `rate_analytic_hz`. 해석해: I_ext > 7 이면 1000 / (τ_m·ln(I_ext/(I_ext − 7)) + t_ref) [Hz], 아니면 0.
- `01_trace.png`: I_ext = 0, 10, 30 의 v(t) 처음 200 ms.
- `01_summary.json` 키: `stage`, `dt_ms`, `sim_ms`, `I_ext_mV`(목록), `rate_hz`(목록), `wall_seconds`.

### ② `outputs/02_reflex.png`, `outputs/02_summary.json`

- 뉴런 4개, 인덱스 0 = V(시각), 1 = I(억제), 2 = G(GF), 3 = J(점프 운동).
- 연결: V→G syn 50 sign +1, I→G syn 150 sign −1, G→J syn 250 sign +1. (w = 0.275 × syn × sign. G→J 가 큰 이유: 스파이크 한 발이 다음 뉴런을 넘기려면 임계값 7 mV 를 혼자 넘어야 해서다)
- 자극: V 를 150 Hz 포아송으로 500 ms. "억제 켜짐" 조건에서는 I 도 150 Hz 포아송으로 같은 500 ms. 두 조건 모두 시드 0, 시뮬레이션 500 ms.
- `02_summary.json` 키: `stage`, `sim_ms`, `spikes` = {`off`: {`V`,`I`,`G`,`J`}, `on`: {`V`,`I`,`G`,`J`}} (스파이크 수), `ratio_J_on_over_off`(on 의 J ÷ off 의 J; off 가 0 이면 null), `wall_seconds`.
- `02_reflex.png`: 두 조건의 래스터(4개 뉴런 × 500 ms).

### ③ `outputs/03_raster.png`, `outputs/03_rates.csv`, `outputs/03_summary.json`

- 두 번 시뮬레이션, 각 1000 ms, 시드 0: (a) 자극 = `LPLC2_L` ∪ `LPLC2_R` 150 Hz, (b) 무자극.
- `03_rates.csv` 컬럼: `index`, `group`(groups.json 의 그룹 이름, 없으면 빈칸, 여러 개면 `;` 로 연결), `rate_stim_hz`, `rate_ctrl_hz`. 행: (a)에서 1번이라도 발화한 뉴런 전부 + groups.json 의 모든 뉴런.
- `03_summary.json` 키: `stage`, `sim_ms`, `stim_groups`, `stim_rate_hz`, `gf` = {`GF_L`: {`stim_hz`, `ctrl_hz`}, `GF_R`: {`stim_hz`, `ctrl_hz`}}, `n_active_stim`, `n_active_ctrl`, `n_neurons`, `n_connections`, `wall_seconds`.
- `03_raster.png`: (a)의 래스터 — 자극 뉴런 일부(예: 20개), GF_L·GF_R, 그리고 자극 뉴런과 GF 를 뺀 나머지 중 발화율 상위 20개 뉴런. GF 는 눈에 띄게 표시.

### ④ `outputs/04_dino.gif`, `outputs/04_speed_vs_pass.png`, `outputs/04_log.csv`, `outputs/04_summary.json`

- `04_log.csv` 컬럼: `episode_id`, `speed_level`(1..5), `v_units_per_ms`, `d0`, `t_theta_on_ms`, `t_gf_first_ms`(GF 첫 스파이크 시각, 없으면 빈칸), `latency_ms`(t_gf_first − t_theta_on, 없으면 빈칸), `t_collision_ms`(= d0 / v), `jumped`(GF 가 한 번이라도 발화했으면 1 — 시점과 무관), `passed`(0/1), `fail_reason`(통과면 빈칸, 아니면 `no_jump` / `too_early` / `too_late` 중 하나). 15행(속도 5단계 × 선인장 3개).
- `04_speed_vs_pass.png`: x = 속도(로그축), y = 통과율(0~1), 단계별 점 + 선.
- `04_dino.gif`: 기본 속도 에피소드 1개와 최고 속도 에피소드 1개(각각 j = 1)를 이어 붙인 애니메이션. 게임 시간 10 ms 마다 1 프레임(두 에피소드 합쳐 약 42 프레임, 최소 30), 재생 10 fps(10배 슬로모션), 프레임 크기 640×360 이상. 매 프레임에 지면, 공룡(사각형, 공중이면 위로 올라감), 선인장(사각형, 위치 d(t) 에 따라 왼쪽으로 이동), 텍스트(에피소드·t·θ·GF 스파이크 여부·결과)를 그린다. 빈 프레임·정지 프레임은 실패다. matplotlib + `matplotlib.animation.PillowWriter` 로 만든다.
- `04_summary.json` 키: `stage`, `constants`(§4 표의 값), `levels` = [{`speed_level`, `v`, `n`, `passed`, `pass_rate`}], `base_speed_level`, `base_pass_rate`, `max_speed_fail_count`, `wall_seconds`.
