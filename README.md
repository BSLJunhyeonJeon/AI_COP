# AI_COP — 박사후연구원 학습공동체 AI 실습 자료

생명공학 분야 박사후연구원(코딩 초보) 대상 **컴퓨터비전 AI 실습 자료** 모음입니다.
회차(세션)별로 자기완결적인 폴더를 두며, **노트북을 열고 ▶ 만 누르면** 따라갈 수 있도록 만듭니다.

## 세션 목록

| 세션 | 주제 | 바로가기 |
|---|---|---|
| **session2** | 분류·감지·분할 개념 체험 + 데이터 형식·증강 | [session2/README.md](session2/README.md) |
| **session3** | 전이학습(파인튜닝) — YOLO11n 을 혈액 데이터로 | [session3/README.md](session3/README.md) |
| **session4** | 학습(Training) — 하이퍼파라미터 실험실 + 포즈 데모 | [session4/README.md](session4/README.md) |
| **session5** | 프로젝트 루트(하네스) 구축 — 에이전트에게 초파리 전뇌 시뮬레이션·공룡 게임 만들게 하기 | [session5/README.md](session5/README.md) |
| **session6** | 마무리 — 지난 회차 요약 + 빌려 쓰는 AI(학습 없이 쓰는 모델 · MCP · Fusion 360) | [session6/README.md](session6/README.md) |

> session5 는 예외 회차입니다 — 참가자용 노트북 대신 에이전트용 프로젝트 루트(`session5/harness/`)를 제공합니다. 예외 근거는 [docs/session5_spec_agent_harness.md](docs/session5_spec_agent_harness.md) §8.
> session6 도 참가자용 노트북이 없습니다 — 강의 자료(`session6/session6_lecture.html`)의 “따라 해 보기” 절차와, 검증 예시를 재현하는 `session6/tools/` 를 제공합니다. 근거는 [docs/session6_spec_borrowed_ai.md](docs/session6_spec_borrowed_ai.md) §8·§13.

## 공통 규칙

모든 세션에 적용되는 불변 규칙·구조 원칙은 **[CONVENTIONS.md](CONVENTIONS.md)** 가 단일 출처입니다.
세션별 기획·스펙 문서는 [docs/](docs/) 에 보관됩니다.

## 폴더 구조

```
AI_COP/
├─ README.md          # 이 파일 (레포 인덱스)
├─ CONVENTIONS.md     # 모든 세션 공통 규칙 (단일 출처)
├─ docs/              # 기획·스펙 문서 보관
├─ session2/          # 한 세션 = 자기완결 폴더 (README·노트북·requirements·conda 스크립트)
├─ session3/
├─ session4/
├─ session5/          # 예외: 노트북 없음. harness/(원본 하네스) + solved/(클로드 코드 완료본)
└─ session6/          # 예외: 노트북 없음. 강의 HTML + tools/(검증 예시 재현 스크립트)
```
