# DATA — 데이터 파일 스키마·출처·라이선스

`data/` 는 읽기 전용이다. 세 파일 모두 이 폴더 안에 있고, 인터넷은 필요 없다.
아래 수치는 2026-09-16 생성 시 실측값이다(생성 스크립트: 레포의 `session5/tools/build_data.py`).

---

## 1. 파일 목록

| 파일 | 내용 | 크기 |
|---|---|---|
| `data/connections.parquet` | 뉴런 → 뉴런 연결 2,700,513 행 (시냅스 5개 이상만) | 10.1 MB |
| `data/neurons.csv.gz` | 뉴런 138,639개의 인덱스·root_id·주석 (gzip CSV) | 1.5 MB |
| `data/groups.json` | 뉴런 그룹 이름 → 인덱스 목록 (9개 그룹) | 5 KB |

## 2. `connections.parquet`

| 컬럼 | 타입 | 뜻 |
|---|---|---|
| `pre` | int32 | 프리시냅스 뉴런 인덱스 (0 ~ 138,638) |
| `post` | int32 | 포스트시냅스 뉴런 인덱스 (0 ~ 138,638) |
| `syn` | int16 | 시냅스 수 (≥ 5) |
| `sign` | int8 | +1 흥분 / −1 억제 (신경전달물질 예측 기반) |

- (pre, post) 쌍은 유일하다(생성 시 검증: 중복 0). 부호 분포 +1: 1,648,006 행 / −1: 1,052,507 행. syn 최대 2,405. 프리시냅스 뉴런 129,351개, 포스트시냅스 뉴런 125,192개.
- 가중치는 코드에서 만든다: w = 0.275 mV × syn × sign.
- 원본은 시냅스 1개짜리 연결까지 15,091,983 행이지만, 모델 규칙(최소 시냅스 5)에 맞춰 걸러 둔 것이다.

## 3. `neurons.csv.gz`

| 컬럼 | 뜻 |
|---|---|
| `index` | 0 ~ 138,638. `connections.parquet` 의 pre/post 와 같은 번호 |
| `root_id` | FlyWire v783 root ID (18자리 정수). 문헌·Codex 검색용 |
| `super_class`, `cell_class`, `cell_sub_class`, `cell_type`, `hemibrain_type`, `side`, `top_nt` | 주석 (Schlegel et al. 2024). 138,625개 뉴런이 매칭되고 137,147개에 `cell_type` 이 있다. 없는 뉴런은 빈칸 |

이 파일은 사람이 뉴런을 알아볼 때 쓴다(`pd.read_csv("data/neurons.csv.gz")` 로 바로 읽힌다). 시뮬레이션 자체에는 `connections.parquet` 와 `groups.json` 만 있으면 된다.

## 4. `groups.json`

```json
{
  "LPLC2_L": [ ... ],   "LPLC2_R": [ ... ],
  "LC4_L":   [ ... ],   "LC4_R":   [ ... ],
  "GF_L":    [ ... ],   "GF_R":    [ ... ],
  "sugar_GRN": [ ... ], "bitter_GRN": [ ... ], "ingestion_MN": [ ... ]
}
```

값은 `index` 의 목록이다. 그룹별 개수: LPLC2_L 108, LPLC2_R 102, LC4_L 54, LC4_R 50, GF_L 1(index 57246), GF_R 1(index 108748), sugar_GRN 129, bitter_GRN 65, ingestion_MN 28.

- `LPLC2_*`, `LC4_*`: 다가오는 물체(looming)에 반응하는 시각 투사 뉴런. ③④의 자극 대상은 LPLC2.
- `GF_*`: 거대섬유(giant fiber, DNp01). 도망 점프를 일으키는 하강 뉴런. 좌우 1개씩. 같은 쪽 LPLC2 에서 GF_L 로 305개, GF_R 로 539개의 시냅스가 들어온다(LC4 에서는 329개, 428개). 반대쪽에서는 0.
- `sugar_GRN`, `bitter_GRN`, `ingestion_MN`: 섭식 회로(설탕 감각뉴런 → 주둥이·섭식 운동뉴런, 쓴맛은 억제). `ingestion_MN` 은 `cell_sub_class = ingestion_motor_neuron` 28개로 MN9 를 포함하는 운동뉴런군이다. 이번 과제에서는 쓰지 않는다. 참고용.

## 5. 로딩 예시

```python
import json, numpy as np, pandas as pd, scipy.sparse as sp

N = 138_639
conn = pd.read_parquet("data/connections.parquet")
w = 0.275 * conn["syn"].to_numpy() * conn["sign"].to_numpy()          # mV
W = sp.csr_matrix((w, (conn["pre"].to_numpy(), conn["post"].to_numpy())), shape=(N, N))  # W[pre, post]

groups = json.load(open("data/groups.json", encoding="utf-8"))
stim = np.array(groups["LPLC2_L"] + groups["LPLC2_R"])
gf = {"GF_L": groups["GF_L"], "GF_R": groups["GF_R"]}
```

## 6. 출처와 라이선스

- 연결 데이터: FlyWire 전뇌 커넥톰 v783 — Dorkenwald et al., Nature 634, 124–138 (2024). 데이터 라이선스 CC BY 4.0. 이 폴더의 파일은 Shiu et al. 2024 코드 레포(`philshiu/Drosophila_brain_model`, MIT)의 `Connectivity_783.parquet`(15,091,983 행, 총 시냅스 54,492,922)를 시냅스 ≥ 5 로 거르고 정수 인덱스만 남긴 것이다. 인덱스는 그 레포의 `Completeness_783.csv` 행 순서와 같다(검증됨).
- 뉴런 주석: Schlegel et al., Nature 634, 139–152 (2024) — `flyconnectome/flywire_annotations` v783.
- 모델 파라미터: Shiu et al., Nature 634, 210–219 (2024) "A Drosophila computational brain model reveals sensorimotor processing".
- 논문·데이터를 인용할 때는 위 세 편을 함께 적는다.
