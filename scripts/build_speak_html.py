#!/usr/bin/env python3
"""data/speak/*.json -> views/speak/*.html 생성.

한국어 원문과 영어 번역을 나란히 놓고, 발음 듣기 + 단어 대응 하이라이트를 붙인다.

입력 JSON은 문장 안에 `[[n:텍스트]]` 마커로 대응 관계를 표시한다.
같은 번호 n을 가진 한국어 덩어리와 영어 덩어리가 서로 대응한다.
`[[n*:텍스트]]`처럼 `*`를 붙이면 업계 전용 워딩으로 보고 밑줄까지 긋는다.

    python3 scripts/build_speak_html.py                    # 전체 다시 빌드
    python3 scripts/build_speak_html.py data/speak/x.json  # 하나만 빌드
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "speak"
OUT = ROOT / "views" / "speak"

MARK = re.compile(r"\[\[(\d+)(\*?):([^\]]*)\]\]")

CSS = """
:root{
  --paper:#ECEEEC; --card:#FAFBFA; --ko:#F6F2EA;
  --ink:#131A18; --ink-2:#5C6764; --rule:#DCE1DE; --rule-2:#C4CCC8;
  --indigo:#24406E; --clay:#A6432F; --hl:#FCE8A6; --hl-line:#C9A227;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; padding:34px 24px 110px; background:var(--paper); color:var(--ink);
  font-family:"IBM Plex Sans","IBM Plex Sans KR",-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;
  font-size:15px; line-height:1.5;
}
.wrap{max-width:1180px;margin:0 auto}
a{color:var(--indigo)}

/* ── masthead ─────────────────────────────────── */
.masthead{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
  padding-bottom:16px;border-bottom:2px solid var(--ink)}
.mark{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.2em;
  color:var(--indigo);border:1px solid var(--indigo);border-radius:2px;padding:3px 7px}
.masthead h1{margin:0;font-family:"IBM Plex Serif",Georgia,serif;font-size:25px;
  font-weight:600;letter-spacing:-.015em;word-break:keep-all}
.stat{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:11.5px;
  color:var(--ink-2);letter-spacing:.03em}

/* ── toolbar ──────────────────────────────────── */
.toolbar{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:8px;
  flex-wrap:wrap;padding:13px 0;background:var(--paper);border-bottom:1px solid var(--rule)}
.chip{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.04em;
  padding:6px 11px;border:1px solid var(--rule-2);border-radius:99px;background:var(--card);
  color:var(--ink-2);cursor:pointer;transition:background .15s,color .15s,border-color .15s}
.chip:hover{border-color:var(--ink-2)}
.chip[aria-pressed="true"]{background:var(--indigo);border-color:var(--indigo);color:#fff}
#quiz[aria-pressed="true"]{background:var(--clay);border-color:var(--clay);color:#fff}
.chip:focus-visible{outline:2px solid var(--indigo);outline-offset:2px}
.sel{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.04em;
  padding:6px 26px 6px 11px;max-width:190px;border:1px solid var(--rule-2);border-radius:99px;
  color:var(--ink-2);cursor:pointer;appearance:none;-webkit-appearance:none;
  background-color:var(--card);background-repeat:no-repeat;
  background-position:right 10px center;background-size:9px 5px;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%235C6764' stroke-width='1.4' stroke-linecap='round'/%3E%3C/svg%3E")}
.sel:hover{border-color:var(--ink-2)}
.sel:focus-visible{outline:2px solid var(--indigo);outline-offset:2px}
.sel[hidden]{display:none}
.spacer{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--ink-2)}

/* ── 본문 ─────────────────────────────────────── */
.doc{margin-top:18px;background:var(--card);border:1px solid var(--rule-2)}
h2.sec{margin:0;padding:16px 16px 12px;border-top:1.5px solid var(--rule-2);
  font-family:"IBM Plex Serif",Georgia,serif;font-size:18px;font-weight:600;
  letter-spacing:-.01em;word-break:keep-all}
h2.sec:first-child{border-top:none}
h2.sec .sub{display:block;margin-top:3px;font-family:"IBM Plex Sans KR",sans-serif;
  font-size:12.5px;font-weight:400;color:var(--ink-2)}

.pair{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--rule)}
.pair:first-child{border-top:none}
.pair.bullet .tx{padding-left:15px;position:relative}
.pair.bullet .tx::before{content:"·";position:absolute;left:3px;color:var(--ink-2)}
.pair.active{box-shadow:inset 3px 0 0 var(--indigo)}

