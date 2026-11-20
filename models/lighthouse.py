import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (242, 245, 250, 255),  # Crisp Lighthouse White
    2: (212, 44, 48, 255),    # Maritime Crimson Red
    3: (146, 26, 34, 255),    # Deep Lantern Dome Red
    4: (102, 118, 136, 255),  # Coastal Slate Stone
    5: (64, 76, 94, 255),     # Wet Coastal Granite
    6: (38, 42, 52, 255),     # Wrought Iron Catwalk / Frame
    7: (116, 72, 42, 255),    # Weathered Timber Door
    8: (115, 224, 255, 255),  # Lantern Glass Cyan
    9: (255, 226, 76, 255),   # Radiant Fresnel Gold
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


def fill_cyl(grid, cx, cy, r_out, r_in, z0, z1, col):
    """Fill a hollow or solid vertical cylinder centered at (cx, cy)."""
    X, Y, Z = grid.shape
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    r_out2 = r_out * r_out
    r_in2 = r_in * r_in if r_in > 0 else -1.0
    for x in range(X):
        dx = x - cx
        dx2 = dx * dx
        if dx2 > r_out2:
            continue
        for y in range(Y):
            dy = y - cy
            d2 = dx2 + dy * dy
            if r_in2 <= d2 <= r_out2:
                grid[x, y, z0:z1 + 1] = col


