# 4회차 스펙 — 학습(Training): 손잡이를 돌리면 성능이 변한다

> **대상**: 클로드 코드
> **전제**: 레포 루트의 `CONVENTIONS.md` 가 상위 규칙. 충돌 시 **CONVENTIONS.md 우선**.
> **범위**: `session4/` 신규 생성. 노트북 3개 + requirements + README + conda 스크립트.
> **금지**: HTML 강의 템플릿 작성(claude.ai 담당). 스펙에 없는 기능·옵션 임의 추가.
> **작업 후**: 커밋·push, 무엇을 만들었는지 + 사람이 확인하는 법 + 직접 돌려본 범위 보고.

---

## 0. 이 회차의 한 문장

3회차는 학습을 **돌려 봤다**. 4회차는 학습이 **잘 되고 있는지 읽는 법**을 배운다.
→ 그래서 모든 실험은 **짧게(30~60초), 여러 번** 돌아가야 한다. 이게 설계의 제1원칙이다.

---

## 1. 산출물

```
session4/
├─ README.md                 # 세션 소개 + Open in Colab 배지 (session3 형식 복제)
├─ requirements.txt
├─ setup_env.bat / setup_env.sh      # conda env 이름: ai_cop_session4
├─ data/  weights/  outputs/         # .gitkeep 만
└─ notebooks/
   ├─ 01_train_lab.ipynb     # ★ 본체 — 하이퍼파라미터 실험실
   ├─ 02_pose_demo.ipynb     # 웹캠 손 포즈 + 전신 포즈 (독립 실행)
   └─ 03_build_html.ipynb    # session3/notebooks/02_build_html.ipynb 복제·개조
```

**중요 — 실행 순서 제약**: `03` 은 `01` 의 `outputs/` 를 읽는다. `02` 는 `mediapipe` 를 설치해
런타임 환경을 바꿀 수 있으므로 **`01` → `03` 을 먼저 끝내고, `02` 는 마지막에** 돌린다.
이 제약을 `02` 노트북 최상단과 `README.md` 에 명시할 것.

---

## 2. 데이터 — beans (검증 완료, 그대로 쓸 것)

**출처**: Makerere AI Lab ibean / HuggingFace `AI-Lab-Makerere/beans` · **라이선스 MIT**
**받는 법** (`datasets` 라이브러리 불필요 — 새 의존성 0개):

```
https://huggingface.co/datasets/AI-Lab-Makerere/beans/resolve/main/data/train.zip        # 143.8 MB
https://huggingface.co/datasets/AI-Lab-Makerere/beans/resolve/main/data/validation.zip   #  18.5 MB
https://huggingface.co/datasets/AI-Lab-Makerere/beans/resolve/main/data/test.zip         #  17.7 MB
```

압축을 풀면 **그대로 ImageFolder 구조**다 (zip 안에 split 폴더가 이미 들어있음):

```
data/beans/
├─ train/       {angular_leaf_spot, bean_rust, healthy}
├─ validation/  {angular_leaf_spot, bean_rust, healthy}
└─ test/        {angular_leaf_spot, bean_rust, healthy}
```

**실측 장수 (아래 숫자를 그대로 쓸 것. 추측 금지.)**

| split | 총 | angular_leaf_spot | bean_rust | healthy |
|---|---|---|---|---|
| train | **1034** | 345 | 348 | 341 |
| validation | **133** | 44 | 45 | 44 |
| test | **128** | 43 | 43 | 42 |

> **[정정 2026-08-13]** 이 표의 train 은 원래 **1035 / healthy 342** 였고 "HF 카드의 1034 는 부정확"
> 이라고 적혀 있었으나, **그 서술이 틀렸다.** `train.zip` 의 central directory 를 직접 집계한 결과:
> zip 안 파일은 1035개가 맞지만 그중 `train/healthy/healthy_train.120tore`(6148 bytes) 는 **이미지가 아니라**
> 배포 중 섞여 들어간 macOS 파인더 메타데이터(`.DS_Store` 형식)다. `ImageFolder` 는 이미지 확장자만 읽으므로
> 이 파일을 세지 않는다 → **실제 학습 이미지는 1034장(345 / 348 / 341)**. HF 카드의 1034 가 맞다.
> 셀 3이 이 파일을 지우고 1034 기준으로 검증한다. **§10 통과 조건의 "train 1035" 도 1034 로 읽을 것.**
> (val 133 / test 128 은 클래스별 수까지 원래 표와 일치 — 그대로다.)

