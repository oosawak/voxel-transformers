import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Taikobo / Jiang Ziya (太公望・姜子牙) 【封神演義の主役】 -> Grand Taoist-Sage Strategist Robot!
# Fishing rod (釣り竿), Investiture Scroll (封神榜), God-Beating Whip (打神鞭),
# white-haired wise elder (白髪の老人), beard & fishing rod preserved on the Robot!
PALETTE = {
    1: (44, 148, 168, 255),   # Celestial Jade-Cyan Taoist Robe & Armor
    2: (24, 92, 114, 255),    # Deep Teal-Indigo Robe Shading & Hat
    3: (244, 246, 252, 255),  # Pure White Elder Hair, Long White Beard (白髪・髭!) & Inner Robe
    4: (246, 202, 54, 255),   # Radiant Imperial Gold Investiture Scroll (封神榜) & Dashinben Whip!
    5: (168, 112, 42, 255),   # Bamboo Fishing Rod (釣り竿!) & Wooden Trim
    6: (196, 42, 48, 255),    # Crimson Scroll Seal & Waist Ribbon
    7: (54, 62, 82, 255),     # Calm Slate Inner Joints
    8: (250, 222, 198, 255),  # Wise Elder Face
    9: (106, 246, 255, 255),  # Luminous Celestial-Cyan Sage Eyes & Bagua Core!
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


def draw_fishing_rod(grid, hx, hy, z_hand, z_tip):
    """Draw Taikobo's iconic Curved Bamboo Fishing Rod with Straight-Hook Line (釣り竿!)."""
    draw_6conn_line(grid, (hx, hy, z_hand - 2), (hx + 2, hy + 2, z_tip - 5), 5)
    draw_6conn_line(grid, (hx + 2, hy + 2, z_tip - 5), (hx + 5, hy + 5, z_tip), 5)
    # Dangling fishing line with glowing golden baitless straight-pin hook!
    draw_6conn_line(grid, (hx + 5, hy + 5, z_tip), (hx + 5, hy + 5, z_hand - 6), 3)
    fill_box(grid, hx + 5, hx + 5, hy + 5, hy + 5, z_hand - 8, z_hand - 6, 4)


# ============================================================
# FORM A: TAIKOBO / JIANG ZIYA (WHITE-HAIRED TAOIST ELDER) (44 x 28 x 44)
# ============================================================
def build_a():
    grid = np.zeros((44, 28, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21
    cx_r = X // 2      # 22

    # Flowing Celestial-Cyan & Cream Taoist Robe (Z: 0..27)
    fill_sym_box(grid, 1, 4, 10, 15, 0, 1, 2)     # Taoist cloth shoes
    fill_sym_box(grid, 0, 5, 9, 15, 1, 14, 1)     # Flowing jade-cyan lower robe
    fill_sym_box(grid, 0, 5, 9, 15, 1, 2, 4)      # Gold bottom border
    fill_sym_box(grid, 0, 4, 10, 15, 15, 27, 1)   # Upper Taoist robe
    fill_sym_box(grid, 0, 2, 15, 16, 15, 26, 3)   # Pure-white inner Taoist vest
    fill_sym_box(grid, 0, 5, 10, 16, 15, 16, 6)   # Crimson waist sash
    fill_sym_box(grid, 0, 1, 16, 16, 15, 16, 4)   # Gold Yin-Yang buckle
    # ICONIC GOLDEN INVESTITURE SCROLL (封神榜!) slung diagonally across his back!
    draw_6conn_line(grid, (cx_l - 4, 9, 14), (cx_r + 5, 9, 28), 4)
    draw_6conn_line(grid, (cx_l - 4, 8, 14), (cx_r + 5, 8, 28), 4)
    fill_box(grid, cx_l - 5, cx_l - 4, 8, 9, 13, 14, 6)  # Crimson scroll end-caps
    fill_box(grid, cx_r + 5, cx_r + 6, 8, 9, 28, 29, 6)

    # Wide Sleeved Arms: GOD-BEATING WHIP (打神鞭) IN LEFT + FISHING ROD (釣り竿) IN RIGHT!
    fill_box(grid, cx_l - 7, cx_l - 5, 11, 15, 18, 26, 1)
    fill_box(grid, cx_l - 8, cx_l - 6, 14, 17, 18, 20, 8)   # Left hand holding Dashinben Whip!
    # Iconic Segmented Golden God-Beating Whip (打神鞭!)
    fill_box(grid, cx_l - 8, cx_l - 8, 17, 17, 18, 33, 4)
    for wz in range(21, 33, 3):
        fill_box(grid, cx_l - 9, cx_l - 8, 17, 18, wz, wz, 6)  # Whip segments!

    fill_box(grid, cx_r + 5, cx_r + 7, 11, 15, 18, 26, 1)
    fill_box(grid, cx_r + 6, cx_r + 9, 14, 18, 19, 21, 8)   # Right hand holding Fishing Rod!
    draw_fishing_rod(grid, cx_r + 9, 17, z_hand=20, z_tip=41)

    # Wise White-Haired Elder Head, LONG FLOWING WHITE BEARD & Taoist Crown! (Z: 28..40)
    fill_sym_box(grid, 0, 2, 11, 16, 28, 34, 8)   # Kindly elder face
    fill_sym_box(grid, 1, 2, 16, 16, 31, 31, 9)   # Wise calm eyes
    # LONG FLOWING WHITE SAGE BEARD (白髪の老人・長い白髭!)
    fill_sym_box(grid, 0, 1, 16, 17, 18, 29, 3)
    fill_sym_box(grid, 0, 0, 17, 17, 17, 22, 3)
    # Full White Hair & Taoist Sage Cap
    fill_sym_box(grid, 0, 3, 10, 16, 34, 36, 3)   # Pure white hair
    fill_sym_box(grid, 0, 3, 9, 10, 27, 35, 3)    # Long white hair down back
    fill_sym_box(grid, 0, 2, 11, 16, 36, 40, 2)   # Tall Taoist cap
    fill_sym_box(grid, 0, 1, 16, 16, 37, 39, 4)   # Gold Bagua cap badge!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: TAIKOBO GRAND SAGE STRATEGIST ROBOT (髭と釣り竿を残すロボ!) (50 x 28 x 48)
# ============================================================
def build_b():
    grid = np.zeros((50, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 24
    cx_r = X // 2      # 25

    # Celestial-Cyan & Gold Sage Greaves (Z: 0..16)
    fill_sym_box(grid, 2, 5, 10, 17, 0, 2, 2)
    fill_sym_box(grid, 3, 4, 17, 18, 0, 1, 4)
    fill_sym_box(grid, 2, 5, 11, 16, 3, 14, 1)    # Jade-cyan greaves
    fill_sym_box(grid, 3, 4, 16, 17, 4, 13, 3)    # Pure-white inlay
    fill_sym_box(grid, 2, 5, 16, 18, 12, 15, 4)   # Gold Bagua knee shields

    # Flowing Taoist Robe Skirt Tassets (Z: 15..23)
    fill_sym_box(grid, 2, 4, 11, 15, 15, 19, 7)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 2)
    fill_sym_box(grid, 1, 5, 16, 17, 14, 21, 1)
    fill_sym_box(grid, 1, 5, 17, 17, 14, 14, 4)
    fill_sym_box(grid, 0, 1, 16, 18, 16, 22, 6)   # Crimson Taoist sash
    fill_sym_box(grid, 0, 1, 18, 18, 20, 21, 4)

    # Grand Sage Cuirass & GIANT GOLDEN INVESTITURE SCROLL (封神榜) BACKPACK! (Z: 22..38)
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 7)
    fill_sym_box(grid, 0, 6, 10, 17, 25, 33, 1)   # Celestial-cyan chest
    fill_sym_box(grid, 1, 5, 17, 18, 26, 32, 3)   # Pure-white inner chest armor
    fill_sym_box(grid, 0, 2, 18, 19, 27, 31, 4)   # Gold Bagua core frame
    fill_sym_box(grid, 0, 1, 19, 19, 28, 30, 9)   # Glowing sage-cyan core!
    # Giant Golden Investiture Scroll (封神榜!) mounted horizontally across back like a wing-rack!
    fill_sym_box(grid, 0, 4, 8, 10, 25, 33, 2)
    fill_sym_box(grid, 0, 13, 6, 8, 30, 34, 4)    # Giant golden scroll cylinder!
    fill_sym_box(grid, 13, 15, 6, 8, 29, 35, 6)   # Crimson scroll end-caps!
    fill_sym_box(grid, 0, 10, 6, 6, 31, 33, 3)    # Glowing scroll text band

    # Sage Pauldrons, GOD-BEATING WHIP (打神鞭) & ARMORED FISHING ROD (釣り竿!) (Z: 14..46)
    fill_sym_box(grid, 6, 8, 12, 15, 29, 32, 7)
    fill_sym_box(grid, 7, 11, 11, 16, 28, 34, 1)
    fill_sym_box(grid, 8, 12, 12, 15, 33, 35, 4)
    fill_sym_box(grid, 7, 9, 12, 15, 22, 28, 7)
    # Left Arm (-X): Holding Armored Golden God-Beating Whip (打神鞭!)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 1)
    fill_box(grid, cx_l - 11, cx_l - 8, 15, 19, 16, 19, 4)
    fill_box(grid, cx_l - 11, cx_l - 11, 18, 18, 16, 38, 4)  # Long golden Dashinben whip!
    for wz in range(20, 38, 3):
        fill_box(grid, cx_l - 12, cx_l - 11, 18, 19, wz, wz, 6)
    # Right Arm (+X): Holding Armored FISHING ROD (釣り竿を残す!)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 12, 15, 19, 17, 20, 4)
    draw_fishing_rod(grid, cx_r + 12, 18, z_hand=19, z_tip=45)

    # Wise Elder Sage Robot Head WITH LONG ARMORED WHITE BEARD! (ロボでも髭を残す!) (Z: 24..46)
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 7)
    fill_sym_box(grid, 0, 3, 11, 17, 35, 41, 3)   # Pure white sage helm
    fill_sym_box(grid, 0, 2, 17, 18, 37, 38, 2)   # Dark visor
    fill_sym_box(grid, 1, 2, 18, 18, 37, 38, 9)   # Luminous sage-cyan eyes!
    # ICONIC LONG FLOWING ARMORED WHITE BEARD hanging prominently down over chest!
    fill_sym_box(grid, 0, 2, 17, 19, 33, 36, 3)
    fill_sym_box(grid, 0, 1, 18, 20, 26, 34, 3)
    fill_sym_box(grid, 0, 0, 19, 20, 24, 27, 3)
    # Tall Taoist Crown Helm!
    fill_sym_box(grid, 0, 3, 11, 17, 41, 45, 2)
    fill_sym_box(grid, 0, 1, 17, 18, 42, 46, 4)   # Gold Bagua crest!

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
    v_a = export_vox(model_a, "taikobo_a.vox")
    v_b = export_vox(model_b, "taikobo_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #12: TAIKOBO / JIANG ZIYA (FENGSHEN HERO) -> SAGE ROBOT",
        "1. TAIKOBO (CHARACTER)",
        "2. TAIKOBO ROBOT",
        "preview_taikobo.png",
    )
    print(f"taikobo: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
