"""ALSAKKAF Brand Identity System v1 - PNG asset generator (PRJ-010).

Generates the raster brand assets from the same geometry as the SVG family,
using only the Python standard library (no Pillow, no external packages):

  docs/assets/brand/favicon-32x32.png
  docs/assets/brand/apple-touch-icon.png   (180x180)
  docs/assets/brand/social/og-image.png    (1200x630)

Run from anywhere:
  py 09_AI_Systems\\02_Tools\\Brand_Assets\\generate_brand_png.py
"""

import os
import struct
import zlib

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BRAND_DIR = os.path.join(REPO_ROOT, "docs", "assets", "brand")

NAVY = (10, 35, 66, 255)         # #0A2342
ELECTRIC = (30, 111, 255, 255)   # #1E6FFF
CYAN = (56, 214, 255, 255)       # #38D6FF
WHITE = (255, 255, 255, 255)
OFFWHITE = (244, 247, 251, 255)  # #F4F7FB
GRAY = (110, 122, 145, 255)


class Canvas:
    """Minimal RGBA raster canvas with scanline polygon fill."""

    def __init__(self, width, height, background=WHITE):
        self.w = width
        self.h = height
        self.rows = [bytearray(bytes(background) * width) for _ in range(height)]

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            row = self.rows[y]
            row[x * 4:x * 4 + 4] = bytes(color)

    def fill_span(self, x0, x1, y, color):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, int(x0))
        x1 = min(self.w, int(x1))
        if x1 <= x0:
            return
        self.rows[y][x0 * 4:x1 * 4] = bytes(color) * (x1 - x0)

    def fill_polygon(self, points, color):
        n = len(points)
        for y in range(self.h):
            yc = y + 0.5
            xs = []
            for i in range(n):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % n]
                if (y1 <= yc < y2) or (y2 <= yc < y1):
                    t = (yc - y1) / (y2 - y1)
                    xs.append(x1 + t * (x2 - x1))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_span(round(xs[j]), round(xs[j + 1]), y, color)

    def fill_rect(self, x, y, w, h, color):
        for yy in range(int(y), int(y + h)):
            self.fill_span(x, x + w, yy, color)

    def fill_rounded_rect(self, x, y, w, h, r, color):
        for yy in range(int(y), int(y + h)):
            yc = yy + 0.5
            dy = 0.0
            if yc < y + r:
                dy = (y + r) - yc
            elif yc > y + h - r:
                dy = yc - (y + h - r)
            if dy > 0:
                if dy >= r:
                    continue
                inset = r - (r * r - dy * dy) ** 0.5
            else:
                inset = 0.0
            self.fill_span(x + inset, x + w - inset, yy, color)

    def fill_circle(self, cx, cy, r, color):
        for yy in range(int(cy - r) - 1, int(cy + r) + 2):
            yc = yy + 0.5
            dy = yc - cy
            if abs(dy) >= r:
                continue
            dx = (r * r - dy * dy) ** 0.5
            self.fill_span(cx - dx, cx + dx, yy, color)

    def downsample(self, factor):
        out = Canvas(self.w // factor, self.h // factor)
        for y in range(out.h):
            orow = out.rows[y]
            for x in range(out.w):
                rs = gs = bs = as_ = 0
                for sy in range(factor):
                    srow = self.rows[y * factor + sy]
                    base = x * factor * 4
                    for sx in range(factor):
                        i = base + sx * 4
                        rs += srow[i]
                        gs += srow[i + 1]
                        bs += srow[i + 2]
                        as_ += srow[i + 3]
                n = factor * factor
                o = x * 4
                orow[o] = rs // n
                orow[o + 1] = gs // n
                orow[o + 2] = bs // n
                orow[o + 3] = as_ // n
        return out

    def to_png(self):
        raw = b"".join(b"\x00" + bytes(row) for row in self.rows)
        def chunk(tag, data):
            block = tag + data
            return struct.pack(">I", len(data)) + block + struct.pack(">I", zlib.crc32(block))
        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw, 9))
                + chunk(b"IEND", b""))

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(self.to_png())
        print("wrote", os.path.relpath(path, REPO_ROOT))


