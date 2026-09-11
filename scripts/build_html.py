#!/usr/bin/env python3
"""data/vocab.jsonl -> views/wordlist.html 생성. 표제어·뜻·예문·해석을 한 표에서 본다."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOCAB = ROOT / "data" / "vocab.jsonl"
VIEWS = ROOT / "views"

POS_LABEL = {
    "n": "명사", "v": "동사", "adj": "형용사", "adv": "부사",
    "phr": "구문", "idiom": "관용구", "phrasal_verb": "구동사",
}
POS_ORDER = ["n", "v", "adj", "adv", "phrasal_verb", "idiom", "phr"]

CSS = """
:root{
  --paper:#ECEEEC; --card:#FAFBFA; --ko:#F6F2EA;
  --ink:#131A18; --ink-2:#5C6764; --rule:#DCE1DE; --rule-2:#C4CCC8;
  --indigo:#24406E; --clay:#A6432F;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; padding:34px 24px 110px; background:var(--paper); color:var(--ink);
  font-family:"IBM Plex Sans","IBM Plex Sans KR",-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;
  font-size:15px; line-height:1.5;
}
.wrap{max-width:1180px;margin:0 auto}

/* ── masthead ─────────────────────────────────── */
.masthead{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
  padding-bottom:16px;border-bottom:2px solid var(--ink)}
.mark{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.2em;
  color:var(--indigo);border:1px solid var(--indigo);border-radius:2px;padding:3px 7px}
.masthead h1{margin:0;font-family:"IBM Plex Serif",Georgia,serif;font-size:25px;
  font-weight:600;letter-spacing:-.015em}
.stat{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:11.5px;
  color:var(--ink-2);letter-spacing:.03em}

/* ── toolbar ──────────────────────────────────── */
.toolbar{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:10px;
  flex-wrap:wrap;padding:13px 0;background:var(--paper);border-bottom:1px solid var(--rule)}
.tools{display:flex;align-items:center;gap:10px;flex-wrap:wrap;flex:1 1 auto}
#q{flex:1 1 220px;max-width:320px;font:inherit;font-size:14px;padding:9px 12px;
  border:1px solid var(--rule-2);border-radius:3px;background:var(--card);color:var(--ink)}
#q::placeholder{color:var(--ink-2)}
#q:focus-visible{outline:2px solid var(--indigo);outline-offset:1px;border-color:transparent}
.chips{display:flex;gap:5px;flex-wrap:wrap}
.chip{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.04em;
  padding:6px 11px;border:1px solid var(--rule-2);border-radius:99px;background:var(--card);
  color:var(--ink-2);cursor:pointer;transition:background .15s,color .15s,border-color .15s}
.chip:hover{border-color:var(--ink-2)}
.chip[aria-pressed="true"]{background:var(--indigo);border-color:var(--indigo);color:#fff}
#quiz[aria-pressed="true"]{background:var(--clay);border-color:var(--clay);color:#fff}
.chip:focus-visible{outline:2px solid var(--indigo);outline-offset:2px}
.count{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--ink-2)}
/* ── 하단 이동 바 (모바일 전용) ───────────────── */
.deck{display:none}
.nav{width:46px;height:46px;flex:0 0 auto;border-radius:99px;
  border:1px solid var(--rule-2);background:var(--card);color:var(--indigo);
  font-family:"IBM Plex Sans",sans-serif;font-size:24px;line-height:1;cursor:pointer;
  display:inline-flex;align-items:center;justify-content:center;
  transition:background .12s,color .12s,border-color .12s}
