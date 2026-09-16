# harness — 에이전트에게 초파리 전뇌 시뮬레이션을 만들게 하는 프로젝트 루트

이 폴더는 코드가 아니라 하네스(harness)입니다. 에이전트가 일할 수 있도록 데이터·규칙·과제·검증기를 한 폴더에 모아 둔 것이고, 코드는 여러분의 에이전트가 씁니다. 여러분이 할 일은 폴더를 에이전트에 물리고 한 문장을 붙여넣는 것뿐입니다.

> 공통 규칙은 레포 루트의 [CONVENTIONS.md](../../CONVENTIONS.md) 를 따릅니다. 이번 회차는 참가자용 노트북이 없는 예외 회차입니다(5회차 스펙 §8).

---

## 시작하기 (3단계)

1. 이 폴더(`harness/`)를 통째로 복사해 자기 작업 위치에 둡니다. 예: `내문서/fly_brain/`. 옆에 `solved/` 가 있는 위치에서 그대로 열지 마세요 — 에이전트가 정답을 베낍니다.
2. 에이전트에 그 폴더를 물립니다(아래 도구별 메모).
3. 아래 문장을 그대로 붙여넣습니다.

자동 완주(수업용):

```
AGENTS.md 의 규칙대로 docs/TASK.md 의 1~4단계를 순서대로 수행해. 각 단계는 python tests/verify.py --stage N 이 PASS 해야 다음으로 넘어가고, 단계마다 AGENTS.md 의 완료 보고 형식으로 짧게 보고해. 4단계까지 끝나면 python tests/verify.py --all 의 출력을 outputs/verify_all.txt 에 저장하고 단계별 wall time 을 표로 보고해.
```

한 단계씩 확인하며 가고 싶으면 마지막 문장을 "1단계가 끝나면 멈추고 보고해" 로 바꾸면 됩니다.

## 도구별 메모

- Claude Code: 터미널에서 복사한 폴더로 이동한 뒤 `claude` 를 실행하고 위 문장을 붙여넣습니다. `CLAUDE.md` 가 `AGENTS.md` 를 자동으로 불러옵니다.
- Claude 데스크톱(Cowork): 복사한 폴더를 연결하고 위 문장을 붙여넣습니다.
- Codex(ChatGPT): 복사한 폴더를 열고(또는 GitHub 에 올린 뒤 연결) 위 문장을 붙여넣습니다. `AGENTS.md` 를 자동으로 읽습니다.
- Google Colab + Gemini: (확정 전) 폴더를 업로드하거나 `!git clone` 한 뒤 같은 문장을 Gemini 에게 줍니다.

어느 도구든 파이썬 3.12 와 `requirements.txt` 의 패키지가 필요합니다. 클라우드 샌드박스(Claude Code 웹, Codex 클라우드)는 보통 `pip install -r requirements.txt` 한 줄로 끝납니다.

## 로컬 파이썬 환경 (선택, 아나콘다 기준)

```
# 윈도우: setup_env.bat   /   맥·리눅스: chmod +x setup_env.sh && ./setup_env.sh
conda activate ai_cop_session5
```

환경 이름은 `ai_cop_session5`. 에이전트가 이 환경의 파이썬을 쓰도록 같은 터미널에서 에이전트를 실행하세요.

## 폴더 구조

```
harness/
├─ README.md          # 이 파일 (사람용)
├─ AGENTS.md          # 에이전트용 규칙 — 지시의 단일 출처
├─ CLAUDE.md          # Claude Code 용 한 줄(@AGENTS.md)
├─ docs/
│  ├─ TASK.md         # 과제 4단계 + 통과 조건
│  ├─ MODEL_SPEC.md   # 수식·파라미터·게임 규칙·출력 규격
│  └─ DATA.md         # 데이터 스키마·출처
├─ data/              # 커넥톰 10.1 MB·뉴런 표 1.5 MB·뉴런 그룹 5 KB — 읽기 전용
├─ tests/verify.py    # 단계별 통과 검사
├─ src/               # (비움) 에이전트가 채움
├─ outputs/           # (비움) 에이전트가 채움
├─ requirements.txt
└─ setup_env.bat / setup_env.sh
```

## 결과 확인법

- 단계별: `python tests/verify.py --stage 1` … `--stage 4`
- 전체: `python tests/verify.py --all` → `outputs/verify_all.txt`
- 볼 것: `outputs/03_raster.png`(전뇌가 실제로 반응하는가), `outputs/04_dino.gif`(점프 장면), `outputs/04_speed_vs_pass.png`(어느 속도부터 실패하는가)

## 데이터 출처

FlyWire v783 커넥톰(Dorkenwald et al. 2024, CC BY 4.0), 뉴런 주석(Schlegel et al. 2024), 모델 파라미터(Shiu et al. 2024). 자세한 것은 `docs/DATA.md`.
