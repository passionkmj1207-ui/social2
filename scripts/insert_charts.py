#!/usr/bin/env python3
"""draft.md의 anchor 문단 뒤에 차트 이미지를 삽입해 final.md를 만든다.

사용: python scripts/insert_charts.py output/<slug>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_json  # noqa: E402


def main():
    if len(sys.argv) < 2:
        sys.exit("사용: insert_charts.py output/<slug>")
    d = Path(sys.argv[1])
    draft = (d / "draft.md").read_text(encoding="utf-8")
    charts = load_json(d / "charts.json").get("charts", [])

    blocks = draft.split("\n\n")
    errors = []
    inserts = {}  # block index -> [markdown...]
    for ch in charts:
        png = d / "charts" / f"{ch['id']}.png"
        if not png.exists():
            errors.append(f"{ch['id']}: 이미지가 없습니다 (make_charts.py 먼저 실행)")
            continue
        hits = [i for i, b in enumerate(blocks) if ch["anchor"] in b]
        if len(hits) != 1:
            errors.append(f"{ch['id']}: anchor가 {len(hits)}곳에 있음 → '{ch['anchor']}' (정확히 1곳이어야 함)")
            continue
        md = f"![{ch.get('alt', ch['title'])}](charts/{ch['id']}.png)"
        inserts.setdefault(hits[0], []).append(md)
    if errors:
        for e in errors:
            print("[오류]", e)
        sys.exit(1)

    out = []
    for i, b in enumerate(blocks):
        out.append(b)
        out.extend(inserts.get(i, []))
    (d / "final.md").write_text("\n\n".join(out), encoding="utf-8")
    print(f"생성: {d / 'final.md'} (그래프 {sum(len(v) for v in inserts.values())}개 삽입)")


if __name__ == "__main__":
    main()
