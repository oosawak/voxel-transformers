import math
import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (242, 245, 248, 255),  # Clean Mixer White (Cab trim, drum base, armor)
    2: (22, 138, 178, 255),   # Industrial Teal-Blue (Cab paint, drum spiral, armor)
    3: (224, 62, 54, 255),    # Safety Candy-Red (Drum spiral accent, tail lights, crest)
    4: (36, 40, 48, 255),     # Heavy Tire Rubber / Dark Charcoal Chassis & Joints
    5: (184, 194, 206, 255),  # Brushed Silver / Steel (Grille, chute, hubs, roller rings)
    6: (108, 120, 134, 255),  # Industrial Gunmetal Grey (Pedestals, hopper, inner frame)
    7: (28, 50, 74, 255),     # Dark Tinted Windshield Glass
    8: (94, 224, 255, 255),   # Bright Cyan Glass Glint / Robot Visor & Cannon Core
    9: (250, 186, 46, 255),   # Construction Amber / Warning Yellow (Headlights & Beacons)
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(x0, x1)), min(X - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center (requires even X)."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


def fill_sym_wheel(grid, x_off0, x_off1, cy, cz, radius=2, tire_col=4, hub_col=5):
    """Draw a symmetrical pair of chunky rounded wheels aligned along X axis."""
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1
    cx_r = X // 2
    for dy in range(-radius, radius + 1):
        for dz in range(-radius, radius + 1):
            d2 = dy * dy + dz * dz
            if d2 <= radius * radius + 1:
                y = cy + dy
                z = cz + dz
                if 0 <= y < Y and 0 <= z < Z:
                    for x_off in range(x_off0, x_off1 + 1):
                        col = tire_col
                        if x_off == x_off1 and d2 <= 1:
                            col = hub_col
                        grid[cx_l - x_off, y, z] = col
                        grid[cx_r + x_off, y, z] = col


def hollow_interior(grid):
    """Remove strictly interior voxels (entire 3x3x3 neighborhood solid) while preserving 6-connectivity."""
    solid = grid > 0
    X, Y, Z = grid.shape
    interior = np.ones((X - 2, Y - 2, Z - 2), dtype=bool)
    for dx in (0, 1, 2):
        for dy in (0, 1, 2):
            for dz in (0, 1, 2):
                interior &= solid[dx:dx + X - 2, dy:dy + Y - 2, dz:dz + Z - 2]
    grid[1:-1, 1:-1, 1:-1][interior] = 0
    return grid


def drum_spiral_color(theta, t, n_starts=2, twist=0.14):
    """Iconic candy-stripe diagonal spiral pattern (White + Teal-Blue + Candy-Red)."""
    phase = (theta / (2.0 * math.pi) * n_starts + t * twist) % 1.0
    if phase < 0.34:
        return 2  # Bold Teal-Blue stripe
    elif phase < 0.49:
        return 3  # Crisp Candy-Red accent stripe
    return 1      # Clean Mixer White


# ==========================================
# FORM A: CEMENT MIXER TRUCK (16 x 34 x 20)
# ==========================================
def build_a():
    grid = np.zeros((16, 34, 20), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 7.5

    # --- DARK CHASSIS & FRAME (Y: 3..31, Z: 2..4) ---
    fill_sym_box(grid, 0, 3, 3, 31, 2, 4, 4)
    fill_sym_box(grid, 1, 2, 4, 30, 3, 4, 6)
    # Side hydraulic/fuel tanks between front and rear axles
    fill_sym_box(grid, 3, 4, 17, 21, 2, 4, 6)
    fill_sym_box(grid, 4, 4, 18, 20, 3, 4, 5)
    # Rear bumper & red/amber tail lights (Y: 3, Z: 2..3)
    fill_sym_box(grid, 0, 5, 3, 3, 2, 3, 4)
    fill_sym_box(grid, 4, 5, 3, 3, 3, 3, 3)  # Red tail lights
    fill_sym_box(grid, 3, 3, 3, 3, 3, 3, 9)  # Amber turn signals
    fill_sym_box(grid, 0, 2, 2, 3, 2, 2, 5)  # Rear underrun bar

    # --- 6 CHUNKY TIRES (2 front steer + 4 tandem rear dualies) ---
    for ay in (7, 13, 27):
        fill_sym_box(grid, 0, 4, ay - 1, ay + 1, 1, 3, 4)
    fill_sym_wheel(grid, 4, 6, cy=7, cz=2, radius=2, tire_col=4, hub_col=5)
    fill_sym_wheel(grid, 4, 6, cy=13, cz=2, radius=2, tire_col=4, hub_col=5)
    fill_sym_wheel(grid, 4, 5, cy=27, cz=2, radius=2, tire_col=4, hub_col=5)

    # Rear tandem fenders / mudguards (Y: 4..16, Z: 5)
    fill_sym_box(grid, 4, 6, 4, 16, 5, 5, 6)
    fill_sym_box(grid, 5, 6, 4, 4, 3, 5, 4)
    fill_sym_box(grid, 5, 6, 16, 16, 4, 5, 4)
    fill_sym_box(grid, 6, 6, 5, 15, 5, 5, 1)  # White fender trim

    # --- FRONT HEAVY CAB (Y: 23..32, Z: 2..14) ---
    # Heavy silver front bumper with amber headlights
    fill_sym_box(grid, 0, 5, 31, 32, 2, 4, 5)
    fill_sym_box(grid, 0, 3, 32, 32, 2, 2, 4)  # Lower bumper step
    fill_sym_box(grid, 4, 5, 32, 32, 3, 4, 9)  # Amber headlights
    fill_sym_box(grid, 3, 3, 32, 32, 3, 3, 3)  # Red tow-hook accents
    # Lower cab body
    fill_sym_box(grid, 0, 5, 23, 31, 5, 8, 2)  # Teal-Blue lower cab
    # Front wheel arches around front tire (Y: 25..29)
    fill_sym_box(grid, 4, 6, 24, 30, 5, 5, 4)
    fill_sym_box(grid, 5, 6, 25, 29, 5, 5, 0)  # Wheel arch clearance
    fill_sym_box(grid, 4, 5, 24, 24, 3, 5, 4)  # Cab steps
    # Silver radiator grille on front face (Y: 31, Z: 5..7) with dark intake contrast
    fill_sym_box(grid, 0, 3, 31, 31, 5, 7, 4)
    fill_sym_box(grid, 0, 2, 31, 31, 6, 6, 5)
    fill_sym_box(grid, 0, 3, 31, 31, 7, 7, 5)
    # Clean white cab beltline stripe
    fill_sym_box(grid, 5, 5, 23, 31, 8, 8, 1)
    fill_sym_box(grid, 0, 5, 31, 31, 8, 8, 1)
    # Upper cab greenhouse & roof (Y: 23..30, Z: 9..13)
    fill_sym_box(grid, 0, 4, 23, 30, 9, 12, 1)
    # Dark tinted front windshield + cyan glare
    fill_sym_box(grid, 0, 3, 30, 30, 9, 11, 7)
    fill_sym_box(grid, 1, 2, 30, 30, 10, 11, 8)
    # Side cab windows
    fill_sym_box(grid, 4, 4, 25, 29, 9, 11, 7)
    fill_sym_box(grid, 4, 4, 27, 28, 11, 11, 8)
    # Cab roof visor, teal roof cap & amber beacon lights (Z: 12..14)
    fill_sym_box(grid, 0, 4, 23, 30, 12, 12, 2)
    fill_sym_box(grid, 0, 3, 31, 31, 12, 12, 2)  # Sun-visor overhang
    fill_sym_box(grid, 0, 3, 24, 29, 13, 13, 1)  # Roof aero cap
    fill_sym_box(grid, 3, 3, 28, 29, 13, 14, 9)  # Twin amber roof beacons
    fill_sym_box(grid, 0, 0, 29, 29, 13, 13, 3)  # Red center marker
    # Side mirrors (solidly connected at top & bottom)
    fill_sym_box(grid, 5, 6, 29, 29, 9, 9, 4)
    fill_sym_box(grid, 5, 6, 29, 29, 11, 11, 4)
    fill_sym_box(grid, 6, 6, 28, 29, 9, 11, 4)
    fill_sym_box(grid, 6, 6, 29, 29, 10, 10, 5)
    # Rear cab window
    fill_sym_box(grid, 0, 2, 23, 23, 10, 11, 7)

    # --- CAB-BACK EXHAUST STACKS & WATER TANK (Y: 20..22) ---
    fill_sym_box(grid, 4, 4, 21, 22, 5, 13, 5)  # Twin vertical chrome exhausts
    fill_sym_box(grid, 4, 4, 21, 22, 6, 8, 6)   # Heat shields
    fill_sym_box(grid, 4, 4, 21, 21, 13, 14, 4) # Exhaust tips
    fill_sym_box(grid, 3, 4, 22, 22, 5, 10, 4)  # Support bracket to cab
    # Front drum pedestal & gearbox tower (Y: 20..22, Z: 4..13)
    fill_sym_box(grid, 0, 2, 20, 22, 4, 10, 6)
    fill_sym_box(grid, 0, 2, 20, 22, 10, 12, 2) # Hydraulic motor housing
    fill_sym_box(grid, 0, 2, 21, 22, 13, 14, 5) # Pressurized water tank

    # --- REAR DRUM A-FRAME PEDESTAL & ROLLERS (Y: 5..7, Z: 4..13) ---
    fill_sym_box(grid, 2, 3, 5, 7, 4, 12, 6)
    fill_sym_box(grid, 0, 2, 5, 6, 4, 8, 6)
    fill_sym_box(grid, 2, 3, 5, 6, 11, 12, 5)  # Support rollers
    # Rear maintenance ladder on left side (x=4..5)
    fill_box(grid, 4, 4, 4, 4, 4, 14, 5)
    fill_box(grid, 6, 6, 4, 4, 4, 14, 5)
    for lz in (5, 8, 11, 13):
        fill_box(grid, 4, 6, 4, 5, lz, lz, 5)

    # --- MASSIVE TILTED BARREL-SHAPED MIXING DRUM (Y: 6..20) ---
    # Tilted axis: lower at front (y=20, z=9.4), higher at rear (y=6, z=13.8)
    y_start, y_end = 6, 20
    for y in range(y_start, y_end + 1):
        u = (y - y_start) / float(y_end - y_start)  # 0 at rear mouth, 1 at front nose
        cz = 13.8 - 4.4 * u
        # Barrel profile: mouth (r=3.2) -> big belly at u=0.58 (r=5.8) -> front cone (r=2.5)
        if u < 0.58:
            t_prof = u / 0.58
            r_outer = 3.2 + 2.6 * math.sin(t_prof * math.pi * 0.5)
        else:
            t_prof = (u - 0.58) / 0.42
            r_outer = 5.8 - 3.3 * (t_prof ** 1.35)
        r_inner = max(0.0, r_outer - 1.35)

        for x in range(1, X - 1):
            dx = x - cx
            for z in range(4, Z):
                dz = z - cz
                dist = math.sqrt(dx * dx + dz * dz)
                if dist <= r_outer:
                    is_front_cap = (y == y_end)
                    if is_front_cap or dist >= r_inner:
                        theta = math.atan2(dz, dx)
                        if y in (8, 9):
                            col = 5  # Silver roller track ring
                        elif y == 19 or is_front_cap:
                            col = 6  # Front drive ring
                        elif y == y_start:
                            col = 4  # Dark mouth lip
                        else:
                            col = drum_spiral_color(theta, y - y_start, n_starts=2, twist=0.15)
                        grid[x, y, z] = col

    # --- REAR CHARGING HOPPER & DISCHARGE CHUTE (Y: 0..6) ---
    # Upper charging hopper funnel feeding into the rear drum mouth (Z: 14..18)
    fill_sym_box(grid, 0, 2, 4, 6, 14, 17, 6)
    fill_sym_box(grid, 0, 3, 3, 6, 17, 18, 6)
    fill_sym_box(grid, 0, 2, 4, 5, 17, 18, 0)  # Hollow funnel opening
    fill_sym_box(grid, 0, 3, 3, 3, 18, 18, 5)  # Silver rim
    # Slanted discharge chute projecting rearward (Y: 0..5, Z: 8..12)
    fill_sym_box(grid, 0, 2, 4, 6, 10, 12, 5)
    fill_sym_box(grid, 0, 1, 4, 5, 11, 12, 6)
    fill_sym_box(grid, 0, 1, 2, 4, 9, 10, 5)
    fill_sym_box(grid, 0, 1, 0, 2, 8, 9, 5)
    fill_sym_box(grid, 0, 0, 1, 3, 9, 10, 6)   # Chute channel
    fill_sym_box(grid, 0, 1, 3, 5, 7, 9, 4)    # Hydraulic chute lift arm

    return hollow_interior(grid)


# ==========================================
# FORM B: MIXER JUGGERNAUT ROBOT (32 x 24 x 37)
# ==========================================
def build_b():
    grid = np.zeros((32, 24, 37), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 15.5

    # --- STOMPING FEET (Z: 0..3) - Heavy bumper toes + charcoal treads ---
    fill_sym_box(grid, 3, 7, 7, 14, 0, 1, 4)    # Chunky rubber sole
    fill_sym_box(grid, 3, 7, 13, 16, 0, 2, 5)   # Heavy silver bumper toe caps
    fill_sym_box(grid, 4, 6, 15, 16, 1, 2, 2)   # Teal armored toe guard
    fill_sym_box(grid, 6, 7, 16, 16, 1, 1, 9)   # Amber hazard lights on toes
    fill_sym_box(grid, 3, 6, 6, 8, 0, 2, 6)     # Gunmetal heel spurs
    fill_sym_box(grid, 4, 6, 9, 12, 2, 3, 4)    # Ankle piston block

    # --- THICK STOMPING LOWER LEGS (Z: 4..11) + 4 TANDEM TIRES ---
    fill_sym_box(grid, 3, 6, 8, 13, 4, 10, 2)   # Teal-blue heavy leg armor
    fill_sym_box(grid, 3, 6, 13, 14, 5, 10, 1)  # White front shin plates
    fill_sym_box(grid, 4, 5, 14, 14, 6, 9, 5)   # Silver shin reinforcement
    fill_sym_box(grid, 3, 6, 12, 15, 9, 11, 5)  # Heavy knee bumper armor
    fill_sym_box(grid, 4, 5, 15, 15, 10, 10, 3) # Candy-red knee stripe
    # Rear calf mudguards & red/amber tail lights
    fill_sym_box(grid, 4, 6, 7, 8, 5, 9, 6)
    fill_sym_box(grid, 5, 6, 7, 7, 6, 6, 3)     # Tail lights on calves
    fill_sym_box(grid, 4, 4, 7, 7, 6, 6, 9)
    # Chunky tandem tires mounted on outer lower legs (2 per leg = 4 rear tires!)
    fill_sym_wheel(grid, 6, 8, cy=10, cz=5, radius=2, tire_col=4, hub_col=5)
    fill_sym_wheel(grid, 6, 7, cy=11, cz=9, radius=2, tire_col=4, hub_col=5)

    # --- STURDY THIGHS & PELVIS / WAIST (Z: 11..15) ---
    fill_sym_box(grid, 3, 5, 9, 12, 11, 14, 6)  # Thick gunmetal thighs
    fill_sym_box(grid, 4, 5, 12, 13, 12, 13, 5) # Silver thigh hydraulics
    # Compact armored pelvis cradling the mixing drum belly
    fill_sym_box(grid, 0, 6, 8, 14, 13, 15, 4)
    fill_sym_box(grid, 0, 2, 13, 15, 13, 15, 5) # Silver central codpiece
    fill_sym_box(grid, 0, 1, 15, 16, 14, 15, 9) # Amber construction belt buckle
    fill_sym_box(grid, 0, 2, 15, 15, 13, 13, 3) # Red waist trim
    fill_sym_box(grid, 5, 6, 9, 13, 13, 15, 2)  # Hip side-skirt fenders

    # --- MASSIVE BARREL MIXING DRUM TORSO (Z: 15..27) ---
    # The giant diagonal-striped mixing drum IS the rotund barrel torso itself!
    z_bot, z_top = 15, 27
    cy_drum = 11.2
    for z in range(z_bot, z_top + 1):
        u = (z - z_bot) / float(z_top - z_bot)  # 0 at waist, 1 at upper chest
        bulge = math.sin(u * math.pi)
        rx = 5.0 + 2.6 * bulge
        ry = 4.6 + 2.4 * bulge
        rx_in = max(0.0, rx - 1.45)
        ry_in = max(0.0, ry - 1.45)

        for x in range(7, X - 7):
            dx = x - cx
            for y in range(4, 20):
                dy = y - cy_drum
                d_out = (dx / rx) ** 2 + (dy / ry) ** 2
                if d_out <= 1.0:
                    d_in = (dx / rx_in) ** 2 + (dy / ry_in) ** 2 if rx_in > 0 and ry_in > 0 else 2.0
                    is_cap = (z == z_bot or z == z_top)
                    if is_cap or d_in >= 1.0:
                        theta = math.atan2(dy, dx)
                        if z in (z_bot, z_top):
                            col = 5  # Silver drum roller rings at waist & upper chest!
                        else:
                            col = drum_spiral_color(theta, z - z_bot, n_starts=3, twist=0.14)
                        grid[x, y, z] = col

    # --- TRUCK CAB FOLDED OVER UPPER CHEST & COLLAR (Z: 25..31) ---
    # Compact cab front perched atop the giant striped drum belly!
    fill_sym_box(grid, 0, 4, 14, 17, 25, 29, 2)  # Teal-blue cab chest shell
    # Front radiator grille & headlights directly from Form A's cab!
    fill_sym_box(grid, 0, 2, 17, 18, 25, 26, 4)  # Grille recess
    fill_sym_box(grid, 0, 2, 18, 18, 26, 26, 5)  # Silver grille bar
    fill_sym_box(grid, 0, 1, 18, 18, 25, 25, 5)  # Lower silver grille accent
    fill_sym_box(grid, 3, 4, 17, 18, 25, 26, 9)  # Twin amber cab headlights!
    # White cab beltline & dark tinted cab windshield across upper chest!
    fill_sym_box(grid, 0, 4, 17, 17, 27, 27, 1)
    fill_sym_box(grid, 0, 3, 16, 17, 28, 29, 7)  # Dark tinted cab windshield
    fill_sym_box(grid, 1, 2, 17, 17, 28, 29, 8)  # Cyan windshield glint
    # Cab roof collar & twin amber cab roof beacons framing the head (Z: 28..31)
    fill_sym_box(grid, 0, 4, 10, 16, 28, 29, 1)  # Upper chest deck
    fill_sym_box(grid, 3, 4, 11, 16, 29, 30, 2)  # Raised teal cab collar walls
    fill_sym_box(grid, 3, 4, 14, 15, 31, 31, 9)  # Twin amber cab roof beacons!
    fill_sym_box(grid, 0, 2, 9, 10, 29, 30, 6)   # Rear neck rollbar

    # --- RUGGED CAB-ROOF HELMET HEAD (Z: 30..36) ---
    fill_sym_box(grid, 0, 1, 11, 13, 29, 30, 4)  # Thick charcoal neck
    fill_sym_box(grid, 0, 2, 10, 14, 30, 34, 1)  # White helmet core
    fill_sym_box(grid, 0, 2, 10, 14, 34, 35, 2)  # Teal cab-roof helmet crown
    fill_sym_box(grid, 0, 2, 14, 15, 34, 34, 2)  # Rugged cab sun-visor brow!
    # Glowing cyan visor & steel respirator faceplate
    fill_sym_box(grid, 0, 2, 14, 14, 32, 33, 8)  # Glowing cyan visor
    fill_sym_box(grid, 2, 2, 14, 14, 32, 32, 7)  # Visor frame shadow
    fill_sym_box(grid, 0, 1, 14, 15, 30, 31, 5)  # Steel mouthguard / jaw
    fill_sym_box(grid, 0, 0, 15, 15, 30, 30, 4)  # Chin vent
    # Construction crest & antenna ear pods
    fill_sym_box(grid, 0, 0, 12, 15, 35, 36, 3)  # Candy-red forehead crest
    fill_sym_box(grid, 0, 0, 15, 15, 34, 35, 9)  # Amber forehead beacon
    fill_sym_box(grid, 3, 3, 11, 13, 31, 33, 6)  # Helmet ear pods
    fill_sym_box(grid, 3, 3, 12, 12, 34, 36, 5)  # Twin comm antennas

    # --- COMPACT UPPER HOPPER FUNNEL & EXHAUST STACKS (Rear leaves striped drum visible!) ---
    fill_sym_box(grid, 0, 3, 5, 7, 25, 29, 6)    # Upper hopper mount (keeps drum Z:16..24 visible!)
    fill_sym_box(grid, 0, 2, 3, 5, 26, 31, 6)    # Rear charging hopper funnel
    fill_sym_box(grid, 0, 1, 4, 5, 29, 31, 0)    # Hollow hopper opening
    fill_sym_box(grid, 0, 2, 3, 5, 31, 31, 5)    # Silver hopper rim
    # Twin vertical chrome exhaust stacks rising behind shoulders
    fill_sym_box(grid, 5, 5, 6, 7, 25, 33, 5)
    fill_sym_box(grid, 5, 5, 6, 7, 27, 29, 6)
    fill_sym_box(grid, 5, 5, 6, 6, 33, 34, 4)    # Exhaust tips
    fill_sym_box(grid, 4, 5, 7, 8, 25, 27, 4)    # Solid connector to upper torso

    # --- MASSIVE JUGGERNAUT SHOULDERS & BLOCKY ARMS (Z: 11..30) ---
    # Heavy shoulder axles bridging out from the barrel torso
    fill_sym_box(grid, 6, 8, 10, 12, 23, 27, 4)
    fill_sym_box(grid, 7, 8, 10, 12, 24, 26, 6)
    # Huge armored pauldrons (X_off: 8..11, Z: 24..30)
    fill_sym_box(grid, 8, 11, 9, 14, 24, 29, 2)  # Teal-blue shoulder blocks
    fill_sym_box(grid, 8, 11, 10, 13, 29, 30, 1) # White shoulder top caps
    fill_sym_box(grid, 9, 10, 14, 14, 26, 28, 1) # Front white armor trim
    fill_sym_box(grid, 9, 10, 14, 14, 25, 25, 3) # Candy-red warning stripe
    fill_sym_box(grid, 10, 11, 13, 14, 30, 30, 9) # Amber shoulder clearance beacons
    # Front truck tires mounted on outer shoulders (2 front tires!)
    fill_sym_wheel(grid, 11, 13, cy=11, cz=26, radius=2, tire_col=4, hub_col=5)

    # Heavy hydraulic upper arms (Z: 19..23)
    fill_sym_box(grid, 9, 11, 10, 12, 19, 23, 6)
    fill_sym_box(grid, 9, 10, 10, 12, 20, 22, 4)
    fill_sym_box(grid, 11, 11, 11, 11, 20, 23, 5) # Outer silver piston rod

    # Blocky armored forearms (Z: 13..18)
    fill_sym_box(grid, 9, 12, 9, 14, 13, 18, 2)  # Teal-blue heavy gauntlets (high contrast vs cannon!)
    fill_sym_box(grid, 9, 12, 13, 14, 14, 17, 1) # White front forearm trim
    fill_sym_box(grid, 12, 12, 10, 13, 14, 17, 6) # Gunmetal outer guard plate
    fill_sym_box(grid, 10, 11, 14, 14, 13, 13, 3) # Red cuff trim
    # Heavy blocky fists (Z: 10..12)
    fill_sym_box(grid, 9, 11, 10, 13, 10, 12, 4)
    fill_sym_box(grid, 10, 11, 13, 13, 11, 12, 5) # Silver knuckle guards

    # --- RIGHT ARM DISCHARGE CHUTE CANNON (+X side, x: 26..29, Y: 13..22, Z: 14..18) ---
    # Solid mount on robot's right forearm (cx_r = 16, x_off 10..13 is x = 26..29)
    fill_box(grid, 26, 29, 13, 21, 14, 18, 5)     # Silver chute cannon housing
    fill_box(grid, 27, 28, 14, 22, 15, 17, 6)     # Gunmetal inner trough/barrel
    fill_box(grid, 27, 28, 17, 22, 16, 16, 0)     # Hollow cannon bore!
    fill_box(grid, 26, 29, 21, 22, 14, 18, 5)     # Flared chute muzzle
    fill_box(grid, 27, 28, 21, 22, 15, 17, 0)     # Hollow muzzle opening
    fill_box(grid, 27, 28, 15, 20, 18, 18, 8)     # Glowing cyan energy/slurry core strip
    fill_box(grid, 26, 29, 19, 19, 14, 18, 3)     # Candy-red hazard muzzle band
    fill_box(grid, 25, 26, 14, 17, 15, 17, 4)     # Solid brace to right forearm

    # --- LEFT ARM MUDGUARD SHIELD PLATE (-X side, x: 2..3) ---
    # Heavy fender shield on left forearm (cx_l = 15, x_off 12 is x = 3)
    fill_box(grid, 3, 3, 10, 15, 12, 18, 6)
    fill_box(grid, 2, 2, 11, 14, 13, 17, 5)
    fill_box(grid, 2, 2, 12, 13, 14, 16, 2)
    fill_box(grid, 2, 2, 14, 14, 13, 17, 9)       # Amber hazard stripe

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
    v_a = export_vox(model_a, "mixer_a.vox")
    v_b = export_vox(model_b, "mixer_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: CEMENT MIXER TRUCK -> MIXER JUGGERNAUT ROBOT",
        "1. CEMENT MIXER TRUCK",
        "2. MIXER JUGGERNAUT ROBOT",
        "preview_mixer.png",
        yaw_a=42, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"mixer: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
