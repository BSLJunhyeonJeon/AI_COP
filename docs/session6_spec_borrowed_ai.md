# 6회차 스펙 — 마무리: 지난 회차 한 장 요약 + 빌려 쓰는 AI (사전학습 모델 · MCP · Fusion 360)

> 대상: 이 스펙을 구현하는 클로드 + 사람(준현).
> 전제: 레포 루트 `CONVENTIONS.md` 가 상위 규칙. 충돌 시 CONVENTIONS 우선 — 단, §8 의 예외는 승인 후 이 스펙이 적용한다.
> 범위: `session6/` 신규 생성. 참가자용 노트북은 기본적으로 없다(§13-2).
> 금지: 스펙에 없는 도구·기능 임의 추가. 확인하지 않은 내용을 사실로 적기. 유료 도구를 "무료"로 소개하기.
> 작업 후: 무엇을 만들었는지 + 사람이 확인하는 법 + 직접 돌려본 범위를 보고한다.
> 작성일: 2026-10-22. 도구·라이선스·요금 정보는 같은 날 웹 조사(공식 페이지 위주)로 확인했다. ✓ = 1차 출처에서 확인, ~ = 2차 출처이거나 추정, 미확인 = 확인하지 못함. 자주 바뀌는 항목은 §11 에서 수업 직전에 다시 확인한다.

---

## 0. 이 회차의 한 문장

학습시키기 전에 먼저 빌려 본다. 빌릴 때는 라이선스와 데이터가 어디로 가는지 본다.

- 학습공동체의 **마지막 모임(예정)** 이다. 앞부분은 2~5회차를 한 장으로 정리하고, 뒷부분은 모임이 끝난 뒤 각자 무료로 써 볼 수 있는 사전학습 모델과 MCP 를 소개한다.
- 참가자는 **자기 데이터를 가져올 수 없다.** 그래서 개인 데이터 실습은 하지 않는다. 원래 목표였던 "각자 분야에 맞는 분석용 AI" 는 §7 의 "내 데이터로 이어가는 3단계" 로 회수한다(모임 이후 각자 연구실에서).
- 흐름: 2~4회차 = 모델을 **만드는** 법, 5회차 = 에이전트에게 일을 **시키는** 법, 6회차 = 이미 있는 모델과 도구를 **빌려서 에이전트에 연결하는** 법. MCP 는 5회차 하네스에 다는 "손" 이다.
- 대상 분야는 **TME 면역세포 · 예쁜꼬마선충 행동 · LSPR 나노소재(SEM)** 3개. **PDA 비색 센서는 이번 회차 사례에서 제외**한다(준현 결정, 2026-10-22).

---

## 1. 산출물 트리

```
session6/
├─ README.md               # 사람용 — 회차 소개, 파일 안내, 모임 이후 참고 순서
├─ session6_lecture.html   # 강의 자료(단독 열람 한 파일). Part 1~5 + 리허설 캡처
├─ CATALOG.md              # ★ 모델·MCP 카탈로그 — 모임 이후 참고용 단일 출처 (이름·용도·무료 경로·라이선스·확인일)
├─ MCP_GUIDE.md            # 참가자용 — 커넥터 켜기, 로컬 MCP 설치, 데이터 주의, 무료로 이어가기
└─ demos/
   ├─ prompts.md           # 시연에 쓰는 프롬프트 원문 (Part 3 MCP, Part 4 Fusion)
   └─ fusion/              # Fusion 시연 결과 — STL(소용량) + 스크린샷. 녹화 영상은 커밋하지 않는다
```

- **수업 당일 판(§13-1)**: `CATALOG.md`·`MCP_GUIDE.md` 는 강의 HTML 에 합쳐서 만들지 않는다. 실제로 만드는 것은 `README.md`, `session6_lecture.html`, `tools/`(검증 예시 재현 스크립트)다.
- 시연용 이미지·영상은 레포에 넣지 않는다(규칙 2). 출처 링크와 라이선스를 강의 HTML 에 적는다.
- 노트북을 만들기로 하면(§13-2) `notebooks/01_zero_shot_check.ipynb` 하나를 추가하고, 그때는 `requirements.txt`·conda 스크립트도 둔다.

---

## 2. 수업 구성 (약 120분)

