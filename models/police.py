import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (244, 247, 252, 255),  # Crisp Police Panda White
    2: (186, 196, 212, 255),  # Silver Chrome / Rims / Trim
    3: (36, 40, 50, 255),     # Jet Panda Black / Tires / Bumpers
    4: (86, 96, 114, 255),    # Gunmetal Chassis / Joints / Blaster
    5: (28, 52, 94, 255),     # Dark Tinted Window Glass
    6: (95, 218, 255, 255),   # Cyan Glass Glint / Robot Visor
    7: (246, 188, 40, 255),   # Gold Police Emblem / Turn Signals
    8: (236, 32, 46, 255),    # Glowing Crimson Patrol Lightbar / Taillights
    9: (255, 242, 175, 255),  # Bright Headlights / Siren Flash Core
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
# FORM A: POLICE CRUISER (16 x 34 x 14)
# ==========================================
def build_a():
    grid = np.zeros((16, 34, 14), dtype=np.uint8)

    # Undercarriage & floor pan (Z: 1..2)
    fill_sym_box(grid, 0, 5, 2, 31, 1, 2, 4)

    # Rear & Front Jet-Black Bumpers (Z: 2..3)
    fill_sym_box(grid, 0, 6, 0, 1, 2, 3, 3)
    fill_sym_box(grid, 0, 5, 0, 0, 2, 2, 2)  # Rear chrome trim
    fill_sym_box(grid, 4, 4, 0, 0, 1, 1, 2)  # Twin exhausts
    fill_sym_box(grid, 0, 6, 32, 33, 2, 3, 3)
    fill_sym_box(grid, 0, 4, 33, 33, 2, 2, 2)  # Front lower grille trim

    # Classic Japanese Panda Lower Body (Jet Black, Z: 2..4)
    fill_sym_box(grid, 0, 6, 2, 31, 2, 4, 3)

    # Classic Japanese Panda Upper Body (Crisp White, Z: 5..6)
    fill_sym_box(grid, 0, 6, 2, 30, 5, 6, 1)
    fill_sym_box(grid, 0, 5, 31, 31, 5, 5, 1)  # Sloped front hood tip
    fill_sym_box(grid, 0, 5, 1, 1, 5, 5, 1)    # Rear trunk upper edge
    fill_sym_box(grid, 0, 4, 23, 23, 6, 6, 3)  # Black windshield wiper cowl

    # Door police marking & silver handles
    fill_sym_box(grid, 6, 6, 17, 19, 5, 5, 3)
    fill_sym_box(grid, 6, 6, 18, 18, 5, 5, 7)  # Gold door emblem glint
    fill_sym_box(grid, 6, 6, 13, 13, 6, 6, 2)
    fill_sym_box(grid, 6, 6, 18, 18, 6, 6, 2)

    # Front Grille, Iconic Gold Police Emblem & Bright Headlights (Y: 31..32)
    fill_sym_box(grid, 0, 5, 32, 32, 4, 4, 3)
    fill_sym_box(grid, 1, 3, 32, 32, 4, 4, 4)
    fill_sym_box(grid, 1, 2, 32, 32, 4, 4, 2)  # Silver grille bar
    fill_sym_box(grid, 0, 0, 32, 32, 4, 5, 7)  # Gold Police Emblem (center)
    fill_sym_box(grid, 0, 0, 31, 31, 5, 5, 7)
    fill_sym_box(grid, 4, 5, 32, 32, 4, 5, 9)  # Bright headlights
    fill_sym_box(grid, 6, 6, 31, 31, 4, 5, 7)  # Amber front corner markers

    # Rear Taillights & License Plate (Y: 1)
    fill_sym_box(grid, 0, 5, 1, 1, 4, 4, 3)
    fill_sym_box(grid, 0, 1, 1, 1, 4, 4, 1)    # White license plate
    fill_sym_box(grid, 3, 5, 1, 1, 4, 5, 8)    # Crimson red taillights
    fill_sym_box(grid, 3, 3, 1, 1, 4, 4, 7)    # Amber rear indicators

    # Wheel Wells & 4 Octagonal Tires with Silver Rims
    for y0 in (7, 24):
        fill_sym_box(grid, 5, 6, y0, y0 + 3, 1, 3, 0)       # Wheel arch cutout
        fill_sym_box(grid, 4, 4, y0, y0 + 3, 1, 4, 4)       # Inner wheel well backing
        fill_sym_box(grid, 0, 4, y0 + 1, y0 + 2, 1, 2, 4)   # Axle
        fill_sym_box(grid, 5, 6, y0 + 1, y0 + 2, 0, 3, 3)   # Tire vertical
        fill_sym_box(grid, 5, 6, y0, y0 + 3, 1, 2, 3)       # Tire horizontal
        fill_sym_box(grid, 6, 6, y0 + 1, y0 + 2, 1, 2, 2)   # Silver rim

    # Greenhouse / Cabin with Sloped Windshields & White Pillars (Z: 7..10)
    fill_sym_box(grid, 0, 5, 9, 22, 7, 7, 5)
    fill_sym_box(grid, 5, 5, 22, 22, 7, 7, 1)  # A-pillar
    fill_sym_box(grid, 5, 5, 15, 16, 7, 7, 1)  # B-pillar
    fill_sym_box(grid, 5, 5, 9, 10, 7, 7, 1)   # C-pillar

    fill_sym_box(grid, 0, 5, 10, 21, 8, 8, 5)
    fill_sym_box(grid, 5, 5, 21, 21, 8, 8, 1)
    fill_sym_box(grid, 5, 5, 15, 16, 8, 8, 1)
    fill_sym_box(grid, 5, 5, 10, 11, 8, 8, 1)

    fill_sym_box(grid, 0, 5, 11, 20, 9, 9, 5)
    fill_sym_box(grid, 5, 5, 20, 20, 9, 9, 1)
    fill_sym_box(grid, 5, 5, 15, 16, 9, 9, 1)
    fill_sym_box(grid, 5, 5, 11, 11, 9, 9, 1)

    # Cyan Glass Glints on Windshield, Side Windows & Rear Window
    fill_box(grid, 5, 6, 22, 22, 7, 7, 6)
    fill_box(grid, 6, 7, 21, 21, 8, 8, 6)
    fill_box(grid, 7, 8, 20, 20, 9, 9, 6)
    fill_box(grid, 10, 11, 21, 21, 8, 8, 6)
    fill_sym_box(grid, 5, 5, 19, 19, 8, 8, 6)
    fill_sym_box(grid, 5, 5, 18, 18, 9, 9, 6)
    fill_sym_box(grid, 5, 5, 13, 13, 8, 8, 6)
    fill_sym_box(grid, 5, 5, 12, 12, 9, 9, 6)
    fill_box(grid, 6, 7, 10, 10, 8, 8, 6)
    fill_box(grid, 7, 8, 11, 11, 9, 9, 6)

    # Crisp White Roof & Side Mirrors
    fill_sym_box(grid, 0, 5, 11, 20, 10, 10, 1)
    fill_sym_box(grid, 6, 7, 21, 22, 6, 6, 3)  # Black mirror stalk
    fill_sym_box(grid, 7, 7, 21, 22, 7, 7, 1)  # White mirror cap

    # Roof Shark-Fin Radio Antenna
    fill_sym_box(grid, 0, 0, 12, 13, 11, 11, 3)

    # Bold Glowing Crimson Boomerang Patrol Lightbar (パトランプ, Z: 11..12)
    fill_sym_box(grid, 0, 4, 15, 17, 11, 11, 2)  # Silver mounting bar
    fill_sym_box(grid, 0, 0, 15, 17, 11, 12, 1)  # White center siren box
    fill_sym_box(grid, 0, 0, 17, 17, 12, 12, 4)  # Siren speaker front
    fill_sym_box(grid, 1, 2, 16, 17, 11, 12, 8)  # Inner crimson pod
    fill_sym_box(grid, 3, 4, 15, 16, 11, 12, 8)  # Swept outer crimson pod
    fill_sym_box(grid, 2, 2, 17, 17, 12, 12, 9)  # Front flash highlight
    fill_sym_box(grid, 3, 3, 16, 16, 12, 12, 9)  # Top-outer flash highlight

    # Hollow unseen interior to keep voxel count in ideal 1500-2100 target range
    fill_sym_box(grid, 0, 4, 3, 29, 2, 5, 0)
    fill_sym_box(grid, 0, 3, 12, 19, 7, 9, 0)
    # Restore wheel well inner backing & axles cleanly
    for y0 in (7, 24):
        fill_sym_box(grid, 4, 4, y0, y0 + 3, 1, 4, 4)
        fill_sym_box(grid, 0, 4, y0 + 1, y0 + 2, 1, 2, 4)

    return grid


