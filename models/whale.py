import math
import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (28, 76, 152, 255),    # Deep Ocean Blue (Whale upper body / Primary armor)
    2: (54, 124, 212, 255),   # Cobalt Marine Blue (Highlights / Flippers / Armor crest)
    3: (18, 42, 92, 255),     # Abyssal Navy (Dorsal keel / Mouth seam / Dark trim)
    4: (224, 238, 248, 255),  # Pale Ice-Cream (Pleated ventral belly / Leg & chest trim)
    5: (152, 196, 228, 255),  # Pale Ice-Blue (Ventral throat grooves / Flipper underside)
    6: (38, 45, 58, 255),     # Dark Slate (Whale eye / Robot inner frame & joints)
    7: (72, 228, 255, 255),   # Bright Seafoam Cyan (Water spout / Visor / Hydro vents)
    8: (242, 250, 255, 255),  # Pure Sea Spray White (Spout crown / Eye & blade glint)
    9: (242, 196, 76, 255),   # Oceanic Gold (Helm crown crest / Belt & armor trim)
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


def set_sym(grid, x_off, y, z, col):
    """Set a symmetric pair of voxels around X center."""
    X, Y, Z = grid.shape
    if 0 <= y < Y and 0 <= z < Z:
        cx_l = X // 2 - 1 - x_off
        cx_r = X // 2 + x_off
        if 0 <= cx_l < X:
            grid[cx_l, y, z] = col
        if 0 <= cx_r < X:
            grid[cx_r, y, z] = col


def hollow_interior(grid):
    """Hollow completely unseen interior voxels (all 6 face neighbors occupied)."""
    occ = grid > 0
    interior = np.zeros_like(occ)
    interior[1:-1, 1:-1, 1:-1] = (
        occ[1:-1, 1:-1, 1:-1]
        & occ[:-2, 1:-1, 1:-1]
        & occ[2:, 1:-1, 1:-1]
        & occ[1:-1, :-2, 1:-1]
        & occ[1:-1, 2:, 1:-1]
        & occ[1:-1, 1:-1, :-2]
        & occ[1:-1, 1:-1, 2:]
    )
    grid[interior] = 0


