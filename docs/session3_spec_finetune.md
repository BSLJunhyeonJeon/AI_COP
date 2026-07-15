# 학습공동체 3회차 — 구현 스펙 (파인튜닝 노트북 + HTML 빌더)

> 이 문서는 클로드 코드가 `session3/` 을 구현할 때의 지시서입니다.
> **레포 루트의 `CONVENTIONS.md` 가 상위 규칙**이며, 충돌 시 CONVENTIONS 가 우선합니다.
> 아래 "검증된 사실"은 실제로 클론해 확인한 값입니다. **추측으로 바꾸지 마세요.**
> **수업은 내일입니다. 스펙에 없는 것은 추가하지 마세요.**

---

## 0. 이번 회차의 역할 (왜 이렇게 짜는가)

3회차 수업 흐름은 **"학습을 켜놓고 이론을 한다"** 입니다.

| 시각 | 하는 일 |
|---|---|
| 00:00 | 코랩에서 **셀 4(학습)** ▶ — 그대로 두고 화면 전환 |
| 00:05 ~ 01:15 | 이론 강의 (HTML 자료 — 모델 지도, 백본/헤드, 도메인 갭, 지표, 라이선스) |
| 01:15 ~ 01:25 | 코랩으로 복귀 → **셀 5~8** 실행, 결과 확인 |
| 01:25 ~ 01:55 | 워크숍 |

따라서 노트북의 요구사항은 딱 두 개입니다.

1. **셀 4는 "누르고 잊는" 셀**이어야 한다 — 무료 코랩 T4에서 10~15분 안에 끝나고, 중간에 사람 개입이 필요 없어야 한다.
2. **셀 4가 실패해도 수업이 안 깨져야 한다** — 사전 학습된 가중치로 셀 5~8이 그대로 돌아가야 한다.

2회차의 클라이맥스는 "COCO 사전학습 YOLO11n 이 혈액 도말에서 빗나갔다"(`session2/outputs/02_detection.png`)였습니다.
3회차는 **바로 그 모델을 우리 데이터로 길들여 맞히게 만드는 것**이 결말입니다.

---

## 1. 검증된 사실 (그대로 사용)

### 1-1. BCCD (`https://github.com/Shenggan/BCCD_Dataset`, MIT)

```
BCCD/
├─ JPEGImages/BloodImage_XXXXX.jpg    # 364장, 전부 640×480
├─ Annotations/BloodImage_XXXXX.xml   # 364개, Pascal VOC 형식
└─ ImageSets/Main/{train,val,test,trainval}.txt   # 공식 분할
```

- **공식 분할**: train **205**장 / val **87**장 / test **72**장  → **이 분할을 그대로 쓴다. 직접 나누지 말 것.**
- **클래스 3개** (VOC XML의 `<object><name>`): `RBC`, `WBC`, `Platelets`
- **박스 수**: RBC **4155**, WBC **372**, Platelets **361** → **심한 클래스 불균형**. 이건 버그가 아니라 **강의 소재**다(셀 8에서 드러낸다).
- 이미지당 박스 평균 13.4개 (최소 1, 최대 30)
- 2회차 `01_data.ipynb` 셀 4가 이미 이 레포를 `data/_bccd_src/` 로 shallow clone 하고 **3장만** `data/detection/` 에 복사한다. 3회차는 **전체 364장**이 필요하다.

### 1-2. 전/후 비교 이미지 — **`BloodImage_00011`**

- **`BloodImage_00011` 은 test split** 이다 (학습·검증 어디에도 안 쓰임). 박스: WBC 1 + RBC 17 + Platelets 1 → **세 클래스가 다 보인다.**
- ⚠️ 2회차 실패 데모에 쓴 `BloodImage_00000` 은 **val split** 이다. 전/후 비교에 쓰면 "검증에 쓴 이미지로 자랑하는" 그림이 된다. **쓰지 말 것.**
- 강의 메시지: *"학습에도 검증에도 안 쓴 이미지에서 맞혀야 진짜 실력"* → 2회차 §5(일반화/과적합) 회수.

### 1-3. 2회차 자산 (재사용)