- 이미지: **500×500 RGB JPEG**
- 클래스 인덱스는 `ImageFolder` 알파벳 순 → `0=angular_leaf_spot, 1=bean_rust, 2=healthy`
- **거의 균형**(약 1.0 : 1.01 : 0.99). 이건 강의 소재다 — 3회차 BCCD 는 11배 불균형이었다.

---

## 3. 모델·학습 설정 (고정)

- **모델**: `torchvision.models.resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)`, `fc` 를 `Linear(512, 3)` 으로 교체.
  전체 파인튜닝(freeze 없음). freeze 비교는 **이번 범위 아님**(§8 참조).
- **입력**: `Resize(256)` → `CenterCrop(224)` → `ToTensor` → ImageNet 정규화.
- **옵티마이저**: SGD(momentum=0.9). 스케줄러 없음 — 학습률 효과를 순수하게 보여줘야 한다.
- **손실**: CrossEntropyLoss.
- **배치**: 32. `num_workers=2`.
- **기본 학습 데이터**: **클래스당 100장 = 총 300장** 서브셋(시드 고정 샘플링).
  → 1 epoch ≈ 3~5초. **작은 데이터라 과적합이 확실히 나타난다 — 이게 의도다.**
- **검증**: `validation/` 133장 전체(서브샘플 금지).
- **테스트**: `test/` 128장. **셀 9에서 딱 한 번만** 쓴다.
- **시드**: `torch/np/random` 모두 고정(예: 42). `torch.backends.cudnn.deterministic=True`.

---

## 4. `01_train_lab.ipynb` — 셀 구성

헤더 3줄(배우는 것 / 입력 / 출력). 각 셀 독립 실행(CONVENTIONS 규칙 4).

**모든 실험 결과는 `outputs/runs.json` 에 누적 append** 한다. 런타임이 끊겨도 뒤 셀이 앞 결과를
읽어 그림을 다시 그릴 수 있어야 한다(같은 이름의 실험은 덮어쓴다).

### 셀 1 — 환경 셋업
session3 `01_finetune.ipynb` 셀 1 과 동일 패턴. `acquire_project()`, `PROJECT_ROOT=session4`, GPU 확인.

### 셀 2 — 의존성
`requirements.txt` 설치 후 **실제 버전 출력**(torch / torchvision / numpy / matplotlib / Pillow).
CONVENTIONS 규칙 3 — 출력값을 보고 나중에 핀을 확정한다.

### 셀 3 — 데이터 확보
1. zip 3개 다운로드 → `data/beans/` 에 해제. **멱등**(이미 있으면 건너뜀).
2. split × 클래스 장수 표 출력. §2 표와 **정확히 일치해야 한다** — 불일치 시 경고 출력.
3. 클래스당 1장씩 샘플 3장 + 각 클래스 이름 → `outputs/04_dataset.png` 로 저장.
4. 한 줄 출력:
   `"train 1035 / val 133 / test 128 — 세 클래스가 거의 균형입니다. 3회차 BCCD 는 11배 불균형이었죠. 오늘은 데이터 탓을 할 수 없습니다."`

### 셀 4 — 실험 함수 정의 (실행 아님, 정의만)
```python
run_experiment(name, lr, epochs, aug=False, n_per_class=100, seed=42) -> dict
```
- 반환/저장: epoch 별 `train_loss, train_acc, val_loss, val_acc`, 최고 val_acc 와 그 epoch, 소요 초.
- `aug=True` 일 때만 train 변환에 **`RandomHorizontalFlip` + `RandomRotation(15)` + `ColorJitter(0.3,0.3,0.3)`** 추가.
  (val/test 변환은 **절대** 증강하지 않는다 — 이것도 강의 포인트다.)
