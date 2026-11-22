import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Xuanzang / Sanzo Hoshi (三蔵法師) -> Serene White-and-Gold Monk Paladin Robot!
# Sacred Kasaya robe (袈裟), ringed Shakujo staff (錫杖), Vairocana crown, white & gold base (白と金の基調)!
PALETTE = {
    1: (246, 246, 250, 255),  # Pure Sacred White Monk Robe & Armor (白基調)
    2: (212, 218, 232, 255),  # Soft Pearl-Silver Robe Shading
    3: (246, 200, 48, 255),   # Radiant Imperial Gold Kasaya Trim, Crown & Shakujo (金基調)
    4: (196, 148, 28, 255),   # Warm Antique Gold Shading
    5: (204, 38, 44, 255),    # Sacred Crimson Kasaya (袈裟) Diagonal Sash & Crown Panels
    6: (138, 24, 34, 255),    # Deep Ruby Kasaya Fold Shading
    7: (54, 62, 84, 255),     # Calm Slate Inner Joints
    8: (252, 224, 202, 255),  # Serene Gentle Monk Face
    9: (102, 228, 255, 255),  # Pure Luminous Sky-Blue Halo Core & Eyes!
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


def draw_shakujo_staff(grid, hx, hy, z_bot, z_top):
    """Draw Xuanzang's Golden Ringed Shakujo Staff (錫杖 — golden staff with pewter ring loop!)."""
    fill_box(grid, hx, hx, hy, hy, z_bot, z_top - 6, 4)      # Antique gold shaft
    fill_box(grid, hx, hx, hy, hy, z_bot, z_bot + 1, 3)      # Gold butt cap
    # Ornate 6-connected Golden Finial Loop with hanging rings!
    fill_box(grid, hx - 2, hx + 2, hy, hy, z_top - 6, z_top - 5, 3)
    fill_box(grid, hx - 2, hx - 2, hy, hy, z_top - 5, z_top, 3)
    fill_box(grid, hx + 2, hx + 2, hy, hy, z_top - 5, z_top, 3)
    fill_box(grid, hx - 2, hx + 2, hy, hy, z_top, z_top, 3)
    fill_box(grid, hx, hx, hy, hy, z_top + 1, z_top + 2, 3)  # Top lotus spire
    # Hanging jingle rings!
    fill_box(grid, hx - 3, hx - 3, hy, hy, z_top - 4, z_top - 3, 2)
    fill_box(grid, hx + 3, hx + 3, hy, hy, z_top - 4, z_top - 3, 2)


# ============================================================
# FORM A: SANZO HOSHI / XUANZANG CHARACTER (36 x 22 x 44)
# ============================================================
def build_a():
    grid = np.zeros((36, 22, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 17
    cx_r = X // 2      # 18

    # Flowing Pure-White Buddhist Robes (Z: 0..27)
    fill_sym_box(grid, 1, 4, 9, 14, 0, 1, 3)      # Golden slippers peeking out
    fill_sym_box(grid, 0, 5, 8, 14, 1, 14, 1)     # Flowing white lower robe
    fill_sym_box(grid, 0, 5, 8, 14, 1, 2, 3)      # Gold bottom hem!
    fill_sym_box(grid, 0, 4, 9, 14, 15, 27, 1)    # Pure white upper robe
    # Iconic Sacred Crimson & Gold KASAYA (袈裟) draped diagonally across torso!
    for z in range(13, 28):
        shift = (z - 13) // 2
        x0 = max(cx_l - 4, cx_l - 5 + shift)
        x1 = min(cx_r + 4, x0 + 5)
        fill_box(grid, x0, x1, 14, 15, z, z, 5)
        if z % 3 == 0:
            fill_box(grid, x0, x1, 15, 15, z, z, 3)  # Gold kasaya lattice trim!
    # Draped crimson kasaya over back too
    fill_sym_box(grid, 0, 4, 8, 9, 12, 27, 5)
    fill_sym_box(grid, 0, 4, 8, 8, 12, 13, 3)

    # Wide White Sleeves, Prayer Hand & Ringed SHAKUJO STAFF (錫杖!) (Z: 15..42)
    fill_box(grid, cx_l - 7, cx_l - 5, 10, 14, 16, 26, 1)
    fill_box(grid, cx_l - 7, cx_l - 5, 13, 15, 16, 16, 3)
    fill_box(grid, cx_l - 6, cx_l - 4, 14, 16, 18, 20, 8)   # Gentle left hand raised in mudra
    fill_box(grid, cx_r + 5, cx_r + 7, 10, 14, 17, 26, 1)
    fill_box(grid, cx_r + 6, cx_r + 9, 13, 16, 18, 20, 8)   # Right hand holding Shakujo!
    draw_shakujo_staff(grid, cx_r + 9, 15, z_bot=2, z_top=40)

    # Serene Monk Head & Ornate Five-Buddha VAIROCANA CROWN (五仏冠!) (Z: 28..41)
    fill_sym_box(grid, 0, 2, 10, 15, 28, 34, 8)   # Gentle serene face
    fill_sym_box(grid, 1, 2, 15, 15, 31, 31, 9)   # Calm compassionate eyes
    # Tall Ornate White, Gold & Crimson Vairocana Crown (Z: 34..41)
    fill_sym_box(grid, 0, 3, 9, 15, 34, 37, 3)    # Gold crown base
    fill_sym_box(grid, 0, 3, 15, 16, 35, 39, 5)   # Crimson lotus petals!
    fill_sym_box(grid, 0, 1, 16, 16, 36, 41, 3)   # Tall golden central lotus petal
    fill_sym_box(grid, 2, 3, 15, 15, 37, 39, 3)   # Side golden petals
    fill_sym_box(grid, 0, 2, 9, 14, 37, 39, 1)    # Pure white inner miter
    # Flowing white crown ribbons behind shoulders
    fill_sym_box(grid, 2, 3, 8, 9, 25, 34, 1)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: SANZO HOSHI WHITE-AND-GOLD PALADIN ROBOT (46 x 26 x 48)
# ============================================================
def build_b():
    grid = np.zeros((46, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 22
    cx_r = X // 2      # 23

    # Noble Pure-White & Gold Greaves (Z: 0..16)
    fill_sym_box(grid, 2, 5, 10, 17, 0, 2, 3)     # Gold armored boots
    fill_sym_box(grid, 2, 5, 11, 16, 3, 14, 1)    # Crisp pure-white greaves
    fill_sym_box(grid, 3, 4, 16, 17, 4, 13, 3)    # Radiant gold shin inlay
    fill_sym_box(grid, 2, 5, 16, 18, 12, 15, 5)   # Crimson lotus knee shields
    fill_sym_box(grid, 3, 4, 18, 18, 13, 14, 3)

    # Flowing Armored White Robe Tassets (Z: 15..23)
    fill_sym_box(grid, 2, 4, 11, 15, 15, 19, 7)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 1)
    fill_sym_box(grid, 1, 5, 16, 17, 14, 21, 1)   # Long white robe tassets!
    fill_sym_box(grid, 1, 5, 17, 17, 14, 15, 3)   # Gold lower hem
    fill_sym_box(grid, 5, 6, 11, 15, 15, 21, 1)   # Side white plates
    fill_sym_box(grid, 0, 1, 16, 18, 16, 22, 5)   # Crimson front sash
    fill_sym_box(grid, 0, 1, 18, 18, 20, 21, 3)   # Gold buckle

    # Serene White-Gold Chest Cuirass, Armored KASAYA Sash & GOLDEN BACK HALO! (Z: 22..44)
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 7)
    fill_sym_box(grid, 0, 6, 10, 17, 25, 33, 1)   # Pure white paladin chest
    # Diagonal Armored Crimson & Gold Kasaya Sash across chest!
    for z in range(25, 34):
        sx = cx_l - 4 + (z - 25)
        fill_box(grid, sx, min(cx_r + 5, sx + 3), 17, 18, z, z, 5)
    fill_sym_box(grid, 0, 2, 17, 18, 27, 31, 3)   # Gold lotus breastplate!
    fill_sym_box(grid, 0, 1, 18, 19, 28, 30, 9)   # Luminous serene sky-blue core!
    # Radiant Golden Lotus Halo Ring mounted behind back! (光背!)
    fill_sym_box(grid, 0, 4, 7, 10, 25, 33, 1)    # White backpack core
    fill_sym_box(grid, 0, 2, 6, 7, 29, 34, 3)     # Halo strut
    for dy_h, dz_h in [(-9, 36), (-9, 39), (-7, 42), (-4, 44), (0, 45), (4, 44), (7, 42), (9, 39), (9, 36)]:
        pass
    # Clean 6-connected Octagonal Golden Halo Ring at Y=6..7!
    fill_sym_box(grid, 0, 6, 6, 7, 43, 44, 3)     # Halo top bar
    fill_sym_box(grid, 6, 8, 6, 7, 41, 43, 3)
    fill_sym_box(grid, 8, 9, 6, 7, 33, 41, 3)     # Halo side arcs
    fill_sym_box(grid, 6, 8, 6, 7, 30, 33, 3)
    fill_sym_box(grid, 2, 6, 6, 7, 29, 31, 3)     # Connects solidly into backpack!

    # Winged White-Gold Pauldrons & Giant Ringed SHAKUJO STAFF! (Z: 15..46)
    fill_sym_box(grid, 6, 8, 12, 15, 29, 32, 7)
    fill_sym_box(grid, 7, 11, 11, 16, 28, 34, 1)  # Pure white layered pauldrons
    fill_sym_box(grid, 8, 12, 12, 15, 33, 35, 3)  # Radiant gold shoulder trim
    fill_box(grid, cx_l - 11, cx_l - 8, 12, 16, 29, 32, 5)  # Crimson kasaya shoulder drape!
    fill_sym_box(grid, 7, 9, 12, 15, 22, 28, 2)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 1)
    fill_box(grid, cx_l - 10, cx_l - 7, 13, 16, 16, 17, 3)
    fill_box(grid, cx_l - 9, cx_l - 7, 13, 15, 14, 15, 7)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 13, 15, 19, 17, 20, 3)
    draw_shakujo_staff(grid, cx_r + 13, 18, z_bot=2, z_top=45)

    # Noble Monk-Paladin Head & Five-Petal VAIROCANA CROWN! (Z: 34..46)
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 7)
    fill_sym_box(grid, 0, 2, 11, 17, 35, 41, 1)   # White helm
    fill_sym_box(grid, 0, 2, 17, 18, 35, 36, 2)   # Silver mouthplate
    fill_sym_box(grid, 0, 2, 17, 18, 37, 38, 7)   # Dark eye recess
    fill_sym_box(grid, 1, 2, 18, 18, 37, 38, 9)   # Serene luminous blue eyes!
    # Armored Five-Buddha Vairocana Crown!
    fill_sym_box(grid, 0, 3, 11, 18, 40, 43, 3)
    fill_sym_box(grid, 0, 3, 17, 19, 41, 44, 5)   # Crimson lotus panels
    fill_sym_box(grid, 0, 1, 18, 19, 42, 46, 3)   # Tall golden lotus spire!
    fill_sym_box(grid, 3, 4, 16, 18, 42, 45, 3)   # Flared golden side crown petals!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