| Part | 시간 | 내용 | 방식 |
|---|---|---|---|
| 1. 지난 회차 한 장 요약 | 20분 | STEP 1~5 지도 + 회차별 "한 줄 정리" | 강의 |
| 2. 학습 없이 쓰는 모델 | 35분 | 공통 1개 + 분야별 1개. 검증 · 라이선스 · "안 쓰는 게 정답" | 웹 데모·GUI 시연 |
| 3. MCP — 에이전트의 손 | 35분 | 문헌 검색 · 그림 · 모델 찾기 · napari 조작 | 라이브 + 참가자 1개 직접 |
| 4. Fusion 360 시연 | 15분 | 96-well plate 트레이를 말로 만들고 수정 | 강사 화면 |
| 5. 혼자 이어가기 | 15분 | 무료로 계속 쓰는 길, 데이터 주의, 내 데이터로 이어가는 3단계 | 강의 + 마무리 |

---

## 3. Part 1 — 지난 회차 한 장 요약 (20분)

새 내용은 없다. 각 회차 강의 HTML 에 이미 있는 그림·문장을 재사용한다.

| 회차 | 주제 | 데이터 · 모델 | 한 줄 정리 (원문) | 6회차와의 연결 |
|---|---|---|---|---|
| 2 | 분류·감지·분할, 데이터 형식, SAM2 라벨링, 증강 | BCCD 혈액 · YOLO11n·SegFormer 추론 | "모델은 도구일 뿐입니다. 좋은 데이터와 라벨, 그리고 적절한 증강이 결과를 만듭니다." | SAM2 클릭 라벨링 → SAM 3·micro-sam |
| 3 | 전이학습(파인튜닝) | BCCD · YOLO11n | "모델은 지도에서 고르고, 데이터로 길들이고, 목적에 맞는 자로 잰다. 그리고 때로는, 안 쓰는 게 정답이다." | AGPL 함정 → 라이선스 3겹 / "안 쓰는 게 정답" → SEM 비교 |
| 4 | 학습 읽기 — 학습률·에폭·증강·데이터 양, 지표 | beans · ResNet18 | (강의에 한 줄 정리 박스 없음 — Wrap-up 발췌) "한 번에 하나만 바꾼다. test 는 마지막에 딱 한 번. 지표는 연구 질문이 정한다." | 빌린 모델도 Dice/F1 로 잰다 |
| 5 | 프로젝트 루트(하네스) | FlyWire 커넥톰 · LIF | "모델은 빌리는 것이고, 폴더는 내 것이다. 폴더가 좋으면 어떤 모델도 일한다." | MCP = 하네스에 다는 손 |

- STEP 1~5 지도(2회차 Part 1·8) 를 다시 띄우고, 이번엔 다섯 칸이 모두 "완료" 인 상태로 보여 준다.
- 4회차 한 줄은 발췌이므로 강의 HTML 에 "Wrap-up 에서" 라고 표기한다.

---

## 4. Part 2 — 학습 없이 쓰는 모델 (35분)

원칙: **참가자가 아무것도 설치하지 않는다.** 시연은 웹 데모 또는 강사 PC 의 GUI 로 한다. 분야당 1개(SEM 만 비교용 1개 추가), 공통 1개.

| 분야 | 도구 (버전·날짜) | 입력 → 출력 | 무료 경로 | 라이선스 | 약점 |
|---|---|---|---|---|---|
| 공통 | **SAM 3** ✓ (2025-11-19), SAM 3.1 ✓ (2026-03-27) | 이미지·영상 + **글자**("worm")/점/박스 → 해당 물체 전부의 마스크 | Segment Anything Playground (웹) | 자체 "SAM License"(오픈소스 아님). 저작자 표시 필요, 군사 용도 금지. HF 가중치는 승인제 ✓ | 병리 핵에는 글자 지시가 잘 안 먹힘(arXiv 2604.18225) → 점·박스로 |
| TME 면역세포 | **Cellpose 4** ✓ (4.2.1.1, 2026-06-14, `cpsam` 등) | 세포·핵 이미지 → 개별 마스크 | HF Space(무료 GPU 하루 약 5분 ✓), cellpose.org, 공식 코랩 | 코드 BSD-3(README 배지는 GPL — 출처끼리 불일치). **가중치는 CC-BY-NC 데이터로 학습 → 사실상 비상업** | 세포가 아닌 물체 |
| TME 면역세포 | **QuPath 0.7.0 + InstanSeg** ✓ | H&E·H-DAB·다중 형광 → 세포 검출 → 마커 분류·공간 분석 | GUI, CPU 로 동작 | 코드 Apache-2.0, 모델 라이선스 명시 없음 | 학습 데이터와 다른 염색·배율 |
| 선충 | **Tierpsy Tracker** ✓ | 영상 → 골격 + 행동 지표 | 설치형(Docker 권장) | MIT | 몸을 말거나 서로 겹칠 때 |
| SEM 나노입자 | **NP-SAM** ✓ (`npsam` 3.2.3, 2025-07-25) | 전자현미경 이미지 → SAM 마스크 + 과·소분할 필터 → 크기·형태 통계 | 윈도우 실행 파일(CUDA 판 약 2.5 GB, CPU 판 약 500 MB) | Apache-2.0 | 입자 겹침 |
| SEM 나노입자 (비교) | **Fiji 기본 방식** | 스케일 지정 → 임계값 → watershed → Analyze Particles → 크기 분포 | 무료 GUI | GPL ~ | 뭉친 입자, 스케일바 영역이 입자로 잡힘(잘라내야 함) |