- `session2/outputs/02_detection.png` — COCO YOLO11n 실패 그림. **3회차에서 다시 만들지 말고, 셀 6에서 같은 방식으로 `BloodImage_00011` 에 대해 새로 그린다.**
- HTML 빌더 방식: `session2/notebooks/05_build_html.ipynb` 셀 4의 `data-embed="파일명"` → base64 `src=` 정규식 주입. **이 메커니즘을 그대로 복제한다.**

---

## 2. 산출물

```
session3/
├─ README.md                  # Open in Colab 배지 (session2/README.md 패턴)
├─ requirements.txt           # 아래 §3
├─ setup_env.sh / setup_env.bat   # session2 것 복사, 경로만 session3
├─ data/ weights/ outputs/    # .gitkeep (비움)
└─ notebooks/
   ├─ 01_finetune.ipynb       # ★ 수업용 (라이브에서 이걸 연다)
   └─ 02_build_html.ipynb     # 강의자료 빌더 (수업 전에 1회 실행)
```

**HTML 템플릿(`session3/session3_lecture_template.html`)은 claude.ai 가 별도로 작성해 커밋합니다. 클로드 코드는 만들지 마세요.**
02 빌더는 그 템플릿이 **없으면 명확한 에러 메시지를 내고 멈추면** 됩니다.

---

## 3. `session3/requirements.txt`

session2 에서 **검증된 핀만** 가져오고, 3회차에 안 쓰는 건 뺀다 (medmnist·transformers·albumentations 제외).

```
torch==2.11.0
torchvision==0.26.0
ultralytics==8.4.76      # YOLO11 학습 + 추론
numpy==2.0.2
matplotlib==3.10.0
Pillow==11.3.0
```

- 학습에 필요한 `pandas`/`pyyaml`/`seaborn` 은 코랩 사전설치 + ultralytics 의존성으로 해결된다. **추측해서 추가하지 말 것.** 셀 2에서 버전을 **출력**하고, 코랩에서 실제 확인된 값만 나중에 핀에 반영한다.

---

## 4. `01_finetune.ipynb` — 셀 구성

노트북 최상단 마크다운 3줄(배우는 것 / 입력 / 출력) + Open in Colab 배지. 설명·주석은 한국어, **그림 안 글자는 영문**(폰트 호환).

각 셀은 **독립 실행 가능**해야 한다(필요한 변수·경로·모델 로드를 셀 안에서 재확보).

---

### 셀 1 — 환경 감지 + 프로젝트 루트

`session2/notebooks/01_data.ipynb` 셀 1과 **동일 패턴**. `SESSION = "session3"` 만 변경.

### 셀 2 — 의존성 설치

session2 패턴. 설치 후 `torch / torchvision / ultralytics / numpy / matplotlib / PIL` 버전 출력.
**추가로 GPU 유무와 이름을 출력한다** (`torch.cuda.is_available()`, `torch.cuda.get_device_name(0)`). 셀 4의 학습 시간이 여기서 갈리므로 학생이 미리 알아야 한다.

### 셀 3 — BCCD 전체 준비 + VOC → YOLO 변환 + `bccd.yaml`

1. `data/_bccd_src/` 에 BCCD shallow clone (이미 있으면 건너뜀).
2. **공식 분할 파일**(`ImageSets/Main/{train,val}.txt`)을 읽어 YOLO 폴더 구조를 만든다:

```
data/bccd/
├─ images/train/*.jpg   (205)   images/val/*.jpg   (87)
└─ labels/train/*.txt   (205)   labels/val/*.txt   (87)
```

3. **VOC XML → YOLO txt 변환** — 한 줄 = `class_id cx cy w h` (모두 0~1 정규화).
   - `cx = (xmin+xmax)/2 / W`, `cy = (ymin+ymax)/2 / H`, `w = (xmax-xmin)/W`, `h = (ymax-ymin)/H` (W=640, H=480)
   - 좌표가 이미지 밖으로 나가는 어노테이션이 있을 수 있으니 **0~1 로 clip** 하고, clip 된 개수를 출력한다.
   - 클래스 id: `0=RBC, 1=WBC, 2=Platelets` (아래 yaml 과 순서 일치)
4. `data/bccd.yaml` 생성:

```yaml
path: <PROJECT_ROOT>/data/bccd     # 절대경로여야 ultralytics 가 찾는다 (os.path.abspath 로 생성)
train: images/train
val: images/val
names:
  0: RBC
  1: WBC
  2: Platelets
```

