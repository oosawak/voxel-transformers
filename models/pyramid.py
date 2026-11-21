import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (224, 194, 134, 255),  # Warm Desert Limestone / Sandstone
    2: (184, 146, 86, 255),   # Shaded Ochre Stone Blocks
    3: (128, 96, 56, 255),    # Dark Mortar / Weathered Stone Masonry
    4: (246, 202, 54, 255),   # Radiant Golden Pyramidion Capstone & Pharaoh Gold
    5: (34, 72, 168, 255),    # Royal Lapis-Lazuli Blue Egyptian Trim
    6: (46, 232, 224, 255),   # Glowing Turquoise / Cyan Eye-of-Horus Visor & Runes
    7: (38, 36, 44, 255),     # Deep Obsidian / Charcoal Inner Frame & Temple Entrance
    8: (244, 224, 174, 255),  # Warm Desert Sand Highlight
    9: (196, 48, 52, 255),    # Crimson / Carnelian Jewel Accent
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


def fill_pyramid_course(grid, r, z, hollow_r=None):
    """Fill a horizontal sandstone pyramid tier with realistic stone block masonry variation."""
    X, Y, _ = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    cy_l, cy_r = Y // 2 - 1, Y // 2
    x0, x1 = cx_l - r, cx_r + r
    y0, y1 = cy_l - r, cy_r + r

    fill_box(grid, x0, x1, y0, y1, z, z, 1)
    if hollow_r is not None and hollow_r >= 0:
        fill_box(grid, cx_l - hollow_r, cx_r + hollow_r, cy_l - hollow_r, cy_r + hollow_r, z, z, 0)

    # Realistic coursed limestone block masonry variation (2-voxel wide stone blocks)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            if grid[x, y, z] == 0:
                continue
            dx = min(abs(x - x0), abs(x1 - x))
            dy = min(abs(y - y0), abs(y1 - y))
            if dx == 0 or dy == 0 or dx == 1 or dy == 1:
                bx = (x + (z % 2)) // 2
                by = (y + ((z + 1) % 2)) // 2
                h = (bx * 3 + by * 5 + z * 7) % 10
                if h in (0, 4, 7):
                    grid[x, y, z] = 2
                elif h == 2 and (dx == 0 or dy == 0):
                    grid[x, y, z] = 3
                elif h in (6, 9) and (dx == 0 or dy == 0):
                    grid[x, y, z] = 8


