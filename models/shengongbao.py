import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shen Gongbao (申公豹) -> Black-Leopard Dark Taoist Robot!
# Dark Taoist riding his sleek Black Leopard (黒豹に乗る道士!), Leopard armor motif & Kaitenju Orb (開天珠!)
PALETTE = {
    1: (28, 28, 40, 255),     # Sleek Obsidian Black Leopard Coat & Armor (黒豹!)
    2: (66, 52, 98, 255),     # Dark Royal-Violet Taoist Robe & Trim
    3: (118, 72, 168, 255),   # Bright Amethyst Leopard Spots & Energy Piping
    4: (242, 198, 56, 255),   # Imperial Gold Taoist Crown, Claws & Orb Frame
    5: (52, 54, 72, 255),     # Dark Gunmetal Inner Joints
    6: (224, 232, 246, 255),  # Gleaming Leopard Fangs & Silver Staff
    7: (246, 218, 198, 255),  # Pale Charismatic Rival Taoist Face
    8: (192, 34, 58, 255),    # Crimson Inner Lining
    9: (255, 198, 62, 255),   # Blazing Golden-Amber KAITENJU ORB (開天珠!) & Leopard Eyes!
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


# ============================================================
# FORM A: SHEN GONGBAO RIDING HIS BLACK LEOPARD (黒豹に乗る道士!) (32 x 36 x 42)
# ============================================================
def build_a():
    grid = np.zeros((32, 36, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 15
    cx_r = X // 2      # 16

    # --- 1. SLEEK BLACK LEOPARD MOUNT (黒豹!) GROUNDED AT Z=0..16 ---
    # Four muscular paws & legs
    fill_sym_box(grid, 2, 4, 21, 25, 0, 2, 1)     # Front paws
    fill_sym_box(grid, 2, 4, 25, 26, 0, 1, 6)     # White claws
    fill_sym_box(grid, 2, 4, 22, 24, 3, 9, 1)     # Front legs
    fill_sym_box(grid, 2, 4, 7, 11, 0, 2, 1)      # Hind paws
    fill_sym_box(grid, 2, 4, 8, 10, 3, 9, 1)      # Hind legs
    # Sleek Black Leopard Torso with Subtle Amethyst Spots! (Y: 8..25, Z: 8..15)
    fill_sym_box(grid, 0, 4, 8, 25, 8, 14, 1)
    fill_sym_box(grid, 4, 4, 11, 22, 10, 13, 3)   # Subtle amethyst rosettes!
    fill_sym_box(grid, 0, 4, 13, 20, 14, 15, 2)   # Royal violet saddle cloth!
    fill_sym_box(grid, 0, 4, 13, 20, 15, 15, 4)   # Gold saddle trim
    # Fierce Black Leopard Head, Pointed Ears & Glowing Amber Eyes! (Y: 25..33, Z: 11..19)
    fill_sym_box(grid, 0, 3, 24, 30, 12, 17, 1)
    fill_sym_box(grid, 0, 2, 30, 33, 12, 14, 1)   # Snout
    fill_sym_box(grid, 0, 1, 32, 33, 12, 12, 6)   # Sharp white fangs
    fill_sym_box(grid, 2, 3, 29, 30, 15, 16, 9)   # Glowing amber predator eyes!
    fill_sym_box(grid, 2, 3, 25, 27, 18, 19, 1)   # Pointed leopard ears
    # Long Whipping Black Leopard Tail curling behind! (Y: 2..8)
    tail_a = [(cx_r, 8, 12), (cx_r, 4, 10), (cx_r + 1, 2, 13), (cx_r + 1, 3, 18)]
    for i in range(len(tail_a) - 1):
        draw_6conn_line(grid, tail_a[i], tail_a[i + 1], 1)

    # --- 2. SHEN GONGBAO SEATED IN DARK-VIOLET TAOIST ROBES HOLDING KAITENJU ORB! (Z: 14..41) ---
    fill_sym_box(grid, 3, 5, 14, 19, 10, 16, 2)   # Rider legs straddling leopard!
    fill_sym_box(grid, 0, 4, 13, 19, 16, 28, 2)   # Dark violet Taoist robe
    fill_sym_box(grid, 0, 2, 19, 20, 17, 27, 1)   # Black front lapel
    fill_sym_box(grid, 0, 1, 20, 20, 20, 25, 4)   # Gold Taoist trim
    fill_sym_box(grid, 0, 4, 12, 13, 16, 28, 1)   # Flowing black cloak
    # Arms: Right hand raising the BLAZING KAITENJU ORB (開天珠!)
    fill_box(grid, cx_l - 6, cx_l - 4, 14, 19, 19, 27, 2)
    fill_box(grid, cx_l - 6, cx_l - 5, 19, 21, 18, 20, 7)
    fill_box(grid, cx_r + 4, cx_r + 6, 14, 19, 21, 28, 2)
    fill_box(grid, cx_r + 5, cx_r + 7, 18, 22, 25, 28, 7)   # Raised hand holding Kaitenju Orb!
    # ICONIC GLOWING KAITENJU ORB (開天珠!)
    fill_box(grid, cx_r + 5, cx_r + 9, 19, 23, 29, 33, 9)   # Radiant golden-amber orb!
    fill_box(grid, cx_r + 6, cx_r + 8, 20, 22, 30, 32, 3)   # Amethyst swirl core!

    # Pale Rival Taoist Head & Ornate Dark-Gold Taoist Crown! (Z: 28..41)
    fill_sym_box(grid, 0, 2, 14, 19, 28, 34, 7)
    fill_sym_box(grid, 1, 2, 19, 19, 31, 32, 9)   # Sharp amber eyes!
    fill_sym_box(grid, 0, 0, 19, 20, 27, 29, 1)   # Thin rival goatee
    fill_sym_box(grid, 0, 3, 13, 19, 34, 37, 1)   # Black hair & cap
    fill_sym_box(grid, 0, 2, 14, 19, 37, 41, 4)   # Tall gold-and-violet Taoist crown!
    fill_sym_box(grid, 0, 1, 19, 19, 38, 40, 3)   # Amethyst crown gem

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: SHEN GONGBAO BLACK-LEOPARD TAOIST ROBOT (48 x 26 x 48)
# ============================================================
def build_b():
    grid = np.zeros((48, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # Sleek Black-Leopard Claw Boots & Agile Greaves (Z: 0..16)
    fill_sym_box(grid, 2, 5, 10, 17, 0, 2, 1)
    fill_sym_box(grid, 2, 5, 17, 19, 0, 1, 6)     # Sharp silver leopard claws!
    fill_sym_box(grid, 2, 5, 11, 16, 3, 14, 1)    # Sleek obsidian greaves
    fill_sym_box(grid, 3, 4, 16, 17, 4, 13, 3)    # Amethyst leopard spots/piping
    fill_sym_box(grid, 2, 5, 16, 18, 12, 15, 4)   # Gold knee guards

    # Waist Armor & LONG WHIPPING BLACK LEOPARD TAIL! (Z: 15..24)
    fill_sym_box(grid, 2, 4, 11, 15, 15, 19, 5)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 2)
    fill_sym_box(grid, 1, 5, 16, 17, 15, 21, 2)   # Violet Taoist robe tassets
    fill_sym_box(grid, 1, 5, 17, 17, 15, 15, 4)
    fill_sym_box(grid, 0, 1, 16, 18, 17, 22, 8)
    fill_sym_box(grid, 0, 1, 18, 18, 20, 21, 4)
    # Sleek Armored Black Leopard Tail!
    tail_b = [(cx_l, 11, 20), (cx_l - 3, 6, 18), (cx_l - 7, 4, 21), (cx_l - 9, 5, 27)]
    for i in range(len(tail_b) - 1):
        draw_6conn_line(grid, tail_b[i], tail_b[i + 1], 1)
    fill_box(grid, cx_l - 10, cx_l - 8, 4, 6, 26, 28, 3)  # Amethyst tail blade!

    # ARMORED BLACK LEOPARD HEAD CHESTPLATE! (黒豹の意匠!) (Z: 22..34)
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 5)
    fill_sym_box(grid, 0, 6, 10, 17, 25, 33, 1)   # Sleek obsidian chest
    # Protruding Black Leopard Head sculpted right onto chest!
    fill_sym_box(grid, 0, 3, 17, 20, 26, 32, 1)   # Leopard chest head!
    fill_sym_box(grid, 0, 2, 19, 21, 26, 28, 6)   # Silver leopard fangs!
    fill_sym_box(grid, 2, 3, 20, 20, 30, 31, 9)   # Glowing amber leopard chest-eyes!
    fill_sym_box(grid, 2, 3, 18, 19, 32, 34, 1)   # Leopard ears on chest collar!
    fill_sym_box(grid, 0, 4, 8, 10, 25, 33, 2)    # Dark-violet Taoist cloak pack
    fill_sym_box(grid, 0, 5, 7, 8, 12, 32, 2)

    # Leopard-Spot Pauldrons, Claws & BLAZING KAITENJU ORB STAFF (開天珠!) (Z: 15..45)
    fill_sym_box(grid, 6, 8, 12, 15, 29, 32, 5)
    fill_sym_box(grid, 7, 11, 11, 16, 28, 34, 1)  # Obsidian feline pauldrons
    fill_sym_box(grid, 8, 11, 12, 15, 33, 35, 3)  # Amethyst highlights
    fill_sym_box(grid, 10, 12, 13, 15, 34, 36, 4) # Gold claws
    fill_sym_box(grid, 7, 9, 12, 15, 22, 28, 5)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 2)
    fill_box(grid, cx_l - 10, cx_l - 8, 13, 16, 13, 15, 6)  # Triple silver leopard claws!
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 2)
    fill_box(grid, cx_r + 9, cx_r + 13, 15, 19, 17, 20, 4)
    # KAITENJU ORB SCEPTER (開天珠!) held prominently in right hand!
    fill_box(grid, cx_r + 13, cx_r + 13, 18, 18, 4, 36, 6)  # Silver staff
    fill_box(grid, cx_r + 11, cx_r + 15, 16, 20, 37, 41, 9) # GIANT BLAZING KAITENJU ORB!
    fill_box(grid, cx_r + 12, cx_r + 14, 17, 19, 38, 40, 3) # Amethyst core glow!
    fill_box(grid, cx_r + 11, cx_r + 15, 18, 18, 36, 36, 4) # Gold orb cradle!

    # Black-Leopard Taoist Robot Head WITH POINTED FELINE EARS & GOLD CROWN! (Z: 34..46)
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 5)
    fill_sym_box(grid, 0, 3, 11, 17, 35, 41, 1)   # Sleek obsidian helm
    fill_sym_box(grid, 0, 2, 17, 18, 35, 36, 5)   # Dark mask
    fill_sym_box(grid, 1, 2, 18, 18, 37, 38, 9)   # Sharp amber predator eyes!
    fill_sym_box(grid, 2, 3, 13, 16, 41, 44, 1)   # Armored Black-Leopard Ears!
    fill_sym_box(grid, 0, 2, 13, 18, 41, 45, 4)   # Tall gold Taoist crown!
    fill_sym_box(grid, 0, 1, 18, 18, 42, 44, 3)   # Amethyst brow gem

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: SLEEK BLACK LEOPARD (黒豹 — 豹形態!) (24 x 44 x 26)
# ============================================================
def build_c():
    grid = np.zeros((24, 44, 26), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 11
    cx_r = X // 2      # 12

    # Four Lithe Muscular Black Leopard Legs & Silver Claws (Z: 0..10)
    for ly0, ly1 in ((10, 13), (26, 29)):
        fill_sym_box(grid, 2, 4, ly0, ly1 + 1, 0, 1, 1)
        fill_sym_box(grid, 2, 4, ly1 + 1, ly1 + 2, 0, 0, 6)  # Razor silver leopard claws!
        fill_sym_box(grid, 2, 4, ly0, ly1, 2, 10, 1)         # Lithe obsidian legs

    # Sleek Prowling Black Leopard Body with Subtle Amethyst Rosettes! (Z: 8..17)
    fill_sym_box(grid, 0, 4, 10, 31, 9, 15, 1)    # Long sleek obsidian feline torso!
    # Subtle dark-amethyst leopard spots along flanks!
    for sy, sz in ((13, 13), (18, 11), (22, 14), (26, 12)):
        fill_sym_box(grid, 4, 4, sy, sy + 1, sz, sz + 1, 3)
    # Shen Gongbao's Royal-Violet & Gold Collar with Blazing KAITENJU ORB Pendant!
    fill_sym_box(grid, 0, 4, 27, 30, 11, 16, 2)
    fill_sym_box(grid, 0, 1, 30, 32, 9, 12, 9)    # Glowing golden-amber Kaitenju Orb pendant!
    fill_sym_box(grid, 0, 1, 30, 31, 12, 13, 4)   # Gold collar clasp
    # Long Whipping Arched Black Leopard Tail! (Y: 1..10, Z: 10..23)
    tail_c = [(cx_r, 10, 14), (cx_r, 6, 11), (cx_r, 3, 13), (cx_r, 2, 18), (cx_r, 4, 22)]
    for i in range(len(tail_c) - 1):
        draw_6conn_line(grid, tail_c[i], tail_c[i + 1], 1)
        draw_6conn_line(grid, (tail_c[i][0] - 1, tail_c[i][1], tail_c[i][2]),
                        (tail_c[i + 1][0] - 1, tail_c[i + 1][1], tail_c[i + 1][2]), 1)
    fill_box(grid, cx_l, cx_r, 3, 5, 21, 23, 3)   # Amethyst tail tip!

    # Fierce Prowling Black Leopard Head, Bared Fangs & Amber Predator Eyes! (Y: 29..41, Z: 12..23)
    fill_sym_box(grid, 0, 3, 29, 36, 13, 19, 1)   # Sleek feline cranium
    fill_sym_box(grid, 0, 2, 36, 40, 13, 16, 1)   # Predator muzzle
    fill_sym_box(grid, 0, 2, 38, 40, 12, 13, 6)   # Gleaming silver leopard fangs!
    fill_sym_box(grid, 2, 3, 35, 36, 16, 17, 9)   # Piercing glowing golden-amber eyes!
    fill_sym_box(grid, 2, 3, 30, 32, 19, 22, 1)   # Rounded feline ears!
    fill_sym_box(grid, 2, 2, 32, 32, 20, 21, 3)   # Amethyst inner ear highlight

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
    v_a = export_vox(model_a, "shengongbao_a.vox")
    v_b = export_vox(model_b, "shengongbao_b.vox")
    v_c = export_vox(model_c, "shengongbao_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview(
        [
            ("1. SHEN GONGBAO ON BLACK LEOPARD", model_a, v_a, 38, 20),
            ("2. SHEN GONGBAO ROBOT", model_b, v_b, 28, 18),
            ("3. BLACK LEOPARD (BEAST)", model_c, v_c, 44, 20),
        ],
        "CLASSICS ROBO #16: SHEN GONGBAO (FENGSHEN) - 3-FORM TRANSFORMATION",
        "preview_shengongbao.png",
    )
    print(f"shengongbao: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}), "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}), "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
