import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (242, 108, 22, 255),   # Vibrant Safety Orange (Cab, Body, Plow Blade, Chest Armor)
    2: (184, 62, 16, 255),    # Deep Orange-Red Shading (Fenders, Lower Armor, Trim)
    3: (250, 212, 36, 255),   # High-Vis Safety Yellow (Warning Stripes, Beacons, Crest)
    4: (44, 48, 58, 255),     # Heavy Rubber Tire Charcoal (Tires, Undercarriage, Pillars)
    5: (92, 100, 114, 255),   # Gunmetal Steel (Hydraulic Rams, Chassis, Push Frame, Joints)
    6: (186, 198, 212, 255),  # Brushed Silver / Steel (Plow Cutting Edge, Snow Chains, Grille)
    7: (94, 214, 246, 255),   # Icy Cyan (Cab Windshield Glass, Side Windows, Visor)
    8: (255, 240, 140, 255),  # Bright Warm Headlights / Work Lights / Beacon Core
    9: (234, 244, 252, 255),  # Snow-White / Frost Accent (Salt Mound, Stripes, Frost Trim)
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


def hollow_interior(grid):
    """Remove strictly interior voxels (all 26 3x3x3 neighbors occupied), preserving 6-connectivity."""
    occ = grid > 0
    interior = np.zeros_like(occ)
    inner = occ[1:-1, 1:-1, 1:-1].copy()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                inner &= occ[1 + dx:occ.shape[0] - 1 + dx,
                             1 + dy:occ.shape[1] - 1 + dy,
                             1 + dz:occ.shape[2] - 1 + dz]
    interior[1:-1, 1:-1, 1:-1] = inner
    grid[interior] = 0
    return grid


def fill_sym_chained_wheel_x(
    grid, x_off0, x_off1, cy, cz, r_outer, r_rim, r_hub,
    tire_col=4, chain_col=6, rim_col=5, hub_col=6, recess_outer=True,
):
    """Draw a pair of symmetrical chunky snow-chained tires along the X axis."""
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1
    cx_r = X // 2
    y_min = max(0, int(np.floor(cy - r_outer - 1)))
    y_max = min(Y - 1, int(np.ceil(cy + r_outer + 1)))
    z_min = max(0, int(np.floor(cz - r_outer - 1)))
    z_max = min(Z - 1, int(np.ceil(cz + r_outer + 1)))

    for y in range(y_min, y_max + 1):
        for z in range(z_min, z_max + 1):
            dy = y - cy
            dz = z - cz
            dist = np.hypot(dy, dz)
            if dist > r_outer:
                continue

            angle = np.arctan2(dz, dy)
            chain_link = int(np.floor((angle + np.pi) / (np.pi / 4.0))) % 2 == 0

            for x_off in range(x_off0, x_off1 + 1):
                is_outer_face = (x_off == x_off1)
                is_inner_face = (x_off == x_off0)
                if dist <= r_hub:
                    col = hub_col if (is_outer_face or is_inner_face) else 5
                elif dist <= r_rim:
                    if recess_outer and is_outer_face and dist > r_hub + 0.55:
                        continue
                    col = rim_col
                else:
                    if dist >= r_outer - 0.85 and chain_link:
                        col = chain_col
                    else:
                        col = tire_col
                xl = cx_l - x_off
                xr = cx_r + x_off
                if 0 <= xl < X:
                    grid[xl, y, z] = col
                if 0 <= xr < X:
                    grid[xr, y, z] = col


