import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (84, 46, 26, 255),     # Rich Dark Mahogany Hull Wood
    2: (152, 98, 54, 255),    # Warm Teak / Tan Planked Wood
    3: (246, 239, 220, 255),  # Crisp Cream-White Sail Canvas
    4: (204, 192, 164, 255),  # Shaded Linen Sail / Naval Trim
    5: (212, 156, 38, 255),   # Burnished Galleon Gold Trim
    6: (204, 36, 46, 255),    # Crimson Pennant / Captain Crest
    7: (28, 42, 68, 255),     # Deep Naval Blue Coat / Keel
    8: (96, 108, 124, 255),   # Forged Iron Cannons / Joints
    9: (255, 236, 118, 255),  # Glowing Warm Lantern Amber / Visor
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


# ==========================================
# FORM A: TALL SAILING SHIP (20 x 48 x 40)
# ==========================================
def build_a():
    grid = np.zeros((20, 48, 40), dtype=np.uint8)

    # Helper: half-width profile along Y (stern y=3 to bow prow y=39)
    def hull_hw(y):
        if y < 3 or y > 39:
            return -1
        if y == 3:
            return 3
        if y <= 5:
            return 4
        if y <= 27:
            return 5
        if y <= 30:
            return 4
        if y <= 33:
            return 3
        if y <= 35:
            return 2
        if y <= 37:
            return 1
        return 0

    # --- HOLLOW PLANKED HULL (Y: 3..39, Z: 0..8) ---
    # Grounded deep keel & rudder
    fill_sym_box(grid, 0, 0, 5, 36, 0, 1, 7)
    fill_sym_box(grid, 0, 0, 2, 4, 1, 4, 1)  # Rudder at -Y
    fill_sym_box(grid, 0, 1, 7, 31, 0, 0, 1)  # Stable keel base

    for y in range(3, 40):
        hw = hull_hw(y)
        # Hull rises from z=1 to z=7 (and z=8 at forecastle/bulwarks)
        for z in range(1, 8):
            if z == 1:
                w = max(0, hw - 3)
            elif z == 2:
                w = max(0, hw - 2)
            elif z == 3:
                w = max(0, hw - 1)
            elif z <= 5:
                w = hw
            else:
                # Subtle tumblehome curving inward at top of hull
                w = max(0, hw - 1) if hw >= 4 else hw

            # Plank color banding: dark mahogany, warm teak strake, golden gunport trim
            if z == 1:
                col = 7 if y % 3 == 0 else 1
            elif z == 2 or z == 3:
                col = 1
            elif z == 4:
                col = 2
            elif z == 5:
                col = 1
            elif z == 6:
                col = 5  # Iconic golden hull trim band
            else:
                col = 1

            # Hollow hull: fill only bottom steps and outer walls + bow/stern caps
            if y == 3 or y >= 37:
                fill_sym_box(grid, 0, w, y, y, z, z, col)
            elif z <= 2:
                fill_sym_box(grid, 0, w, y, y, z, z, col)
            else:
                prev_w = max(0, hw - (3 if z - 1 == 1 else (2 if z - 1 == 2 else (1 if z - 1 == 3 else 0))))
                # Connect cleanly across width steps
                w_in = min(w, prev_w)
                fill_sym_box(grid, w_in, w, y, y, z, z, col)

        # Main wooden planked deck at z=6 (hollow underneath!)
        if 4 <= y <= 36:
            deck_w = max(0, hw - 1) if hw >= 4 else max(0, hw - 1)
            fill_sym_box(grid, 0, deck_w, y, y, 6, 6, 2)

        # Bulwark railings along midship & forecastle (z=8)
        if 11 <= y <= 36:
            rw = max(0, hw - 1) if hw >= 4 else hw
            fill_sym_box(grid, rw, rw, y, y, 8, 8, 2 if y % 2 == 0 else 1)

    # Golden gunport trim & iron cannons along midship flanks (Y: 13..29)
    for cy in (14, 18, 22, 26):
        fill_sym_box(grid, 5, 5, cy, cy + 1, 5, 5, 7)      # Dark gunport recess
        fill_sym_box(grid, 5, 5, cy, cy, 4, 4, 5)          # Gold sill accent
        fill_sym_box(grid, 5, 6, cy, cy, 5, 5, 8)          # Iron cannon muzzle peeking out

    # Deck hatches & companionway (midship detail)
    fill_sym_box(grid, 0, 1, 23, 26, 7, 7, 1)
    fill_sym_box(grid, 0, 1, 24, 25, 7, 7, 7)

    # --- FORECASTLE & BOWSPRIT (+Y: 31..47) ---
    # Raised forecastle deck (y=31..37)
    for y in range(31, 38):
        hw = hull_hw(y)
        rw = max(0, hw - 1) if hw >= 4 else hw
        fill_sym_box(grid, 0, rw, y, y, 8, 8, 2)
        fill_sym_box(grid, rw, rw, y, y, 9, 9, 5 if y in (31, 34, 37) else 1)
    # Pointed prow beakhead & golden figurehead
    fill_sym_box(grid, 0, 0, 38, 40, 5, 7, 1)
    fill_sym_box(grid, 0, 0, 39, 41, 6, 7, 5)   # Golden figurehead
    fill_sym_box(grid, 0, 0, 41, 41, 7, 8, 5)

    # Diagonal wooden bowsprit jutting forward (+Y: 36..47, Z: 8..13)
    bowsprit_pts = [
        (36, 8), (37, 8), (38, 9), (39, 9), (40, 10),
        (41, 10), (42, 11), (43, 11), (44, 12), (45, 12), (46, 13), (47, 13),
    ]
    for by, bz in bowsprit_pts:
        fill_sym_box(grid, 0, 0, by, by, bz, bz, 2)
    # Gold collar & spritsail yard under bowsprit
    fill_sym_box(grid, 0, 3, 42, 42, 10, 10, 2)
    fill_sym_box(grid, 0, 2, 42, 43, 8, 9, 3)   # Small crisp spritsail
    fill_sym_box(grid, 0, 1, 43, 43, 8, 8, 4)

    # --- RAISED STERN CASTLE (-Y: 2..13, Z: 7..16) ---
    # Quarterdeck step (y=10..13, z=7..9)
    for y in range(10, 14):
        fill_sym_box(grid, 0, 4, y, y, 8, 8, 2)
        fill_sym_box(grid, 4, 4, y, y, 7, 9, 1)
        fill_sym_box(grid, 4, 4, y, y, 9, 9, 5)
    # Tall stern castle (hollow inside! y=3..10, z=7..12)
    for y in range(3, 11):
        sw = 3 if y <= 4 else 4
        for z in range(7, 13):
            col = 5 if z in (9, 12) else 1
            if y == 3 or y == 10:
                fill_sym_box(grid, 0, sw, y, y, z, z, col)
            else:
                fill_sym_box(grid, sw, sw, y, y, z, z, col)
        # Poop deck floor at z=12
        fill_sym_box(grid, 0, sw - 1, y, y, 12, 12, 2)
        # Golden poop deck railings at z=13
        fill_sym_box(grid, sw, sw, y, y, 13, 13, 5 if y % 2 == 1 else 2)
    fill_sym_box(grid, 0, 3, 3, 3, 13, 13, 5)

    # Glowing amber stern castle windows across transom (y=3) and aft gallery sides
    fill_sym_box(grid, 0, 2, 3, 3, 10, 11, 9)   # Glowing stern transom windows
    fill_sym_box(grid, 1, 1, 3, 3, 10, 11, 5)   # Gold mullions
    fill_sym_box(grid, 0, 2, 3, 3, 8, 8, 9)     # Lower cabin windows
    fill_sym_box(grid, 1, 1, 3, 3, 8, 8, 5)
    # Aft side gallery glowing windows
    for wy in (5, 7, 9):
        fill_sym_box(grid, 4, 4, wy, wy, 10, 11, 9)
    # Ornate Stern Lantern perched at the very back (-Y: y=2..3, z=14..16)
    fill_sym_box(grid, 0, 0, 2, 3, 13, 13, 5)
    fill_sym_box(grid, 0, 0, 2, 2, 14, 15, 9)
    fill_sym_box(grid, 0, 0, 2, 2, 16, 16, 5)

    # --- HELPER FOR WIND-FILLED BILLOWING SQUARE SAILS ---
    def add_billowing_sail(y_mast, z_bot, z_top, half_w, billow_max, trim_red=False):
        # Upper and lower wooden yardarms attached to mast
        fill_sym_box(grid, 0, half_w + 1, y_mast + 1, y_mast + 1, z_top, z_top, 2)
        fill_sym_box(grid, half_w + 1, half_w + 1, y_mast + 1, y_mast + 1, z_top, z_top, 5)
        fill_sym_box(grid, 0, half_w, y_mast + 1, y_mast + 1, z_bot, z_bot, 2)

        h = z_top - z_bot
        for z in range(z_bot, z_top + 1):
            t_z = (z - z_bot) / max(1.0, float(h))
            # Smooth wind belly curve bulging forward (+Y)
            belly_z = np.sin(t_z * np.pi)
            # Slight taper narrower near top yardarm
            w_z = half_w - int((1.0 - t_z) * 0.5)
            prev_y = None
            for x_off in range(0, w_z + 1):
                t_x = x_off / max(1.0, float(w_z))
                belly_x = np.cos(t_x * np.pi * 0.45)
                y_off = int(round(billow_max * belly_z * belly_x))
                sy = y_mast + 1 + y_off

                # Shading: crisp cream-white canvas with shaded linen seams & borders
                if z == z_bot or z == z_top or x_off == w_z:
                    scol = 4
                elif trim_red and z == (z_bot + z_top) // 2 and x_off <= max(1, w_z // 2):
                    scol = 6  # Crimson naval emblem stripe across center of main sail
                elif x_off % 3 == 2:
                    scol = 4
                else:
                    scol = 3

                fill_sym_box(grid, x_off, x_off, sy, sy, z, z, scol)
                # Ensure 6-connected continuity horizontally when billow steps in Y
                if prev_y is not None and abs(sy - prev_y) > 0:
                    y_lo, y_hi = min(sy, prev_y), max(sy, prev_y)
                    fill_sym_box(grid, x_off, x_off, y_lo, y_hi, z, z, scol)
                prev_y = sy
                # Ensure 6-connected continuity vertically with z-1
                if z > z_bot:
                    t_zp = (z - 1 - z_bot) / max(1.0, float(h))
                    y_below = y_mast + 1 + int(round(billow_max * np.sin(t_zp * np.pi) * belly_x))
                    if abs(sy - y_below) > 1:
                        y_lo, y_hi = min(sy, y_below), max(sy, y_below)
                        fill_sym_box(grid, x_off, x_off, y_lo, y_hi, z, z, scol)

    # --- MAIN MAST (Y: 18..19, Z: 6..37) ---
    fill_sym_box(grid, 0, 0, 18, 19, 6, 24, 1)
    fill_sym_box(grid, 0, 0, 18, 19, 10, 10, 5)  # Mast gold band
    fill_sym_box(grid, 0, 0, 19, 19, 25, 37, 2)  # Upper topmast
    fill_sym_box(grid, 0, 0, 19, 19, 37, 38, 5)  # Gold masthead finial

    # Main Crow's Nest (Z: 23..25)
    fill_sym_box(grid, 0, 2, 17, 20, 23, 23, 1)
    fill_sym_box(grid, 0, 2, 17, 20, 24, 24, 2)
    fill_sym_box(grid, 0, 1, 18, 19, 24, 24, 1)
    fill_sym_box(grid, 2, 2, 17, 20, 24, 24, 5)

    # Main Lower Course Sail & Upper Topsail (billowing forward +Y!)
    add_billowing_sail(y_mast=19, z_bot=11, z_top=22, half_w=7, billow_max=3.2, trim_red=True)
    add_billowing_sail(y_mast=19, z_bot=26, z_top=34, half_w=5, billow_max=2.4, trim_red=False)

    # Fluttering Crimson Main Pennant Flag streaming forward (+Y) at masthead!
    pennant_main = [
        (20, 36, 37), (21, 36, 37), (22, 36, 38), (23, 37, 38),
        (24, 37, 38), (25, 36, 37), (26, 36, 37), (27, 37, 37), (28, 37, 37),
    ]
    for py, pz0, pz1 in pennant_main:
        fill_box(grid, 9, 10, py, py, pz0, pz1, 6)
    fill_box(grid, 9, 10, 20, 21, 37, 37, 5)  # Gold canton accent

    # --- FORE MAST (Y: 29..30, Z: 6..31) ---
    fill_sym_box(grid, 0, 0, 29, 30, 6, 20, 1)
    fill_sym_box(grid, 0, 0, 30, 30, 21, 31, 2)
    fill_sym_box(grid, 0, 0, 30, 30, 31, 32, 5)  # Gold finial

    # Fore Crow's Nest (Z: 20..21)
    fill_sym_box(grid, 0, 1, 28, 31, 20, 21, 1)
    fill_sym_box(grid, 1, 1, 28, 31, 21, 21, 5)

    # Fore Lower Sail & Fore Topsail
    add_billowing_sail(y_mast=30, z_bot=11, z_top=19, half_w=5, billow_max=2.6, trim_red=False)
    add_billowing_sail(y_mast=30, z_bot=23, z_top=29, half_w=4, billow_max=2.0, trim_red=False)

    # Fore Crimson Pennant streaming +Y
    pennant_fore = [
        (31, 30, 31), (32, 30, 31), (33, 31, 31), (34, 30, 31), (35, 31, 31), (36, 31, 31),
    ]
    for py, pz0, pz1 in pennant_fore:
        fill_box(grid, 9, 10, py, py, pz0, pz1, 6)

    # --- SHROUD RIGGING LINES (connect masts to gunwales for silhouette richness) ---
    # Main shrouds (connecting hull rail at y=18 to crow's nest)
    for k in range(1, 15):
        sz = 9 + k
        sx = max(2, 4 - (k * 2) // 14)
        fill_sym_box(grid, sx, sx, 18, 18, sz, sz, 7)

    # Fore-to-bowsprit jib sail (crisp diagonal triangular headsail)
    for step in range(9):
        jy = 37 + step
        jz_bot = 10 + (step // 2)
        jz_top = 19 - step
        if jz_top >= jz_bot:
            fill_box(grid, 9, 10, jy, jy, jz_bot, jz_top, 3 if step % 2 == 0 else 4)
    # Connect jib cleanly to foremast stay
    for step in range(6):
        fill_box(grid, 9, 10, 31 + step, 31 + step, 23 - step, 24 - step, 4)

    return grid


# ==========================================
# FORM B: GALLEON CAPTAIN ROBOT (36 x 26 x 44)
# ==========================================
def build_b():
    grid = np.zeros((36, 26, 44), dtype=np.uint8)

    # --- 1. SHIP-PROW BOOTS (Z: 0..4) - Split hull bows as rugged boots ---
    # Heavy grounded navy/iron keel sole
    fill_sym_box(grid, 2, 5, 9, 18, 0, 1, 7)
    fill_sym_box(grid, 3, 4, 18, 20, 0, 1, 1)
    # Wooden ship-prow upper boot & pointed prow toes (+Y)
    fill_sym_box(grid, 2, 5, 10, 18, 1, 3, 1)
    fill_sym_box(grid, 2, 5, 10, 17, 2, 2, 2)   # Teak plank strake
    fill_sym_box(grid, 2, 5, 11, 18, 3, 3, 5)   # Golden hull trim on boots
    # Pointed prow toe cap with golden figurehead tip
    fill_sym_box(grid, 3, 4, 19, 20, 1, 3, 1)
    fill_sym_box(grid, 3, 4, 21, 21, 1, 2, 5)
    fill_sym_box(grid, 3, 4, 22, 22, 2, 2, 5)
    # Iron rudder heel spurs at back (-Y)
    fill_sym_box(grid, 3, 4, 8, 9, 0, 2, 8)

    # --- 2. LOWER LEGS / SPLIT HULL GREAVES (Z: 4..14) ---
    fill_sym_box(grid, 2, 5, 10, 15, 4, 14, 1)  # Dark mahogany split-hull greaves
    fill_sym_box(grid, 2, 5, 11, 14, 4, 4, 2)   # Teak cuff
    # Vertical teak hull planking & golden gunport trim lines
    fill_sym_box(grid, 3, 4, 15, 15, 5, 13, 2)
    fill_sym_box(grid, 2, 2, 15, 15, 5, 13, 5)  # Inner gold trim
    fill_sym_box(grid, 5, 5, 10, 15, 5, 13, 1)
    fill_sym_box(grid, 5, 5, 14, 14, 5, 13, 5)  # Outer gold hull trim
    fill_sym_box(grid, 5, 5, 11, 11, 5, 13, 2)
    # Authentic Galleon Gunports & mini iron cannons on outer shin flanks!
    for gz in (6, 9, 12):
        fill_sym_box(grid, 5, 5, 12, 13, gz, gz, 7)
        fill_sym_box(grid, 6, 6, 12, 12, gz, gz, 8)
    # Rear hull paneling & golden deck railing detail on calves
    fill_sym_box(grid, 3, 4, 9, 10, 5, 12, 2)
    fill_sym_box(grid, 2, 5, 9, 9, 7, 7, 5)
    fill_sym_box(grid, 2, 5, 9, 9, 11, 11, 5)
    # Ornate Ship-Prow Knee Guards (Z: 12..15)
    fill_sym_box(grid, 2, 4, 16, 16, 12, 14, 5)
    fill_sym_box(grid, 3, 3, 16, 17, 13, 15, 1)
    fill_sym_box(grid, 3, 3, 17, 17, 13, 14, 9)  # Small glowing knee lantern jewel

    # --- 3. THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 2, 4, 11, 15, 15, 20, 7)  # Deep naval blue mechanical thighs
    fill_sym_box(grid, 3, 3, 12, 14, 15, 15, 8)  # Iron knee joint
    fill_sym_box(grid, 2, 4, 15, 15, 16, 19, 3)  # Crisp white naval trouser panel
    fill_sym_box(grid, 4, 4, 12, 14, 16, 19, 5)  # Gold side stripe

    # --- 4. WAIST / CAPTAIN'S SASH & NAVAL COAT SKIRTS (Z: 20..24) ---
    fill_sym_box(grid, 0, 4, 10, 15, 20, 23, 7)  # Pelvis core
    fill_sym_box(grid, 0, 1, 12, 16, 19, 23, 1)  # Mahogany center codpiece
    fill_sym_box(grid, 0, 1, 16, 16, 20, 22, 5)  # Gold center crest
    # Crimson Swashbuckling Captain's Sash around waist (Z: 21..22)
    fill_sym_box(grid, 0, 4, 15, 16, 22, 23, 6)
    fill_sym_box(grid, 0, 4, 10, 10, 22, 23, 6)
    fill_sym_box(grid, 0, 1, 16, 17, 22, 23, 5)  # Burnished Gold Captain Buckle
    # Sweeping Captain's Coat Side-Tassets & Rear Coattails
    fill_sym_box(grid, 5, 5, 10, 15, 17, 22, 7)
    fill_sym_box(grid, 5, 5, 10, 15, 17, 17, 5)  # Gold hem
    fill_sym_box(grid, 5, 5, 14, 15, 18, 21, 5)
    fill_sym_box(grid, 0, 4, 9, 10, 17, 21, 7)   # Rear naval coattail
    fill_sym_box(grid, 0, 4, 9, 9, 17, 17, 5)    # Rear gold hem
    fill_sym_box(grid, 0, 0, 9, 9, 17, 20, 0)    # Split coattail vent

    # --- 5. TORSO / CHEST (Z: 24..34) - Folded White Sail Breastplate + Wood/Gold Armor ---
    # Core dark mahogany & navy torso
    fill_sym_box(grid, 0, 4, 10, 15, 24, 33, 1)
    fill_sym_box(grid, 0, 3, 10, 14, 24, 25, 7)  # Tapered naval waist
    fill_sym_box(grid, 4, 4, 11, 14, 25, 32, 7)  # Side navy coat panels
    fill_sym_box(grid, 0, 4, 10, 15, 33, 34, 5)  # Golden collar rim

    # Signature Folded Crisp White Sail Breastplate (+Y front chest, Z: 25..33)
    fill_sym_box(grid, 0, 4, 15, 16, 26, 32, 3)  # Broad crisp cream-white sail front
    fill_sym_box(grid, 1, 3, 16, 17, 27, 31, 3)  # Sculpted forward sail pleat
    # Diagonal linen fold shading & naval double-breasted lapel lines
    fill_sym_box(grid, 2, 2, 17, 17, 27, 31, 4)
    fill_sym_box(grid, 3, 4, 16, 16, 26, 32, 4)
    fill_sym_box(grid, 3, 3, 17, 17, 28, 28, 5)  # Gold naval coat buttons
    fill_sym_box(grid, 3, 3, 17, 17, 30, 30, 5)
    fill_sym_box(grid, 1, 3, 16, 16, 25, 26, 5)  # Lower gold breastplate V-trim
    # Crimson scarf / cravat collar accent at upper chest
    fill_sym_box(grid, 0, 1, 16, 17, 32, 33, 6)

    # Stern-Castle Glowing Lantern Core embedded in chest center!
    fill_sym_box(grid, 0, 1, 16, 17, 27, 31, 5)  # Ornate gold window frame
    fill_sym_box(grid, 0, 0, 17, 18, 28, 30, 9)  # Glowing amber lantern core!

    # --- 6. BACKPACK & SWEEPING TWIN BILLOWING WING-SAILS (Y: 2..10, Z: 19..42) ---
    # Rear Stern-Castle Backpack (visible in REAR VIEW!)
    fill_sym_box(grid, 0, 3, 7, 10, 24, 33, 1)
    fill_sym_box(grid, 0, 3, 7, 9, 25, 25, 5)    # Gold stern gallery rail
    fill_sym_box(grid, 0, 3, 7, 9, 32, 33, 5)    # Upper gold stern crest
    fill_sym_box(grid, 0, 2, 6, 7, 27, 30, 5)    # Rear stern window frame
    fill_sym_box(grid, 0, 1, 6, 6, 28, 29, 9)    # Glowing rear stern lantern windows!
    fill_sym_box(grid, 2, 2, 6, 7, 24, 26, 8)    # Iron thrusters / lower stern cannon ports

    # Twin Sweeping Wing-Sails draping dynamically off the back!
    # Built from x_off = 3..14 along curving diagonal wooden spars + billowing cream-white sails
    for k in range(12):
        xo = 3 + k
        # Upper yardarm spar rises from z=32 to z=41, curving smoothly backward in Y
        z_top = 32 + int(round(k * 0.85))
        y_spar = 8 - int(round(k * 0.45))
        # Lower spar sweeps outward & slightly downward, then lifts at wingtip for dramatic sail taper
        z_bot = 24 - int(round(np.sin(k / 11.0 * np.pi) * 4.5)) + int(round(k * 0.45))
        if z_top - z_bot < 4:
            z_bot = z_top - 4

        # Wooden upper yardarm & gold tip
        fill_sym_box(grid, xo, xo, y_spar, y_spar + 1, z_top, z_top, 5 if k == 11 else 2)
        if k > 0:
            # Ensure continuous diagonal spar connection
            prev_z = 32 + int(round((k - 1) * 0.85))
            prev_y = 8 - int(round((k - 1) * 0.45))
            fill_sym_box(grid, xo, xo, min(y_spar, prev_y), max(y_spar, prev_y), min(z_top, prev_z), max(z_top, prev_z), 2)

        # Lower wooden boom (partial span for authentic nautical rigging)
        if k <= 8:
            fill_sym_box(grid, xo, xo, y_spar, y_spar, z_bot, z_bot, 1)

        # Billowing canvas wing-sail between z_bot and z_top
        span_h = max(1, z_top - z_bot)
        for z in range(z_bot, z_top):
            tz = (z - z_bot) / float(span_h)
            # Wind-filled curve bulging gracefully toward -Y (back)
            billow = int(round(np.sin(tz * np.pi) * (1.8 if k < 9 else 1.0)))
            sy = max(1, y_spar - billow)

            # Sail coloring: crisp cream-white canvas with linen folds & crimson naval wing stripe
            if k == 11 or z == z_bot:
                scol = 4
            elif 4 <= k <= 8 and abs(z - (z_bot + span_h // 2)) <= 0:
                scol = 6  # Crimson naval stripe across wings!
            elif k % 3 == 1:
                scol = 4
            else:
                scol = 3

            fill_sym_box(grid, xo, xo, sy, sy, z, z, scol)
            # Connect smoothly in Y so sail surface has no diagonal gaps
            if sy < y_spar and (z == z_top - 1 or z == z_bot):
                fill_sym_box(grid, xo, xo, sy, y_spar, z, z, scol)
            if k > 0:
                # Guarantee horizontal connectivity to xo - 1
                prev_ys = 8 - int(round((k - 1) * 0.45))
                if abs(sy - prev_ys) > 1:
                    fill_sym_box(grid, xo, xo, min(sy, prev_ys - 1), max(sy, prev_ys - 1), z, z, scol)

        # Crimson trailing wingtip pennant streamer at top outer corner!
        if k == 11:
            fill_sym_box(grid, 15, 16, y_spar - 1, y_spar, z_top, z_top, 6)
            fill_sym_box(grid, 16, 17, y_spar - 2, y_spar - 1, z_top - 1, z_top, 6)

    # --- 7. SHOULDERS & ARMS (Z: 17..35) ---
    # Ornate Captain's Epaulette Pauldrons
    fill_sym_box(grid, 5, 8, 10, 15, 29, 34, 7)   # Deep navy shoulder base
    fill_sym_box(grid, 5, 8, 11, 14, 34, 35, 5)   # Burnished gold braided epaulettes!
    fill_sym_box(grid, 8, 9, 11, 14, 31, 34, 5)   # Hanging gold epaulette fringe
    fill_sym_box(grid, 6, 8, 15, 15, 30, 33, 1)   # Mahogany front armor trim
    fill_sym_box(grid, 6, 7, 15, 15, 31, 32, 6)   # Crimson shoulder accent

    # Upper Arms (Z: 24..28)
    fill_sym_box(grid, 6, 7, 11, 14, 24, 28, 8)   # Iron mechanical bicep
    fill_sym_box(grid, 6, 7, 11, 14, 26, 27, 7)   # Navy sleeve
    fill_sym_box(grid, 6, 7, 11, 14, 25, 25, 5)   # Gold sleeve band

    # LEFT ARM (-X, x = 8..11): Naval Gauntlet + Ship's Helm Buckler Shield
    fill_box(grid, 9, 11, 11, 15, 18, 23, 1)      # Mahogany forearm
    fill_box(grid, 9, 11, 11, 15, 22, 23, 3)      # Crisp white turned-back naval cuff
    fill_box(grid, 9, 11, 11, 15, 21, 21, 5)      # Gold cuff trim
    fill_box(grid, 9, 11, 12, 14, 16, 17, 8)      # Iron fist
    # Ship's Helm-Wheel Buckler mounted on outer left forearm (x = 7..8)
    fill_box(grid, 8, 8, 11, 16, 18, 23, 1)       # Mahogany buckler base
    fill_box(grid, 7, 8, 12, 15, 19, 22, 5)       # Golden helm-wheel ring
    fill_box(grid, 7, 7, 13, 14, 20, 21, 8)       # Iron central hub
    fill_box(grid, 7, 7, 13, 14, 17, 24, 2)       # Vertical wheel spokes
    fill_box(grid, 7, 7, 10, 17, 20, 21, 2)       # Horizontal wheel spokes
    fill_box(grid, 7, 7, 13, 14, 20, 21, 9)       # Glowing center boss

    # RIGHT ARM (+X, x = 24..27): Forward-posed forearm gripping the Grand Mast-Lance!
    fill_box(grid, 24, 26, 12, 17, 19, 23, 1)     # Mahogany forearm reaching forward
    fill_box(grid, 24, 26, 12, 16, 22, 23, 3)     # Crisp white naval cuff
    fill_box(grid, 24, 26, 12, 16, 21, 21, 5)     # Gold cuff trim
    fill_box(grid, 25, 27, 16, 19, 18, 20, 8)     # Iron right hand firmly gripping mast shaft!
    fill_box(grid, 26, 27, 18, 19, 19, 20, 5)     # Gold knuckle guard

    # --- 8. GRAND MAST-LANCE / SPEAR (Right Hand +X: x=27..33, y=17..23, z=3..43) ---
    # Tall turned wooden mast shaft passing solidly through right fist (x=27..28, y=18..19)
    fill_box(grid, 27, 28, 18, 19, 4, 34, 2)      # Warm teak mast shaft
    for bz in (8, 14, 24, 30):
        fill_box(grid, 27, 28, 18, 19, bz, bz, 1)  # Dark mahogany mast lashings
    # Weighted iron & gold pommel butt cap (grounded near feet, z=3..5)
    fill_box(grid, 27, 28, 18, 19, 3, 4, 8)
    fill_box(grid, 27, 28, 18, 19, 5, 5, 5)

    # Miniature Crow's Nest Guard (Z: 25..26)
    fill_box(grid, 26, 29, 17, 20, 25, 26, 1)
    fill_box(grid, 26, 29, 17, 20, 26, 26, 5)

    # Wide Yardarm Crossguard (Z: 32..33) with furled white sail accent
    fill_box(grid, 24, 32, 18, 19, 32, 33, 2)
    fill_box(grid, 24, 24, 18, 19, 32, 33, 5)     # Gold yardarm endcap
    fill_box(grid, 32, 32, 18, 19, 32, 33, 5)     # Gold yardarm endcap
    fill_box(grid, 25, 31, 19, 19, 31, 32, 3)     # Furled crisp white sail wrap
    fill_box(grid, 26, 30, 19, 19, 31, 31, 4)

    # Grand Bowsprit Spearhead Blade (Z: 34..43)
    fill_box(grid, 27, 28, 18, 19, 34, 35, 5)     # Gold blade collar
    fill_box(grid, 26, 29, 18, 19, 35, 37, 8)     # Broad iron lance base
    fill_box(grid, 27, 28, 18, 19, 38, 41, 8)     # Tapered lance blade
    fill_box(grid, 27, 28, 19, 19, 36, 40, 5)     # Gold central ridge
    fill_box(grid, 27, 28, 18, 18, 42, 43, 9)     # Gleaming bright lance tip!

    # Fluttering Crimson Masthead Pennant streaming from below the yardarm (+X / +Y)
    pennant_lance = [
        (29, 18, 29, 31), (30, 18, 28, 31), (31, 17, 27, 30),
        (32, 17, 26, 29), (33, 16, 26, 28), (34, 16, 25, 27), (35, 16, 25, 26),
    ]
    for px, py, pz0, pz1 in pennant_lance:
        fill_box(grid, px, px, py, py, pz0, pz1, 6)
    fill_box(grid, 29, 30, 18, 18, 30, 31, 5)     # Gold pennant emblem

    # --- 9. HEAD: BICORNE CAPTAIN-CREST HELMET (Z: 34..43) ---
    # Mechanical neck
    fill_sym_box(grid, 0, 1, 12, 13, 34, 35, 8)
    # Armored Captain Head (Z: 35..39)
    fill_sym_box(grid, 0, 2, 11, 15, 35, 39, 7)   # Deep navy helmet shell
    fill_sym_box(grid, 2, 2, 12, 14, 36, 38, 1)   # Mahogany cheek guards
    fill_sym_box(grid, 0, 1, 15, 15, 35, 36, 4)   # Crisp linen/silver faceplate & chin
    fill_sym_box(grid, 0, 0, 15, 16, 35, 35, 5)   # Gold chin jewel
    # Glowing Amber Lantern Visor (Z: 37)
    fill_sym_box(grid, 0, 1, 15, 16, 37, 37, 9)
    fill_sym_box(grid, 0, 2, 15, 16, 38, 38, 5)   # Gold brow ridge over visor

    # Iconic Swashbuckling Bicorne Captain's Hat Crest (Z: 39..43)
    fill_sym_box(grid, 0, 3, 11, 15, 39, 40, 7)   # Hat crown base
    fill_sym_box(grid, 0, 4, 12, 15, 40, 41, 7)   # Wide swept bicorne wings
    fill_sym_box(grid, 4, 5, 12, 14, 41, 42, 7)   # Swept-up bicorne tips
    fill_sym_box(grid, 0, 4, 15, 16, 40, 41, 5)   # Burnished gold front brim trim!
    fill_sym_box(grid, 4, 5, 13, 15, 42, 42, 5)   # Gold-tipped bicorne horns
    fill_sym_box(grid, 0, 3, 11, 11, 40, 41, 5)   # Rear gold brim trim
    # Central Crimson Captain's Cockade & Plume Crest
    fill_sym_box(grid, 0, 0, 15, 16, 40, 42, 6)
    fill_sym_box(grid, 0, 1, 13, 15, 42, 43, 6)
    fill_sym_box(grid, 0, 0, 16, 16, 41, 41, 5)   # Gold skull/anchor cockade center

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
    v_a = export_vox(model_a, "sailship_a.vox")
    v_b = export_vox(model_b, "sailship_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: TALL SAILING SHIP -> GALLEON CAPTAIN ROBOT",
        "1. TALL SAILING SHIP",
        "2. GALLEON CAPTAIN ROBOT",
        "preview_sailship.png",
        yaw_a=42, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"sailship: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
