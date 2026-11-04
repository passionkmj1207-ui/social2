---
description: 월급노트 블로그 글을 작가 → 수치검증 → 그래프 삽입 → 캔바 썸네일 순서로 완성한다
argument-hint: <주제 | 화제의 원글 요약 | 슬러그>
---

`$ARGUMENTS`를 주제로 아래 워크플로우를 **순서대로** 실행한다. 각 단계는 해당 서브에이전트에게 맡기고, 게이트를 통과해야 다음으로 간다.

## 0. 준비
- 슬러그를 정한다(영문 소문자·하이픈). `output/<slug>/` 디렉터리를 만든다.
- `output/<slug>/brief.md`에 주제, 원글 요약(닉네임·회사명 제외), 독자 질문, 글 유형(A/B)을 적는다.

## 1. 작가 (`writer` 에이전트)
- `draft.md`, `claims.json`, `writer_notes.md` 작성.
- **게이트 1**: `python scripts/validate_claims.py output/<slug>` 가 오류 없이 끝나야 한다.

## 2. 수치검증 (`fact-checker` 에이전트)
- `verification.json`, (필요 시) `verification_report.md` 작성.
- **게이트 2**: `overall == PASS`. 아니면 작가에게 재작업을 맡기고 2번으로 돌아간다. **최대 2회**. 그래도 통과하지 못하면 중단하고 사용자에게 남은 쟁점을 보고한다.

## 3. 이미지 크리에이터 (`chart-creator` 에이전트)
- `charts.json` 설계 → `make_charts.py` → `insert_charts.py` → `render_html.py`.
- 그래프가 필요 없다고 판단하면 `charts: []`로 두고 `final.md`는 draft와 동일하게 만든다.
- **게이트 3**: `final.md`, `final.html` 생성, PNG를 눈으로 확인.

## 4. 썸네일 (`thumbnail-designer` 에이전트)
- 3단계가 끝난 뒤에만 실행한다. **글의 내용을 관통하는 배경**을 Canva로 생성하고, 정사각형 썸네일에 헤드라인과 `@월급노트`를 넣는다.
- 미리보기 확인 후 저장한다.

## 5. 최종 결과물 HTML
```bash
python scripts/build_html.py output/<slug> --thumb-link "Canva에서 열기(원본 1080×1080)=<Canva URL>"
```
- **최종 결과물은 `output/<slug>/result.html` 한 파일**이다. 제목·썸네일·본문·그래프 이미지를 담고, [본문 복사] 버튼으로 네이버 블로그에 그대로 붙여넣을 수 있으며, 이미지마다 [다운로드] 버튼이 있다.

## 6. 마무리 보고
- `result.html` 경로, 검증 요약(PASS/PASS_SECONDARY 개수), 사람이 발행 전에 확인할 항목(단일 출처 수치, 직접 계산 값, 캡처 식별 정보)을 짧게 보고한다.
