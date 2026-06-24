# session2 — 분류 · 감지 · 분할 체험

분류(classification) · 감지(detection) · 분할(segmentation) 세 가지 컴퓨터비전 태스크를
**개념과 체험으로** 이해하기 위한 2회차 실습 자료입니다. 코딩 경험이 없어도
**노트북을 열고 ▶ 만 누르면** 따라갈 수 있도록 만들었습니다.

> 현재 상태: **0단계(프로젝트 뼈대) 완료.** 1단계 이후 콘텐츠(데이터·모델·라벨링·증강)는 순차적으로 추가됩니다.
> 공통 규칙은 레포 루트의 [CONVENTIONS.md](../CONVENTIONS.md) 를 따릅니다.

---

## 🚀 코랩에서 바로 시작 (학생용)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BSLJunhyeonJeon/AI_COP/blob/main/session2/notebooks/00_setup.ipynb)

준비 절차는 두 단계가 전부입니다.

1. 위 **"Open in Colab"** 배지를 클릭합니다. → 코랩에서 `session2/notebooks/00_setup.ipynb` 가 열립니다.
2. 위에서부터 셀을 **▶ 순서대로** 실행합니다. 끝.

- 공개 레포라서 **로그인·토큰·계정이 필요 없습니다.** 드라이브 마운트도 없습니다.
- 첫 셀이 레포를 코랩에 내려받아 `session2` 폴더를 작업 루트로 잡습니다.
- 마지막 **셀 5**의 출력에서 실행 환경 · 프로젝트 루트(`session2`) · GPU 사용 가능 여부 · 폴더 상태를 한눈에 확인하세요.

---

## 📁 폴더 구조

```
session2/
├─ README.md              # 이 파일
├─ requirements.txt       # 의존성(버전 고정)
├─ setup_env.bat          # 윈도우: conda 환경 자동 셋업
├─ setup_env.sh           # 맥/리눅스: conda 환경 자동 셋업
├─ data/                  # (비어 있음) 1단계에서 코드로 다운로드되어 채워짐
├─ weights/               # 사전학습 가중치 (이후 단계에서 다운로드)
├─ outputs/               # 실행 결과 저장 (캡처·마스크·애니메이션 등)
└─ notebooks/
   └─ 00_setup.ipynb      # 환경 확인 + 폴더 준비 (+ 데이터 다운로드 자리)
```

---

## 💻 로컬에서 실행 (선택, 아나콘다 기준)

**아나콘다(또는 미니콘다)가 설치돼 있다고 가정**합니다. 설치돼 있지 않으면 스크립트가 안내 후 종료합니다.

1. 레포를 클론하고 이 세션 폴더로 이동합니다.
   ```bash
   git clone https://github.com/BSLJunhyeonJeon/AI_COP.git
   cd AI_COP/session2
   ```
2. conda 환경 자동 셋업 스크립트를 실행합니다.
   - **윈도우** (Anaconda Prompt 권장): `setup_env.bat`
   - **맥/리눅스**: `chmod +x setup_env.sh && ./setup_env.sh`

   → `ai_cop_session2` 환경을 만들고(`requirements.txt` 설치) 다음 단계를 안내합니다. (이미 있으면 그대로 사용 — 멱등)
3. 환경을 활성화하고 주피터에서 노트북을 엽니다.
   ```bash
   conda activate ai_cop_session2
   jupyter notebook notebooks/00_setup.ipynb
   ```

> **버전 고정 안내**: `requirements.txt` 의 `torch` 핀과 셋업 스크립트의 `PY_VERSION` 은 **코랩 사전설치 버전에 맞춰** 확정합니다.
> 코랩에서 `00_setup.ipynb` 셀 5를 한 번 실행하면 Python·torch 버전이 출력되며, 그 값으로 핀을 채웁니다.
> (확정 전에는 torch 미설치/conda 기본 Python 으로 동작하며, 노트북은 그래도 에러 없이 상태를 보고합니다.)
