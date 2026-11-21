import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (136, 140, 148, 255),  # Warm Elephant Grey Skin
    2: (92, 98, 108, 255),    # Deeper Slate-Grey Shading & Wrinkles
    3: (218, 164, 168, 255),  # Soft Pale-Pink Inner Ear Tint
    4: (248, 244, 232, 255),  # Pure Ivory-White Curved Tusks
    5: (46, 50, 58, 255),     # Dark Charcoal Toenails & Mechanical Joints
    6: (216, 162, 62, 255),   # Bronze / Gold Ceremonial Forehead & Chest Trim
    7: (62, 220, 248, 255),   # Glowing Cyan Eyes, Visor & Energy Core
    8: (72, 78, 90, 255),     # Gunmetal Inner Frame & Thrusters
    9: (176, 170, 160, 255),  # Warm Sandstone Highlight
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(x0, x1)), min(X - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


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


# ==========================================
# FORM A: AFRICAN ELEPHANT (28 x 38 x 24)
# ==========================================
def build_a():
    grid = np.zeros((28, 38, 24), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 13.5

    # --- FOUR THICK PILLAR LEGS WITH CHARCOAL TOENAILS (Z: 0..11) ---
    for leg_cy in (19.5, 8.5):
        for z in range(0, 12):
            if z <= 1:
                rx_l, ry_l = 2.35, 2.55
            elif z <= 5:
                rx_l, ry_l = 1.95, 2.15
            else:
                rx_l, ry_l = 2.15, 2.35
            x_center_off = 3.5
            for sign in (-1, 1):
                lcx = cx + sign * x_center_off
                for x in range(int(lcx - 3), int(lcx + 4)):
                    for y in range(int(leg_cy - 3), int(leg_cy + 4)):
                        if 0 <= x < X and 0 <= y < Y:
                            if ((x - lcx) / rx_l) ** 2 + ((y - leg_cy) / ry_l) ** 2 <= 1.0:
                                if z in (2, 6):
                                    col = 2
                                elif z >= 8 and abs(x - cx) > 4.5:
                                    col = 9
                                else:
                                    col = 1
                                grid[x, y, z] = col
        # Three distinct dark charcoal toenails along front (+Y) of each pillar foot
        nail_y = int(round(leg_cy + 2.5))
        fill_sym_box(grid, 2, 2, nail_y, nail_y, 0, 1, 5)
        fill_sym_box(grid, 4, 4, nail_y, nail_y, 0, 1, 5)
        fill_sym_box(grid, 5, 5, nail_y - 1, nail_y - 1, 0, 1, 5)

    # --- BULKY SCULPTED ELEPHANT BODY (Y: 5..23, Z: 7..19) ---
    body_slices = [
        (5,  3.2, 10, 15),
        (6,  4.4, 9,  16),
        (7,  5.2, 8,  17),
        (8,  5.6, 8,  17),
        (9,  5.9, 8,  18),
        (10, 6.1, 8,  18),
        (11, 6.2, 8,  18),
        (12, 6.2, 7,  18),
        (13, 6.2, 7,  18),
        (14, 6.2, 7,  18),
        (15, 6.1, 7,  18),
        (16, 6.0, 8,  19),
        (17, 5.9, 8,  19),
        (18, 5.8, 8,  19),  # High African elephant shoulder hump
        (19, 5.6, 8,  19),
        (20, 5.4, 9,  19),
        (21, 5.0, 9,  18),
        (22, 4.4, 10, 18),
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
                        col = 2
                    elif z >= zt - 1 and dx <= rx * 0.55:
                        col = 9
                    elif y in (9, 13, 17, 20) and dx >= rx - 1.1 and zb + 2 <= z <= zt - 2:
                        col = 2
                    else:
                        col = 1
                    grid[x, y, z] = col

    # --- SHORT ELEPHANT TAIL WITH CHARCOAL TUFT (Y: 2..5, Z: 6..13) ---
    fill_sym_box(grid, 0, 0, 4, 5, 12, 13, 1)
    fill_sym_box(grid, 0, 0, 3, 4, 10, 12, 2)
    fill_sym_box(grid, 0, 0, 2, 3, 8, 10, 2)
    fill_sym_box(grid, 0, 0, 2, 3, 6, 7, 5)

    # --- SCULPTED AFRICAN ELEPHANT HEAD (Y: 22..29, Z: 12..22) ---
    head_slices = [
        (22, 4.4, 12, 20),
        (23, 4.8, 12, 21),
        (24, 5.0, 12, 22),
        (25, 4.9, 12, 22),
        (26, 4.6, 12, 22),
        (27, 4.1, 12, 21),
        (28, 3.3, 13, 20),
        (29, 2.4, 13, 18),
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
                    if z >= zt - 1 and dx <= rx * 0.6:
                        col = 9
                    elif z == zb:
                        col = 2
                    else:
                        col = 1
                    grid[x, y, z] = col

    # Ceremonial bronze forehead ornament & bright cyan eyes
    fill_sym_box(grid, 0, 1, 28, 28, 19, 20, 6)
    fill_sym_box(grid, 0, 0, 29, 29, 19, 19, 7)
    fill_sym_box(grid, 4, 4, 26, 27, 17, 17, 5)
    fill_sym_box(grid, 4, 4, 27, 27, 17, 17, 7)
    fill_sym_box(grid, 3, 4, 26, 27, 18, 18, 2)

    # --- BIG WIDE FLAPPING AFRICAN ELEPHANT EARS (x_off: 4..13, Y: 20..25, Z: 11..22) ---
    ear_profile = [
        (22, 4, 9,  23),
        (21, 4, 11, 23),
        (20, 4, 12, 22),
        (19, 4, 13, 22),
        (18, 4, 13, 22),
        (17, 4, 13, 22),
        (16, 4, 12, 22),
        (15, 4, 12, 22),
        (14, 4, 11, 22),
        (13, 5, 10, 22),
        (12, 5, 9,  22),
        (11, 6, 8,  22),
    ]
    for z, x0, x1, yb in ear_profile:
        for x_off in range(x0, x1 + 1):
            y_ear = yb - max(0, (x_off - 6) // 3)
            is_rim = (x_off == x1 or z in (22, 11) or (x_off == x1 - 1 and z in (21, 12)))
            col_back = 2 if is_rim else 1
            fill_sym_box(grid, x_off, x_off, y_ear, y_ear + 1, z, z, col_back)
            # Soft pale-pink inner ear tint framed cleanly inside warm-grey margin
            if not is_rim and x_off >= x0 + 2 and x_off <= x1 - 2 and 13 <= z <= 19:
                fill_sym_box(grid, x_off, x_off, y_ear + 1, y_ear + 1, z, z, 3)

    # --- CURVED PURE IVORY-WHITE TUSKS (6-CONNECTED SOLIDLY INTO CHEEKS!) ---
    # Each step overlaps in X or Y to guarantee 100% 6-connectivity
    tusk_segs = [
        # (x0, x1, y0, y1, z0, z1)
        (2, 2, 26, 28, 13, 14),  # Deep anchor inside head cheeks
        (2, 3, 28, 29, 12, 13),  # Sweeping outward with full X-face overlap
        (3, 3, 29, 31, 11, 12),  # Lower curve
        (3, 4, 31, 32, 11, 12),  # Outward sweep with full X-face overlap
        (4, 4, 32, 34, 12, 13),  # Rising arc
        (4, 4, 34, 35, 13, 14),  # Sharp upward ivory tip
        (4, 4, 35, 35, 15, 15),
    ]
    for x0, x1, y0, y1, z0, z1 in tusk_segs:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, 4)
    # Ceremonial bronze tusk collar rings at cheek emergence
    fill_sym_box(grid, 2, 2, 27, 27, 13, 14, 6)

    # --- LONG ARTICULATED CURVING TRUNK REACHING FORWARD & UP (Y: 28..37, Z: 6..16) ---
    trunk_path = [
        (28, 15.0, 1.8, 1.8),
        (29, 14.3, 1.7, 1.7),
        (30, 13.2, 1.6, 1.6),
        (31, 11.8, 1.5, 1.5),
        (32, 10.2, 1.4, 1.4),
        (32, 8.8,  1.35, 1.35),
        (33, 7.8,  1.3, 1.3),
        (34, 7.4,  1.25, 1.25),
        (35, 7.8,  1.2, 1.2),
        (36, 8.8,  1.15, 1.15),
        (37, 10.0, 1.05, 1.05),
        (37, 11.4, 0.95, 0.95),
    ]
    for idx, (ty, tz, rx_t, rz_t) in enumerate(trunk_path):
        col = 2 if (idx % 2 == 1) else 1
        fill_sphere_local(grid, cx, ty, tz, rx_t, 1.15, rz_t, col)
    # Trunk tip finger & nostril detail
    fill_sym_box(grid, 0, 0, 37, 37, 12, 12, 2)
    fill_sym_box(grid, 0, 0, 36, 36, 12, 12, 3)

    # Hollow unseen interior of legs, body & head
    hollow_interior_26(grid, 2, 21)

    return grid


# ==========================================
# FORM B: HEAVY TITAN ELEPHANT ROBOT (44 x 28 x 42)
# ==========================================
def build_b():
    grid = np.zeros((44, 28, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21 (-X robot left)
    cx_r = X // 2      # 22 (+X robot right)

    # --- MASSIVE STOMPING PILLAR BOOTS WITH CHARCOAL TOENAILS (Z: 0..4) ---
    fill_sym_box(grid, 3, 7, 7, 16, 0, 1, 5)    # Heavy dark charcoal sole
    fill_sym_box(grid, 4, 6, 6, 8, 0, 2, 8)     # Gunmetal heel counterweight
    fill_sym_box(grid, 3, 7, 9, 16, 1, 3, 1)    # Warm elephant-grey pillar boot
    fill_sym_box(grid, 3, 7, 15, 17, 1, 2, 2)   # Slate lower foot bumper
    # Three massive dark charcoal elephant toenail claws on each foot
    fill_sym_box(grid, 3, 3, 17, 18, 0, 1, 5)
    fill_sym_box(grid, 5, 5, 17, 18, 0, 1, 5)
    fill_sym_box(grid, 7, 7, 16, 17, 0, 1, 5)
    # Bronze ankle cuff trim & gunmetal ankle joint
    fill_sym_box(grid, 4, 6, 15, 16, 3, 3, 6)
    fill_sym_box(grid, 4, 6, 9, 14, 3, 4, 8)

    # --- THICK PILLAR ROBOT LOWER LEGS & BRONZE KNEE CRESTS (Z: 4..15) ---
    fill_sym_box(grid, 3, 6, 8, 14, 4, 14, 1)   # Massive elephant-pillar shin armor
    fill_sym_box(grid, 3, 6, 14, 15, 5, 12, 9)  # Warm sandstone front shin bevel
    # Horizontal elephant-wrinkle armor seams on pillar legs
    for wz in (6, 9, 12):
        fill_sym_box(grid, 3, 6, 9, 14, wz, wz, 2)
    fill_sym_box(grid, 3, 3, 10, 13, 5, 13, 8)  # Inner leg gunmetal hydraulics
    # Rear heavy leg thrusters
    fill_sym_box(grid, 4, 5, 7, 8, 6, 9, 8)
    fill_sym_box(grid, 4, 5, 6, 6, 6, 7, 7)
    # Ceremonial Bronze Knee Guards
    fill_sym_box(grid, 3, 6, 14, 16, 12, 15, 2)
    fill_sym_box(grid, 4, 6, 15, 16, 13, 15, 6)
    fill_sym_box(grid, 4, 5, 16, 16, 14, 14, 7)

    # --- HEAVY THIGHS & CEREMONIAL PELVIS (Z: 15..22) ---
    fill_sym_box(grid, 3, 6, 9, 14, 15, 20, 8)
    fill_sym_box(grid, 3, 6, 11, 14, 16, 19, 1)
    fill_sym_box(grid, 4, 5, 14, 15, 16, 19, 9)
    fill_sym_box(grid, 6, 6, 10, 13, 16, 19, 2)
    # Heavy Waist / Pelvis
    fill_sym_box(grid, 0, 6, 9, 14, 19, 22, 8)
    fill_sym_box(grid, 2, 6, 13, 15, 19, 21, 1)
    fill_sym_box(grid, 2, 5, 15, 15, 20, 21, 6)
    fill_sym_box(grid, 6, 7, 10, 13, 19, 22, 2)
    # Center bronze titan belt buckle
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 6)
    fill_sym_box(grid, 0, 0, 16, 16, 20, 21, 7)
    # Rear elephant tail stabilizer with charcoal tuft
    fill_sym_box(grid, 0, 0, 7, 8, 19, 21, 2)
    fill_sym_box(grid, 0, 0, 6, 7, 16, 19, 2)
    fill_sym_box(grid, 0, 0, 5, 6, 14, 16, 5)

    # --- TITAN TORSO WITH TWIN CURVED IVORY TUSK CHEST MOTIF (Z: 22..33) ---
    # Mechanical gunmetal abdomen
    fill_sym_box(grid, 0, 5, 9, 14, 22, 24, 8)
    fill_sym_box(grid, 0, 4, 14, 15, 22, 24, 5)
    fill_sym_box(grid, 1, 2, 15, 15, 23, 24, 6)
    # Massive Broad Elephant Titan Chest Core
    fill_sym_box(grid, 0, 7, 8, 15, 25, 32, 1)
    fill_sym_box(grid, 0, 6, 14, 17, 25, 31, 1)
    fill_sym_box(grid, 0, 5, 16, 17, 26, 30, 9)
    # Ceremonial Bronze/Gold Chest Plate & Glowing Cyan Reactor Core
    fill_sym_box(grid, 0, 3, 16, 18, 26, 31, 6)
    fill_sym_box(grid, 0, 2, 17, 18, 27, 30, 2)
    fill_sym_box(grid, 0, 1, 18, 18, 28, 29, 7)
    fill_sym_box(grid, 0, 2, 17, 18, 31, 32, 6)
    fill_sym_box(grid, 3, 6, 11, 14, 32, 33, 2)

    # ICONIC TWIN CURVED PURE IVORY TUSKS FRAMING THE CHEST PLATE! (牙が胸の意匠)
    # Sweeping boldly forward & up from lower bronze chest sockets past the collar!
    fill_sym_box(grid, 5, 6, 15, 17, 25, 27, 6)  # Bronze tusk sockets
    chest_tusk_segs = [
        # (x0, x1, y0, y1, z0, z1)
        (5, 5, 17, 19, 25, 26),
        (4, 5, 18, 20, 26, 27),
        (4, 4, 19, 21, 27, 29),
        (4, 4, 19, 20, 29, 31),
        (4, 5, 18, 19, 31, 32),
        (5, 6, 17, 18, 32, 33),
        (6, 6, 16, 17, 33, 35),
    ]
    for x0, x1, y0, y1, z0, z1 in chest_tusk_segs:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, 4)

    # --- ELEPHANT BACKPACK / ARMORED HUMP (Y: 4..8, Z: 23..33) ---
    fill_sym_box(grid, 0, 6, 5, 8, 24, 32, 1)
    fill_sym_box(grid, 0, 5, 4, 5, 25, 31, 2)
    fill_sym_box(grid, 0, 3, 4, 4, 27, 31, 9)
    fill_sym_box(grid, 0, 2, 4, 4, 31, 32, 6)
    # Twin heavy gunmetal jet thrusters at bottom of backpack
    fill_sym_box(grid, 2, 4, 3, 5, 23, 26, 8)
    fill_sym_box(grid, 2, 4, 3, 3, 23, 24, 7)

    # --- COLOSSAL ELEPHANT-EAR SHIELD PAULDRONS (x_off: 7..17, Y: 9..15, Z: 26..39) ---
    # Sleek, wide, organically curved 2-voxel-thick African elephant ear shields with pale-pink inner ear!
    fill_sym_box(grid, 6, 10, 10, 13, 29, 32, 8)  # Heavy shoulder axle mount
    fill_sym_box(grid, 7, 10, 10, 13, 28, 32, 5)  # Inner shoulder joint core

    ear_shield_rows = [
        # (z, x_off0, x_off1)
        (39, 9,  13),
        (38, 8,  15),
        (37, 8,  16),
        (36, 8,  17),
        (35, 8,  17),
        (34, 8,  17),
        (33, 8,  17),
        (32, 9,  16),
        (31, 9,  16),
        (30, 10, 15),
        (29, 10, 15),
        (28, 11, 14),
        (27, 11, 13),
    ]
    for z, x0, x1 in ear_shield_rows:
        for x_off in range(x0, x1 + 1):
            # Sleek curved shield arc: wraps gently forward at outer tip
            y_back = 10 + max(0, (x_off - 12) // 2)
            y_front = y_back + 2
            is_outer_rim = (x_off == x1 or z in (39, 27) or (x_off == x1 - 1 and z in (38, 28)))
            is_inner_edge = (x_off == x0 and z >= 34)
            # Back layer (warm grey + slate rim + sandstone crest)
            if is_outer_rim:
                col_b = 6 if (z in (38, 35, 31) and x_off == x1) else 2
            elif is_inner_edge:
                col_b = 6
            elif z in (35, 32) and x0 + 1 <= x_off <= x1 - 1:
                col_b = 2
            elif z == 37 and x0 + 2 <= x_off <= x1 - 2:
                col_b = 9
            else:
                col_b = 1
            fill_sym_box(grid, x_off, x_off, y_back, y_back + 1, z, z, col_b)
            # Front layer (shows unmistakable soft pale-pink inner elephant ear inside grey/bronze shield border!)
            if is_outer_rim:
                col_f = 6 if (z in (38, 35, 31) and x_off == x1) else 2
            elif is_inner_edge:
                col_f = 6
            elif (x0 + 2 <= x_off <= x1 - 2) and (30 <= z <= 36):
                col_f = 3  # Soft pale-pink inner ear shield recess!
            else:
                col_f = 1
            fill_sym_box(grid, x_off, x_off, y_front, y_front, z, z, col_f)

    # Top curved bronze ear-cap & solid shoulder connector into shield
    fill_sym_box(grid, 9, 12, 10, 13, 30, 33, 8)
    fill_sym_box(grid, 10, 12, 10, 12, 39, 39, 6)

    # --- MASSIVE ARMS (Z: 15..29) ---
    # Upper arms descending from shoulder hubs
    fill_sym_box(grid, 9, 11, 10, 13, 23, 29, 8)
    fill_sym_box(grid, 9, 11, 10, 13, 25, 27, 2)

    # LEFT ARM (-X, viewer's right): Thick armored forearm & heavy Titan Battering Gauntlet
    fill_box(grid, cx_l - 12, cx_l - 9, 9, 14, 17, 22, 1)
    fill_box(grid, cx_l - 12, cx_l - 9, 14, 14, 18, 21, 9)
    fill_box(grid, cx_l - 12, cx_l - 12, 10, 13, 18, 21, 6)
    fill_box(grid, cx_l - 11, cx_l - 9, 10, 13, 15, 16, 5)
    fill_box(grid, cx_l - 13, cx_l - 12, 11, 15, 16, 21, 2)
    fill_box(grid, cx_l - 13, cx_l - 13, 12, 14, 17, 20, 6)
    fill_box(grid, cx_l - 12, cx_l - 9, 14, 15, 15, 17, 5)
    fill_box(grid, cx_l - 11, cx_l - 10, 15, 15, 16, 16, 4)

    # --- RIGHT ARM (+X, viewer's left): FORMIDABLE ARTICULATED TRUNK CANNON / WHIP-BLASTER! (長い鼻が右腕の武器) ---
    # Sweeps boldly OUTWARD (+X) & FORWARD (+Y) in a dramatic curving elephant-trunk S-arc so it
    # stands out cleanly against the background silhouette as an unmistakable Trunk Cannon!
    fill_box(grid, cx_r + 9, cx_r + 12, 10, 14, 17, 23, 1)   # Right forearm armor
    fill_box(grid, cx_r + 10, cx_r + 14, 11, 15, 17, 21, 8)  # Heavy cannon breech housing
    fill_box(grid, cx_r + 12, cx_r + 14, 12, 15, 17, 21, 6)  # Ceremonial bronze breech collar
    fill_box(grid, cx_r + 13, cx_r + 14, 15, 15, 18, 20, 7)  # Glowing side charge bar

    # Long curving articulated Elephant Trunk Cannon extending boldly outward (+X), dipping, then curling UP (+Z, +Y)!
    trunk_cannon_segs = [
        # (x_center, y_center, z_center, rx, ry, rz, col)
        (cx_r + 14.5, 14.5, 19.0, 1.75, 1.75, 1.75, 1),
        (cx_r + 15.8, 15.6, 18.2, 1.65, 1.65, 1.65, 2),  # Elephant trunk wrinkle ring!
        (cx_r + 17.0, 16.8, 17.5, 1.60, 1.60, 1.60, 1),
        (cx_r + 18.0, 18.0, 17.2, 1.55, 1.55, 1.55, 2),  # Trunk wrinkle ring!
        (cx_r + 18.8, 19.2, 17.6, 1.50, 1.50, 1.50, 8),  # Gunmetal stabilizer ring
        (cx_r + 19.4, 20.4, 18.6, 1.45, 1.45, 1.45, 1),
        (cx_r + 19.7, 21.5, 19.8, 1.45, 1.45, 1.45, 2),  # Trunk wrinkle ring curling UP!
        (cx_r + 19.8, 22.5, 21.2, 1.50, 1.50, 1.50, 1),
        (cx_r + 19.8, 23.4, 22.5, 1.65, 1.65, 1.65, 6),  # Flared bronze trunk-nozzle collar!
        (cx_r + 19.8, 24.3, 23.6, 1.80, 1.70, 1.80, 2),  # Flared elephant-trunk blaster lip!
    ]
    for txc, tyc, tzc, trx, try_, trz, tcol in trunk_cannon_segs:
        fill_sphere_local(grid, txc, tyc, tzc, trx, try_, trz, tcol)
    # Glowing cyan plasma beam core inside flared trunk tip + upper trunk-finger sight & ivory fang!
    fill_box(grid, cx_r + 19, cx_r + 20, 24, 26, 23, 24, 7)  # Glowing cyan plasma nozzle core!
    fill_box(grid, cx_r + 19, cx_r + 20, 24, 25, 25, 26, 1)  # Upper trunk-finger sight prong
    fill_box(grid, cx_r + 19, cx_r + 20, 24, 25, 22, 22, 4)  # Ivory lower fang prong

    # --- HEROIC WAR-ELEPHANT TITAN HEAD (Z: 33..41) ---
    fill_sym_box(grid, 0, 2, 10, 13, 32, 33, 8)
    fill_sym_box(grid, 0, 3, 9, 14, 34, 39, 1)
    fill_sym_box(grid, 0, 2, 9, 14, 39, 40, 1)
    fill_sym_box(grid, 0, 1, 10, 13, 40, 40, 9)
    # Side cheek guards & ivory jaw-tusks
    fill_sym_box(grid, 3, 3, 10, 14, 34, 38, 2)
    fill_sym_box(grid, 2, 3, 14, 15, 34, 35, 4)
    # Gunmetal faceplate & bronze chin gem
    fill_sym_box(grid, 0, 1, 14, 15, 34, 35, 8)
    fill_sym_box(grid, 0, 0, 15, 15, 34, 34, 6)
    # Glowing bright cyan wrap-around heroic visor
    fill_sym_box(grid, 0, 2, 14, 15, 36, 37, 7)
    # Ceremonial Bronze/Gold War-Elephant Forehead Crown & V-Crest
    fill_sym_box(grid, 0, 2, 14, 15, 38, 39, 6)
    fill_sym_box(grid, 0, 0, 15, 16, 38, 39, 7)
    fill_sym_box(grid, 0, 0, 12, 15, 40, 41, 6)
    fill_sym_box(grid, 1, 2, 14, 15, 39, 40, 6)
    fill_sym_box(grid, 3, 3, 13, 14, 40, 41, 6)

    # Hollow strictly interior bulk across the entire robot to stay cleanly in 2,300-3,700
    hollow_interior_26(grid, 1, 39)

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


def render_voxel_iso(grid, yaw_deg=35, pitch_deg=25, scale=None, img_size=(386, 266), margin=14):
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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=40, pitch_a=22, yaw_b=34, pitch_b=20):
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
    v_a = export_vox(model_a, "elephant_a.vox")
    v_b = export_vox(model_b, "elephant_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: AFRICAN ELEPHANT -> HEAVY TITAN ELEPHANT ROBOT",
        "1. AFRICAN ELEPHANT",
        "2. HEAVY TITAN ELEPHANT ROBOT",
        "preview_elephant.png",
        yaw_a=40, pitch_a=22, yaw_b=34, pitch_b=20,
    )
    print(f"elephant: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
