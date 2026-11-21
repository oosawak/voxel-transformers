import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across all 3 forms (Normal Robot -> Power-Up Robot -> One-Eyed Dragon)
PALETTE = {
    1: (34, 58, 118, 255),    # Deep Date Navy / Midnight Blue Armor (紺)
    2: (64, 102, 178, 255),   # Highlight Indigo Armor Bevels & Dragon Scales
    3: (244, 200, 48, 255),   # Rich Gold Crescent Crest, Trim & Dragon Horns (金)
    4: (184, 134, 24, 255),   # Burnished Antique Gold Shading & Belly Plates
    5: (36, 40, 52, 255),     # Black Lacquer Armor, Eyepatch & Inner Joints (黒)
    6: (204, 38, 46, 255),    # Crimson Samurai Lacing Cords & Accents (赤)
    7: (240, 242, 248, 255),  # Crisp White Collar/Obi Accents, Claws & Fangs (白)
    8: (176, 188, 204, 255),  # Honed Silver Katana/Odachi Steel & Pistons
    9: (255, 176, 26, 255),   # Blazing Glowing Amber-Gold Eye & Energy Cores (独眼)
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(int(x0), int(x1))), min(X - 1, max(int(x0), int(x1)))
    y0, y1 = max(0, min(int(y0), int(y1))), min(Y - 1, max(int(y0), int(y1)))
    z0, z1 = max(0, min(int(z0), int(z1))), min(Z - 1, max(int(z0), int(z1)))
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center (requires even X)."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


def fill_sphere_local(grid, cx, cy, cz, rx, ry, rz, col):
    """Fill an ellipsoid centered at (cx, cy, cz)."""
    X, Y, Z = grid.shape
    x0 = max(0, int(np.floor(cx - rx)))
    x1 = min(X - 1, int(np.ceil(cx + rx)))
    y0 = max(0, int(np.floor(cy - ry)))
    y1 = min(Y - 1, int(np.ceil(cy + ry)))
    z0 = max(0, int(np.floor(cz - rz)))
    z1 = min(Z - 1, int(np.ceil(cz + rz)))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                d2 = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                if d2 <= 1.0:
                    grid[x, y, z] = col


def draw_6conn_line(grid, p0, p1, col, pad=(0, 0, 0), only_empty=False):
    """Draw a guaranteed 6-connected line between 3D points p0 and p1."""
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


def hollow_interior_26(grid, z_min, z_max):
    """Hollow strictly interior voxels (all 26 neighbors occupied) to preserve 6-connectivity."""
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


def check_6_connected(grid):
    """Return number of 6-connected components and min Z."""
    xs, ys, zs = np.nonzero(grid)
    if len(xs) == 0:
        return 0, -1
    occupied = set(zip(xs.tolist(), ys.tolist(), zs.tolist()))
    visited = set()
    components = 0
    for start in occupied:
        if start in visited:
            continue
        components += 1
        q = deque([start])
        visited.add(start)
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nb = (x + dx, y + dy, z + dz)
                if nb in occupied and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
    return components, int(zs.min())


def draw_crescent_crest(grid, cx_l, cx_r, y_front, z_base, right_span, left_span,
                        right_height, left_height, blazing=False):
    """Draw Date Masamune's iconic asymmetrical sweeping golden crescent moon (三日月前立て)."""
    # Sleek center mount tucked cleanly onto kabuto brow
    fill_box(grid, cx_l, cx_r, y_front - 1, y_front, z_base, z_base + 1, 4)
    fill_box(grid, cx_l, cx_r, y_front, y_front, z_base, z_base + 1, 3)

    # Right horn (+X, viewer's left): iconic wide sweeping asymmetrical crescent arm!
    r_pts = []
    n_r = 28
    for i in range(n_r + 1):
        t = i / n_r
        # Sweeps far outward first, then curves gracefully upward & slightly inward at tip!
        x = cx_r + 0.4 + right_span * (np.sin(t * np.pi * 0.58) / np.sin(np.pi * 0.58))
        z = z_base + 0.3 + right_height * (t ** 1.95)
        y = y_front - (1 if t > 0.72 else 0)
        r_pts.append((x, y, z))

    for i in range(len(r_pts) - 1):
        t = i / (len(r_pts) - 1)
        col_main = 9 if (blazing and t > 0.80) else 3
        col_bevel = 4 if t < 0.65 else col_main
        p0, p1 = r_pts[i], r_pts[i + 1]
        draw_6conn_line(grid, p0, p1, col_main)
        if t < 0.68:
            draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), col_bevel)
        if t < 0.38:
            draw_6conn_line(grid, (p0[0], p0[1] - 1, p0[2]), (p1[0], p1[1] - 1, p1[2]), 4)

    # Left horn (-X, viewer's right): shorter asymmetrical Date Masamune crescent arm!
    l_pts = []
    n_l = 20
    for i in range(n_l + 1):
        t = i / n_l
        x = cx_l - 0.4 - left_span * (np.sin(t * np.pi * 0.58) / np.sin(np.pi * 0.58))
        z = z_base + 0.3 + left_height * (t ** 1.85)
        y = y_front - (1 if t > 0.72 else 0)
        l_pts.append((x, y, z))

    for i in range(len(l_pts) - 1):
        t = i / (len(l_pts) - 1)
        col_main = 9 if (blazing and t > 0.82) else 3
        col_bevel = 4 if t < 0.62 else col_main
        p0, p1 = l_pts[i], l_pts[i + 1]
        draw_6conn_line(grid, p0, p1, col_main)
        if t < 0.62:
            draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), col_bevel)
        if t < 0.35:
            draw_6conn_line(grid, (p0[0], p0[1] - 1, p0[2]), (p1[0], p1[1] - 1, p1[2]), 4)


