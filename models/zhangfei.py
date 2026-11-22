import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Zhang Fei (張飛) -> Burly Black-Iron Juggernaut Robot!
# Black-dominant (黒基調), sturdy heavy build (がっしりした体格), wavy Serpent Spear (蛇矛)!
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
    # Iconic wavy zigzag serpent-blade!
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
# FORM A: ZHANG FEI CHARACTER FIGURE (BURLY BLACK-ARMORED GENERAL) (40 x 24 x 44)
# ============================================================
def build_a():
    grid = np.zeros((40, 24, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 19
    cx_r = X // 2      # 20

    # Heavy Wide Stance Boots & Thick Legs (がっしりした体格!) (Z: 0..15)
    fill_sym_box(grid, 3, 6, 9, 16, 0, 2, 1)      # Heavy black boots
    fill_sym_box(grid, 3, 6, 15, 16, 0, 1, 4)     # Brass toe trim
    fill_sym_box(grid, 3, 5, 10, 15, 3, 14, 1)    # Thick black armored leggings
    fill_sym_box(grid, 4, 5, 14, 15, 5, 12, 2)    # Gunmetal shin guards
    fill_sym_box(grid, 3, 5, 14, 16, 11, 13, 4)   # Brass knee bosses

    # Broad Barrel Waist & Black Scale-Armor Skirt (Z: 14..21)
    fill_sym_box(grid, 0, 6, 9, 15, 14, 20, 1)    # Broad black armor waist
    fill_sym_box(grid, 0, 6, 15, 16, 14, 15, 4)   # Brass hem
    fill_sym_box(grid, 0, 6, 15, 16, 18, 20, 3)   # Wide crimson battle sash!
    fill_sym_box(grid, 0, 1, 16, 16, 18, 20, 4)   # Brass lion belt buckle

    # Massive Burly Black-Scale Chest & Broad Shoulders (Z: 20..30)
    fill_sym_box(grid, 0, 6, 9, 16, 20, 29, 1)    # Massive broad black cuirass!
    fill_sym_box(grid, 1, 5, 16, 16, 22, 28, 2)   # Gunmetal scale plates
    fill_sym_box(grid, 0, 2, 16, 17, 25, 27, 4)   # Brass beast-head breastplate boss!
    fill_sym_box(grid, 2, 5, 10, 15, 29, 30, 3)   # Crimson collar trim
    # Rear dark cape (Y: 7..9, Z: 8..29)
    fill_sym_box(grid, 0, 5, 7, 8, 8, 28, 1)
    fill_sym_box(grid, 0, 5, 7, 7, 8, 9, 3)

    # Thick Burly Arms & Wavy Serpent Spear! (Z: 15..30)
    fill_sym_box(grid, 6, 9, 10, 15, 25, 30, 1)   # Broad black shoulder pauldrons
    fill_sym_box(grid, 8, 9, 11, 14, 29, 30, 4)   # Brass shoulder spikes
    fill_box(grid, cx_l - 9, cx_l - 6, 10, 14, 17, 24, 2)  # Left thick arm
    fill_box(grid, cx_l - 9, cx_l - 7, 11, 14, 15, 16, 7)  # Clenched fist
    fill_box(grid, cx_r + 6, cx_r + 9, 10, 15, 18, 24, 2)  # Right thick arm
    fill_box(grid, cx_r + 8, cx_r + 11, 14, 17, 17, 20, 7) # Gripping hand!
    draw_serpent_spear(grid, cx_r + 12, 16, z_bot=2, z_top=42)

    # Fierce Head, Wild Bristly Black Beard & Horned Warrior Headband! (Z: 30..39)
    fill_sym_box(grid, 0, 3, 10, 15, 30, 36, 7)   # Rugged face
    # Wild flaring bristly black beard & fierce whiskers!
    fill_sym_box(grid, 0, 4, 14, 17, 28, 32, 1)
    fill_sym_box(grid, 3, 5, 13, 16, 30, 33, 1)   # Flaring side-whiskers!
    fill_sym_box(grid, 1, 2, 15, 16, 33, 34, 1)   # Fierce thick black brows
    fill_sym_box(grid, 1, 2, 16, 16, 33, 33, 9)   # Fiery glaring eyes!
    # Wild spiky black hair & brass-crimson warrior headband!
    fill_sym_box(grid, 0, 4, 9, 15, 35, 38, 1)
    fill_sym_box(grid, 0, 3, 15, 16, 35, 36, 3)   # Crimson war headband
    fill_sym_box(grid, 0, 1, 16, 16, 36, 38, 4)   # Brass brow badge

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: ZHANG FEI BURLY BLACK-IRON JUGGERNAUT ROBOT (48 x 26 x 46)
# ============================================================
def build_b():
    grid = np.zeros((48, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # Heavy Tank-Like Black-Iron Boots & Massive Legs (Z: 0..16)
    fill_sym_box(grid, 3, 7, 9, 17, 0, 2, 1)      # Colossal black iron boots
    fill_sym_box(grid, 4, 6, 17, 19, 0, 2, 2)     # Heavy ramming toes
    fill_sym_box(grid, 4, 6, 18, 19, 2, 2, 4)     # Brass toe trim
    fill_sym_box(grid, 3, 7, 10, 15, 3, 14, 1)    # Massive black greaves!
    fill_sym_box(grid, 4, 6, 15, 16, 4, 13, 2)    # Gunmetal front armor
    fill_sym_box(grid, 7, 7, 11, 14, 5, 12, 3)    # Crimson leg war-stripe
    fill_sym_box(grid, 3, 7, 15, 18, 12, 15, 2)   # Spiked juggernaut knee armor!
    fill_sym_box(grid, 4, 6, 18, 18, 13, 14, 4)

    # Broad Armored Pelvis & Heavy Waist Skirt (Z: 15..23)
    fill_sym_box(grid, 3, 6, 10, 15, 15, 19, 2)
    fill_sym_box(grid, 0, 6, 10, 15, 19, 22, 1)
    fill_sym_box(grid, 2, 7, 15, 17, 17, 21, 1)   # Heavy black front tassets
    fill_sym_box(grid, 2, 7, 17, 17, 19, 19, 3)   # Crimson waist belt!
    fill_sym_box(grid, 6, 8, 10, 15, 17, 21, 2)   # Bulky hip armor
    fill_sym_box(grid, 0, 2, 16, 18, 18, 22, 3)   # Crimson codpiece
    fill_sym_box(grid, 0, 1, 18, 18, 20, 21, 4)   # Brass buckle

    # Massive Broad-Chested Black-Iron Cuirass (Z: 22..34)
    fill_sym_box(grid, 0, 5, 10, 15, 22, 24, 2)
    fill_sym_box(grid, 0, 8, 9, 17, 25, 33, 1)    # Massive juggernaut chest!
    fill_sym_box(grid, 2, 7, 17, 18, 26, 32, 2)   # Heavy angled pectoral plates
    fill_sym_box(grid, 0, 2, 17, 19, 27, 31, 3)   # Crimson center chest core!
    fill_sym_box(grid, 0, 1, 19, 19, 28, 30, 4)   # Brass fierce beast-emblem
    fill_sym_box(grid, 0, 0, 19, 19, 29, 29, 9)   # Glowing fiery chest eye!
    fill_sym_box(grid, 0, 6, 6, 9, 24, 33, 1)     # Heavy rear booster backpack
    fill_sym_box(grid, 2, 5, 5, 6, 25, 31, 2)

    # Colossal Spiked Black-Iron Shoulder Pauldrons & Heavy Arms + Serpent Spear! (Z: 14..38)
    fill_sym_box(grid, 8, 10, 11, 15, 28, 33, 2)
    fill_sym_box(grid, 9, 14, 10, 16, 28, 35, 1)  # Massive black pauldrons!
    fill_sym_box(grid, 10, 14, 10, 16, 34, 35, 2)
    fill_sym_box(grid, 14, 14, 11, 15, 30, 32, 3) # Crimson side accent
    # Twin brass shoulder spikes jutting outward!
    draw_6conn_line(grid, (cx_r + 12, 13, 35), (cx_r + 15, 13, 38), 4)
    draw_6conn_line(grid, (cx_l - 12, 13, 35), (cx_l - 15, 13, 38), 4)
    # Massive arms
    fill_sym_box(grid, 9, 11, 11, 15, 22, 27, 2)
    fill_box(grid, cx_l - 13, cx_l - 9, 11, 16, 15, 21, 1)  # Heavy left gauntlet
    fill_box(grid, cx_l - 13, cx_l - 13, 12, 15, 16, 20, 4) # Brass knuckle-guard
    fill_box(grid, cx_l - 12, cx_l - 9, 12, 15, 13, 15, 2)
    fill_box(grid, cx_r + 9, cx_r + 13, 11, 16, 16, 21, 1)  # Right gauntlet
    fill_box(grid, cx_r + 11, cx_r + 14, 15, 19, 15, 19, 2) # Gripping iron fist!
    draw_serpent_spear(grid, cx_r + 15, 18, z_bot=2, z_top=45)

    # Fierce Black-Iron Horned Demon-General Head & Jagged Beard-Mask! (Z: 34..45)
    fill_sym_box(grid, 0, 2, 11, 15, 34, 35, 2)
    fill_sym_box(grid, 0, 3, 10, 16, 35, 41, 1)   # Black iron helmet
    # Jagged bristly black-iron beard-plate menpo!
    fill_sym_box(grid, 0, 4, 15, 18, 34, 37, 1)
    fill_sym_box(grid, 2, 4, 16, 18, 35, 36, 8)   # Steel jaw-fang vents!
    fill_sym_box(grid, 1, 2, 17, 17, 38, 39, 9)   # Blazing fiery-orange fierce eyes!
    fill_sym_box(grid, 0, 3, 15, 18, 40, 40, 3)   # Crimson fierce brow band!
    # Sweeping brass war-horns on helmet!
    draw_6conn_line(grid, (cx_r + 2, 16, 40), (cx_r + 6, 15, 45), 4)
    draw_6conn_line(grid, (cx_l - 2, 16, 40), (cx_l - 6, 15, 45), 4)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=28, pitch_a=18, yaw_b=28, pitch_b=18):
    canvas = Image.new("RGBA", (860, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, 860, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (860, gy)], fill=(28, 34, 48, 255), width=1)
    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate([(label_a, grid_a, v_a, yaw_a, pitch_a), (label_b, grid_b, v_b, yaw_b, pitch_b)]):
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
        for pi in range(1, 10):
            px0, py0 = bx + 14 + (pi - 1) * 20, by + 430
            draw.rectangle([px0, py0, px0 + 15, py0 + 15], fill=PALETTE[pi], outline=(70, 82, 105, 255))
    canvas.save(out_path)


if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    v_a = export_vox(model_a, "zhangfei_a.vox")
    v_b = export_vox(model_b, "zhangfei_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #02: ZHANG FEI (THREE KINGDOMS) -> BLACK-IRON ROBOT",
        "1. ZHANG FEI (CHARACTER)",
        "2. ZHANG FEI ROBOT",
        "preview_zhangfei.png",
        yaw_a=28, pitch_a=18, yaw_b=28, pitch_b=18,
    )
    print(f"zhangfei: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
