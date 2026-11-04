#!/usr/bin/env python3
"""최종 결과물 result.html 을 만든다 (단일 파일, 이미지는 base64 내장).

- [본문 복사] 버튼: 네이버 블로그 에디터에 그대로 붙여넣을 수 있는 서식(HTML)을 클립보드에 복사
- 이미지(썸네일, 그래프)마다 [다운로드] 버튼, 전체 받기 버튼
- 제목 복사 버튼

사용: python scripts/build_html.py output/<slug> [--thumbnail path.png] [--thumb-link URL ...]
  썸네일 기본값: output/<slug>/thumbnail.png → thumbnail_local.png 순으로 찾는다.
"""
import argparse
import base64
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import brand  # noqa: E402
from md_render import render  # noqa: E402


def data_uri(p):
    return "data:image/png;base64," + base64.b64encode(Path(p).read_bytes()).decode()


TEMPLATE = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · 발행 패키지</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f4f6;color:#222;font-family:'Noto Sans KR','Malgun Gothic','Apple SD Gothic Neo',sans-serif}
.bar{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #e5e7eb;padding:12px 20px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.bar b{margin-right:auto;font-size:15px}
.btn{display:inline-block;border:1px solid #d1d5db;background:#fff;color:#111;border-radius:8px;padding:9px 14px;font-size:14px;cursor:pointer;text-decoration:none;font-family:inherit}
.btn:hover{background:#f9fafb}
.btn.primary{background:#03c75a;border-color:#03c75a;color:#fff;font-weight:700}
.btn.primary:hover{background:#02b350}
.wrap{max-width:860px;margin:24px auto;padding:0 16px 80px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:24px;margin-bottom:20px}
.card h2{margin:0 0 14px;font-size:16px;color:#374151}
.hint{font-size:13px;color:#6b7280;line-height:1.7;margin:10px 0 0}
.thumb{display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap}
.thumb img{width:260px;border-radius:10px;border:1px solid #e5e7eb}
.thumb .side{flex:1;min-width:220px}
.titlebox{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.titlebox .t{flex:1;min-width:240px;font-size:20px;font-weight:700;line-height:1.5}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}
.gitem{border:1px solid #e5e7eb;border-radius:10px;padding:10px;text-align:center}
.gitem img{width:100%;border-radius:6px}
.gitem .n{font-size:12px;color:#6b7280;margin:8px 0}
#article{padding:8px 4px}
#article figure{margin:28px 0;text-align:center}
#article figure img{max-width:100%;border:1px solid #eee;border-radius:6px}
#article figure .btn{margin-top:10px;font-size:13px;padding:6px 10px}
.toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:#111;color:#fff;padding:11px 18px;border-radius:999px;font-size:14px;opacity:0;pointer-events:none;transition:opacity .2s}
.toast.on{opacity:.95}
</style></head><body>
<div class="bar">
  <b>월급노트 발행 패키지</b>
  <button class="btn primary" onclick="copyArticle('full')">본문 복사 (네이버용)</button>
  <button class="btn" onclick="copyArticle('placeholder')">본문 복사 (이미지 자리 표시)</button>
  <button class="btn" onclick="downloadAll()">이미지 전체 다운로드</button>
</div>
<div class="wrap">

  <div class="card"><h2>① 제목</h2>
    <div class="titlebox"><div class="t" id="post-title">__TITLE__</div>
    <button class="btn" onclick="copyTitle()">제목 복사</button></div>
  </div>

  <div class="card"><h2>② 썸네일</h2>
    <div class="thumb">__THUMB__</div>
  </div>

  <div class="card"><h2>③ 본문 (이 영역이 복사됩니다)</h2>
    <div id="article">__ARTICLE__</div>
    <p class="hint">「본문 복사 (네이버용)」은 서식(노란 형광펜·빨간 글씨·볼드)과 그래프 이미지를 함께 복사합니다.
    네이버 에디터에서 이미지가 붙지 않으면 「이미지 자리 표시」로 복사해 붙여넣은 뒤, 아래 ④의 이미지를 받아 해당 위치에 업로드하세요.</p>
  </div>

  <div class="card"><h2>④ 이미지 모음</h2>
    <div class="gallery">__GALLERY__</div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
var IMAGES = __IMAGES_JSON__;
document.querySelectorAll('img[data-idx]').forEach(function(im){im.src=IMAGES[+im.getAttribute('data-idx')].uri;});

function toast(msg){var t=document.getElementById('toast');t.textContent=msg;t.classList.add('on');
  clearTimeout(window.__tt);window.__tt=setTimeout(function(){t.classList.remove('on')},2200);}

function buildClone(mode){
  var c=document.getElementById('article').cloneNode(true);
  c.querySelectorAll('.no-copy').forEach(function(e){e.remove()});
  if(mode==='placeholder'){
    c.querySelectorAll('figure').forEach(function(f){
      var img=f.querySelector('img');
      var p=document.createElement('p');
      p.setAttribute('style','margin:0 0 22px;line-height:1.9;font-size:14px;color:#6b7280');
      p.textContent='[그림 삽입 위치: '+(img.getAttribute('data-file')||'image')+' — '+(img.getAttribute('alt')||'')+']';
      f.replaceWith(p);
    });
  }
  return c;
}
function plainText(c){
  return Array.prototype.map.call(c.children,function(e){return e.textContent.trim()}).filter(Boolean).join('\n\n');
}
function legacyCopy(html){
  var box=document.createElement('div');
  box.setAttribute('contenteditable','true');
  box.style.cssText='position:fixed;left:-9999px;top:0;width:700px';
  box.innerHTML=html;document.body.appendChild(box);
  var r=document.createRange();r.selectNodeContents(box);
  var s=window.getSelection();s.removeAllRanges();s.addRange(r);
  var ok=false;try{ok=document.execCommand('copy')}catch(e){}
  s.removeAllRanges();box.remove();return ok;
}
async function copyRich(html,text,okMsg){
  try{
    if(navigator.clipboard&&window.ClipboardItem){
      await navigator.clipboard.write([new ClipboardItem({
        'text/html':new Blob([html],{type:'text/html'}),
        'text/plain':new Blob([text],{type:'text/plain'})})]);
      toast(okMsg);return;
    }
  }catch(e){}
  if(legacyCopy(html)){toast(okMsg);}else{toast('복사에 실패했습니다. 본문을 직접 선택해 복사해 주세요.');}
}
function copyArticle(mode){
  var c=buildClone(mode);
  copyRich(c.innerHTML,plainText(c),
    mode==='full'?'본문을 복사했습니다. 네이버 에디터에 붙여넣으세요.':'본문(이미지 자리 표시)을 복사했습니다.');
}
function copyTitle(){
  var t=document.getElementById('post-title').textContent.trim();
  copyRich('<span>'+t.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</span>',t,'제목을 복사했습니다.');
}
function dl(name,uri){var a=document.createElement('a');a.href=uri;a.download=name;
  document.body.appendChild(a);a.click();a.remove();}
function downloadOne(i){dl(IMAGES[i].file,IMAGES[i].uri);}
function downloadAll(){
  IMAGES.forEach(function(im,i){setTimeout(function(){dl(im.file,im.uri)},i*350)});
  toast('이미지 '+IMAGES.length+'개를 다운로드합니다.');
}
</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--thumbnail")
    ap.add_argument("--thumb-link", action="append", default=[],
                    help="썸네일 원본(Canva 등) 링크, 여러 번 지정 가능. 형식: 라벨=URL")
    ap.add_argument("--out", default="result.html")
    args = ap.parse_args()
    d = Path(args.dir)
    src = d / "final.md"
    if not src.exists():
        sys.exit("final.md가 없습니다. insert_charts.py를 먼저 실행하세요.")

    images = []  # {file, uri, alt}

    def fig(alt, path):
        p = d / path
        if not p.exists():
            sys.exit(f"[오류] 이미지가 없습니다: {p}")
        idx = len(images)
        images.append({"file": p.name, "uri": data_uri(p), "alt": alt})
        return (
            f'<figure><img data-idx="{idx}" alt="{html.escape(alt)}" '
            f'data-file="{html.escape(p.name)}" style="max-width:100%">'
            f'<br class="no-copy"><button class="btn no-copy" onclick="downloadOne({idx})">'
            f"이미지 다운로드 ({html.escape(p.name)})</button></figure>"
        )

    title, blocks = render(src.read_text(encoding="utf-8"), fig)

    # 썸네일
    thumb_path = Path(args.thumbnail) if args.thumbnail else next(
        (d / n for n in ("thumbnail.png", "thumbnail_local.png") if (d / n).exists()), None)
    if thumb_path and thumb_path.exists():
        tidx = len(images)
        images.append({"file": "thumbnail.png", "uri": data_uri(thumb_path),
                       "alt": f"{brand()['handle']} 썸네일"})
        links = ""
        for item in args.thumb_link:
            label, _, url = item.partition("=")
            links += f'<a class="btn" target="_blank" rel="noopener" href="{html.escape(url)}">{html.escape(label)}</a> '
        thumb_html = (
            f'<img data-idx="{tidx}" alt="썸네일">'
            f'<div class="side"><button class="btn primary" onclick="downloadOne({tidx})">썸네일 다운로드</button> '
            f"{links}"
            f'<p class="hint">네이버 대표 이미지(정사각형)로 사용하세요. 헤드라인과 {html.escape(brand()["handle"])}가 들어 있습니다.</p></div>'
        )
    else:
        thumb_html = '<p class="hint">썸네일이 아직 없습니다. 썸네일 단계 후 다시 빌드하세요.</p>'

    gallery = "".join(
        f'<div class="gitem"><img data-idx="{i}" alt="{html.escape(im["alt"])}">'
        f'<div class="n">{html.escape(im["file"])}</div>'
        f'<button class="btn" onclick="downloadOne({i})">다운로드</button></div>'
        for i, im in enumerate(images)
    )
    images_json = json.dumps([{"file": i["file"], "uri": i["uri"]} for i in images], ensure_ascii=False)

    page = (TEMPLATE
            .replace("__TITLE__", html.escape(title or "월급노트"))
            .replace("__THUMB__", thumb_html)
            .replace("__ARTICLE__", "\n".join(blocks))
            .replace("__GALLERY__", gallery)
            .replace("__IMAGES_JSON__", images_json))
    out = d / args.out
    out.write_text(page, encoding="utf-8")
    print(f"생성: {out} (이미지 {len(images)}개, {out.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    main()
