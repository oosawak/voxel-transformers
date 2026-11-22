import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Yatagarasu (Sacred Three-Legged Solar Crow) -> Winged Divine Robot!
# Three distinct golden-clawed legs -> Robot's bird-clawed legs (+ 3rd talon spur),
# Grand black wings -> Back Wing-Binders & Winged Forearms!
PALETTE = {
    1: (34, 38, 48, 255),     # Glossy Obsidian-Black Sacred Crow Plumage
    2: (70, 78, 96, 255),     # Deep Slate-Charcoal Feather Bevels & Highlights
    3: (54, 44, 92, 255),     # Iridescent Raven Purple-Indigo Wing Sheen
    4: (244, 198, 46, 255),   # Radiant Solar Gold Three Legs, Sun Crest & Trim
    5: (184, 134, 24, 255),   # Burnished Antique Gold Shading
    6: (214, 42, 38, 255),    # Sacred Solar Vermilion-Crimson Markings & Halo
    7: (244, 246, 250, 255),  # Crisp Sacred White Shide / Pinion Tip Accents
    8: (52, 56, 66, 255),     # Dark Metallic Beak & Joints
    9: (255, 170, 32, 255),   # Blazing Solar Amber Glowing Eyes & Chest Sun
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
# FORM A: YATAGARASU (GRAND THREE-LEGGED SACRED CROW) (58 x 48 x 38)
# ============================================================
def build_a():
    grid = np.zeros((58, 48, 38), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 28.5
    cx_l = X // 2 - 1   # 28
    cx_r = X // 2       # 29

    # --- 1. GRAND OBSIDIAN SACRED CROW BODY (Y: 14..35, Z: 10..22) ---
    body_slices = [
        (14, 2.4, 12, 16),
        (15, 3.2, 11, 17),
        (16, 3.9, 11, 18),
        (17, 4.5, 10, 18),
        (18, 4.9, 10, 19),
        (19, 5.2, 10, 19),
        (20, 5.4, 10, 20),
        (21, 5.5, 10, 20),
        (22, 5.6, 10, 21),
        (23, 5.6, 10, 21),
        (24, 5.5, 10, 21),
        (25, 5.4, 11, 22),
        (26, 5.2, 11, 22),
        (27, 4.9, 12, 22),
        (28, 4.5, 13, 22),
        (29, 4.1, 14, 23),
        (30, 3.7, 15, 24),
        (31, 3.4, 17, 25),
        (32, 3.2, 18, 26),
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
                    if z >= zt - 1 and dx <= rx * 0.55:
                        col = 2  # Slate-charcoal glossy crown sheen
                    elif (y + z) % 4 == 0 and dx >= rx * 0.65:
                        col = 3  # Iridescent dark purple-indigo plumage sheen
                    else:
                        col = 1  # Glossy obsidian-black plumage
                    grid[x, y, z] = col

    # Sacred Solar Crimson & Radiant Gold Sun-Disc Chest Emblem! (Y: 28..33)
    fill_sym_box(grid, 0, 2, 29, 32, 14, 18, 6)  # Vermilion solar disc
    fill_sym_box(grid, 0, 1, 31, 32, 15, 17, 4)  # Gold sun ring
    fill_sym_box(grid, 0, 0, 32, 32, 16, 16, 9)  # Blazing solar core

    # --- 2. ICONIC THREE GOLDEN-CLAWED LEGS (三本足!) (Z: 0..13) ---
    # Explicitly spaced so ALL THREE LEGS (Left, Center-Front, Right) are unmistakably distinct in BOTH front & rear views!
    def build_golden_leg(leg_x, y_hip, y_foot):
        # Obsidian feathered thigh
        fill_sphere_local(grid, leg_x, y_hip, 10.5, 1.8, 2.0, 2.4, 1)
        fill_box(grid, leg_x - 1, leg_x + 1, y_hip - 1, y_hip + 1, 8, 9, 6)  # Sacred vermilion leg band
        # Gleaming radiant gold tarsus!
        draw_6conn_line(grid, (leg_x, y_hip, 8), (leg_x, y_foot, 1), 4, pad=(0, 1, 0))
        fill_box(grid, leg_x, leg_x, y_foot - 1, y_foot + 1, 1, 2, 5)  # Antique gold ankle
        # Three sharp forward golden-and-obsidian talons + rear hallux grounded firmly at z=0!
        fill_box(grid, leg_x - 1, leg_x + 1, y_foot - 1, y_foot + 1, 0, 1, 4)
        draw_6conn_line(grid, (leg_x - 1, y_foot + 1, 0), (leg_x - 2, y_foot + 4, 0), 4)
        draw_6conn_line(grid, (leg_x,     y_foot + 1, 0), (leg_x,     y_foot + 5, 0), 4)
        draw_6conn_line(grid, (leg_x + 1, y_foot + 1, 0), (leg_x + 2, y_foot + 4, 0), 4)
        draw_6conn_line(grid, (leg_x,     y_foot - 1, 0), (leg_x,     y_foot - 4, 0), 4)
        # Sharp white/dark claw tips
        for cx_t, cy_t in ((leg_x - 2, y_foot + 4), (leg_x, y_foot + 5), (leg_x + 2, y_foot + 4)):
            if 0 <= cx_t < X and 0 <= cy_t < Y:
                grid[cx_t, cy_t, 0] = 7

    # Outer Left Leg (-X), Outer Right Leg (+X), and Prominent THIRD CENTER-FORWARD LEG!
    build_golden_leg(cx_r + 5, y_hip=20, y_foot=22)   # Right leg (+X)
    build_golden_leg(cx_l - 5, y_hip=20, y_foot=22)   # Left leg (-X)
    build_golden_leg(cx_r,     y_hip=25, y_foot=29)   # Iconic 3RD CENTER LEG stepping boldly forward!

    # --- 3. FANNED SACRED TAIL FEATHERS WITH GOLD & CRIMSON TRIM (Y: 1..15, Z: 10..17) ---
    for i in range(14):
        ty = 14 - i
        tz = 14 - i // 4
        hw = 2 + i // 3
        for xo in range(0, hw + 1):
            if i >= 12:
                col_t = 4 if xo % 2 == 0 else 6  # Gold & vermilion tail-tip trim!
            elif xo == hw:
                col_t = 2
            elif (xo + i) % 3 == 0:
                col_t = 3
            else:
                col_t = 1
            fill_sym_box(grid, xo, xo, ty, ty, tz, tz + 1, col_t)

    # --- 4. MAJESTIC CROW HEAD, SOLAR GOLD FOREHEAD CREST & CURVED BEAK (Y: 31..46, Z: 20..31) ---
    fill_sphere_local(grid, cx, 34.0, 25.0, 3.4, 3.8, 3.6, 1)
    fill_sym_box(grid, 0, 2, 32, 36, 27, 28, 2)   # Glossy slate crown
    # Sacred Golden Solar-Crest Crown & Flowing Head Plumes! (Z: 28..32)
    fill_sym_box(grid, 0, 1, 35, 37, 28, 30, 4)   # Forehead solar-gold disc
    fill_sym_box(grid, 0, 0, 37, 37, 29, 29, 6)   # Crimson center sun dot
    draw_6conn_line(grid, (cx_r + 1, 34, 28), (cx_r + 3, 29, 31), 4)
    draw_6conn_line(grid, (cx_l - 1, 34, 28), (cx_l - 3, 29, 31), 4)
    # Blazing Solar-Amber Eyes!
    fill_sym_box(grid, 2, 3, 35, 37, 25, 26, 6)   # Vermilion eye ring
    fill_sym_box(grid, 3, 3, 36, 37, 25, 26, 9)   # Glowing amber eyes!
    # Strong Curved Sacred Crow Beak with Gold Ridge (Y: 37..46)
    fill_sym_box(grid, 0, 1, 37, 40, 23, 26, 8)
    fill_sym_box(grid, 0, 1, 40, 43, 23, 25, 8)
    fill_sym_box(grid, 0, 0, 43, 46, 22, 24, 8)
    fill_sym_box(grid, 0, 0, 38, 43, 26, 26, 4)   # Gold upper beak crest!

    # --- 5. GRAND SPREAD OBSIDIAN WINGS WITH SACRED GOLD & VERMILION PINIONS! (Z: 16..37) ---
    for sign in (-1, 1):
        bx_o = cx_r if sign == 1 else cx_l
        def wx(off):
            return bx_o + sign * off

        fill_box(grid, wx(3), wx(6), 22, 28, 17, 21, 1)
        fill_box(grid, wx(4), wx(6), 24, 28, 19, 21, 4)  # Gold wing-shoulder crest!

        # High soaring wing leading edge
        lead = [
            (wx(5),  26, 20),
            (wx(11), 27, 25),
            (wx(17), 26, 30),
            (wx(23), 24, 34),
            (wx(27), 22, 36),
        ]
        for i in range(len(lead) - 1):
            draw_6conn_line(grid, lead[i], lead[i + 1], 4 if i < 2 else 2)
            p0, p1 = lead[i], lead[i + 1]
            draw_6conn_line(grid, (p0[0], p0[1] - 1, p0[2] - 1), (p1[0], p1[1] - 1, p1[2] - 1), 6 if i == 1 else 1)

        # Sweeping Obsidian Primary & Secondary Wing Feathers!
        for xo in range(6, 28):
            u = (xo - 6) / 21.0
            if xo <= 17:
                t1 = (xo - 5) / 12.0
                ly = 26 + 1 * np.sin(t1 * np.pi)
                lz = 20 + 10 * t1
            else:
                t2 = (xo - 17) / 10.0
                ly = 26 - 4 * t2
                lz = 30 + 6 * t2
            ty = ly - (14 - 4 * u)
            tz = lz - (6 + 2 * np.sin(u * np.pi))
            if xo >= 21 and xo % 2 == 0:
                ty -= 2  # Distinct fanned crow flight feathers!

            c_rib = 3 if (xo % 4 == 0) else (2 if xo % 4 == 2 else 1)
            draw_6conn_line(grid, (wx(xo), ly, lz), (wx(xo), ty, tz), c_rib)
            draw_6conn_line(grid, (wx(xo), ly, lz - 1), (wx(xo), ty, tz - 1), 1, only_empty=True)
            # Sacred gold & crimson feather tips along trailing wing edge!
            tx_i, ty_i, tz_i = int(round(wx(xo))), int(round(ty)), int(round(tz))
            if 0 <= tx_i < X and 0 <= ty_i < Y and 0 <= tz_i < Z:
                if xo >= 21 and xo % 2 == 0:
                    grid[tx_i, ty_i, tz_i] = 4  # Gold wingtip pinions
                elif xo % 3 == 0:
                    grid[tx_i, ty_i, tz_i] = 6  # Vermilion trailing trim

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: YATAGARASU DIVINE WINGED ROBOT (52 x 28 x 48)
# Wings -> Back Wing-Binders & Winged Arms, Legs -> Bird-Clawed Robot Legs (+ 3rd Talon Spur)!
# ============================================================
def build_b():
    grid = np.zeros((52, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 25
    cx_r = X // 2      # 26

    # --- 1. GOLDEN BIRD-CLAWED ROBOT LEGS (脚がロボの脚!) (Z: 0..20) ---
    # Grounded 3-talon radiant gold crow-feet! (Z: 0..3)
    fill_sym_box(grid, 3, 5, 11, 16, 0, 2, 4)    # Gold talon foot base
    fill_sym_box(grid, 3, 3, 16, 19, 0, 1, 4)    # Inner golden toe
    fill_sym_box(grid, 4, 4, 16, 20, 0, 1, 4)    # Center golden toe
    fill_sym_box(grid, 5, 5, 16, 19, 0, 1, 4)    # Outer golden toe
    fill_sym_box(grid, 3, 5, 19, 20, 0, 0, 7)    # Sharp white claws
    fill_sym_box(grid, 4, 4, 8, 11, 0, 1, 4)     # Rear golden hallux heel-talon!
    fill_sym_box(grid, 3, 5, 12, 15, 3, 4, 5)    # Antique gold ankle

    # Sleek Obsidian & Gold Bird-Leg Greaves (Z: 4..15)
    fill_sym_box(grid, 3, 5, 11, 15, 4, 14, 1)   # Obsidian greaves
    fill_sym_box(grid, 4, 4, 15, 16, 5, 13, 4)   # Radiant gold shin crest!
    fill_sym_box(grid, 5, 6, 11, 14, 6, 12, 2)   # Outer feathered calf fins
    fill_sym_box(grid, 3, 5, 11, 15, 6, 6, 6)    # Sacred vermilion shin cord
    # Sharp Golden Knee Talons
    fill_sym_box(grid, 3, 5, 15, 17, 13, 16, 1)
    fill_sym_box(grid, 4, 4, 17, 18, 14, 16, 4)

    # Thighs, Waist & FOLDED 3RD GOLDEN TALON TAIL-STABILIZER! (Z: 15..23)
    fill_sym_box(grid, 3, 5, 11, 15, 15, 19, 8)
    fill_sym_box(grid, 3, 5, 13, 16, 15, 18, 1)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 8)  # Pelvis
    fill_sym_box(grid, 2, 6, 15, 16, 17, 21, 1)  # Obsidian feather-skirt tassets
    fill_sym_box(grid, 2, 6, 16, 16, 17, 17, 4)  # Gold hem
    fill_sym_box(grid, 5, 7, 11, 15, 17, 21, 3)  # Purple-indigo hip plates
    fill_sym_box(grid, 0, 1, 15, 17, 18, 22, 6)  # Vermilion front loin cloth
    fill_sym_box(grid, 0, 1, 17, 17, 20, 21, 4)  # Gold solar belt buckle
    # THIRD GOLDEN LEG folded cleanly as a distinctive rear/central golden-talon stabilizer spur! (visible in REAR VIEW!)
    draw_6conn_line(grid, (cx_r, 11, 19), (cx_r, 6, 13), 4, pad=(1, 0, 0))
    fill_sym_box(grid, 0, 1, 4, 6, 11, 13, 4)    # Third golden claw-talon fan!
    fill_sym_box(grid, 0, 0, 3, 4, 11, 11, 7)

    # --- 2. SACRED SOLAR-CREST OBSIDIAN TORSO (Z: 22..34) ---
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 8)
    fill_sym_box(grid, 0, 6, 10, 16, 25, 32, 1)  # Obsidian feathered chest
    fill_sym_box(grid, 2, 5, 16, 17, 26, 31, 2)  # Slate-charcoal breastplate bevels
    # Sacred Solar Crimson & Radiant Gold Sun-Disc Chest Core!
    fill_sym_box(grid, 0, 2, 16, 18, 26, 31, 6)  # Vermilion solar disc
    fill_sym_box(grid, 0, 1, 18, 18, 27, 30, 4)  # Radiant gold sun ring
    fill_sym_box(grid, 0, 0, 18, 19, 28, 29, 9)  # Blazing solar core!
    fill_sym_box(grid, 1, 4, 11, 15, 32, 33, 4)  # Gold sacred collar
    fill_sym_box(grid, 2, 4, 15, 16, 32, 32, 7)  # White shide collar tabs

    # --- 3. GRAND UNFOLDED OBSIDIAN BACK WINGS (翼が背中!) (Y: 4..10, Z: 18..45) ---
    fill_sym_box(grid, 0, 4, 8, 10, 24, 32, 1)   # Wing pack mount
    fill_sym_box(grid, 0, 2, 7, 8, 27, 30, 6)    # Rear solar disc
    fill_sym_box(grid, 0, 1, 7, 7, 28, 29, 4)
    for sign in (-1, 1):
        bx_o = cx_r if sign == 1 else cx_l
        def wx(off):
            return bx_o + sign * off
        # High arched golden-edged wing spars!
        spar = [
            (wx(4),  8, 29),
            (wx(10), 7, 34),
            (wx(17), 6, 40),
            (wx(23), 5, 44),
        ]
        for i in range(len(spar) - 1):
            draw_6conn_line(grid, spar[i], spar[i + 1], 4 if i < 2 else 2)
            p0, p1 = spar[i], spar[i + 1]
            draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), 1)
        # Four dramatic fanned obsidian wing pinion-blades with gold & crimson tips!
        feathers = [
            (21, 5, 43, 24, 5, 33),
            (17, 6, 39, 22, 5, 26),
            (13, 6, 35, 18, 6, 21),
            (9,  7, 32, 13, 6, 18),
        ]
        for fi, (sx, sy, sz, ex, ey, ez) in enumerate(feathers):
            draw_6conn_line(grid, (wx(sx), sy, sz), (wx(ex), ey, ez), 1)
            draw_6conn_line(grid, (wx(sx), sy, sz - 1), (wx(ex), ey, ez - 1), 3 if fi % 2 == 0 else 2)
            draw_6conn_line(grid, (wx(ex - 1), ey, ez), (wx(ex), ey, ez), 4 if fi < 2 else 6)
        # Inner wing covert fill
        for xo in range(5, 16):
            zt = int(round(29 + (xo - 4) * 0.9))
            zb = int(round(24 + (xo - 5) * 0.2))
            draw_6conn_line(grid, (wx(xo), 7, zb), (wx(xo), 7, min(zt, 38)), 1, only_empty=True)

    # --- 4. FEATHERED WING-ARM GAUNTLETS & SHOULDERS (翼が腕!) (Z: 14..35) ---
    fill_sym_box(grid, 6, 8, 12, 15, 29, 32, 8)
    # Feathered Obsidian & Gold Shoulder Wing-Mantles!
    fill_sym_box(grid, 7, 11, 11, 16, 28, 34, 1)
    fill_sym_box(grid, 8, 12, 11, 16, 33, 35, 4) # Gold winged shoulder ridge!
    fill_sym_box(grid, 11, 12, 12, 15, 30, 32, 6)# Vermilion feather accent
    fill_sym_box(grid, 8, 9, 12, 15, 23, 28, 8)  # Upper arms
    # BOTH FOREARMS: Sweeping Wing-Pinion Arm Blades! (翼が腕!)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        def ax(off):
            return bx + sign * off
        fill_box(grid, ax(8), ax(10), 12, 16, 16, 22, 1)  # Forearm gauntlet
        fill_box(grid, ax(8), ax(10), 13, 16, 16, 16, 4)  # Gold wrist cuff
        fill_box(grid, ax(8), ax(9), 13, 15, 14, 15, 8)   # Talon fist
        # Sweeping Wing-Feather Pinion Blades attached along outer forearms!
        draw_6conn_line(grid, (ax(11), 15, 21), (ax(13), 10, 15), 1)
        draw_6conn_line(grid, (ax(11), 15, 20), (ax(13), 11, 14), 2)
        draw_6conn_line(grid, (ax(11), 16, 18), (ax(12), 20, 16), 4)  # Forward gold wing-claw blade!
        fill_box(grid, ax(13), ax(13), 10, 11, 14, 15, 6)  # Vermilion pinion tip!

    # --- 5. RAVEN-BEAK HELM & SOLAR HALO CREST HEAD (Z: 33..47) ---
    fill_sym_box(grid, 0, 1, 12, 15, 33, 34, 8)
    fill_sym_box(grid, 0, 2, 11, 16, 34, 40, 1)  # Obsidian raven helmet
    fill_sym_box(grid, 0, 3, 10, 14, 34, 37, 2)  # Feathered shikoro guard
    # Pointed Crow-Beak Visor Faceplate!
    fill_sym_box(grid, 0, 2, 16, 17, 34, 36, 8)
    fill_sym_box(grid, 0, 0, 17, 19, 34, 36, 4)  # Prominent gold raven-beak face ridge!
    fill_sym_box(grid, 0, 2, 16, 17, 37, 38, 1)
    fill_sym_box(grid, 1, 2, 17, 17, 37, 38, 9)  # Blazing solar amber eyes!
    # Radiant Solar-Disc Forehead Crest & Twin Golden Crow Plumes (Z: 39..47)
    fill_sym_box(grid, 0, 1, 17, 18, 39, 41, 6)  # Vermilion sun disc
    fill_sym_box(grid, 0, 0, 18, 18, 40, 40, 4)  # Gold center
    draw_6conn_line(grid, (cx_r + 1, 17, 40), (cx_r + 5, 14, 46), 4)
    draw_6conn_line(grid, (cx_l - 1, 17, 40), (cx_l - 5, 14, 46), 4)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=36, pitch_a=22, yaw_b=26, pitch_b=18):
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
    v_a = export_vox(model_a, "yatagarasu_a.vox")
    v_b = export_vox(model_b, "yatagarasu_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: YATAGARASU (THREE-LEGGED CROW) -> WINGED ROBOT",
        "1. YATAGARASU (THREE-LEGGED CROW)",
        "2. YATAGARASU WINGED ROBOT",
        "preview_yatagarasu.png",
        yaw_a=36, pitch_a=22, yaw_b=26, pitch_b=18,
    )
    print(f"yatagarasu: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
