# social2 — 월급노트 블로그 제작 인프라

경영관리 실무자의 시선으로 경제·부동산 이슈를 데이터로 풀어 쓰는 블로그 "월급노트"(`@월급노트`)의 글 제작 파이프라인이다.

## 워크플로우
```
/post <주제>
  └ 작가 ──▶ 수치검증 ──(PASS)──▶ 그래프 ──▶ 썸네일(Canva)   (전부 Claude 단독 수행)
        ▲            │
        └─(FIX/FAIL, 최대 2회)
```
- **서브에이전트는 쓰지 않는다. 모든 단계를 Claude가 단독으로 직접 수행한다.**
- 단계별 절차: `guidelines/stages/*.md`, 오케스트레이션: `.claude/commands/post.md`
- 작업 폴더: `output/<slug>/` (git 제외)
  - `brief.md` → `draft.md` + `claims.json` → `verification.json` → `charts.json` + `charts/*.png` → `final.md`/`final.html` → `thumbnail.json` + `thumbnail.png` → **`result.html`(최종 결과물)**

## 규칙
- 글은 `guidelines/writing-guide.md`를 따른다. 썸네일은 `guidelines/thumbnail-guide.md`. 썸네일 배경은 글의 내용에 맞는 장면이어야 한다.
- **본문의 모든 수치는 `claims.json`에 기록하고 fact-checker를 통과해야 한다.** 통과하지 못한 수치는 쓰지 않는다.
- 그래프는 검증을 통과(`PASS`)한 수치로만 만든다.
- 현재 시점 통계는 반드시 검색으로 확인한다. 기억으로 쓰지 않는다.
- 커뮤니티 원문은 요약만 하고 닉네임·회사명 등 식별 정보를 쓰지 않는다.
- 투자·매매 권유 문구는 쓰지 않는다.
- 이 저장소는 **공개**다. 비밀키, 미발행 초안, 배경 사진 원본(`assets/thumbnail/`)을 커밋하지 않는다.

## 스크립트 (`python3`, matplotlib 필요)
| 명령 | 역할 |
|---|---|
| `python scripts/validate_claims.py output/<slug>` | claims 구조·계산식·문구 존재 검사, 미등록 숫자 경고 |
| `python scripts/make_charts.py output/<slug>` | charts.json → PNG (검증 PASS만 허용) |
| `python scripts/insert_charts.py output/<slug>` | draft.md + 그래프 → final.md |
| `python scripts/render_html.py output/<slug>` | final.md → final.html (서식 표기 변환, 중간 산출물) |
| `python scripts/build_html.py output/<slug>` | **최종 결과물 result.html**: 제목·썸네일·본문·그래프, 네이버용 복사 버튼, 이미지별 다운로드 버튼 |
| `python scripts/compose_thumbnail.py output/<slug>` | thumbnail.json → 로컬 썸네일 합성(Canva 대체 경로) |
| `python tests/run_tests.py` | 예제로 전체 스크립트 회귀 테스트 |
