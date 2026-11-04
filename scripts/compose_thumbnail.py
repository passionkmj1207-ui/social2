#!/usr/bin/env python3
"""thumbnail.json 사양으로 로컬에서 썸네일을 합성한다 (Canva를 쓸 수 없을 때의 대체 경로).

사용: python scripts/compose_thumbnail.py output/<slug> [--base path/to/photo.png]
입력: output/<slug>/thumbnail.json, 배경 사진(기본 config/brand.json의 base_image)
출력: output/<slug>/thumbnail_local.png

- 배경 하단에 어두운 그라데이션을 깔고, 흰색 굵은 헤드라인 + 좌하단 계정명을 얹는다.
- 배경 사진에 다른 사람의 글자·계정명이 있으면 먼저 제거하거나 다른 사진을 쓴다(thumbnail-guide.md).
"""
import argparse
import glob
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, brand, load_json  # noqa: E402

FONT_GLOBS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/**/NanumGothicExtraBold.ttf",
    "/usr/share/fonts/**/NanumGothicBold.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "C:/Windows/Fonts/malgunbd.ttf",
]


def find_font(size):
    for pattern in FONT_GLOBS:
        for p in glob.glob(pattern, recursive=True):
            try:
                return ImageFont.truetype(p, size, index=1 if p.endswith(".ttc") and "Noto" in p else 0)
            except OSError:
                continue
    sys.exit("[오류] 한글 굵은 폰트를 찾지 못했습니다.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--base")
    args = ap.parse_args()
    d = Path(args.dir)
    spec = load_json(d / "thumbnail.json")
    cfg = brand()["thumbnail"]
    lines = spec["headline_lines"]
    handle = spec.get("handle", brand()["handle"])
    if handle != brand()["handle"]:
        sys.exit(f"[오류] 계정명은 {brand()['handle']} 여야 합니다: {handle}")
    if len(lines) > cfg["max_lines"] or any(len(l) > cfg["max_chars_per_line"] for l in lines):
        sys.exit(f"[오류] 헤드라인은 {cfg['max_lines']}줄 이하, 줄당 {cfg['max_chars_per_line']}자 이하")

    base_path = Path(args.base or ROOT / spec.get("base_image", cfg["base_image"]))
    if not base_path.exists():
        sys.exit(f"[오류] 배경 사진이 없습니다: {base_path} (assets/thumbnail/ 은 저장소에 올리지 않는다)")
    W, H = cfg["size"]
    img = Image.open(base_path).convert("RGB")
    s = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    img = img.crop(((img.width - W) // 2, 0, (img.width - W) // 2 + W, H))

    # 하단 그라데이션
    y = np.arange(H)
    a = np.repeat((np.clip((y - H * 0.35) / (H * 0.30), 0, 1) ** 1.05 * 0.9)[:, None], W, axis=1)
    arr = np.asarray(img).astype(np.float32) * (1 - a[..., None]) + 12 * a[..., None]
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")

    size = int(124 * W / 1080)
    hf, af = find_font(size), find_font(int(50 * W / 1080))
    step = int(size * 1.15)
    margin = int(70 * W / 1080)
    top = int(H * 0.592) if len(lines) == 2 else int(H * 0.52)
    ay = int(H * 0.907)

    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    yy = top
    for ln in lines:
        sd.text((margin + 3, yy + 4), ln, font=hf, fill=(0, 0, 0, 180))
        yy += step
    sd.text((margin + 2, ay + 3), handle, font=af, fill=(0, 0, 0, 180))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(5)))
    dr = ImageDraw.Draw(img)
    yy = top
    for ln in lines:
        dr.text((margin, yy), ln, font=hf, fill=(255, 255, 255, 255))
        yy += step
    dr.text((margin, ay), handle, font=af, fill=(255, 255, 255, 255))
    out = d / "thumbnail_local.png"
    img.convert("RGB").save(out, optimize=True)
    print(f"생성: {out}")


if __name__ == "__main__":
    main()