### 함께 짚을 점 (Part 2 의 메시지)

1. **학습 없이 써도 검증은 한다.** 정답 마스크가 있는 이미지 1장(또는 손으로 20개쯤 라벨)으로 Dice/F1 을 재서 보여 준다. 4회차 지표를 그대로 쓴다. 수치는 리허설(§9-4)에서 미리 계산해 강의 자료에 넣는다.
2. **라이선스는 세 겹이다 — 코드 · 가중치 · 학습 데이터.** Cellpose 처럼 코드는 BSD 여도 가중치는 비상업일 수 있다. 3회차 AGPL 함정의 연장. 참고: SAM 을 `ultralytics` 패키지로 돌리면 AGPL 래퍼를 거친다 ~ → Meta 공식 레포나 `transformers` 를 쓴다.
3. **때로는 안 쓰는 게 정답이다.** 같은 SEM 이미지 두 장(입자가 잘 떨어진 것 / 뭉친 것)에 Fiji 기본 방식과 NP-SAM 을 나란히 돌린다. 떨어진 입자는 Fiji 로 충분하고, 뭉친 입자에서만 NP-SAM 이 낫다는 걸 보여 준다(리허설에서 실제로 그렇게 나오는지 확인하고, 아니면 나온 대로 서술한다).

### 소개만 하고 시연하지 않는 것 (한 줄씩)

- 병리 파운데이션 모델 **UNI2-h · CONCH · Virchow2** ✓: 승인제, 기관 이메일 필요(gmail 거절), CC-BY-NC-ND, 임상 사용 금지(Virchow2). 세포를 세는 도구가 아니라 특징 벡터를 내는 도구.
- **CellViT++** ✓: GPU 메모리 24 GB 이상 필요 → 무료 코랩 불가.
- **micro-sam** ✓ (1.8.14, 2026-09-06, MIT): napari 에서 클릭·자동 분할, 병리·전자현미경 전용 모델 포함. Part 3 napari 시연과 이어진다.
- 선충용 **DeepLabCut·SLEAP** ✓: 선충 사전학습 모델이 없다 → 라벨링이 필요해 "빌려 쓰기" 대상이 아님.

### 시연 샘플 데이터

분야별 공개 이미지·영상 1세트씩. 후보 선정과 라이선스 확인은 §9-2 에서 한다(아직 미정). 조건: 무료 공개, 교육 목적 사용 가능, 출처 명시 가능, TME 는 환자 식별 정보 없음.

---

## 5. Part 3 — MCP: 에이전트의 손 (35분)

한 줄 설명: MCP 는 에이전트가 바깥 도구·데이터베이스를 부르는 표준 플러그다. 5회차에서 폴더(하네스)를 만들었다면, 오늘은 그 에이전트에 손을 단다.

| 등급 | MCP / 커넥터 | 하는 일 | 비용 ✓ | 연결 | 분야 |
|---|---|---|---|---|---|
| A 라이브 · 참가자 직접 | **PubMed** (Anthropic) | 검색, 메타데이터, 관련 논문, PMC 전문 | 무료, 로그인 없음 | Claude 기본 커넥터 | 전체 |
| A 라이브 | **bioRxiv/medRxiv** (Anthropic) | 프리프린트 검색·열람 | 무료, 로그인 없음 | 기본 커넥터 | TME·선충 |
| B 라이브 | **Consensus** / **Scholar Gateway**(Wiley) | 근거 검색 / Wiley 전문 | 무료 계정(사용량 한도 미확인) | 기본 커넥터 | 전체(LSPR 포함) |
| B 라이브 | **BioRender** (공식) | 아이콘·템플릿 검색, 그림 초안 | 무료 계정, 일부 프리미엄 자산 제한 | 기본 커넥터 | TME·선충 |
| B 라이브 | **Hugging Face** (공식) | 모델·데이터셋·논문·Space 검색 | 무료 계정 | 기본 커넥터 | 전체 — Part 2 와 연결 |
| C 강사 시연 | **napari-mcp** (royerlab, BSD-3) | 에이전트가 napari 를 조작(레이어, 스크린샷, 파이썬 실행) | 무료 | 로컬 `pip install napari-mcp` | 전체 |
| C 소개 | **Zotero MCP** (커뮤니티, MIT) | 내 Zotero 라이브러리·PDF 검색 | 무료 | 로컬 설치 | 전체 |
| D 한 줄 소개 | **Owkin** (공식) | TCGA H&E 에서 세포 유형 수·TME 특징 | 로그인 필요, 가격 미확인 | 기본 커넥터 | TME (공개 TCGA 만, 내 슬라이드 업로드는 문서에 없음) |
| D 한 줄 소개 | **BioContextAI KB** (학계) | Europe PMC·STRING·Reactome·PanglaoDB 등 묶음 | 무료(원격 엔드포인트는 시험용) | 로컬 / 원격 | TME |
| D 한 줄 소개 | **WormBase MCP** | 유전자·표현형·균주 | 무료 | 로컬 `npx` | 선충 (매우 초기 — 커밋 11개) |