- 진행 상황을 epoch 마다 한 줄로 출력(초보자가 뭔가 돌아가는 걸 봐야 한다).
- 결과를 `outputs/runs.json` 에 저장.

### 셀 5 — 실험 A: 학습률 (보폭)
**5개 값을 순차 실행**: `lr ∈ {1e-1, 1e-2, 1e-3, 1e-4, 1e-6}`, `epochs=8`, `aug=False`.
예상 소요 ≈ 2.5분.

산출물 **2종**:
- `outputs/04_lr_compare.png` — 5개 val_acc 곡선을 **한 장에 겹쳐** 그림 (범례에 lr 표기)
- `outputs/04_lr_1e-1.png` … `04_lr_1e-6.png` — **개별 5장**(HTML 슬라이더용).
  **5장은 축 범위·크기·여백이 모두 동일해야 한다**(슬라이더에서 갈아끼울 때 튀면 안 됨).
  각 장에 train/val 곡선 2개 + 제목에 lr 과 최고 val_acc 표기.

한 줄 출력: `"같은 데이터, 같은 모델, 같은 시간. 바뀐 건 숫자 하나(학습률)뿐입니다."`

### 셀 6 — 실험 B: 과적합 (에폭)
`lr` = 셀 5 에서 **가장 좋았던 값**, `epochs=30`, `aug=False`, 300장.
- `outputs/04_overfit.png`: train_acc 와 val_acc 를 한 장에. **최고 val_acc 지점에 세로선 + "여기서 멈췄어야"** 주석.
  train/val 격차 구간을 옅게 음영 처리.
- 출력: 최종 train_acc, 최종 val_acc, 최고 val_acc 와 epoch, **"몇 epoch 을 헛돌았는지"**.

### 셀 7 — 실험 C: 증강
셀 6 과 **완전히 동일한 설정에 `aug=True` 만** 바꿔 1회 실행(30 epochs).
- `outputs/04_aug.png`: 셀 6(증강 없음) val 곡선과 셀 7(증강) val 곡선을 **겹쳐서** 비교.
  (셀 6 결과는 `runs.json` 에서 읽는다 — 다시 학습하지 않는다.)
- 출력: 두 조건의 최고 val_acc 차이. **차이가 작거나 역전되면 그대로 정직하게 출력할 것**
  — 결과를 좋게 보이게 조작하지 말 것. (3회차 RBC 사례처럼, 예상과 다른 결과도 수업 소재다.)

### 셀 8 — 지표 심화
셀 7 모델(증강 on, 최고 epoch 가중치)로 **validation** 예측:
1. **혼동행렬 3×3** → `outputs/04_confusion.png`. 셀에 개수와 비율 함께 표기.
2. 클래스별 **precision / recall / F1** 표 출력. **sklearn 쓰지 말고 numpy 로 직접 계산**
   (Colab 사전설치에 의존하지 않기 위함, 그리고 계산식을 보여주는 게 교육적).
3. **precision–recall 트레이드오프**: "healthy vs 병(2병합)" 이진 관점으로 임계값을
   0.1~0.9 로 옮기며 precision·recall 두 곡선을 그림 → `outputs/04_tradeoff.png`.
   한 줄 출력: `"병든 잎을 놓치지 않으려면 recall, 헛경보를 줄이려면 precision. 어느 쪽이 중요한지는 모델이 아니라 연구 질문이 정합니다."`

### 셀 9 — 요약표 + test 개봉
1. `runs.json` 의 모든 실험을 한 표로: 이름 / lr / epochs / 증강 / 최고 val_acc / 소요초.
2. **가장 좋은 설정 하나만** 골라 `test/` 128장으로 딱 한 번 평가. test 정확도 출력.
3. 한 줄 출력:
   `"방금 test 를 열었습니다. 이제부터 이 결과를 보고 설정을 또 바꾸면, test 는 더 이상 test 가 아닙니다."`

