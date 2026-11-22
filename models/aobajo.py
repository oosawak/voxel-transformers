import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across Aoba Castle (Sendai Castle) & Aoba-jo Fortress Robot!
# No tenshu keep, no equestrian statue: stone walls (ishigaki), 4 corner watchtowers (monomi-yagura),
# single-story Honmaru Goten palace (golden motif), and Hirose-River cliffside Kakezukuri overhang!
PALETTE = {
    1: (158, 162, 168, 255),  # Sendai Castle Light Stone Wall (Ishigaki)
    2: (98, 104, 114, 255),   # Deep Stone Masonry Shadow & Hirose Cliff Rock
    3: (242, 238, 230, 255),  # Crisp White Shikkui Plaster Walls
    4: (44, 54, 74, 255),     # Deep Slate-Blue Kawara Roof Tiles
    5: (82, 98, 126, 255),    # Mid Roof-Tile Ridge Highlights & Iron Trim
    6: (154, 96, 50, 255),    # Warm Cedar Timber (Kakezukuri Stilt Lattice)
    7: (88, 52, 28, 255),     # Deep Cedar Shadow Beams & Dark Windows
    8: (244, 198, 52, 255),   # Radiant Sendai Palace Gold (Honmaru Goten Crown & Trim)
    9: (56, 152, 82, 255),    # Aoba ("Green Leaf") Pine Foliage & Glowing Emerald Eyes
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


def fill_ishigaki(grid, x0, x1, y0, y1, z0, z1):
    """Fill stone wall masonry with realistic alternating ashlar stone blocks."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(int(x0), int(x1))), min(X - 1, max(int(x0), int(x1)))
    y0, y1 = max(0, min(int(y0), int(y1))), min(Y - 1, max(int(y0), int(y1)))
    z0, z1 = max(0, min(int(z0), int(z1))), min(Z - 1, max(int(z0), int(z1)))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                bx = (x + (z // 2) * 2) // 3
                by = (y + (z // 2) * 2) // 3
                bz = z // 2
                grid[x, y, z] = 2 if (bx + by + bz) % 3 == 0 else 1


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


def build_yagura(grid, cx, cy, z_base, half_w=4):
    """Build a crisp 2-story corner watchtower (Monomi-Yagura) with white plaster & tile roofs."""
    fill_ishigaki(grid, cx - half_w, cx + half_w, cy - half_w, cy + half_w, z_base, z_base + 1)
    # 1st story white plaster walls
    fill_box(grid, cx - half_w + 1, cx + half_w - 1, cy - half_w + 1, cy + half_w - 1, z_base + 2, z_base + 5, 3)
    fill_box(grid, cx - 1, cx + 1, cy + half_w - 1, cy + half_w - 1, z_base + 3, z_base + 4, 7)
    fill_box(grid, cx - 1, cx + 1, cy - half_w + 1, cy - half_w + 1, z_base + 3, z_base + 4, 7)
    fill_box(grid, cx + half_w - 1, cx + half_w - 1, cy - 1, cy + 1, z_base + 3, z_base + 4, 7)
    fill_box(grid, cx - half_w + 1, cx - half_w + 1, cy - 1, cy + 1, z_base + 3, z_base + 4, 7)
    # 1st story eaves
    fill_box(grid, cx - half_w - 1, cx + half_w + 1, cy - half_w - 1, cy + half_w + 1, z_base + 6, z_base + 6, 4)
    fill_box(grid, cx - half_w, cx + half_w, cy - half_w, cy + half_w, z_base + 7, z_base + 7, 5)
    # 2nd story turret
    w2 = half_w - 2
    fill_box(grid, cx - w2, cx + w2, cy - w2, cy + w2, z_base + 8, z_base + 10, 3)
    fill_box(grid, cx - 1, cx + 1, cy + w2, cy + w2, z_base + 9, z_base + 9, 7)
    fill_box(grid, cx + w2, cx + w2, cy - 1, cy + 1, z_base + 9, z_base + 9, 7)
    # Top hip-and-gable roof + gold ridge
    for i in range(4):
        rw = half_w - i
        fill_box(grid, cx - rw, cx + rw, cy - rw, cy + rw, z_base + 11 + i, z_base + 11 + i, 4 if i % 2 == 0 else 5)
    fill_box(grid, cx - 1, cx + 1, cy, cy, z_base + 15, z_base + 15, 8)
    fill_box(grid, cx - 1, cx - 1, cy, cy, z_base + 16, z_base + 16, 8)
    fill_box(grid, cx + 1, cx + 1, cy, cy, z_base + 16, z_base + 16, 8)


# ============================================================
# FORM A: AOBA CASTLE / SENDAI CASTLE (58 x 54 x 36)
# ============================================================
def build_a():
    grid = np.zeros((58, 54, 36), dtype=np.uint8)
    X, Y, Z = grid.shape

    # --- 1. HIROSE RIVER CLIFF & TOWERING SLOPED ISHIGAKI STONE WALLS (Z: 0..15) ---
    for z in range(0, 16):
        inset = z // 3
        x0 = 5 + inset
        x1 = 52 - inset
        y0 = 5 + inset
        y1 = 41 - inset
        if z <= 4:
            fill_box(grid, x0 - 2, x1 + 2, y0 - 2, y1 + 2, z, z, 2)
            if z in (1, 2):
                fill_box(grid, x0 - 2, x0 + 2, y1 + 1, y1 + 2, z, z + 1, 9)
                fill_box(grid, x1 - 3, x1 + 2, y1 + 1, y1 + 2, z, z + 1, 9)
                fill_box(grid, x1 + 1, x1 + 2, y0 + 6, y0 + 16, z, z + 1, 9)
                fill_box(grid, x0 - 2, x0 - 1, y0 + 8, y0 + 18, z, z + 1, 9)
        fill_ishigaki(grid, x0, x1, y0, y1, z, z)

    # Honmaru courtyard & white plaster perimeter parapet walls connecting the 4 corner yagura
    fill_box(grid, 10, 47, 10, 36, 15, 15, 1)
    fill_box(grid, 10, 47, 10, 11, 16, 18, 3)
    fill_box(grid, 10, 47, 35, 36, 16, 18, 3)
    fill_box(grid, 10, 11, 10, 36, 16, 18, 3)
    fill_box(grid, 46, 47, 10, 36, 16, 18, 3)
    fill_box(grid, 9, 48, 9, 11, 19, 19, 4)
    fill_box(grid, 9, 48, 35, 37, 19, 19, 4)
    fill_box(grid, 9, 11, 9, 37, 19, 19, 4)
    fill_box(grid, 46, 48, 9, 37, 19, 19, 4)

    # --- 2. FOUR CORNER WATCHTOWERS (四隅の物見櫓) (NO TENSHU KEEP!) (Z: 15..31) ---
    for yx, yy in [(14, 14), (43, 14), (14, 32), (43, 32)]:
        build_yagura(grid, yx, yy, z_base=15, half_w=4)

    # --- 3. LARGE SINGLE-STORY HONMARU GOTEN PALACE (平屋の大きな本丸御殿) (Z: 16..28) ---
    fill_box(grid, 19, 38, 16, 31, 16, 20, 3)
    for px in range(20, 38, 3):
        fill_box(grid, px, px, 31, 31, 16, 20, 6)
        fill_box(grid, px, px, 16, 16, 16, 20, 6)
    fill_box(grid, 21, 36, 30, 30, 17, 19, 8)     # Golden palace wall screens
    fill_box(grid, 19, 38, 16, 31, 16, 16, 6)     # Raised cedar veranda floor
    for i in range(5):
        fill_box(grid, 17 + i, 40 - i, 14 + i, 33 - i, 21 + i, 21 + i, 4 if i % 2 == 0 else 5)
    # Radiant Golden Roof Ridge & Ornate Golden Karahafu Front Gable!
    fill_box(grid, 21, 36, 23, 24, 26, 26, 8)
    fill_box(grid, 21, 22, 23, 24, 27, 28, 8)
    fill_box(grid, 35, 36, 23, 24, 27, 28, 8)
    fill_box(grid, 26, 31, 31, 34, 20, 21, 4)
    fill_box(grid, 27, 30, 32, 34, 22, 23, 8)

    # --- 4. DRAMATIC CLIFFSIDE KAKEZUKURI OVERHANG (崖へ突き出た懸造り) (Y: 36..50, Z: 0..24) ---
    fill_box(grid, 21, 36, 38, 49, 0, 4, 2)
    fill_box(grid, 23, 34, 41, 50, 0, 2, 2)
    fill_box(grid, 22, 25, 47, 49, 2, 3, 9)
    fill_box(grid, 32, 35, 47, 49, 2, 3, 9)
    stilt_xs = (23, 27, 30, 34)
    stilt_ys = (39, 43, 46, 49)
    for sx in stilt_xs:
        for sy in stilt_ys:
            fill_box(grid, sx, sx, sy, sy, 2, 15, 6)
    for bz in (6, 10, 13):
        for sy in stilt_ys:
            fill_box(grid, 23, 34, sy, sy, bz, bz, 7)
        for sx in stilt_xs:
            fill_box(grid, sx, sx, 36, 49, bz, bz, 7)
    # Overhanging Kakezukuri Stage Deck, Golden Balcony & Pavilion Roof!
    fill_box(grid, 22, 35, 36, 50, 15, 16, 6)
    fill_box(grid, 22, 35, 50, 50, 17, 18, 8)
    fill_box(grid, 22, 22, 37, 50, 17, 18, 8)
    fill_box(grid, 35, 35, 37, 50, 17, 18, 8)
    fill_box(grid, 24, 33, 36, 45, 17, 20, 3)
    fill_box(grid, 25, 32, 45, 45, 17, 19, 8)
    for i in range(4):
        fill_box(grid, 22 + i, 35 - i, 35, 48 - i, 21 + i, 21 + i, 4 if i % 2 == 0 else 5)
    fill_box(grid, 26, 31, 37, 44, 25, 25, 8)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: AOBA-JO FORTRESS ROBOT (54 x 28 x 60) — cleanly <= 6,000 voxels!
# ============================================================
def build_b():
    grid = np.zeros((54, 28, 60), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 26
    cx_r = X // 2      # 27

    # --- 1. ISHIGAKI STONE-WALL BOOTS & HEAVY FORTRESS LEGS (石垣が脚!) (Z: 0..23) ---
    fill_sym_box(grid, 3, 7, 9, 18, 0, 1, 2)      # Dark cliff-rock armored sole
    for z in range(2, 5):
        fill_ishigaki(grid, cx_r + 3, cx_r + 7, 10, 18 - (z - 2), z, z)
        fill_ishigaki(grid, cx_l - 7, cx_l - 3, 10, 18 - (z - 2), z, z)
    fill_sym_box(grid, 4, 6, 17, 18, 2, 2, 8)     # Gold fortress toe trim
    fill_sym_box(grid, 4, 6, 8, 9, 0, 2, 2)       # Heel cliff buttress

    # Towering Battered Ishigaki Stone-Wall Greaves (Z: 4..18)
    for z in range(4, 19):
        flare = 1 if z <= 7 else 0
        fill_ishigaki(grid, cx_r + 3, cx_r + 6 + flare, 10, 16 + flare, z, z)
        fill_ishigaki(grid, cx_l - 6 - flare, cx_l - 3, 10, 16 + flare, z, z)
    # Tiled Kawara Knee Ramparts & White Plaster Knee Wall
    fill_sym_box(grid, 3, 7, 16, 18, 15, 18, 4)
    fill_sym_box(grid, 4, 6, 17, 19, 16, 17, 3)
    fill_sym_box(grid, 5, 5, 19, 19, 16, 17, 8)
    fill_sym_box(grid, 7, 7, 12, 15, 4, 6, 9)     # Aoba moss accent

    # Thighs (Z: 18..24)
    fill_sym_box(grid, 3, 6, 11, 16, 18, 24, 2)
    fill_ishigaki(grid, cx_r + 3, cx_r + 6, 13, 17, 19, 23)
    fill_ishigaki(grid, cx_l - 6, cx_l - 3, 13, 17, 19, 23)

    # --- 2. STONE-WALL BASTION WAIST & PARAPET SKIRT (石垣が腰!) (Z: 23..30) ---
    fill_ishigaki(grid, cx_l - 7, cx_r + 7, 10, 17, 24, 29)
    fill_sym_box(grid, 2, 8, 17, 18, 23, 27, 3)   # White plaster front waist wall
    fill_sym_box(grid, 2, 8, 17, 19, 28, 28, 4)   # Dark Kawara eaves belt
    fill_sym_box(grid, 7, 8, 10, 17, 23, 27, 1)   # Stone hip ramparts
    fill_sym_box(grid, 8, 9, 10, 17, 28, 28, 4)   # Side tiled belt eaves
    fill_sym_box(grid, 0, 7, 9, 10, 23, 27, 3)    # Rear plaster waist skirt
    fill_sym_box(grid, 0, 7, 9, 9, 28, 28, 4)
    fill_sym_box(grid, 0, 1, 17, 19, 24, 28, 6)   # Cedar gate waist buckle
    fill_sym_box(grid, 0, 1, 19, 19, 25, 27, 8)   # Gold plaque

    # --- 3. HONMARU BASTION TORSO & GOLDEN PALACE CHEST (Z: 29..43) ---
    fill_sym_box(grid, 0, 5, 11, 16, 29, 31, 2)
    fill_sym_box(grid, 0, 8, 9, 18, 32, 42, 3)    # Broad white-plaster Honmaru chest bastion
    fill_ishigaki(grid, cx_l - 7, cx_r + 7, 10, 18, 32, 34)
    # Central Golden Honmaru Goten Fusuma Chest Shrine
    fill_sym_box(grid, 0, 3, 18, 19, 35, 40, 6)
    fill_sym_box(grid, 0, 2, 19, 19, 36, 39, 8)
    fill_sym_box(grid, 0, 1, 19, 20, 37, 38, 9)   # Glowing Aoba emerald core
    # Sweeping Dark Tile Chest Eaves across collar (Z: 41..43)
    fill_sym_box(grid, 0, 9, 9, 19, 41, 42, 4)
    fill_sym_box(grid, 0, 8, 10, 18, 43, 43, 5)
    fill_sym_box(grid, 2, 6, 19, 19, 42, 42, 8)

    # Rear Cliffside Backpack Fortress (Y: 6..9, Z: 31..42)
    fill_ishigaki(grid, cx_l - 5, cx_r + 5, 7, 9, 32, 41)
    fill_sym_box(grid, 0, 4, 6, 7, 34, 40, 3)
    fill_sym_box(grid, 0, 4, 5, 7, 41, 42, 4)
    fill_sym_box(grid, 0, 2, 6, 6, 36, 38, 8)

    # --- 4. FOUR CORNER WATCHTOWERS AS SHOULDERS & ARMS + KAKEZUKURI SHOULDER OVERHANGS! ---
    fill_sym_box(grid, 8, 10, 12, 16, 37, 40, 7)

    for sign in (-1, 1):
        scx = (cx_r + 12) if sign == 1 else (cx_l - 12)
        scy = 14
        # UPPER WATCHTOWERS -> SHOULDER BASTIONS (Z: 37..51)
        fill_box(grid, scx - 3, scx + 3, scy - 3, scy + 3, 37, 43, 3)
        fill_box(grid, scx - 1, scx + 1, scy + 3, scy + 3, 39, 41, 7)
        fill_box(grid, scx + sign * 3, scx + sign * 3, scy - 1, scy + 1, 39, 41, 7)
        fill_box(grid, scx - 4, scx + 4, scy - 4, scy + 4, 44, 44, 4)
        fill_box(grid, scx - 3, scx + 3, scy - 3, scy + 3, 45, 45, 5)
        fill_box(grid, scx - 2, scx + 2, scy - 2, scy + 2, 46, 47, 3)
        for i in range(3):
            rw = 3 - i
            fill_box(grid, scx - rw, scx + rw, scy - rw, scy + rw, 48 + i, 48 + i, 4 if i % 2 == 0 else 5)
        fill_box(grid, scx - 1, scx + 1, scy, scy, 51, 51, 8)

        # SIGNATURE KAKEZUKURI (懸造り) TIMBER-STILT OVERHANG PROJECTING FROM SHOULDERS!
        kx0 = scx + sign * 3
        kx1 = scx + sign * 11
        xa, xb = min(kx0, kx1), max(kx0, kx1)
        for sy_k in (11, 14, 17):
            draw_6conn_line(grid, (scx + sign * 3, sy_k, 37), (scx + sign * 10, sy_k, 43), 6)
            draw_6conn_line(grid, (scx + sign * 6, sy_k, 40), (scx + sign * 6, sy_k, 43), 7)
            draw_6conn_line(grid, (scx + sign * 9, sy_k, 42), (scx + sign * 9, sy_k, 43), 7)
        fill_box(grid, xa, xb, 10, 18, 44, 44, 6)
        fill_box(grid, xa, xb, 10, 18, 45, 45, 8)
        fill_box(grid, scx + sign * 11, scx + sign * 11, 10, 18, 45, 47, 8)
        fill_box(grid, xa, xb, 18, 18, 46, 46, 8)
        fill_box(grid, xa, xb, 10, 10, 46, 46, 8)

        # UPPER ARMS (Z: 31..37)
        fill_box(grid, scx - 2, scx + 2, scy - 2, scy + 2, 31, 36, 7)
        fill_box(grid, scx - 2, scx + 2, scy - 1, scy + 2, 33, 35, 6)

        # LOWER TWO WATCHTOWERS -> FOREARM TURRET GAUNTLETS (Z: 21..31)
        fill_box(grid, scx - 3, scx + 3, scy - 3, scy + 3, 22, 29, 3)
        fill_box(grid, scx - 1, scx + 1, scy + 3, scy + 3, 24, 27, 7)
        fill_box(grid, scx + sign * 3, scx + sign * 3, scy - 1, scy + 1, 24, 27, 7)
        fill_box(grid, scx - 4, scx + 4, scy - 4, scy + 4, 30, 30, 4)
        fill_box(grid, scx - 4, scx + 4, scy - 4, scy + 4, 21, 22, 4)
        fill_box(grid, scx - 3, scx + 3, scy + 4, scy + 4, 22, 22, 8)
        # Heavy Stone-Block Fortress Fists (Z: 18..21)
        fill_box(grid, scx - 2, scx + 2, scy - 2, scy + 2, 18, 20, 2)
        fill_box(grid, scx - 2, scx + 2, scy + 1, scy + 2, 18, 20, 1)

    # --- 5. HEAD: GOLDEN HONMARU GOTEN PALACE CROWN (本丸御殿が頭・金色っぽい意匠!) (Z: 43..59) ---
    fill_sym_box(grid, 0, 2, 12, 16, 43, 44, 7)
    fill_sym_box(grid, 0, 3, 11, 17, 45, 50, 3)
    fill_sym_box(grid, 0, 2, 16, 18, 45, 46, 8)   # Golden menpo jaw
    fill_sym_box(grid, 0, 2, 16, 18, 47, 49, 7)   # Shadowed face recess
    fill_sym_box(grid, 1, 2, 18, 18, 47, 48, 9)   # Glowing Aoba emerald eyes!
    fill_sym_box(grid, 0, 0, 18, 18, 47, 48, 8)   # Gold nose bridge
    # GRAND GOLDEN HONMARU GOTEN PALACE ROOF CROWN (Z: 50..59)
    fill_sym_box(grid, 0, 6, 10, 19, 50, 51, 8)   # Sweeping golden palace eaves!
    fill_sym_box(grid, 0, 5, 11, 18, 52, 53, 4)   # Kawara tiled roof tier
    fill_sym_box(grid, 0, 4, 12, 17, 54, 55, 8)   # Radiant golden upper palace roof!
    fill_sym_box(grid, 0, 3, 13, 16, 56, 56, 8)
    fill_sym_box(grid, 0, 2, 18, 20, 51, 54, 8)   # Golden Karahafu forehead arch!
    fill_sym_box(grid, 0, 1, 20, 20, 52, 53, 9)   # Emerald gable gem
    fill_sym_box(grid, 0, 3, 13, 15, 57, 57, 8)   # Golden roof ridge
    fill_sym_box(grid, 3, 4, 13, 15, 57, 59, 8)   # Twin golden palace roof finials!

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=36, pitch_a=26, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "aobajo_a.vox")
    v_b = export_vox(model_b, "aobajo_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: AOBA CASTLE (SENDAI CASTLE) -> FORTRESS ROBOT",
        "1. AOBA CASTLE (4 YAGURA + KAKEZUKURI)",
        "2. AOBA-JO FORTRESS ROBOT",
        "preview_aobajo.png",
        yaw_a=36, pitch_a=26, yaw_b=28, pitch_b=18,
    )
    print(f"aobajo: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
