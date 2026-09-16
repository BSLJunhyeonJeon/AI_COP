# 5회차 스펙 — 프로젝트 루트(하네스) 구축: 에이전트에게 초파리 전뇌 시뮬레이션을 만들게 하기

> 대상: 이 스펙을 구현하는 클로드 + 사람(준현).
> 전제: 레포 루트 `CONVENTIONS.md` 가 상위 규칙. 충돌 시 CONVENTIONS 우선 — 단, §8 의 예외 2건은 승인 후 이 스펙이 적용한다.
> 범위: `session5/` 신규 생성. 참가자용 노트북은 없다(코드는 참가자의 에이전트가 쓴다).
> 금지: 스펙에 없는 기능·옵션 임의 추가. `harness/` 안에 정답·힌트 코드 넣기. 실시간 게임 엔진.
> 작업 후: 무엇을 만들었는지 + 사람이 확인하는 법 + 직접 돌려본 범위를 보고한다.
> 작성일: 2026-09-16. 수치는 같은 날 강사 레퍼런스 실측으로 확정됨(§2·§5).

---

## 0. 이 회차의 한 문장

좋은 프로젝트 루트는 싼 모델도 일하게 만든다.

참가자는 코드를 쓰지 않는다. 각자의 에이전트(Claude Code / Codex / Cowork / Colab Gemini 등)에 하네스 폴더를 물리고 한 문장으로 시작시킨다. 우리는 에이전트가 성공할 수밖에 없는 폴더를 만든다 — 데이터·파라미터·통과 조건·검증기를 전부 폴더 안에 둔다. 인터넷은 필요 없다.

우리 자신도 참가자와 똑같이 한다. 하네스 폴더를 만들고 → 복사해서 → 클로드 코드에게 자동화된 업무를 지시하고 → 통과를 확인한 뒤 → 원본 하네스 폴더와 구현 완료 폴더를 둘 다 커밋·푸시한다. 그 다음 "프로젝트용 하네스 구축" HTML 문서를 만든다.

원안(2·3회차 로드맵의 STEP5 "적용 — 내 연구에")은 수업 마지막 10분 "이 뼈대를 내 연구 폴더로 옮기기"로 회수한다.

---

## 1. 산출물 트리

```
session5/
├─ README.md                 # 사람용 — harness/ 와 solved/ 가 무엇인지, 참가자 사용법
├─ session5_lecture.html     # (2차 산출물) 프로젝트용 하네스 구축 문서 — §13
├─ harness/                  # ★ 원본 하네스 폴더. 참가자는 이 폴더를 복사해 별도 위치에서 작업한다
│  ├─ README.md              #   사람용 — 폴더를 에이전트에 물리는 법 + 첫 문장(붙여넣기용)
│  ├─ AGENTS.md              #   에이전트용 헌법(범용). 지시의 단일 출처
│  ├─ CLAUDE.md              #   한 줄: @AGENTS.md  (Claude Code 가 자동 로드)
│  ├─ docs/
│  │  ├─ TASK.md             #   과제 4단계 + 단계별 산출물 파일명 + 통과 조건
│  │  ├─ MODEL_SPEC.md       #   LIF 식·파라미터 표·시냅스/자극 규칙·공룡 게임 규칙·출력 규격
│  │  └─ DATA.md             #   데이터 파일 스키마·출처·라이선스·로딩 예시
│  ├─ data/                  #   커밋 대상(예외 승인 필요, §8). 합계 ≤ 15 MB
│  │  ├─ connections.parquet #   pre, post, syn, sign — 시냅스 ≥5 연결 2,700,513 행
│  │  ├─ neurons.csv.gz      #   index, root_id, cell_class, cell_type, side … (1.5 MB)
│  │  └─ groups.json         #   뉴런 그룹 → 인덱스 목록 (LPLC2_L/R, LC4_L/R, GF_L/R, 폴백: sugar_GRN, bitter_GRN, ingestion_MN)
│  ├─ tests/verify.py        #   python tests/verify.py --stage N → PASS/FAIL + 이유
│  ├─ src/  outputs/         #   (비움) 에이전트가 채운다
│  ├─ requirements.txt       #   numpy scipy pandas pyarrow matplotlib pillow — 핀은 실측 후
│  └─ setup_env.bat / .sh    #   conda env: ai_cop_session5
├─ tools/build_data.py       # 강사용 — harness/data 3종을 원본에서 재생성(출처 추적용)
└─ solved/                   # ★ harness/ 를 복사해 클로드 코드가 4단계를 완료한 폴더(그대로 커밋)
   ├─ (harness/ 와 동일 구조 + src/step1..4, outputs/01..04, outputs/verify_all.txt)
   └─ RUN_LOG.md             #   모델·시작/종료 시각·verify 실행 횟수·막혔던 곳·총 소요 시간
```

