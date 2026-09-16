# session5 — 프로젝트 루트(하네스) 구축: 에이전트에게 일을 시키는 법

2~4회차는 여러분이 노트북을 열고 ▶ 를 눌렀습니다. 5회차는 노트북이 없습니다.
대신 에이전트(Claude Code, Codex, Cowork 등)가 일할 수 있게 꾸며 둔 폴더 하나를 드립니다. 여러분은 그 폴더를 에이전트에 물리고 한 문장을 붙여넣습니다. 에이전트는 초파리 뇌 전체(뉴런 138,639개)를 시뮬레이션하고, 다가오는 물체를 피하는 도망 반사로 공룡 점프 게임을 하게 만듭니다.

오늘 배우는 것은 초파리가 아니라 폴더입니다 — 좋은 프로젝트 루트는 싼 모델도 일하게 만든다는 것.

> 공통 규칙은 레포 루트의 [CONVENTIONS.md](../CONVENTIONS.md) 를 따릅니다. 이번 회차의 예외 2건(데이터 커밋, 노트북 없음)은 [docs/session5_spec_agent_harness.md](../docs/session5_spec_agent_harness.md) §8 에 있습니다.

---

## 폴더 두 개

```
session5/
├─ harness/   # ★ 원본 하네스. 참가자는 이 폴더를 복사해서 씁니다
└─ solved/    # harness/ 를 복사해 클로드 코드가 4단계를 완료한 결과 (수업 후 참고용)
```

- `harness/` — 데이터·규칙(AGENTS.md)·과제(docs/TASK.md)·수식(docs/MODEL_SPEC.md)·검증기(tests/verify.py)만 있고 코드는 없습니다. 사용법은 [harness/README.md](harness/README.md).
- `solved/` — 같은 폴더를 클로드 코드에게 주고 자동 지시 한 문장으로 완주시킨 결과입니다. `src/` 의 코드, `outputs/` 의 그림·GIF·로그, `RUN_LOG.md`(모델·소요 시간·막힌 곳)가 그대로 들어 있습니다. 수업 중에는 열지 마세요 — 에이전트가 베낍니다.

## 참가자 순서 (수업 중)

1. `harness/` 폴더를 통째로 복사해 자기 위치에 둡니다(`solved/` 옆이 아닌 곳).
2. 에이전트에 그 폴더를 물리고 `harness/README.md` 의 자동 완주 문장을 붙여넣습니다.
3. 에이전트가 단계별로 `python tests/verify.py --stage N` 을 통과하며 진행하는 것을 지켜봅니다. 60분 안에 4단계까지 가는 것이 목표입니다.
4. 끝나면 `outputs/04_dino.gif` 와 `outputs/04_speed_vs_pass.png` 를 열어 봅니다. 그리고 옆 사람과 비교합니다 — 어떤 모델이 몇 번 만에 통과했는지, 어디서 막혔는지.

## 이 폴더를 내 연구로 옮기려면

`harness/` 의 다섯 요소 — 폴더 구조, 규칙(AGENTS.md), 과제(TASK.md), 데이터(data/), 검증(tests/) — 를 내 연구 폴더에 같은 이름으로 만들면 됩니다. 절차와 빈 템플릿은 강의 자료 `session5_lecture.html` 에 있습니다(준비 중).

## 데이터 출처

FlyWire v783 커넥톰(Dorkenwald et al. 2024, CC BY 4.0), 뉴런 주석(Schlegel et al. 2024), LIF 모델 파라미터(Shiu et al. 2024). 자세한 것은 [harness/docs/DATA.md](harness/docs/DATA.md).