# ==========================================
# FORM A: COASTAL LIGHTHOUSE (22 x 22 x 48)
# ==========================================
def build_a():
    grid = np.zeros((22, 22, 48), dtype=np.uint8)
    cx, cy = 10.5, 10.5

    # --- ROCKY COASTAL STONE BASE (Z: 0..6) ---
    # Irregular rocky crag foundation (hollow inside for lean voxel count)
    fill_cyl(grid, cx, cy, 9.0, 6.9, 0, 1, 5)
    fill_cyl(grid, cx, cy, 8.2, 6.2, 1, 2, 4)
    # Organic coastal boulders around the perimeter
    boulders = [
        (2, 4, 6, 10, 0, 2, 4),
        (17, 19, 5, 9, 0, 2, 5),
        (4, 7, 15, 18, 0, 2, 4),
        (15, 18, 14, 18, 0, 2, 5),
        (7, 14, 2, 4, 0, 2, 4),
        (2, 4, 11, 15, 0, 1, 5),
        (17, 19, 10, 14, 0, 1, 4),
        (6, 15, 17, 19, 0, 1, 5),
    ]
    for x0, x1, y0, y1, z0, z1, col in boulders:
        fill_box(grid, x0, x1, y0, y1, z0, z1, col)

    # Dressed stone plinth (Z: 2..6, hollow interior)
    fill_cyl(grid, cx, cy, 7.1, 5.4, 2, 3, 4)
    fill_cyl(grid, cx, cy, 6.3, 4.9, 4, 5, 4)
    fill_cyl(grid, cx, cy, 6.5, 4.9, 6, 6, 5)  # Stone cornice ledge

    # Front (+Y) stone entry steps, dark wooden door & iron porch light
    fill_box(grid, 8, 13, 17, 19, 0, 0, 4)
    fill_box(grid, 8, 13, 16, 18, 1, 1, 4)
    fill_box(grid, 8, 13, 16, 17, 2, 6, 5)    # Stone door surround
    fill_box(grid, 9, 12, 17, 17, 2, 5, 7)    # Dark wooden door
    fill_box(grid, 10, 11, 17, 17, 4, 4, 6)   # Iron door crossbar
    fill_box(grid, 9, 12, 16, 17, 6, 6, 4)    # Door lintel
    fill_box(grid, 10, 11, 18, 18, 6, 6, 9)   # Warm entrance lamp

    # --- TAPERING RED-AND-WHITE STRIPED TOWER (Z: 7..31) ---
    # 5 bold alternating horizontal bands (5 layers each, hollow thin shell)
    bands = [
        (7, 11, 5.6, 4.5, 1),   # White band 1
        (12, 16, 5.3, 4.2, 2),  # Maritime Red band 1
        (17, 21, 5.0, 3.9, 1),  # White band 2
        (22, 26, 4.7, 3.6, 2),  # Maritime Red band 2
        (27, 31, 4.4, 3.3, 1),  # White band 3
    ]
    for z0, z1, r_out, r_in, col in bands:
        fill_cyl(grid, cx, cy, r_out, r_in, z0, z1, col)

    # Small dark porthole windows on front, back, and sides
    # Front (+Y) portholes
    fill_box(grid, 9, 12, 15, 16, 13, 15, 6)
    fill_box(grid, 10, 11, 15, 16, 14, 14, 8)
    fill_box(grid, 9, 12, 14, 15, 23, 25, 6)
    fill_box(grid, 10, 11, 14, 15, 24, 24, 8)
    # Rear (-Y) portholes
    fill_box(grid, 9, 12, 5, 6, 13, 15, 6)
    fill_box(grid, 10, 11, 5, 6, 14, 14, 8)
    fill_box(grid, 9, 12, 6, 7, 23, 25, 6)
    fill_box(grid, 10, 11, 6, 7, 24, 24, 8)
    # Side (+X / -X) portholes on white bands
    for sx0, sx1 in ((5, 6), (15, 16)):
        fill_box(grid, sx0, sx1, 9, 12, 18, 20, 6)
        fill_box(grid, sx0, sx1, 10, 11, 19, 19, 8)
    for sx0, sx1 in ((6, 7), (14, 15)):
        fill_box(grid, sx0, sx1, 9, 12, 28, 30, 6)
        fill_box(grid, sx0, sx1, 10, 11, 29, 29, 8)

    # --- PROTRUDING DARK-IRON CATWALK GALLERY & RAILING (Z: 31..35) ---
    fill_cyl(grid, cx, cy, 5.2, 3.3, 31, 31, 5)  # Corbel support ring
    fill_cyl(grid, cx, cy, 6.2, 2.5, 32, 32, 6)  # Iron catwalk deck

    # Open gallery railing: continuous top handrail (Z=34) on 8 clean iron posts (Z=33)
    fill_cyl(grid, cx, cy, 6.2, 5.0, 34, 34, 6)
    post_coords = [
        (10, 16), (11, 5), (16, 11), (5, 10),
        (15, 14), (6, 14), (15, 7), (6, 7),
    ]
    for px, py in post_coords:
        grid[px, py, 33] = 6

    # --- GLOWING GLASS LANTERN ROOM & FRESNEL LENS CORE (Z: 33..39) ---
    fill_cyl(grid, cx, cy, 4.0, 2.7, 33, 33, 3)  # Deep red lantern base wall
    # Outer glowing cyan glass cylinder (Z: 34..38)
    fill_cyl(grid, cx, cy, 3.7, 2.7, 34, 38, 8)
    # Bright glowing Fresnel gold lens core visible across mid-lantern (Z: 35..37)
    fill_cyl(grid, cx, cy, 3.7, 2.7, 35, 37, 9)
    # Cyan glass glints on top/bottom edges for sparkling glass look
    for z in (35, 37):
        for gx, gy in ((10, 14), (11, 14), (10, 7), (11, 7), (14, 10), (14, 11), (7, 10), (7, 11)):
            grid[gx, gy, z] = 8
    # 4 dark-iron diagonal window mullions framing the glass
    for mx, my in ((13, 13), (8, 13), (13, 8), (8, 8)):
        grid[mx, my, 34:39] = 6

    # --- DARK RED CONICAL DOME & LIGHTNING ROD (Z: 39..47) ---
    fill_cyl(grid, cx, cy, 4.3, 2.5, 39, 39, 6)  # Iron lantern eaves
    fill_cyl(grid, cx, cy, 3.9, 2.3, 40, 40, 2)  # Red dome ring 1
    fill_cyl(grid, cx, cy, 3.3, 1.8, 41, 41, 3)  # Deep red dome ring 2
    fill_cyl(grid, cx, cy, 2.6, 1.0, 42, 42, 2)  # Red dome ring 3
    fill_cyl(grid, cx, cy, 1.8, 0.0, 43, 43, 3)  # Deep red dome peak
    fill_box(grid, 10, 11, 10, 11, 44, 44, 9)    # Golden ventilator finial
    fill_box(grid, 10, 11, 10, 11, 45, 45, 6)    # Lightning rod base
    grid[10, 10, 46:48] = 6                      # Lightning rod spire
    grid[11, 11, 46] = 6

    return grid


