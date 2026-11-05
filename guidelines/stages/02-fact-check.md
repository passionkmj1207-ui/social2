# 2단계 수치검증: 독립 재확인

(Claude가 단독으로 수행한다. 서브에이전트를 쓰지 않는다.)

이 단계에서는 수치검증 담당으로 일한다. 1단계에서 직접 쓴 글이라도 믿지 않는다. 적어 둔 출처와 값을 **처음부터 다시 검색해** 확인하고, 기억이나 앞 단계 메모에 기대지 않는다.

## 입력
- `output/<slug>/draft.md`, `output/<slug>/claims.json`

## 절차
1. **구조 점검**: `python scripts/validate_claims.py output/<slug>` 를 실행한다. 오류가 있으면 verification.json에 그대로 기록하고 작가에게 돌려보낸다.
2. **claim별 재확인** (모든 claim, 빠짐없이)
   - `reported`: `source_url`을 WebFetch로 열거나 같은 수치를 WebSearch로 다시 찾아 **값·단위·기준 시점**을 대조한다. 작가가 적은 URL만 보지 말고 다른 매체나 기관 자료로 교차 확인한다.
   - `calculated`: `formula`를 `python3`으로 직접 계산해 값을 확인하고, 입력이 되는 claim들이 먼저 통과했는지 본다. 반올림 표기("약 71%")가 계산값과 맞는지 확인한다.
   - 문맥 점검: 본문 문장이 수치의 의미를 왜곡하지 않는지(전주 대비 vs 연초 대비, 상승률 vs 상승폭, 명목 vs 실질, 신고일 vs 계약일 등) 본다.
3. **판정**
   - `PASS`: 기관 원자료를 직접 확인했거나, **서로 독립된 2개 이상 출처**에서 같은 값을 확인했다.
   - `PASS_SECONDARY`: 값은 확인했지만 단일 매체 보도에만 근거한다(원자료 미대조). 글에는 쓸 수 있으나 차트에는 기본적으로 쓰지 않는다.
   - `FIX`: 값/단위/기준 시점/표현이 틀렸다. 맞는 값과 근거를 `correction`에 쓴다.
   - `FAIL`: 확인할 수 없거나 출처가 없다. 삭제하거나 문장을 바꿔야 한다.
4. **결과 기록**: `output/<slug>/verification.json`

```json
{
  "slug": "예시-슬러그",
  "claims": {
    "c1": {
      "verdict": "PASS",
      "checked_value": 0.09,
      "as_of": "2026-10-26",
      "sources": ["https://...", "https://..."],
      "evidence": "부동산원 10월 4주 발표에서 서울 +0.09% 확인, 2개 매체 일치",
      "correction": ""
    }
  },
  "summary": {"PASS": 0, "PASS_SECONDARY": 0, "FIX": 0, "FAIL": 0},
  "overall": "PASS | NEEDS_REVISION"
}
```
5. `overall`은 **FIX/FAIL이 하나도 없을 때만** `PASS`다. 그렇지 않으면 `NEEDS_REVISION`이고, 수정이 필요한 문장을 `output/<slug>/verification_report.md`에 작가가 바로 고칠 수 있도록 정리한다.

## 원칙
- 확인하지 못한 값에 PASS를 주지 않는다. 확인 못 했으면 FAIL이다.
- 기준 시점이 다르면(예: 주간 값을 월간처럼 표기) FIX다.
- 작가의 문장을 직접 고치지 않는다. 판정과 근거만 남긴다.
- 검증은 2회까지 반복한다. 2회 후에도 FAIL이 남으면 `overall: NEEDS_REVISION`으로 두고 사람에게 알린다.
