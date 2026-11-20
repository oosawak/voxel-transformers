import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (36, 152, 58, 255),    # Vibrant Tractor Green (Bonnet, Cab Roof, Chest, Armor)
    2: (22, 104, 40, 255),    # Deep Forest Green (Shading, Fenders, Lower Armor)
    3: (248, 204, 34, 255),   # Sunny Harvest Yellow (Wheel Rims, Hood Stripe, Crest)
    4: (48, 52, 62, 255),     # Heavy Rubber Tire Charcoal / Exhaust Smokestack
    5: (88, 96, 110, 255),    # Gunmetal Steel (Chassis, Engine Block, Treads, Joints)
    6: (174, 186, 200, 255),  # Brushed Chrome / Silver (Grille Bars, Hubs, Blade)
    7: (88, 206, 240, 255),   # Bright Cyan Cab Glass / Robot Visor
    8: (255, 238, 128, 255),  # Warm Headlight Glow / Core Light
    9: (228, 58, 46, 255),    # Signal Barn Red (Tail Lights, Beacon, Crest Jewel)
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


def fill_sym_wheel_x(
    grid, x_off0, x_off1, cy, cz, r_outer, r_rim, r_hub,
    tire_col=4, tread_col=5, rim_col=3, hub_col=6, recess_outer=True,
):
    """Draw a pair of symmetrical treaded tractor wheels along the X axis."""
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

            # Determine outer tread lug pattern for authentic tractor tire look
            angle = np.arctan2(dz, dy)
            lug = int(np.floor((angle + np.pi) / (np.pi / 6.0))) % 2 == 0

            for x_off in range(x_off0, x_off1 + 1):
                is_outer_face = (x_off == x_off1)
                is_inner_face = (x_off == x_off0)
                if dist <= r_hub:
                    col = hub_col if (is_outer_face or is_inner_face) else 5
                elif dist <= r_rim:
                    if recess_outer and is_outer_face and dist > r_hub + 0.6:
                        # Subtle recess on the outer rim for crisp 3D depth
                        continue
                    col = rim_col
                else:
                    # Tire rubber & raised alternating tread lugs near outer circumference
                    if dist >= r_outer - 0.95 and lug and (x_off in (x_off0, x_off1) or (y + z) % 2 == 0):
                        col = tread_col
                    else:
                        col = tire_col
                xl = cx_l - x_off
                xr = cx_r + x_off
                if 0 <= xl < X:
                    grid[xl, y, z] = col
                if 0 <= xr < X:
                    grid[xr, y, z] = col


