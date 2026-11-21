import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across both Hojo Ujiyasu Samurai Robot and Lion of Sagami
PALETTE = {
    1: (218, 174, 96, 255),   # Warm Tawny-Sand Fur & Armor Plates
    2: (208, 136, 34, 255),   # Sculpted Golden-Ochre Lion Mane
    3: (144, 80, 22, 255),    # Deep Amber-Ochre Mane Shadow & Tail Tuft
    4: (146, 28, 40, 255),    # Deep Burgundy-Crimson Samurai Armor & Lacing
    5: (42, 46, 54, 255),     # Dark Forged Iron Armor, Frame & Claws
    6: (248, 210, 70, 255),   # Bright Burnished Gold Crests & Hojo Trim
    7: (240, 226, 194, 255),  # Warm Cream-Ivory Muzzle, Underbelly & Fangs
    8: (214, 224, 238, 255),  # Gleaming Katana Steel Blade & Claw Tips
    9: (64, 232, 168, 255),   # Fierce Glowing Emerald-Jade Eyes & Crest Core
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(x0, x1)), min(X - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center (requires even X)."""
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


def count_6_components(grid):
    """Count 6-connected components of nonzero voxels to guarantee no floating parts."""
    xs, ys, zs = np.nonzero(grid)
    if len(xs) == 0:
        return 0
    X, Y, Z = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    comps = 0
    for sx, sy, sz in zip(xs, ys, zs):
        if visited[sx, sy, sz]:
            continue
        comps += 1
        q = deque([(int(sx), int(sy), int(sz))])
        visited[sx, sy, sz] = True
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < X and 0 <= ny < Y and 0 <= nz < Z and grid[nx, ny, nz] > 0 and not visited[nx, ny, nz]:
                    visited[nx, ny, nz] = True
                    q.append((nx, ny, nz))
    return comps


# ============================================================
# FORM A: HOJO UJIYASU ROBOT — LION OF SAGAMI (44 x 26 x 44)
# ============================================================
def build_a():
    grid = np.zeros((44, 26, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21 (-X robot left)
    cx_r = X // 2      # 22 (+X robot right)

    # --- ARMORED LION-PAW SABATON FEET (Z: 0..4) ---
    fill_sym_box(grid, 3, 6, 8, 16, 0, 1, 5)     # Forged iron heavy sole
    fill_sym_box(grid, 4, 5, 7, 8, 0, 2, 5)      # Rear heel spur
    fill_sym_box(grid, 3, 6, 9, 16, 1, 2, 1)     # Tawny-sand lion paw boot
    fill_sym_box(grid, 3, 6, 15, 17, 1, 2, 1)    # Front paw arch
    fill_sym_box(grid, 4, 5, 16, 17, 2, 2, 7)    # Cream paw knuckle highlight
    # Three gleaming armored lion claws per foot (+Y front)
    fill_sym_box(grid, 3, 3, 17, 18, 0, 1, 8)
    fill_sym_box(grid, 5, 5, 17, 18, 0, 1, 8)
    fill_sym_box(grid, 6, 6, 16, 17, 0, 1, 8)
    # Burgundy-crimson ankle collar & gold trim
    fill_sym_box(grid, 3, 6, 9, 15, 3, 3, 4)
    fill_sym_box(grid, 4, 5, 15, 16, 3, 3, 6)
    fill_sym_box(grid, 4, 5, 10, 13, 3, 4, 5)

    # --- SAMURAI SUNEATE LOWER LEGS (Z: 4..15) ---
    fill_sym_box(grid, 3, 6, 9, 13, 4, 13, 5)    # Dark iron leg structure
    fill_sym_box(grid, 3, 6, 11, 14, 5, 12, 1)   # Tawny-sand shin armor
    # Burgundy-crimson horizontal samurai armor bands & gold lacing
    for bz in (6, 9, 12):
        fill_sym_box(grid, 3, 6, 9, 14, bz, bz, 4)
    fill_sym_box(grid, 4, 5, 14, 15, 5, 11, 4)   # Front crimson shin plate
    fill_sym_box(grid, 4, 5, 15, 15, 6, 10, 6)   # Vertical gold shin ridge
    # Rear calf crimson plate & golden-ochre fur/mane cuff trim (echoes lion hocks!)
    fill_sym_box(grid, 4, 5, 8, 9, 6, 11, 4)
    fill_sym_box(grid, 4, 5, 8, 8, 8, 9, 6)
    fill_sym_box(grid, 6, 6, 9, 11, 5, 7, 2)     # Outer ankle ochre mane tuft
    # Sculpted Lion-Crest Samurai Knee Guards (Z: 12..15)
    fill_sym_box(grid, 3, 6, 13, 15, 12, 14, 5)
    fill_sym_box(grid, 4, 5, 14, 16, 13, 15, 4)
    fill_sym_box(grid, 4, 5, 15, 16, 14, 15, 6)

    # --- THIGHS & KUSAZURI SAMURAI TASSETS (Z: 15..22) ---
    fill_sym_box(grid, 3, 5, 10, 13, 15, 19, 1)  # Tawny-sand thighs
    fill_sym_box(grid, 3, 4, 10, 12, 15, 17, 5)  # Inner iron knee/thigh frame
    fill_sym_box(grid, 5, 5, 10, 13, 16, 18, 4)  # Outer crimson thigh guard
    # Pelvis core
    fill_sym_box(grid, 0, 5, 9, 14, 19, 22, 5)
    # Front Kusazuri layered crimson samurai tassets with gold odoshi trim
    fill_sym_box(grid, 2, 5, 14, 15, 17, 21, 4)
    fill_sym_box(grid, 2, 5, 15, 15, 18, 18, 6)
    fill_sym_box(grid, 2, 5, 15, 15, 20, 20, 6)
    # Side Kusazuri hip armor skirts flaring outward
    fill_sym_box(grid, 6, 7, 10, 13, 17, 21, 4)
    fill_sym_box(grid, 7, 7, 10, 13, 18, 18, 6)
    fill_sym_box(grid, 7, 7, 10, 13, 20, 20, 6)
    # Rear Kusazuri skirt plates
    fill_sym_box(grid, 1, 5, 8, 9, 17, 21, 4)
    fill_sym_box(grid, 2, 5, 8, 8, 18, 18, 6)
    fill_sym_box(grid, 2, 5, 8, 8, 20, 20, 6)
    # Center front samurai sash & Hojo gold buckle
    fill_sym_box(grid, 0, 1, 14, 16, 18, 22, 4)
    fill_sym_box(grid, 0, 1, 15, 16, 19, 21, 6)
    fill_sym_box(grid, 0, 0, 16, 16, 20, 20, 9)

    # Rear Lion Tail tucked neatly down the back waist (transformation link!)
    fill_sym_box(grid, 0, 0, 7, 8, 19, 21, 1)
    fill_sym_box(grid, 0, 0, 6, 7, 16, 19, 1)
    fill_sym_box(grid, 0, 0, 6, 7, 15, 15, 4)
    fill_sym_box(grid, 0, 1, 5, 6, 12, 14, 3)    # Sculpted amber tail tuft
    fill_sym_box(grid, 0, 0, 5, 6, 11, 13, 2)

    # --- SAMURAI ABDOMEN & BROAD CHEST CORE (Z: 22..33) ---
    # Tapered samurai do-maru waist with crimson odoshi lacing
    fill_sym_box(grid, 0, 4, 9, 14, 22, 24, 5)
    fill_sym_box(grid, 0, 4, 13, 15, 22, 24, 4)
    fill_sym_box(grid, 0, 3, 15, 15, 23, 23, 6)
    # Broad Samurai Torso
    fill_sym_box(grid, 0, 6, 9, 15, 25, 32, 4)   # Deep burgundy-crimson chest cuirass
    fill_sym_box(grid, 0, 5, 10, 15, 31, 32, 5)  # Dark iron gorget / upper armor
    fill_sym_box(grid, 4, 6, 14, 16, 26, 30, 1)  # Tawny-sand pectoral armor plates
    fill_sym_box(grid, 5, 6, 15, 16, 27, 29, 6)  # Gold breastplate edge trim

    # --- ICONIC LION-CREST CHEST PLATE (Y: 15..19, Z: 25..32) ---
    # Outer golden-ochre & amber sculpted mane ring around chest lion emblem
    fill_sym_box(grid, 0, 4, 15, 16, 25, 31, 2)
    fill_sym_box(grid, 4, 4, 15, 17, 26, 30, 3)
    fill_sym_box(grid, 3, 4, 16, 17, 31, 32, 2)
    fill_sym_box(grid, 1, 3, 16, 17, 24, 25, 3)
    # Sculpted Lion Face Relief on Chest
    fill_sym_box(grid, 0, 2, 16, 18, 27, 30, 1)  # Tawny lion brow & cheeks
    fill_sym_box(grid, 0, 1, 17, 19, 26, 27, 7)  # Cream-ivory roaring lion muzzle
    fill_sym_box(grid, 0, 0, 19, 19, 27, 27, 5)  # Dark iron lion nose
    fill_sym_box(grid, 0, 1, 18, 18, 25, 25, 4)  # Crimson roaring mouth
    fill_sym_box(grid, 1, 1, 19, 19, 26, 26, 8)  # Tiny gleaming fangs
    fill_sym_box(grid, 2, 2, 18, 18, 29, 29, 9)  # Glowing emerald lion-crest eyes!
    fill_sym_box(grid, 0, 1, 17, 18, 30, 31, 6)  # Gold lion brow crown

    # --- SAMURAI BACKPACK & MANE CAPE FINS (Y: 5..9, Z: 24..33) ---
    fill_sym_box(grid, 0, 4, 6, 9, 24, 31, 5)    # Dark iron armored back core
    fill_sym_box(grid, 0, 3, 5, 7, 25, 30, 4)    # Burgundy samurai backplate
    fill_sym_box(grid, 0, 2, 5, 5, 26, 29, 6)    # Gold Hojo dorsal emblem
    fill_sym_box(grid, 0, 1, 5, 5, 27, 28, 1)    # Tawny crest center
    # Flared sculpted golden-ochre mane tufts framing backpack (reused in Lion mane!)
    fill_sym_box(grid, 3, 5, 5, 8, 27, 32, 2)
    fill_sym_box(grid, 4, 6, 5, 7, 27, 30, 3)
    fill_sym_box(grid, 5, 6, 6, 8, 29, 33, 2)

    # --- BROAD SCULPTED LION-MANE SHOULDER PAULDRONS (Z: 26..39, x_off: 6..16) ---
    # ("たてがみが兜と肩の装甲になる" — Lion mane directly forms grand layered shoulder pauldrons!)
    # Structural shoulder axles & crimson samurai O-sode armor core
    fill_sym_box(grid, 6, 9, 10, 13, 28, 32, 5)  # Dark iron shoulder joint
    fill_sym_box(grid, 7, 10, 9, 14, 27, 32, 4)  # Burgundy-crimson samurai o-sode plate
    fill_sym_box(grid, 8, 10, 14, 14, 28, 31, 6) # Gold front o-sode lacing frame
    fill_sym_box(grid, 8, 10, 9, 9, 28, 31, 6)   # Gold rear o-sode lacing frame

    # Crisp sculpted Golden-Ochre (2) & Deep Amber (3) Lion Mane Pauldron Spikes!
    mane_shoulder_layers = [
        # (x0, x1, y0, y1, z0, z1, col)
        # Inner mane collar hugging top of shoulder
        (6,  10, 9,  14, 32, 34, 2),
        (7,  11, 9,  14, 33, 35, 3),
        # Sweeping upper mane flame crest (sharp heroic silhouette!)
        (9,  12, 10, 13, 34, 36, 2),
        (11, 13, 10, 13, 36, 37, 2),
        (12, 14, 11, 12, 37, 39, 3),
        (13, 14, 11, 12, 38, 39, 2),
        # Broad middle flaring mane spikes (sweeping wide to x_off=16!)
        (10, 13, 9,  14, 30, 34, 2),
        (12, 15, 10, 13, 31, 34, 3),
        (14, 16, 10, 13, 32, 34, 2),
        (15, 16, 11, 12, 33, 35, 2),
        # Lower cascading mane locks over outer upper arm
        (11, 13, 9,  14, 27, 30, 3),
        (12, 14, 10, 13, 28, 30, 2),
        (13, 15, 10, 13, 27, 29, 3),
        (13, 14, 11, 12, 25, 27, 2),
        # Sculpted front & rear crest accents
        (8,  11, 14, 15, 30, 33, 2),
        (9,  11, 15, 15, 31, 32, 3),
        (8,  11, 8,  9,  30, 33, 2),
        (9,  11, 8,  8,  31, 32, 3),
    ]
    for x0, x1, y0, y1, z0, z1, col in mane_shoulder_layers:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)
    # Gold samurai studs accenting the mane pauldrons
    fill_sym_box(grid, 9, 10, 14, 15, 33, 33, 6)
    fill_sym_box(grid, 9, 10, 8, 9, 33, 33, 6)

    # --- ARMS & KOTE SAMURAI FOREARMS (Z: 14..28) ---
    # Upper arms
    fill_sym_box(grid, 8, 10, 10, 13, 22, 27, 5)  # Dark iron upper arm
    fill_sym_box(grid, 9, 10, 10, 13, 23, 26, 4)  # Crimson upper arm sleeve
    fill_sym_box(grid, 10, 10, 11, 12, 24, 25, 6) # Gold elbow rivet

    # LEFT ARM (-X, viewer's right): Armored Kote Forearm & Lion-Claw Buckler
    fill_box(grid, cx_l - 11, cx_l - 8, 10, 14, 16, 22, 1)    # Tawny-sand armored forearm
    fill_box(grid, cx_l - 11, cx_l - 8, 13, 14, 17, 21, 4)    # Burgundy forearm plate
    fill_box(grid, cx_l - 11, cx_l - 9, 10, 13, 14, 16, 5)    # Dark iron fist
    fill_box(grid, cx_l - 10, cx_l - 9, 13, 14, 14, 15, 7)    # Knuckle highlight
    # Left forearm Samurai Shield / Lion-Claw Guard
    fill_box(grid, cx_l - 12, cx_l - 11, 10, 15, 16, 22, 4)
    fill_box(grid, cx_l - 13, cx_l - 12, 11, 14, 17, 21, 5)
    fill_box(grid, cx_l - 13, cx_l - 13, 12, 13, 18, 20, 6)   # Gold Hojo shield crest
    fill_box(grid, cx_l - 12, cx_l - 12, 14, 15, 14, 16, 8)   # Steel lion-claw guard tips

    # RIGHT ARM (+X, viewer's left): Angled OUTWARD & FORWARD holding GLEAMING KATANA clear of chest!
    fill_box(grid, cx_r + 9, cx_r + 12, 10, 14, 18, 22, 1)    # Tawny-sand armored forearm
    fill_box(grid, cx_r + 10, cx_r + 13, 12, 16, 17, 21, 4)   # Burgundy kote guard angling outward
    fill_box(grid, cx_r + 13, cx_r + 13, 13, 15, 18, 20, 6)   # Gold bracer trim
    fill_box(grid, cx_r + 12, cx_r + 14, 15, 18, 16, 18, 5)   # Right fist held clearly outside shoulder!

    # --- GLEAMING SAMURAI KATANA / ODACHI BLADE (Sweeping cleanly OUTWARD & UP!) ---
    # Hilt (tsuka) + Gold pommel (kashira) + Gold guard (tsuba)
    fill_box(grid, cx_r + 13, cx_r + 13, 15, 16, 12, 16, 4)   # Crimson wrapped hilt
    fill_box(grid, cx_r + 13, cx_r + 13, 15, 16, 11, 11, 6)   # Gold pommel
    fill_box(grid, cx_r + 12, cx_r + 15, 16, 19, 18, 19, 6)   # Burnished gold tsuba guard!
    # Long gleaming steel katana blade rising boldly OUTWARD (+X) & FORWARD (+Y) clear of the shoulder mane!
    blade_profile = [
        # (z, y_back, y_front, x_off)
        (20, 17, 19, 14),
        (21, 17, 19, 14),
        (22, 17, 19, 14),
        (23, 18, 20, 15),
        (24, 18, 20, 15),
        (25, 18, 20, 15),
        (26, 19, 21, 16),
        (27, 19, 21, 16),
        (28, 19, 21, 16),
        (29, 19, 21, 17),
        (30, 20, 22, 17),
        (31, 20, 22, 17),
        (32, 20, 22, 18),
        (33, 20, 22, 18),
        (34, 21, 23, 18),
        (35, 21, 23, 19),
        (36, 21, 23, 19),
        (37, 21, 22, 19),
        (38, 22, 23, 20),
        (39, 22, 22, 20),
    ]
    prev_x = None
    prev_yb = None
    prev_yf = None
    for bz, yb, yf, bx_off in blade_profile:
        fill_box(grid, cx_r + bx_off, cx_r + bx_off, yb, yf, bz, bz, 8)
        if yf - yb >= 2:
            grid[cx_r + bx_off, yb, bz] = 5  # Dark iron mune spine
        if prev_x is not None and bx_off != prev_x:
            # Explicit 6-connected face bridge at each outward diagonal step
            fill_box(grid, cx_r + prev_x, cx_r + bx_off, max(yb, prev_yb), min(yf, prev_yf), bz - 1, bz - 1, 8)
        prev_x, prev_yb, prev_yf = bx_off, yb, yf

    # --- NOBLE HOJO UJIYASU KABUTO HELMET WITH FLARING LION MANE (Z: 32..43) ---
    # Neck & samurai throat guard
    fill_sym_box(grid, 0, 1, 11, 13, 32, 34, 5)
    fill_sym_box(grid, 0, 2, 13, 14, 32, 33, 4)

    # Samurai Head & Fierce Menpo Faceplate (Z: 34..39)
    fill_sym_box(grid, 0, 2, 10, 14, 34, 38, 5)   # Dark iron inner head & kabuto core
    fill_sym_box(grid, 0, 1, 14, 15, 34, 35, 5)   # Samurai menpo chin mask
    fill_sym_box(grid, 0, 0, 15, 15, 34, 34, 6)   # Gold chin gem
    fill_sym_box(grid, 2, 2, 14, 15, 34, 36, 7)   # Cream-ivory samurai cheek guards
    fill_sym_box(grid, 0, 2, 14, 15, 36, 36, 9)   # Fierce glowing emerald-jade eyes!
    fill_sym_box(grid, 0, 0, 15, 15, 36, 36, 5)   # Nose bridge separating glowing eyes!

    # Deep Burgundy-Crimson Kabuto Dome & Shikoro Neck Guard (Z: 36..40)
    fill_sym_box(grid, 0, 3, 9, 14, 37, 39, 4)
    fill_sym_box(grid, 0, 2, 10, 14, 39, 40, 4)
    fill_sym_box(grid, 0, 2, 14, 15, 37, 38, 5)   # Dark iron visor brim (mabizashi)
    fill_sym_box(grid, 0, 3, 8, 10, 34, 37, 4)    # Rear burgundy shikoro neck-guard

    # GRAND FLARING SCULPTED GOLDEN-OCHRE LION MANE AROUND THE KABUTO! ("たてがみが兜になる")
    kabuto_mane_layers = [
        # Radiating side mane flares around the helmet cheeks/temples
        (3, 5, 9,  13, 35, 38, 2),
        (4, 6, 10, 13, 36, 39, 3),
        (5, 6, 10, 12, 37, 39, 2),
        (4, 5, 9,  12, 39, 40, 2),
        # Upper crown mane tufts flaring behind the gold crest
        (1, 3, 9,  12, 40, 41, 2),
        (2, 3, 10, 11, 41, 42, 3),
        # Lush cascading rear lion mane down the back of the kabuto (epic REAR VIEW!)
        (0, 4, 7,  9,  35, 39, 2),
        (1, 3, 6,  8,  34, 38, 3),
        (0, 2, 6,  7,  33, 36, 2),
        (0, 3, 8,  10, 39, 41, 3),
    ]
    for x0, x1, y0, y1, z0, z1, col in kabuto_mane_layers:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)

    # Grand Burnished-Gold Hojo Kabuto Maedate & Sweeping Kuwagata Horns (Z: 38..43)
    fill_sym_box(grid, 0, 1, 14, 16, 38, 39, 6)
    fill_sym_box(grid, 0, 0, 15, 16, 40, 41, 6)
    fill_sym_box(grid, 0, 0, 16, 16, 39, 39, 9)   # Glowing jade center gem
    # Sweeping Golden Kuwagata Horns curving outward & high
    fill_sym_box(grid, 1, 2, 14, 15, 39, 40, 6)
    fill_sym_box(grid, 2, 3, 14, 15, 40, 41, 6)
    fill_sym_box(grid, 3, 4, 13, 14, 41, 42, 6)
    fill_sym_box(grid, 4, 5, 13, 14, 42, 43, 6)

    # Hollow unseen strictly-interior voxels to keep crisp voxel budget
    hollow_interior_26(grid, 1, 41)

    return grid


# ============================================================
# FORM B: LION OF SAGAMI — 相模の獅子 (26 x 46 x 32)
# ============================================================
def build_b():
    grid = np.zeros((26, 46, 32), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 12.5

    # --- FOUR TALL, MUSCULAR ARMORED LION LEGS & GROUNDED PAWS (Z: 0..17) ---
    # 1) FRONT LEGS (Y: 29..36, x_off: 2..5)
    # Broad grounded feline paws (Z: 0..2)
    fill_sym_box(grid, 2, 5, 30, 35, 0, 1, 1)    # Tawny-sand paw base
    fill_sym_box(grid, 2, 5, 33, 35, 1, 2, 7)    # Cream-ivory paw toe pads
    fill_sym_box(grid, 2, 4, 30, 34, 2, 2, 1)
    # Three gleaming steel claws protruding forward (+Y) on each front paw
    fill_sym_box(grid, 2, 2, 35, 36, 0, 1, 8)
    fill_sym_box(grid, 4, 4, 35, 36, 0, 1, 8)
    fill_sym_box(grid, 5, 5, 34, 35, 0, 1, 8)

    # Sleek muscular lower forelegs with Burgundy & Dark-Iron Samurai Leg Bands! (Z: 3..12)
    fill_sym_box(grid, 2, 4, 30, 33, 3, 5, 4)    # Deep burgundy samurai wrist band
    fill_sym_box(grid, 2, 4, 32, 33, 3, 3, 5)    # Dark iron lower rim
    fill_sym_box(grid, 3, 4, 33, 33, 4, 5, 6)    # Burnished gold front shin trim
    fill_sym_box(grid, 2, 4, 29, 33, 6, 12, 1)   # Athletic tawny-sand foreleg
    fill_sym_box(grid, 2, 5, 28, 32, 12, 17, 1)  # Muscular lion shoulder top
    # Upper foreleg dark-iron & burgundy armor cuff + elbow mane tufts!
    fill_sym_box(grid, 3, 4, 29, 33, 9, 10, 5)
    fill_sym_box(grid, 3, 4, 30, 33, 10, 11, 4)
    fill_sym_box(grid, 4, 4, 32, 33, 10, 11, 6)
    fill_sym_box(grid, 3, 4, 28, 29, 8, 11, 2)   # Golden-ochre elbow fur tuft
    fill_sym_box(grid, 3, 4, 27, 28, 9, 10, 3)

    # 2) HIND LEGS (Athletic Feline S-Curve, Y: 7..18, Z: 0..18)
    # Grounded hind paws (Z: 0..2)
    fill_sym_box(grid, 2, 5, 9, 14, 0, 1, 1)
    fill_sym_box(grid, 2, 5, 13, 14, 1, 2, 7)    # Cream-ivory toe pads
    fill_sym_box(grid, 2, 2, 14, 15, 0, 1, 8)    # Gleaming claws
    fill_sym_box(grid, 4, 4, 14, 15, 0, 1, 8)
    fill_sym_box(grid, 5, 5, 13, 14, 0, 1, 8)
    # Angled feline hock/metatarsus sweeping back (Z: 2..9)
    fill_sym_box(grid, 2, 4, 9, 12, 2, 4, 4)     # Burgundy samurai ankle band
    fill_sym_box(grid, 3, 4, 12, 12, 3, 4, 6)    # Gold trim
    fill_sym_box(grid, 2, 4, 8, 11, 4, 8, 1)     # Swept-back athletic hock
    fill_sym_box(grid, 2, 4, 7, 9, 7, 9, 5)      # Dark iron hock armor band
    fill_sym_box(grid, 3, 4, 7, 7, 7, 8, 2)      # Small ochre hock tuft
    # Powerful muscular hind thighs sweeping forward into haunches (Z: 9..18)
    fill_sym_box(grid, 2, 4, 8, 14, 9, 12, 1)
    fill_sym_box(grid, 2, 5, 9, 16, 11, 16, 1)
    fill_sym_box(grid, 3, 5, 10, 17, 15, 18, 1)
    # Burgundy & gold armored thigh plate (reused from robot kusazuri!)
    fill_sym_box(grid, 4, 5, 10, 15, 13, 15, 4)
    fill_sym_box(grid, 5, 5, 11, 14, 14, 14, 6)
    fill_sym_box(grid, 4, 5, 10, 14, 12, 12, 5)

    # --- MUSCULAR TAWNY-GOLD LION BODY (Y: 9..33, Z: 10..21) ---
    # Raised +2Z for proud, athletic big-cat posture with clear daylight under belly!
    body_slices = [
        # (y, rx, zb, zt)
        (9,  3.1, 14, 18),
        (10, 3.9, 13, 19),
        (11, 4.5, 12, 19),
        (12, 4.8, 12, 20),
        (13, 4.9, 12, 20),
        (14, 4.8, 12, 20),
        (15, 4.5, 12, 20),
        (16, 4.0, 13, 19),   # Lean athletic feline waist tuck!
        (17, 3.8, 13, 19),
        (18, 3.7, 13, 19),
        (19, 3.8, 13, 19),
        (20, 4.0, 12, 20),
        (21, 4.3, 12, 20),
        (22, 4.7, 11, 20),   # Deepening muscular ribcage
        (23, 5.0, 11, 21),
        (24, 5.3, 10, 21),
        (25, 5.5, 10, 21),
        (26, 5.5, 10, 21),
        (27, 5.5, 10, 21),
        (28, 5.4, 10, 21),
        (29, 5.2, 10, 21),
        (30, 5.0, 10, 21),
        (31, 4.6, 11, 21),
        (32, 4.2, 11, 20),
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
                        col = 7   # Warm cream-ivory underbelly
                    else:
                        col = 1   # Muscular tawny-sand lion coat
                    grid[x, y, z] = col

    # --- SAMURAI ARMORED BACK SADDLE & CHEST COLLAR (reused from robot armor!) ---
    # Deep burgundy-crimson & dark-iron Hojo armor saddle along the lion's mid-back
    fill_sym_box(grid, 0, 4, 16, 23, 18, 20, 4)  # Crimson samurai saddle plates
    fill_sym_box(grid, 0, 3, 15, 24, 20, 21, 5)  # Dark iron spine ridge armor
    fill_sym_box(grid, 0, 1, 17, 22, 21, 21, 6)  # Burnished gold dorsal spine crest
    fill_sym_box(grid, 4, 4, 17, 22, 17, 19, 5)  # Side dark iron saddle edge
    fill_sym_box(grid, 4, 4, 18, 21, 18, 18, 6)  # Gold saddle rivet trim
    # Armored burgundy & gold chest collar emerging proudly beneath the front mane!
    fill_sym_box(grid, 0, 4, 31, 35, 11, 15, 4)
    fill_sym_box(grid, 0, 3, 34, 36, 12, 14, 5)
    fill_sym_box(grid, 0, 2, 35, 36, 12, 14, 6)
    fill_sym_box(grid, 0, 0, 36, 36, 13, 13, 9)  # Glowing emerald chest collar gem

    # --- FULL VOLUMETRIC SCULPTED GOLDEN-OCHRE LION MANE (Y: 23..38, Z: 11..30) ---
    # Directly reuses the robot's kabuto mane & lion-mane shoulder pauldrons!
    mane_center_y = 31.5
    mane_center_z = 21.0
    for x in range(X):
        dx = abs(x - cx)
        for y in range(23, 38):
            dy = y - mane_center_y
            for z in range(12, 30):
                dz = z - mane_center_z
                rx_m = 7.9 - max(0.0, (29.0 - y) * 0.48) - max(0.0, (y - 34.0) * 0.9)
                rz_m = 7.8 - max(0.0, (29.0 - y) * 0.35)
                if rx_m <= 1.5 or rz_m <= 1.5:
                    continue
                d2 = (dx / rx_m) ** 2 + (dy / 6.3) ** 2 + (dz / rz_m) ** 2
                angle = np.arctan2(dz, dx + 0.01)
                spike_mod = 0.16 * np.cos(angle * 7.0) + 0.09 * np.sin((y + z) * 0.9)
                if d2 <= 1.0 + spike_mod:
                    # Leave clean front pocket for the roaring lion face
                    if y >= 35 and dx <= 4.3 and 16 <= z <= 25:
                        continue
                    lock_band = int(np.floor((angle + np.pi) * 3.5 + (y * 0.35))) % 3
                    if lock_band == 0 or (d2 < 0.72 and z < 18):
                        col = 3
                    else:
                        col = 2
                    grid[x, y, z] = col

    # Dramatic outer radiating mane flare spikes (echoing the robot's shoulder pauldrons!)
    mane_flares = [
        # Upper crown & nape flares
        (0, 3, 27, 33, 28, 29, 2),
        (2, 5, 28, 33, 27, 29, 3),
        (4, 7, 29, 34, 26, 28, 2),
        # Wide lateral mane flares (broad majestic lion silhouette!)
        (7, 9, 29, 34, 20, 25, 2),
        (8, 10, 30, 33, 21, 24, 3),
        (7, 9, 28, 33, 16, 20, 3),
        (8, 9, 29, 32, 17, 19, 2),
        # Sweeping rear shoulder mane cape locks (flowing over back!)
        (0, 4, 22, 25, 21, 24, 2),
        (2, 6, 23, 26, 19, 23, 3),
        (5, 7, 24, 27, 17, 21, 2),
        # Cascading front chest mane bib framing the burgundy/gold collar
        (0, 4, 33, 36, 14, 17, 2),
        (1, 3, 35, 37, 13, 16, 3),
        (0, 2, 35, 36, 11, 13, 2),
        (3, 5, 34, 36, 15, 18, 3),
    ]
    for x0, x1, y0, y1, z0, z1, col in mane_flares:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)

    # Samurai Kabuto Hojo Crest integrated into top of the Lion's mane crown!
    fill_sym_box(grid, 0, 1, 31, 34, 28, 29, 4)  # Burgundy kabuto spine ridge
    fill_sym_box(grid, 0, 0, 32, 35, 29, 30, 6)  # Gold Hojo crown tip
    fill_sym_box(grid, 1, 2, 33, 34, 29, 30, 6)  # Mini gold kuwagata horn tips peeking from mane!
    fill_sym_box(grid, 3, 3, 32, 33, 30, 31, 6)

    # --- FIERCE ROARING LION HEAD (Y: 34..44, Z: 16..27) ---
    # Solid sculpted tawny-sand lion cranium & cheeks
    fill_sym_box(grid, 0, 4, 34, 39, 18, 25, 1)
    fill_sym_box(grid, 0, 3, 35, 40, 19, 26, 1)
    fill_sym_box(grid, 0, 2, 37, 41, 24, 26, 1)  # Broad noble lion forehead
    fill_sym_box(grid, 0, 1, 39, 41, 25, 25, 6)  # Gold Hojo forehead emblem!

    # Rounded Lion Ears poking cleanly out of the top mane!
    fill_sym_box(grid, 4, 5, 34, 36, 25, 27, 1)
    fill_sym_box(grid, 4, 4, 36, 36, 26, 26, 3)  # Inner dark-amber ear hollow
    fill_sym_box(grid, 5, 5, 34, 35, 27, 27, 5)  # Dark ear rim tip

    # Fierce Sculpted Brow & Glowing Emerald-Jade Eyes!
    fill_sym_box(grid, 2, 4, 39, 40, 24, 24, 3)  # Furrowed amber lion brow ridge
    fill_sym_box(grid, 3, 3, 39, 40, 23, 23, 5)  # Dark eye socket outline
    fill_sym_box(grid, 3, 3, 40, 40, 23, 23, 9)  # Fierce glowing emerald-jade lion eyes!
    fill_sym_box(grid, 4, 4, 38, 39, 21, 22, 7)  # Cheek highlight

    # Distinctive Squared Lion Muzzle & Open Roaring Jaws!
    fill_sym_box(grid, 0, 2, 40, 43, 20, 23, 1)  # Strong tawny nose bridge
    fill_sym_box(grid, 0, 2, 41, 44, 20, 21, 7)  # Broad cream-ivory whisker muzzle pads
    fill_sym_box(grid, 0, 1, 43, 44, 22, 22, 1)
    fill_sym_box(grid, 0, 1, 44, 44, 21, 22, 5)  # Broad dark-iron feline nose!
    # Open Roaring Mouth Cavity & Gleaming Fangs!
    fill_sym_box(grid, 0, 2, 39, 42, 18, 19, 4)  # Deep burgundy roaring mouth interior
    fill_sym_box(grid, 0, 1, 42, 43, 18, 19, 0)  # Open mouth space between jaws
    fill_sym_box(grid, 2, 2, 42, 43, 19, 19, 8)  # Upper gleaming canine fangs!
    fill_sym_box(grid, 2, 2, 42, 42, 18, 18, 8)  # Lower canine fangs!
    # Strong Lower Jaw & Lion Chin Beard
    fill_sym_box(grid, 0, 2, 38, 43, 16, 17, 1)  # Lower tawny jaw
    fill_sym_box(grid, 0, 1, 42, 43, 16, 17, 7)  # Cream-ivory chin
    fill_sym_box(grid, 0, 1, 39, 41, 15, 16, 2)  # Golden-ochre lion chin beard

    # --- PROUD RAISED S-CURVED TUFTED LION TAIL (Y: 1..11, Z: 17..30) ---
    tail_segs = [
        # (x0, x1, y0, y1, z0, z1, col)
        (0, 0, 8,  10, 17, 18, 1),   # Solid tail root anchored in rump
        (0, 0, 7,  8,  18, 19, 1),
        (0, 0, 5,  7,  19, 20, 1),
        (0, 0, 4,  5,  20, 22, 1),
        (0, 0, 3,  4,  21, 23, 4),   # Small crimson/gold samurai tail band
        (0, 0, 3,  4,  22, 22, 6),
        (0, 0, 2,  3,  23, 25, 1),
        (0, 0, 3,  4,  25, 27, 1),   # Graceful forward curl at top of tail
        # Lush sculpted flame-like tail tuft (amber-ochre & golden-ochre)
        (0, 1, 3,  5,  26, 28, 3),
        (0, 1, 4,  6,  27, 29, 2),
        (0, 0, 5,  7,  28, 29, 3),
        (0, 0, 6,  7,  29, 30, 2),
    ]
    for x0, x1, y0, y1, z0, z1, col in tail_segs:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)

    # Hollow strictly interior voxels inside bulky body & mane while keeping 100% 6-connectivity
    hollow_interior_26(grid, 1, 28)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=34, pitch_a=20, yaw_b=40, pitch_b=22):
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
    c_a = count_6_components(model_a)
    c_b = count_6_components(model_b)
    v_a = export_vox(model_a, "ujiyasu_a.vox")
    v_b = export_vox(model_b, "ujiyasu_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: HOJO UJIYASU ROBOT -> LION OF SAGAMI",
        "1. HOJO UJIYASU ROBOT",
        "2. LION OF SAGAMI",
        "preview_ujiyasu.png",
        yaw_a=34, pitch_a=20, yaw_b=42, pitch_b=20,
    )
    print(f"ujiyasu: A={v_a} voxels {model_a.shape} (comps={c_a}), B={v_b} voxels {model_b.shape} (comps={c_b})")