# ==========================================
# FORM A: BLUE WHALE (32 x 48 x 22)
# ==========================================
def build_a():
    grid = np.zeros((32, 48, 22), dtype=np.uint8)
    cx_r = grid.shape[0] // 2

    # --- MAIN WHALE BODY (Y: 9..46, facing +Y) ---
    for y in range(9, 47):
        if y >= 33:
            # Massive broad rounded head tapering smoothly to rounded snout at y=46
            t = (y - 33) / 13.5  # 0 at brow -> ~0.96 at nose tip
            rx = 5.6 * math.sqrt(max(0.06, 1.0 - (t ** 2.15)))
            z_bot = 0.0 + 3.0 * (t ** 2.6)
            z_top = 10.8 - 4.4 * (t ** 1.85)
        elif y >= 22:
            # Broad majestic torso tapering gently toward tail
            t = (33 - y) / 11.0
            rx = 5.6 - 2.1 * (t ** 1.25)
            z_bot = 0.0 + 1.8 * (t ** 1.5)
            z_top = 10.8 - 1.8 * (t ** 1.2)
        else:
            # Tapered tail stock (peduncle) rising smoothly to tail flukes
            t = (22 - y) / 13.0
            rx = 3.5 - 2.2 * (t ** 0.9)
            z_bot = 1.8 + 2.5 * (t ** 1.1)
            z_top = 9.0 - 2.0 * (t ** 1.0)

        zc = 0.5 * (z_bot + z_top)
        rz = max(0.8, 0.5 * (z_top - z_bot))

        # Sweeping baleen mouth seam on head (Y: 31..46)
        if y >= 31:
            tm = (y - 31) / 15.0
            z_mouth = 4.3 + 0.5 * math.sin(tm * math.pi * 0.5) - 0.5 * math.sin(tm * math.pi)
        else:
            z_mouth = z_bot + 0.34 * (z_top - z_bot)

        max_xoff = int(math.ceil(rx))
        for x_off in range(0, max_xoff + 1):
            u = (x_off + 0.35) / max(rx, 0.5)
            for z in range(max(0, int(math.floor(z_bot))), min(21, int(math.ceil(z_top))) + 1):
                v = (z - zc) / rz
                # Slightly broader, rounded U-profile on upper head and full throat pouch
                shape_exp = 2.15 if y >= 31 else 2.0
                if (abs(u) ** shape_exp) + (abs(v) ** 2.0) <= 1.03:
                    # Determine natural Blue Whale coloration
                    if y >= 22 and z < z_mouth - 0.35:
                        # Iconic pleated ventral throat grooves & pale belly
                        col = 4 if (x_off % 2 == 0) else 5
                    elif y >= 31 and abs(z - z_mouth) <= 0.55 and u > 0.55:
                        # Crisp dark navy baleen mouth line along head & snout
                        col = 3
                    elif y < 22 and v < -0.35:
                        # Tapered pale ice-blue lower tail underside
                        col = 5
                    else:
                        # Deep ocean blue upper body with cobalt lateral mottling
                        col = 1
                        if 0.05 <= v <= 0.58 and u >= 0.45 and ((y + z) % 3 != 0):
                            col = 2
                        if y >= 35 and v > 0.55 and x_off <= 2:
                            col = 2  # Cobalt rostral brow sheen
                    set_sym(grid, x_off, y, z, col)

        # Sleek Abyssal Navy dorsal keel ridge along centerline
        top_z = -1
        for z in range(21, -1, -1):
            if grid[cx_r, y, z] > 0:
                top_z = z
                break
        if top_z >= 0 and 10 <= y <= 43:
            set_sym(grid, 0, y, top_z, 3)

    # --- FRIENDLY / NOBLE EYES (placed cleanly on outermost head flank, Y: 33..34, Z: 5) ---
    for ey in (33, 34):
        outer_x = 0
        for x_off in range(15, -1, -1):
            if grid[cx_r + x_off, ey, 5] > 0:
                outer_x = x_off
                break
        if outer_x > 0:
            # Dark slate pupil + crisp white glint + cobalt brow
            set_sym(grid, outer_x, ey, 5, 6 if ey == 33 else 8)
            set_sym(grid, outer_x, ey, 6, 2)
            if ey == 33:
                set_sym(grid, outer_x, 32, 5, 6)
                set_sym(grid, outer_x, 34, 4, 4)

    # --- BLOWHOLE & PLAYFUL WHITE-CYAN WATER SPOUT (Y: 32..34, Z: 11..20) ---
    fill_sym_box(grid, 0, 1, 32, 34, 11, 11, 3)  # Blowhole splashguard ridge
    fill_sym_box(grid, 0, 0, 33, 33, 11, 11, 6)  # Twin blowhole nostrils
    # Rising central column (6-connected solid stream)
    fill_sym_box(grid, 0, 0, 33, 33, 12, 16, 7)
    fill_sym_box(grid, 0, 0, 33, 33, 14, 17, 8)
    fill_sym_box(grid, 0, 0, 32, 34, 16, 17, 7)
    # Graceful twin-fountain spray arching outward to left & right
    fill_sym_box(grid, 1, 2, 33, 33, 17, 18, 7)
    fill_sym_box(grid, 1, 2, 33, 33, 18, 19, 8)
    fill_sym_box(grid, 2, 3, 33, 33, 19, 19, 8)
    fill_sym_box(grid, 3, 4, 33, 33, 18, 18, 7)
    fill_sym_box(grid, 4, 4, 33, 33, 17, 17, 8)
    # Small forward/aft mist plumes connected at top of spout
    fill_sym_box(grid, 0, 0, 31, 32, 18, 18, 8)
    fill_sym_box(grid, 0, 0, 34, 35, 18, 18, 8)

    # --- SMALL CURVED BLUE WHALE DORSAL FIN (Y: 14..19, Z: 8..11) ---
    fill_sym_box(grid, 0, 0, 15, 19, 8, 9, 1)
    fill_sym_box(grid, 0, 0, 15, 17, 10, 10, 2)
    fill_sym_box(grid, 0, 0, 14, 15, 11, 11, 3)

    # --- LONG GRACEFUL PECTORAL FLIPPERS (Y: 18..31, x_off: 4..14) ---
    for x_off in range(4, 15):
        t = (x_off - 4) / 10.0
        y_front = int(round(30.5 - 8.5 * (t ** 1.05)))
        y_back = int(round(25.0 - 5.5 * (t ** 0.9)))
        if y_back > y_front - 1:
            y_back = y_front - 1
        z_top = int(round(3.3 - 1.4 * t))
        z_bot = z_top - (1 if x_off <= 10 else 0)
        for y in range(y_back, y_front + 1):
            # Underside pale ice-blue/cream
            if z_bot < z_top:
                set_sym(grid, x_off, y, z_bot, 5 if y < y_front else 4)
            # Upper flipper deep ocean blue with cobalt leading edge & navy trailing edge
            if y == y_front:
                top_col = 2
            elif y == y_back and x_off >= 7:
                top_col = 3
            else:
                top_col = 1
            set_sym(grid, x_off, y, z_top, top_col)
        # Ensure continuous Z overlap between adjacent x_off steps
        if x_off > 4:
            prev_z = int(round(3.3 - 1.4 * ((x_off - 5) / 10.0)))
            if prev_z > z_top:
                set_sym(grid, x_off, (y_front + y_back) // 2, prev_z, 1)

    # --- WIDE HORIZONTAL TWIN-LOBED TAIL FLUKES (Y: 1..10, x_off: 0..12, Z: 5..6) ---
    # Tail root bridge (creates crisp central V-notch behind y=6)
    fill_sym_box(grid, 0, 1, 6, 10, 5, 6, 1)
    fill_sym_box(grid, 0, 0, 6, 10, 6, 6, 3)
    for x_off in range(1, 13):
        t = (x_off - 1) / 11.0
        y_front = int(round(9.5 - 5.2 * (t ** 1.15)))
        y_back = int(round(5.0 - 3.8 * math.sin(t * math.pi * 0.72)))
        if y_back > y_front:
            y_back = y_front
        for y in range(y_back, y_front + 1):
            # Thicker inner fluke with pale underside
            if x_off <= 8:
                set_sym(grid, x_off, y, 5, 5)
            # Upper fluke surface
            if y == y_back:
                col = 3  # Abyssal navy trailing edge
            elif y == y_front or (x_off in (4, 5, 6, 7) and y == y_front - 1):
                col = 2  # Cobalt marine leading edge
            else:
                col = 1
            set_sym(grid, x_off, y, 6, col)

    # Hollow unseen bulky body interior so voxel count stays sleek (1300-2450)
    hollow_interior(grid)
    return grid


# ==========================================
# FORM B: WHALE LEVIATHAN ROBOT (36 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((36, 24, 42), dtype=np.uint8)

    # --- FEET (Z: 0..3) - Grounded ocean-blue & cream armored boots ---
    fill_sym_box(grid, 2, 6, 7, 16, 0, 1, 6)    # Heavy dark slate soles
    fill_sym_box(grid, 2, 6, 11, 17, 1, 2, 1)   # Deep ocean blue toe armor
    fill_sym_box(grid, 3, 5, 16, 18, 1, 2, 2)   # Cobalt armored toe caps
    fill_sym_box(grid, 3, 5, 12, 16, 2, 3, 4)   # Pale cream forefoot plates
    fill_sym_box(grid, 2, 6, 9, 13, 2, 3, 2)    # Cobalt ankle collar
    fill_sym_box(grid, 3, 5, 6, 8, 1, 2, 3)     # Heel stabilizer block
    fill_sym_box(grid, 4, 4, 6, 6, 1, 1, 7)     # Rear heel water-jet glow

    # --- LOWER LEGS / SHINS (Z: 4..14) - Ocean-blue armor + pleated belly shins + water-jet thrusters ---
    fill_sym_box(grid, 2, 5, 9, 14, 4, 14, 1)   # Main deep-blue shin armor
    fill_sym_box(grid, 5, 6, 9, 13, 5, 12, 1)   # Flared outer calf armor
    fill_sym_box(grid, 6, 6, 10, 12, 6, 12, 2)  # Cobalt hydrodynamic side fin
    fill_sym_box(grid, 6, 6, 10, 11, 4, 5, 3)   # Lower ankle guard trim
    # Pleated pale cream & ice-blue whale-belly shin panels
    fill_sym_box(grid, 3, 4, 14, 15, 4, 12, 4)
    fill_sym_box(grid, 3, 3, 15, 15, 5, 11, 5)  # Vertical ventral pleat groove
    fill_sym_box(grid, 4, 4, 15, 15, 5, 11, 4)
    # Heroic Knee Guards
    fill_sym_box(grid, 2, 5, 14, 16, 12, 15, 2)
    fill_sym_box(grid, 2, 5, 14, 15, 12, 12, 3)
    fill_sym_box(grid, 3, 4, 16, 16, 13, 14, 9) # Gold knee emblem
    # Calf Water-Jet Thrusters (back of lower legs)
    fill_sym_box(grid, 3, 5, 7, 9, 6, 11, 6)    # Thruster housing
    fill_sym_box(grid, 3, 5, 8, 9, 10, 11, 3)   # Navy upper cowling
    fill_sym_box(grid, 3, 5, 6, 7, 6, 9, 7)     # Glowing cyan water-jet nozzles
    fill_sym_box(grid, 4, 4, 6, 6, 7, 8, 8)     # Bright sea-spray core

    # --- THIGHS (Z: 15..20) - Cream & slate armored thighs ---
    fill_sym_box(grid, 2, 4, 10, 13, 14, 20, 6) # Inner mechanical frame
    fill_sym_box(grid, 2, 5, 10, 14, 15, 19, 4) # Pale cream armored thigh plates
    fill_sym_box(grid, 2, 4, 14, 14, 16, 18, 5) # Ice-blue inner front contour
    fill_sym_box(grid, 5, 5, 11, 13, 16, 19, 2) # Cobalt outer thigh accent

    # --- WAIST / PELVIS (Z: 20..24) ---
    fill_sym_box(grid, 0, 5, 9, 14, 20, 23, 6)  # Dark slate pelvis frame
    fill_sym_box(grid, 2, 5, 14, 15, 19, 22, 1) # Deep-blue front skirt armor
    fill_sym_box(grid, 2, 5, 14, 15, 19, 19, 4) # Cream lower skirt trim
    fill_sym_box(grid, 2, 4, 15, 15, 21, 22, 2) # Cobalt skirt ridge
    fill_sym_box(grid, 0, 1, 13, 16, 19, 23, 2) # Center codpiece
    fill_sym_box(grid, 0, 1, 15, 16, 22, 23, 9) # Oceanic gold belt buckle
    fill_sym_box(grid, 0, 0, 16, 16, 22, 22, 7) # Cyan center belt core
    fill_sym_box(grid, 5, 6, 10, 13, 19, 22, 1) # Side hip skirts
    fill_sym_box(grid, 6, 6, 11, 12, 20, 21, 2)
    fill_sym_box(grid, 0, 4, 8, 9, 20, 22, 3)   # Rear skirt plate
    # Armored abdomen / waist taper connecting to massive whale chest
    fill_sym_box(grid, 0, 4, 9, 14, 23, 25, 6)
    fill_sym_box(grid, 0, 3, 14, 15, 23, 24, 5) # Ice-blue ribbed midriff

    # --- TORSO / CHEST (Z: 25..34) - MASSIVE BLUE WHALE HEAD CHEST! ---
    # Core torso housing
    fill_sym_box(grid, 0, 6, 9, 16, 25, 34, 1)
    fill_sym_box(grid, 0, 5, 9, 14, 25, 26, 3)  # Lower chest dark trim

    # Massive protruding rounded Blue Whale Head forming the heroic broad chest (Y: 15..21, Z: 25..33)
    # Lower whale jaw with unmistakable pleated cream & ice-blue ventral throat grooves (Z: 25..28)
    for y_j, x_max in ((16, 5), (17, 5), (18, 4), (19, 3), (20, 2)):
        for x_off in range(0, x_max + 1):
            pleat_col = 4 if (x_off % 2 == 0) else 5
            z_lo = 25 if y_j <= 18 else 26
            fill_sym_box(grid, x_off, x_off, y_j, y_j, z_lo, 28, pleat_col)

    # Crisp Abyssal Navy whale mouth line + glowing cyan baleen energy vent (Z: 28..29)
    for y_m, x_max in ((16, 5), (17, 5), (18, 4), (19, 4), (20, 3), (21, 2)):
        fill_sym_box(grid, 0, x_max, y_m, y_m, 28, 29, 3)
    fill_sym_box(grid, 0, 2, 20, 21, 28, 28, 7)  # Glowing cyan hydro-baleen core vent
    fill_sym_box(grid, 0, 0, 21, 21, 28, 28, 8)  # Bright white center spark

    # Broad massive rounded Deep-Ocean-Blue upper whale head brow (Z: 29..33)
    for y_h, x_max, z_hi in (
        (16, 6, 34),
        (17, 5, 33),
        (18, 5, 33),
        (19, 4, 32),
        (20, 3, 31),
        (21, 2, 30),
    ):
        fill_sym_box(grid, 0, x_max, y_h, y_h, 29, z_hi, 1)
        # Cobalt rostral sheen across upper brow
        if y_h <= 20:
            fill_sym_box(grid, 0, max(0, x_max - 1), y_h, y_h, z_hi, z_hi, 2)
    # Center dorsal rostral ridge along whale-head chest
    fill_sym_box(grid, 0, 0, 16, 21, 30, 33, 3)
    fill_sym_box(grid, 0, 0, 18, 20, 31, 32, 9)  # Subtle gold oceanic prow emblem

    # Whale eye sensors on the flanks of the whale-head chest!
    fill_sym_box(grid, 5, 5, 17, 18, 30, 30, 6)
    fill_sym_box(grid, 5, 5, 18, 18, 30, 30, 7)  # Glowing cyan whale eye sensor
    fill_sym_box(grid, 5, 5, 17, 18, 31, 31, 2)  # Cobalt brow above eye

    # Twin Blowhole Collar Vents flanking the neck (reprising Form A's blowhole + cyan spout!)
    fill_sym_box(grid, 2, 4, 13, 16, 34, 35, 3)  # Navy blowhole collar frame
    fill_sym_box(grid, 2, 3, 14, 16, 35, 35, 7)  # Glowing cyan blowhole vents
    fill_sym_box(grid, 3, 3, 15, 15, 35, 35, 8)  # White spray highlight
    fill_sym_box(grid, 4, 4, 14, 15, 34, 35, 9)  # Gold collar accent

    # --- BACKPACK & SWEEPING HORIZONTAL TAIL-FLUKE WINGS (Y: 2..8, Z: 24..38) ---
    # Tail-stock dorsal backpack
    fill_sym_box(grid, 0, 4, 5, 8, 25, 33, 1)
    fill_sym_box(grid, 0, 3, 4, 5, 26, 32, 3)
    # Small whale dorsal fin mounted centrally on backpack spine
    fill_sym_box(grid, 0, 0, 3, 5, 27, 32, 2)
    fill_sym_box(grid, 0, 0, 2, 3, 29, 31, 3)
    # Twin dorsal water-jet thrusters
    fill_sym_box(grid, 2, 3, 4, 6, 24, 26, 6)
    fill_sym_box(grid, 2, 3, 4, 4, 24, 25, 7)
    fill_sym_box(grid, 2, 2, 4, 4, 24, 24, 8)

    # Sweeping Horizontal Oceanic Wings (= Form A's Wide Twin-Lobed Tail Flukes!)
    # Solid root mounts connecting to backpack at x_off = 3..4
    fill_sym_box(grid, 3, 5, 5, 7, 29, 32, 3)
    for x_off in range(4, 17):
        t = (x_off - 4) / 12.0
        # Sweeping outward horizontally with graceful heroic dihedral & crescent fluke curve
        z_top = int(round(32.5 + 5.2 * (t ** 0.95)))
        z_bot = int(round(28.5 + 7.2 * (t ** 1.15)))
        if z_bot > z_top - 1:
            z_bot = z_top - 1
        y_mid = int(round(6.2 - 2.6 * (t ** 1.1)))
        y_lo = max(2, y_mid - (1 if x_off <= 11 else 0))
        y_hi = min(8, y_mid + (1 if x_off <= 8 else 0))

        for z in range(z_bot, z_top + 1):
            for y in range(y_lo, y_hi + 1):
                if z == z_top:
                    col = 2  # Cobalt sweeping upper edge
                elif z == z_bot:
                    col = 3  # Abyssal navy trailing fluke edge
                elif y == y_lo and x_off <= 12:
                    col = 5  # Pale ice-blue inner rear fluke face
                else:
                    col = 1  # Deep ocean blue main fluke wing
                set_sym(grid, x_off, y, z, col)
        # Glowing cyan hydro-slit near wing root
        if x_off in (5, 6, 7):
            set_sym(grid, x_off, y_hi, z_top - 1, 7)

    # --- SHOULDERS & ARMORED FLIPPER-ARMS (Z: 13..35) ---
    # Broad Oceanic Shoulder Pauldrons
    fill_sym_box(grid, 6, 10, 9, 15, 29, 34, 1)
    fill_sym_box(grid, 7, 10, 10, 14, 34, 35, 2)  # Cobalt upper shoulder crest
    fill_sym_box(grid, 10, 10, 10, 14, 30, 33, 2) # Outer pauldron stripe
    fill_sym_box(grid, 6, 10, 10, 14, 29, 29, 4)  # Pale cream lower pauldron trim
    fill_sym_box(grid, 8, 9, 15, 15, 31, 32, 9)   # Gold front shoulder stud
    fill_sym_box(grid, 7, 9, 14, 15, 32, 33, 3)   # Navy vent recess

    # Upper Arms (dark slate joints + ice-blue inner armor)
    fill_sym_box(grid, 7, 9, 10, 13, 23, 28, 6)
    fill_sym_box(grid, 7, 8, 11, 13, 24, 27, 5)

    # Forearms + Iconic Pectoral Flipper-Gauntlets / Forearm Shields!
    fill_sym_box(grid, 7, 9, 10, 14, 16, 22, 1)   # Main deep-blue forearm
    fill_sym_box(grid, 7, 8, 13, 14, 17, 21, 4)   # Pale cream inner wrist plate
    # Sculpted Long Blue Pectoral Flipper mounted along outer forearm (x_off: 10..12, Z: 13..25)
    for z_f in range(13, 26):
        tf = (25 - z_f) / 12.0  # 0 at elbow top -> 1 at sleek lower flipper tip
        x_out = 10 + (2 if 15 <= z_f <= 22 else (1 if 14 <= z_f <= 24 else 0))
        y_f0 = int(round(10.0 + 1.5 * tf))
        y_f1 = int(round(14.5 + 1.2 * math.sin(tf * math.pi)))
        for x_off in range(10, x_out + 1):
            for y in range(y_f0, y_f1 + 1):
                if y == y_f1:
                    col = 2  # Cobalt flipper leading edge
                elif x_off == x_out and z_f in (17, 18, 19, 20):
                    col = 7  # Glowing cyan hydro-shield edge
                elif y == y_f0:
                    col = 3  # Abyssal navy trailing edge
                elif x_off == 10 and z_f <= 16:
                    col = 5  # Pale ice-blue underside
                else:
                    col = 1  # Deep ocean blue flipper armor
                set_sym(grid, x_off, y, z_f, col)

    # Fists (Z: 14..15)
    fill_sym_box(grid, 7, 9, 11, 13, 14, 15, 6)
    fill_sym_box(grid, 8, 9, 13, 13, 14, 15, 3)

    # Right-Hand Hydro-Fin Blade (+X side, extending forward cleanly along +Y)
    cx_r = grid.shape[0] // 2
    fill_box(grid, cx_r + 7, cx_r + 9, 14, 16, 14, 15, 3)   # Navy hilt
    fill_box(grid, cx_r + 8, cx_r + 8, 15, 16, 15, 16, 9)   # Gold handguard
    fill_box(grid, cx_r + 8, cx_r + 9, 16, 22, 14, 16, 7)   # Glowing cyan hydro-blade
    fill_box(grid, cx_r + 8, cx_r + 8, 16, 21, 15, 15, 2)   # Cobalt blade spine
    fill_box(grid, cx_r + 9, cx_r + 9, 18, 22, 15, 15, 8)   # White razor edge glint
    fill_box(grid, cx_r + 8, cx_r + 8, 22, 23, 15, 15, 8)   # Sleek blade tip

    # --- NOBLE OCEANIC HELM (Z: 34..41) ---
    fill_sym_box(grid, 0, 1, 11, 13, 34, 35, 6)   # Neck joint
    fill_sym_box(grid, 0, 2, 10, 14, 35, 39, 1)   # Deep-blue helmet shell
    fill_sym_box(grid, 0, 2, 10, 13, 40, 40, 2)   # Rounded cobalt crown
    fill_sym_box(grid, 0, 0, 10, 14, 40, 41, 2)   # Central crest ridge
    # Faceplate & Glowing Cyan Visor
    fill_sym_box(grid, 0, 1, 14, 15, 35, 36, 4)   # Pale cream faceplate & chin
    fill_sym_box(grid, 0, 2, 14, 15, 37, 38, 7)   # Bright cyan oceanic visor!
    fill_sym_box(grid, 0, 0, 15, 15, 37, 38, 8)   # Visor center glint
    # Noble Oceanic Gold V-Crest Crown
    fill_sym_box(grid, 0, 0, 15, 15, 39, 40, 9)   # Center crown jewel
    fill_sym_box(grid, 1, 1, 14, 15, 39, 40, 9)
    fill_sym_box(grid, 2, 3, 14, 14, 40, 41, 9)   # Sweeping gold V-crest tips
    # Swept-back Cobalt Ear-Fins
    fill_sym_box(grid, 3, 3, 10, 13, 36, 39, 2)
    fill_sym_box(grid, 3, 3, 9, 10, 38, 39, 4)    # Cream fin tip

    # Hollow unseen bulky interior of chest/torso so voxel count stays sleek (2200-3500)
    hollow_interior(grid)
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
    v_a = export_vox(model_a, "whale_a.vox")
    v_b = export_vox(model_b, "whale_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: BLUE WHALE -> WHALE LEVIATHAN ROBOT",
        "1. BLUE WHALE",
        "2. WHALE LEVIATHAN ROBOT",
        "preview_whale.png",
        yaw_a=44, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"whale: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
