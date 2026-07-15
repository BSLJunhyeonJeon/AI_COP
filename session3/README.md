# session3 — 전이학습(파인튜닝): YOLO11n 을 우리 혈액 데이터로 길들이기

2회차의 클라이맥스는 **"COCO 사전학습 YOLO11n 이 혈액 도말에서 빗나갔다"** 였습니다.
3회차는 **바로 그 모델을 우리 데이터(BCCD)로 파인튜닝해서 맞히게 만드는 것**이 결말입니다.

> 공통 규칙은 레포 루트의 [CONVENTIONS.md](../CONVENTIONS.md) 를 따릅니다.

---

## 🚀 코랩에서 바로 시작 (수업용)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BSLJunhyeonJeon/AI_COP/blob/main/session3/notebooks/01_finetune.ipynb)

1. 위 **"Open in Colab"** 배지를 클릭합니다 → `session3/notebooks/01_finetune.ipynb` 가 열립니다.
2. **런타임 > 런타임 유형 변경 > GPU(T4)** 로 설정합니다. (학습 속도가 여기서 갈립니다)
3. 셀을 위에서부터 ▶ 실행합니다.

> **수업 진행**: **셀 4(학습)** 를 누르고 이론 강의로 넘어갑니다(무료 T4에서 10~15분).
> 강의 후 돌아와 **셀 5~9** 를 실행해 결과를 확인합니다.
> 학습이 실패해도 **백업 가중치**로 셀 6~8 이 그대로 돌아갑니다.

---

## 📁 폴더 구조

```
session3/
├─ README.md              # 이 파일
├─ requirements.txt       # 의존성(버전 고정)
├─ setup_env.bat / .sh    # 로컬 conda 환경 자동 셋업 (ai_cop_session3)
├─ data/                  # (비어 있음) 셀 3이 BCCD 를 받아 YOLO 형식으로 채움
├─ weights/               # 학습된 가중치 (셀 4 결과 + 라이브 백업)
├─ outputs/               # 결과 그림 (곡선·전후비교·conf 스윕·클래스별 성능)
└─ notebooks/
   ├─ 01_finetune.ipynb   # ★ 수업용 (라이브에서 이걸 엽니다)
   └─ 02_build_html.ipynb # 강의자료 빌더 (수업 전에 1회 실행)
```

---

## 💻 로컬에서 실행 (선택, 아나콘다 기준)

```bash
git clone https://github.com/BSLJunhyeonJeon/AI_COP.git
cd AI_COP/session3
# 윈도우: setup_env.bat   /   맥·리눅스: chmod +x setup_env.sh && ./setup_env.sh
conda activate ai_cop_session3
jupyter notebook notebooks/01_finetune.ipynb
```

> GPU 없는 로컬에서는 셀 4가 자동으로 짧은 학습(5 epoch)으로 분기하지만 결과가 약합니다. **코랩 T4 사용을 권장**합니다.

---

## 데이터 출처

- **BCCD** ([Shenggan/BCCD_Dataset](https://github.com/Shenggan/BCCD_Dataset), MIT) — 혈액 도말 364장 + Pascal VOC 박스.
  공식 분할(train 205 / val 87 / test 72)을 **그대로** 사용합니다. 클래스: `RBC` / `WBC` / `Platelets`.
