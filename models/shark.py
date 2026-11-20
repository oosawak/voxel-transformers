import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (88, 122, 156, 255),   # Steel-Blue / Slate-Grey Shark Upper Body
    2: (46, 70, 102, 255),    # Deep Oceanic Navy Dorsal Ridge & Fin Shading
    3: (224, 232, 240, 255),  # Crisp Ice-White Underbelly & Fin Undersides
    4: (252, 252, 254, 255),  # Pure White Razor Teeth & Fin Blade Edges
    5: (198, 42, 58, 255),    # Menacing Crimson Open Mouth & Gums
    6: (22, 26, 34, 255),     # Jet Black Fierce Shark Eyes & Gill Slits
    7: (52, 60, 74, 255),     # Dark Gunmetal Mechanical Frame & Joints
    8: (138, 154, 174, 255),  # Brushed Marine Steel Armor & Vents
    9: (44, 224, 244, 255),   # Glowing Aqua-Cyan Visor & Hydro Core
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


def hollow_interior(grid, y0, y1):
    """Hollow strictly interior voxels (all 6 neighbors solid) within Y range."""
    X, Y, Z = grid.shape
    to_clear = []
    for x in range(1, X - 1):
        for y in range(max(1, y0), min(Y - 1, y1 + 1)):
            for z in range(1, Z - 1):
                if (grid[x, y, z] > 0 and
                        grid[x - 1, y, z] > 0 and grid[x + 1, y, z] > 0 and
                        grid[x, y - 1, z] > 0 and grid[x, y + 1, z] > 0 and
                        grid[x, y, z - 1] > 0 and grid[x, y, z + 1] > 0):
                    to_clear.append((x, y, z))
    for x, y, z in to_clear:
        grid[x, y, z] = 0