.side{padding:13px 16px;min-width:0}
.side.k{background:var(--ko);
  font-family:"IBM Plex Sans KR","Apple SD Gothic Neo","Noto Sans KR",sans-serif;
  font-size:14px;line-height:1.7;word-break:keep-all}
.side.e{font-size:15.5px;line-height:1.65;display:flex;align-items:flex-start;gap:9px}
.side.e .tx{flex:1 1 auto;min-width:0}
.lbl{display:none}

/* 대응 하이라이트 — 마우스를 올린 덩어리와 짝을 같이 밝힌다 */
.al{border-radius:2px;padding:0 1px;margin:0 -1px;cursor:pointer;
  transition:background .12s,box-shadow .12s}
.al.term{text-decoration:underline;text-decoration-color:var(--clay);
  text-decoration-thickness:1.5px;text-underline-offset:3px}
.al.hl{background:var(--hl);box-shadow:0 1px 0 var(--hl-line)}
.al.lock{background:var(--hl);box-shadow:0 0 0 1px var(--hl-line)}

/* ── 읽어주기 버튼 ────────────────────────────── */
.say{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;
  width:22px;height:22px;padding:0;border:1px solid var(--rule-2);border-radius:99px;
  background:var(--card);color:var(--ink-2);cursor:pointer;margin-top:3px;opacity:.55;
  transition:opacity .15s,background .15s,color .15s,border-color .15s}
