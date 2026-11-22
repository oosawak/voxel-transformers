import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Zhao Yun (趙雲) -> Silver Lancer Robot -> Noble White Warhorse (白馬)!
PALETTE = {
    1: (234, 240, 248, 255),  # Gleaming Pure Silver-White Armor (白銀の鎧)
    2: (172, 186, 206, 255),  # Honed Steel-Silver Shading & Spear Shaft
    3: (44, 112, 198, 255),   # Heroic Sky-Sapphire Cloak, Sash & Accents
    4: (26, 62, 126, 255),    # Deep Cobalt Under-Armor & Joints
    5: (242, 202, 74, 255),   # Refined Pale-Gold Crest & Fittings
    6: (212, 46, 54, 255),    # Crisp Crimson Spear Tassel & Waist Accent
    7: (250, 224, 206, 255),  # Noble Youthful Warrior Face
    8: (42, 46, 58, 255),     # Dark Hair & Boot Soles
    9: (96, 224, 255, 255),   # Luminous Ice-Cyan Glowing Eyes & Lance Core
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(int(x0), int(x1))), min(X - 1, max(int(x0), int(x1)))
    y0, y1 = max(0, min(int(y0), int(y1))), min(Y - 1, max(int(y0), int(y1)))
    z0, z1 = max(0, min(int(z0), int(z1))), min(Z - 1, max(int(z0), int(z1)))
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


def draw_6conn_line(grid, p0, p1, col, pad=(0, 0, 0), only_empty=False):
    X, Y, Z = grid.shape
    x0, y0, z0 = int(round(p0[0])), int(round(p0[1])), int(round(p0[2]))
    x1, y1, z1 = int(round(p1[0])), int(round(p1[1])), int(round(p1[2]))
    steps = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1) * 2
    prev = None
    px, py, pz = pad

    def stamp(cx_, cy_, cz_):
        xa, xb = max(0, cx_ - px), min(X - 1, cx_ + px)
        ya, yb = max(0, cy_ - py), min(Y - 1, cy_ + py)
        za, zb = max(0, cz_ - pz), min(Z - 1, cz_ + pz)
        if only_empty:
            sub = grid[xa:xb + 1, ya:yb + 1, za:zb + 1]
            sub[sub == 0] = col
        else:
            grid[xa:xb + 1, ya:yb + 1, za:zb + 1] = col

    for i in range(steps + 1):
        t = i / steps
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        z = int(round(z0 + (z1 - z0) * t))
        if prev is not None:
            ox, oy, oz = prev
            if x != ox:
                stamp(x, oy, oz)
                ox = x
            if y != oy:
                stamp(ox, y, oz)
                oy = y
            if z != oz:
                stamp(ox, oy, z)
        else:
            stamp(x, y, z)
        prev = (x, y, z)


def hollow_interior_26(grid, z_min, z_max):
    X, Y, Z = grid.shape
    to_clear = []
    for x in range(1, X - 1):
        for y in range(1, Y - 1):
            for z in range(max(1, z_min), min(Z - 1, z_max + 1)):
                if grid[x, y, z] == 0:
                    continue
                if np.all(grid[x - 1:x + 2, y - 1:y + 2, z - 1:z + 2] > 0):
                    to_clear.append((x, y, z))
    for x, y, z in to_clear:
        grid[x, y, z] = 0


def count_components_6(grid):
    xs, ys, zs = np.nonzero(grid)
    if len(xs) == 0:
        return 0, -1
    occupied = set(zip(xs.tolist(), ys.tolist(), zs.tolist()))
    visited = set()
    comps = 0
    for start in occupied:
        if start in visited:
            continue
        comps += 1
        q = deque([start])
        visited.add(start)
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nb = (x + dx, y + dy, z + dz)
                if nb in occupied and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
    return comps, int(zs.min())


