import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (128, 140, 154, 255),  # Naval Battleship Steel Grey (Upper Hull, Superstructure, Armor)
    2: (68, 76, 90, 255),     # Darker Gunmetal Shadow (Armor Trim, Joints, Turret Roof)
    3: (166, 36, 44, 255),    # Deep Crimson Anti-Fouling Lower Hull (喫水線下の赤)
    4: (196, 158, 104, 255),  # Warm Teak Wooden Deck Tan (甲板)
    5: (34, 40, 52, 255),     # Crisp Dark Navy/Black (Gun Barrels, Funnel Cap, Recesses)
    6: (198, 208, 220, 255),  # Light Silver-Grey (Radar, Rangefinder, Trim, Blade Edge)
    7: (84, 212, 248, 255),   # Glowing Cyan (Bridge Windows, Admiral Robot Visor)
    8: (248, 184, 52, 255),   # Warm Golden-Orange (Muzzle Accent, Searchlights, Crest)
    9: (242, 246, 252, 255),  # Signal White (Hull Waterline Stripe, Naval Insignia)
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
# FORM A: DREADNOUGHT BATTLESHIP (16 x 48 x 20)
# ==========================================
def build_a():
    grid = np.zeros((16, 48, 20), dtype=np.uint8)

    # --- SLEEK TAPERED BATTLESHIP HULL (Y: 2..46, Z: 0..6) ---
    # Compute hull half-width profile (x_off_max) from stern (Y=2) to clipper bow (Y=46)
    def hull_half_w(y):
        if y < 2 or y > 46:
            return -1
        if y <= 5:
            return 2 + (y - 2) // 2       # Stern rounds from 2 -> 3
        if y <= 10:
            return 4
        if y <= 31:
            return 5                      # Broad dreadnought amidships beam
        if y <= 35:
            return 4
        if y <= 39:
            return 3
        if y <= 42:
            return 2
        if y <= 44:
            return 1
        return 0                          # Sharp knife-edge clipper bow

    # Build hollow-shell hull layer by layer for clean voxel count & authentic flared prow
    for y in range(2, 47):
        w_deck = hull_half_w(y)
        # Keel narrows slightly below waterline
        w_keel = max(0, w_deck - 1) if y > 4 else max(0, w_deck - 1)
        # Z=0..1: Deep Crimson Anti-Fouling Lower Hull (喫水線下の赤)
        fill_sym_box(grid, 0, w_keel, y, y, 0, 0, 3)
        fill_sym_box(grid, 0, w_deck, y, y, 1, 2, 3)
        # Z=3..4: Naval Battleship Steel Grey Upper Hull
        fill_sym_box(grid, 0, w_deck, y, y, 3, 4, 1)
        # Z=5: Warm Teak Wooden Main Deck with Steel Grey Gunwale Rim
        fill_sym_box(grid, 0, w_deck, y, y, 5, 5, 4)
        fill_sym_box(grid, w_deck, w_deck, y, y, 5, 5, 1)

        # Hollow out completely unseen interior core of the hull (Z: 1..4)
        if 4 <= y <= 41 and w_deck >= 2:
            inner_w = max(0, w_deck - 2)
            fill_sym_box(grid, 0, inner_w, y, y, 1, 4, 0)

    # Flared Atlantic/Yamato Clipper Bow Rising at Prow (Y: 41..46, Z: 6)
    fill_sym_box(grid, 0, 2, 40, 42, 6, 6, 1)
    fill_sym_box(grid, 0, 1, 43, 45, 6, 6, 1)
    fill_sym_box(grid, 0, 0, 45, 46, 6, 6, 1)
    fill_sym_box(grid, 0, 0, 46, 46, 5, 6, 8)   # Golden Imperial Bow Crest
    fill_sym_box(grid, 0, 1, 41, 43, 5, 5, 4)   # Raised teak foredeck
    # Dark anchor chains on foredeck
    fill_sym_box(grid, 1, 1, 38, 42, 6, 6, 5)

    # Hull Waterline & Armor Belt Styling
    for y in range(6, 39):
        w = hull_half_w(y)
        # Crisp dark navy waterline shadow stripe at Z=2/3 transition on midships
        if 11 <= y <= 31:
            fill_sym_box(grid, w, w, y, y, 3, 3, 2)  # Gunmetal midship armor belt
        # Signal white hull identification stripe near bow
        if y in (36, 37, 38):
            fill_sym_box(grid, w, w, y, y, 4, 4, 9)
    # Rudder & twin brass/gold propellers at stern (Y: 1..3, Z: 0..1)
    fill_sym_box(grid, 0, 0, 1, 2, 0, 1, 3)
    fill_sym_box(grid, 2, 2, 2, 3, 0, 0, 8)

    # --- MASSIVE MAIN GUN TURRETS (主砲塔!) ---
    # Helper to draw an iconic battleship main turret (twin heavy barrels + blast bags + muzzle tips)
    def build_turret(y_back, y_front, z_base, dir_y):
        # Armored barbette & turret house
        fill_sym_box(grid, 0, 2, y_back, y_front, z_base, z_base + 1, 1)
        fill_sym_box(grid, 0, 1, y_back + 1, y_front - 1, z_base, z_base, 0)  # Hollow interior
        fill_sym_box(grid, 0, 2, y_back, y_front, z_base + 2, z_base + 2, 2)  # Sloped dark roof
        fill_sym_box(grid, 0, 1, y_back + 1, y_front - 1, z_base + 2, z_base + 2, 1)
        # Rangefinder ears on turret sides
        y_mid = (y_back + y_front) // 2
        fill_sym_box(grid, 3, 3, y_mid, y_mid, z_base + 1, z_base + 1, 6)
        # Blast bags & Twin Long Dark Navy Main Gun Barrels!
        y_face = y_front if dir_y > 0 else y_back
        fill_sym_box(grid, 1, 1, y_face, y_face, z_base + 1, z_base + 1, 6)  # Silver blast bags
        y_b0 = y_face + dir_y
        y_b1 = y_face + dir_y * 5
        fill_sym_box(grid, 1, 1, y_b0, y_b1, z_base + 1, z_base + 1, 5)      # Dark navy barrels
        fill_sym_box(grid, 1, 1, y_b1, y_b1, z_base + 1, z_base + 1, 8)      # Golden muzzle rim

    # Turret #1: Forward A-Turret (Y: 32..36, Z: 6..8, pointing +Y)
    build_turret(32, 36, 6, dir_y=+1)
    # Turret #2: Superfiring Elevated B-Turret (Y: 26..30, Z: 7..9, pointing +Y)
    fill_sym_box(grid, 0, 2, 26, 30, 6, 6, 2)  # Armored superfiring barbette base
    build_turret(26, 30, 7, dir_y=+1)
    # Turret #3: Aft C-Turret (Y: 9..13, Z: 6..8, pointing -Y)
    build_turret(9, 13, 6, dir_y=-1)

    # --- TOWERING PAGODA BRIDGE SUPERSTRUCTURE (艦橋) (Y: 14..25, Z: 6..19) ---
    # Broad lower armored citadel deckhouse (Y: 14..25, Z: 6..8)
    fill_sym_box(grid, 0, 3, 14, 25, 6, 8, 1)
    fill_sym_box(grid, 0, 2, 15, 24, 6, 7, 0)  # Hollow citadel core
    fill_sym_box(grid, 0, 3, 14, 25, 8, 8, 2)  # Citadel upper deck
    # Anti-aircraft secondary gun tubs flanking the superstructure
    for aay in (16, 20, 23):
        fill_sym_box(grid, 4, 4, aay, aay + 1, 6, 7, 2)
        fill_sym_box(grid, 4, 4, aay, aay, 8, 8, 5)
    # Lifeboats tucked along superstructure flanks
    fill_sym_box(grid, 4, 4, 12, 14, 6, 6, 9)

    # Tiered Pagoda Bridge Tower (Y: 20..24, Z: 9..15)
    fill_sym_box(grid, 0, 2, 20, 24, 9, 11, 1)
    fill_sym_box(grid, 0, 1, 21, 23, 9, 10, 0)  # Hollow bridge tower
    # Bridge Wings + Glowing Cyan Bridge Windows + Golden Searchlights!
    fill_sym_box(grid, 0, 3, 21, 24, 11, 11, 1)
    fill_sym_box(grid, 0, 2, 24, 24, 11, 11, 7)  # Glowing cyan forward bridge windows
    fill_sym_box(grid, 3, 3, 22, 23, 11, 11, 7)  # Side bridge wing windows
    fill_sym_box(grid, 3, 3, 21, 21, 10, 10, 8)  # Warm golden naval searchlights
    # Upper Fire-Control Tower & Wide Optical Rangefinder (Z: 12..14)
    fill_sym_box(grid, 0, 1, 21, 23, 12, 14, 1)
    fill_sym_box(grid, 0, 1, 24, 24, 13, 13, 7)  # Upper director window
    fill_sym_box(grid, 0, 3, 22, 22, 14, 14, 6)  # Wide silver-grey rangefinder bar!
    # Tall Pagoda Radar Mast (Z: 15..19)
    fill_sym_box(grid, 0, 0, 22, 22, 15, 19, 6)
    fill_sym_box(grid, 0, 2, 22, 22, 17, 17, 6)  # Radar cross-yardarm
    fill_sym_box(grid, 0, 1, 22, 23, 16, 16, 2)  # Crow's nest radar dish
    fill_sym_box(grid, 0, 0, 22, 22, 19, 19, 9)  # Signal white mast peak

    # --- RAKE-BACK SMOKESTACK FUNNEL (Y: 15..18, Z: 9..14) ---
    fill_sym_box(grid, 0, 1, 16, 18, 9, 11, 1)
    fill_sym_box(grid, 0, 1, 15, 17, 12, 13, 1)  # Raked slightly aft
    fill_sym_box(grid, 0, 1, 15, 17, 12, 12, 9)  # Signal white funnel stripe
    fill_sym_box(grid, 0, 1, 15, 17, 14, 14, 5)  # Crisp dark navy/black funnel cap!
    # Rear secondary rangefinder / aft mast (Y: 14, Z: 9..12)
    fill_sym_box(grid, 0, 0, 14, 14, 9, 12, 6)
    fill_sym_box(grid, 0, 1, 14, 14, 11, 11, 6)

    # --- AFT FANTAIL CATAPULT & CRANE (Y: 4..7, Z: 6..8) ---
    fill_sym_box(grid, 0, 0, 4, 6, 6, 7, 6)      # Silver catapult rail
    fill_sym_box(grid, 2, 2, 5, 7, 6, 6, 5)      # Aft AA gun mount

    return grid