### 시연 시나리오 (프롬프트 원문은 `demos/prompts.md`)

1. PubMed — "최근 2년간 예쁜꼬마선충 행동 정량화에 딥러닝을 쓴 논문 5편을 찾아 방법·데이터·코드 공개 여부를 표로."
2. bioRxiv — "최근 6개월 TME 면역세포 공간 분석 프리프린트."
3. Hugging Face — "SEM 나노입자 분할 모델과 데이터셋을 찾아 라이선스 열을 포함한 표로." (Part 2 의 라이선스 3겹과 연결)
4. BioRender — 분야 하나를 골라 모식도 초안.
5. napari-mcp (강사 PC) — "이 이미지를 napari 로 열고 분할해서 개수와 면적 분포를 보여 줘." Part 2 의 모델을 에이전트가 직접 부르는 장면.

- 참가자 직접 실습은 **PubMed 커넥터 1개만**(설치 없음, 로그인 없음). 나머지는 강사 화면.
- 넣지 않는 것: Fiji MCP(개념 증명 단계, 수동 빌드 필요), arXiv 커뮤니티 서버(버전·라이선스 표기 불일치), PubChem MCP(확인된 서버 없음).
- 보안: napari-mcp 의 코드 실행 기능은 아무 파이썬이나 돌린다(로컬 인증 없음). **강사 PC 에서만**, 도구 호출마다 승인. 참가자에게 설치를 지시하지 않는다.

---

## 6. Part 4 — Fusion 360 시연 (15분)

### 확인된 사실 (2026-10-22)

- **공식 Fusion MCP 서버가 Fusion 데스크톱에 내장**돼 있다 ✓. Autodesk 문서상 정식 버전(GA). 켜는 곳: 환경설정 > General > API > "Fusion MCP Server (runs locally on this device)". 주소 `http://127.0.0.1:27182/mcp`, 같은 PC 에서만 동작, 웹판 Fusion 에서는 안 됨.
- 2026-04-28 Anthropic "Claude for Creative Work" 발표 때 함께 나왔다 ✓. Claude 데스크톱에 **"Autodesk Fusion" 커넥터**(Autodesk 제작) ✓.
- 할 수 있는 것(Autodesk 블로그 2026-06-29 ✓): 열린 설계 읽기(크기·질량·재료·타임라인·매개변수), 이름 붙은 시점 스크린샷, Fusion API 파이썬 실행, 매개변수 일괄 수정, STL·STEP·F3D 내보내기, 단순 부품(돌출·구멍·필렛·쉘·패턴). Autodesk 스스로 "복잡한 모델·전체 조립품에는 아직 믿을 만하지 않다" 고 적었다.
- 클라우드판 **Fusion Compute MCP** 는 공개 베타(2026-09-15 발표) ✓ — Autodesk 로그인 + 유효 라이선스 + Fusion Team 허브 필요. 이번 시연에는 쓰지 않는다.
- Claude Code 연결(`claude mcp add --transport http fusion http://127.0.0.1:27182/mcp`)은 제3자 안내뿐이다 — 미확인. 시연은 Claude 데스크톱으로 한다.

### 라이선스 (시연 방식을 정하는 이유)

- Anthropic·Autodesk 모두 **"Fusion 구독자용"** 으로 소개한다 ✓. 상용 구독 연 $680.
- 개인용 무료 라이선스: MCP 허용 여부를 밝힌 Autodesk 공식 문서를 찾지 못함(미확인). 게다가 개인용 약관은 "주 업무·회사 환경" 을 제외하므로 연구실 업무는 해당하지 않을 가능성이 크다(해석).
- 교육용: 연구실은 대상 외로 적혀 있다 ✓ → 박사후연구원은 해당이 불확실하다.
- **30일 무료 체험판에서 공식 커넥터가 작동했다는 블로그 사례 1건** ~ → 강사 시연은 체험판 또는 기존 구독으로 한다(§13-4).
- 그래서 **참가자 실습이 아니라 강사 시연**이다. 참가자에게는 §6 끝의 무료 대안을 안내한다.