# 5x7 bitmap font (uppercase subset used by brand assets).
FONT = {
    "A": [".XXX.", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    "B": ["XXXX.", "X...X", "X...X", "XXXX.", "X...X", "X...X", "XXXX."],
    "C": [".XXX.", "X...X", "X....", "X....", "X....", "X...X", ".XXX."],
    "D": ["XXXX.", "X...X", "X...X", "X...X", "X...X", "X...X", "XXXX."],
    "E": ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "XXXXX"],
    "F": ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "X...."],
    "G": [".XXX.", "X...X", "X....", "X.XXX", "X...X", "X...X", ".XXX."],
    "H": ["X...X", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    "I": ["XXXXX", "..X..", "..X..", "..X..", "..X..", "..X..", "XXXXX"],
    "K": ["X...X", "X..X.", "X.X..", "XX...", "X.X..", "X..X.", "X...X"],
    "L": ["X....", "X....", "X....", "X....", "X....", "X....", "XXXXX"],
    "M": ["X...X", "XX.XX", "X.X.X", "X.X.X", "X...X", "X...X", "X...X"],
    "N": ["X...X", "XX..X", "X.X.X", "X..XX", "X...X", "X...X", "X...X"],
    "O": [".XXX.", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    "P": ["XXXX.", "X...X", "X...X", "XXXX.", "X....", "X....", "X...."],
    "R": ["XXXX.", "X...X", "X...X", "XXXX.", "X.X..", "X..X.", "X...X"],
    "S": [".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."],
    "T": ["XXXXX", "..X..", "..X..", "..X..", "..X..", "..X..", "..X.."],
    "U": ["X...X", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    "V": ["X...X", "X...X", "X...X", "X...X", "X...X", ".X.X.", "..X.."],
    "W": ["X...X", "X...X", "X...X", "X.X.X", "X.X.X", "XX.XX", "X...X"],
    "Y": ["X...X", "X...X", ".X.X.", "..X..", "..X..", "..X..", "..X.."],
    ".": [".....", ".....", ".....", ".....", ".....", ".XX..", ".XX.."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}


def draw_text(canvas, x, y, scale, text, color, tracking=1):
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for gy, grow in enumerate(glyph):
            for gx, cell in enumerate(grow):
                if cell == "X":
                    canvas.fill_rect(cx + gx * scale, y + gy * scale, scale, scale, color)
        cx += (5 + tracking) * scale
    return cx


def text_width(text, scale, tracking=1):
    return len(text) * (5 + tracking) * scale - tracking * scale


def draw_a_mark(canvas, ox, oy, unit, left=NAVY, right=CYAN, bar=ELECTRIC, favicon_geometry=True):
    """Draw the geometric A. Coordinates match the SVG family (100-unit box)."""
    def pts(raw):
        return [(ox + px * unit, oy + py * unit) for px, py in raw]
    if favicon_geometry:
        canvas.fill_polygon(pts([(50, 14), (16, 88), (32, 88), (50, 50)]), left)
        canvas.fill_polygon(pts([(50, 14), (84, 88), (68, 88), (50, 50)]), right)
        canvas.fill_polygon(pts([(39, 62), (61, 62), (66, 76), (34, 76)]), bar)
    else:
        canvas.fill_polygon(pts([(50, 10), (12, 92), (28, 92), (50, 44)]), left)
        canvas.fill_polygon(pts([(50, 10), (88, 92), (72, 92), (50, 44)]), right)
        canvas.fill_polygon(pts([(41, 64), (59, 64), (64, 76), (36, 76)]), bar)


def make_favicon_32():
    ss = 4  # supersample
    c = Canvas(32 * ss, 32 * ss, background=(0, 0, 0, 0))
    size = 32 * ss
    c.fill_rounded_rect(0, 0, size, size, size * 0.22, NAVY)
    draw_a_mark(c, 0, 0, size / 100.0, left=WHITE, right=CYAN, bar=ELECTRIC)
    c.downsample(ss).save(os.path.join(BRAND_DIR, "favicon-32x32.png"))


def make_apple_touch_icon():
    ss = 4
    c = Canvas(180 * ss, 180 * ss, background=NAVY)
    size = 180 * ss
    draw_a_mark(c, 0, 0, size / 100.0, left=WHITE, right=CYAN, bar=ELECTRIC)
    c.downsample(ss).save(os.path.join(BRAND_DIR, "apple-touch-icon.png"))


def make_og_image():
    ss = 2
    w, h = 1200 * ss, 630 * ss
    c = Canvas(w, h, background=WHITE)
    # Left accent panel and baseline accent bar (white-background master direction).
    c.fill_rect(0, 0, 14 * ss, h, ELECTRIC)
    c.fill_rect(0, h - 14 * ss, w, 14 * ss, CYAN)
    # Mark.
    draw_a_mark(c, 90 * ss, 120 * ss, 3.6 * ss, left=NAVY, right=CYAN, bar=ELECTRIC,
                favicon_geometry=False)
    # Wordmark block.
    tx = 520 * ss
    draw_text(c, tx, 190 * ss, 9 * ss, "ALSAKKAF", NAVY)
    draw_text(c, tx, 270 * ss, 5 * ss, "SYSTEMS", ELECTRIC, tracking=3)
    draw_text(c, tx, 350 * ss, 3 * ss, "AOS AI SERVICES", GRAY, tracking=2)
    draw_text(c, tx, 420 * ss, 3 * ss, "ALSAKKAFSYSTEMS.COM", CYAN, tracking=2)
    c.downsample(ss).save(os.path.join(BRAND_DIR, "social", "og-image.png"))


if __name__ == "__main__":
    make_favicon_32()
    make_apple_touch_icon()
    make_og_image()
    print("done")
