#!/usr/bin/env python3
"""views/에 PWA 껍데기(manifest·service worker·아이콘)를 만든다.

홈 화면에 추가했을 때 아이콘이 붙고, 지하철처럼 네트워크가 없는 곳에서도
단어장이 열리게 하는 용도. build_views.py가 build_html.py 다음에 부른다.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOCAB = ROOT / "data" / "vocab.jsonl"
VIEWS = ROOT / "views"
ICONS = VIEWS / "icons"

BG = (236, 238, 236)      # --paper
INDIGO = (36, 64, 110)    # --indigo
SIZES = [180, 192, 512]

MANIFEST = {
    "name": "ENG 단어장",
    "short_name": "단어장",
    "description": "표제어·뜻·예문·해석을 한 표에서 보는 개인 영어 단어장",
    "start_url": "./wordlist.html",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#ECEEEC",
    "theme_color": "#ECEEEC",
    "lang": "ko",
    "icons": [
        {"src": "./icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "./icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "./icons/icon-maskable-512.png", "sizes": "512x512",
         "type": "image/png", "purpose": "maskable"},
    ],
}

# HTML은 network-first — 온라인이면 항상 최신 단어장을 본다.
# 폰트·아이콘은 cache-first — 한 번 받으면 오프라인에서도 그대로 뜬다.
SW = """/* 자동 생성 — scripts/build_pwa.py. 직접 고치지 말 것. */
const V = '%(version)s';
const SHELL = %(shell)s;
const FONTS = /fonts\\.(googleapis|gstatic)\\.com/;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  /* 폰트 — 캐시 우선. 없으면 받아서 넣어둔다(교차 출처라 opaque여도 그대로 쓴다) */
  if (FONTS.test(req.url)) {
    e.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => {
        const copy = res.clone();
        caches.open(V).then(c => c.put(req, copy));
        return res;
      }).catch(() => hit))
    );
    return;
  }

  if (new URL(req.url).origin !== location.origin) return;

  /* 앱 파일 — 네트워크 우선, 실패하면 캐시 */
  e.respondWith(
    fetch(req).then(res => {
      const copy = res.clone();
      caches.open(V).then(c => c.put(req, copy));
      return res;
    }).catch(() => caches.match(req).then(hit => hit || caches.match('./wordlist.html')))
  );
});
"""


def draw_icons():
    """PIL이 있으면 아이콘을 그린다. 없으면 건너뛰고 알린다."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  ! PIL 없음 — 아이콘 생성 건너뜀 (pip install pillow)")
        return False

    fonts = [
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    def render(size, pad_ratio):
        """pad_ratio만큼 안쪽에 그린다. maskable은 잘려나갈 여백이 필요하다."""
        img = Image.new("RGB", (size, size), BG)
        d = ImageDraw.Draw(img)
        inset = round(size * pad_ratio)
        box = (inset, inset, size - inset - 1, size - inset - 1)
        d.rounded_rectangle(box, radius=round((size - 2 * inset) * 0.22), fill=INDIGO)

        side = box[2] - box[0]
        text = "ENG"
        font = None
        for path in fonts:
            try:
                font = ImageFont.truetype(path, round(side * 0.34))
                break
            except OSError:
                continue
        if font is None:
            font = ImageFont.load_default()
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        d.text((cx, cy), text, font=font, fill=BG, anchor="mm")

        # 밑줄 — masthead의 2px 규칙선을 축소해 옮겨 놓은 것
        w = side * 0.30
        y = cy + side * 0.26
        d.rounded_rectangle((cx - w / 2, y, cx + w / 2, y + max(2, side * 0.035)),
                            radius=side * 0.02, fill="#A6432F")
        return img

    ICONS.mkdir(parents=True, exist_ok=True)
    for s in SIZES:
        render(s, 0.06).save(ICONS / f"icon-{s}.png", optimize=True)
    # maskable — 안전 영역(중앙 80%) 안에 들어오도록 여백을 크게 준다
    render(512, 0.18).save(ICONS / "icon-maskable-512.png", optimize=True)
    return True


def main():
    VIEWS.mkdir(exist_ok=True)
    (VIEWS / "manifest.webmanifest").write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    have_icons = draw_icons()

    # 단어 데이터가 바뀌면 버전이 바뀌고, 그래야 낡은 캐시가 버려진다
    digest = hashlib.sha256(VOCAB.read_bytes()).hexdigest()[:10]
    shell = ["./", "./wordlist.html", "./manifest.webmanifest"]
    if have_icons:
        shell += [f"./icons/icon-{s}.png" for s in SIZES] + ["./icons/icon-maskable-512.png"]

    (VIEWS / "sw.js").write_text(
        SW % {"version": f"eng-{digest}", "shell": json.dumps(shell)}, encoding="utf-8")

    print(f"wrote views/manifest.webmanifest, views/sw.js (eng-{digest})"
          + (f", views/icons/*.png ({len(SIZES) + 1}개)" if have_icons else ""))


if __name__ == "__main__":
    main()
