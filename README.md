# social2 · 월급노트 블로그 제작 인프라

경제·부동산 이슈를 데이터로 풀어 쓰는 블로그 **월급노트(@월급노트)** 의 글 제작 파이프라인.
작가 → 수치검증 → 그래프 삽입 → 캔바 썸네일을 에이전트 워크플로우로 묶었다.

```
/post <주제>
  ① writer ─────▶ ② fact-checker ──(PASS)──▶ ③ chart-creator ──▶ ④ thumbnail-designer (Canva)
       ▲                │
       └── FIX/FAIL ────┘   (최대 2회 재작업)
```

| 단계 | 에이전트 | 산출물 (`output/<slug>/`) | 게이트 |
|---|---|---|---|
| ① 초안 | `writer` | `draft.md`, `claims.json`, `writer_notes.md` | `validate_claims.py` 오류 0 |
| ② 검증 | `fact-checker` | `verification.json`, `verification_report.md` | `overall == PASS` |
| ③ 그래프 | `chart-creator` | `charts.json`, `charts/*.png`, `final.md`, `final.html` | 검증 PASS 수치만 사용 |
| ④ 썸네일 | `thumbnail-designer` | `thumbnail.json`, `thumbnail.png` | 사용자 승인 후 저장 |

## 핵심 설계
- **수치 장부(`claims.json`)**: 본문의 모든 숫자를 출처·기준 시점과 함께 기록한다. 직접 계산한 값은 `formula`로 남기고 스크립트가 재계산해 대조한다.
- **독립 검증**: 수치검증 에이전트는 작가의 출처를 믿지 않고 원출처에서 다시 확인한다. 판정은 `PASS`(원자료 또는 독립 2개 출처) / `PASS_SECONDARY`(단일 매체) / `FIX` / `FAIL`.
- **그래프 게이트**: 그래프의 모든 점은 `claim_id`에 연결되고, 값이 장부와 다르거나 판정이 `PASS`가 아니면 생성이 중단된다(`--allow-secondary`로만 단일 매체 수치 허용).
- **서식 표기**: `==노랑==`, `[빨강: …]`, `**볼드**` → `render_html.py`가 실제 서식으로 변환해 네이버 에디터 붙여넣기용 HTML을 만든다.

## 사용법

### Claude Code에서
```
/post 한강벨트 집값 폭락설, 사실일까
```
`.claude/commands/post.md` 가 4개 서브에이전트를 순서대로 호출한다.

### 스크립트만 따로
```bash
pip install -r requirements.txt
python scripts/validate_claims.py output/<slug> [--strict] [--require-pass]
python scripts/make_charts.py     output/<slug> [--allow-secondary]
python scripts/insert_charts.py   output/<slug>
python scripts/render_html.py     output/<slug> [--inline-images]
python scripts/compose_thumbnail.py output/<slug>   # Canva를 못 쓸 때 대체
python tests/run_tests.py          # examples/hangang-belt 로 회귀 테스트
```

## 썸네일 (Canva)
- 배경 사진은 **저장소에 올리지 않는다**(공개 저장소, 저작권). 로컬 `assets/thumbnail/base.png`에 두거나 세션에 첨부한다.
- 규격 1080×1080, 흰색 굵은 헤드라인 2~3줄, 좌하단 `@월급노트`. 자세한 규칙은 `guidelines/thumbnail-guide.md`.
- 사진에 다른 사람의 글자·계정명이 박혀 있으면 쓰지 않는다. 글자 없는 원본을 쓴다.

## 폴더
```
.claude/agents/      writer · fact-checker · chart-creator · thumbnail-designer
.claude/commands/    post.md (워크플로우)
guidelines/          writing-guide.md (v3) · thumbnail-guide.md
config/brand.json    계정명, 썸네일·차트 규격
scripts/             검증·차트·삽입·HTML 변환
examples/            hangang-belt (예제 입력)
tests/run_tests.py   회귀 테스트
output/              생성 산출물 (git 제외)
```

## 주의
- 공개 저장소다. 미발행 초안(`output/`), 비밀키, 배경 사진 원본은 커밋하지 않는다.
- 예제 수치는 2026-11-04 시점 보도 기준의 **테스트용**이다. 발행 전에는 항상 재검증한다.
- 투자·매매 권유 문구를 쓰지 않는다.
