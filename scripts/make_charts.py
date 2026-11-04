#!/usr/bin/env python3
"""charts.json → PNG. 검증을 통과한 claim 값만 그린다.

사용: python scripts/make_charts.py output/<slug> [--allow-secondary]
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (brand, claims_by_id, load_json, pick_font,  # noqa: E402
                    require_verified)


def fmt_default(v):
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"


def draw(chart, cfg, font):
    pal = cfg["palette"]
    figsize = tuple(cfg.get("size_inches", [8, 4.5]))
    fig, ax = plt.subplots(figsize=figsize, dpi=cfg.get("dpi", 200))
    if font:
        plt.rcParams["font.family"] = font
    plt.rcParams["axes.unicode_minus"] = False

    pts = chart["points"]
    labels = [p["label"] for p in pts]
    vals = [p["value"] for p in pts]
    vf = chart.get("value_format")
    fmt = (lambda v: vf.format(v)) if vf else fmt_default
    kind = chart.get("type", "bar")
    colors = [pal["neg"] if v < 0 else pal["pos"] for v in vals]
    hi = set(chart.get("highlight", []))
    if hi:
        colors = [c if l in hi else pal["neutral"] for c, l in zip(colors, labels)]

    span = (max(vals + [0]) - min(vals + [0])) or 1
    if kind == "line":
        ax.plot(labels, vals, color=pal["pos"], linewidth=2.5, marker="o")
        for x, v in zip(labels, vals):
            ax.annotate(fmt(v), (x, v), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=10, color=pal["text"])
    elif kind == "barh":
        bars = ax.barh(labels[::-1], vals[::-1], color=colors[::-1], height=0.6)
        for b, v in zip(bars, vals[::-1]):
            ax.text(b.get_width() + (span * 0.01 if v >= 0 else -span * 0.01),
                    b.get_y() + b.get_height() / 2, fmt(v),
                    va="center", ha="left" if v >= 0 else "right",
                    fontsize=10, color=pal["text"])
        ax.margins(x=0.15)
    else:
        bars = ax.bar(labels, vals, color=colors, width=0.6)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2,
                    v + (span * 0.02 if v >= 0 else -span * 0.02), fmt(v),
                    ha="center", va="bottom" if v >= 0 else "top",
                    fontsize=10, color=pal["text"])
        ax.margins(y=0.15)

    if min(vals) < 0:
        (ax.axhline if kind != "barh" else ax.axvline)(0, color=pal["text"], linewidth=0.8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(pal["grid"])
    ax.tick_params(axis="both", length=0, labelsize=10, colors=pal["text"])
    (ax.xaxis if kind == "barh" else ax.yaxis).set_visible(False)
    ax.grid(False)

    fig.suptitle(chart["title"], x=0.02, y=0.98, ha="left", va="top",
                 fontsize=15, fontweight="bold", color=pal["text"])
    if chart.get("subtitle"):
        fig.text(0.02, 0.865, chart["subtitle"], ha="left", fontsize=10.5, color=pal["neutral"])
    fig.text(0.02, 0.02, f"출처: {chart['source']}", ha="left", fontsize=9, color=pal["neutral"])
    fig.text(0.98, 0.02, brand()["handle"], ha="right", fontsize=9, color=pal["neutral"])
    fig.subplots_adjust(top=0.78, bottom=0.14, left=0.04, right=0.97)
    return fig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--allow-secondary", action="store_true",
                    help="PASS_SECONDARY(단일 매체 근거) 수치도 허용")
    args = ap.parse_args()

    d = Path(args.dir)
    charts = load_json(d / "charts.json").get("charts", [])
    if not charts:
        print("charts.json에 그래프가 없습니다. 건너뜁니다.")
        return
    claims = claims_by_id(load_json(d / "claims.json"))
    verification = load_json(d / "verification.json")
    cfg = brand()["chart"]
    font = pick_font()
    if not font:
        print("[경고] 한글 폰트를 찾지 못했습니다. 글자가 깨질 수 있습니다.")

    # 1) 사전 검사: claim 연결, 값 일치, 검증 판정
    problems = []
    for ch in charts:
        pts = ch.get("points", [])
        if len(pts) < 2:
            problems.append(f"{ch.get('id')}: 데이터 포인트가 2개 미만")
        for p in pts:
            cid = p.get("claim_id")
            if cid not in claims:
                problems.append(f"{ch['id']}: claim_id '{cid}' 가 claims.json에 없음")
                continue
            if abs(claims[cid]["value"] - p["value"]) > 1e-9:
                problems.append(
                    f"{ch['id']}: '{p['label']}' 값 {p['value']} ≠ claim {cid} 값 {claims[cid]['value']}")
        for cid, v in require_verified([p.get("claim_id") for p in pts],
                                       verification, args.allow_secondary):
            problems.append(f"{ch['id']}: claim {cid} 검증 판정 {v} (허용되지 않음)")
    if problems:
        print("[차트 생성 중단]")
        for p in problems:
            print(" -", p)
        sys.exit(1)

    # 2) 렌더링
    out = d / "charts"
    out.mkdir(exist_ok=True)
    for ch in charts:
        fig = draw(ch, cfg, font)
        path = out / f"{ch['id']}.png"
        fig.savefig(path, facecolor="white")
        plt.close(fig)
        print(f"생성: {path}")


if __name__ == "__main__":
    main()
