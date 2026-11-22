import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Huang Feihu (黄飛虎) -> Martial-King Five-Colored Divine Ox Robot!
# Martial King (武成王), Five-Colored Divine Ox motif (五色神牛の意匠 — Gold/Crimson/Azure/Emerald/White!),
# commanding general build (堂々とした武将の姿)!
PALETTE = {
    1: (238, 184, 42, 255),   # Commanding Imperial-Gold Martial-King Armor (1: Gold)
    2: (196, 36, 44, 255),    # Heroic Crimson Cape & Five-Color Band (2: Red)
    3: (38, 112, 206, 255),   # Divine-Ox Azure Accent (3: Blue)
    4: (42, 168, 112, 255),   # Divine-Ox Emerald Accent (4: Green)
    5: (242, 244, 250, 255),  # Divine-Ox Pure-White Horns & Spear Blade (5: White)
    6: (52, 46, 58, 255),     # Heavy Iron Under-Armor & Boots
    7: (168, 118, 28, 255),   # Burnished Bronze-Gold Shading
    8: (248, 218, 194, 255),  # Commanding Noble General Face
    9: (106, 244, 255, 255),  # Radiant Five-Element Jewel Core & Eyes!
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


def draw_6conn_line(grid, p0, p1, col):
    X, Y, Z = grid.shape
    x0, y0, z0 = int(round(p0[0])), int(round(p0[1])), int(round(p0[2]))
    x1, y1, z1 = int(round(p1[0])), int(round(p1[1])), int(round(p1[2]))
    steps = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1) * 2
    prev = None

    def stamp(cx_, cy_, cz_):
        if 0 <= cx_ < X and 0 <= cy_ < Y and 0 <= cz_ < Z:
            grid[cx_, cy_, cz_] = col

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


def draw_golden_spear(grid, hx, hy, z_bot, z_top):
    """Draw Martial King Huang Feihu's Gilded Imperial War-Spear (金攥提蘆槍)."""
    fill_box(grid, hx, hx, hy, hy, z_bot, z_top - 8, 7)
    fill_box(grid, hx, hx, hy, hy, z_top - 10, z_top - 8, 2)  # Crimson tassel
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_top - 8, z_top - 7, 1)
    fill_box(grid, hx, hx, hy, hy, z_top - 7, z_top, 5)
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_top - 6, z_top - 4, 5)