# ==========================================
# FORM A: FARM TRACTOR (20 x 30 x 21)
# ==========================================
def build_a():
    grid = np.zeros((20, 30, 21), dtype=np.uint8)
    cx_r = grid.shape[0] // 2  # +X right side of tractor (10)

    # --- MASSIVE TREADED REAR WHEELS (Y: 3..13, Z: 0..10, x_off: 5..8) ---
    fill_sym_wheel_x(
        grid, 5, 8, cy=8.0, cz=5.0,
        r_outer=5.35, r_rim=3.15, r_hub=1.25,
        tire_col=4, tread_col=5, rim_col=3, hub_col=6, recess_outer=True,
    )
    # Yellow wheel rim accents & raised chrome axle cap on outer face
    fill_sym_box(grid, 8, 8, 8, 8, 5, 5, 6)
    fill_sym_box(grid, 7, 7, 7, 9, 4, 6, 3)
    fill_sym_box(grid, 7, 8, 8, 8, 5, 5, 6)
    # Hollow unseen inner wheel core slightly to keep voxel budget crisp
    fill_sym_box(grid, 6, 6, 6, 10, 3, 7, 0)

    # --- SMALL STEERABLE FRONT WHEELS (Y: 21..26, Z: 0..5, x_off: 4..6) ---
    fill_sym_wheel_x(
        grid, 4, 6, cy=23.5, cz=2.5,
        r_outer=2.85, r_rim=1.65, r_hub=0.75,
        tire_col=4, tread_col=4, rim_col=3, hub_col=6, recess_outer=False,
    )

    # --- HEAVY CHASSIS, AXLES & ENGINE BLOCK (Y: 2..28, Z: 2..7) ---
    # Rear axle housing connecting the two massive rear wheels
    fill_sym_box(grid, 0, 5, 7, 9, 4, 6, 5)
    fill_sym_box(grid, 0, 4, 6, 10, 4, 6, 4)
    # Rear 3-point hitch & tow bar (Y: 1..5, Z: 3..6)
    fill_sym_box(grid, 0, 2, 3, 6, 4, 5, 5)
    fill_sym_box(grid, 2, 2, 1, 3, 3, 4, 5)
    fill_sym_box(grid, 0, 1, 1, 2, 3, 4, 6)
    fill_sym_box(grid, 0, 0, 1, 1, 5, 6, 9)  # Red hitch pin
    # Front steering axle & steering linkage
    fill_sym_box(grid, 0, 4, 23, 24, 2, 3, 5)
    fill_sym_box(grid, 0, 2, 22, 25, 3, 4, 4)
    # Main longitudinal engine chassis beam
    fill_sym_box(grid, 0, 2, 10, 26, 4, 6, 5)
    fill_sym_box(grid, 0, 1, 12, 25, 3, 4, 4)
    # Exposed metallic engine cylinders & pipes under hood sides
    for ey in (16, 19, 22):
        fill_sym_box(grid, 2, 2, ey, ey + 1, 5, 6, 6)
    fill_sym_box(grid, 2, 2, 17, 24, 4, 4, 4)
    # Side boarding steps & fuel tank between front and rear wheels
    fill_sym_box(grid, 3, 4, 14, 16, 4, 5, 4)
    fill_sym_box(grid, 3, 4, 14, 15, 3, 3, 5)
    fill_sym_box(grid, 4, 4, 14, 15, 3, 3, 3)  # Yellow safety step edge
    # Front heavy counterweight bumper
    fill_sym_box(grid, 0, 2, 27, 29, 4, 5, 5)
    fill_sym_box(grid, 0, 1, 29, 29, 4, 5, 4)
    fill_sym_box(grid, 2, 2, 28, 29, 4, 5, 3)  # Yellow bumper corners

    # --- LONG NARROW ENGINE HOOD / BONNET (Y: 14..28, Z: 7..11, x_off: 0..2) ---
    fill_sym_box(grid, 0, 2, 14, 27, 7, 11, 1)
    # Hollow unseen hood interior to keep voxel count sleek
    fill_sym_box(grid, 0, 1, 15, 25, 7, 10, 0)
    # Tapered front nose of bonnet
    fill_sym_box(grid, 0, 2, 28, 28, 6, 10, 1)
    fill_sym_box(grid, 0, 1, 27, 27, 11, 11, 1)
    # Iconic sunny yellow side stripe along the green bonnet!
    fill_sym_box(grid, 2, 2, 14, 27, 8, 8, 3)
    fill_sym_box(grid, 2, 2, 14, 26, 7, 7, 2)  # Deep green lower hood crease
    # Center raised ridge on top of hood
    fill_sym_box(grid, 0, 0, 15, 26, 11, 11, 2)
    # Dark front radiator grille with silver slats & yellow emblem
    fill_sym_box(grid, 0, 1, 28, 28, 6, 9, 4)
    fill_sym_box(grid, 0, 1, 28, 28, 7, 7, 6)
    fill_sym_box(grid, 0, 1, 28, 28, 9, 9, 6)
    fill_sym_box(grid, 0, 0, 28, 28, 10, 10, 3)  # Front hood badge
    # Side engine louver vents
    for vy in (22, 24, 26):
        fill_sym_box(grid, 2, 2, vy, vy, 9, 10, 4)
    # Twin bright headlights on side stalks flanking radiator
    fill_sym_box(grid, 3, 3, 25, 26, 8, 9, 4)
    fill_sym_box(grid, 3, 3, 27, 27, 8, 9, 8)  # Bright glowing lenses
    # Air intake pre-cleaner on front hood
    fill_box(grid, cx_r - 2, cx_r - 2, 23, 23, 12, 13, 4)
    fill_box(grid, cx_r - 2, cx_r - 2, 23, 23, 14, 14, 6)

    # --- TALL VERTICAL BLACK EXHAUST SMOKESTACK (+X side of hood) ---
    # Anchored solidly into right side of engine hood (x = cx_r + 2 = 12)
    fill_box(grid, cx_r + 2, cx_r + 2, 18, 19, 10, 14, 4)
    fill_box(grid, cx_r + 3, cx_r + 3, 18, 19, 11, 14, 4)
    fill_box(grid, cx_r + 3, cx_r + 3, 18, 19, 12, 12, 6)  # Silver heatshield clamp
    fill_box(grid, cx_r + 3, cx_r + 3, 18, 18, 15, 19, 4)  # Tall vertical pipe
    fill_box(grid, cx_r + 3, cx_r + 4, 18, 18, 20, 20, 6)  # Curved rain-cap tip

    # --- CURVED REAR WHEEL FENDERS (Y: 2..14, Z: 8..12) ---
    fill_sym_box(grid, 4, 8, 4, 12, 11, 11, 1)
    fill_sym_box(grid, 4, 8, 5, 11, 12, 12, 1)
    fill_sym_box(grid, 5, 8, 2, 3, 9, 10, 2)   # Rear mudflap curve
    fill_sym_box(grid, 5, 8, 13, 14, 9, 10, 2)  # Front fender lip
    fill_sym_box(grid, 6, 7, 2, 2, 10, 10, 9)  # Red rear fender tail lights
    fill_sym_box(grid, 8, 8, 6, 10, 12, 12, 3)  # Yellow fender trim stripe

    # --- ELEVATED REAR OPERATOR CAB & ROOF CANOPY (Y: 5..14, Z: 7..19) ---
    # Lower cab deck & rear body
    fill_sym_box(grid, 0, 4, 5, 14, 7, 11, 2)
    fill_sym_box(grid, 0, 3, 6, 13, 8, 10, 0)  # Hollow interior
    fill_sym_box(grid, 0, 4, 5, 5, 7, 11, 1)
    fill_sym_box(grid, 3, 4, 5, 5, 9, 10, 9)   # Rear cab tail lights
    # Cab glass enclosure (Z: 12..16) with hollow interior + driver seat
    fill_sym_box(grid, 0, 3, 6, 14, 12, 16, 7)
    fill_sym_box(grid, 0, 2, 7, 13, 12, 16, 0)  # Hollow cab interior
    # Driver seat & steering column visible inside glass cab
    fill_sym_box(grid, 0, 1, 8, 9, 11, 13, 4)
    fill_sym_box(grid, 0, 1, 7, 8, 13, 15, 4)
    fill_sym_box(grid, 0, 0, 12, 13, 11, 13, 5)
    fill_sym_box(grid, 0, 1, 12, 12, 14, 14, 4)
    # Dark structural cab corner pillars (4 corners)
    fill_sym_box(grid, 3, 3, 6, 6, 12, 16, 4)
    fill_sym_box(grid, 3, 3, 14, 14, 12, 16, 4)
    fill_sym_box(grid, 3, 3, 10, 10, 12, 16, 4)  # Door frame mullion
    # Elevated Green Cab Roof Canopy (Z: 17..18)
    fill_sym_box(grid, 0, 4, 5, 15, 17, 17, 1)
    fill_sym_box(grid, 0, 3, 6, 14, 18, 18, 1)
    fill_sym_box(grid, 0, 3, 15, 15, 17, 17, 3)  # Yellow front sun-visor trim
    fill_sym_box(grid, 3, 3, 15, 15, 17, 17, 8)  # Twin cab roof work lights
    fill_sym_box(grid, 0, 0, 11, 12, 19, 19, 9)  # Red roof hazard beacon

    return grid


