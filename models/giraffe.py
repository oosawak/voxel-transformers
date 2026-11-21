import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (228, 158, 44, 255),   # Sunny Golden-Ochre Coat (Primary Giraffe Body & Armor)
    2: (126, 56, 24, 255),    # Rich Chestnut-Brown Giraffe Spots (Madara Pattern)
    3: (242, 224, 180, 255),  # Pale Cream Belly, Lower Legs & Inner Armor
    4: (58, 34, 22, 255),     # Dark Umber-Brown Hooves, Mane, Tail Tuft & Ossicone Tips
    5: (56, 64, 78, 255),     # Dark Slate Mecha Joints & Inner Frame
    6: (186, 118, 46, 255),   # Warm Tan Shading & Joint Accents
    7: (250, 208, 72, 255),   # Metallic Gleaming Gold/Bronze Lance Blade & Crest
    8: (44, 228, 194, 255),   # Glowing Emerald-Cyan Visor Eyes & Lance Core
    9: (252, 248, 232, 255),  # Warm Ivory Highlight, Faceplate & Blade Edge
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


def giraffe_spot_mask(u, v, centers, border=0.68):
    """Return True if (u, v) falls inside a polygonal chestnut giraffe spot (Voronoi reticulation)."""
    d1 = 1e9
    d2 = 1e9
    for cu, cv in centers:
        d = np.hypot(u - cu, v - cv)
        if d < d1:
            d2 = d1
            d1 = d
        elif d < d2:
            d2 = d
    return (d2 - d1) >= border