### 시연 절차

1. 전날: Fusion 최신으로 업데이트 → MCP 서버 체크 + Apply → Claude 데스크톱 설정 > 커넥터 > "Autodesk Fusion" 설치 → 재시작 → 도구 권한 목록이 채워졌는지 확인 → "10 mm 정육면체를 만들어 줘" 로 시험.
2. 당일: Fusion 을 열고 새 문서를 연 상태에서 시작. 수정 전에 저장.
3. 프롬프트 1 (원문은 `demos/prompts.md`): 단위 mm. 사용자 매개변수 clearance=0.4, wall=4, depth=8, base=3. ANSI/SLAS 96-well plate(127.76 × 85.48 mm) 거치 트레이 — 포켓은 바닥면 + 사방 clearance, 바깥 세로 모서리 필렛 2 mm, 긴 변 양쪽에 20 mm 손가락 홈. 바운딩 박스 보고, 등각 스크린샷, STL 내보내기.
4. 프롬프트 2: "clearance 를 0.6 으로 바꿔서 다시 내보내 줘." — **매개변수 하나로 다시 뽑는 장면이 시연의 핵심.**
5. 결과 STL·스크린샷을 `demos/fusion/` 에 저장.

주의: 항상 "mm" 를 명시한다(API 내부 단위가 cm 라는 제3자 보고 ~). 한 단계에 수십 초 걸린다. 방화벽에서 로컬 포트 허용. **녹화 백업 필수**(로컬에만 보관, 커밋하지 않음).

### 무료 대안 (한 장으로 소개)

- **FreeCAD + freecad-mcp** (neka-nat, MIT) — 완전 무료 파라메트릭 CAD.
- **Claude Code + CadQuery / build123d / OpenSCAD** — 코드로 STL 생성, 라이선스 걱정 없음. 5회차 하네스 방식과 가장 잘 맞는다.
- Blender(공식 Claude 커넥터 있음 ~)는 메시 도구라 정밀 CAD 용이 아니다 — 한 줄만.

---

## 7. Part 5 — 혼자 이어가기 (15분)

### 무료로 계속 쓰는 길

| 항목 | 내용 | 상태 |
|---|---|---|
| Claude 무료 플랜 — 기본 커넥터 | 지원 문서상 "모든 사용자" 사용 가능(2026-10 주 갱신, 예전 판은 "일부 무료 사용자") | ✓, 계정마다 확인 |
| Claude 무료 플랜 — URL 로 추가하는 커넥터 | 1개까지 | ✓ |
| Claude 데스크톱 로컬 MCP | 로그인 상태에서 동작, 플랜 제한 명시 없음 | ✓ |
| Claude Code | Pro 이상 필요 | 미확인 |
| **Claude Team plan for scientists** (2026-08-27 발표) | 기본 좌석 12개월 $0, 프리미엄 좌석 월 $15, 1~25석. PI 가 학술·비영리 인증(5~7일) 후 랩원 초대. Claude Code·Claude Science·커넥터 포함. "한정 제공", 90일 비활성 시 정상가 전환 가능 | ✓, **한국 적용 미확인** |
| Claude Science (베타 데스크톱 앱) | 파이썬/R 작업대 + 키 없이 쓰는 커넥터 약 20개(UniProt·PDB·AlphaFold·PubChem·GEO·OpenAlex·arXiv 등), 재료과학 지원 | ✓, Pro 이상 |
| LM Studio | 무료, MCP 호스트(v0.3.17~), **완전 로컬** — 미발표 데이터에 가장 안전. 품질은 로컬 모델·GPU 에 좌우 | ✓ |
| VS Code + Copilot Free | 에이전트 모드에서 MCP 사용 가능. 무료 플랜에 MCP 포함 여부는 추정 | ~ |
| Gemini CLI | 2026-06-18 무료·개인 사용자는 Antigravity CLI 로 전환, 무료 한도 미확인 | ~ |
| ChatGPT 개발자 모드(MCP) | 무료 플랜에서 불가 | ✓ |

### 데이터 주의 (반드시 말할 것)

