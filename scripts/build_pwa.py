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
        {"src": "./icons/icon-192.png?v=__V__", "sizes": "192x192", "type": "image/png"},
        {"src": "./icons/icon-512.png?v=__V__", "sizes": "512x512", "type": "image/png"},
        {"src": "./icons/icon-maskable-512.png?v=__V__", "sizes": "512x512",
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
    """PIL이 있으면 아이콘을 그린다. 없으면 건너뛰고 알린다.

    라임 그라디언트: 연두 → 크림빛으로 번지는 타원이 겹겹이 놓이고, 가운데 「ENG」.
    iOS 가 모서리를 알아서 둥글게 자르므로 바탕은 끝까지 채운다.
    """
    try:
        from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
    except ImportError:
        print("  ! PIL 없음 — 아이콘 생성 건너뜀 (pip install pillow)")
        return False

    FONTS = ["/System/Library/Fonts/SFNSRounded.ttf", "/System/Library/Fonts/Avenir Next.ttc",
             "/System/Library/Fonts/HelveticaNeue.ttc"]
    LIME_D = (92, 190, 12)      # 짙은 연두
    LIME = (184, 238, 34)       # 형광 연두
    WHITE = (250, 255, 238)     # 크림빛 흰색

    def grad(S, angle, stops):
        """angle 방향(도)으로 stops[(위치, 색)] 그라디언트."""
        g = Image.linear_gradient("L").resize((S * 2, S * 2)).rotate(angle).crop((S // 2, S // 2, S // 2 + S, S // 2 + S))
        lut = []
        for v in range(256):
            t = v / 255
            for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
                if p0 <= t <= p1:
                    k = (t - p0) / (p1 - p0) if p1 > p0 else 0
                    lut.append(tuple(round(c0[i] + (c1[i] - c0[i]) * k) for i in range(3)))
                    break
            else:
                lut.append(stops[-1][1] if t > stops[-1][0] else stops[0][1])
        out = Image.new("RGB", (S, S))
        out.putdata([lut[v] for v in g.get_flattened_data()])
        return out

    def render(size, scale=1.0, text=True):
        S = 1024
        img = Image.new("RGB", (S, S), (255, 255, 255))
        cx, cy = S / 2, S / 2
        # (가로 반지름, 세로 반지름, 가운데 x 이동, 그라디언트 방향, 색 띠)
        G1, G2, PALE = (96, 192, 8), (150, 222, 20), (222, 250, 150)
        layers = [
            (0.75, 0.80, -0.04, 80,  [(0, G1), (0.50, G2), (0.85, PALE), (1, WHITE)]),
            (0.42, 0.53, 0.035, 260, [(0, G1), (0.40, G2), (0.78, PALE), (1, WHITE)]),
            (0.31, 0.42, 0.07, 80,  [(0, G2), (0.45, LIME), (0.85, PALE), (1, WHITE)]),
            (0.21, 0.30, 0.10, 260, [(0, LIME), (0.55, PALE), (1, WHITE)]),
            (0.12, 0.18, 0.12, 80,  [(0, (200, 244, 90)), (0.6, WHITE), (1, WHITE)]),
        ]
        for rx, ry, dx, ang, stops in layers:
            rx, ry = rx * S * scale, ry * S * scale
            x = cx + dx * S * scale
            box = (x - rx, cy - ry, x + rx, cy + ry)
            fill = grad(S, ang, stops)
            m = Image.new("L", (S, S), 0)
            ImageDraw.Draw(m).ellipse(box, fill=255)
            m = m.filter(ImageFilter.GaussianBlur(S * 0.0015))
            # 아래 겹에 드리우는 부드러운 그림자 — 겹이 떠 보이게
            sh = Image.new("L", (S, S), 0)
            ImageDraw.Draw(sh).ellipse((box[0] - S * .01, box[1] + S * .012, box[2] + S * .01, box[3] + S * .02), fill=0)
            sh = sh.filter(ImageFilter.GaussianBlur(S * 0.02))
            img = Image.composite(Image.new("RGB", (S, S), (70, 140, 10)), img, sh)
            # 가장자리 쪽으로 갈수록 크림빛으로 번지는 부드러운 테 — 렌즈처럼 볼록해 보이게
            inner = m.filter(ImageFilter.GaussianBlur(S * 0.035))
            edge = ImageChops.multiply(ImageChops.invert(inner), m).point(lambda v: min(255, v * 1.6))
            fill = Image.composite(Image.new("RGB", (S, S), (236, 252, 196)), fill, edge)
            # 한쪽(왼쪽 아래)에 짙은 초록 그늘
            shade = Image.new("L", (S, S), 0)
            ImageDraw.Draw(shade).ellipse((box[0] + S * .02, box[1] + S * .06, box[2] - S * .10, box[3] - S * .02), fill=120)
            shade = ImageChops.multiply(shade.filter(ImageFilter.GaussianBlur(S * 0.07)), m)
            fill = Image.composite(Image.new("RGB", (S, S), (88, 178, 6)), fill, shade)
            img = Image.composite(fill, img, m)
            # 가는 흰 테
            rim = Image.new("L", (S, S), 0)
            ImageDraw.Draw(rim).ellipse(box, outline=255, width=round(S * 0.005))
            rim = ImageChops.multiply(rim.filter(ImageFilter.GaussianBlur(S * 0.002)), m)
            img = Image.composite(Image.new("RGB", (S, S), (255, 255, 255)), img, rim.point(lambda v: v * 0.85))
        # 가운데 은은한 흰 빛
        glow = Image.new("L", (S, S), 0)
        r = S * 0.10 * scale
        gx = cx + 0.12 * S * scale
        ImageDraw.Draw(glow).ellipse((gx - r, cy - r, gx + r, cy + r), fill=170)
        img = Image.composite(Image.new("RGB", (S, S), (255, 255, 255)), img, glow.filter(ImageFilter.GaussianBlur(S * 0.05)))

        if text:
            font = None
            for p in FONTS:
                try:
                    font = ImageFont.truetype(p, round(S * 0.11 * scale)); break
                except OSError:
                    continue
            try:
                font.set_variation_by_name("Bold")
            except Exception:
                pass
            d = ImageDraw.Draw(img)
            d.text((gx, cy), "ENG", font=font, fill=(62, 140, 6), anchor="mm")
        return img.resize((size, size), Image.LANCZOS)

    ICONS.mkdir(parents=True, exist_ok=True)
    for s in SIZES:
        render(s).save(ICONS / f"icon-{s}.png", optimize=True)
    # maskable — 안전 영역(가운데 원) 안에 들어오도록 조금 작게
    render(512, scale=0.86).save(ICONS / "icon-maskable-512.png", optimize=True)
    return True


def main():
    VIEWS.mkdir(exist_ok=True)
    have_icons = draw_icons()

    # 아이콘 주소에 버전을 붙인다 — 같은 주소면 iPhone 이 옛 아이콘을 계속 쓴다
    i180 = ICONS / "icon-180.png"
    icon_v = hashlib.sha256(i180.read_bytes()).hexdigest()[:8] if i180.exists() else "1"
    (VIEWS / "manifest.webmanifest").write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=2).replace("__V__", icon_v) + "\n",
        encoding="utf-8")

    # 단어 데이터·아이콘이 바뀌면 버전이 바뀌고, 그래야 낡은 캐시가 버려진다
    h = hashlib.sha256(VOCAB.read_bytes())
    for f in sorted(ICONS.glob("*.png")):   # 아이콘이 바뀌어도 새 캐시로
        h.update(f.read_bytes())
    digest = h.hexdigest()[:10]
    shell = ["./", "./wordlist.html", "./manifest.webmanifest"]
    if have_icons:
        shell += [f"./icons/icon-{s}.png" for s in SIZES] + ["./icons/icon-maskable-512.png"]

    (VIEWS / "sw.js").write_text(
        SW % {"version": f"eng-{digest}", "shell": json.dumps(shell)}, encoding="utf-8")

    print(f"wrote views/manifest.webmanifest, views/sw.js (eng-{digest})"
          + (f", views/icons/*.png ({len(SIZES) + 1}개)" if have_icons else ""))


if __name__ == "__main__":
    main()