# ============================================================
# FORM A: DATE MASAMUNE ROBOT - NORMAL (40 x 26 x 45)
# ============================================================
def build_a():
    grid = np.zeros((40, 26, 45), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 19 (-X, robot left / viewer's right)
    cx_r = X // 2      # 20 (+X, robot right / viewer's left)

    # --- GROUNDED SAMURAI ARMORED BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 2, 5, 9, 17, 0, 1, 5)    # Black lacquer heavy sole
    fill_sym_box(grid, 3, 5, 8, 9, 0, 2, 5)     # Heel counterweight
    fill_sym_box(grid, 2, 5, 10, 17, 1, 2, 1)   # Deep navy foot armor
    fill_sym_box(grid, 2, 5, 17, 18, 1, 2, 3)   # Gold upturned samurai toe-cap
    fill_sym_box(grid, 3, 4, 16, 17, 2, 2, 2)   # Indigo foot bevel
    fill_sym_box(grid, 3, 4, 10, 15, 3, 3, 7)   # Crisp white tabi ankle wrap
    fill_sym_box(grid, 2, 5, 11, 15, 3, 3, 6)   # Crimson ankle cord tie
    fill_sym_box(grid, 3, 4, 11, 14, 3, 4, 5)   # Black ankle joint

    # --- LOWER LEGS / SUNEATE GREAVES (Z: 4..14) ---
    fill_sym_box(grid, 2, 5, 10, 15, 4, 13, 1)  # Deep navy armored greaves
    fill_sym_box(grid, 3, 4, 15, 16, 5, 11, 2)  # Indigo shin ridge
    fill_sym_box(grid, 2, 2, 11, 14, 5, 12, 5)  # Black lacquer inner shin
    fill_sym_box(grid, 5, 6, 11, 14, 5, 11, 1)  # Outer calf armor fin
    fill_sym_box(grid, 6, 6, 11, 13, 6, 10, 2)  # Indigo calf trim
    # Crimson suneate horizontal lacing cords
    fill_sym_box(grid, 2, 5, 10, 15, 6, 6, 6)
    fill_sym_box(grid, 2, 5, 10, 15, 9, 9, 6)
    # Rear calf vernier detail
    fill_sym_box(grid, 3, 4, 9, 10, 6, 10, 5)
    fill_sym_box(grid, 3, 4, 9, 9, 7, 9, 8)
    # Samurai Knee Armor (Tateage) with Gold Crest
    fill_sym_box(grid, 2, 5, 14, 16, 11, 14, 1)
    fill_sym_box(grid, 3, 4, 15, 17, 12, 14, 3)
    fill_sym_box(grid, 3, 4, 17, 17, 13, 13, 4)

    # --- THIGHS (Z: 14..18) ---
    fill_sym_box(grid, 2, 4, 10, 14, 14, 18, 5) # Black lacquer thigh base
    fill_sym_box(grid, 2, 5, 12, 14, 15, 17, 1) # Navy front thigh plate
    fill_sym_box(grid, 3, 4, 14, 15, 15, 17, 2) # Indigo highlight
    fill_sym_box(grid, 5, 5, 11, 13, 15, 17, 7) # White inner accent stripe

    # --- WAIST & KUSAZURI SAMURAI SKIRT TASSETS (Z: 17..22) ---
    fill_sym_box(grid, 0, 5, 10, 14, 19, 22, 5) # Pelvis black lacquer core
    # Front & back flared kusazuri tassets
    fill_sym_box(grid, 1, 5, 14, 15, 17, 20, 1)
    fill_sym_box(grid, 1, 5, 15, 15, 19, 19, 6) # Crimson lacing stripe
    fill_sym_box(grid, 1, 5, 15, 15, 17, 17, 3) # Gold bottom tasset hem
    fill_sym_box(grid, 0, 5, 9, 10, 17, 20, 1)  # Rear kusazuri skirt
    fill_sym_box(grid, 0, 5, 9, 9, 19, 19, 6)
    fill_sym_box(grid, 0, 5, 9, 9, 17, 17, 3)
    # Side hip kusazuri plates
    fill_sym_box(grid, 5, 6, 10, 14, 17, 20, 1)
    fill_sym_box(grid, 6, 6, 11, 13, 19, 19, 6)
    fill_sym_box(grid, 6, 6, 11, 13, 17, 17, 3)
    # Center white obi sash, crimson waist cord & gold medallion
    fill_sym_box(grid, 0, 5, 14, 15, 21, 21, 7) # Crisp white obi belt
    fill_sym_box(grid, 0, 1, 14, 16, 19, 21, 6) # Crimson front sash knot
    fill_sym_box(grid, 0, 0, 15, 16, 18, 19, 1)
    fill_sym_box(grid, 0, 0, 16, 16, 21, 21, 3) # Gold waist buckle

    # Left Waist Slung Katana Scabbard (Saya) (-X, viewer's right)
    draw_6conn_line(grid, (cx_l - 7, 7, 21), (cx_l - 7, 17, 17), 5)
    draw_6conn_line(grid, (cx_l - 6, 11, 19), (cx_l - 7, 12, 19), 6) # Crimson sageo cord tie
    fill_box(grid, cx_l - 7, cx_l - 7, 7, 7, 21, 21, 3)              # Gold kojiri tip
    fill_box(grid, cx_l - 7, cx_l - 7, 17, 17, 17, 17, 3)            # Gold koiguchi mouth

    # --- TORSO / YUKINOSHITA-DO SAMURAI CUIRASS (Z: 22..31) ---
    fill_sym_box(grid, 0, 4, 10, 14, 22, 24, 5) # Black lacquer abs
    fill_sym_box(grid, 0, 3, 14, 15, 22, 24, 1) # Navy abdominal plate
    fill_sym_box(grid, 0, 2, 15, 15, 23, 23, 6) # Crimson waist lacing
    # Broad Samurai Chest
    fill_sym_box(grid, 0, 6, 9, 15, 25, 30, 1)  # Deep navy chest core
    fill_sym_box(grid, 0, 5, 15, 16, 25, 30, 5) # Black lacquer Yukinoshita cuirass
    fill_sym_box(grid, 1, 5, 15, 16, 26, 29, 1) # Navy pectoral armor plates
    fill_sym_box(grid, 2, 5, 16, 16, 27, 29, 2) # Indigo angled chest bevel
    # Crimson vertical samurai lacing cords & refined gold trim
    fill_sym_box(grid, 2, 2, 16, 16, 25, 29, 6)
    fill_sym_box(grid, 0, 5, 16, 16, 25, 25, 3) # Gold lower chest trim
    fill_sym_box(grid, 0, 1, 16, 16, 28, 29, 3) # Gold Date chest crest
    fill_sym_box(grid, 0, 0, 16, 16, 28, 28, 4)
    # Crisp white samurai collar lapels framing the neck
    fill_sym_box(grid, 1, 3, 13, 15, 30, 31, 7)
    fill_sym_box(grid, 0, 5, 10, 13, 30, 31, 1)
    fill_sym_box(grid, 2, 5, 11, 14, 31, 31, 3) # Gold collarbone trim

    # --- COMPACT FOLDED DRAGON-WING BACKPACK (Y: 4..9, Z: 21..34) ---
    fill_sym_box(grid, 0, 4, 7, 9, 23, 30, 5)   # Black lacquer back housing
    fill_sym_box(grid, 0, 3, 6, 7, 25, 29, 1)   # Navy central pack
    fill_sym_box(grid, 0, 1, 6, 6, 27, 28, 3)   # Gold spine emblem
    fill_sym_box(grid, 2, 3, 6, 7, 23, 24, 8)   # Silver lower thruster nozzles
    # Compact folded navy-and-gold wing-binders (foreshadowing Form B's wings!)
    for i in range(12):
        z_w = 22 + i
        x_w = 4 + i // 4
        y_w = 5 - i // 6
        fill_sym_box(grid, x_w, x_w + 1, y_w, y_w + 2, z_w, z_w, 1)
        fill_sym_box(grid, x_w + 1, x_w + 1, y_w, y_w + 1, z_w, z_w, 2 if i % 2 == 0 else 3)
    fill_sym_box(grid, 6, 7, 4, 5, 33, 34, 3)   # Folded gold wingtips
    fill_sym_box(grid, 2, 3, 7, 8, 26, 28, 6)   # Crimson backpack cord straps

    # --- SHOULDERS (LAYERED SAMURAI SODE) & ARMS (Z: 14..32) ---
    fill_sym_box(grid, 6, 8, 11, 13, 27, 30, 5) # Shoulder joint core
    # Tiered Sode shoulder pauldrons
    fill_sym_box(grid, 7, 10, 10, 15, 27, 31, 1)
    fill_sym_box(grid, 7, 10, 10, 15, 31, 31, 3) # Gold top trim
    fill_sym_box(grid, 10, 10, 10, 15, 29, 29, 6) # Crimson odoshi cord
    fill_sym_box(grid, 10, 10, 10, 15, 27, 27, 3) # Gold lower rim
    fill_sym_box(grid, 8, 10, 15, 15, 28, 30, 2) # Indigo front bevel
    fill_sym_box(grid, 7, 9, 11, 14, 32, 32, 2)  # Upper cap
    # Upper arms
    fill_sym_box(grid, 7, 8, 11, 13, 22, 26, 5)
    fill_sym_box(grid, 8, 8, 11, 13, 23, 25, 6)  # Crimson arm lacing

    # Left Arm (-X, viewer's right): Armored Kote Forearm & Fist
    fill_box(grid, cx_l - 9, cx_l - 7, 11, 15, 16, 21, 1)
    fill_box(grid, cx_l - 9, cx_l - 9, 12, 14, 17, 20, 2)
    fill_box(grid, cx_l - 9, cx_l - 7, 12, 15, 16, 16, 3) # Gold wrist cuff
    fill_box(grid, cx_l - 8, cx_l - 7, 12, 14, 14, 15, 5) # Black armored fist

    # Right Arm (+X, viewer's left): Angled slightly outward & forward wielding DRAWN KATANA!
    fill_box(grid, cx_r + 7, cx_r + 9, 11, 15, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 11, 13, 16, 16, 19, 1)
    fill_box(grid, cx_r + 10, cx_r + 11, 14, 16, 16, 18, 3) # Gold wrist cuff
    fill_box(grid, cx_r + 10, cx_r + 11, 15, 17, 15, 17, 5) # Gripping fist

    # Drawn Samurai Katana (sweeping boldly OUTWARD +X and UPWARD clear of body!)
    fill_box(grid, cx_r + 11, cx_r + 11, 13, 17, 15, 16, 6) # Crimson tsuka hilt
    fill_box(grid, cx_r + 11, cx_r + 11, 12, 12, 15, 15, 3) # Gold pommel
    fill_box(grid, cx_r + 10, cx_r + 12, 17, 18, 15, 17, 3) # Gold tsuba guard
    blade_pts = [
        (cx_r + 11, 18, 17),
        (cx_r + 12, 20, 20),
        (cx_r + 13, 21, 24),
        (cx_r + 14, 22, 28),
        (cx_r + 15, 23, 32),
        (cx_r + 15, 23, 35),
    ]
    for i in range(len(blade_pts) - 1):
        p0, p1 = blade_pts[i], blade_pts[i + 1]
        draw_6conn_line(grid, p0, p1, 8)                                              # Honed silver blade
        draw_6conn_line(grid, (p0[0], p0[1] + 1, p0[2]), (p1[0], p1[1] + 1, p1[2]), 7) # Crisp white edge!

    # --- HEAD & SAMURAI KABUTO (Z: 31..44) ---
    fill_sym_box(grid, 0, 1, 11, 13, 31, 32, 5) # Neck
    fill_sym_box(grid, 0, 2, 10, 14, 32, 38, 5) # Black lacquer kabuto & head core
    fill_sym_box(grid, 0, 2, 11, 14, 38, 39, 5) # Rounded kabuto crown
    fill_sym_box(grid, 0, 1, 12, 13, 39, 39, 3) # Gold tehen crown stud

    # Flared Navy Shikoro (Samurai helmet neck-guard)
    fill_sym_box(grid, 0, 4, 9, 13, 32, 36, 1)
    fill_sym_box(grid, 3, 4, 9, 12, 32, 35, 1)
    fill_sym_box(grid, 0, 4, 9, 9, 34, 34, 6)   # Crimson rear shikoro cord
    fill_sym_box(grid, 0, 4, 9, 9, 32, 32, 3)   # Gold bottom rim
    fill_sym_box(grid, 3, 3, 13, 14, 35, 36, 3) # Gold fukigaeshi ear-guards

    # Faceplate / Menpo & SUPER READABLE ONE GLOWING EYE (独眼)!
    fill_sym_box(grid, 0, 2, 14, 15, 32, 33, 8) # Silver menpo jaw guard
    fill_sym_box(grid, 0, 0, 15, 15, 32, 32, 5) # Black chin detail
    fill_sym_box(grid, 0, 2, 14, 15, 34, 36, 5) # Dark black-lacquer upper face frame
    # RIGHT EYE (+X, viewer's left): ONE vivid glowing amber-gold eye!
    fill_box(grid, cx_r, cx_r + 1, 15, 15, 34, 35, 9)
    # LEFT EYE (-X, viewer's right): Dark armored black-lacquer eyepatch plate + diagonal crimson strap!
    fill_box(grid, cx_l - 1, cx_l, 15, 16, 34, 35, 5)
    fill_box(grid, cx_l - 2, cx_l - 1, 15, 15, 36, 36, 6) # Diagonal crimson eyepatch strap
    fill_box(grid, cx_l - 1, cx_l - 1, 16, 16, 35, 35, 4) # Subtle antique-gold eyepatch rivet
    # Sleek navy kabuto brow visor (Mabisashi)
    fill_sym_box(grid, 0, 2, 15, 16, 37, 37, 1)
    fill_sym_box(grid, 0, 2, 16, 16, 37, 37, 3)

    # ICONIC WIDE ASYMMETRICAL GOLDEN CRESCENT MOON CREST (三日月前立て)
    draw_crescent_crest(
        grid, cx_l, cx_r,
        y_front=16, z_base=37,
        right_span=11.0, left_span=6.0,
        right_height=7.2, left_height=4.8,
        blazing=False,
    )

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: DATE MASAMUNE ROBOT - POWER-UP (54 x 28 x 48)
# ============================================================
def build_b():
    grid = np.zeros((54, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 26 (-X, robot left / viewer's right)
    cx_r = X // 2      # 27 (+X, robot right / viewer's left)

    # --- EXPANDED HEAVY ARMORED BOOTS (Z: 0..4) ---
    fill_sym_box(grid, 3, 6, 9, 17, 0, 1, 5)    # Heavy black lacquer sole
    fill_sym_box(grid, 4, 5, 8, 9, 0, 2, 5)     # Rear stabilizer heel
    fill_sym_box(grid, 3, 6, 10, 17, 1, 3, 1)   # Deep navy boot armor
    fill_sym_box(grid, 3, 6, 17, 18, 1, 2, 3)   # Expanded gold dragon-claw toes
    fill_sym_box(grid, 3, 3, 18, 19, 0, 1, 7)   # White inner toe claw
    fill_sym_box(grid, 6, 6, 18, 19, 0, 1, 7)   # White outer toe claw
    fill_sym_box(grid, 4, 5, 11, 15, 3, 4, 7)   # White ankle wrap
    fill_sym_box(grid, 3, 6, 11, 16, 3, 3, 6)   # Crimson ankle cord

    # --- UPGRADED SUNEATE GREAVES & GOLD DRAGON KNEE CRESTS (Z: 4..16) ---
    fill_sym_box(grid, 3, 5, 10, 15, 4, 14, 1)  # Deep navy heavy greaves
    fill_sym_box(grid, 4, 5, 15, 16, 5, 12, 2)  # Indigo armored shin plate
    fill_sym_box(grid, 5, 6, 11, 14, 5, 12, 1)  # Flared outer greave fin
    fill_sym_box(grid, 6, 6, 11, 13, 6, 11, 3)  # Gold vertical side trim
    fill_sym_box(grid, 3, 5, 10, 15, 7, 7, 6)   # Crimson lacing
    fill_sym_box(grid, 3, 5, 10, 15, 10, 10, 6)
    # Rear leg thrusters
    fill_sym_box(grid, 4, 5, 8, 10, 6, 10, 5)
    fill_sym_box(grid, 4, 5, 8, 8, 6, 8, 9)     # Blazing amber thruster glow
    # Expanded Gold Dragon Knee Armor
    fill_sym_box(grid, 3, 6, 15, 17, 12, 16, 1)
    fill_sym_box(grid, 3, 5, 16, 18, 13, 16, 3) # Prominent gold knee shield
    fill_sym_box(grid, 4, 4, 17, 18, 14, 17, 3) # Rising golden knee horn
    fill_sym_box(grid, 4, 4, 18, 18, 14, 15, 9) # Glowing amber knee gem

    # --- THIGHS & UPGRADED KUSAZURI WAIST ARMOR (Z: 15..23) ---
    fill_sym_box(grid, 3, 5, 11, 15, 15, 20, 5)
    fill_sym_box(grid, 3, 5, 13, 15, 16, 19, 1)
    fill_sym_box(grid, 4, 5, 15, 16, 16, 19, 2)
    fill_sym_box(grid, 5, 5, 12, 14, 16, 19, 7) # White thigh trim
    # Waist & Expanded Gold-Rimmed Kusazuri Tassets
    fill_sym_box(grid, 0, 5, 10, 15, 20, 23, 5)
    fill_sym_box(grid, 2, 6, 15, 16, 18, 22, 1) # Front wide tassets
    fill_sym_box(grid, 2, 6, 16, 16, 20, 20, 6) # Crimson cord
    fill_sym_box(grid, 2, 6, 16, 16, 18, 18, 3) # Gold bottom rim
    fill_sym_box(grid, 5, 7, 10, 15, 18, 22, 1) # Flared hip armor plates
    fill_sym_box(grid, 7, 7, 11, 14, 18, 22, 3) # Gold outer hip trim
    fill_sym_box(grid, 0, 5, 9, 10, 18, 21, 1)  # Rear kusazuri skirt
    fill_sym_box(grid, 0, 5, 9, 9, 18, 18, 3)
    # White obi, crimson sash & blazing gold dragon waist buckle
    fill_sym_box(grid, 0, 5, 15, 16, 22, 22, 7)
    fill_sym_box(grid, 0, 1, 15, 17, 19, 22, 6)
    fill_sym_box(grid, 0, 1, 16, 18, 20, 22, 3)
    fill_sym_box(grid, 0, 0, 18, 18, 21, 21, 9) # Glowing amber buckle core

    # --- POWER-UP CHEST WITH EXPANDED GOLD DRAGON PLATING (Z: 23..34) ---
    fill_sym_box(grid, 0, 4, 10, 15, 23, 25, 5) # Black lacquer abs
    fill_sym_box(grid, 0, 3, 15, 16, 23, 25, 6) # Crimson waist lacing
    fill_sym_box(grid, 0, 6, 10, 16, 26, 33, 1) # Broad heroic navy chest
    fill_sym_box(grid, 0, 5, 15, 17, 26, 32, 5) # Black lacquer inner cuirass
    fill_sym_box(grid, 2, 5, 16, 17, 27, 32, 1) # Navy armored pectorals
    fill_sym_box(grid, 3, 5, 17, 17, 28, 31, 2) # Indigo bevel
    # Sweeping Golden Dragon V-Crest Chest Armor!
    fill_sym_box(grid, 0, 2, 17, 18, 27, 31, 3)
    fill_sym_box(grid, 2, 4, 17, 18, 29, 32, 3)
    fill_sym_box(grid, 4, 6, 16, 18, 31, 33, 3) # Sweeping up into golden chest wings
    fill_sym_box(grid, 1, 2, 17, 18, 26, 27, 4) # Burnished gold under-bevel
    # Blazing Amber-Gold Dragon Reactor Core at Center Chest!
    fill_sym_box(grid, 0, 1, 18, 19, 28, 30, 9)
    fill_sym_box(grid, 0, 1, 18, 18, 31, 31, 3)
    # Crimson chest cords & high white/gold samurai collar
    fill_sym_box(grid, 3, 3, 17, 17, 26, 28, 6)
    fill_sym_box(grid, 1, 3, 13, 16, 33, 34, 7) # White collar
    fill_sym_box(grid, 2, 4, 11, 15, 33, 34, 3) # Gold collar trim

    # --- EXPANDED BACKPACK & DRAMATIC DEPLOYED DRAGON WINGS (Y: 2..10, Z: 17..44) ---
    fill_sym_box(grid, 0, 4, 7, 10, 24, 33, 5)  # Heavy wing-mount backpack
    fill_sym_box(grid, 0, 3, 6, 7, 26, 32, 1)   # Navy central core
    fill_sym_box(grid, 0, 2, 5, 6, 28, 31, 3)   # Gold back emblem
    fill_sym_box(grid, 0, 1, 5, 5, 29, 30, 9)   # Glowing amber back core
    fill_sym_box(grid, 2, 3, 5, 7, 23, 26, 8)   # Twin silver thruster bells
    fill_sym_box(grid, 2, 3, 5, 5, 23, 24, 9)   # Glowing thruster nozzles

    # Deployed Mechanical Navy-and-Gold Dragon Wings (Symmetric ±X)
    # Positioned slightly wider and lower near the head so the golden crescent moon silhouettes cleanly!
    fill_sym_box(grid, 3, 7, 6, 8, 27, 31, 3)
    fill_sym_box(grid, 4, 7, 7, 8, 28, 30, 5)
    for sign in (-1, 1):
        bx_origin = cx_r if sign == 1 else cx_l
        def wx(off):
            return bx_origin + sign * off

        spar_pts = [
            (wx(5),  7, 29),
            (wx(10), 6, 32),
            (wx(15), 5, 37),  # High golden wing-elbow apex (clear of crescent!)
            (wx(21), 4, 41),
            (wx(25), 3, 44),  # Dramatic outer wingtip!
        ]
        for i in range(len(spar_pts) - 1):
            p0, p1 = spar_pts[i], spar_pts[i + 1]
            draw_6conn_line(grid, p0, p1, 3)
            draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), 4)
        # Wing-elbow forward gold claw spike
        draw_6conn_line(grid, (wx(15), 5, 37), (wx(16), 7, 40), 3)
        draw_6conn_line(grid, (wx(16), 7, 40), (wx(16), 7, 41), 9)

        # Four fanned Navy-and-Indigo Mechanical Dragon Wing Feathers/Blades!
        feathers = [
            # (start_off, start_y, start_z, end_off, end_y, end_z, thickness_z)
            (19, 4, 40, 25, 3, 35, 2),  # Outer primary feather
            (15, 5, 37, 23, 4, 29, 2),  # Second sweeping feather
            (12, 5, 34, 20, 4, 23, 2),  # Third mid feather
            (9,  6, 31, 16, 5, 18, 2),  # Inner lower feather
        ]
        for sx, sy, sz, ex, ey, ez, th in feathers:
            draw_6conn_line(grid, (wx(sx), sy, sz), (wx(ex), ey, ez), 3)
            draw_6conn_line(grid, (wx(sx), sy, sz - 1), (wx(ex), ey, ez - 1), 2)
            draw_6conn_line(grid, (wx(sx), sy, sz - 2), (wx(ex), ey, ez - 2), 1)
            # Glowing amber energy wingtip accent
            draw_6conn_line(grid, (wx(ex - 1), ey, ez), (wx(ex), ey, ez), 9)
        # Inner wing membrane connecting spars into lush navy plates
        for x_off in range(6, 17):
            z_top = int(round(29 + (x_off - 5) * (8.0 / 10.0))) if x_off <= 15 else int(round(37 + (x_off - 15) * 0.6))
            z_bot = int(round(24 + (x_off - 6) * 0.35))
            y_m = 6 if x_off < 12 else 5
            draw_6conn_line(grid, (wx(x_off), y_m, z_bot), (wx(x_off), y_m, min(z_top, 40)), 1, only_empty=True)
            if x_off % 2 == 0 and z_bot + 2 < z_top:
                grid[wx(x_off), y_m, z_bot + 2] = 2
            if 6 <= x_off <= 13:
                grid[wx(x_off), y_m, z_bot] = 6

    # --- MASSIVE UPGRADED O-SODE SHOULDER PAULDRONS & ARMS (Z: 15..36) ---
    fill_sym_box(grid, 6, 8, 11, 14, 29, 32, 5)
    # Multi-tiered flaring Navy & Gold Dragon Pauldrons
    fill_sym_box(grid, 7, 11, 10, 16, 28, 34, 1)
    fill_sym_box(grid, 8, 12, 11, 15, 32, 35, 2)
    fill_sym_box(grid, 7, 12, 10, 16, 34, 34, 3) # Gold top ridge
    fill_sym_box(grid, 11, 13, 11, 15, 34, 36, 3) # Sweeping outer gold shoulder horn
    fill_sym_box(grid, 12, 13, 12, 14, 36, 36, 9) # Glowing amber shoulder flare
    fill_sym_box(grid, 11, 11, 10, 16, 30, 30, 6) # Crimson odoshi lacing
    fill_sym_box(grid, 11, 11, 10, 16, 28, 28, 3) # Gold lower rim
    fill_sym_box(grid, 8, 11, 16, 16, 29, 33, 2)  # Indigo front face
    fill_sym_box(grid, 9, 10, 16, 16, 31, 32, 3)  # Gold shoulder crest medallion

    # Upper arms
    fill_sym_box(grid, 7, 9, 11, 14, 23, 28, 5)
    fill_sym_box(grid, 9, 9, 11, 14, 24, 26, 6)

    # LEFT ARM (-X, viewer's right): Armored Dragon-Gauntlet Shield & Twin Fang Blades / Arm Cannon!
    fill_box(grid, cx_l - 10, cx_l - 7, 11, 16, 17, 23, 1)
    fill_box(grid, cx_l - 10, cx_l - 8, 12, 16, 15, 17, 5) # Fist
    # Dragon-Head Forearm Shield-Cannon
    fill_box(grid, cx_l - 12, cx_l - 10, 12, 20, 17, 22, 1)
    fill_box(grid, cx_l - 12, cx_l - 11, 13, 19, 21, 22, 3)
    fill_box(grid, cx_l - 12, cx_l - 12, 14, 18, 18, 20, 2)
    fill_box(grid, cx_l - 12, cx_l - 12, 15, 17, 19, 19, 6)
    fill_box(grid, cx_l - 11, cx_l - 10, 20, 21, 18, 20, 9) # Glowing amber dragon-cannon muzzle!
    # Twin forward-extending honed silver secondary blades on left gauntlet
    draw_6conn_line(grid, (cx_l - 12, 20, 21), (cx_l - 12, 26, 22), 8)
    draw_6conn_line(grid, (cx_l - 12, 20, 18), (cx_l - 12, 25, 17), 8)
    grid[cx_l - 12, 26, 22] = 7
    grid[cx_l - 12, 25, 17] = 7

    # RIGHT ARM (+X, viewer's left): Angled outward wielding Towering GOLDEN DRAGON-ODACHI!
    fill_box(grid, cx_r + 7, cx_r + 10, 11, 16, 18, 23, 1)
    fill_box(grid, cx_r + 9, cx_r + 12, 14, 18, 17, 20, 3) # Heavy gold cuff
    fill_box(grid, cx_r + 10, cx_r + 12, 16, 19, 16, 19, 5) # Armored gripping gauntlet

    # Long Golden Dragon-Odachi angled outward (+X) so it clears the right shoulder cleanly!
    draw_6conn_line(grid, (cx_r + 10, 14, 9), (cx_r + 12, 19, 19), 6)  # Crimson pole/odachi hilt
    fill_box(grid, cx_r + 9, cx_r + 10, 13, 14, 8, 9, 3)               # Gold butt-cap
    # Ornate Gold Dragon-Mouth Crossguard (Tsuba) with glowing amber gem
    fill_box(grid, cx_r + 11, cx_r + 14, 18, 21, 19, 21, 3)
    fill_box(grid, cx_r + 12, cx_r + 13, 21, 21, 20, 21, 9)            # Blazing dragon-guard jewel
    # Sweeping Long Honed Silver Odachi Blade with Gold Spine & White Razor Edge!
    odachi_pts = [
        (cx_r + 12, 20, 21),
        (cx_r + 14, 21, 26),
        (cx_r + 15, 23, 31),
        (cx_r + 16, 24, 36),
        (cx_r + 17, 25, 41),
        (cx_r + 17, 25, 45),
    ]
    for i in range(len(odachi_pts) - 1):
        p0, p1 = odachi_pts[i], odachi_pts[i + 1]
        draw_6conn_line(grid, p0, p1, 8)
        draw_6conn_line(grid, (p0[0], p0[1] - 1, p0[2]), (p1[0], p1[1] - 1, p1[2]), 3)
        if i >= 1:
            draw_6conn_line(grid, (p0[0], p0[1] + 1, p0[2]), (p1[0], p1[1] + 1, p1[2]), 7)

    # --- HEAD & BLAZING UPGRADED CRESCENT KABUTO (Z: 34..47) ---
    fill_sym_box(grid, 0, 1, 12, 14, 33, 35, 5) # Neck
    fill_sym_box(grid, 0, 2, 11, 15, 35, 40, 5) # Kabuto bowl
    fill_sym_box(grid, 0, 2, 12, 15, 40, 41, 5) # High crown
    fill_sym_box(grid, 0, 1, 13, 14, 41, 41, 3) # Gold crown cap

    # Expanded Navy & Gold Shikoro Helmet Guard
    fill_sym_box(grid, 0, 4, 10, 14, 35, 38, 1)
    fill_sym_box(grid, 3, 5, 10, 13, 35, 37, 1)
    fill_sym_box(grid, 0, 5, 10, 10, 36, 36, 6) # Crimson rear cord
    fill_sym_box(grid, 0, 5, 10, 10, 35, 35, 3) # Gold bottom rim
    # Upgraded Golden Fukigaeshi Winged Cheek-Guards (clear of face!)
    fill_sym_box(grid, 3, 4, 14, 15, 36, 38, 3)
    fill_sym_box(grid, 4, 4, 14, 15, 38, 39, 9)

    # Faceplate & SUPER READABLE ONE GLOWING EYE + DARK ARMORED EYEPATCH!
    fill_sym_box(grid, 0, 2, 15, 16, 35, 36, 8) # Silver menpo
    fill_sym_box(grid, 0, 0, 16, 16, 35, 35, 3) # Gold chin emblem
    fill_sym_box(grid, 0, 2, 15, 16, 37, 38, 5) # Shadowed eye band
    # RIGHT EYE (+X, viewer's left): Blazing amber-gold eye!
    fill_box(grid, cx_r, cx_r + 1, 16, 16, 37, 38, 9)
    # LEFT EYE (-X, viewer's right): Dark armored black-lacquer eyepatch plate + crimson strap!
    fill_box(grid, cx_l - 1, cx_l, 16, 17, 37, 38, 5)
    fill_box(grid, cx_l - 2, cx_l - 1, 16, 16, 38, 38, 6)
    fill_box(grid, cx_l - 1, cx_l - 1, 17, 17, 38, 38, 3) # Gold stud
    # Forehead gold brow visor
    fill_sym_box(grid, 0, 2, 16, 17, 39, 39, 3)

    # LARGER BLAZING ASYMMETRICAL GOLDEN CRESCENT MOON CREST (Z: 39..47)
    draw_crescent_crest(
        grid, cx_l, cx_r,
        y_front=17, z_base=39,
        right_span=12.5, left_span=6.8,
        right_height=7.8, left_height=5.2,
        blazing=True,
    )

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: ONE-EYED DRAGON / DOKUGANRYU (54 x 58 x 36)
# ============================================================
def build_c():
    grid = np.zeros((54, 58, 36), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 26.5
    cx_l = X // 2 - 1   # 26 (-X, dragon left / viewer's right)
    cx_r = X // 2       # 27 (+X, dragon right / viewer's left)

    # --- ARMORED SCULPTED DRAGON TORSO (Y: 18..38, Z: 7..18) ---
    body_slices = [
        # (y, rx, z_bot, z_top)
        (18, 3.2, 9,  15),
        (19, 4.0, 9,  16),
        (20, 4.6, 8,  16),
        (21, 4.9, 8,  17),  # Muscular hind hip
        (22, 4.8, 8,  17),
        (23, 4.4, 8,  16),
        (24, 4.1, 8,  16),  # Taut armored waist
        (25, 4.0, 8,  16),
        (26, 4.2, 8,  16),
        (27, 4.6, 7,  17),
        (28, 5.1, 7,  17),
        (29, 5.5, 7,  18),  # Broad armored dragon chest
        (30, 5.7, 7,  18),
        (31, 5.8, 7,  18),
        (32, 5.7, 7,  18),
        (33, 5.4, 8,  18),
        (34, 5.0, 8,  18),
        (35, 4.5, 9,  18),
        (36, 3.9, 10, 18),
        (37, 3.4, 11, 18),
    ]
    for y, rx, zb, zt in body_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    if z <= zb + 1:
                        # Segmented Gold & Antique-Gold Dragon Belly Plates!
                        col = 3 if (y % 2 == 0) else 4
                    elif z == zb + 2 and dx >= rx - 1.2:
                        col = 6 if (y % 3 == 0) else 5  # Crimson samurai armor trim!
                    elif z >= zt - 1 and dx <= 1.6:
                        col = 2  # Highlight indigo dorsal plate
                    elif y % 3 == 0 and dx >= rx - 1.1:
                        col = 5  # Black lacquer armor segment seam
                    else:
                        col = 1  # Deep navy dragon armor
                    grid[x, y, z] = col

    # Golden Dorsal Spine Fins running down the dragon's back (Y: 19..36)
    for y in range(19, 37, 2):
        z_top = 18 if y >= 29 else (17 if y >= 21 else 16)
        fill_sym_box(grid, 0, 0, y, y + 1, z_top, z_top + 1, 3)
        if y % 4 == 1:
            fill_sym_box(grid, 0, 0, y, y, z_top + 2, z_top + 2, 3)
        else:
            fill_sym_box(grid, 0, 0, y, y, z_top + 1, z_top + 1, 4)

    # Blazing Amber-Gold Chest Core on dragon's front sternum (echoing Form B chest!)
    fill_sym_box(grid, 0, 1, 35, 37, 11, 13, 3)
    fill_sym_box(grid, 0, 0, 37, 38, 12, 13, 9)

    # --- FOUR GROUNDED ARMORED CLAWED DRAGON LEGS (Z: 0..14) ---
    for leg_type, ly_hip, ly_foot, x_hip, x_foot in [
        ("front", 32, 36, 5.5, 6.5),
        ("hind",  21, 21, 5.5, 6.5),
    ]:
        for sign in (-1, 1):
            bx = cx_r if sign == 1 else cx_l
            def lx(off):
                return int(round(bx + sign * off))

            # Upper haunch / shoulder muscle connecting solidly into torso
            fill_sphere_local(grid, cx + sign * x_hip, ly_hip, 11.5, 2.3, 2.8, 3.2, 1)
            fill_sphere_local(grid, cx + sign * (x_hip + 0.6), ly_hip, 12.2, 1.4, 2.0, 2.0, 2)
            # Gold samurai shoulder/hip armor plate
            fill_box(grid, lx(x_hip + 1), lx(x_hip + 2), ly_hip - 2, ly_hip + 2, 11, 13, 3)
            fill_box(grid, lx(x_hip + 2), lx(x_hip + 2), ly_hip - 1, ly_hip + 1, 10, 10, 6)

            # Digitigrade knee/elbow bent back then shin angling forward to foot
            knee_y = ly_hip - 2 if leg_type == "hind" else ly_hip - 1
            draw_6conn_line(grid, (lx(x_hip), ly_hip, 11), (lx(x_foot), knee_y, 7), 5, pad=(1, 1, 1))
            draw_6conn_line(grid, (lx(x_foot), knee_y, 7), (lx(x_foot), ly_foot, 2), 1, pad=(1, 1, 0))
            # Gold shin guard & crimson ankle lacing
            fill_box(grid, lx(x_foot - 1), lx(x_foot + 1), ly_foot, ly_foot + 1, 3, 6, 1)
            fill_box(grid, lx(x_foot), lx(x_foot + 1), ly_foot + 1, ly_foot + 1, 4, 6, 3)
            fill_box(grid, lx(x_foot - 1), lx(x_foot + 1), ly_foot - 1, ly_foot + 1, 3, 3, 6)

            # Grounded Armored Dragon Foot (Z: 0..2) with 3 sharp white/silver claws!
            fill_box(grid, lx(x_foot - 1), lx(x_foot + 1), ly_foot - 2, ly_foot + 2, 0, 2, 5)
            fill_box(grid, lx(x_foot - 1), lx(x_foot + 1), ly_foot - 1, ly_foot + 2, 1, 2, 1)
            for c_off in (-1, 0, 1):
                cx_c = lx(x_foot) + c_off * 2
                cy_c = ly_foot + 3 + (1 if c_off == 0 else 0)
                draw_6conn_line(grid, (lx(x_foot) + c_off, ly_foot + 2, 1), (cx_c, cy_c, 0), 8)
                if 0 <= cx_c < X and 0 <= cy_c < Y:
                    grid[cx_c, cy_c, 0] = 7
            # Rear dewclaw
            fill_box(grid, lx(x_foot), lx(x_foot), ly_foot - 3, ly_foot - 2, 0, 1, 7)

    # --- GRACEFUL RAISED S-CURVED ARMORED DRAGON NECK (Y: 36..44, Z: 13..25) ---
    neck_path = [
        # (y, z, rx, rz)
        (36, 14.5, 3.2, 3.0),
        (37, 15.8, 3.0, 2.9),
        (38, 17.2, 2.8, 2.8),
        (39, 18.6, 2.7, 2.7),
        (40, 20.0, 2.6, 2.6),
        (41, 21.4, 2.5, 2.5),
        (42, 22.6, 2.5, 2.4),
        (43, 23.4, 2.6, 2.4),
    ]
    for idx, (ny, nz, rx_n, rz_n) in enumerate(neck_path):
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx_n + 0.2:
                continue
            for z in range(int(nz - rz_n), int(nz + rz_n) + 1):
                dz = z - nz
                if 0 <= z < Z and (dx / rx_n) ** 2 + (dz / rz_n) ** 2 <= 1.0:
                    if z <= nz - rz_n + 1.2:
                        col = 3 if (idx % 2 == 0) else 4  # Gold throat armor plates!
                    elif idx % 2 == 1 and dx >= rx_n - 0.9:
                        col = 5                           # Black armor seam
                    elif z >= nz + rz_n - 1.1 and dx <= 1.2:
                        col = 2                           # Indigo dorsal ridge
                    else:
                        col = 1
                    grid[x, ny, z] = col
        if idx % 2 == 0:
            fill_sym_box(grid, int(rx_n), int(rx_n), ny, ny, int(nz), int(nz), 6)
            z_sp = int(round(nz + rz_n))
            fill_sym_box(grid, 0, 0, ny - 1, ny, z_sp, z_sp + 2, 3)

    # --- FIERCE ONE-EYED DRAGON HEAD (Y: 42..55, Z: 18..28) ---
    # Armored Cranium / Skull
    fill_sym_box(grid, 0, 3, 43, 48, 21, 26, 1)
    fill_sym_box(grid, 0, 2, 44, 48, 26, 27, 2)  # Indigo armored crown
    fill_sym_box(grid, 0, 3, 43, 45, 22, 25, 5)  # Black lacquer samurai cheek-plates
    # Sweeping Gold Cheek-Spikes / Samurai Ear-Frills
    draw_6conn_line(grid, (cx_r + 3, 44, 23), (cx_r + 6, 41, 24), 3)
    draw_6conn_line(grid, (cx_l - 3, 44, 23), (cx_l - 6, 41, 24), 3)
    draw_6conn_line(grid, (cx_r + 3, 44, 21), (cx_r + 5, 42, 20), 4)
    draw_6conn_line(grid, (cx_l - 3, 44, 21), (cx_l - 5, 42, 20), 4)

    # Tapered Armored Dragon Upper Snout (Y: 48..55, Z: 22..25)
    fill_sym_box(grid, 0, 2, 48, 51, 22, 25, 1)
    fill_sym_box(grid, 0, 1, 51, 55, 22, 24, 1)
    fill_sym_box(grid, 0, 1, 49, 53, 25, 25, 2)  # Indigo snout bridge
    fill_sym_box(grid, 0, 0, 53, 55, 25, 26, 3)  # Golden nose-horn!
    fill_sym_box(grid, 1, 1, 54, 54, 24, 24, 5)  # Nostrils
    # Sharp White Upper Fangs!
    fill_sym_box(grid, 2, 2, 49, 49, 21, 21, 7)
    fill_sym_box(grid, 1, 1, 53, 53, 21, 21, 7)

    # Roaring Open Lower Jaw (Y: 45..54, Z: 18..21)
    fill_sym_box(grid, 0, 2, 45, 49, 19, 20, 5)  # Black jaw hinge
    fill_sym_box(grid, 0, 1, 49, 54, 18, 19, 1)  # Navy lower jaw
    fill_sym_box(grid, 0, 1, 49, 53, 18, 18, 4)  # Burnished gold chin underplate
    fill_sym_box(grid, 0, 0, 53, 54, 17, 18, 3)  # Gold chin barb
    fill_sym_box(grid, 0, 1, 47, 52, 20, 20, 6)  # Crimson inner mouth & tongue!
    fill_sym_box(grid, 1, 1, 52, 53, 20, 20, 7)  # White lower fangs!

    # ONE FIERCE GLOWING AMBER-GOLD RIGHT EYE (+X) + ARMORED EYEPATCH OVER LEFT EYE (-X)!
    # Right side (+X, viewer's left, directly facing camera in 3/4 view):
    fill_box(grid, cx_r + 2, cx_r + 3, 45, 49, 23, 26, 5) # Crisp black socket frame
    fill_box(grid, cx_r + 2, cx_r + 3, 46, 48, 24, 25, 9) # Blazing amber-gold dragon eye!
    fill_box(grid, cx_r + 2, cx_r + 3, 45, 49, 26, 26, 3) # Fierce golden brow ridge
    # Left side (-X, viewer's right): Dark armored black-lacquer eyepatch/scar plate!
    fill_box(grid, cx_l - 4, cx_l - 2, 45, 49, 23, 25, 5) # Black lacquer armored eyepatch plate
    fill_box(grid, cx_l - 4, cx_l - 4, 47, 47, 24, 24, 3) # Gold armor bolt on eyepatch
    # Diagonal crimson eyepatch strap/scar crossing across left brow onto snout bridge!
    draw_6conn_line(grid, (cx_l - 4, 46, 25), (cx_l, 49, 26), 6)
    draw_6conn_line(grid, (cx_l - 4, 48, 23), (cx_l - 2, 50, 23), 6)

    # --- ROBOT CRESCENT MOON CREST -> SWEEPING GOLDEN DRAGON HORNS! (Z: 26..35) ---
    fill_box(grid, cx_l - 1, cx_r + 1, 47, 49, 26, 27, 3)
    fill_box(grid, cx_l, cx_r, 49, 49, 27, 27, 9)
    # Right Horn (+X): Iconic long asymmetrical sweeping golden crescent-dragon horn!
    r_horn = [
        (cx_r + 1, 48, 27),
        (cx_r + 5, 47, 28),
        (cx_r + 8, 46, 30),
        (cx_r + 10, 45, 32),
        (cx_r + 11, 44, 35),
    ]
    for i in range(len(r_horn) - 1):
        col_h = 9 if i == len(r_horn) - 2 else 3
        draw_6conn_line(grid, r_horn[i], r_horn[i + 1], col_h)
        if i < 3:
            p0, p1 = r_horn[i], r_horn[i + 1]
            draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), 4)
    # Left Horn (-X): Shorter asymmetrical golden crescent-dragon horn!
    l_horn = [
        (cx_l - 1, 48, 27),
        (cx_l - 4, 47, 28),
        (cx_l - 6, 46, 30),
        (cx_l - 7, 45, 32),
    ]
    for i in range(len(l_horn) - 1):
        col_h = 9 if i == len(l_horn) - 2 else 3
        draw_6conn_line(grid, l_horn[i], l_horn[i + 1], col_h)
        if i < 2:
            p0, p1 = l_horn[i], l_horn[i + 1]
            draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), 4)

    # --- MAJESTIC UNFOLDED NAVY-AND-GOLD DRAGON WINGS (100% 6-CONNECTED!) ---
    # Swept wide along +-X (less far back in -Y) so BOTH wings display broad membranes in 3/4 view!
    for sign in (-1, 1):
        bx_origin = cx_r if sign == 1 else cx_l
        def wx(off):
            return bx_origin + sign * off

        # Solid armored wing shoulder joint embedded in torso
        fill_box(grid, wx(3), wx(6), 30, 33, 15, 18, 5)
        fill_box(grid, wx(4), wx(6), 31, 33, 17, 19, 3)

        # Articulated Golden Wing Leading Arm: Shoulder -> Wrist Apex -> Wingtip!
        arm_pts = [
            (wx(5),  32, 18),
            (wx(9),  32, 23),
            (wx(14), 31, 29),  # Wing-wrist apex
            (wx(20), 29, 33),
            (wx(25), 27, 35),  # High outer dragon wingtip!
        ]
        for i in range(len(arm_pts) - 1):
            p0, p1 = arm_pts[i], arm_pts[i + 1]
            draw_6conn_line(grid, p0, p1, 3)
            draw_6conn_line(grid, (p0[0], p0[1] - 1, p0[2]), (p1[0], p1[1] - 1, p1[2]), 4)
            if i < 2:
                draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), 5)

        # Fierce White/Gold Wing Thumb-Claw at the wrist apex (6-connected!)
        draw_6conn_line(grid, (wx(14), 31, 29), (wx(14), 34, 32), 3)
        draw_6conn_line(grid, (wx(14), 34, 32), (wx(14), 35, 33), 7)

        # Four Golden Wing Finger-Spars radiating backward & outward from wrist
        finger_tips = [
            (25, 27, 35),  # Finger 1 (leading edge tip)
            (24, 22, 28),  # Finger 2 (wide mid-outer sweep)
            (20, 19, 22),  # Finger 3 (mid trailing sweep)
            (14, 19, 17),  # Finger 4 (inner wing edge)
        ]
        wrist = (14, 31, 29)
        for fi in range(1, len(finger_tips)):
            tx, ty, tz = finger_tips[fi]
            draw_6conn_line(grid, (wx(wrist[0]), wrist[1], wrist[2]), (wx(tx), ty, tz), 3)
            mx = int(round((wrist[0] + tx) * 0.55))
            my = int(round((wrist[1] + ty) * 0.55))
            mz = int(round((wrist[2] + tz) * 0.55))
            draw_6conn_line(grid, (wx(mx), my, mz), (wx(mx), my, mz), 9)

        # Guaranteed 6-connected Scalloped Navy & Highlight-Indigo Wing Membranes!
        # Draw each membrane slice as a continuous 6-connected line from root edge to trailing edge!
        panels = [
            ((5, 31, 17),  (5, 22, 14),  (14, 31, 29), (14, 19, 17)),
            ((14, 31, 29), (14, 19, 17), (14, 31, 29), (20, 19, 22)),
            ((14, 31, 29), (20, 19, 22), (14, 31, 29), (24, 22, 28)),
            ((14, 31, 29), (24, 22, 28), (19, 29, 32), (25, 27, 35)),
        ]
        for ra, ta, rb, tb in panels:
            u_steps = 20
            for iu in range(u_steps + 1):
                u = iu / u_steps
                scallop = 1.0 - 0.14 * np.sin(np.pi * u)
                ax = ra[0] + (rb[0] - ra[0]) * u
                ay = ra[1] + (rb[1] - ra[1]) * u
                az = ra[2] + (rb[2] - ra[2]) * u
                bx_p = ta[0] + (tb[0] - ta[0]) * u
                by_p = ta[1] + (tb[1] - ta[1]) * u
                bz_p = ta[2] + (tb[2] - ta[2]) * u
                ex = ax + (bx_p - ax) * scallop
                ey = ay + (by_p - ay) * scallop
                ez = az + (bz_p - az) * scallop
                col_rib = 2 if (iu % 4 == 0) else 1
                draw_6conn_line(grid, (wx(ax), ay, az), (wx(ex), ey, ez), col_rib, only_empty=True)
                # Crimson/indigo scalloped trailing edge dot (guaranteed adjacent to line endpoint!)
                ex_i, ey_i, ez_i = int(round(wx(ex))), int(round(ey)), int(round(ez))
                if 0 <= ex_i < X and 0 <= ey_i < Y and 0 <= ez_i < Z and grid[ex_i, ey_i, ez_i] in (1, 2):
                    if iu % 3 == 0:
                        grid[ex_i, ey_i, ez_i] = 6

    # --- LONG SWEEPING SEGMENTED NAVY-AND-GOLD ARMORED DRAGON TAIL (Y: 1..18, Z: 7..20) ---
    # Sweeps gracefully behind the hind legs and curls outward (+X) & up so it silhouettes clearly in BOTH views!
    tail_nodes = [
        # (x_shift, y, z, rx, rz)
        (0.0,  18, 12.0, 2.9, 2.6),
        (0.8,  17, 11.4, 2.6, 2.3),
        (1.6,  16, 10.8, 2.4, 2.1),
        (2.5,  15, 10.2, 2.2, 1.9),
        (3.4,  14,  9.7, 2.0, 1.8),
        (4.3,  13,  9.3, 1.9, 1.7),
        (5.1,  12,  9.1, 1.8, 1.6),
        (5.9,  11,  9.1, 1.7, 1.5),
        (6.6,  10,  9.3, 1.6, 1.5),
        (7.2,   9,  9.7, 1.5, 1.4),
        (7.7,   8, 10.3, 1.4, 1.4),
        (8.0,   7, 11.0, 1.3, 1.3),
        (8.2,   6, 11.8, 1.25, 1.25),
        (8.2,   5, 12.6, 1.2, 1.2),
        (8.0,   4, 13.5, 1.15, 1.15),
        (7.7,   3, 14.4, 1.1, 1.1),
    ]
    prev_center = None
    for idx, (xs_t, ty, tz, rx_t, rz_t) in enumerate(tail_nodes):
        tcx = cx + xs_t
        cur_center = (tcx, ty, tz)
        if prev_center is not None:
            # Guarantee 100% 6-connected armored spine between every tail segment
            draw_6conn_line(grid, prev_center, cur_center, 1)
            draw_6conn_line(grid, (prev_center[0], prev_center[1], prev_center[2] - 1),
                            (cur_center[0], cur_center[1], cur_center[2] - 1), 4)
        prev_center = cur_center
        for x in range(int(tcx - rx_t - 1), int(tcx + rx_t + 2)):
            for z in range(int(tz - rz_t - 1), int(tz + rz_t + 2)):
                if 0 <= x < X and 0 <= z < Z:
                    if ((x - tcx) / rx_t) ** 2 + ((z - tz) / rz_t) ** 2 <= 1.0:
                        if z <= tz - rz_t + 0.9:
                            col = 3 if (idx % 2 == 0) else 4  # Gold armored underside
                        elif idx % 3 == 1:
                            col = 5                           # Black lacquer armor ring
                        elif z >= tz + rz_t - 0.9:
                            col = 2
                        else:
                            col = 1
                        grid[x, ty, z] = col
        # Golden dorsal tail spikes & crimson ring accents
        if idx % 2 == 0:
            z_sp = int(round(tz + rz_t))
            tx_i = int(round(tcx))
            if 0 <= tx_i < X and 0 <= z_sp + 1 < Z:
                grid[tx_i, ty, z_sp] = 3
                grid[tx_i, ty, z_sp + 1] = 3
        if idx in (4, 9, 13):
            tx_i = int(round(tcx))
            if 0 <= tx_i < X and 0 <= int(tz) < Z:
                grid[min(X - 1, tx_i + int(rx_t)), ty, int(tz)] = 6
                grid[max(0, tx_i - int(rx_t)), ty, int(tz)] = 6

    # Sharp Katana-Blade Tail Fin (transformed from robot's katana/odachi!)
    tx_tip = int(round(cx + 7.7))
    draw_6conn_line(grid, (tx_tip, 3, 14), (tx_tip - 1, 1, 19), 8)
    draw_6conn_line(grid, (tx_tip, 3, 13), (tx_tip - 1, 1, 18), 3)
    draw_6conn_line(grid, (tx_tip, 4, 14), (tx_tip - 1, 2, 19), 7)

    hollow_interior_26(grid, 1, Z - 2)
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


