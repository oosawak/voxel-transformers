import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Huang Tianhua (黄天化) -> Jade Qilin Young General Robot!
# Divine Treasure Sword (宝剣 — 莫邪宝剣) & Jade Qilin (玉麒麟) armor motif, youthful warrior look!
PALETTE = {
    1: (44, 178, 134, 255),   # Luminous Jade-Emerald Qilin Armor (玉麒麟の翡翠!)
    2: (22, 114, 88, 255),    # Deep Jade Scale Shading
    3: (242, 248, 244, 255),  # Pure Jade-White Qilin Mane, Tunic & Horns
    4: (246, 202, 48, 255),   # Imperial Gold Crown, Qilin Antlers & Sword Hilt
    5: (204, 42, 48, 255),    # Heroic Crimson War-Scarf & Sash
    6: (42, 50, 66, 255),     # Dark Slate Frame & Boots
    7: (252, 222, 198, 255),  # Youthful General Face
    8: (218, 232, 246, 255),  # Gleaming Silver Treasure Sword Blade (宝剣!)
    9: (106, 252, 212, 255),  # Radiant Jade-Mint Qilin Eyes & Sword Core!
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


def draw_treasure_sword(grid, hx, hy, z_hilt, z_tip):
    """Draw Huang Tianhua's gleaming Bakuya Treasure Sword (宝剣)."""
    fill_box(grid, hx, hx, hy, hy, z_hilt - 3, z_hilt, 4)        # Gold pommel & grip
    fill_box(grid, hx - 2, hx + 2, hy, hy, z_hilt + 1, z_hilt + 1, 4)  # Ornate crossguard
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_hilt + 2, z_tip - 2, 8)   # Gleaming wide double-edged blade!
    fill_box(grid, hx, hx, hy, hy, z_hilt + 3, z_tip, 9)         # Radiant jade-spirit fuller!


