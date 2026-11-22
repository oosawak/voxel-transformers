import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Zhuge Liang (諸葛亮) -> Strategist Strategos Robot!
# White Taoist robe (白い道服), crane-feather fan (羽扇), wooden 4-wheel chariot (四輪車) -> wheel & fan armor!
PALETTE = {
    1: (244, 246, 250, 255),  # Crisp Pure-White Taoist Robe, Feather Fan & Armor
    2: (196, 206, 222, 255),  # Cool Silver-White Shading & Feather Ribs
    3: (32, 42, 74, 255),     # Deep Scholar Midnight-Indigo Hat, Trim & Bagua Borders
    4: (64, 92, 152, 255),    # Celestial Strategist Blue Accents
    5: (146, 94, 48, 255),    # Warm Cedar Four-Wheel Chariot Timber & Wheels!
    6: (86, 52, 28, 255),     # Deep Wood Axle & Spokes
    7: (242, 198, 56, 255),   # Imperial Gold Wheel Rims, Fan Handle & Bagua Seal
    8: (250, 222, 200, 255),  # Refined Scholar Face
    9: (76, 218, 246, 255),   # Luminous Azure Strategist Eyes & Core
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


def draw_wheel_yz(grid, x_pos, cy, cz, radius, rim_col=7, wood_col=5, spoke_col=6):
    """Draw a 6-connected spoked wooden-and-gold chariot wheel in the Y-Z plane."""
    X, Y, Z = grid.shape
    for dy in range(-radius, radius + 1):
        for dz in range(-radius, radius + 1):
            d = np.sqrt(dy * dy + dz * dz)
            y, z = cy + dy, cz + dz
            if 0 <= x_pos < X and 0 <= y < Y and 0 <= z < Z:
                if radius - 1.15 <= d <= radius + 0.35:
                    grid[x_pos, y, z] = rim_col if (abs(dy) + abs(dz)) % 2 == 0 else wood_col
                elif d <= 1.2:
                    grid[x_pos, y, z] = rim_col
                elif d < radius - 1.15 and (dy == 0 or dz == 0):
                    grid[x_pos, y, z] = spoke_col


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


# ============================================================
# FORM A: ZHUGE LIANG IN HIS FOUR-WHEEL CHARIOT WITH FEATHER FAN (30 x 34 x 38)
# ============================================================
def build_a():
    grid = np.zeros((30, 34, 38), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 14
    cx_r = X // 2      # 15

    # --- 1. ICONIC WOODEN & GOLD FOUR-WHEEL CHARIOT (四輪車!) (Z: 0..17) ---
    # Four Spoked Wheels grounded at z=0 (2 front + 2 rear!)
    for wy in (9, 23):
        draw_wheel_yz(grid, cx_r + 8, wy, 4, radius=4)
        draw_wheel_yz(grid, cx_l - 8, wy, 4, radius=4)
        # Solid wooden axles connecting both wheels into chassis!
        fill_sym_box(grid, 0, 8, wy, wy, 4, 4, 6)
    # Chariot Deck, Armrests & Ornate Seat Backrest (Y: 6..27, Z: 5..17)
    fill_sym_box(grid, 0, 7, 7, 26, 5, 6, 5)      # Wooden chariot platform
    fill_sym_box(grid, 6, 7, 7, 25, 7, 13, 5)     # Side armrests/railings
    fill_sym_box(grid, 6, 7, 7, 25, 13, 13, 7)    # Gold rail trim
    fill_sym_box(grid, 0, 6, 7, 9, 7, 18, 5)      # High wooden backrest
    fill_sym_box(grid, 0, 5, 7, 7, 18, 19, 7)     # Gold backrest crest
    fill_sym_box(grid, 4, 5, 25, 29, 6, 7, 6)     # Front chariot shafts!

    # --- 2. ZHUGE LIANG SEATED SERENELY IN WHITE TAOIST ROBE (白い道服) (Z: 7..37) ---
    # Seated draped white Taoist robe & knees
    fill_sym_box(grid, 0, 5, 10, 21, 7, 13, 1)    # Crisp white Taoist robe lap
    fill_sym_box(grid, 0, 5, 21, 22, 7, 11, 1)    # Draped lower robe
    fill_sym_box(grid, 0, 5, 22, 22, 7, 7, 3)     # Indigo hem trim
    # Upright torso in White Taoist Robe with Midnight-Indigo Bagua Trim! (Z: 13..25)
    fill_sym_box(grid, 0, 4, 10, 16, 13, 25, 1)
    fill_sym_box(grid, 0, 4, 16, 16, 13, 14, 3)   # Indigo waist sash
    fill_sym_box(grid, 0, 1, 16, 17, 18, 22, 3)   # Indigo Bagua center lapel!
    fill_sym_box(grid, 0, 0, 17, 17, 19, 21, 7)   # Gold yin-yang clasp!
    fill_sym_box(grid, 1, 3, 15, 16, 23, 25, 3)   # Crossed Taoist collar

    # Sleeved Arms & ICONIC WHITE CRANE-FEATHER FAN (羽扇!) (Z: 15..29)
    fill_box(grid, cx_l - 6, cx_l - 4, 11, 16, 16, 24, 1)   # Left wide robe sleeve
    fill_box(grid, cx_l - 6, cx_l - 5, 16, 18, 16, 18, 8)   # Left hand on armrest
    fill_box(grid, cx_r + 4, cx_r + 6, 11, 16, 17, 24, 1)   # Right sleeve raised
    fill_box(grid, cx_r + 5, cx_r + 7, 16, 19, 18, 20, 8)   # Right hand holding fan!
    # White Crane-Feather Fan (羽扇) fanned gracefully upward!
    fx = cx_r + 7
    fill_box(grid, fx, fx, 19, 19, 16, 20, 7)     # Gold fan handle
    for dx_f, dz_f in [(-2, 7), (-1, 9), (0, 10), (1, 9), (2, 7), (3, 5)]:
        draw_6conn_line(grid, (fx, 19, 20), (fx + dx_f, 20, 20 + dz_f), 1)
    fill_box(grid, fx - 1, fx + 2, 20, 20, 22, 25, 2)  # Soft silver feather texture

    # Refined Strategist Head, Short Goatee & Tall Black Guan-Jin Strategist Cap (綸巾)! (Z: 25..37)
    fill_sym_box(grid, 0, 2, 11, 16, 25, 31, 8)   # Scholarly face
    fill_sym_box(grid, 0, 0, 16, 17, 23, 26, 3)   # Neat scholarly goatee!
    fill_sym_box(grid, 1, 2, 16, 16, 29, 29, 9)   # Wise calm eyes
    # Tall Black-Indigo Guan-Jin Hat (綸巾) with gold gem! (Z: 31..37)
    fill_sym_box(grid, 0, 3, 10, 16, 31, 34, 3)
    fill_sym_box(grid, 0, 2, 10, 15, 35, 37, 3)
    fill_sym_box(grid, 0, 1, 16, 16, 32, 34, 7)   # Gold hat ornament!
    fill_sym_box(grid, 0, 2, 9, 10, 26, 32, 3)    # Trailing rear cap ribbon

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: ZHUGE LIANG STRATEGIST ROBOT (50 x 26 x 48)
# Chariot Wheels -> Armored Shoulder Wheels & Ankle Rollers,
# Feather Fan -> Grand Back Crane-Feather Wing-Fan & Handheld Feather Fan!
# ============================================================
def build_b():
    grid = np.zeros((50, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 24
    cx_r = X // 2      # 25

    # --- 1. WHEELED-ANKLE STRATEGIST LEGS & WHITE ROBE GREAVES (Z: 0..16) ---
    fill_sym_box(grid, 2, 5, 10, 17, 0, 2, 3)     # Indigo boots
    fill_sym_box(grid, 2, 5, 11, 16, 3, 14, 1)    # Crisp white Taoist greaves
    fill_sym_box(grid, 3, 4, 16, 16, 4, 13, 4)    # Celestial blue shin inlay
    fill_sym_box(grid, 2, 5, 15, 17, 12, 15, 3)   # Indigo knee shields
    fill_sym_box(grid, 3, 4, 17, 17, 13, 14, 7)   # Gold knee seal
    # LOWER CHARIOT WHEELS mounted cleanly onto outer ankles! (四輪車の車輪!)
    draw_wheel_yz(grid, cx_r + 6, 12, 4, radius=4)
    draw_wheel_yz(grid, cx_l - 6, 12, 4, radius=4)

    # --- 2. THIGHS & LONG WHITE TAOIST ROBE SKIRT-TASSETS (Z: 15..23) ---
    fill_sym_box(grid, 2, 4, 11, 15, 15, 19, 3)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 3)
    fill_sym_box(grid, 1, 5, 15, 16, 14, 21, 1)   # Long flowing white robe front tassets!
    fill_sym_box(grid, 1, 5, 16, 16, 14, 14, 3)   # Indigo bottom robe hem
    fill_sym_box(grid, 5, 6, 11, 15, 15, 21, 1)   # Side white robe plates
    fill_sym_box(grid, 0, 5, 10, 11, 15, 21, 1)   # Rear robe skirt
    fill_sym_box(grid, 0, 1, 15, 17, 16, 22, 3)   # Indigo center Bagua sash
    fill_sym_box(grid, 0, 1, 17, 17, 20, 21, 7)   # Gold waist emblem

    # --- 3. WHITE TAOIST BAGUA CHEST ARMOR (Z: 22..34) ---
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 3)
    fill_sym_box(grid, 0, 6, 10, 16, 25, 33, 1)   # Crisp white Taoist cuirass!
    fill_sym_box(grid, 0, 3, 16, 17, 26, 32, 3)   # Midnight-indigo Bagua breastplate!
    fill_sym_box(grid, 0, 2, 17, 17, 27, 31, 7)   # Gold octagonal Bagua border!
    fill_sym_box(grid, 0, 1, 17, 18, 28, 30, 9)   # Glowing azure strategist core!
    fill_sym_box(grid, 1, 4, 11, 15, 33, 34, 3)   # High indigo Taoist collar

    # --- 4. GRAND BACK MOTIF: FANNED WHITE CRANE-FEATHER FAN WING-HALO! (羽扇が意匠!) (Z: 20..45) ---
    fill_sym_box(grid, 0, 4, 7, 10, 24, 32, 5)    # Cedar chariot-frame backpack
    fill_sym_box(grid, 0, 2, 6, 7, 26, 30, 7)     # Gold Bagua backpack hub
    # 7 Dramatic Radiating White Crane-Feather Fan Blades fanning out behind shoulders!
    fan_tips = [
        (0,  45), (7,  44), (-7,  44), (14, 40), (-14, 40), (19, 34), (-19, 34)
    ]
    for dx_w, z_w in fan_tips:
        bx_w = (cx_r if dx_w >= 0 else cx_l) + dx_w
        ox_w = cx_r if dx_w >= 0 else cx_l
        draw_6conn_line(grid, (ox_w, 7, 29), (bx_w, 6, z_w), 1, pad=(1, 0, 0))
        draw_6conn_line(grid, (ox_w, 6, 29), (bx_w, 5, z_w - 1), 2)
        if abs(dx_w) in (0, 14):
            draw_6conn_line(grid, (ox_w, 7, 29), (int(round((ox_w + bx_w) * 0.5)), 6, int(round((29 + z_w) * 0.5))), 7)

    # --- 5. UPPER CHARIOT-WHEEL SHOULDER PAULDRONS & FEATHER-FAN ARMS! (車輪が肩意匠!) (Z: 15..36) ---
    fill_sym_box(grid, 6, 8, 12, 15, 29, 32, 6)
    fill_sym_box(grid, 7, 10, 11, 16, 28, 33, 1)  # White shoulder armor
    # UPPER TWO SPOKED CHARIOT WHEELS mounted proudly on outer shoulders! (四輪車!)
    draw_wheel_yz(grid, cx_r + 11, 13, 31, radius=4)
    draw_wheel_yz(grid, cx_l - 11, 13, 31, radius=4)
    # Arms
    fill_sym_box(grid, 7, 9, 12, 15, 22, 28, 3)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 1)
    fill_box(grid, cx_l - 10, cx_l - 7, 13, 16, 16, 16, 7)
    fill_box(grid, cx_l - 9, cx_l - 7, 13, 15, 14, 15, 3)
    # Right Arm (+X): Holding an armored Crane-Feather Energy Fan!
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 12, 15, 18, 17, 20, 7)
    fill_box(grid, cx_r + 11, cx_r + 12, 17, 19, 16, 18, 3)
    fx = cx_r + 13
    fill_box(grid, fx, fx, 18, 19, 15, 19, 7)     # Gold fan handle
    for dx_f, dz_f in [(-2, 8), (0, 10), (2, 9), (4, 6)]:
        draw_6conn_line(grid, (fx, 19, 19), (fx + dx_f, 20, 19 + dz_f), 1, pad=(0, 0, 0))
    fill_box(grid, fx - 1, fx + 3, 19, 20, 21, 25, 1)
    fill_box(grid, fx, fx + 2, 20, 20, 22, 24, 9) # Glowing azure feather-fan energy!

    # --- 6. STRATEGIST HEAD & GUAN-JIN CROWN HELM (Z: 34..46) ---
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 3)
    fill_sym_box(grid, 0, 2, 11, 16, 35, 41, 1)   # White helm core
    fill_sym_box(grid, 0, 2, 16, 17, 35, 36, 2)   # Silver jaw plate
    fill_sym_box(grid, 0, 2, 16, 17, 37, 38, 3)   # Indigo eye recess
    fill_sym_box(grid, 1, 2, 17, 17, 37, 38, 9)   # Luminous azure strategist eyes!
    # Tall Armored Midnight-Indigo Guan-Jin Crown (綸巾!) (Z: 39..46)
    fill_sym_box(grid, 0, 3, 11, 17, 39, 42, 3)
    fill_sym_box(grid, 0, 2, 11, 16, 43, 46, 3)
    fill_sym_box(grid, 0, 1, 17, 18, 40, 43, 7)   # Gold forehead Bagua crest!

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=22, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "zhugeliang_a.vox")
    v_b = export_vox(model_b, "zhugeliang_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #03: ZHUGE LIANG (THREE KINGDOMS) -> STRATEGIST ROBOT",
        "1. ZHUGE LIANG (4-WHEEL CHARIOT)",
        "2. ZHUGE LIANG ROBOT",
        "preview_zhugeliang.png",
        yaw_a=38, pitch_a=22, yaw_b=28, pitch_b=18,
    )
    print(f"zhugeliang: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