# ==========================================
# FORM B: LIGHTHOUSE BEACON ROBOT (34 x 24 x 46)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 46), dtype=np.uint8)

    # --- HEAVY ROCKY COASTAL STONE BOOTS (Z: 0..3) ---
    # Wide planted granite & slate stone feet
    fill_sym_box(grid, 2, 5, 7, 15, 0, 1, 5)     # Wet granite rocky sole
    fill_sym_box(grid, 2, 5, 8, 14, 2, 3, 4)     # Coastal slate boot body
    fill_sym_box(grid, 3, 4, 15, 17, 0, 0, 5)    # Front rocky toe crag
    fill_sym_box(grid, 3, 4, 14, 16, 1, 2, 4)    # Armored rocky toe cap
    fill_sym_box(grid, 5, 5, 9, 13, 1, 2, 5)     # Outer boulder flange
    fill_sym_box(grid, 2, 4, 7, 8, 2, 3, 5)      # Heel spur
    fill_sym_box(grid, 2, 4, 12, 14, 3, 3, 6)    # Iron ankle collar

    # --- RED-AND-WHITE STRIPED TOWER LOWER LEGS (Z: 4..13) ---
    # Split cylindrical striped lighthouse shins (athletic stance with clear gap)
    fill_sym_box(grid, 2, 4, 9, 13, 4, 6, 1)     # White stripe 1
    fill_sym_box(grid, 2, 4, 9, 13, 7, 9, 2)     # Maritime Red stripe 1
    fill_sym_box(grid, 2, 4, 9, 13, 10, 12, 1)   # White stripe 2
    # Outer shin curve & porthole
    fill_sym_box(grid, 5, 5, 10, 12, 5, 6, 1)
    fill_sym_box(grid, 5, 5, 10, 12, 7, 9, 2)
    fill_sym_box(grid, 5, 5, 10, 12, 10, 11, 1)
    fill_sym_box(grid, 5, 5, 11, 11, 8, 8, 8)    # Side porthole glass
    # Hollow shin core
    fill_sym_box(grid, 3, 3, 10, 12, 5, 11, 0)
    # Red armored knee-guards with iron/cyan porthole
    fill_sym_box(grid, 2, 4, 13, 14, 11, 14, 2)
    fill_sym_box(grid, 3, 3, 14, 15, 12, 13, 6)
    fill_sym_box(grid, 3, 3, 15, 15, 12, 12, 8)

    # --- THIGHS (Z: 14..18) ---
    fill_sym_box(grid, 2, 3, 9, 12, 14, 18, 5)   # Granite inner thigh
    fill_sym_box(grid, 2, 4, 10, 13, 15, 16, 1)  # White thigh armor band
    fill_sym_box(grid, 2, 4, 10, 13, 17, 18, 2)  # Red thigh armor band
    fill_sym_box(grid, 2, 3, 10, 12, 14, 14, 6)  # Knee joint axle

    # --- WAIST / PELVIS & TIMBER DOOR BUCKLE (Z: 19..21) ---
    fill_sym_box(grid, 0, 3, 9, 12, 19, 21, 6)   # Wrought-iron waist core
    fill_sym_box(grid, 0, 2, 12, 13, 19, 21, 4)  # Coastal stone front belt
    fill_sym_box(grid, 0, 1, 13, 14, 18, 21, 2)  # Center red waist plate
    fill_sym_box(grid, 0, 0, 14, 14, 19, 20, 9)  # Golden center belt beacon
    fill_sym_box(grid, 2, 3, 13, 13, 19, 20, 7)  # Timber door accents on belt
    # Hip side-skirts (striped)
    fill_sym_box(grid, 4, 4, 9, 12, 18, 19, 1)
    fill_sym_box(grid, 4, 4, 9, 12, 20, 21, 2)

    # --- TORSO: STRIPED LIGHTHOUSE TOWER BODY (Z: 22..32) ---
    # Sturdy cylindrical-profile striped chest & back (hollow core inside)
    fill_sym_box(grid, 0, 4, 8, 13, 22, 24, 2)   # Maritime Red band
    fill_sym_box(grid, 0, 4, 8, 13, 25, 27, 1)   # Crisp White band
    fill_sym_box(grid, 0, 4, 8, 13, 28, 30, 2)   # Maritime Red band
    fill_sym_box(grid, 0, 4, 8, 13, 31, 32, 1)   # Crisp White upper chest
    # Slight forward chest barrel curve
    fill_sym_box(grid, 0, 2, 14, 14, 22, 24, 2)
    fill_sym_box(grid, 0, 2, 14, 14, 25, 27, 1)
    fill_sym_box(grid, 0, 2, 14, 14, 28, 30, 2)
    fill_sym_box(grid, 0, 2, 14, 14, 31, 32, 1)
    # Hollow unseen inner chest cavity
    fill_sym_box(grid, 0, 3, 9, 12, 23, 31, 0)

    # --- RADIATING GOLDEN FRESNEL LIGHT-BEAM CHEST EMBLEM (Y: 14..16, Z: 23..32) ---
    # Octagonal dark-iron Fresnel lens housing in center chest
    fill_sym_box(grid, 0, 2, 14, 15, 25, 30, 6)
    fill_sym_box(grid, 0, 1, 15, 16, 26, 29, 8)  # Glowing cyan Fresnel glass ring
    fill_sym_box(grid, 0, 0, 16, 16, 27, 28, 9)  # Blazing bright gold core
    fill_sym_box(grid, 1, 1, 15, 16, 27, 28, 9)  # Horizontal core flare
    # Sharp radiating golden light rays blazing outward across the striped chest!
    # Upper diagonal rays flaring toward shoulders
    fill_sym_box(grid, 2, 2, 14, 15, 29, 30, 9)
    fill_sym_box(grid, 3, 3, 14, 15, 30, 31, 9)
    fill_sym_box(grid, 4, 4, 13, 14, 31, 32, 9)
    # Horizontal side beams
    fill_sym_box(grid, 2, 3, 14, 15, 27, 28, 9)
    fill_sym_box(grid, 4, 4, 13, 14, 27, 28, 9)
    # Lower diagonal rays
    fill_sym_box(grid, 2, 2, 14, 15, 25, 25, 9)
    fill_sym_box(grid, 3, 3, 14, 14, 24, 24, 9)
    fill_sym_box(grid, 4, 4, 13, 14, 23, 23, 9)
    # Top & bottom vertical light spikes
    fill_sym_box(grid, 0, 0, 15, 15, 30, 31, 9)
    fill_sym_box(grid, 0, 0, 15, 15, 24, 25, 9)

    # --- BOLD ARMORED CATWALK GALLERY COLLAR (Z: 32..34) ---
    # Iconic protruding dark-iron lighthouse gallery ring wrapping the neck/collar
    fill_sym_box(grid, 0, 5, 7, 15, 33, 33, 6)   # Wide wrought-iron gallery deck
    fill_sym_box(grid, 0, 2, 9, 13, 33, 34, 3)   # Deep red inner watchroom neck
    # Open iron railing posts around sides & rear + front angled collar lip
    fill_sym_box(grid, 5, 5, 8, 14, 34, 34, 6)   # Side gallery rails
    fill_sym_box(grid, 0, 4, 7, 7, 34, 34, 6)    # Rear gallery rail
    fill_sym_box(grid, 3, 4, 15, 15, 34, 34, 6)  # Front angled collar rails

    # --- GLOWING BEACON-HEAD: LANTERN ROOM + RED CONICAL DOME (Z: 34..45) ---
    # Glowing lantern room head (Z: 35..39)
    fill_sym_box(grid, 0, 2, 9, 13, 35, 39, 8)   # Glowing cyan lantern glass block
    fill_sym_box(grid, 3, 3, 10, 12, 35, 39, 8)  # Rounded octagonal side glass
    fill_sym_box(grid, 0, 1, 10, 12, 36, 38, 0)  # Hollow interior of head
    # Dark-iron vertical corner mullions framing the lantern room
    fill_sym_box(grid, 3, 3, 9, 9, 35, 39, 6)    # Rear corner mullions
    fill_sym_box(grid, 3, 3, 13, 13, 35, 39, 6)  # Front corner mullions
    # Expressive blazing Fresnel-gold beacon visor/eyes on front (+Y)
    fill_sym_box(grid, 0, 2, 13, 14, 36, 38, 9)  # Radiant glowing Fresnel face
    fill_sym_box(grid, 0, 0, 14, 14, 36, 36, 6)  # Subtle iron chin/mouth guard
    fill_sym_box(grid, 1, 2, 14, 14, 38, 38, 8)  # Upper cyan glass glint
    fill_sym_box(grid, 0, 2, 13, 13, 35, 35, 6)  # Lower iron chin frame
    # Glowing gold core visible on sides & rear too
    fill_sym_box(grid, 3, 3, 11, 11, 36, 38, 9)
    fill_sym_box(grid, 0, 1, 9, 9, 36, 38, 9)

    # Dark Red Conical Dome Roof & Lightning Rod (Z: 40..45)
    fill_sym_box(grid, 0, 3, 8, 14, 40, 40, 6)   # Iron lantern eaves
    fill_sym_box(grid, 0, 3, 9, 13, 41, 41, 2)   # Maritime Red conical dome base
    fill_sym_box(grid, 0, 2, 9, 13, 42, 42, 3)   # Deep Red conical dome mid
    fill_sym_box(grid, 0, 1, 10, 12, 43, 43, 2)  # Maritime Red dome upper
    fill_sym_box(grid, 0, 0, 10, 12, 44, 44, 9)  # Golden ventilator finial
    fill_sym_box(grid, 0, 0, 11, 11, 45, 45, 6)  # Lightning rod crest

    # --- BACKPACK: COASTAL GENERATOR & LIGHT-REFLECTOR VANE WINGS (Y: 4..7) ---
    fill_sym_box(grid, 0, 3, 5, 7, 22, 31, 4)    # Coastal stone housing
    fill_sym_box(grid, 1, 2, 4, 5, 23, 25, 2)    # Red thruster band
    fill_sym_box(grid, 1, 2, 4, 5, 26, 28, 1)    # White thruster band
    fill_sym_box(grid, 1, 2, 4, 5, 29, 31, 2)    # Red top cap
    fill_sym_box(grid, 2, 2, 4, 4, 22, 22, 6)    # Iron exhaust nozzles
    # Swept Fresnel light-reflector wing fins rising heroically behind shoulders!
    for i in range(6):
        fill_sym_box(grid, 4 + i, 5 + i, 5, 6, 28 + i, 29 + i, 6)
        fill_sym_box(grid, 4 + i, 4 + i, 6, 6, 29 + i, 30 + i, 9 if i % 2 == 0 else 8)

    # --- SHOULDERS & ARMS (Z: 13..33) ---
    # Shoulder joint connector (creates crisp athletic gap from torso!)
    fill_sym_box(grid, 5, 6, 10, 12, 28, 30, 6)
    # Striped Lighthouse Shoulder Pauldrons (X_off: 6..9)
    fill_sym_box(grid, 6, 9, 9, 13, 27, 28, 1)   # White lower pauldron
    fill_sym_box(grid, 6, 9, 9, 13, 29, 30, 2)   # Red mid pauldron
    fill_sym_box(grid, 6, 9, 9, 13, 31, 32, 1)   # White upper pauldron
    fill_sym_box(grid, 7, 9, 10, 12, 33, 33, 3)  # Deep red top cap
    fill_sym_box(grid, 9, 9, 10, 12, 31, 33, 6)  # Outer iron railing trim
    fill_sym_box(grid, 7, 8, 13, 13, 29, 30, 6)  # Front shoulder porthole frame
    fill_sym_box(grid, 7, 7, 13, 13, 29, 29, 8)  # Front shoulder porthole glass
    # Hollow shoulder interior
    fill_sym_box(grid, 7, 8, 10, 12, 28, 31, 0)

    # Upper Arms (Z: 22..26) - Slim mechanical arms
    fill_sym_box(grid, 7, 8, 10, 12, 22, 26, 6)
    fill_sym_box(grid, 7, 8, 10, 12, 23, 25, 5)

    # Left Forearm (-X, viewer's right) & Right Forearm (+X, viewer's left, posed forward!)
    # Left forearm (x = 7..9 -> cx_l=16, so x=7..9)
    fill_box(grid, 7, 9, 9, 13, 15, 17, 1)       # White lower gauntlet
    fill_box(grid, 7, 9, 9, 13, 18, 20, 2)       # Red upper gauntlet
    fill_box(grid, 7, 9, 9, 13, 21, 21, 6)       # Iron elbow cuff
    fill_box(grid, 7, 7, 10, 12, 16, 19, 8)      # Cyan wrist strip
    fill_box(grid, 8, 9, 10, 12, 13, 14, 6)      # Left fist

    # Right forearm angled slightly outward & forward to wield the Beacon Halberd cleanly!
    fill_box(grid, 24, 26, 10, 13, 19, 21, 6)    # Iron elbow joint
    fill_box(grid, 25, 27, 11, 14, 17, 20, 2)    # Red upper gauntlet
    fill_box(grid, 25, 27, 12, 15, 15, 17, 1)    # White forward gauntlet
    fill_box(grid, 27, 27, 13, 14, 16, 19, 8)    # Cyan wrist beacon strip
    fill_box(grid, 26, 28, 13, 15, 13, 14, 6)    # Right fist gripping halberd

    # --- RIGHT HAND (+X, viewer's left): BEACON HALBERD / SIGNAL LANCE ---
    # Held cleanly clear to the right (x=28..29, y=14..15) so both halberd & shoulder pop!
    fill_box(grid, 28, 29, 14, 15, 6, 30, 6)     # Tall wrought-iron halberd shaft
    fill_box(grid, 28, 29, 14, 15, 5, 5, 9)      # Golden butt-cap pommel
    # Mini lighthouse beacon head & energy halberd blade at top (Z: 30..38)
    fill_box(grid, 27, 30, 13, 16, 30, 30, 6)    # Mini iron gallery ring
    fill_box(grid, 27, 30, 14, 16, 31, 34, 9)    # Glowing golden Fresnel core
    fill_box(grid, 28, 29, 16, 18, 31, 35, 8)    # Swept cyan light-beam halberd blade
    fill_box(grid, 28, 29, 18, 19, 32, 34, 9)    # Radiant golden blade edge
    fill_box(grid, 27, 30, 13, 16, 35, 35, 2)    # Mini red conical dome base
    fill_box(grid, 28, 29, 14, 15, 36, 37, 3)    # Mini red dome spire
    fill_box(grid, 28, 29, 14, 15, 38, 38, 9)    # Golden spear finial

    # --- LEFT FOREARM (-X, viewer's right): COASTAL DOOR BUCKLER SHIELD ---
    # Reuses the lighthouse's rocky stone wall & dark wooden door!
    fill_box(grid, 5, 6, 9, 15, 14, 22, 4)       # Coastal stone shield rim
    fill_box(grid, 5, 5, 10, 14, 15, 21, 7)      # Dark wooden door plank center
    fill_box(grid, 5, 5, 10, 14, 18, 18, 6)      # Iron door strap across shield
    fill_box(grid, 4, 5, 11, 13, 17, 19, 9)      # Golden beacon shield boss
    fill_box(grid, 5, 5, 9, 15, 14, 14, 5)       # Bottom granite edge
    fill_box(grid, 5, 5, 9, 15, 22, 22, 5)       # Top granite edge

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
    v_a = export_vox(model_a, "lighthouse_a.vox")
    v_b = export_vox(model_b, "lighthouse_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: COASTAL LIGHTHOUSE -> LIGHTHOUSE BEACON ROBOT",
        "1. COASTAL LIGHTHOUSE",
        "2. LIGHTHOUSE BEACON ROBOT",
        "preview_lighthouse.png",
        yaw_a=36, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"lighthouse: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