참가자는 `harness/` 만 복사해 자기 폴더에서 작업한다(`solved/` 가 같은 루트에 있으면 에이전트가 베낀다). 그래서 AGENTS.md 에 "작업 루트 밖을 읽지 않는다" 규칙을 둔다. `solved/` 는 수업 후 참고용이자 "이 하네스로 클로드 코드가 N분 만에 통과했다"는 증거다.

---

## 2. 데이터 (검증된 사실 — 2026-09-16 실측)

- 출처: FlyWire v783 (Dorkenwald et al. 2024, Nature; 데이터 CC BY 4.0). 원본 파일은 Shiu et al. 2024 코드 레포 `philshiu/Drosophila_brain_model`(MIT)의 `Connectivity_783.parquet`(96 MB).
- 원본 실측: 15,091,983 행(시냅스 1개짜리 연결까지 전부), 뉴런 138,639개(인덱스 0~138,638). 컬럼 `Presynaptic_Index` / `Postsynaptic_Index` / `Connectivity`(시냅스 수) / `Excitatory`(+1/−1). 부호 분포 +1: 9,059,302 행, −1: 6,032,681 행. 총 시냅스 54,492,922.
- 가공: 시냅스 ≥ 5 연결만 남김 → 2,700,513 행. 컬럼 `pre`(int32) `post`(int32) `syn`(int16) `sign`(int8). zstd parquet 10.1 MB(csv.gz 로 하면 14.4 MB).
- 뉴런 그룹: `flyconnectome/flywire_annotations`(Schlegel et al. 2024, 2026-07-21 커밋본)의 `Supplemental_file1_neuron_annotations.tsv`(139,248 행) 에서 추출. 실측: LPLC2_L 108, LPLC2_R 102, LC4_L 54, LC4_R 50, GF_L 1(index 57246), GF_R 1(index 108748); 폴백 sugar_GRN 129, bitter_GRN 65, ingestion_MN 28(`ingestion_motor_neuron`, MN9 포함 운동뉴런군). 138,639개 중 138,625개가 주석과 매칭.
- 인덱스 ↔ root_id: `Completeness_783.csv` 행 순서 = 인덱스임을 pre/post 양쪽에서 검증. (pre, post) 중복 0. `data/` 합계 11.6 MB.
- 도망 회로 배선: 같은 쪽 LPLC2 → GF_L 305 시냅스, → GF_R 539 시냅스(LC4 는 329, 428). 반대쪽 0.
- 레퍼런스 실측(2026-09-16, 이 세션의 2코어 CPU): LPLC2 210개를 150 Hz 로 1 s 자극 → GF_L 264 Hz, GF_R 349 Hz, 발화 뉴런 1,519개, 총 스파이크 94,695개, wall 15.5 s. 무자극 1 s → 발화 0, wall 8.3 s. 자극 시작 → GF 첫 스파이크 5.7~6.5 ms(시드 5개). 도망 회로 재현 확인 → 공룡 게임으로 확정, 설탕물은 폴백 데이터로만 남긴다.
- MaleCNS v1.0(2026-09-05 구글 공개, 16.6만 뉴런)은 쓰지 않는다 — 용량이 크고 검증된 LIF 파라미터가 없다. 도입 이야기로만 쓴다.

