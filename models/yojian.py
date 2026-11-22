import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Yang Jian / Yojian (楊戩) -> Three-Eyed Celestial Hound-Knight Robot!
# Three-pointed double-edged glaive (三尖両刃刀), glowing forehead third eye (額の三つ目),
# loyal celestial hound Xiaotian Quan (哮天犬) beside him -> Hound-head pauldron & chest crest on Robot!
PALETTE = {
    1: (228, 236, 248, 255),  # Gleaming Celestial Silver-White Armor
    2: (158, 174, 202, 255),  # Cool Steel-Silver Trim & Glaive Blades
    3: (36, 78, 168, 255),    # Royal Sapphire-Blue Celestial Robe & Cape
    4: (22, 46, 108, 255),    # Deep Midnight-Blue Undersuit & Hound Shading
    5: (244, 198, 52, 255),   # Celestial Gold Crown, Third-Eye Frame & Trim
    6: (44, 42, 54, 255),     # Sleek Black-Silver Fur of Xiaotian Quan (哮天犬!)
    7: (250, 222, 198, 255),  # Noble Young Celestial Face
    8: (196, 36, 46, 255),    # Crimson Collar & Spear Tassel
    9: (102, 242, 255, 255),  # Luminous Celestial-Cyan THIRD EYE (額の三つ目!) & Core!
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


def draw_sanjian_glaive(grid, hx, hy, z_bot, z_top):
    """Draw Yang Jian's iconic Three-Pointed Double-Edged Glaive (三尖両刃刀!)."""
    fill_box(grid, hx, hx, hy, hy, z_bot, z_top - 9, 4)        # Dark-blue steel shaft
    fill_box(grid, hx, hx, hy, hy, z_bot, z_bot + 1, 5)        # Gold butt-cap
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_top - 10, z_top - 9, 5)  # Gold guard
    fill_box(grid, hx, hx, hy - 1, hy - 1, z_top - 12, z_top - 10, 8) # Crimson tassel
    # Central tall spear-blade + Two sharp flanking side-points (三尖!)
    fill_box(grid, hx, hx, hy, hy, z_top - 8, z_top, 1)        # Tall center blade
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_top - 8, z_top - 5, 2)
    fill_box(grid, hx - 2, hx - 2, hy, hy, z_top - 7, z_top - 3, 1)  # Left point!
    fill_box(grid, hx + 2, hx + 2, hy, hy, z_top - 7, z_top - 3, 1)  # Right point!
    fill_box(grid, hx, hx, hy, hy, z_top - 7, z_top - 4, 9)    # Celestial-cyan energy edge!


