"""강의 자료 빌더 — 템플릿의 <img data-embed="outputs/..."> 슬롯에 그림을 base64 로 넣어 한 파일로 만든다.

입력: session6_lecture_template.html, outputs/ 의 그림 (tools/zero_shot_check.py --run 으로 생성)
출력: session6_lecture.html (단독 열람용 — 인터넷·다른 파일 없이 열린다)
사용법 (session6 폴더에서): python tools/build_html.py
"""
import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "session6_lecture_template.html"
DST = ROOT / "session6_lecture.html"
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".svg": "image/svg+xml"}


def main():
    html = SRC.read_text(encoding="utf-8")
    missing = []

    def embed(m):
        rel = m.group(1)
        f = ROOT / rel
        if not f.exists():
            missing.append(rel)
            return m.group(0)
        b64 = base64.b64encode(f.read_bytes()).decode("ascii")
        return f'src="data:{MIME[f.suffix.lower()]};base64,{b64}" data-src="{rel}"'

    out = re.sub(r'data-embed="([^"]+)"', embed, html)
    if missing:
        print("그림이 없습니다 (먼저 tools/zero_shot_check.py --run):", ", ".join(missing))
        sys.exit(1)
    DST.write_text(out, encoding="utf-8")
    print(f"완료: {DST.name}  {DST.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