---

## 3. 모델 (고정 — Shiu 2024 / flypoke 값. 바꾸지 않는다)

| 항목 | 값 |
|---|---|
| 뉴런 모델 | LIF (leaky integrate-and-fire), 전압 단위의 지수 감쇠 시냅스 |
| 휴지 전위 = 리셋 전위 | −52 mV |
| 발화 임계값 | −45 mV |
| 막 시간상수 τ_m | 20 ms |
| 시냅스 시간상수 τ_syn | 5 ms |
| 불응기 | 2.2 ms |
| 시냅스 지연 | 1.8 ms (전역 고정) |
| 시냅스 1개의 크기 | 0.275 mV × sign |
| 연결 가중치 | w_ij = 0.275 mV × syn_ij × sign_ij |
| 최소 시냅스 수 | 5 (데이터에서 이미 걸러짐) |
| 적분 | exponential Euler, dt = 0.1 ms |
| 자극 | 지정 뉴런 그룹에 독립 포아송 스파이크, 기본 150 Hz |
| 시드 | 0 고정 |

방정식: τ_m·dv/dt = (v_rest − v) + g + I_ext,  τ_syn·dg/dt = −g.
프리시냅스 뉴런 j 가 시각 t 에 발화하면 t + 1.8 ms 에 g_i += w_ij. v ≥ −45 mV 이면 스파이크 → v = −52 mV, 2.2 ms 동안 정지.
(Shiu 원문처럼 g 를 전압 단위로 두는 단순화를 그대로 따른다. 이산화 식은 MODEL_SPEC.md §2.)

---

## 4. 과제 4단계 (TASK.md 의 원본)

각 단계는 `python tests/verify.py --stage N` 이 PASS 해야 다음으로 간다. 모든 단계는 `outputs/0N_summary.json` 에 `stage`, `wall_seconds` 를 기록한다.

| 단계 | 내용 | 산출물(파일명 고정) | 통과 조건 | 예상 |
|---|---|---|---|---|
| ① 뉴런 1개 | LIF 하나에 상수 입력 I_ext 를 넣어 f-I 곡선 | `src/step1_neuron.py` → `outputs/01_trace.png`, `outputs/01_fi_curve.csv`, `outputs/01_summary.json` | I_ext ≤ 7 mV 에서 스파이크 0; I_ext 증가 시 발화율 단조 증가; I_ext ≥ 10 mV 에서 해석해 f = 1/(τ_m·ln(I/(I−7)) + 2.2 ms) 와 5 % 이내 | 10분 |
| ② 반사궁 4뉴런 | V(시각) → G(GF) → J(점프) 사슬 + 억제 뉴런 I → G 토글 (V→G 50, I→G 150, G→J 250 시냅스) | `src/step2_reflex.py` → `outputs/02_reflex.png`, `outputs/02_summary.json` | I 꺼짐: J 발화 ≥ 1; I 켜짐: J 발화 수 ≤ I 꺼짐의 20 % (레퍼런스 시드 0: 28 → 0) | 10분 |
| ③ 전뇌 장착 | `data/` 로드 → 희소 W → LPLC2 좌·우 150 Hz 1 s 자극 vs 무자극 1 s | `src/step3_brain.py` → `outputs/03_raster.png`, `outputs/03_rates.csv`, `outputs/03_summary.json` | GF_L·GF_R 자극 시 발화율 ≥ 50 Hz(레퍼런스 264/349); 무자극 시 0 Hz; wall time 기록 | 20분 |
| ④ 공룡 게임 | 속도 5단계 × 선인장 3개 에피소드 → looming 인코딩 → 시뮬 → GF 스파이크 = 점프 → 판정·GIF | `src/step4_dino.py` → `outputs/04_dino.gif`, `outputs/04_speed_vs_pass.png`, `outputs/04_log.csv`, `outputs/04_summary.json` | 기본 속도 통과율 ≥ 0.8; 최고 속도에서 실패 ≥ 1(속도 상한이 보임); 선인장별 반응 지연 기록 | 20분 |

