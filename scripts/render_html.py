#!/usr/bin/env python3
"""final.md → final.html. 서식 표기(==노랑==, [빨강: …], **볼드**)를 실제 서식으로 변환한다.
네이버 에디터에 브라우저에서 열어 복사·붙여넣기 하기 위한 용도다.

사용: python scripts/render_html.py output/<slug> [--inline-images]
"""
import argparse
import base64
import html
import re
import sys
from pathlib import Path


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"==(.+?)==", r'<mark style="background:#FFF3A3;color:inherit">\1</mark>', t)
    t = re.sub(r"\[빨강:\s*(.+?)\]", r'<span style="color:#E02020">\1</span>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t


def img_tag(alt, src, base, inline_images):
    if inline_images:
        p = base / src
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            src = f"data:image/png;base64,{b64}"
    return (f'<p style="text-align:center"><img src="{html.escape(src)}" '
            f'alt="{html.escape(alt)}" style="max-width:100%"></p>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--inline-images", action="store_true")
    args = ap.parse_args()
    d = Path(args.dir)
    src = d / "final.md"
    if not src.exists():
        sys.exit("final.md가 없습니다. insert_charts.py를 먼저 실행하세요.")

    out, title = [], "월급노트"
    for raw in src.read_text(encoding="utf-8").split("\n\n"):
        blk = raw.strip()
        if not blk or blk.startswith("<!--"):
            continue
        m = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", blk)
        if m:
            out.append(img_tag(m.group(1), m.group(2), d, args.inline_images))
        elif blk.startswith("# "):
            title = blk[2:].strip()
            out.append(f"<h1>{inline(title)}</h1>")
        elif blk.startswith("### "):
            out.append(f"<h3>{inline(blk[4:])}</h3>")
        elif blk == "---":
            out.append("<hr>")
        elif blk.startswith(("※", "**출처")):
            out.append(f'<p style="font-size:0.85em;color:#6b7280">{inline(blk)}</p>')
        elif all(l.lstrip().startswith("- ") for l in blk.splitlines()):
            items = "".join(f"<li>{inline(l.lstrip()[2:])}</li>" for l in blk.splitlines())
            out.append(f"<ul>{items}</ul>")
        else:
            out.append(f"<p>{inline(blk).replace(chr(10), '<br>')}</p>")

    page = (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        f"<title>{html.escape(title)}</title>"
        '<style>body{max-width:720px;margin:40px auto;padding:0 16px;'
        'font-family:"Noto Sans KR","Malgun Gothic",sans-serif;line-height:1.85;color:#222}'
        "h1{font-size:1.6em;line-height:1.4}h3{margin-top:2em}</style></head><body>"
        + "\n".join(out) + "</body></html>"
    )
    (d / "final.html").write_text(page, encoding="utf-8")
    print(f"생성: {d / 'final.html'}")


if __name__ == "__main__":
    main()