- 로컬 도구(napari·Jupyter·파일·Zotero)로 읽은 내용도 결국 **클라우드 모델로 넘어간다.** 원격 커넥터는 질의를 제3자 서버로 보낸다.
- 개인 플랜(Free·Pro·Max)은 **학습 데이터 사용 동의(opt-in)** 시 대화가 학습에 쓰이고 5년 보관된다(2025-08-28 부터) ✓. Team·Enterprise·Education 은 제외. 미발표 데이터·환자 유래 TME 이미지를 다루기 전에 설정을 확인한다.
- Claude Science 는 HIPAA BAA 대상이 아니다 ✓ → 보호 대상 건강정보는 넣지 않는다.
- 연구 데이터를 완전히 밖으로 내보내면 안 되는 경우 → LM Studio 같은 완전 로컬 경로, 또는 Part 2 의 로컬 GUI 도구(QuPath·Fiji·NP-SAM)만 쓴다.

### 내 데이터로 이어가는 3단계 (원래 목표의 회수)

1. **빌려 본다** — Part 2 의 도구를 내 이미지에 로컬로 돌린다.
2. **잰다** — 정답 20개를 손으로 만들고 Dice/F1 을 계산한다(4회차).
3. **부족하면 가르친다** — 3·4회차 노트북에 내 폴더를 넣어 파인튜닝하거나, 5회차 하네스 템플릿으로 에이전트에게 맡긴다.

마지막 한 줄 후보: "빌려 보고, 재 보고, 부족할 때만 가르친다."

---

## 8. 컨벤션 예외 (승인 필요)

1. **노트북 없음**(기본안) — 5회차와 같은 예외. 규칙 12(로컬·코랩 실행 검증)는 §9 의 강사 리허설 A~C 로 대체한다. §13-2 에서 노트북을 만들기로 하면 그 노트북에는 규칙 12 를 그대로 적용한다.
2. **외부 서비스 의존** — 웹 데모·커넥터·Fusion 은 수업 당일 상태에 좌우된다. 대비: 리허설 캡처와 녹화 백업을 필수로 한다.

데이터는 커밋하지 않는다(규칙 2 준수). CONVENTIONS.md 본문은 고치지 않는다.

---

## 9. 작업 순서 (한 단계씩, 각 단계 후 보고)

1. 스펙 확정 — §13 열린 결정 해소(준현).
2. 시연 샘플 선정 — 분야별 공개 이미지·영상 1세트(SEM 은 "떨어진 입자" / "뭉친 입자" 2장). 출처·라이선스 확인 후 기록.
3. `CATALOG.md` — §4·§5·§6·§7 표를 참가자용으로 정리. 항목마다 확인일과 ✓/~/미확인 표시.
4. 강사 리허설 A (Part 2) — 각 도구를 샘플에 실제로 돌려 캡처. Dice/F1 1개 이상 계산. SEM 비교가 예상대로 나오는지 확인(아니면 서술을 결과에 맞춘다).
5. 강사 리허설 B (Part 3) — `demos/prompts.md` 시나리오 1~5 실행, 결과 캡처. **무료 계정**으로 PubMed 커넥터가 켜지는지 확인. napari-mcp 설치·동작 확인.
6. 강사 리허설 C (Part 4) — Fusion 체험판(또는 구독) + 커넥터로 트레이 생성 → 수정 → 재출력. 녹화 백업.
7. `MCP_GUIDE.md` — 참가자용 연결 안내 + §7 표 + 데이터 주의.
8. `session6_lecture.html` — 이전 회차와 같은 단독 열람 HTML. Part 1~5 + 리허설 캡처. 수치·사실은 전부 리허설 결과와 CATALOG 에서 대조.
9. `session6/README.md` + 루트 README 세션 목록 갱신 + 커밋·푸시.

---

## 10. 회차 통과 조건

- [~] Part 2 도구가 리허설에서 실제 결과를 냈다 — Cellpose·InstanSeg·Fiji·NP-SAM 은 결과와 그림, F1/Dice 수치 있음(§14-1). QuPath GUI·SAM 3 로컬·Tierpsy 는 못 함.
- [~] Part 3 — PubMed MCP 검색은 서버 직접 호출로 확인. 무료 계정의 커넥터 켜기와 시나리오 ②~⑤ 의 채팅 실행은 수업 전 준현 확인 필요.
- [ ] Fusion 시연: STL 생성 → clearance 수정 → 재출력 성공, 녹화 백업 있음. (준현 — 포트 27183)
- [x] 강의 HTML 의 모든 도구 항목에 무료 경로·라이선스·확인일·확인 상태가 있다(CATALOG.md 대신, §13-1). 링크 39개 접속 확인(Autodesk 블로그만 자동 요청 차단으로 403 — 조사 에이전트가 우회 경로로 본문을 읽음).
- [x] §11 재확인 — 2026-10-22 당일 조사.
- [x] 레포에 시연 데이터·녹화 영상이 없다(`data/`·`outputs/` 는 gitignore).