5. **출력**: train/val 장수, 클래스별 박스 수, 그리고 한 줄 —
   `"RBC 4155 : WBC 372 : Platelets 361 — 11배 불균형. 이게 나중에 성능 표에서 그대로 드러납니다."`

### 셀 4 — ★ 학습 (수업 시작 때 누르는 셀)

```python
from ultralytics import YOLO
model = YOLO("yolo11n.pt")          # 2회차에서 빗나갔던 바로 그 COCO 사전학습 모델
model.train(
    data="data/bccd.yaml",
    epochs=EPOCHS, imgsz=640, batch=16,
    project="runs", name="bccd", exist_ok=True,
    seed=0, plots=True, verbose=True,
)
```

- `EPOCHS`: GPU 있으면 **50**, 없으면 **5** 로 자동 분기하고, **분기 결과와 예상 소요시간을 먼저 print** 한다.
  - GPU(T4) 기준 50 epoch ≈ 10~15분. CPU 는 결과가 약하다는 경고를 명시.
- 셀 맨 위 마크다운에 크게: **"이 셀을 누르고 이론 강의로 넘어갑니다. 끝날 때까지 두세요."**
- 학습 끝나면 `runs/bccd/weights/best.pt` → **`weights/bccd_yolo11n.pt` 로 복사**한다.

### 셀 5 — 학습 곡선

- `runs/bccd/results.png` 를 `outputs/03_curves.png` 로 복사(있으면).
- 없으면 `runs/bccd/results.csv` 를 읽어 **box loss / mAP50 두 개만** 직접 플롯. (곡선 6개를 다 보여주면 초보자가 길을 잃는다.)
- 아래 한 줄 출력: `"loss 는 내려가고 mAP 는 올라간다 — 이게 '배우고 있다'는 뜻입니다."`

### 셀 6 — ★ 전/후 비교 (이 노트북의 클라이맥스)

- 대상: **`BloodImage_00011`** (test split — `data/_bccd_src/BCCD/JPEGImages/` 에서 직접 읽는다. `data/bccd/` 에는 없다.)
- 왼쪽: `YOLO("yolo11n.pt")` (COCO) 결과 — 2회차와 같은 실패
- 오른쪽: `YOLO(FT_WEIGHTS)` 결과 — 맞힘
- 두 패널 제목에 **검출된 박스 개수**를 표시. `conf=0.25` 고정.
- 저장: **`outputs/03_before_after.png`**
- `FT_WEIGHTS` 결정 로직 (**라이브 보험 — 반드시 이 순서**):
  1. `weights/bccd_yolo11n.pt` (셀 4가 만든 것)
  2. `runs/bccd/weights/best.pt`
  3. 둘 다 없으면 → **레포에 커밋된 `weights/bccd_yolo11n_pretrained.pt`** 사용 + `"[백업] 사전 학습된 가중치로 진행합니다."` 출력
  4. 그것도 없으면 → 명확한 에러 메시지

### 셀 7 — confidence 임계값 스윕 (HTML 슬라이더용)

- **같은 이미지(`BloodImage_00011`), 같은 모델(FT_WEIGHTS)**, conf 만 바꾼다: `0.10 / 0.25 / 0.50 / 0.70`
- 각각 **별도 파일**로 저장 (HTML 이 슬라이더로 넘긴다):
  `outputs/03_conf_010.png`, `03_conf_025.png`, `03_conf_050.png`, `03_conf_070.png`
- **네 장의 그림 크기·여백·DPI 가 완전히 동일**해야 한다 (슬라이더에서 튀면 안 됨). `figsize` 와 `dpi` 를 하드코딩하고 `bbox_inches` 는 쓰지 말 것.
- 각 패널 제목에 `conf=0.xx | boxes=N` 표시.

### 셀 8 — 클래스별 성능 (불균형 회수)

- `model.val(data="data/bccd.yaml", split="val")` → 클래스별 mAP50 / precision / recall 을 **표 그림**으로 그린다.
- 각 클래스의 **학습 박스 수**를 같이 표시해 "박스 많은 클래스가 잘 맞는다"가 눈에 보이게 한다.
- 저장: **`outputs/03_per_class.png`**
- 한 줄 출력: `"Platelets 가 약합니다. 모델이 나빠서가 아니라 라벨이 361개뿐이라서입니다. — 4회차 주제."`

