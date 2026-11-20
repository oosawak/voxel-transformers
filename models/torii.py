import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (222, 48, 34, 255),    # Vibrant Shinto Vermilion Red (Shu-iro)
    2: (150, 26, 22, 255),    # Deep Crimson Lacquer Shading
    3: (34, 36, 44, 255),     # Obsidian Black Roof Cap / Plaque / Nemaki
    4: (112, 118, 130, 255),  # Shrine Granite Stone Grey / Steel
    5: (240, 192, 58, 255),   # Sacred Imperial Gold Trim / Plaque Emblem
    6: (196, 156, 88, 255),   # Braided Shimenawa Hemp Rope Straw
    7: (245, 243, 236, 255),  # Pure White Paper Shide / Armor Accents
    8: (58, 226, 174, 255),   # Sacred Jade Glow (Visor / Spirit Core)
    9: (64, 68, 82, 255),     # Dark Iron Wedges / Mecha Frame Joints
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


def fill_sym_oct_pillar(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill a chamfered octagonal vertical pillar symmetrically in X."""
    fill_sym_box(grid, x_off0 + 1, x_off1 - 1, y0, y1, z0, z1, col)
    fill_sym_box(grid, x_off0, x_off1, y0 + 1, y1 - 1, z0, z1, col)


# ==========================================
# FORM A: SHINTO TORII GATE (36 x 10 x 34)
# ==========================================
def build_a():
    grid = np.zeros((36, 10, 34), dtype=np.uint8)

    # --- GRANITE STONE PLINTH (Kamebara) & BLACK NEMAKI BASES (Z: 0..5) ---
    fill_sym_oct_pillar(grid, 6, 11, 2, 7, 0, 1, 4)
    fill_sym_oct_pillar(grid, 6, 11, 2, 7, 2, 2, 9)
    fill_sym_oct_pillar(grid, 6, 11, 2, 7, 3, 4, 3)
    fill_sym_oct_pillar(grid, 7, 10, 3, 6, 5, 5, 3)
    # Gold collar accents on front/back of nemaki top
    fill_sym_box(grid, 8, 9, 3, 3, 5, 5, 5)
    fill_sym_box(grid, 8, 9, 6, 6, 5, 5, 5)

    # --- TWIN MAIN PILLARS (Hashira) (Z: 6..24) ---
    fill_sym_oct_pillar(grid, 7, 10, 3, 6, 6, 23, 1)
    # Subtle deep crimson lacquer groove down outer/inner sides
    fill_sym_box(grid, 10, 10, 4, 5, 7, 17, 2)
    fill_sym_box(grid, 7, 7, 4, 5, 7, 17, 2)
    # Upper black Daiwa collar rings right under the shimaki (Z: 24)
    fill_sym_box(grid, 7, 10, 3, 6, 24, 24, 3)
    fill_sym_box(grid, 8, 9, 3, 3, 24, 24, 5)
    fill_sym_box(grid, 8, 9, 6, 6, 24, 24, 5)

    # --- LOWER TIE BEAM (Nuki) & BLACK KUSABI WEDGES (Z: 18..20) ---
    fill_sym_box(grid, 0, 13, 4, 5, 18, 18, 2)
    fill_sym_box(grid, 0, 14, 4, 5, 19, 20, 1)
    fill_sym_box(grid, 14, 14, 4, 5, 19, 20, 5)
    # Black lacquered Kusabi wedges clamping the nuki at each pillar
    fill_sym_box(grid, 6, 6, 4, 5, 18, 21, 3)
    fill_sym_box(grid, 11, 11, 4, 5, 18, 21, 3)
    fill_sym_box(grid, 6, 6, 4, 5, 21, 21, 9)
    fill_sym_box(grid, 11, 11, 4, 5, 21, 21, 9)

    # --- CENTRAL PLAQUE (Gakuzuka) (Z: 20..25) ---
    # Sleek black tablet framed in imperial gold between nuki and shimaki
    fill_sym_box(grid, 0, 2, 3, 7, 20, 25, 5)
    fill_sym_box(grid, 0, 1, 3, 7, 21, 24, 3)
    # Front sacred emblem (gold calligraphy bar + central jade jewel on Y=7)
    fill_sym_box(grid, 0, 0, 7, 7, 22, 23, 5)
    fill_sym_box(grid, 0, 0, 7, 7, 23, 23, 8)
    # Rear gold trim accent (Y=3)
    fill_sym_box(grid, 0, 0, 3, 3, 22, 23, 5)

    # --- UPPER CROSSBEAM (Shimaki) & SWEEPING CURVED KASAGI LINTEL (Z: 25..33) ---
    curve_dz = [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,   # x_off 0..9
        1, 1, 1,                         # x_off 10..12
        2, 2,                            # x_off 13..14
        3, 3,                            # x_off 15..16
        4,                               # x_off 17 (dramatic upturned tips)
    ]
    for xo, dz in enumerate(curve_dz):
        if xo <= 15:
            fill_sym_box(grid, xo, xo, 3, 6, 25 + dz, 25 + dz, 2)
            fill_sym_box(grid, xo, xo, 3, 6, 26 + dz, 26 + dz, 1)
        elif xo == 16:
            fill_sym_box(grid, xo, xo, 3, 6, 26 + dz, 26 + dz, 1)

        if xo <= 16:
            fill_sym_box(grid, xo, xo, 2, 7, 27 + dz, 27 + dz, 1)
        else:
            fill_sym_box(grid, xo, xo, 3, 6, 27 + dz, 27 + dz, 1)
            fill_sym_box(grid, xo, xo, 4, 5, 27 + dz, 27 + dz, 5)

        if xo <= 16:
            fill_sym_box(grid, xo, xo, 2, 7, 28 + dz, 28 + dz, 3)
            fill_sym_box(grid, xo, xo, 3, 6, 29 + dz, 29 + dz, 3)
        else:
            fill_sym_box(grid, xo, xo, 3, 6, 28 + dz, 28 + dz, 3)
            fill_sym_box(grid, xo, xo, 4, 5, 29 + dz, 29 + dz, 5)

    # Gold trim caps at kasagi ends and central ridge highlight
    fill_sym_box(grid, 16, 16, 2, 7, 30, 30, 5)
    fill_sym_box(grid, 0, 2, 4, 5, 29, 29, 5)

    # --- BRAIDED SHIMENAWA ROPE & FOUR CRISP WHITE PAPER SHIDE ZIGZAGS (Y=6) ---
    fill_sym_box(grid, 0, 2, 6, 6, 16, 17, 6)
    fill_sym_box(grid, 3, 5, 6, 6, 17, 17, 6)
    fill_sym_box(grid, 6, 6, 5, 6, 17, 18, 6)
    # Gold braided twist accents
    fill_sym_box(grid, 0, 0, 6, 6, 17, 17, 5)
    fill_sym_box(grid, 2, 2, 6, 6, 16, 16, 5)
    fill_sym_box(grid, 4, 4, 6, 6, 17, 17, 5)

    # Four airy, clearly separated 6-connected White Paper Shide zigzags
    # Inner pair at x_off = 1..2, outer pair at x_off = 5..6 (clean 2-voxel gaps!)
    for sx, sz_top in ((1, 15), (5, 16)):
        fill_sym_box(grid, sx, sx, 6, 6, sz_top - 1, sz_top, 7)
        fill_sym_box(grid, sx + 1, sx + 1, 6, 6, sz_top - 2, sz_top - 1, 7)
        fill_sym_box(grid, sx, sx, 6, 6, sz_top - 3, sz_top - 2, 7)

    return grid


# ==========================================
# FORM B: TORII SHRINE GUARDIAN ROBOT (40 x 24 x 46)
# ==========================================
def build_b():
    grid = np.zeros((40, 24, 46), dtype=np.uint8)

    # --- FEET / BOOTS (Z: 0..4) - Granite Stone Plinths + Black Nemaki Boots ---
    # Commanding heroic wide stance (x_off: 3..7)
    fill_sym_box(grid, 3, 7, 8, 16, 0, 1, 4)
    fill_sym_box(grid, 4, 6, 16, 17, 0, 1, 4)  # Forward stone toes
    fill_sym_box(grid, 4, 6, 7, 8, 0, 2, 9)    # Iron heel spur
    # Black lacquered Nemaki upper boots
    fill_sym_box(grid, 4, 7, 9, 15, 2, 3, 3)
    fill_sym_box(grid, 4, 6, 15, 16, 2, 2, 3)
    fill_sym_box(grid, 5, 5, 15, 16, 2, 2, 5)  # Gold toe crest
    fill_sym_box(grid, 4, 6, 9, 14, 4, 4, 3)
    # Vermilion ankle guard front
    fill_sym_box(grid, 4, 6, 14, 15, 3, 4, 1)
    fill_sym_box(grid, 5, 5, 15, 15, 4, 4, 5)

    # --- LOWER LEGS / SHINS (Z: 5..14) - Stout Vermilion Torii Pillars ---
    fill_sym_oct_pillar(grid, 4, 7, 9, 13, 5, 14, 1)
    # Hollow unseen shin interior to keep voxel count sleek
    fill_sym_box(grid, 5, 6, 10, 12, 6, 12, 0)
    # Deep crimson pillar flutes
    fill_sym_box(grid, 7, 7, 10, 12, 6, 12, 2)
    fill_sym_box(grid, 4, 4, 10, 12, 6, 12, 2)
    # Gold ankle collar ring (recalling nemaki collar)
    fill_sym_box(grid, 5, 6, 9, 9, 5, 5, 5)
    fill_sym_box(grid, 5, 6, 13, 13, 5, 5, 5)
    # Black Kusabi wedge fins on outer calves
    fill_sym_box(grid, 7, 8, 10, 12, 10, 12, 3)
    fill_sym_box(grid, 8, 8, 11, 11, 11, 12, 5)
    # Armored samurai knee guards (Black Daiwa ring + Vermilion/Gold plate)
    fill_sym_box(grid, 4, 7, 9, 13, 13, 13, 3)
    fill_sym_box(grid, 4, 6, 14, 15, 12, 15, 1)
    fill_sym_box(grid, 5, 5, 15, 15, 13, 14, 5)
    fill_sym_box(grid, 4, 6, 14, 14, 15, 15, 3)

    # --- THIGHS (Z: 15..20) - Slight A-Stance Taper + White Hakama Armor ---
    fill_sym_box(grid, 3, 5, 10, 12, 15, 20, 9)
    # Solid knee-to-thigh bridge across A-stance step
    fill_sym_box(grid, 4, 5, 10, 12, 14, 16, 9)
    fill_sym_box(grid, 3, 5, 12, 13, 16, 19, 7)
    fill_sym_box(grid, 5, 5, 10, 12, 16, 19, 7)
    fill_sym_box(grid, 3, 3, 11, 12, 16, 19, 2)
    fill_sym_box(grid, 4, 4, 13, 13, 17, 18, 5)

    # --- WAIST / PELVIS & SHIMENAWA ROPE BELT (Z: 18..23) ---
    fill_sym_box(grid, 0, 4, 9, 13, 20, 23, 3)
    fill_sym_box(grid, 0, 3, 10, 12, 23, 23, 9)
    # Braided Shimenawa straw rope belt wrapping waist
    fill_sym_box(grid, 0, 4, 14, 14, 21, 22, 6)
    fill_sym_box(grid, 5, 5, 10, 13, 21, 22, 6)
    fill_sym_box(grid, 0, 4, 8, 8, 21, 22, 6)
    # Gold rope twist highlights
    fill_sym_box(grid, 2, 2, 14, 14, 21, 22, 5)
    fill_sym_box(grid, 4, 4, 14, 14, 22, 22, 5)
    # Center front armored groin guard (Black & Gold)
    fill_sym_box(grid, 0, 1, 14, 15, 18, 22, 3)
    fill_sym_box(grid, 1, 1, 15, 15, 18, 21, 5)
    fill_sym_box(grid, 0, 0, 15, 15, 19, 20, 1)
    # Hanging White Paper Shide zigzag tassets flanking center skirt
    fill_sym_box(grid, 2, 2, 14, 14, 19, 20, 7)
    fill_sym_box(grid, 3, 3, 14, 14, 18, 19, 7)
    fill_sym_box(grid, 2, 2, 14, 14, 17, 18, 7)
    # Side hip Kusazuri armor skirts (Vermilion + Black + Gold)
    fill_sym_box(grid, 5, 6, 9, 13, 18, 21, 1)
    fill_sym_box(grid, 6, 6, 10, 12, 19, 20, 3)
    fill_sym_box(grid, 5, 6, 10, 12, 18, 18, 5)

    # --- TORSO / CHEST (Z: 24..33) - Shrine Armor + Gakuzuka Plaque + Shimenawa ---
    fill_sym_box(grid, 0, 4, 9, 13, 24, 32, 1)
    fill_sym_box(grid, 0, 5, 9, 13, 27, 31, 1)
    # Hollow unseen torso core
    fill_sym_box(grid, 0, 2, 10, 12, 25, 30, 0)
    fill_sym_box(grid, 4, 4, 9, 12, 24, 26, 2)
    fill_sym_box(grid, 0, 4, 9, 13, 32, 32, 3)
    # Sculpted chest pectoral plates
    fill_sym_box(grid, 2, 4, 14, 15, 26, 31, 1)
    fill_sym_box(grid, 2, 4, 14, 14, 31, 31, 3)
    fill_sym_box(grid, 4, 4, 14, 15, 27, 30, 5)
    fill_sym_box(grid, 3, 3, 15, 15, 28, 29, 7)
    # Braided Shimenawa chest sash across lower chest
    fill_sym_box(grid, 0, 4, 14, 15, 24, 25, 6)
    fill_sym_box(grid, 1, 1, 15, 15, 25, 25, 5)
    fill_sym_box(grid, 3, 3, 15, 15, 24, 24, 5)
    # Iconic Gakuzuka Plaque mounted on center chest with glowing Jade core
    fill_sym_box(grid, 0, 1, 15, 16, 26, 31, 5)
    fill_sym_box(grid, 0, 0, 15, 16, 27, 30, 3)
    fill_sym_box(grid, 0, 0, 16, 16, 28, 29, 8)
    # High samurai shrine collar framing head
    fill_sym_box(grid, 2, 3, 10, 13, 33, 34, 3)
    fill_sym_box(grid, 3, 3, 11, 12, 34, 34, 5)

    # --- BACKPACK (Y: 5..8, Z: 23..35) - Folded Nuki Crossbeam & Wing-Stays ---
    fill_sym_box(grid, 0, 3, 6, 8, 24, 31, 3)
    fill_sym_box(grid, 0, 2, 6, 7, 25, 30, 1)
    fill_sym_box(grid, 0, 1, 5, 6, 26, 29, 4)
    fill_sym_box(grid, 0, 0, 5, 5, 27, 28, 5)
    # Twin spirit thrusters
    fill_sym_box(grid, 2, 3, 5, 6, 23, 25, 9)
    fill_sym_box(grid, 2, 2, 5, 5, 23, 23, 8)
    # Folded Nuki beam wing-stays jutting upward from upper back
    for i in range(4):
        fill_sym_box(grid, 3 + i, 4 + i, 6, 7, 31 + i, 32 + i, 1)
    fill_sym_box(grid, 6, 7, 6, 7, 34, 35, 3)
    fill_sym_box(grid, 7, 7, 6, 7, 35, 35, 5)
    # Rear white shide accent
    fill_sym_box(grid, 0, 0, 5, 5, 24, 25, 7)

    # --- GRAND UPTURNED KASAGI SHOULDER PAULDRONS (Z: 29..38) ---
    # Shoulder joint connecting solidly to torso
    fill_sym_box(grid, 5, 8, 10, 12, 29, 31, 9)
    # Sweeping split Kasagi lintel forming pagoda-like upturned shoulder pauldrons!
    pauldron_curve = [
        (6, 0), (7, 0),
        (8, 1), (9, 1),
        (10, 2), (11, 2),
        (12, 3), (13, 4),
    ]
    for xo, dz in pauldron_curve:
        if xo <= 11:
            fill_sym_box(grid, xo, xo, 9, 14, 30 + dz, 30 + dz, 2)
            fill_sym_box(grid, xo, xo, 9, 14, 31 + dz, 32 + dz, 1)
        elif xo == 12:
            fill_sym_box(grid, xo, xo, 9, 14, 31 + dz, 32 + dz, 1)
        else:
            fill_sym_box(grid, xo, xo, 10, 13, 31 + dz, 32 + dz, 1)
            fill_sym_box(grid, xo, xo, 11, 12, 32 + dz, 32 + dz, 5)

        if xo <= 11:
            fill_sym_box(grid, xo, xo, 8, 15, 33 + dz, 33 + dz, 3)
            fill_sym_box(grid, xo, xo, 9, 14, 34 + dz, 34 + dz, 3)
        elif xo == 12:
            fill_sym_box(grid, xo, xo, 9, 14, 33 + dz, 34 + dz, 3)
            fill_sym_box(grid, xo, xo, 10, 13, 34 + dz, 34 + dz, 5)
        else:
            fill_sym_box(grid, xo, xo, 10, 13, 33 + dz, 33 + dz, 3)
            fill_sym_box(grid, xo, xo, 11, 12, 34 + dz, 34 + dz, 5)
    # Gold edge trim & white talisman accent on front of pauldrons
    fill_sym_box(grid, 7, 9, 14, 14, 31, 32, 5)
    fill_sym_box(grid, 8, 8, 14, 14, 29, 30, 7)

    # --- SHRINE-PILLAR ARMS (Z: 15..29) ---
    # Upper arms stepped outward (x_off: 7..9) for crisp torso silhouette
    fill_sym_box(grid, 7, 9, 10, 12, 24, 29, 9)
    fill_sym_box(grid, 7, 9, 10, 12, 25, 28, 1)
    fill_sym_box(grid, 9, 9, 10, 12, 26, 27, 2)
    fill_sym_box(grid, 7, 9, 10, 12, 24, 24, 5)  # Gold elbow ring

    # LEFT ARM (-X side, x = 8..11) - Angled heroically outward with shrine buckler
    fill_box(grid, 9, 11, 10, 13, 17, 23, 1)
    fill_box(grid, 9, 9, 10, 12, 18, 22, 2)
    fill_box(grid, 9, 11, 10, 13, 17, 18, 3)     # Black daiwa wrist cuff
    fill_box(grid, 9, 9, 11, 12, 18, 21, 5)      # Outer gold bracer ridge
    fill_box(grid, 8, 10, 13, 14, 18, 21, 3)     # Compact black/gold shrine buckler
    fill_box(grid, 9, 9, 14, 14, 19, 20, 5)
    fill_box(grid, 9, 11, 10, 12, 15, 16, 9)     # Left fist

    # RIGHT ARM (+X side, x = 28..35) - Extended outward to hold halberd cleanly outside shoulder!
    fill_box(grid, 28, 30, 10, 13, 19, 23, 1)
    fill_box(grid, 30, 30, 11, 12, 20, 22, 2)
    fill_box(grid, 29, 32, 10, 13, 18, 20, 1)    # Forearm angled outward toward halberd
    fill_box(grid, 31, 33, 10, 13, 18, 20, 3)    # Black daiwa wrist cuff
    fill_box(grid, 31, 32, 13, 13, 18, 20, 5)    # Gold cuff trim
    # Right armored fist gripping halberd shaft at x=35, y=12..13
    fill_box(grid, 33, 35, 11, 13, 17, 19, 9)
    fill_box(grid, 34, 35, 13, 13, 17, 18, 3)

    # --- SACRED SHRINE HALBERD / GOHEI-NAGINATA (Held proudly outside +X at x=35, y=12) ---
    # Sleek iron shaft passing solidly through right fist, completely clear of right shoulder!
    fill_box(grid, 35, 35, 12, 12, 3, 34, 9)
    # Gold ferrule, grip rings, and collar accents
    fill_box(grid, 35, 35, 12, 12, 2, 4, 5)
    fill_box(grid, 35, 35, 12, 12, 15, 16, 5)
    fill_box(grid, 35, 35, 12, 12, 20, 21, 5)
    fill_box(grid, 35, 35, 12, 12, 32, 33, 5)
    # Mini Torii crossguard right below the naginata blade!
    fill_box(grid, 33, 37, 12, 12, 34, 34, 1)
    fill_box(grid, 32, 38, 12, 12, 35, 35, 3)
    fill_box(grid, 32, 32, 12, 12, 36, 36, 5)
    fill_box(grid, 38, 38, 12, 12, 36, 36, 5)
    # Sweeping curved Naginata blade arching proudly outward (+X) with Jade crystal!
    fill_box(grid, 35, 36, 12, 12, 36, 37, 8)    # Glowing sacred jade crystal core
    fill_box(grid, 35, 35, 12, 12, 38, 41, 4)    # Steel blade spine
    fill_box(grid, 36, 37, 12, 12, 37, 41, 7)    # Gleaming white blade edge
    fill_box(grid, 36, 38, 12, 12, 41, 43, 7)    # Sweeping curved blade tip
    fill_box(grid, 37, 38, 12, 12, 44, 44, 7)
    # Fluttering White Paper Shide streamer below halberd crossguard
    fill_box(grid, 36, 36, 12, 12, 32, 33, 7)
    fill_box(grid, 37, 37, 12, 12, 31, 32, 7)
    fill_box(grid, 36, 36, 12, 12, 29, 31, 7)

    # --- HEAD & DRAMATIC WINGED TORII-ARCH CROWN (Z: 33..44) ---
    fill_sym_box(grid, 0, 1, 10, 12, 33, 34, 9)
    # Samurai Kabuto helmet shell
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 3)
    fill_sym_box(grid, 2, 2, 9, 12, 34, 37, 1)   # Vermilion cheek guards
    fill_sym_box(grid, 2, 2, 10, 11, 35, 36, 5)  # Gold ear medallions
    # Pure white faceplate & red chin guard
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 7)
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 1)
    # Glowing Sacred Jade Visor Eyes
    fill_sym_box(grid, 0, 1, 14, 14, 36, 36, 8)
    fill_sym_box(grid, 0, 1, 14, 14, 37, 38, 3)  # Helmet brow
    # Forehead Gold-Trimmed Gakuzuka Plaque Crest
    fill_sym_box(grid, 0, 0, 15, 15, 37, 39, 5)
    fill_sym_box(grid, 0, 0, 15, 15, 38, 38, 3)
    # Dramatic Winged Torii-Arch Kasagi Crown on Helmet Top (Z: 39..44)!
    # Twin mini red Torii pillars with crisp open window between them
    fill_sym_box(grid, 1, 2, 11, 13, 39, 40, 1)
    fill_sym_box(grid, 0, 0, 11, 13, 39, 40, 0)  # Open mini-Torii archway!
    # Crown sweeping upturned Kasagi arch
    fill_sym_box(grid, 0, 3, 11, 13, 41, 41, 1)
    fill_sym_box(grid, 0, 3, 11, 13, 42, 42, 3)
    fill_sym_box(grid, 0, 0, 12, 13, 42, 42, 5)  # Center gold plaque jewel
    fill_sym_box(grid, 4, 5, 11, 13, 42, 42, 1)
    fill_sym_box(grid, 4, 5, 11, 13, 43, 43, 3)
    fill_sym_box(grid, 5, 6, 12, 13, 43, 44, 5)  # Upturned golden kabuto wingtips

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=32, pitch_a=20, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "torii_a.vox")
    v_b = export_vox(model_b, "torii_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SHINTO TORII GATE -> TORII SHRINE GUARDIAN ROBOT",
        "1. SHINTO TORII GATE",
        "2. TORII SHRINE GUARDIAN ROBOT",
        "preview_torii.png",
        yaw_a=32, pitch_a=20, yaw_b=32, pitch_b=20,
    )
    print(f"torii: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
