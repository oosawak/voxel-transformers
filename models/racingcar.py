import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (222, 34, 42, 255),    # Vibrant Racing Crimson Red (Chassis, Nosecone, Sidepods, Armor)
    2: (146, 20, 28, 255),    # Deep Maroon Red (Shading, Undercut, Lower Armor)
    3: (244, 246, 252, 255),  # Crisp Racing White (Center Stripe, Number Plate, Wing Planes)
    4: (36, 40, 48, 255),     # Deep Slick-Tire Rubber Charcoal / Carbon Floor
    5: (92, 100, 114, 255),   # Gunmetal Carbon-Steel (Suspension, Wishbones, Exhaust, Joints)
    6: (210, 218, 228, 255),  # Machined Silver / Chrome (Wheel Hubs, Exhaust Tips, Faceplate)
    7: (78, 214, 248, 255),   # Bright Cyan Helmet / Cockpit Visor
    8: (250, 198, 42, 255),   # Championship Gold / Racing Yellow (Rims, Wing Endplates, Crest)
    9: (255, 118, 36, 255),   # Turbo Exhaust Afterburner Orange (Thrusters, Core, Rain Light)
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


def fill_sym_slick_wheel_x(
    grid, x_off0, x_off1, cy, cz, r_outer, r_rim, r_hub,
    tire_col=4, wall_col=5, rim_col=8, hub_col=6, recess_outer=True, hollow_inner=False,
):
    """Draw a pair of wide smooth Formula/GT racing slick wheels along the X axis."""
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

            for x_off in range(x_off0, x_off1 + 1):
                is_outer_face = (x_off == x_off1)
                is_inner_face = (x_off == x_off0)
                if hollow_inner and not is_outer_face and not is_inner_face and dist <= r_outer - 1.15:
                    continue

                if dist <= r_hub:
                    col = hub_col if (is_outer_face or is_inner_face) else 5
                elif dist <= r_rim:
                    if recess_outer and is_outer_face and dist > r_hub + 0.55:
                        continue
                    col = rim_col
                else:
                    # Smooth slick rubber with subtle racing sidewall ring on outer face
                    if is_outer_face and r_rim < dist <= r_rim + 0.65:
                        col = wall_col
                    else:
                        col = tire_col

                xl = cx_l - x_off
                xr = cx_r + x_off
                if 0 <= xl < X:
                    grid[xl, y, z] = col
                if 0 <= xr < X:
                    grid[xr, y, z] = col


