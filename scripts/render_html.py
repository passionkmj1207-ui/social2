#!/usr/bin/env python3
"""final.md → final.html (본문 미리보기용). 최종 결과물은 build_html.py 의 result.html 이다.

사용: python scripts/render_html.py output/<slug> [--inline-images]
"""
import argparse
import base64
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md_render import render  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--inline-images", action="store_true")
    args = ap.parse_args()
    d = Path(args.dir)
    src = d / "final.md"
    if not src.exists():
        sys.exit("final.md가 없습니다. insert_charts.py를 먼저 실행하세요.")

    def fig(alt, path):
        if args.inline_images and (d / path).exists():
            path = "data:image/png;base64," + base64.b64encode((d / path).read_bytes()).decode()
        return (f'<p style="text-align:center"><img src="{html.escape(path)}" '
                f'alt="{html.escape(alt)}" style="max-width:100%"></p>')

    title, blocks = render(src.read_text(encoding="utf-8"), fig)
    page = (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        f"<title>{html.escape(title or '월급노트')}</title></head>"
        '<body style="max-width:720px;margin:40px auto;padding:0 16px;'
        'font-family:\'Noto Sans KR\',\'Malgun Gothic\',sans-serif">'
        f'<h1 style="line-height:1.4">{html.escape(title)}</h1>' + "\n".join(blocks) + "</body></html>"
    )
    (d / "final.html").write_text(page, encoding="utf-8")
    print(f"생성: {d / 'final.html'}")


if __name__ == "__main__":
    main()
