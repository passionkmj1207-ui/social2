#!/usr/bin/env python3
"""예제(examples/hangang-belt)로 파이프라인 스크립트를 회귀 테스트한다.
사용: python tests/run_tests.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "examples" / "hangang-belt"
PY = sys.executable


def run(script, d, *extra):
    p = subprocess.run([PY, str(ROOT / "scripts" / script), str(d), *extra],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def fresh():
    d = Path(tempfile.mkdtemp()) / "hangang-belt"
    shutil.copytree(EX, d)
    return d


def check(name, cond, info=""):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        print(info)
        sys.exit(1)


def main():
    # 1) 정상 경로
    d = fresh()
    rc, out = run("validate_claims.py", d, "--require-pass")
    check("validate: 예제 통과", rc == 0, out)
    rc, out = run("make_charts.py", d)
    check("make_charts: SECONDARY 수치는 기본 차단", rc == 1 and "PASS_SECONDARY" in out, out)
    rc, out = run("make_charts.py", d, "--allow-secondary")
    check("make_charts: --allow-secondary로 생성", rc == 0 and (d / "charts" / "chart1.png").exists(), out)
    rc, out = run("insert_charts.py", d)
    final = (d / "final.md").read_text(encoding="utf-8")
    check("insert_charts: 앵커 뒤에 삽입", rc == 0 and "![" in final
          and final.index("chart1.png") < final.index("실거래에서도 확인된다"), out)
    check("insert_charts: 두 번째 그래프", final.index("chart2.png") < final.index("팔려는 사람은 늘었고"))
    rc, out = run("render_html.py", d, "--inline-images")
    html = (d / "final.html").read_text(encoding="utf-8")
    check("render_html: 노랑/빨강/볼드 변환", rc == 0 and "#FFF3A3" in html
          and "#E02020" in html and "<b>" in html and "data:image/png;base64" in html, out)

    # 2) 계산 불일치 탐지
    d = fresh()
    c = json.loads((d / "claims.json").read_text(encoding="utf-8"))
    for x in c["claims"]:
        if x["id"] == "c21":
            x["value"] = 80.0
    (d / "claims.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    rc, out = run("validate_claims.py", d)
    check("validate: 계산 불일치 탐지", rc == 1 and "c21" in out and "계산 불일치" in out, out)

    # 3) 본문에 없는 quote 탐지
    d = fresh()
    c = json.loads((d / "claims.json").read_text(encoding="utf-8"))
    c["claims"][0]["quote"] = "존재하지 않는 문구"
    (d / "claims.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    rc, out = run("validate_claims.py", d)
    check("validate: 본문에 없는 quote 탐지", rc == 1 and "c1" in out, out)

    # 4) 장부에 없는 숫자 경고
    d = fresh()
    t = (d / "draft.md").read_text(encoding="utf-8").replace("전주 0.13%보다", "전주 0.13%보다 약 4.2%p")
    (d / "draft.md").write_text(t, encoding="utf-8")
    rc, out = run("validate_claims.py", d)
    check("validate: 미등록 숫자 경고", "장부에 없는 숫자" in out and "4.2" in out, out)
    rc, out = run("validate_claims.py", d, "--strict")
    check("validate: strict면 오류", rc == 1, out)

    # 5) 검증 실패 claim은 그래프 차단
    d = fresh()
    v = json.loads((d / "verification.json").read_text(encoding="utf-8"))
    v["claims"]["c5"]["verdict"] = "FAIL"
    (d / "verification.json").write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
    rc, out = run("make_charts.py", d, "--allow-secondary")
    check("make_charts: FAIL claim 차단", rc == 1 and "c5" in out, out)

    # 6) 그래프 값이 claim과 다르면 차단
    d = fresh()
    ch = json.loads((d / "charts.json").read_text(encoding="utf-8"))
    ch["charts"][0]["points"][0]["value"] = -0.99
    (d / "charts.json").write_text(json.dumps(ch, ensure_ascii=False), encoding="utf-8")
    rc, out = run("make_charts.py", d, "--allow-secondary")
    check("make_charts: claim과 다른 값 차단", rc == 1 and "≠" in out, out)

    print("\n모든 테스트 통과")


if __name__ == "__main__":
    main()
