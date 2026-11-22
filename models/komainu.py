import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Komainu (Agyo / Open-Mouthed Roaring Shrine Guardian) -> Guardian Lion-Dog Robot!
# Curled mane & fierce fangs -> Robot's Head & Massive Lion-Mane Shoulders!
PALETTE = {
    1: (224, 218, 200, 255),  # Warm Carved Shrine Granite / Cream-Stone Body
    2: (168, 162, 146, 255),  # Shaded Stone Bevels & Muscle Contours
    3: (88, 86, 82, 255),     # Deep Carved Stone Recesses & Inner Joints
    4: (62, 148, 126, 255),   # Sacred Jade-Teal Curled Karajishi Mane & Tail
    5: (36, 98, 84, 255),     # Deep Moss-Emerald Mane Shading
    6: (212, 46, 38, 255),    # Shrine Vermilion-Red Bib, Roaring Mouth & Sash
    7: (252, 250, 244, 255),  # Pure Ivory-White Fierce Fangs & Claws (牙)
    8: (244, 198, 48, 255),   # Sacred Gold Shrine Bell (Suzu) & Armor Trim
    9: (255, 204, 44, 255),   # Blazing Guardian Amber-Gold Eyes
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
# FORM A: KOMAINU AGYO (ROARING SHRINE LION-DOG) (28 x 44 x 36)
# ============================================================
def build_a():
    grid = np.zeros((28, 44, 36), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 13.5

    # --- 1. CLASSIC SEATED/CROUCHING GUARDIAN KOMAINU TORSO (Y: 11..32, Z: 4..24) ---
    # Classic shrine guardian posture: planted seated haunches rising up into a proud, broad muscular chest!
    body_slices = [
        # (y, rx, zb, zt)
        (11, 4.0, 2,  11),   # Seated muscular hindquarters
        (12, 5.2, 2,  13),
        (13, 5.8, 2,  14),
        (14, 6.0, 2,  15),
        (15, 5.8, 3,  16),
        (16, 5.4, 4,  17),
        (17, 5.0, 5,  17),   # Tucked guardian waist
        (18, 4.9, 6,  18),
        (19, 5.0, 7,  19),
        (20, 5.3, 8,  20),   # Rising proud lion chest!
        (21, 5.7, 9,  21),
        (22, 6.1, 10, 22),
        (23, 6.4, 11, 22),
        (24, 6.5, 11, 23),   # Broad muscular shoulders
        (25, 6.4, 12, 23),
        (26, 6.2, 13, 24),
        (27, 5.8, 14, 24),
        (28, 5.3, 15, 24),
        (29, 4.8, 16, 25),
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
                        col = 2  # Shaded carved stone underside
                    elif z >= zt - 1 and dx <= 1.5 and y <= 24:
                        col = 4  # Jade-teal curled dorsal mane ridge!
                    else:
                        col = 1  # Warm shrine granite stone
                    grid[x, y, z] = col

    # --- 2. STURDY PLANTED FORE-PILLAR LEGS & SEATED HIND LEGS (Z: 0..16) ---
    # Seated haunches & grounded hind paws (Y: 10..20, Z: 0..9)
    for sign in (-1, 1):
        hx = cx + sign * 5.2
        fill_sphere_local(grid, hx, 14.5, 6.5, 2.6, 3.6, 4.5, 1)
        fill_sphere_local(grid, hx + sign * 0.6, 14.0, 7.5, 1.4, 2.2, 2.2, 2)
        # Forward planted hind paws grounded at z=0
        px0, px1 = int(round(hx - 1.5)), int(round(hx + 1.5))
        fill_box(grid, px0, px1, 13, 20, 0, 2, 1)
        fill_box(grid, px0, px1, 19, 21, 0, 1, 7)  # Ivory hind claws!
        # Curled jade-teal leg-tuft scrolls on hind thighs
        fill_box(grid, int(round(hx + sign * 2.0)), int(round(hx + sign * 2.5)), 11, 14, 7, 10, 4)

    # Strong Upright Pillar Forelegs bracing heroically forward! (Y: 25..34, Z: 0..17)
    for sign in (-1, 1):
        fx = cx + sign * 4.6
        draw_6conn_line(grid, (fx, 26, 16), (fx, 30, 2), 1, pad=(1, 2, 0))
        # Curled jade-teal elbow flame-tufts!
        fill_box(grid, int(round(fx + sign * 1.8)), int(round(fx + sign * 2.3)), 24, 27, 9, 13, 4)
        fill_box(grid, int(round(fx + sign * 1.8)), int(round(fx + sign * 2.3)), 25, 26, 10, 12, 5)
        # Heavy grounded lion front paws + sharp ivory claws!
        px0, px1 = int(round(fx - 2.0)), int(round(fx + 2.0))
        fill_box(grid, px0, px1, 28, 33, 0, 2, 1)
        fill_box(grid, px0, px0, 33, 34, 0, 1, 7)
        fill_box(grid, int(round(fx)), int(round(fx)), 33, 34, 0, 1, 7)
        fill_box(grid, px1, px1, 33, 34, 0, 1, 7)

    # --- 3. SHRINE VERMILION BIB (前掛け) & GOLDEN SUZU BELL ON CHEST! ---
    fill_sym_box(grid, 0, 4, 28, 30, 14, 20, 6)  # Vermilion shrine bib
    fill_sym_box(grid, 0, 3, 29, 31, 13, 18, 6)
    fill_sym_box(grid, 0, 1, 31, 32, 15, 17, 8)  # Radiant golden shrine suzu bell!
    fill_sym_box(grid, 0, 0, 32, 32, 16, 16, 3)

    # --- 4. VOLUMINOUS CURLED JADE-TEAL KARAJISHI MANE (たてがみ!) (Y: 22..33, Z: 18..34) ---
    # Lush swirling spherical mane curls framing head, neck & upper shoulders!
    mane_curls = [
        # (x_off, y, z, r)
        (0.0, 25.0, 27.5, 3.2),
        (3.5, 25.5, 26.5, 3.0),
        (5.8, 26.5, 24.0, 2.8),
        (6.8, 27.5, 21.0, 2.6),
        (5.5, 28.5, 18.5, 2.5),
        (2.8, 29.0, 19.0, 2.4),
        (4.5, 23.0, 23.5, 2.7),
        (2.5, 22.0, 25.0, 2.7),
        (0.0, 21.5, 25.0, 2.8),
        (5.2, 28.5, 27.5, 2.6),
        (2.8, 28.0, 30.0, 2.6),
        (0.0, 27.5, 31.0, 2.6),
    ]
    for xo, my, mz, mr in mane_curls:
        c_m = 4 if (int(my + mz) % 2 == 0) else 5
        fill_sphere_local(grid, cx + xo, my, mz, mr, mr, mr, c_m)
        if xo > 0:
            fill_sphere_local(grid, cx - xo, my, mz, mr, mr, mr, c_m)
        # Sculpted highlight curls (bright jade tips)
        if mr >= 2.6:
            fill_sphere_local(grid, cx + xo + (0.6 if xo > 0 else 0), my + 0.6, mz + 0.6, mr * 0.5, mr * 0.5, mr * 0.5, 4)
            if xo > 0:
                fill_sphere_local(grid, cx - xo - 0.6, my + 0.6, mz + 0.6, mr * 0.5, mr * 0.5, mr * 0.5, 4)

    # --- 5. FIERCE AGYO (阿形) ROARING HEAD WITH OPEN MOUTH & PROMINENT IVORY FANGS (牙!) (Y: 29..42, Z: 19..33) ---
    fill_sym_box(grid, 0, 4, 29, 36, 22, 31, 1)  # Broad sculpted lion-dog skull
    fill_sym_box(grid, 0, 3, 30, 35, 31, 32, 4)  # Curled mane brow crown
    # Flared Rounded Lion Ears
    fill_sym_box(grid, 4, 5, 29, 32, 29, 32, 1)
    fill_sym_box(grid, 4, 5, 32, 32, 30, 31, 2)
    # Fierce Sculpted Brow & Blazing Amber Guardian Eyes!
    fill_sym_box(grid, 2, 4, 35, 37, 27, 29, 3)  # Deep carved eye sockets
    fill_sym_box(grid, 2, 3, 37, 37, 27, 28, 9)  # Blazing guardian amber-gold eyes!
    fill_sym_box(grid, 1, 4, 36, 38, 29, 30, 4)  # Swirling jade-teal fierce eyebrows!
    # Broad Lion-Dog Snout & Wide Open AGYO Roaring Mouth (Y: 36..42)!
    fill_sym_box(grid, 0, 3, 36, 40, 25, 27, 1)  # Broad upper muzzle
    fill_sym_box(grid, 0, 1, 40, 42, 26, 28, 2)  # Sculpted broad lion nose!
    fill_sym_box(grid, 0, 0, 42, 42, 26, 26, 3)
    # Wide Open Vermilion Roaring Mouth Cavity (Z: 21..24)
    fill_sym_box(grid, 0, 2, 35, 39, 21, 24, 6)  # Bright vermilion Agyo open mouth!
    # Strong Lower Stone Jaw (Z: 19..20)
    fill_sym_box(grid, 0, 3, 34, 40, 19, 20, 1)
    fill_sym_box(grid, 0, 2, 37, 41, 19, 19, 2)
    # PROMINENT PURE-IVORY UPPER & LOWER FANGS (牙!) clearly flashing in the roaring mouth!
    fill_sym_box(grid, 2, 2, 39, 40, 23, 25, 7)  # Large upper canine fangs pointing down!
    fill_sym_box(grid, 2, 2, 39, 40, 20, 22, 7)  # Large lower canine fangs pointing up!
    fill_sym_box(grid, 0, 1, 40, 40, 24, 24, 7)  # Front upper incisors
    fill_sym_box(grid, 0, 1, 40, 40, 20, 20, 7)  # Front lower incisors

    # --- 6. GRAND CURLED FLAME-LIKE JADE-TEAL KOMAINU TAIL (Y: 2..12, Z: 9..26) ---
    tail_nodes = [
        (cx, 11.5, 11.0, 2.2, 4),
        (cx,  9.5, 12.5, 2.5, 5),
        (cx,  7.5, 14.5, 2.8, 4),
        (cx,  6.0, 17.0, 3.0, 4),
        (cx,  5.5, 20.0, 2.8, 5),
        (cx,  6.2, 22.8, 2.4, 4),
        (cx,  7.8, 24.5, 2.0, 4),
        (cx,  9.2, 23.8, 1.6, 5),  # Classic inward-curled karajishi tail scroll!
    ]
    prev_t = None
    for txc, tyc, tzc, tr, tcol in tail_nodes:
        if prev_t is not None:
            draw_6conn_line(grid, prev_t, (txc, tyc, tzc), tcol)
        prev_t = (txc, tyc, tzc)
        fill_sphere_local(grid, txc, tyc, tzc, tr, tr, tr, tcol)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: KOMAINU GUARDIAN ROBOT (48 x 26 x 46)
# Curled mane & fierce fangs -> Robot's Head & Massive Lion-Mane Shoulders!
# ============================================================
def build_b():
    grid = np.zeros((48, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # --- 1. HEAVY STONE-GUARDIAN LION-PAW BOOTS & PILLAR LEGS (Z: 0..20) ---
    fill_sym_box(grid, 3, 6, 9, 17, 0, 1, 3)     # Heavy stone sole
    fill_sym_box(grid, 3, 6, 10, 17, 1, 3, 1)    # Carved granite footplate
    fill_sym_box(grid, 3, 3, 17, 19, 0, 1, 7)    # Three ivory guardian lion-claws!
    fill_sym_box(grid, 5, 5, 17, 19, 0, 1, 7)
    fill_sym_box(grid, 6, 6, 16, 18, 0, 1, 7)
    fill_sym_box(grid, 4, 5, 8, 9, 0, 2, 3)      # Heel block

    # Massive Carved Granite Greaves with Jade Mane-Tuft Calf Guards (Z: 4..15)
    fill_sym_box(grid, 3, 6, 10, 15, 4, 14, 1)   # Granite pillar shins
    fill_sym_box(grid, 4, 5, 15, 16, 5, 13, 2)   # Shaded stone shin ridge
    fill_sym_box(grid, 6, 7, 11, 14, 6, 12, 4)   # Curled jade-teal calf tufts!
    fill_sym_box(grid, 3, 6, 11, 15, 5, 5, 6)    # Shrine vermilion ankle band
    # Lion-Crested Stone Knee Guards
    fill_sym_box(grid, 3, 6, 15, 17, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 17, 18, 13, 15, 8)  # Gold shrine knee boss

    # Thighs & Shrine-Apron Waist Skirt (Z: 15..23)
    fill_sym_box(grid, 3, 5, 10, 15, 15, 19, 3)
    fill_sym_box(grid, 3, 5, 13, 16, 15, 18, 1)
    fill_sym_box(grid, 0, 5, 10, 15, 19, 22, 3)
    # Vermilion & Granite Guardian Waist Skirt
    fill_sym_box(grid, 2, 6, 15, 16, 17, 21, 1)
    fill_sym_box(grid, 2, 6, 16, 16, 17, 17, 8)  # Gold hem
    fill_sym_box(grid, 6, 7, 10, 15, 17, 21, 4)  # Jade-teal curled hip tassets!
    fill_sym_box(grid, 0, 5, 9, 10, 17, 21, 1)
    fill_sym_box(grid, 0, 2, 15, 17, 18, 22, 6)  # Shrine vermilion center apron!
    fill_sym_box(grid, 0, 1, 17, 17, 20, 21, 8)  # Gold suzu waist bell!

    # --- 2. BROAD GUARDIAN CHEST WITH VERMILION BIB & GOLDEN SUZU BELL (Z: 22..33) ---
    fill_sym_box(grid, 0, 4, 10, 15, 22, 24, 3)
    fill_sym_box(grid, 0, 7, 9, 16, 25, 32, 1)   # Broad carved granite chest
    fill_sym_box(grid, 3, 6, 16, 17, 26, 31, 2)  # Stone pectoral armor
    # Shrine Vermilion Chest Bib & Giant Golden Suzu Bell Core!
    fill_sym_box(grid, 0, 3, 16, 18, 26, 31, 6)
    fill_sym_box(grid, 0, 1, 18, 19, 27, 30, 8)  # Prominent gold suzu bell on chest!
    fill_sym_box(grid, 0, 0, 19, 19, 28, 29, 3)  # Bell slit
    fill_sym_box(grid, 1, 5, 11, 15, 32, 33, 4)  # Jade-teal curled mane collar!

    # Rear Curled Jade-Teal Flame-Tail Backpack Crest! (clearly visible in REAR VIEW)
    fill_sym_box(grid, 0, 4, 6, 9, 24, 32, 2)
    cx_f = (X - 1) / 2.0
    for ty, tz, tr, c_t in [(6, 25, 2.2, 4), (4, 28, 2.4, 5), (3, 31, 2.5, 4), (4, 34, 2.2, 4), (6, 35, 1.8, 5)]:
        fill_sphere_local(grid, cx_f, ty, tz, tr, tr, tr, c_t)

    # --- 3. MASSIVE CURLED-MANE & PROJECTING-FANG LION SHOULDERS (たてがみと牙が肩!) (Z: 27..38) ---
    fill_sym_box(grid, 7, 9, 11, 15, 28, 32, 3)  # Shoulder joints
    for sign in (-1, 1):
        scx = (cx_r + 11) if sign == 1 else (cx_l - 11)
        # Sculpted swirling Jade-Teal Lion-Mane Shoulder Pauldrons!
        fill_sphere_local(grid, scx, 13.0, 31.5, 3.8, 3.8, 3.8, 4)
        fill_sphere_local(grid, scx + sign * 2.2, 13.0, 33.5, 2.6, 2.8, 2.8, 5)
        fill_sphere_local(grid, scx + sign * 1.0, 13.0, 35.0, 2.5, 2.6, 2.5, 4)
        fill_sphere_local(grid, scx + sign * 2.8, 13.0, 29.5, 2.3, 2.6, 2.4, 4)
        # Carved Stone Inner Face & PROMINENT IVORY FANGS PROJECTING FROM EACH SHOULDER!
        fill_box(grid, scx - 2, scx + 2, 15, 17, 29, 32, 1)
        fill_box(grid, scx - 1, scx + 1, 17, 17, 30, 31, 6)  # Vermilion shoulder roar-maw!
        # Giant Sweeping Ivory Shoulder Fangs (牙が肩の意匠!) curving boldly upward & outward!
        draw_6conn_line(grid, (scx + sign * 2, 15, 33), (scx + sign * 5, 16, 37), 7)
        draw_6conn_line(grid, (scx + sign * 2, 16, 32), (scx + sign * 5, 17, 36), 7)
        # Lower pair of sharp shoulder fangs pointing down-forward
        draw_6conn_line(grid, (scx + sign * 1, 17, 30), (scx + sign * 2, 18, 27), 7)

        # Heavy Guardian Stone Arms & Clawed Fists (Z: 14..28)
        fill_box(grid, scx - 2, scx + 1, 11, 15, 22, 28, 3)  # Upper arms
        fill_box(grid, scx - 2, scx + 2, 11, 16, 16, 22, 1)  # Massive granite forearm gauntlets
        fill_box(grid, scx + sign * 2, scx + sign * 2, 12, 15, 17, 21, 4)  # Jade mane trim
        fill_box(grid, scx - 2, scx + 2, 12, 16, 16, 16, 8)  # Gold wrist band
        fill_box(grid, scx - 1, scx + 1, 12, 15, 14, 15, 3)  # Heavy fists
        fill_box(grid, scx + sign * 1, scx + sign * 1, 15, 17, 14, 15, 7)  # Ivory knuckle-fangs!

    # --- 4. AGYO LION-MANE & ROARING FANG-VISOR ROBOT HEAD (たてがみと牙が頭!) (Z: 33..45) ---
    fill_sym_box(grid, 0, 1, 12, 15, 33, 34, 3)  # Neck
    fill_sym_box(grid, 0, 3, 11, 16, 34, 40, 1)  # Sculpted stone helmet skull
    # Voluminous Curled Jade-Teal Lion Mane Crown & Side Locks framing the head!
    fill_sphere_local(grid, cx_f, 13.0, 41.0, 4.2, 3.2, 2.5, 4)
    fill_sphere_local(grid, cx_f + 4.0, 13.0, 38.5, 2.2, 2.8, 2.8, 5)
    fill_sphere_local(grid, cx_f - 4.0, 13.0, 38.5, 2.2, 2.8, 2.8, 5)
    fill_sphere_local(grid, cx_f, 10.5, 37.5, 3.6, 2.2, 3.2, 4)  # Rear mane locks!
    # Fierce Roaring AGYO Fanged Menpo Faceplate!
    fill_sym_box(grid, 0, 2, 16, 18, 34, 36, 6)  # Vermilion Agyo roaring mouth-guard!
    fill_sym_box(grid, 2, 2, 17, 18, 34, 36, 7)  # Sharp IVORY FANGS flashing on robot's jaw!
    fill_sym_box(grid, 0, 2, 16, 17, 37, 38, 3)  # Dark eye recess
    fill_sym_box(grid, 1, 2, 17, 17, 37, 38, 9)  # Blazing guardian amber-gold eyes!
    fill_sym_box(grid, 0, 0, 17, 17, 37, 38, 1)  # Stone nose bridge
    # Gold Shrine Forehead Crest & Swept Ivory Brow Fangs (Z: 39..45)
    fill_sym_box(grid, 0, 2, 16, 18, 39, 40, 8)
    draw_6conn_line(grid, (cx_r + 2, 17, 40), (cx_r + 4, 17, 44), 7)  # Twin ivory crown fangs!
    draw_6conn_line(grid, (cx_l - 2, 17, 40), (cx_l - 4, 17, 44), 7)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=20, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "komainu_a.vox")
    v_b = export_vox(model_b, "komainu_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: KOMAINU (AGYO GUARDIAN) -> LION-DOG ROBOT",
        "1. KOMAINU (AGYO ROARING FORM)",
        "2. KOMAINU GUARDIAN ROBOT",
        "preview_komainu.png",
        yaw_a=38, pitch_a=20, yaw_b=28, pitch_b=18,
    )
    print(f"komainu: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
