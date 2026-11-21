import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (218, 36, 44, 255),    # Electric-Rock Cherry Red (Guitar Body, Chest, Shield, Armor)
    2: (132, 22, 36, 255),    # Deep Mahogany / Burgundy Bevel Shading
    3: (248, 246, 238, 255),  # Crisp Pearl-White Pickguard & Trim
    4: (102, 58, 36, 255),    # Warm Rosewood / Maple Fretboard & Neck
    5: (192, 214, 238, 255),  # Gleaming Metallic Silver / Chrome Strings, Pickups & Pegs
    6: (44, 48, 58, 255),     # Dark Charcoal Bridge, Knobs, Stand & Mechanical Joints
    7: (62, 224, 255, 255),   # Glowing Electric-Cyan Amp Energy & Robot Visor
    8: (244, 194, 52, 255),   # Golden Brass Frets, Tone Knobs & Crest
    9: (246, 132, 38, 255),   # Warm Amber Sunburst Center Glow
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


def guitar_body_mask(x, z, cx=10.5):
    """Double-cutaway electric rock guitar body silhouette in (x, z)."""
    dx = x - cx
    # Lower bout (generous rounded body, z: 3..13)
    in_lower = ((dx / 8.4) ** 2 + ((z - 8.2) / 5.4) ** 2) <= 1.0
    # Mid waist (sculpted inward around z=13.5)
    in_waist = (11.0 <= z <= 16.5) and (abs(dx) <= 5.4 + 0.35 * ((z - 13.5) ** 2))
    # Upper bout base
    in_upper = ((dx / 7.2) ** 2 + ((z - 16.5) / 3.8) ** 2) <= 1.0
    # Longer sleek bass-side cutaway horn (+X, viewer's left)
    in_bass_horn = (((x - (cx + 5.1)) / 2.3) ** 2 + ((z - 20.0) / 3.4) ** 2) <= 1.0
    # Shorter sharp treble-side cutaway horn (-X, viewer's right)
    in_treble_horn = (((x - (cx - 5.1)) / 2.2) ** 2 + ((z - 18.8) / 2.6) ** 2) <= 1.0

    in_body = in_lower or in_waist or in_upper or in_bass_horn or in_treble_horn
    # Carve clean double cutaway scoops beside the neck heel (z >= 17.5)
    if z >= 17.5 and 1.8 < abs(dx) < 3.6:
        if dx > 0 and z < 23.0:
            in_body = False
        if dx < 0 and z < 21.5:
            in_body = False
    # Carve waist indents cleanly so hourglass silhouette pops
    if 12.2 <= z <= 14.8 and abs(dx) > 5.8:
        in_body = False
    return in_body


