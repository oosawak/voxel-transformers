import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Sha Wujing / Sagojo (沙悟浄) -> Kappa River-Guardian Robot!
# Kappa-style head dish & hair (河童風の姿), crescent-spade staff (宝杖), neck gourd (首の瓢箪), blue-green palette (青緑基調)!
PALETTE = {
    1: (32, 152, 146, 255),   # Iconic River-Teal / Blue-Green Kappa Armor & Robe (青緑基調)
    2: (20, 96, 98, 255),     # Deep River-Jade Shell, Hair & Shading
    3: (92, 206, 186, 255),   # Bright Mint-Aqua Kappa Skin & Head-Dish Rim
    4: (224, 156, 52, 255),   # Warm Amber-Gold Neck Gourd (瓢箪) & Waist Cord
    5: (178, 92, 34, 255),    # Deep Burnt-Orange Gourd Shading & Crimson Tassel
    6: (218, 228, 236, 255),  # Honed Silver Crescent-Spade Staff Blades (宝杖!)
    7: (116, 76, 44, 255),    # River-Driftwood Staff Pole
    8: (42, 54, 66, 255),     # Deep Slate Frame & Boots
    9: (108, 244, 255, 255),  # Luminous Water-Cyan Dish Core & Eyes!
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


def draw_monk_spade(grid, hx, hy, z_bot, z_top):
    """Draw Sha Wujing's Crescent-Spade Staff (宝杖 — crescent moon at top, flat spade at bottom!)."""
    fill_box(grid, hx, hx, hy, hy, z_bot + 3, z_top - 4, 7)
    # Bottom flat monk spade blade
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_bot, z_bot + 2, 6)
    fill_box(grid, hx, hx, hy, hy, z_bot + 3, z_bot + 3, 4)
    # Top Crescent Moon Blade (月牙鏟!)
    fill_box(grid, hx, hx, hy, hy, z_top - 4, z_top - 3, 4)
    draw_6conn_line(grid, (hx, hy, z_top - 3), (hx - 2, hy, z_top - 2), 6)
    draw_6conn_line(grid, (hx - 2, hy, z_top - 2), (hx - 3, hy, z_top), 6)
    draw_6conn_line(grid, (hx, hy, z_top - 3), (hx + 2, hy, z_top - 2), 6)
    draw_6conn_line(grid, (hx + 2, hy, z_top - 2), (hx + 3, hy, z_top), 6)