# ==========================================
# FORM B: POLICE ENFORCER ROBOT (32 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((32, 24, 42), dtype=np.uint8)

    # --- FEET (Z: 0..3) - Grounded Black Car-Bumper Toes & Stabilizers ---
    fill_sym_box(grid, 2, 5, 8, 16, 0, 1, 3)
    fill_sym_box(grid, 2, 5, 13, 17, 0, 1, 3)
    fill_sym_box(grid, 2, 4, 13, 16, 2, 2, 1)   # White upper foot plate
    fill_sym_box(grid, 3, 4, 16, 17, 1, 1, 2)   # Silver bumper accent
    fill_sym_box(grid, 2, 4, 7, 9, 0, 2, 4)     # Gunmetal heel spur
    fill_sym_box(grid, 2, 4, 9, 13, 2, 3, 4)    # Ankle joint

    # --- LOWER LEGS / SHINS (Z: 4..15) - Split Car Rear Quarters + Rear Tires ---
    fill_sym_box(grid, 2, 4, 9, 14, 4, 15, 4)   # Inner frame
    fill_sym_box(grid, 2, 5, 9, 14, 4, 9, 3)    # Black lower panda half
    fill_sym_box(grid, 2, 5, 9, 14, 10, 14, 1)  # White upper panda half
    fill_sym_box(grid, 3, 4, 14, 15, 5, 13, 1)  # Front white shin plate
    fill_sym_box(grid, 4, 5, 14, 15, 11, 12, 8) # Car red taillights on upper shins
    fill_sym_box(grid, 5, 5, 13, 13, 11, 11, 7) # Amber turn indicator detail
    # Heroic Patlabor Knee Guards
    fill_sym_box(grid, 2, 4, 14, 16, 13, 15, 1)
    fill_sym_box(grid, 3, 3, 15, 16, 15, 16, 3)
    fill_sym_box(grid, 3, 3, 16, 16, 14, 14, 2)
    # Rear Car Tires with Silver Rims mounted on outer ankles/calves
    fill_sym_box(grid, 6, 7, 10, 11, 4, 7, 3)
    fill_sym_box(grid, 6, 7, 9, 12, 5, 6, 3)
    fill_sym_box(grid, 7, 7, 10, 11, 5, 6, 2)   # Silver wheel rim

    # --- THIGHS (Z: 16..21) - Crisp White Armor over Gunmetal Joints ---
    fill_sym_box(grid, 2, 4, 10, 13, 16, 21, 4)
    fill_sym_box(grid, 2, 4, 10, 14, 17, 20, 1)
    fill_sym_box(grid, 4, 4, 11, 12, 17, 20, 2)
    fill_sym_box(grid, 2, 3, 10, 13, 21, 21, 3)

    # --- WAIST / PELVIS (Z: 21..24) - Police Utility Belt & Gold Buckle ---
    fill_sym_box(grid, 0, 4, 9, 14, 21, 23, 3)
    fill_sym_box(grid, 2, 4, 14, 15, 21, 22, 1) # Crisp white front tassets
    fill_sym_box(grid, 2, 4, 14, 15, 20, 20, 3) # Black lower tasset trim
    fill_sym_box(grid, 0, 1, 14, 15, 20, 23, 3) # Black center pelvis guard
    fill_sym_box(grid, 0, 1, 15, 15, 22, 23, 1) # White belt accent
    fill_sym_box(grid, 0, 0, 15, 15, 21, 22, 7) # Gold police belt buckle
    fill_sym_box(grid, 5, 5, 10, 13, 20, 22, 3) # Side hip armor
    fill_sym_box(grid, 5, 5, 10, 13, 22, 22, 1)
    fill_sym_box(grid, 0, 3, 10, 13, 23, 25, 4) # Gunmetal abs
    fill_sym_box(grid, 0, 2, 14, 14, 24, 24, 2) # Silver abdominal trim

    # --- TORSO / CHEST (Z: 25..34) - Panda Car Hood, Gold Badge & Headlights ---
    fill_sym_box(grid, 0, 4, 9, 14, 25, 34, 1)
    # Car Front Bumper & Grille forming lower chest (Z: 26..28)
    fill_sym_box(grid, 0, 4, 15, 17, 26, 28, 3)
    fill_sym_box(grid, 0, 3, 18, 18, 26, 27, 3)
    fill_sym_box(grid, 1, 2, 18, 18, 27, 27, 2) # Silver front grille slats
    fill_sym_box(grid, 3, 4, 17, 17, 28, 29, 9) # Bright car headlights
    fill_sym_box(grid, 5, 5, 15, 16, 28, 28, 7) # Amber fender markers
    # Crisp White Car Hood forming upper chest (Z: 29..32)
    fill_sym_box(grid, 0, 4, 15, 17, 29, 31, 1)
    fill_sym_box(grid, 0, 3, 15, 16, 32, 32, 1)
    # Bold Gold Police Emblem (旭日章) dead center on chest
    fill_sym_box(grid, 0, 0, 18, 18, 28, 31, 7)
    fill_sym_box(grid, 0, 1, 18, 18, 29, 30, 7)
    # Folded Dark Tinted Windshield Collar (Z: 33)
    fill_sym_box(grid, 0, 3, 14, 15, 33, 33, 5)
    fill_sym_box(grid, 1, 2, 15, 15, 33, 33, 6) # Cyan windshield glint
    fill_sym_box(grid, 3, 4, 12, 14, 33, 34, 1) # Armored collar flanks
    fill_sym_box(grid, 4, 4, 13, 14, 34, 34, 3)

    # --- BACKPACK & FANNED CAR-DOOR WINGS (Y: 3..8, Z: 23..37) ---
    fill_sym_box(grid, 0, 3, 6, 8, 24, 33, 1)   # Folded white car roof backpack
    fill_sym_box(grid, 0, 2, 5, 5, 26, 31, 5)   # Folded tinted rear window
    fill_sym_box(grid, 1, 1, 5, 5, 29, 30, 6)   # Cyan glass glint
    fill_sym_box(grid, 1, 2, 6, 7, 23, 24, 4)   # Twin backpack thrusters
    fill_sym_box(grid, 1, 1, 6, 6, 23, 23, 6)

    # Fanned Black-and-White Car Doors (Classic Prowl Car-Bot Door Wings)
    for i in range(5):
        x0 = 4 + i * 2
        x1 = 5 + i * 2
        yb = 7 - i
        zb = 26 + i
        fill_sym_box(grid, x0, x1, yb, yb + 1, zb, zb + 1, 3)      # Black lower door
        fill_sym_box(grid, x0, x1, yb, yb + 1, zb + 2, zb + 3, 1)  # White upper door
        fill_sym_box(grid, x0, x1, yb, yb + 1, zb + 4, zb + 5, 5)  # Tinted side window
        fill_sym_box(grid, x0, x1, yb, yb + 1, zb + 6, zb + 6, 1)  # White window frame
        if i in (1, 2):
            fill_sym_box(grid, x0, x0, yb, yb + 1, zb + 5, zb + 5, 6)  # Cyan glint
    # Wing gold police badge hint
    fill_sym_box(grid, 6, 7, 6, 7, 29, 29, 7)

    # --- SHOULDERS WITH PROMINENT RED PATROL LIGHTBARS (Z: 29..37) ---
    fill_sym_box(grid, 4, 7, 10, 13, 30, 32, 4) # Shoulder joint
    fill_sym_box(grid, 6, 10, 9, 14, 29, 34, 1) # White shoulder pauldron
    fill_sym_box(grid, 6, 10, 9, 14, 29, 30, 3) # Black lower pauldron trim
    fill_sym_box(grid, 10, 10, 10, 13, 31, 33, 3)
    fill_sym_box(grid, 7, 9, 14, 14, 31, 31, 7) # Gold police shoulder stripe
    # Split Patrol Lightbars mounted prominently atop BOTH shoulders!
    fill_sym_box(grid, 6, 9, 10, 13, 35, 35, 2) # Silver lightbar mount
    fill_sym_box(grid, 6, 9, 10, 13, 36, 37, 8) # Glowing crimson red shoulder lightbar
    fill_sym_box(grid, 7, 8, 11, 12, 37, 37, 9) # Top siren flash core
    fill_sym_box(grid, 7, 8, 13, 13, 36, 36, 9) # Front siren flash core

    # --- ARMS, FOREARMS & RIGHT-HAND POLICE ENFORCER BLASTER (Z: 14..28) ---
    # Upper arms
    fill_sym_box(grid, 7, 8, 10, 13, 24, 28, 4)
    fill_sym_box(grid, 7, 8, 11, 13, 25, 27, 1)
    # Sturdy Black & White Forearms + Front Car Tires on outer gauntlets
    fill_sym_box(grid, 6, 9, 10, 14, 17, 23, 1)
    fill_sym_box(grid, 8, 9, 10, 14, 17, 22, 3)
    fill_sym_box(grid, 6, 9, 10, 14, 17, 18, 3)
    fill_sym_box(grid, 6, 9, 11, 14, 17, 17, 2) # Silver wrist cuff
    # Front Tires folded on outer forearms
    fill_sym_box(grid, 10, 10, 11, 12, 19, 22, 3)
    fill_sym_box(grid, 10, 10, 10, 13, 20, 21, 3)
    fill_sym_box(grid, 10, 10, 11, 12, 20, 21, 2) # Silver wheel rim
    # Articulated Fists
    fill_sym_box(grid, 7, 8, 11, 13, 15, 16, 4)
    # Right Hand (+X, x=23..24) Police Enforcer Plasma Blaster / Baton
    fill_box(grid, 23, 24, 12, 13, 14, 16, 3)   # Black pistol grip
    fill_box(grid, 23, 24, 12, 20, 16, 18, 4)   # Gunmetal blaster receiver
    fill_box(grid, 23, 24, 14, 20, 18, 18, 1)   # Crisp white police shroud
    fill_box(grid, 23, 24, 21, 23, 17, 18, 2)   # Silver barrel tip
    fill_box(grid, 23, 24, 15, 21, 17, 17, 6)   # Glowing cyan stun-coil rail
    fill_box(grid, 23, 24, 13, 15, 19, 19, 8)   # Red police laser sight

    # --- HEAD WITH RED PATROL LIGHTBAR CROWN (Z: 34..41) ---
    fill_sym_box(grid, 0, 1, 11, 12, 34, 35, 4) # Neck
    fill_sym_box(grid, 0, 2, 10, 14, 35, 39, 1) # Crisp white police helmet
    fill_sym_box(grid, 0, 1, 14, 14, 35, 36, 2) # Silver faceplate
    fill_sym_box(grid, 0, 1, 14, 15, 37, 37, 6) # Glowing cyan police visor
    fill_sym_box(grid, 2, 2, 13, 14, 35, 37, 3) # Black cheek guards
    fill_sym_box(grid, 0, 0, 15, 15, 38, 39, 7) # Gold police forehead badge
    fill_sym_box(grid, 3, 3, 11, 12, 36, 38, 3) # Black ear comm pods
    fill_sym_box(grid, 3, 3, 11, 11, 39, 40, 2) # Silver Patlabor radio antennae
    # Crimson Red Patrol Lightbar crowning the helmet!
    fill_sym_box(grid, 0, 2, 11, 13, 40, 40, 8)
    fill_sym_box(grid, 0, 1, 11, 13, 41, 41, 8)
    fill_sym_box(grid, 0, 0, 12, 13, 41, 41, 9) # Bright beacon flash core

    # Hollow unseen interiors (torso, lower legs, shoulders, backpack) to hit ideal 2800-3400 range
    fill_sym_box(grid, 0, 3, 10, 13, 26, 32, 0)
    fill_sym_box(grid, 3, 4, 10, 13, 5, 13, 0)
    fill_sym_box(grid, 7, 9, 10, 13, 30, 33, 0)
    fill_sym_box(grid, 0, 2, 7, 8, 25, 32, 0)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=40, pitch_a=24, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "police_a.vox")
    v_b = export_vox(model_b, "police_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: POLICE CRUISER -> POLICE ENFORCER ROBOT",
        "1. POLICE CRUISER",
        "2. POLICE ENFORCER ROBOT",
        "preview_police.png",
        yaw_a=40, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"police: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
