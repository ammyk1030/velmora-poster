#!/usr/bin/env python3
"""Velmora poster: a travel poster for a place that does not exist.

Pure Python standard library only, no network, deterministic.
Writes /output/entry.png in the sandbox, or entry.png beside this
file when run locally (where /output does not exist).
Image: 768x1024, PNG, under 1 MiB.
"""
import os
import random
import struct
import zlib

W, H = 768, 1024

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "01010", "01010", "00100", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
}


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.set(x, y, c)

    def disc(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def text(self, s, x, y, scale, c, shadow=None):
        # x,y is top-left; returns width
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        if shadow:
                            self.fill_rect(cx + gx * scale + 3, y + gy * scale + 3,
                                           cx + (gx + 1) * scale + 3, y + (gy + 1) * scale + 3, shadow)
                        self.fill_rect(cx + gx * scale, y + gy * scale,
                                       cx + (gx + 1) * scale, y + (gy + 1) * scale, c)
            cx += 6 * scale
        return cx - x - scale

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale


def main():
    cv = Canvas(W, H)
    rng = random.Random(20261121)

    # Sky gradient: indigo -> violet -> amber, down to the horizon at y=700.
    stops = [(0, (18, 28, 74)), (300, (74, 52, 110)), (520, (178, 84, 96)),
             (700, (242, 166, 90)), (760, (242, 166, 90))]
    for y in range(0, 761):
        for si in range(len(stops) - 1):
            y0, c0 = stops[si]
            y1, c1 = stops[si + 1]
            if y0 <= y <= y1:
                t = 0 if y1 == y0 else (y - y0) / (y1 - y0)
                col = lerp(c0, c1, t)
                break
        else:
            col = stops[-1][1]
        for x in range(W):
            cv.set(x, y, col)

    # Stars in the upper sky.
    for _ in range(140):
        x = rng.randrange(0, W)
        y = rng.randrange(0, 340)
        b = rng.choice([(255, 255, 255), (255, 240, 200), (200, 220, 255)])
        cv.set(x, y, b)
        if rng.random() < 0.3:
            cv.set(x + 1, y, b)

    # Sun with a soft halo, low over the lake.
    for r, col in [(170, (244, 190, 110)), (140, (250, 205, 125)), (112, (255, 217, 138))]:
        cv.disc(384, 640, r, col)

    # Far mountains.
    for x in range(W):
        top = 620 - int(70 * (0.5 + 0.5 * __import__("math").sin(x * 0.011 + 1.2))
                        + 40 * (0.5 + 0.5 * __import__("math").sin(x * 0.031 + 0.4)))
        for y in range(top, 762):
            # darken with depth
            t = min(1.0, (y - top) / 140.0)
            cv.set(x, y, lerp((62, 48, 96), (40, 30, 68), t))
    # Near mountains, left and right, with a smooth valley for the sun.
    for x in range(W):
        top = 690 - int(55 * (0.5 + 0.5 * __import__("math").sin(x * 0.017 + 3.0)))
        d = abs(x - 385) / 130.0
        valley = 48 * max(0.0, 1.0 - d * d)
        top += int(valley)
        for y in range(top, 762):
            cv.set(x, y, (34, 26, 58))

    # Lake, y 762..1023, deep teal-indigo with a warm sun path.
    for y in range(762, H):
        t = (y - 762) / (H - 762)
        col = lerp((38, 52, 96), (16, 22, 52), t)
        for x in range(W):
            cv.set(x, y, col)
    # Sun reflection: broken warm streaks down the centre.
    for _ in range(90):
        x = 384 + rng.randrange(-70, 71)
        y = rng.randrange(770, 1010)
        ln = rng.randrange(8, 42)
        col = (255, 205, 130) if rng.random() < 0.7 else (250, 170, 100)
        cv.fill_rect(x, y, x + ln, y + 3, col)

    # Floating lanterns in the sky, warm diamonds.
    for _ in range(26):
        x = rng.randrange(30, W - 30)
        y = rng.randrange(180, 560)
        s = rng.choice([3, 4, 5])
        col = (255, 196, 110)
        cv.fill_rect(x - s, y, x + s + 1, y + 1, col)
        cv.fill_rect(x, y - s, x + 1, y + s + 1, col)
        cv.set(x, y, (255, 240, 200))

    # A small lantern boat on the lake, larger and clearer.
    bx, by = 384, 892
    for x in range(bx - 95, bx + 96):
        dy = int(14 * (1 - abs(x - bx) / 95))
        for y in range(by, by + dy + 16):
            cv.set(x, y, (18, 12, 34))
    cv.fill_rect(bx - 46, by - 4, bx + 47, by + 2, (255, 196, 110))
    cv.fill_rect(bx - 12, by - 38, bx + 13, by - 4, (255, 196, 110))
    cv.fill_rect(bx - 3, by - 62, bx + 4, by - 38, (30, 20, 48))
    cv.disc(bx, by - 38, 4, (255, 240, 200))

    # Title: VELMORA, large, cream with a dark shadow, centred near the top.
    title = "VELMORA"
    scale = 15
    tw = cv.text_width(title, scale)
    tx = (W - tw) // 2
    cv.text(title, tx, 84, scale, (255, 243, 214), shadow=(24, 18, 54))
    # Rule line under the title.
    cv.fill_rect(tx, 84 + 7 * scale + 18, tx + tw, 84 + 7 * scale + 22, (255, 214, 140))
    # Subtitle, smaller.
    sub = "WHERE THE SKY KEEPS ITS LIGHT"
    s2 = 4
    sw = cv.text_width(sub, s2)
    cv.text(sub, (W - sw) // 2, 84 + 7 * scale + 38, s2, (255, 236, 200), shadow=(24, 18, 54))
    sub2 = "ISLE OF LANTERNS"
    s3 = 4
    sw2 = cv.text_width(sub2, s3)
    cv.text(sub2, (W - sw2) // 2, 84 + 7 * scale + 38 + 7 * s3 + 12, s3,
            (255, 214, 140), shadow=(24, 18, 54))

    # Write PNG, pure stdlib: filter Up (2) per row, zlib level 9.
    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    prev = bytes(W * 3)
    for y in range(H):
        row = bytes(cv.px[y * W * 3:(y + 1) * W * 3])
        if y == 0:
            raw.append(0)
            raw.extend(row)
        else:
            raw.append(2)
            raw.extend((b - p) & 0xFF for b, p in zip(row, prev))
        prev = row
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")

    out = "/output/entry.png" if os.path.isdir("/output") else "entry.png"
    with open(out, "wb") as f:
        f.write(png)
    print(f"wrote {out} {len(png)} bytes {W}x{H}")


if __name__ == "__main__":
    main()
