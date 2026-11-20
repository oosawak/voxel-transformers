import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (246, 194, 24, 255),   # Bright Construction Yellow
    2: (206, 142, 16, 255),   # Deep Industrial Ochre / Ribs & Trim
    3: (34, 38, 46, 255),     # Heavy Rubber Tire Black / Charcoal
    4: (68, 76, 88, 255),     # Dark Gunmetal Steel / Frame & Bed Floor
    5: (192, 202, 214, 255),  # Brushed Silver Metallic / Grille & Pistons
    6: (26, 48, 76, 255),     # Dark Tinted Cab Glass
    7: (92, 218, 255, 255),   # Cyan Glass Glint / Robot Visor
    8: (255, 162, 32, 255),   # Bright Amber Headlights / Beacons
    9: (224, 44, 48, 255),    # Signal Red Taillights / Warning Accents
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


def fill_sym_wheel(grid, x_off0, x_off1, cy, cz, radius=2, tire_col=3, hub_col=5, cap_col=2):
    """Draw a pair of rounded, treaded heavy tires symmetric in X with silver hubs."""
    max_d2 = radius * radius + 1
    for dy in range(-radius, radius + 1):
        for dz in range(-radius, radius + 1):
            if dy * dy + dz * dz <= max_d2:
                fill_sym_box(grid, x_off0, x_off1, cy + dy, cy + dy, cz + dz, cz + dz, tire_col)
    # Tread highlights on outer tire rim
    if radius == 2:
        for dy, dz in ((-2, 1), (-2, -1), (2, 1), (2, -1), (1, 2), (-1, 2)):
            fill_sym_box(grid, x_off1, x_off1, cy + dy, cy + dy, cz + dz, cz + dz, 4)
        # 3x3 cross/octagonal silver metallic hub + ochre center lug
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if abs(dy) + abs(dz) <= 1:
                    fill_sym_box(grid, x_off1, x_off1, cy + dy, cy + dy, cz + dz, cz + dz, hub_col)
    else:
        for dy in range(-1, 2):
            for dz in range(-1, 2):
                fill_sym_box(grid, x_off1, x_off1, cy + dy, cy + dy, cz + dz, cz + dz, hub_col)
    fill_sym_box(grid, x_off1, x_off1, cy, cy, cz, cz, cap_col)


def hollow_interior(grid):
    """Remove strictly hidden voxels whose entire 3x3x3 neighborhood is occupied.
    Keeping all 26-boundary voxels preserves 100% 6-connectivity and outer visuals.
    """
    occ = (grid > 0).astype(np.uint8)
    # Count occupied voxels in each 3x3x3 neighborhood via separable 1D sums
    s = occ[:-2, :, :] + occ[1:-1, :, :] + occ[2:, :, :]
    s = s[:, :-2, :] + s[:, 1:-1, :] + s[:, 2:, :]
    s = s[:, :, :-2] + s[:, :, 1:-1] + s[:, :, 2:]
    interior = np.zeros_like(grid, dtype=bool)
    interior[1:-1, 1:-1, 1:-1] = (s == 27)
    grid[interior] = 0
    return grid