### 셀 9 — 검증 / 요약

- `outputs/` 에 아래 7개 파일이 모두 있는지 체크해 표로 출력:
  `03_curves.png`, `03_before_after.png`, `03_conf_010.png`, `03_conf_025.png`, `03_conf_050.png`, `03_conf_070.png`, `03_per_class.png`
- `weights/bccd_yolo11n.pt` 존재 여부
- 배운 것 3줄 출력.

---

## 5. `02_build_html.ipynb` — 빌더

`session2/notebooks/05_build_html.ipynb` 의 **직접 복제**. 차이는 이것뿐:

- 대상 세션: `session3`
- 템플릿: `session3/session3_lecture_template.html`
- 01 을 먼저 실행해 `outputs/` 를 채운 뒤(같은 코랩 세션 안에서), `data-embed` 슬롯에 base64 주입
- 결과: `outputs/session3_lecture.html` (자체완결 1파일)
- 임베드/누락 파일 목록을 출력한다.

**주의**: 01 은 학습(10~15분)을 포함한다. 빌더 실행 시간이 그만큼 걸린다는 걸 셀 상단에 명시.

---

## 6. 라이브 보험 (`.gitignore` 예외) — **승인 필요**

`.gitignore` 가 `*.pt` 를 막고 있다. 라이브에서 학습이 실패해도 셀 6~8 이 돌게 하려면 **사전 학습된 가중치 1개(≈6MB)를 레포에 커밋**해야 한다.

`.gitignore` 에 예외 한 줄 추가:

```gitignore
# ===== 예외: 3회차 라이브 백업 가중치 (수업 중 학습 실패 대비, ~6MB) =====
!session3/weights/bccd_yolo11n_pretrained.pt
```

절차: 선생님이 오늘 밤 01 을 1회 실행 → 나온 `best.pt` 를 `session3/weights/bccd_yolo11n_pretrained.pt` 로 커밋.
**이 예외를 넣을지는 선생님 승인 후 진행하세요.**

---

## 7. 하지 말 것 (스코프 고정)

- **SegFormer 분할 파인튜닝** — 4회차. 이번엔 검출(YOLO)만.
- **Cellpose / micro-SAM 실행** — HTML 에서 개념으로만 다룬다. 설치 리스크 때문에 라이브 실행 안 함.
- **모델 크기 n/s/m/l/x 비교 학습** — 5번 학습해야 한다. HTML 에 공개 수치 표로 대체.
- **하이퍼파라미터 튜닝 / 스윕** — 4회차 주제.
- **ipywidgets 등 인터랙티브 위젯** — 코랩에서 불안정(2회차 결론). 인터랙티브는 전부 HTML(JS)이 맡는다.
- **HTML 템플릿 작성** — claude.ai 담당.
- 스펙에 없는 기능·옵션 임의 추가 금지. 필요해 보이면 **추가하지 말고 질문/메모로 남긴다.**

---

## 8. 통과 조건 (구현 후 자가 점검 → 보고)

- [ ] `session3/` 이 CONVENTIONS 구조를 따르고, 01·02 노트북이 코랩에서 열린다
- [ ] 셀 3 실행 후 `data/bccd/images/{train,val}` = **205 / 87** 장, 라벨 txt 개수 동일
- [ ] 셀 4 가 **사람 개입 없이** 끝나고 `weights/bccd_yolo11n.pt` 가 생긴다
- [ ] 셀 6 의 좌/우가 눈에 띄게 다르다 (좌: 박스 거의 없음 / 우: 세포에 박스)
- [ ] 셀 7 의 4장이 **동일한 크기·여백**이다
- [ ] `weights/` 를 지우고 셀 6 을 다시 실행해도 **백업 가중치로 동작**한다 (라이브 보험 검증)
- [ ] `outputs/` 에 7개 파일이 모두 생긴다
- [ ] 셀 2 가 출력한 **실제 버전**으로 `requirements.txt` 핀이 맞다

구현 후 **변경 요약 + 사람이 확인하는 법**을 보고하고, **직접 돌려본 범위**를 밝히세요(학습을 몇 epoch 까지 실제로 돌렸는지 포함).
