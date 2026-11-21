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

    라벤더 바탕 위 반달 라임 조각. 껍질 · 속껍질 · 과육 4조각에 연두 그라디언트.
    iOS 가 모서리를 알아서 둥글게 자르므로 바탕은 끝까지 채운다.
    """
    try:
        from PIL import Image, ImageChops, ImageDraw, ImageFilter
    except ImportError:
        print("  ! PIL 없음 — 아이콘 생성 건너뜀 (pip install pillow)")
        return False
    import math

    BG = (198, 204, 247)


    def vgrad(S, y0, y1, stops):
        """세로 그라디언트(y0→y1)."""
        col = []
        for y in range(S):
            t = min(1, max(0, (y - y0) / (y1 - y0)))
            for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
                if p0 <= t <= p1:
                    k = (t - p0) / (p1 - p0) if p1 > p0 else 0
                    col.append(tuple(round(c0[i] + (c1[i] - c0[i]) * k) for i in range(3)))
                    break
        strip = Image.new("RGB", (1, S)); strip.putdata(col)
        return strip.resize((S, S))


    def hgrad(S, x0, x1, c0, c1):
        g = Image.linear_gradient("L").rotate(90).transpose(Image.FLIP_LEFT_RIGHT).resize((S, S))
        g = g.point(lambda v: round(min(255, max(0, (v / 255 * S - x0) / (x1 - x0) * 255))))
        return Image.composite(Image.new("RGB", (S, S), c1), Image.new("RGB", (S, S), c0), g)


    def round_mask(m, r):
        return m.filter(ImageFilter.GaussianBlur(r)).point(lambda v: 255 if v > 128 else 0).filter(ImageFilter.GaussianBlur(1.2))


    def render(size, scale=1.0, angle=-38, bg=None):
        S = 1024
        bgc = bg or BG
        layer = Image.new("RGBA", (S, S), bgc + (0,))   # 투명 칸도 바탕색 — 가장자리에 검은 테가 안 생기게
        cx, cy, R = S / 2, S * 0.36, S * 0.44 * scale
        pie = lambda r: (cx - r, cy - r, cx + r, cy + r)

        # 1) 껍질 — 왼쪽 파랑 → 아래 초록
        rind = Image.new("L", (S, S), 0)
        ImageDraw.Draw(rind).pieslice(pie(R), 0, 180, fill=255)
        rind = round_mask(rind, S * 0.012)
        rind_col = hgrad(S, cx - R, cx + R * 0.3, (84, 178, 6), (196, 242, 60))
        layer.paste(rind_col, (0, 0), rind)

        # 2) 흰 속껍질 — 크림빛, 잘린 면 쪽은 살짝 복숭아빛
        # 속껍질 = 껍질 모양에서 바깥 테만 뺀 것 → 자른 면에서 껍질 색이 비치지 않는다
        ring = Image.new("L", (S, S), 0)
        ImageDraw.Draw(ring).ellipse(pie(R * 0.92), fill=255)
        pith = ImageChops.multiply(rind, ring.filter(ImageFilter.GaussianBlur(1.2)))
        pith_col = vgrad(S, cy, cy + R, [(0, (252, 255, 236)), (0.5, (240, 252, 206)), (1, (226, 248, 176))])
        layer.paste(pith_col, (0, 0), pith)

        # 3) 과육 4조각
        flesh_col = vgrad(S, cy, cy + R * 0.86, [(0, (246, 255, 226)), (0.30, (206, 246, 110)),
                                                (0.62, (150, 222, 24)), (1, (96, 192, 8))])
        rf, gap = R * 0.85, S * 0.016
        for k in range(4):
            a0, a1 = k * 45, (k + 1) * 45
            seg = Image.new("L", (S, S), 0)
            ImageDraw.Draw(seg).pieslice(pie(rf), a0, a1, fill=255)
            cut = ImageDraw.Draw(seg)
            for a in (a0, a1):                                       # 조각 사이 틈
                r = math.radians(a)
                cut.line((cx, cy, cx + rf * 1.1 * math.cos(r), cy + rf * 1.1 * math.sin(r)), fill=0, width=round(gap * 2))
            cut.ellipse(pie(R * 0.07), fill=0)                       # 가운데 심
            seg = round_mask(seg, S * 0.014)
            # 조각마다 바깥 아래쪽에 짙은 청록 그늘, 안쪽 위에 노란 빛
            mid = math.radians((a0 + a1) / 2)
            sx, sy = cx + rf * 0.78 * math.cos(mid + 0.25), cy + rf * 0.78 * math.sin(mid + 0.25)
            shade = Image.new("L", (S, S), 0)
            ImageDraw.Draw(shade).ellipse((sx - rf * .28, sy - rf * .22, sx + rf * .28, sy + rf * .22), fill=200)
            shade = shade.filter(ImageFilter.GaussianBlur(S * 0.05))
            hx, hy = cx + rf * 0.35 * math.cos(mid - 0.2), cy + rf * 0.35 * math.sin(mid - 0.2)
            hi = Image.new("L", (S, S), 0)
            ImageDraw.Draw(hi).ellipse((hx - rf * .2, hy - rf * .14, hx + rf * .2, hy + rf * .14), fill=190)
            hi = hi.filter(ImageFilter.GaussianBlur(S * 0.05))
            col = Image.composite(Image.new("RGB", (S, S), (88, 178, 6)), flesh_col, shade)
            col = Image.composite(Image.new("RGB", (S, S), (250, 255, 238)), col, hi)
            layer.paste(col, (0, 0), seg)

        # 4) 껍질 왼쪽 위 끝에 흰 반짝임
        sp = Image.new("L", (S, S), 0)
        ImageDraw.Draw(sp).pieslice(pie(R * 1.0), 160, 180, fill=255)
        ImageDraw.Draw(sp).pieslice(pie(R * 0.92), 150, 185, fill=0)
        sp = ImageChops.multiply(sp.filter(ImageFilter.GaussianBlur(S * 0.01)), layer.split()[3])
        white = Image.new("RGBA", (S, S), (255, 255, 255, 255)); white.putalpha(sp.point(lambda v: v * 0.8))
        layer = Image.alpha_composite(layer, white)

        # 회전해서 가운데로
        # 바탕에 먼저 얹은 뒤 돌린다 — 투명한 채로 돌리면 가장자리에 어두운 테가 생긴다
        ctr = (cx, cy + R * 0.42)
        bbox = layer.split()[3].rotate(angle, resample=Image.BICUBIC, center=ctr).getbbox()
        dx = round(S / 2 - (bbox[0] + bbox[2]) / 2); dy = round(S / 2 - (bbox[1] + bbox[3]) / 2)
        flat = Image.new("RGBA", (S, S), bgc + (255,)); flat.alpha_composite(layer)
        out = flat.convert("RGB").rotate(angle, resample=Image.BICUBIC, center=ctr,
                                         translate=(dx, dy), fillcolor=bgc)
        return out.resize((size, size), Image.LANCZOS)

    ICONS.mkdir(parents=True, exist_ok=True)
    for s in SIZES:
        render(s).save(ICONS / f"icon-{s}.png", optimize=True)
    # maskable — 안전 영역(가운데 원) 안에 들어오도록 조금 작게
    render(512, scale=0.80).save(ICONS / "icon-maskable-512.png", optimize=True)
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
