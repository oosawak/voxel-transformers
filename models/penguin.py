import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (40, 46, 58, 255),     # Glossy Emperor Charcoal-Black
    2: (76, 88, 110, 255),    # Slate-Blue-Grey Feather Mantle / Shading
    3: (244, 248, 255, 255),  # Crisp Snow-White Belly / Breastplate
    4: (196, 212, 232, 255),  # Cool Glacier-Silver Belly Shading / Plating
    5: (255, 208, 66, 255),   # Warm Golden-Yellow Emperor Neck & Cheek Patch
    6: (248, 130, 30, 255),   # Vibrant Orange-Amber Beak, Feet & Helmet Crest
    7: (202, 76, 20, 255),    # Deep Coral-Orange Beak / Webbed Foot Shading
    8: (92, 226, 255, 255),   # Glacial Ice-Cyan Visor / Eye Glint / Cryo-Edge
    9: (124, 142, 168, 255),  # Polar Steel-Blue Joints / Thruster Frame
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


# ==========================================
# FORM A: EMPEROR PENGUIN (24 x 22 x 32)
# ==========================================
def build_a():
    grid = np.zeros((24, 22, 32), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 11.5

    # --- CHUNKY ORANGE WEBBED FEET (Z: 0..2) ---
    # Webbed foot pads grounded at Z=0
    fill_sym_box(grid, 1, 4, 10, 15, 0, 0, 6)
    # Three distinct webbed toes extending forward to Y=16..17
    fill_sym_box(grid, 1, 1, 16, 16, 0, 0, 6)
    fill_sym_box(grid, 2, 3, 16, 17, 0, 0, 6)
    fill_sym_box(grid, 4, 4, 16, 16, 0, 0, 6)
    # Subtle deep-orange webbing ridges
    fill_sym_box(grid, 2, 2, 13, 15, 0, 0, 7)
    fill_sym_box(grid, 4, 4, 13, 15, 0, 0, 7)
    # Upper foot instep & sturdy ankles (Z: 1..2)
    fill_sym_box(grid, 2, 3, 9, 14, 1, 1, 6)
    fill_sym_box(grid, 2, 3, 14, 15, 1, 1, 7)
    fill_sym_box(grid, 2, 3, 9, 11, 2, 2, 7)

    # --- SCULPTED UPRIGHT EMPEROR BODY (Z: 2..22) ---
    # (z, rx, y_center, ry_back, ry_front)
    body_profile = [
        (2,  4.4, 10.6, 3.2, 3.6),
        (3,  5.3, 10.6, 4.0, 4.5),
        (4,  5.9, 10.5, 4.5, 5.1),
        (5,  6.2, 10.5, 4.8, 5.5),
        (6,  6.4, 10.5, 5.0, 5.7),
        (7,  6.5, 10.5, 5.1, 5.8),
        (8,  6.5, 10.5, 5.1, 5.8),
        (9,  6.4, 10.5, 5.0, 5.8),
        (10, 6.3, 10.5, 4.9, 5.7),
        (11, 6.2, 10.5, 4.8, 5.6),
        (12, 6.0, 10.5, 4.7, 5.4),
        (13, 5.8, 10.5, 4.6, 5.2),
        (14, 5.6, 10.5, 4.4, 5.0),
        (15, 5.4, 10.5, 4.3, 4.8),
        (16, 5.1, 10.5, 4.1, 4.6),
        (17, 4.8, 10.5, 3.9, 4.4),
        (18, 4.6, 10.5, 3.7, 4.2),
        (19, 4.3, 10.5, 3.5, 4.0),
        (20, 4.1, 10.5, 3.3, 3.8),
        (21, 3.9, 10.5, 3.1, 3.6),
        (22, 3.8, 10.5, 3.0, 3.5),
    ]

    for z, rx, yc, ry_b, ry_f in body_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for y in range(Y):
                dy = y - yc
                ry = ry_f if dy >= 0 else ry_b
                dist2 = (dx / rx) ** 2 + (dy / ry) ** 2
                if dist2 <= 1.0:
                    # Determine iconic emperor penguin tuxedo markings
                    # Front belly is crisp white, sides & back glossy charcoal
                    belly_y_cut = 10.2 + 0.14 * (dx ** 1.4)
                    if z >= 19:
                        belly_y_cut += (z - 18) * 0.45

                    if y >= belly_y_cut:
                        # Upper chest golden-yellow emperor glow (Z: 18..21)
                        if z >= 19 and y >= belly_y_cut + 0.5:
                            col = 5
                        elif z == 18 and dx <= 3.2 and y >= 13:
                            col = 5
                        elif z <= 3:
                            col = 4  # Cool glacier shading on underside
                        elif y < belly_y_cut + 1.0:
                            col = 4  # Soft glacier-silver tuxedo transition
                        else:
                            col = 3  # Crisp snow-white belly
                    else:
                        # Glossy charcoal back with slate-blue-grey mantle sheen
                        if dy <= -ry_b * 0.52 and dx <= rx * 0.62 and 5 <= z <= 19:
                            col = 2
                        else:
                            col = 1
                    grid[x, y, z] = col

    # --- STUBBY TAIL AT -Y (Z: 1..5) ---
    fill_sym_box(grid, 0, 1, 2, 5, 1, 1, 1)
    fill_sym_box(grid, 0, 2, 3, 6, 2, 2, 1)
    fill_sym_box(grid, 0, 0, 3, 5, 2, 2, 2)
    fill_sym_box(grid, 0, 2, 4, 7, 3, 3, 1)
    fill_sym_box(grid, 0, 1, 4, 6, 3, 3, 2)
    fill_sym_box(grid, 0, 2, 5, 7, 4, 5, 1)
    fill_sym_box(grid, 0, 1, 5, 6, 4, 5, 2)

    # --- SLEEK EMPEROR FLIPPER WINGS (Z: 6..19) ---
    # Sweeping gracefully outward and downward from the shoulders
    flipper_layers = [
        # (z, x_off0, x_off1, y0, y1)
        (19, 4, 5, 8, 11),
        (18, 5, 6, 8, 11),
        (17, 5, 7, 8, 12),
        (16, 6, 7, 8, 12),
        (15, 6, 8, 8, 12),
        (14, 7, 8, 8, 12),
        (13, 7, 9, 8, 12),
        (12, 8, 9, 9, 12),
        (11, 8, 9, 9, 12),
        (10, 8, 10, 9, 12),
        (9,  9, 10, 9, 12),
        (8,  9, 10, 10, 12),
        (7,  9, 10, 10, 11),
        (6,  10, 10, 10, 11),
    ]
    for z, x0, x1, y0, y1 in flipper_layers:
        fill_sym_box(grid, x0, x1, y0, y1, z, z, 1)
        # Slate-blue-grey leading/outer feather edge
        fill_sym_box(grid, x1, x1, y0, y0 + 1, z, z, 2)
        # Crisp snow-white / glacier inner trailing edge
        if x1 > x0 and z >= 8:
            fill_sym_box(grid, x0, x0, y1, y1, z, z, 4 if z <= 10 else 3)

    # --- EMPEROR PENGUIN HEAD (Z: 22..30) ---
    head_profile = [
        (23, 3.8, 10.8, 3.2, 3.5),
        (24, 3.9, 10.9, 3.3, 3.6),
        (25, 3.9, 11.0, 3.3, 3.6),
        (26, 3.8, 11.0, 3.2, 3.5),
        (27, 3.6, 11.0, 3.0, 3.4),
        (28, 3.2, 10.9, 2.7, 3.0),
        (29, 2.6, 10.8, 2.2, 2.5),
        (30, 1.8, 10.7, 1.5, 1.8),
    ]
    for z, rx, yc, ry_b, ry_f in head_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for y in range(Y):
                dy = y - yc
                ry = ry_f if dy >= 0 else ry_b
                if (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0:
                    col = 2 if (z >= 29 and dx <= 1.6 and dy <= 0.5) else 1
                    grid[x, y, z] = col

    # --- ICONIC GOLDEN-YELLOW / ORANGE CHEEK-EAR PATCHES (Z: 20..25) ---
    # Sweeping from upper breast collar up onto the sides of the head
    fill_sym_box(grid, 2, 3, 12, 13, 21, 22, 5)
    fill_sym_box(grid, 3, 3, 10, 13, 22, 24, 5)
    fill_sym_box(grid, 3, 3, 10, 11, 24, 25, 6)  # Warm orange auricular glow
    fill_sym_box(grid, 3, 3, 11, 12, 21, 21, 5)
    fill_sym_box(grid, 1, 2, 13, 14, 20, 21, 5)  # Golden throat wash
    fill_sym_box(grid, 0, 1, 14, 14, 19, 20, 5)

    # --- BRIGHT EXPRESSIVE EYES (Z: 26..27) ---
    # Clean snow-white sclera + bright glacial-cyan glint contrasting against charcoal head
    fill_sym_box(grid, 3, 3, 13, 13, 26, 27, 3)
    fill_sym_box(grid, 3, 3, 14, 14, 26, 26, 8)
    fill_sym_box(grid, 2, 2, 14, 14, 27, 27, 1)  # Expressive brow line

    # --- SLEEK ORANGE-AMBER EMPEROR BEAK FACING +Y (Y: 14..20, Z: 24..26) ---
    # Base bridge connecting solidly to face
    fill_sym_box(grid, 0, 1, 14, 15, 25, 26, 6)
    fill_sym_box(grid, 0, 1, 14, 15, 24, 24, 7)
    # Mid beak
    fill_sym_box(grid, 0, 1, 16, 17, 25, 25, 6)
    fill_sym_box(grid, 0, 0, 16, 17, 26, 26, 6)
    fill_sym_box(grid, 0, 1, 16, 16, 24, 24, 7)
    fill_sym_box(grid, 0, 0, 17, 18, 24, 24, 7)
    # Tapered tip with characteristic gentle emperor beak curve
    fill_sym_box(grid, 0, 0, 18, 19, 25, 25, 6)
    fill_sym_box(grid, 0, 0, 19, 20, 24, 24, 6)

    # Hollow unseen torso & head interior so voxel count stays crisp & compact
    hollow_interior(grid, 3, 28)

    return grid


# ==========================================
# FORM B: PENGUIN POLAR ROBOT (32 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((32, 24, 42), dtype=np.uint8)

    # --- ORANGE-TOED WEBBED POLAR BOOTS (Z: 0..3) ---
    # Dark charcoal sole & polar steel heel spur
    fill_sym_box(grid, 2, 5, 8, 15, 0, 1, 1)
    fill_sym_box(grid, 2, 5, 7, 8, 0, 2, 9)
    fill_sym_box(grid, 3, 4, 7, 7, 1, 2, 2)
    # Iconic webbed orange three-toed polar boot front (from Penguin webbed feet!)
    fill_sym_box(grid, 2, 5, 13, 16, 0, 1, 6)
    fill_sym_box(grid, 2, 2, 16, 17, 0, 1, 6)  # Inner toe
    fill_sym_box(grid, 3, 4, 16, 18, 0, 1, 6)  # Center armored toe
    fill_sym_box(grid, 5, 5, 16, 17, 0, 1, 6)  # Outer toe
    fill_sym_box(grid, 2, 5, 13, 15, 2, 2, 6)
    fill_sym_box(grid, 3, 4, 15, 16, 2, 2, 7)  # Deep coral toe ridge
    fill_sym_box(grid, 2, 5, 11, 12, 2, 2, 4)  # Glacier-silver ankle collar
    # Ankle joint
    fill_sym_box(grid, 3, 4, 9, 12, 2, 3, 9)

    # --- LOWER LEGS & KNEE GUARDS (Z: 4..14) ---
    # Core frame
    fill_sym_box(grid, 3, 4, 9, 12, 4, 13, 9)
    # Crisp snow-white front shin armor (echoing penguin belly)
    fill_sym_box(grid, 2, 5, 11, 13, 4, 12, 3)
    fill_sym_box(grid, 3, 4, 13, 14, 5, 11, 3)
    fill_sym_box(grid, 2, 2, 12, 13, 5, 11, 4)
    fill_sym_box(grid, 5, 5, 12, 13, 5, 11, 4)
    # Sleek charcoal-black calf shell & outer polar fin trim
    fill_sym_box(grid, 2, 5, 8, 10, 4, 12, 1)
    fill_sym_box(grid, 5, 5, 9, 11, 5, 11, 2)
    fill_sym_box(grid, 3, 4, 7, 8, 5, 10, 1)
    # Rear polar jet calf-thrusters
    fill_sym_box(grid, 3, 4, 7, 7, 6, 8, 9)
    fill_sym_box(grid, 3, 4, 6, 6, 6, 7, 8)
    # Sculpted knee guards with golden-yellow accent & cyan dot
    fill_sym_box(grid, 2, 5, 12, 14, 12, 14, 3)
    fill_sym_box(grid, 3, 4, 14, 15, 12, 14, 5)
    fill_sym_box(grid, 3, 4, 15, 15, 13, 13, 8)
    fill_sym_box(grid, 3, 4, 10, 12, 13, 14, 1)

    # --- THIGHS (Z: 14..19) ---
    fill_sym_box(grid, 2, 4, 9, 13, 14, 19, 4)
    fill_sym_box(grid, 2, 4, 12, 13, 15, 18, 3)
    fill_sym_box(grid, 2, 4, 9, 10, 15, 18, 1)
    fill_sym_box(grid, 4, 4, 10, 12, 15, 18, 2)
    fill_sym_box(grid, 3, 3, 10, 11, 14, 14, 9)

    # --- WAIST / PELVIS & REAR TAIL-SKIRT (Z: 18..22) ---
    fill_sym_box(grid, 0, 4, 9, 13, 19, 22, 1)
    fill_sym_box(grid, 0, 4, 12, 14, 20, 21, 3)
    # Side hip armor skirts with orange trim
    fill_sym_box(grid, 5, 5, 10, 13, 19, 21, 1)
    fill_sym_box(grid, 5, 5, 12, 13, 19, 20, 6)
    # Center tuxedo belt buckle
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 1)
    fill_sym_box(grid, 0, 1, 14, 15, 20, 21, 5)
    fill_sym_box(grid, 0, 0, 15, 15, 20, 20, 8)
    # Rear penguin tail-coat stabilizer (from Form A stubby tail!)
    fill_sym_box(grid, 0, 2, 6, 8, 19, 21, 1)
    fill_sym_box(grid, 0, 2, 5, 7, 18, 20, 1)
    fill_sym_box(grid, 0, 1, 4, 6, 17, 19, 1)
    fill_sym_box(grid, 0, 1, 5, 7, 20, 21, 2)
    fill_sym_box(grid, 0, 0, 4, 5, 18, 19, 2)

    # --- HEROIC TUXEDO TORSO (Z: 22..33) - DIRECTLY FORM A'S PENGUIN BODY! ---
    # Mid-section taper (abdomen)
    fill_sym_box(grid, 0, 4, 8, 13, 22, 24, 1)
    fill_sym_box(grid, 0, 3, 12, 14, 22, 24, 4)
    fill_sym_box(grid, 0, 2, 13, 14, 23, 24, 3)

    # Broad Penguin Tuxedo Chest Core
    fill_sym_box(grid, 0, 5, 8, 14, 25, 32, 1)
    # Crisp snow-white armored penguin breastplate!
    fill_sym_box(grid, 0, 4, 12, 15, 25, 31, 3)
    fill_sym_box(grid, 0, 3, 14, 16, 26, 30, 3)
    fill_sym_box(grid, 4, 4, 13, 15, 25, 30, 4)  # Sculpted glacier-silver side bevel
    fill_sym_box(grid, 0, 2, 15, 16, 25, 25, 4)
    # Glowing Glacial Ice-Cyan Polar Core in center chest
    fill_sym_box(grid, 0, 1, 16, 16, 28, 29, 8)
    fill_sym_box(grid, 0, 1, 16, 16, 27, 27, 4)
    fill_sym_box(grid, 2, 2, 16, 16, 28, 29, 5)  # Golden core frame accents

    # Iconic Warm Golden-Yellow Emperor Collar Markings (sweeping around neck & upper chest!)
    fill_sym_box(grid, 0, 4, 12, 15, 31, 32, 5)
    fill_sym_box(grid, 0, 2, 15, 16, 30, 31, 5)
    fill_sym_box(grid, 3, 5, 11, 14, 31, 32, 5)
    fill_sym_box(grid, 4, 5, 12, 14, 32, 33, 6)  # Warm orange collar flare tips
    fill_sym_box(grid, 2, 3, 10, 12, 32, 33, 5)  # High emperor collar guards

    # --- SLEEK BLACK PENGUIN BACK-SHELL / POLAR BACKPACK (Y: 4..8, Z: 23..33) ---
    # Rounded glossy charcoal shell directly evoking Form A's emperor back
    fill_sym_box(grid, 0, 4, 6, 8, 24, 31, 1)
    fill_sym_box(grid, 0, 3, 5, 6, 25, 30, 1)
    fill_sym_box(grid, 0, 2, 5, 5, 25, 30, 2)  # Slate-blue-grey mantle stripe down center back
    fill_sym_box(grid, 0, 3, 7, 8, 32, 32, 2)
    # Twin Polar Cryo-Thrusters mounted on back-shell
    fill_sym_box(grid, 2, 3, 4, 5, 25, 29, 9)
    fill_sym_box(grid, 2, 3, 4, 4, 25, 26, 8)  # Glowing ice-cyan thruster vents
    fill_sym_box(grid, 3, 4, 6, 7, 30, 33, 1)  # Upper dorsal snow-fins
    fill_sym_box(grid, 4, 4, 5, 6, 31, 34, 2)
    fill_sym_box(grid, 4, 4, 5, 5, 33, 34, 8)

    # --- SHOULDERS & FLIPPER-BLADE ARMS (Z: 14..34) - DIRECTLY FORM A'S FLIPPERS! ---
    # Shoulder joint connector
    fill_sym_box(grid, 5, 6, 10, 12, 29, 31, 9)
    # Rounded Tuxedo Shoulder Pauldrons (black outer shell, white lower trim, gold stripe)
    fill_sym_box(grid, 6, 10, 9, 13, 28, 33, 1)
    fill_sym_box(grid, 7, 10, 10, 12, 33, 34, 2)  # Slate-blue pauldron crest
    fill_sym_box(grid, 10, 10, 9, 13, 27, 32, 1)
    fill_sym_box(grid, 10, 10, 10, 12, 28, 31, 2)
    fill_sym_box(grid, 7, 9, 13, 14, 30, 31, 5)   # Golden-yellow shoulder patch
    fill_sym_box(grid, 6, 9, 13, 13, 28, 29, 3)   # Crisp white lower trim

    # Articulated Upper Arms
    fill_sym_box(grid, 7, 8, 10, 12, 23, 27, 9)
    fill_sym_box(grid, 7, 8, 12, 13, 24, 26, 3)
    fill_sym_box(grid, 8, 8, 10, 11, 24, 26, 1)

    # Agile Flipper-Fin Forearms (white inner arm + sweeping black penguin flipper blade + cyan edge!)
    fill_sym_box(grid, 7, 9, 9, 13, 16, 22, 3)    # Crisp white inner forearm
    fill_sym_box(grid, 7, 8, 13, 14, 17, 21, 4)   # Glacier-silver forearm cuff
    fill_sym_box(grid, 9, 10, 9, 13, 16, 23, 1)   # Glossy charcoal outer flipper casing
    # Sweeping Penguin Flipper Fin-Blade along outer arm
    fill_sym_box(grid, 10, 11, 8, 13, 17, 24, 1)
    fill_sym_box(grid, 11, 11, 8, 12, 15, 22, 1)
    fill_sym_box(grid, 11, 12, 9, 12, 15, 20, 2)  # Slate-blue blade bevel
    fill_sym_box(grid, 12, 12, 10, 13, 14, 19, 8) # Glowing glacial cryo-edge along flipper fin!
    fill_sym_box(grid, 10, 11, 11, 13, 14, 16, 1) # Lower tapered flipper tip
    fill_sym_box(grid, 11, 11, 12, 13, 13, 14, 8) # Glowing tip

    # Articulated Mecha Fists
    fill_sym_box(grid, 7, 8, 10, 12, 14, 15, 1)
    fill_sym_box(grid, 7, 8, 12, 12, 14, 15, 9)

    # Right-hand Polar Flipper-Lance (X > center, extending forward along +Y)
    # Mounted cleanly to right fist (x=23..24)
    fill_box(grid, 23, 24, 13, 16, 14, 15, 9)     # Guard & grip
    fill_box(grid, 23, 24, 14, 15, 16, 16, 6)     # Orange pommel accent
    fill_box(grid, 23, 24, 16, 20, 14, 15, 1)     # Charcoal flipper blade spine
    fill_box(grid, 24, 24, 16, 21, 14, 15, 8)     # Glowing ice-cyan lance edge
    fill_box(grid, 23, 24, 21, 22, 14, 14, 8)     # Sharp blade point

    # --- HEROIC EMPEROR HELMET WITH ICONIC BEAK CREST (Z: 33..41) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 9)
    # Glossy charcoal-black penguin helmet dome
    fill_sym_box(grid, 0, 2, 9, 14, 34, 39, 1)
    fill_sym_box(grid, 0, 3, 10, 13, 35, 38, 1)
    fill_sym_box(grid, 0, 2, 9, 13, 39, 40, 1)
    fill_sym_box(grid, 0, 1, 9, 13, 40, 40, 2)    # Slate-blue crown ridge
    # Crisp snow-white faceplate & chin guard
    fill_sym_box(grid, 0, 1, 14, 15, 34, 35, 3)
    fill_sym_box(grid, 0, 0, 15, 15, 34, 34, 6)   # Small orange chin accent
    # Warm golden-yellow emperor cheek/ear panels!
    fill_sym_box(grid, 3, 3, 10, 13, 35, 37, 5)
    fill_sym_box(grid, 3, 3, 11, 12, 37, 38, 6)   # Orange upper ear-fin highlight
    # Glowing Glacial Ice-Cyan Heroic Visor
    fill_sym_box(grid, 0, 2, 14, 15, 36, 36, 8)
    fill_sym_box(grid, 2, 2, 13, 14, 36, 36, 8)

    # ICONIC ORANGE PENGUIN BEAK VISOR-BROW & CREST EMBLEM!
    # V-shaped orange brow curving over the glowing cyan visor
    fill_sym_box(grid, 0, 2, 14, 15, 37, 37, 6)
    fill_sym_box(grid, 2, 3, 13, 14, 37, 38, 6)   # Swept-back orange brow fins
    # Forward-jutting sculpted Emperor Penguin Beak Crest!
    fill_sym_box(grid, 0, 1, 15, 16, 37, 38, 6)
    fill_sym_box(grid, 0, 0, 17, 18, 37, 38, 6)   # Iconic beak point facing +Y
    fill_sym_box(grid, 0, 0, 18, 19, 37, 37, 7)   # Tip bevel
    # Swept forehead crest ridge rising onto crown
    fill_sym_box(grid, 0, 0, 13, 16, 39, 40, 6)
    fill_sym_box(grid, 0, 0, 11, 14, 41, 41, 5)   # Golden-yellow crest highlight

    # Hollow unseen torso core if needed to keep Form B cleanly within target range
    hollow_interior(grid, 24, 31)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=36, pitch_a=20, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "penguin_a.vox")
    v_b = export_vox(model_b, "penguin_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: EMPEROR PENGUIN -> PENGUIN POLAR ROBOT",
        "1. EMPEROR PENGUIN",
        "2. PENGUIN POLAR ROBOT",
        "preview_penguin.png",
        yaw_a=36, pitch_a=20, yaw_b=32, pitch_b=20,
    )
    print(f"penguin: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