def render_preview(grid_a, v_a, grid_b, v_b, grid_c, v_c, title_banner,
                   label_a, label_b, label_c, out_path,
                   yaw_a=26, pitch_a=18, yaw_b=24, pitch_b=18, yaw_c=42, pitch_c=24):
    canvas = Image.new("RGBA", (1274, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, 1274, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (1274, gy)], fill=(28, 34, 48, 255), width=1)

    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))

    models = [
        (label_a, grid_a, v_a, yaw_a, pitch_a),
        (label_b, grid_b, v_b, yaw_b, pitch_b),
        (label_c, grid_c, v_c, yaw_c, pitch_c),
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
    model_c = build_c()
    v_a = export_vox(model_a, "masamune_a.vox")
    v_b = export_vox(model_b, "masamune_b.vox")
    v_c = export_vox(model_c, "masamune_c.vox")
    comp_a, minz_a = check_6_connected(model_a)
    comp_b, minz_b = check_6_connected(model_b)
    comp_c, minz_c = check_6_connected(model_c)
    render_preview(
        model_a, v_a, model_b, v_b, model_c, v_c,
        "TRANSFORMING VOXEL MODEL: DATE MASAMUNE ROBOT -> POWER-UP -> ONE-EYED DRAGON (DOKUGANRYU)",
        "1. DATE MASAMUNE ROBOT (NORMAL)",
        "2. DATE MASAMUNE ROBOT (POWER-UP)",
        "3. ONE-EYED DRAGON (DOKUGANRYU)",
        "preview_masamune.png",
        yaw_a=26, pitch_a=18, yaw_b=24, pitch_b=18, yaw_c=42, pitch_c=24,
    )
    print(f"masamune: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b}), "
          f"C={v_c} voxels {model_c.shape} (comp={comp_c}, minZ={minz_c})")
