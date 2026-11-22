#!/usr/bin/env python3
"""Procedural PNG generator: top-down bowl of ramen, stdlib only.

Renders at 2x (1536x1536) with box downsampling to 768x768 for smooth
edges, then encodes PNG by hand (struct + zlib). No PIL, no network.
"""
import math
import random
import struct
import zlib

S = 1536          # render resolution (2x supersample)
OUT = 768
CX, CY = S // 2, S // 2

buf = bytearray(S * S * 3)


def set_px(x, y, r, g, b):
    if 0 <= x < S and 0 <= y < S:
        i = (y * S + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = r, g, b


def blend_px(x, y, r, g, b, a):
    if 0 <= x < S and 0 <= y < S and a > 0:
        i = (y * S + x) * 3
        buf[i] = int(buf[i] * (1 - a) + r * a)
        buf[i + 1] = int(buf[i + 1] * (1 - a) + g * a)
        buf[i + 2] = int(buf[i + 2] * (1 - a) + b * a)


def disc(cx, cy, rad, col, alpha=1.0):
    r0 = max(0, int(cx - rad)); r1 = min(S - 1, int(cx + rad))
    c0 = max(0, int(cy - rad)); c1 = min(S - 1, int(cy + rad))
    rr = rad * rad
    cr, cg, cb = col
    for y in range(c0, c1 + 1):
        dy = y - cy
        for x in range(r0, r1 + 1):
            dx = x - cx
            if dx * dx + dy * dy <= rr:
                if alpha >= 1.0:
                    set_px(x, y, cr, cg, cb)
                else:
                    blend_px(x, y, cr, cg, cb, alpha)


def ellipse(cx, cy, rx, ry, col, alpha=1.0):
    r0 = max(0, int(cx - rx)); r1 = min(S - 1, int(cx + rx))
    c0 = max(0, int(cy - ry)); c1 = min(S - 1, int(cy + ry))
    cr, cg, cb = col
    for y in range(c0, c1 + 1):
        ny = (y - cy) / ry
        for x in range(r0, r1 + 1):
            nx = (x - cx) / rx
            if nx * nx + ny * ny <= 1.0:
                if alpha >= 1.0:
                    set_px(x, y, cr, cg, cb)
                else:
                    blend_px(x, y, cr, cg, cb, alpha)


def ring(cx, cy, rad, w, col, alpha=1.0):
    r0 = max(0, int(cx - rad - w)); r1 = min(S - 1, int(cx + rad + w))
    c0 = max(0, int(cy - rad - w)); c1 = min(S - 1, int(cy + rad + w))
    cr, cg, cb = col
    for y in range(c0, c1 + 1):
        dy = y - cy
        for x in range(r0, r1 + 1):
            dx = x - cx
            d = math.sqrt(dx * dx + dy * dy)
            if abs(d - rad) <= w / 2:
                if alpha >= 1.0:
                    set_px(x, y, cr, cg, cb)
                else:
                    blend_px(x, y, cr, cg, cb, alpha)


def capsule(x1, y1, x2, y2, w, col, alpha=1.0):
    dx, dy = x2 - x1, y2 - y1
    ln2 = dx * dx + dy * dy
    hw = w / 2
    r0 = max(0, int(min(x1, x2) - hw)); r1 = min(S - 1, int(max(x1, x2) + hw))
    c0 = max(0, int(min(y1, y2) - hw)); c1 = min(S - 1, int(max(y1, y2) + hw))
    cr, cg, cb = col
    for y in range(c0, c1 + 1):
        for x in range(r0, r1 + 1):
            if ln2 == 0:
                t = 0.0
            else:
                t = ((x - x1) * dx + (y - y1) * dy) / ln2
                t = 0.0 if t < 0 else (1.0 if t > 1 else t)
            px, py = x1 + t * dx, y1 + t * dy
            ddx, ddy = x - px, y - py
            if ddx * ddx + ddy * ddy <= hw * hw:
                if alpha >= 1.0:
                    set_px(x, y, cr, cg, cb)
                else:
                    blend_px(x, y, cr, cg, cb, alpha)


def wavy_line(pts, w, col, alpha=1.0):
    for i in range(len(pts) - 1):
        capsule(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], w, col, alpha)


