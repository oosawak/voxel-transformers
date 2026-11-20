import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (238, 114, 20, 255),   # Industrial Safety Orange (Counterweight & Armor)
    2: (252, 206, 36, 255),   # Caution Yellow (Hazard Stripes, Beacon, Hard-Hat)
    3: (28, 32, 40, 255),     # Tire Rubber & ROPS Charcoal Black
    4: (68, 78, 92, 255),     # Dark Industrial Gunmetal (Chassis & Outer Mast)
    5: (144, 156, 172, 255),  # Heavy Forged Steel (Twin L-Forks & Inner Mast)
    6: (216, 226, 238, 255),  # Bright Hydraulic Chrome (Pistons, Rims, Faceplate)
    7: (62, 218, 255, 255),   # Electric Cyan (Headlight Glint, Robot Visor & Core)
    8: (226, 44, 48, 255),    # Signal Red (Tail Lights, Valves, Warning Accents)
    9: (176, 74, 18, 255),    # Deep Burnt Orange (Counterweight Shade & Seat Pad)
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
# FORM A: FORKLIFT (16 x 36 x 26)
# ==========================================
def build_a():
    grid = np.zeros((16, 36, 26), dtype=np.uint8)
    cx_l = 7
    cx_r = 8

    # --- UNDERCARRIAGE & AXLES (Z: 1..3) ---
    fill_sym_box(grid, 0, 4, 3, 18, 2, 3, 4)
    fill_sym_box(grid, 0, 4, 4, 5, 1, 2, 4)     # Rear axle
    fill_sym_box(grid, 0, 5, 15, 16, 2, 3, 4)   # Front drive axle

    # --- SMALL CHUNKY REAR STEERING WHEELS (Y: 3..6, Z: 0..3) ---
    fill_sym_box(grid, 5, 6, 4, 5, 0, 3, 3)
    fill_sym_box(grid, 5, 6, 3, 6, 1, 2, 3)
    fill_sym_box(grid, 6, 6, 4, 5, 1, 2, 6)     # Chrome wheel hub

    # --- LARGER CHUNKY FRONT DRIVE WHEELS (Y: 13..18, Z: 0..5) ---
    fill_sym_box(grid, 5, 7, 14, 17, 0, 5, 3)
    fill_sym_box(grid, 5, 7, 13, 18, 1, 4, 3)
    fill_sym_box(grid, 7, 7, 14, 17, 2, 3, 5)   # Forged steel rim cross
    fill_sym_box(grid, 7, 7, 15, 16, 1, 4, 5)
    fill_sym_box(grid, 7, 7, 15, 16, 2, 3, 6)   # Bright chrome center hub

    # --- HEAVY COUNTERWEIGHT BODY (Y: 1..8, Z: 3..9) ---
    fill_sym_box(grid, 0, 4, 2, 7, 3, 4, 1)
    fill_sym_box(grid, 0, 5, 2, 7, 5, 8, 1)
    fill_sym_box(grid, 0, 4, 1, 1, 4, 7, 1)     # Rounded rear counterweight bulge
    fill_sym_box(grid, 0, 4, 2, 7, 9, 9, 1)     # Counterweight top deck
    fill_sym_box(grid, 0, 3, 3, 6, 4, 7, 0)     # Hollow unseen interior

    # Counterweight vents, tow pin, tail lights & exhaust
    fill_sym_box(grid, 0, 2, 1, 1, 5, 6, 4)     # Rear cooling vent grille
    fill_sym_box(grid, 0, 0, 0, 1, 4, 4, 5)     # Rear tow pin
    fill_sym_box(grid, 3, 4, 1, 1, 7, 7, 8)     # Signal red tail lights
    fill_sym_box(grid, 0, 3, 2, 4, 9, 9, 9)     # Recessed top engine louvers
    fill_box(grid, cx_l - 4, cx_l - 4, 2, 2, 9, 11, 4)   # Exhaust pipe
    fill_box(grid, cx_l - 4, cx_l - 4, 2, 2, 12, 12, 5)  # Steel exhaust tip

    # Bold black-and-yellow hazard stripes on counterweight rear & sides
    for ox in range(1, 5):
        fill_sym_box(grid, ox, ox, 1, 1, 4, 4, 2 if ox % 2 == 1 else 3)
    for hy in range(2, 8):
        fill_sym_box(grid, 5, 5, hy, hy, 5, 5, 2 if hy % 2 == 1 else 3)
        fill_sym_box(grid, 5, 5, hy, hy, 6, 6, 3 if hy % 2 == 1 else 2)

    # --- MID CHASSIS, FLOORBOARD, SIDE SILLS & FRONT FENDERS (Y: 8..18) ---
    fill_sym_box(grid, 4, 5, 8, 12, 2, 3, 4)    # Step sill
    fill_sym_box(grid, 4, 5, 8, 12, 4, 4, 1)    # Orange side skirt
    fill_sym_box(grid, 0, 3, 8, 12, 4, 5, 9)    # Engine cover hump under seat
    fill_sym_box(grid, 0, 3, 13, 14, 3, 3, 3)   # Rubber floor mat

    # Front fender arches & front cowl / dashboard housing
    fill_sym_box(grid, 4, 4, 12, 18, 3, 6, 1)
    fill_sym_box(grid, 5, 6, 13, 18, 6, 6, 1)   # Fender flare above front tires
    fill_sym_box(grid, 5, 5, 12, 12, 4, 5, 1)   # Rear fender apron
    fill_sym_box(grid, 0, 4, 15, 18, 3, 7, 1)   # Front cowl & dash block
    fill_sym_box(grid, 0, 2, 16, 17, 4, 6, 0)   # Hollow unseen cowl interior
    fill_sym_box(grid, 0, 4, 18, 18, 2, 4, 4)   # Heavy dark-steel front bumper
    fill_sym_box(grid, 0, 4, 17, 18, 7, 7, 2)   # Caution yellow hood lip
    for hy in range(8, 13):
        fill_sym_box(grid, 5, 5, hy, hy, 4, 4, 2 if hy % 2 == 0 else 3)

    # --- OPEN OPERATOR CAB: SEAT, STEERING WHEEL & LEVERS ---
    fill_sym_box(grid, 0, 2, 8, 11, 6, 6, 3)    # Seat cushion
    fill_sym_box(grid, 0, 2, 8, 8, 7, 10, 3)    # Seat backrest frame
    fill_sym_box(grid, 0, 1, 9, 9, 7, 9, 9)     # Cushioned burnt-orange seat pad
    # Steering column & wheel
    fill_sym_box(grid, 0, 0, 15, 15, 8, 9, 4)
    fill_sym_box(grid, 0, 0, 14, 14, 9, 10, 4)
    fill_sym_box(grid, 0, 1, 13, 14, 10, 10, 3)
    # Right-side hydraulic control levers (red & yellow knobs)
    fill_box(grid, cx_r + 2, cx_r + 2, 15, 15, 8, 9, 5)
    fill_box(grid, cx_r + 2, cx_r + 2, 15, 15, 10, 10, 8)
    fill_box(grid, cx_r + 3, cx_r + 3, 15, 15, 8, 9, 5)
    fill_box(grid, cx_r + 3, cx_r + 3, 15, 15, 10, 10, 2)

    # --- OPEN DARK-STEEL ROPS OVERHEAD ROLL-CAGE CAB (Z: 7..17) ---
    # Rear pillars rising from counterweight
    fill_sym_box(grid, 5, 5, 5, 6, 9, 17, 3)
    # Front angled pillars rising from front fenders (6-connected stepping)
    fill_sym_box(grid, 5, 5, 16, 16, 7, 11, 3)
    fill_sym_box(grid, 5, 5, 15, 16, 11, 12, 3)
    fill_sym_box(grid, 5, 5, 14, 15, 13, 14, 3)
    fill_sym_box(grid, 5, 5, 13, 14, 15, 17, 3)
    # Front work headlights on ROPS pillars
    fill_sym_box(grid, 5, 5, 16, 16, 12, 12, 4)
    fill_sym_box(grid, 5, 5, 17, 17, 12, 12, 7)  # Glowing cyan/white work light
    # Overhead guard roof perimeter & open protective grate bars
    fill_sym_box(grid, 5, 5, 5, 14, 17, 17, 3)
    fill_sym_box(grid, 0, 5, 5, 6, 17, 17, 3)
    fill_sym_box(grid, 0, 5, 13, 14, 17, 17, 3)
    fill_sym_box(grid, 1, 1, 6, 13, 17, 17, 4)
    fill_sym_box(grid, 3, 3, 6, 13, 17, 17, 4)

    # --- AMBER ROOF BEACON LIGHT (Z: 18..20) ---
    fill_sym_box(grid, 0, 0, 5, 6, 18, 18, 4)    # Dark beacon collar
    fill_sym_box(grid, 0, 0, 5, 6, 19, 20, 2)    # Bright amber-yellow strobe dome
    fill_sym_box(grid, 0, 0, 5, 5, 19, 19, 1)    # Warm orange core glow

    # --- TALL VERTICAL TWIN-RAIL STEEL LIFT MAST (Y: 19..21, Z: 2..25) ---
    # Mast-to-chassis lower pivot & tilt hydraulic cylinders
    fill_sym_box(grid, 0, 4, 18, 19, 2, 4, 4)
    fill_sym_box(grid, 3, 3, 17, 19, 5, 5, 6)    # Chrome tilt piston rods

    # Outer twin dark-steel I-beam rails
    fill_sym_box(grid, 4, 5, 19, 20, 2, 24, 4)
    fill_sym_box(grid, 5, 5, 21, 21, 2, 24, 4)
    fill_sym_box(grid, 4, 5, 19, 21, 24, 24, 2)  # Caution yellow rail caps
    # Inner telescoping forged-steel rails
    fill_sym_box(grid, 3, 3, 20, 21, 3, 25, 5)
    # Mast horizontal crossbars
    fill_sym_box(grid, 0, 5, 19, 20, 2, 3, 4)
    fill_sym_box(grid, 0, 5, 19, 20, 14, 15, 4)
    fill_sym_box(grid, 0, 4, 19, 20, 23, 24, 4)
    # Center vertical hydraulic lift cylinder & lift chains
    fill_sym_box(grid, 0, 0, 19, 20, 3, 15, 4)   # Hydraulic barrel
    fill_sym_box(grid, 0, 0, 19, 19, 4, 4, 8)    # Red hydraulic valve
    fill_sym_box(grid, 0, 0, 20, 20, 16, 23, 6)  # Gleaming chrome piston rod
    fill_sym_box(grid, 0, 1, 20, 21, 22, 23, 3)  # Top chain pulley sheave
    fill_sym_box(grid, 1, 1, 21, 21, 8, 22, 3)   # Twin lift chains

    # --- FORK CARRIAGE & LOAD BACKREST (Y: 22, Z: 3..11) ---
    fill_sym_box(grid, 3, 4, 21, 22, 3, 8, 4)    # Carriage guide rollers
    fill_sym_box(grid, 0, 5, 22, 22, 3, 4, 4)    # Lower carriage rail
    fill_sym_box(grid, 0, 5, 22, 22, 7, 8, 4)    # Upper carriage rail
    # Load backrest guard grate
    fill_sym_box(grid, 0, 5, 22, 22, 11, 11, 3)
    fill_sym_box(grid, 5, 5, 22, 22, 8, 11, 3)
    fill_sym_box(grid, 2, 2, 22, 22, 8, 11, 3)
    fill_sym_box(grid, 0, 0, 22, 22, 8, 11, 3)

    # --- TWIN LONG HEAVY GREY STEEL L-SHAPED FORKS (Y: 23..35, Z: 1..8) ---
    # Vertical shanks hooked to carriage
    fill_sym_box(grid, 2, 3, 23, 23, 1, 8, 5)
    fill_sym_box(grid, 2, 3, 23, 23, 8, 8, 4)    # Top carriage hooks
    # Long low horizontal blades jutting forward at Z=1..2
    fill_sym_box(grid, 2, 3, 23, 30, 1, 2, 5)
    fill_sym_box(grid, 3, 3, 24, 29, 2, 2, 6)    # Metallic top-edge highlight
    fill_sym_box(grid, 2, 3, 31, 34, 1, 1, 5)    # Tapered blade front
    fill_sym_box(grid, 2, 3, 35, 35, 1, 1, 2)    # Safety caution-yellow fork tips

    return grid