### 셀 10 — 검증/요약
`outputs/` 에 아래 **11개 파일**이 다 있는지 표로 점검:
`04_dataset.png`, `04_lr_compare.png`, `04_lr_1e-1.png`, `04_lr_1e-2.png`, `04_lr_1e-3.png`,
`04_lr_1e-4.png`, `04_lr_1e-6.png`, `04_overfit.png`, `04_aug.png`, `04_confusion.png`, `04_tradeoff.png`
+ `runs.json`. 배운 것 3줄 출력.

---

## 5. `02_pose_demo.ipynb` — 웹캠 포즈 데모

**최상단 경고(마크다운)**: 이 노트북은 `mediapipe` 를 설치해 런타임 패키지 구성을 바꿀 수 있다.
**`01`·`03` 을 먼저 끝낸 뒤 마지막에** 실행하라. 문제가 생기면 런타임 재시작 후 이 노트북만 다시 열면 된다.

### 셀 1 — 환경 셋업
`01` 과 동일 패턴.

### 셀 2 — 설치 + 안전 점검
- `pip install mediapipe` (**버전 미고정** — §7 참조)
- `hand_landmarker.task` 모델 번들 다운로드 →
  `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`
  → `weights/` 에 저장. 멱등.
- **설치 후 `numpy` / `torch` / `ultralytics` 버전을 다시 출력**해 mediapipe 가 핀을 덮어썼는지 검사
  (session2 에서 ultralytics 가 torch 를 덮어썼는지 검사한 것과 같은 방어 패턴).

### 셀 3 — 사진 확보 (웹캠 1장, 폴백 필수)
- **코랩**: `google.colab.output.eval_js` + JS `getUserMedia` 로 **정지 사진 1장** 캡처 → `data/webcam.jpg`.
  **라이브 영상 스트림은 구현하지 않는다**(범위 밖).
- **폴백 3단**: 웹캠 거부/실패 → 파일 업로드 위젯 → 그것도 실패 → 샘플 이미지 다운로드
  `https://storage.googleapis.com/mediapipe-tasks/hand_landmarker/woman_hands.jpg`
- **어떤 경우에도 셀이 예외로 죽지 않아야 한다.** 수업 중 웹캠 권한 거부는 흔하다.

### 셀 4 — 손 랜드마크 (MediaPipe Tasks API)
**반드시 Tasks API 를 쓸 것. 레거시 `mp.solutions.hands` 는 2023년 폐기되어 최신 버전에서 동작을 보장할 수 없다.**

```python
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
base = mp_python.BaseOptions(model_asset_path=str(TASK_PATH))
opts = vision.HandLandmarkerOptions(base_options=base, num_hands=2)
with vision.HandLandmarker.create_from_options(opts) as lm:
    result = lm.detect(mp.Image.create_from_file(str(IMG_PATH)))
```
- 21개 랜드마크에 점 + 손가락 연결선(스켈레톤) 오버레이 → `outputs/04_hand.png`
- 손이 검출되지 않으면 그 사실을 친절히 출력(예외 금지).
- 출력: 검출된 손 개수, 좌/우(handedness), 랜드마크 21개라는 사실.

### 셀 5 — 전신 포즈 (YOLO11n-pose)
- `YOLO("yolo11n-pose.pt")` — **ultralytics 는 이미 핀되어 있어 새 의존성 0개**.
- 같은 사진(사람이 없으면 셀 3 폴백 이미지)에 17개 COCO 키포인트 스켈레톤 → `outputs/04_pose.png`
- 한 줄 출력:
  `"3회차에서 본 그 YOLO 입니다. 백본은 그대로, 헤드만 바뀌어 '네모'가 '관절'이 됐습니다."`

### 셀 6 — 비교 정리 (표만 출력, 학습 없음)
| | MediaPipe HandLandmarker | YOLO11n-pose |
|---|---|---|
| 찾는 것 | 손 | 사람 |
| 키포인트 | 21 | 17 |
| 라이선스 | Apache-2.0 | **AGPL-3.0** |

라이선스 줄에 한 마디: **3회차의 라이선스 함정이 여기서도 그대로 적용된다.**

---

