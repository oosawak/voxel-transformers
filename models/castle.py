import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (240, 236, 226, 255),  # Shikkui White Plaster Wall
    2: (54, 68, 84, 255),     # Dark Blue-Grey Kawara Roof Tiles
    3: (172, 182, 192, 255),  # White-Grey Kawara Ridge Trim
    4: (132, 128, 118, 255),  # Ishigaki Stone Foundation
    5: (84, 80, 74, 255),     # Dark Stone Masonry / Inner Joints
    6: (242, 196, 46, 255),   # Golden Shachihoko & Kabuto Crest
    7: (94, 62, 40, 255),     # Dark Wood Lattice / Gates / Beams
    8: (202, 48, 42, 255),    # Vermilion Red Trim / Armor Lacing
    9: (255, 222, 102, 255),  # Warm Lantern Glow / Robot Eyes
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(x0, x1)), min(X - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


def fill_stone_layer(grid, x_off1, y0, y1, z):
    """Fill an ishigaki stone layer with subtle masonry variation."""
    fill_sym_box(grid, 0, x_off1, y0, y1, z, z, 4)
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    for dx in range(0, x_off1 + 1):
        for y in range(y0, y1 + 1):
            if (dx + y + z) % 3 == 0:
                if dx == x_off1 or y == y0 or y == y1:
                    grid[cx_l - dx, y, z] = 5
                    grid[cx_r + dx, y, z] = 5


# ==========================================
# FORM A: JAPANESE CASTLE (26 x 22 x 25)
# ==========================================
def build_a():
    grid = np.zeros((26, 22, 25), dtype=np.uint8)

    # --- SLOPED ISHIGAKI STONE BASE (Z: 0..4) ---
    for z in range(5):
        shrink = z // 2
        fill_stone_layer(grid, 10 - shrink, 3 + shrink, 18 - shrink, z)
    fill_sym_box(grid, 0, 7, 5, 16, 0, 3, 0)  # Hollow interior under stone base
    # Front wooden Otemon gate
    fill_sym_box(grid, 0, 1, 17, 18, 0, 3, 7)
    fill_sym_box(grid, 0, 0, 18, 18, 0, 2, 5)
    fill_sym_box(grid, 0, 2, 17, 19, 4, 4, 2)
    fill_sym_box(grid, 0, 2, 19, 19, 4, 4, 3)

    # --- FLANKING CORNER YAGURA TURRETS (Z: 5..14) ---
    fill_sym_box(grid, 5, 6, 9, 12, 5, 8, 1)
    fill_sym_box(grid, 5, 6, 8, 13, 9, 9, 2)
    fill_sym_box(grid, 7, 9, 7, 14, 5, 9, 1)
    fill_sym_box(grid, 8, 8, 8, 13, 6, 8, 0)
    fill_sym_box(grid, 8, 8, 14, 14, 7, 8, 7)
    fill_sym_box(grid, 9, 9, 10, 11, 7, 8, 7)
    fill_sym_box(grid, 6, 10, 6, 15, 10, 10, 2)
    fill_sym_box(grid, 10, 10, 6, 15, 10, 10, 3)
    fill_sym_box(grid, 7, 9, 8, 13, 11, 12, 1)
    fill_sym_box(grid, 7, 9, 7, 14, 13, 13, 2)
    fill_sym_box(grid, 8, 8, 9, 12, 14, 14, 3)

    # --- MAIN TENSHU KEEP - TIER 1 (Z: 5..11) ---
    fill_sym_box(grid, 0, 5, 6, 15, 5, 9, 1)
    fill_sym_box(grid, 0, 3, 8, 13, 5, 8, 0)
    fill_sym_box(grid, 1, 1, 15, 15, 7, 8, 7)
    fill_sym_box(grid, 3, 4, 15, 15, 7, 8, 7)
    fill_sym_box(grid, 1, 1, 15, 15, 7, 7, 9)
    # Tier 1 flared roof
    fill_sym_box(grid, 0, 6, 5, 16, 10, 10, 2)
    fill_sym_box(grid, 6, 6, 5, 16, 10, 10, 3)
    fill_sym_box(grid, 0, 6, 16, 16, 10, 10, 3)
    fill_sym_box(grid, 0, 5, 6, 15, 11, 11, 2)
    # Chidori-hafu gable
    fill_sym_box(grid, 0, 1, 16, 16, 11, 11, 1)
    fill_sym_box(grid, 0, 0, 16, 16, 12, 12, 6)

    # --- MAIN TENSHU KEEP - TIER 2 (Z: 12..16) ---
    fill_sym_box(grid, 0, 3, 8, 13, 12, 14, 1)
    fill_sym_box(grid, 0, 2, 9, 12, 12, 13, 0)
    fill_sym_box(grid, 1, 2, 13, 13, 13, 13, 7)
    fill_sym_box(grid, 3, 3, 9, 12, 13, 13, 7)
    fill_sym_box(grid, 0, 5, 6, 15, 15, 15, 2)
    fill_sym_box(grid, 5, 5, 6, 15, 15, 15, 3)
    fill_sym_box(grid, 0, 4, 7, 14, 16, 16, 2)

    # --- MAIN TENSHU KEEP - TOP TIER 3 (Z: 17..24) ---
    fill_sym_box(grid, 0, 2, 9, 12, 17, 19, 1)
    fill_sym_box(grid, 0, 2, 12, 12, 18, 18, 8)  # Vermilion balcony
    fill_sym_box(grid, 1, 1, 12, 12, 19, 19, 9)  # Warm lantern windows
    fill_sym_box(grid, 0, 4, 7, 14, 20, 20, 2)
    fill_sym_box(grid, 4, 4, 7, 14, 20, 20, 3)
    fill_sym_box(grid, 0, 3, 8, 13, 21, 21, 2)
    fill_sym_box(grid, 0, 2, 10, 11, 22, 22, 3)
    # Twin Golden Shachihoko!
    fill_sym_box(grid, 2, 2, 10, 11, 23, 24, 6)
    fill_sym_box(grid, 3, 3, 10, 11, 24, 24, 6)

    return grid


# ==========================================
# FORM B: CASTLE SHOGUN ROBOT (32 x 22 x 40)
# ==========================================
def build_b():
    grid = np.zeros((32, 22, 40), dtype=np.uint8)

    # --- FEET (Z: 0..3) - Heavy Ishigaki stone bases ---
    fill_sym_box(grid, 2, 5, 7, 15, 0, 1, 5)
    fill_sym_box(grid, 2, 5, 8, 15, 1, 2, 4)
    fill_sym_box(grid, 3, 4, 13, 16, 1, 2, 7)    # Wooden gate toes
    fill_sym_box(grid, 2, 5, 8, 14, 3, 3, 2)     # Kawara ankle cuff

    # --- LOWER LEGS (Z: 4..13) - Split Ishigaki stone legs ---
    for z in range(4, 14):
        fill_sym_box(grid, 2, 4, 9, 13, z, z, 4)
        X = grid.shape[0]
        cx_l, cx_r = X // 2 - 1, X // 2
        for dx in range(2, 5):
            for y in (9, 13):
                if (dx + y + z) % 3 == 0:
                    grid[cx_l - dx, y, z] = 5
                    grid[cx_r + dx, y, z] = 5
    fill_sym_box(grid, 3, 3, 13, 14, 5, 10, 7)   # Wooden gate shin guards
    fill_sym_box(grid, 2, 3, 13, 14, 11, 14, 2)  # Kawara knee armor
    fill_sym_box(grid, 3, 3, 14, 15, 12, 13, 6)  # Gold knee crest

    # --- THIGHS (Z: 14..18) ---
    fill_sym_box(grid, 2, 3, 9, 12, 14, 18, 1)
    fill_sym_box(grid, 2, 3, 10, 11, 14, 15, 5)
    fill_sym_box(grid, 3, 3, 10, 11, 16, 17, 7)

    # --- WAIST / KUSAZURI TASSETS (Z: 18..22) - Flared Kawara Roof Skirt ---
    fill_sym_box(grid, 0, 4, 9, 13, 19, 21, 2)
    fill_sym_box(grid, 0, 4, 13, 14, 18, 20, 2)
    fill_sym_box(grid, 0, 4, 14, 14, 18, 18, 3)
    fill_sym_box(grid, 0, 1, 13, 15, 19, 21, 8)  # Vermilion sash
    fill_sym_box(grid, 0, 0, 15, 15, 20, 20, 6)  # Gold medallion
    fill_sym_box(grid, 4, 5, 9, 13, 18, 20, 2)

    # --- TORSO / CHEST (Z: 22..31) - Multi-Tier White Tenshu Keep ---
    fill_sym_box(grid, 0, 4, 8, 13, 22, 30, 1)
    fill_sym_box(grid, 0, 3, 13, 14, 22, 24, 7)  # Timber abs
    fill_sym_box(grid, 0, 2, 14, 14, 23, 24, 8)  # Vermilion cords
    # Flared Tenshu roof eave across mid-chest!
    fill_sym_box(grid, 0, 5, 13, 15, 25, 26, 2)
    fill_sym_box(grid, 0, 5, 15, 15, 25, 25, 3)
    fill_sym_box(grid, 0, 3, 13, 14, 27, 29, 1)  # Upper white keep wall
    fill_sym_box(grid, 1, 2, 14, 14, 28, 28, 7)  # Lattice windows
    fill_sym_box(grid, 2, 2, 14, 14, 28, 28, 9)  # Glowing lantern
    fill_sym_box(grid, 0, 4, 9, 14, 30, 30, 2)   # Upper collar roof
    fill_sym_box(grid, 0, 1, 14, 15, 28, 29, 8)  # Vermilion chest collar
    fill_sym_box(grid, 0, 0, 15, 15, 29, 29, 6)  # Gold gable emblem

    # --- BACKPACK (Y: 5..7) - Rear Tenshu Roof Tiers ---
    fill_sym_box(grid, 0, 3, 5, 7, 22, 29, 1)
    fill_sym_box(grid, 0, 4, 4, 7, 24, 25, 2)
    fill_sym_box(grid, 0, 4, 4, 7, 28, 29, 2)
    fill_sym_box(grid, 0, 4, 4, 4, 28, 28, 3)

    # --- SHOULDERS & ARMS (Z: 13..33) - Flanking Yagura Turrets ---
    fill_sym_box(grid, 5, 8, 9, 13, 27, 30, 1)   # White turret walls
    fill_sym_box(grid, 7, 7, 13, 13, 28, 29, 7)  # Turret window
    fill_sym_box(grid, 5, 10, 8, 14, 31, 31, 2)  # Sweeping pagoda shoulder roof!
    fill_sym_box(grid, 10, 10, 8, 14, 31, 31, 3)
    fill_sym_box(grid, 6, 9, 9, 13, 32, 32, 2)
    fill_sym_box(grid, 7, 8, 10, 12, 33, 33, 3)
    # Upper arm
    fill_sym_box(grid, 6, 7, 10, 12, 22, 26, 7)
    fill_sym_box(grid, 6, 7, 10, 12, 23, 24, 8)
    # Forearm
    fill_sym_box(grid, 6, 8, 9, 13, 16, 21, 1)
    fill_sym_box(grid, 8, 8, 10, 12, 17, 20, 2)
    fill_sym_box(grid, 7, 7, 13, 13, 18, 19, 7)
    # Heavy stone/wood fists
    fill_sym_box(grid, 6, 7, 10, 12, 13, 15, 5)
    # Right hand Naginata held slightly outward & forward (clear of shoulder!)
    fill_box(grid, 24, 24, 14, 15, 8, 26, 7)
    fill_box(grid, 24, 24, 14, 16, 25, 26, 6)
    fill_box(grid, 24, 24, 15, 17, 27, 33, 3)
    # Left forearm Kawara Roof Shield
    fill_box(grid, 5, 6, 10, 15, 15, 22, 2)
    fill_box(grid, 5, 5, 11, 14, 16, 21, 1)
    fill_box(grid, 5, 5, 12, 13, 18, 19, 6)

    # --- HEAD (Z: 31..39) - Samurai Kabuto crowned by Golden Shachihoko! ---
    fill_sym_box(grid, 0, 1, 10, 11, 30, 31, 5)
    fill_sym_box(grid, 0, 2, 9, 13, 31, 35, 2)
    fill_sym_box(grid, 0, 3, 9, 12, 32, 33, 2)
    fill_sym_box(grid, 0, 1, 13, 14, 32, 32, 5)
    fill_sym_box(grid, 0, 1, 13, 14, 33, 33, 9)  # Glowing amber samurai eyes
    fill_sym_box(grid, 0, 2, 10, 12, 36, 36, 3)
    # Golden Shachihoko Kuwagata V-Crest!
    fill_sym_box(grid, 0, 0, 13, 14, 34, 36, 6)
    fill_sym_box(grid, 1, 2, 13, 14, 36, 37, 6)
    fill_sym_box(grid, 2, 3, 13, 14, 38, 39, 6)

    return grid


# ==========================================
# MAGICA-VOXEL (.vox) EXPORTER
# ==========================================
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
    header = b'VOX ' + struct.pack('<I', 150)

    with open(filename, 'wb') as f:
        f.write(header + main_chunk)
    return len(voxels)


# ==========================================
# TRUE ISOMETRIC / 3D VOXEL RENDERER
# ==========================================
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

    cx = (xs.min() + xs.max() + 1) / 2.0
    cy = (ys.min() + ys.max() + 1) / 2.0
    cz = (zs.min() + zs.max() + 1) / 2.0

    yaw = np.radians(yaw_deg)
    pitch = np.radians(pitch_deg)
    cos_y, sin_y = np.cos(yaw), np.sin(yaw)
    cos_p, sin_p = np.cos(pitch), np.sin(pitch)

    def project_unit(x, y, z):
        dx, dy, dz = x - cx, y - cy, z - cz
        rx = -dx * cos_y + dy * sin_y
        ry = dx * sin_y + dy * cos_y
        sy = ry * sin_p - dz * cos_p
        depth = ry * cos_p + dz * sin_p
        return rx, sy, depth

    corners = [
        (x, y, z)
        for x in (xs.min(), xs.max() + 1)
        for y in (ys.min(), ys.max() + 1)
        for z in (zs.min(), zs.max() + 1)
    ]
    proj_c = [project_unit(x, y, z) for x, y, z in corners]
    min_rx = min(p[0] for p in proj_c)
    max_rx = max(p[0] for p in proj_c)
    min_sy = min(p[1] for p in proj_c)
    max_sy = max(p[1] for p in proj_c)

    if scale is None:
        sx_fit = (img_size[0] - 2 * margin) / max(1e-5, max_rx - min_rx)
        sy_fit = (img_size[1] - 2 * margin) / max(1e-5, max_sy - min_sy)
        scale = min(sx_fit, sy_fit, 9.5)

    ox = img_size[0] / 2.0 - ((min_rx + max_rx) / 2.0) * scale
    oy = img_size[1] / 2.0 - ((min_sy + max_sy) / 2.0) * scale

    def project(x, y, z):
        rx, sy, depth = project_unit(x, y, z)
        return (rx * scale + ox, sy * scale + oy), depth

    visible = []
    for x, y, z in zip(xs, ys, zs):
        x, y, z = int(x), int(y), int(z)
        if (0 < x < X - 1 and 0 < y < Y - 1 and 0 < z < Z - 1 and
                grid[x - 1, y, z] and grid[x + 1, y, z] and
                grid[x, y - 1, z] and grid[x, y + 1, z] and
                grid[x, y, z - 1] and grid[x, y, z + 1]):
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

    vx_dir = sin_y * cos_p
    vy_dir = cos_y * cos_p
    vz_dir = sin_p

    for _, x, y, z, c in visible:
        base_col = PALETTE[c]
        for verts, normal, light in faces:
            nx, ny, nz = normal
            nnx, nny, nnz = x + nx, y + ny, z + nz
            if 0 <= nnx < X and 0 <= nny < Y and 0 <= nnz < Z and grid[nnx, nny, nnz] > 0:
                continue
            dot = nx * vx_dir + ny * vy_dir + nz * vz_dir
            if dot <= 1e-6:
                continue
            poly = [project(x + vx, y + vy, z + vz)[0] for vx, vy, vz in verts]
            fcol = shade_color(base_col, light)
            draw.polygon(poly, fill=fcol, outline=shade_color(fcol, 0.85))
    return img


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=24, yaw_b=32, pitch_b=20):
    canvas = Image.new("RGBA", (860, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, 860, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (860, gy)], fill=(28, 34, 48, 255), width=1)

    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))

    models = [
        (label_a, grid_a, v_a, yaw_a, pitch_a),
        (label_b, grid_b, v_b, yaw_b, pitch_b),
    ]
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(models):
        bx = 24 + idx * 414
        by = 48
        w, h = 398, 468
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
            px0 = bx + 14 + (pi - 1) * 20
            py0 = by + 430
            draw.rectangle([px0, py0, px0 + 15, py0 + 15], fill=PALETTE[pi], outline=(70, 82, 105, 255))

    canvas.save(out_path)


if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    v_a = export_vox(model_a, "castle_a.vox")
    v_b = export_vox(model_b, "castle_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: JAPANESE CASTLE -> SHOGUN ROBOT",
        "1. JAPANESE CASTLE (TENSHU)",
        "2. CASTLE SHOGUN ROBOT",
        "preview_castle.png",
        yaw_a=34, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"castle: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