# ==========================================
# FORM B: FORKLIFT LIFTER ROBOT (32 x 30 x 44)
# ==========================================
def build_b():
    grid = np.zeros((32, 30, 44), dtype=np.uint8)
    cx_l = 15
    cx_r = 16

    # --- GROUNDED HEAVY FEET (Z: 0..3) ---
    fill_sym_box(grid, 2, 5, 7, 16, 0, 1, 3)     # Heavy rubber tread soles
    fill_sym_box(grid, 2, 5, 14, 17, 1, 2, 5)    # Steel-toe boots
    fill_sym_box(grid, 3, 4, 17, 17, 1, 1, 2)    # Caution-yellow toe bumper
    fill_sym_box(grid, 2, 5, 10, 15, 2, 3, 1)    # Orange armored instep
    fill_sym_box(grid, 3, 5, 9, 13, 3, 3, 4)     # Dark ankle joint cuff
    fill_sym_box(grid, 3, 4, 9, 14, 1, 1, 0)     # Hollow unseen foot interior
    # Rear forklift wheels tucked into outer heels (Z: 0..3)
    fill_sym_box(grid, 5, 6, 8, 9, 0, 3, 3)
    fill_sym_box(grid, 5, 6, 7, 10, 1, 2, 3)
    fill_sym_box(grid, 6, 6, 8, 9, 1, 2, 6)

    # --- STOCKY LOWER LEGS + LARGE FRONT WHEELS ON OUTER CALVES (Z: 4..13) ---
    fill_sym_box(grid, 3, 5, 9, 13, 4, 13, 4)    # Inner steel leg skeleton
    fill_sym_box(grid, 3, 5, 10, 14, 4, 12, 1)   # Safety orange shin armor
    fill_sym_box(grid, 3, 3, 10, 13, 5, 11, 9)   # Burnt-orange inner calf recess
    fill_sym_box(grid, 3, 5, 14, 14, 5, 10, 4)   # Front shin guard
    for ox in range(3, 6):
        fill_sym_box(grid, ox, ox, 14, 14, 6, 6, 2 if ox % 2 == 1 else 3)
        fill_sym_box(grid, ox, ox, 14, 14, 8, 8, 3 if ox % 2 == 1 else 2)
    # Heavy mechanical knee guards
    fill_sym_box(grid, 3, 5, 13, 15, 11, 14, 4)
    fill_sym_box(grid, 4, 4, 15, 15, 12, 13, 2)
    fill_sym_box(grid, 5, 5, 12, 13, 12, 13, 6)  # Chrome knee pivot bolt
    fill_sym_box(grid, 4, 4, 10, 13, 5, 11, 0)   # Hollow unseen shin core
    # Large chunky front forklift drive wheels on outer calves (Z: 5..10)
    fill_sym_box(grid, 5, 7, 9, 12, 5, 10, 3)
    fill_sym_box(grid, 5, 7, 8, 13, 6, 9, 3)
    fill_sym_box(grid, 6, 6, 10, 11, 7, 8, 0)    # Hollow unseen wheel hub core
    fill_sym_box(grid, 7, 7, 9, 12, 7, 8, 5)
    fill_sym_box(grid, 7, 7, 10, 11, 6, 9, 5)
    fill_sym_box(grid, 7, 7, 10, 11, 7, 8, 6)
    fill_sym_box(grid, 5, 6, 9, 12, 11, 11, 1)   # Orange fender cap over wheel

    # --- MUSCULAR HYDRAULIC THIGHS (Z: 14..18) ---
    fill_sym_box(grid, 3, 4, 9, 13, 14, 18, 4)
    fill_sym_box(grid, 3, 4, 13, 14, 15, 18, 1)
    fill_sym_box(grid, 5, 5, 10, 11, 15, 18, 6)  # Side chrome hydraulic pistons
    fill_sym_box(grid, 5, 5, 10, 11, 14, 14, 4)
    fill_sym_box(grid, 5, 5, 10, 11, 18, 18, 4)

    # --- WAIST / PELVIS: COUNTERWEIGHT BUMPER SKIRT (Z: 19..22) ---
    fill_sym_box(grid, 0, 4, 8, 14, 19, 22, 4)
    fill_sym_box(grid, 0, 3, 9, 13, 20, 21, 0)   # Hollow unseen pelvis core
    fill_sym_box(grid, 5, 5, 9, 13, 19, 22, 1)   # Orange hip side-skirts
    for hy in range(9, 14):
        fill_sym_box(grid, 5, 5, hy, hy, 19, 19, 2 if hy % 2 == 1 else 3)
    fill_sym_box(grid, 0, 4, 14, 15, 20, 22, 1)  # Front bumper skirt
    for ox in range(0, 5):
        fill_sym_box(grid, ox, ox, 15, 15, 20, 20, 2 if ox % 2 == 0 else 3)
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 4)  # Central tow-hitch buckle
    fill_sym_box(grid, 0, 0, 16, 16, 20, 20, 5)  # Steel tow ring
    fill_sym_box(grid, 0, 0, 16, 16, 21, 21, 8)  # Red warning indicator

    # --- TORSO / CHEST: STOCKY ORANGE COUNTERWEIGHT BODY (Z: 23..31) ---
    fill_sym_box(grid, 0, 5, 8, 15, 23, 31, 1)
    fill_sym_box(grid, 0, 4, 9, 14, 24, 30, 0)   # Hollow hidden torso interior
    fill_sym_box(grid, 0, 3, 9, 14, 23, 24, 4)   # Armored lower ab frame
    fill_sym_box(grid, 0, 2, 10, 13, 23, 24, 0)  # Hollow ab interior
    fill_sym_box(grid, 4, 4, 10, 13, 23, 24, 9)  # Burnt-orange rib vents
    # Sculpted protruding counterweight chest
    fill_sym_box(grid, 0, 4, 15, 17, 25, 30, 1)
    fill_sym_box(grid, 0, 3, 15, 16, 26, 29, 0)  # Hollow chest protrusion core
    fill_sym_box(grid, 0, 4, 15, 16, 30, 31, 2)  # Caution-yellow upper collar trim
    fill_sym_box(grid, 0, 3, 9, 14, 31, 31, 4)   # Heavy steel neck deck
    # Recessed industrial power-core & mini ROPS chest bumper bars
    fill_sym_box(grid, 0, 2, 17, 17, 26, 29, 4)
    fill_sym_box(grid, 0, 1, 17, 17, 27, 28, 7)  # Glowing electric cyan core
    fill_sym_box(grid, 2, 2, 18, 18, 26, 29, 3)  # Protective ROPS chest bars
    fill_sym_box(grid, 0, 2, 18, 18, 26, 26, 3)
    fill_sym_box(grid, 0, 2, 18, 18, 29, 29, 3)
    # Front forklift headlights & signal markers on chest
    fill_sym_box(grid, 4, 4, 16, 17, 29, 29, 6)
    fill_sym_box(grid, 4, 4, 17, 17, 29, 29, 7)
    fill_sym_box(grid, 4, 4, 16, 16, 25, 25, 8)
    fill_sym_box(grid, 5, 5, 11, 14, 26, 28, 9)  # Side counterweight vents

    # --- HEAVY INDUSTRIAL BACKPACK: TALL TWIN-RAIL LIFT MAST + ROPS + BEACON ---
    # Backpack counterweight mounting block (Y: 6..8, Z: 22..30)
    fill_sym_box(grid, 0, 4, 6, 8, 22, 30, 4)
    fill_sym_box(grid, 0, 3, 7, 8, 23, 29, 0)    # Hollow backpack core
    fill_sym_box(grid, 0, 3, 6, 6, 23, 29, 1)
    fill_sym_box(grid, 0, 2, 6, 6, 25, 27, 9)    # Rear vent louver
    fill_sym_box(grid, 3, 3, 6, 6, 24, 25, 8)    # Rear signal red tail lights

    # Tall twin-rail steel lift mast rising behind back & over shoulders (Z: 18..41)
    fill_sym_box(grid, 4, 5, 3, 5, 18, 40, 4)    # Outer heavy gunmetal rails
    fill_sym_box(grid, 4, 4, 4, 4, 20, 38, 0)    # Hollow rail channel interior
    fill_sym_box(grid, 4, 5, 3, 5, 40, 40, 2)    # Caution-yellow top rail caps
    for hz in range(34, 39):
        fill_sym_box(grid, 5, 5, 4, 5, hz, hz, 2 if hz % 2 == 0 else 3)
    fill_sym_box(grid, 3, 3, 4, 5, 19, 41, 5)    # Inner telescoping forged-steel rails
    # Mast crossbars
    fill_sym_box(grid, 0, 5, 4, 5, 19, 20, 4)
    fill_sym_box(grid, 0, 5, 4, 5, 29, 30, 4)
    fill_sym_box(grid, 0, 5, 4, 5, 39, 40, 4)
    # Center vertical hydraulic lift cylinder & lift chains
    fill_sym_box(grid, 0, 0, 4, 5, 20, 31, 4)    # Cylinder barrel
    fill_sym_box(grid, 0, 0, 3, 3, 21, 22, 8)    # Red hydraulic manifold
    fill_sym_box(grid, 0, 0, 4, 4, 32, 39, 6)    # Bright chrome piston rod
    fill_sym_box(grid, 1, 1, 3, 3, 21, 39, 3)    # Twin lift chains
    fill_sym_box(grid, 0, 1, 3, 4, 38, 39, 3)    # Top chain pulley block

    # Folded ROPS overhead roll-cage frame arching above backpack (Z: 31..38)
    fill_sym_box(grid, 4, 4, 6, 7, 31, 38, 3)
    fill_sym_box(grid, 4, 4, 5, 6, 36, 38, 3)    # Solid tie into mast rails
    fill_sym_box(grid, 0, 4, 6, 6, 38, 38, 3)    # Rear overhead bar
    fill_sym_box(grid, 0, 4, 8, 8, 38, 38, 3)    # Front overhead bar
    fill_sym_box(grid, 0, 0, 6, 8, 38, 38, 4)    # Roof grate ribs
    fill_sym_box(grid, 2, 2, 6, 8, 38, 38, 4)
    fill_sym_box(grid, 4, 4, 6, 8, 38, 38, 3)

    # Amber Roof Beacon perched proudly atop the mast crossbar (Z: 41..43)
    fill_sym_box(grid, 0, 0, 4, 5, 41, 41, 4)    # Beacon base collar
    fill_sym_box(grid, 0, 0, 4, 5, 42, 43, 2)    # Glowing amber-yellow dome
    fill_sym_box(grid, 0, 0, 4, 4, 42, 42, 1)    # Warm orange beacon core

    # --- EXPRESSIVE INDUSTRIAL HARD-HAT HEAD (Z: 31..37) ---
    fill_sym_box(grid, 0, 1, 10, 12, 31, 32, 4)  # Neck
    fill_sym_box(grid, 0, 2, 9, 14, 32, 35, 4)   # Dark-steel head base
    fill_sym_box(grid, 0, 1, 10, 13, 33, 34, 0)  # Hollow head interior
    # Yellow construction hard-hat helmet with brim & safety orange ridge
    fill_sym_box(grid, 0, 2, 9, 14, 35, 36, 2)
    fill_sym_box(grid, 0, 1, 10, 13, 35, 35, 0)
    fill_sym_box(grid, 0, 2, 15, 15, 35, 35, 2)  # Hard-hat visor brim
    fill_sym_box(grid, 1, 1, 10, 13, 37, 37, 2)
    fill_sym_box(grid, 0, 0, 10, 14, 37, 37, 1)  # Safety-orange crest ridge
    # Ear comm pods & antenna
    fill_sym_box(grid, 3, 3, 10, 12, 33, 35, 3)
    fill_sym_box(grid, 3, 3, 11, 11, 34, 34, 6)
    fill_box(grid, cx_l - 3, cx_l - 3, 10, 10, 36, 38, 5)  # Left comms antenna
    # Glowing cyan visor & chrome mouth guard
    fill_sym_box(grid, 0, 1, 14, 15, 34, 34, 7)
    fill_sym_box(grid, 0, 1, 14, 15, 32, 33, 6)
    fill_sym_box(grid, 0, 0, 15, 15, 32, 32, 4)

    # --- SHOULDERS & UPPER ARMS (Z: 21..33) ---
    fill_sym_box(grid, 5, 6, 10, 13, 27, 30, 4)  # Heavy shoulder axles
    fill_sym_box(grid, 6, 10, 9, 14, 27, 32, 1)  # Blocky orange shoulder pauldrons
    fill_sym_box(grid, 7, 9, 10, 13, 28, 31, 0)  # Hollow shoulder interior
    fill_sym_box(grid, 7, 10, 10, 13, 32, 33, 2) # Caution-yellow shoulder top
    fill_sym_box(grid, 10, 10, 10, 13, 33, 33, 3) # Shoulder ROPS roll-bar
    fill_sym_box(grid, 10, 10, 14, 14, 30, 30, 8) # Red side clearance light
    for hy in range(9, 15):
        fill_sym_box(grid, 10, 10, hy, hy, 28, 28, 3 if hy % 2 == 0 else 2)
    # Upper arms & elbow joints
    fill_sym_box(grid, 7, 8, 10, 13, 22, 27, 4)
    fill_sym_box(grid, 7, 8, 13, 13, 23, 25, 6)  # Chrome bicep pistons
    fill_sym_box(grid, 7, 8, 10, 13, 21, 22, 3)  # Elbow hinges

    # --- RIGHT ARM (+X, x >= 16): MASSIVE TWIN-PRONGED FORK-CLAW / POWER-LANCE ---
    fill_box(grid, cx_r + 6, cx_r + 9, 10, 15, 17, 21, 1)   # Right forearm armor
    fill_box(grid, cx_r + 7, cx_r + 8, 11, 14, 18, 20, 0)   # Hollow forearm core
    fill_box(grid, cx_r + 6, cx_r + 9, 10, 14, 20, 21, 4)   # Forearm steel cuff
    fill_box(grid, cx_r + 7, cx_r + 8, 11, 14, 15, 16, 3)   # Right mechanical fist
    # Heavy fork carriage mounted across front & outer right forearm
    fill_box(grid, cx_r + 6, cx_r + 11, 15, 16, 16, 21, 4)
    for rx in range(cx_r + 6, cx_r + 12):
        fill_box(grid, rx, rx, 15, 16, 21, 21, 2 if rx % 2 == 0 else 3)
    # Outer hydraulic actuator piston driving the fork-lance
    fill_box(grid, cx_r + 10, cx_r + 10, 11, 13, 18, 20, 4)
    fill_box(grid, cx_r + 10, cx_r + 10, 14, 15, 19, 19, 6)
    fill_box(grid, cx_r + 10, cx_r + 10, 12, 12, 20, 20, 8)
    # TWIN PARALLEL FORGED-STEEL L-FORK PRONGS (inner x=22..23, outer x=26..27)
    for fx0, fx1 in ((cx_r + 6, cx_r + 7), (cx_r + 10, cx_r + 11)):
        fill_box(grid, fx0, fx1, 16, 16, 16, 22, 5)         # Vertical L-shank
        fill_box(grid, fx0, fx1, 16, 16, 22, 22, 4)         # Top carriage hook
        fill_box(grid, fx0, fx1, 16, 20, 16, 18, 5)         # Heavy reinforced heel
        fill_box(grid, fx0, fx1, 21, 25, 16, 17, 5)         # Twin power-lance blades
        fill_box(grid, fx1, fx1, 18, 25, 17, 17, 6)         # Chrome upper bevel glint
        fill_box(grid, fx0, fx1, 26, 27, 16, 16, 5)         # Tapered blade front
        fill_box(grid, fx0, fx1, 28, 29, 16, 16, 2)         # Safety-yellow fork tips

    # --- LEFT ARM (-X, x <= 15): HEAVY CLAMP / BUMPER GUARD SHIELD ---
    fill_box(grid, cx_l - 9, cx_l - 6, 10, 15, 16, 21, 1)   # Left forearm armor
    fill_box(grid, cx_l - 8, cx_l - 7, 11, 14, 17, 19, 0)   # Hollow forearm core
    fill_box(grid, cx_l - 9, cx_l - 6, 10, 14, 20, 21, 4)   # Forearm steel cuff
    # Heavy industrial bumper guard / load-backrest shield on outer left forearm
    fill_box(grid, cx_l - 10, cx_l - 9, 11, 14, 17, 20, 4)  # Shield mount strut
    fill_box(grid, cx_l - 11, cx_l - 10, 10, 16, 15, 21, 4) # Shield steel backing
    fill_box(grid, cx_l - 11, cx_l - 11, 11, 15, 16, 20, 1) # Safety-orange bumper plate
    for sy in range(11, 16):
        fill_box(grid, cx_l - 11, cx_l - 10, sy, sy, 15, 15, 2 if sy % 2 == 1 else 3)
    for sz in range(16, 21):
        fill_box(grid, cx_l - 11, cx_l - 10, 16, 16, sz, sz, 2 if sz % 2 == 0 else 3)
    # Load-backrest guard grate rising above shield
    fill_box(grid, cx_l - 11, cx_l - 11, 10, 16, 23, 23, 3)
    for sy in (11, 13, 15):
        fill_box(grid, cx_l - 11, cx_l - 11, sy, sy, 21, 23, 3)
    # Heavy hydraulic pincer clamp fist
    fill_box(grid, cx_l - 8, cx_l - 7, 11, 13, 14, 15, 4)   # Wrist block
    fill_box(grid, cx_l - 9, cx_l - 6, 12, 13, 13, 14, 3)   # Clamp cross-pivot
    fill_box(grid, cx_l - 9, cx_l - 9, 12, 16, 12, 14, 5)   # Outer steel clamp jaw
    fill_box(grid, cx_l - 6, cx_l - 6, 12, 16, 12, 14, 5)   # Inner steel clamp jaw
    fill_box(grid, cx_l - 9, cx_l - 9, 15, 16, 13, 13, 6)   # Chrome grip teeth
    fill_box(grid, cx_l - 6, cx_l - 6, 15, 16, 13, 13, 6)

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
    v_a = export_vox(model_a, "forklift_a.vox")
    v_b = export_vox(model_b, "forklift_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: FORKLIFT -> FORKLIFT LIFTER ROBOT",
        "1. FORKLIFT",
        "2. FORKLIFT LIFTER ROBOT",
        "preview_forklift.png",
        yaw_a=42, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"forklift: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
