import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (216, 34, 34, 255),    # Vivid Traditional Lacquer Crimson-Red
    2: (148, 18, 26, 255),    # Deeper Lacquer Red Shading / Robe Fold
    3: (244, 198, 50, 255),   # Rich Ceremonial Gold Trim / Calligraphy Accents
    4: (246, 232, 204, 255),  # Warm Cream Face Panel
    5: (26, 26, 32, 255),     # Sumi Ink-Black (Brows, Mustache, Beard, Pupils)
    6: (78, 86, 102, 255),    # Dark Slate Mecha Joints / Frame
    7: (238, 242, 248, 255),  # Crisp White Sclera / Highlight
    8: (255, 168, 30, 255),   # Glowing Fiery-Gold / Amber Robot Eyes & Core
    9: (66, 52, 46, 255),     # Deep Bronze-Iron Weighted Base
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
    """Hollow only strictly interior voxels (all 26 neighbors occupied) so 6-connectivity is preserved."""
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


def paint_front_surface(grid, x, z, col, protrude=0):
    """Paint the frontmost (+Y) occupied voxel at (x, z), optionally protruding +Y."""
    X, Y, Z = grid.shape
    if not (0 <= x < X and 0 <= z < Z):
        return
    ys = np.nonzero(grid[x, :, z])[0]
    if len(ys) == 0:
        return
    y_front = int(ys.max())
    if protrude > 0:
        for dy in range(1, protrude + 1):
            if y_front + dy < Y:
                grid[x, y_front + dy, z] = col
    else:
        grid[x, y_front, z] = col


