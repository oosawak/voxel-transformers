import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (242, 236, 220, 255),  # Warm Cream / Off-White (Camper Living Box, Cab, Armor)
    2: (206, 194, 168, 255),  # Soft Beige / Sand Shading (Lower Skirt, Shading, Trim)
    3: (34, 148, 138, 255),   # Retro Teal / Turquoise (Adventure Stripes, Crest, Accent)
    4: (216, 128, 52, 255),   # Warm Wood / Tan-Orange (Awning, Retro Stripe, Trim)
    5: (44, 48, 56, 255),     # Dark Charcoal (Tires, Window Frames, Undercarriage)
    6: (104, 114, 126, 255),  # Gunmetal Steel (Chassis, Roof Rack, Ladder, Joints)
    7: (96, 206, 238, 255),   # Bright Cyan Glass (Cab Windshield, Row of Side Windows, Visor)
    8: (255, 224, 116, 255),  # Warm Amber (Headlights, Cozy Window Glow, Lantern Core)
    9: (214, 62, 54, 255),    # Crimson Red (Tail Lights, Roof Luggage, Crest Jewel)
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


def fill_sym_wheel_x(
    grid, x_off0, x_off1, cy, cz, r_outer, r_rim, r_hub,
    tire_col=5, rim_col=1, hub_col=6, recess_outer=False,
):
    """Draw a pair of symmetrical camper wheels along the X axis."""
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
                if dist <= r_hub:
                    col = hub_col
                elif dist <= r_rim:
                    if recess_outer and is_outer_face and dist > r_hub + 0.55:
                        continue
                    col = rim_col
                else:
                    col = tire_col
                xl = cx_l - x_off
                xr = cx_r + x_off
                if 0 <= xl < X:
                    grid[xl, y, z] = col
                if 0 <= xr < X:
                    grid[xr, y, z] = col


