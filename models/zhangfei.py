import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Zhang Fei (張飛) -> Burly Black-Iron Juggernaut Robot -> Giant Black Serpent (大蛇)!
PALETTE = {
    1: (30, 32, 40, 255),     # Jet-Black Iron Armor & Wild Bristly Beard (黒基調)
    2: (68, 72, 86, 255),     # Forged Dark-Gunmetal Armor Bevels
    3: (196, 38, 42, 255),    # Fierce Crimson Battle Sash & Under-Tunic
    4: (234, 184, 52, 255),   # Burnished Brass-Gold Studs & Trim
    5: (218, 224, 234, 255),  # Honed Silver Wavy Serpent Spear Blade (蛇矛)
    6: (118, 74, 42, 255),    # Dark Hardwood Spear Shaft & Leather Straps
    7: (218, 174, 144, 255),  # Tanned Rugged Warrior Face
    8: (126, 134, 148, 255),  # Brushed Steel Armor Rivets
    9: (255, 132, 34, 255),   # Blazing Fiery-Orange Fierce Eyes
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


def draw_serpent_spear(grid, sx, sy, z_bot, z_top):
    """Draw Zhang Fei's iconic Wavy Serpent Spear (丈八蛇矛)."""
    fill_box(grid, sx, sx, sy, sy, z_bot, z_top - 12, 6)       # Heavy spear shaft
    fill_box(grid, sx, sx, sy, sy, z_bot, z_bot + 1, 4)        # Brass butt-cap
    fill_box(grid, sx - 1, sx + 1, sy, sy, z_top - 13, z_top - 12, 4)  # Brass guard collar
    fill_box(grid, sx, sx, sy - 1, sy - 1, z_top - 16, z_top - 13, 3)  # Crimson spear tassel
    pts = [
        (sx,     sy, z_top - 12),
        (sx + 1, sy, z_top - 9),
        (sx - 1, sy, z_top - 6),
        (sx + 1, sy, z_top - 3),
        (sx,     sy, z_top),
    ]
    for i in range(len(pts) - 1):
        draw_6conn_line(grid, pts[i], pts[i + 1], 5)


# ============================================================
# FORM A: ZHANG FEI CHARACTER FIGURE (40 x 24 x 44) [UNCHANGED]
# ============================================================
def build_a():
    grid = np.zeros((40, 24, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 19
    cx_r = X // 2      # 20

    fill_sym_box(grid, 3, 6, 9, 16, 0, 2, 1)
    fill_sym_box(grid, 3, 6, 15, 16, 0, 1, 4)
    fill_sym_box(grid, 3, 5, 10, 15, 3, 14, 1)
    fill_sym_box(grid, 4, 5, 14, 15, 5, 12, 2)
    fill_sym_box(grid, 3, 5, 14, 16, 11, 13, 4)

    fill_sym_box(grid, 0, 6, 9, 15, 14, 20, 1)
    fill_sym_box(grid, 0, 6, 15, 16, 14, 15, 4)
    fill_sym_box(grid, 0, 6, 15, 16, 18, 20, 3)
    fill_sym_box(grid, 0, 1, 16, 16, 18, 20, 4)

    fill_sym_box(grid, 0, 6, 9, 16, 20, 29, 1)
    fill_sym_box(grid, 1, 5, 16, 16, 22, 28, 2)
    fill_sym_box(grid, 0, 2, 16, 17, 25, 27, 4)
    fill_sym_box(grid, 2, 5, 10, 15, 29, 30, 3)
    fill_sym_box(grid, 0, 5, 7, 8, 8, 28, 1)
    fill_sym_box(grid, 0, 5, 7, 7, 8, 9, 3)

    fill_sym_box(grid, 6, 9, 10, 15, 25, 30, 1)
    fill_sym_box(grid, 8, 9, 11, 14, 29, 30, 4)
    fill_box(grid, cx_l - 9, cx_l - 6, 10, 14, 17, 24, 2)
    fill_box(grid, cx_l - 9, cx_l - 7, 11, 14, 15, 16, 7)
    fill_box(grid, cx_r + 6, cx_r + 9, 10, 15, 18, 24, 2)
    fill_box(grid, cx_r + 8, cx_r + 11, 14, 17, 17, 20, 7)
    draw_serpent_spear(grid, cx_r + 12, 16, z_bot=2, z_top=42)

    fill_sym_box(grid, 0, 3, 10, 15, 30, 36, 7)
    fill_sym_box(grid, 0, 4, 14, 17, 28, 32, 1)
    fill_sym_box(grid, 3, 5, 13, 16, 30, 33, 1)
    fill_sym_box(grid, 1, 2, 15, 16, 33, 34, 1)
    fill_sym_box(grid, 1, 2, 16, 16, 33, 33, 9)
    fill_sym_box(grid, 0, 4, 9, 15, 35, 38, 1)
    fill_sym_box(grid, 0, 3, 15, 16, 35, 36, 3)
    fill_sym_box(grid, 0, 1, 16, 16, 36, 38, 4)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: ZHANG FEI BURLY BLACK-IRON ROBOT (48 x 26 x 46) [UNCHANGED]
# ============================================================
def build_b():
    grid = np.zeros((48, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    fill_sym_box(grid, 3, 7, 9, 17, 0, 2, 1)
    fill_sym_box(grid, 4, 6, 17, 19, 0, 2, 2)
    fill_sym_box(grid, 4, 6, 18, 19, 2, 2, 4)
    fill_sym_box(grid, 3, 7, 10, 15, 3, 14, 1)
    fill_sym_box(grid, 4, 6, 15, 16, 4, 13, 2)
    fill_sym_box(grid, 7, 7, 11, 14, 5, 12, 3)
    fill_sym_box(grid, 3, 7, 15, 18, 12, 15, 2)
    fill_sym_box(grid, 4, 6, 18, 18, 13, 14, 4)

    fill_sym_box(grid, 3, 6, 10, 15, 15, 19, 2)
    fill_sym_box(grid, 0, 6, 10, 15, 19, 22, 1)
    fill_sym_box(grid, 2, 7, 15, 17, 17, 21, 1)
    fill_sym_box(grid, 2, 7, 17, 17, 19, 19, 3)
    fill_sym_box(grid, 6, 8, 10, 15, 17, 21, 2)
    fill_sym_box(grid, 0, 2, 16, 18, 18, 22, 3)
    fill_sym_box(grid, 0, 1, 18, 18, 20, 21, 4)

    fill_sym_box(grid, 0, 5, 10, 15, 22, 24, 2)
    fill_sym_box(grid, 0, 8, 9, 17, 25, 33, 1)
    fill_sym_box(grid, 2, 7, 17, 18, 26, 32, 2)
    fill_sym_box(grid, 0, 2, 17, 19, 27, 31, 3)
    fill_sym_box(grid, 0, 1, 19, 19, 28, 30, 4)
    fill_sym_box(grid, 0, 0, 19, 19, 29, 29, 9)
    fill_sym_box(grid, 0, 6, 6, 9, 24, 33, 1)
    fill_sym_box(grid, 2, 5, 5, 6, 25, 31, 2)

    fill_sym_box(grid, 8, 10, 11, 15, 28, 33, 2)
    fill_sym_box(grid, 9, 14, 10, 16, 28, 35, 1)
    fill_sym_box(grid, 10, 14, 10, 16, 34, 35, 2)
    fill_sym_box(grid, 14, 14, 11, 15, 30, 32, 3)
    draw_6conn_line(grid, (cx_r + 12, 13, 35), (cx_r + 15, 13, 38), 4)
    draw_6conn_line(grid, (cx_l - 12, 13, 35), (cx_l - 15, 13, 38), 4)
    fill_sym_box(grid, 9, 11, 11, 15, 22, 27, 2)
    fill_box(grid, cx_l - 13, cx_l - 9, 11, 16, 15, 21, 1)
    fill_box(grid, cx_l - 13, cx_l - 13, 12, 15, 16, 20, 4)
    fill_box(grid, cx_l - 12, cx_l - 9, 12, 15, 13, 15, 2)
    fill_box(grid, cx_r + 9, cx_r + 13, 11, 16, 16, 21, 1)
    fill_box(grid, cx_r + 11, cx_r + 14, 15, 19, 15, 19, 2)
    draw_serpent_spear(grid, cx_r + 15, 18, z_bot=2, z_top=45)

    fill_sym_box(grid, 0, 2, 11, 15, 34, 35, 2)
    fill_sym_box(grid, 0, 3, 10, 16, 35, 41, 1)
    fill_sym_box(grid, 0, 4, 15, 18, 34, 37, 1)
    fill_sym_box(grid, 2, 4, 16, 18, 35, 36, 8)
    fill_sym_box(grid, 1, 2, 17, 17, 38, 39, 9)
    fill_sym_box(grid, 0, 3, 15, 18, 40, 40, 3)
    draw_6conn_line(grid, (cx_r + 2, 16, 40), (cx_r + 6, 15, 45), 4)
    draw_6conn_line(grid, (cx_l - 2, 16, 40), (cx_l - 6, 15, 45), 4)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: GIANT BLACK SERPENT (大蛇: 黒い大きな蛇) (34 x 34 x 34)
# ============================================================
def build_c():
    grid = np.zeros((34, 34, 34), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx, cy = 17, 16

    # Massive Coiled Black Serpent Base (2 thick grounded coils, Z: 0..14)
    pts = []
    n_steps = 50
    for i in range(n_steps + 1):
        t = i / n_steps
        ang = t * 2.15 * np.pi - 0.3 * np.pi
        if t < 0.72:
            rad = 11.2 - 3.5 * t
            z = 2.0 + 13.0 * (t / 0.72)
        else:
            u = (t - 0.72) / 0.28
            rad = 8.6 * (1.0 - 0.85 * u)
            z = 15.0 + 13.5 * u
        x = cx + rad * np.cos(ang)
        y = cy + rad * np.sin(ang) - (2.0 * max(0.0, t - 0.72))
        pts.append((x, y, z))

    for i in range(len(pts) - 1):
        t = i / len(pts)
        pad_r = (2, 2, 2) if t < 0.65 else (2, 2, 1)
        col = 1 if (i % 4 != 0) else 2
        draw_6conn_line(grid, pts[i], pts[i + 1], col, pad=pad_r)
        # Gunmetal & brass scale ribs along lower belly
        if i % 3 == 0:
            px_, py_, pz_ = int(round(pts[i][0])), int(round(pts[i][1])), int(round(pts[i][2]))
            fill_box(grid, px_ - 1, px_ + 1, py_ + 2, py_ + 2, max(0, pz_ - 1), pz_, 4 if (i % 6 == 0) else 2)

    # Ensure lower coil rests firmly at Z=0
    for i in range(18):
        px_, py_ = int(round(pts[i][0])), int(round(pts[i][1]))
        fill_box(grid, px_ - 2, px_ + 2, py_ - 2, py_ + 2, 0, 1, 1)

    # Tapered rattling tail curling out on the side
    t0 = pts[0]
    draw_6conn_line(grid, t0, (t0[0] + 4, t0[1] - 5, 1), 1, pad=(1, 1, 0))
    draw_6conn_line(grid, (t0[0] + 4, t0[1] - 5, 1), (t0[0] + 6, t0[1] - 7, 3), 4)

    # Flaring Crimson-and-Black Cobra/Viper Hood behind Upright Neck (Z: 17..28)
    draw_6conn_line(grid, pts[-1], (cx, 15, 27), 1, pad=(2, 2, 1))
    fill_box(grid, cx - 7, cx + 7, 13, 15, 19, 26, 1)    # Wide menacing black hood!
    fill_box(grid, cx - 6, cx + 6, 15, 16, 20, 25, 3)    # Fierce crimson inner hood markings!
    fill_box(grid, cx - 3, cx + 3, 16, 17, 19, 25, 4)    # Brass scale belly on neck
    fill_box(grid, cx - 5, cx + 5, 14, 15, 27, 28, 1)

    # Fierce Giant Serpent Head lunging forward (+Y, Z: 25..33)
    fill_box(grid, cx - 4, cx + 4, 15, 22, 26, 31, 1)    # Broad triangular viper skull
    fill_box(grid, cx - 3, cx + 3, 22, 27, 28, 30, 1)    # Upper jaw
    fill_box(grid, cx - 3, cx + 3, 21, 26, 25, 26, 2)    # Open lower jaw!
    fill_box(grid, cx - 2, cx + 2, 22, 25, 26, 27, 3)    # Crimson mouth interior
    fill_box(grid, cx - 3, cx - 3, 25, 25, 26, 28, 5)    # Gleaming silver serpent fangs!
    fill_box(grid, cx + 3, cx + 3, 25, 25, 26, 28, 5)
    # Blazing fiery-orange eyes & brass horn-brows!
    fill_box(grid, cx - 4, cx - 4, 20, 21, 29, 30, 9)
    fill_box(grid, cx + 4, cx + 4, 20, 21, 29, 30, 9)
    fill_box(grid, cx - 4, cx - 3, 19, 21, 31, 32, 4)    # Brass brow horns
    fill_box(grid, cx + 3, cx + 4, 19, 21, 31, 32, 4)
    # Iconic crimson forked tongue darting out!
    draw_6conn_line(grid, (cx, 25, 26), (cx, 30, 25), 3)
    draw_6conn_line(grid, (cx, 30, 25), (cx - 2, 32, 24), 3)
    draw_6conn_line(grid, (cx, 30, 25), (cx + 2, 32, 24), 3)

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
    v_a = export_vox(model_a, "zhangfei_a.vox")
    v_b = export_vox(model_b, "zhangfei_b.vox")
    v_c = export_vox(model_c, "zhangfei_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview_3(
        [
            ("1. ZHANG FEI (CHARACTER)", model_a, v_a, 28, 18),
            ("2. ZHANG FEI ROBOT", model_b, v_b, 28, 18),
            ("3. GIANT SERPENT (BEAST)", model_c, v_c, 32, 22),
        ],
        "THREE KINGDOMS #02: ZHANG FEI - CHARACTER / ROBOT / GIANT SERPENT",
        "preview_zhangfei.png",
    )
    print(f"zhangfei: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
