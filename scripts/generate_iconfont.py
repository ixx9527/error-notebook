"""
生成 iconfont.ttf 字体文件（纯直线段，无曲线）
运行: python scripts/generate_iconfont.py
依赖: pip install fonttools
"""
import os
import math
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen


UPM = 1024
ASCENT = 880
DESCENT = -144
SW = 56  # stroke width
N_POLY = 20  # polygon sides for circles


ICONS = {
    "camera": 0xE001,
    "book": 0xE002,
    "chart": 0xE003,
    "ai": 0xE004,
    "calendar": 0xE005,
    "user": 0xE006,
    "pdf": 0xE007,
    "star": 0xE008,
    "check": 0xE009,
    "party": 0xE00A,
    "search": 0xE00B,
    "bell": 0xE00C,
    "edit": 0xE00D,
    "delete": 0xE00E,
    "add": 0xE00F,
    "arrow-right": 0xE010,
}


def _poly_points(cx, cy, r, n=N_POLY):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _rect(pen, x1, y1, x2, y2):
    pen.moveTo((x1, y1))
    pen.lineTo((x2, y1))
    pen.lineTo((x2, y2))
    pen.lineTo((x1, y2))
    pen.closePath()


def _hollow_rect(pen, x1, y1, x2, y2, sw=SW):
    _rect(pen, x1, y1, x2, y2)
    _rect(pen, x1 + sw, y1 + sw, x2 - sw, y2 - sw)


def _poly_ring(pen, cx, cy, r_outer, r_inner, n=N_POLY):
    outer = _poly_points(cx, cy, r_outer, n)
    inner = _poly_points(cx, cy, r_inner, n)
    pen.moveTo(outer[0])
    for pt in outer[1:]:
        pen.lineTo(pt)
    pen.closePath()
    pen.moveTo(inner[0])
    for pt in inner[1:]:
        pen.lineTo(pt)
    pen.closePath()


def _poly_filled(pen, cx, cy, r, n=N_POLY):
    pts = _poly_points(cx, cy, r, n)
    pen.moveTo(pts[0])
    for pt in pts[1:]:
        pen.lineTo(pt)
    pen.closePath()


def draw_camera(pen):
    # Body
    _hollow_rect(pen, 172, 280, 852, 720)
    # Top bump
    _rect(pen, 380, 720, 644, 790)
    _rect(pen, 380 + SW, 720, 644 - SW, 790 - SW)
    # Lens ring (polygon)
    _poly_ring(pen, 512, 500, 140, 140 - SW, 24)
    # Flash dot
    _poly_filled(pen, 760, 660, 24, 8)


def draw_book(pen):
    # Left page
    _hollow_rect(pen, 128, 220, 496, 832)
    # Right page
    _hollow_rect(pen, 528, 220, 896, 832)
    # Spine
    _rect(pen, 496, 192, 528, 864)
    # Text lines left
    for y in [700, 600, 500]:
        _rect(pen, 200, y, 430, y + 20)
    # Text lines right
    for y in [700, 600, 500]:
        _rect(pen, 594, y, 824, y + 20)


def draw_chart(pen):
    # Y axis
    _rect(pen, 160, 192, 160 + SW, 832)
    # X axis
    _rect(pen, 160, 192, 864, 192 + SW)
    # Bars
    _rect(pen, 260, 560, 350, 776)
    _rect(pen, 410, 380, 500, 776)
    _rect(pen, 560, 500, 650, 776)
    _rect(pen, 710, 300, 800, 776)


