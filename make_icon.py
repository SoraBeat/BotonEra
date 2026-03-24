"""Genera assets/icon.ico desde cero con Pillow.
Diseño: speaker con ondas de sonido, gradiente purple→cyan sobre fondo oscuro.
Uso: py -3 make_icon.py
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFilter

PURPLE = (108, 99, 255)
MID    = (74, 144, 226)
CYAN   = (0, 217, 255)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def grad(x, y, w, h):
    t = max(0.0, min(1.0, x / w * 0.5 + y / h * 0.5))
    return lerp(PURPLE, MID, t / 0.55) if t < 0.55 else lerp(MID, CYAN, (t - 0.55) / 0.45)


def sv(v, S):
    return int(v / 64 * S)


def render(SIZE=256):
    SCALE = 4
    S = SIZE * SCALE

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark rounded-square background
    R = int(S * 0.18)
    draw.rounded_rectangle([0, 0, S - 1, S - 1], radius=R, fill=(10, 10, 15, 255))

    # ── Speaker body ──────────────────────────────────────────────────────
    pts = [
        (sv(6,S), sv(23,S)), (sv(6,S), sv(41,S)), (sv(17,S), sv(41,S)),
        (sv(30,S), sv(52,S)), (sv(30,S), sv(12,S)), (sv(17,S), sv(23,S)),
    ]
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    m_px = mask.load()
    i_px = img.load()
    for y in range(S):
        for x in range(S):
            if m_px[x, y]:
                i_px[x, y] = grad(x, y, S, S) + (255,)

    # ── Sound waves (quadratic bezier → polyline) ─────────────────────────
    def wave(x1, y1, cx, cy, x2, y2, width, opacity):
        pts2 = []
        for i in range(40):
            t = i / 39
            bx = (1-t)**2 * sv(x1,S) + 2*(1-t)*t*sv(cx,S) + t**2*sv(x2,S)
            by = (1-t)**2 * sv(y1,S) + 2*(1-t)*t*sv(cy,S) + t**2*sv(y2,S)
            pts2.append((bx, by))
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(layer).line(pts2, fill=(255, 255, 255, 255), width=width)
        layer = layer.filter(ImageFilter.GaussianBlur(radius=SCALE * 0.5))
        l_px = layer.load()
        i_px2 = img.load()
        for y in range(S):
            for x in range(S):
                la = l_px[x, y][3]
                if la > 8:
                    c = grad(x, y, S, S)
                    fa = int(la * opacity)
                    ex = i_px2[x, y]
                    ea, na = ex[3] / 255, fa / 255
                    fa2 = na + ea * (1 - na)
                    if fa2 > 0:
                        r = int((c[0]*na + ex[0]*ea*(1-na)) / fa2)
                        g = int((c[1]*na + ex[1]*ea*(1-na)) / fa2)
                        b = int((c[2]*na + ex[2]*ea*(1-na)) / fa2)
                        i_px2[x, y] = (r, g, b, int(fa2 * 255))

    wave(35, 27, 39.5, 32, 35, 37, int(SCALE*2.8), 1.0)
    wave(40, 21, 48,   32, 40, 43, int(SCALE*2.4), 0.82)
    wave(45.5, 16, 57, 32, 45.5, 48, int(SCALE*2.0), 0.55)

    # ── Glow pass ────────────────────────────────────────────────────────
    glow = img.copy().filter(ImageFilter.GaussianBlur(radius=SCALE * 1.5))
    final = Image.alpha_composite(glow, img)
    return final.resize((SIZE, SIZE), Image.LANCZOS)


if __name__ == "__main__":
    sizes = [256, 128, 64, 48, 32, 16]
    frames = [render(s) for s in sizes]
    out = "assets/icon.ico"
    frames[0].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=frames[1:])
    print(f"Saved {out}  ({len(sizes)} sizes: {', '.join(str(s) for s in sizes)})")