rng = random.Random(20261122)

# ---- 1. wooden table background: warm vertical gradient + planks ----
for y in range(S):
    t = y / S
    r = int(122 - 52 * t)
    g = int(76 - 32 * t)
    b = int(42 - 18 * t)
    base = y * S * 3
    for x in range(S):
        # subtle horizontal grain
        grain = int(7 * math.sin(x * 0.011 + 3.0 * math.sin(y * 0.004)))
        buf[base + x * 3] = max(0, min(255, r + grain))
        buf[base + x * 3 + 1] = max(0, min(255, g + grain))
        buf[base + x * 3 + 2] = max(0, min(255, b + grain))
# plank seams
for py in (S * 0.22, S * 0.52, S * 0.82):
    for x in range(S):
        blend_px(x, int(py), 30, 18, 10, 0.55)
        blend_px(x, int(py) + 2, 150, 100, 60, 0.25)

# soft shadow under bowl
disc(CX + 26, CY + 40, 640, (20, 10, 5), 0.35)

# ---- 2. bowl: indigo ceramic, rim band, broth ----
disc(CX, CY, 600, (24, 34, 58))                       # outer body
disc(CX, CY, 585, (38, 52, 82))                       # body gradient edge
disc(CX, CY, 540, (52, 70, 108))                      # rim band
disc(CX, CY, 512, (30, 42, 70))                       # inner rim shadow
# broth: radial golden gradient (paint concentric discs)
for i in range(60, 0, -1):
    rad = 500 * i / 60
    t = i / 60
    r = int(232 - 62 * t)
    g = int(164 - 66 * t)
    b = int(66 - 30 * t)
    disc(CX, CY, rad, (r, g, b))
# glossy oil sheen blobs on broth
for (ox, oy, orad) in [(-180, -150, 150), (190, 120, 120), (60, -260, 90),
                       (-260, 180, 80), (250, -120, 70)]:
    disc(CX + ox, CY + oy, orad, (250, 205, 105), 0.22)
# chili-oil red swirls
for k in range(3):
    pts = []
    a0 = rng.uniform(0, 6.28)
    for s in range(40):
        a = a0 + s * 0.09
        rr = 120 + k * 90 + 26 * math.sin(s * 0.5)
        pts.append((CX + rr * math.cos(a), CY + rr * math.sin(a)))
    wavy_line(pts, 16, (176, 48, 32), 0.45)

# ---- 3. noodles: wavy strands across the broth ----
NOODLE = (243, 214, 140)
NOODLE_D = (214, 168, 82)
for n in range(38):
    y0 = CY - 430 + n * 23 + rng.uniform(-6, 6)
    amp = rng.uniform(14, 34)
    lam = rng.uniform(150, 260)
    ph = rng.uniform(0, 6.28)
    pts = []
    x = CX - 470
    while x < CX + 470:
        yy = y0 + amp * math.sin(6.283 * x / lam + ph)
        if (x - CX) ** 2 + (yy - CY) ** 2 < 495 * 495:
            pts.append((x, yy))
        x += 9
    if len(pts) > 3:
        wavy_line(pts, 13, NOODLE_D, 0.9)
        wavy_line([(px, py - 3) for px, py in pts], 8, NOODLE, 0.95)

# ---- 4. toppings ----
# chashu slices (lower right): pink rounds with fat edge
for (sx, sy, sr) in [(260, 210, 112), (140, 330, 88), (350, 320, 80)]:
    disc(CX + sx, CY + sy, sr, (244, 214, 196))
    disc(CX + sx, CY + sy, sr - 16, (228, 150, 130))
    disc(CX + sx, CY + sy, sr - 44, (196, 116, 98))
    disc(CX + sx - sr * 0.25, CY + sy - sr * 0.3, sr * 0.28, (252, 226, 205), 0.8)

