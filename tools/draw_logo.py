"""Rise & Shine logo: fire rising from an open Bible. White on transparent, drawn large and scaled down.

    python tools/draw_logo.py assets/logo-white.png preview.png
"""
import sys

from PIL import Image, ImageDraw

N = 4                      # supersampling
SIZE = 600 * N
WHITE, CLEAR = (255, 255, 255, 255), (0, 0, 0, 0)


def bez(p0, p1, p2, p3, steps=40):
    """Points along a cubic Bézier curve."""
    points = []
    for i in range(steps + 1):
        t = i / steps
        a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        points.append((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))
    return points


def s(points):  # scale 600-unit design coordinates to the canvas
    return [(x*N, y*N) for x, y in points]


def flame(cx, base, w, h, curl=0.0):
    """A tongue of fire: a rounded foot, one side swelling and one hollowing, and a tip that curls."""
    tip = (cx + curl * w * 0.7, base - h)
    left = bez((cx - w, base), (cx - w * 1.15, base - h * 0.38), (cx - w * 0.15 + curl * w * 0.35, base - h * 0.62), tip)
    right = bez(tip, (cx + w * 0.3 + curl * w * 0.45, base - h * 0.58), (cx + w * 1.12, base - h * 0.3), (cx + w, base))
    foot = bez((cx + w, base), (cx + w * 0.6, base + h * 0.1), (cx - w * 0.6, base + h * 0.1), (cx - w, base))
    return left + right + foot


def draw(path, preview):
    img = Image.new("RGBA", (SIZE, SIZE), CLEAR)
    d = ImageDraw.Draw(img)
    cx = 300
    # ---- fire: one blaze of curling tongues rising out of the open pages
    base = 340
    tongues = [(cx, 78, 270, 0.12), (cx - 62, 50, 185, -0.55), (cx + 64, 50, 200, 0.5),
               (cx - 116, 26, 100, -0.75), (cx + 118, 26, 108, 0.7)]
    for x, w, h, curl in tongues:
        d.polygon(s(flame(x, base, w, h, curl)), fill=WHITE)
    for x, w, h, curl in [(cx + 4, 30, 140, 0.2), (cx - 58, 17, 82, -0.5), (cx + 62, 17, 90, 0.5)]:
        d.polygon(s(flame(x, base - 24, w, h, curl)), fill=CLEAR)
    # ---- open Bible: two pages curving up from the spine, a cover edge underneath
    spine_top, spine_bot = 330, 492
    left_page = (bez((cx, spine_top), (250, 300), (160, 300), (78, 322)) +
                 [(78, 322), (78, 462)] +
                 bez((78, 462), (160, 446), (250, 448), (cx, spine_bot)))
    right_page = [(2*cx - x, y) for x, y in left_page]
    cover_l = (bez((cx, spine_bot + 26), (240, 476), (150, 474), (60, 492)) + [(60, 492), (60, 470)] +
               bez((60, 470), (150, 452), (240, 456), (cx, spine_bot + 8)))
    cover_r = [(2*cx - x, y) for x, y in cover_l]
    for poly in (cover_l, cover_r, left_page, right_page):  # a clear outline separates the book from the fire
        d.polygon(s(poly), fill=CLEAR, outline=CLEAR, width=11 * N)
    for poly in (cover_l, cover_r, left_page, right_page):
        d.polygon(s(poly), fill=WHITE)
    # ribbon bookmark hanging from the spine
    d.polygon(s([(cx + 8, 494), (cx + 30, 494), (cx + 30, 572), (cx + 19, 559), (cx + 8, 572)]), fill=WHITE)
    # spine: a clear gap between the pages
    d.line(s([(cx, spine_top + 8), (cx, spine_bot - 2)]), fill=CLEAR, width=9*N)
    # text lines on each page, following the page curve
    for i in range(4):
        y0 = 352 + i * 26
        for side in (-1, 1):
            line = bez((cx + side*26, y0 + 4), (cx + side*60, y0 - 12 + i*1.5), (cx + side*130, y0 - 12 + i*1.5),
                       (cx + side*196, y0 - 2 + i*2.5), 30)
            d.line(s(line), fill=CLEAR, width=6*N, joint="curve")
    logo = img.resize((600, 600), Image.LANCZOS)
    logo.save(path)
    # preview: on the slide colour, and at icon size
    canvas = Image.new("RGB", (900, 600), "#2b2f4a")
    canvas.paste(logo, (0, 0), logo)
    small = Image.new("RGBA", (180, 180), "#3a2616")
    small.alpha_composite(logo.resize((140, 140), Image.LANCZOS), (20, 20))
    canvas.paste(small.convert("RGB"), (660, 40))
    tiny = Image.new("RGBA", (64, 64), "#3a2616")
    tiny.alpha_composite(logo.resize((52, 52), Image.LANCZOS), (6, 6))
    canvas.paste(tiny.convert("RGB"), (720, 280))
    canvas.save(preview)


draw(sys.argv[1], sys.argv[2])