# ==========================================
# FORM A: GREAT WHITE SHARK (28 x 46 x 22)
# ==========================================
def build_a():
    grid = np.zeros((28, 46, 22), dtype=np.uint8)
    cx_l, cx_r = 13, 14

    # --- SLEEK TORPEDO FUSELAGE (Y: 9..36, Z: 3..11) ---
    # Smooth elliptical cross-section peaking around Y=27..30, tapering to tail stalk
    for y in range(9, 37):
        if y >= 28:
            t = (y - 28) / 8.0
            rx = 4.4 - 1.1 * (t ** 1.3)
            rz = 4.2 - 0.8 * (t ** 1.3)
            zc = 7.0 + 0.3 * t
        else:
            t = (28 - y) / 19.0
            rx = 4.4 - 3.3 * (t ** 1.15)
            rz = 4.2 - 3.0 * (t ** 1.2)
            zc = 7.0
        for x_off in range(0, 6):
            for z in range(2, 13):
                nx = (x_off + 0.5) / max(0.6, rx)
                nz = (z - zc) / max(0.6, rz)
                if nx * nx + nz * nz <= 1.0:
                    # Crisp countershading: white belly below z=6, steel-blue above, navy spine
                    if z <= 5:
                        col = 3
                    elif z >= int(round(zc + rz - 0.4)) and x_off <= 1:
                        col = 2
                    else:
                        col = 1
                    fill_sym_box(grid, x_off, x_off, y, y, z, z, col)

    # Caudal peduncle lateral keels (authentic Great White Shark detail)
    fill_sym_box(grid, 2, 2, 10, 14, 7, 7, 2)

    # --- DARK GILL SLITS BEHIND HEAD (Y: 29, 31, 33) ---
    for gy in (29, 31, 33):
        # Find outermost body voxel on flank at z=6..8
        for z in (6, 7, 8):
            for x_off in range(5, -1, -1):
                if grid[cx_r + x_off, gy, z] > 0:
                    fill_sym_box(grid, x_off, x_off, gy, gy, z, z, 6)
                    break

    # --- POINTED SNOUT, FIERCE EYES & OPEN CRIMSON MOUTH (Y: 35..45) ---
    # Upper cranium & pointed hydrodynamic snout
    fill_sym_box(grid, 0, 3, 35, 38, 7, 10, 1)
    fill_sym_box(grid, 0, 2, 35, 38, 10, 10, 2)   # Navy brow crest
    fill_sym_box(grid, 0, 2, 39, 41, 8, 9, 1)
    fill_sym_box(grid, 0, 1, 39, 41, 10, 10, 2)
    fill_sym_box(grid, 0, 1, 42, 43, 8, 9, 1)
    fill_sym_box(grid, 0, 0, 44, 45, 8, 8, 1)     # Sharp pointed snout tip
    fill_sym_box(grid, 0, 1, 42, 43, 7, 7, 3)     # White underside of snout tip
    # Fierce jet-black eyes with dark brow
    fill_sym_box(grid, 3, 3, 37, 38, 8, 9, 6)
    fill_sym_box(grid, 2, 3, 37, 38, 10, 10, 2)
    # Recessed menacing crimson mouth interior & dark throat
    fill_sym_box(grid, 0, 2, 35, 39, 5, 7, 5)
    fill_sym_box(grid, 0, 1, 35, 36, 6, 7, 6)
    # Upper razor-sharp white triangular teeth
    fill_sym_box(grid, 2, 2, 38, 38, 7, 7, 4)
    fill_sym_box(grid, 2, 2, 40, 40, 7, 7, 4)
    fill_sym_box(grid, 1, 1, 42, 42, 7, 7, 4)
    # Crisp white lower jaw angling slightly open + crimson lower gums
    fill_sym_box(grid, 0, 2, 34, 38, 3, 4, 3)
    fill_sym_box(grid, 0, 2, 39, 40, 4, 4, 3)
    fill_sym_box(grid, 0, 1, 41, 41, 4, 4, 3)
    fill_sym_box(grid, 0, 1, 36, 40, 5, 5, 5)     # Crimson lower gums
    # Lower sharp white teeth
    fill_sym_box(grid, 2, 2, 39, 39, 5, 5, 4)
    fill_sym_box(grid, 1, 1, 41, 41, 5, 5, 4)

    # --- TALL ICONIC SWEPT DORSAL FIN (Y: 19..29, Z: 11..21) ---
    dorsal_profile = [
        # (z, y_back, y_front)
        (11, 19, 29),
        (12, 20, 28),
        (13, 21, 27),
        (14, 21, 26),
        (15, 21, 25),
        (16, 21, 25),
        (17, 20, 24),
        (18, 20, 23),
        (19, 19, 22),
        (20, 19, 21),
        (21, 19, 20),
    ]
    for z, yb, yf in dorsal_profile:
        fill_sym_box(grid, 0, 0, yb, yf, z, z, 1)
        fill_sym_box(grid, 0, 0, yf, yf, z, z, 2)  # Navy leading edge
        if z >= 19:
            fill_sym_box(grid, 0, 0, yb, yf, z, z, 2)  # Dark fin tip
    # Sturdy base flare into back
    fill_sym_box(grid, 1, 1, 21, 27, 11, 11, 1)
    # Small second dorsal fin near tail
    fill_sym_box(grid, 0, 0, 12, 14, 9, 10, 1)
    fill_sym_box(grid, 0, 0, 11, 13, 11, 11, 2)

    # --- WIDE SWEPT PECTORAL FINS (X_off: 4..12, Y: 20..31, Z: 2..5) ---
    pec_profile = [
        # (x_off, y_back, y_front, z_low, z_high)
        (4, 24, 31, 4, 5),
        (5, 23, 30, 4, 5),
        (6, 23, 29, 3, 4),
        (7, 22, 28, 3, 4),
        (8, 22, 27, 3, 4),
        (9, 21, 26, 2, 3),
        (10, 21, 25, 2, 3),
        (11, 20, 23, 2, 2),
        (12, 20, 22, 2, 2),
    ]
    for xo, yb, yf, zl, zh in pec_profile:
        fill_sym_box(grid, xo, xo, yb, yf, zl, zh, 1)
        if zl < zh:
            fill_sym_box(grid, xo, xo, yb, yf - 1, zl, zl, 3)  # White underside
        fill_sym_box(grid, xo, xo, yf, yf, zl, zh, 2)          # Navy leading edge
        if xo >= 11:
            fill_sym_box(grid, xo, xo, yb, yf, zl, zh, 2)      # Dark fin tips

    # --- PELVIC FINS & ANAL FIN ---
    fill_sym_box(grid, 2, 4, 16, 19, 3, 4, 1)
    fill_sym_box(grid, 4, 5, 15, 17, 3, 3, 2)
    fill_sym_box(grid, 2, 3, 16, 18, 3, 3, 3)
    fill_sym_box(grid, 0, 0, 12, 14, 4, 5, 3)

    # --- TALL CRESCENT-SHAPED CAUDAL TAIL FIN (Y: 0..9, Z: 0..19) ---
    # Tail root bridge
    fill_sym_box(grid, 0, 1, 7, 9, 6, 8, 1)
    fill_sym_box(grid, 0, 0, 6, 8, 6, 8, 1)
    # Upper caudal lobe sweeping up and back to Z=19
    upper_tail = [
        # (z, y_back, y_front)
        (8, 5, 9),
        (9, 5, 8),
        (10, 5, 8),
        (11, 4, 7),
        (12, 4, 7),
        (13, 3, 6),
        (14, 3, 5),
        (15, 2, 5),
        (16, 2, 4),
        (17, 1, 3),
        (18, 1, 3),
        (19, 0, 2),
    ]
    for z, yb, yf in upper_tail:
        fill_sym_box(grid, 0, 0, yb, yf, z, z, 1)
        fill_sym_box(grid, 0, 0, yf, yf, z, z, 2)
        if z >= 17:
            fill_sym_box(grid, 0, 0, yb, yf, z, z, 2)
    # Lower caudal lobe sweeping down and back to Z=0
    lower_tail = [
        # (z, y_back, y_front)
        (6, 5, 9),
        (5, 5, 8),
        (4, 4, 7),
        (3, 4, 7),
        (2, 3, 6),
        (1, 2, 5),
        (0, 1, 3),
    ]
    for z, yb, yf in lower_tail:
        fill_sym_box(grid, 0, 0, yb, yf, z, z, 3 if z <= 3 else 1)
        fill_sym_box(grid, 0, 0, yf, yf, z, z, 1 if z > 1 else 2)

    # Hollow unseen torso core to keep voxel count sleek and efficient
    hollow_interior(grid, 14, 35)

    return grid


