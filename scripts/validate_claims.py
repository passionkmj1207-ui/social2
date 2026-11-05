#!/usr/bin/env python3
"""claims.json 구조·계산식·문구 존재를 검사하고, 장부에 없는 숫자를 경고한다.

사용: python scripts/validate_claims.py output/<slug> [--strict] [--require-pass]
  --strict        미등록 숫자 경고도 오류로 취급
  --require-pass  verification.json의 overall이 PASS이고 모든 claim이 PASS/PASS_SECONDARY인지 확인
"""
import argparse
import ast
import operator
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import GOOD_SECONDARY, claims_by_id, load_json  # noqa: E402

REQUIRED = ["id", "value", "unit", "type", "source_name", "as_of"]
TYPES = {"reported", "calculated"}
OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
DATE_SUFFIX = ("월", "일", "년", "번째", "호", "차", "구", "㎡", "가지")
WEEK_OF_MONTH = re.compile(r"\d월\s*$")  # "10월 4주" 같은 주차 표기
SKIP_LINE = ("**출처", "출처", "※", "<!--")


def safe_eval(expr, env):
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.Name):
            if n.id not in env:
                raise ValueError(f"알 수 없는 claim id: {n.id}")
            return env[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.operand))
        raise ValueError(f"허용되지 않는 수식 요소: {ast.dump(n)[:40]}")
    return ev(ast.parse(expr, mode="eval"))


def strip_markup(text):
    text = re.sub(r"\[빨강:\s*", "", text)
    text = text.replace("==", "").replace("**", "")
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--require-pass", action="store_true")
    args = ap.parse_args()

    d = Path(args.dir)
    claims_doc = load_json(d / "claims.json")
    draft = (d / "draft.md").read_text(encoding="utf-8")
    plain = strip_markup(draft)
    claims = claims_doc.get("claims", [])
    by_id = claims_by_id(claims_doc)
    errors, warnings = [], []

    if len(by_id) != len(claims):
        errors.append("claim id가 비어 있거나 중복되었습니다.")

    # 1) 필드 검사
    for c in claims:
        cid = c.get("id", "?")
        for f in REQUIRED:
            if f not in c:
                errors.append(f"{cid}: 필수 필드 '{f}' 없음")
        if c.get("type") not in TYPES:
            errors.append(f"{cid}: type은 reported/calculated 중 하나여야 함")
        if c.get("type") == "reported" and not c.get("source_url") and not c.get("user_provided"):
            errors.append(f"{cid}: reported는 source_url(또는 user_provided: true)이 필요함")
        if c.get("type") == "calculated" and not c.get("formula"):
            errors.append(f"{cid}: calculated는 formula가 필요함")
        in_draft = c.get("in_draft", True)
        if in_draft:
            q = c.get("quote")
            if not q:
                errors.append(f"{cid}: quote 없음 (차트 전용이면 in_draft: false)")
            elif q not in draft and q not in plain:
                errors.append(f"{cid}: quote가 draft.md에 없음 → '{q}'")

    # 2) 계산식 재현
    env = {cid: c["value"] for cid, c in by_id.items()
           if isinstance(c.get("value"), (int, float))}
    for c in claims:
        if c.get("type") != "calculated" or not c.get("formula"):
            continue
        try:
            got = safe_eval(c["formula"], env)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{c['id']}: 수식 오류 ({e})")
            continue
        tol = c.get("tolerance", 0.05)
        if abs(got - c["value"]) > tol:
            errors.append(
                f"{c['id']}: 계산 불일치 — 수식 결과 {got:.4f}, 기록값 {c['value']} (허용오차 {tol})")

    # 3) 미등록 숫자 경고
    spans = []
    for c in claims:
        q = c.get("quote")
        if q and c.get("in_draft", True):
            for src in (plain,):
                for m in re.finditer(re.escape(strip_markup(q)), src):
                    spans.append((m.start(), m.end()))
    offset = 0
    for line in plain.splitlines(keepends=True):
        start = offset
        offset += len(line)
        if line.strip().startswith(SKIP_LINE):
            continue
        for m in NUM.finditer(line):
            s, e = start + m.start(), start + m.end()
            tail = plain[e:e + 2]
            if tail.startswith(DATE_SUFFIX):
                continue
            if tail.startswith("주") and WEEK_OF_MONTH.search(line[:m.start()]):
                continue
            # 결산 분기 표기(1~4분기)는 수치가 아니므로 제외. 12분기 같은 값은 계속 검사한다.
            if tail.startswith("분기") and m.group() in ("1", "2", "3", "4"):
                continue
            if not any(a <= s and e <= b for a, b in spans):
                warnings.append(f"장부에 없는 숫자: '{m.group()}' → …{line.strip()[:50]}…")

    # 4) 검증 결과 게이트
    if args.require_pass:
        v = load_json(d / "verification.json")
        if v.get("overall") != "PASS":
            errors.append(f"verification.json overall = {v.get('overall')} (PASS 필요)")
        for cid in by_id:
            verdict = v.get("claims", {}).get(cid, {}).get("verdict", "MISSING")
            if verdict not in GOOD_SECONDARY:
                errors.append(f"{cid}: 검증 판정 {verdict}")

    for w in warnings:
        print(f"[경고] {w}")
    for e in errors:
        print(f"[오류] {e}")
    if args.strict and warnings:
        errors.append("strict 모드: 미등록 숫자 경고")
    print(f"claims {len(claims)}개 / 오류 {len(errors)}개 / 경고 {len(warnings)}개")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