# ==========================================
# FORM A: HEAVY MINING DUMP TRUCK (18 x 28 x 16)
# ==========================================
def build_a():
    grid = np.zeros((18, 28, 16), dtype=np.uint8)

    # --- MASSIVE TREADED TIRES & AXLES (Z: 0..4) ---
    # Rear heavy dual-width tires (Y: 5..9, Z: 0..4)
    fill_sym_wheel(grid, 5, 7, cy=7, cz=2, radius=2)
    # Front heavy tires (Y: 19..23, Z: 0..4)
    fill_sym_wheel(grid, 6, 7, cy=21, cz=2, radius=2)
    # Steel axles & differentials
    fill_sym_box(grid, 0, 5, 6, 8, 1, 3, 4)
    fill_sym_box(grid, 0, 5, 20, 22, 1, 3, 4)
    fill_sym_box(grid, 0, 1, 6, 8, 1, 3, 3)

    # --- CHASSIS FRAME, FUEL TANKS & HYDRAULIC PISTONS (Z: 2..5) ---
    fill_sym_box(grid, 2, 3, 3, 25, 2, 4, 4)
    for cy in (3, 12, 16, 25):
        fill_sym_box(grid, 0, 3, cy, cy, 2, 4, 4)
    # Side fuel & hydraulic tanks between wheels
    fill_sym_box(grid, 4, 6, 12, 16, 2, 4, 4)
    fill_sym_box(grid, 6, 6, 13, 13, 2, 4, 5)  # Silver tank straps
    fill_sym_box(grid, 6, 6, 15, 15, 2, 4, 5)
    # Hydraulic dump-lift pistons under bed
    fill_sym_box(grid, 3, 3, 11, 13, 4, 5, 5)
    fill_sym_box(grid, 3, 3, 12, 12, 3, 4, 3)

    # --- FRONT BUMPER, HOOD & SILVER METALLIC GRILLE (Y: 17..27, Z: 2..7) ---
    # Heavy front bumper
    fill_sym_box(grid, 0, 7, 26, 26, 2, 3, 3)
    fill_sym_box(grid, 6, 7, 26, 26, 2, 3, 2)  # Ochre hazard bumper ends
    fill_sym_box(grid, 2, 2, 27, 27, 2, 2, 5)  # Silver tow hooks
    # Front engine hood & fender deck
    fill_sym_box(grid, 0, 7, 18, 25, 4, 7, 1)
    # Wheel arch cutouts over front tires
    fill_sym_box(grid, 5, 7, 19, 23, 4, 5, 0)
    fill_sym_box(grid, 6, 7, 18, 24, 6, 6, 2)  # Ochre fender flare
    fill_sym_box(grid, 6, 7, 18, 24, 7, 7, 1)
    # Silver slatted radiator grille on front face (+Y)
    fill_sym_box(grid, 0, 3, 25, 25, 4, 6, 3)
    for gx in (0, 2, 3):
        fill_sym_box(grid, gx, gx, 25, 25, 4, 6, 5)
    fill_sym_box(grid, 0, 3, 25, 25, 6, 6, 5)
    # Bright Amber Headlights in charcoal bezels
    fill_sym_box(grid, 4, 7, 25, 25, 4, 6, 3)
    fill_sym_box(grid, 5, 6, 25, 25, 5, 5, 8)
    # Front boarding handrail
    fill_sym_box(grid, 4, 4, 26, 26, 4, 6, 5)
    # Rear bumper & Signal Red taillights
    fill_sym_box(grid, 0, 5, 3, 3, 3, 4, 3)
    fill_sym_box(grid, 3, 5, 3, 3, 3, 4, 9)  # Red taillights
    fill_sym_box(grid, 4, 5, 3, 3, 2, 2, 5)  # Rear mudflap brackets

    # --- FRONT CAB (Y: 17..22, Z: 8..12) ---
    fill_sym_box(grid, 0, 5, 17, 22, 8, 12, 1)
    # Dark tinted wrap-around windshield + cyan glint
    fill_sym_box(grid, 0, 4, 22, 22, 9, 11, 6)
    fill_sym_box(grid, 1, 2, 22, 22, 11, 11, 7)  # Cyan glass glint
    fill_sym_box(grid, 2, 2, 22, 22, 10, 10, 7)
    fill_sym_box(grid, 0, 0, 22, 22, 9, 11, 3)   # Center wiper bar
    # Side cab windows + glint
    fill_sym_box(grid, 5, 5, 18, 21, 9, 11, 6)
    fill_sym_box(grid, 5, 5, 20, 21, 11, 11, 7)
    # Side mirrors
    fill_sym_box(grid, 6, 6, 22, 22, 10, 11, 3)
    # Cab roof trim
    fill_sym_box(grid, 0, 5, 17, 22, 12, 12, 2)
    fill_sym_box(grid, 0, 4, 18, 21, 12, 12, 1)
    # Twin vertical chrome exhaust stacks behind cab
    fill_sym_box(grid, 6, 6, 16, 16, 6, 12, 5)
    fill_sym_box(grid, 6, 6, 15, 16, 12, 12, 5)

    # --- MASSIVE RIBBED DUMP BED WITH FORWARD CANOPY OVERHANG (Y: 0..23, Z: 5..15) ---
    # Bed floor (gunmetal steel interior floor + yellow underside)
    fill_sym_box(grid, 0, 7, 3, 15, 6, 6, 4)
    fill_sym_box(grid, 0, 7, 3, 15, 5, 5, 1)
    # Rear wheel clearance arch under bed
    fill_sym_box(grid, 5, 7, 5, 9, 5, 5, 0)
    fill_sym_box(grid, 5, 7, 5, 9, 6, 6, 4)
    # Sloped rear dump chute / tailgate lip (Y: 0..2)
    fill_sym_box(grid, 0, 7, 2, 2, 6, 6, 4)
    fill_sym_box(grid, 0, 7, 1, 1, 7, 7, 4)
    fill_sym_box(grid, 0, 7, 0, 0, 8, 8, 2)
    # Thick outer dump bed side walls (open top, hollow inside!)
    fill_sym_box(grid, 7, 7, 2, 15, 6, 12, 1)
    fill_sym_box(grid, 7, 7, 1, 1, 7, 12, 1)
    fill_sym_box(grid, 7, 7, 0, 0, 8, 11, 1)
    # Top reinforced ochre side rails
    fill_sym_box(grid, 7, 8, 1, 15, 12, 12, 2)
    fill_sym_box(grid, 7, 8, 0, 0, 11, 11, 2)
    # Iconic external vertical structural ribs on bed sides
    for ry in (3, 7, 11, 15):
        fill_sym_box(grid, 8, 8, ry, ry, 6, 12, 2)
        fill_sym_box(grid, 8, 8, ry, ry, 7, 11, 1)
    # Lower horizontal side stiffener
    fill_sym_box(grid, 8, 8, 3, 15, 6, 6, 2)
    # Front bed bulkhead wall (Y: 15, Z: 6..13)
    fill_sym_box(grid, 0, 7, 15, 15, 6, 13, 1)
    fill_sym_box(grid, 0, 6, 15, 15, 7, 11, 4)  # Inner steel wear-plate
    fill_sym_box(grid, 0, 7, 15, 15, 12, 13, 2)
    # Rear red warning stripes on bed corners
    fill_sym_box(grid, 8, 8, 2, 2, 8, 10, 9)

    # Forward Canopy Overhang protecting the cab (Y: 15..23, Z: 13..15)
    fill_sym_box(grid, 0, 7, 15, 20, 13, 14, 1)
    fill_sym_box(grid, 0, 6, 16, 19, 13, 13, 0)  # Thin overhead canopy shell
    fill_sym_box(grid, 0, 7, 21, 23, 13, 13, 1)  # Forward sloped visor lip
    # Ochre canopy ribs & hazard trim
    fill_sym_box(grid, 7, 8, 15, 20, 13, 14, 2)
    fill_sym_box(grid, 7, 7, 21, 23, 13, 13, 2)
    fill_sym_box(grid, 0, 7, 23, 23, 13, 13, 2)
    fill_sym_box(grid, 3, 3, 15, 22, 14, 14, 2)
    # Twin Amber roof beacons on canopy overhang
    fill_sym_box(grid, 4, 5, 19, 20, 15, 15, 8)
    fill_sym_box(grid, 4, 5, 19, 20, 14, 14, 3)

    return hollow_interior(grid)