# ==========================================
# FORM B: ADMIRAL DREADNOUGHT BATTLESHIP ROBOT (34 x 24 x 44)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 44), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 16 (-X robot left)
    cx_r = grid.shape[0] // 2      # 17 (+X robot right)

    # --- HULL-BOW FEET & BOOTS (Z: 0..3) ---
    # Deep Crimson anti-fouling lower hull soles tapering to pointed ship-prow toes!
    fill_sym_box(grid, 3, 7, 7, 15, 0, 1, 3)    # Crimson lower hull sole
    fill_sym_box(grid, 4, 6, 9, 14, 1, 1, 0)    # Hollow unseen boot interior
    fill_sym_box(grid, 4, 6, 16, 17, 0, 1, 3)   # Tapered prow toe
    fill_sym_box(grid, 5, 5, 18, 18, 0, 1, 3)   # Sharp clipper bow tip
    fill_sym_box(grid, 3, 7, 7, 8, 0, 2, 2)     # Heavy gunmetal heel anchor
    # Naval steel grey upper hull boot vamp + signal white waterline stripe
    fill_sym_box(grid, 3, 7, 9, 15, 2, 2, 1)
    fill_sym_box(grid, 4, 6, 10, 14, 2, 2, 0)   # Hollow inside ankle base
    fill_sym_box(grid, 4, 6, 15, 17, 2, 3, 1)
    fill_sym_box(grid, 7, 7, 9, 15, 2, 2, 9)    # Signal white hull waterline stripe
    fill_sym_box(grid, 5, 5, 17, 18, 2, 2, 8)   # Golden bow crest on toe tip

    # --- SPLIT BATTLESHIP HULL LOWER LEGS / SHINS (艦体が脚!) (Z: 3..15) ---
    fill_sym_box(grid, 3, 7, 9, 14, 3, 15, 1)
    fill_sym_box(grid, 4, 6, 10, 13, 3, 14, 0)  # Hollow shin core cleanly
    # Outer vertical split-hull armor: Deep Crimson Lower Hull + Signal White Waterline + Steel Grey!
    fill_sym_box(grid, 7, 7, 9, 12, 4, 14, 3)   # Deep crimson anti-fouling hull panel
    fill_sym_box(grid, 7, 7, 13, 13, 4, 14, 9)  # Crisp signal white waterline stripe
    fill_sym_box(grid, 7, 7, 14, 14, 4, 14, 1)  # Steel grey upper hull edge
    # Front shin: Warm Teak Wooden Deck panel framed by steel grey gunwales!
    fill_sym_box(grid, 4, 6, 14, 14, 4, 12, 4)  # Warm teak deck armor
    fill_sym_box(grid, 3, 3, 10, 13, 4, 14, 2)  # Inner leg gunmetal armor
    # Heavy battleship prow knee guards (Z: 12..15)
    fill_sym_box(grid, 3, 6, 14, 15, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 15, 16, 13, 15, 2)
    fill_sym_box(grid, 4, 5, 16, 16, 14, 14, 8)  # Golden knee emblem
    fill_sym_box(grid, 4, 5, 15, 15, 12, 12, 9)  # Signal white stripe

    # --- MECHANICAL THIGHS (Z: 16..20) ---
    fill_sym_box(grid, 3, 5, 9, 13, 16, 20, 2)
    fill_sym_box(grid, 4, 4, 10, 12, 16, 19, 0)  # Hollow core
    fill_sym_box(grid, 3, 5, 13, 14, 17, 20, 1)  # Steel grey thigh armor
    fill_sym_box(grid, 4, 4, 14, 14, 17, 19, 6)  # Silver-grey hydraulic strut
    fill_sym_box(grid, 5, 5, 10, 12, 17, 19, 5)  # Dark navy recessed thigh vents

    # --- WAIST & HULL-DECK ARMOR SKIRTS (艦体が腰!) (Z: 19..23) ---
    fill_sym_box(grid, 0, 6, 8, 14, 20, 23, 2)
    fill_sym_box(grid, 0, 5, 9, 13, 21, 22, 0)   # Hollow pelvis core
    # Front Battleship-Deck Skirt Plates (Steel Grey + Warm Teak Deck + Crimson Trim)
    fill_sym_box(grid, 2, 5, 14, 15, 19, 22, 1)
    fill_sym_box(grid, 3, 4, 15, 15, 20, 21, 4)  # Warm teak deck inlay on front skirts!
    fill_sym_box(grid, 2, 5, 15, 15, 19, 19, 3)  # Deep crimson lower hull trim
    fill_sym_box(grid, 2, 5, 15, 15, 22, 22, 9)  # Signal white waist belt stripe
    # Side Hull Hip Armor Guards
    fill_sym_box(grid, 6, 7, 9, 13, 19, 22, 1)
    fill_sym_box(grid, 7, 7, 10, 12, 19, 20, 3)  # Crimson lower hull edge
    fill_sym_box(grid, 7, 7, 10, 12, 21, 21, 4)  # Teak deck strip
    # Heroic Center Admiral Codpiece
    fill_sym_box(grid, 0, 1, 14, 16, 19, 23, 1)
    fill_sym_box(grid, 0, 1, 16, 16, 19, 20, 3)  # Crimson prow bottom
    fill_sym_box(grid, 0, 1, 16, 16, 21, 22, 8)  # Golden imperial crest

    # --- BRIDGE SUPERSTRUCTURE TORSO & CHEST PLATE (艦橋が胸!) (Z: 24..34) ---
    fill_sym_box(grid, 0, 6, 8, 14, 24, 33, 1)
    # Armored gunmetal abdomen with warm teak deck waist ribs
    fill_sym_box(grid, 0, 4, 14, 15, 24, 26, 2)
    fill_sym_box(grid, 1, 3, 15, 15, 24, 25, 4)  # Teak deck abdomen strips
    fill_sym_box(grid, 0, 0, 15, 15, 24, 26, 5)  # Dark navy center spine

    # Prominent Tiered Battleship Bridge Chest Plate! (Y: 14..17, Z: 27..33)
    fill_sym_box(grid, 0, 5, 14, 16, 27, 33, 1)
    fill_sym_box(grid, 0, 4, 16, 17, 28, 32, 1)  # Jutting armored conning-tower bridge
    fill_sym_box(grid, 0, 4, 16, 17, 33, 33, 2)  # Dark gunmetal bridge roof deck
    # Hollow entire unified torso + bridge chest interior cleanly!
    fill_sym_box(grid, 0, 5, 9, 13, 24, 32, 0)
    fill_sym_box(grid, 0, 4, 14, 15, 28, 32, 0)
    fill_sym_box(grid, 0, 3, 15, 16, 29, 31, 0)
    fill_sym_box(grid, 0, 4, 17, 17, 27, 27, 9)  # Signal white naval stripe below bridge
    # ICONIC GLOWING CYAN BRIDGE WINDOWS ACROSS THE CHEST! (Z: 30..31, Y: 17)
    fill_sym_box(grid, 0, 4, 17, 17, 30, 31, 7)
    fill_sym_box(grid, 0, 0, 17, 17, 30, 31, 5)  # Center dark window mullion
    fill_sym_box(grid, 3, 3, 17, 17, 30, 31, 5)  # Outer dark window mullions
    # Twin Warm Golden Naval Searchlights flanking lower bridge chest!
    fill_sym_box(grid, 5, 5, 15, 16, 28, 29, 2)
    fill_sym_box(grid, 5, 5, 16, 17, 28, 29, 8)  # Glowing golden searchlights
    # Lower chest vents & silver optical rangefinder collar bar
    fill_sym_box(grid, 1, 2, 17, 17, 28, 29, 2)
    fill_sym_box(grid, 0, 4, 15, 16, 33, 34, 6)  # Silver rangefinder collar bar
    fill_sym_box(grid, 2, 5, 10, 14, 33, 34, 2)  # Armored collar flanks

    # --- SMOKESTACK FUNNEL BACKPACK (Y: 3..7, Z: 23..38) ---
    fill_sym_box(grid, 0, 4, 5, 7, 23, 32, 1)
    fill_sym_box(grid, 0, 3, 6, 8, 24, 31, 0)    # Hollow backpack + shared torso back wall!
    fill_sym_box(grid, 0, 4, 4, 5, 25, 31, 2)    # Armored rear bulkhead
    # Tall Iconic Battleship Smokestack Funnel rising proudly behind the collar!
    fill_sym_box(grid, 0, 2, 4, 7, 31, 37, 1)
    fill_sym_box(grid, 0, 1, 5, 6, 32, 36, 0)    # Hollow funnel interior
    fill_sym_box(grid, 0, 2, 4, 7, 35, 35, 9)    # Signal white naval funnel band
    fill_sym_box(grid, 0, 2, 4, 7, 37, 38, 5)    # Crisp dark navy/black funnel cap!
    # Twin Lower Rear Booster Thrusters
    fill_sym_box(grid, 2, 3, 3, 5, 23, 25, 5)
    fill_sym_box(grid, 2, 3, 3, 3, 23, 24, 7)    # Glowing cyan turbine exhaust

    # --- TWIN MAIN GUN TURRET SHOULDER CANNONS (主砲塔が肩の大砲!) (Z: 29..38, x_off: 7..13) ---
    # Heavy steel/gunmetal shoulder axle bridge
    fill_sym_box(grid, 6, 8, 10, 12, 30, 32, 2)
    fill_sym_box(grid, 7, 8, 10, 12, 30, 32, 5)
    # Massive Battleship Main Gun Turret Pauldrons on BOTH shoulders!
    fill_sym_box(grid, 8, 13, 8, 14, 30, 36, 1)
    fill_sym_box(grid, 9, 12, 9, 13, 31, 35, 0)  # Hollow turret interior
    # Re-anchor inner shoulder mount solidly through turret cavity
    fill_sym_box(grid, 8, 10, 10, 12, 30, 32, 2)
    # Sloped dark gunmetal turret roof & signal white naval turret markings
    fill_sym_box(grid, 8, 13, 9, 13, 36, 36, 2)
    fill_sym_box(grid, 9, 12, 9, 12, 37, 37, 1)
    fill_sym_box(grid, 10, 11, 9, 12, 37, 37, 9)  # Signal white turret top stripe
    # Light silver-grey turret rangefinder ears sticking out the sides
    fill_sym_box(grid, 14, 14, 10, 11, 33, 34, 6)
    # Crimson lower pauldron skirt stripe (ties into ship hull colors)
    fill_sym_box(grid, 8, 13, 8, 14, 30, 30, 3)

    # TWIN HEAVY MAIN GUN BARRELS MOUNTED ON BOTH SHOULDERS POINTING FORWARD! (Y: 14..22, Z: 33..34)
    for barrel_off in (9, 12):
        # Light silver-grey armored blast bags at turret face
        fill_sym_box(grid, barrel_off, barrel_off, 14, 15, 33, 34, 6)
        # Long, imposing dark navy/black main battleship gun barrels!
        fill_sym_box(grid, barrel_off, barrel_off, 15, 22, 33, 34, 5)
        # Warm golden-orange muzzle brake rings at cannon tips!
        fill_sym_box(grid, barrel_off, barrel_off, 22, 22, 33, 34, 8)
    # Secondary small AA twin turret / director pod on upper inner shoulder
    fill_sym_box(grid, 8, 9, 11, 13, 37, 38, 6)

    # --- ARMS, FOREARMS & NAVAL ANCHOR-BLADE / HULL SHIELD (Z: 15..29) ---
    # Upper arms descending solidly from turret shoulders
    fill_sym_box(grid, 9, 11, 10, 12, 23, 29, 2)
    fill_sym_box(grid, 10, 10, 11, 11, 24, 28, 0)  # Hollow bicep core
    fill_sym_box(grid, 10, 11, 10, 12, 25, 27, 5)  # Dark navy bicep piston
    # Armored Battleship Forearms
    fill_sym_box(grid, 9, 12, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 10, 11, 10, 13, 18, 21, 0)  # Hollow forearm interior
    fill_sym_box(grid, 12, 12, 10, 13, 18, 21, 4)  # Warm teak deck outer forearm inlay
    fill_sym_box(grid, 9, 12, 14, 14, 17, 17, 3)   # Deep crimson wrist cuff
    fill_sym_box(grid, 9, 12, 14, 14, 21, 21, 6)   # Silver upper cuff
    # Heavy mechanical fists
    fill_sym_box(grid, 9, 11, 10, 13, 15, 16, 5)
    fill_sym_box(grid, 9, 11, 13, 13, 15, 16, 6)

    # RIGHT HAND (+X, viewer's left): DREADNOUGHT PROW ANCHOR-HALBERD!
    # Anchored cleanly on outer right fist (X = cx_r + 11..12 = 28..29) so it clears the right leg!
    fill_box(grid, cx_r + 11, cx_r + 11, 12, 21, 15, 16, 5)  # Heavy dark gunmetal haft
    fill_box(grid, cx_r + 11, cx_r + 12, 16, 22, 15, 18, 1)  # Steel grey anchor-blade core
    fill_box(grid, cx_r + 11, cx_r + 12, 18, 23, 14, 15, 6)  # Gleaming silver lower blade edge
    fill_box(grid, cx_r + 11, cx_r + 12, 19, 23, 17, 19, 6)  # Hooked upper anchor fluke
    fill_box(grid, cx_r + 12, cx_r + 12, 17, 20, 16, 17, 3)  # Deep crimson hull accent
    fill_box(grid, cx_r + 11, cx_r + 12, 15, 16, 17, 18, 8)  # Golden crossguard emblem

    # LEFT FOREARM (-X, viewer's right): TAPERED BATTLESHIP HULL-DECK SHIELD!
    fill_box(grid, cx_l - 13, cx_l - 12, 10, 16, 17, 23, 1)  # Steel grey hull shield
    fill_box(grid, cx_l - 13, cx_l - 13, 11, 15, 17, 18, 3)  # Deep crimson lower hull
    fill_box(grid, cx_l - 13, cx_l - 13, 11, 15, 19, 19, 9)  # Signal white waterline stripe
    fill_box(grid, cx_l - 13, cx_l - 13, 11, 15, 20, 22, 4)  # Warm teak deck top face
    fill_box(grid, cx_l - 13, cx_l - 12, 16, 16, 18, 21, 6)  # Silver armored shield prow

    # --- RADAR-CROWNED ADMIRAL HEAD (艦橋が頭!) (Z: 34..43) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 12, 34, 35, 2)
    # Main Admiral Bridge-Tower Helmet
    fill_sym_box(grid, 0, 2, 9, 13, 36, 40, 1)
    fill_sym_box(grid, 0, 1, 10, 12, 37, 39, 0)  # Hollow unseen head interior
    # Signal White Naval Admiral Cap Crown & Dark Navy Visor Peak!
    fill_sym_box(grid, 0, 2, 9, 13, 40, 40, 9)
    fill_sym_box(grid, 0, 2, 14, 15, 39, 39, 5)  # Dark navy admiral cap brim
    # Glowing Cyan Bridge-Window Visor!
    fill_sym_box(grid, 0, 2, 14, 14, 38, 38, 7)
    # Light silver-grey faceplate & dark chin guard
    fill_sym_box(grid, 0, 1, 14, 14, 36, 37, 6)
    fill_sym_box(grid, 0, 0, 14, 14, 36, 36, 2)
    # Rangefinder side ear pods
    fill_sym_box(grid, 3, 3, 10, 12, 37, 39, 2)
    fill_sym_box(grid, 3, 3, 11, 11, 38, 38, 6)
    # Golden Naval Admiral V-Crest on forehead!
    fill_sym_box(grid, 0, 0, 15, 15, 40, 41, 8)
    fill_sym_box(grid, 1, 2, 14, 15, 40, 41, 8)
    fill_sym_box(grid, 2, 3, 13, 14, 41, 42, 8)
    # Towering Battleship Radar Mast crowning the back/top of the Admiral Helmet!
    fill_sym_box(grid, 0, 0, 10, 11, 41, 43, 6)  # Vertical silver radar mast
    fill_sym_box(grid, 0, 3, 10, 10, 42, 42, 6)  # Wide horizontal radar yardarm
    fill_sym_box(grid, 3, 3, 10, 10, 42, 42, 8)  # Golden radar tip beacons

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
    v_a = export_vox(model_a, "battleship_a.vox")
    v_b = export_vox(model_b, "battleship_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: DREADNOUGHT BATTLESHIP -> ADMIRAL ROBOT",
        "1. DREADNOUGHT BATTLESHIP",
        "2. ADMIRAL BATTLESHIP ROBOT",
        "preview_battleship.png",
        yaw_a=42, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"battleship: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