# ==========================================
# FORM A: GREAT STEPPED PYRAMID (28 x 28 x 21)
# ==========================================
def build_a():
    grid = np.zeros((28, 28, 21), dtype=np.uint8)

    # --- STEPPED LIMESTONE PYRAMID BODY (Z: 0..13) ---
    # Alternating 2-voxel and 1-voxel courses for classic Giza / stepped-stone majesty
    # Hollow interior keeps voxel count clean while preserving full 6-connected overlap between steps
    courses = [
        (0, 12, 10),
        (1, 12, 10),
        (2, 11, 9),
        (3, 10, 8),
        (4, 10, 8),
        (5, 9, 7),
        (6, 8, 6),
        (7, 8, 6),
        (8, 7, 5),
        (9, 6, 4),
        (10, 6, 4),
        (11, 5, 3),
        (12, 4, 2),
        (13, 4, 2),
    ]
    for z, r, hr in courses:
        fill_pyramid_course(grid, r, z, hollow_r=hr)

    # Corner stone highlight ridges running up the 4 diagonal edges of the pyramid
    X, Y, _ = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    cy_l, cy_r = Y // 2 - 1, Y // 2
    for z, r, _ in courses:
        if z <= 12:
            for sx in (cx_l - r, cx_r + r):
                for sy in (cy_l - r, cy_r + r):
                    grid[sx, sy, z] = 8 if z % 2 == 0 else 2

    # --- ROYAL LAPIS-LAZULI & GOLD CEREMONIAL COLLAR BAND (Z: 13..14) ---
    # Sits right below the gleaming golden pyramidion capstone
    fill_box(grid, cx_l - 4, cx_r + 4, cy_l - 4, cy_r + 4, 13, 13, 5)
    fill_box(grid, cx_l - 2, cx_r + 2, cy_l - 2, cy_r + 2, 13, 13, 0)
    # Gold corner blocks & alternating gold inlays on lapis band
    for sx in (cx_l - 4, cx_r + 4):
        for sy in (cy_l - 4, cy_r + 4):
            grid[sx, sy, 13] = 4
    fill_sym_box(grid, 0, 1, cy_r + 4, cy_r + 4, 13, 13, 4)
    fill_sym_box(grid, 0, 1, cy_l - 4, cy_l - 4, 13, 13, 4)
    fill_sym_box(grid, 4, 4, cy_l, cy_r, 13, 13, 4)
    # Glowing cyan Eye-of-Horus rune jewels centered on front/back of lapis collar
    fill_sym_box(grid, 0, 0, cy_r + 4, cy_r + 4, 13, 13, 6)
    fill_sym_box(grid, 0, 0, cy_l - 4, cy_l - 4, 13, 13, 6)

    # --- GLEAMING GOLDEN PYRAMIDION CAPSTONE (Z: 14..19) ---
    fill_box(grid, cx_l - 3, cx_r + 3, cy_l - 3, cy_r + 3, 14, 14, 4)
    fill_box(grid, cx_l - 1, cx_r + 1, cy_l - 1, cy_r + 1, 14, 14, 0)  # Hollow core
    fill_box(grid, cx_l - 2, cx_r + 2, cy_l - 2, cy_r + 2, 15, 16, 4)
    fill_box(grid, cx_l - 1, cx_r + 1, cy_l - 1, cy_r + 1, 17, 17, 4)
    fill_box(grid, cx_l, cx_r, cy_l, cy_r, 18, 19, 4)
    # Subtle warm sunlit highlight corners along the golden pyramidion edges
    for z_g, r_g in ((14, 3), (16, 2), (17, 1)):
        for sx in (cx_l - r_g, cx_r + r_g):
            for sy in (cy_l - r_g, cy_r + r_g):
                grid[sx, sy, z_g] = 8

    # --- CEREMONIAL FRONT TEMPLE ENTRANCE GATEWAY (+Y, Y: 24..27, Z: 0..6) ---
    # Flanking sandstone & gold-capped pylon pillars projecting cleanly from front slope
    fill_sym_box(grid, 2, 3, 25, 27, 0, 4, 1)
    fill_sym_box(grid, 3, 3, 26, 27, 0, 3, 2)
    fill_sym_box(grid, 2, 3, 25, 27, 5, 5, 4)    # Golden pylon cornice
    fill_sym_box(grid, 2, 2, 27, 27, 1, 3, 5)    # Lapis vertical hieroglyph strips
    fill_sym_box(grid, 2, 2, 27, 27, 2, 2, 6)    # Glowing turquoise rune dots
    # Temple entrance lintel & winged sun-disc crest
    fill_sym_box(grid, 0, 3, 25, 26, 4, 5, 1)
    fill_sym_box(grid, 0, 2, 26, 27, 4, 4, 5)    # Lapis lintel frieze
    fill_sym_box(grid, 0, 2, 26, 27, 5, 5, 4)    # Golden winged sun lintel
    fill_sym_box(grid, 0, 0, 27, 27, 5, 5, 9)    # Crimson carnelian solar jewel
    fill_sym_box(grid, 0, 1, 25, 26, 6, 6, 4)    # Stepped golden pediment cap
    # Dark obsidian recessed temple doorway (with solid obsidian back wall so interior is sealed!)
    fill_sym_box(grid, 0, 1, 23, 26, 0, 3, 7)
    fill_sym_box(grid, 0, 1, 26, 27, 0, 3, 0)    # Carved dark entrance recess
    fill_sym_box(grid, 0, 1, 25, 25, 0, 3, 7)    # Deep obsidian sanctuary portal
    fill_sym_box(grid, 0, 1, 26, 27, 0, 0, 3)    # Weathered entrance threshold step
    fill_sym_box(grid, 0, 0, 25, 25, 2, 2, 6)    # Faint inner turquoise temple glow

    # --- REAR CEREMONIAL NICHE (-Y, Y: 0..3, Z: 0..4) ---
    fill_sym_box(grid, 2, 2, 0, 2, 0, 3, 2)
    fill_sym_box(grid, 0, 2, 1, 2, 4, 4, 4)
    fill_sym_box(grid, 0, 1, 1, 2, 0, 3, 7)
    fill_sym_box(grid, 0, 1, 1, 1, 0, 2, 0)
    fill_sym_box(grid, 0, 1, 2, 2, 0, 3, 7)
    fill_sym_box(grid, 0, 0, 1, 1, 4, 4, 5)

    return grid


