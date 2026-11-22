import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Distinct from Shingen's crimson & fiery-orange tiger:
# Silver Naga-Eboshi, Deep Pine-Teal Armor, Pale Golden-Ochre Fur & Espresso-Brown Jagged Stripes!
PALETTE = {
    1: (212, 220, 232, 255),  # Honed Silver-Steel Naga-Eboshi Kabuto & Katakama-Yari
    2: (24, 82, 78, 255),     # Deep Pine-Teal / Viridian Samurai Armor (Kiyomasa)
    3: (236, 204, 114, 255),  # Pale Golden-Ochre / Sand-Gold Tiger Fur
    4: (188, 142, 54, 255),   # Warm Tawny-Ochre Dorsal Fur Shading & Bevels
    5: (48, 36, 30, 255),     # Deep Espresso-Umber Broken Tiger Stripes & Lacquer
    6: (244, 202, 48, 255),   # Radiant Gold Janome (Snake-Eye Ring) Crest & Trim
    7: (248, 244, 232, 255),  # Crisp Ivory-White Tiger Belly, Muzzle & Claws
    8: (206, 46, 40, 255),    # Vermilion-Red Sun Disc (Hinomaru on Eboshi) & Lacing
    9: (54, 234, 186, 255),   # Vivid Emerald-Cyan Glowing Eyes & Crest Core
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


def count_components_6(grid):
    """Return number of 6-connected components and min Z."""
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
# FORM A: KATO KIYOMASA ROBOT (NAGA-EBOSHI KABUTO) (44 x 26 x 56)
# ============================================================
def build_a():
    grid = np.zeros((44, 26, 56), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21 (-X, robot left / viewer's right)
    cx_r = X // 2      # 22 (+X, robot right / viewer's left)

    # --- 1. HEAVY TIGER-SLAYER SAMURAI BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 9, 16, 0, 1, 5)      # Deep espresso lacquer sole
    fill_sym_box(grid, 3, 6, 10, 16, 1, 2, 2)     # Deep pine-teal footplate
    fill_sym_box(grid, 3, 6, 15, 17, 1, 2, 1)     # Silver armored toe-cap
    fill_sym_box(grid, 3, 3, 17, 18, 0, 1, 7)     # Ivory tiger-claw toes
    fill_sym_box(grid, 5, 5, 17, 18, 0, 1, 7)
    fill_sym_box(grid, 4, 5, 8, 9, 0, 2, 5)       # Rear heel
    fill_sym_box(grid, 3, 5, 10, 14, 3, 4, 5)     # Ankle joint
    fill_sym_box(grid, 3, 5, 14, 15, 3, 3, 6)     # Gold ankle band

    # --- 2. GOLDEN-OCHRE TIGER-STRIPED GREAVES (Z: 4..14) ---
    fill_sym_box(grid, 3, 5, 10, 14, 4, 14, 2)    # Deep pine-teal inner leg
    fill_sym_box(grid, 3, 6, 11, 15, 4, 12, 3)    # Pale golden-ochre tiger shin armor!
    fill_sym_box(grid, 6, 6, 11, 14, 5, 11, 4)    # Warm tawny outer bevel
    # Distinct jagged double-banded espresso tiger stripes (NOT straight bars like Shingen)
    fill_sym_box(grid, 3, 5, 13, 15, 6, 6, 5)
    fill_sym_box(grid, 5, 6, 11, 14, 7, 7, 5)
    fill_sym_box(grid, 3, 5, 13, 15, 10, 10, 5)
    fill_sym_box(grid, 5, 6, 11, 14, 9, 9, 5)
    # Silver & Teal Samurai Knee Guards with Gold Rivet
    fill_sym_box(grid, 3, 6, 14, 16, 12, 15, 2)
    fill_sym_box(grid, 4, 5, 16, 17, 13, 15, 1)
    fill_sym_box(grid, 4, 5, 17, 17, 14, 14, 6)

    # --- 3. THIGHS & PINE-TEAL KUSAZURI WAIST ARMOR (Z: 15..22) ---
    fill_sym_box(grid, 3, 5, 10, 14, 15, 19, 5)
    fill_sym_box(grid, 3, 5, 13, 15, 15, 18, 2)
    fill_sym_box(grid, 4, 5, 15, 15, 16, 17, 1)
    # Pelvis & Flared Kusazuri
    fill_sym_box(grid, 0, 5, 10, 14, 19, 22, 5)
    fill_sym_box(grid, 2, 6, 15, 15, 17, 21, 2)   # Front pine-teal tassets
    fill_sym_box(grid, 2, 6, 15, 15, 19, 19, 8)   # Vermilion odoshi cord
    fill_sym_box(grid, 2, 6, 15, 15, 17, 17, 6)   # Gold hem
    fill_sym_box(grid, 5, 7, 10, 14, 17, 21, 2)   # Side hip plates
    fill_sym_box(grid, 7, 7, 11, 13, 19, 19, 8)
    fill_sym_box(grid, 7, 7, 11, 13, 17, 17, 6)
    fill_sym_box(grid, 0, 5, 9, 9, 17, 21, 2)     # Rear tassets
    fill_sym_box(grid, 0, 5, 9, 9, 17, 17, 6)
    # Vermilion war obi & Gold Janome belt buckle
    fill_sym_box(grid, 0, 5, 14, 16, 21, 22, 8)
    fill_sym_box(grid, 0, 1, 15, 16, 19, 22, 6)
    fill_sym_box(grid, 0, 0, 16, 16, 20, 21, 2)   # Janome hollow center!

    # Rear Tiger Tail tucked cleanly behind waist (clearly visible in REAR VIEW)
    tail_r = [
        (0, 0, 8, 9, 19, 20, 3),
        (0, 0, 7, 8, 17, 19, 5),
        (0, 0, 6, 7, 15, 17, 3),
        (0, 0, 5, 6, 13, 15, 4),
        (0, 0, 4, 5, 12, 13, 5),
    ]
    for x0, x1, y0, y1, z0, z1, col in tail_r:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)

    # --- 4. TORSO / PINE-TEAL & SILVER CUIRASS WITH GOLD JANOME (蛇の目) CREST (Z: 22..33) ---
    fill_sym_box(grid, 0, 4, 10, 14, 22, 24, 5)
    fill_sym_box(grid, 0, 4, 14, 15, 22, 24, 2)
    fill_sym_box(grid, 0, 6, 9, 15, 25, 32, 2)    # Broad deep pine-teal chest
    fill_sym_box(grid, 0, 5, 15, 16, 25, 31, 1)   # Silver-steel pectoral armor!
    fill_sym_box(grid, 4, 5, 15, 16, 26, 30, 2)   # Teal outer trim
    # Iconic Gold JANOME (蛇の目 — Bull's-Eye Ring) Crest on chest!
    fill_sym_box(grid, 0, 2, 16, 17, 26, 30, 6)   # Outer gold ring
    fill_sym_box(grid, 0, 1, 17, 17, 27, 29, 2)   # Inner pine-teal ring hole!
    fill_sym_box(grid, 0, 0, 17, 17, 28, 28, 9)   # Glowing emerald core dot
    # Vermilion lacing & silver collar
    fill_sym_box(grid, 3, 3, 16, 16, 26, 30, 8)
    fill_sym_box(grid, 1, 4, 11, 15, 32, 33, 1)
    fill_sym_box(grid, 2, 4, 13, 15, 33, 33, 6)

    # Rear Backpack (Y: 6..9, Z: 24..32)
    fill_sym_box(grid, 0, 4, 7, 9, 24, 31, 2)
    fill_sym_box(grid, 0, 3, 6, 7, 25, 30, 1)
    fill_sym_box(grid, 2, 3, 6, 7, 26, 30, 3)     # Folded golden tiger dorsal armor
    fill_sym_box(grid, 2, 3, 6, 6, 28, 28, 5)
    fill_sym_box(grid, 0, 1, 6, 6, 27, 29, 6)     # Rear gold emblem

    # --- 5. TIGER-PELT & PINE-TEAL SODE SHOULDER PAULDRONS (Z: 27..35) ---
    fill_sym_box(grid, 6, 8, 11, 14, 29, 32, 5)
    fill_sym_box(grid, 7, 11, 10, 15, 28, 34, 3)  # Golden-ochre tiger-fur shoulder armor!
    fill_sym_box(grid, 7, 11, 10, 15, 34, 34, 1)  # Silver upper ridge
    fill_sym_box(grid, 8, 11, 10, 15, 28, 28, 2)  # Pine-teal lower rim
    fill_sym_box(grid, 11, 11, 10, 15, 29, 33, 4) # Tawny outer bevel
    # Broken espresso tiger stripes on shoulders
    fill_sym_box(grid, 9, 11, 10, 13, 32, 32, 5)
    fill_sym_box(grid, 8, 11, 12, 15, 30, 30, 5)
    fill_sym_box(grid, 7, 10, 15, 15, 34, 34, 6)  # Gold shoulder trim
    fill_sym_box(grid, 10, 11, 12, 13, 34, 35, 6) # Gold shoulder boss

    # --- 6. ARMS & ICONIC KATAKAMA-YARI (片鎌槍 — SINGLE-HOOKED SPEAR) ---
    fill_sym_box(grid, 7, 9, 11, 14, 22, 28, 5)
    fill_sym_box(grid, 8, 9, 11, 14, 24, 26, 2)

    # Left Arm (-X, viewer's right): Armored Forearm + Tiger-Claw Gauntlet
    fill_box(grid, cx_l - 10, cx_l - 7, 11, 15, 16, 21, 2)
    fill_box(grid, cx_l - 10, cx_l - 10, 12, 14, 17, 20, 1)
    fill_box(grid, cx_l - 10, cx_l - 7, 13, 15, 16, 16, 6)
    fill_box(grid, cx_l - 9, cx_l - 7, 12, 14, 14, 15, 5)
    fill_box(grid, cx_l - 10, cx_l - 10, 14, 16, 14, 15, 7) # Ivory claw blade

    # Right Arm (+X, viewer's left): Angled outward wielding KATAKAMA-YARI!
    fill_box(grid, cx_r + 7, cx_r + 10, 11, 15, 17, 22, 2)
    fill_box(grid, cx_r + 10, cx_r + 13, 13, 16, 17, 20, 2)
    fill_box(grid, cx_r + 11, cx_r + 13, 15, 17, 17, 19, 6) # Gold cuff
    fill_box(grid, cx_r + 12, cx_r + 14, 16, 18, 16, 19, 5) # Gripping fist

    # Katakama-yari polearm (standing clean and tall on viewer's left, X = cx_r + 14!)
    sx = cx_r + 14
    fill_box(grid, sx, sx + 1, 17, 18, 4, 34, 5)   # Dark lacquered spear shaft
    fill_box(grid, sx, sx + 1, 17, 18, 4, 5, 6)    # Gold butt cap (ishizuki)
    fill_box(grid, sx, sx + 1, 17, 18, 22, 23, 8)  # Vermilion grip wrap
    fill_box(grid, sx, sx + 1, 17, 18, 33, 35, 6)  # Gold spear collar
    # Main tall silver spearhead (Z: 35..50)
    fill_box(grid, sx, sx + 1, 17, 18, 35, 45, 1)
    fill_box(grid, sx, sx, 17, 18, 46, 50, 1)
    fill_box(grid, sx, sx, 18, 18, 36, 48, 7)      # Honed bright edge
    # Signature SINGLE SIDE-HOOK BLADE (片鎌 — curving outward +X & slightly upward!)
    draw_6conn_line(grid, (sx + 1, 17, 36), (sx + 5, 17, 37), 1)
    draw_6conn_line(grid, (sx + 5, 17, 37), (sx + 6, 17, 41), 1)
    draw_6conn_line(grid, (sx + 5, 18, 37), (sx + 6, 18, 41), 7)
    draw_6conn_line(grid, (sx + 1, 18, 36), (sx + 5, 18, 36), 6)

    # --- 7. HEAD & ICONIC TOWERING SILVER NAGA-EBOSHI KABUTO (長烏帽子兜) (Z: 33..55) ---
    fill_sym_box(grid, 0, 1, 11, 14, 32, 34, 5)   # Neck
    fill_sym_box(grid, 0, 2, 10, 15, 34, 39, 5)   # Inner skull
    fill_sym_box(grid, 0, 3, 9, 13, 34, 36, 2)    # Pine-teal shikoro neck-guard
    fill_sym_box(grid, 0, 3, 9, 9, 34, 34, 6)     # Gold shikoro rim
    # Fierce Samurai Menpo & Bright Emerald-Cyan Eyes
    fill_sym_box(grid, 0, 2, 14, 15, 34, 35, 5)   # Dark bearded menpo mask
    fill_sym_box(grid, 1, 2, 15, 16, 35, 35, 7)   # White tiger-fang mustache accent
    fill_sym_box(grid, 0, 2, 14, 16, 36, 37, 5)   # Eye frame
    fill_sym_box(grid, 1, 2, 16, 16, 36, 37, 9)   # Vivid glowing emerald-cyan eyes!
    fill_sym_box(grid, 0, 0, 16, 16, 36, 37, 1)   # Silver nose bridge
    fill_sym_box(grid, 0, 2, 14, 16, 38, 38, 2)   # Pine-teal brow visor
    fill_sym_box(grid, 0, 2, 16, 16, 38, 38, 6)   # Gold brow band

    # ICONIC TOWERING SILVER NAGA-EBOSHI HELMET (Z: 39..55 — tall vertical tapered court-cap kabuto!)
    eboshi_layers = [
        # (z, x_off, y0, y1)
        (39, 2, 10, 15),
        (40, 2, 10, 15),
        (41, 2, 10, 15),
        (42, 2, 10, 15),
        (43, 2, 10, 15),
        (44, 2, 10, 15),
        (45, 2, 10, 14),
        (46, 2, 10, 14),
        (47, 2, 10, 14),
        (48, 1, 10, 14),
        (49, 1, 10, 14),
        (50, 1, 10, 13),
        (51, 1, 10, 13),
        (52, 1, 10, 13),
        (53, 1, 10, 12),
        (54, 0, 10, 12),
        (55, 0, 10, 11),
    ]
    for ez, ex_off, ey0, ey1 in eboshi_layers:
        fill_sym_box(grid, 0, ex_off, ey0, ey1, ez, ez, 1) # Gleaming silver-foil Naga-Eboshi!
    # Vertical gold ridge seam along front & back of the tall Naga-Eboshi
    fill_sym_box(grid, 0, 0, 15, 15, 39, 44, 6)
    fill_sym_box(grid, 0, 0, 14, 14, 45, 49, 6)
    fill_sym_box(grid, 0, 0, 13, 13, 50, 52, 6)
    # Iconic VERMILION RED SUN DISC (日の丸) painted on BOTH sides of the tall Silver Naga-Eboshi!
    fill_sym_box(grid, 2, 2, 11, 13, 42, 46, 8)
    fill_sym_box(grid, 2, 2, 12, 12, 41, 47, 8)
    # Small gold kuwagata crescent base hugging the Eboshi brow
    fill_sym_box(grid, 1, 3, 15, 16, 39, 40, 6)
    fill_sym_box(grid, 3, 4, 15, 15, 40, 42, 6)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: GOLDEN-OCHRE TIGER (KIYOMASA'S TIGER) (26 x 52 x 28)
# ============================================================
def build_b():
    grid = np.zeros((26, 52, 28), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 12.5

    # Distinct Pale Golden-Ochre & Tawny Fur with BROKEN DOUBLE-CHEVRON ESPRESSO STRIPES!
    # Visually unmistakable from Shingen's fiery vivid orange + solid black stripes!
    def kiyomasa_tiger_fur(x, y, z, zb, zt, dx, rx):
        # Crisp ivory-white underbelly & lower flanks
        if z <= zb + 1 and dx <= rx * 0.78:
            return 7
        if z == zb + 2 and dx <= rx * 0.50 and y >= 24:
            return 7
        # Jagged / chevron-forked espresso-brown double stripes!
        z_rel = z - zb
        # Forked diagonal offset creating bold chevron-like broken stripes
        y_chev = y + (1 if (z_rel % 4 in (1, 2)) else 0)
        stripe_bands = (12, 13, 18, 19, 24, 25, 30)
        if y_chev in stripe_bands and z >= zb + 2:
            # Leave bright ochre gap inside double-stripe for distinctive Bengal/Golden pattern!
            if (y_chev in (12, 18, 24) and z_rel in (4, 5) and dx > 1.8):
                return 4
            if dx >= rx * 0.18 or z >= zt - 1:
                return 5
        # Warm tawny-ochre dorsal saddle shading
        if z >= zt - 2 and dx <= rx * 0.70:
            return 4
        return 3  # Pale golden-ochre fur

    # --- 1. POWERFUL CROUCHING / LEAPING GOLDEN TIGER BODY (Y: 10..35, Z: 7..19) ---
    body_slices = [
        (10, 3.0, 11, 17),
        (11, 3.9, 10, 18),
        (12, 4.4, 9,  19),
        (13, 4.5, 9,  19),
        (14, 4.3, 9,  19),
        (15, 4.0, 9,  18),
        (16, 3.8, 9,  18),
        (17, 3.7, 9,  18),
        (18, 3.8, 9,  18),
        (19, 4.0, 9,  18),
        (20, 4.2, 8,  18),
        (21, 4.5, 8,  18),
        (22, 4.8, 8,  18),
        (23, 5.0, 8,  19),
        (24, 5.2, 7,  19),
        (25, 5.3, 7,  19),
        (26, 5.4, 7,  20),
        (27, 5.3, 7,  20),
        (28, 5.1, 7,  20),
        (29, 4.8, 8,  19),
        (30, 4.5, 8,  19),
        (31, 4.2, 9,  19),
        (32, 4.0, 10, 19),
        (33, 3.8, 11, 19),
        (34, 3.7, 12, 20),
    ]
    for y, rx, zb, zt in body_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.25:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    grid[x, y, z] = kiyomasa_tiger_fur(x, y, z, zb, zt, dx, rx)

    # Ivory-White Chest Bib
    fill_sym_box(grid, 0, 2, 29, 34, 8, 14, 7)
    fill_sym_box(grid, 0, 1, 34, 36, 11, 15, 7)

    # --- 2. FOUR POWERFUL LEGS WITH ESPRESSO DOUBLE-BANDS & PINE-TEAL ARMOR CUFFS (Z: 0..14) ---
    def build_leg(side_sign, y_hip, y_knee, y_paw, is_front):
        x_hip = cx + side_sign * (4.1 if is_front else 3.8)
        x_paw = cx + side_sign * (4.3 if is_front else 4.0)
        z_top = 14
        for z in range(0, z_top + 1):
            t = z / float(z_top)
            if t < 0.45:
                s = t / 0.45
                ly = y_paw * (1 - s) + y_knee * s
            else:
                s = (t - 0.45) / 0.55
                ly = y_knee * (1 - s) + y_hip * s
            lx = x_paw * (1 - t) + x_hip * t
            if z <= 1:
                rx_l, ry_l = 1.85, 2.35
            elif z <= 5:
                rx_l, ry_l = 1.50, 1.75
            elif z <= 9:
                rx_l, ry_l = 1.80, 2.15
            else:
                rx_l, ry_l = 2.15, 2.60 if not is_front else 2.40
            for x in range(int(lx - 3), int(lx + 4)):
                for y in range(int(ly - 3), int(ly + 4)):
                    if 0 <= x < X and 0 <= y < Y:
                        if ((x - lx) / rx_l) ** 2 + ((y - ly) / ry_l) ** 2 <= 1.0:
                            if z <= 2 and y >= ly - 0.4:
                                col = 7  # Ivory white paws
                            elif z in (5, 6, 10, 11) and (x - cx) * side_sign >= abs(lx - cx) - 0.7:
                                col = 5  # Bold espresso leg bands
                            elif z >= 12:
                                col = 4
                            else:
                                col = 3
                            grid[x, y, z] = col
        # Ivory paws & dark claws
        px0 = int(round(x_paw - 1.5))
        px1 = int(round(x_paw + 1.5))
        py_front = int(round(y_paw + 2.0))
        fill_box(grid, px0, px1, int(round(y_paw)), py_front, 0, 1, 7)
        fill_box(grid, px0, px0, py_front + 1, py_front + 1, 0, 0, 5)
        fill_box(grid, int(round(x_paw)), int(round(x_paw)), py_front + 1, py_front + 1, 0, 0, 5)
        fill_box(grid, px1, px1, py_front + 1, py_front + 1, 0, 0, 5)
        # Pine-teal & silver armored forearm greaves on forelegs (shared from robot!)
        if is_front:
            cy_f = int(round(y_paw * 0.5 + y_knee * 0.5))
            fill_box(grid, int(round(x_paw - 1.5)), int(round(x_paw + 1.5)), cy_f - 1, cy_f + 2, 3, 5, 2)
            fill_box(grid, int(round(x_paw - 1.5)), int(round(x_paw + 1.5)), cy_f + 2, cy_f + 2, 4, 5, 1)
            fill_box(grid, int(round(x_paw - 1.5)), int(round(x_paw + 1.5)), cy_f + 2, cy_f + 2, 3, 3, 6)

    build_leg(+1, y_hip=28.5, y_knee=27.5, y_paw=33.0, is_front=True)
    build_leg(-1, y_hip=28.5, y_knee=25.5, y_paw=28.5, is_front=True)
    build_leg(+1, y_hip=13.5, y_knee=10.5, y_paw=14.5, is_front=False)
    build_leg(-1, y_hip=13.5, y_knee=9.0,  y_paw=11.5, is_front=False)

    # --- 3. SHARED KIYOMASA ARMOR: FOLDED SILVER NAGA-EBOSHI DORSAL FIN & PINE-TEAL SADDLE! ---
    # Deep pine-teal shoulder armor plates with silver bevel & gold trim
    fill_sym_box(grid, 0, 4, 24, 31, 19, 20, 2)
    fill_sym_box(grid, 4, 6, 25, 30, 15, 19, 2)
    fill_sym_box(grid, 5, 6, 26, 29, 16, 18, 1)   # Silver armor plate inlay
    fill_sym_box(grid, 5, 6, 25, 30, 15, 15, 6)   # Gold lower edge
    # Swept-back SILVER NAGA-EBOSHI DORSAL CREST (folded from robot's iconic tall helmet!)
    eboshi_back = [
        (0, 1, 31, 35, 20, 22, 1),
        (0, 1, 28, 32, 21, 23, 1),
        (0, 1, 25, 29, 22, 24, 1),
        (0, 1, 22, 26, 23, 25, 1),
        (0, 0, 19, 23, 24, 25, 1),
    ]
    for x0, x1, y0, y1, z0, z1, col in eboshi_back:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)
    # Vermilion sun-disc emblem on BOTH sides of the folded silver Naga-Eboshi fin!
    fill_sym_box(grid, 1, 1, 26, 30, 22, 23, 8)
    fill_sym_box(grid, 0, 0, 23, 33, 24, 24, 6)   # Gold spine ridge
    # Pine-teal Collar & Gold Janome Chest Medallion
    fill_sym_box(grid, 0, 4, 32, 35, 13, 20, 2)
    fill_sym_box(grid, 0, 2, 35, 36, 11, 14, 6)   # Gold Janome ring on chest!
    fill_sym_box(grid, 0, 1, 36, 36, 12, 13, 2)
    fill_sym_box(grid, 0, 0, 36, 36, 12, 12, 9)   # Glowing emerald core

    # --- 4. FIERCE GOLDEN-OCHRE TIGER HEAD, CHEEK RUFFS & EMERALD EYES (Y: 36..50, Z: 13..25) ---
    head_slices = [
        (36, 4.5, 14, 23),
        (37, 4.7, 14, 23),
        (38, 4.6, 14, 23),
        (39, 4.4, 14, 23),
        (40, 4.1, 14, 22),
        (41, 3.7, 14, 22),
        (42, 3.3, 14, 21),
    ]
    for y, rx, zb, zt in head_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    if z <= 16 and dx >= 1.5:
                        col = 7  # Crisp ivory cheeks
                    elif z <= 15:
                        col = 7
                    elif z in (17, 19) and y in (38, 40) and dx >= rx - 1.1:
                        col = 5  # Espresso cheek stripes
                    elif z >= zt - 1 and (y in (38, 40, 42) or dx < 0.8):
                        col = 5 if (dx < 0.8 or (y in (38, 40) and dx <= 2.6)) else 4
                    else:
                        col = 3
                    grid[x, y, z] = col

    # Fluffy pale-gold & ivory cheek ruffs (sculpted, non-blocky)
    fill_sym_box(grid, 4, 6, 36, 39, 15, 19, 7)
    fill_sym_box(grid, 5, 6, 36, 38, 17, 19, 3)
    fill_sym_box(grid, 6, 6, 36, 36, 15, 15, 0)

    # Rounded Tiger Ears with espresso backs & ivory ear-spots
    fill_sym_box(grid, 3, 4, 38, 40, 22, 24, 3)
    fill_sym_box(grid, 3, 4, 37, 38, 22, 24, 5)
    fill_sym_box(grid, 4, 4, 37, 37, 23, 23, 7)
    fill_sym_box(grid, 3, 3, 40, 40, 23, 23, 7)

    # Silver Forehead Brow Plate (echoes silver kabuto!) + Glowing Emerald-Cyan Eyes!
    fill_sym_box(grid, 0, 2, 40, 42, 22, 23, 1)
    fill_sym_box(grid, 0, 1, 42, 43, 22, 22, 6)   # Gold brow trim
    fill_sym_box(grid, 2, 3, 41, 43, 19, 21, 5)   # Dark espresso eyeliner
    fill_sym_box(grid, 2, 3, 43, 43, 19, 20, 9)   # Vivid glowing emerald-cyan eyes!

    # Broad Snarling Tiger Muzzle & Roaring Fangs (Y: 43..50)
    fill_sym_box(grid, 0, 1, 43, 47, 18, 20, 3)
    fill_sym_box(grid, 0, 1, 45, 46, 20, 20, 4)
    fill_sym_box(grid, 0, 1, 47, 48, 18, 19, 8)   # Vermilion-pink nose
    fill_sym_box(grid, 0, 0, 48, 48, 18, 18, 5)
    fill_sym_box(grid, 0, 2, 43, 47, 16, 17, 7)   # Ivory whisker pads
    fill_sym_box(grid, 2, 3, 43, 46, 16, 17, 7)
    fill_sym_box(grid, 0, 1, 43, 46, 14, 15, 8)   # Open roaring mouth
    fill_sym_box(grid, 1, 1, 46, 46, 15, 15, 7)   # Upper fangs
    fill_sym_box(grid, 0, 2, 43, 47, 13, 13, 7)   # Lower ivory jaw
    fill_sym_box(grid, 1, 1, 46, 46, 14, 14, 7)   # Lower fangs

    # --- 5. LONG STRIPED TAIL WITH KATAKAMA-YARI SILVER SPEAR-HOOK TIP! (Y: 1..11, Z: 12..24) ---
    tail_path = [
        (cx,       10.5, 16.0, 1.35, 3),
        (cx,        9.2, 15.2, 1.25, 5),
        (cx + 0.4,  8.0, 14.4, 1.20, 3),
        (cx + 0.9,  6.8, 13.8, 1.15, 5),
        (cx + 1.3,  5.6, 13.8, 1.15, 4),
        (cx + 1.6,  4.5, 14.4, 1.10, 5),
        (cx + 1.8,  3.6, 15.6, 1.05, 3),
        (cx + 1.8,  3.0, 17.0, 1.05, 5),
        (cx + 1.6,  2.7, 18.4, 1.00, 3),
        (cx + 1.3,  2.8, 19.8, 1.00, 6),  # Gold collar on tail tip
    ]
    prev_t = None
    for txc, tyc, tzc, tr, tcol in tail_path:
        if prev_t is not None:
            draw_6conn_line(grid, prev_t, (txc, tyc, tzc), tcol)
        prev_t = (txc, tyc, tzc)
        fill_sphere_local(grid, txc, tyc, tzc, tr, tr, tr, tcol)
    # Transformed Katakama-yari hooked silver spear-blade on the tail tip!
    tx_b = int(round(cx + 1.3))
    draw_6conn_line(grid, (tx_b, 3, 20), (tx_b, 2, 25), 1)
    draw_6conn_line(grid, (tx_b, 3, 21), (tx_b + 3, 3, 22), 1)
    draw_6conn_line(grid, (tx_b + 3, 3, 22), (tx_b + 3, 3, 24), 7)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=30, pitch_a=18, yaw_b=44, pitch_b=20):
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
    v_a = export_vox(model_a, "kiyomasa_a.vox")
    v_b = export_vox(model_b, "kiyomasa_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: KATO KIYOMASA ROBOT -> GOLDEN TIGER (TORATAIJI)",
        "1. KATO KIYOMASA ROBOT (NAGA-EBOSHI)",
        "2. GOLDEN-OCHRE TIGER",
        "preview_kiyomasa.png",
        yaw_a=30, pitch_a=18, yaw_b=44, pitch_b=20,
    )
    print(f"kiyomasa: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