# ==========================================
# FORM A: ELECTRIC GUITAR ON STAND (22 x 16 x 46)
# ==========================================
def build_a():
    grid = np.zeros((22, 16, 46), dtype=np.uint8)
    cx = 10.5

    # --- COMPACT DARK A-FRAME GUITAR STAND (Z: 0..15) ---
    # Splayed front & rear tubular legs (ground contact at Z=0)
    for leg_x in (6, 15):
        # Front rubber foot + angled front leg rising to lower cradle
        fill_box(grid, leg_x, leg_x, 10, 12, 0, 1, 6)
        fill_box(grid, leg_x, leg_x, 9, 10, 2, 3, 6)
        # Rear splayed foot + angled rear tripod leg
        fill_box(grid, leg_x, leg_x, 1, 3, 0, 1, 6)
        for step in range(1, 9):
            ly = 3 + step // 2
            lz = 1 + step
            fill_box(grid, leg_x, leg_x, ly, ly, lz, lz + 1, 6)
        # Front cradle arm supporting the guitar lower bout (Z=2..3)
        fill_box(grid, leg_x, leg_x, 7, 12, 2, 2, 6)
        fill_box(grid, leg_x, leg_x, 12, 12, 2, 3, 8)  # Gold cushioned front tip
    # Horizontal crossbars connecting left & right stand legs
    fill_box(grid, 6, 15, 2, 3, 1, 1, 6)
    fill_box(grid, 6, 15, 6, 7, 8, 9, 6)
    # Central rear upright support bar cradling the guitar back (Y=6..7)
    fill_box(grid, 10, 11, 5, 6, 8, 15, 6)
    fill_box(grid, 9, 12, 6, 7, 13, 14, 6)

    # --- CONTOURED DOUBLE-CUTAWAY GUITAR BODY (Z: 3..23, Y: 7..10) ---
    body_cells = set()
    for x in range(1, 21):
        for z in range(3, 24):
            if guitar_body_mask(x, z, cx=cx):
                body_cells.add((x, z))

    for x, z in body_cells:
        # Determine if on outer silhouette rim for rich mahogany bevel shading
        is_rim = any((x + dx, z + dz) not in body_cells for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        is_inner_sunburst = ((x - cx) ** 2 / 14.0 + (z - 10.5) ** 2 / 20.0) <= 1.0
        for y in range(7, 11):
            is_bevel_edge = is_rim and (y in (7, 10))
            if is_rim:
                col = 2
            elif y == 10 and is_inner_sunburst:
                col = 9  # Warm amber sunburst glow at center
            else:
                col = 1  # Vibrant cherry red
            if is_bevel_edge:
                col = 2
            grid[x, y, z] = col

    # Hollow unseen inner body core (Y: 8..9) to keep voxel budget crisp
    for x, z in body_cells:
        if all((x + dx, z + dz) in body_cells for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
            grid[x, 8:10, z] = 0

    # Rear tremolo spring cavity plate on guitar back (Y=7)
    fill_box(grid, 9, 12, 7, 7, 7, 12, 6)
    fill_box(grid, 10, 11, 7, 7, 8, 11, 5)
    # Neck mounting chrome plate on back (Y=7, Z: 17..19)
    fill_box(grid, 9, 12, 7, 7, 17, 19, 5)

    # --- CRISP PEARL-WHITE PICKGUARD (Front face Y=10..11) ---
    for x, z in body_cells:
        # Classic sweeping pickguard covering treble (-X) side and looping around pickups
        in_pg_treble = (4 <= x <= 11) and (6 <= z <= 18) and (z <= 19 - max(0, 6 - x))
        in_pg_center = (8 <= x <= 13) and (9 <= z <= 18)
        in_pg_upper = (12 <= x <= 15) and (15 <= z <= 19)
        if (in_pg_treble or in_pg_center or in_pg_upper):
            # Stay 1 voxel inside the outer rim so red/mahogany outline frames it cleanly
            if all((x + dx, z + dz) in body_cells for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                grid[x, 10, z] = 3

    # --- BRIDGE, WHAMMY BAR, PICKUPS & GOLDEN KNOBS (Front Y=11) ---
    # Heavy charcoal & chrome tremolo bridge (Z: 6..8, X: 8..13)
    fill_box(grid, 8, 13, 11, 11, 6, 8, 6)
    fill_box(grid, 9, 12, 11, 11, 7, 7, 5)  # Gleaming chrome string saddles
    # Angled chrome whammy / tremolo bar curving out from treble side of bridge (6-connected!)
    fill_box(grid, 7, 8, 11, 12, 6, 6, 5)
    fill_box(grid, 6, 7, 12, 13, 6, 6, 5)
    fill_box(grid, 5, 6, 13, 13, 5, 6, 5)
    grid[5, 13, 5] = 3  # Pearl-white whammy tip
    # Three rock pickups (Bridge Humbucker, Middle Single, Neck Single)
    fill_box(grid, 8, 13, 11, 11, 10, 11, 6)  # Bridge humbucker frame
    fill_box(grid, 8, 13, 11, 11, 14, 14, 6)  # Middle pickup
    fill_box(grid, 8, 13, 11, 11, 17, 17, 6)  # Neck pickup
    # Chrome pickup pole dots
    for pz in (10, 11, 14, 17):
        grid[9, 11, pz] = 5
        grid[12, 11, pz] = 5
    # Golden brass volume & tone knobs on lower treble pickguard + cyan amp LED
    grid[6, 11, 7] = 8
    grid[5, 11, 10] = 8
    grid[6, 11, 13] = 8
    grid[4, 10, 6] = 7  # Electric-cyan output jack LED glow
    # Strap button at bottom center & upper bass horn tip
    fill_box(grid, 10, 11, 8, 9, 2, 2, 5)
    grid[16, 9, 23] = 5

    # --- LONG FRETTED ROSEWOOD NECK (Z: 18..38, X: 9..12) ---
    # Warm wood neck back (Y: 8..9) and dark rosewood fretboard (Y: 10)
    fill_box(grid, 9, 12, 8, 9, 18, 38, 4)
    fill_box(grid, 9, 12, 10, 10, 18, 38, 4)
    # Crisp golden brass frets every 3 layers across the fretboard!
    for fz in (20, 23, 26, 29, 32, 35):
        fill_box(grid, 9, 12, 10, 10, fz, fz, 8)
    # Pearl-white fret dot inlays cleanly visible between the two silver string rails
    for iz in (21, 24, 27, 30, 33):
        grid[10, 10, iz] = 3
    # Crisp pearl-white nut at top of fretboard (Z=38)
    fill_box(grid, 9, 12, 10, 11, 38, 38, 3)

    # --- GLEAMING METALLIC SILVER STRINGS (弦の色! Z: 7..39, Y=11) ---
    # Two bold continuous bright silver string rails running uninterrupted from bridge to headstock,
    # leaving the dark rosewood fretboard & golden frets crisply visible between them!
    fill_box(grid, 9, 9, 11, 11, 7, 39, 5)
    fill_box(grid, 12, 12, 11, 11, 7, 39, 5)

    # --- ANGLED ROCK HEADSTOCK WITH TUNING PEGS (Z: 38..45) ---
    # Classic sweeping asymmetric electric headstock (tilting slightly toward +X)
    fill_box(grid, 9, 12, 8, 10, 39, 41, 1)
    fill_box(grid, 10, 13, 8, 10, 41, 43, 1)
    fill_box(grid, 11, 14, 8, 10, 43, 45, 1)
    # Mahogany bevel & amber logo accent on headstock face
    fill_box(grid, 11, 14, 8, 9, 45, 45, 2)
    fill_box(grid, 11, 12, 10, 10, 42, 43, 9)
    fill_box(grid, 10, 11, 10, 10, 40, 40, 3)  # Headstock truss rod badge
    # Gleaming metallic silver tuning pegs & posts (4 bold pegs along +X side + 2 on -X)
    for tz, tx in ((40, 13), (42, 14), (44, 15)):
        fill_box(grid, tx, tx + 1, 9, 9, tz, tz, 5)
        grid[tx + 1, 9, tz] = 8  # Golden tuning button tip
        grid[tx - 2, 11, tz] = 5  # Front tuning post
    for tz, tx in ((40, 8), (42, 9)):
        fill_box(grid, tx - 1, tx, 9, 9, tz, tz, 5)
        grid[tx - 1, 9, tz] = 8

    return grid


# ==========================================
# FORM B: ROCK-KNIGHT GUITAR ROBOT (38 x 24 x 44)
# ==========================================
def build_b():
    grid = np.zeros((38, 24, 44), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 18 (-X robot left)
    cx_r = grid.shape[0] // 2      # 19 (+X robot right)

    # --- ROCK-KNIGHT BOOTS & FEET (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 8, 15, 0, 1, 6)    # Heavy charcoal soles
    fill_sym_box(grid, 3, 6, 7, 9, 0, 2, 2)     # Burgundy heel armor
    fill_sym_box(grid, 3, 6, 10, 17, 1, 2, 1)   # Cherry-red vamp
    fill_sym_box(grid, 4, 5, 9, 14, 1, 1, 0)    # Hollow unseen inner boot core
    fill_sym_box(grid, 4, 5, 14, 17, 2, 3, 3)   # Pearl-white toe guard
    fill_sym_box(grid, 4, 5, 17, 17, 1, 1, 5)   # Gleaming silver toe edge

    # --- SHINS WITH SILVER STRING STRIPES & PICKGUARD KNEES (Z: 3..15) ---
    fill_sym_box(grid, 3, 6, 9, 14, 3, 14, 1)
    fill_sym_box(grid, 4, 5, 10, 13, 3, 14, 0)  # Hollow shin core
    fill_sym_box(grid, 6, 6, 9, 13, 4, 13, 2)   # Outer mahogany bevel
    fill_sym_box(grid, 3, 3, 10, 13, 4, 13, 6)  # Inner mechanical frame
    # Gleaming Silver String Stripes running down front shins!
    fill_sym_box(grid, 4, 4, 14, 14, 4, 13, 5)
    fill_sym_box(grid, 5, 5, 14, 14, 4, 13, 3)
    # Flared Pearl-White & Gold Knee Guards
    fill_sym_box(grid, 3, 6, 14, 15, 12, 15, 3)
    fill_sym_box(grid, 4, 5, 15, 16, 13, 15, 1)
    fill_sym_box(grid, 4, 5, 16, 16, 14, 14, 8)  # Gold tone-knob knee jewel
    # Side ankle guitar-knob accents
    fill_sym_box(grid, 7, 7, 10, 12, 4, 6, 6)
    fill_sym_box(grid, 7, 7, 11, 11, 5, 5, 8)

    # --- MECHANICAL ROSEWOOD/CHARCOAL THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 20, 6)
    fill_sym_box(grid, 4, 4, 10, 12, 15, 20, 0)  # Hollow thigh interior
    fill_sym_box(grid, 3, 5, 13, 14, 16, 19, 4)  # Rosewood fretboard thigh plate
    fill_sym_box(grid, 4, 4, 14, 14, 16, 19, 5)  # Silver string stripe on thigh
    fill_sym_box(grid, 6, 6, 10, 12, 16, 19, 2)  # Burgundy outer thigh armor

    # --- BRIDGE-BUCKLE WAIST & HIP ARMOR (Z: 19..23) ---
    fill_sym_box(grid, 0, 5, 9, 13, 20, 22, 6)
    fill_sym_box(grid, 0, 4, 10, 12, 20, 22, 0)  # Hollow unseen waist core
    # Front waist skirts with pearl-white trim
    fill_sym_box(grid, 2, 5, 13, 14, 19, 22, 1)
    fill_sym_box(grid, 2, 5, 14, 14, 19, 19, 3)
    fill_sym_box(grid, 3, 4, 14, 14, 21, 21, 8)  # Golden knob studs
    # Center Guitar-Bridge Codpiece Buckle (with silver saddle!)
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 6)
    fill_sym_box(grid, 0, 1, 15, 15, 20, 21, 5)  # Silver bridge saddle
    fill_sym_box(grid, 0, 0, 15, 15, 22, 22, 7)  # Cyan amp LED
    # Side hip cutaway skirts
    fill_sym_box(grid, 6, 7, 9, 13, 19, 22, 2)
    fill_sym_box(grid, 7, 7, 10, 12, 20, 21, 3)

    # --- TORSO: SCULPTED GUITAR-BODY PICKGUARD & STRING CHEST (Z: 23..33) ---
    fill_sym_box(grid, 0, 6, 8, 14, 23, 32, 1)
    fill_sym_box(grid, 0, 5, 9, 13, 23, 31, 0)  # Hollow torso core
    # Recessed dark abdomen with golden fret-like ribs
    fill_sym_box(grid, 0, 4, 13, 14, 23, 25, 6)
    fill_sym_box(grid, 1, 3, 14, 14, 23, 23, 8)
    fill_sym_box(grid, 1, 3, 14, 14, 25, 25, 8)
    # Sculpted Guitar-Body Front Chest Plate (Y: 14..17, Z: 25..32)
    fill_sym_box(grid, 0, 5, 14, 17, 25, 32, 1)
    fill_sym_box(grid, 0, 4, 14, 16, 26, 31, 0)  # Hollow chest core
    # Warm amber sunburst framing inner chest
    fill_sym_box(grid, 0, 3, 17, 17, 27, 30, 9)
    # Bold Pearl-White Pickguard Chest Facings!
    fill_sym_box(grid, 2, 5, 17, 17, 26, 31, 3)
    fill_sym_box(grid, 5, 5, 16, 17, 26, 31, 2)  # Burgundy contoured outer edge
    # Dark Humbucker Pickup Vents + Glowing Electric-Cyan Amp Core!
    fill_sym_box(grid, 0, 2, 17, 17, 26, 26, 6)  # Lower chest pickup
    fill_sym_box(grid, 0, 2, 17, 17, 30, 30, 6)  # Upper chest pickup
    fill_sym_box(grid, 0, 1, 17, 18, 27, 29, 7)  # Glowing cyan amp-tube chest core!
    fill_sym_box(grid, 0, 0, 18, 18, 28, 28, 3)  # Bright center highlight
    # GLEAMING VERTICAL SILVER STRING STRIPES (弦の色!) across the entire chest!
    fill_sym_box(grid, 2, 2, 17, 18, 23, 32, 5)
    fill_sym_box(grid, 4, 4, 17, 17, 26, 31, 5)
    # Golden brass tone knobs on outer chest pickguard
    fill_sym_box(grid, 4, 4, 18, 18, 26, 26, 8)
    fill_sym_box(grid, 4, 4, 18, 18, 29, 29, 8)
    # Raised Double-Cutaway Collar Horns flanking the neck!
    fill_sym_box(grid, 3, 5, 10, 14, 32, 34, 1)
    fill_sym_box(grid, 4, 5, 11, 14, 34, 35, 2)
    fill_sym_box(grid, 4, 4, 14, 14, 33, 34, 3)

    # --- GUITAR-AMP & STAND BACKPACK (Y: 3..8, Z: 21..33) ---
    fill_sym_box(grid, 0, 5, 5, 8, 22, 32, 6)
    fill_sym_box(grid, 0, 4, 5, 7, 23, 31, 0)  # Hollow backpack interior
    # Twin guitar-amp speaker grille panels & red cab trim visible from rear!
    fill_sym_box(grid, 0, 5, 4, 4, 23, 31, 2)
    fill_sym_box(grid, 1, 4, 4, 4, 24, 30, 6)
    fill_sym_box(grid, 2, 3, 4, 4, 26, 28, 5)  # Silver speaker cones
    fill_sym_box(grid, 2, 3, 4, 4, 27, 27, 7)  # Glowing cyan amp LEDs
    fill_sym_box(grid, 0, 0, 4, 5, 23, 32, 8)  # Golden center control bar
    # Folded A-frame stand thruster nozzles at bottom of backpack
    fill_sym_box(grid, 2, 4, 3, 5, 21, 23, 6)
    fill_sym_box(grid, 3, 3, 3, 3, 21, 22, 7)

    # --- SWEEPING DOUBLE-CUTAWAY SHOULDER PAULDRONS (Z: 28..36, x_off: 7..12) ---
    fill_sym_box(grid, 6, 8, 10, 12, 29, 31, 6)
    fill_sym_box(grid, 7, 11, 8, 14, 29, 34, 1)
    fill_sym_box(grid, 8, 10, 9, 13, 29, 33, 0)  # Hollow pauldron interior
    fill_sym_box(grid, 8, 12, 9, 13, 33, 35, 1)  # Flared outer cutaway fin
    fill_sym_box(grid, 9, 11, 10, 12, 33, 34, 0)
    fill_sym_box(grid, 11, 12, 9, 13, 34, 36, 2)  # Burgundy horn tip
    fill_sym_box(grid, 8, 11, 14, 14, 30, 33, 3)  # Pearl-white front shoulder stripe
    fill_sym_box(grid, 9, 10, 14, 14, 31, 32, 7)  # Cyan shoulder amp vent
    fill_sym_box(grid, 11, 12, 10, 12, 30, 32, 5)  # Silver string shoulder bars
    # Tuning-peg gold/silver spikes on top of shoulders
    fill_sym_box(grid, 10, 10, 11, 11, 36, 37, 5)
    fill_sym_box(grid, 10, 10, 11, 11, 37, 37, 8)

    # --- ARMS & FOREARMS (Z: 14..29) ---
    fill_sym_box(grid, 8, 10, 10, 12, 23, 29, 6)
    fill_sym_box(grid, 9, 9, 11, 11, 24, 28, 0)  # Hollow upper arm core
    fill_sym_box(grid, 9, 10, 10, 12, 25, 27, 4)
    # Armored forearms with gleaming silver string trim
    fill_sym_box(grid, 8, 11, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 9, 10, 10, 13, 18, 21, 0)  # Hollow forearm interior
    fill_sym_box(grid, 8, 11, 14, 14, 18, 21, 3)  # White forearm cuff
    fill_sym_box(grid, 11, 11, 10, 13, 18, 21, 5)  # Silver string strip on outer forearm
    # Heavy mechanical fists
    fill_sym_box(grid, 8, 10, 10, 13, 14, 16, 6)
    fill_sym_box(grid, 8, 10, 13, 13, 14, 16, 5)  # Chrome knuckles

    # --- RIGHT HAND (+X, viewer's left): GUITAR-NECK GREATSWORD (Z: 9..43) ---
    # Held cleanly outward & forward of right shoulder (X: 30..33, Y: 16..18) so full fretboard & strings shine!
    sx = cx_r + 12  # 31 (blade X: 30..33, facing +Y so fretboard, frets & silver strings are unmistakable!)
    # Extended weapon-grip wrist bridge from right fist (X: 27..29, Y: 13) forward/outward to hilt (X: 30..32, Y: 16)
    fill_box(grid, cx_r + 9, sx, 13, 16, 14, 16, 6)
    # Lower rosewood hilt & golden pommel below fist (Z: 9..13)
    fill_box(grid, sx, sx + 1, 15, 16, 10, 14, 4)
    fill_box(grid, sx, sx + 1, 15, 16, 9, 10, 8)   # Golden pommel cap
    fill_box(grid, sx - 1, sx + 2, 15, 16, 11, 11, 5)
    # Sculpted Rock-Guitar Bridge Crossguard right above fist (Z: 16..18)
    fill_box(grid, sx - 2, sx + 3, 15, 17, 16, 18, 1)
    fill_box(grid, sx - 2, sx - 2, 15, 17, 17, 18, 2)
    fill_box(grid, sx + 3, sx + 3, 15, 17, 17, 18, 2)
    fill_box(grid, sx - 1, sx + 2, 17, 17, 17, 17, 6)  # Charcoal bridge bar
    fill_box(grid, sx, sx + 1, 17, 17, 18, 18, 7)      # Electric-cyan amp guard jewel
    # LONG FRETTED ROSEWOOD GUITAR-NECK BLADE (Z: 19..37, X: sx-1..sx+2, Y: 16..17)!
    # Warm rosewood fretboard facing +Y so every fret & silver string pops in Front 3/4 view!
    fill_box(grid, sx - 1, sx + 2, 16, 17, 19, 37, 4)
    # Crisp Golden Brass Frets across the fretboard face!
    for fz in (20, 23, 26, 29, 32, 35):
        fill_box(grid, sx - 1, sx + 2, 17, 17, fz, fz, 8)
    # Pearl-white fret inlay dots
    for iz in (21, 24, 27, 30, 33):
        grid[sx, 17, iz] = 3
    # GLEAMING METALLIC SILVER STRING BLADE EDGES (弦の色!) flanking both sides of the neck!
    fill_box(grid, sx - 1, sx - 1, 17, 18, 19, 37, 5)  # Inner razor silver string edge!
    fill_box(grid, sx + 2, sx + 2, 17, 18, 19, 38, 5)  # Outer razor silver string edge!
    # ANGLED ROCK HEADSTOCK BLADE-TIP WITH TUNING-PEG SERRATIONS (Z: 37..43)!
    fill_box(grid, sx - 1, sx + 2, 16, 17, 37, 39, 1)
    fill_box(grid, sx, sx + 3, 16, 17, 39, 41, 1)
    fill_box(grid, sx + 1, sx + 3, 16, 17, 41, 42, 2)
    fill_box(grid, sx + 2, sx + 3, 16, 17, 42, 43, 5)  # Sharp silver tip
    fill_box(grid, sx, sx + 1, 17, 17, 39, 40, 9)      # Amber sunburst headstock flare
    # Gleaming silver & gold tuning-peg barbs along outer headstock edge!
    for tz, tx in ((38, sx + 3), (40, sx + 4), (42, sx + 4)):
        fill_box(grid, tx, tx + 1, 16, 17, tz, tz, 5)
        grid[tx + 1, 17, tz] = 8

    # --- LEFT ARM (-X, viewer's right): FORWARD-FACING GUITAR-BODY SHIELD (ボディが盾! Z: 11..27) ---
    # Oriented facing FORWARD (+Y) on the left forearm (X: 0..8, Y: 14..17) so the iconic guitar-body
    # double-cutaway contour, pearl-white pickguard, pickups & gleaming silver strings shine in Front 3/4 view!
    fill_box(grid, cx_l - 12, cx_l - 10, 12, 15, 18, 21, 6)  # Solid arm-to-shield mount bracket
    sh_cx = 4.5  # Shield center X (spans X: 0..9, clear of left leg/torso)
    for x in range(0, 10):
        for z in range(11, 28):
            dx = x - sh_cx
            in_low = ((dx / 4.4) ** 2 + ((z - 15.8) / 4.5) ** 2) <= 1.0
            in_mid = (18.0 <= z <= 22.0) and (abs(dx) <= 3.3)
            in_top = ((dx / 4.0) ** 2 + ((z - 22.5) / 3.0) ** 2) <= 1.0
            in_horn_l = (((x - (sh_cx + 3.0)) / 1.5) ** 2 + ((z - 25.0) / 2.2) ** 2) <= 1.0
            in_horn_r = (((x - (sh_cx - 3.0)) / 1.5) ** 2 + ((z - 24.4) / 1.9) ** 2) <= 1.0
            if in_low or in_mid or in_top or in_horn_l or in_horn_r:
                if z >= 24.0 and abs(dx) < 1.5:
                    continue  # Authentic double-cutaway neck-pocket notch at top of shield!
                grid[x, 15, z] = 2  # Deep burgundy backplate
                grid[x, 16, z] = 1  # Electric cherry-red shield body
                if (dx ** 2 / 5.5 + (z - 17.5) ** 2 / 9.5) <= 1.0:
                    grid[x, 16, z] = 9  # Warm amber sunburst center
    # Pearl-White Pickguard, Charcoal Pickups, Golden Knobs & Gleaming Silver Strings on front face (Y=17)!
    fill_box(grid, 2, 6, 16, 17, 14, 22, 3)      # Crisp pearl-white pickguard
    fill_box(grid, 3, 6, 17, 17, 15, 15, 6)      # Bridge pickup bar
    fill_box(grid, 3, 6, 17, 17, 20, 20, 6)      # Neck pickup bar
    # Gleaming Silver String Stripes (弦の色!) running vertically up the Guitar-Body Shield!
    fill_box(grid, 3, 3, 17, 17, 13, 24, 5)
    fill_box(grid, 6, 6, 17, 17, 13, 24, 5)
    # Golden brass tone knobs & cyan amp jewel
    grid[2, 17, 15] = 8
    grid[2, 17, 18] = 8
    grid[4, 17, 17] = 7
    grid[5, 17, 17] = 7

    # --- HEROIC ROCK-KNIGHT HEAD WITH CYAN VISOR & GOLD V-CREST (Z: 33..42) ---
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 6)
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 1)
    fill_sym_box(grid, 0, 1, 10, 12, 35, 37, 0)  # Hollow head core
    fill_sym_box(grid, 0, 2, 10, 13, 38, 39, 3)  # Pearl-white helmet crown
    fill_sym_box(grid, 0, 0, 10, 14, 38, 40, 1)  # Center helmet mohawk ridge
    # Glowing Electric-Cyan Rock Visor!
    fill_sym_box(grid, 0, 2, 14, 14, 36, 37, 7)
    # Chrome faceplate mouthguard
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 5)
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 6)
    # Side helmet guitar-headstock ear fins
    fill_sym_box(grid, 3, 3, 10, 12, 35, 38, 2)
    fill_sym_box(grid, 3, 3, 11, 11, 36, 37, 5)  # Silver ear pegs
    # Golden Brass V-Crest & Cyan Forehead Jewel
    fill_sym_box(grid, 0, 0, 14, 15, 38, 39, 7)
    fill_sym_box(grid, 1, 1, 14, 15, 39, 40, 8)
    fill_sym_box(grid, 2, 3, 13, 14, 40, 42, 8)

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
    v_a = export_vox(model_a, "guitar_a.vox")
    v_b = export_vox(model_b, "guitar_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: ELECTRIC GUITAR -> ROCK-KNIGHT ROBOT",
        "1. ELECTRIC GUITAR (ON STAND)",
        "2. ROCK-KNIGHT GUITAR ROBOT",
        "preview_guitar.png",
        yaw_a=34, pitch_a=18, yaw_b=32, pitch_b=20,
    )
    print(f"guitar: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