# ==========================================
# FORM B: TRACTOR HARVEST ROBOT (34 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 42), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 16 (-X robot left)
    cx_r = grid.shape[0] // 2      # 17 (+X robot right)

    # --- FEET & HEAVY PLOW-TREAD BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 3, 7, 8, 16, 0, 1, 4)   # Heavy dark rubber sole
    fill_sym_box(grid, 3, 7, 7, 9, 0, 2, 5)    # Steel heel spur
    fill_sym_box(grid, 3, 7, 11, 17, 1, 2, 1)  # Green armored boot vamp
    fill_sym_box(grid, 4, 6, 13, 17, 2, 3, 2)  # Toe cap armor
    fill_sym_box(grid, 4, 6, 17, 17, 1, 2, 3)  # Sunny yellow toe bumper
    # Small Front Tractor Wheels mounted on outer ankles (x_off: 7..8, Y: 9..13, Z: 1..5)
    fill_sym_wheel_x(
        grid, 7, 8, cy=11.0, cz=3.0,
        r_outer=2.45, r_rim=1.35, r_hub=0.65,
        tire_col=4, tread_col=4, rim_col=3, hub_col=6, recess_outer=False,
    )

    # --- LOWER LEGS & HUGE WHEEL-CALVED SHINS (Z: 3..15) ---
    # Core shin frame
    fill_sym_box(grid, 3, 6, 9, 14, 3, 14, 2)
    fill_sym_box(grid, 4, 5, 10, 13, 4, 13, 0)  # Hollow interior for crisp count
    fill_sym_box(grid, 3, 6, 13, 14, 4, 13, 1)  # Front green shin plate
    fill_sym_box(grid, 4, 5, 14, 14, 5, 11, 3)  # Yellow front shin stripe
    fill_sym_box(grid, 3, 3, 10, 13, 4, 13, 5)  # Inner leg gunmetal hydraulics
    # Heavy knee guards
    fill_sym_box(grid, 3, 6, 14, 15, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 15, 16, 13, 15, 3)
    fill_sym_box(grid, 4, 5, 15, 15, 14, 14, 6)
    # HUGE REAR TRACTOR WHEELS ON OUTER CALVES (x_off: 7..9, Y: 6..14, Z: 5..13)
    fill_sym_wheel_x(
        grid, 7, 9, cy=10.0, cz=9.5,
        r_outer=4.45, r_rim=2.55, r_hub=1.05,
        tire_col=4, tread_col=5, rim_col=3, hub_col=6, recess_outer=True,
    )
    fill_sym_box(grid, 9, 9, 10, 10, 9, 10, 6)  # Protruding chrome hub cap
    # Curved green rear fender hooding the top of each leg-wheel
    fill_sym_box(grid, 6, 9, 7, 13, 14, 14, 1)
    fill_sym_box(grid, 7, 9, 6, 7, 12, 13, 2)
    fill_sym_box(grid, 7, 8, 6, 6, 13, 13, 9)  # Red tail light accent on leg fender

    # --- MUSCULAR MECHANICAL THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 3, 6, 9, 13, 15, 20, 5)
    fill_sym_box(grid, 4, 5, 10, 12, 16, 19, 0)  # Hollow interior
    fill_sym_box(grid, 3, 6, 13, 14, 16, 19, 2)  # Deep green front thigh armor
    fill_sym_box(grid, 4, 5, 14, 14, 17, 18, 6)  # Chrome hydraulic piston
    fill_sym_box(grid, 6, 6, 10, 12, 16, 19, 1)  # Outer thigh green plate

    # --- WAIST / HEAVY CHASSIS PELVIS (Z: 19..23) ---
    fill_sym_box(grid, 0, 6, 9, 13, 20, 22, 5)
    fill_sym_box(grid, 0, 5, 10, 12, 20, 22, 4)
    # Front waist armor skirts
    fill_sym_box(grid, 2, 5, 13, 14, 19, 22, 1)
    fill_sym_box(grid, 2, 5, 14, 14, 21, 21, 3)  # Yellow waist belt
    # Heroic center codpiece with red hitch-jewel
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 1)
    fill_sym_box(grid, 0, 1, 15, 15, 20, 21, 3)
    fill_sym_box(grid, 0, 0, 15, 15, 21, 21, 9)
    # Side hip armor guards
    fill_sym_box(grid, 6, 7, 9, 13, 20, 22, 2)
    fill_sym_box(grid, 7, 7, 10, 12, 21, 21, 3)

    # --- TORSO & PROMINENT TRACTOR ENGINE BONNET CHEST (Z: 23..33) ---
    # Core torso block
    fill_sym_box(grid, 0, 6, 8, 14, 23, 32, 1)
    fill_sym_box(grid, 0, 5, 9, 13, 24, 31, 0)  # Hollow torso core
    # Recessed gunmetal mechanical abdomen
    fill_sym_box(grid, 0, 4, 13, 14, 23, 25, 5)
    fill_sym_box(grid, 0, 3, 14, 14, 23, 24, 4)
    fill_sym_box(grid, 1, 2, 14, 14, 24, 24, 6)  # Silver engine pipes
    # Prominent Jutting Green Tractor Bonnet Chest! (Y: 14..18, Z: 25..32)
    fill_sym_box(grid, 0, 4, 14, 17, 25, 31, 1)
    fill_sym_box(grid, 0, 3, 15, 16, 26, 30, 0)  # Hollow bonnet chest core
    fill_sym_box(grid, 0, 3, 14, 17, 32, 32, 1)  # Sloped upper hood deck
    fill_sym_box(grid, 0, 4, 18, 18, 25, 30, 1)  # Front hood fascia
    # Iconic sunny yellow bonnet stripes along chest flanks!
    fill_sym_box(grid, 4, 4, 14, 18, 27, 27, 3)
    fill_sym_box(grid, 4, 4, 14, 17, 26, 26, 2)
    fill_sym_box(grid, 0, 0, 14, 17, 32, 32, 2)  # Center hood ridge
    # Iconic Tractor Radiator Grille on center chest (Y: 18, Z: 25..30)
    fill_sym_box(grid, 0, 2, 18, 18, 25, 29, 4)
    fill_sym_box(grid, 0, 2, 18, 18, 26, 26, 6)  # Chrome grille slat
    fill_sym_box(grid, 0, 2, 18, 18, 28, 28, 6)  # Chrome grille slat
    fill_sym_box(grid, 0, 1, 18, 18, 30, 30, 3)  # Sunny yellow emblem bar
    fill_sym_box(grid, 0, 0, 18, 18, 29, 30, 8)  # Glowing chest core light
    # Lower chest bumper bar (from Form A front counterweight)
    fill_sym_box(grid, 0, 3, 17, 18, 24, 24, 5)
    fill_sym_box(grid, 3, 3, 18, 18, 24, 24, 3)
    # Twin Bright Tractor Headlights flanking the bonnet chest!
    fill_sym_box(grid, 5, 5, 15, 16, 28, 30, 4)
    fill_sym_box(grid, 5, 5, 17, 17, 28, 29, 8)  # Glowing warm headlights
    # Collar armor framing neck
    fill_sym_box(grid, 2, 5, 10, 13, 32, 33, 2)
    fill_sym_box(grid, 3, 5, 12, 13, 33, 33, 3)

    # --- TALL VERTICAL BLACK EXHAUST SMOKESTACK ON RIGHT SHOULDER (+X) ---
    # Anchored solidly into right collar/upper back (X = cx_r + 5..6 = 22..23)
    fill_box(grid, cx_r + 5, cx_r + 6, 9, 10, 32, 36, 4)  # Heavy muffler drum
    fill_box(grid, cx_r + 5, cx_r + 6, 9, 10, 34, 34, 6)  # Chrome heatshield band
    fill_box(grid, cx_r + 6, cx_r + 6, 9, 10, 37, 40, 4)  # Tall exhaust stack
    fill_box(grid, cx_r + 6, cx_r + 7, 9, 10, 41, 41, 6)  # Angled chrome tip

    # --- OPERATOR CAB ROOF BACKPACK (Y: 3..8, Z: 22..34) ---
    fill_sym_box(grid, 0, 5, 5, 8, 23, 33, 1)
    fill_sym_box(grid, 0, 4, 6, 7, 24, 32, 0)  # Hollow backpack interior
    # Folded Cab Glass Window Panes & Dark Pillars visible from rear!
    fill_sym_box(grid, 0, 4, 4, 5, 25, 31, 7)  # Cyan cab rear/front glass
    fill_sym_box(grid, 4, 4, 4, 5, 25, 31, 4)  # Outer cab pillars
    fill_sym_box(grid, 0, 0, 4, 5, 25, 31, 4)  # Center cab mullion
    # Cab Roof Canopy & Work Lights crowning the backpack
    fill_sym_box(grid, 0, 5, 4, 8, 32, 33, 1)
    fill_sym_box(grid, 0, 4, 4, 4, 33, 33, 3)  # Yellow canopy edge
    fill_sym_box(grid, 4, 4, 4, 4, 32, 32, 9)  # Red tail lights
    fill_sym_box(grid, 0, 0, 5, 6, 34, 34, 9)  # Red roof warning beacon
    # Lower 3-point hitch thrusters at bottom of backpack
    fill_sym_box(grid, 1, 3, 3, 5, 22, 24, 5)
    fill_sym_box(grid, 2, 2, 3, 3, 22, 23, 6)

    # --- COLOSSAL REAR-WHEEL SHOULDER PAULDRONS (Z: 27..38, x_off: 7..13) ---
    # Heavy axle bridge connecting torso to wheel shoulders
    fill_sym_box(grid, 6, 9, 10, 12, 29, 32, 5)
    fill_sym_box(grid, 7, 8, 10, 12, 30, 31, 4)
    # MASSIVE TREADED TRACTOR WHEELS AS SHOULDERS! (x_off: 9..12, Y: 6..16, Z: 27..37)
    fill_sym_wheel_x(
        grid, 9, 12, cy=11.0, cz=32.0,
        r_outer=4.95, r_rim=2.85, r_hub=1.15,
        tire_col=4, tread_col=5, rim_col=3, hub_col=6, recess_outer=True,
    )
    fill_sym_box(grid, 12, 12, 11, 11, 32, 32, 6)  # Center chrome wheel cap
    # Hollow unseen inner core of massive shoulder tires
    fill_sym_box(grid, 10, 11, 9, 13, 30, 34, 0)
    # Re-anchor inner axle through the hollow cavity so arm connects solidly
    fill_sym_box(grid, 9, 11, 10, 12, 30, 32, 5)
    # Green Curved Tractor Fender Armor arching over top of each wheel-shoulder!
    fill_sym_box(grid, 8, 13, 8, 14, 37, 37, 1)
    fill_sym_box(grid, 8, 12, 9, 13, 38, 38, 1)
    fill_sym_box(grid, 9, 13, 14, 14, 36, 37, 3)  # Yellow front fender trim
    fill_sym_box(grid, 9, 13, 7, 7, 35, 36, 2)    # Rear fender curve
    fill_sym_box(grid, 10, 11, 7, 7, 36, 36, 9)   # Rear shoulder red light

    # --- ARMS, FOREARMS & HARVESTER PLOW-BLADE (Z: 15..29) ---
    # Upper arms descending solidly from inside the wheel-shoulder hubs
    fill_sym_box(grid, 9, 11, 10, 12, 23, 29, 5)
    fill_sym_box(grid, 10, 11, 10, 12, 25, 27, 4)  # Elbow/bicep piston dark band
    # Blocky armored forearms
    fill_sym_box(grid, 9, 12, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 10, 11, 10, 13, 18, 21, 0)  # Hollow forearm interior
    fill_sym_box(grid, 9, 12, 14, 14, 18, 21, 2)   # Front forearm guard
    fill_sym_box(grid, 10, 11, 14, 14, 19, 20, 3)  # Yellow forearm stripe
    # Small tractor wheel / hubcap accent on outer forearms (x_off: 12..13)
    fill_sym_wheel_x(
        grid, 12, 13, cy=11.5, cz=19.5,
        r_outer=2.05, r_rim=1.15, r_hub=0.55,
        tire_col=4, tread_col=4, rim_col=3, hub_col=6, recess_outer=False,
    )
    # Heavy mechanical fists
    fill_sym_box(grid, 9, 11, 10, 13, 15, 16, 4)
    fill_sym_box(grid, 9, 11, 13, 13, 15, 16, 5)  # Steel knuckles

    # RIGHT HAND (+X, viewer's left): HARVESTER PLOW-CLAW / SCYTHE BLADE
    # Attached directly into right fist (X = cx_r + 9..11 = 26..28)
    fill_box(grid, cx_r + 9, cx_r + 11, 13, 17, 15, 16, 5)   # Weapon hilt/mount
    fill_box(grid, cx_r + 10, cx_r + 11, 16, 22, 15, 17, 1)  # Green blade spine
    fill_box(grid, cx_r + 10, cx_r + 11, 17, 23, 14, 15, 6)  # Gleaming silver plow edge
    fill_box(grid, cx_r + 10, cx_r + 11, 21, 23, 16, 18, 6)  # Hooked harvester tip
    fill_box(grid, cx_r + 11, cx_r + 11, 17, 21, 16, 16, 3)  # Yellow harvest accent
    fill_box(grid, cx_r + 10, cx_r + 11, 15, 18, 18, 19, 6)  # Upper twin prong

    # LEFT FOREARM (-X, viewer's right): COMPACT DOZER-PLOW BUCKLER
    fill_box(grid, cx_l - 13, cx_l - 12, 12, 16, 17, 21, 2)
    fill_box(grid, cx_l - 13, cx_l - 13, 13, 15, 18, 20, 1)
    fill_box(grid, cx_l - 13, cx_l - 12, 16, 17, 17, 21, 6)  # Silver plow teeth edge
    fill_box(grid, cx_l - 13, cx_l - 13, 14, 15, 19, 19, 3)

    # --- HEROIC HEAD WITH CAB-ROOF HELMET & GLOWING VISOR (Z: 33..41) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 5)
    # Main head block
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 1)
    # Cab-roof overhanging helmet visor brim
    fill_sym_box(grid, 0, 3, 10, 14, 38, 39, 1)
    fill_sym_box(grid, 0, 2, 14, 15, 38, 38, 3)  # Yellow visor trim
    # Glowing bright cyan wrap-around cab-glass visor!
    fill_sym_box(grid, 0, 2, 14, 14, 36, 37, 7)
    # Brushed chrome faceplate mouthguard
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 6)
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 5)
    # Side helmet ear pods
    fill_sym_box(grid, 3, 3, 10, 12, 35, 37, 2)
    fill_sym_box(grid, 3, 3, 11, 11, 36, 37, 3)
    # Iconic Harvest-Yellow V-Crest & Red Forehead Beacon Jewel
    fill_sym_box(grid, 0, 0, 15, 15, 38, 39, 9)  # Red beacon jewel
    fill_sym_box(grid, 1, 1, 14, 15, 39, 40, 3)  # Inner V-horn
    fill_sym_box(grid, 2, 3, 13, 14, 40, 41, 3)  # Swept outer V-horn tips

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
    v_a = export_vox(model_a, "tractor_a.vox")
    v_b = export_vox(model_b, "tractor_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: FARM TRACTOR -> TRACTOR HARVEST ROBOT",
        "1. FARM TRACTOR",
        "2. TRACTOR HARVEST ROBOT",
        "preview_tractor.png",
        yaw_a=42, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"tractor: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