# ==========================================
# FORM B: PHARAOH-GUARDIAN PYRAMID ROBOT (36 x 22 x 44)
# ==========================================
def build_b():
    grid = np.zeros((36, 22, 44), dtype=np.uint8)
    X = grid.shape[0]
    cx_l, cx_r = X // 2 - 1, X // 2

    # --- FEET / STEPPED STONE PLINTH BOOTS (Z: 0..4) ---
    # Heavy terraced pyramid-base soles
    fill_sym_box(grid, 3, 7, 7, 16, 0, 1, 2)
    fill_sym_box(grid, 4, 6, 16, 17, 0, 1, 1)    # Stepped sandstone toes
    fill_sym_box(grid, 3, 7, 7, 8, 0, 1, 3)      # Weathered heel block
    fill_sym_box(grid, 3, 6, 8, 15, 2, 3, 1)     # Upper stepped foot tier
    fill_sym_box(grid, 4, 6, 14, 16, 2, 2, 8)    # Sand highlight toe ledge
    fill_sym_box(grid, 5, 5, 15, 16, 2, 2, 4)    # Golden toe emblem
    fill_sym_box(grid, 4, 6, 9, 14, 4, 4, 7)     # Obsidian ankle joint ring
    fill_sym_box(grid, 4, 6, 14, 15, 3, 4, 5)    # Lapis ankle guard
    fill_sym_box(grid, 5, 5, 15, 15, 4, 4, 4)

    # --- LOWER LEGS / STEPPED PYRAMID PILLAR SHINS (Z: 5..14) ---
    # Broad stepped limestone leg blocks stepping slightly inward from ankle to knee
    for z in range(5, 15):
        outer_x = 7 if z <= 8 else 6
        fill_sym_box(grid, 3, outer_x, 9, 13, z, z, 1)
        # Masonry stone block variation along outer leg faces
        for dx in range(3, outer_x + 1):
            for y in (9, 13):
                if (dx * 3 + y * 2 + z * 5) % 5 == 0:
                    grid[cx_l - dx, y, z] = 2
                    grid[cx_r + dx, y, z] = 2
                elif (dx + y + z) % 7 == 0:
                    grid[cx_l - dx, y, z] = 8
                    grid[cx_r + dx, y, z] = 8
        # Outer side masonry
        for y in range(9, 14):
            if (y + z) % 3 == 0:
                grid[cx_l - outer_x, y, z] = 2
                grid[cx_r + outer_x, y, z] = 2
            elif (y + z) % 5 == 0:
                grid[cx_l - outer_x, y, z] = 3
                grid[cx_r + outer_x, y, z] = 3
    # Hollow unseen shin interior to keep voxel count sleek
    fill_sym_box(grid, 4, 5, 10, 12, 6, 12, 0)
    # Stepped horizontal sandstone trim band & lapis shin stripe
    fill_sym_box(grid, 4, 5, 13, 14, 6, 11, 5)   # Royal lapis vertical shin panel
    fill_sym_box(grid, 5, 5, 14, 14, 7, 10, 4)   # Gold center strip
    fill_sym_box(grid, 5, 5, 14, 14, 8, 9, 6)    # Glowing cyan hieroglyph rune
    # Outer stepped pyramid fin on calf
    fill_sym_box(grid, 7, 8, 10, 12, 5, 7, 2)
    fill_sym_box(grid, 7, 7, 10, 12, 8, 10, 4)
    # Stepped Pharaoh Knee Armor (Z: 12..15)
    fill_sym_box(grid, 3, 6, 13, 15, 12, 14, 1)
    fill_sym_box(grid, 4, 5, 15, 15, 12, 15, 4)  # Gold stepped knee plate
    fill_sym_box(grid, 4, 5, 15, 15, 13, 14, 9)  # Carnelian scarab jewel
    fill_sym_box(grid, 4, 5, 14, 14, 15, 15, 8)  # Sandstone knee cap ridge

    # --- THIGHS (Z: 15..19) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 19, 7)   # Obsidian inner mecha thigh frame
    fill_sym_box(grid, 3, 5, 12, 13, 16, 19, 1)  # Front sandstone thigh armor
    fill_sym_box(grid, 5, 5, 10, 12, 16, 19, 2)  # Side ochre armor
    fill_sym_box(grid, 4, 4, 13, 13, 17, 18, 5)  # Lapis inlay
    fill_sym_box(grid, 3, 5, 9, 10, 16, 18, 2)   # Rear thigh sandstone plates

    # --- WAIST / PHARAOH SHENDYT SKIRT (Z: 18..23) ---
    fill_sym_box(grid, 0, 4, 9, 13, 20, 23, 7)   # Obsidian pelvis & waist frame
    # Golden Pharaoh belt with lapis & carnelian buckle
    fill_sym_box(grid, 0, 4, 13, 14, 21, 22, 4)
    fill_sym_box(grid, 0, 4, 8, 9, 21, 22, 4)
    fill_sym_box(grid, 2, 3, 14, 14, 21, 21, 5)
    fill_sym_box(grid, 0, 0, 14, 15, 21, 22, 9)  # Carnelian waist gem
    # Hanging royal Shendyt front apron (gold + lapis + glowing turquoise rune)
    fill_sym_box(grid, 0, 1, 14, 15, 17, 20, 4)
    fill_sym_box(grid, 0, 0, 15, 15, 18, 20, 5)
    fill_sym_box(grid, 0, 0, 15, 15, 19, 19, 6)
    fill_sym_box(grid, 2, 3, 14, 14, 19, 20, 1)  # Flanked sandstone skirt blocks
    fill_sym_box(grid, 2, 3, 14, 14, 18, 18, 8)
    # Stepped pyramid-block side hip tassets
    fill_sym_box(grid, 5, 6, 9, 13, 18, 21, 1)
    fill_sym_box(grid, 6, 6, 9, 13, 18, 19, 2)
    fill_sym_box(grid, 5, 6, 10, 12, 21, 21, 4)
    fill_sym_box(grid, 6, 6, 11, 11, 19, 20, 5)

    # --- TORSO / CHEST (Z: 23..32) - Unfolded Stepped Pyramid Chest Armor ---
    # Lower stepped sandstone abdomen stepping outward into broad tiered chest!
    fill_sym_box(grid, 0, 4, 9, 13, 23, 26, 1)
    fill_sym_box(grid, 0, 5, 9, 14, 27, 31, 1)
    # Hollow unseen torso core
    fill_sym_box(grid, 0, 3, 10, 12, 24, 30, 0)
    # Stepped sandstone masonry courses on abdomen & torso sides
    fill_sym_box(grid, 0, 3, 13, 14, 23, 25, 2)
    fill_sym_box(grid, 0, 2, 14, 14, 24, 25, 7)  # Obsidian ab vents
    fill_sym_box(grid, 1, 1, 14, 14, 24, 25, 4)  # Gold ab ribs
    fill_sym_box(grid, 5, 5, 9, 13, 27, 29, 2)
    fill_sym_box(grid, 5, 5, 9, 13, 30, 31, 8)
    # Prominent tiered sandstone chest armor plates (stepping forward like pyramid courses!)
    fill_sym_box(grid, 0, 4, 14, 15, 26, 31, 1)
    fill_sym_box(grid, 2, 4, 15, 16, 27, 30, 1)  # Outer stepped pectoral blocks
    fill_sym_box(grid, 3, 4, 16, 16, 27, 27, 8)  # Sand highlight step edge
    fill_sym_box(grid, 2, 4, 16, 16, 28, 28, 2)  # Ochre step course
    # Iconic Egyptian Usekh Broad Collar (alternating Gold, Lapis, Turquoise rows!)
    fill_sym_box(grid, 0, 4, 14, 16, 29, 29, 5)  # Royal lapis collar band
    fill_sym_box(grid, 0, 4, 14, 16, 30, 30, 4)  # Radiant gold collar band
    fill_sym_box(grid, 0, 3, 14, 15, 31, 31, 5)  # Upper lapis collar
    fill_sym_box(grid, 2, 3, 16, 16, 29, 29, 6)  # Glowing turquoise chest inlays
    # Central Pyramid / Eye-of-Horus Chest Core (Z: 26..30)
    fill_sym_box(grid, 0, 1, 15, 16, 26, 30, 4)  # Golden bezel
    fill_sym_box(grid, 0, 1, 16, 16, 27, 29, 7)  # Obsidian inner temple frame
    fill_sym_box(grid, 0, 0, 16, 16, 28, 29, 6)  # Glowing cyan Eye-of-Horus core!
    fill_sym_box(grid, 0, 0, 16, 16, 27, 27, 9)  # Crimson carnelian jewel
    # Upper shoulder/collar deck
    fill_sym_box(grid, 0, 4, 9, 13, 32, 32, 4)

    # --- BACKPACK (Y: 5..8, Z: 23..32) - Folded Rear Pyramid Slope Panels ---
    # Clearly reads as folded stepped pyramid masonry from the rear!
    fill_sym_box(grid, 0, 4, 7, 8, 24, 31, 1)
    fill_sym_box(grid, 0, 3, 6, 7, 25, 30, 2)
    fill_sym_box(grid, 0, 2, 5, 6, 26, 29, 1)
    fill_sym_box(grid, 0, 1, 5, 5, 27, 28, 4)    # Central golden rear pyramid crest
    fill_sym_box(grid, 0, 0, 5, 5, 27, 28, 6)    # Glowing cyan rear rune
    fill_sym_box(grid, 0, 3, 6, 6, 30, 30, 5)    # Rear lapis band
    fill_sym_box(grid, 0, 3, 6, 6, 31, 31, 8)    # Rear sand ledge highlight
    # Twin sun-thrusters at base of backpack
    fill_sym_box(grid, 2, 3, 5, 7, 23, 25, 7)
    fill_sym_box(grid, 2, 3, 5, 5, 23, 23, 4)
    fill_sym_box(grid, 2, 2, 6, 6, 23, 23, 6)

    # --- STEPPED PYRAMID SHOULDER PAULDRONS (Z: 28..35) ---
    # Solid obsidian shoulder joint connecting into torso
    fill_sym_box(grid, 5, 7, 10, 12, 28, 31, 7)
    # 3-Tier Stepped Sandstone Pyramid Shoulder Pauldrons!
    # Tier 1 (base step)
    fill_sym_box(grid, 6, 10, 8, 14, 29, 31, 1)
    fill_sym_box(grid, 10, 10, 8, 14, 29, 30, 2)
    fill_sym_box(grid, 6, 10, 14, 14, 29, 29, 5)  # Lapis front pauldron trim
    fill_sym_box(grid, 6, 10, 8, 8, 29, 29, 5)    # Lapis rear pauldron trim
    fill_sym_box(grid, 8, 8, 14, 14, 30, 30, 6)   # Turquoise pauldron rune
    # Tier 2 (middle pyramid step)
    fill_sym_box(grid, 6, 9, 9, 13, 32, 33, 2)
    fill_sym_box(grid, 6, 9, 13, 13, 32, 32, 8)
    fill_sym_box(grid, 9, 9, 9, 13, 32, 32, 8)
    # Tier 3 (golden pyramidion shoulder apex!)
    fill_sym_box(grid, 7, 8, 10, 12, 34, 34, 4)
    fill_sym_box(grid, 7, 7, 11, 11, 35, 35, 4)

    # --- ARMS (Z: 15..29) ---
    # Upper arms (x_off: 7..9)
    fill_sym_box(grid, 7, 9, 10, 12, 24, 28, 7)
    fill_sym_box(grid, 7, 9, 10, 12, 25, 27, 1)
    fill_sym_box(grid, 9, 9, 10, 12, 26, 27, 2)
    fill_sym_box(grid, 7, 9, 10, 12, 24, 24, 4)  # Golden Pharaoh armband

    # LEFT ARM (-X side, x = 8..10) + Pyramid-Faceted Sandstone & Gold Buckler Shield
    fill_box(grid, 8, 10, 10, 13, 17, 23, 1)
    fill_box(grid, 8, 8, 10, 13, 18, 22, 2)
    fill_box(grid, 8, 10, 10, 13, 17, 18, 5)     # Lapis wrist cuff
    fill_box(grid, 8, 10, 13, 13, 18, 18, 4)     # Gold wrist trim
    fill_box(grid, 8, 10, 10, 12, 15, 16, 7)     # Left obsidian fist
    # Stepped Egyptian Pyramid Buckler Shield mounted on outer left forearm (x = 5..7)
    fill_box(grid, 7, 7, 9, 14, 16, 23, 4)       # Gold shield rim
    fill_box(grid, 6, 7, 10, 13, 17, 22, 1)      # Stepped sandstone face
    fill_box(grid, 6, 6, 10, 13, 17, 17, 5)      # Lapis lower inlay
    fill_box(grid, 6, 6, 10, 13, 22, 22, 5)      # Lapis upper inlay
    fill_box(grid, 5, 5, 11, 12, 18, 21, 4)      # Raised golden pyramid boss
    fill_box(grid, 5, 5, 11, 12, 19, 20, 6)      # Glowing Eye-of-Horus shield core

    # RIGHT ARM (+X side, x = 25..33) - Extended outward to wield Golden Ankh-Khopesh Staff
    fill_box(grid, 25, 27, 10, 13, 19, 23, 1)
    fill_box(grid, 27, 27, 11, 12, 20, 22, 2)
    fill_box(grid, 26, 30, 10, 13, 18, 20, 1)    # Forearm angled outward
    fill_box(grid, 29, 31, 10, 13, 18, 20, 5)    # Lapis wrist cuff
    fill_box(grid, 29, 30, 13, 13, 18, 20, 4)    # Gold cuff band
    # Right obsidian fist gripping staff shaft at x=31..33, y=11..13
    fill_box(grid, 31, 33, 11, 13, 17, 19, 7)
    fill_box(grid, 32, 33, 13, 13, 17, 18, 4)

    # --- GOLDEN ANKH-KHOPESH PHARAOH STAFF (+X side at x=33, y=12, cleanly clear of shoulder!) ---
    # Obsidian & gold ringed scepter shaft
    fill_box(grid, 33, 33, 12, 12, 3, 33, 7)
    fill_box(grid, 33, 33, 12, 12, 2, 4, 4)      # Bottom gold finial
    fill_box(grid, 33, 33, 12, 12, 15, 16, 4)
    fill_box(grid, 33, 33, 12, 12, 20, 21, 4)
    fill_box(grid, 33, 33, 12, 12, 30, 32, 4)
    fill_box(grid, 33, 33, 12, 12, 31, 31, 5)    # Lapis collar ring
    # Golden Ankh crossbar & glowing turquoise Ankh loop (Z: 33..41)
    fill_box(grid, 31, 35, 12, 12, 33, 33, 4)    # Ankh horizontal arms
    fill_box(grid, 31, 31, 12, 12, 34, 34, 5)    # Lapis wing tips
    fill_box(grid, 35, 35, 12, 12, 34, 34, 5)
    fill_box(grid, 33, 33, 12, 12, 34, 35, 9)    # Carnelian jewel heart
    # Radiant Golden Ankh Loop + Sickle-Khopesh Energy Crest
    fill_box(grid, 32, 34, 12, 12, 35, 35, 4)
    fill_box(grid, 31, 32, 12, 12, 36, 39, 4)    # Left arc of Ankh loop
    fill_box(grid, 34, 35, 12, 12, 36, 39, 4)    # Right arc of Ankh loop
    fill_box(grid, 32, 34, 12, 12, 40, 41, 4)    # Top of Ankh loop
    fill_box(grid, 33, 33, 12, 12, 42, 42, 4)    # Solar apex tip
    fill_box(grid, 33, 33, 12, 12, 36, 39, 6)    # Glowing turquoise energy crystal inside Ankh!

    # --- HEAD (Z: 32..43) - GOLDEN PYRAMIDION CAPSTONE PHARAOH HEAD! ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 7)
    # Pharaoh Nemes Headdress Side Flaps (striking royal lapis & gold horizontal stripes!)
    fill_sym_box(grid, 2, 3, 9, 13, 32, 36, 5)
    fill_sym_box(grid, 2, 3, 9, 13, 33, 33, 4)
    fill_sym_box(grid, 2, 3, 9, 13, 35, 35, 4)
    fill_sym_box(grid, 3, 3, 9, 12, 32, 34, 4)   # Flared lower Nemes wing tips
    fill_sym_box(grid, 3, 3, 9, 12, 33, 33, 5)
    # Obsidian Faceplate + Bold Glowing Turquoise Eye-of-Horus Visor + Pharaoh Chin Beard
    fill_sym_box(grid, 0, 1, 9, 14, 33, 36, 7)
    fill_sym_box(grid, 0, 1, 14, 15, 35, 35, 6)  # Bold glowing turquoise Eye-of-Horus visor!
    fill_sym_box(grid, 0, 0, 14, 14, 33, 34, 4)  # Iconic golden Pharaoh chin beard!
    fill_sym_box(grid, 0, 0, 14, 14, 32, 32, 5)  # Lapis beard tip
    # Rear Nemes tail draping down back of head
    fill_sym_box(grid, 0, 1, 8, 9, 32, 35, 5)
    fill_sym_box(grid, 0, 1, 8, 8, 33, 33, 4)
    fill_sym_box(grid, 0, 1, 8, 8, 35, 35, 4)

    # THE GLEAMING GOLDEN PYRAMIDION CAPSTONE CROWN (Z: 36..43)!
    # Matches Form A's exact stepped golden pyramidion apex right on top of the robot's head!
    # Step 1 (8x6 base brim, Z: 36..37) - cleanly framing the glowing cyan visor below!
    fill_sym_box(grid, 0, 3, 8, 14, 36, 37, 4)
    fill_sym_box(grid, 1, 3, 14, 14, 36, 36, 5)  # Royal lapis brow trim
    fill_sym_box(grid, 0, 0, 15, 15, 37, 38, 4)  # Golden Uraeus cobra crest (above visor!)
    fill_sym_box(grid, 0, 0, 15, 15, 37, 37, 9)  # Crimson carnelian Uraeus jewel
    # Step 2 (6x5 golden pyramidion tier, Z: 38..39)
    fill_sym_box(grid, 0, 2, 9, 13, 38, 39, 4)
    fill_sym_box(grid, 2, 2, 9, 13, 38, 38, 5)   # Subtle lapis pyramidion trim
    # Step 3 (4x3 golden tier, Z: 40..41)
    fill_sym_box(grid, 0, 1, 10, 12, 40, 41, 4)
    # Step 4 (2x2 gleaming golden apex peak, Z: 42..43)
    fill_sym_box(grid, 0, 0, 11, 12, 42, 43, 4)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=24, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "pyramid_a.vox")
    v_b = export_vox(model_b, "pyramid_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: GREAT PYRAMID -> PHARAOH-GUARDIAN ROBOT",
        "1. GREAT STEPPED PYRAMID",
        "2. PHARAOH-GUARDIAN ROBOT",
        "preview_pyramid.png",
        yaw_a=36, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"pyramid: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