①의 해석해는 v 가 임계값에 닿는 시간 T = τ_m·ln(I_ext/(I_ext − 7 mV)) 에 불응기 2.2 ms 를 더한 주기의 역수다(임계값 − 휴지 = 7 mV). dt = 0.1 ms 이산화 오차는 1~2 % 수준이라 5 % 허용치 안에 든다.

---

## 5. 공룡 게임 규칙 (MODEL_SPEC.md §4 의 원본)

- 게임 시간 = 신경 시간(ms). 실시간 엔진 없음. 에피소드를 통째로 시뮬레이션한 뒤 GIF 로 렌더한다.
- 에피소드 = (속도 단계 k, 선인장 j) 하나. 뇌는 휴지 상태에서 시작한다. 시드 = 1000·k + j.
- 공룡은 x = 0 고정. 선인장은 거리 d0 에서 나타나 속도 v_k(단위/ms)로 접근: d(t) = d0 − v_k·t. 높이 h.
- 각크기 θ(t) = 2·atan(h / (2·d(t))). θ(t) ≥ θ_on 이면 LPLC2 좌·우 그룹에 150 Hz 포아송 자극, 아니면 0. (실제 LPLC2 는 팽창 속도에 반응하지만 수업용 단순화. θ_on = 20°, h = 10 → d_on ≈ 28.4)
- 점프: GF 좌 또는 우의 첫 스파이크 시각 t_s → 구간 [t_s + t_motor, t_s + t_motor + T_jump] 동안 공중. t_motor = 10 ms, T_jump = 300 ms. 공중일 때 GF 스파이크는 무시.
- 판정: 선인장이 x = 0 에 닿는 시각 t_c = d0 / v_k 에 공중이면 통과, 아니면 충돌. 에피소드는 t_c + 50 ms 까지만 돌린다.
- K = 5 단계(v = 0.05, 0.1, 0.25, 0.6, 2.0 단위/ms), 단계당 M = 3 개(사전 점검 후 5 → 3 으로 축소, §9-4), 기본 속도 k = 3. 선인장은 θ_on 도달 100 ms 전 위치(d0 = d_on + 100 ms × v_k)에서 나타난다. 예상: k = 1 은 너무 일찍 뛰어 실패(θ_on 뒤 충돌까지 568 ms, 점프는 16~316 ms), k = 2~4 통과, k = 5 는 늦어서 실패(충돌 14 ms, 점프 시작 16 ms). 에피소드 15개의 총 시뮬레이션 시간 ≈ 5.3 s → 레퍼런스 속도로 1~2분.
- θ 임계 방식은 발화 거리 d_on 이 속도와 무관하다. 그래서 너무 느린 물체에는 너무 일찍 뛰어 착지 후 부딪히고, 너무 빠른 물체에는 늦는다. 속도 단계는 통과 구간을 가운데 두고 양끝이 보이게 잡되, 그래프는 나온 대로 둔다(좋게 보이게 조정하지 않는다).
- 산출: `04_log.csv`(cactus_id, speed_level, v, t_theta_on_ms, t_gf_first_ms, latency_ms, jumped, passed), `04_speed_vs_pass.png`(속도 vs 통과율), `04_dino.gif`(matplotlib PillowWriter; 기본 속도 1개 + 최고 속도 1개 에피소드), `04_summary.json`.
- 메시지: 반사 지연과 발화 거리가 고정이라 어느 속도부터 반드시 실패한다 → "커넥톰은 반사를 재현하지, 속도를 학습하진 못한다".

---

## 6. AGENTS.md 규칙 (요지 — 본문은 `harness/AGENTS.md`)