# ============================================================
# FORM A: HUANG FEIHU (COMMANDING MARTIAL KING GENERAL) (42 x 24 x 46)
# ============================================================
def build_a():
    grid = np.zeros((42, 24, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 20
    cx_r = X // 2      # 21

    # Commanding General Boots & Golden Greaves (堂々とした武将!) (Z: 0..15)
    fill_sym_box(grid, 2, 5, 10, 16, 0, 2, 6)
    fill_sym_box(grid, 3, 4, 16, 17, 0, 1, 1)
    fill_sym_box(grid, 2, 5, 11, 15, 3, 14, 1)    # Golden general greaves
    fill_sym_box(grid, 3, 4, 15, 15, 4, 13, 3)    # Azure inlay
    fill_sym_box(grid, 2, 5, 15, 16, 12, 14, 2)   # Crimson knee pads

    # Five-Color Striped Martial Skirt & Broad Golden Cuirass (五色神牛の意匠!) (Z: 15..31)
    fill_sym_box(grid, 0, 6, 10, 16, 15, 21, 1)
    # Five-Colored Divine Ox Stripe Band across waist-skirt (Gold/Red/Blue/Green/White)!
    for idx_c, col_c in enumerate((1, 2, 3, 4, 5)):
        fill_box(grid, cx_l - 4 + idx_c * 2, cx_l - 3 + idx_c * 2, 16, 16, 16, 19, col_c)
    fill_sym_box(grid, 0, 6, 10, 16, 21, 31, 1)   # Broad commanding gold cuirass!
    fill_sym_box(grid, 1, 5, 16, 17, 23, 30, 2)   # Crimson martial breastplate
    fill_sym_box(grid, 0, 2, 17, 17, 25, 28, 5)   # White-gold Divine Ox emblem!
    # Flowing Crimson Martial-King Cape on Back
    fill_sym_box(grid, 0, 6, 8, 9, 5, 31, 2)
    fill_sym_box(grid, 0, 6, 8, 8, 5, 6, 1)

    # Broad Armored Pauldrons, Arms & Gilded War-Spear! (Z: 16..45)
    fill_sym_box(grid, 6, 8, 10, 16, 27, 32, 1)
    fill_sym_box(grid, 7, 8, 11, 15, 30, 32, 3)
    fill_box(grid, cx_l - 8, cx_l - 6, 11, 15, 19, 26, 6)
    fill_box(grid, cx_l - 8, cx_l - 6, 12, 15, 17, 18, 8)
    fill_box(grid, cx_r + 6, cx_r + 8, 11, 15, 19, 26, 6)
    fill_box(grid, cx_r + 7, cx_r + 10, 14, 17, 19, 21, 8)
    draw_golden_spear(grid, cx_r + 10, 16, z_bot=2, z_top=44)

    # Commanding General Head, Short Martial Beard & FIVE-COLORED DIVINE OX HORNED HELM! (Z: 31..44)
    fill_sym_box(grid, 0, 2, 11, 16, 31, 37, 8)   # Noble fierce face
    fill_sym_box(grid, 0, 2, 16, 17, 30, 32, 6)   # Commanding dark martial beard!
    fill_sym_box(grid, 1, 2, 16, 16, 34, 35, 9)   # Piercing eyes
    fill_sym_box(grid, 0, 3, 10, 16, 37, 41, 1)   # Tall golden Martial-King helm!
    fill_sym_box(grid, 0, 1, 16, 17, 38, 41, 2)   # Crimson helm crest
    # Curved Ivory-White Divine Ox Horns on Helm!
    draw_6conn_line(grid, (cx_r + 3, 14, 39), (cx_r + 7, 15, 43), 5)
    draw_6conn_line(grid, (cx_l - 3, 14, 39), (cx_l - 7, 15, 43), 5)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: HUANG FEIHU FIVE-COLORED DIVINE OX MARTIAL ROBOT (50 x 26 x 50)
# ============================================================
def build_b():
    grid = np.zeros((50, 26, 50), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 24
    cx_r = X // 2      # 25

    # Commanding Divine-Ox Hoof Boots & Gold Greaves (Z: 0..17)
    fill_sym_box(grid, 2, 6, 10, 18, 0, 2, 6)
    fill_sym_box(grid, 3, 5, 18, 20, 0, 1, 5)     # Ivory ox-hoof toes!
    fill_sym_box(grid, 2, 5, 11, 16, 3, 15, 1)    # Golden martial greaves
    fill_sym_box(grid, 3, 4, 16, 17, 4, 14, 3)    # Azure stripe
    fill_sym_box(grid, 2, 5, 16, 18, 13, 16, 2)   # Crimson knee shields
    fill_sym_box(grid, 3, 4, 18, 18, 14, 15, 4)   # Emerald knee gem!

    # Broad Waist & Five-Color Tasset Skirt (Z: 15..24)
    fill_sym_box(grid, 2, 5, 11, 15, 16, 20, 6)
    fill_sym_box(grid, 0, 6, 11, 15, 20, 23, 7)
    fill_sym_box(grid, 1, 6, 16, 17, 16, 22, 1)
    # Five-Color Radiant Gems across waist armor (Gold/Red/Blue/Green/White)!
    for idx_c, col_c in enumerate((2, 3, 4, 5, 1)):
        fill_box(grid, cx_l - 4 + idx_c * 2, cx_l - 3 + idx_c * 2, 17, 18, 19, 21, col_c)

    # FIVE-COLORED DIVINE OX HEAD CHEST CUIRASS (五色神牛装甲!) & Five-Element Cape! (Z: 23..36)
    fill_sym_box(grid, 0, 5, 11, 15, 23, 25, 6)
    fill_sym_box(grid, 0, 7, 10, 17, 26, 35, 1)   # Commanding golden chest!
    # Sculpted Divine-Ox Head Emblem on Chest with Curved White Horns & Five-Color Jewels!
    fill_sym_box(grid, 0, 3, 17, 20, 27, 33, 2)   # Crimson-gold Ox face!
    fill_sym_box(grid, 0, 2, 19, 21, 27, 29, 1)   # Golden Ox snout & ring
    fill_sym_box(grid, 2, 3, 20, 20, 31, 32, 9)   # Glowing cyan Ox eyes!
    draw_6conn_line(grid, (cx_r + 3, 19, 32), (cx_r + 6, 20, 35), 5)  # Chest Divine-Ox Horns!
    draw_6conn_line(grid, (cx_l - 3, 19, 32), (cx_l - 6, 20, 35), 5)
    # Rear Five-Colored Martial Cape-Wing Pack!
    fill_sym_box(grid, 0, 5, 8, 10, 25, 34, 6)
    fill_sym_box(grid, 0, 6, 7, 8, 11, 33, 2)
    fill_sym_box(grid, 4, 6, 7, 8, 25, 35, 3)     # Azure wing-trim
    fill_sym_box(grid, 2, 4, 7, 8, 25, 35, 4)     # Emerald wing-trim

    # Horned Martial-King Pauldrons, Arms & Giant Gilded Spear! (Z: 15..48)
    fill_sym_box(grid, 7, 9, 12, 15, 30, 34, 6)
    fill_sym_box(grid, 8, 13, 11, 16, 29, 36, 1)  # Broad gold pauldrons
    fill_sym_box(grid, 9, 13, 12, 15, 35, 37, 2)  # Crimson crests
    draw_6conn_line(grid, (cx_r + 12, 14, 37), (cx_r + 16, 14, 41), 5)  # White Ox-Horn spikes!
    draw_6conn_line(grid, (cx_l - 12, 14, 37), (cx_l - 16, 14, 41), 5)
    fill_sym_box(grid, 8, 10, 12, 15, 22, 29, 6)
    fill_box(grid, cx_l - 12, cx_l - 8, 12, 16, 16, 22, 1)
    fill_box(grid, cx_l - 11, cx_l - 8, 13, 16, 14, 15, 6)
    fill_box(grid, cx_r + 8, cx_r + 12, 12, 16, 17, 22, 1)
    fill_box(grid, cx_r + 10, cx_r + 14, 15, 19, 17, 20, 2)
    draw_golden_spear(grid, cx_r + 14, 18, z_bot=2, z_top=47)

    # Commanding Martial-King Robot Head WITH CURVED WHITE DIVINE-OX HORNS & 5-COLOR CREST! (Z: 35..48)
    fill_sym_box(grid, 0, 2, 12, 15, 35, 36, 6)
    fill_sym_box(grid, 0, 3, 11, 17, 36, 42, 1)   # Gold martial helm
    fill_sym_box(grid, 0, 2, 17, 18, 36, 37, 6)   # Dark chin guard
    fill_sym_box(grid, 0, 2, 17, 18, 38, 39, 6)
    fill_sym_box(grid, 1, 2, 18, 18, 38, 39, 9)   # Radiant cyan visor eyes!
    fill_sym_box(grid, 0, 2, 13, 18, 42, 45, 2)   # Tall crimson crest
    fill_sym_box(grid, 0, 1, 18, 19, 43, 46, 4)   # Emerald centerpiece!
    # Prominent Curved Ivory Divine-Ox Horns on Helm!
    draw_6conn_line(grid, (cx_r + 3, 14, 42), (cx_r + 9, 15, 47), 5)
    draw_6conn_line(grid, (cx_l - 3, 14, 42), (cx_l - 9, 15, 47), 5)

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
    v_a = export_vox(model_a, "huangfeihu_a.vox")
    v_b = export_vox(model_b, "huangfeihu_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #19: HUANG FEIHU (FENGSHEN) -> FIVE-COLOR OX GENERAL ROBOT",
        "1. HUANG FEIHU (MARTIAL KING)",
        "2. HUANG FEIHU ROBOT",
        "preview_huangfeihu.png",
    )
    print(f"huangfeihu: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
