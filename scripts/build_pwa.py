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
    """PIL이 있으면 아이콘을 그린다. 없으면 건너뛰고 알린다.

    라임 스타일 글래스모피즘: 초록 그라데이션 바탕 + 라임 단면 + 흐린 유리 카드 위 흰 「ENG」.
    iOS 가 모서리를 알아서 둥글게 자르므로 바탕은 끝까지 채운다.
    """
    try:
        from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
    except ImportError:
        print("  ! PIL 없음 — 아이콘 생성 건너뜀 (pip install pillow)")
        return False
    import math

    FONTS = ["/System/Library/Fonts/SFNSRounded.ttf", "/System/Library/Fonts/Avenir Next.ttc",
             "/System/Library/Fonts/HelveticaNeue.ttc"]

    def render(size, card_ratio=0.62):
        S = size * 4                                   # 크게 그리고 줄여서 가장자리를 매끈하게
        # 1) 바탕 — 왼쪽 위 연둣빛 → 오른쪽 아래 짙은 초록
        tl, br = (150, 214, 70), (8, 92, 58)
        gy = Image.linear_gradient("L").resize((S, S))
        grad = ImageChops.add(gy.point(lambda v: v // 2), gy.rotate(90).transpose(Image.FLIP_LEFT_RIGHT).point(lambda v: v // 2))
        bg = Image.composite(Image.new("RGB", (S, S), br), Image.new("RGB", (S, S), tl), grad)

        # 2) 뒤에 깔리는 라임 단면 + 빛 번짐 (유리가 이걸 흐리게 비춘다)
        art = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(art)
        cx, cy, R = S * 0.66, S * 0.33, S * 0.27
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(46, 140, 52, 255))            # 껍질
        r2 = R * 0.90
        d.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=(240, 250, 205, 255))      # 흰 속껍질
        r3 = R * 0.82
        d.ellipse((cx - r3, cy - r3, cx + r3, cy + r3), fill=(170, 226, 70, 255))       # 과육
        for k in range(10):                                                              # 조각 경계
            a = k * math.pi / 5
            d.line((cx, cy, cx + r3 * math.cos(a), cy + r3 * math.sin(a)),
                   fill=(236, 250, 190, 255), width=round(S * 0.012))
        r4 = R * 0.10
        d.ellipse((cx - r4, cy - r4, cx + r4, cy + r4), fill=(236, 250, 190, 255))
        # 왼쪽 아래 노란 빛
        glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse((S * -0.10, S * 0.55, S * 0.45, S * 1.10), fill=(225, 255, 120, 120))
        glow = glow.filter(ImageFilter.GaussianBlur(S * 0.08))
        base = Image.alpha_composite(bg.convert("RGBA"), glow)
        base = Image.alpha_composite(base, art)

        # 3) 유리 카드
        w = S * card_ratio
        x0, y0 = (S - w) / 2, S * 0.5 - w / 2 + S * 0.06
        box = tuple(round(v) for v in (x0, y0, x0 + w, y0 + w * 0.78))
        rad = round(w * 0.20)
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).rounded_rectangle(box, rad, fill=255)

        shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        sb = (box[0], box[1] + S * 0.03, box[2], box[3] + S * 0.03)
        ImageDraw.Draw(shadow).rounded_rectangle(sb, rad, fill=(10, 60, 30, 110))
        shadow = shadow.filter(ImageFilter.GaussianBlur(S * 0.035))
        out = Image.alpha_composite(base, shadow)

        frosted = base.filter(ImageFilter.GaussianBlur(S * 0.045))
        frosted = Image.alpha_composite(frosted, Image.new("RGBA", (S, S), (255, 255, 255, 46)))
        # 위쪽이 더 밝은 유리 반사
        sheen = Image.linear_gradient("L").resize((S, S)).point(lambda v: round((255 - v) * 0.30))
        frosted = Image.composite(Image.new("RGBA", (S, S), (255, 255, 255, 255)), frosted, sheen)
        out.paste(frosted, (0, 0), mask)

        # 테두리 — 위는 밝고 아래로 갈수록 흐린 흰 선
        edge = Image.new("L", (S, S), 0)
        lw = round(S * 0.008)
        ImageDraw.Draw(edge).rounded_rectangle(box, rad, outline=255, width=lw)
        fade = Image.linear_gradient("L").resize((S, S)).point(lambda v: round(255 - v * 0.75))
        edge = ImageChops.multiply(edge, fade)
        out.paste(Image.new("RGBA", (S, S), (255, 255, 255, 255)), (0, 0), edge.point(lambda v: round(v * 0.9)))

        # 4) 글자
        font = None
        for p in FONTS:
            try:
                font = ImageFont.truetype(p, round(w * 0.30)); break
            except OSError:
                continue
        try:
            font.set_variation_by_name("Bold")
        except Exception:
            pass
        tcx, tcy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        ts = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(ts).text((tcx, tcy + S * 0.006), "ENG", font=font, fill=(10, 70, 35, 140), anchor="mm")
        out = Image.alpha_composite(out, ts.filter(ImageFilter.GaussianBlur(S * 0.006)))
        ImageDraw.Draw(out).text((tcx, tcy), "ENG", font=font, fill=(255, 255, 255, 255), anchor="mm")

        return out.convert("RGB").resize((size, size), Image.LANCZOS)

    ICONS.mkdir(parents=True, exist_ok=True)
    for s in SIZES:
        render(s).save(ICONS / f"icon-{s}.png", optimize=True)
    # maskable — 안전 영역(가운데 원) 안에 들어오도록 카드를 조금 작게
    render(512, card_ratio=0.56).save(ICONS / "icon-maskable-512.png", optimize=True)
    return True


def main():
    VIEWS.mkdir(exist_ok=True)
    (VIEWS / "manifest.webmanifest").write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    have_icons = draw_icons()

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