읽기 순서(TASK → MODEL_SPEC → DATA), 한 단계씩, verify 통과 전 다음 단계 금지, 작업 루트 밖 접근 금지, `data/` 읽기 전용, 인터넷·다운로드 금지, requirements 외 패키지 금지, 상대경로, 산출물 파일명 고정, 시드 0, 파라미터 변경 금지, 한국어 설명/영어 식별자, 스펙 외 기능 금지(질문은 `outputs/QUESTIONS.md`), 실패 시 오류 전문 보고와 3회 반복 금지, wall time 기록, 단계별 완료 보고 형식.

---

## 7. verify.py 규격

- 호출: `python tests/verify.py --stage N`(N = 1..4), `--all`. 종료코드 0 = 전부 PASS.
- 검사 순서: 산출물 존재 → 형식(컬럼·키) → 수치 조건(§4). 항목마다 PASS/FAIL 과 이유 한 줄.
- 에이전트의 코드를 import 하지 않는다. 산출물 파일만 본다(구현 자유도 보장).
- 의존성은 requirements.txt 안에서만. 기준치 상수는 파일 상단 한 곳에 모은다.
- 기준치(② 비율 0.2, ③ GF ≥ 50 Hz, ④ 기본 통과율 0.8)는 강사 레퍼런스 실측으로 확정했다. `solved/` 가 나오면 같은 verify 로 `--all` PASS 를 재확인한다.

---

## 8. 컨벤션 예외 (승인 필요 — 2건)

1. 규칙 2(데이터 레포 미포함) 예외: `harness/data/` 3파일(≈ 10–15 MB)을 커밋한다(`solved/data/` 는 복사본이라 중복 커밋 — 용량이 문제면 `solved/data/` 만 gitignore 하고 README 에 "harness/data 를 복사하라"고 적는다). 근거: 참가자 에이전트가 인터넷 없이 동작해야 한다(싼 모델·클라우드 샌드박스). `.gitignore` 에 3·4회차 백업 가중치와 같은 방식으로 파일 단위 재포함 블록을 추가한다.
2. 노트북 구조 예외: 참가자용 코랩 노트북이 없다. 노트북 대신 프로젝트 루트가 산출물이고, `00_/01_` 접두사 규칙은 `src/stepN_*.py` 로 대체한다. `solved/outputs/` 는 gitignore 대상이지만 이번엔 결과 그림·로그가 곧 증거이므로 파일 단위로 재포함한다.

CONVENTIONS.md 본문은 고치지 않고 이 스펙에 예외로 기록한다.

---

## 9. 작업 순서 (한 단계씩, 각 단계 후 보고)