# ============================================================
# FORM A: SHA WUJING / SAGOJO CHARACTER (KAPPA MONK) (38 x 24 x 42)
# ============================================================
def build_a():
    grid = np.zeros((38, 24, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18
    cx_r = X // 2      # 19

    # Boots & Teal Monk Trousers (Z: 0..14)
    fill_sym_box(grid, 2, 4, 10, 15, 0, 2, 8)
    fill_sym_box(grid, 2, 4, 11, 14, 3, 14, 1)
    fill_sym_box(grid, 2, 4, 14, 14, 4, 13, 2)

    # Blue-Green Monk Tunic, Kappa Shell Backpack & Neck Gourd (瓢箪!) (Z: 14..29)
    fill_sym_box(grid, 0, 4, 10, 15, 14, 28, 1)
    fill_sym_box(grid, 0, 5, 10, 16, 15, 17, 4)   # Amber waist sash
    fill_sym_box(grid, 0, 1, 16, 16, 16, 26, 2)   # Deep jade lapel
    # Kappa River-Shell on back (Y: 7..10, Z: 16..27)
    fill_sym_box(grid, 0, 4, 8, 10, 16, 27, 2)
    fill_sym_box(grid, 1, 3, 7, 8, 18, 25, 3)     # Mint-aqua shell scales
    # ICONIC PRAYER-BEAD NECKLACE & HANGING NECK GOURD (首の瓢箪!)
    fill_sym_box(grid, 0, 3, 15, 16, 26, 27, 5)   # Red-amber bead necklace
    # Double-bulb gourd hanging cleanly on chest/neck!
    fill_sym_box(grid, 0, 0, 16, 17, 24, 25, 4)   # Upper gourd bulb
    fill_sym_box(grid, 0, 1, 16, 18, 21, 23, 4)   # Lower fat gourd bulb!
    fill_sym_box(grid, 0, 0, 18, 18, 22, 22, 5)   # Gourd waist cord

    # Arms & ICONIC CRESCENT-SPADE STAFF (宝杖!) (Z: 15..41)
    fill_box(grid, cx_l - 7, cx_l - 5, 11, 15, 19, 27, 1)
    fill_box(grid, cx_l - 7, cx_l - 5, 12, 15, 16, 18, 3)   # Mint kappa hand
    fill_box(grid, cx_r + 5, cx_r + 7, 11, 15, 19, 27, 1)
    fill_box(grid, cx_r + 6, cx_r + 9, 14, 17, 18, 21, 3)   # Right hand holding staff
    draw_monk_spade(grid, cx_r + 9, 16, z_bot=2, z_top=40)

    # Kappa Head, Shaggy Hair Ring & Iconic WATER DISH (河童の皿!) (Z: 28..38)
    fill_sym_box(grid, 0, 3, 10, 16, 29, 35, 3)   # Mint-aqua kappa face
    fill_sym_box(grid, 0, 1, 16, 17, 30, 31, 4)   # Subtle kappa beak/mouth
    fill_sym_box(grid, 1, 2, 16, 16, 33, 33, 9)   # Bright water-cyan eyes
    # Shaggy dark-jade kappa hair ring around crown
    fill_sym_box(grid, 0, 4, 9, 15, 34, 36, 2)
    fill_sym_box(grid, 3, 4, 10, 16, 31, 35, 2)   # Side hair
    fill_sym_box(grid, 0, 3, 9, 10, 29, 35, 2)    # Back hair
    # Iconic Flat Water-Dish on Top of Head (河童の皿!)
    fill_sym_box(grid, 0, 2, 11, 15, 36, 37, 3)
    fill_sym_box(grid, 0, 1, 12, 14, 37, 37, 9)   # Shimmering aqua water pool!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: SHA WUJING KAPPA RIVER-GUARDIAN ROBOT (48 x 26 x 46)
# ============================================================
def build_b():
    grid = np.zeros((48, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # Amphibious Webbed Boots & Teal Greaves (Z: 0..15)
    fill_sym_box(grid, 2, 6, 10, 18, 0, 2, 8)
    fill_sym_box(grid, 2, 6, 17, 19, 0, 1, 3)     # Mint webbed flipper-toes!
    fill_sym_box(grid, 2, 5, 11, 16, 3, 13, 1)    # Blue-green river greaves
    fill_sym_box(grid, 3, 4, 16, 17, 4, 12, 3)    # Mint aqua vents
    fill_sym_box(grid, 2, 5, 16, 18, 12, 15, 2)   # Deep jade knee armor
    fill_sym_box(grid, 3, 4, 18, 18, 13, 14, 4)

    # Thighs, River-Armor Waist & Armored Hip-Gourd Pods (Z: 14..23)
    fill_sym_box(grid, 2, 4, 11, 15, 14, 19, 8)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 2)
    fill_sym_box(grid, 1, 5, 15, 17, 17, 21, 1)
    fill_sym_box(grid, 0, 1, 16, 18, 18, 22, 4)   # Amber waist core

    # Teal Cuirass, ARMORED NECK-GOURD CHEST REACTOR & HEAVY KAPPA SHELL BACKPACK! (Z: 22..34)
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 8)
    fill_sym_box(grid, 0, 6, 10, 17, 25, 33, 1)   # Blue-green armored chest
    # Armored Prayer-Bead Collar + Iconic Gourd Reactor Core on Chest! (首の瓢箪!)
    fill_sym_box(grid, 0, 5, 16, 18, 31, 32, 5)   # Armored red-amber collar beads!
    fill_sym_box(grid, 0, 1, 17, 19, 29, 30, 4)   # Upper gourd reactor bulb
    fill_sym_box(grid, 0, 2, 17, 20, 25, 28, 4)   # Lower gourd reactor bulb!
    fill_sym_box(grid, 0, 1, 20, 20, 26, 27, 9)   # Glowing water-energy core inside gourd!
    # HEAVY ARMORED KAPPA SHELL BACKPACK (Y: 5..10, Z: 20..34)
    fill_sym_box(grid, 0, 6, 7, 10, 21, 33, 2)
    fill_sym_box(grid, 1, 5, 6, 7, 23, 31, 3)     # Mint hexagonal shell plate!
    fill_sym_box(grid, 2, 4, 5, 6, 24, 29, 1)
    fill_sym_box(grid, 3, 5, 7, 9, 20, 21, 9)     # Hydro-jet nozzles

    # Shell-Styled Pauldrons, Arms & Giant CRESCENT-SPADE HALBERD (宝杖!) (Z: 14..45)
    fill_sym_box(grid, 6, 8, 12, 15, 28, 32, 8)
    fill_sym_box(grid, 7, 11, 11, 16, 28, 34, 2)  # Deep jade shell pauldrons
    fill_sym_box(grid, 8, 11, 12, 15, 33, 35, 3)  # Mint hydro-fins
    fill_sym_box(grid, 7, 9, 12, 15, 22, 27, 8)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 1)
    fill_box(grid, cx_l - 10, cx_l - 8, 13, 15, 14, 15, 3)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 13, 15, 19, 16, 20, 3)
    draw_monk_spade(grid, cx_r + 13, 18, z_bot=2, z_top=44)

    # Kappa Robot Head: ARMORED WATER-DISH RADAR CROWN! (河童の皿!) (Z: 33..43)
    fill_sym_box(grid, 0, 1, 12, 15, 33, 34, 8)
    fill_sym_box(grid, 0, 3, 11, 17, 34, 40, 3)   # Mint-aqua kappa helm
    fill_sym_box(grid, 0, 2, 17, 18, 34, 36, 4)   # Armored kappa beak mouthplate!
    fill_sym_box(grid, 0, 2, 17, 18, 37, 38, 8)   # Dark visor
    fill_sym_box(grid, 1, 2, 18, 18, 37, 38, 9)   # Luminous cyan eyes!
    fill_sym_box(grid, 3, 4, 11, 16, 35, 40, 2)   # Armored side-hair fins
    # Armored Circular Kappa Water-Dish Radar on Crown!
    fill_sym_box(grid, 0, 4, 10, 17, 40, 41, 2)   # Dish rim
    fill_sym_box(grid, 0, 3, 11, 16, 41, 42, 3)   # Raised dish ring
    fill_sym_box(grid, 0, 2, 12, 15, 42, 42, 9)   # Glowing hydro-dish core!

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
    v_a = export_vox(model_a, "sagojo_a.vox")
    v_b = export_vox(model_b, "sagojo_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #03: SHA WUJING (JOURNEY TO THE WEST) -> KAPPA RIVER ROBOT",
        "1. SHA WUJING (CHARACTER)",
        "2. SHA WUJING ROBOT",
        "preview_sagojo.png",
    )
    print(f"sagojo: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
