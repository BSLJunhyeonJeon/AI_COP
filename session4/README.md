# session4 — 학습(Training): 손잡이를 돌리면 성능이 변한다

3회차는 학습을 **돌려 봤습니다**. 4회차는 학습이 **잘 되고 있는지 읽는 법**을 배웁니다.
학습률·에폭·증강·데이터 양 — 손잡이를 하나씩 돌리며 성능이 어떻게 변하는지 눈으로 봅니다.

실험 1회가 **30~60초**입니다. "누르고 기다리는" 수업이 아니라 **여러 번 돌려 보는** 수업입니다.

> 공통 규칙은 레포 루트의 [CONVENTIONS.md](../CONVENTIONS.md) 를 따릅니다.

---

## 🚀 코랩에서 바로 시작 (수업용)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BSLJunhyeonJeon/AI_COP/blob/main/session4/notebooks/01_train_lab.ipynb)

1. 위 **"Open in Colab"** 배지를 클릭합니다 → `session4/notebooks/01_train_lab.ipynb` 가 열립니다.
2. **런타임 > 런타임 유형 변경 > GPU(T4)** 로 설정합니다.
3. 셀을 위에서부터 ▶ 실행합니다.

---

## ⚠️ 실행 순서 (중요)

```
01_train_lab  →  03_build_html  →  02_pose_demo   ← 02 는 반드시 맨 마지막
```

- `03_build_html` 은 `01` 이 만든 `outputs/` 를 읽습니다. **`01` 을 먼저** 돌리세요.
- `02_pose_demo` 는 **`mediapipe` 를 설치**해 런타임의 패키지 구성을 바꿀 수 있습니다.
  그래서 **`01` → `03` 을 끝낸 뒤 맨 마지막**에 엽니다.
  문제가 생기면 **런타임 재시작 후 `02` 만 다시** 열면 됩니다(`01`·`03` 결과물은 그대로 남습니다).

---

## 📁 폴더 구조

```
session4/
├─ README.md              # 이 파일
├─ requirements.txt       # 의존성(버전 고정) — mediapipe 는 여기 없음(02 에서만 설치)
├─ setup_env.bat / .sh    # 로컬 conda 환경 자동 셋업 (ai_cop_session4)
├─ data/                  # (비어 있음) 01 셀 3이 beans 를 받아 채웁니다
├─ weights/               # 실험별 최고 epoch 가중치 + 라이브 백업
├─ outputs/               # 결과 그림 11(+1)장 + runs.json
└─ notebooks/
   ├─ 01_train_lab.ipynb  # ★ 수업용 (라이브에서 이걸 엽니다)
   ├─ 02_pose_demo.ipynb  # 웹캠 손·전신 포즈 (독립 실행, 맨 마지막)
   └─ 03_build_html.ipynb # 강의자료 빌더 (수업 전에 1회 실행)
```

---

## 🔬 01_train_lab 에서 돌리는 실험

| 셀 | 실험 | 바꾸는 손잡이 | 산출물 |
|---|---|---|---|
| 5 | A — 학습률 | `lr` 5개 값 (1e-1 … 1e-6), 8 epoch | `04_lr_compare.png` + 개별 5장 |
| 6 | B — 과적합 | `epochs` 30 | `04_overfit.png` |
| 6.5 | D — 데이터 양 | 클래스당 100장 vs train 전체 | `04_datasize.png` |
| 7 | C — 증강 | `aug=True` | `04_aug.png` |
| 8 | 지표 심화 | (학습 없음) | `04_confusion.png`, `04_tradeoff.png` |
| 9 | 요약 + **test 개봉** | (학습 없음) | 표 + test 정확도 |

모든 실험 결과는 **`outputs/runs.json` 에 누적**됩니다(같은 이름은 덮어씀).
런타임이 끊겨도 뒤 셀이 앞 결과를 읽어 그림을 다시 그립니다 — 다시 학습하지 않습니다.

> **수업 중 런타임이 끊겼다면**: 셀 **1 → 2 → 3 → 4** 를 다시 실행한 뒤, 보던 셀로 바로 가세요.
> 셀 4는 함수를 **정의만** 해서 1초도 안 걸립니다(학습하지 않습니다). 셀 5~7 을 다시 돌릴 필요는
> 없습니다 — 셀 8·9 는 `runs.json` 과 `weights/` 에 남은 결과를 읽습니다.

**`test/` 는 셀 9에서 딱 한 번만** 엽니다.

---

## 💻 로컬에서 실행 (선택, 아나콘다 기준)

```bash
git clone https://github.com/BSLJunhyeonJeon/AI_COP.git
cd AI_COP/session4
# 윈도우: setup_env.bat   /   맥·리눅스: chmod +x setup_env.sh && ./setup_env.sh
conda activate ai_cop_session4
jupyter notebook notebooks/01_train_lab.ipynb
```

> GPU 없는 로컬에서는 실험 1회가 수 분씩 걸립니다. **코랩 T4 사용을 권장**합니다.

---

## 데이터 출처

- **beans (ibean)** — [Makerere AI Lab](https://github.com/AI-Lab-Makerere/ibean) / HuggingFace [`AI-Lab-Makerere/beans`](https://huggingface.co/datasets/AI-Lab-Makerere/beans), **MIT**.
  콩잎 병해 사진 500×500 RGB. 클래스: `angular_leaf_spot` / `bean_rust` / `healthy`.
  공식 분할을 **그대로** 사용합니다.

| split | 총 | angular_leaf_spot | bean_rust | healthy |
|---|---|---|---|---|
| train | **1034** | 345 | 348 | 341 |
| validation | **133** | 44 | 45 | 44 |
| test | **128** | 43 | 43 | 42 |

> 세 클래스가 **거의 균형**(약 1.01 : 1.02 : 1.00)입니다. 3회차 BCCD 는 11배 불균형이었죠.
> 오늘은 성능이 안 나와도 **데이터 탓을 할 수 없습니다**.
>
> **참고**: `train.zip` 안에는 파일이 1035개 있지만 그중 1개(`healthy_train.120tore`)는 이미지가 아니라
> 배포 과정에 섞여 들어간 **macOS 파인더 메타데이터**(`.DS_Store` 형식)입니다. 셀 3이 이 파일을 지우므로
> 실제 학습에 쓰이는 이미지는 **1034장**입니다.

---

## 라이브 백업 (수업 중 실패 대비)

`weights/beans_resnet18_aug_backup.pt` 가 있으면 **셀 8** 이 학습 없이 그 가중치로 돌아갑니다.
없으면 셀 8이 `runs.json` 의 설정으로 **자동 재학습(30~60초)** 하므로 수업이 멈추지는 않습니다.

백업을 만들려면 코랩에서 `01` 을 한 번 완주한 뒤:

```bash
cp weights/C_aug_best.pt weights/beans_resnet18_aug_backup.pt
```

이 경로만 `.gitignore` 예외로 커밋되도록 열어 두었습니다(약 45MB).
