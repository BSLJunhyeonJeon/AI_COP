# 5단계 스펙 — 발표용 HTML 빌더 (`05_build_html`)

> **대상**: 클로드 코드.
> **전제**: `CONVENTIONS.md` + 0~4단계 결과 위에. 충돌 시 **CONVENTIONS.md 우선**.
> **범위**: **5단계(HTML 빌더)만**. **새 개념·새 그림·새 노트북 로직 추가 금지** — 기존 01~04 산출물을 모아 HTML로 묶는 것뿐. **템플릿 HTML의 내용·디자인 변경 금지**(claude.ai 제공본 보존, 그림 `src`만 주입).
> **방식**: ① claude.ai가 제공한 `session2_lecture_template.html`을 레포 `session2/`에 추가(커밋) ② `session2/notebooks/05_build_html.ipynb` 신규 ③ requirements.txt의 albumentations 핀 확정. 작업 후 커밋·push, 확인 보고.

---

## 1. 목적

- 0~4단계 **결과 그림** + claude.ai가 작성한 **강의 HTML 템플릿**을 묶어, **파일 하나짜리 자체완결 발표 자료 `session2_lecture.html`**를 만든다.
- 노트북 하나를 **'런타임 → 모두 실행'**하면: 01~04를 **같은 VM에서 실행** → `outputs/` 채움 → 템플릿에 그림을 **base64로 인라인** → 최종 HTML 완성. (선생님이 노트북을 하나씩 돌릴 필요 없음)

---

## 2. 입력 (확정)

- **강의 템플릿**: `session2/session2_lecture_template.html` (claude.ai 제공, 레포에 추가). 그림 자리는 `<img ... data-embed="파일명" ...>` 표식이고 **현재 `src`가 없다.** 빌더가 이 표식을 `outputs/`의 같은 파일명 이미지로 채운다.
  - **임베드할 파일명(10개)**: `three_formats.png`, `02_classification.png`, `02_detection.png`, `02_segmentation.png`, `03_sam2_clicks.png`, `03_labeling_workflow.png`, `04_geometric.png`, `04_pixel.png`, `04_bad_aug.png`, `04_aug_animation.gif`.
- **그림 출처**: 01~04 노트북 실행 결과(`outputs/`). **빌더가 직접 실행해 생성**한다.

---

## 3. 산출물

- `session2/session2_lecture_template.html` (추가 — claude.ai 제공본 **그대로** 커밋)
- `session2/notebooks/05_build_html.ipynb` (신규)
- `outputs/session2_lecture.html` (빌더 결과 — 자체완결. `outputs/`는 `.gitignore`이므로 **비커밋**, 선생님이 다운로드해서 사용)
- `session2/requirements.txt`: **albumentations 핀 확정**(빌더 셀에서 버전 확인 후 `==`고정)

---

## 4. `05_build_html.ipynb` 구성 (셀)

헤더 3줄. **이 노트북은 파이프라인 성격이라 셀 1→2→3→4→5 순서 실행이 전제**다(다른 노트북의 셀 독립 원칙 예외 — 노트북 안에 명시).

**셀 1 — 환경 셋업**: 00~04와 동일 패턴(코랩에서 `/content/AI_COP` 클론, `session2`로 cd).

**셀 2 — 의존성 + 도구 확인**: `requirements.txt` 설치. **albumentations 버전 출력**(핀용). 노트북 실행 도구(`jupyter nbconvert` 내장; 필요하면 `papermill`) 가용 확인·없으면 설치.

**셀 3 — 01~04 순차 실행 (같은 VM)**: `jupyter nbconvert --to notebook --execute`(또는 papermill)로 `01_data` → `02_inference_demo` → `03_labeling_sam2` → `04_augmentation`을 **차례로** 실행한다.
- 각 노트북은 자기 셀 1에서 `/content/AI_COP/session2`로 cd하므로 **`outputs/`가 한곳에 누적**된다.
- **GPU 필요**(02·03). 무료 T4로 충분. **모델·데이터 다운로드로 수 분 소요** — 타임아웃 넉넉히(예: 노트북당 600초).
- 한 노트북이 실패해도 **전체가 멈추지 않게**(예외 처리) 하고, 실행 후 `outputs/`에 위 10개 그림이 있는지 점검·출력(없는 것 표시).

**셀 4 — HTML 조립**: 템플릿을 읽고, 각 `data-embed="X"`에 대해 `outputs/X`를 base64로 읽어 **`src="data:MIME;base64,..."`를 주입**한다(`.png`→`image/png`, `.gif`→`image/gif`). **템플릿의 다른 내용·구조·CSS는 절대 건드리지 않는다**(src 주입만). 누락된 파일은 그대로 둬서 템플릿 CSS의 자리표시가 보이게 한다(빌드는 진행). 결과를 `outputs/session2_lecture.html`로 저장.

**셀 5 — 검증/안내**: 최종 파일 크기, **임베드된 그림 수 / 누락 목록**을 출력. "이 파일을 다운로드해 브라우저로 열면 외부 연결 없이 단독으로 보이는 발표 자료"라고 안내. (`present_files`로 다운로드 제공 가능)

---

## 5. `requirements.txt` 갱신

- **albumentations 핀 확정**: 셀 2 출력 버전으로 `albumentations==X.Y.Z` 고정. 나머지 기존 핀 유지.

---

## 6. 제약

- **새 개념·새 그림·새 노트북 로직 금지** — 기존 01~04 산출물을 모아 묶는 것만.
- **템플릿 HTML의 내용/디자인/CSS 변경 금지** — `data-embed` 자리에 `src`만 주입(claude.ai 제공본 보존).
- **무료 Colab(GPU) 한도 안.** 01~04 실행은 **한 세션에서**(빌더가 orchestration).
- `outputs/session2_lecture.html`은 **비커밋**(`.gitignore`). 선생님 다운로드용.
- 한국어 안내. 셀 1→5 순서 실행 전제(노트북에 명시).

---

## 7. 통과 조건 (구현 후 자가 점검 → 보고)

- [ ] `05_build_html.ipynb` '모두 실행' → 01~04가 같은 VM에서 실행되어 `outputs/`에 그림 10개 생성.
- [ ] 템플릿의 `data-embed` 자리들이 base64로 채워진 **자체완결 `session2_lecture.html`** 생성(외부 링크 없이 단독 열람 가능).
- [ ] 누락 그림이 있으면 명확히 표시(빌드는 진행).
- [ ] **albumentations 핀 확정**.
- [ ] 템플릿 내용/디자인 **무변경**(src 주입만).

구현을 마치면 **변경 요약 + 사람이 확인하는 법**(어떤 셀을 실행하면 최종 HTML이 어디에 나오는지)을 보고한다. 직접 확인한 범위를 밝힌다(01~04 orchestration을 어디까지 돌려봤는지 포함).

---

## 8. 하지 말 것

- **템플릿 내용/디자인 수정**, **새 개념/그림 추가**, **노트북 로직 변경** — 금지.
- 스펙에 없는 기능·옵션 임의 추가 — 금지. 필요해 보이면 추가하지 말고 **질문/메모로 남긴다**.