.nav:disabled{opacity:.3;cursor:default}
.nav:not(:disabled):active{background:var(--indigo);border-color:var(--indigo);color:#fff}
.nav:focus-visible{outline:2px solid var(--indigo);outline-offset:2px}
.deck .pos{min-width:96px;text-align:center;font-family:"IBM Plex Mono",monospace;
  font-size:13px;color:var(--ink-2);font-variant-numeric:tabular-nums}

/* ── 정렬 세그먼트 ────────────────────────────── */
.seg{display:inline-flex;border:1px solid var(--rule-2);border-radius:99px;
  background:var(--card);overflow:hidden}
.seg .chip{border:none;border-radius:0;background:transparent}
.seg .chip+.chip{border-left:1px solid var(--rule-2)}
.seg .chip:hover{color:var(--ink)}
.seg .chip[aria-pressed="true"]{background:var(--indigo);color:#fff}
.seg .chip:focus-visible{outline:2px solid var(--indigo);outline-offset:-3px}

/* ── table ────────────────────────────────────── */
table{width:100%;border-collapse:collapse;margin-top:16px;background:var(--card);
  border:1px solid var(--rule-2)}
thead th{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.16em;
  text-transform:uppercase;font-weight:500;color:var(--ink-2);text-align:left;
  padding:11px 14px;border-bottom:1.5px solid var(--ink);background:var(--card)}
col.c1{width:17%} col.c2{width:24%} col.c3{width:33%} col.c4{width:26%}
td,tbody th{padding:12px 14px;vertical-align:top;text-align:left;font-weight:400;
  border-top:1px solid var(--rule)}
tr.first>*{border-top:1.5px solid var(--rule-2)}
tbody:hover .w{box-shadow:inset 3px 0 0 var(--indigo)}

/* 언어 줄무늬 — 한국어 칸은 따뜻한 색으로 구분 */
.ko{background:var(--ko);
  font-family:"IBM Plex Sans KR","Apple SD Gothic Neo","Noto Sans KR",sans-serif;
  font-size:14px;line-height:1.62;word-break:keep-all}
.en{font-size:14.5px;line-height:1.55}

.w{font-family:"IBM Plex Serif",Georgia,serif;font-size:18px;font-weight:600;
  letter-spacing:-.01em;line-height:1.3}
.w .meta{display:block;margin-top:5px;font-family:"IBM Plex Mono",monospace;
  font-size:10.5px;font-weight:400;letter-spacing:.05em;color:var(--ink-2);line-height:1.7}
/* 등록일 — 최근순으로 볼 때만 드러난다 */
.w .date{display:none;margin-top:3px;font-family:"IBM Plex Mono",monospace;
  font-size:10px;font-weight:400;letter-spacing:.06em;color:var(--clay)}
body.by-new .w .date{display:block}
.note{margin-top:7px;padding-left:9px;border-left:2px solid var(--rule-2);
  font-size:12.5px;line-height:1.55;color:var(--ink-2)}

/* ── 구분 (confusables) ───────────────────────── */
.cf-btn{margin-top:8px;font-family:"IBM Plex Mono",monospace;font-size:10.5px;
  letter-spacing:.05em;padding:3px 8px;border:1px solid var(--rule-2);border-radius:2px;
  background:transparent;color:var(--clay);cursor:pointer}
.cf-btn:hover{border-color:var(--clay)}
.cf-btn:focus-visible{outline:2px solid var(--clay);outline-offset:2px}
tr.cf{display:none}
tr.cf.open{display:table-row}
tr.cf td{background:#F3F0EA;border-top:1px dashed var(--rule-2);
  font-family:"IBM Plex Sans KR","Apple SD Gothic Neo",sans-serif;font-size:13px;
  word-break:keep-all}
tr.cf ul{margin:0;padding-left:0;list-style:none}
tr.cf li{padding:3px 0 3px 15px;position:relative;line-height:1.6}
tr.cf li::before{content:"↔";position:absolute;left:0;color:var(--clay);font-size:11px;top:5px}

/* ── 음성 선택 ────────────────────────────────── */
.sel{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.04em;
  padding:6px 26px 6px 11px;max-width:190px;border:1px solid var(--rule-2);border-radius:99px;
  color:var(--ink-2);cursor:pointer;appearance:none;-webkit-appearance:none;
  background-color:var(--card);background-repeat:no-repeat;
  background-position:right 10px center;background-size:9px 5px;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%235C6764' stroke-width='1.4' stroke-linecap='round'/%3E%3C/svg%3E")}
.sel:hover{border-color:var(--ink-2)}
.sel:focus-visible{outline:2px solid var(--indigo);outline-offset:2px}
.sel[hidden]{display:none}

/* ── 읽어주기 버튼 ────────────────────────────── */
.say{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;
  width:22px;height:22px;padding:0;border:1px solid var(--rule-2);border-radius:99px;
  background:var(--card);color:var(--ink-2);cursor:pointer;vertical-align:middle;
  transition:background .15s,color .15s,border-color .15s}
.say svg{width:11px;height:11px;display:block}
.say:hover{color:var(--indigo);border-color:var(--indigo)}
.say:focus-visible{outline:2px solid var(--indigo);outline-offset:2px}
.say.playing{background:var(--indigo);border-color:var(--indigo);color:#fff}
.say-w{margin-left:7px}
.line{display:flex;align-items:flex-start;gap:9px}
.line .tx{flex:1 1 auto;min-width:0}
.line .say{margin-top:1px;opacity:.55;transition:opacity .15s,background .15s,color .15s,border-color .15s}
tbody:hover .line .say,.line .say:focus-visible,.line .say.playing{opacity:1}
body.no-tts .say{display:none}
@media (hover:none){.line .say{opacity:1}}

/* ── 가리기 모드 ──────────────────────────────── */
body.quiz .ko>*{filter:blur(5px);transition:filter .18s ease}
body.quiz .ko{cursor:pointer}
body.quiz .ko.shown>*{filter:none}
tbody.hide{display:none}
.empty{display:none;padding:40px 14px;text-align:center;color:var(--ink-2);
  font-family:"IBM Plex Mono",monospace;font-size:12px}
.empty.on{display:block}

.hint{margin-top:14px;font-family:"IBM Plex Mono",monospace;font-size:10.5px;
  letter-spacing:.04em;color:var(--ink-2)}
.hint kbd{font-family:inherit;border:1px solid var(--rule-2);border-radius:2px;
  padding:1px 5px;background:var(--card)}

@media (max-width:780px){
  /* 노치·홈 인디케이터를 피해 좌우·아래 여백을 잡는다 */
  body{padding:18px calc(14px + env(safe-area-inset-right)) calc(60px + env(safe-area-inset-bottom))
       calc(14px + env(safe-area-inset-left))}
  thead,col{display:none}
  table,tbody,tr,td,tbody th{display:block;width:auto}

  /* 앱 화면처럼 카드 한 장이 화면을 채운다. 이동은 하단 화살표로만 한다 */
  table{display:block;border:none;background:transparent;margin-top:12px;padding:0}
  tbody{display:none}
  tbody.cur{display:block;
    height:calc(100svh - 224px - env(safe-area-inset-bottom));
    overflow-y:auto;overscroll-behavior-y:contain;scrollbar-width:none;
    background:var(--card);border:1px solid var(--rule-2);border-radius:10px;
    box-shadow:0 1px 3px rgba(19,26,24,.07);margin:0}
  tbody.hide{display:none}
  tbody::-webkit-scrollbar{display:none}
  /* 카드가 길어 안에서 스크롤할 때도 표제어는 머리에 붙어 있는다 */
  tbody th.w{position:sticky;top:0;z-index:1;background:var(--card);
    border-bottom:1px solid var(--rule);border-radius:10px 10px 0 0}
  tr.cf.open{display:block}

  td,tbody th{border-top:1px solid var(--rule)}
  tr.first>*{border-top:none}
  td::before{content:attr(data-l);display:block;margin-bottom:4px;
    font-family:"IBM Plex Mono",monospace;font-size:9.5px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--ink-2)}
  .masthead{padding-bottom:10px}
  .masthead h1{font-size:21px}
  .stat{display:none}           /* 개수는 하단 바의 위치 표시가 대신한다 */
  .hint{display:none}           /* 키보드 안내는 폰에서 쓸 일이 없다 */

  /* 툴바 2줄 고정 — 1줄은 검색, 2줄은 옆으로 미는 도구 띠.
     칩이 10개라 그냥 두면 sticky 툴바가 화면 절반을 먹는다. */
  .toolbar{gap:8px;padding:10px 0}
  #q{flex:1 1 100%;max-width:none;min-width:0}
  .tools{flex-wrap:nowrap;overflow-x:auto;overscroll-behavior-x:contain;
    -webkit-overflow-scrolling:touch;scrollbar-width:none;
    margin:0 calc(-1 * (14px + env(safe-area-inset-left)));
    padding:2px calc(14px + env(safe-area-inset-left))}
  .tools::-webkit-scrollbar{display:none}
  .tools>*{flex:0 0 auto}
  .chips{flex-wrap:nowrap}
  .count{display:none}          /* 카드 모드에서는 하단 바의 위치 표시가 개수를 겸한다 */

  /* 하단 이동 바 — 화살표로만 앞뒤 카드로 넘어간다 */
  .deck{display:flex;align-items:center;justify-content:center;gap:20px;
    position:fixed;left:0;right:0;bottom:0;z-index:6;
    padding:9px 14px calc(9px + env(safe-area-inset-bottom));
    background:var(--paper);border-top:1px solid var(--rule-2)}
}

/* 손가락용 — 22px 버튼은 터치 타깃으로 너무 작다 */
@media (pointer:coarse){
  .say{position:relative;width:30px;height:30px}
  .say svg{width:13px;height:13px}
  .say::after{content:"";position:absolute;inset:-7px}   /* 44px 히트 영역 */
  .chip{padding:9px 13px}
  .cf-btn{padding:6px 10px}
  .ko,.en{font-size:15px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = """
const q=document.getElementById('q'),quiz=document.getElementById('quiz'),
      cnt=document.getElementById('count'),empty=document.getElementById('empty'),
      posEl=document.getElementById('pos'),table=document.querySelector('table'),
      groups=[...document.querySelectorAll('tbody[data-word]')];
let pos='all';

function apply(){
  const t=q.value.trim().toLowerCase();
  let n=0;
  for(const g of groups){
    const okPos = pos==='all' || g.dataset.pos===pos;
    const okTxt = !t || g.dataset.find.includes(t);
    const show = okPos && okTxt;
    g.classList.toggle('hide',!show);
    if(show) n++;
  }
  cnt.textContent = n===groups.length ? groups.length+'개' : n+' / '+groups.length+'개';
  empty.classList.toggle('on', n===0);
  if(deckMq.matches) showCard(0);   /* 목록이 바뀌면 첫 카드부터 */
}
q.addEventListener('input',apply);

/* ── 모바일 카드 모드 — 한 장씩 보여주고 화살표로 넘긴다 ── */
const deckMq=matchMedia('(max-width:780px)'),
      prevBtn=document.getElementById('prev'),
      nextBtn=document.getElementById('next');
let idx=0;

/* groups는 로드 시점 순서로 굳어 있다. 카드 차례는 정렬된 DOM 순서를 따라야 하므로
   여기서는 매번 표에서 다시 읽는다. */
const visible=()=>[...table.querySelectorAll('tbody[data-word]:not(.hide)')];

/* i번째 카드만 남긴다. 범위를 벗어난 i는 양 끝으로 붙인다. */
function showCard(i){
  if(!deckMq.matches) return;
  const vis=visible();
  groups.forEach(g=>g.classList.remove('cur'));
  if(!vis.length){
    idx=0; posEl.textContent='0';
    prevBtn.disabled=nextBtn.disabled=true;
    return;
  }
  idx=Math.max(0,Math.min(i,vis.length-1));
  const cur=vis[idx];
  cur.classList.add('cur');
  cur.scrollTop=0;                      /* 새 카드는 늘 맨 위부터 */
  posEl.textContent=(idx+1)+' / '+vis.length;
  prevBtn.disabled = idx===0;
  nextBtn.disabled = idx===vis.length-1;
}

function initDeck(){
  if(deckMq.matches){ showCard(idx); }
  else { groups.forEach(g=>g.classList.remove('cur')); posEl.textContent=''; }
}
prevBtn.addEventListener('click',()=>showCard(idx-1));
nextBtn.addEventListener('click',()=>showCard(idx+1));
deckMq.addEventListener('change',initDeck);
initDeck();

/* ── 정렬 (abc순 / 최근 등록순) ────────────────── */
const sortBtns=[...document.querySelectorAll('.chip[data-sort]')],
      KEY={abc:'oAbc',new:'oNew'};

function sortBy(key,save){
  if(!KEY[key]) key='abc';
  document.body.classList.toggle('by-new',key==='new');
  sortBtns.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.sort===key)));
  const frag=document.createDocumentFragment();
  [...groups].sort((a,b)=>a.dataset[KEY[key]]-b.dataset[KEY[key]])
             .forEach(g=>frag.appendChild(g));
  table.appendChild(frag);
  if(deckMq.matches) showCard(0);
  if(save) localStorage.setItem('eng-sort',key);
}
sortBtns.forEach(b=>b.addEventListener('click',()=>sortBy(b.dataset.sort,true)));
sortBy(localStorage.getItem('eng-sort')||'abc',false);

document.querySelectorAll('.chip[data-pos]').forEach(c=>{
  c.addEventListener('click',()=>{
    pos=c.dataset.pos;
    document.querySelectorAll('.chip[data-pos]').forEach(o=>
      o.setAttribute('aria-pressed', String(o===c)));
    apply();
  });
});

quiz.addEventListener('click',()=>{
  const on=document.body.classList.toggle('quiz');
  quiz.setAttribute('aria-pressed',String(on));
  quiz.textContent = on ? '뜻 보이기' : '뜻 가리기';
  document.querySelectorAll('.ko.shown').forEach(c=>c.classList.remove('shown'));
});

document.querySelectorAll('td.ko,th.ko').forEach(c=>{
  c.addEventListener('click',()=>{
    if(document.body.classList.contains('quiz')) c.classList.toggle('shown');
  });
});

document.querySelectorAll('.cf-btn').forEach(b=>{
  b.addEventListener('click',()=>{
    const row=document.getElementById(b.dataset.for);
    const open=row.classList.toggle('open');
    b.setAttribute('aria-expanded',String(open));
  });
});

/* ── 읽어주기 (Web Speech API) ─────────────────── */
let stopSay = () => {};
const synth = window.speechSynthesis;
if(!synth){
  document.body.classList.add('no-tts');
}else{
  const rateBtn = document.getElementById('rate');
  const voiceSel = document.getElementById('voice');
  const RATES = [1, 0.85, 0.7];
  let ri = parseInt(localStorage.getItem('eng-rate-i'), 10);
  if(!(ri >= 0 && ri < RATES.length)) ri = 0;
  let voice = null, voices = [], cur = null;

  /* 영어 음성 점수제 — Premium/Enhanced를 우선하고, 이름 선호 순서로 가른다.
     브라우저마다 목록이 다르므로 하나만 찍지 않고 전부 줄 세운다. */
  const PREF = ['Ava','Samantha','Allison','Serena','Alex','Daniel','Google US English'];
  const score = v => {
    let s = 0;
    if(/premium/i.test(v.name)) s += 40;
    else if(/enhanced/i.test(v.name)) s += 30;
    const i = PREF.findIndex(n => v.name.indexOf(n) >= 0);
    if(i >= 0) s += 20 - i;
    if(/^en[-_]US/i.test(v.lang)) s += 5;
    if(v.localService) s += 3;   /* 오프라인에서도 되는 로컬 음성 우대 */
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
  /* 크롬은 음성 목록을 비동기로 채운다 */
  synth.addEventListener('voiceschanged', fillVoices);

  const clear = () => { if(cur){ cur.classList.remove('playing'); cur = null; } };
  stopSay = () => { synth.cancel(); clear(); };

  const speak = (text, btn) => {
    if(btn && cur === btn){ stopSay(); return; }   /* 재생 중 다시 누르면 정지 */
    stopSay();
    const u = new SpeechSynthesisUtterance(text);
    if(voice) u.voice = voice;
    u.lang = (voice && voice.lang) || 'en-US';
    u.rate = RATES[ri];
    u.onend = u.onerror = () => { if(cur === btn) clear(); };
    cur = btn;
    if(btn) btn.classList.add('playing');
    synth.speak(u);
  };

  voiceSel.addEventListener('change', () => {
    voice = voices.find(v => v.voiceURI === voiceSel.value) || voice;
    localStorage.setItem('eng-voice', voiceSel.value);
    speak('This is how I sound.', null);   /* 바꾼 음성 미리듣기 */
  });

  document.addEventListener('click', e => {
    const b = e.target.closest('.say');
    if(!b) return;
    const line = b.closest('.line');
    const text = b.dataset.say || (line ? line.querySelector('.tx').textContent : '');
    if(text.trim()) speak(text.trim(), b);
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

/* ── 오프라인 캐시 (https에서만 등록된다) ────────── */
if('serviceWorker' in navigator){
  addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(()=>{}));
}

addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT') { if(e.key==='Escape'){q.value='';apply();q.blur();} return; }
  if(e.key==='/'){e.preventDefault();q.focus();}
  if(e.key==='h'||e.key==='ㅗ'){quiz.click();}
  if(e.key==='s'||e.key==='ㄴ'){
    sortBy(document.body.classList.contains('by-new')?'abc':'new',true);
  }
  if(e.key==='Escape'){stopSay();}
});
apply();
"""


SAY_SVG = (
    '<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M8.4 2.6 4.7 5.7H2.2v4.6h2.5l3.7 3.1z"/>'
    '<path d="M11.1 5.8a3.2 3.2 0 0 1 0 4.4"/>'
    '<path d="M13.2 3.6a6.2 6.2 0 0 1 0 8.8"/></svg>'
)


def esc(s):
    return html.escape(str(s or ""))


def say_btn(cls, label, data=""):
    """읽어주기 버튼. data가 있으면 그 문자열을, 없으면 옆 .tx 내용을 읽는다."""
    attr = f' data-say="{esc(data)}"' if data else ""
    return (f'<button class="say {cls}"{attr} title="{esc(label)}" '
            f'aria-label="{esc(label)}">{SAY_SVG}</button>')


def load():
    return [json.loads(l) for l in VOCAB.read_text(encoding="utf-8").splitlines() if l.strip()]


def with_order(entries):
    """abc순·최근 등록순 두 순서를 미리 계산해 각 항목에 심는다.

    같은 날 등록된 항목은 jsonl에 쓰인 순서가 곧 등록 순서라 뒷줄이 더 최근이다.
    브라우저 로케일에 따라 정렬이 달라지지 않도록 순서는 파이썬에서 확정한다.
    """
    for i, e in enumerate(entries):
        e["_line"] = i
    for i, e in enumerate(sorted(entries, key=lambda e: (e["word"].lower(), e["pos"]))):
        e["_o_abc"] = i
    for i, e in enumerate(sorted(entries, key=lambda e: (e["added_at"], e["_line"]), reverse=True)):
        e["_o_new"] = i
    return sorted(entries, key=lambda e: e["_o_abc"])


def group_html(e):
    sents = e["sentences"]
    span = len(sents)
    haystack = " ".join([
        e["word"], e["meaning_ko"], e.get("meaning_en", ""),
        " ".join(s["en"] for s in sents), " ".join(s["ko"] for s in sents),
        " ".join(e.get("tags", [])),
    ]).lower()

    meta = [POS_LABEL.get(e["pos"], e["pos"])]
    if e.get("level"):
        meta.append(e["level"])
    if e.get("register") and e["register"] != "neutral":
        meta.append(e["register"])
    if e.get("ipa"):
        meta.append(e["ipa"])

    cf = e.get("confusables") or []
    cf_id = f"cf-{e['id']}"
    cf_btn = ""
    if cf:
        cf_btn = (f'<button class="cf-btn" data-for="{esc(cf_id)}" aria-expanded="false">'
                  f'구분 {len(cf)}</button>')

    word_say = say_btn("say-w", f'{e["word"]} 발음 듣기', e["word"])

    out = [f'<tbody data-word="{esc(e["word"])}" data-pos="{esc(e["pos"])}" '
           f'data-o-abc="{e["_o_abc"]}" data-o-new="{e["_o_new"]}" '
           f'data-find="{esc(haystack)}">']

    for i, s in enumerate(sents):
        first = " first" if i == 0 else ""
        out.append(f'<tr class="s{first}">')
        if i == 0:
            out.append(
                f'<th class="w" rowspan="{span}" scope="rowgroup">{esc(e["word"])}'
                f'{word_say}'
                f'<span class="meta">{esc(" · ".join(meta))}</span>'
                f'<span class="date">{esc(e["added_at"])}</span>{cf_btn}</th>'
                f'<td class="ko m" data-l="뜻" rowspan="{span}">'
                f'<div>{esc(e["meaning_ko"])}</div></td>'
            )
        note = (f'<div class="note">💡 {esc(s["note"])}</div>') if s.get("note") else ""
        out.append(f'<td class="en ex" data-l="예문"><div class="line">'
                   f'<span class="tx">{esc(s["en"])}</span>'
                   f'{say_btn("say-ex", "예문 듣기")}</div></td>')
        out.append(f'<td class="ko gl" data-l="해석"><div>{esc(s["ko"])}{note}</div></td>')
        out.append("</tr>")

    if cf:
        items = "".join(f"<li>{esc(c)}</li>" for c in cf)
        out.append(f'<tr class="cf" id="{esc(cf_id)}"><td colspan="4"><ul>{items}</ul></td></tr>')

    out.append("</tbody>")
    return "".join(out)


def main():
    entries = with_order(load())
    n_sent = sum(len(e["sentences"]) for e in entries)
    updated = max(e["added_at"] for e in entries)

    present = [p for p in POS_ORDER if any(e["pos"] == p for e in entries)]
    chips = ['<button class="chip" data-pos="all" aria-pressed="true">전체</button>']
    chips += [f'<button class="chip" data-pos="{p}" aria-pressed="false">'
              f'{POS_LABEL[p]}</button>' for p in present]

    doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>단어장 — ENG</title>
<meta name="theme-color" content="#ECEEEC">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="단어장">
<link rel="manifest" href="./manifest.webmanifest">
<link rel="apple-touch-icon" href="./icons/icon-180.png">
<link rel="icon" href="./icons/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+KR:wght@400;500&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Serif:wght@500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

<header class="masthead">
  <span class="mark">ENG</span>
  <h1>단어장</h1>
  <p class="stat">표제어 {len(entries)} · 예문 {n_sent} · 갱신 {esc(updated)}</p>
</header>

<div class="toolbar">
  <input id="q" type="search" placeholder="단어 · 뜻 · 예문 검색" aria-label="검색">
  <div class="tools">
    <div class="seg" role="group" aria-label="정렬">
      <button class="chip" data-sort="abc" aria-pressed="true">abc순</button>
      <button class="chip" data-sort="new" aria-pressed="false">최근순</button>
    </div>
    <div class="chips">{"".join(chips)}</div>
    <button class="chip" id="quiz" aria-pressed="false">뜻 가리기</button>
    <button class="chip" id="rate" title="읽기 속도 바꾸기">속도 1.0×</button>
    <select class="sel" id="voice" title="읽어줄 음성" aria-label="읽어줄 음성" hidden></select>
    <span class="count" id="count">{len(entries)}개</span>
  </div>
</div>

<table>
  <colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"></colgroup>
  <thead><tr><th scope="col">표제어</th><th scope="col">뜻</th>
  <th scope="col">예문</th><th scope="col">해석</th></tr></thead>
  {"".join(group_html(e) for e in entries)}
</table>
<p class="empty" id="empty">일치하는 단어 없음</p>

<nav class="deck" id="deck" aria-label="카드 이동">
  <button class="nav" id="prev" aria-label="이전 단어">&lsaquo;</button>
  <span class="pos" id="pos" aria-live="polite"></span>
  <button class="nav" id="next" aria-label="다음 단어">&rsaquo;</button>
</nav>

<p class="hint"><kbd>/</kbd> 검색 · <kbd>h</kbd> 뜻 가리기 · <kbd>s</kbd> 정렬 전환 ·
<kbd>Esc</kbd> 읽기 중지 · 가린 상태에서 칸을 누르면 한 칸만 열림 ·
표제어·예문 옆 스피커를 누르면 읽어줌 · 최근순에서는 표제어 아래 등록일이 보임</p>

</div>
<script>{JS}</script>
</body>
</html>
"""
    VIEWS.mkdir(exist_ok=True)
    (VIEWS / "wordlist.html").write_text(doc, encoding="utf-8")
    print(f"wrote views/wordlist.html ({len(entries)} entries, {n_sent} sentences)")


if __name__ == "__main__":
    main()
