import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Bull Demon King / Gyumao (牛魔王) -> Towering Minotaur Boss Robot!
# Giant curving bull horns (大きな牛の角), heavy iron club (混鉄棍), extra large imposing build (ひときわ大柄)!
PALETTE = {
    1: (48, 36, 38, 255),     # Deep Charcoal-Ox Hide & Dark Armor
    2: (84, 62, 60, 255),     # Warm Dark-Brown Bull Fur & Inner Plates
    3: (188, 32, 34, 255),    # Fiery Crimson Demon-King Cloak & Trim
    4: (242, 194, 46, 255),   # Heavy Imperial Gold Armor Trim & Nose Ring!
    5: (244, 238, 224, 255),  # Massive Sweeping Ivory Bull Horns (大きな牛の角!)
    6: (196, 186, 168, 255),  # Horn Base Shading
    7: (66, 72, 86, 255),     # Heavy Forged Iron Kontetsu-kon Club (混鉄棍!)
    8: (132, 140, 158, 255),  # Iron Club Spikes & Trim
    9: (255, 86, 36, 255),    # Blazing Fiery-Orange Demon-Bull Eyes!
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


def draw_6conn_line(grid, p0, p1, col, pad=(0, 0, 0)):
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


def draw_bull_horns(grid, cx_l, cx_r, y_base, z_base, span_x=10, rise_z=9):
    """Draw massive sweeping ivory bull horns (大きな牛の角!)."""
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        p0 = (bx + sign * 3, y_base, z_base)
        p1 = (bx + sign * (span_x - 2), y_base + 1, z_base + 1)
        p2 = (bx + sign * span_x, y_base + 3, z_base + rise_z * 0.6)
        p3 = (bx + sign * (span_x - 2), y_base + 4, z_base + rise_z)
        draw_6conn_line(grid, p0, p1, 6, pad=(0, 1, 1))
        draw_6conn_line(grid, p1, p2, 5, pad=(0, 0, 1))
        draw_6conn_line(grid, p2, p3, 5, pad=(0, 0, 0))


def draw_iron_club(grid, hx, hy, z_bot, z_top):
    """Draw Gyumao's massive Kontetsu-kon Iron Club (混鉄棍 — heavy studded iron rod!)."""
    fill_box(grid, hx, hx + 1, hy, hy + 1, z_bot + 2, z_top - 2, 7)
    fill_box(grid, hx, hx + 1, hy, hy + 1, z_bot, z_bot + 1, 4)     # Gold end band
    fill_box(grid, hx, hx + 1, hy, hy + 1, z_top - 1, z_top, 4)     # Gold top band
    # Heavy iron studs along upper club!
    for sz in range(z_top - 11, z_top - 2, 3):
        fill_box(grid, hx - 1, hx + 2, hy, hy + 1, sz, sz, 8)
        fill_box(grid, hx, hx + 1, hy - 1, hy + 2, sz, sz, 8)


# ============================================================
# FORM A: GYUMAO / BULL DEMON KING CHARACTER (EXTRA LARGE!) (46 x 26 x 50)
# ============================================================
def build_a():
    grid = np.zeros((46, 26, 50), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 22
    cx_r = X // 2      # 23

    # Heavy Cloven-Hoof War Boots & Thick Legs (Z: 0..15)
    fill_sym_box(grid, 3, 5, 11, 16, 0, 2, 1)
    fill_sym_box(grid, 3, 5, 16, 17, 0, 1, 6)     # Cloven bull hooves!
    fill_sym_box(grid, 3, 5, 12, 15, 3, 14, 1)
    fill_sym_box(grid, 4, 5, 15, 15, 4, 13, 4)
    fill_sym_box(grid, 3, 5, 15, 16, 12, 14, 3)

    # Massive Broad Torso, Heavy Golden Armor & Flowing Crimson Cape (Z: 15..32)
    fill_sym_box(grid, 0, 6, 11, 16, 15, 21, 1)
    fill_sym_box(grid, 0, 6, 16, 17, 17, 20, 3)   # Broad crimson waistcloth
    fill_sym_box(grid, 0, 2, 17, 17, 18, 20, 4)   # Heavy gold bull buckle
    fill_sym_box(grid, 0, 6, 11, 16, 22, 32, 2)   # Broad muscular dark-brown chest!
    fill_sym_box(grid, 1, 5, 16, 17, 23, 30, 4)   # Massive golden demon-king breastplate
    fill_sym_box(grid, 0, 2, 17, 17, 25, 28, 3)
    # Flowing Crimson Demon-King Cloak on Back (Y: 9..10, Z: 7..31)
    fill_sym_box(grid, 0, 6, 10, 10, 7, 31, 3)
    fill_sym_box(grid, 0, 6, 9, 10, 7, 8, 4)

    # Huge Shoulders, Thick Arms & Heavy Iron KONTETSU-KON Club! (Z: 16..45)
    fill_sym_box(grid, 6, 9, 11, 16, 27, 32, 4)   # Heavy gold shoulder armor
    fill_sym_box(grid, 8, 9, 12, 15, 29, 31, 3)
    fill_box(grid, cx_l - 9, cx_l - 6, 12, 15, 19, 26, 2)
    fill_box(grid, cx_l - 9, cx_l - 6, 12, 15, 17, 18, 1)
    fill_box(grid, cx_r + 6, cx_r + 9, 12, 15, 20, 26, 2)
    fill_box(grid, cx_r + 8, cx_r + 11, 15, 18, 19, 21, 1)  # Massive hand gripping club
    draw_iron_club(grid, cx_r + 11, 17, z_bot=2, z_top=43)

    # Fierce Bull Head, Golden Nose Ring & GIGANTIC SWEEPING BULL HORNS (大きな牛の角!) (Z: 32..49)
    fill_sym_box(grid, 0, 3, 11, 17, 32, 40, 2)   # Broad bull head
    fill_sym_box(grid, 0, 2, 17, 19, 33, 35, 1)   # Dark bull muzzle
    fill_sym_box(grid, 0, 1, 19, 20, 32, 34, 4)   # ICONIC GOLDEN NOSE RING!
    fill_sym_box(grid, 2, 3, 17, 17, 37, 38, 9)   # Blazing orange demon eyes!
    fill_sym_box(grid, 0, 3, 12, 17, 39, 41, 4)   # Golden crown band
    # GIGANTIC SWEEPING IVORY BULL HORNS!
    draw_bull_horns(grid, cx_l, cx_r, y_base=14, z_base=39, span_x=10, rise_z=8)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: GYUMAO TOWERING MINOTAUR BOSS ROBOT (52 x 28 x 54)
# ============================================================
def build_b():
    grid = np.zeros((52, 28, 54), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 25
    cx_r = X // 2      # 26

    # Massive Hoof-Boots & Hulking Legs (ひときわ大柄!) (Z: 0..17)
    fill_sym_box(grid, 3, 6, 11, 18, 0, 2, 1)
    fill_sym_box(grid, 3, 6, 18, 20, 0, 2, 5)     # Ivory cloven-hoof armor toes!
    fill_sym_box(grid, 3, 6, 12, 16, 3, 15, 1)    # Towering charcoal greaves
    fill_sym_box(grid, 4, 5, 16, 17, 4, 14, 3)    # Crimson shin armor
    fill_sym_box(grid, 3, 6, 16, 18, 13, 16, 4)   # Gold spiked knee shields

    # Hulking Waist & Bull-Emblem Skirt (Z: 15..24)
    fill_sym_box(grid, 3, 5, 12, 16, 16, 20, 7)
    fill_sym_box(grid, 0, 6, 12, 16, 20, 23, 1)
    fill_sym_box(grid, 2, 6, 16, 17, 17, 22, 2)
    fill_sym_box(grid, 2, 6, 17, 17, 17, 17, 4)
    fill_sym_box(grid, 0, 2, 16, 18, 18, 23, 3)
    fill_sym_box(grid, 0, 1, 18, 18, 20, 22, 4)

    # Colossal Broad Demon-Bull Chest & Crimson Cape-Pack (Z: 23..36)
    fill_sym_box(grid, 0, 5, 12, 16, 23, 25, 7)
    fill_sym_box(grid, 0, 7, 12, 17, 26, 35, 1)   # Massive broad ox-chest!
    fill_sym_box(grid, 1, 6, 17, 18, 27, 34, 4)   # Heavy golden breastplate!
    fill_sym_box(grid, 0, 3, 18, 19, 28, 33, 3)   # Crimson demon bull crest
    fill_sym_box(grid, 0, 1, 19, 19, 30, 31, 9)   # Blazing fiery core!
    # Rear Armored Crimson Cloak
    fill_sym_box(grid, 0, 5, 9, 11, 26, 34, 7)
    fill_sym_box(grid, 0, 6, 8, 9, 11, 33, 3)
    fill_sym_box(grid, 0, 6, 8, 8, 11, 12, 4)

    # Massive Horned Bull Pauldrons & Giant KONTETSU-KON Iron Club! (Z: 15..50)
    fill_sym_box(grid, 7, 9, 12, 16, 30, 34, 7)
    fill_sym_box(grid, 8, 13, 12, 17, 29, 36, 1)  # Colossal dark pauldrons!
    fill_sym_box(grid, 9, 13, 12, 16, 35, 37, 4)  # Gold pauldron crests
    # Mini ivory bull-horns jutting from outer shoulders!
    draw_6conn_line(grid, (cx_r + 13, 14, 34), (cx_r + 16, 15, 38), 5)
    draw_6conn_line(grid, (cx_l - 13, 14, 34), (cx_l - 16, 15, 38), 5)
    # Massive arms
    fill_sym_box(grid, 8, 10, 12, 16, 22, 29, 7)
    fill_box(grid, cx_l - 12, cx_l - 8, 12, 16, 15, 22, 2)
    fill_box(grid, cx_l - 11, cx_l - 8, 13, 16, 13, 15, 1)
    fill_box(grid, cx_r + 8, cx_r + 12, 12, 16, 16, 22, 2)
    fill_box(grid, cx_r + 10, cx_r + 14, 15, 18, 16, 20, 1)
    draw_iron_club(grid, cx_r + 14, 18, z_bot=2, z_top=49)

    # Colossal Minotaur Robot Head, Golden Nose-Ring & GIGANTIC BULL HORNS! (Z: 35..53)
    fill_sym_box(grid, 0, 2, 12, 16, 35, 36, 7)
    fill_sym_box(grid, 0, 3, 12, 17, 36, 43, 1)   # Heavy horned bull helm
    fill_sym_box(grid, 0, 2, 17, 19, 36, 38, 2)   # Armored snout grill
    fill_sym_box(grid, 0, 1, 19, 20, 35, 37, 4)   # Armored Golden Nose Ring!
    fill_sym_box(grid, 1, 3, 17, 18, 39, 40, 9)   # Blazing orange visor eyes!
    fill_sym_box(grid, 0, 3, 12, 18, 42, 44, 4)   # Gold crown crest
    # COLOSSAL SWEEPING IVORY BULL HORNS!
    draw_bull_horns(grid, cx_l, cx_r, y_base=14, z_base=42, span_x=13, rise_z=10)

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
    v_a = export_vox(model_a, "gyumao_a.vox")
    v_b = export_vox(model_b, "gyumao_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #05: GYUMAO (JOURNEY TO THE WEST) -> BULL DEMON BOSS ROBOT",
        "1. GYUMAO (CHARACTER)",
        "2. GYUMAO ROBOT",
        "preview_gyumao.png",
    )
    print(f"gyumao: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
