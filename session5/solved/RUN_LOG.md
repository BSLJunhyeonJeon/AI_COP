# RUN_LOG — session5 초파리 전뇌 시뮬레이션 4단계 실행 기록

- **사용한 모델**: Claude Fable 5.1 (`claude-fable-5-1`), Claude Code 데스크톱 앱
- **시작 시각**: 2026-09-17 01:38:09 (환경 확인 첫 명령)
- **종료 시각**: 2026-09-17 01:53:06 (`verify.py --all` 최종 PASS)
- **실행 환경**: Windows 11, conda env `ai_cop_session5` (Python 3.12; numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, pyarrow 25.0.1, matplotlib 3.11.2, Pillow 12.3.0)
- **최종 결과**: `python tests/verify.py --all` → 단계 1~4 모두 PASS (19/19, 16/16, 28/28, 33/33), 출력은 `outputs/verify_all.txt`

## 단계별 wall time

| 단계 | 스크립트 | wall (summary 의 `wall_seconds`) | 비고 |
|---|---|---|---|
| ① 뉴런 1개 | `src/step1_neuron.py` | 1.4 s | 8개 I_ext × 1000 ms |
| ② 반사궁 | `src/step2_reflex.py` | 0.4 s | 2 조건 × 500 ms |
| ③ 전뇌 | `src/step3_brain.py` | 48.1 s | 자극 1 s: 26.2 s, 무자극 1 s: 20.7 s, W 조립 0.4 s |
| ④ 공룡 게임 | `src/step4_dino.py` | 116.1 s (첫 완주) | 에피소드 15개 합 110.9 s(신경 시간 5.33 s) + 그림·GIF. 그림 수정 후 재실행은 저장된 에피소드를 이어받아 5.0 s — 현재 `04_summary.json` 의 `wall_seconds` 는 이 값이고 `wall_seconds_episodes_total` = 110.9 s |

## 단계별 verify 실행 횟수

| 단계 | 실행 횟수 | 결과 |
|---|---|---|
| `--stage 1` | 2 | PASS, PASS (2회째는 한글 폰트 설정 뒤 재실행 확인) |
| `--stage 2` | 1 | PASS |
| `--stage 3` | 1 | PASS |
| `--stage 4` | 2 | PASS, PASS (2회째는 그래프 눈금·GIF 표현 수정 뒤) |
| `--all` | 2 | PASS, PASS |

실패한 verify 는 없다.

## 주요 결과

- ① 해석해 대비 오차: I=10: +0.1 %, 15: +1.0 %, 20: +1.6 %, 30: +1.6 %. I ≤ 7 mV 는 0 Hz.
- ② 억제 꺼짐 V=83, G=23, J=26 / 억제 켜짐 V=68, I=75, G=0, J=0 → J(on)/J(off) = 0.
- ③ GF_L 255 Hz, GF_R 336 Hz, 발화 뉴런 1,462개, 총 스파이크 89,270개, 첫 GF 스파이크 6.0 ms, LPLC2 평균 149.8 Hz (레퍼런스 264 / 349 Hz, 1,519개, 94,695개, ~6 ms — 난수 순서 차이로 수 % 차이).
- ④ 통과율 k=1..5: 0/3, 3/3, 3/3, 3/3, 0/3. 반사 지연(θ_on → GF 첫 스파이크) 5.8~7.0 ms. k=1 은 전부 `too_early`, k=5 는 전부 `too_late`. 상수는 건드리지 않았다.

## 막혔던 곳과 고친 방법

1. **환경**: 기본 anaconda 의 pandas/pyarrow 가 numpy 2.4.6 과 바이너리 불일치(`_ARRAY_API not found`)로 시작 전 확인 명령이 실패. 기존 env(`ai_cop_session4`)에는 pandas 가 없었다.
   → AGENTS.md 지시대로 `setup_env.bat` 과 같은 절차(`conda create -n ai_cop_session5 python=3.12 pip` → `pip install -r requirements.txt`)를 `conda run` 으로 수행했다(비대화 셸에서는 `conda activate` 가 되지 않아 배치 파일을 직접 돌리지 않고 같은 명령을 실행). 이후 모든 실행은 이 env 의 python 으로 했다. requirements.txt 밖의 패키지는 설치하지 않았다.