## 6. `03_build_html.ipynb` — 빌더

`session3/notebooks/02_build_html.ipynb` 의 **직접 복제**. 차이는 이것뿐:
- 대상 세션 `session4`, 템플릿 `session4/session4_lecture_template.html`
- 주입 대상: §4 셀 10 의 그림 **11개**
- 결과: `outputs/session4_lecture.html` (자체완결 1파일)
- 임베드/누락 파일 목록 출력
- **`02_pose_demo` 산출물(`04_hand.png`, `04_pose.png`)은 주입하지 않는다** — 개인 얼굴/손 사진이라 레포·HTML 에 넣지 않는다. 라이브에서 화면으로만 본다.

> **템플릿 파일은 claude.ai 가 별도 제공한다. 클로드 코드는 템플릿을 작성하지 않는다.**
> 템플릿이 아직 없으면 빌더만 만들어 두고, 템플릿 부재 시 안내 메시지를 출력하게 한다.

---

## 7. `requirements.txt`

session3 의 **코랩 검증 완료 핀**을 그대로 가져오고, 학습에 필요한 것만 둔다.

```
torch==2.11.0
torchvision==0.26.0
ultralytics==8.4.76      # 02 의 YOLO11n-pose 용
numpy==2.0.2
matplotlib==3.10.0
Pillow==11.3.0
```

- **`mediapipe` 는 여기에 넣지 않는다.** `02` 셀 2 에서만 설치한다. 이유를 주석으로 명시:
  torch/numpy 핀을 덮어쓸 위험이 있어 학습 노트북 환경과 분리한다. 코랩 실행으로 안전이 확인되면
  그때 핀을 확정한다.
- `scikit-learn` 추가 금지 — 셀 8 은 numpy 로 직접 계산한다.

---

## 8. 하지 말 것 (스코프 고정)

- **freeze vs 전체 파인튜닝 비교 학습** — HTML 에서 표로만. 라이브 실행 안 함.
- **배치 크기 실험** — HTML 표로만.
- **학습 데이터 양 실험(100장 vs 전체)** — §9 질문 참조. **승인 전까지 구현하지 말 것.**
- **라이브 웹캠 영상 스트림** — 정지 사진 1장만.
- **ipywidgets 등 인터랙티브 위젯** — 코랩에서 불안정(2회차 결론). 인터랙티브는 HTML(JS) 담당.
- **HTML 템플릿 작성** — claude.ai 담당.
- **BCCD·혈액 데이터 재등장** — 이번 회차엔 쓰지 않는다.
- 스펙에 없는 기능·옵션 임의 추가 금지. 필요해 보이면 **추가하지 말고 질문/메모로 남긴다.**

---

## 9. 선생님 승인이 필요한 항목 (구현 전 물어볼 것)

1. **4번째 손잡이 "데이터 양"**: 클래스당 100장 vs 345장 전체 비교 1쌍을 셀 6.5 로 추가할지.
   (+1.5분, 3회차 "데이터 양 ≠ 성능" 서사와 정면으로 이어짐)
2. **백업 가중치 커밋**: 3회차처럼 라이브 실패 대비 가중치를 커밋할지.
   → 이번 실험은 회당 30~60초라 **불필요하다고 판단**. 대신 `runs.json` 만 있으면 그림은 다시 그려진다.

> **[승인 결과 2026-08-13] 2건 모두 승인 — 구현 완료.**
> 1. 셀 6.5 추가. `D_data_full` 1회만 새로 학습하고, 짝 비교 상대는 셀 5의 최적 lr 실험(`A_lr_*`)을
>    `runs.json` 에서 읽어 쓴다. 산출물 `04_datasize.png` 는 **필수 11장과 분리**해 관리한다
>    (셀 10은 별도 줄, 빌더는 선택 슬롯).
> 2. 백업 가중치 커밋. `.gitignore` 에 `!session4/weights/beans_resnet18_aug_backup.pt` 예외 추가.
>    셀 8 폴백 순서: `weights/C_aug_best.pt` → 커밋 백업 → `runs.json` 설정으로 재학습(30~60초).