---

## 11. 수업 직전 재확인 목록 (자주 바뀌는 것)

- Fusion MCP 라이선스 조건, 체험판에서 커넥터 동작 여부.
- Claude 무료 플랜의 커넥터 범위, Claude Code 플랜 요건.
- SAM 3 Playground 로그인 필요 여부, HF 가중치 승인 상태.
- Cellpose HF Space 무료 GPU 한도.
- Claude Team plan for scientists 한국 적용 여부·신청 가능 여부.
- Owkin 커넥터 가격.

---

## 12. 하지 말 것

- 참가자 개인 데이터 사용(반입 불가 전제).
- 참가자 PC 에 코드 실행형 MCP(napari-mcp 등) 설치 지시.
- 새 학습 실습 — 이번 회차는 빌려 쓰기다.
- 확인하지 않은 내용을 사실로, 유료 도구를 무료로 소개.
- PDA 비색 센서 사례.
- 카탈로그 부풀리기 — 분야당 시연 1개(SEM 만 비교용 2개) 원칙.

---

## 13. 결정 사항 (2026-10-22 준현 확정)

1. 수업 날짜 — **2026-10-22 10:00.** 남은 시간이 짧아 §9 작업 순서를 줄인다: `CATALOG.md`·`MCP_GUIDE.md` 는 따로 만들지 않고 강의 HTML 의 표와 "따라 해 보기" 상자로 합친다. 리허설은 강사 랩탑(이 PC, RTX 5050 Laptop 8 GB)에서 가능한 범위만 한다.
2. 노트북 — 참가자 전원과 강사가 **랩탑을 가져온다.** 주피터 노트북은 만들지 않는다(기본안). Dice/F1 예시는 강사 랩탑에서 계산해 강의 자료에 넣는다.
3. 직접 실습 범위 — 시간상 **강사 설명 위주로 끝날 수 있다.** 대신 모든 실습 절차를 강의 HTML 의 "따라 해 보기" 상자에 넣어 모임 이후 혼자 해 볼 수 있게 한다.
4. Fusion — 강사는 **아카데믹 라이선스**로 그대로 시연한다. 주의: 강사 랩탑에서는 Fusion MCP 기본 포트 27182 를 MATLAB 서비스(MathWorksServiceHost)가 이미 쓰고 있다(2026-10-22 01:55 확인). Fusion 환경설정 > General > API 의 Fusion MCP Server Port 를 비어 있는 27183 으로 바꾸고, Claude 데스크톱 > Customize > Connectors > Autodesk Fusion > Configure 의 포트도 같게 맞춘 뒤 Claude 를 완전히 재시작한다(Autodesk 블로그 2026-06-29 의 설정 절차 기준, 충돌 해결법 자체는 공식 문서에 없음).
5. Team plan for scientists — 강의 HTML Part 5 에 설명으로 넣는다.
6. 시연 샘플 데이터 — 공개 데이터셋을 쓴다.
7. 4회차 "한 줄 정리" — 넣지 않는다. Part 1 표는 회차별 "가져간 것" 으로 정리한다.

---

## 14-1. 실행 기록 (2026-10-22 02:00~04:00, 강사 랩탑, Claude Code 가 준현 요청으로 무인 진행)