# ==========================================
# FORM B: SHARK HUNTER ROBOT (34 x 28 x 41)
# ==========================================
def build_b():
    grid = np.zeros((34, 28, 41), dtype=np.uint8)

    # --- GROUNDED HYDRO-BOOTS / FEET (Z: 0..2) ---
    fill_sym_box(grid, 2, 5, 9, 17, 0, 1, 7)      # Gunmetal boot sole
    fill_sym_box(grid, 2, 5, 11, 18, 1, 2, 1)     # Steel-blue armored toe
    fill_sym_box(grid, 3, 4, 16, 19, 0, 1, 3)     # Crisp white sleek hydro-toe tips
    fill_sym_box(grid, 3, 4, 8, 10, 0, 2, 2)      # Navy stabilizer heel spur

    # --- SLEEK FINNED LOWER LEGS (Z: 3..14) - SPLIT CRESCENT TAIL FIN ANKLES/SHINS ---
    fill_sym_box(grid, 2, 5, 10, 15, 3, 13, 1)    # Steel-blue leg armor
    fill_sym_box(grid, 2, 4, 15, 16, 4, 12, 3)    # Crisp white shin plates
    fill_sym_box(grid, 3, 4, 16, 17, 11, 14, 2)   # Deep navy pointed knee guards
    fill_sym_box(grid, 3, 4, 17, 17, 12, 13, 9)   # Aqua-cyan knee hydro-slit
    # Split crescent caudal tail fin blades sweeping outward & backward on each calf/ankle!
    for step in range(9):
        z = 3 + step
        # Crescent curve: widest at bottom & top, slightly recessed mid-calf
        out_ext = 2 if step in (0, 1, 7, 8) else (1 if step in (2, 6) else 0)
        fill_sym_box(grid, 6, 6 + out_ext, 9 - out_ext, 13 - out_ext // 2, z, z, 1)
        fill_sym_box(grid, 6 + out_ext, 6 + out_ext, 9 - out_ext, 11 - out_ext // 2, z, z, 2)
        if step <= 3:
            fill_sym_box(grid, 6, 6 + out_ext, 12 - out_ext // 2, 13 - out_ext // 2, z, z, 3)
    # Rear calf tail-fin stabilizer keel
    fill_sym_box(grid, 3, 4, 7, 9, 4, 11, 2)
    fill_sym_box(grid, 3, 4, 6, 7, 6, 10, 1)

    # --- THIGHS (Z: 14..19) ---
    fill_sym_box(grid, 2, 4, 10, 14, 14, 19, 3)   # Ice-white underbelly thigh armor
    fill_sym_box(grid, 2, 3, 11, 13, 14, 15, 7)   # Gunmetal knee joint
    fill_sym_box(grid, 4, 4, 11, 14, 15, 18, 1)   # Steel-blue outer thigh plating
    fill_sym_box(grid, 4, 4, 12, 13, 16, 17, 8)   # Steel panel detail

    # --- WAIST / PELVIS (Z: 19..22) ---
    fill_sym_box(grid, 0, 4, 10, 14, 19, 21, 7)   # Gunmetal waist frame
    fill_sym_box(grid, 0, 4, 14, 15, 20, 21, 1)   # Steel-blue hip armor
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 2)   # Navy front pelvic crest
    fill_sym_box(grid, 0, 0, 16, 16, 20, 21, 9)   # Aqua-cyan belt core
    fill_sym_box(grid, 4, 5, 10, 13, 19, 21, 2)   # Side hip pelvic-fin skirts
    fill_sym_box(grid, 5, 5, 10, 12, 19, 20, 3)   # White skirt trim

    # --- TORSO / CHEST (Z: 22..31) - WHITE BELLY PLATES & GILL-SLIT VENTS ---
    fill_sym_box(grid, 0, 5, 9, 15, 22, 31, 1)    # Main steel-blue torso
    fill_sym_box(grid, 0, 3, 15, 16, 22, 26, 3)   # Crisp white shark-belly ab plates
    fill_sym_box(grid, 0, 4, 15, 17, 26, 30, 3)   # White upper chest belly armor
    fill_sym_box(grid, 3, 5, 15, 17, 27, 31, 1)   # Steel-blue outer chest flanks
    fill_sym_box(grid, 0, 2, 16, 17, 30, 31, 2)   # Deep navy collar armor
    # Dark gill-slit vents detailing both sides of the chest!
    for gz in (27, 29):
        fill_sym_box(grid, 3, 4, 17, 17, gz, gz, 6)  # Jet-black gill slits
    fill_sym_box(grid, 2, 2, 17, 17, 27, 29, 8)      # Steel gill-vent frame
    # Glowing aqua-cyan hydro-core reactor in center of chest
    fill_sym_box(grid, 0, 1, 17, 18, 27, 29, 8)
    fill_sym_box(grid, 0, 0, 18, 18, 27, 29, 9)
    fill_sym_box(grid, 0, 1, 17, 17, 24, 24, 8)      # Ab rib vent

    # --- BACKPACK & TALL ICONIC SWEPT DORSAL FIN ON BACK (Y: 2..9, Z: 22..40) ---
    fill_sym_box(grid, 0, 3, 7, 9, 23, 30, 7)     # Gunmetal hydro-pack
    fill_sym_box(grid, 0, 2, 6, 7, 24, 29, 8)     # Steel pack casing
    fill_sym_box(grid, 2, 3, 6, 7, 22, 24, 2)     # Twin rear hydro-thrusters
    fill_sym_box(grid, 2, 3, 6, 6, 22, 22, 9)     # Aqua thruster glow
    # Tall swept shark dorsal fin rising boldly behind shoulders & head!
    back_dorsal = [
        # (z, y_back, y_front)
        (25, 4, 8),
        (26, 4, 8),
        (27, 3, 8),
        (28, 3, 8),
        (29, 3, 8),
        (30, 3, 8),
        (31, 3, 8),
        (32, 3, 8),
        (33, 3, 7),
        (34, 3, 7),
        (35, 2, 6),
        (36, 2, 6),
        (37, 2, 5),
        (38, 1, 4),
        (39, 1, 3),
        (40, 1, 2),
    ]
    for z, yb, yf in back_dorsal:
        fill_sym_box(grid, 0, 0, yb, yf, z, z, 1)
        fill_sym_box(grid, 0, 0, yf, yf, z, z, 2)
        if z >= 38:
            fill_sym_box(grid, 0, 0, yb, yf, z, z, 2)
    fill_sym_box(grid, 1, 1, 5, 8, 26, 31, 1)     # Sturdy dorsal fin spine root

    # --- SWEPT PECTORAL-FIN SHOULDERS (Z: 27..35) ---
    fill_sym_box(grid, 6, 9, 10, 15, 27, 32, 1)   # Main armored shoulder blocks
    fill_sym_box(grid, 7, 9, 11, 14, 32, 32, 2)   # Navy top cap
    fill_sym_box(grid, 6, 8, 15, 15, 28, 31, 3)   # White front shoulder plate
    # Swept pectoral shoulder fins flaring outward and upward!
    for i in range(4):
        fill_sym_box(grid, 9 + i, 10 + i, 10 - i // 2, 14 - i, 30 + i, 32 + i, 1)
        fill_sym_box(grid, 10 + i, 10 + i, 10 - i // 2, 13 - i, 32 + i, 32 + i, 2)
        if i <= 1:
            fill_sym_box(grid, 9 + i, 10 + i, 13 - i, 14 - i, 30 + i, 30 + i, 3)

    # --- RIGHT ARM (+X): ENTIRE GREAT WHITE SHARK HEAD CHOMP WEAPON! ---
    # Right upper arm (X: 23..26, Y: 11..14, Z: 21..26)
    fill_box(grid, 24, 26, 11, 14, 21, 26, 7)     # Gunmetal joint
    fill_box(grid, 24, 26, 12, 14, 22, 25, 8)     # Steel piston sleeve
    # Massive Shark Head mounted forward (+Y) on right forearm! (X: 22..29, Y: 11..27, Z: 14..22)
    # Cranium & gill collar
    fill_box(grid, 22, 29, 11, 18, 17, 21, 1)     # Steel-blue shark cranium
    fill_box(grid, 23, 28, 12, 18, 22, 22, 2)     # Deep navy dorsal brow ridge
    fill_box(grid, 22, 29, 11, 15, 16, 16, 3)     # White throat underside
    # Gill slits on shark head collar
    for gy in (13, 15):
        fill_box(grid, 22, 22, gy, gy, 18, 20, 6)
        fill_box(grid, 29, 29, gy, gy, 18, 20, 6)
    # Fierce jet-black shark eyes on BOTH sides of head!
    fill_box(grid, 22, 22, 17, 18, 19, 20, 6)
    fill_box(grid, 29, 29, 17, 18, 19, 20, 6)
    # Tapered pointed upper snout (Y: 19..27, Z: 18..21)
    fill_box(grid, 23, 28, 19, 21, 18, 21, 1)
    fill_box(grid, 24, 27, 19, 21, 21, 21, 2)
    fill_box(grid, 24, 27, 22, 24, 18, 20, 1)
    fill_box(grid, 25, 26, 22, 24, 20, 20, 2)
    fill_box(grid, 25, 26, 25, 27, 19, 19, 1)     # Pointed shark snout tip!
    # Menacing open crimson mouth interior & dark throat
    fill_box(grid, 24, 27, 15, 21, 16, 18, 5)
    fill_box(grid, 25, 26, 15, 17, 17, 18, 6)
    # Sharp white upper teeth hanging from snout!
    for ty, xl, xr in ((19, 23, 28), (21, 23, 28), (23, 24, 27), (25, 25, 26)):
        fill_box(grid, xl, xl, ty, ty, 17, 17, 4)
        fill_box(grid, xr, xr, ty, ty, 17, 17, 4)
    # Crisp white lower jaw + crimson lower gums + lower white teeth!
    fill_box(grid, 23, 28, 14, 20, 14, 15, 3)     # White lower jaw base
    fill_box(grid, 24, 27, 21, 23, 14, 15, 3)
    fill_box(grid, 25, 26, 24, 25, 15, 15, 3)     # Lower chin tip
    fill_box(grid, 24, 27, 16, 22, 15, 15, 5)     # Crimson lower gums
    for ty, xl, xr in ((20, 23, 28), (22, 24, 27), (24, 25, 26)):
        fill_box(grid, xl, xl, ty, ty, 16, 16, 4)
        fill_box(grid, xr, xr, ty, ty, 16, 16, 4)

    # --- LEFT ARM (-X): ARMORED FOREARM + SWEPT PECTORAL FIN BLADE! ---
    fill_box(grid, 7, 9, 11, 14, 22, 26, 7)       # Left upper arm
    fill_box(grid, 7, 9, 12, 14, 23, 25, 8)
    fill_box(grid, 6, 10, 10, 15, 16, 21, 1)      # Steel-blue forearm gauntlet
    fill_box(grid, 8, 10, 14, 15, 17, 20, 3)      # White inner wrist armor
    fill_box(grid, 7, 9, 11, 14, 13, 15, 7)       # Left fist
    # Swept pectoral fin blade mounted on outer left forearm extending forward!
    fill_box(grid, 5, 6, 11, 17, 16, 21, 2)       # Navy fin spine mount
    fill_box(grid, 4, 5, 13, 20, 14, 19, 1)       # Steel-blue swept fin blade
    fill_box(grid, 3, 4, 16, 22, 13, 17, 1)
    fill_box(grid, 3, 3, 17, 23, 13, 16, 4)       # Pure white razor blade edge!
    fill_box(grid, 4, 4, 15, 19, 16, 17, 9)       # Aqua-cyan energy conduit

    # --- HEAD (Z: 32..38) - SHARK HUNTER HELMET WITH AQUA VISOR & FIN CREST ---
    fill_sym_box(grid, 0, 1, 11, 13, 31, 32, 7)   # Neck joint
    fill_sym_box(grid, 0, 2, 10, 14, 32, 36, 1)   # Steel-blue helmet
    fill_sym_box(grid, 0, 2, 10, 14, 36, 37, 2)   # Deep navy helmet crown
    fill_sym_box(grid, 0, 0, 10, 15, 37, 38, 2)   # Swept mini dorsal head crest!
    fill_sym_box(grid, 0, 0, 13, 15, 38, 38, 4)   # White crest highlight
    fill_sym_box(grid, 0, 1, 14, 15, 34, 35, 9)   # Glowing aqua-cyan shark visor!
    fill_sym_box(grid, 0, 1, 14, 15, 32, 33, 8)   # Metallic steel mouthplate
    fill_sym_box(grid, 2, 3, 12, 14, 33, 35, 3)   # Crisp white shark-fin ear guards

    # Hollow strictly interior torso core so voxel count stays crisp
    hollow_interior(grid, 10, 14)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=46, pitch_a=22, yaw_b=34, pitch_b=20):
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
    v_a = export_vox(model_a, "shark_a.vox")
    v_b = export_vox(model_b, "shark_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: GREAT WHITE SHARK -> SHARK HUNTER ROBOT",
        "1. GREAT WHITE SHARK",
        "2. SHARK HUNTER ROBOT",
        "preview_shark.png",
        yaw_a=46, pitch_a=22, yaw_b=34, pitch_b=20,
    )
    print(f"shark: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