def draw_6conn_line_c(grid, p0, p1, col, pad=(0, 0, 0)):
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


# ============================================================
# FORM C: WHITE JADE DRAGON PRINCE / GYOKURYU (白い竜 — 白と金の細身の竜) (32 x 32 x 42)
# ============================================================
def build_c():
    grid = np.zeros((32, 32, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = X // 2  # 16

    # Soft Cloud-Lotus Mist Base grounded cleanly at Z=0..2
    fill_box(grid, cx - 7, cx + 6, 11, 21, 0, 1, 2)
    fill_box(grid, cx - 5, cx + 4, 13, 19, 2, 2, 1)

    # Slender Noble White-and-Gold Dragon Spine coiling gracefully upward! (白と金の細身の竜!)
    spine = [
        (cx - 5, 17, 3), (cx - 8, 12, 6), (cx - 2, 9, 10), (cx + 6, 11, 14),
        (cx + 7, 18, 18), (cx + 1, 21, 22), (cx - 5, 18, 26), (cx - 3, 13, 30),
        (cx, 16, 34)
    ]
    for i in range(len(spine) - 1):
        draw_6conn_line_c(grid, spine[i], spine[i + 1], 1, pad=(1, 1, 1))
        p0, p1 = spine[i], spine[i + 1]
        draw_6conn_line_c(grid, (p0[0], p0[1] + 1, p0[2] - 1), (p1[0], p1[1] + 1, p1[2] - 1), 3)
        draw_6conn_line_c(grid, (p0[0], p0[1] - 1, p0[2] + 1), (p1[0], p1[1] - 1, p1[2] + 1), 3)

    # Graceful Slender White-Gold Tail Plume
    draw_6conn_line_c(grid, (cx - 5, 17, 3), (cx - 10, 20, 3), 1, pad=(1, 0, 1))
    draw_6conn_line_c(grid, (cx - 10, 20, 3), (cx - 12, 23, 6), 3)
    fill_box(grid, cx - 13, cx - 11, 23, 25, 5, 8, 5)

    # Slender Dragon Claws + Sacred Lotus Pearl (宝珠!)
    draw_6conn_line_c(grid, (cx + 1, 21, 22), (cx + 6, 25, 21), 1)
    fill_box(grid, cx + 6, cx + 8, 25, 27, 20, 22, 9)
    fill_box(grid, cx + 7, cx + 7, 26, 26, 22, 23, 3)
    draw_6conn_line_c(grid, (cx - 5, 18, 26), (cx - 8, 23, 24), 1)
    fill_box(grid, cx - 9, cx - 7, 23, 24, 23, 24, 3)

    # Refined White Dragon Head, Golden Antlers, Whiskers & Crimson Crest! (Z: 32..41)
    fill_box(grid, cx - 2, cx + 2, 16, 23, 33, 37, 1)
    fill_box(grid, cx - 2, cx + 2, 23, 27, 33, 35, 1)
    fill_box(grid, cx - 1, cx + 1, 22, 26, 32, 33, 3)
    fill_box(grid, cx - 2, cx - 2, 22, 23, 35, 36, 9)
    fill_box(grid, cx + 2, cx + 2, 22, 23, 35, 36, 9)
    fill_box(grid, cx - 1, cx + 1, 19, 22, 37, 39, 5)
    fill_box(grid, cx - 3, cx + 3, 14, 16, 33, 37, 2)
    for sign in (-1, 1):
        draw_6conn_line_c(grid, (cx + sign * 2, 18, 37), (cx + sign * 5, 14, 41), 3)
        draw_6conn_line_c(grid, (cx + sign * 2, 26, 34), (cx + sign * 6, 28, 33), 3)
        draw_6conn_line_c(grid, (cx + sign * 6, 28, 33), (cx + sign * 8, 26, 30), 3)

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


def render_preview(models, title_banner, out_path):
    n = len(models)
    cw = 24 + n * 398 + (n - 1) * 16 + 24
    canvas = Image.new("RGBA", (cw, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, cw, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (cw, gy)], fill=(28, 34, 48, 255), width=1)
    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(models):
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
    v_a = export_vox(model_a, "sanzo_a.vox")
    v_b = export_vox(model_b, "sanzo_b.vox")
    v_c = export_vox(model_c, "sanzo_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview(
        [
            ("1. SANZO HOSHI (CHARACTER)", model_a, v_a, 28, 18),
            ("2. SANZO HOSHI ROBOT", model_b, v_b, 28, 18),
            ("3. WHITE DRAGON (GYOKURYU)", model_c, v_c, 36, 20),
        ],
        "CLASSICS ROBO #04: SANZO HOSHI (JOURNEY TO THE WEST) - 3-FORM TRANSFORMATION",
        "preview_sanzo.png",
    )
    print(f"sanzo: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}), "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}), "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