- 환경: Windows 11, RTX 5050 Laptop 8 GB. conda env `ai_cop_session6`(Py 3.11.17, torch 2.11.0+cu128, cellpose[gui] 4.2.1.1, instanseg-torch 0.1.2), `ai_cop_npsam`(Py 3.10.22, npsam 3.2.3, torch cu128), `ai_cop_napari`(napari 0.9.2, napari-mcp 0.1.0). Fiji 2.16 은 `C:\Users\BSL\AI_COP_tools\Fiji.app`.
- Part 2 메시지 1 (`tools/zero_shot_check.py`): NuInsSeg 사람 흑색종·편도·비장 58장, 정답 정리 후 핵 4,990개. Cellpose cpsam_v2 기본 P 0.83 / R 0.65 / F1 0.73 / Dice 0.87, 이미지당 < 1 s. 면적 사분위별 재현율(가장자리 제외) 0.13 / 0.61 / 0.88 / 0.92 — 작은 핵을 놓친다. cellprob −3 은 F1 0.59 로 악화, diameter 20 은 0.72 로 변화 없음. InstanSeg brightfield_nuclei: 픽셀 크기 미지정 0.52, 0.25 µm 지정 0.73. 정답 라벨에 흩어진 조각(약 900개 핵)·30 px 미만 찌꺼기(256개)가 있어 정리함(정리 전 F1 0.70).
- Part 2 메시지 3 (`tools/sem_check.py`, `tools/npsam_run.py`): BAM TiO2 1908248(정답 143개) — Fiji 기본 방식 F1 0.42, NP-SAM FastSAM 0.58, NP-SAM SAM ViT-H 0.46. NFFA 이미지(작고 틈이 있는 입자)에서는 눈으로 보아 Fiji 가 더 깔끔. → 메시지 3 서술을 "이미지가 정한다, 고전 방식 먼저" 로 확정. 겹침 규칙(number_of_overlapping_masks ≤ 1) 일괄 적용은 두 모델 모두 악화(0.31, 0.40).
- 발견한 함정(강의 자료 부록 점검표에 반영): `cellpose` 만 설치하면 GUI 없음 → `cellpose[gui]`; Fiji `--headless` 에서 Analyze Particles NPE → `-batch`; Fiji Black background; NP-SAM 설치 시 cp949 → `PYTHONUTF8=1`; NP-SAM 가중치 OSF 다운로드 DNS 실패 → 공식 출처(FastSAM-x, Meta SAM ViT-H); NP-SAM 은 GPU 없으면 FastSAM(AGPL) 자동 선택; napari-mcp 는 `napari[all]` 필요.
- MCP: PubMed 원격 서버 도구 7개 확인 + 검색 1회(18편), bioRxiv 응답 확인, napari-mcp stdio 서버 도구 16개 확인(Claude 데스크톱 등록은 하지 않음 — 준현이 수업 전에).
- 하지 못한 것: QuPath GUI, SAM 3 로컬(가중치 승인제), Tierpsy(Docker 없음), Zotero MCP(Zotero 없음), Fusion 시연 리허설(준현 몫), 참가자 무료 계정에서 커넥터 켜기.
- 계획 변경: 작업이 늘어난 대신 `CATALOG.md`·`MCP_GUIDE.md` 는 만들지 않고 HTML 로 통합(§13-1). 그림을 넣는 빌더(`tools/build_html.py`)와 템플릿을 3회차 방식으로 분리.

## 14. 근거 (조사 2026-10-22)

- 사전학습 모델: pypi.org/project/cellpose · github.com/MouseLand/cellpose · cellpose.readthedocs.io/en/latest/models.html · mouseland-cellpose.hf.space · pypi.org/project/micro-sam · github.com/facebookresearch/sam2 · github.com/facebookresearch/sam3 · huggingface.co/facebook/sam3 · arxiv.org/abs/2604.18225 · qupath.readthedocs.io/en/0.7/docs/deep/instanseg.html · github.com/Tierpsy/tierpsy-tracker · pypi.org/pypi/npsam/json · github.com/TIO-IKIM/CellViT-plus-plus · huggingface.co/MahmoodLab/UNI2-h · huggingface.co/MahmoodLab/CONCH · huggingface.co/paige-ai/Virchow2 · pypi.org/project/dlclibrary
- MCP: anthropic.com/news/claude-for-life-sciences · anthropic.com/news/healthcare-life-sciences · support.claude.com/en/articles/11176164-pre-built-web-connectors-using-remote-mcp · claude.com/connectors/{pubmed, biorxiv, consensus, scholar-gateway, biorender, hugging-face, owkin} · github.com/royerlab/napari-mcp · github.com/54yyyu/zotero-mcp · github.com/biocontext-ai/knowledgebase-mcp · github.com/WormBase/wormbase-mcp · github.com/NicoKiaru/fiji_mcp
- Fusion: anthropic.com/news/claude-for-creative-work · help.autodesk.com/view/ADSKMCP/ENU/ · claude.com/connectors/autodesk-fusion · autodesk.com/products/fusion-360/blog/how-to-improve-your-fusion-workflow-with-the-claude-desktop-connector/ · autodesk.com/products/fusion-360/blog/fusion-compute-mcp/ · autodesk.com/products/fusion-360/personal · autodesk.com/support/account/education/admin/eligibility · note.com/tokyomakers/n/n35aae26aa835 (체험판 사례) · github.com/neka-nat/freecad-mcp
- 플랜·데이터: claude.com/programs/team-plan-for-scientists · support.claude.com/en/articles/16634237-claude-team-plan-for-scientists · claude.com/docs/claude-science/overview.md · anthropic.com/news/updates-to-our-consumer-terms · lmstudio.ai/blog/mcp · code.visualstudio.com/docs/copilot/faq