# ==========================================
# FORM A: HEAVY WINTER SNOWPLOW TRUCK (22 x 34 x 19)
# ==========================================
def build_a():
    grid = np.zeros((22, 34, 19), dtype=np.uint8)
    cx_r = grid.shape[0] // 2  # 11 (+X right side)

    # --- CHUNKY SNOW-CHAINED TIRES (Front Y: 20.5, Rear Y: 7.5, Z: 0..7) ---
    fill_sym_chained_wheel_x(
        grid, 5, 7, cy=20.5, cz=3.5,
        r_outer=3.45, r_rim=1.75, r_hub=0.75,
        tire_col=4, chain_col=6, rim_col=5, hub_col=3, recess_outer=True,
    )
    fill_sym_chained_wheel_x(
        grid, 5, 7, cy=7.5, cz=3.5,
        r_outer=3.45, r_rim=1.75, r_hub=0.75,
        tire_col=4, chain_col=6, rim_col=5, hub_col=3, recess_outer=True,
    )
    # Hubcaps & axle studs
    fill_sym_box(grid, 7, 7, 20, 21, 3, 4, 6)
    fill_sym_box(grid, 7, 7, 7, 8, 3, 4, 6)

    # --- HEAVY CHASSIS, AXLES & SIDE STEPS (Y: 2..27, Z: 2..6) ---
    fill_sym_box(grid, 0, 5, 7, 8, 3, 4, 5)    # Rear axle
    fill_sym_box(grid, 0, 5, 20, 21, 3, 4, 5)  # Front axle
    fill_sym_box(grid, 0, 4, 2, 26, 4, 5, 5)   # Main frame rails
    fill_sym_box(grid, 0, 3, 4, 24, 4, 4, 0)   # Hollow inner chassis underside
    fill_sym_box(grid, 0, 4, 2, 3, 3, 5, 4)    # Rear chassis bumper
    fill_sym_box(grid, 0, 4, 25, 26, 3, 5, 4)  # Front steel bumper
    # Side fuel tank & boarding steps between wheels
    fill_sym_box(grid, 5, 6, 13, 16, 3, 5, 5)
    fill_sym_box(grid, 6, 6, 14, 15, 3, 3, 6)  # Steel step grate
    fill_sym_box(grid, 6, 6, 13, 16, 5, 5, 3)  # Yellow safety sill stripe

    # --- REAR SALT / GRIT SPREADER HOPPER BED (Y: 2..15, Z: 6..13) ---
    # Tapered V-hopper lower & upper walls (hollow core to keep voxel budget crisp)
    fill_sym_box(grid, 0, 5, 2, 15, 6, 11, 1)
    fill_sym_box(grid, 0, 4, 3, 14, 6, 10, 0)  # Hollow interior
    # Deep orange-red lower fender & mudflaps over rear wheels
    fill_sym_box(grid, 5, 7, 4, 11, 7, 8, 2)
    fill_sym_box(grid, 5, 7, 3, 3, 4, 7, 4)    # Rear rubber mudflaps
    # High-vis yellow & white diagonal/stripe safety banding along hopper sides
    fill_sym_box(grid, 5, 5, 2, 15, 9, 9, 3)
    fill_sym_box(grid, 5, 5, 4, 13, 10, 10, 2)
    fill_sym_box(grid, 5, 5, 11, 14, 9, 9, 9)  # Frost/white reflective stripe
    # Hopper top rim & piled snow-white salt/grit mound (hollowed underneath)
    fill_sym_box(grid, 0, 5, 2, 15, 11, 11, 2)
    fill_sym_box(grid, 0, 4, 3, 14, 11, 11, 9)  # White salt bed top
    fill_sym_box(grid, 0, 3, 4, 13, 12, 12, 9)  # Raised salt mound
    fill_sym_box(grid, 0, 2, 6, 11, 13, 13, 9)  # Salt crest
    fill_sym_box(grid, 0, 3, 4, 13, 11, 11, 0)  # Hollow unseen cavity below salt mound
    fill_sym_box(grid, 0, 2, 6, 11, 12, 12, 0)  # Hollow unseen cavity below salt crest
    # Steel hopper screen bars across the salt mound
    for sy in (5, 9, 12):
        fill_sym_box(grid, 0, 4, sy, sy, 12, 12, 6)
    # Rear hazard chevrons & rotary salt spinner chute (Y: 0..2, Z: 2..9)
    fill_sym_box(grid, 3, 4, 2, 2, 7, 8, 3)    # Yellow rear hazard lamps
    fill_sym_box(grid, 4, 5, 2, 2, 6, 6, 8)    # Rear work lights
    fill_sym_box(grid, 0, 2, 1, 2, 4, 8, 5)    # Spreader chute housing
    fill_sym_box(grid, 0, 1, 0, 1, 2, 5, 5)    # Vertical drop chute
    fill_sym_box(grid, 0, 2, 0, 1, 2, 2, 6)    # Silver rotary salt spinner disc
    fill_sym_box(grid, 0, 1, 1, 1, 6, 7, 3)    # Yellow chute warning badge

    # --- HIGH-VISIBILITY ORANGE SNOWPLOW CAB (Y: 16..26, Z: 6..16) ---
    # Lower cab body & engine hood
    fill_sym_box(grid, 0, 5, 16, 25, 6, 10, 1)
    fill_sym_box(grid, 0, 4, 17, 24, 6, 9, 0)  # Hollow interior
    # Deep orange-red front wheel arches
    fill_sym_box(grid, 5, 7, 17, 24, 7, 8, 2)
    fill_sym_box(grid, 5, 5, 16, 24, 9, 9, 3)  # Yellow door safety stripe
    fill_sym_box(grid, 5, 5, 18, 20, 9, 9, 9)  # White cab fleet decal
    # Front nose grille & headlights (Y: 25..26)
    fill_sym_box(grid, 0, 4, 26, 26, 6, 9, 1)
    fill_sym_box(grid, 0, 2, 26, 26, 6, 9, 4)  # Dark grille recess
    fill_sym_box(grid, 0, 2, 26, 26, 7, 7, 6)  # Steel grille bar
    fill_sym_box(grid, 0, 2, 26, 26, 9, 9, 6)  # Steel grille bar
    fill_sym_box(grid, 3, 4, 26, 26, 7, 8, 8)  # Main warm headlights
    # Elevated plow-clearance headlights on front hood corners (Z: 10..11)
    fill_sym_box(grid, 4, 5, 24, 25, 10, 11, 4)
    fill_sym_box(grid, 4, 5, 26, 26, 10, 11, 8)
    # Cab glass enclosure (Z: 11..14, Y: 16..23)
    fill_sym_box(grid, 0, 4, 16, 23, 11, 14, 7)
    fill_sym_box(grid, 0, 3, 17, 22, 11, 14, 0)  # Hollow cab interior
    # Structural charcoal cab corner pillars & windshield frame
    fill_sym_box(grid, 4, 4, 16, 16, 11, 14, 4)
    fill_sym_box(grid, 4, 4, 23, 23, 11, 14, 4)
    fill_sym_box(grid, 4, 4, 19, 19, 11, 14, 4)
    fill_sym_box(grid, 0, 0, 23, 23, 11, 14, 4)  # Center windshield divider
    # Rear cab window frame
    fill_sym_box(grid, 0, 4, 16, 16, 11, 14, 1)
    fill_sym_box(grid, 0, 2, 16, 16, 12, 13, 7)
    # Side mirrors on stalks
    fill_sym_box(grid, 5, 6, 22, 22, 11, 11, 4)
    fill_sym_box(grid, 6, 6, 22, 22, 11, 13, 4)
    fill_sym_box(grid, 6, 6, 21, 21, 12, 13, 6)
    # Cab roof & high-vis warning beacon lightbar (Z: 15..18)
    fill_sym_box(grid, 0, 5, 16, 23, 15, 15, 1)
    fill_sym_box(grid, 0, 4, 17, 22, 16, 16, 9)  # Frost-white roof cap
    fill_sym_box(grid, 0, 4, 24, 24, 15, 15, 2)  # Cab sun visor
    # Warning lightbar across roof
    fill_sym_box(grid, 0, 3, 20, 21, 17, 17, 5)  # Steel mounting bar
    fill_sym_box(grid, 2, 3, 20, 21, 17, 18, 3)  # Twin yellow rotating beacons
    fill_sym_box(grid, 2, 2, 21, 21, 18, 18, 8)  # Bright beacon flash
    fill_sym_box(grid, 0, 1, 20, 21, 17, 17, 3)
    # Vertical chrome exhaust stack behind right cab corner (+X)
    fill_box(grid, cx_r + 5, cx_r + 5, 15, 16, 8, 15, 6)
    fill_box(grid, cx_r + 5, cx_r + 5, 15, 15, 16, 17, 5)
    fill_box(grid, cx_r + 5, cx_r + 6, 15, 15, 17, 17, 6)

    # --- HYDRAULIC PUSH FRAME & RAMS (Y: 25..30, Z: 2..9) ---
    fill_sym_box(grid, 2, 3, 25, 29, 3, 4, 5)   # Heavy lower push beams
    fill_sym_box(grid, 1, 2, 26, 29, 5, 6, 5)   # Angled A-frame struts
    fill_sym_box(grid, 0, 1, 25, 26, 5, 9, 5)   # Vertical lift tower
    fill_sym_box(grid, 0, 0, 26, 29, 7, 8, 6)   # Chrome upper lift hydraulic cylinder
    fill_sym_box(grid, 3, 3, 26, 29, 4, 5, 6)   # Twin chrome angling pistons

    # --- HUGE CURVED FRONT SNOWPLOW BLADE (Y: 29..33, Z: 1..9, width 20!) ---
    # Concave snow-throwing scoop profile (x_off: 0..9 -> X: 1..20)
    # Bottom steel cutting edge jutting forward (Z: 1..2, Y: 30..32)
    fill_sym_box(grid, 0, 9, 31, 32, 1, 1, 6)   # Gleaming steel scraper edge
    fill_sym_box(grid, 0, 9, 30, 31, 2, 2, 6)
    # Frost/snow dust highlight along outer cutting tips
    fill_sym_box(grid, 7, 9, 32, 32, 1, 1, 9)
    # Middle concave curved orange plow face (Z: 3..6, sleek 1-voxel curved shell at Y: 30)
    fill_sym_box(grid, 0, 9, 30, 30, 3, 6, 1)
    # Swept-forward outer wing scoops (x_off: 7..9) for aggressive plow silhouette
    fill_sym_box(grid, 7, 9, 31, 31, 3, 6, 1)
    fill_sym_box(grid, 8, 9, 31, 32, 2, 5, 2)
    # Upper curved snow-deflector curl (Z: 7..8, Y: 30..32)
    fill_sym_box(grid, 0, 9, 30, 31, 7, 7, 1)
    fill_sym_box(grid, 0, 9, 31, 32, 8, 8, 3)   # High-vis yellow top deflector lip!
    fill_sym_box(grid, 0, 2, 32, 32, 8, 8, 9)   # White snow-deflector center strip
    # High-vis yellow hazard stripes on outer plow wings
    fill_sym_box(grid, 8, 9, 31, 31, 4, 4, 3)
    fill_sym_box(grid, 8, 9, 31, 31, 6, 6, 3)
    # Heavy vertical gunmetal reinforcement ribs on back of blade (Y: 29)
    for rx in (1, 4, 7):
        fill_sym_box(grid, rx, rx, 29, 29, 2, 7, 5)
    fill_sym_box(grid, 0, 8, 29, 29, 4, 4, 5)   # Horizontal rear brace bar
    # Tall yellow boundary guide rods on outer top corners of plow
    fill_sym_box(grid, 9, 9, 31, 31, 9, 10, 3)
    fill_sym_box(grid, 9, 9, 31, 31, 11, 11, 9)

    return hollow_interior(grid)


