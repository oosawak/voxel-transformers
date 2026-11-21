import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (40, 44, 56, 255),     # Glossy Piano Lacquer Black (Body, Lid, Wings, Legs)
    2: (78, 86, 104, 255),    # Sleek Lacquer Highlight / Specular Bevel Grey
    3: (248, 246, 238, 255),  # Pure Ivory-White Piano Keys (白鍵) & Trim
    4: (18, 20, 26, 255),     # Deep Ebony Black Sharp Keys (黒鍵) & Inner Joints
    5: (238, 190, 56, 255),   # Gleaming Polished Brass / Gold Harp, Pedals, Hinges & Crown
    6: (200, 38, 50, 255),    # Rich Crimson Felt Trim & Maestro Lining
    7: (162, 106, 56, 255),   # Warm Spruce Wood Soundboard & Interior Accent
    8: (196, 210, 226, 255),  # Silver Piano Strings, Tuning Pins & Struts
    9: (76, 224, 255, 255),   # Luminous Cyan Maestro Visor & Energy Core
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


def piano_body_mask(x, y):
    """Iconic Concert Grand Piano wing-shaped footprint in (x, y).
    +Y is FRONT (keyboard), +X is straight bass spine (lid hinge), -X is curved treble bentside.
    """
    if y < 2 or y > 24 or x < 2 or x > 23:
        return False
    # Rounded rear tail (y: 2..11)
    if y < 11:
        # Elliptical tail centered around (16.5, 10.5)
        dx = (x - 16.5) / 6.8
        dy = (y - 10.5) / 8.5
        return (dx * dx + dy * dy) <= 1.0 and x <= 23
    # Front keyboard cheek block (y: 20..24)
    if y >= 20:
        return 2 <= x <= 23
    # Sweeping treble S-curve bentside (y: 11..20)
    t = (y - 11.0) / 9.0  # 0 at tail waist -> 1 at front treble cheek
    x_min = 9.7 - 7.7 * (0.5 - 0.5 * np.cos(np.pi * t))
    return x_min <= x <= 23