def draw_ai(pen):
    # Outer ring (polygon)
    _poly_ring(pen, 512, 512, 320, 320 - SW, 28)
    # Cross lines
    _rect(pen, 280, 512 - SW // 2, 744, 512 + SW // 2)
    _rect(pen, 512 - SW // 2, 280, 512 + SW // 2, 744)
    # Center dot
    _poly_filled(pen, 512, 512, 48, 12)
    # Corner dots
    for cx, cy in [(380, 380), (644, 380), (380, 644), (644, 644)]:
        _poly_filled(pen, cx, cy, 32, 10)


def draw_calendar(pen):
    # Body
    _hollow_rect(pen, 160, 256, 864, 864)
    # Top bar (filled header)
    _rect(pen, 160, 256, 864, 380)
    # Hooks
    _rect(pen, 330, 148, 330 + SW, 300)
    _rect(pen, 694, 148, 694 + SW, 300)
    # Grid dots (3x4)
    for row in range(3):
        for col in range(4):
            cx = 280 + col * 150
            cy = 740 - row * 140
            _rect(pen, cx - 18, cy - 18, cx + 18, cy + 18)


def draw_user(pen):
    # Head (polygon ring)
    _poly_ring(pen, 512, 680, 130, 130 - SW, 20)
    # Body (octagonal arc approximation)
    body_pts_outer = [
        (240, 192), (240, 380), (320, 480), (512, 520),
        (704, 480), (784, 380), (784, 192),
    ]
    body_pts_inner = [
        (240 + SW, 192), (240 + SW, 360), (340, 448), (512, 480),
        (684, 448), (784 - SW, 360), (784 - SW, 192),
    ]
    pen.moveTo(body_pts_outer[0])
    for pt in body_pts_outer[1:]:
        pen.lineTo(pt)
    pen.closePath()
    pen.moveTo(body_pts_inner[0])
    for pt in body_pts_inner[1:]:
        pen.lineTo(pt)
    pen.closePath()


def draw_pdf(pen):
    # Document
    _hollow_rect(pen, 200, 128, 824, 896)
    # Fold corner
    pen.moveTo((660, 128))
    pen.lineTo((824, 292))
    pen.lineTo((660, 292))
    pen.closePath()
    # Text lines
    _rect(pen, 300, 480, 724, 480 + SW)
    _rect(pen, 300, 580, 600, 580 + SW)
    _rect(pen, 300, 680, 680, 680 + SW)


def draw_star(pen):
    cx, cy = 512, 520
    r_outer, r_inner = 340, 140
    pts = []
    for i in range(5):
        a_o = math.pi / 2 + 2 * math.pi * i / 5
        a_i = a_o + math.pi / 5
        pts.append((cx + r_outer * math.cos(a_o), cy + r_outer * math.sin(a_o)))
        pts.append((cx + r_inner * math.cos(a_i), cy + r_inner * math.sin(a_i)))
    pen.moveTo(pts[0])
    for pt in pts[1:]:
        pen.lineTo(pt)
    pen.closePath()


def draw_check(pen):
    pen.moveTo((160, 520))
    pen.lineTo((224, 456))
    pen.lineTo((420, 652))
    pen.lineTo((800, 240))
    pen.lineTo((864, 304))
    pen.lineTo((420, 740))
    pen.closePath()


def draw_party(pen):
    # Popper cone
    pen.moveTo((192, 832))
    pen.lineTo((460, 564))
    pen.lineTo((380, 500))
    pen.closePath()
    # Confetti rectangles
    _rect(pen, 540, 680, 600, 740)
    _rect(pen, 660, 560, 720, 620)
    _rect(pen, 740, 720, 800, 780)
    _rect(pen, 580, 440, 630, 490)
    # Confetti dots (small polygons)
    _poly_filled(pen, 600, 360, 24, 6)
    _poly_filled(pen, 760, 480, 20, 6)
    _poly_filled(pen, 520, 280, 18, 6)
    _poly_filled(pen, 720, 340, 16, 6)


def draw_search(pen):
    # Glass ring (polygon)
    _poly_ring(pen, 420, 580, 240, 240 - SW, 24)
    # Handle
    a = math.pi / 4
    sx = 420 + 240 * math.cos(a)
    sy = 580 + 240 * math.sin(a)
    ex = sx + 200 * math.cos(a)
    ey = sy + 200 * math.sin(a)
    dx = SW * math.cos(a + math.pi / 2)
    dy = SW * math.sin(a + math.pi / 2)
    pen.moveTo((sx, sy))
    pen.lineTo((ex, ey))
    pen.lineTo((ex + dx, ey + dy))
    pen.lineTo((sx + dx, sy + dy))
    pen.closePath()


def draw_bell(pen):
    # Bell body (polygon outline)
    outer = [
        (260, 500), (260, 360), (320, 260), (420, 200),
        (512, 180), (604, 200), (704, 260), (764, 360),
        (764, 500), (764, 640), (260, 640),
    ]
    inner = [
        (260 + SW, 500), (260 + SW, 370), (330, 280), (430, 230),
        (512, 214), (594, 230), (694, 280), (764 - SW, 370),
        (764 - SW, 500), (764 - SW, 640 - SW), (260 + SW, 640 - SW),
    ]
    pen.moveTo(outer[0])
    for pt in outer[1:]:
        pen.lineTo(pt)
    pen.closePath()
    pen.moveTo(inner[0])
    for pt in inner[1:]:
        pen.lineTo(pt)
    pen.closePath()
    # Bottom bar
    _rect(pen, 200, 640, 824, 640 + SW)
    # Clapper
    _rect(pen, 484, 700, 540, 800)


def draw_edit(pen):
    # Pencil body (diagonal rectangle)
    pen.moveTo((192, 688))
    pen.lineTo((640, 240))
    pen.lineTo((720, 320))
    pen.lineTo((272, 768))
    pen.closePath()
    # Inner cutout
    pen.moveTo((232, 688))
    pen.lineTo((640, 280))
    pen.lineTo((680, 320))
    pen.lineTo((272, 728))
    pen.closePath()
    # Tip
    pen.moveTo((192, 688))
    pen.lineTo((140, 840))
    pen.lineTo((272, 768))
    pen.closePath()
    # Eraser band
    _rect(pen, 610, 250, 730, 350)


def draw_delete(pen):
    # Can body
    _hollow_rect(pen, 280, 300, 744, 864)
    # Lid
    _rect(pen, 210, 240, 814, 240 + SW)
    # Handle
    _hollow_rect(pen, 410, 150, 614, 240, sw=SW // 2)
    # Internal lines
    _rect(pen, 430, 400, 430 + SW // 2, 760)
    _rect(pen, 512 - SW // 4, 400, 512 + SW // 4, 760)
    _rect(pen, 594, 400, 594 + SW // 2, 760)


def draw_add(pen):
    _rect(pen, 484, 192, 540, 832)
    _rect(pen, 192, 484, 832, 540)


def draw_arrow_right(pen):
    pen.moveTo((192, 444))
    pen.lineTo((580, 444))
    pen.lineTo((580, 280))
    pen.lineTo((832, 512))
    pen.lineTo((580, 744))
    pen.lineTo((580, 580))
    pen.lineTo((192, 580))
    pen.closePath()


DRAW_FUNCS = {
    "camera": draw_camera, "book": draw_book, "chart": draw_chart,
    "ai": draw_ai, "calendar": draw_calendar, "user": draw_user,
    "pdf": draw_pdf, "star": draw_star, "check": draw_check,
    "party": draw_party, "search": draw_search, "bell": draw_bell,
    "edit": draw_edit, "delete": draw_delete, "add": draw_add,
    "arrow-right": draw_arrow_right,
}


def generate(output_path):
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder([".notdef"] + list(ICONS.keys()))
    fb.setupCharacterMap({code: name for name, code in ICONS.items()})

    glyph_dict = {}

    notdef_pen = TTGlyphPen(None)
    notdef_pen.moveTo((0, 0))
    notdef_pen.lineTo((1, 0))
    notdef_pen.lineTo((1, 1))
    notdef_pen.lineTo((0, 1))
    notdef_pen.closePath()
    glyph_dict[".notdef"] = notdef_pen.glyph()

    for name, func in DRAW_FUNCS.items():
        pen = TTGlyphPen(None)
        try:
            func(pen)
        except Exception as e:
            print(f"Warning: error drawing {name}: {e}")
        glyph_dict[name] = pen.glyph()

    fb.setupGlyf(glyph_dict)

    metrics = {name: (UPM, 0) for name in [".notdef"] + list(ICONS.keys())}
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable({
        "familyName": "ErrorNotebookIcons",
        "styleName": "Regular",
    })
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT,
                usWinAscent=ASCENT, usWinDescent=abs(DESCENT))
    fb.setupPost()

    fb.font.save(output_path)
    print(f"Generated: {output_path}")
    print(f"Icons: {len(ICONS)}")
    for name, code in ICONS.items():
        print(f"  .icon-{name} -> U+{code:04X}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output = os.path.join(project_root, "miniprogram", "assets", "fonts", "iconfont.ttf")
    os.makedirs(os.path.dirname(output), exist_ok=True)
    generate(output)
