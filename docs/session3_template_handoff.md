# session3 강의 템플릿 — claude.ai 앞 인수인계 (빌더 계약 + 이력)

> 작성: 클로드 코드. 대상: `session3/session3_lecture_template.html` 를 담당하는 claude.ai.
> **빌더(`session3/notebooks/02_build_html.ipynb`)는 완성·검증 완료**입니다.

## ✅ 해결됨 — 아래 §4 의 결정 요청은 **(B) 로 처리되었습니다**

claude.ai 가 `<img data-embed>` 슬롯을 추가했고, 새 템플릿으로 빌더를 실제 실행해 검증했습니다:

- **슬롯 8개 → 임베드 8개, 누락 0** (`03_before_after.png` 는 2곳에서 재사용, `03_curves.png` 1, conf 4장, `03_per_class.png` 1)
- 이제 `data-embed` 8건이 **전부 `<img>` 태그**이며 `src=` 는 0개(빌더가 주입)
- 템플릿 무결성 유지(주입된 `src` 만 제거하면 원본과 바이트 동일)

즉 **7장이 모두 HTML 에 박힙니다.** 아래 §3 은 이력(수정 전 상태)으로 남겨둡니다.

---

## 1. 빌더 동작 규격 (템플릿이 맞춰야 하는 계약)

빌더 셀 4는 **`<img>` 태그에 붙은 `data-embed` 만** 채웁니다.

```python
IMG_RE = re.compile(r'<img\b[^>]*?\bdata-embed="([^"]+)"[^>]*?>', re.IGNORECASE | re.DOTALL)
# 매칭된 <img ...> 의 '<img' 바로 뒤에 src="data:image/png;base64,...." 를 삽입
```

- **채우는 것**: `<img ... data-embed="파일명" ...>` → `outputs/파일명` 을 base64 로 읽어 `src=` 주입
- **건드리지 않는 것**: `<img>` 가 **아닌** 곳의 `data-embed` 언급(예: `<code>data-embed="…"</code>` 설명 텍스트) → **원본 그대로 보존**
- 파일이 없으면 그 슬롯은 원본 유지(템플릿의 자리표시 CSS 가 그대로 보임). 빌드는 계속됨.
- 템플릿의 내용·구조·CSS 는 **일절 수정하지 않음**(`src` 속성 추가만). 실제 템플릿으로 검증: 주입된 `src` 만 제거하면 원본과 **바이트 단위 동일**.

> 참고(이력): 초기 빌더는 `data-embed="…"` 를 위치 무관하게 치환해 `<code>` **설명 텍스트 안에 base64 를 주입**하는 버그가 있었습니다(화면에 `data:image/png;base64,…` 가 그대로 노출). **수정 완료**(커밋 `2b0eddc`). 이제 설명 텍스트는 안전하니 자유롭게 쓰셔도 됩니다.

---

## 2. `01_finetune.ipynb` 가 `outputs/` 에 만드는 파일 — 총 7개

| 파일명 | 내용 |
|---|---|
| `03_before_after.png` | **전/후 비교 (이 수업의 클라이맥스)** — 좌: COCO YOLO11n 실패 / 우: 파인튜닝 성공. 대상 `BloodImage_00011`(test split) |
| `03_curves.png` | 학습 곡선 (box loss ↓ / mAP50 ↑) |
| `03_conf_010.png` | conf 0.10 결과 |
| `03_conf_025.png` | conf 0.25 결과 |
| `03_conf_050.png` | conf 0.50 결과 |
| `03_conf_070.png` | conf 0.70 결과 |
| `03_per_class.png` | 클래스별 성능 표 (mAP50/precision/recall + train 박스 수) |

conf 4장은 **크기·여백·DPI 가 완전히 동일**하게 저장됩니다(910×715 px). 슬라이더에서 튀지 않습니다.

---

## 3. 현재 템플릿 상태 (사실)

- 파일: `session3/session3_lecture_template.html` (91,234 bytes, 커밋됨 `e56a8e3`)
- **실제 `<img data-embed>` 슬롯: 4개뿐** — conf 슬라이더:
  ```html
  <img class="cs-img is-on" data-embed="03_conf_010.png" data-conf="0.10" alt="conf 0.10 결과">
  <img class="cs-img"       data-embed="03_conf_025.png" data-conf="0.25" alt="conf 0.25 결과">
  <img class="cs-img"       data-embed="03_conf_050.png" data-conf="0.50" alt="conf 0.50 결과">
  <img class="cs-img"       data-embed="03_conf_070.png" data-conf="0.70" alt="conf 0.70 결과">
  ```
- **`<img>` 슬롯이 없는 파일 3개** — `<code>` 설명 텍스트로만 언급됨:

  | 파일 | 언급 위치(줄) | 현재 형태 |
  |---|---|---|
  | `03_before_after.png` | 657, 1053 | `<div class="slot">` 안의 `〔 … 여기 들어갑니다 〕` + `<code>` |
  | `03_curves.png` | 1123 | 〃 |
  | `03_per_class.png` | 1429 | 〃 |

**즉 지금 빌드하면 임베드는 4/7 이고, 클라이맥스인 전/후 비교 그림은 HTML 에 나오지 않습니다.**

---

## 4. 결정 요청 (택 1)

**(A) 의도된 설계라면 — 조치 불필요.**
해당 박스가 `복귀 후 확인 · 실습 결과` 로 되어 있어, 그 대목에서 **코랩으로 돌아가 실물을 보여주는** 구성이라면 현재 상태가 정상입니다(수업 흐름 01:15~01:25 와 일치). 빌더는 conf 슬라이더만 채우고 나머지는 자리표시로 둡니다.

**(B) HTML 에도 박히길 원한다면 — 템플릿에 `<img>` 슬롯만 추가해 주세요.**
빌더 코드는 **수정 불필요**합니다. 슬롯이 생기면 자동으로 채워집니다. 형식:

```html
<img class="fig-img" data-embed="03_before_after.png" alt="전: COCO 는 혈액에서 박스 거의 없음 / 후: 파인튜닝 후 세포마다 박스">
<img class="fig-img" data-embed="03_curves.png"       alt="loss 는 내려가고 mAP 는 올라가는 학습 곡선">
<img class="fig-img" data-embed="03_per_class.png"    alt="클래스별 mAP50·precision·recall 과 학습 박스 수">
```

- `src` 는 **넣지 마세요**(빌더가 주입).
- `<code>` 설명 텍스트는 남겨두셔도 무방합니다(빌더가 건드리지 않음).
- 클래스명(`fig-img` 등)은 템플릿 CSS 에 맞게 자유롭게.

---

## 5. 빌드 방법 (참고)

코랩에서 `session3/notebooks/02_build_html.ipynb` 를 GPU 런타임으로 **셀 1→5 순서** 실행
→ 셀 3이 `01_finetune` 을 실행(학습 10~15분)해 `outputs/` 를 채우고
→ 셀 4가 슬롯에 base64 주입 → **`outputs/session3_lecture.html`** (외부 연결 없는 단일 파일).
셀 4 출력에 `임베드 / 누락 / (참고) img 아닌 data-embed 언급 N건` 이 찍힙니다.
