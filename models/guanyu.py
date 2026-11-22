import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Guan Yu (関羽) -> Emerald-Gold General Robot -> Azure/Emerald Dragon (青龍)!
# Green battle robe, ruddy crimson face, long black beard & Green Dragon Crescent Blade -> armor & dragon motifs!
PALETTE = {
    1: (28, 128, 72, 255),    # Iconic Guan Yu Emerald-Green Battle Robe & Main Armor
    2: (18, 82, 48, 255),     # Deep Forest-Green Robe Shading & Inner Armor
    3: (242, 196, 52, 255),   # Radiant Imperial Gold Dragon Trim & Blade Collar
    4: (26, 28, 36, 255),     # Jet-Black Long Flowing Beard (美髯) & Boots/Joints
    5: (204, 62, 54, 255),    # Iconic Ruddy Crimson Face (赤顔) & Sash Accent
    6: (218, 226, 236, 255),  # Honed Silver Green Dragon Crescent Blade (青龍偃月刀)
    7: (134, 82, 42, 255),    # Dark Hardwood Glaive Shaft & Belt Trim
    8: (246, 242, 228, 255),  # Crisp Ivory Inner Robe Collar & Trim
    9: (102, 244, 152, 255),  # Glowing Jade-Emerald Eyes & Dragon Core
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


def draw_crescent_glaive(grid, gx, gy, z_bot, z_top):
    """Draw Guan Yu's iconic Green Dragon Crescent Blade (青龍偃月刀)."""
    fill_box(grid, gx, gx, gy, gy, z_bot, z_top - 10, 7)       # Pole shaft
    fill_box(grid, gx, gx, gy, gy, z_bot, z_bot + 1, 3)        # Gold butt-cap
    fill_box(grid, gx - 1, gx + 1, gy, gy, z_top - 11, z_top - 9, 3)  # Golden dragon-mouth collar!
    # Sweeping broad curved crescent blade
    for i in range(11):
        bz = z_top - 9 + i
        bx_r = gx + (2 if i < 6 else (1 if i < 9 else 0))
        bx_l = gx - (1 if i < 4 else 0)
        fill_box(grid, bx_l, bx_r, gy, gy, bz, bz, 6)          # Honed silver blade
        if i in (2, 3, 4, 5):
            fill_box(grid, bx_r, bx_r, gy, gy, bz, bz, 8)      # Gleaming sharp edge
        if i <= 7:
            fill_box(grid, bx_l, bx_l, gy, gy, bz, bz, 1)      # Green dragon spine inlay!
    # Iconic crimson tassel beneath dragon-mouth collar
    fill_box(grid, gx + 1, gx + 1, gy, gy, z_top - 14, z_top - 11, 5)


# ============================================================
# FORM A: GUAN YU CHARACTER FIGURE (36 x 22 x 44) [UNCHANGED]
# ============================================================
def build_a():
    grid = np.zeros((36, 22, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 17
    cx_r = X // 2      # 18

    # Boots & Lower Flowing Emerald Battle Robe (Z: 0..17)
    fill_sym_box(grid, 2, 4, 9, 14, 0, 2, 4)      # Black warrior boots
    fill_sym_box(grid, 2, 4, 14, 15, 0, 1, 3)     # Gold toe trim
    for z in range(2, 18):
        rw = 6 - (z - 2) // 8
        fill_sym_box(grid, 0, rw, 8, 14, z, z, 1) # Long flowing emerald-green battle robe!
        if z == 2:
            fill_sym_box(grid, 0, rw, 8, 14, z, z, 3)  # Gold robe hem
        fill_sym_box(grid, 0, 1, 14, 15, z, z, 2) # Center robe fold
    # Waist Sash & Golden Belt Clasp (Z: 17..19)
    fill_sym_box(grid, 0, 5, 8, 15, 17, 19, 3)
    fill_sym_box(grid, 0, 1, 15, 15, 17, 19, 5)   # Crimson waist sash knot

    # Torso & Layered Emerald-Gold Robe Chest (Z: 19..29)
    fill_sym_box(grid, 0, 5, 8, 14, 19, 28, 1)
    fill_sym_box(grid, 2, 4, 14, 15, 20, 27, 2)   # Robe lapel shading
    fill_sym_box(grid, 0, 2, 14, 15, 27, 29, 8)   # White inner collar
    fill_sym_box(grid, 3, 5, 9, 14, 26, 29, 3)    # Gold-trimmed warrior shoulders
    # Rear flowing green cloak (Y: 6..8, Z: 6..27)
    fill_sym_box(grid, 0, 4, 7, 8, 6, 27, 2)
    fill_sym_box(grid, 0, 4, 7, 7, 6, 7, 3)

    # Arms: Left hand poised stroking beard, Right hand holding Green Dragon Crescent Blade!
    fill_box(grid, cx_l - 7, cx_l - 5, 9, 13, 21, 27, 1)   # Left sleeve
    fill_box(grid, cx_l - 7, cx_l - 5, 12, 15, 20, 22, 1)
    fill_box(grid, cx_l - 5, cx_l - 3, 14, 16, 20, 22, 5)  # Left ruddy hand near beard!
    fill_box(grid, cx_r + 5, cx_r + 7, 9, 13, 21, 27, 1)   # Right sleeve
    fill_box(grid, cx_r + 6, cx_r + 9, 12, 16, 20, 22, 1)
    fill_box(grid, cx_r + 8, cx_r + 9, 15, 17, 20, 22, 5)  # Gripping hand!
    # Iconic Green Dragon Crescent Blade standing tall on right!
    draw_crescent_glaive(grid, cx_r + 10, 16, z_bot=2, z_top=42)

    # Head: Iconic Ruddy Crimson Face, Dignified Brows, Green Cap & LONG FLOWING BLACK BEARD! (Z: 29..40)
    fill_sym_box(grid, 0, 1, 10, 13, 29, 30, 5)   # Neck
    fill_sym_box(grid, 0, 3, 9, 14, 30, 36, 5)    # Ruddy crimson face (赤顔)!
    fill_sym_box(grid, 1, 2, 14, 15, 33, 33, 4)   # Fierce phoenix eyes & brows
    fill_sym_box(grid, 1, 2, 15, 15, 34, 34, 4)
    # Green Scholar-General Headscarf Cap (緑幘) + Gold Crown Band!
    fill_sym_box(grid, 0, 3, 8, 15, 35, 38, 1)
    fill_sym_box(grid, 0, 2, 9, 14, 39, 40, 1)
    fill_sym_box(grid, 0, 3, 14, 15, 35, 36, 3)   # Gold brow band
    fill_sym_box(grid, 0, 2, 6, 8, 28, 36, 1)     # Rear trailing green cap ribbons!
    # ICONIC LONG FLOWING JET-BLACK BEARD (美髯) cascading dramatically down chest! (Z: 17..32)
    fill_sym_box(grid, 0, 2, 14, 16, 29, 32, 4)
    fill_sym_box(grid, 0, 2, 15, 16, 23, 29, 4)
    fill_sym_box(grid, 0, 1, 15, 16, 17, 23, 4)   # Tapered long beard tip reaching waist!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: GUAN YU EMERALD-GOLD GENERAL ROBOT (46 x 26 x 48) [UNCHANGED]
# ============================================================
def build_b():
    grid = np.zeros((46, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 22
    cx_r = X // 2      # 23

    # Heavy Armored Boots & Emerald Greaves (Z: 0..16)
    fill_sym_box(grid, 3, 6, 9, 17, 0, 2, 4)      # Dark steel sole
    fill_sym_box(grid, 3, 6, 10, 17, 1, 3, 1)     # Emerald foot armor
    fill_sym_box(grid, 4, 5, 17, 18, 1, 2, 3)     # Gold dragon toe-cap
    fill_sym_box(grid, 3, 6, 10, 15, 4, 14, 1)    # Emerald greaves
    fill_sym_box(grid, 4, 5, 15, 16, 5, 13, 3)    # Gold shin ridge
    fill_sym_box(grid, 6, 6, 11, 14, 6, 12, 2)    # Dark green outer fin
    fill_sym_box(grid, 3, 6, 15, 17, 12, 15, 3)   # Gold knee shields
    fill_sym_box(grid, 4, 5, 17, 17, 13, 14, 9)   # Glowing jade knee core

    # Thighs & Emerald-Gold General Skirt Armor (Z: 15..23)
    fill_sym_box(grid, 3, 5, 10, 15, 15, 19, 4)
    fill_sym_box(grid, 3, 5, 13, 15, 15, 18, 2)
    fill_sym_box(grid, 0, 5, 10, 15, 19, 22, 4)
    fill_sym_box(grid, 2, 6, 15, 16, 17, 21, 1)   # Emerald front tassets
    fill_sym_box(grid, 2, 6, 16, 16, 17, 17, 3)   # Gold hem
    fill_sym_box(grid, 6, 7, 10, 15, 17, 21, 1)   # Side hip skirts
    fill_sym_box(grid, 0, 5, 9, 10, 17, 21, 2)    # Rear skirt
    fill_sym_box(grid, 0, 1, 15, 17, 18, 22, 5)   # Crimson waist sash core
    fill_sym_box(grid, 0, 1, 17, 17, 20, 21, 3)   # Gold buckle

    # Broad Emerald Dragon-Cuirass Torso (Z: 22..34)
    fill_sym_box(grid, 0, 4, 10, 15, 22, 24, 4)
    fill_sym_box(grid, 0, 7, 9, 16, 25, 33, 1)    # Broad emerald armored chest!
    fill_sym_box(grid, 2, 6, 16, 17, 26, 32, 2)   # Layered green breastplate
    fill_sym_box(grid, 0, 3, 16, 18, 27, 31, 3)   # Golden Green-Dragon chest emblem!
    fill_sym_box(grid, 0, 1, 18, 18, 28, 30, 9)   # Glowing jade dragon core!
    fill_sym_box(grid, 1, 5, 10, 15, 33, 34, 8)   # White inner collar
    # Rear Armored Cloak-Wing Backpack (Y: 5..9, Z: 14..33)
    fill_sym_box(grid, 0, 5, 7, 9, 24, 32, 2)
    fill_sym_box(grid, 0, 5, 6, 7, 14, 31, 1)     # Armored green cape plates!
    fill_sym_box(grid, 0, 5, 6, 6, 14, 15, 3)     # Gold cape hem

    # CRESCENT-BLADE SHOULDER PAULDRONS (青龍偃月刀の意匠が肩装甲に!) (Z: 28..38)
    fill_sym_box(grid, 7, 9, 11, 15, 29, 32, 4)
    fill_sym_box(grid, 8, 12, 10, 16, 28, 34, 1)  # Emerald heavy pauldrons
    fill_sym_box(grid, 8, 12, 10, 16, 34, 34, 3)  # Gold shoulder rim
    # Sweeping Silver Crescent-Glaive Shoulder Fin-Blades arching outward & upward!
    draw_6conn_line(grid, (cx_r + 10, 13, 34), (cx_r + 15, 13, 38), 6, pad=(0, 1, 0))
    draw_6conn_line(grid, (cx_r + 12, 13, 34), (cx_r + 16, 13, 36), 8)
    draw_6conn_line(grid, (cx_l - 10, 13, 34), (cx_l - 15, 13, 38), 6, pad=(0, 1, 0))
    draw_6conn_line(grid, (cx_l - 12, 13, 34), (cx_l - 16, 13, 36), 8)

    # Arms & Giant Green Dragon Crescent Blade!
    fill_sym_box(grid, 8, 10, 11, 15, 22, 28, 4)
    fill_box(grid, cx_l - 11, cx_l - 8, 11, 16, 16, 21, 1)
    fill_box(grid, cx_l - 11, cx_l - 8, 12, 16, 16, 16, 3)
    fill_box(grid, cx_l - 10, cx_l - 8, 12, 15, 14, 15, 4)
    fill_box(grid, cx_r + 8, cx_r + 11, 11, 16, 17, 22, 1)
    fill_box(grid, cx_r + 10, cx_r + 13, 14, 18, 16, 19, 3)
    fill_box(grid, cx_r + 12, cx_r + 14, 16, 19, 15, 18, 4)
    draw_crescent_glaive(grid, cx_r + 15, 18, z_bot=3, z_top=46)

    # Head: Ruddy-Crimson Armored Face, Emerald-Gold General Helm & ARMORED BEARD PLUME (髭が装甲意匠!)
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 4)
    fill_sym_box(grid, 0, 3, 11, 16, 35, 42, 1)   # Emerald general kabuto
    fill_sym_box(grid, 0, 3, 10, 15, 42, 43, 1)   # High cap dome
    fill_sym_box(grid, 0, 2, 16, 17, 35, 39, 5)   # Ruddy-crimson face armor!
    fill_sym_box(grid, 1, 2, 17, 17, 38, 38, 9)   # Glowing jade dragon eyes!
    fill_sym_box(grid, 0, 3, 15, 18, 39, 40, 3)   # Gold brow dragon crown!
    fill_sym_box(grid, 0, 1, 17, 18, 41, 44, 3)   # Tall gold forehead crest!
    # SIGNATURE ARMORED LAYERED BLACK-AND-GOLD BEARD CHIN-GUARD cascading over chest! (Z: 24..36)
    fill_sym_box(grid, 0, 2, 17, 18, 31, 36, 4)   # Armored segmented black beard plate!
    fill_sym_box(grid, 0, 1, 18, 19, 25, 31, 4)   # Flowing tapered armored beard spine!
    fill_sym_box(grid, 0, 1, 19, 19, 29, 29, 3)   # Gold armor clasp on beard!
    fill_sym_box(grid, 0, 1, 19, 19, 25, 25, 3)   # Gold beard finial tip!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: AZURE / EMERALD DRAGON (青龍: 緑と金の竜) (32 x 32 x 42)
# ============================================================
def build_c():
    grid = np.zeros((32, 32, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx, cy = 16, 16

    # Sweeping Coiled Emerald-and-Gold Serpentine Dragon rising from Z=0!
    pts = []
    n_steps = 56
    for i in range(n_steps + 1):
        t = i / n_steps
        ang = t * 2.55 * np.pi - 0.5 * np.pi
        rad = 10.5 * (1.0 - 0.52 * t)
        z = 1.5 + 31.0 * (t ** 1.05)
        x = cx + rad * np.cos(ang)
        y = cy + rad * np.sin(ang)
        pts.append((x, y, z))

    # Draw coiled emerald dragon body + gold belly plates + dorsal ridge spines
    for i in range(len(pts) - 1):
        t = i / len(pts)
        pad_r = (2, 2, 1) if t < 0.55 else (1, 1, 1)
        col_main = 1 if (i % 3 != 0) else 2
        draw_6conn_line(grid, pts[i], pts[i + 1], col_main, pad=pad_r)
        # Golden belly-scale stripe on underside/front
        p_belly = (pts[i][0], pts[i][1] + 1, max(0, pts[i][2] - 1))
        draw_6conn_line(grid, p_belly, (pts[i + 1][0], pts[i + 1][1] + 1, max(0, pts[i + 1][2] - 1)), 3, pad=(1, 0, 0))
        # Golden dorsal fin ridge along upper spine
        if i % 4 == 0 and t > 0.08:
            px_, py_, pz_ = int(round(pts[i][0])), int(round(pts[i][1])), int(round(pts[i][2]))
            fill_box(grid, px_, px_, py_, py_, pz_ + 1, pz_ + 2, 3)

    # Ensure bottom coil rests solidly on Z=0 directly under the lower dragon spiral
    for i in range(14):
        px_, py_ = int(round(pts[i][0])), int(round(pts[i][1]))
        fill_box(grid, px_ - 2, px_ + 2, py_ - 2, py_ + 2, 0, 1, 2)

    # Tail tip with golden crescent-blade fin!
    t0 = pts[0]
    draw_6conn_line(grid, t0, (t0[0] + 4, t0[1] - 4, 2), 1, pad=(1, 1, 0))
    fill_box(grid, int(t0[0]) + 4, int(t0[0]) + 6, int(t0[1]) - 6, int(t0[1]) - 3, 1, 4, 3)

    # Front Dragon Claws anchored directly to spiral mid-body, holding Glowing Jade-Gold Dragon Pearl!
    anchor = pts[32]
    draw_6conn_line(grid, anchor, (10, 24, 22), 1, pad=(1, 1, 0))
    draw_6conn_line(grid, anchor, (22, 24, 22), 1, pad=(1, 1, 0))
    fill_box(grid, 9, 11, 24, 26, 21, 23, 3)     # Left golden claws
    fill_box(grid, 21, 23, 24, 26, 21, 23, 3)   # Right golden claws
    draw_6conn_line(grid, (11, 25, 22), (14, 26, 22), 3)
    draw_6conn_line(grid, (21, 25, 22), (18, 26, 22), 3)
    fill_box(grid, 14, 18, 24, 28, 20, 24, 9)   # Glowing Jade Dragon Pearl!
    fill_box(grid, 15, 17, 25, 27, 21, 23, 8)

    # Majestic Emerald Dragon Head facing +Y with Guan Yu's Long Black Whiskers & Gold Antlers! (Z: 31..41)
    hx, hy, hz = int(round(pts[-1][0])), int(round(pts[-1][1])), int(round(pts[-1][2]))
    draw_6conn_line(grid, (hx, hy, hz), (16, 18, 34), 1, pad=(2, 2, 1))
    fill_box(grid, 13, 19, 17, 24, 33, 37, 1)   # Dragon cranium
    fill_box(grid, 14, 18, 24, 28, 33, 36, 1)   # Upper dragon snout
    fill_box(grid, 14, 18, 23, 27, 31, 32, 3)   # Golden lower jaw
    fill_box(grid, 15, 17, 24, 26, 32, 32, 5)   # Crimson inner mouth!
    fill_box(grid, 14, 14, 26, 26, 32, 33, 8)   # Ivory fangs
    fill_box(grid, 18, 18, 26, 26, 32, 33, 8)
    fill_box(grid, 13, 13, 21, 22, 35, 36, 9)   # Glowing jade dragon eyes!
    fill_box(grid, 19, 19, 21, 22, 35, 36, 9)
    fill_box(grid, 14, 18, 20, 23, 37, 37, 3)   # Gold brow ridge
    # Sweeping Golden Antlers (Z: 37..41)
    draw_6conn_line(grid, (14, 18, 37), (10, 13, 41), 3)
    draw_6conn_line(grid, (18, 18, 37), (22, 13, 41), 3)
    draw_6conn_line(grid, (11, 15, 39), (9, 16, 41), 3)
    draw_6conn_line(grid, (21, 15, 39), (23, 16, 41), 3)
    # Guan Yu's Signature Long Flowing Black Dragon Beard & Whiskers!
    draw_6conn_line(grid, (16, 25, 31), (16, 28, 26), 4, pad=(1, 0, 0))
    draw_6conn_line(grid, (14, 27, 34), (9, 29, 31), 4)
    draw_6conn_line(grid, (18, 27, 34), (23, 29, 31), 4)

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


def render_preview_3(forms, title_banner, out_path):
    cw, ch = 1274, 540
    canvas = Image.new("RGBA", (cw, ch), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, cw, 20):
        draw.line([(gx, 0), (gx, ch)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, ch, 20):
        draw.line([(0, gy), (cw, gy)], fill=(28, 34, 48, 255), width=1)
    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(forms):
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
    v_a = export_vox(model_a, "guanyu_a.vox")
    v_b = export_vox(model_b, "guanyu_b.vox")
    v_c = export_vox(model_c, "guanyu_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview_3(
        [
            ("1. GUAN YU (CHARACTER)", model_a, v_a, 28, 18),
            ("2. GUAN YU ROBOT", model_b, v_b, 28, 18),
            ("3. AZURE DRAGON (BEAST)", model_c, v_c, 32, 20),
        ],
        "THREE KINGDOMS #01: GUAN YU - CHARACTER / ROBOT / AZURE DRAGON",
        "preview_guanyu.png",
    )
    print(f"guanyu: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