1. 하네스 문서 골격 — `harness/{README, AGENTS, CLAUDE}.md`, `docs/{TASK, MODEL_SPEC, DATA}.md`, requirements, conda 스크립트, 빈 폴더. (완료 2026-09-16)
2. 데이터 3종 생성 → `harness/data/`. DATA.md 에 실측값 기입. 도망 회로 재현을 강사 레퍼런스로 확인. (완료 2026-09-16)
3. `tests/verify.py`. (완료 2026-09-16)
4. 사전 점검: 여기(클로드 세션)에서 싼 모델 서브에이전트에게 `harness/` 복사본만 주고 4단계를 시켜 문서·verify 의 결함을 먼저 잡는다.
   - 1차(2026-09-16, Haiku): ①②③ PASS — verify 각 1·1·2회, 처음 세 단계까지 약 16분, ③ wall 37 s(GF_L 263 Hz, GF_R 349 Hz, 발화 뉴런 1,496개). ④ 는 명령 도구의 120 s 시간 제한에 3회 걸려 규칙 13 으로 중단 — 코드가 아니라 실행 방식 문제였는데 모델은 최적화를 반복했다. 조치: AGENTS.md 규칙 14(긴 실행은 제한 연장·백그라운드), TASK ④ 시간 안내 + 이어쓰기 힌트, M 5 → 3(총 시뮬 8.9 → 5.3 s). 문서 피드백: 참고값이 실측과 ±수 % 다를 수 있음을 명시(난수 사용 순서 차이).
   - 2차(같은 날, 같은 에이전트 재개): ④ PASS — 15 에피소드 wall 101 s, 결과는 예측대로(k=1 too_early 3/3, k=2~4 통과 9/9, k=5 too_late 3/3, GF 지연 5.1~6.3 ms). 그러나 `04_dino.gif` 는 100×100 흰 프레임 2장 — verify 가 "프레임 ≥ 2" 만 봤더니 모델이 스펙 대신 검사기를 만족시켰다. 조치: verify 에 GIF 프레임 수(≥ 30)·크기(≥ 640×360)·빈 프레임·정지 화면 검사와 모든 PNG 의 빈 그림 검사 추가, MODEL_SPEC §5-④ 규격 명시. 수업 소재: "검사기가 약하면 모델은 검사기를 통과하지 스펙을 통과하지 않는다".
   - 3차(같은 날, 같은 에이전트 재개): 강화된 verify 로 GIF 재작성 지시 → 44 프레임 800×450 의 실제 장면(공룡·선인장·θ·GF 시각·PASS/FAIL 표시)으로 통과, 92/92. 다만 GIF 를 별도 스크립트(`step4_render_gif.py`)로 분리함 → verify 에 단계별 주 스크립트 파일 존재 검사 추가, TASK ① 힌트에 "주 스크립트 하나" 명시. 최종 하네스로 처음부터 다시 도는 4차(깨끗한 실행)는 아래 기록.
   - 4차(같은 날, 새 Haiku 에이전트, 최종 하네스, 개입 없음): 4단계 모두 PASS, verify 96/96, verify 실행 1·1·1·2회(④ 첫 실패는 점프 판정 부등호 실수 → 스스로 수정). 에이전트 총 소요 11.3분, 계산 wall 192 s(③ 66.5 s, ④ 124.6 s). 결과 동일(k=1 too_early, k=2~4 통과, k=5 too_late, GF 지연 5.1~6.3 ms). docs/tests/data 무수정 확인(md5 일치). 남은 결함: GIF 에 텍스트 오버레이(t·θ·GF·결과)를 넣지 않음 — verify 로 강제하기 어려워 육안 확인 항목으로 남김. 문서 피드백 "불명확한 곳 없음". → 사전 점검 완료, §9-5(준현 PC 클로드 코드 실행)로.
5. 실제 실행: 준현 PC 에서 `harness/` → `solved/` 복사 후 클로드 코드에게 README 의 자동 지시 문장으로 4단계 완주. `RUN_LOG.md`, `outputs/verify_all.txt` 남김.
   - 결과(2026-09-17 01:38–01:53, Claude Code 데스크톱, 모델 Claude Fable 5.1, Windows 11 conda): 4단계 PASS 96/96, verify 실패 0회(단계별 2·1·1·2 + --all 2), 총 15분(그중 conda env 생성·pip 설치 포함). wall ③ 48 s, ④ 116 s. GF_L 255 Hz / GF_R 336 Hz, 발화 뉴런 1,462개, 지연 5.8~7.0 ms, 통과율 0/3·3/3·3/3·3/3·0/3. 규격 문서·검증기 무수정(md5 일치). GIF 는 44 프레임 800×450 에 텍스트 오버레이(에피소드·t·d·θ·자극·GF 누적·결과) 포함. 스펙과 다르게 한 곳 없음. `outputs/QUESTIONS.md` 에 모호점 7개(재점프 규칙, 접촉 후 θ, 자극 뉴런의 막전위 발화, 래스터 모집단, 이어서 실행 시 wall_seconds, 보조 파일 허용 여부, "3뉴런" 제목) → 하네스 문서 v1.1 로 명시(규칙 변경 없음, 설명만 추가). `solved/` 의 docs 는 v1.0 그대로 둔다(그 문서로 수행했다는 증거).
