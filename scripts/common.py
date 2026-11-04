"""공통 유틸: JSON 로딩, 검증 판정 게이트, 한글 폰트 선택."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOOD = {"PASS"}
GOOD_SECONDARY = {"PASS", "PASS_SECONDARY"}

FONT_CANDIDATES = [
    "NanumGothic", "NanumBarunGothic", "Noto Sans CJK KR", "Noto Sans KR",
    "Malgun Gothic", "AppleGothic", "Noto Sans CJK JP", "Noto Sans CJK SC",
]


def load_json(path):
    path = Path(path)
    if not path.exists():
        sys.exit(f"[오류] 파일이 없습니다: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"[오류] JSON 형식 오류 {path}: {e}")


def brand():
    return load_json(ROOT / "config" / "brand.json")


def claims_by_id(claims_doc):
    return {c["id"]: c for c in claims_doc.get("claims", []) if "id" in c}


def require_verified(claim_ids, verification, allow_secondary=False):
    """claim_ids 전부가 허용된 판정인지 확인하고, 위반 목록을 돌려준다."""
    ok = GOOD_SECONDARY if allow_secondary else GOOD
    bad = []
    verdicts = verification.get("claims", {})
    for cid in claim_ids:
        v = verdicts.get(cid, {}).get("verdict", "MISSING")
        if v not in ok:
            bad.append((cid, v))
    return bad


def pick_font():
    from matplotlib import font_manager
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in FONT_CANDIDATES:
        if name in available:
            return name
    return None