2. **Bash 히어독**: Git Bash 로 `step4_dino.py` 를 히어독으로 쓰는 명령이 인용 부호 오류로 실패 → 파일 쓰기 도구로 저장했다(코드 내용은 동일).
3. **그림 폰트(경미)**: 기본 폰트(DejaVu Sans)에 한글이 없어 경고 → 공용 모듈에 Malgun Gothic 설정 추가. Malgun Gothic 에는 유니코드 마이너스(U+2212)가 없어 라벨은 ASCII `-` 로, 로그축 눈금은 속도 값을 직접 표기했다.
4. **긴 실행**: ③(48 s)·④(116 s)는 명령 도구의 시간 제한을 10분으로 늘리고 로그를 `outputs/0N_run.log` 로 남겨 실행했다. 코드 최적화로 돌아가지 않았다(규칙 14).

## 스펙과 다르게 한 곳

없음. (파라미터·수식·파일 이름·시드 규칙 모두 MODEL_SPEC/TASK 그대로.) 구현상 선택은 아래 "불명확했던 부분"에 적었다.

- 막전위 갱신은 `v += (v_rest − v + g + I)·(1 − a_m)` 형태로 썼다. 스펙의 `v_rest + (v − v_rest)·a_m + (g + I)(1 − a_m)` 과 대수적으로 같고, I_ext = 7 mV 에서 부동소수 반올림으로 임계값에 정확히 닿는 일이 없게 하려는 선택이다.
- `W[idx].sum(axis=0)` 은 CSR 의 indptr/indices 로 발화한 행의 항목만 모아 `np.bincount` 로 합쳤다(같은 값, 밀집 행렬 없음).

## 문서에서 불명확했던 부분 (해석은 `outputs/QUESTIONS.md` 에 정리)

1. ④ 착지 후 GF 가 다시 발화하면 재점프하는지 — 규칙 3 은 공중 스파이크 무시만 말한다. 에피소드당 점프 1회(첫 GF 스파이크)로 해석. 재점프를 허용하면 k=1 이 통과해 "느린 물체엔 너무 일찍" 이라는 메시지와 어긋난다.
2. ④ 접촉 후(d ≤ 0)의 θ(t) 정의 없음 — 180° 로 두어 자극 유지. 결과에 영향 없음.
3. 자극 뉴런이 막전위로도 발화할 수 있는지 — 자극이 켜진 동안은 포아송 추첨만 스파이크로 삼음(LPLC2 평균 149.8 Hz).
4. ③ 래스터 "발화율 상위 20개" 의 모집단 — 자극 뉴런·GF 를 뺀 나머지로 해석.
5. 이어서 실행했을 때 `wall_seconds` 의 의미(전체 vs 이번 실행) — 이번 실행 wall 로 기록하고 실제 시뮬레이션 시간은 별도 키에 남김.
6. outputs/ 의 중간 결과 파일(npz)·실행 로그가 규칙 7("모든 파일은 src 가 만든다")에 저촉되는지 — 규칙 12·14 가 권하는 이어가기·로그용이라 그대로 뒀다.
7. TASK 제목은 "3뉴런 반사궁" 이지만 실제 뉴런은 4개(V, I, G, J) — 스펙 §5-② 대로 4개 구현.

## 만든 파일

- `src/lif.py` (공용: 파라미터, 이산화 스텝, 지연 큐, 포아송 자극, W 조립, 한글 폰트), `src/step1_neuron.py`, `src/step2_reflex.py`, `src/step3_brain.py`, `src/step4_dino.py`
- `outputs/01_trace.png`, `01_fi_curve.csv`, `01_summary.json`, `02_reflex.png`, `02_summary.json`, `03_raster.png`, `03_rates.csv`, `03_summary.json`, `04_dino.gif`(44 프레임, 800×450, 10 fps), `04_speed_vs_pass.png`, `04_log.csv`, `04_summary.json`, `verify_all.txt`, `QUESTIONS.md`
- 보조: `outputs/03_spikes_{stim,ctrl}.npz`, `outputs/04_episodes/ep_k*_j*.npz`(이어가기용), `outputs/03_run.log`, `outputs/04_run.log`
