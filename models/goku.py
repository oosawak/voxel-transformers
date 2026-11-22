import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Sun Wukong / Son Goku (孫悟空) -> Monkey King Robot!
# Ruyi Jingu Bang (如意棒), golden headband (緊箍児), tiger-skin waistcloth (虎の皮の腰巻き),
# monkey ears & curling monkey tail preserved on the Robot!
PALETTE = {
    1: (236, 134, 28, 255),   # Fiery Monkey-King Orange Tunic & Armor
    2: (246, 198, 42, 255),   # Imperial Gold Kinkoji Headband, Staff Caps & Tiger Pelt Base
    3: (196, 30, 38, 255),    # Crimson Ruyi Staff Shaft, Scarf & Trim
    4: (132, 78, 36, 255),    # Warm Monkey Fur Brown (Ears, Tail, Forearms)
    5: (42, 30, 24, 255),     # Dark Espresso Tiger Stripes, Boots & Frame
    6: (250, 212, 178, 255),  # Expressive Monkey Face Peach
    7: (238, 242, 248, 255),  # Crisp Cloud-White Trim & Undershirt
    8: (64, 72, 92, 255),     # Slate Inner Joint Steel
    9: (255, 232, 68, 255),   # Blazing Fiery-Gold Eyes (火眼金睛!)
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


def draw_6conn_line(grid, p0, p1, col, pad=(0, 0, 0)):
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


def draw_ruyi_staff(grid, hx, hy, z_bot, z_top):
    """Draw Sun Wukong's iconic Ruyi Jingu Bang (如意棒 — crimson shaft with golden end-bands)."""
    fill_box(grid, hx, hx, hy, hy, z_bot, z_top, 3)
    fill_box(grid, hx, hx, hy, hy, z_bot, z_bot + 4, 2)
    fill_box(grid, hx, hx, hy, hy, z_top - 4, z_top, 2)
    # Slightly flared golden caps
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_bot, z_bot + 1, 2)
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_top - 1, z_top, 2)


def draw_tiger_belt(grid, x_off0, x_off1, y0, y1, z0, z1):
    """Paint vibrant tiger-skin waistcloth (虎の皮の腰巻き) with dark stripes on golden pelt."""
    fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, 2)
    X = grid.shape[0]
    cx_l, cx_r = X // 2 - 1, X // 2
    for z in range(z0, z1 + 1):
        if (z - z0) % 2 == 1:
            for dx in range(x_off0, x_off1 + 1, 2):
                grid[cx_r + dx, y1, z] = 5
                grid[cx_l - dx, y1, z] = 5
                grid[cx_r + dx, y0, z] = 5
                grid[cx_l - dx, y0, z] = 5