# ============================================================
# FORM A: HUANG TIANHUA (YOUNG JADE-QILIN GENERAL) (38 x 24 x 44)
# ============================================================
def build_a():
    grid = np.zeros((38, 24, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18
    cx_r = X // 2      # 19

    # Agile Young General Boots & Jade-White Greaves (Z: 0..14)
    fill_sym_box(grid, 2, 4, 10, 15, 0, 2, 6)
    fill_sym_box(grid, 2, 4, 15, 16, 0, 1, 4)     # Gold boot tips
    fill_sym_box(grid, 2, 4, 11, 14, 3, 14, 3)    # Pure jade-white greaves
    fill_sym_box(grid, 3, 4, 14, 14, 4, 13, 1)    # Jade shin scales

    # Jade-Emerald War-Skirt & Youthful Armored Torso (Z: 14..29)
    fill_sym_box(grid, 0, 5, 10, 15, 14, 20, 1)
    fill_sym_box(grid, 0, 5, 15, 16, 14, 15, 4)   # Gold skirt hem
    fill_sym_box(grid, 0, 1, 16, 16, 15, 20, 5)   # Crimson center sash
    fill_sym_box(grid, 0, 5, 10, 15, 20, 29, 3)   # Jade-white cuirass
    fill_sym_box(grid, 1, 4, 15, 16, 21, 28, 1)   # Jade Qilin scale breastplate!
    fill_sym_box(grid, 0, 1, 16, 16, 23, 26, 4)   # Gold Qilin seal
    fill_sym_box(grid, 0, 4, 10, 16, 28, 29, 5)   # Heroic crimson neck-scarf
    # Flowing White-and-Jade Qilin-Mane Cape on Back
    fill_sym_box(grid, 0, 5, 8, 9, 6, 29, 3)
    fill_sym_box(grid, 0, 5, 8, 8, 6, 7, 1)

    # Qilin-Crested Shoulders, Arms & Gleaming TREASURE SWORD (宝剣!)
    fill_sym_box(grid, 5, 7, 10, 15, 25, 29, 1)
    fill_sym_box(grid, 6, 7, 11, 14, 29, 30, 4)   # Gold Qilin shoulder scales
    fill_box(grid, cx_l - 7, cx_l - 5, 11, 14, 18, 24, 3)
    fill_box(grid, cx_l - 7, cx_l - 5, 12, 14, 16, 17, 7)
    fill_box(grid, cx_r + 5, cx_r + 7, 11, 14, 19, 24, 3)
    fill_box(grid, cx_r + 6, cx_r + 9, 14, 17, 19, 21, 7)
    draw_treasure_sword(grid, cx_r + 9, 16, z_hilt=20, z_tip=41)

    # Youthful Handsome General Head & JADE QILIN ANTLER CROWN (玉麒麟の意匠!) (Z: 29..41)
    fill_sym_box(grid, 0, 2, 11, 16, 29, 35, 7)
    fill_sym_box(grid, 1, 2, 16, 16, 32, 33, 9)   # Bright jade eyes!
    fill_sym_box(grid, 0, 3, 10, 16, 35, 37, 6)   # Dark youthful hair
    fill_sym_box(grid, 0, 2, 11, 16, 37, 39, 4)   # Gold young-general crown!
    fill_sym_box(grid, 0, 1, 16, 16, 38, 39, 9)   # Jade forehead gem
    # Iconic Curved Jade Qilin Antler-Horns on Helm!
    draw_6conn_line(grid, (cx_r + 2, 14, 38), (cx_r + 5, 13, 42), 3)
    draw_6conn_line(grid, (cx_l - 2, 14, 38), (cx_l - 5, 13, 42), 3)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: HUANG TIANHUA JADE-QILIN KNIGHT ROBOT (48 x 26 x 48)
# ============================================================
def build_b():
    grid = np.zeros((48, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # Hoof-Styled Qilin Greaves & Jade Armor (Z: 0..16)
    fill_sym_box(grid, 2, 5, 10, 17, 0, 2, 6)
    fill_sym_box(grid, 2, 5, 17, 19, 0, 1, 4)     # Golden Qilin hoof-toes!
    fill_sym_box(grid, 2, 5, 11, 16, 3, 14, 3)    # Jade-white greaves
    fill_sym_box(grid, 3, 4, 16, 17, 4, 13, 1)    # Jade scale stripe
    fill_sym_box(grid, 2, 5, 16, 18, 12, 15, 4)   # Gold knee guards
    fill_sym_box(grid, 3, 4, 18, 18, 13, 14, 9)

    # Waist Armor & Flowing Qilin Mane-Tail (Z: 15..23)
    fill_sym_box(grid, 2, 4, 11, 15, 15, 19, 6)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 2)
    fill_sym_box(grid, 1, 5, 16, 17, 15, 21, 1)
    fill_sym_box(grid, 1, 5, 17, 17, 15, 15, 4)
    fill_sym_box(grid, 0, 1, 16, 18, 17, 22, 5)
    fill_sym_box(grid, 0, 1, 18, 18, 20, 21, 4)

    # JADE QILIN HEAD CHEST ARMOR (玉麒麟の胸部装甲!) & Wing-Mane Pack (Z: 22..35)
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 6)
    fill_sym_box(grid, 0, 6, 10, 17, 25, 33, 1)   # Jade-emerald cuirass
    # Sculpted White & Gold Jade-Qilin Head Emblem protruding from chest!
    fill_sym_box(grid, 0, 3, 17, 19, 26, 32, 3)   # White Qilin face on chest!
    fill_sym_box(grid, 0, 2, 19, 20, 27, 29, 4)   # Golden Qilin muzzle & fangs!
    fill_sym_box(grid, 2, 3, 19, 19, 30, 31, 9)   # Glowing jade Qilin chest-eyes!
    draw_6conn_line(grid, (cx_r + 2, 18, 32), (cx_r + 4, 19, 35), 4)  # Chest Qilin horns!
    draw_6conn_line(grid, (cx_l - 2, 18, 32), (cx_l - 4, 19, 35), 4)
    # Rear Jade-White Mane-Wing Thrusters
    fill_sym_box(grid, 0, 4, 8, 10, 25, 33, 2)
    fill_sym_box(grid, 2, 6, 6, 8, 26, 36, 3)
    fill_sym_box(grid, 4, 6, 6, 7, 34, 38, 1)

    # Horned Jade-Qilin Pauldrons, Arms & Giant TREASURE SWORD! (Z: 14..46)
    fill_sym_box(grid, 6, 8, 12, 15, 29, 32, 6)
    fill_sym_box(grid, 7, 11, 11, 16, 28, 34, 1)
    fill_sym_box(grid, 8, 12, 12, 15, 33, 35, 3)  # Jade-white mane ridges
    draw_6conn_line(grid, (cx_r + 11, 14, 35), (cx_r + 14, 14, 39), 4)
    draw_6conn_line(grid, (cx_l - 11, 14, 35), (cx_l - 14, 14, 39), 4)
    fill_sym_box(grid, 7, 9, 12, 15, 22, 28, 6)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 3)
    fill_box(grid, cx_l - 10, cx_l - 8, 13, 15, 14, 15, 4)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 3)
    fill_box(grid, cx_r + 9, cx_r + 13, 15, 19, 17, 20, 4)
    draw_treasure_sword(grid, cx_r + 13, 18, z_hilt=19, z_tip=46)

    # Young Jade-Qilin Knight Robot Head & Antler-V Crest! (Z: 34..46)
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 6)
    fill_sym_box(grid, 0, 3, 11, 17, 35, 41, 3)   # Jade-white helm
    fill_sym_box(grid, 0, 2, 17, 18, 35, 36, 1)   # Jade jaw guard
    fill_sym_box(grid, 0, 2, 17, 18, 37, 38, 6)   # Dark eye recess
    fill_sym_box(grid, 1, 2, 18, 18, 37, 38, 9)   # Radiant jade eyes!
    fill_sym_box(grid, 0, 2, 13, 18, 41, 43, 4)   # Gold Qilin crown
    draw_6conn_line(grid, (cx_r + 2, 16, 42), (cx_r + 6, 15, 46), 4)  # Qilin antler horns!
    draw_6conn_line(grid, (cx_l - 2, 16, 42), (cx_l - 6, 15, 46), 4)

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
    v_a = export_vox(model_a, "huangtianhua_a.vox")
    v_b = export_vox(model_b, "huangtianhua_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #14: HUANG TIANHUA (FENGSHEN) -> JADE QILIN ROBOT",
        "1. HUANG TIANHUA (CHARACTER)",
        "2. HUANG TIANHUA ROBOT",
        "preview_huangtianhua.png",
    )
    print(f"huangtianhua: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