# ==========================================
# FORM A: CONCERT GRAND PIANO (26 x 30 x 26)
# ==========================================
def build_a():
    grid = np.zeros((26, 30, 26), dtype=np.uint8)

    # --- THREE TURNED BLACK LACQUER LEGS WITH BRASS CASTERS (Z: 0..8) ---
    legs = [
        (21, 22),  # Front-left (bass) leg
        (4, 22),   # Front-right (treble) leg
        (16, 5),   # Rear tail leg
    ]
    for lx, ly in legs:
        # Gleaming golden brass caster wheel & ferrule (Z: 0..1)
        fill_box(grid, lx, lx + 1, ly, ly + 1, 0, 1, 5)
        # Tapered turned lacquer column (Z: 2..6)
        fill_box(grid, lx, lx + 1, ly, ly + 1, 2, 6, 1)
        grid[lx, ly + 1, 3] = 2
        grid[lx, ly + 1, 5] = 2
        # Upper square capital block & brass trim ring joining rim (Z: 7..8)
        fill_box(grid, lx - 1, lx + 1, ly - 1, ly + 1, 7, 8, 1)
        fill_box(grid, lx, lx + 1, ly, ly + 1, 6, 6, 5)  # Brass collar ring

    # --- BRASS PEDAL LYRE UNDERNEATH KEYBED (Z: 1..8, X: 11..15, Y: 18..21) ---
    fill_box(grid, 11, 11, 18, 19, 2, 8, 1)  # Left lyre pillar
    fill_box(grid, 15, 15, 18, 19, 2, 8, 1)  # Right lyre pillar
    fill_box(grid, 11, 15, 18, 20, 1, 2, 1)  # Lower pedal box
    fill_box(grid, 12, 14, 18, 18, 3, 8, 5)  # Twin brass vertical pedal rods
    # Three gleaming golden brass concert pedals jutting forward!
    fill_box(grid, 11, 11, 20, 22, 1, 1, 5)
    fill_box(grid, 13, 13, 20, 22, 1, 1, 5)
    fill_box(grid, 15, 15, 20, 22, 1, 1, 5)

    # --- CURVED GRAND PIANO BODY / RIM & GOLDEN HARP INTERIOR (Z: 8..13) ---
    body_cells = set()
    for x in range(2, 24):
        for y in range(2, 25):
            if piano_body_mask(x, y):
                body_cells.add((x, y))

    for x, y in body_cells:
        is_outer_rim = any(
            (x + dx, y + dy) not in body_cells
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        # Bottom belly plate (Z: 8..9) - leave slight center hollow under soundboard
        grid[x, y, 8] = 1
        grid[x, y, 9] = 7 if not is_outer_rim else 1
        if is_outer_rim:
            # Tall curved glossy lacquer rim wall (Z: 8..13)
            for z in range(8, 14):
                grid[x, y, z] = 2 if z == 13 else 1
        else:
            # Warm spruce wood soundboard inside the open rim (Z=10)
            grid[x, y, 10] = 7

    # Hollow unseen belly interior at Z=8..9 where safely surrounded (keeps soundboard Z=10 solid!)
    for x, y in body_cells:
        if all((x + dx, y + dy) in body_cells for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            if not (10 <= x <= 16 and 17 <= y <= 20):  # Keep lyre anchor solid
                if not ((3 <= x <= 6 and 21 <= y <= 24) or (20 <= x <= 23 and 21 <= y <= 24) or (15 <= x <= 18 and 4 <= y <= 7)):
                    grid[x, y, 8] = 0
                    grid[x, y, 9] = 0

    # --- GLEAMING GOLDEN BRASS HARP FRAME & SILVER STRINGS INSIDE (Z: 11) ---
    for x, y in body_cells:
        if any((x + dx, y + dy) not in body_cells for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            continue
        # Perimeter golden cast-iron harp plate near tail & pinblock
        if y >= 19 or y <= 6 or x >= 21:
            grid[x, y, 11] = 5
        # Radiating golden brass harp struts
        elif abs((x - 19) - 0.35 * (y - 5)) <= 0.8 or abs((x - 15) - 0.55 * (y - 6)) <= 0.8:
            grid[x, y, 11] = 5
        # Gleaming silver strings stretched across the warm spruce soundboard!
        elif (x + y // 3) % 2 == 0 and y < 19:
            grid[x, y, 11] = 8
    # Tuning pins (silver dots along pinblock at Y=20..21)
    for px in range(5, 21, 2):
        grid[px, 20, 12] = 8
    # Crimson felt damper bar across the strings
    fill_box(grid, 5, 20, 18, 18, 11, 11, 6)

    # --- EXPOSED CRISP PIANO KEYBOARD (鍵盤) & MUSIC DESK (Y: 23..28, Z: 9..16) ---
    # Keybed shelf & cheek blocks
    fill_box(grid, 2, 23, 23, 28, 9, 10, 1)
    fill_box(grid, 2, 3, 23, 28, 10, 12, 1)   # Treble cheek block
    fill_box(grid, 22, 23, 23, 28, 10, 12, 1)  # Bass cheek block
    fill_box(grid, 2, 3, 28, 28, 12, 12, 2)    # Cheek lacquer highlight
    fill_box(grid, 22, 23, 28, 28, 12, 12, 2)
    # Pure Ivory-White Natural Keys (白鍵: X: 4..21, Y: 25..28, Z: 11)
    fill_box(grid, 4, 21, 25, 28, 11, 11, 3)
    # Deep Ebony Black Sharp Keys (黒鍵: authentic 2-3-2 octave pattern, Z: 12, Y: 25..26)
    for kx in (5, 7, 10, 12, 14, 17, 19):
        fill_box(grid, kx, kx, 25, 26, 12, 12, 4)
    # Rich Crimson Felt Strip directly above the keys!
    fill_box(grid, 4, 21, 24, 24, 11, 12, 6)
    # Glossy black fallboard & sleek upright Music Desk with Ivory Sheet Music
    fill_box(grid, 4, 21, 22, 23, 12, 13, 1)
    fill_box(grid, 8, 17, 22, 22, 13, 15, 1)
    fill_box(grid, 8, 17, 22, 22, 15, 15, 5)  # Brass music desk rail
    fill_box(grid, 9, 12, 23, 23, 13, 15, 3)  # Left sheet music page
    fill_box(grid, 14, 17, 23, 23, 13, 15, 3)  # Right sheet music page

    # --- DRAMATICALLY PROPPED-OPEN CURVED GRAND LID (大蓋, Z: 13..25) ---
    # Hinged along straight bass spine (X=23, Z=13), sweeping upward toward curved treble side (-X)!
    for x, y in body_cells:
        if y > 22:
            continue
        dx = 23 - x
        z_lid = 13 + int(round(dx * 0.56))
        z_prev = 13 + int(round(max(0, dx - 1) * 0.56))
        # Ensure strict 6-connectivity along the diagonal rise
        z_lo = min(z_lid, z_prev)
        is_lid_edge = (
            y == 22
            or x == 23
            or any((x + ox, y + oy) not in body_cells for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        )
        for zz in range(z_lo, z_lid + 1):
            if 0 <= zz < 26:
                if zz == z_lid and is_lid_edge:
                    grid[x, y, zz] = 2  # Crisp lacquer bevel highlight around lid edge
                elif zz == z_lid and (dx in (6, 12) and 8 <= y <= 19):
                    grid[x, y, zz] = 2  # Subtle specular gloss streak on top of lid
                else:
                    grid[x, y, zz] = 1
    # Gleaming Golden Brass Hinges along the straight +X bass spine (X=23, Z=13)
    for hy in (9, 15, 20):
        grid[23, hy, 13] = 5
        grid[23, hy, 14] = 5
    # Gleaming Golden Brass Lid Prop Stick holding the open lid high!
    # Anchored inside treble rim at X=7, Y=17, rising solidly to lid underside
    prop_z_top = 13 + int(round((23 - 7) * 0.56))
    fill_box(grid, 7, 7, 17, 17, 10, prop_z_top, 5)
    grid[7, 17, 11] = 8  # Silver brass-cup base

    return grid


# ==========================================
# FORM B: MAESTRO GRAND-PIANO ROBOT (38 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((38, 24, 42), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 18 (-X robot left)
    cx_r = grid.shape[0] // 2      # 19 (+X robot right)

    # --- TURNED PIANO-LEG FEET WITH BRASS CASTER WHEELS (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 8, 15, 0, 1, 4)    # Ebony soles
    fill_sym_box(grid, 4, 5, 7, 9, 0, 1, 5)     # Rear brass caster heel!
    fill_sym_box(grid, 3, 6, 11, 16, 1, 2, 1)   # Glossy lacquer vamp
    fill_sym_box(grid, 4, 5, 9, 14, 1, 1, 0)    # Hollow unseen foot interior
    fill_sym_box(grid, 4, 5, 14, 17, 0, 1, 5)   # Front brass caster toe-roller!
    fill_sym_box(grid, 4, 5, 13, 16, 2, 2, 2)   # Lacquer specular highlight

    # --- SLEEK TURNED PIANO LEGS AS ROBOT LEGS (脚がそのまま脚! Z: 3..15) ---
    fill_sym_box(grid, 3, 5, 9, 13, 3, 13, 1)
    fill_sym_box(grid, 4, 4, 10, 12, 3, 13, 0)  # Hollow shin core
    # Turned lacquer highlight flutes on front & outer leg
    fill_sym_box(grid, 4, 4, 13, 14, 5, 11, 2)
    fill_sym_box(grid, 5, 5, 10, 12, 5, 11, 2)
    # Gleaming Golden Brass Turned Collar Rings (piano leg capitals & ferrules!)
    fill_sym_box(grid, 3, 6, 9, 14, 3, 3, 5)    # Lower brass ankle ferrule
    fill_sym_box(grid, 3, 6, 9, 14, 11, 11, 5)  # Upper turned brass ring
    # Sculpted Piano-Cheek Knee Guards with Ivory & Crimson accents
    fill_sym_box(grid, 3, 6, 13, 15, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 15, 15, 13, 14, 3)  # Ivory knee crest
    fill_sym_box(grid, 4, 5, 15, 15, 12, 12, 6)  # Crimson felt accent
    fill_sym_box(grid, 4, 5, 15, 15, 15, 15, 5)  # Gold knee crown

    # --- ELEGANT MECHANICAL THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 20, 4)
    fill_sym_box(grid, 4, 4, 10, 12, 15, 20, 0)  # Hollow thigh interior
    fill_sym_box(grid, 3, 5, 12, 13, 16, 19, 1)  # Front black thigh plate
    fill_sym_box(grid, 4, 4, 13, 13, 16, 19, 8)  # Silver tuning-strut piston
    fill_sym_box(grid, 5, 5, 10, 12, 16, 19, 2)

    # --- PEDAL-LYRE WAIST & TUXEDO TAILCOAT SKIRTS (Z: 18..23) ---
    fill_sym_box(grid, 0, 5, 9, 13, 20, 22, 4)
    fill_sym_box(grid, 0, 4, 10, 12, 20, 22, 0)  # Hollow waist core
    # Front tuxedo waist tassets in glossy black + crimson lining
    fill_sym_box(grid, 2, 5, 13, 14, 19, 22, 1)
    fill_sym_box(grid, 2, 5, 14, 14, 19, 19, 5)  # Gold skirt trim
    fill_sym_box(grid, 3, 4, 14, 14, 21, 21, 6)  # Crimson sash inlay
    # Center Golden Brass Pedal-Lyre Buckle (3 vertical gold pedals!)
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 1)
    fill_sym_box(grid, 0, 1, 15, 15, 19, 21, 5)  # Gleaming brass pedal motif
    grid[cx_l, 15, 20] = 4
    grid[cx_r, 15, 20] = 4
    # Rear tuxedo coattails & side hip panels
    fill_sym_box(grid, 6, 7, 9, 13, 19, 22, 1)
    fill_sym_box(grid, 7, 7, 10, 12, 20, 21, 2)
    fill_sym_box(grid, 1, 4, 8, 9, 17, 21, 1)
    fill_sym_box(grid, 1, 4, 8, 8, 17, 17, 6)  # Crimson coattail hem

    # --- TORSO: ICONIC PIANO KEYBOARD CHEST & GOLDEN HARP CORE (Z: 23..33) ---
    fill_sym_box(grid, 0, 6, 8, 14, 23, 32, 1)
    fill_sym_box(grid, 0, 5, 9, 13, 23, 31, 0)  # Hollow torso core
    # Recessed ebony abdomen with warm spruce/gold harp ribs
    fill_sym_box(grid, 0, 4, 13, 14, 23, 25, 4)
    fill_sym_box(grid, 1, 3, 14, 14, 23, 25, 7)
    fill_sym_box(grid, 0, 2, 14, 14, 24, 24, 5)  # Gold waist harp bar
    # PROMINENT KEYBOARD CHEST DECK (Y: 14..18, Z: 25..31)
    fill_sym_box(grid, 0, 6, 14, 17, 25, 31, 1)
    fill_sym_box(grid, 0, 5, 14, 16, 26, 30, 0)  # Hollow chest cavity
    # Glossy black piano-cheek borders framing the chest keyboard
    fill_sym_box(grid, 6, 6, 15, 18, 26, 29, 1)
    fill_sym_box(grid, 6, 6, 18, 18, 26, 29, 2)
    # CRISP IVORY-WHITE PIANO KEYBOARD WRAPPING ACROSS CHEST! (12 wide: x_off 0..5, Z: 26..28, Y: 17..18)
    fill_sym_box(grid, 0, 5, 17, 18, 26, 28, 3)
    # Raised DEEP EBONY SHARP KEYS (黒鍵) in unmistakable piano 2-3-2 grouping across Y=18, Z=27..28!
    for kx in (cx_l - 4, cx_l - 2, cx_r, cx_r + 2, cx_r + 4):
        fill_box(grid, kx, kx, 18, 18, 27, 28, 4)
    # Rich Crimson Felt Collar Strip directly above the keyboard! (Z: 29, Y: 17..18)
    fill_sym_box(grid, 0, 5, 17, 18, 29, 29, 6)
    # Upper Chest Golden Brass Harp & Luminous Cyan Maestro Core (Z: 30..32)
    fill_sym_box(grid, 0, 5, 15, 17, 30, 31, 5)
    fill_sym_box(grid, 2, 4, 17, 17, 30, 31, 8)  # Silver harp strings
    fill_sym_box(grid, 0, 1, 17, 18, 30, 31, 9)  # Luminous cyan chest jewel!
    # Raised tuxedo-collar armor flanking neck
    fill_sym_box(grid, 2, 5, 10, 14, 32, 33, 1)
    fill_sym_box(grid, 3, 5, 13, 14, 33, 33, 5)

    # --- BACKPACK & UNFOLDED CURVED GRAND-LID WING-CAPE PANELS (大蓋が背中の翼! Z: 18..39) ---
    fill_sym_box(grid, 0, 4, 5, 8, 23, 32, 1)
    fill_sym_box(grid, 0, 3, 6, 7, 24, 31, 0)  # Hollow backpack core (keep Y=5 wall solid for rear harp)
    fill_sym_box(grid, 0, 2, 4, 4, 25, 30, 5)  # Golden brass harp spine on rear!
    fill_sym_box(grid, 1, 1, 4, 4, 26, 29, 8)  # Silver strings on rear
    fill_sym_box(grid, 0, 0, 4, 4, 27, 28, 9)  # Cyan rear core
    # Gleaming Golden Brass Wing Hinges connecting backpack to Grand-Lid Wings
    fill_sym_box(grid, 4, 6, 5, 6, 25, 30, 5)

    # Sleek 1-voxel-thick Sweeping Grand-Lid Wing Panels flaring dramatically outward!
    for x_off in range(5, 16):
        t = (x_off - 5.0) / 10.0
        z_top = int(round(32 + 7.5 * np.sin(np.pi * 0.62 * t) + 1.5 * t))
        z_bot = int(round(19 + 11.0 * (t ** 1.35)))
        y_wing = 5 - int(round(2.4 * t))
        y_prev = 5 - int(round(2.4 * max(0.0, (x_off - 6.0) / 10.0)))
        for z in range(z_bot, z_top + 1):
            is_edge = (z == z_top or z == z_bot or x_off == 15)
            if is_edge:
                col = 2  # Crisp lacquer bevel highlight tracing the curved grand-lid wing!
            elif z == z_top - 1 and x_off <= 13:
                col = 5  # Golden brass wing spar
            elif z == z_bot + 1 and x_off <= 12:
                col = 6  # Rich crimson inner wing lining
            elif (x_off + z) % 4 == 0 and x_off <= 12:
                col = 8  # Silver string shimmer
            else:
                col = 1  # Glossy piano lacquer black
            fill_sym_box(grid, x_off, x_off, y_wing, y_wing, z, z, col)
            # Only add minimal bridge voxel when y steps back so wings stay ultra-sleek & 6-connected!
            if y_wing != y_prev and (z in (z_top, z_bot) or z % 3 == 0):
                fill_sym_box(grid, x_off, x_off, y_prev, y_prev, z, z, col)

    # --- CURVED PIANO-CHEEK SHOULDER PAULDRONS & ARMS (Z: 14..34) ---
    fill_sym_box(grid, 6, 8, 10, 12, 29, 31, 4)
    fill_sym_box(grid, 7, 11, 8, 14, 29, 33, 1)
    fill_sym_box(grid, 8, 10, 9, 13, 29, 32, 0)  # Hollow pauldron core
    fill_sym_box(grid, 7, 11, 9, 13, 33, 34, 2)  # Specular curved top bevel
    fill_sym_box(grid, 8, 10, 10, 12, 33, 33, 0)
    fill_sym_box(grid, 8, 11, 14, 14, 30, 32, 5)  # Brass front trim
    fill_sym_box(grid, 9, 10, 14, 14, 31, 31, 3)  # Ivory key accent
    fill_sym_box(grid, 11, 11, 9, 13, 29, 32, 6)  # Crimson shoulder edge
    # Upper arms
    fill_sym_box(grid, 8, 9, 10, 12, 23, 29, 4)
    fill_sym_box(grid, 9, 9, 11, 12, 25, 27, 5)  # Brass bicep ring
    # Sleek lacquer forearms
    fill_sym_box(grid, 8, 10, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 9, 9, 10, 13, 18, 21, 0)  # Hollow forearm interior
    fill_sym_box(grid, 8, 10, 14, 14, 18, 21, 2)
    fill_sym_box(grid, 8, 10, 14, 14, 19, 20, 3)  # White cuff key-stripe
    # Ebony mechanical fists
    fill_sym_box(grid, 8, 10, 10, 13, 14, 16, 4)
    fill_sym_box(grid, 8, 10, 13, 13, 14, 16, 5)  # Brass knuckle guard

    # --- RIGHT HAND (+X, viewer's left): BRASS PROP-STICK CONDUCTOR'S RAPIER (Z: 10..39) ---
    # Held cleanly forward & outward of right shoulder (X: 30..31, Y: 16..18)
    rx = cx_r + 11  # 30
    fill_box(grid, cx_r + 9, rx, 13, 16, 14, 16, 4)  # Fist-to-hilt bridge
    fill_box(grid, rx, rx, 15, 16, 11, 17, 1)        # Black lacquer grip
    fill_box(grid, rx, rx, 15, 16, 10, 11, 5)        # Gold pommel
    # Ornate Golden Lyre-Basket Handguard (Z: 17..20)
    fill_box(grid, rx - 1, rx + 1, 14, 19, 17, 18, 5)
    fill_box(grid, rx, rx, 18, 19, 18, 20, 5)
    fill_box(grid, rx, rx, 16, 17, 18, 19, 6)        # Crimson hilt jewel
    # Sleek Golden Brass Prop-Stick & Silver String Rapier Blade (Z: 19..39)!
    fill_box(grid, rx, rx, 16, 17, 19, 36, 5)        # Gleaming brass prop-stick spine
    fill_box(grid, rx, rx, 18, 18, 20, 38, 8)        # Razor silver piano-string edge
    fill_box(grid, rx, rx, 17, 17, 37, 39, 9)        # Luminous cyan baton tip

    # --- LEFT ARM (-X, viewer's right): FORWARD-FACING CURVED GRAND-PIANO LID SHIELD (大蓋が盾! Z: 11..27) ---
    # Mounted facing FORWARD (+Y) on the left forearm (X: 1..9, Y: 15..17) so the curved grand-lid contour,
    # golden brass harp, warm spruce soundboard & silver strings shine unmistakably in Front 3/4 view!
    fill_box(grid, cx_l - 12, cx_l - 10, 12, 15, 18, 21, 5)  # Brass arm-to-shield mount
    for x in range(1, 10):
        for z in range(11, 28):
            # Iconic Grand-Piano curved wing-lid silhouette in (x, z)!
            # Straight bass edge on inner side (x=9), sweeping S-curve bentside on outer edge (x=1..5)!
            if z < 16:
                x_min, x_max = 1, 9
            elif z < 23:
                u = (z - 16.0) / 7.0
                x_min = int(round(1 + 3.8 * (0.5 - 0.5 * np.cos(np.pi * u))))
                x_max = 9
            else:
                dx = (x - 6.8) / 2.6
                dz = (z - 22.5) / 5.0
                if (dx * dx + dz * dz) > 1.0:
                    continue
                x_min, x_max = 4, 9
            if x_min <= x <= x_max:
                is_rim = (x in (x_min, x_max) or z in (11, 27))
                grid[x, 15, z] = 4  # Ebony backing
                grid[x, 16, z] = 2 if is_rim else 1  # Glossy lacquer grand lid with specular rim!
    # Inlaid Golden Brass Harp, Warm Spruce Soundboard & Silver Strings on front shield face (Y=17)!
    fill_box(grid, 4, 8, 17, 17, 14, 22, 7)  # Warm spruce soundboard heart
    fill_box(grid, 3, 8, 17, 17, 13, 14, 5)  # Gold harp base
    fill_box(grid, 8, 8, 17, 17, 14, 23, 5)  # Gold harp straight bass spine
    fill_box(grid, 5, 7, 17, 17, 22, 23, 5)  # Gold harp tail arch
    fill_box(grid, 5, 5, 17, 17, 15, 21, 8)  # Silver piano string
    fill_box(grid, 7, 7, 17, 17, 15, 21, 8)  # Silver piano string
    fill_box(grid, 2, 8, 17, 17, 12, 12, 6)  # Crimson felt trim at shield bottom
    fill_box(grid, 3, 4, 17, 17, 15, 17, 3)  # Ivory key emblem

    # --- MAESTRO KNIGHT HEAD WITH CYAN VISOR & GOLD LYRE V-CREST (Z: 33..41) ---
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 4)
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 1)
    fill_sym_box(grid, 0, 1, 10, 12, 35, 37, 0)  # Hollow head core
    fill_sym_box(grid, 0, 2, 10, 13, 38, 39, 2)  # Specular helmet crown
    fill_sym_box(grid, 0, 0, 10, 14, 38, 39, 5)  # Golden center crest ridge
    # Luminous Cyan Maestro Visor Eyes!
    fill_sym_box(grid, 0, 2, 14, 14, 36, 37, 9)
    # Ivory faceplate mouthguard
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 3)
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 4)
    # Side helmet gold/lacquer ear-fin guards
    fill_sym_box(grid, 3, 3, 10, 12, 35, 38, 1)
    fill_sym_box(grid, 3, 3, 11, 11, 36, 37, 5)
    # Sweeping Golden Brass Lyre V-Crest & Crimson Forehead Jewel!
    fill_sym_box(grid, 0, 0, 14, 15, 38, 39, 6)  # Crimson jewel
    fill_sym_box(grid, 1, 1, 14, 15, 39, 40, 5)  # Inner gold lyre horn
    fill_sym_box(grid, 2, 3, 13, 14, 40, 41, 5)  # Swept golden lyre tips

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
    v_a = export_vox(model_a, "piano_a.vox")
    v_b = export_vox(model_b, "piano_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: CONCERT GRAND PIANO -> MAESTRO ROBOT",
        "1. CONCERT GRAND PIANO",
        "2. MAESTRO GRAND-PIANO ROBOT",
        "preview_piano.png",
        yaw_a=-36, pitch_a=25, yaw_b=32, pitch_b=20,
    )
    print(f"piano: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