# ============================================================
# FORM A: YANG JIAN / YOJIAN WITH XIAOTIAN QUAN HOUND (42 x 26 x 46)
# ============================================================
def build_a():
    grid = np.zeros((42, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 20
    cx_r = X // 2      # 21

    # --- 1. YANG JIAN NOBLE SILVER-AND-SAPPHIRE CELESTIAL GENERAL (Z: 0..42) ---
    fill_sym_box(grid, 2, 4, 11, 16, 0, 2, 4)     # Royal blue boots
    fill_sym_box(grid, 2, 4, 12, 15, 3, 14, 1)    # Silver greaves
    fill_sym_box(grid, 3, 4, 15, 15, 4, 13, 5)    # Gold trim
    fill_sym_box(grid, 0, 5, 11, 16, 14, 20, 3)   # Sapphire war-skirt
    fill_sym_box(grid, 0, 4, 16, 16, 14, 15, 5)
    fill_sym_box(grid, 0, 5, 11, 16, 20, 30, 1)   # Silver chest armor
    fill_sym_box(grid, 1, 4, 16, 17, 22, 29, 3)   # Sapphire breastplate inlay
    fill_sym_box(grid, 0, 1, 17, 17, 24, 27, 5)   # Gold celestial seal
    # Flowing Sapphire Celestial Cape on Back
    fill_sym_box(grid, 0, 5, 9, 10, 5, 30, 3)
    fill_sym_box(grid, 0, 5, 9, 9, 5, 6, 5)

    # Shoulders, Arms & THREE-POINTED DOUBLE-EDGED GLAIVE (三尖両刃刀!)
    fill_sym_box(grid, 5, 7, 11, 16, 26, 30, 5)
    fill_box(grid, cx_l - 7, cx_l - 5, 12, 15, 19, 25, 1)
    fill_box(grid, cx_l - 7, cx_l - 5, 13, 15, 17, 18, 7)
    fill_box(grid, cx_r + 5, cx_r + 7, 12, 15, 19, 25, 1)
    fill_box(grid, cx_r + 6, cx_r + 9, 14, 17, 19, 21, 7)
    draw_sanjian_glaive(grid, cx_r + 9, 16, z_bot=2, z_top=44)

    # Noble Young Celestial Head, VERTICAL THIRD EYE (額の三つ目!) & Silver Hair Crown! (Z: 30..42)
    fill_sym_box(grid, 0, 2, 11, 16, 30, 37, 7)   # Handsome young face
    fill_sym_box(grid, 1, 2, 16, 16, 33, 33, 4)   # Sharp eyes
    # ICONIC GLOWING VERTICAL THIRD EYE ON FOREHEAD (額の三つ目!)
    fill_box(grid, cx_l, cx_r, 16, 17, 35, 36, 9)
    fill_box(grid, cx_l, cx_r, 16, 16, 37, 37, 5) # Gold brow arch
    # Silver-gold Celestial Coronet & Flowing Hair!
    fill_sym_box(grid, 0, 3, 10, 16, 37, 39, 6)
    fill_sym_box(grid, 0, 2, 12, 16, 39, 42, 5)   # Gold celestial crown!
    fill_sym_box(grid, 0, 3, 9, 10, 29, 37, 6)

    # --- 2. LOYAL CELESTIAL HOUND XIAOTIAN QUAN (哮天犬!) STANDING AT HIS LEFT SIDE! (Z: 0..12) ---
    hx0 = cx_l - 12  # X: 8..13, connected cleanly to Yang Jian's left boot via ground plinth/paw!
    fill_box(grid, cx_l - 11, cx_l - 2, 11, 15, 0, 0, 2)    # Thin silver ground stone connecting hound & master!
    fill_box(grid, hx0 + 1, hx0 + 4, 10, 16, 1, 7, 6)       # Sleek black-silver hound body!
    fill_box(grid, hx0 + 1, hx0 + 2, 10, 11, 1, 4, 6)       # Hind leg
    fill_box(grid, hx0 + 3, hx0 + 4, 15, 16, 1, 4, 6)       # Front leg
    fill_box(grid, hx0 + 1, hx0 + 4, 15, 17, 6, 7, 8)       # Crimson hound collar!
    fill_box(grid, hx0 + 1, hx0 + 4, 15, 19, 8, 10, 6)      # Alert hound head & snout!
    fill_box(grid, hx0 + 1, hx0 + 1, 16, 16, 11, 12, 6)     # Pointed hound ears!
    fill_box(grid, hx0 + 4, hx0 + 4, 16, 16, 11, 12, 6)
    fill_box(grid, hx0 + 2, hx0 + 3, 19, 19, 9, 9, 9)       # Glowing celestial hound eyes!
    fill_box(grid, hx0 + 2, hx0 + 3, 8, 10, 7, 9, 6)        # Raised tail

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: YANG JIAN THREE-EYED CELESTIAL HOUND-KNIGHT ROBOT (48 x 26 x 48)
# ============================================================
def build_b():
    grid = np.zeros((48, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # Gleaming Silver & Sapphire Greaves (Z: 0..16)
    fill_sym_box(grid, 2, 5, 10, 17, 0, 2, 4)
    fill_sym_box(grid, 3, 4, 17, 18, 0, 1, 5)
    fill_sym_box(grid, 2, 5, 11, 16, 3, 14, 1)    # Gleaming silver greaves
    fill_sym_box(grid, 3, 4, 16, 17, 4, 13, 3)    # Royal sapphire stripe
    fill_sym_box(grid, 2, 5, 16, 18, 12, 15, 5)   # Gold knee guards
    fill_sym_box(grid, 3, 4, 18, 18, 13, 14, 9)

    # Thighs & Celestial Knight Skirt Armor (Z: 15..23)
    fill_sym_box(grid, 2, 4, 11, 15, 15, 19, 6)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 4)
    fill_sym_box(grid, 1, 5, 16, 17, 15, 21, 1)
    fill_sym_box(grid, 1, 5, 17, 17, 15, 15, 5)
    fill_sym_box(grid, 0, 1, 16, 18, 17, 22, 3)
    fill_sym_box(grid, 0, 1, 18, 18, 20, 21, 5)

    # Silver-Sapphire Chest Cuirass & Celestial Cape-Wing Pack (Z: 22..34)
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 6)
    fill_sym_box(grid, 0, 6, 10, 17, 25, 33, 1)   # Gleaming silver chest
    fill_sym_box(grid, 1, 5, 17, 18, 26, 32, 3)   # Sapphire celestial chestplate
    fill_sym_box(grid, 0, 2, 18, 19, 27, 31, 5)   # Gold third-eye chest seal!
    fill_sym_box(grid, 0, 1, 19, 19, 28, 30, 9)   # Luminous vertical cyan chest-eye!
    # Rear Armored Sapphire Celestial Cape
    fill_sym_box(grid, 0, 5, 8, 10, 12, 33, 3)
    fill_sym_box(grid, 0, 5, 8, 8, 12, 13, 5)

    # Asymmetric Pauldrons: ARMORED XIAOTIAN QUAN HOUND-HEAD ON LEFT SHOULDER! (哮天犬の意匠!)
    fill_sym_box(grid, 6, 8, 12, 15, 29, 32, 6)
    # Right Pauldron (+X): Sleek silver-gold celestial pauldron
    fill_box(grid, cx_r + 7, cx_r + 11, 11, 16, 28, 34, 1)
    fill_box(grid, cx_r + 8, cx_r + 12, 12, 15, 33, 35, 5)
    # Left Pauldron (-X): ARMORED HOUND-HEAD OF XIAOTIAN QUAN (哮天犬装甲!)
    fill_box(grid, cx_l - 12, cx_l - 7, 11, 18, 28, 34, 6)   # Sleek black-silver hound head!
    fill_box(grid, cx_l - 11, cx_l - 8, 18, 21, 29, 32, 6)   # Protruding armored hound snout!
    fill_box(grid, cx_l - 11, cx_l - 8, 19, 21, 28, 29, 1)   # Silver lower fang jaw!
    fill_box(grid, cx_l - 11, cx_l - 11, 13, 15, 35, 37, 6)  # Pointed hound ears!
    fill_box(grid, cx_l - 8, cx_l - 8, 13, 15, 35, 37, 6)
    fill_box(grid, cx_l - 11, cx_l - 10, 18, 18, 32, 33, 9)  # Glowing hound eyes!
    fill_box(grid, cx_l - 9, cx_l - 8, 18, 18, 32, 33, 9)
    fill_box(grid, cx_l - 12, cx_l - 7, 12, 16, 28, 28, 8)   # Crimson collar trim!

    # Arms & Giant THREE-POINTED DOUBLE-EDGED GLAIVE (三尖両刃刀!)
    fill_sym_box(grid, 7, 9, 12, 15, 22, 28, 6)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 1)
    fill_box(grid, cx_l - 10, cx_l - 8, 13, 15, 14, 15, 6)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 13, 15, 19, 17, 20, 5)
    draw_sanjian_glaive(grid, cx_r + 13, 18, z_bot=2, z_top=46)

    # Three-Eyed Celestial Robot Head (額の三つ目!) (Z: 34..46)
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 6)
    fill_sym_box(grid, 0, 3, 11, 17, 35, 42, 1)   # Gleaming silver helm
    fill_sym_box(grid, 0, 2, 17, 18, 35, 36, 2)   # Silver faceplate
    fill_sym_box(grid, 0, 2, 17, 18, 37, 38, 4)   # Dark eye visor
    fill_sym_box(grid, 1, 2, 18, 18, 37, 38, 9)   # Two main celestial eyes
    # ICONIC GLOWING VERTICAL THIRD EYE ON FOREHEAD!
    fill_box(grid, cx_l, cx_r, 17, 19, 39, 41, 9)
    fill_sym_box(grid, 0, 3, 12, 18, 41, 43, 5)   # Gold celestial crown!
    fill_sym_box(grid, 0, 1, 17, 18, 43, 46, 5)   # Tall golden crest

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: XIAOTIAN QUAN CELESTIAL HOUND (哮天犬 — 黒い犬) (24 x 40 x 28)
# ============================================================
def build_c():
    grid = np.zeros((24, 40, 28), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 11
    cx_r = X // 2      # 12

    # Four Sleek Agile Black Hound Legs & Silver-White Paws (Z: 0..11)
    for ly0, ly1 in ((10, 13), (24, 27)):
        fill_sym_box(grid, 2, 4, ly0, ly1 + 1, 0, 1, 1)  # Silver-white paws!
        fill_sym_box(grid, 2, 4, ly0, ly1, 2, 11, 6)     # Sleek black hound legs

    # Sleek Muscular Black Celestial Hound Torso & Royal-Sapphire Harness (Z: 9..19)
    fill_sym_box(grid, 0, 4, 10, 28, 10, 17, 6)   # Sleek black hound torso!
    fill_sym_box(grid, 0, 3, 13, 25, 9, 10, 2)    # Silver underbelly fur
    # Yang Jian's Sapphire-and-Gold Celestial Armor Blanket on Back!
    fill_sym_box(grid, 0, 4, 14, 23, 15, 18, 3)
    fill_sym_box(grid, 0, 4, 14, 23, 14, 14, 5)   # Gold trim
    # Crimson Hound Collar with Gold Medallion!
    fill_sym_box(grid, 0, 4, 25, 28, 13, 18, 8)
    fill_sym_box(grid, 0, 1, 28, 29, 13, 15, 5)
    # Alert Curved Black Hound Tail! (Y: 3..10, Z: 15..24)
    fill_sym_box(grid, 0, 1, 7, 10, 15, 17, 6)
    fill_sym_box(grid, 0, 1, 5, 7, 17, 21, 6)
    fill_sym_box(grid, 0, 0, 4, 6, 21, 24, 1)     # Silver tail tip!

    # Fierce Alert Black Hound Head, Pointed Ears & Glowing Third-Eye Gem! (Y: 26..38, Z: 16..27)
    fill_sym_box(grid, 0, 3, 26, 33, 17, 23, 6)   # Noble hound head
    fill_sym_box(grid, 0, 2, 33, 38, 17, 20, 6)   # Long sleek canine snout!
    fill_sym_box(grid, 0, 1, 36, 38, 16, 17, 1)   # Sharp white fangs & jaw!
    fill_sym_box(grid, 2, 3, 32, 33, 20, 21, 9)   # Glowing celestial-cyan eyes!
    fill_box(grid, cx_l, cx_r, 33, 34, 22, 23, 9) # Yang Jian's signature vertical Third-Eye gem!
    fill_sym_box(grid, 2, 3, 27, 29, 23, 27, 6)   # Tall pointed hound ears!
    fill_sym_box(grid, 2, 2, 29, 29, 24, 26, 8)   # Crimson inner ear accent

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
    v_a = export_vox(model_a, "yojian_a.vox")
    v_b = export_vox(model_b, "yojian_b.vox")
    v_c = export_vox(model_c, "yojian_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview(
        [
            ("1. YANG JIAN & XIAOTIAN QUAN", model_a, v_a, 28, 18),
            ("2. YANG JIAN ROBOT", model_b, v_b, 28, 18),
            ("3. XIAOTIAN QUAN (HOUND)", model_c, v_c, 42, 20),
        ],
        "CLASSICS ROBO #11: YANG JIAN / YOJIAN (FENGSHEN) - 3-FORM TRANSFORMATION",
        "preview_yojian.png",
    )
    print(f"yojian: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}), "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}), "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