6. `solved/` 를 verify `--all` 로 재검증. 기준치를 손볼 일이 생기면 여기서 고치고 문서에 반영.
7. `.gitignore` 예외 + 루트 README 세션 목록 갱신 + `harness/`·`solved/` 커밋·푸시(준현 PC).
8. `session5_lecture.html` — 프로젝트용 하네스 구축 문서(§13). (완료 2026-09-16 — 단일 HTML 7.3 MB, 영상·GIF·그림 base64 내장. 구성: Part 0 오프닝 영상 + 밈 정리 / 1 에이전트=모델+하네스 / 2 harness/ 해부(문장·AGENTS 5조·TASK 4단계·verify 원칙) / 3 커넥톰·LIF·도망 회로·flybody·재생기 / 4 Haiku 사전 점검 4회와 교훈 3개 / 5 클로드 코드 vs Haiku 비교표 + solved/ 그림 / 6 속도 창 그림(반사 재현, 속도 미학습) / 7 내 연구 폴더 템플릿 + 주제 4개 + 체크리스트. 수치는 전부 §9-4·§9-5 기록과 solved/·사전 점검 outputs 에서 대조. 오프닝 밈의 근거는 각주에 명시(MaleCNS Cell 2026-09, BANC Nature 2026-06, doomfly README 인용). 빌드 소스(템플릿 HTML + 미디어 인라인 스크립트)는 강사 세션에만 있음 — 수정은 HTML 직접 편집으로 충분.)

---

## 10. 회차 통과 조건

- [x] 클로드 코드가 `harness/` 복사본만으로 4단계 verify 를 통과했고, 그 결과가 `solved/` 에 그대로 있다(`verify_all.txt`, `RUN_LOG.md`) — 2026-09-17, 강사 재검증 96/96.
- [x] 싼 모델 사전 점검에서도 4단계 통과 — Haiku, 최종 하네스로 개입 없이 96/96, 11.3분(2026-09-16).
- [x] 총 소요 ≤ 60분 — 클로드 코드 15분, Haiku 11.7분.
- [x] `harness/data/` 합계 11.6 MB, 인터넷 불필요.
- [ ] 로컬(윈도우 conda) + 코랩 CPU 양쪽에서 `solved/src` 실행 확인(컨벤션 규칙 12).
- [x] `harness/` 안에 정답·힌트 코드가 없다.

---

## 11. 하지 말 것

pygame·실시간 루프, 뉴런 모델 복잡화(conductance-based, adaptation), 파라미터 임의 조정(§3 고정), MaleCNS 사용, `harness/` 에 정답·힌트 코드, 요청 외 기능(웹 UI, 학습 규칙·도파민, 익룡·숙이기).

---

## 12. 열린 결정

1. 참가자 도구(Claude Code / Codex / Cowork / Colab Gemini) — 미정. 지시 파일은 범용 `AGENTS.md`, `CLAUDE.md` 는 `@AGENTS.md` 한 줄. Gemini 용 `GEMINI.md` 도 같은 한 줄로 둘지.
2. 수업 날짜.
3. §8 예외 2건 승인.
4. 에이전트 없이 챗만 쓰는 참가자 대응: 코랩 + Gemini 로 할지, 강사 화면 공유로 할지.
5. §9-5 를 준현 PC 의 클로드 코드로 할지, 이 세션의 서브에이전트로 할지(기본: 준현 PC — 윈도우 conda 경로까지 같이 검증되고, 수업에서 보여 줄 실물 로그가 남는다).

---

## 13. 2차 산출물 — 프로젝트용 하네스 구축 HTML 문서

`session5/session5_lecture.html` (완료 — §9-8 참조). 이전 회차와 같은 단독 열람용 HTML. 내용: 에이전트 = 모델 + 하네스, 프로젝트 루트의 5요소(폴더·지시·과제·데이터·검증), `harness/` 를 예제로 한 요소별 해부, `solved/` 의 실제 결과(그림·로그·소요 시간), 싼 모델 vs 비싼 모델 비교, 내 연구 폴더로 옮기는 절차(빈 템플릿 포함). 별도 스펙으로 §9-8 에서 작성한다.
