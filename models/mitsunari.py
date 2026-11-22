import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across Ishida Mitsunari Robot & White Fox so parts visibly transform!
PALETTE = {
    1: (242, 244, 248, 255),  # Pearl Snow-White Armor & Fox Fur
    2: (192, 202, 218, 255),  # Cool Silver-Grey Armor Bevels & Fur Shading
    3: (42, 52, 98, 255),     # Deep Slate-Indigo Samurai Armor & Fox Stockings
    4: (78, 96, 156, 255),    # Mid Indigo-Blue Highlights & Crest Frame
    5: (214, 48, 44, 255),    # Vermilion-Red Kitsune Markings & Lacing Cords
    6: (238, 194, 54, 255),   # Refined Gold Trim, Crest & War Fan Ribs
    7: (34, 38, 48, 255),     # Dark Lacquer Joints, Fox Nose & Paw Tips
    8: (255, 212, 52, 255),   # Glowing Amber-Gold Eyes & Crest Gem
    9: (246, 230, 198, 255),  # Warm Cream Obi, Inner Ears & Underbelly
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
# FORM A: ISHIDA MITSUNARI ROBOT (SLENDER STRATEGIST) (38 x 26 x 48)
# ============================================================
def build_a():
    grid = np.zeros((38, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18 (-X, robot left / viewer's right)
    cx_r = X // 2      # 19 (+X, robot right / viewer's left)

    # --- 1. SLENDER FOX-PAW ARMORED BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 2, 4, 10, 16, 0, 1, 7)     # Sleek dark lacquer sole (fox paw)
    fill_sym_box(grid, 2, 4, 11, 16, 1, 2, 3)     # Deep slate-indigo footplate (fox stocking)
    fill_sym_box(grid, 2, 4, 16, 17, 0, 1, 7)     # Tapered dark fox-toe tip
    fill_sym_box(grid, 3, 3, 16, 17, 1, 2, 6)     # Gold center toe ridge
    fill_sym_box(grid, 3, 4, 9, 10, 0, 2, 7)      # Slender heel spur
    fill_sym_box(grid, 2, 4, 11, 14, 3, 3, 5)     # Vermilion ankle cord tie

    # --- 2. SLENDER ATHLETIC GREAVES / SUNEATE (Z: 4..15) ---
    # Sleek tapered proportions for refined strategist Mitsunari!
    fill_sym_box(grid, 2, 4, 11, 14, 4, 14, 3)    # Slate-indigo lower leg (becomes fox dark stockings)
    fill_sym_box(grid, 2, 4, 12, 15, 7, 14, 1)    # Pearl white upper greave wrap
    fill_sym_box(grid, 3, 3, 15, 15, 8, 13, 2)    # Silver shin ridge
    fill_sym_box(grid, 4, 4, 12, 14, 7, 13, 5)    # Vermilion side kitsune stripe
    fill_sym_box(grid, 2, 4, 11, 14, 7, 7, 6)     # Gold stocking band
    # Sharp diamond samurai knee armor
    fill_sym_box(grid, 2, 4, 14, 16, 13, 16, 1)
    fill_sym_box(grid, 3, 3, 16, 16, 14, 15, 5)   # Vermilion knee accent
    fill_sym_box(grid, 2, 4, 15, 16, 13, 13, 6)   # Gold knee trim

    # --- 3. SLENDER THIGHS & LONG FLOWING KUSAZURI COAT-TAILS (Z: 15..23) ---
    fill_sym_box(grid, 2, 4, 11, 14, 15, 20, 7)   # Dark inner thigh joint
    fill_sym_box(grid, 2, 4, 12, 15, 16, 19, 1)   # White haidate thigh armor
    fill_sym_box(grid, 3, 4, 14, 15, 17, 18, 2)
    # Slim Waist & Pelvis
    fill_sym_box(grid, 0, 3, 11, 14, 20, 23, 3)
    # Refined long white & indigo skirt-tassets (strategist robe silhouette!)
    fill_sym_box(grid, 1, 4, 15, 15, 16, 21, 1)   # Front white tassets
    fill_sym_box(grid, 1, 4, 15, 15, 16, 16, 6)   # Gold bottom hem
    fill_sym_box(grid, 2, 3, 15, 15, 18, 19, 5)   # Vermilion kitsune crest mark
    fill_sym_box(grid, 4, 5, 11, 14, 16, 21, 3)   # Slate-indigo hip plates
    fill_sym_box(grid, 5, 5, 12, 13, 17, 20, 1)   # White outer hip inlay
    fill_sym_box(grid, 5, 5, 11, 14, 16, 16, 6)   # Gold trim
    fill_sym_box(grid, 0, 4, 10, 10, 16, 21, 1)   # Rear white tasset
    # Cream obi sash & gold Daiichi-Daiman-Daikichi waist buckle
    fill_sym_box(grid, 0, 4, 14, 16, 21, 22, 9)   # Cream obi sash
    fill_sym_box(grid, 0, 1, 15, 16, 19, 22, 5)   # Vermilion front sash knot
    fill_sym_box(grid, 0, 0, 16, 16, 21, 22, 6)   # Gold waist buckle

    # --- SIGNATURE BUSHY WHITE FOX-TAIL CLOAK STABILIZER ON LOWER BACK! ---
    # Sweeps gracefully back & up behind waist (clearly visible in 3/4 and REAR VIEW, transforms into Fox's tail!)
    tail_nodes = [
        (0.0,  9.5, 20.5, 1.5, 1.4, 1),
        (0.0,  8.0, 19.0, 1.9, 1.8, 1),
        (0.0,  6.5, 17.5, 2.3, 2.2, 1),
        (0.0,  5.0, 16.0, 2.5, 2.4, 1),
        (0.0,  3.8, 15.0, 2.4, 2.3, 2),
        (0.0,  2.8, 14.5, 2.0, 2.0, 1),
        (0.0,  2.0, 14.8, 1.6, 1.6, 5),  # Vermilion-tipped tail accent
        (0.0,  1.4, 15.6, 1.2, 1.2, 1),  # Crisp snow-white fox tail tip!
    ]
    cx_f = (X - 1) / 2.0
    prev_p = None
    for x_s, ty, tz, rx_t, rz_t, col in tail_nodes:
        cur_p = (cx_f + x_s, ty, tz)
        if prev_p is not None:
            draw_6conn_line(grid, prev_p, cur_p, col)
        prev_p = cur_p
        fill_sphere_local(grid, cx_f + x_s, ty, tz, rx_t, 1.4, rz_t, col)
    # Gold ring clasp anchoring fox tail to waist
    fill_sym_box(grid, 0, 1, 9, 10, 20, 21, 6)
    fill_sym_box(grid, 0, 1, 8, 9, 19, 20, 5)

    # --- 4. SLIM STRATEGIST TORSO & DAIICHI-DAIMAN-DAIKICHI CREST (Z: 23..33) ---
    fill_sym_box(grid, 0, 3, 11, 14, 23, 25, 7)   # Slim tapered waist core
    fill_sym_box(grid, 0, 3, 14, 15, 23, 25, 3)   # Indigo abdominal armor
    fill_sym_box(grid, 0, 1, 15, 15, 24, 24, 6)   # Gold waist accent
    # Crisp White & Indigo Chest Cuirass (refined, narrower than brute-force warriors!)
    fill_sym_box(grid, 0, 5, 10, 15, 26, 32, 1)   # Pearl white chest armor
    fill_sym_box(grid, 0, 4, 15, 16, 26, 31, 3)   # Deep slate-indigo breastplate
    fill_sym_box(grid, 2, 4, 15, 16, 27, 31, 4)   # Indigo angled chest bevel
    # Gold Daiichi-Daiman-Daikichi Emblem (white-and-gold square seal) + Glowing Amber Core
    fill_sym_box(grid, 0, 1, 16, 16, 27, 30, 1)
    fill_sym_box(grid, 0, 1, 16, 16, 27, 27, 6)
    fill_sym_box(grid, 0, 1, 16, 16, 30, 30, 6)
    fill_sym_box(grid, 0, 0, 16, 17, 28, 29, 8)   # Glowing amber strategist core
    # High White Fox-Fur Collar & Vermilion Lacing
    fill_sym_box(grid, 2, 4, 14, 16, 31, 32, 5)   # Vermilion shoulder straps
    fill_sym_box(grid, 0, 3, 10, 14, 32, 33, 1)   # High white collar ruff
    fill_sym_box(grid, 2, 4, 10, 13, 33, 33, 6)   # Gold collar trim
    # Sleek Rear Backpack (Z: 24..32)
    fill_sym_box(grid, 0, 3, 8, 10, 25, 31, 3)
    fill_sym_box(grid, 0, 2, 7, 8, 26, 30, 1)
    fill_sym_box(grid, 0, 1, 7, 7, 28, 29, 6)     # Rear gold crest
    fill_sym_box(grid, 2, 3, 7, 9, 25, 27, 5)     # Rear vermilion winglet tabs

    # --- 5. SLEEK SWEPT SHOULDER PAULDRONS & ARMS (Z: 15..34) ---
    fill_sym_box(grid, 5, 7, 11, 14, 29, 32, 7)   # Shoulder joints
    # Layered streamlined white & indigo Sode pauldrons
    fill_sym_box(grid, 6, 8, 10, 15, 28, 33, 1)
    fill_sym_box(grid, 6, 8, 10, 15, 33, 33, 6)   # Gold upper shoulder trim
    fill_sym_box(grid, 8, 9, 11, 14, 30, 32, 3)   # Indigo outer bevel
    fill_sym_box(grid, 8, 9, 11, 14, 29, 29, 5)   # Vermilion kitsune stripe
    fill_sym_box(grid, 7, 8, 15, 15, 29, 32, 2)
    # Slender upper arms
    fill_sym_box(grid, 6, 7, 11, 14, 23, 28, 3)
    fill_sym_box(grid, 7, 7, 12, 13, 25, 26, 5)

    # Left Arm (-X, viewer's right): Sleek white armored gauntlet & dark fox-clawed hand
    fill_box(grid, cx_l - 8, cx_l - 6, 11, 15, 17, 22, 1)
    fill_box(grid, cx_l - 8, cx_l - 8, 12, 14, 18, 21, 3)
    fill_box(grid, cx_l - 8, cx_l - 6, 12, 15, 17, 17, 6)  # Gold wrist cuff
    fill_box(grid, cx_l - 7, cx_l - 6, 12, 14, 15, 16, 7)  # Dark hand

    # Right Arm (+X, viewer's left): Angled outward holding Mitsunari's WHITE & GOLD TESSEN WAR FAN (鉄扇)!
    fill_box(grid, cx_r + 6, cx_r + 8, 11, 15, 18, 23, 1)
    fill_box(grid, cx_r + 8, cx_r + 10, 13, 16, 17, 20, 1)
    fill_box(grid, cx_r + 9, cx_r + 10, 14, 16, 17, 19, 6) # Gold cuff
    fill_box(grid, cx_r + 9, cx_r + 10, 15, 17, 16, 18, 7) # Gripping hand

    # Open White-and-Gold Strategist Folding Fan (Sensu / Tessen) held cleanly clear of body!
    fx = cx_r + 11
    fill_box(grid, fx, fx + 1, 16, 17, 15, 18, 6) # Gold pivot
    fill_box(grid, fx, fx + 1, 16, 17, 13, 14, 5) # Vermilion tassel
    fan_rays = [
        (fx + 0, 17, 18, fx - 2, 18, 26, 1),
        (fx + 0, 17, 18, fx + 0, 18, 28, 1),
        (fx + 1, 17, 18, fx + 2, 18, 28, 1),
        (fx + 1, 17, 18, fx + 4, 18, 26, 1),
        (fx + 1, 17, 18, fx + 6, 18, 23, 1),
    ]
    for x0, y0, z0, x1, y1, z1, c in fan_rays:
        draw_6conn_line(grid, (x0, y0, z0), (x1, y1, z1), c)
    # Fill fan face cleanly between outer ribs
    for rz in range(19, 28):
        t = (rz - 18) / 10.0
        lx_f = int(round(fx - 2 * t))
        rx_f = int(round(fx + 1 + 5.2 * min(1.0, t * 1.2)))
        for x_p in range(lx_f, min(X, rx_f + 1)):
            if rz >= 26:
                col = 6  # Gold upper fan border
            elif 22 <= rz <= 24 and fx <= x_p <= fx + 2:
                col = 5  # Vermilion sun/seal emblem on fan!
            elif (x_p - fx) % 2 == 0 and rz <= 21:
                col = 6  # Gold fan ribs
            else:
                col = 1  # Crisp white fan paper
            fill_box(grid, x_p, x_p, 17, 18, rz, rz, col)

    # --- 6. REFINED HEAD & TALL FOX-EAR KABUTO CREST (Z: 33..47) ---
    fill_sym_box(grid, 0, 1, 11, 14, 33, 34, 7)   # Neck
    fill_sym_box(grid, 0, 2, 10, 14, 34, 39, 1)   # White kabuto dome
    fill_sym_box(grid, 0, 3, 10, 13, 34, 36, 3)   # Slate-indigo shikoro neck-guard
    fill_sym_box(grid, 0, 3, 10, 10, 34, 34, 6)   # Gold shikoro rim
    # Face & Fox-Mask Menpo with Glowing Amber Eyes
    fill_sym_box(grid, 0, 2, 14, 15, 34, 35, 2)   # Sleek silver chin/menpo
    fill_sym_box(grid, 0, 2, 14, 15, 36, 37, 7)   # Dark visor socket
    fill_sym_box(grid, 1, 2, 15, 15, 36, 37, 8)   # Sharp glowing amber fox-eyes!
    fill_sym_box(grid, 0, 0, 15, 15, 36, 37, 1)   # White nose bridge
    fill_sym_box(grid, 1, 2, 15, 15, 35, 35, 5)   # Kitsune red cheek markings!
    fill_sym_box(grid, 0, 2, 14, 16, 38, 38, 3)   # Indigo kabuto brow visor
    fill_sym_box(grid, 0, 1, 16, 16, 38, 39, 6)   # Gold central maedate diamond

    # ICONIC POINTED WHITE FOX-EAR HELMET CRESTS (transform directly into Fox's ears!)
    ear_segs = [
        (2, 3, 12, 14, 39, 41, 1),
        (2, 4, 12, 14, 41, 42, 1),
        (3, 4, 12, 13, 42, 44, 1),
        (3, 4, 12, 13, 44, 45, 5),  # Vermilion inner/mid-tip accent
        (4, 4, 12, 13, 45, 47, 7),  # Crisp dark fox-ear tips!
    ]
    for x0, x1, y0, y1, z0, z1, col in ear_segs:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)
    # Warm cream inner ear lining on front
    fill_sym_box(grid, 2, 3, 14, 14, 40, 43, 9)
    fill_sym_box(grid, 3, 3, 14, 14, 41, 42, 5)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: WHITE FOX (SHIRO-GITSUNE) (24 x 54 x 28)
# ============================================================
def build_b():
    grid = np.zeros((24, 54, 28), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 11.5

    # --- 1. SLENDER GRACEFUL WHITE FOX BODY (Y: 16..37, Z: 8..17) ---
    body_slices = [
        # (y, rx, zb, zt)
        (16, 2.5, 11, 16),   # Tapered rump
        (17, 3.2, 10, 17),
        (18, 3.6, 10, 17),   # Hindquarters
        (19, 3.7, 10, 17),
        (20, 3.5, 10, 17),
        (21, 3.2, 10, 16),
        (22, 2.9, 10, 16),   # Graceful slender waist
        (23, 2.8, 10, 16),
        (24, 2.8, 10, 16),
        (25, 2.9, 10, 16),
        (26, 3.1, 9,  16),   # Sleek ribcage
        (27, 3.4, 9,  17),
        (28, 3.7, 9,  17),
        (29, 3.9, 9,  17),   # Chest & shoulders
        (30, 4.0, 9,  17),
        (31, 4.0, 9,  18),
        (32, 3.8, 9,  18),
        (33, 3.5, 10, 18),
        (34, 3.2, 11, 18),   # Upright graceful fox neck
        (35, 3.0, 12, 19),
        (36, 2.9, 13, 20),
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
                    if z <= zb + 1 and dx <= rx * 0.65:
                        col = 9  # Warm cream underbelly
                    elif z >= zt - 1 and dx <= 1.1:
                        col = 2  # Soft silver-grey dorsal sheen
                    else:
                        col = 1  # Pearl snow-white fox fur
                    grid[x, y, z] = col

    # Fluffy White Chest Ruff
    fill_sym_box(grid, 0, 2, 33, 36, 10, 16, 1)
    fill_sym_box(grid, 0, 1, 36, 37, 12, 15, 9)

    # --- 2. MITSUNARI'S INDIGO & GOLD ARMORED SADDLE & COLLAR (Shared Armor!) ---
    # Deep slate-indigo saddle armor across shoulders/back echoing robot cuirass!
    fill_sym_box(grid, 0, 3, 27, 33, 16, 18, 3)
    fill_sym_box(grid, 3, 4, 28, 32, 14, 17, 3)  # Indigo shoulder-armor side flaps
    fill_sym_box(grid, 4, 4, 29, 31, 15, 16, 4)  # Mid-indigo bevel
    fill_sym_box(grid, 3, 4, 28, 32, 14, 14, 6)  # Gold lower trim
    fill_sym_box(grid, 0, 1, 28, 32, 18, 18, 6)  # Gold dorsal spine trim
    # Vermilion Kitsune Neck Cord & Gold Daiichi-Daiman-Daikichi Chest Medallion!
    fill_sym_box(grid, 0, 3, 33, 36, 15, 19, 5)  # Vermilion shrine-cord collar
    fill_sym_box(grid, 0, 2, 36, 37, 13, 15, 3)  # Indigo front pendant plate
    fill_sym_box(grid, 0, 1, 37, 38, 13, 15, 6)  # Gold crest medallion
    fill_sym_box(grid, 0, 0, 38, 38, 14, 14, 8)  # Glowing amber core gem

    # --- 3. FOUR SLENDER FOX LEGS WITH DARK INDIGO STOCKINGS (Z: 0..13) ---
    def build_fox_leg(side_sign, y_hip, y_knee, y_paw, is_front):
        x_hip = cx + side_sign * (3.1 if is_front else 2.9)
        x_paw = cx + side_sign * (2.9 if is_front else 2.8)
        z_top = 13
        for z in range(0, z_top + 1):
            t = z / float(z_top)
            if t < 0.48:
                s = t / 0.48
                ly = y_paw * (1 - s) + y_knee * s
            else:
                s = (t - 0.48) / 0.52
                ly = y_knee * (1 - s) + y_hip * s
            lx = x_paw * (1 - t) + x_hip * t
            if z <= 1:
                rx_l, ry_l = 1.25, 1.85
            elif z <= 6:
                rx_l, ry_l = 1.05, 1.15
            elif z <= 10:
                rx_l, ry_l = 1.25, 1.55
            else:
                rx_l, ry_l = 1.65, 2.05 if not is_front else 1.85
            for x in range(int(lx - 2), int(lx + 3)):
                for y in range(int(ly - 3), int(ly + 4)):
                    if 0 <= x < X and 0 <= y < Y:
                        if ((x - lx) / rx_l) ** 2 + ((y - ly) / ry_l) ** 2 <= 1.0:
                            if z <= 1:
                                col = 7  # Dark fox paw tips
                            elif z <= 5:
                                col = 3  # Iconic slate-indigo fox stockings!
                            elif z == 6:
                                col = 6 if is_front else 5  # Gold/vermilion stocking band!
                            else:
                                col = 1  # Pearl white upper legs
                            grid[x, y, z] = col
        # Crisp neat dark fox paws grounded at z=0
        px0 = int(round(x_paw - 1.0))
        px1 = int(round(x_paw + 1.0))
        py0 = int(round(y_paw - 0.5))
        py1 = int(round(y_paw + 2.0))
        fill_box(grid, px0, px1, py0, py1, 0, 1, 7)

    # Graceful trotting / alert stance!
    build_fox_leg(+1, y_hip=31.0, y_knee=30.0, y_paw=34.0, is_front=True)
    build_fox_leg(-1, y_hip=31.0, y_knee=29.0, y_paw=31.0, is_front=True)
    build_fox_leg(+1, y_hip=19.0, y_knee=16.0, y_paw=20.0, is_front=False)
    build_fox_leg(-1, y_hip=19.0, y_knee=15.0, y_paw=17.5, is_front=False)

    # --- 4. SHARP SLEEK FOX HEAD, POINTED MUZZLE & TALL EARS (Y: 35..51, Z: 15..27) ---
    # Sleek triangular fox skull
    head_slices = [
        (36, 3.6, 16, 22),
        (37, 3.9, 16, 23),
        (38, 4.0, 16, 23),
        (39, 3.8, 16, 23),
        (40, 3.5, 16, 22),
        (41, 3.1, 16, 22),
        (42, 2.7, 16, 21),
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
                    if z <= 17 and dx >= 1.5:
                        col = 1  # Cheek fur ruffs
                    elif z == 18 and y in (39, 41) and dx >= rx - 1.1:
                        col = 5  # Kitsune vermilion cheek markings!
                    elif z >= zt - 1 and dx <= 0.7 and y >= 39:
                        col = 5  # Vermilion forehead diamond
                    else:
                        col = 1
                    grid[x, y, z] = col

    # Fluffy sculpted white cheek tufts flaring slightly outward
    fill_sym_box(grid, 3, 4, 37, 39, 16, 18, 1)
    fill_sym_box(grid, 4, 4, 37, 38, 17, 17, 2)

    # Sharp Glowing Amber Fox Eyes with dark eyeliner!
    fill_sym_box(grid, 2, 3, 40, 42, 19, 20, 7)
    fill_sym_box(grid, 2, 3, 41, 42, 19, 20, 8)  # Glowing amber fox eyes!
    fill_sym_box(grid, 2, 3, 41, 42, 18, 18, 5)  # Vermilion kitsune eye-corner streak!

    # Long Pointed Fox Snout (distinctly sleeker & longer than a tiger or wolf!)
    fill_sym_box(grid, 0, 1, 42, 46, 17, 20, 1)
    fill_sym_box(grid, 0, 1, 46, 49, 17, 19, 1)
    fill_sym_box(grid, 0, 0, 49, 51, 18, 19, 1)
    fill_sym_box(grid, 0, 0, 51, 52, 18, 19, 7)  # Crisp black fox nose tip!
    fill_sym_box(grid, 0, 1, 43, 48, 16, 16, 9)  # Cream lower jaw/chin
    fill_sym_box(grid, 0, 0, 48, 50, 16, 17, 1)

    # TALL POINTED WHITE FOX EARS (transformed directly from robot's helmet crests!)
    fox_ears = [
        (2, 3, 37, 39, 22, 23, 1),
        (2, 4, 37, 39, 23, 24, 1),
        (3, 4, 37, 38, 24, 25, 1),
        (3, 4, 37, 38, 25, 26, 5),  # Vermilion upper ear band
        (3, 4, 37, 38, 26, 27, 7),  # Dark pointed fox ear tips!
    ]
    for x0, x1, y0, y1, z0, z1, col in fox_ears:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)
    # Warm cream inner ear front face & dark back edge
    fill_sym_box(grid, 2, 3, 39, 39, 23, 25, 9)
    fill_sym_box(grid, 3, 3, 37, 37, 24, 26, 3)  # Indigo-dark ear backs

    # --- 5. GRAND VOLUMINOUS SWEEPING WHITE FOX TAIL (Y: 1..17, Z: 11..23) ---
    # Lush, iconic bushy kitsune tail sweeping gracefully backward and curling high!
    tail_path = [
        (cx,       16.0, 14.5, 1.8, 1.8, 1),
        (cx,       14.5, 14.0, 2.3, 2.3, 1),
        (cx + 0.2, 12.8, 13.5, 2.8, 2.7, 1),
        (cx + 0.5, 11.0, 13.5, 3.2, 3.1, 1),
        (cx + 0.8,  9.2, 14.0, 3.4, 3.3, 1),
        (cx + 1.0,  7.4, 15.0, 3.4, 3.3, 1),
        (cx + 1.1,  5.8, 16.4, 3.2, 3.1, 2),
        (cx + 1.0,  4.4, 18.0, 2.9, 2.8, 1),
        (cx + 0.8,  3.4, 19.6, 2.5, 2.4, 5),  # Vermilion kitsune tail-tip band!
        (cx + 0.6,  2.8, 21.2, 2.0, 2.0, 1),  # Crisp snow-white plush tip!
        (cx + 0.4,  2.5, 22.6, 1.4, 1.4, 1),
    ]
    prev_t = None
    for txc, tyc, tzc, trx, trz, tcol in tail_path:
        if prev_t is not None:
            draw_6conn_line(grid, prev_t, (txc, tyc, tzc), tcol)
        prev_t = (txc, tyc, tzc)
        fill_sphere_local(grid, txc, tyc, tzc, trx, 1.8, trz, tcol)
    # Gold ring clasp at tail base echoing robot waist clasp
    fill_sym_box(grid, 0, 1, 15, 16, 15, 16, 6)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=28, pitch_a=20, yaw_b=42, pitch_b=20):
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
    v_a = export_vox(model_a, "mitsunari_a.vox")
    v_b = export_vox(model_b, "mitsunari_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: ISHIDA MITSUNARI ROBOT -> WHITE FOX (SHIRO-GITSUNE)",
        "1. ISHIDA MITSUNARI ROBOT",
        "2. WHITE FOX (KITSUNE)",
        "preview_mitsunari.png",
        yaw_a=28, pitch_a=20, yaw_b=44, pitch_b=20,
    )
    print(f"mitsunari: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