# ==========================================
# FORM A: CLASSIC CAB-OVER CAMPER RV (16 x 33 x 19)
# ==========================================
def build_a():
    grid = np.zeros((16, 33, 19), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 7
    cx_r = grid.shape[0] // 2      # 8 (+X right side, viewer's left in yaw=40)

    # --- 4 RV WHEELS & UNDERCARRIAGE CHASSIS (Z: 0..4, Y: 1..31) ---
    fill_sym_wheel_x(
        grid, 4, 5, cy=25.5, cz=2.5,
        r_outer=2.65, r_rim=1.35, r_hub=0.65,
        tire_col=5, rim_col=1, hub_col=6,
    )
    fill_sym_wheel_x(
        grid, 4, 5, cy=9.0, cz=2.5,
        r_outer=2.65, r_rim=1.35, r_hub=0.65,
        tire_col=5, rim_col=1, hub_col=6,
    )
    # Axles & chassis frame
    fill_sym_box(grid, 0, 4, 8, 10, 2, 3, 6)
    fill_sym_box(grid, 0, 4, 25, 26, 2, 3, 6)
    fill_sym_box(grid, 0, 3, 2, 30, 3, 3, 6)
    fill_sym_box(grid, 0, 2, 4, 28, 3, 3, 0)  # Hollow underside core
    # Gunmetal front & rear bumpers
    fill_sym_box(grid, 0, 4, 1, 2, 2, 3, 6)
    fill_sym_box(grid, 0, 4, 30, 31, 2, 3, 6)

    # --- LONG BOXY LIVING QUARTERS (Y: 2..22, Z: 4..15, x_off: 0..5) ---
    fill_sym_box(grid, 0, 5, 2, 22, 4, 15, 1)
    fill_sym_box(grid, 0, 4, 3, 21, 5, 14, 0)  # Hollow living-box interior
    # Soft beige lower utility skirt & wheel-well trim (Z: 4..5)
    fill_sym_box(grid, 5, 5, 2, 22, 4, 5, 2)
    fill_sym_box(grid, 0, 5, 2, 2, 4, 5, 2)
    # Wheel arch framing around rear wheels (Y: 7..11, Z: 4..5)
    fill_sym_box(grid, 5, 5, 7, 11, 4, 5, 5)
    fill_sym_box(grid, 5, 5, 6, 12, 6, 6, 2)
    # Iconic Retro Adventure Stripes running along the living quarters! (Teal 3 + Warm Tan 4)
    fill_sym_box(grid, 5, 5, 2, 22, 6, 6, 3)   # Lower retro teal stripe
    fill_sym_box(grid, 5, 5, 2, 22, 7, 7, 4)   # Warm wood-tan middle stripe
    fill_sym_box(grid, 5, 5, 2, 22, 12, 12, 3)  # Upper teal window header band
    fill_sym_box(grid, 5, 5, 2, 22, 15, 15, 2)  # Soft beige roof molding
    # NEAT ROW OF 4 SIDE CAMPER WINDOWS (Z: 8..11)
    for wy in (3, 8, 13, 18):
        fill_sym_box(grid, 5, 5, wy, wy + 2, 8, 11, 5)   # Charcoal window frame
        fill_sym_box(grid, 5, 5, wy, wy + 2, 9, 10, 7)   # Bright cyan glass
        fill_sym_box(grid, 5, 5, wy + 1, wy + 1, 9, 9, 8)  # Cozy warm amber interior glow!
    # Camper entry door & solidly-attached folding entry step on +X side (Y: 13..15)
    fill_box(grid, cx_r + 5, cx_r + 5, 13, 15, 4, 11, 2)
    fill_box(grid, cx_r + 5, cx_r + 5, 14, 14, 4, 7, 1)
    fill_box(grid, cx_r + 5, cx_r + 5, 13, 15, 6, 6, 3)
    fill_box(grid, cx_r + 5, cx_r + 5, 13, 15, 8, 10, 7)  # Door window
    fill_box(grid, cx_r + 5, cx_r + 5, 14, 14, 9, 9, 8)
    fill_box(grid, cx_r + 5, cx_r + 6, 13, 15, 3, 3, 6)   # Metal entry step anchored to body!

    # --- FRONT TRUCK CAB (Y: 23..30, Z: 4..10, x_off: 0..4) ---
    fill_sym_box(grid, 0, 4, 23, 30, 4, 10, 1)
    fill_sym_box(grid, 0, 3, 24, 29, 5, 9, 0)  # Hollow cab interior
    fill_sym_box(grid, 4, 4, 23, 30, 4, 5, 2)  # Beige lower cab skirt
    fill_sym_box(grid, 4, 4, 23, 30, 6, 6, 3)  # Continuing teal stripe
    fill_sym_box(grid, 4, 4, 23, 30, 7, 7, 4)  # Continuing tan stripe
    # Step back front windshield above engine hood (Y: 30, Z: 8..10 cleared)
    fill_sym_box(grid, 0, 4, 30, 30, 8, 10, 0)
    # Front cab grille & warm amber headlights (Y: 30, Z: 4..7)
    fill_sym_box(grid, 0, 2, 30, 30, 4, 6, 5)
    fill_sym_box(grid, 0, 2, 30, 30, 5, 5, 6)  # Gunmetal grille bar
    fill_sym_box(grid, 0, 1, 30, 30, 6, 6, 3)  # Teal grille emblem
    fill_sym_box(grid, 3, 4, 30, 30, 5, 6, 8)  # Warm glowing headlights!
    # Sloped cab windshield & cab door windows (Z: 8..10)
    fill_sym_box(grid, 0, 3, 28, 29, 8, 10, 7)
    fill_sym_box(grid, 4, 4, 28, 29, 8, 10, 5)  # Cab A-pillars
    fill_sym_box(grid, 4, 4, 24, 27, 8, 10, 7)  # Cab door windows
    fill_sym_box(grid, 4, 4, 24, 24, 8, 10, 5)  # Rear door pillar
    # Side view mirrors
    fill_sym_box(grid, 5, 6, 27, 27, 8, 8, 6)
    fill_sym_box(grid, 6, 6, 27, 27, 8, 10, 5)

    # --- CLASSIC OVERHANGING CAB-OVER BUNK (Y: 22..30, Z: 11..15, x_off: 0..5) ---
    fill_sym_box(grid, 0, 5, 22, 29, 11, 15, 1)
    fill_sym_box(grid, 0, 4, 23, 28, 12, 14, 0)  # Hollow bunk interior
    # Aerodynamic tapered bunk nose overhanging front windshield
    fill_sym_box(grid, 0, 4, 30, 30, 12, 14, 1)
    fill_sym_box(grid, 0, 4, 29, 29, 15, 15, 2)
    # Panoramic front cab-over bunk window & side bunk windows
    fill_sym_box(grid, 0, 3, 30, 30, 12, 13, 7)
    fill_sym_box(grid, 4, 4, 30, 30, 13, 13, 8)  # Amber clearance marker lights
    fill_sym_box(grid, 5, 5, 24, 27, 12, 13, 7)  # Side bunk window
    fill_sym_box(grid, 5, 5, 23, 29, 11, 11, 3)  # Teal bunk accent stripe
    fill_sym_box(grid, 5, 5, 23, 28, 14, 14, 4)  # Tan upper stripe
    fill_sym_box(grid, 0, 4, 30, 30, 14, 14, 9)  # Crimson front brow accent
    # Clear unseen interior partition between living box and bunk
    fill_sym_box(grid, 0, 4, 22, 22, 12, 14, 0)

    # --- ROLLED SIDE AWNING (+X side, Y: 4..21, Z: 13..14) ---
    fill_box(grid, cx_r + 6, cx_r + 6, 4, 21, 13, 14, 4)   # Warm wood-tan awning roll
    fill_box(grid, cx_r + 6, cx_r + 6, 4, 5, 13, 14, 3)    # Teal awning end-caps
    fill_box(grid, cx_r + 6, cx_r + 6, 20, 21, 13, 14, 3)
    fill_box(grid, cx_r + 6, cx_r + 6, 9, 10, 14, 14, 1)   # Striped canvas highlight
    fill_box(grid, cx_r + 6, cx_r + 6, 15, 16, 14, 14, 1)

    # --- ROOF AC UNIT & LUGGAGE RACK (Z: 16..18) ---
    # Rooftop AC unit (Y: 15..20)
    fill_sym_box(grid, 0, 2, 15, 20, 16, 17, 1)
    fill_sym_box(grid, 0, 1, 16, 19, 17, 17, 2)
    fill_sym_box(grid, 2, 2, 16, 19, 16, 16, 6)  # AC vent grille
    # Gunmetal roof luggage rack & adventure gear (Y: 3..12)
    fill_sym_box(grid, 3, 4, 3, 12, 16, 17, 6)   # Side rack rails
    fill_sym_box(grid, 0, 4, 3, 3, 16, 17, 6)    # Rear rail
    fill_sym_box(grid, 0, 4, 12, 12, 16, 17, 6)  # Front rail
    # Crimson camping duffle & tan rolled tent strapped inside roof rack
    fill_sym_box(grid, 0, 2, 5, 8, 16, 18, 9)    # Crimson luggage pack
    fill_sym_box(grid, 1, 1, 5, 8, 18, 18, 4)    # Tan luggage straps
    fill_sym_box(grid, 0, 2, 10, 11, 16, 17, 4)  # Rolled canvas tent
    fill_sym_box(grid, 2, 2, 10, 11, 16, 17, 3)

    # --- REAR WALL DETAILS: SPARE TIRE, LADDER, TAIL LIGHTS (Y: 1..2) ---
    fill_sym_box(grid, 0, 2, 2, 2, 10, 12, 7)    # Rear panoramic window
    fill_sym_box(grid, 3, 4, 2, 2, 5, 6, 9)      # Crimson tail lights!
    fill_sym_box(grid, 4, 4, 2, 2, 13, 13, 9)    # Upper red marker lights
    # Rear mounted spare tire (centered at Y: 1, Z: 4..9)
    fill_sym_box(grid, 0, 2, 1, 1, 5, 8, 5)
    fill_sym_box(grid, 0, 1, 1, 1, 4, 9, 5)
    fill_sym_box(grid, 0, 1, 1, 1, 6, 7, 3)      # Teal spare tire cover
    fill_sym_box(grid, 0, 0, 1, 1, 6, 7, 1)      # Cream badge center
    # Rear steel access ladder on -X side (x = cx_l - 4..cx_l - 2)
    fill_box(grid, cx_l - 4, cx_l - 4, 1, 1, 4, 16, 6)
    fill_box(grid, cx_l - 2, cx_l - 2, 1, 1, 9, 16, 6)
    for lz in (10, 12, 14, 16):
        fill_box(grid, cx_l - 4, cx_l - 2, 1, 1, lz, lz, 6)
    fill_box(grid, cx_l - 4, cx_l - 2, 1, 2, 16, 16, 6)  # Anchor ladder into roof

    return hollow_interior(grid)


# ==========================================
# FORM B: ADVENTURER CAMPER ROBOT (34 x 24 x 41)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 41), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 16 (-X robot left / viewer right)
    cx_r = grid.shape[0] // 2      # 17 (+X robot right / viewer left)

    # --- ADVENTURER HIKING-BOOT FEET (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 8, 16, 0, 1, 5)   # Rugged dark charcoal sole
    fill_sym_box(grid, 3, 6, 7, 9, 0, 2, 6)    # Gunmetal heel block
    fill_sym_box(grid, 3, 6, 11, 17, 1, 2, 1)  # Warm cream boot armor
    fill_sym_box(grid, 4, 5, 13, 17, 2, 3, 2)  # Soft beige toe guard
    fill_sym_box(grid, 4, 5, 17, 17, 1, 2, 3)  # Retro teal toe bumper

    # --- LOWER LEGS WITH TUCKED REAR WHEELS (Z: 3..15) ---
    fill_sym_box(grid, 3, 6, 9, 14, 3, 14, 2)
    fill_sym_box(grid, 4, 5, 10, 13, 4, 13, 0)  # Hollow shin core
    fill_sym_box(grid, 3, 6, 13, 14, 4, 13, 1)  # Warm cream shin armor
    # Retro teal & warm tan adventure stripes running vertically down shins!
    fill_sym_box(grid, 4, 4, 14, 14, 5, 11, 3)
    fill_sym_box(grid, 5, 5, 14, 14, 5, 11, 4)
    fill_sym_box(grid, 3, 3, 10, 13, 4, 13, 6)  # Inner gunmetal strut
    # Armored knee pads with crimson reflector accents
    fill_sym_box(grid, 3, 6, 14, 15, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 15, 16, 13, 15, 3)
    fill_sym_box(grid, 4, 5, 16, 16, 14, 14, 9)  # Crimson knee reflector
    # Rear RV wheels tucked neatly on outer lower calves (x_off: 6..7, cz: 6.5)
    fill_sym_wheel_x(
        grid, 6, 7, cy=10.5, cz=6.5,
        r_outer=2.65, r_rim=1.35, r_hub=0.65,
        tire_col=5, rim_col=1, hub_col=6,
    )

    # --- MECHANICAL THIGHS & TUCKED HIP WHEELS (Z: 15..22) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 20, 6)
    fill_sym_box(grid, 4, 4, 10, 12, 16, 19, 0)  # Hollow core
    fill_sym_box(grid, 3, 5, 13, 14, 16, 19, 2)  # Sand-beige thigh plates
    fill_sym_box(grid, 4, 4, 14, 14, 17, 18, 1)
    # Front RV wheels tucked onto outer hips (x_off: 6..7, cz: 19.5)
    fill_sym_wheel_x(
        grid, 6, 7, cy=10.5, cz=19.5,
        r_outer=2.45, r_rim=1.25, r_hub=0.6,
        tire_col=5, rim_col=1, hub_col=6,
    )

    # --- WAIST / UTILITY BELT PELVIS (Z: 19..23) ---
    fill_sym_box(grid, 0, 5, 9, 13, 20, 22, 6)
    fill_sym_box(grid, 0, 4, 10, 12, 20, 22, 5)
    fill_sym_box(grid, 2, 5, 13, 14, 19, 22, 2)  # Beige waist skirts
    fill_sym_box(grid, 2, 4, 14, 14, 21, 21, 4)  # Warm tan belt pouches
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 1)  # Cream center codpiece
    fill_sym_box(grid, 0, 1, 15, 15, 20, 21, 3)  # Teal belt buckle
    fill_sym_box(grid, 0, 0, 15, 15, 21, 21, 8)  # Warm amber compass core

    # --- BOXY LIVING-QUARTERS TORSO WITH ROW OF CAMPER WINDOWS! (Z: 23..33) ---
    # Sturdy boxy RV living quarters forming the chest/torso (hollow interior)
    fill_sym_box(grid, 0, 6, 8, 16, 23, 32, 1)
    fill_sym_box(grid, 0, 5, 9, 15, 24, 31, 0)  # Hollow torso core
    # Recessed beige & gunmetal lower utility abdomen (Z: 23..24)
    fill_sym_box(grid, 0, 5, 15, 16, 23, 24, 2)
    fill_sym_box(grid, 0, 3, 16, 16, 23, 24, 6)
    fill_sym_box(grid, 1, 2, 16, 16, 24, 24, 4)
    # Iconic Retro Adventure Stripes across the chest below the windows! (Z: 25..26)
    fill_sym_box(grid, 0, 6, 16, 16, 25, 25, 3)  # Retro teal horizontal band
    fill_sym_box(grid, 0, 6, 16, 16, 26, 26, 4)  # Warm wood-tan horizontal band
    fill_sym_box(grid, 6, 6, 9, 16, 25, 25, 3)   # Wrap stripes onto torso flanks
    fill_sym_box(grid, 6, 6, 9, 16, 26, 26, 4)
    # ICONIC ROW OF 4 CAMPER WINDOWS ACROSS THE CHEST! (Z: 27..30, Y: 16)
    fill_sym_box(grid, 0, 5, 16, 16, 27, 30, 5)
    # Center pillar with warm glowing cabin emblem (x_off = 0)
    fill_sym_box(grid, 0, 0, 16, 16, 27, 30, 1)
    fill_sym_box(grid, 0, 0, 16, 16, 28, 29, 8)  # Warm amber cabin glow core
    # Inner pair of camper windows (x_off = 1..2)
    fill_sym_box(grid, 1, 2, 16, 16, 28, 29, 7)  # Bright cyan glass
    fill_sym_box(grid, 1, 1, 16, 16, 28, 28, 8)  # Cozy amber interior glint
    # Mullion divider between inner and outer windows (x_off = 3)
    fill_sym_box(grid, 3, 3, 16, 16, 27, 30, 1)
    # Outer pair of camper windows (x_off = 4..5)
    fill_sym_box(grid, 4, 5, 16, 16, 28, 29, 7)  # Bright cyan glass
    fill_sym_box(grid, 4, 4, 16, 16, 28, 28, 8)  # Cozy amber interior glint
    # Upper teal header stripe & overhanging camper roof collar (Z: 31..32)
    fill_sym_box(grid, 0, 6, 16, 16, 31, 31, 3)
    fill_sym_box(grid, 0, 6, 10, 16, 32, 32, 2)
    fill_sym_box(grid, 2, 5, 11, 14, 32, 33, 1)
    fill_sym_box(grid, 3, 5, 14, 14, 33, 33, 9)  # Crimson collar detail

    # --- ROOF RACK, AC UNIT, LUGGAGE & SPARE TIRE BACKPACK (Y: 3..8, Z: 22..35) ---
    fill_sym_box(grid, 0, 5, 5, 8, 23, 32, 1)
    fill_sym_box(grid, 0, 4, 6, 7, 24, 31, 0)  # Hollow backpack interior
    fill_sym_box(grid, 0, 5, 5, 5, 25, 25, 3)  # Rear teal trim
    fill_sym_box(grid, 4, 5, 5, 5, 23, 24, 9)  # Crimson RV tail lights on lower back!
    # Rear RV Spare Tire mounted dead-center on backpack (Y: 3..4, Z: 25..30)
    fill_sym_box(grid, 0, 2, 4, 4, 26, 29, 5)
    fill_sym_box(grid, 0, 1, 4, 4, 25, 30, 5)
    fill_sym_box(grid, 0, 1, 3, 4, 27, 28, 3)  # Teal spare-tire cover
    fill_sym_box(grid, 0, 0, 3, 3, 27, 28, 1)  # Cream hub emblem
    # Rooftop Gunmetal Luggage Rack & Camping Pack crowning the backpack (Z: 32..35)
    fill_sym_box(grid, 4, 5, 5, 7, 33, 35, 6)  # Rack uprights
    fill_sym_box(grid, 0, 5, 5, 5, 34, 35, 6)  # Top crossbar
    fill_sym_box(grid, 0, 3, 5, 7, 33, 34, 9)  # Crimson camping duffle bag!
    fill_sym_box(grid, 2, 2, 5, 7, 34, 34, 4)  # Tan pack straps
    fill_sym_box(grid, 0, 3, 4, 5, 31, 32, 4)  # Rolled tan sleeping tent under pack
    # Lower exhaust/bumper thrusters
    fill_sym_box(grid, 1, 3, 4, 5, 22, 23, 6)

    # --- CHUNKY CAB-DOOR & CAB-FENDER SHOULDERS (Z: 28..35, x_off: 7..11) ---
    fill_sym_box(grid, 6, 8, 10, 12, 29, 32, 6)
    fill_sym_box(grid, 7, 11, 8, 14, 28, 34, 1)
    fill_sym_box(grid, 8, 10, 9, 13, 29, 33, 0)  # Hollow pauldron interior
    fill_sym_box(grid, 7, 10, 10, 12, 29, 32, 6)  # Solid internal arm joint
    # Cab front fascia & headlights on front of each shoulder! (Y: 14)
    fill_sym_box(grid, 8, 10, 14, 14, 30, 31, 8)  # Warm glowing cab headlights!
    fill_sym_box(grid, 7, 7, 14, 14, 29, 31, 5)   # Split grille slats
    fill_sym_box(grid, 7, 7, 14, 14, 30, 30, 6)
    fill_sym_box(grid, 7, 11, 14, 14, 28, 29, 2)  # Beige lower cab bumper trim
    # Cab side door window & retro stripes on outer shoulder face (x_off: 11)
    fill_sym_box(grid, 11, 11, 9, 13, 31, 33, 7)  # Cyan cab door window!
    fill_sym_box(grid, 11, 11, 9, 9, 31, 33, 5)   # Cab door pillar
    fill_sym_box(grid, 11, 11, 13, 13, 31, 33, 5)
    fill_sym_box(grid, 11, 11, 9, 13, 30, 30, 3)  # Retro teal door stripe
    fill_sym_box(grid, 11, 11, 9, 13, 29, 29, 4)  # Warm tan stripe
    # Cab roof cap & side-mirror antenna fin on top of shoulder
    fill_sym_box(grid, 7, 10, 9, 13, 35, 35, 2)
    fill_sym_box(grid, 10, 10, 12, 13, 35, 36, 6)

    # --- ARMS, FOREARMS & ADVENTURER GEAR (Z: 15..29) ---
    fill_sym_box(grid, 8, 10, 10, 12, 23, 28, 6)  # Gunmetal upper arms
    fill_sym_box(grid, 9, 10, 10, 12, 25, 26, 5)
    # Warm cream & beige armored forearms
    fill_sym_box(grid, 8, 10, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 9, 9, 10, 13, 18, 21, 0)   # Hollow forearm interior
    fill_sym_box(grid, 8, 10, 14, 14, 18, 21, 2)
    fill_sym_box(grid, 8, 10, 14, 14, 19, 20, 3)  # Teal forearm cuff
    fill_sym_box(grid, 10, 10, 10, 13, 18, 21, 4)  # Warm tan side trim
    # Charcoal mechanical fists
    fill_sym_box(grid, 8, 10, 10, 13, 15, 16, 5)
    fill_sym_box(grid, 8, 10, 13, 13, 15, 16, 6)

    # --- RIGHT HAND (+X, viewer's left): AWNING-POLE LANTERN STAFF! ---
    # Held slightly forward and clear of the right shoulder (x = cx_r + 12 = 29, Y: 16)
    fill_box(grid, cx_r + 9, cx_r + 12, 13, 16, 15, 16, 5)   # Extended grip/wrist brace to staff
    fill_box(grid, cx_r + 12, cx_r + 12, 16, 16, 4, 34, 6)   # Tall telescoping awning pole
    fill_box(grid, cx_r + 12, cx_r + 12, 16, 16, 15, 20, 4)  # Warm wood grip wrap
    fill_box(grid, cx_r + 12, cx_r + 12, 16, 16, 4, 5, 5)    # Rubber trekking foot tip
    # Glowing Warm-Amber Camping Lantern rising proudly above right shoulder (Z: 34..39)!
    fill_box(grid, cx_r + 11, cx_r + 13, 15, 17, 34, 34, 3)  # Teal lantern base
    fill_box(grid, cx_r + 11, cx_r + 13, 15, 17, 35, 37, 8)  # Glowing amber lantern core!
    fill_box(grid, cx_r + 11, cx_r + 13, 15, 17, 38, 38, 3)  # Teal lantern cap
    fill_box(grid, cx_r + 12, cx_r + 12, 16, 16, 39, 39, 9)  # Crimson finial tip
    # Rolled tan awning banner pennant fluttering beneath lantern
    fill_box(grid, cx_r + 12, cx_r + 13, 17, 18, 29, 33, 4)
    fill_box(grid, cx_r + 13, cx_r + 13, 17, 18, 30, 32, 1)

    # --- LEFT FOREARM (-X, viewer's right): AWNING-CANOPY TRAIL SHIELD ---
    # Connected cleanly to left forearm (x = cx_l - 10..cx_l - 8 = 6..8)
    fill_box(grid, cx_l - 12, cx_l - 10, 11, 15, 18, 21, 6)  # Shield mounting bracket
    # Striped tan/teal/cream awning shield facing forward-left (X: 1..6, Y: 15..18, Z: 14..25)
    fill_box(grid, 1, 6, 15, 16, 14, 25, 6)   # Gunmetal roof-rack frame
    fill_box(grid, 2, 5, 16, 17, 15, 24, 4)   # Warm tan striped awning canvas
    fill_box(grid, 2, 5, 16, 17, 17, 18, 1)   # Cream canvas stripe
    fill_box(grid, 2, 5, 16, 17, 22, 23, 3)   # Retro teal upper stripe
    fill_box(grid, 1, 6, 17, 18, 24, 25, 3)   # Slight awning-canopy top overhang!
    fill_box(grid, 3, 4, 17, 17, 19, 20, 9)   # Crimson trail compass emblem!

    # --- CAB-OVER HELMETED HEAD WITH OVERHANGING BUNK CREST (Z: 33..40) ---
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 6)  # Neck
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 1)   # Warm cream cab-over helmet
    # Overhanging cab-over bunk brow & explorer visor cap
    fill_sym_box(grid, 0, 3, 9, 15, 38, 39, 1)
    fill_sym_box(grid, 0, 2, 10, 14, 39, 39, 2)
    fill_sym_box(grid, 0, 2, 15, 15, 38, 38, 3)  # Teal visor brim trim
    # Panoramic bright cyan cab-windshield visor!
    fill_sym_box(grid, 0, 2, 14, 14, 36, 37, 7)
    # Beige & gunmetal faceplate
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 2)
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 6)
    # Warm tan ear pods
    fill_sym_box(grid, 3, 3, 10, 12, 35, 37, 4)
    fill_sym_box(grid, 3, 3, 11, 11, 36, 37, 3)
    # Retro Teal Explorer V-Crest & Crimson Compass Forehead Jewel
    fill_sym_box(grid, 0, 0, 15, 15, 38, 39, 9)  # Crimson forehead jewel
    fill_sym_box(grid, 1, 1, 14, 15, 39, 40, 3)  # Inner V-crest
    fill_sym_box(grid, 2, 3, 13, 14, 39, 40, 3)  # Swept outer V-crest

    # Clear completely enclosed internal partition between torso and backpack
    fill_sym_box(grid, 0, 4, 6, 15, 24, 31, 0)

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
    v_a = export_vox(model_a, "camper_a.vox")
    v_b = export_vox(model_b, "camper_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: CAMPER RV -> ADVENTURER CAMPER ROBOT",
        "1. CAB-OVER CAMPER RV",
        "2. ADVENTURER CAMPER ROBOT",
        "preview_camper.png",
        yaw_a=40, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"camper: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