# ==========================================
# FORM A: FORMULA / GT RACING CAR (22 x 42 x 14)
# ==========================================
def build_a():
    grid = np.zeros((22, 42, 14), dtype=np.uint8)

    # --- WIDE CHUNKY REAR SLICK TIRES (Y: 4..11, Z: 0..7, x_off: 6..10) ---
    fill_sym_slick_wheel_x(
        grid, 6, 10, cy=7.5, cz=3.5,
        r_outer=3.85, r_rim=2.35, r_hub=0.95,
        tire_col=4, wall_col=5, rim_col=8, hub_col=6,
        recess_outer=True, hollow_inner=True,
    )
    # Keep inner axle core solid for suspension linkage
    fill_sym_box(grid, 6, 8, 7, 8, 3, 4, 5)
    fill_sym_box(grid, 9, 9, 7, 8, 3, 4, 6)  # Center-lock chrome wheel nut inside gold rim

    # --- WIDE FRONT SLICK TIRES (Y: 28..35, Z: 0..6, x_off: 6..9) ---
    fill_sym_slick_wheel_x(
        grid, 6, 9, cy=31.5, cz=3.0,
        r_outer=3.35, r_rim=1.95, r_hub=0.85,
        tire_col=4, wall_col=5, rim_col=8, hub_col=6,
        recess_outer=True, hollow_inner=True,
    )
    fill_sym_box(grid, 6, 7, 31, 32, 3, 3, 5)
    fill_sym_box(grid, 8, 8, 31, 32, 3, 3, 6)  # Front chrome center-lock nut

    # --- CARBON FLOOR UNDERTRAY, DIFFUSER & SUSPENSION WISHBONES (Z: 1..4) ---
    fill_sym_box(grid, 0, 5, 5, 29, 1, 1, 4)
    fill_sym_box(grid, 0, 3, 6, 26, 2, 2, 4)
    fill_sym_box(grid, 0, 2, 7, 25, 2, 2, 0)  # Hollow internal floor mass
    # Rear diffuser & glowing turbo exhaust port (Y: 2..5, Z: 1..4)
    fill_sym_box(grid, 0, 3, 3, 5, 1, 3, 5)
    fill_sym_box(grid, 2, 3, 2, 3, 1, 2, 4)   # Diffuser strakes
    fill_sym_box(grid, 0, 1, 2, 3, 2, 3, 9)   # Glowing orange turbo exhaust
    fill_sym_box(grid, 0, 0, 2, 2, 4, 4, 9)   # Rear F1 LED rain light
    # Rear suspension wishbones & driveshafts
    fill_sym_box(grid, 3, 6, 7, 8, 3, 4, 5)
    fill_sym_box(grid, 3, 5, 6, 9, 2, 2, 5)
    # Front double-wishbone suspension arms
    fill_sym_box(grid, 2, 6, 31, 32, 2, 3, 5)
    fill_sym_box(grid, 2, 5, 30, 31, 4, 4, 5)

    # --- SCULPTED SIDEPODS & RADIATOR INTAKES (Y: 11..25, Z: 2..6) ---
    fill_sym_box(grid, 3, 6, 12, 24, 2, 5, 1)
    fill_sym_box(grid, 4, 5, 13, 23, 3, 4, 0)  # Hollow sidepod interior
    fill_sym_box(grid, 3, 5, 12, 23, 6, 6, 1)  # Sloped top deck of sidepod
    fill_sym_box(grid, 5, 6, 11, 24, 2, 2, 2)  # Deep maroon lower undercut
    fill_sym_box(grid, 6, 6, 13, 23, 4, 4, 3)  # Crisp white racing side stripe
    fill_sym_box(grid, 6, 6, 14, 16, 5, 5, 8)  # Championship gold sponsor trim
    # Sidepod cooling mouth intake (front of sidepod at Y: 25)
    fill_sym_box(grid, 3, 5, 25, 25, 3, 5, 4)
    fill_sym_box(grid, 3, 5, 25, 25, 5, 5, 2)
    fill_sym_box(grid, 6, 6, 24, 25, 3, 5, 1)  # Outer intake bargeboard
    # Tapered rear Coke-bottle engine bodywork (Y: 5..12)
    fill_sym_box(grid, 0, 3, 6, 12, 3, 5, 1)
    fill_sym_box(grid, 0, 2, 7, 11, 4, 4, 0)  # Hollow engine bay
    fill_sym_box(grid, 0, 2, 5, 12, 6, 6, 1)
    fill_sym_box(grid, 2, 3, 6, 10, 3, 4, 2)  # Maroon rear cowling shade
    # Twin side exhaust pipes peeking near rear deck
    fill_sym_box(grid, 2, 2, 6, 9, 5, 5, 6)

    # --- CENTRAL MONOCOQUE, COCKPIT & AIRBOX ROLL-HOOP (Y: 12..27, Z: 3..10) ---
    fill_sym_box(grid, 0, 2, 13, 26, 3, 6, 1)
    fill_sym_box(grid, 0, 1, 14, 25, 4, 5, 0)  # Hollow monocoque interior
    # Cockpit tub & driver helmet (Y: 19..25, Z: 5..8)
    fill_sym_box(grid, 0, 1, 19, 25, 6, 6, 4)
    fill_sym_box(grid, 0, 1, 20, 22, 7, 8, 3)  # Crisp white racing helmet dome
    fill_sym_box(grid, 0, 1, 23, 23, 7, 7, 7)  # Bright cyan helmet visor
    fill_sym_box(grid, 2, 2, 19, 24, 6, 7, 1)  # Cockpit safety bolsters
    fill_sym_box(grid, 2, 2, 23, 24, 7, 7, 3)  # White halo trim
    # Overhead Roll-Hoop Airbox & Dorsal Shark Fin (Y: 6..18, Z: 7..10)
    fill_sym_box(grid, 0, 1, 14, 18, 7, 9, 1)
    fill_sym_box(grid, 0, 1, 19, 19, 8, 9, 4)  # Airbox intake scoop
    fill_sym_box(grid, 0, 0, 16, 18, 10, 10, 8)  # Gold T-cam pod on top
    fill_sym_box(grid, 0, 0, 6, 14, 7, 8, 1)   # Dorsal shark fin
    fill_sym_box(grid, 0, 0, 7, 13, 9, 9, 3)   # White shark fin crest stripe

    # --- SLEEK POINTED AERO NOSECONE (Y: 26..40, Z: 2..6) ---
    fill_sym_box(grid, 0, 2, 26, 31, 3, 5, 1)
    fill_sym_box(grid, 0, 1, 27, 30, 3, 4, 0)  # Hollow nose interior
    fill_sym_box(grid, 0, 2, 26, 29, 6, 6, 1)
    fill_sym_box(grid, 0, 1, 32, 36, 3, 4, 1)
    fill_sym_box(grid, 0, 1, 32, 34, 5, 5, 1)
    fill_sym_box(grid, 0, 0, 37, 40, 2, 3, 1)
    # Crisp white center racing stripe + number plate down the nose!
    fill_sym_box(grid, 0, 0, 26, 29, 6, 6, 3)
    fill_sym_box(grid, 0, 0, 30, 34, 5, 5, 3)
    fill_sym_box(grid, 0, 0, 35, 36, 4, 4, 3)
    fill_sym_box(grid, 0, 0, 37, 39, 3, 3, 3)
    fill_sym_box(grid, 0, 0, 40, 40, 2, 3, 8)  # Championship gold nose emblem
    fill_sym_box(grid, 1, 1, 27, 29, 5, 5, 3)  # White nose number-plate flanks
    fill_sym_box(grid, 1, 1, 30, 34, 3, 3, 2)  # Lower nose maroon shadow

    # --- WIDE MULTI-ELEMENT FRONT WING (Y: 36..40, Z: 1..3) ---
    fill_sym_box(grid, 1, 1, 36, 38, 1, 3, 5)  # Wing mounting pylons under nose
    fill_sym_box(grid, 0, 8, 37, 39, 1, 1, 3)  # Crisp white main front wing plane
    fill_sym_box(grid, 2, 8, 36, 37, 2, 2, 1)  # Vibrant red upper aero flap
    fill_sym_box(grid, 8, 8, 36, 39, 1, 3, 8)  # Championship gold wing endplates
    fill_sym_box(grid, 8, 8, 37, 38, 2, 2, 1)  # Red endplate trim

    # --- BIG ELEVATED REAR WING (Y: 1..6, Z: 6..13) ---
    # Swan-neck pylons rising from rear engine cover
    fill_sym_box(grid, 1, 1, 4, 6, 6, 10, 5)
    fill_sym_box(grid, 0, 0, 4, 5, 6, 9, 2)    # Rear central fin support
    # Dual-element wide rear wing blades
    fill_sym_box(grid, 0, 8, 3, 5, 10, 10, 3)  # Crisp white main aero plane
    fill_sym_box(grid, 0, 8, 2, 3, 11, 11, 1)  # Vibrant red DRS upper flap
    fill_sym_box(grid, 0, 8, 2, 2, 12, 12, 1)  # Upper wing trailing lip
    # Sleek vertical rear wing endplates
    fill_sym_box(grid, 8, 8, 1, 5, 8, 12, 8)   # Championship gold endplates
    fill_sym_box(grid, 8, 8, 2, 5, 9, 11, 1)   # Red outer endplate graphic
    fill_sym_box(grid, 8, 8, 1, 3, 13, 13, 3)  # White top endplate wingtip

    # Hollow unseen enclosed chassis belly under floor & sidepods
    fill_sym_box(grid, 0, 4, 13, 24, 1, 1, 0)

    return grid


