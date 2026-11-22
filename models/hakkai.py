import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Zhu Bajie / Cho Hakkai (猪八戒) -> Plump Boar-Guardian Robot!
# Big pig ears & snout (豚の耳と鼻), nine-tooth iron rake (釘鈀), round stout build (丸い体格)!
PALETTE = {
    1: (44, 50, 74, 255),     # Deep Navy-Black Monk Tunic & Heavy Armor
    2: (246, 174, 178, 255),  # Warm Rosy Pig Skin (Snout, Big Ears, Belly)
    3: (218, 126, 136, 255),  # Deep Pink Snout Nostrils & Inner Ears
    4: (204, 42, 46, 255),    # Crimson Belt Sash & Cloth Accents
    5: (240, 194, 52, 255),   # Brass-Gold Belt Clasp & Rake Binding
    6: (206, 214, 226, 255),  # Forged Steel Nine-Tooth Rake Head (釘鈀!)
    7: (132, 82, 44, 255),    # Cedar Rake Shaft
    8: (86, 94, 118, 255),    # Slate Heavy Armor Trim
    9: (102, 232, 168, 255),  # Cheerful Emerald Visor / Eyes
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


def fill_ellipsoid(grid, cx, cy, cz, rx, ry, rz, col):
    X, Y, Z = grid.shape
    x0, x1 = max(0, int(np.floor(cx - rx))), min(X - 1, int(np.ceil(cx + rx)))
    y0, y1 = max(0, int(np.floor(cy - ry))), min(Y - 1, int(np.ceil(cy + ry)))
    z0, z1 = max(0, int(np.floor(cz - rz))), min(Z - 1, int(np.ceil(cz + rz)))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                val = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                if val <= 1.0:
                    grid[x, y, z] = col


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


def draw_iron_rake(grid, hx, hy, z_bot, z_top):
    """Draw Zhu Bajie's iconic Nine-Tooth Iron Rake (釘鈀 — wide rake bar with iron tines!)."""
    fill_box(grid, hx, hx, hy, hy, z_bot, z_top - 3, 7)      # Cedar shaft
    fill_box(grid, hx, hx, hy, hy, z_top - 4, z_top - 3, 5)  # Brass collar
    # Wide steel rake crossbar
    fill_box(grid, hx - 3, hx + 3, hy, hy, z_top - 2, z_top - 1, 6)
    # Prominent Rake Tines curving forward (+Y) and up!
    for tx in (hx - 3, hx - 1, hx + 1, hx + 3):
        fill_box(grid, tx, tx, hy, hy + 2, z_top - 2, z_top, 6)
        fill_box(grid, tx, tx, hy + 2, hy + 2, z_top - 3, z_top - 1, 6)


# ============================================================
# FORM A: ZHU BAJIE / CHO HAKKAI CHARACTER (ROUND STOUT BUILD) (38 x 26 x 40)
# ============================================================
def build_a():
    grid = np.zeros((38, 26, 40), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18
    cx_r = X // 2      # 19

    # Short Sturdy Legs & Boots (Z: 0..10)
    fill_sym_box(grid, 2, 5, 10, 16, 0, 2, 1)
    fill_sym_box(grid, 2, 5, 11, 15, 3, 10, 8)

    # ICONIC PLUMP ROUND BELLY & MONK TUNIC (丸い体格!) (Z: 9..26)
    fill_ellipsoid(grid, X / 2 - 0.5, 13.0, 17.5, rx=7.2, ry=6.2, rz=8.5, col=1)
    # Round rosy belly peeking over crimson belt!
    fill_ellipsoid(grid, X / 2 - 0.5, 16.5, 16.0, rx=4.2, ry=3.4, rz=4.0, col=2)
    # Crimson sash & gold buckle stretched round the belly!
    fill_sym_box(grid, 0, 6, 9, 19, 13, 14, 4)
    fill_sym_box(grid, 0, 1, 19, 20, 13, 15, 5)
    # White/slate open collar
    fill_sym_box(grid, 2, 5, 16, 18, 20, 25, 8)

    # Arms & ICONIC NINE-TOOTH IRON RAKE (釘鈀!) (Z: 14..38)
    fill_box(grid, cx_l - 9, cx_l - 6, 11, 16, 18, 24, 1)
    fill_box(grid, cx_l - 9, cx_l - 7, 12, 15, 15, 17, 2)   # Rosy hand
    fill_box(grid, cx_r + 6, cx_r + 9, 11, 16, 18, 24, 1)
    fill_box(grid, cx_r + 8, cx_r + 11, 14, 18, 17, 20, 2)  # Hand gripping rake!
    draw_iron_rake(grid, cx_r + 11, 17, z_bot=2, z_top=37)

    # Round Pig Head, Prominent Snout, Big Floppy Pig Ears & Monk Cap! (Z: 25..36)
    fill_ellipsoid(grid, X / 2 - 0.5, 13.5, 29.5, rx=4.6, ry=4.4, rz=4.5, col=2)
    # BIG PROTRUDING PIG SNOUT (豚の鼻!)
    fill_sym_box(grid, 0, 1, 17, 20, 27, 29, 2)
    fill_sym_box(grid, 1, 1, 20, 20, 28, 28, 3)   # Pink nostrils!
    fill_sym_box(grid, 2, 3, 17, 17, 30, 31, 9)   # Friendly bright eyes
    # BIG FLOPPY PIG EARS (豚の耳!)
    fill_sym_box(grid, 4, 7, 12, 15, 28, 32, 2)
    fill_sym_box(grid, 6, 8, 12, 15, 26, 29, 2)   # Flopping down tips!
    fill_sym_box(grid, 5, 7, 15, 15, 27, 30, 3)   # Inner pink ear
    # Black Monk Cap with Gold Forehead Badge (Z: 32..36)
    fill_sym_box(grid, 0, 4, 10, 16, 32, 35, 1)
    fill_sym_box(grid, 0, 1, 16, 17, 33, 34, 5)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: ZHU BAJIE STOUT BOAR-GUARDIAN ROBOT (48 x 28 x 44)
# ============================================================
def build_b():
    grid = np.zeros((48, 28, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # Heavy Stout Legs & Broad Feet (Z: 0..14)
    fill_sym_box(grid, 3, 7, 10, 18, 0, 2, 1)
    fill_sym_box(grid, 4, 6, 18, 19, 0, 1, 5)
    fill_sym_box(grid, 3, 7, 11, 17, 3, 13, 1)
    fill_sym_box(grid, 4, 6, 17, 18, 4, 12, 8)
    fill_sym_box(grid, 3, 6, 17, 19, 11, 14, 4)   # Crimson knee pads
    fill_sym_box(grid, 4, 5, 19, 19, 12, 13, 5)

    # ROUND ARMORED SUMO-MECH TORSO & ROSY-PLATED BELLY CORE (丸い体格ロボ!) (Z: 13..31)
    fill_ellipsoid(grid, X / 2 - 0.5, 14.0, 22.0, rx=9.2, ry=7.2, rz=9.2, col=1)
    # Armored pink-peach belly dome with gold & crimson waist ring!
    fill_ellipsoid(grid, X / 2 - 0.5, 18.2, 20.5, rx=5.2, ry=3.6, rz=4.5, col=2)
    fill_sym_box(grid, 0, 8, 9, 21, 16, 18, 4)    # Heavy crimson waist belt!
    fill_sym_box(grid, 0, 2, 21, 22, 16, 19, 5)   # Gold waist emblem
    fill_sym_box(grid, 0, 1, 22, 22, 17, 18, 9)   # Glowing core
    fill_sym_box(grid, 2, 7, 19, 21, 24, 29, 8)   # Slate chest vents
    fill_sym_box(grid, 0, 5, 6, 9, 19, 29, 8)     # Heavy rear booster pack

    # Broad Armored Pauldrons & Giant NINE-TOOTH IRON RAKE! (Z: 14..42)
    fill_sym_box(grid, 8, 12, 11, 17, 25, 31, 1)
    fill_sym_box(grid, 9, 13, 12, 16, 30, 32, 4)  # Crimson shoulder trim
    fill_sym_box(grid, 11, 13, 13, 15, 26, 29, 5) # Gold rivets
    fill_sym_box(grid, 8, 11, 12, 16, 19, 25, 8)
    fill_box(grid, cx_l - 13, cx_l - 9, 12, 17, 14, 20, 1)
    fill_box(grid, cx_l - 12, cx_l - 9, 13, 16, 12, 14, 2)  # Pink-plated fist
    fill_box(grid, cx_r + 9, cx_r + 13, 12, 17, 15, 21, 1)
    fill_box(grid, cx_r + 11, cx_r + 15, 15, 19, 15, 19, 2) # Right fist gripping rake
    draw_iron_rake(grid, cx_r + 15, 18, z_bot=2, z_top=41)

    # Boar-Guardian Robot Head: ARMORED SNOUT VISOR & BIG FLOPPY MECHA PIG EARS! (Z: 30..41)
    fill_sym_box(grid, 0, 4, 10, 18, 31, 38, 2)   # Rosy-plated boar helm
    # Armored Snout Module!
    fill_sym_box(grid, 0, 2, 18, 21, 32, 34, 2)
    fill_sym_box(grid, 1, 1, 21, 21, 33, 33, 3)   # Twin intake nostrils!
    fill_sym_box(grid, 0, 3, 18, 19, 35, 36, 1)   # Dark visor band
    fill_sym_box(grid, 1, 3, 19, 19, 35, 36, 9)   # Bright emerald optic eyes!
    # BIG ARMORED FLOPPY PIG EARS (豚の耳装甲!)
    fill_sym_box(grid, 4, 8, 12, 16, 34, 38, 2)
    fill_sym_box(grid, 7, 10, 12, 16, 31, 35, 2)
    fill_sym_box(grid, 6, 9, 16, 16, 32, 35, 3)   # Pink armor inlay
    # Armored Black Monk Cap Crown!
    fill_sym_box(grid, 0, 4, 11, 18, 38, 41, 1)
    fill_sym_box(grid, 0, 1, 18, 19, 39, 41, 5)   # Gold forehead plate!

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
    v_a = export_vox(model_a, "hakkai_a.vox")
    v_b = export_vox(model_b, "hakkai_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #02: ZHU BAJIE (JOURNEY TO THE WEST) -> BOAR GUARDIAN ROBOT",
        "1. ZHU BAJIE (CHARACTER)",
        "2. ZHU BAJIE ROBOT",
        "preview_hakkai.png",
    )
    print(f"hakkai: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
