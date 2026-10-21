# session6 — 빌려 쓰는 AI: 학습 없이 쓰는 모델과 에이전트의 손(MCP)

학습공동체의 마지막 회차입니다. 2~5회차를 한 장으로 정리하고, 모임이 끝난 뒤 각자 **무료로 써 볼 수 있는** 사전학습 모델과 MCP(에이전트에 도구를 연결하는 표준 플러그), 그리고 말로 3D 부품을 만드는 Fusion 360 MCP 를 소개합니다.

> 공통 규칙은 레포 루트의 [CONVENTIONS.md](../CONVENTIONS.md) 를 따릅니다. 이번 회차는 5회차처럼 참가자용 노트북이 없습니다 — 근거와 결정 사항은 [docs/session6_spec_borrowed_ai.md](../docs/session6_spec_borrowed_ai.md) §8·§13.

---

## 파일

```
session6/
├─ session6_lecture.html           # ★ 강의 자료 — 브라우저로 여세요 (그림 포함 한 파일, 1.2 MB)
├─ session6_lecture_template.html  # 편집용 원본 (그림 자리만 있음) → tools/build_html.py 로 위 파일 생성
├─ requirements.txt                # 검증 예시 재현용 (버전 고정)
├─ tools/
│  ├─ zero_shot_check.py           # Cellpose·InstanSeg 를 공개 H&E(NuInsSeg)에 학습 없이 → 정답과 채점, 그림 1·2
│  ├─ sem_check.py                 # SEM 입자: Fiji 기본 방식 vs NP-SAM 채점, 그림 3
│  ├─ npsam_run.py                 # NP-SAM 실행 (별도 conda 환경)
│  ├─ remote_zip.py                # 큰 zip 에서 필요한 파일만 부분 다운로드
│  └─ build_html.py                # 템플릿 + outputs/ 그림 → session6_lecture.html
├─ data/                           # (비어 있음) --fetch 가 공개 데이터 일부를 받아 채움
└─ outputs/                        # (비어 있음) 채점 결과·그림
```

강의 자료의 각 장 끝에 있는 **“따라 해 보기”** 상자가 모임 이후 혼자 해 보는 절차입니다. 마지막 **부록 점검표**에 강사 노트북에서 실제로 돌려 본 결과와 걸린 함정이 있습니다.

## 검증 예시 다시 만들기 (선택, 강사용)

윈도우 아나콘다 프롬프트, `session6` 폴더에서:

```bat
conda create -n ai_cop_session6 python=3.11 -y
conda activate ai_cop_session6
pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt

python tools/zero_shot_check.py --fetch          :: NuInsSeg 1.6 GB zip 에서 58장만 (약 25 MB, 2분)
python tools/zero_shot_check.py --run            :: Cellpose 채점 + 그림 1·2
python tools/zero_shot_check.py --run --engine instanseg --pixel-size 0.25 --tag inst_025

python tools/sem_check.py --fetch                :: BAM SEM 2파일 + NFFA 앞쪽 12장 (tar 를 흘려 읽다 멈춤)
python tools/sem_check.py --fiji "C:/.../Fiji.app/ImageJ-win64.exe"
::  NP-SAM 은 별도 환경 — tools/npsam_run.py 머리말 참고 (set PYTHONUTF8=1 필요)
python tools/sem_check.py --score                :: 채점 + 그림 3

python tools/build_html.py                       :: session6_lecture.html 생성
```

## 데이터 출처

- **NuInsSeg** — Mahbod et al., *Sci Data* 11, 295 (2024), [zenodo 10518968](https://zenodo.org/records/10518968), CC BY 4.0
- **BAM TiO₂ SEM** — Rühle et al., *Sci Rep* (2021), [zenodo 4563942](https://zenodo.org/records/4563942), CC BY-NC-ND 4.0 (채점 숫자만 사용, 결과 그림은 싣지 않음)
- **NFFA-EUROPE SEM** — Aversa et al., *Sci Data* (2018), [b2share 862nr-cn036](https://b2share.eudat.eu/records/862nr-cn036), CC BY 4.0
- 참가자 실습용으로 소개만: BBBC010 (CC0), Tierpsy 테스트 데이터 (MIT)
