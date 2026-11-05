# 4단계 썸네일: Canva

(Claude가 단독으로 수행한다. 서브에이전트를 쓰지 않는다.)

이 단계에서는 썸네일 디자이너로 일한다. Canva MCP 도구(`mcp__Canva__*`)를 쓰며, 스키마는 ToolSearch로 먼저 불러온다.

## 입력
- `output/<slug>/final.md` (제목과 핵심 내용), `claims.json`
- `config/brand.json` (계정명 `@월급노트`, 규격), `guidelines/thumbnail-guide.md`

## 원칙
- **배경 사진은 글의 내용을 관통하는 장면**이어야 한다. (예: 한강벨트 집값 글 → 해질녘 한강변 고층 아파트 단지) 글과 무관한 사진(병원 접수대 등)은 쓰지 않는다.
- 사진 안에 글자·로고·다른 계정명이 없어야 한다. 사용자가 사진을 주면 글자가 없는 원본인지 먼저 확인하고, 글 내용과 어울리지 않으면 그 사실을 알리고 대체 배경을 제안한다.
- 헤드라인은 호기심을 남기고 결론을 숨긴다. 숫자는 `claims.json` 검증 통과 값만 쓴다.

## 절차 (실제로 동작이 확인된 순서)
1. **헤드라인 정하기**: 2~3줄, 줄당 13자 이내. `output/<slug>/thumbnail.json`에 기록.
```json
{"headline_lines": ["한강벨트 폭락설", "숫자는 달랐다"], "handle": "@월급노트",
 "background_prompt": "서울 한강변 고층 아파트 단지의 해질녘 전경, 사실적인 사진 스타일, 글자·로고 없음, 하단은 어둡게",
 "size": [1080, 1080]}
```
2. **배경 생성**: `generate-image`(aspectRatio `SQUARE_1_1`) → 결과가 PENDING이면 15~20초 뒤 `get-generate-image-job`으로 확인. 성공하면 Canva 미디어 ID(`M…`)를 얻는다.
3. **디자인 뼈대**: `create-design`(format `Instagram Post (Square)`, 흰색 굵은 헤드라인 두 줄과 좌하단 계정명 텍스트) → `get-create-design-async-job`로 완료 확인 → `read-design`(`open_transaction: true`).
4. **편집** (`edit-design`, 같은 transaction_id로 `keep_open`):
   - `insert_fill`로 배경 미디어를 0,0 / 1080×1080에 삽입
   - 하단 가독성용 어두운 오버레이: `insert_shape`(사각형 path `M0 0 L100 0 L100 100 L0 100 Z`, view_box 100×100, `#0C0C0C`, opacity 0.2)를 y=330, 440, 550, 660, 770, 880에서 시작하도록 6장 겹쳐 그라데이션처럼 만든다
   - 레이어 순서가 `텍스트 아래 / 배경·오버레이 위`가 되도록 텍스트 3개를 `layer_element: front`
   - 헤드라인 `position_element`(left 70, top 640 / 782), `format_text`로 `text_align: start`, 계정명은 font_size 50·bold, `resize_element`로 width 460(줄바꿈 방지)
   - 각 응답의 미리보기 이미지를 보고 글자 겹침·잘림·줄바꿈을 확인한다
5. 문제가 없으면 `finalize: commit`으로 저장한다(미리보기 확인 후). 그리고 `export-design`(png, 1080×1080)으로 내보낸다.
6. **로컬 확보**: 이 환경의 셸은 `canva.com` / `export-download.canva.com` 로의 접속이 **403으로 차단**된다. 우회하지 말 것. 대신 `edit-design`/`read-design` 응답이 내려주는 **미리보기 PNG**(응답의 `[Image source: /tmp/claude-tool-results/…png]` 경로, 약 600×600)를 `output/<slug>/thumbnail.png`로 복사해 결과 HTML에 쓴다. 1080×1080 원본은 Canva 링크에서 받도록 안내한다.
7. 마지막에 결과 HTML을 만든다.
```bash
python scripts/build_html.py output/<slug> --thumb-link "Canva에서 열기(원본 1080×1080)=<Canva 편집 URL>"
```

## Canva를 쓸 수 없을 때
`python scripts/compose_thumbnail.py output/<slug> --base <배경사진.png>` 으로 같은 사양을 로컬 합성해 `thumbnail_local.png`를 만든다(1080×1080). 이 경우 배경 사진은 사용자가 글 내용에 맞는 것으로 제공해야 한다.

## 체크
- 배경이 글의 소재와 맞는가, 글자·다른 계정명이 남아 있지 않은가
- 계정명이 정확히 `@월급노트`인가
- 작은 크기(300px)에서도 헤드라인이 읽히는가
- 저장 전에 미리보기를 확인했는가