.say svg{width:11px;height:11px;display:block}
.say:hover{color:var(--indigo);border-color:var(--indigo);opacity:1}
.say:focus-visible{outline:2px solid var(--indigo);outline-offset:2px;opacity:1}
.say.playing{background:var(--indigo);border-color:var(--indigo);color:#fff;opacity:1}
.pair:hover .say{opacity:1}
body.no-tts .say,body.no-tts #rate,body.no-tts #play{display:none}
@media (hover:none){.say{opacity:1}}

/* ── 영어 가리기 (섀도잉) ─────────────────────── */
body.quiz .side.e .tx{filter:blur(5px);transition:filter .18s ease;cursor:pointer}
body.quiz .side.e.shown .tx{filter:none}

/* ── 워딩 / 대안 표현 ─────────────────────────── */
.panel{margin-top:22px;background:var(--card);border:1px solid var(--rule-2)}
.panel h2{margin:0;padding:13px 16px;border-bottom:1.5px solid var(--ink);
  font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.16em;
  text-transform:uppercase;font-weight:500;color:var(--ink-2)}
.panel ul{margin:0;padding:0;list-style:none}
.panel li{padding:11px 16px;border-top:1px solid var(--rule)}
.panel li:first-child{border-top:none}
.t{font-weight:500;text-decoration:underline;text-decoration-color:var(--clay);
  text-decoration-thickness:1.5px;text-underline-offset:3px}
.t-ko{font-family:"IBM Plex Sans KR","Apple SD Gothic Neo",sans-serif;font-size:13.5px;
  color:var(--ink);word-break:keep-all}
.t-note{display:block;margin-top:3px;font-size:12.5px;color:var(--ink-2);word-break:keep-all}
.alt-a{color:var(--ink-2);text-decoration:line-through;text-decoration-thickness:1px}
.alt-b{display:block;margin-top:4px;font-size:15px}
.alt-b::before{content:"→ ";color:var(--clay)}

.hint{margin-top:14px;font-family:"IBM Plex Mono",monospace;font-size:10.5px;
  letter-spacing:.04em;color:var(--ink-2);line-height:1.9}
.hint kbd{font-family:inherit;border:1px solid var(--rule-2);border-radius:2px;
  padding:1px 5px;background:var(--card)}

/* ── 목록 페이지 ──────────────────────────────── */
.list{margin-top:18px;background:var(--card);border:1px solid var(--rule-2)}
.list a.row{display:flex;align-items:baseline;gap:12px;padding:13px 16px;
  border-top:1px solid var(--rule);text-decoration:none;color:inherit}
.list a.row:first-child{border-top:none}
.list a.row:hover{background:var(--ko)}
.list .ttl{font-family:"IBM Plex Serif",Georgia,serif;font-size:16px;font-weight:600;
  word-break:keep-all}
.list .meta{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:11px;
  color:var(--ink-2);white-space:nowrap}

@media (max-width:760px){
  body{padding:22px 14px 80px}
  .pair{grid-template-columns:1fr}
  .side.k{border-bottom:1px solid var(--rule)}
  .lbl{display:block;margin-bottom:4px;font-family:"IBM Plex Mono",monospace;
    font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2)}
  .stat{margin-left:0;width:100%}
  .spacer{margin-left:0}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = """
/* ── 대응 하이라이트 ──────────────────────────── */
const clearHl = () => document.querySelectorAll('.al.hl,.al.lock')
  .forEach(s => s.classList.remove('hl','lock'));
const paint = (span, cls) => {
  const pair = span.closest('.pair');
  if(!pair) return;
  pair.querySelectorAll('.al[data-g="'+span.dataset.g+'"]')
    .forEach(s => s.classList.add(cls));
};
let locked = null;   /* 클릭으로 고정한 덩어리. 고정 중엔 호버를 무시한다 */

document.addEventListener('mouseover', e => {
  if(locked) return;
  const s = e.target.closest('.al');
  clearHl();
  if(s) paint(s, 'hl');
});
document.addEventListener('mouseleave', () => { if(!locked) clearHl(); });

document.addEventListener('click', e => {
  const s = e.target.closest('.al');
  if(!s){ if(locked){ locked = null; clearHl(); } return; }
  const key = s.closest('.pair').id + '/' + s.dataset.g;
  clearHl();
  if(locked === key){ locked = null; return; }
  locked = key;
  paint(s, 'lock');
});

/* ── 영어 가리기 ──────────────────────────────── */
const quiz = document.getElementById('quiz');
quiz.addEventListener('click', () => {
  const on = document.body.classList.toggle('quiz');
  quiz.setAttribute('aria-pressed', String(on));
  quiz.textContent = on ? '영어 보이기' : '영어 가리기';
  document.querySelectorAll('.side.e.shown').forEach(c => c.classList.remove('shown'));
});
document.querySelectorAll('.side.e').forEach(c => {
  c.addEventListener('click', e => {
    if(e.target.closest('.say')) return;
    if(document.body.classList.contains('quiz')) c.classList.toggle('shown');
  });
});

/* ── 읽어주기 (Web Speech API) ─────────────────── */
let stopSay = () => {};
const synth = window.speechSynthesis;
if(!synth){
  document.body.classList.add('no-tts');
}else{
  const rateBtn = document.getElementById('rate');
  const playBtn = document.getElementById('play');
  const voiceSel = document.getElementById('voice');
  const RATES = [1, 0.85, 0.7];
  let ri = parseInt(localStorage.getItem('eng-rate-i'), 10);
  if(!(ri >= 0 && ri < RATES.length)) ri = 0;
  let voice = null, voices = [], cur = null, queue = null;

  /* 영어 음성 점수제 — 단어장(wordlist.html)과 같은 기준을 쓴다 */
  const PREF = ['Ava','Samantha','Allison','Serena','Alex','Daniel','Google US English'];
  const score = v => {
    let s = 0;
    if(/premium/i.test(v.name)) s += 40;
    else if(/enhanced/i.test(v.name)) s += 30;
    const i = PREF.findIndex(n => v.name.indexOf(n) >= 0);
    if(i >= 0) s += 20 - i;
    if(/^en[-_]US/i.test(v.lang)) s += 5;
    if(v.localService) s += 3;
    return s;
  };

  const fillVoices = () => {
    const vs = synth.getVoices().filter(v => /^en[-_]?/i.test(v.lang))
      .sort((a, b) => score(b) - score(a) || a.name.localeCompare(b.name));
    if(!vs.length){ voiceSel.hidden = true; return; }
    voiceSel.hidden = false;
    voiceSel.textContent = '';
    for(const v of vs){
      const o = document.createElement('option');
      o.value = v.voiceURI;
      o.textContent = v.name + (/^en[-_]GB/i.test(v.lang) ? ' · UK' : '');
      voiceSel.appendChild(o);
    }
    const saved = localStorage.getItem('eng-voice');
    voice = vs.find(v => v.voiceURI === saved) || vs[0];
    voiceSel.value = voice.voiceURI;
    voices = vs;
  };
  fillVoices();
  synth.addEventListener('voiceschanged', fillVoices);   /* 크롬은 비동기로 채운다 */

  const clear = () => {
    if(cur){ cur.classList.remove('playing'); cur = null; }
    document.querySelectorAll('.pair.active').forEach(p => p.classList.remove('active'));
  };
  const endPlayAll = () => {
    queue = null;
    playBtn.setAttribute('aria-pressed', 'false');
    playBtn.textContent = '전체 재생';
  };
  stopSay = () => { endPlayAll(); synth.cancel(); clear(); };

  const speak = (text, btn, done) => {
    const u = new SpeechSynthesisUtterance(text);
    if(voice) u.voice = voice;
    u.lang = (voice && voice.lang) || 'en-US';
    u.rate = RATES[ri];
    u.onend = u.onerror = () => { if(cur === btn) clear(); if(done) done(); };
    cur = btn;
    if(btn){
      btn.classList.add('playing');
      const p = btn.closest('.pair');
      if(p) p.classList.add('active');
    }
    synth.speak(u);
  };

  const sayBtns = () => [...document.querySelectorAll('.pair .say')];
  const step = i => {
    const btns = sayBtns();
    if(queue === null || i >= btns.length){ endPlayAll(); clear(); return; }
    queue = i;
    const b = btns[i];
    b.scrollIntoView({block:'center', behavior:'smooth'});
    speak(b.dataset.say, b, () => { if(queue !== null) step(i + 1); });
  };

  playBtn.addEventListener('click', () => {
    if(queue !== null){ stopSay(); return; }
    synth.cancel(); clear();
    queue = 0;
    playBtn.setAttribute('aria-pressed', 'true');
    playBtn.textContent = '정지';
    step(0);
  });

  voiceSel.addEventListener('change', () => {
    voice = voices.find(v => v.voiceURI === voiceSel.value) || voice;
    localStorage.setItem('eng-voice', voiceSel.value);
    stopSay();
    speak('This is how I sound.', null);   /* 바꾼 음성 미리듣기 */
  });

  document.addEventListener('click', e => {
    const b = e.target.closest('.say');
    if(!b) return;
    if(cur === b){ stopSay(); return; }     /* 재생 중 다시 누르면 정지 */
    stopSay();
    const text = (b.dataset.say || '').trim();
    if(text) speak(text, b);
  });

  const showRate = () => {
    rateBtn.textContent = '속도 ' + RATES[ri].toFixed(2).replace(/0$/, '') + '×';
  };
  rateBtn.addEventListener('click', () => {
    ri = (ri + 1) % RATES.length;
    localStorage.setItem('eng-rate-i', ri);
    showRate();
    stopSay();
  });
  showRate();

  addEventListener('pagehide', stopSay);
}

addEventListener('keydown', e => {
  if(e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if(e.key === 'h' || e.key === 'ㅗ') quiz.click();
  if(e.key === 'p' || e.key === 'ㅔ'){
    const b = document.getElementById('play');
    if(b) b.click();
  }
  if(e.key === 'Escape'){ stopSay(); locked = null; clearHl(); }
});
"""

SAY_SVG = (
    '<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M8.4 2.6 4.7 5.7H2.2v4.6h2.5l3.7 3.1z"/>'
    '<path d="M11.1 5.8a3.2 3.2 0 0 1 0 4.4"/>'
    '<path d="M13.2 3.6a6.2 6.2 0 0 1 0 8.8"/></svg>'
)

HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+KR:wght@400;500&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Serif:wght@500;600&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<div class="wrap">
"""


def esc(s):
    return html.escape(str(s or ""))


def plain(text):
    """마커를 걷어낸 순수 문장. 읽어주기와 검증에 쓴다."""
    return MARK.sub(lambda m: m.group(3), str(text or "")).strip()


def marked(text):
    """`[[n:...]]` / `[[n*:...]]`를 하이라이트 span으로 바꾼다. (html, 등장한 그룹번호)"""
    out, groups, pos = [], set(), 0
    text = str(text or "")
    for m in MARK.finditer(text):
        out.append(esc(text[pos:m.start()]))
        gid, star, body = m.group(1), m.group(2), m.group(3)
        cls = "al term" if star else "al"
        out.append(f'<span class="{cls}" data-g="{esc(gid)}">{esc(body)}</span>')
        groups.add(gid)
        pos = m.end()
    out.append(esc(text[pos:]))
    return "".join(out), groups


def block_html(b, idx, warn):
    kind = b.get("type", "pair")
    ko_raw, en_raw = b.get("ko", ""), b.get("en", "")

    if kind == "heading":
        sub = f'<span class="sub">{esc(plain(ko_raw))}</span>' if ko_raw else ""
        return f'<h2 class="sec">{esc(plain(en_raw))}{sub}</h2>'

    ko_html, ko_g = marked(ko_raw)
    en_html, en_g = marked(en_raw)

    # 짝이 안 맞는 마커는 하이라이트가 한쪽만 켜지므로 빌드할 때 알려준다
    for gid in sorted(ko_g - en_g, key=int):
        warn.append(f"  블록 {idx}: 그룹 {gid} — 한국어에만 있음")
    for gid in sorted(en_g - ko_g, key=int):
        warn.append(f"  블록 {idx}: 그룹 {gid} — 영어에만 있음")

    en_text = plain(en_raw)
    if not en_text:
        warn.append(f"  블록 {idx}: 영어 문장이 비어 있음")

    bullet = " bullet" if kind == "bullet" else ""
    say = (f'<button class="say" data-say="{esc(en_text)}" title="영어 문장 듣기" '
           f'aria-label="영어 문장 듣기">{SAY_SVG}</button>')
    return (
        f'<section class="pair{bullet}" id="p{idx}">'
        f'<div class="side k"><span class="lbl">한국어</span>'
        f'<div class="tx">{ko_html}</div></div>'
        f'<div class="side e"><div class="tx" lang="en">'
        f'<span class="lbl">English</span>{en_html}</div>{say}</div>'
        f'</section>'
    )


def terms_panel(terms):
    if not terms:
        return ""
    items = []
    for t in terms:
        note = f'<span class="t-note">{esc(t["note"])}</span>' if t.get("note") else ""
        items.append(
            f'<li><span class="t" lang="en">{esc(t.get("term"))}</span> '
            f'<span class="t-ko">— {esc(t.get("ko"))}</span>{note}</li>'
        )
    return ('<section class="panel"><h2>업계 전용 워딩</h2><ul>'
            + "".join(items) + "</ul></section>")


def alts_panel(alts):
    if not alts:
        return ""
    items = []
    for a in alts:
        note = f'<span class="t-note">{esc(a["note"])}</span>' if a.get("note") else ""
        items.append(
            f'<li><span class="alt-a" lang="en">{esc(a.get("en"))}</span>'
            f'<span class="alt-b" lang="en">{esc(a.get("alt"))}</span>{note}</li>'
        )
    return ('<section class="panel"><h2>이렇게도 말할 수 있어요</h2><ul>'
            + "".join(items) + "</ul></section>")


def build(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    blocks = doc.get("blocks") or []
    if not blocks:
        raise SystemExit(f"{path.name}: blocks가 비어 있다")

    warn = []
    body = "".join(block_html(b, i + 1, warn) for i, b in enumerate(blocks))
    n_pair = sum(1 for b in blocks if b.get("type", "pair") != "heading")

    meta = [f"문장 {n_pair}"]
    if doc.get("created_at"):
        meta.append(doc["created_at"])
    if doc.get("source"):
        meta.append(doc["source"])

    title = doc.get("title") or path.stem
    html_doc = HEAD.format(title=esc(title) + " — ENG speak", css=CSS) + f"""
<header class="masthead">
  <span class="mark">SPEAK</span>
  <h1>{esc(title)}</h1>
  <p class="stat">{esc(" · ".join(meta))}</p>
</header>

<div class="toolbar">
  <button class="chip" id="play" aria-pressed="false" title="영어 문장을 순서대로 재생">전체 재생</button>
  <button class="chip" id="quiz" aria-pressed="false">영어 가리기</button>
  <button class="chip" id="rate" title="읽기 속도 바꾸기">속도 1.0×</button>
  <select class="sel" id="voice" title="읽어줄 음성" aria-label="읽어줄 음성" hidden></select>
  <span class="spacer"><a href="index.html">← 목록</a></span>
</div>

<div class="doc">{body}</div>
{terms_panel(doc.get("terms"))}
{alts_panel(doc.get("alts"))}

<p class="hint">
단어에 마우스를 올리면 반대쪽 언어의 짝이 같이 밝아짐 · 누르면 고정, 다시 누르면 해제<br>
<kbd>p</kbd> 전체 재생 · <kbd>h</kbd> 영어 가리기 (가린 칸을 누르면 그 칸만 열림) ·
<kbd>Esc</kbd> 읽기 중지 · <span class="t">밑줄</span>은 업계에서만 쓰는 워딩
</p>

</div>
<script>{JS}</script>
</body>
</html>
"""
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / (path.stem + ".html")
    dst.write_text(html_doc, encoding="utf-8")
    print(f"wrote views/speak/{dst.name} ({n_pair} pairs)")
    for w in warn:
        print("  ⚠ " + w.strip())
    return {"file": dst.name, "title": title, "n": n_pair,
            "date": doc.get("created_at", ""), "source": doc.get("source", "")}


def build_index(rows):
    rows.sort(key=lambda r: (r["date"], r["file"]), reverse=True)
    items = "".join(
        f'<a class="row" href="{esc(r["file"])}">'
        f'<span class="ttl">{esc(r["title"])}</span>'
        f'<span class="meta">{esc(r["date"])} · 문장 {r["n"]}</span></a>'
        for r in rows
    )
    doc = HEAD.format(title="speak — ENG", css=CSS) + f"""
<header class="masthead">
  <span class="mark">SPEAK</span>
  <h1>번역 기록</h1>
  <p class="stat">{len(rows)}건</p>
</header>
<div class="list">{items or '<div class="row">아직 없음</div>'}</div>
</div>
</body>
</html>
"""
    (OUT / "index.html").write_text(doc, encoding="utf-8")
    print(f"wrote views/speak/index.html ({len(rows)} docs)")


def meta_of(path):
    """목록에 쓸 요약. 빌드 없이 JSON만 읽는다."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    blocks = doc.get("blocks") or []
    return {
        "file": path.stem + ".html",
        "title": doc.get("title") or path.stem,
        "n": sum(1 for b in blocks if b.get("type", "pair") != "heading"),
        "date": doc.get("created_at", ""),
        "source": doc.get("source", ""),
    }


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    args = [Path(a) for a in sys.argv[1:]]
    targets = args or sorted(SRC.glob("*.json"))
    if not targets:
        raise SystemExit("data/speak/ 에 JSON이 없다")

    for p in targets:
        if not p.exists():
            raise SystemExit(f"{p}: 파일 없음")
        build(p)

    # 하나만 빌드했더라도 목록은 항상 전체 기준으로 다시 만든다
    build_index([meta_of(p) for p in sorted(SRC.glob("*.json"))])


if __name__ == "__main__":
    main()