# narutomaki (upper left): white disc, pink spiral
nx, ny = CX - 270, CY - 250
disc(nx, ny, 74, (255, 250, 242))
ring(nx, ny, 52, 13, (242, 125, 157))
ring(nx, ny, 26, 11, (242, 125, 157))
disc(nx, ny, 10, (242, 125, 157))

# ajitama egg halves (left + upper right)
for (ex, ey, tilt) in [(CX - 300, CY + 60, 0.5), (CX + 40, CY - 330, -0.4)]:
    ellipse(ex, ey, 118, 92, (253, 246, 232))
    ellipse(ex, ey, 108, 82, (250, 240, 220))
    disc(ex, ey, 52, (245, 158, 11))
    disc(ex, ey, 40, (232, 130, 6))
    disc(ex - 14, ey - 16, 14, (252, 190, 60), 0.9)

# green onions scattered
for _ in range(60):
    a = rng.uniform(0, 6.283)
    rr = rng.uniform(60, 460)
    gx, gy = CX + rr * math.cos(a), CY + rr * math.sin(a)
    if (gx - (CX - 300)) ** 2 / 118 ** 2 + (gy - (CY + 60)) ** 2 / 92 ** 2 < 1.1:
        continue
    if (gx - (CX + 40)) ** 2 / 118 ** 2 + (gy - (CY - 330)) ** 2 / 92 ** 2 < 1.1:
        continue
    ring(gx, gy, rng.uniform(9, 15), 6, (46, 139, 60))
    disc(gx, gy, 4, (28, 94, 38))

# sesame seeds
for _ in range(70):
    a = rng.uniform(0, 6.283)
    rr = rng.uniform(80, 470)
    disc(CX + rr * math.cos(a), CY + rr * math.sin(a), 4, (255, 244, 214), 0.85)

# ---- 5. chopsticks resting on rim (upper right, diagonal) ----
capsule(CX + 300, CY - 640, CX + 620, CY - 260, 26, (122, 74, 33))
capsule(CX + 340, CY - 620, CX + 660, CY - 240, 26, (122, 74, 33))
capsule(CX + 300, CY - 640, CX + 620, CY - 260, 10, (168, 110, 52))
capsule(CX + 340, CY - 620, CX + 660, CY - 240, 10, (168, 110, 52))

# ---- 6. steam wisps above the bowl ----
for k, xoff in enumerate((-140, 0, 150)):
    pts = []
    for s in range(30):
        yy = CY - 560 - s * 9
        xx = CX + xoff + 26 * math.sin(s * 0.45 + k * 2.1)
        pts.append((xx, yy))
    wavy_line(pts, 22, (255, 255, 255), 0.10)

# ---- 7. downsample 2x2 + vignette, then PNG encode ----
small = bytearray(OUT * OUT * 3)
for y in range(OUT):
    for x in range(OUT):
        dx = (x - OUT / 2) / (OUT / 2)
        dy = (y - OUT / 2) / (OUT / 2)
        d2 = dx * dx + dy * dy
        vig = 1.0 - 0.22 * max(0.0, d2 - 0.55)
        acc = [0, 0, 0]
        for oy in (0, 1):
            for ox in (0, 1):
                si = ((2 * y + oy) * S + (2 * x + ox)) * 3
                acc[0] += buf[si]; acc[1] += buf[si + 1]; acc[2] += buf[si + 2]
        di = (y * OUT + x) * 3
        for c in range(3):
            v = int(acc[c] / 4 * vig)
            # gentle warm saturation lift
            small[di + c] = max(0, min(255, v))


def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


ihdr = struct.pack(">IIBBBBB", OUT, OUT, 8, 2, 0, 0, 0)
raw = b"".join(b"\x00" + bytes(small[y * OUT * 3:(y + 1) * OUT * 3])
               for y in range(OUT))
png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
       + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))

with open("entry.png", "wb") as fh:
    fh.write(png)
print("wrote entry.png", len(png), "bytes,", OUT, "x", OUT)