# ==========================================
# FORM A: SAVANNA GIRAFFE (14 x 30 x 45)
# ==========================================
def build_a():
    grid = np.zeros((14, 30, 45), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 6.5

    # Well-spaced spot centers in (Y, Z) side-view space for unmistakable polygonal giraffe spots
    body_spots = [
        (6.5, 17.5), (9.5, 15.2), (10.2, 19.0), (13.2, 16.6), (13.8, 20.5),
        (16.8, 15.5), (17.2, 19.2), (20.2, 17.5), (20.0, 21.6), (16.5, 22.5),
        (8.0, 12.8), (18.2, 12.8),
        # Neck spots
        (19.0, 25.0), (21.5, 26.5), (19.5, 28.8), (22.0, 30.4),
        (20.0, 32.6), (22.5, 34.2), (20.8, 36.4), (22.8, 37.8),
    ]

    # --- 4 LONG SLENDER GIRAFFE LEGS (Z: 0..18) ---
    # Front legs (long, sleek & straight, Y: 17..19, x_off: 2..3)
    # Dark brown hooves at Z=0..1
    fill_sym_box(grid, 2, 3, 17, 19, 0, 0, 4)
    fill_sym_box(grid, 2, 3, 17, 18, 1, 1, 4)
    # Pale cream slender lower legs (Z: 2..10)
    fill_sym_box(grid, 2, 3, 17, 18, 2, 10, 3)
    # Subtle warm tan knee joint bump at Z=9..10
    fill_sym_box(grid, 2, 3, 18, 19, 9, 10, 6)
    # Golden-ochre slender upper front legs (Z: 11..17)
    fill_sym_box(grid, 2, 3, 17, 19, 11, 17, 1)
    # Chestnut spots on upper front legs
    fill_sym_box(grid, 3, 3, 17, 18, 12, 13, 2)
    fill_sym_box(grid, 3, 3, 17, 18, 15, 16, 2)
    fill_sym_box(grid, 2, 3, 19, 19, 14, 15, 2)

    # Rear legs (classic angled hock, Y: 6..9, x_off: 2..3)
    # Dark brown hooves at Z=0..1
    fill_sym_box(grid, 2, 3, 6, 8, 0, 0, 4)
    fill_sym_box(grid, 2, 3, 6, 7, 1, 1, 4)
    # Pale cream slender lower legs curving slightly back toward hock (Z: 2..10)
    fill_sym_box(grid, 2, 3, 6, 7, 2, 7, 3)
    fill_sym_box(grid, 2, 3, 5, 7, 8, 10, 3)
    fill_sym_box(grid, 2, 3, 5, 5, 8, 9, 6)  # Tan hock joint accent
    # Golden-ochre upper hind legs & sleek haunches (Z: 11..16)
    fill_sym_box(grid, 2, 3, 6, 8, 11, 13, 1)
    fill_sym_box(grid, 2, 3, 6, 9, 13, 16, 1)
    # Chestnut spots on upper hind legs
    fill_sym_box(grid, 3, 3, 7, 8, 12, 13, 2)
    fill_sym_box(grid, 3, 3, 6, 7, 14, 15, 2)

    # --- SLOPING SPOTTED GIRAFFE BODY (Y: 5..21, Z: 14..23) ---
    # Classic giraffe back slopes gently upward from rump (Y=6, top Z=20) to withers (Y=19, top Z=23.5)
    for y in range(5, 22):
        t = (y - 5.0) / 16.0  # 0 at rump, 1 at chest
        z_bot = 14.0 + 0.8 * t
        z_top = 19.8 + 3.6 * (t ** 0.85)
        zc = (z_bot + z_top) / 2.0
        rz = (z_top - z_bot) / 2.0
        # Elliptical width tapering at chest & rump
        rx = 4.3 * np.sin(np.pi * np.clip((y - 4.2) / 17.6, 0.05, 0.95)) ** 0.55
        rx = max(2.2, rx)
        for z in range(13, 25):
            dz = (z - zc) / max(0.5, rz)
            if abs(dz) > 1.02:
                continue
            for x in range(X):
                dx = (x - cx) / rx
                if dx * dx + dz * dz <= 1.0:
                    # Pale cream belly along underside
                    if dz < -0.58:
                        col = 3
                    elif dz < -0.40:
                        col = 6  # Warm tan belly transition
                    else:
                        # Unmistakable chestnut-brown polygonal giraffe spots on golden-ochre
                        u = y + 0.35 * (abs(x - cx) < 1.5)
                        v = z + 0.25 * (abs(x - cx) < 1.5)
                        col = 2 if giraffe_spot_mask(u, v, body_spots, border=0.66) else 1
                    grid[x, y, z] = col

    # Withers / shoulder hump crest connecting smoothly into neck base
    fill_sym_box(grid, 0, 2, 17, 20, 22, 23, 1)
    fill_sym_box(grid, 1, 2, 18, 19, 22, 23, 2)

    # --- TUFTED GIRAFFE TAIL (Y: 2..5, Z: 9..18) ---
    fill_sym_box(grid, 0, 0, 4, 5, 17, 18, 1)
    fill_sym_box(grid, 0, 0, 3, 4, 15, 17, 1)
    fill_sym_box(grid, 0, 0, 3, 3, 12, 15, 6)
    # Dark brown bushy tail tuft at bottom
    fill_sym_box(grid, 0, 1, 2, 3, 9, 11, 4)
    fill_sym_box(grid, 0, 0, 2, 3, 8, 9, 4)

    # --- VERY LONG UPRIGHT SPOTTED NECK WITH SHORT MANE (Z: 21..39) ---
    for z in range(21, 40):
        t = (z - 21.0) / 18.0  # 0 at chest base, 1 at top of neck
        yc = 18.8 + 2.8 * t    # Gently angled forward like a real giraffe
        rx = 2.7 * (1.0 - t) + 1.45 * t
        ry = 3.1 * (1.0 - t) + 1.85 * t
        for x in range(X):
            dx = (x - cx) / rx
            if abs(dx) > 1.05:
                continue
            for y in range(Y):
                dy = (y - yc) / ry
                if dx * dx + dy * dy <= 1.0:
                    # Pale cream throat strip down the front (+Y)
                    if dy > 0.62 and abs(dx) < 0.65:
                        col = 3
                    else:
                        col = 2 if giraffe_spot_mask(y, z, body_spots, border=0.64) else 1
                    grid[x, y, z] = col

        # Short bristly dark-brown giraffe mane along back edge (-Y) of neck (Z: 22..39)
        if z >= 22:
            mane_y = int(round(yc - ry - 0.3))
            fill_sym_box(grid, 0, 0, mane_y - 1, mane_y, z, z, 4)
            if z % 3 == 0:
                fill_sym_box(grid, 0, 0, mane_y - 1, mane_y - 1, z, z, 6)

    # --- GRACEFUL GIRAFFE HEAD, EARS & TWIN OSSICONES (Y: 19..28, Z: 38..44) ---
    # Cranium (Y: 20..24, Z: 38..41)
    fill_sym_box(grid, 0, 2, 20, 24, 38, 41, 1)
    fill_sym_box(grid, 0, 1, 20, 23, 41, 41, 1)
    # Forehead spot & cheek shading
    fill_sym_box(grid, 0, 1, 21, 22, 40, 41, 2)
    fill_sym_box(grid, 2, 2, 21, 22, 39, 39, 2)
    # Tapered slender muzzle / snout extending toward +Y (Y: 25..28, Z: 38..40)
    fill_sym_box(grid, 0, 1, 25, 26, 38, 40, 1)
    fill_sym_box(grid, 0, 1, 27, 28, 38, 39, 3)  # Pale cream velvety nose
    fill_sym_box(grid, 0, 0, 28, 28, 38, 38, 4)  # Dark nostril / mouth tip
    fill_sym_box(grid, 0, 1, 24, 26, 37, 37, 3)  # Cream lower jaw

    # Gentle organic dark-brown giraffe eyes with warm ivory glint
    fill_sym_box(grid, 2, 2, 23, 24, 40, 40, 4)
    fill_sym_box(grid, 2, 2, 24, 24, 40, 40, 9)

    # Leaf-shaped Giraffe Ears flaring outward at back of head (x_off: 2..4, Y: 20..21, Z: 40..41)
    fill_sym_box(grid, 3, 4, 20, 21, 40, 41, 1)
    fill_sym_box(grid, 3, 4, 21, 21, 40, 40, 3)  # Pale cream inner ear
    fill_sym_box(grid, 4, 4, 20, 20, 41, 41, 6)  # Tapered ear tip

    # Iconic Twin Ossicones (Giraffe Horns) rising from crown (x_off: 1, Y: 21, Z: 42..44)
    fill_sym_box(grid, 1, 1, 21, 21, 42, 43, 1)  # Golden-ochre stalks
    fill_sym_box(grid, 1, 1, 21, 21, 44, 44, 4)  # Dark-brown furry ossicone caps

    # Hollow strictly interior voxels so Form A stays compact & crisp
    hollow_interior_26(grid, 14, 40)

    return grid


# ==========================================
# FORM B: GIRAFFE LANCER ROBOT (36 x 24 x 52)
# ==========================================
def build_b():
    grid = np.zeros((36, 24, 52), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 17 (-X robot left)
    cx_r = X // 2      # 18 (+X robot right / lance arm)

    # --- SLENDER GIRAFFE HOOF-FEET (Z: 0..2) ---
    # Cloven dark-brown giraffe hoof boots with sleek dark slate heel spur
    fill_sym_box(grid, 3, 4, 11, 15, 0, 1, 4)   # Sleek dark umber cloven hoof front
    fill_sym_box(grid, 3, 4, 9, 10, 0, 1, 5)    # Dark slate heel spur
    fill_sym_box(grid, 3, 4, 11, 14, 2, 2, 4)   # Upper hoof rim
    fill_sym_box(grid, 3, 4, 10, 12, 2, 3, 5)   # Ankle mechanical joint

    # --- LONG SLENDER GIRAFFE LEGS (Z: 3..21) ---
    # Sleek, agile 2-voxel-wide slender legs directly retaining Form A's giraffe legs!
    # Pale cream slender lower shins (Z: 3..11) with dark slate rear hydraulics
    fill_sym_box(grid, 3, 4, 10, 11, 3, 11, 5)  # Slender slate frame
    fill_sym_box(grid, 3, 4, 11, 13, 3, 11, 3)  # Pale cream sleek front shin armor
    fill_sym_box(grid, 4, 4, 13, 13, 4, 10, 9)  # Crisp ivory front shin highlight
    fill_sym_box(grid, 4, 4, 10, 11, 5, 9, 6)   # Warm tan side calf trim

    # Sculpted Agile Knee Guards (Z: 11..14)
    fill_sym_box(grid, 3, 4, 12, 14, 11, 13, 1)
    fill_sym_box(grid, 3, 4, 14, 14, 12, 12, 8)  # Glowing emerald knee sensor
    fill_sym_box(grid, 3, 4, 10, 12, 12, 13, 5)  # Knee joint

    # Slender Spotted Golden-Ochre Thighs (Z: 14..21)
    fill_sym_box(grid, 3, 4, 10, 13, 14, 20, 1)
    # Crisp chestnut-brown giraffe spots on thighs!
    fill_sym_box(grid, 3, 4, 13, 13, 15, 16, 2)
    fill_sym_box(grid, 4, 4, 13, 13, 18, 19, 2)
    fill_sym_box(grid, 4, 4, 10, 11, 15, 16, 2)
    fill_sym_box(grid, 4, 4, 11, 12, 18, 19, 2)
    fill_sym_box(grid, 3, 4, 10, 10, 16, 17, 2)
    fill_sym_box(grid, 3, 4, 10, 12, 20, 21, 5)  # Hip joint socket

    # --- ATHLETIC WAIST, SPOTTED HIP SKIRTS & REAR TAIL STABILIZER (Z: 20..24) ---
    fill_sym_box(grid, 0, 4, 9, 13, 21, 23, 5)   # Dark slate waist chassis
    # Front spotted golden-ochre skirt plates
    fill_sym_box(grid, 2, 4, 13, 14, 20, 23, 1)
    fill_sym_box(grid, 2, 3, 14, 14, 21, 22, 2)  # Giraffe spot on waist skirt
    fill_sym_box(grid, 4, 5, 10, 13, 20, 22, 1)  # Side hip tassets
    fill_sym_box(grid, 5, 5, 11, 12, 20, 21, 2)  # Side tasset spot
    # Center pelvic armor & emerald belt gem
    fill_sym_box(grid, 0, 1, 13, 15, 20, 23, 3)
    fill_sym_box(grid, 0, 1, 14, 15, 22, 23, 7)  # Gold belt buckle
    fill_sym_box(grid, 0, 0, 15, 15, 22, 22, 8)  # Glowing emerald core gem

    # Rear Giraffe Tail Stabilizer descending from back of pelvis (Y: 4..9, Z: 13..22)
    fill_sym_box(grid, 0, 0, 7, 9, 21, 22, 1)
    fill_sym_box(grid, 0, 0, 6, 7, 19, 21, 1)
    fill_sym_box(grid, 0, 0, 5, 6, 16, 19, 6)
    fill_sym_box(grid, 0, 1, 4, 5, 13, 15, 4)    # Dark brown tufted tail tip

    # --- SPOTTED GIRAFFE TORSO & CHEST (Z: 24..34) - DIRECTLY FORM A'S BODY! ---
    # Tapered athletic abdomen (Z: 24..26)
    fill_sym_box(grid, 0, 3, 9, 13, 24, 26, 5)
    fill_sym_box(grid, 0, 2, 13, 14, 24, 26, 3)  # Pale cream belly plates
    fill_sym_box(grid, 2, 3, 12, 13, 24, 25, 6)

    # Broad Sculpted Giraffe-Patterned Chest (Z: 26..34)
    fill_sym_box(grid, 0, 5, 9, 15, 26, 33, 1)
    fill_sym_box(grid, 0, 4, 14, 16, 27, 32, 1)
    # Crisp unmistakable chestnut-brown giraffe spots (madara) across front & sides of chest!
    fill_sym_box(grid, 2, 4, 15, 16, 28, 29, 2)  # Bold chest flank spot
    fill_sym_box(grid, 1, 2, 15, 16, 31, 32, 2)  # Upper chest spot
    fill_sym_box(grid, 4, 5, 13, 14, 30, 31, 2)  # Side rib spot
    fill_sym_box(grid, 4, 5, 10, 11, 27, 28, 2)  # Outer rib spot
    fill_sym_box(grid, 3, 4, 15, 15, 26, 27, 2)  # Lower pectoral spot
    # Pale cream sternum collar & glowing emerald-cyan chest reactor
    fill_sym_box(grid, 0, 1, 15, 16, 27, 30, 3)
    fill_sym_box(grid, 0, 1, 16, 16, 28, 29, 8)  # Glowing emerald core
    fill_sym_box(grid, 0, 2, 15, 16, 30, 30, 7)  # Metallic gold chest V-trim
    fill_sym_box(grid, 2, 3, 14, 15, 33, 34, 3)  # High cream collar guards
    fill_sym_box(grid, 3, 4, 12, 14, 33, 34, 7)  # Gold collar tips

    # --- SLEEK SPOTTED BACKPACK WITH MANE-FIN RIDGE (Y: 5..9, Z: 25..34) ---
    fill_sym_box(grid, 0, 4, 6, 9, 26, 33, 1)
    fill_sym_box(grid, 1, 3, 6, 6, 27, 28, 2)    # Crisp giraffe spots on back!
    fill_sym_box(grid, 2, 4, 6, 7, 30, 31, 2)
    fill_sym_box(grid, 0, 0, 5, 6, 26, 34, 4)    # Central dark-brown mane crest fin!
    fill_sym_box(grid, 0, 0, 4, 5, 29, 34, 4)    # Flared upper mane dorsal fin
    fill_sym_box(grid, 2, 3, 5, 6, 25, 26, 5)    # Compact sleek rear thrusters
    fill_sym_box(grid, 2, 3, 5, 5, 25, 25, 8)    # Emerald thruster vents

    # --- SPOTTED SHOULDER PAULDRONS & AGILE ARMS (Z: 17..35) ---
    # Shoulder connector joints
    fill_sym_box(grid, 5, 6, 10, 12, 30, 32, 5)
    # Swept Lancer Shoulder Pauldrons (golden-ochre with clear giraffe spots!)
    fill_sym_box(grid, 6, 9, 9, 13, 29, 34, 1)
    fill_sym_box(grid, 7, 9, 10, 12, 34, 35, 1)  # Swept upper pauldron peak
    fill_sym_box(grid, 9, 10, 10, 12, 31, 34, 7) # Metallic gold outer shoulder crest
    fill_sym_box(grid, 6, 8, 13, 13, 30, 31, 2)  # Front pauldron giraffe spot!
    fill_sym_box(grid, 7, 8, 9, 9, 31, 32, 2)    # Rear pauldron giraffe spot!
    fill_sym_box(grid, 8, 9, 11, 12, 32, 33, 2)  # Top pauldron spot
    fill_sym_box(grid, 6, 8, 12, 13, 29, 29, 3)  # Pale cream lower trim

    # LEFT ARM (-X, x_off: 7..9) — Agile arm with compact spotted savanna buckler
    fill_box(grid, cx_l - 8, cx_l - 7, 10, 12, 24, 28, 5)  # Slender upper arm
    fill_box(grid, cx_l - 8, cx_l - 7, 12, 12, 25, 27, 3)  # Cream bicep plate
    fill_box(grid, cx_l - 9, cx_l - 7, 10, 13, 18, 23, 1)  # Spotted golden forearm
    fill_box(grid, cx_l - 9, cx_l - 8, 13, 13, 19, 20, 2)  # Forearm spot
    fill_box(grid, cx_l - 9, cx_l - 9, 10, 11, 21, 22, 2)  # Outer forearm spot
    fill_box(grid, cx_l - 8, cx_l - 7, 11, 13, 16, 17, 5)  # Left mecha fist
    # Compact Savanna Lancer Buckler mounted on outer left forearm
    fill_box(grid, cx_l - 10, cx_l - 10, 10, 15, 17, 24, 1)
    fill_box(grid, cx_l - 11, cx_l - 11, 11, 14, 18, 23, 1)
    fill_box(grid, cx_l - 11, cx_l - 11, 12, 13, 21, 22, 2)  # Shield giraffe spot
    fill_box(grid, cx_l - 11, cx_l - 11, 11, 12, 18, 19, 2)  # Shield giraffe spot
    fill_box(grid, cx_l - 11, cx_l - 11, 14, 14, 19, 22, 7)  # Gold shield edge
    fill_box(grid, cx_l - 11, cx_l - 11, 13, 13, 20, 20, 8)  # Emerald emblem

    # RIGHT ARM (+X, x_off: 7..13) — Extended cleanly outward & forward so Tall Lance has crisp negative space!
    # Upper arm angling slightly outward from right shoulder
    fill_box(grid, cx_r + 7, cx_r + 8, 10, 12, 25, 28, 5)
    fill_box(grid, cx_r + 8, cx_r + 9, 11, 13, 23, 26, 5)
    fill_box(grid, cx_r + 8, cx_r + 9, 12, 13, 24, 25, 3)
    # Right forearm angling forward (+Y) and outward (+X) so lance clears shoulder cleanly!
    fill_box(grid, cx_r + 8, cx_r + 11, 12, 15, 19, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 11, 14, 15, 20, 21, 2)   # Forearm giraffe spot
    fill_box(grid, cx_r + 11, cx_r + 12, 15, 17, 19, 21, 3)  # Wrist cuff
    # Right mecha hand gripping the Giraffe-Neck Lance at X = cx_r + 13..14, Y = 16..18, Z = 19..21
    fill_box(grid, cx_r + 12, cx_r + 14, 16, 18, 19, 21, 5)
    fill_box(grid, cx_r + 14, cx_r + 14, 17, 18, 19, 21, 4)  # Gripping knuckles

    # --- DRAMATIC TALL GIRAFFE-NECK SPEAR / LANCE (Held in Right Hand +X, Z: 5..51) ---
    # Positioned at X = cx_r + 13..14 (31..32), Y = 17..18 — crisp separation from right pauldron (X<=28, Y<=13)!
    lx0, lx1 = cx_r + 13, cx_r + 14  # 31..32
    ly0, ly1 = 17, 18

    # Lower lance butt-shaft & counter-spike (Z: 5..18)
    fill_box(grid, lx0, lx1, ly0, ly1, 9, 18, 1)
    fill_box(grid, lx0, lx1, ly0, ly1, 12, 13, 2)    # Lower shaft giraffe spot
    fill_box(grid, lx1, lx1, ly0, ly1, 16, 17, 2)    # Lower shaft spot
    fill_box(grid, lx0, lx1, ly0, ly1, 8, 8, 7)      # Gold pommel ring
    fill_box(grid, lx0, lx0, ly0, ly0, 5, 7, 7)      # Tapered bronze-gold butt-spike

    # Upper Giraffe-Neck Lance Shaft (Z: 22..38) — unmistakably Form A's long spotted neck + mane!
    fill_box(grid, lx0, lx1, ly0, ly1, 22, 38, 1)
    # Crisp alternating chestnut-brown giraffe spots climbing up the entire neck-shaft!
    for sz in (23, 27, 31, 35):
        fill_box(grid, lx1, lx1, ly1, ly1, sz, sz + 1, 2)
        fill_box(grid, lx0, lx0, ly0, ly1, sz + 1, sz + 2, 2)
    for sz in (25, 29, 33):
        fill_box(grid, lx0, lx1, ly1, ly1, sz, sz + 1, 2)
    # Bristly dark-brown giraffe mane ridge running cleanly up the back (-Y) of the lance shaft!
    fill_box(grid, lx0, lx0, ly0 - 1, ly0 - 1, 23, 38, 4)
    for mz in range(24, 38, 3):
        fill_box(grid, lx0, lx0, ly0 - 1, ly0 - 1, mz, mz, 6)

    # Ornate Giraffe-Crest Lance Crossguard & Collar (Z: 38..40)
    fill_box(grid, lx0 - 1, lx1 + 1, ly0 - 1, ly1 + 1, 39, 40, 7)  # Gleaming gold guard
    fill_box(grid, lx0 - 1, lx1 + 1, ly0, ly1, 38, 38, 4)          # Dark umber collar band
    fill_box(grid, lx0, lx1, ly1 + 1, ly1 + 1, 39, 40, 8)          # Glowing emerald lance jewel

    # Gleaming Tall Metallic Gold/Bronze Spearhead Blade (Z: 41..51)
    fill_box(grid, lx0, lx1, ly0 - 1, ly1 + 1, 41, 44, 7)          # Broad blade base
    fill_box(grid, lx0, lx1, ly0, ly1 + 1, 45, 47, 7)              # Mid tapered blade
    fill_box(grid, lx0, lx0, ly0, ly1, 48, 49, 7)                  # Upper narrow blade
    fill_box(grid, lx0, lx0, ly1, ly1, 50, 51, 9)                  # Razor ivory spear tip!
    # Sharp warm ivory cutting edges & glowing emerald fuller groove
    fill_box(grid, lx1, lx1, ly1 + 1, ly1 + 1, 41, 46, 9)          # Gleaming front edge
    fill_box(grid, lx0, lx0, ly0 - 1, ly0 - 1, 41, 44, 9)          # Rear blade bevel
    fill_box(grid, lx1, lx1, ly0, ly1, 42, 45, 8)                  # Emerald energy fuller

    # --- HEROIC OSSICONE-CROWNED HORNED HELMET (Z: 34..43) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 12, 33, 34, 5)
    # Helmet cranium (golden-ochre with chestnut giraffe crown markings!)
    fill_sym_box(grid, 0, 2, 9, 14, 35, 39, 1)
    fill_sym_box(grid, 0, 2, 10, 13, 39, 40, 1)
    fill_sym_box(grid, 1, 2, 10, 12, 39, 40, 2)  # Chestnut crown spots
    fill_sym_box(grid, 0, 1, 9, 10, 36, 38, 2)   # Rear helmet spot
    # Warm ivory heroic knight faceplate & chin guard
    fill_sym_box(grid, 0, 1, 14, 15, 35, 36, 9)
    fill_sym_box(grid, 0, 0, 15, 15, 35, 35, 7)  # Gold chin vent
    # Glowing Emerald-Cyan Visor Eyes!
    fill_sym_box(grid, 0, 2, 14, 15, 37, 37, 8)
    fill_sym_box(grid, 2, 2, 13, 14, 37, 37, 8)
    # Sculpted brow & metallic gold forehead V-crest
    fill_sym_box(grid, 0, 2, 14, 15, 38, 38, 1)
    fill_sym_box(grid, 0, 0, 15, 15, 38, 39, 7)  # Gold crest center
    fill_sym_box(grid, 1, 2, 14, 15, 39, 39, 7)  # Gold brow wings
    # Giraffe-ear side helmet fins
    fill_sym_box(grid, 3, 4, 10, 12, 37, 38, 1)
    fill_sym_box(grid, 3, 4, 12, 12, 37, 37, 3)
    # Iconic Twin Ossicone Helmet Horns rising cleanly to Z=43!
    fill_sym_box(grid, 1, 1, 11, 12, 41, 42, 7)  # Gold armored ossicone stalks
    fill_sym_box(grid, 2, 2, 11, 12, 42, 42, 1)  # Slight outward flare
    fill_sym_box(grid, 2, 2, 11, 12, 43, 43, 4)  # Iconic dark-brown ossicone caps!

    # Hollow unseen torso interior to keep voxel count sleek & optimal
    hollow_interior_26(grid, 26, 33)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=42, pitch_a=20, yaw_b=32, pitch_b=18):
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
    v_a = export_vox(model_a, "giraffe_a.vox")
    v_b = export_vox(model_b, "giraffe_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SAVANNA GIRAFFE -> GIRAFFE LANCER ROBOT",
        "1. SAVANNA GIRAFFE",
        "2. GIRAFFE LANCER ROBOT",
        "preview_giraffe.png",
        yaw_a=44, pitch_a=18, yaw_b=32, pitch_b=18,
    )
    print(f"giraffe: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
