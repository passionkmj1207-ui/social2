"""draft/final.md의 서식 표기를 인라인 스타일 HTML로 변환한다.
네이버 에디터에 붙여넣어도 유지되도록 class 대신 **인라인 style**만 쓴다.

표기: ==노랑== / [빨강: …] / **볼드** / # 제목 / ### 소제목 / - 목록 / ※ 각주 / ![alt](src)
"""
import html
import re

P_STYLE = "margin:0 0 22px;line-height:1.95;font-size:16px;color:#222"
H3_STYLE = "margin:44px 0 16px;line-height:1.5;font-size:22px;color:#111"
NOTE_STYLE = "margin:0 0 16px;line-height:1.7;font-size:13px;color:#6b7280"
YELLOW = "#FFF3A3"
RED = "#E02020"


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"==(.+?)==", rf'<span style="background-color:{YELLOW}">\1</span>', t)
    t = re.sub(r"\[빨강:\s*(.+?)\]", rf'<span style="color:{RED}">\1</span>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t


def render(md, image_cb):
    """md 문자열 → (title, [html 블록…]). image_cb(alt, src)가 이미지 블록 HTML을 돌려준다."""
    title, out = "", []
    for raw in md.split("\n\n"):
        blk = raw.strip()
        if not blk or blk.startswith("<!--"):
            continue
        m = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", blk)
        if m:
            out.append(image_cb(m.group(1), m.group(2)))
        elif blk.startswith("# "):
            title = blk[2:].strip()
        elif blk.startswith("### "):
            out.append(f'<p style="{H3_STYLE}"><b>{inline(blk[4:])}</b></p>')
        elif blk == "---":
            out.append('<hr style="border:0;border-top:1px solid #e5e7eb;margin:32px 0">')
        elif blk.startswith(("※", "**출처")):
            out.append(f'<p style="{NOTE_STYLE}">{inline(blk)}</p>')
        elif all(l.lstrip().startswith("- ") for l in blk.splitlines()):
            items = "".join(
                f'<li style="margin:0 0 8px">{inline(l.lstrip()[2:])}</li>' for l in blk.splitlines())
            out.append(f'<ul style="{P_STYLE}">{items}</ul>')
        else:
            out.append(f'<p style="{P_STYLE}">{inline(blk).replace(chr(10), "<br>")}</p>')
    return title, out