# ============================================================
# FORM A: SUN WUKONG (孫悟空) CHARACTER FIGURE (36 x 24 x 42)
# ============================================================
def build_a():
    grid = np.zeros((36, 24, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 17
    cx_r = X // 2      # 18

    # Agile Martial-Arts Boots & Trousers (Z: 0..13)
    fill_sym_box(grid, 2, 4, 10, 15, 0, 2, 5)     # Dark boots
    fill_sym_box(grid, 2, 4, 11, 14, 3, 5, 7)     # White ankle wraps
    fill_sym_box(grid, 2, 4, 11, 14, 6, 13, 1)    # Saffron martial pants

    # Iconic TIGER-SKIN WAISTCLOTH (虎の皮の腰巻き!) & Curling Monkey Tail (Z: 12..19)
    fill_sym_box(grid, 0, 4, 10, 15, 13, 18, 2)
    draw_tiger_belt(grid, 0, 5, 10, 16, 12, 17)
    fill_sym_box(grid, 0, 5, 10, 16, 18, 18, 3)   # Crimson waist sash!
    # Curling Brown Monkey Tail curving gracefully behind (Y: 4..10)
    tail_pts = [(cx_r, 10, 15), (cx_r + 1, 7, 14), (cx_r + 3, 5, 16), (cx_r + 4, 5, 20), (cx_r + 2, 6, 23)]
    for i in range(len(tail_pts) - 1):
        draw_6conn_line(grid, tail_pts[i], tail_pts[i + 1], 4)

    # Fiery Orange Tunic, Crimson Scarf & Agile Arms (Z: 19..29)
    fill_sym_box(grid, 0, 4, 10, 15, 19, 28, 1)   # Orange tunic
    fill_sym_box(grid, 0, 2, 15, 16, 20, 27, 7)   # White inner lapel
    fill_sym_box(grid, 0, 4, 10, 16, 27, 28, 3)   # Crimson hero scarf!
    fill_sym_box(grid, 0, 2, 8, 10, 22, 27, 3)    # Trailing scarf tails on back
    # Arms
    fill_box(grid, cx_l - 7, cx_l - 5, 11, 15, 21, 27, 1)
    fill_box(grid, cx_l - 7, cx_l - 5, 12, 15, 17, 20, 4)   # Monkey fur forearm
    fill_box(grid, cx_l - 7, cx_l - 5, 12, 15, 16, 16, 6)
    fill_box(grid, cx_r + 5, cx_r + 7, 11, 15, 21, 27, 1)
    fill_box(grid, cx_r + 5, cx_r + 8, 14, 17, 19, 22, 4)   # Right arm gripping staff
    fill_box(grid, cx_r + 7, cx_r + 9, 15, 18, 19, 21, 6)   # Hand holding Ruyi Jingu Bang
    # Iconic RUYI JINGU BANG (如意棒!)
    draw_ruyi_staff(grid, cx_r + 9, 17, z_bot=2, z_top=40)

    # Monkey Head, Monkey Ears, Fiery-Gold Eyes & GOLDEN HEADBAND (緊箍児!) (Z: 28..38)
    fill_sym_box(grid, 0, 3, 10, 16, 29, 36, 4)   # Brown monkey fur head
    fill_sym_box(grid, 0, 2, 15, 17, 29, 34, 6)   # Peach monkey muzzle/face
    fill_sym_box(grid, 1, 2, 17, 17, 32, 33, 9)   # Blazing fiery-gold eyes (火眼金睛!)
    fill_sym_box(grid, 4, 5, 12, 14, 31, 34, 4)   # Prominent Monkey Ears!
    fill_sym_box(grid, 4, 4, 14, 14, 32, 33, 6)   # Inner ear peach
    # Iconic GOLDEN KINKOJI HEADBAND (緊箍児) circling the brow!
    fill_sym_box(grid, 0, 3, 10, 17, 35, 36, 2)
    fill_sym_box(grid, 0, 1, 17, 18, 35, 37, 2)   # Center filigree curl!
    fill_sym_box(grid, 0, 2, 11, 15, 37, 38, 4)   # Spiky monkey tuft on top

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: SUN WUKONG MONKEY KING ROBOT (46 x 26 x 46)
# ============================================================
def build_b():
    grid = np.zeros((46, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 22
    cx_r = X // 2      # 23

    # Agile Mecha Boots & Shin Armor (Z: 0..15)
    fill_sym_box(grid, 2, 5, 10, 17, 0, 2, 5)
    fill_sym_box(grid, 3, 4, 17, 18, 0, 1, 2)     # Gold toe-claws
    fill_sym_box(grid, 2, 5, 11, 16, 3, 13, 1)    # Orange greaves
    fill_sym_box(grid, 3, 4, 16, 17, 4, 12, 7)    # White shin stripe
    fill_sym_box(grid, 2, 5, 15, 17, 12, 15, 3)   # Crimson knee guards
    fill_sym_box(grid, 3, 4, 17, 17, 13, 14, 2)

    # Thighs, Armored TIGER-SKIN SKIRT TASSETS & Mechanical Monkey Tail! (Z: 14..23)
    fill_sym_box(grid, 2, 4, 11, 15, 14, 19, 8)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 5)
    # Tiger-striped front & side armored skirt plates (虎の皮装甲!)
    draw_tiger_belt(grid, 1, 6, 10, 17, 15, 21)
    fill_sym_box(grid, 0, 1, 16, 18, 17, 22, 3)   # Crimson center sash armor
    fill_sym_box(grid, 0, 1, 18, 18, 20, 21, 2)   # Gold buckle
    # Armored Monkey Tail retained on Robot! (猿の尻尾!)
    tail_b = [(cx_r, 10, 20), (cx_r + 2, 6, 19), (cx_r + 5, 4, 21), (cx_r + 6, 4, 26), (cx_r + 4, 5, 30)]
    for i in range(len(tail_b) - 1):
        draw_6conn_line(grid, tail_b[i], tail_b[i + 1], 4, pad=(0, 0, 0))
    fill_box(grid, cx_r + 3, cx_r + 5, 4, 6, 29, 31, 2)  # Golden tail-tip thruster!

    # Monkey King Chest Armor & Cloud-Thruster Backpack (Z: 22..33)
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 8)
    fill_sym_box(grid, 0, 6, 10, 17, 25, 32, 1)   # Fiery orange chest
    fill_sym_box(grid, 1, 5, 17, 18, 26, 31, 2)   # Golden Monkey-King breastplate!
    fill_sym_box(grid, 0, 2, 18, 18, 27, 30, 3)   # Crimson chest emblem
    fill_sym_box(grid, 0, 1, 18, 19, 28, 29, 9)   # Glowing gold core
    fill_sym_box(grid, 0, 4, 7, 10, 25, 32, 3)    # Crimson cloud-jet backpack
    fill_sym_box(grid, 2, 4, 6, 7, 26, 31, 7)     # Kintoun cloud-white thruster vents!

    # Pauldrons, Agile Arms & Colossal RUYI JINGU BANG! (Z: 15..44)
    fill_sym_box(grid, 6, 8, 12, 15, 28, 31, 8)
    fill_sym_box(grid, 7, 11, 11, 16, 28, 33, 1)  # Layered orange pauldrons
    fill_sym_box(grid, 8, 12, 12, 15, 32, 34, 2)  # Gold shoulder crests
    fill_sym_box(grid, 7, 9, 12, 15, 22, 27, 4)   # Brown fur-style upper arm frame
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 1)
    fill_box(grid, cx_l - 10, cx_l - 7, 13, 16, 16, 17, 2)
    fill_box(grid, cx_l - 9, cx_l - 7, 13, 15, 14, 15, 5)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 12, 15, 18, 17, 20, 2)
    fill_box(grid, cx_r + 11, cx_r + 13, 16, 19, 17, 19, 5)
    draw_ruyi_staff(grid, cx_r + 13, 18, z_bot=2, z_top=44)

    # Monkey-King Robot Head: ARMORED MONKEY EARS & GOLDEN KINKOJI CROWN! (Z: 33..43)
    fill_sym_box(grid, 0, 1, 12, 15, 33, 34, 8)
    fill_sym_box(grid, 0, 3, 11, 17, 34, 40, 4)   # Armored brown monkey helm
    fill_sym_box(grid, 0, 2, 17, 18, 34, 36, 7)   # White mouthplate
    fill_sym_box(grid, 0, 2, 17, 18, 37, 38, 5)   # Dark visor slit
    fill_sym_box(grid, 1, 2, 18, 18, 37, 38, 9)   # Fiery-gold robot eyes!
    # Prominent Armored Monkey Ears retained! (猿の耳!)
    fill_sym_box(grid, 4, 6, 12, 15, 35, 39, 4)
    fill_sym_box(grid, 5, 6, 14, 15, 36, 38, 2)   # Gold inner-ear sensor!
    # Golden Kinkoji Headband Antenna-Crown (緊箍児!)
    fill_sym_box(grid, 0, 3, 11, 18, 39, 41, 2)
    fill_sym_box(grid, 0, 1, 18, 19, 40, 43, 2)   # Tall golden centerpiece!
    fill_sym_box(grid, 0, 2, 12, 16, 41, 42, 3)   # Crimson head crest

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: GOLDEN STONE MONKEY / ISHIZARU (石猿 — 猿形態) (30 x 34 x 32)
# ============================================================
def build_c():
    grid = np.zeros((30, 34, 32), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 14
    cx_r = X // 2      # 15

    # Craggy Mountain-Stone Rock Perch grounded at Z=0..3 (石猿の岩座!)
    fill_sym_box(grid, 0, 7, 10, 24, 0, 1, 8)
    fill_sym_box(grid, 0, 6, 12, 22, 2, 2, 5)

    # Agile Crouching Golden-Furred Monkey Limbs (金色の毛並み!) (Z: 2..15)
    fill_sym_box(grid, 3, 5, 12, 17, 2, 4, 6)     # Agile peach monkey hind paws
    fill_sym_box(grid, 3, 5, 11, 15, 5, 11, 2)    # Golden haunches!
    fill_sym_box(grid, 4, 5, 12, 14, 6, 10, 1)    # Fiery-orange golden-fur highlight
    fill_sym_box(grid, 4, 6, 20, 24, 2, 4, 6)     # Front monkey hands gripping rock
    fill_sym_box(grid, 4, 6, 19, 22, 5, 14, 2)    # Golden fur arms
    fill_sym_box(grid, 5, 6, 20, 21, 7, 13, 1)

    # Hunched Agile Golden Monkey Torso & Crimson Scarf Accent (Z: 8..20)
    fill_sym_box(grid, 0, 4, 11, 21, 9, 17, 2)    # Golden-furred monkey body!
    fill_sym_box(grid, 0, 3, 13, 22, 8, 13, 1)    # Warm orange golden belly fur
    fill_sym_box(grid, 0, 4, 13, 21, 17, 18, 1)   # Golden shoulder ruff
    fill_sym_box(grid, 0, 4, 16, 22, 16, 17, 3)   # Crimson Sun-Wukong scarf collar!
    for ty in (13, 16):
        fill_sym_box(grid, 1, 3, ty, ty, 16, 17, 5)

    # LONG CURLING GOLDEN MONKEY TAIL arcing high behind! (尻尾!) (Y: 3..11, Z: 11..29)
    tail_c = [
        (cx_r, 11, 12), (cx_r, 7, 11), (cx_r + 1, 4, 14),
        (cx_r + 2, 3, 20), (cx_r + 1, 5, 26), (cx_r - 1, 7, 28), (cx_r - 1, 9, 26)
    ]
    for i in range(len(tail_c) - 1):
        draw_6conn_line(grid, tail_c[i], tail_c[i + 1], 2 if i % 2 == 0 else 1, pad=(1, 0, 0))

    # Expressive Golden Stone-Monkey Head, Big Monkey Ears & GOLDEN KINKOJI HEADBAND! (Z: 17..29)
    fill_sym_box(grid, 0, 3, 18, 25, 18, 26, 2)   # Golden-furred monkey head!
    fill_sym_box(grid, 0, 2, 24, 28, 18, 24, 6)   # Peach monkey face & protruding muzzle!
    fill_sym_box(grid, 0, 1, 28, 29, 19, 21, 6)   # Cheeky snout
    fill_sym_box(grid, 1, 2, 26, 26, 22, 23, 9)   # Blazing fiery-gold eyes (火眼金睛!)
    fill_sym_box(grid, 4, 6, 20, 23, 20, 24, 2)   # Big Round Monkey Ears!
    fill_sym_box(grid, 4, 5, 23, 23, 21, 23, 6)
    fill_sym_box(grid, 0, 3, 18, 26, 25, 26, 3)   # Crimson brow tie
    fill_sym_box(grid, 0, 3, 19, 26, 26, 27, 2)   # Golden Kinkoji headband!
    fill_sym_box(grid, 0, 1, 26, 27, 26, 28, 2)   # Center filigree!
    fill_sym_box(grid, 0, 2, 19, 24, 27, 29, 1)   # Spiky golden-orange monkey crest!

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
    v_a = export_vox(model_a, "goku_a.vox")
    v_b = export_vox(model_b, "goku_b.vox")
    v_c = export_vox(model_c, "goku_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview(
        [
            ("1. SUN WUKONG (CHARACTER)", model_a, v_a, 28, 18),
            ("2. SUN WUKONG ROBOT", model_b, v_b, 28, 18),
            ("3. STONE MONKEY (BEAST)", model_c, v_c, 40, 20),
        ],
        "CLASSICS ROBO #01: SUN WUKONG (JOURNEY TO THE WEST) - 3-FORM TRANSFORMATION",
        "preview_goku.png",
    )
    print(f"goku: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}), "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}), "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