def paint_sym_front(grid, x_off, z, col, protrude=0):
    """Symmetrically paint the frontmost (+Y) voxel at offset x_off and height z."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    paint_front_surface(grid, cx_l - x_off, z, col, protrude=protrude)
    paint_front_surface(grid, cx_r + x_off, z, col, protrude=protrude)


def paint_daruma_face(grid, z_center):
    """Paint the iconic Daruma face (cream panel, gold trim, fierce brows, round eyes, beard) on +Y."""
    # Oval warm cream face opening with thin ceremonial gold framing
    for dz in range(-5, 6):
        z = z_center + dz
        for x_off in range(0, 7):
            dx = x_off + 0.5
            ell = (dx / 5.7) ** 2 + (dz / 4.6) ** 2
            if ell <= 1.0:
                paint_sym_front(grid, x_off, z, 4)
            elif ell <= 1.24 and dz >= -4:
                paint_sym_front(grid, x_off, z, 3)

    # Fierce thick ink-black crane-wing eyebrows (cleanly separated above eyes!)
    paint_sym_front(grid, 0, z_center + 2, 5)
    paint_sym_front(grid, 1, z_center + 2, 5)
    paint_sym_front(grid, 1, z_center + 3, 5)
    paint_sym_front(grid, 2, z_center + 3, 5)
    paint_sym_front(grid, 3, z_center + 3, 5)
    paint_sym_front(grid, 3, z_center + 4, 5)
    paint_sym_front(grid, 4, z_center + 3, 5)
    paint_sym_front(grid, 4, z_center + 2, 5)

    # Intense round Daruma eyes (crisp white sclera + centered bold 2x2 black pupils)
    for x_off in (1, 2, 3):
        for dz in (-1, 0, 1):
            paint_sym_front(grid, x_off, z_center + dz, 7)
    paint_sym_front(grid, 2, z_center, 5)
    paint_sym_front(grid, 2, z_center - 1, 5)
    paint_sym_front(grid, 3, z_center, 5)
    paint_sym_front(grid, 3, z_center - 1, 5)

    # Subtle cream nose bridge & golden cheek accents
    paint_sym_front(grid, 0, z_center, 4, protrude=1)
    paint_sym_front(grid, 4, z_center - 1, 3)

    # Bold ink-black sweeping mustache & jaw-beard framing stern lacquer-red mouth
    paint_sym_front(grid, 0, z_center - 2, 5)
    paint_sym_front(grid, 1, z_center - 2, 5)
    paint_sym_front(grid, 2, z_center - 2, 5)
    paint_sym_front(grid, 3, z_center - 2, 5)
    paint_sym_front(grid, 4, z_center - 2, 5)
    paint_sym_front(grid, 4, z_center - 3, 5)
    paint_sym_front(grid, 3, z_center - 3, 5)
    paint_sym_front(grid, 2, z_center - 4, 5)
    paint_sym_front(grid, 3, z_center - 4, 5)
    paint_sym_front(grid, 0, z_center - 3, 1)  # Stern red mouth
    paint_sym_front(grid, 1, z_center - 3, 2)
    paint_sym_front(grid, 0, z_center - 4, 5)  # Chin beard
    paint_sym_front(grid, 1, z_center - 4, 5)


# ==========================================
# FORM A: JAPANESE DARUMA DOLL (24 x 24 x 26)
# ==========================================
def build_a():
    grid = np.zeros((24, 24, 26), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 11.5
    cy = (Y - 1) / 2.0  # 11.5

    # --- PLUMP OVOID DARUMA BODY & WEIGHTED IRON BASE (Z: 0..24) ---
    daruma_profile = [
        (0,  6.2, 6.0),
        (1,  7.4, 7.1),
        (2,  8.3, 8.0),
        (3,  8.9, 8.5),
        (4,  9.3, 8.9),
        (5,  9.6, 9.2),
        (6,  9.8, 9.4),
        (7,  9.9, 9.5),
        (8,  9.9, 9.5),
        (9,  9.8, 9.4),
        (10, 9.7, 9.3),
        (11, 9.5, 9.1),
        (12, 9.3, 8.9),
        (13, 9.1, 8.7),
        (14, 8.9, 8.5),
        (15, 8.7, 8.3),
        (16, 8.4, 8.1),
        (17, 8.1, 7.8),
        (18, 7.7, 7.4),
        (19, 7.2, 7.0),
        (20, 6.6, 6.4),
        (21, 5.9, 5.7),
        (22, 5.0, 4.9),
        (23, 3.8, 3.7),
        (24, 2.3, 2.2),
    ]

    for z, rx, ry in daruma_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for y in range(Y):
                dy = y - cy
                dist2 = (dx / rx) ** 2 + (dy / ry) ** 2
                if dist2 <= 1.0:
                    # Heavy dark bronze-iron weighted base (Z: 0..3)
                    if z == 0:
                        col = 5  # Ink-black weighted base rim
                    elif z <= 2:
                        col = 9  # Deep bronze-iron weight
                    elif z == 3:
                        # Subtle gold collar ring accent separating dark weight & red body
                        col = 3 if dist2 >= 0.82 else 9
                    else:
                        if dy < -ry * 0.45 and dx < rx * 0.65 and 5 <= z <= 20:
                            col = 2  # Rear lacquer contour shadow
                        elif 4 <= z <= 5 and dist2 >= 0.82 and dy < 2.0:
                            col = 2
                        else:
                            col = 1
                    grid[x, y, z] = col

    # --- DECORATIVE LACQUER ROBE & GOLD BELLY CALLIGRAPHY (Z: 4..11) ---
    # Side golden robe-collar sweeping stripes
    for z, x_off in [(5, 7), (6, 7), (7, 7), (8, 7), (9, 6), (10, 6)]:
        paint_sym_front(grid, x_off, z, 3)
        paint_sym_front(grid, x_off - 1, z, 2)

    # Sleek vertical ceremonial belly banner with stylized gold "福" calligraphy
    for z in range(5, 11):
        for x_off in range(0, 3):
            paint_sym_front(grid, x_off, z, 2)
    for z in range(5, 11):
        paint_sym_front(grid, 2, z, 3)  # Sleek side gold rails
    paint_sym_front(grid, 0, 10, 3)
    paint_sym_front(grid, 1, 10, 3)
    paint_sym_front(grid, 0, 5, 3)
    paint_sym_front(grid, 1, 5, 3)
    # Stylized golden calligraphy strokes down center
    paint_sym_front(grid, 0, 9, 3)
    paint_sym_front(grid, 0, 8, 3)
    paint_sym_front(grid, 1, 8, 3)
    paint_sym_front(grid, 0, 7, 3)
    paint_sym_front(grid, 0, 6, 3)

    # Rear golden sash emblem on -Y
    for z in range(6, 13):
        for x_off in (0, 1):
            for x in (X // 2 - 1 - x_off, X // 2 + x_off):
                ys = np.nonzero(grid[x, :, z])[0]
                if len(ys) > 0:
                    y_back = int(ys.min())
                    if z in (6, 12) or x_off == 0:
                        grid[x, y_back, z] = 3

    # --- ICONIC DARUMA FACE OPENING (Z: 12..21, Front +Y) ---
    paint_daruma_face(grid, z_center=16)

    # Hollow unseen interior to keep voxel count crisp & compact
    hollow_interior_26(grid, 1, 23)

    return grid


# ==========================================
# FORM B: SUMO SHOGUN DARUMA ROBOT (34 x 24 x 40)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 40), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 16.5
    cy = 11.5

    # --- MASSIVE IRON-WEIGHTED STOMPING FEET (Z: 0..4) - FROM DARUMA'S HEAVY BASE! ---
    fill_sym_box(grid, 3, 7, 7, 16, 0, 1, 5)     # Wide sumo-stance ink-black weighted sole
    fill_sym_box(grid, 3, 7, 8, 16, 1, 2, 9)     # Massive bronze-iron weight slab
    fill_sym_box(grid, 4, 6, 16, 17, 0, 1, 9)    # Heavy rounded front iron toe-cap
    fill_sym_box(grid, 4, 6, 15, 16, 2, 2, 2)    # Deep lacquer armored toe guard
    fill_sym_box(grid, 7, 7, 8, 15, 1, 2, 5)     # Outer iron weight clamp
    fill_sym_box(grid, 3, 7, 8, 14, 3, 3, 3)     # Ceremonial gold ankle ring (from Form A base ring!)
    fill_sym_box(grid, 4, 6, 9, 13, 3, 4, 6)     # Dark slate ankle joint

    # --- HEAVY WEIGHTED IRON LOWER LEGS & SUMO GREAVES (Z: 4..14) ---
    fill_sym_box(grid, 3, 6, 8, 14, 4, 12, 9)    # Massive bronze-iron weighted leg pillar
    fill_sym_box(grid, 6, 7, 9, 13, 5, 11, 5)    # Ink-black outer weight plates
    fill_sym_box(grid, 4, 5, 13, 14, 5, 11, 2)   # Deep lacquer crimson shin ridge
    fill_sym_box(grid, 4, 5, 7, 8, 5, 10, 5)     # Rear weighted heel stabilizer
    fill_sym_box(grid, 4, 5, 7, 7, 6, 8, 6)      # Rear calf thruster port
    # Sumo knee guards (crimson + bronze + amber gem, crisp & restrained gold)
    fill_sym_box(grid, 3, 6, 13, 15, 11, 14, 9)
    fill_sym_box(grid, 4, 5, 14, 15, 11, 14, 1)
    fill_sym_box(grid, 3, 6, 15, 15, 14, 14, 3)  # Gold top knee brow
    fill_sym_box(grid, 4, 5, 15, 15, 12, 13, 8)  # Glowing amber knee gem

    # --- STURDY THIGHS & CEREMONIAL WAIST / MAWASHI (Z: 13..19) ---
    fill_sym_box(grid, 3, 5, 9, 13, 14, 18, 6)   # Dark slate thigh frame
    fill_sym_box(grid, 3, 5, 12, 13, 15, 17, 9)  # Bronze-iron thigh armor
    fill_sym_box(grid, 5, 5, 10, 12, 15, 17, 5)  # Ink-black outer thigh
    # Pelvis & Sumo/Shogun ceremonial waist belt
    fill_sym_box(grid, 0, 5, 8, 14, 17, 19, 2)
    fill_sym_box(grid, 0, 5, 14, 15, 18, 18, 3)  # Crisp gold waist sash
    fill_sym_box(grid, 0, 2, 14, 15, 15, 18, 1)  # Front crimson belly-banner flap
    fill_sym_box(grid, 0, 2, 15, 15, 15, 15, 3)  # Gold lower tassel trim
    fill_sym_box(grid, 0, 1, 15, 16, 17, 18, 3)  # Gold belt buckle
    fill_sym_box(grid, 0, 0, 16, 16, 17, 18, 8)  # Fiery-amber waist gem
    # Side hip tassets (lacquer red + bronze + gold border)
    fill_sym_box(grid, 6, 6, 9, 13, 15, 18, 1)
    fill_sym_box(grid, 6, 6, 9, 13, 15, 15, 3)
    # Rear golden waist knot
    fill_sym_box(grid, 0, 3, 7, 8, 17, 19, 3)
    fill_sym_box(grid, 0, 1, 6, 7, 16, 18, 4)

    # --- PLUMP BARREL-CHESTED DARUMA TORSO (Z: 19..31) - ROUND BODY IS THE TORSO! ---
    torso_profile = [
        (19, 6.2, 5.2),
        (20, 6.8, 5.7),
        (21, 7.2, 6.1),
        (22, 7.5, 6.4),
        (23, 7.7, 6.6),
        (24, 7.8, 6.7),
        (25, 7.8, 6.7),
        (26, 7.7, 6.6),
        (27, 7.5, 6.4),
        (28, 7.2, 6.1),
        (29, 6.8, 5.7),
        (30, 6.2, 5.2),
        (31, 5.3, 4.4),
    ]
    for z, rx, ry in torso_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for y in range(Y):
                dy = y - cy
                dist2 = (dx / rx) ** 2 + (dy / ry) ** 2
                if dist2 <= 1.0:
                    if dy < -ry * 0.45 and dx < rx * 0.6:
                        col = 2
                    elif z == 31 and dist2 >= 0.72:
                        col = 3  # Gold collar ring
                    else:
                        col = 1
                    grid[x, y, z] = col

    # --- ICONIC DARUMA FACE EMBLAZONED ON CHEST PLATE! (Z: 20..29, Front +Y) ---
    paint_daruma_face(grid, z_center=25)

    # --- REAR DARUMA BACK-DOME & SUMO THRUSTER PACK (Y: 4..6, Z: 21..30) ---
    fill_sym_box(grid, 0, 3, 4, 6, 22, 29, 2)
    fill_sym_box(grid, 0, 2, 4, 4, 23, 28, 3)    # Golden luck emblem on back
    fill_sym_box(grid, 0, 1, 4, 4, 24, 27, 1)
    fill_sym_box(grid, 0, 0, 4, 4, 25, 26, 3)
    fill_sym_box(grid, 3, 4, 4, 6, 23, 28, 9)    # Twin bronze-iron thruster pods
    fill_sym_box(grid, 3, 4, 3, 4, 23, 24, 8)    # Fiery amber thruster glow

    # --- CURVED LACQUER-RED & GOLD SHOULDER PAULDRONS & POWER ARMS (Z: 13..33) ---
    fill_sym_box(grid, 7, 8, 10, 13, 27, 29, 6)
    fill_sym_box(grid, 8, 12, 9, 14, 26, 31, 1)
    fill_sym_box(grid, 9, 11, 10, 13, 31, 32, 1)
    fill_sym_box(grid, 9, 11, 10, 13, 32, 32, 3)  # Gold dome cap trim
    fill_sym_box(grid, 8, 12, 9, 14, 26, 26, 3)   # Gold lower pauldron rim
    fill_sym_box(grid, 12, 12, 10, 13, 27, 30, 2)
    fill_sym_box(grid, 9, 11, 14, 14, 28, 30, 3)  # Front gold shoulder crest
    fill_sym_box(grid, 10, 10, 14, 14, 29, 29, 8)

    # Upper arms
    fill_sym_box(grid, 9, 10, 10, 13, 22, 25, 6)
    fill_sym_box(grid, 10, 10, 10, 13, 23, 24, 9)

    # Heavy Crimson & Bronze-Iron Forearm Gauntlets (Z: 15..21)
    fill_sym_box(grid, 8, 11, 9, 14, 16, 21, 1)
    fill_sym_box(grid, 11, 11, 10, 13, 17, 20, 9)
    fill_sym_box(grid, 8, 11, 9, 14, 16, 16, 3)   # Gold wrist cuff
    fill_sym_box(grid, 9, 10, 14, 14, 18, 20, 3)

    # Massive Weighted Iron Fists (Z: 13..15)
    fill_sym_box(grid, 9, 10, 10, 13, 13, 15, 9)
    fill_sym_box(grid, 9, 10, 13, 13, 14, 15, 5)

    # Right-hand Gold-Studded Iron Kanabo (War-Club) at +X (viewer's left)
    # Held slightly outward & forward (x=28..31, y=15..18) for clean silhouette separation!
    fill_box(grid, 26, 29, 13, 16, 13, 15, 5)     # Fist grip extending into club shaft
    fill_box(grid, 28, 29, 15, 16, 10, 14, 6)     # Lower pommel shaft
    fill_box(grid, 28, 29, 15, 16, 9, 9, 3)       # Gold pommel cap
    fill_box(grid, 28, 29, 15, 17, 16, 17, 3)     # Gold club collar
    fill_box(grid, 27, 30, 15, 18, 18, 27, 9)     # Heavy bronze-iron Kanabo body
    fill_box(grid, 28, 29, 16, 17, 28, 29, 9)     # Rounded club tip
    fill_box(grid, 28, 29, 16, 17, 29, 29, 3)     # Gold tip finial
    for sz in (19, 22, 25):
        fill_box(grid, 27, 27, 16, 17, sz, sz, 3)
        fill_box(grid, 30, 30, 16, 17, sz, sz, 3)
        fill_box(grid, 28, 29, 18, 18, sz, sz, 3)
        fill_box(grid, 28, 29, 15, 15, sz, sz, 3)

    # Left forearm Ceremonial Crimson & Gold Shogun Buckler Shield (-X)
    fill_box(grid, 4, 5, 10, 15, 15, 22, 1)
    fill_box(grid, 4, 4, 11, 14, 16, 21, 3)
    fill_box(grid, 4, 4, 12, 13, 17, 20, 2)
    fill_box(grid, 4, 4, 12, 13, 18, 19, 8)

    # --- HEROIC GOLD-CRESTED CRIMSON SHOGUN HEAD (Z: 31..39) ---
    fill_sym_box(grid, 0, 1, 10, 13, 31, 32, 6)
    fill_sym_box(grid, 0, 2, 9, 14, 33, 37, 1)
    fill_sym_box(grid, 0, 3, 9, 13, 33, 36, 1)
    fill_sym_box(grid, 0, 2, 10, 13, 37, 38, 1)
    fill_sym_box(grid, 0, 1, 10, 13, 38, 38, 3)   # Gold crown ridge
    # Flared kabuto neck-guard (Shikoro) at sides & rear
    fill_sym_box(grid, 3, 4, 8, 12, 33, 34, 2)
    fill_sym_box(grid, 3, 4, 8, 12, 33, 33, 3)
    fill_sym_box(grid, 0, 3, 8, 9, 32, 34, 2)
    fill_sym_box(grid, 0, 3, 8, 8, 32, 32, 3)
    # Fierce ink-black faceplate & visor brow framing glowing fiery-amber robot eyes!
    fill_sym_box(grid, 0, 2, 14, 14, 33, 35, 5)
    fill_sym_box(grid, 0, 2, 14, 15, 35, 35, 5)   # Crisp dark visor brow shadow
    fill_sym_box(grid, 0, 1, 14, 15, 33, 33, 4)   # Cream jaw guard
    fill_sym_box(grid, 1, 2, 14, 15, 34, 34, 8)   # Glowing fiery-gold/amber robot eyes
    # Sweeping Ceremonial Golden Kabuto Crescent Crest (Maedate)
    fill_sym_box(grid, 0, 0, 14, 15, 36, 37, 3)
    fill_sym_box(grid, 0, 0, 15, 15, 36, 36, 8)   # Glowing forehead jewel
    fill_sym_box(grid, 1, 2, 14, 15, 36, 37, 3)
    fill_sym_box(grid, 2, 3, 14, 15, 38, 39, 3)
    fill_sym_box(grid, 4, 4, 14, 14, 39, 39, 3)

    # Hollow unseen torso & heavy leg interiors to stay cleanly within voxel target
    hollow_interior_26(grid, 1, 30)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=34, pitch_a=20, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "daruma_a.vox")
    v_b = export_vox(model_b, "daruma_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: DARUMA DOLL -> SUMO SHOGUN DARUMA ROBOT",
        "1. TRADITIONAL DARUMA DOLL",
        "2. DARUMA SHOGUN ROBOT",
        "preview_daruma.png",
        yaw_a=34, pitch_a=20, yaw_b=32, pitch_b=20,
    )
    print(f"daruma: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
