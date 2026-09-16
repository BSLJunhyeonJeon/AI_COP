# showcase — 강사용 시연 도구 (5회차)

참가자용이 아니라 강사용입니다. 하네스(`../harness`)와 같은 데이터·같은 규칙(MODEL_SPEC §4)으로 미리 계산한 결과를
쇼츠 영상, 동기화 애니메이션, 그리고 수업 중 멈춰 가며 볼 수 있는 재생기(Windows exe)로 만듭니다.

## 폴더

```
showcase/
├─ player.py            # 재생기 — pack/ 을 읽어 게임·flybody 3D 초파리·뇌 지도·GF 막전위·전체 발화를 한 시간축으로 재생
├─ pack/                # 재생기 데이터 팩(미리 계산된 결과 5 에피소드, 뇌 지도 배경, 초파리 프레임, 나눔고딕) — 약 6 MB
├─ build_exe.bat        # PyInstaller 로 dist\FlyBrainPlayer.exe 생성 (Windows 에서 실행)
├─ run_player.bat       # exe 없이 파이썬으로 바로 실행
├─ requirements.txt     # 재생기: pygame, numpy
├─ make_pack.py         # pack/ 재생성 (강사용, 시뮬레이션 + flybody 렌더 — requirements_make.txt 필요)
├─ viz_episode.py       # 시뮬레이터(MODEL_SPEC §4) + "게임 + 뇌" 동기화 GIF
├─ shorts_render.py     # 세로(9:16) 쇼츠 영상 렌더 (flybody 3D 초파리 포함)
└─ media/               # 완성 영상·GIF: fly_brain_dino_shorts.mp4, episode_k3/k5_game_and_brain.gif
```

## 재생기 (수업 시연)

exe: `build_exe.bat` 을 이 폴더에서 실행하면 `dist\FlyBrainPlayer.exe` 가 생깁니다(파이썬 3.10+ 필요, 처음 한 번). 더블클릭으로 실행.
소스: `run_player.bat` (또는 `python player.py`).

조작: 1~5 속도 단계 선택 · Space 재생/정지 · 좌우 화살표 한 프레임(게임 시간 2.5 ms) · Shift+화살표 10프레임 · [ ] 배속(1/2 ~ 1/40) · Home 처음부터 · A 자동 재생(1→5 순서) · H 도움말 · S 스크린샷 · Esc 종료.
창 크기는 자유롭게 바꿔도 됩니다(내용이 같이 늘어남). 처음 실행 시 SmartScreen 경고는 서명 없는 exe 라서 뜹니다 — "추가 정보 > 실행".

재생기는 계산을 하지 않습니다. 결과는 `make_pack.py` 가 하네스와 같은 시뮬레이터로 미리 만든 것이고, 화면의 시간(t)은 신경 시간(ms)입니다.

## 팩·영상 다시 만들기 (강사)

```
pip install -r requirements_make.txt
git clone --depth 1 https://github.com/TuragaLab/flybody      # 3D 초파리 모델 (Apache-2.0, 메시 161 MB — 레포에 넣지 않음)
python make_pack.py ../harness/data <flywire_annotations>/supplemental_files/Supplemental_file1_neuron_annotations.tsv <Drosophila_brain_model>/Completeness_783.csv flybody/flybody/fruitfly/assets/fruitfly.xml pack
python shorts_render.py ../harness/data <annotations.tsv> <Completeness_783.csv> flybody/flybody/fruitfly/assets/fruitfly.xml media
python viz_episode.py ../harness/data media <annotations.tsv> <Completeness_783.csv>
```
뉴런 위치(`Supplemental_file1_neuron_annotations.tsv`)와 `Completeness_783.csv` 는 `../tools/build_data.py` 가 쓰는 것과 같은 원본입니다(`../harness/docs/DATA.md` 출처 참조).
리눅스 서버에서 렌더할 때는 `MUJOCO_GL=osmesa` 를 앞에 붙입니다. 윈도우 데스크톱은 그대로 됩니다.

## 라이선스·출처

- 커넥톰: FlyWire v783 — Dorkenwald et al. 2024, CC BY 4.0. 뉴런 위치: Schlegel et al. 2024 (flywire_annotations).
- LIF 파라미터: Shiu et al. 2024.
- 3D 초파리: flybody (Janelia Turaga Lab / Google DeepMind), Apache-2.0. 팩에는 렌더된 PNG 프레임만 들어 있습니다.
- 글꼴: 나눔고딕(NanumGothic.ttf), SIL Open Font License 1.1.
- 이 폴더의 코드: 레포와 같은 조건.