---

## 11. 구현하며 스펙에서 의도적으로 벗어난 곳 (전부 근거 있음)

1. **train 1035 → 1034** — §2 정정 박스 참조.
2. **`NUM_WORKERS = 0 if os.name == "nt" else 2`** — 코랩(리눅스)은 스펙대로 2.
   윈도우 로컬 주피터만 0 (워커 spawn 이 멈추는 문제 회피).
3. **`run_experiment(..., n_per_class=None)` 허용** — `None` = train 전체. 승인된 셀 6.5 에 필요.
4. **`run_experiment` 가 실험별 최고 epoch 가중치를 `weights/<name>_best.pt` 로 저장** —
   셀 8·9가 재학습 없이 쓰고, 백업 가중치 항목의 전제. (`weights/` 는 gitignore 대상)
5. **셀 9 요약표에 `n/class` 열 추가** — 셀 6.5 때문에 실험별 데이터 양이 달라져, 없으면 표가 오해를 부름.
6. **레포 루트 `README.md` 세션 목록에 session4 추가** (하는 김에 빠져 있던 session3 행도 보정).

**설계 불변식 — 바꾸면 뒤 셀이 깨진다:**

- 실험 이름 `A_lr_1e-1`…`A_lr_1e-6`(셀5) / `B_overfit`(셀6) / `D_data_full`(셀6.5) / `C_aug`(셀7) 은
  셀 6·7·8·9 가 `runs.json` 에서 찾는 키다. 셀 6은 셀 5의 최고 lr 을, 셀 7은 셀 6의 설정을 읽어 쓴다(하드코딩 없음).
- 셀 5의 개별 5장은 `FIGSIZE`·`DPI`·`subplots_adjust`·`xlim`·`ylim` 을 하드코딩해 동일 크기를 보장한다.
  `tight_layout()` / `bbox_inches` 를 쓰면 크기가 틀어져 HTML 슬라이더에서 튄다.
- 셀 8의 트레이드오프는 **양성 = 병(2클래스 병합)**, 점수 = `P(angular)+P(rust)` 기준이다.
  그래야 "병든 잎을 놓치지 않으려면 recall" 문장과 방향이 맞는다.
- `03` 빌더는 `04_hand.png`·`04_pose.png` 를 **명시적 blocklist 로 차단**한다(개인 사진).
  템플릿에 슬롯이 있어도 주입하지 않고 자리표시만 남긴다.

---

## 10. 통과 조건 (구현 후 자가 점검 → 보고)

- [ ] `session4/` 가 CONVENTIONS 구조를 따르고, 세 노트북이 코랩에서 열린다
- [ ] 셀 3 실행 후 장수가 **train 1035 / val 133 / test 128**, 클래스별 수까지 §2 표와 일치
- [ ] 셀 5 의 5개 학습률에서 **눈에 띄게 다른 곡선**이 나온다 (1e-1 은 발산/정체, 1e-6 은 거의 안 움직임)
- [ ] 셀 5 의 개별 5장이 **동일한 축 범위·크기·여백**이다
- [ ] 셀 6 에서 train_acc 와 val_acc 가 **눈에 띄게 벌어진다**(과적합이 실제로 보인다)
- [ ] 셀 5~7 **전체 학습 시간 합이 8분 이내**다 (실측치를 보고할 것)
- [ ] 런타임을 새로 시작하고 셀 1·2·3 후 **셀 8 만** 돌려도 `runs.json` 으로 동작한다
- [ ] `02` 셀 3 이 웹캠 거부 상황에서도 **예외 없이** 폴백 이미지로 진행된다
- [ ] `02` 셀 2 가 mediapipe 설치 후 numpy/torch 버전을 출력한다
- [ ] `outputs/` 에 11개 그림 + `runs.json` 이 생긴다
- [ ] 셀 2 가 출력한 **실제 버전**으로 `requirements.txt` 핀이 맞다

보고 시 **실제로 몇 epoch·몇 회 학습을 돌려봤는지**와 **셀 5~7 실측 소요 시간**을 반드시 밝힐 것.