# ==========================================
# FORM B: HEAVY SNOWPLOW SHIELD ROBOT (34 x 24 x 41)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 41), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 16 (-X robot left / viewer right)
    cx_r = grid.shape[0] // 2      # 17 (+X robot right / viewer left)

    # --- RUGGED SNOW-BOOT FEET (Z: 0..3) ---
    fill_sym_box(grid, 3, 7, 8, 16, 0, 1, 4)   # Heavy charcoal rubber sole
    fill_sym_box(grid, 3, 7, 15, 16, 0, 0, 6)  # Steel ice-cleat claws
    fill_sym_box(grid, 3, 7, 7, 9, 0, 2, 5)    # Steel heel stabilizer
    fill_sym_box(grid, 3, 7, 11, 17, 1, 2, 1)  # Safety orange boot armor
    fill_sym_box(grid, 4, 6, 13, 17, 2, 3, 2)  # Deep orange-red toe cap
    fill_sym_box(grid, 4, 6, 17, 17, 1, 2, 3)  # High-vis yellow toe bumper

    # --- LOWER LEGS WITH DUAL CHUNKY SNOW-CHAINED TIRES (Z: 3..15) ---
    fill_sym_box(grid, 3, 6, 9, 14, 3, 14, 2)
    fill_sym_box(grid, 4, 5, 10, 13, 4, 13, 0)  # Hollow core
    fill_sym_box(grid, 3, 6, 13, 14, 4, 13, 1)  # Front safety orange shin armor
    fill_sym_box(grid, 4, 5, 14, 14, 5, 11, 3)  # High-vis yellow shin stripe
    fill_sym_box(grid, 4, 5, 14, 14, 8, 9, 9)   # White reflective frost stripe
    fill_sym_box(grid, 3, 3, 10, 13, 4, 13, 5)  # Inner gunmetal hydraulic frame
    # Armored knee guards
    fill_sym_box(grid, 3, 6, 14, 15, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 15, 16, 13, 15, 6)  # Steel knee ram
    fill_sym_box(grid, 4, 5, 16, 16, 14, 14, 3)  # Yellow knee warning bar
    # LOWER SNOW-CHAINED TIRE ON OUTER ANKLE/SHIN (x_off: 7..8, cz: 5.5)
    fill_sym_chained_wheel_x(
        grid, 7, 8, cy=11.0, cz=5.5,
        r_outer=3.25, r_rim=1.65, r_hub=0.75,
        tire_col=4, chain_col=6, rim_col=5, hub_col=3, recess_outer=False,
    )
    # UPPER SNOW-CHAINED TIRE ON OUTER CALF/KNEE (x_off: 7..8, cz: 12.0)
    fill_sym_chained_wheel_x(
        grid, 7, 8, cy=10.0, cz=12.0,
        r_outer=3.25, r_rim=1.65, r_hub=0.75,
        tire_col=4, chain_col=6, rim_col=5, hub_col=3, recess_outer=False,
    )
    # Fender lip capping top of leg tires
    fill_sym_box(grid, 6, 8, 8, 12, 15, 15, 2)

    # --- HEAVY HYDRAULIC THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 3, 6, 9, 13, 15, 20, 5)
    fill_sym_box(grid, 4, 5, 10, 12, 16, 19, 0)  # Hollow interior
    fill_sym_box(grid, 3, 6, 13, 14, 16, 19, 1)  # Front orange thigh plate
    fill_sym_box(grid, 4, 5, 14, 14, 17, 18, 6)  # Silver hydraulic piston
    fill_sym_box(grid, 6, 6, 10, 12, 16, 19, 2)

    # --- WAIST / HEAVY BUMPER PELVIS (Z: 19..23) ---
    fill_sym_box(grid, 0, 6, 9, 13, 20, 22, 5)
    fill_sym_box(grid, 0, 5, 10, 12, 20, 22, 4)
    # Front waist skirts with high-vis yellow chevron belt
    fill_sym_box(grid, 2, 5, 13, 14, 19, 22, 1)
    fill_sym_box(grid, 2, 5, 14, 14, 21, 21, 3)
    fill_sym_box(grid, 3, 4, 14, 14, 20, 20, 9)
    # Center armored codpiece
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 2)
    fill_sym_box(grid, 0, 1, 15, 15, 20, 21, 6)
    fill_sym_box(grid, 0, 0, 15, 15, 21, 21, 3)
    # Hip armor blocks
    fill_sym_box(grid, 6, 7, 9, 13, 20, 22, 2)
    fill_sym_box(grid, 7, 7, 10, 12, 21, 21, 3)

    # --- BULKY ORANGE TRUCK CAB CHEST (Z: 23..33) ---
    # Core torso block (hollow inside)
    fill_sym_box(grid, 0, 6, 8, 14, 23, 32, 1)
    fill_sym_box(grid, 0, 5, 9, 13, 24, 31, 0)
    # Recessed gunmetal hydraulic abdomen
    fill_sym_box(grid, 0, 4, 13, 15, 23, 25, 5)
    fill_sym_box(grid, 0, 3, 15, 15, 23, 24, 4)
    fill_sym_box(grid, 1, 2, 15, 15, 24, 24, 6)
    # Prominent Jutting Snowplow Cab Chest (Y: 14..18, Z: 25..32)
    fill_sym_box(grid, 0, 5, 14, 17, 25, 31, 1)
    fill_sym_box(grid, 0, 4, 15, 16, 26, 30, 0)  # Hollow chest core
    fill_sym_box(grid, 0, 5, 18, 18, 25, 31, 1)  # Front cab fascia
    # ICY CYAN CAB WINDSHIELD ACROSS UPPER CHEST! (Z: 28..30, Y: 18)
    fill_sym_box(grid, 0, 4, 18, 18, 28, 30, 7)
    fill_sym_box(grid, 4, 4, 18, 18, 28, 30, 4)  # Outer cab A-pillars
    fill_sym_box(grid, 0, 0, 18, 18, 28, 30, 4)  # Center windshield divider
    # Cab roof visor & snow-white frost trim over chest windshield
    fill_sym_box(grid, 0, 5, 15, 18, 31, 32, 1)
    fill_sym_box(grid, 0, 4, 16, 18, 32, 32, 9)  # Frost-white cab roof trim
    fill_sym_box(grid, 2, 3, 18, 18, 31, 31, 3)  # Roof clearance amber markers
    # Silver Radiator Grille & Bright Warm Headlights across lower cab chest (Z: 25..27)
    fill_sym_box(grid, 0, 2, 18, 18, 25, 27, 4)
    fill_sym_box(grid, 0, 2, 18, 18, 26, 26, 6)  # Steel grille bar
    fill_sym_box(grid, 0, 1, 18, 18, 27, 27, 6)
    fill_sym_box(grid, 3, 4, 18, 18, 26, 27, 8)  # Bright glowing cab headlights!
    fill_sym_box(grid, 5, 5, 15, 18, 27, 27, 3)  # Yellow cab side stripe
    # Heavy steel front bumper bar under chest
    fill_sym_box(grid, 0, 4, 17, 18, 24, 24, 5)
    fill_sym_box(grid, 3, 4, 18, 18, 24, 24, 3)
    # Collar armor framing neck
    fill_sym_box(grid, 2, 5, 10, 13, 32, 33, 2)
    fill_sym_box(grid, 3, 4, 12, 13, 33, 33, 3)

    # --- SALT SPREADER HOPPER & BEACON BACKPACK (Y: 3..8, Z: 22..35) ---
    fill_sym_box(grid, 0, 5, 5, 8, 23, 33, 1)
    fill_sym_box(grid, 0, 4, 6, 7, 24, 32, 0)  # Hollow backpack interior
    # Sloped hopper back face & hazard stripes
    fill_sym_box(grid, 0, 4, 4, 5, 25, 32, 2)
    fill_sym_box(grid, 1, 4, 4, 4, 29, 29, 3)  # High-vis yellow rear stripe
    fill_sym_box(grid, 1, 3, 4, 4, 27, 27, 9)  # White reflective stripe
    # White salt/grit mound & steel grate crowning the backpack
    fill_sym_box(grid, 0, 4, 5, 7, 33, 33, 9)
    fill_sym_box(grid, 0, 3, 5, 6, 34, 34, 9)
    fill_sym_box(grid, 1, 1, 5, 7, 34, 34, 6)
    # Twin high-vis warning beacons flanking backpack top
    fill_sym_box(grid, 4, 5, 6, 7, 33, 34, 3)
    fill_sym_box(grid, 4, 4, 6, 7, 35, 35, 8)
    # Rotary salt-spreader thruster nozzle at lower back
    fill_sym_box(grid, 0, 2, 3, 5, 22, 25, 5)
    fill_sym_box(grid, 0, 1, 3, 3, 22, 24, 6)
    fill_sym_box(grid, 0, 0, 3, 3, 23, 23, 3)
    # Vertical chrome exhaust pipe on right back (+X)
    fill_box(grid, cx_r + 5, cx_r + 5, 7, 8, 30, 37, 6)
    fill_box(grid, cx_r + 5, cx_r + 6, 7, 8, 38, 38, 5)

    # --- HEAVY SALT-HOPPER & BEACON SHOULDER PAULDRONS (Z: 28..36, x_off: 7..11) ---
    fill_sym_box(grid, 6, 8, 10, 12, 29, 32, 5)   # Heavy shoulder axle bridge
    fill_sym_box(grid, 7, 11, 8, 14, 28, 34, 1)   # Massive orange pauldrons
    fill_sym_box(grid, 8, 10, 9, 13, 29, 33, 0)   # Hollow pauldron core
    fill_sym_box(grid, 7, 10, 10, 12, 29, 32, 5)  # Solid internal arm joint
    fill_sym_box(grid, 7, 11, 8, 14, 34, 34, 2)   # Deep orange-red top bevel
    fill_sym_box(grid, 8, 11, 14, 14, 30, 32, 3)  # Bold front yellow warning bar
    fill_sym_box(grid, 11, 11, 9, 13, 31, 32, 3)  # Outer side yellow hazard stripe
    fill_sym_box(grid, 11, 11, 9, 13, 29, 29, 9)  # White frost stripe
    # High-vis amber roof beacons mounted on top of shoulders!
    fill_sym_box(grid, 8, 10, 10, 12, 35, 35, 5)
    fill_sym_box(grid, 9, 10, 10, 12, 36, 36, 3)
    fill_sym_box(grid, 9, 9, 11, 11, 36, 36, 8)

    # --- ARMS & HYDRAULIC FOREARMS (Z: 15..29) ---
    fill_sym_box(grid, 8, 10, 10, 12, 23, 28, 5)  # Gunmetal hydraulic biceps
    fill_sym_box(grid, 9, 10, 10, 12, 25, 26, 6)  # Chrome piston band
    # Chunky armored forearms
    fill_sym_box(grid, 8, 11, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 9, 10, 10, 13, 18, 21, 0)  # Hollow forearm interior
    fill_sym_box(grid, 8, 11, 14, 14, 18, 21, 2)
    fill_sym_box(grid, 9, 10, 14, 14, 19, 20, 3)
    fill_sym_box(grid, 11, 11, 10, 13, 19, 20, 6)  # Steel outer forearm brace
    # Heavy mechanical fists
    fill_sym_box(grid, 8, 10, 10, 13, 15, 16, 4)
    fill_sym_box(grid, 8, 10, 13, 13, 15, 16, 5)

    # --- RIGHT ARM (+X, viewer's left): HYDRAULIC ICE-BREAKER RAM ---
    fill_box(grid, cx_r + 8, cx_r + 10, 13, 17, 15, 16, 5)   # Hydraulic mount
    fill_box(grid, cx_r + 9, cx_r + 10, 16, 20, 15, 17, 6)   # Chrome pile-bunker spike
    fill_box(grid, cx_r + 9, cx_r + 10, 19, 21, 15, 16, 9)   # Frosted steel tip
    fill_box(grid, cx_r + 10, cx_r + 11, 15, 17, 16, 18, 3)  # Yellow hazard knuckle guard

    # --- LEFT ARM (-X, viewer's right): MASSIVE CURVED SNOWPLOW RIOT SHIELD! ---
    # Heavy twin hydraulic push-arms anchoring shield solidly to left forearm (x: cx_l-11..cx_l-8 = 5..8)
    fill_box(grid, cx_l - 12, cx_l - 8, 12, 16, 17, 21, 5)   # Solid arm-to-shield bracket
    fill_box(grid, cx_l - 13, cx_l - 11, 14, 16, 18, 20, 6)  # Chrome hydraulic cylinders
    # Massive vertical curved snowplow shield (X: 0..7, Y: 16..20, Z: 10..27)
    # Faces forward (+Y) and curves outward (-X) so the entire curved orange blade is dramatic in Front 3/4 view!
    # Rear steel structural ribs (Y: 16)
    fill_box(grid, 1, 7, 16, 16, 12, 25, 5)
    fill_box(grid, 2, 6, 16, 16, 13, 24, 0)  # Hollow rear weight-saving window
    fill_box(grid, 2, 6, 16, 16, 18, 19, 5)  # Horizontal center brace
    fill_box(grid, 4, 4, 16, 16, 12, 25, 5)  # Vertical spine rib
    # Main curved orange snowplow shield body (Y: 17..18, Z: 12..25, X: 1..7)
    fill_box(grid, 1, 7, 17, 18, 12, 25, 1)
    # Concave forward-curling top lip (Z: 25..27, Y: 18..20) & bottom scoop (Z: 10..12, Y: 18..20)
    fill_box(grid, 1, 7, 18, 19, 25, 26, 1)
    fill_box(grid, 1, 7, 19, 20, 26, 27, 3)  # High-vis yellow upper snow-thrower crest!
    fill_box(grid, 3, 5, 20, 20, 27, 27, 9)  # Frost-white crest center
    fill_box(grid, 1, 7, 18, 19, 11, 12, 6)  # Gleaming steel lower plow cutting edge!
    fill_box(grid, 1, 7, 19, 20, 10, 11, 6)  # Jaws / scraper edge at bottom
    fill_box(grid, 1, 2, 20, 20, 10, 11, 9)  # Snow frost on cutting corner
    # Swept-forward outer wing edge (-X edge, X: 0..1) with steel blade trim
    fill_box(grid, 0, 1, 18, 19, 11, 26, 2)
    fill_box(grid, 0, 0, 19, 20, 11, 25, 6)  # Outer vertical steel cutting edge!
    # High-vis yellow & white hazard chevrons across the shield front face (Y: 18)
    fill_box(grid, 2, 6, 18, 18, 22, 23, 3)
    fill_box(grid, 2, 6, 18, 18, 14, 15, 3)
    fill_box(grid, 3, 5, 18, 18, 18, 19, 9)  # White plow emblem center
    fill_box(grid, 4, 4, 18, 18, 17, 20, 9)
    # Recessed armored viewing slit near upper shield
    fill_box(grid, 2, 6, 18, 18, 24, 24, 4)
    fill_box(grid, 3, 5, 18, 18, 24, 24, 7)  # Icy cyan viewport slit!
    # Yellow guide-rod marker spike on top outer corner of shield
    fill_box(grid, 0, 0, 19, 19, 27, 28, 3)
    fill_box(grid, 0, 0, 19, 19, 29, 29, 9)

    # --- HEROIC WINTER-VISOR HEAD (Z: 33..40) ---
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 5)  # Neck
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 1)   # Safety orange helmet
    fill_sym_box(grid, 0, 3, 10, 14, 38, 39, 1)  # Overhanging snow-helmet brow
    fill_sym_box(grid, 0, 2, 14, 15, 38, 38, 9)  # Frost-white visor trim
    # Icy cyan snow-goggle visor
    fill_sym_box(grid, 0, 2, 14, 14, 36, 37, 7)
    # Brushed steel faceplate respirator
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 6)
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 5)
    # Ear pods
    fill_sym_box(grid, 3, 3, 10, 12, 35, 37, 2)
    fill_sym_box(grid, 3, 3, 11, 11, 36, 37, 3)
    # High-vis yellow V-crest & bright warm beacon forehead jewel
    fill_sym_box(grid, 0, 0, 15, 15, 38, 39, 8)
    fill_sym_box(grid, 1, 1, 14, 15, 39, 40, 3)
    fill_sym_box(grid, 2, 3, 13, 14, 39, 40, 3)

    # Clear completely enclosed internal partition walls between chest, torso & backpack
    fill_sym_box(grid, 0, 4, 6, 17, 25, 30, 0)
    fill_sym_box(grid, 0, 4, 6, 13, 24, 31, 0)
    # Clear unseen interior wall behind shield front plate
    fill_box(grid, 2, 6, 17, 17, 13, 24, 0)

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
    v_a = export_vox(model_a, "snowplow_a.vox")
    v_b = export_vox(model_b, "snowplow_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SNOWPLOW TRUCK -> SNOWPLOW SHIELD ROBOT",
        "1. HEAVY SNOWPLOW TRUCK",
        "2. SNOWPLOW SHIELD ROBOT",
        "preview_snowplow.png",
        yaw_a=40, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"snowplow: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