# ==========================================
# FORM B: DUMP TITAN ROBOT (30 x 22 x 38)
# ==========================================
def build_b():
    grid = np.zeros((30, 22, 38), dtype=np.uint8)

    # --- GROUNDED HEAVY FEET (Z: 0..2) ---
    fill_sym_box(grid, 2, 5, 7, 14, 0, 0, 3)     # Heavy rubber tread soles
    fill_sym_box(grid, 2, 5, 8, 13, 1, 2, 4)     # Gunmetal foot core
    fill_sym_box(grid, 2, 5, 11, 15, 1, 2, 1)    # Yellow armored toe-cap
    fill_sym_box(grid, 2, 5, 14, 15, 1, 1, 2)    # Ochre toe bumper
    fill_sym_box(grid, 3, 4, 15, 15, 1, 1, 5)    # Silver toe claws
    fill_sym_box(grid, 2, 5, 7, 8, 0, 2, 4)      # Stabilizer heels
    fill_sym_box(grid, 3, 4, 7, 7, 1, 2, 5)

    # --- LOWER LEGS / CALVES WITH TRUCK TIRES (Z: 3..12) ---
    fill_sym_box(grid, 2, 5, 9, 13, 3, 12, 1)    # Thick yellow shin armor
    fill_sym_box(grid, 2, 2, 9, 13, 3, 12, 4)    # Gunmetal inner leg
    fill_sym_box(grid, 5, 5, 9, 13, 3, 12, 2)    # Ochre outer shin rib
    # Recessed silver hydraulic shin pistons on front (+Y)
    fill_sym_box(grid, 3, 4, 13, 13, 4, 10, 4)
    fill_sym_box(grid, 3, 3, 13, 14, 4, 10, 5)
    # Heavy armored knee guards (Z: 10..13)
    fill_sym_box(grid, 2, 5, 13, 15, 10, 13, 1)
    fill_sym_box(grid, 3, 4, 15, 15, 11, 12, 2)
    fill_sym_box(grid, 3, 4, 14, 15, 13, 13, 3)
    fill_sym_box(grid, 4, 4, 14, 14, 10, 10, 9)  # Red warning light
    # Rear leg taillights
    fill_sym_box(grid, 3, 4, 9, 9, 4, 5, 9)
    # Heavy rear dump-truck tires mounted on outer calves (X_off: 6..7)
    fill_sym_wheel(grid, 6, 7, cy=11, cz=5, radius=2)

    # --- THIGHS (Z: 13..17) ---
    fill_sym_box(grid, 2, 4, 9, 12, 13, 17, 4)   # Mechanical gunmetal thigh
    fill_sym_box(grid, 3, 4, 12, 13, 14, 16, 1)  # Front yellow thigh plate
    fill_sym_box(grid, 4, 5, 10, 12, 14, 16, 2)  # Outer ochre armor
    fill_sym_box(grid, 2, 2, 12, 12, 14, 16, 5)  # Silver hydraulic piston rod

    # --- WAIST / PELVIS & FRONT BUMPER BELT (Z: 17..20) ---
    fill_sym_box(grid, 0, 4, 9, 13, 17, 20, 4)   # Solid dark waist block
    fill_sym_box(grid, 0, 1, 10, 14, 16, 20, 1)  # Yellow pelvis codpiece
    fill_sym_box(grid, 0, 1, 14, 14, 17, 19, 2)  # Ochre armor trim
    fill_sym_box(grid, 0, 0, 14, 15, 18, 19, 9)  # Red industrial belt core
    # Heavy truck front-bumper belt plates
    fill_sym_box(grid, 2, 4, 13, 14, 18, 20, 3)
    fill_sym_box(grid, 2, 3, 14, 14, 19, 19, 5)  # Silver bumper clamps
    # Side hip skirts
    fill_sym_box(grid, 5, 5, 9, 13, 17, 19, 1)
    fill_sym_box(grid, 5, 5, 10, 12, 17, 17, 2)

    # --- TORSO / BROAD CAB CHEST (Z: 21..29) - CAB FORMS THE CHEST! ---
    fill_sym_box(grid, 0, 4, 8, 14, 21, 29, 1)   # Broad yellow cab torso
    fill_sym_box(grid, 0, 3, 8, 13, 21, 21, 4)   # Lower torso ab/waist joint
    fill_sym_box(grid, 4, 4, 9, 14, 22, 29, 2)   # Ochre torso side ribs

    # Lower Chest: Truck Front Grille + Amber Headlights (Z: 21..24, Y: 14..16)
    fill_sym_box(grid, 0, 4, 14, 15, 21, 24, 1)
    # Iconic Silver Metallic Slatted Grille dead-center on chest
    fill_sym_box(grid, 0, 2, 15, 16, 21, 24, 3)
    for gx in (0, 2):
        fill_sym_box(grid, gx, gx, 16, 16, 21, 24, 5)
    fill_sym_box(grid, 0, 2, 16, 16, 24, 24, 5)
    fill_sym_box(grid, 0, 2, 16, 16, 21, 21, 5)
    # Glowing Amber Headlights flanking the grille
    fill_sym_box(grid, 3, 4, 15, 15, 22, 23, 3)
    fill_sym_box(grid, 3, 4, 15, 15, 22, 22, 8)
    fill_sym_box(grid, 4, 4, 15, 15, 23, 23, 8)

    # Upper Chest: Truck Cab Windshield with Cyan Glint (Z: 25..29, Y: 14..16)
    fill_sym_box(grid, 0, 4, 14, 15, 25, 29, 1)
    fill_sym_box(grid, 0, 3, 15, 16, 26, 28, 6)  # Wide dark tinted cab windshield
    fill_sym_box(grid, 1, 2, 16, 16, 28, 28, 7)  # Crisp cyan glass glint
    fill_sym_box(grid, 2, 2, 16, 16, 27, 27, 7)
    fill_sym_box(grid, 0, 0, 16, 16, 26, 28, 3)  # Center cab windshield bar
    # Collar bevel & roof amber warning beacons
    fill_sym_box(grid, 0, 4, 11, 15, 29, 29, 2)
    fill_sym_box(grid, 3, 4, 13, 14, 30, 30, 8)  # Amber beacons on collar
    # Twin vertical chrome exhaust stacks behind shoulders
    fill_sym_box(grid, 4, 4, 8, 8, 26, 33, 5)
    fill_sym_box(grid, 4, 4, 7, 8, 33, 33, 5)

    # --- MASSIVE BACK DUMP-BED SHIELD & WINGED PLATES (Y: 2..7, Z: 18..37) ---
    # Heavy gunmetal hydraulic backpack spine connecting torso to bed-shield
    fill_sym_box(grid, 0, 3, 5, 8, 20, 29, 4)
    # Twin silver hydraulic dump-lift pistons on backpack
    fill_sym_box(grid, 2, 2, 5, 6, 21, 28, 5)
    fill_sym_box(grid, 1, 1, 4, 5, 20, 23, 3)

    # Central protective Canopy Overhang crowning behind head (Z: 29..32)
    fill_sym_box(grid, 0, 3, 3, 6, 29, 32, 1)
    fill_sym_box(grid, 0, 2, 4, 5, 30, 31, 4)
    fill_sym_box(grid, 0, 3, 3, 4, 32, 32, 2)

    # Split Dump-Bed Massive Winged Shield-Plates (flaring out & up behind shoulders!)
    # Lower back shield body (X_off: 1..6, Z: 18..30)
    fill_sym_box(grid, 1, 6, 3, 4, 18, 30, 1)    # Bright yellow dump-bed plates
    fill_sym_box(grid, 1, 5, 4, 4, 19, 29, 4)    # Gunmetal bed-interior wear-plate
    fill_sym_box(grid, 1, 6, 2, 3, 18, 19, 2)    # Lower ochre lip
    # Vertical structural dump-bed ribs on rear face (Y: 2)
    for rx in (2, 5):
        fill_sym_box(grid, rx, rx, 2, 2, 19, 30, 2)
    # Red rear hazard stripes on lower shield
    fill_sym_box(grid, 5, 6, 2, 2, 20, 21, 9)

    # Mid-wing dump-bed shield flare (X_off: 6..10, Z: 23..33)
    fill_sym_box(grid, 6, 10, 3, 4, 23, 33, 1)
    fill_sym_box(grid, 6, 9, 4, 4, 24, 32, 4)    # Inner steel wear-liner
    fill_sym_box(grid, 8, 8, 2, 2, 24, 33, 2)    # Heavy vertical bed rib
    fill_sym_box(grid, 10, 10, 2, 4, 23, 33, 2)  # Outer ochre reinforced edge

    # Outer high wing-shield blades (X_off: 10..14, Z: 28..37)
    fill_sym_box(grid, 10, 13, 2, 3, 28, 35, 1)
    fill_sym_box(grid, 12, 14, 2, 3, 32, 37, 1)
    fill_sym_box(grid, 11, 13, 3, 3, 29, 34, 4)  # Inner steel face
    fill_sym_box(grid, 12, 12, 1, 1, 29, 36, 2)  # Outer rear rib
    fill_sym_box(grid, 10, 14, 2, 3, 36, 37, 2)  # Top ochre wing-rail
    fill_sym_box(grid, 14, 14, 2, 3, 32, 37, 2)
    fill_sym_box(grid, 13, 14, 2, 3, 34, 35, 9)  # Red warning wingtip accents
    # Lower swept tail-shield fins (X_off: 6..8, Z: 18..23)
    fill_sym_box(grid, 6, 8, 3, 4, 18, 23, 1)
    fill_sym_box(grid, 7, 9, 3, 3, 17, 20, 2)

    # --- SHOULDERS WITH FRONT TIRES & BLOCKY ARMS (Z: 12..30) ---
    # Shoulder joint axle connecting torso to shoulders
    fill_sym_box(grid, 4, 6, 10, 12, 25, 28, 4)
    # Chunky yellow shoulder pauldrons
    fill_sym_box(grid, 5, 9, 9, 13, 25, 30, 1)
    fill_sym_box(grid, 5, 9, 9, 13, 30, 30, 2)   # Ochre top ridge
    fill_sym_box(grid, 6, 8, 13, 13, 26, 29, 2)  # Front shoulder armor bevel
    fill_sym_box(grid, 7, 7, 13, 13, 27, 28, 5)  # Silver bolt plate
    # Front dump-truck tires mounted as massive shoulder drums! (X_off: 9..10)
    fill_sym_wheel(grid, 9, 10, cy=11, cz=27, radius=2)

    # Upper arms (gunmetal + silver hydraulic piston)
    fill_sym_box(grid, 6, 8, 10, 12, 20, 24, 4)
    fill_sym_box(grid, 8, 8, 11, 12, 21, 23, 5)  # Silver piston rod

    # Blocky Heavy Brawler Forearms (Z: 14..19)
    fill_sym_box(grid, 6, 9, 9, 14, 14, 19, 1)
    fill_sym_box(grid, 6, 9, 9, 14, 19, 19, 2)   # Elbow ochre cuff
    fill_sym_box(grid, 9, 9, 10, 13, 14, 18, 2)
    fill_sym_box(grid, 9, 9, 11, 12, 15, 18, 5)  # Forearm hydraulic piston rail
    fill_sym_box(grid, 6, 8, 14, 14, 15, 18, 4)  # Front bumper guard
    # Heavy charcoal brawler fists (Z: 12..13)
    fill_sym_box(grid, 6, 8, 10, 13, 12, 13, 3)
    fill_sym_box(grid, 6, 8, 13, 13, 12, 13, 5)  # Silver knuckle studs

    # Right Arm (+X, viewer's left): Heavy Hydraulic Dump-Ram Pile-Bunker!
    # Right arm sits at X = 15 + 6..9 = 21..24
    fill_box(grid, 22, 25, 13, 16, 14, 18, 2)    # Ochre ram housing
    fill_box(grid, 23, 24, 14, 19, 15, 17, 5)    # Gleaming silver hydraulic ram piston
    fill_box(grid, 22, 25, 18, 20, 14, 18, 4)    # Heavy steel battering ram head
    fill_box(grid, 22, 25, 20, 20, 15, 17, 1)    # Yellow hazard ram face
    fill_box(grid, 23, 24, 20, 20, 16, 16, 8)    # Amber impact sensor

    # Left Arm (-X, viewer's right): Reinforced Tailgate Buckler Shield!
    # Left arm sits at X = 14 - 9..6 = 5..8
    fill_box(grid, 3, 4, 9, 16, 13, 20, 1)       # Yellow ribbed shield-plate
    fill_box(grid, 3, 3, 10, 15, 14, 19, 2)      # Ochre vertical ribs
    fill_box(grid, 3, 3, 12, 13, 14, 19, 1)
    fill_box(grid, 3, 4, 16, 16, 13, 20, 2)      # Reinforced front edge
    fill_box(grid, 3, 3, 9, 16, 16, 17, 5)       # Horizontal silver bumper bar
    fill_box(grid, 3, 3, 14, 15, 18, 19, 9)      # Red warning stripe
    fill_box(grid, 4, 5, 11, 13, 15, 17, 4)      # Solid arm-to-shield mount

    # --- EXPRESSIVE TITAN HEAD (Z: 30..36) ---
    fill_sym_box(grid, 0, 1, 10, 12, 29, 31, 4)  # Raised solid neck
    fill_sym_box(grid, 0, 2, 9, 13, 31, 35, 1)   # Yellow hardhat-style titan helmet
    fill_sym_box(grid, 0, 2, 9, 12, 35, 35, 2)   # Ochre helmet crown
    fill_sym_box(grid, 0, 1, 13, 13, 31, 32, 3)  # Dark charcoal chin / faceplate
    fill_sym_box(grid, 0, 1, 13, 14, 33, 33, 7)  # Glowing cyan visor eyes
    fill_sym_box(grid, 0, 2, 13, 14, 34, 34, 2)  # Heavy armored brow ridge
    fill_sym_box(grid, 0, 0, 11, 14, 35, 36, 5)  # Central silver industrial crest
    fill_sym_box(grid, 0, 0, 14, 14, 34, 35, 9)  # Red forehead sensor
    fill_sym_box(grid, 3, 3, 10, 12, 32, 35, 2)  # Side ear-pods
    fill_sym_box(grid, 3, 3, 11, 11, 35, 36, 5)  # Twin silver comms antennae

    return hollow_interior(grid)


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
    v_a = export_vox(model_a, "dump_a.vox")
    v_b = export_vox(model_b, "dump_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: DUMP TRUCK -> DUMP TITAN ROBOT",
        "1. DUMP TRUCK",
        "2. DUMP TITAN ROBOT",
        "preview_dump.png",
        yaw_a=40, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"dump: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
