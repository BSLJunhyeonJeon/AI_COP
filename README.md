# 박사후연구원 학습공동체 — 2회차 실습 자료

분류(classification) · 감지(detection) · 분할(segmentation) 세 가지 컴퓨터비전 태스크를
**개념과 체험으로** 이해하기 위한 2회차 학습 자료입니다. 코딩 경험이 없어도
**노트북을 열고 ▶ 만 누르면** 따라갈 수 있도록 만들었습니다.

> 현재 상태: **0단계(프로젝트 뼈대) 완료.** 1단계 이후 콘텐츠(데이터·모델·라벨링·증강)는 순차적으로 추가됩니다.

---

## 🚀 코랩에서 바로 시작 (학생용)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BSLJunhyeonJeon/AI_COP/blob/main/notebooks/00_setup.ipynb)

준비 절차는 두 단계가 전부입니다.

1. 위 **"Open in Colab"** 배지를 클릭합니다. → 코랩에서 `00_setup.ipynb` 가 열립니다.
2. 위에서부터 셀을 **▶ 순서대로** 실행합니다. 끝.

- 공개 레포라서 **로그인·토큰·계정이 필요 없습니다.**
- 구글 드라이브 마운트도 필요 없습니다.
- 첫 셀이 이 레포를 코랩에 자동으로 내려받아 준비합니다.
- 마지막 **셀 5**의 출력에서 실행 환경 · 프로젝트 루트 · GPU 사용 가능 여부 · 폴더 상태를 한눈에 확인하세요.

---

## 📁 폴더 구조

```
AI_COP/
├─ README.md              # 이 파일
├─ requirements.txt       # 의존성(버전 고정)
├─ data/                  # (비어 있음) 1단계에서 코드로 다운로드되어 채워짐
├─ weights/               # 사전학습 가중치 (이후 단계에서 다운로드)
├─ outputs/               # 실행 결과 저장 (캡처·마스크·애니메이션 등)
└─ notebooks/
   └─ 00_setup.ipynb      # 환경 확인 + 폴더 준비 (+ 데이터 다운로드 자리)
```

---

## 💻 로컬에서 실행 (선택)

1. 레포를 클론합니다.
   ```bash
   git clone https://github.com/BSLJunhyeonJeon/AI_COP.git
   cd AI_COP
   ```
2. 파이썬 가상환경을 만들고 의존성을 설치합니다.
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. 주피터에서 `notebooks/00_setup.ipynb` 를 열고 위에서부터 ▶ 실행합니다.

> **참고 — torch 버전 고정**: `requirements.txt` 의 `torch` 핀은 **코랩 사전설치 버전에 맞춰** 확정합니다.
> 코랩에서 `00_setup.ipynb` 를 한 번 실행하면 셀 5가 torch 버전을 출력하며, 그 값으로 핀을 채웁니다.
> (핀이 채워지기 전이라면 로컬에서는 `pip install torch` 로 임시 설치한 뒤 스모크 테스트를 진행할 수 있습니다. 자세한 안내는 `requirements.txt` 주석 참고.)