def draw_silver_spear(grid, sx, sy, z_bot, z_top):
    """Draw Zhao Yun's gleaming Silver Dragon Spear (龍胆亮銀槍)."""
    fill_box(grid, sx, sx, sy, sy, z_bot, z_top - 10, 2)
    fill_box(grid, sx, sx, sy, sy, z_bot, z_bot + 1, 5)
    fill_box(grid, sx - 1, sx + 1, sy, sy, z_top - 11, z_top - 10, 5)
    fill_box(grid, sx - 1, sx + 1, sy - 1, sy, z_top - 14, z_top - 12, 6)
    fill_box(grid, sx - 1, sx + 1, sy, sy, z_top - 9, z_top - 6, 1)
    fill_box(grid, sx, sx, sy, sy, z_top - 5, z_top, 1)
    fill_box(grid, sx, sx, sy + 1, sy + 1, z_top - 8, z_top - 3, 9)


# ============================================================
# FORM A: ZHAO YUN CHARACTER FIGURE (34 x 22 x 46) [UNCHANGED]
# ============================================================
def build_a():
    grid = np.zeros((34, 22, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 16
    cx_r = X // 2      # 17

    fill_sym_box(grid, 2, 4, 10, 15, 0, 1, 8)
    fill_sym_box(grid, 2, 4, 10, 16, 1, 2, 1)
    fill_sym_box(grid, 2, 3, 11, 14, 3, 15, 1)
    fill_sym_box(grid, 3, 3, 14, 15, 4, 14, 2)
    fill_sym_box(grid, 2, 4, 14, 15, 13, 15, 5)

    fill_sym_box(grid, 0, 4, 10, 14, 16, 21, 4)
    fill_sym_box(grid, 1, 4, 14, 15, 13, 20, 1)
    fill_sym_box(grid, 1, 4, 15, 15, 13, 13, 3)
    fill_sym_box(grid, 0, 4, 14, 15, 20, 21, 3)
    fill_sym_box(grid, 0, 1, 15, 16, 17, 21, 3)
    fill_sym_box(grid, 0, 0, 16, 16, 20, 21, 5)

    fill_sym_box(grid, 0, 4, 10, 15, 22, 30, 1)
    fill_sym_box(grid, 0, 3, 15, 15, 23, 29, 2)
    fill_sym_box(grid, 0, 1, 15, 16, 26, 28, 5)
    fill_sym_box(grid, 1, 3, 11, 15, 30, 31, 3)
    fill_sym_box(grid, 0, 4, 8, 9, 16, 30, 3)
    fill_sym_box(grid, 0, 5, 7, 8, 5, 18, 3)
    fill_sym_box(grid, 0, 5, 7, 7, 5, 6, 1)

    fill_sym_box(grid, 5, 7, 10, 14, 27, 31, 1)
    fill_sym_box(grid, 6, 7, 11, 14, 30, 31, 5)
    fill_box(grid, cx_l - 7, cx_l - 5, 11, 14, 19, 26, 1)
    fill_box(grid, cx_l - 7, cx_l - 6, 12, 14, 17, 18, 7)
    fill_box(grid, cx_r + 5, cx_r + 7, 11, 15, 20, 26, 1)
    fill_box(grid, cx_r + 6, cx_r + 8, 14, 17, 19, 21, 7)
    draw_silver_spear(grid, cx_r + 9, 16, z_bot=2, z_top=44)

    fill_sym_box(grid, 0, 1, 11, 14, 31, 32, 7)
    fill_sym_box(grid, 0, 2, 10, 15, 32, 37, 7)
    fill_sym_box(grid, 1, 2, 15, 15, 34, 35, 9)
    fill_sym_box(grid, 0, 3, 9, 15, 36, 39, 1)
    fill_sym_box(grid, 0, 2, 15, 16, 36, 37, 5)
    fill_sym_box(grid, 0, 0, 11, 13, 40, 42, 5)
    draw_6conn_line(grid, (cx_r, 12, 42), (cx_r, 7, 39), 1, pad=(1, 0, 0))
    draw_6conn_line(grid, (cx_r, 7, 39), (cx_r, 5, 34), 1, pad=(1, 0, 0))

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: ZHAO YUN SLEEK SILVER LANCER ROBOT (42 x 26 x 48) [UNCHANGED]
# ============================================================
def build_b():
    grid = np.zeros((42, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 20
    cx_r = X // 2      # 21

    fill_sym_box(grid, 2, 4, 10, 17, 0, 2, 4)
    fill_sym_box(grid, 2, 4, 11, 17, 1, 2, 1)
    fill_sym_box(grid, 3, 3, 17, 19, 1, 2, 1)
    fill_sym_box(grid, 2, 4, 11, 15, 3, 16, 1)
    fill_sym_box(grid, 3, 3, 15, 16, 4, 15, 2)
    fill_sym_box(grid, 4, 5, 11, 14, 7, 14, 3)
    fill_sym_box(grid, 2, 4, 15, 17, 13, 17, 1)
    fill_sym_box(grid, 3, 3, 17, 17, 14, 16, 5)

    fill_sym_box(grid, 2, 4, 11, 15, 16, 20, 4)
    fill_sym_box(grid, 2, 4, 13, 15, 17, 19, 1)
    fill_sym_box(grid, 0, 4, 11, 15, 20, 23, 4)
    fill_sym_box(grid, 1, 5, 15, 16, 17, 22, 1)
    fill_sym_box(grid, 1, 5, 16, 16, 17, 17, 3)
    fill_sym_box(grid, 4, 6, 11, 15, 18, 22, 3)
    fill_sym_box(grid, 0, 1, 15, 17, 18, 23, 1)
    fill_sym_box(grid, 0, 1, 17, 17, 21, 22, 5)

    fill_sym_box(grid, 0, 3, 11, 15, 23, 25, 4)
    fill_sym_box(grid, 0, 6, 10, 16, 26, 34, 1)
    fill_sym_box(grid, 1, 5, 16, 17, 27, 33, 2)
    fill_sym_box(grid, 0, 2, 17, 18, 28, 32, 3)
    fill_sym_box(grid, 0, 1, 18, 18, 29, 31, 5)
    fill_sym_box(grid, 0, 0, 18, 19, 30, 30, 9)
    fill_sym_box(grid, 1, 4, 11, 15, 34, 35, 3)
    fill_sym_box(grid, 0, 4, 7, 10, 25, 33, 4)
    fill_sym_box(grid, 0, 4, 6, 7, 10, 31, 3)
    fill_sym_box(grid, 0, 4, 6, 6, 10, 11, 1)
    draw_6conn_line(grid, (cx_r + 3, 8, 31), (cx_r + 10, 5, 38), 1)
    draw_6conn_line(grid, (cx_l - 3, 8, 31), (cx_l - 10, 5, 38), 1)

    fill_sym_box(grid, 6, 8, 12, 15, 30, 33, 4)
    fill_sym_box(grid, 7, 10, 11, 16, 29, 34, 1)
    fill_sym_box(grid, 9, 12, 12, 15, 33, 35, 1)
    fill_sym_box(grid, 10, 12, 12, 15, 35, 35, 5)
    fill_sym_box(grid, 7, 9, 12, 15, 23, 29, 4)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 17, 22, 1)
    fill_box(grid, cx_l - 10, cx_l - 10, 13, 16, 18, 21, 3)
    fill_box(grid, cx_l - 9, cx_l - 7, 13, 15, 15, 16, 4)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 18, 23, 1)
    fill_box(grid, cx_r + 9, cx_r + 12, 15, 18, 17, 20, 5)
    fill_box(grid, cx_r + 11, cx_r + 13, 17, 19, 16, 19, 4)
    draw_silver_spear(grid, cx_r + 14, 18, z_bot=2, z_top=47)

    fill_sym_box(grid, 0, 1, 12, 15, 35, 36, 4)
    fill_sym_box(grid, 0, 2, 11, 16, 36, 42, 1)
    fill_sym_box(grid, 0, 2, 16, 17, 36, 37, 2)
    fill_sym_box(grid, 0, 2, 16, 17, 38, 39, 4)
    fill_sym_box(grid, 1, 2, 17, 17, 38, 39, 9)
    fill_sym_box(grid, 0, 2, 16, 18, 40, 40, 5)
    draw_6conn_line(grid, (cx_r, 17, 41), (cx_r + 4, 15, 45), 5)
    draw_6conn_line(grid, (cx_l, 17, 41), (cx_l - 4, 15, 45), 5)
    draw_6conn_line(grid, (cx_r, 13, 42), (cx_r, 7, 46), 1, pad=(1, 0, 0))
    draw_6conn_line(grid, (cx_r, 7, 46), (cx_r, 4, 41), 1, pad=(1, 0, 0))

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: NOBLE WHITE WARHORSE (白馬) (22 x 42 x 34)
# ============================================================
def build_c():
    grid = np.zeros((22, 42, 34), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 10
    cx_r = X // 2      # 11

    # 4 Sleek Athletic White Horse Legs & Dark Hooves (Z: 0..14)
    fill_sym_box(grid, 2, 3, 27, 29, 0, 1, 8)     # Front hooves
    fill_sym_box(grid, 2, 3, 27, 29, 2, 13, 1)    # Front legs
    fill_sym_box(grid, 3, 3, 28, 29, 5, 10, 2)    # Silver leg guards
    fill_sym_box(grid, 2, 3, 11, 13, 0, 1, 8)     # Hind hooves
    fill_sym_box(grid, 2, 3, 11, 13, 2, 12, 1)    # Hind legs
    fill_sym_box(grid, 2, 4, 10, 15, 10, 16, 1)   # Muscular white hindquarters

    # Sleek White Horse Barrel & Sky-Sapphire / Gold Saddle Caparison (Z: 12..21, Y: 9..31)
    fill_sym_box(grid, 0, 4, 10, 30, 12, 20, 1)   # Pure silver-white horse body!
    fill_sym_box(grid, 0, 3, 9, 31, 13, 19, 1)
    # Sky-sapphire saddle cloth with gold border & crimson tassel
    fill_sym_box(grid, 0, 4, 15, 25, 19, 21, 3)   # Sapphire saddle pad
    fill_sym_box(grid, 4, 5, 16, 24, 13, 20, 3)   # Sapphire side barding
    fill_sym_box(grid, 5, 5, 16, 24, 13, 13, 5)   # Gold lower trim
    fill_sym_box(grid, 0, 3, 15, 16, 21, 22, 5)   # Gold cantle
    fill_sym_box(grid, 0, 3, 24, 25, 21, 22, 5)   # Gold pommel
    fill_sym_box(grid, 0, 3, 31, 32, 14, 18, 3)   # Sapphire chest band
    fill_sym_box(grid, 0, 1, 32, 32, 15, 17, 5)   # Gold breastplate emblem

    # Long Flowing Silver-White Horse Tail (Y: 2..10, Z: 6..19)
    draw_6conn_line(grid, (cx_r, 9, 18), (cx_r, 5, 14), 1, pad=(1, 1, 1))
    draw_6conn_line(grid, (cx_r, 5, 14), (cx_r, 3, 7), 2, pad=(1, 1, 0))
    fill_sym_box(grid, 0, 1, 3, 5, 6, 13, 1)

    # Proud Arched White Neck, Flowing Mane & Armored Head (Y: 27..40, Z: 18..33)
    draw_6conn_line(grid, (cx_r, 29, 19), (cx_r, 33, 28), 1, pad=(3, 2, 2))
    fill_sym_box(grid, 0, 2, 29, 34, 20, 29, 1)   # Arched white neck
    # Flowing silver-white mane streaming along back of neck
    for mz in range(20, 31):
        my = 27 + (mz - 20) // 3
        fill_sym_box(grid, 0, 0, my - 1, my, mz, mz, 2 if (mz % 2 == 0) else 1)
    # Noble White Horse Head & Silver Chamfron (Y: 31..40, Z: 25..33)
    fill_sym_box(grid, 0, 2, 31, 37, 26, 30, 1)   # Cranium
    fill_sym_box(grid, 0, 1, 36, 40, 25, 28, 1)   # Tapered white muzzle
    fill_sym_box(grid, 0, 1, 39, 40, 25, 26, 2)   # Silver nose tip
    fill_sym_box(grid, 0, 0, 33, 39, 29, 30, 2)   # Silver chamfron armor plate!
    fill_sym_box(grid, 0, 0, 34, 35, 30, 31, 5)   # Gold brow crest
    fill_sym_box(grid, 2, 2, 34, 35, 28, 29, 9)   # Luminous cyan noble eyes!
    fill_sym_box(grid, 1, 2, 31, 32, 31, 33, 1)   # Pointed white ears!
    fill_sym_box(grid, 2, 2, 32, 38, 26, 26, 5)   # Gold bridle strap
    fill_sym_box(grid, 0, 1, 34, 35, 23, 24, 6)   # Crimson throat tassel!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


def export_vox(grid, filename):
    X, Y, Z = grid.shape
    xs, ys, zs = np.nonzero(grid)
    voxels = [(int(x), int(y), int(z), int(grid[x, y, z])) for x, y, z in zip(xs, ys, zs)]
    size_content = struct.pack('<III', X, Y, Z)
    size_chunk = b'SIZE' + struct.pack('<II', len(size_content), 0) + size_content
    xyzi_content = bytearray(struct.pack('<I', len(voxels)))
    for vx, vy, vz, vc in voxels:
        xyzi_content += struct.pack('<BBBB', vx, vy, vz, vc)
    xyzi_chunk = b'XYZI' + struct.pack('<II', len(xyzi_content), 0) + bytes(xyzi_content)
    rgba_content = bytearray(256 * 4)
    for idx, (r, g, b, a) in PALETTE.items():
        offset = (idx - 1) * 4
        rgba_content[offset:offset + 4] = struct.pack('<BBBB', r, g, b, a)
    rgba_chunk = b'RGBA' + struct.pack('<II', len(rgba_content), 0) + bytes(rgba_content)
    children = size_chunk + xyzi_chunk + rgba_chunk
    main_chunk = b'MAIN' + struct.pack('<II', 0, len(children)) + children
    with open(filename, 'wb') as f:
        f.write(b'VOX ' + struct.pack('<I', 150) + main_chunk)
    return len(voxels)


def shade_color(rgba, factor):
    r, g, b, a = rgba
    return (int(min(255, r * factor)), int(min(255, g * factor)), int(min(255, b * factor)), a)


def render_voxel_iso(grid, yaw_deg=35, pitch_deg=25, scale=None, img_size=(386, 266), margin=12):
    img = Image.new("RGBA", img_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    X, Y, Z = grid.shape
    xs, ys, zs = np.nonzero(grid)
    if len(xs) == 0:
        return img
    cx, cy, cz = (xs.min() + xs.max() + 1) / 2.0, (ys.min() + ys.max() + 1) / 2.0, (zs.min() + zs.max() + 1) / 2.0
    yaw, pitch = np.radians(yaw_deg), np.radians(pitch_deg)
    cos_y, sin_y, cos_p, sin_p = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)

    def project_unit(x, y, z):
        dx, dy, dz = x - cx, y - cy, z - cz
        rx = -dx * cos_y + dy * sin_y
        ry = dx * sin_y + dy * cos_y
        return rx, ry * sin_p - dz * cos_p, ry * cos_p + dz * sin_p

    corners = [(x, y, z) for x in (xs.min(), xs.max() + 1) for y in (ys.min(), ys.max() + 1) for z in (zs.min(), zs.max() + 1)]
    proj_c = [project_unit(x, y, z) for x, y, z in corners]
    min_rx, max_rx = min(p[0] for p in proj_c), max(p[0] for p in proj_c)
    min_sy, max_sy = min(p[1] for p in proj_c), max(p[1] for p in proj_c)
    if scale is None:
        scale = min((img_size[0] - 2 * margin) / max(1e-5, max_rx - min_rx),
                    (img_size[1] - 2 * margin) / max(1e-5, max_sy - min_sy), 9.5)
    ox = img_size[0] / 2.0 - ((min_rx + max_rx) / 2.0) * scale
    oy = img_size[1] / 2.0 - ((min_sy + max_sy) / 2.0) * scale

    def project(x, y, z):
        rx, sy, depth = project_unit(x, y, z)
        return (rx * scale + ox, sy * scale + oy), depth

    visible = []
    for x, y, z in zip(xs, ys, zs):
        x, y, z = int(x), int(y), int(z)
        if (0 < x < X - 1 and 0 < y < Y - 1 and 0 < z < Z - 1 and
                grid[x - 1, y, z] and grid[x + 1, y, z] and grid[x, y - 1, z] and
                grid[x, y + 1, z] and grid[x, y, z - 1] and grid[x, y, z + 1]):
            continue
        _, d = project(x + 0.5, y + 0.5, z + 0.5)
        visible.append((d, x, y, z, int(grid[x, y, z])))
    visible.sort(key=lambda item: item[0])

    faces = [
        ([(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (0, 0, 1), 1.08),
        ([(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)], (0, 0, -1), 0.55),
        ([(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], (0, -1, 0), 0.76),
        ([(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)], (0, 1, 0), 0.94),
        ([(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)], (-1, 0, 0), 0.80),
        ([(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (1, 0, 0), 0.88),
    ]
    vx_dir, vy_dir, vz_dir = sin_y * cos_p, cos_y * cos_p, sin_p
    for _, x, y, z, c in visible:
        base_col = PALETTE[c]
        for verts, normal, light in faces:
            nx, ny, nz = normal
            nnx, nny, nnz = x + nx, y + ny, z + nz
            if 0 <= nnx < X and 0 <= nny < Y and 0 <= nnz < Z and grid[nnx, nny, nnz] > 0:
                continue
            if nx * vx_dir + ny * vy_dir + nz * vz_dir <= 1e-6:
                continue
            poly = [project(x + vx, y + vy, z + vz)[0] for vx, vy, vz in verts]
            fcol = shade_color(base_col, light)
            draw.polygon(poly, fill=fcol, outline=shade_color(fcol, 0.85))
    return img


def render_preview_3(forms, title_banner, out_path):
    cw, ch = 1274, 540
    canvas = Image.new("RGBA", (cw, ch), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, cw, 20):
        draw.line([(gx, 0), (gx, ch)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, ch, 20):
        draw.line([(0, gy), (cw, gy)], fill=(28, 34, 48, 255), width=1)
    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(forms):
        bx, by, w, h = 24 + idx * 414, 48, 398, 468
        draw.rectangle([bx, by, bx + w, by + h], fill=(14, 17, 24, 255), outline=(65, 80, 110, 255), width=2)
        draw.text((bx + 14, by + 12), label, fill=(235, 240, 255, 255))
        gx, gy, gz = m_grid.shape
        draw.text((bx + 14, by + 30), f"Grid: {gx}x{gy}x{gz} | Voxels: {v_cnt}", fill=(130, 155, 195, 255))
        r_front = render_voxel_iso(m_grid, yaw_deg=yaw, pitch_deg=pitch, img_size=(386, 266), margin=12)
        canvas.paste(r_front, (bx + 6, by + 48), r_front)
        rx0, ry0 = bx + 242, by + 318
        draw.rectangle([rx0, ry0, rx0 + 146, ry0 + 140], fill=(20, 24, 34, 255), outline=(50, 62, 85, 255))
        r_rear = render_voxel_iso(m_grid, yaw_deg=yaw + 170, pitch_deg=pitch, img_size=(140, 120), margin=8)
        canvas.paste(r_rear, (rx0 + 3, ry0 + 16), r_rear)
        draw.text((rx0 + 8, ry0 + 5), "REAR VIEW", fill=(120, 140, 175, 255))
        draw.text((bx + 14, by + 406), f"Z-Slices: {gz} layers", fill=(160, 180, 210, 255))
        for pi in range(1, len(PALETTE) + 1):
            px0, py0 = bx + 14 + (pi - 1) * 20, by + 430
            draw.rectangle([px0, py0, px0 + 15, py0 + 15], fill=PALETTE[pi], outline=(70, 82, 105, 255))
    canvas.save(out_path)


if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "zhaoyun_a.vox")
    v_b = export_vox(model_b, "zhaoyun_b.vox")
    v_c = export_vox(model_c, "zhaoyun_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview_3(
        [
            ("1. ZHAO YUN (CHARACTER)", model_a, v_a, 28, 18),
            ("2. ZHAO YUN ROBOT", model_b, v_b, 28, 18),
            ("3. WHITE HORSE (BEAST)", model_c, v_c, 52, 20),
        ],
        "THREE KINGDOMS #04: ZHAO YUN - CHARACTER / ROBOT / WHITE HORSE",
        "preview_zhaoyun.png",
    )
    print(f"zhaoyun: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