# ==========================================
# FORM B: RACING SPEEDSTER WING ROBOT (38 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((38, 24, 42), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 18 (-X robot left)
    cx_r = grid.shape[0] // 2      # 19 (+X robot right)

    # --- FEET & AERO SPEEDSTER BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 8, 16, 0, 1, 4)   # Carbon/rubber grip sole
    fill_sym_box(grid, 3, 5, 7, 9, 0, 2, 5)    # Rear diffuser heel spur
    fill_sym_box(grid, 3, 6, 11, 17, 1, 2, 1)  # Crimson armored boot
    fill_sym_box(grid, 4, 5, 13, 17, 2, 3, 3)  # Crisp white racing toe stripe
    fill_sym_box(grid, 4, 5, 17, 17, 1, 2, 8)  # Gold toe spoiler lip
    # Small outer ankle winglet fins (from front wing endplates)
    fill_sym_box(grid, 7, 7, 10, 13, 1, 3, 8)
    fill_sym_box(grid, 7, 7, 11, 12, 2, 3, 1)

    # --- LOWER LEGS WITH FAT SLICK TIRES ON OUTER CALVES (Z: 3..15) ---
    fill_sym_box(grid, 3, 5, 9, 14, 3, 14, 1)
    fill_sym_box(grid, 4, 4, 10, 13, 4, 13, 0)  # Hollow shin core
    fill_sym_box(grid, 4, 4, 14, 14, 4, 12, 3)  # Crisp white front shin stripe
    fill_sym_box(grid, 3, 3, 10, 13, 4, 13, 2)  # Inner maroon shading
    fill_sym_box(grid, 3, 5, 9, 9, 4, 12, 5)    # Rear gunmetal calf struts
    # Aerodynamic knee cowls
    fill_sym_box(grid, 3, 5, 14, 15, 12, 15, 1)
    fill_sym_box(grid, 4, 4, 15, 16, 13, 15, 8)  # Gold knee crest
    fill_sym_box(grid, 4, 4, 15, 15, 14, 14, 6)  # Chrome intake vent
    # FAT REAR SLICK TIRES ON OUTER LOWER LEGS (x_off: 6..8, Y: 7..15, Z: 4..12)
    fill_sym_slick_wheel_x(
        grid, 6, 8, cy=11.0, cz=8.0,
        r_outer=3.85, r_rim=2.15, r_hub=0.95,
        tire_col=4, wall_col=5, rim_col=8, hub_col=6,
        recess_outer=True, hollow_inner=True,
    )
    fill_sym_box(grid, 5, 7, 10, 12, 7, 9, 5)   # Solid axle anchor into shin
    fill_sym_box(grid, 8, 8, 11, 11, 8, 8, 6)   # Chrome center-lock nut
    # Sleek red/white aero sidepod fin over top of leg tire
    fill_sym_box(grid, 5, 8, 8, 13, 12, 13, 1)
    fill_sym_box(grid, 6, 8, 13, 14, 11, 12, 3)

    # --- ATHLETIC THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 20, 5)
    fill_sym_box(grid, 4, 4, 10, 12, 16, 19, 0)  # Hollow thigh interior
    fill_sym_box(grid, 3, 5, 13, 14, 16, 19, 3)  # Crisp white front thigh armor
    fill_sym_box(grid, 4, 4, 14, 14, 17, 18, 1)  # Red stripe detail
    fill_sym_box(grid, 5, 5, 10, 12, 16, 19, 2)  # Outer maroon plate

    # --- WAIST / SPEEDSTER PELVIS (Z: 19..23) ---
    fill_sym_box(grid, 0, 5, 9, 13, 20, 22, 4)
    fill_sym_box(grid, 0, 4, 10, 12, 20, 22, 5)
    fill_sym_box(grid, 0, 3, 10, 12, 21, 21, 0)  # Hollow enclosed waist core
    # Front waist skirts
    fill_sym_box(grid, 2, 4, 13, 14, 19, 22, 1)
    fill_sym_box(grid, 2, 4, 14, 14, 21, 21, 3)  # White belt stripe
    # Heroic center waist crest
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 1)
    fill_sym_box(grid, 0, 1, 15, 15, 20, 21, 8)  # Championship gold buckle
    fill_sym_box(grid, 0, 0, 15, 15, 21, 21, 9)  # Turbo orange jewel
    # Side hip aero guards
    fill_sym_box(grid, 5, 6, 9, 13, 20, 22, 2)
    fill_sym_box(grid, 6, 6, 10, 12, 21, 21, 8)

    # --- TORSO & POINTED RACING NOSECONE CHEST (Z: 23..33) ---
    fill_sym_box(grid, 0, 5, 8, 14, 23, 32, 1)
    fill_sym_box(grid, 0, 4, 9, 13, 24, 31, 0)  # Hollow torso core
    # Recessed carbon-gunmetal abdomen
    fill_sym_box(grid, 0, 3, 13, 14, 23, 25, 5)
    fill_sym_box(grid, 0, 2, 14, 14, 23, 24, 4)
    fill_sym_box(grid, 1, 2, 14, 14, 24, 24, 6)
    # POINTED RACING NOSECONE FORMING THE CENTRAL CHEST! (Y: 14..19, Z: 24..32)
    fill_sym_box(grid, 0, 3, 14, 16, 26, 31, 1)
    fill_sym_box(grid, 0, 2, 15, 16, 27, 30, 0)  # Hollow nose chest core
    fill_sym_box(grid, 0, 2, 16, 17, 25, 30, 1)
    fill_sym_box(grid, 0, 1, 17, 18, 24, 29, 1)
    fill_sym_box(grid, 0, 0, 18, 19, 24, 27, 1)  # Pointed F1 nose tip!
    # Crisp white center racing stripe down the nosecone chest!
    fill_sym_box(grid, 0, 0, 14, 17, 31, 32, 3)
    fill_sym_box(grid, 0, 0, 17, 18, 28, 30, 3)
    fill_sym_box(grid, 0, 0, 19, 19, 25, 27, 3)
    fill_sym_box(grid, 0, 0, 19, 19, 24, 24, 8)  # Gold nose-tip emblem
    # Glowing turbo-orange chest core & bright cyan cockpit collar vents
    fill_sym_box(grid, 0, 0, 18, 18, 28, 29, 9)  # Glowing engine core
    fill_sym_box(grid, 1, 2, 16, 17, 30, 31, 7)  # Cyan cockpit glass chest vents
    fill_sym_box(grid, 2, 3, 15, 16, 27, 29, 3)  # White number-plate flanks
    fill_sym_box(grid, 3, 4, 14, 15, 26, 28, 2)  # Maroon lower chest undercut
    # Sidepod intake armor wrapping upper flanks
    fill_sym_box(grid, 4, 5, 12, 15, 28, 31, 1)
    fill_sym_box(grid, 4, 5, 15, 15, 29, 30, 4)  # Sidepod intake scoop
    fill_sym_box(grid, 5, 5, 13, 14, 31, 31, 8)  # Gold trim
    # Collar armor framing neck
    fill_sym_box(grid, 2, 4, 10, 13, 32, 33, 2)
    fill_sym_box(grid, 3, 4, 12, 13, 33, 33, 3)

    # --- BACKPACK & DRAMATIC SWEPT REAR-WING BACK WINGS (Y: 2..8, Z: 22..40) ---
    # Central airbox / engine-cover backpack
    fill_sym_box(grid, 0, 4, 5, 8, 23, 33, 1)
    fill_sym_box(grid, 0, 3, 6, 7, 24, 32, 0)  # Hollow backpack interior
    fill_sym_box(grid, 0, 2, 4, 5, 25, 31, 2)  # Rear cowling detail
    fill_sym_box(grid, 0, 0, 3, 5, 27, 34, 3)  # Dorsal shark fin spine
    fill_sym_box(grid, 0, 0, 4, 5, 34, 35, 8)  # Gold T-cam top accent
    # Twin glowing orange rear diffuser thrusters at base of backpack
    fill_sym_box(grid, 1, 3, 4, 5, 22, 24, 5)
    fill_sym_box(grid, 2, 2, 3, 4, 22, 23, 9)  # Glowing afterburner orange
    fill_sym_box(grid, 0, 0, 4, 4, 23, 24, 9)  # F1 rear rain light

    # DRAMATIC SWEPT BACK WINGS (unfolded from the big rear wing!)
    # Anchored solidly into backpack sides (x_off: 3..4, Y: 4..6, Z: 28..32)
    fill_sym_box(grid, 3, 5, 4, 6, 28, 31, 5)  # Swan-neck wing hinge pylons
    # Swept razor-sharp aero wing blades (every step overlaps in X & Z -> 100% 6-connected!)
    wing_steps = [
        (5, 8, 29, 32),
        (7, 10, 31, 34),
        (9, 12, 33, 36),
        (11, 14, 35, 38),
        (13, 16, 37, 40),
    ]
    for x0, x1, z0, z1 in wing_steps:
        fill_sym_box(grid, x0, x1, 4, 4, z0, z1, 1)      # Crimson upper DRS blade
        fill_sym_box(grid, x0, x1, 5, 5, z0, z0 + 1, 3)  # Crisp white main aero plane
        fill_sym_box(grid, x0, x1, 4, 4, z1, z1, 3)      # Leading white edge accent
    # Bold Championship-Gold Wingtip Endplates & Orange Booster Accents!
    fill_sym_box(grid, 16, 16, 3, 6, 36, 41, 8)
    fill_sym_box(grid, 16, 16, 4, 5, 37, 40, 1)
    fill_sym_box(grid, 14, 15, 4, 4, 36, 37, 9)  # Glowing wing thruster trim
    # Lower secondary aero winglet blades for extra F1 wing flair
    fill_sym_box(grid, 5, 8, 4, 4, 26, 28, 3)
    fill_sym_box(grid, 8, 11, 4, 4, 25, 27, 1)
    fill_sym_box(grid, 11, 11, 3, 5, 24, 27, 8)

    # --- BOLD FAT SLICK-TIRE SHOULDERS (Z: 28..38, x_off: 6..11) ---
    # Heavy wishbone/axle shoulder bridge
    fill_sym_box(grid, 5, 8, 10, 12, 29, 32, 5)
    fill_sym_box(grid, 6, 7, 10, 12, 30, 31, 4)
    # WIDE FAT SLICK TIRES AS SHOULDERS! (x_off: 7..10, Y: 7..15, Z: 28..36)
    fill_sym_slick_wheel_x(
        grid, 7, 10, cy=11.0, cz=32.5,
        r_outer=4.15, r_rim=2.25, r_hub=0.95,
        tire_col=4, wall_col=5, rim_col=8, hub_col=6,
        recess_outer=True, hollow_inner=True,
    )
    fill_sym_box(grid, 7, 9, 10, 12, 31, 33, 5)  # Solid inner axle anchor
    fill_sym_box(grid, 10, 10, 11, 11, 32, 33, 6)  # Chrome center-lock cap
    # Sleek crimson & gold aero wheel-arch shoulder cowls crowning the tires!
    fill_sym_box(grid, 6, 11, 8, 14, 37, 37, 1)
    fill_sym_box(grid, 7, 10, 9, 13, 38, 38, 3)  # Crisp white racing stripe on pauldron
    fill_sym_box(grid, 7, 11, 14, 14, 36, 37, 8)  # Gold front aero lip
    fill_sym_box(grid, 7, 10, 7, 7, 35, 36, 2)    # Rear pauldron curve

    # --- ARMS & FRONT-WING WEAPONS (Z: 15..29) ---
    # Upper arms descending solidly from shoulder tire axles
    fill_sym_box(grid, 7, 9, 10, 12, 23, 29, 5)
    fill_sym_box(grid, 8, 9, 10, 12, 25, 27, 4)  # Carbon bicep piston
    # Sleek speedster forearms
    fill_sym_box(grid, 7, 10, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 8, 9, 10, 13, 18, 21, 0)  # Hollow forearm interior
    fill_sym_box(grid, 7, 10, 14, 14, 18, 21, 3)  # White front forearm stripe
    fill_sym_box(grid, 10, 10, 10, 13, 18, 21, 2)  # Outer maroon trim
    fill_sym_box(grid, 10, 10, 11, 12, 19, 20, 8)  # Gold cuff accent
    # Mechanical fists
    fill_sym_box(grid, 7, 9, 10, 13, 15, 16, 4)
    fill_sym_box(grid, 7, 9, 13, 13, 15, 16, 6)  # Chrome knuckles

    # RIGHT HAND (+X, viewer's left): SPLIT FRONT-WING TURBO BLASTER-BLADE
    fill_box(grid, cx_r + 7, cx_r + 9, 13, 16, 15, 16, 5)    # Hilt mount
    fill_box(grid, cx_r + 8, cx_r + 9, 16, 21, 15, 17, 3)    # White aero wing blade
    fill_box(grid, cx_r + 9, cx_r + 9, 16, 22, 16, 17, 1)    # Crimson upper flap
    fill_box(grid, cx_r + 8, cx_r + 9, 20, 22, 15, 15, 8)    # Gold wingtip edge
    fill_box(grid, cx_r + 8, cx_r + 8, 21, 22, 16, 16, 9)    # Glowing orange blaster tip

    # LEFT FOREARM (-X, viewer's right): TWIN-EXHAUST AERO SHIELD BLASTER
    fill_box(grid, cx_l - 11, cx_l - 10, 11, 16, 17, 21, 1)  # Crimson aero shield
    fill_box(grid, cx_l - 11, cx_l - 11, 12, 15, 18, 20, 3)  # White center stripe
    fill_box(grid, cx_l - 11, cx_l - 10, 16, 17, 17, 21, 8)  # Gold endplate edge
    fill_box(grid, cx_l - 11, cx_l - 10, 15, 18, 18, 18, 6)  # Lower chrome exhaust barrel
    fill_box(grid, cx_l - 11, cx_l - 10, 15, 18, 20, 20, 6)  # Upper chrome exhaust barrel
    fill_box(grid, cx_l - 11, cx_l - 11, 18, 18, 18, 18, 9)  # Muzzle glow
    fill_box(grid, cx_l - 11, cx_l - 11, 18, 18, 20, 20, 9)

    # --- HEROIC RACING-HELMET HEAD (Z: 33..41) ---
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 5)  # Neck
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 1)   # Crimson racing helmet
    fill_sym_box(grid, 0, 1, 10, 12, 35, 37, 0)  # Hollow enclosed head core
    fill_sym_box(grid, 0, 0, 9, 13, 38, 39, 3)   # Crisp white center helmet stripe
    fill_sym_box(grid, 0, 2, 10, 14, 38, 38, 1)  # Brow ridge
    # Hollow enclosed boot interior
    fill_sym_box(grid, 4, 5, 9, 15, 1, 1, 0)
    # Bright cyan wrap-around racing visor!
    fill_sym_box(grid, 0, 2, 14, 14, 36, 37, 7)
    # Machined chrome faceplate
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 6)
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 5)
    # Side helmet aero ear pods
    fill_sym_box(grid, 3, 3, 10, 12, 35, 37, 3)
    fill_sym_box(grid, 3, 3, 11, 11, 36, 37, 8)
    # Swept Championship-Gold V-Crest & Turbo-Orange Forehead Sensor
    fill_sym_box(grid, 0, 0, 14, 15, 38, 39, 9)  # Forehead sensor
    fill_sym_box(grid, 1, 1, 13, 14, 39, 40, 8)  # Inner gold V-fin
    fill_sym_box(grid, 2, 3, 12, 13, 40, 41, 8)  # Swept outer gold V-fin tips

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
    v_a = export_vox(model_a, "racingcar_a.vox")
    v_b = export_vox(model_b, "racingcar_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: RACING CAR -> SPEEDSTER WING ROBOT",
        "1. FORMULA RACING CAR",
        "2. SPEEDSTER WING ROBOT",
        "preview_racingcar.png",
        yaw_a=40, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"racingcar: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
