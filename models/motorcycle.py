import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (28, 110, 218, 255),   # Metallic Sportbike Cobalt Blue (Fairing, Fuel Tank, Chest, Armor)
    2: (18, 62, 138, 255),    # Deep Midnight Navy Blue (Shading, Belly Pan, Lower Armor)
    3: (242, 246, 252, 255),  # Pearl Racing White (Fairing Stripes, Tail Trim, Number Plate)
    4: (36, 40, 48, 255),     # Sport Tire Charcoal Rubber (Front & Rear Tires, Seat, Grips)
    5: (88, 96, 112, 255),    # Gunmetal Engine Frame (Trellis Frame, Engine, Swingarm, Joints)
    6: (206, 216, 228, 255),  # Polished Chrome / Silver (Wheel Rims, Exhaust Pipe, Rotors, Face)
    7: (84, 218, 248, 255),   # Electric Cyan (Aerodynamic Windscreen, Robot Visor, Blade Edge)
    8: (244, 188, 42, 255),   # Anodized Gold & Warm Headlight Glow (Inverted Forks, Calipers, Crest)
    9: (232, 46, 54, 255),    # Crimson Tail Light & Racing Accent (LED Tail Light, Rim/Armor Trim)
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


def fill_center_moto_wheel(
    grid, x_off_max, cy, cz, r_outer, r_rim, r_spoke_inner, r_hub,
    tire_col=4, rim_col=6, rotor_col=5, hub_col=6, caliper_col=8,
):
    """Draw a centered sportbike wheel with recessed spokes, rim ring, and brake rotor."""
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

            # 4-spoke + cross pattern for sporty spoked motorcycle rim
            is_spoke = (abs(dy) <= 0.75 or abs(dz) <= 0.75)

            for x_off in range(0, x_off_max + 1):
                is_outer = (x_off == x_off_max)
                if dist <= r_hub:
                    col = hub_col if is_outer else 5
                elif dist <= r_spoke_inner:
                    # Inner hub/brake rotor & 4 chrome spokes with recessed air gaps
                    if is_outer:
                        if is_spoke:
                            col = rim_col
                        else:
                            continue
                    else:
                        col = rim_col if is_spoke else rotor_col
                elif dist <= r_rim:
                    # Polished alloy rim ring
                    col = rim_col
                else:
                    # Rounded sport tire crown (slightly tapered on very outer rim edge)
                    if is_outer and dist > r_outer - 0.55 and x_off_max >= 2:
                        continue
                    col = tire_col

                xl = cx_l - x_off
                xr = cx_r + x_off
                if 0 <= xl < X:
                    grid[xl, y, z] = col
                if 0 <= xr < X:
                    grid[xr, y, z] = col

    # Gold brake caliper gripping front-upper quadrant of rotor
    cal_y = int(round(cy + r_spoke_inner * 0.55))
    cal_z = int(round(cz + r_spoke_inner * 0.45))
    fill_sym_box(grid, x_off_max, x_off_max, cal_y - 1, cal_y, cal_z - 1, cal_z, caliper_col)


def fill_sym_moto_wheel_x(
    grid, x_off0, x_off1, cy, cz, r_outer, r_rim, r_hub,
    tire_col=4, rim_col=6, rotor_col=5, hub_col=8,
):
    """Draw a pair of symmetrical sportbike wheels mounted on robot shoulders or legs."""
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

            is_spoke = (abs(dy) <= 0.7 or abs(dz) <= 0.7)

            for x_off in range(x_off0, x_off1 + 1):
                is_outer = (x_off == x_off1)
                is_inner = (x_off == x_off0)
                if dist <= r_hub:
                    col = hub_col if is_outer else 5
                elif dist <= r_rim - 0.85:
                    if is_outer:
                        if is_spoke:
                            col = rim_col
                        else:
                            continue
                    elif not is_inner:
                        col = rim_col if is_spoke else rotor_col
                    else:
                        col = rotor_col
                elif dist <= r_rim:
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
# FORM A: SPORT MOTORCYCLE (16 x 40 x 21)
# ==========================================
def build_a():
    grid = np.zeros((16, 40, 21), dtype=np.uint8)
    cx_r = grid.shape[0] // 2  # +X right side of motorcycle (8)

    # --- LARGE SPORT REAR WHEEL (Y: 2..14, Z: 0..11, x_off: 0..1 -> 4 voxels wide) ---
    fill_center_moto_wheel(
        grid, x_off_max=1, cy=8.0, cz=5.5,
        r_outer=5.65, r_rim=3.65, r_spoke_inner=2.75, r_hub=1.15,
        tire_col=4, rim_col=6, rotor_col=5, hub_col=6, caliper_col=8,
    )
    # Red sportbike rim accent flecks on rear tire
    fill_sym_box(grid, 1, 1, 8, 8, 9, 9, 9)
    fill_sym_box(grid, 1, 1, 8, 8, 2, 2, 9)

    # --- LARGE SPORT FRONT WHEEL (Y: 26..37, Z: 0..10, x_off: 0..1 -> 4 voxels wide) ---
    fill_center_moto_wheel(
        grid, x_off_max=1, cy=31.5, cz=5.0,
        r_outer=5.25, r_rim=3.35, r_spoke_inner=2.45, r_hub=1.05,
        tire_col=4, rim_col=6, rotor_col=5, hub_col=6, caliper_col=8,
    )
    fill_sym_box(grid, 1, 1, 31, 32, 8, 8, 9)
    # Aerodynamic blue & white front fender hugging front tire
    fill_sym_box(grid, 0, 1, 28, 34, 10, 10, 1)
    fill_sym_box(grid, 0, 1, 29, 32, 11, 11, 1)
    fill_sym_box(grid, 0, 0, 30, 34, 10, 10, 3)

    # --- REAR SWINGARM, ENGINE BLOCK & TRELLIS FRAME (Y: 7..27, Z: 3..12) ---
    # Heavy twin-spar rear swingarm connecting rear wheel axle to central frame
    fill_sym_box(grid, 2, 2, 8, 16, 5, 6, 5)
    fill_sym_box(grid, 1, 2, 8, 9, 5, 6, 6)    # Rear axle bolt
    fill_sym_box(grid, 0, 1, 13, 16, 5, 7, 5)  # Rear shock linkage & monoshock
    fill_sym_box(grid, 0, 0, 14, 16, 7, 10, 9)  # Red rear coilover spring!
    # Exposed mechanical engine block & radiator (Y: 16..26, Z: 4..11)
    fill_sym_box(grid, 0, 2, 16, 25, 4, 10, 5)
    fill_sym_box(grid, 0, 1, 17, 24, 5, 9, 0)  # Hollow engine core
    # Metallic engine fins & clutch case detail
    fill_sym_box(grid, 2, 2, 17, 20, 5, 7, 6)  # Chrome clutch/crank cover
    fill_sym_box(grid, 2, 2, 18, 19, 6, 6, 8)  # Gold bolt cap
    fill_sym_box(grid, 2, 2, 21, 24, 7, 9, 4)  # Dark cylinder ribs
    fill_sym_box(grid, 0, 1, 25, 26, 6, 10, 4)  # Front oil radiator
    # Rider footpegs
    fill_sym_box(grid, 3, 4, 14, 15, 5, 5, 6)

    # --- SLEEK UPSWEPT CHROME EXHAUST PIPE (+X right side, x = cx_r + 2..3) ---
    # Header emerging from lower engine and sweeping back/up cleanly beside rear wheel
    fill_box(grid, cx_r + 2, cx_r + 2, 15, 21, 4, 5, 6)
    fill_box(grid, cx_r + 2, cx_r + 3, 12, 15, 5, 6, 6)
    fill_box(grid, cx_r + 2, cx_r + 3, 9, 12, 7, 8, 6)
    fill_box(grid, cx_r + 2, cx_r + 3, 5, 9, 8, 9, 6)    # Sleek chrome muffler canister
    fill_box(grid, cx_r + 3, cx_r + 3, 7, 8, 8, 9, 8)    # Gold heatshield band
    fill_box(grid, cx_r + 2, cx_r + 3, 5, 5, 9, 9, 4)    # Dark exhaust bore tip

    # --- ANODIZED GOLD INVERTED FRONT FORKS & CLIP-ON HANDLEBARS (Y: 24..31, Z: 5..17) ---
    # Stepped diagonal gold forks (every step overlaps in Y & Z -> 100% 6-connected!)
    fork_steps = [
        (31, 31, 5, 7),
        (30, 31, 7, 9),
        (29, 30, 9, 11),
        (28, 29, 11, 13),
        (27, 28, 13, 15),
        (26, 27, 15, 16),
    ]
    for y0, y1, z0, z1 in fork_steps:
        fill_sym_box(grid, 2, 2, y0, y1, z0, z1, 8)
    fill_sym_box(grid, 1, 2, 31, 31, 5, 5, 6)  # Front wheel axle mount
    # Triple clamp & clip-on handlebars flaring outward (x_off: 0..5)
    fill_sym_box(grid, 0, 2, 25, 27, 15, 16, 5)
    fill_sym_box(grid, 2, 3, 25, 26, 16, 16, 6)  # Fork top caps
    fill_sym_box(grid, 3, 5, 24, 25, 15, 15, 4)  # Rubber handlebar grips
    fill_sym_box(grid, 5, 5, 25, 26, 15, 15, 6)  # Chrome brake/clutch levers
    fill_sym_box(grid, 0, 1, 27, 28, 16, 16, 7)  # Digital dash gauge glow

    # --- AERODYNAMIC FULL SPORTBIKE FAIRING, NOSE COWL & CYAN WINDSCREEN ---
    # Lower deep navy belly pan (Y: 16..26, Z: 3..5)
    fill_sym_box(grid, 1, 2, 16, 26, 3, 5, 2)
    fill_sym_box(grid, 0, 1, 18, 25, 3, 4, 2)
    # Sculpted side fairings (Y: 20..31, Z: 6..13, x_off: 2..3)
    fill_sym_box(grid, 2, 3, 21, 30, 6, 12, 1)
    fill_sym_box(grid, 2, 2, 22, 29, 7, 11, 0)  # Hollow behind fairing
    # Reconnect inner fairing bridge to frame so fairing is rock-solid
    fill_sym_box(grid, 1, 2, 22, 27, 10, 12, 1)
    fill_sym_box(grid, 3, 3, 22, 29, 8, 9, 3)   # Pearl white diagonal fairing stripe
    fill_sym_box(grid, 3, 3, 24, 28, 10, 10, 9)  # Crimson racing accent line
    fill_sym_box(grid, 3, 3, 21, 24, 6, 7, 2)   # Deep navy lower shade
    # Pointed Aerodynamic Front Nose Cowl (Y: 28..37, Z: 10..15)
    fill_sym_box(grid, 0, 2, 29, 33, 11, 14, 1)
    fill_sym_box(grid, 0, 1, 34, 36, 11, 14, 1)
    fill_sym_box(grid, 0, 0, 36, 37, 12, 13, 1)
    fill_sym_box(grid, 0, 1, 30, 34, 12, 13, 0)  # Hollow nose interior
    # White fairing cheek trim & bright glowing headlight!
    fill_sym_box(grid, 2, 2, 30, 33, 12, 13, 3)
    fill_sym_box(grid, 1, 1, 34, 35, 13, 13, 3)
    fill_sym_box(grid, 0, 1, 35, 36, 12, 12, 8)  # Warm bright sportbike headlight!
    fill_sym_box(grid, 0, 0, 37, 37, 12, 12, 8)
    fill_sym_box(grid, 0, 1, 34, 35, 11, 11, 2)  # Chin intake spoiler
    # Raked Electric-Cyan Windscreen (Y: 26..34, Z: 14..19)
    fill_sym_box(grid, 0, 1, 32, 34, 15, 15, 7)
    fill_sym_box(grid, 0, 1, 30, 32, 16, 16, 7)
    fill_sym_box(grid, 0, 1, 28, 30, 17, 17, 7)
    fill_sym_box(grid, 0, 1, 27, 29, 18, 18, 7)
    fill_sym_box(grid, 0, 0, 26, 27, 19, 19, 7)
    fill_sym_box(grid, 2, 2, 29, 31, 15, 16, 1)  # Upper cowl mirror stalks (face-connected!)
    fill_sym_box(grid, 3, 4, 30, 31, 16, 16, 4)  # Aero side mirrors

    # --- SCULPTED FUEL TANK (Y: 17..25, Z: 11..16, x_off: 0..3) ---
    fill_sym_box(grid, 0, 2, 17, 25, 11, 15, 1)
    fill_sym_box(grid, 0, 1, 18, 24, 12, 14, 0)  # Hollow tank core
    fill_sym_box(grid, 2, 3, 19, 24, 12, 14, 1)  # Wide sculpted tank flanks
    fill_sym_box(grid, 0, 1, 18, 24, 16, 16, 1)  # High arched tank crown
    fill_sym_box(grid, 0, 0, 18, 24, 16, 16, 3)  # Pearl white center tank stripe
    fill_sym_box(grid, 0, 0, 21, 22, 16, 16, 6)  # Chrome fuel filler cap
    fill_sym_box(grid, 3, 3, 19, 23, 13, 13, 3)  # White knee-panel accent
    fill_sym_box(grid, 3, 3, 19, 22, 12, 12, 2)  # Deep navy knee recess

    # --- RIDER SEAT & SHARP UPSWEPT SPORT TAIL (Y: 2..17, Z: 10..16) ---
    fill_sym_box(grid, 0, 2, 11, 17, 10, 11, 2)  # Subframe side panels
    fill_sym_box(grid, 0, 1, 11, 17, 11, 12, 4)  # Black sport saddle
    # Upswept aerodynamic tail cowl (Y: 3..11, Z: 12..16)
    fill_sym_box(grid, 0, 2, 8, 11, 12, 13, 1)
    fill_sym_box(grid, 0, 2, 5, 9, 13, 14, 1)
    fill_sym_box(grid, 0, 1, 3, 7, 14, 15, 1)
    fill_sym_box(grid, 0, 0, 2, 5, 15, 16, 1)
    fill_sym_box(grid, 0, 1, 5, 9, 13, 13, 0)   # Hollow tail cowl
    fill_sym_box(grid, 0, 0, 4, 10, 15, 15, 3)  # White tail racing stripe
    fill_sym_box(grid, 2, 2, 6, 9, 13, 13, 3)   # White tail side accent
    fill_sym_box(grid, 0, 1, 4, 8, 12, 12, 2)   # Under-tail dark navy
    fill_sym_box(grid, 0, 1, 2, 3, 14, 15, 9)   # Glowing crimson LED tail light!

    return grid


# ==========================================
# FORM B: CYBER-BIKER SPORTBIKE ROBOT (34 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 42), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 16 (-X robot left)
    cx_r = grid.shape[0] // 2      # 17 (+X robot right)

    # --- AGILE CYBER-BIKER BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 8, 16, 0, 1, 4)   # Sport tire-grip sole
    fill_sym_box(grid, 3, 5, 7, 9, 0, 2, 5)    # Mechanical heel spur
    fill_sym_box(grid, 3, 6, 11, 17, 1, 2, 1)  # Metallic blue boot armor
    fill_sym_box(grid, 4, 5, 13, 17, 2, 3, 3)  # Pearl white toe stripe
    fill_sym_box(grid, 4, 5, 17, 17, 1, 2, 8)  # Anodized gold toe guard
    fill_sym_box(grid, 6, 6, 10, 12, 1, 2, 8)  # Gold ankle caliper

    # --- LOWER LEGS WITH LARGE SPORTBIKE REAR WHEELS ON OUTER CALVES (Z: 3..15) ---
    fill_sym_box(grid, 3, 5, 9, 14, 3, 14, 1)
    fill_sym_box(grid, 4, 4, 10, 13, 4, 13, 0)  # Hollow shin core
    fill_sym_box(grid, 4, 4, 14, 14, 4, 12, 3)  # Crisp white shin fairing stripe
    fill_sym_box(grid, 3, 3, 10, 13, 4, 13, 2)  # Deep navy inner shading
    fill_sym_box(grid, 3, 5, 9, 9, 4, 13, 5)    # Rear swingarm calf strut
    # Sharp sportbike knee guards
    fill_sym_box(grid, 3, 5, 14, 15, 12, 15, 1)
    fill_sym_box(grid, 4, 4, 15, 16, 13, 15, 6)  # Chrome knee blade
    fill_sym_box(grid, 4, 4, 15, 15, 14, 14, 9)  # Crimson accent jewel
    # LARGE REAR MOTORCYCLE WHEELS ON OUTER LOWER LEGS! (x_off: 6..8, Y: 6..15, Z: 4..13)
    fill_sym_moto_wheel_x(
        grid, 6, 8, cy=10.5, cz=8.5,
        r_outer=4.45, r_rim=2.65, r_hub=1.05,
        tire_col=4, rim_col=6, rotor_col=5, hub_col=8,
    )
    fill_sym_box(grid, 5, 7, 10, 11, 8, 9, 5)   # Swingarm axle hub anchor
    fill_sym_box(grid, 8, 8, 10, 11, 11, 11, 9)  # Red sport rim stripe
    # Upswept blue/white fender fairing hooding the leg-wheels
    fill_sym_box(grid, 5, 8, 7, 13, 13, 14, 1)
    fill_sym_box(grid, 6, 8, 13, 14, 12, 13, 3)

    # --- AGILE MECHANICAL THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 20, 5)
    fill_sym_box(grid, 4, 4, 10, 12, 16, 19, 0)  # Hollow thigh core
    fill_sym_box(grid, 3, 5, 13, 14, 16, 19, 3)  # Pearl white thigh armor
    fill_sym_box(grid, 4, 4, 14, 14, 17, 18, 1)  # Cobalt blue stripe
    fill_sym_box(grid, 5, 5, 10, 12, 16, 19, 2)  # Outer navy plate

    # --- WAIST / ENGINE-FRAME PELVIS (Z: 19..23) ---
    fill_sym_box(grid, 0, 5, 9, 13, 20, 22, 5)
    fill_sym_box(grid, 0, 4, 10, 12, 20, 22, 4)
    # Front waist fairing skirts
    fill_sym_box(grid, 2, 4, 13, 14, 19, 22, 1)
    fill_sym_box(grid, 2, 4, 14, 14, 21, 21, 3)  # White belt stripe
    # Center pelvic guard
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 2)
    fill_sym_box(grid, 0, 1, 15, 15, 20, 21, 8)  # Anodized gold waist core
    fill_sym_box(grid, 0, 0, 15, 15, 21, 21, 9)  # Crimson accent
    # Side hip armor guards
    fill_sym_box(grid, 5, 6, 9, 13, 20, 22, 1)
    fill_sym_box(grid, 6, 6, 10, 12, 21, 21, 3)

    # --- TORSO: SCULPTED FUEL TANK & AERODYNAMIC FRONT COWL CHEST (Z: 23..33) ---
    fill_sym_box(grid, 0, 5, 8, 14, 23, 32, 1)
    fill_sym_box(grid, 0, 4, 9, 13, 24, 31, 0)  # Hollow torso core
    # Exposed gunmetal engine-block abdomen (Z: 23..25)
    fill_sym_box(grid, 0, 3, 13, 14, 23, 25, 5)
    fill_sym_box(grid, 0, 2, 14, 14, 23, 24, 4)
    fill_sym_box(grid, 1, 2, 14, 14, 24, 24, 6)  # Chrome engine pistons
    # PROMINENT FRONT COWL & SCULPTED FUEL TANK CHEST! (Y: 14..18, Z: 25..32)
    # Sculpted rounded fuel tank pecs (upper-outer chest)
    fill_sym_box(grid, 0, 4, 14, 16, 26, 31, 1)
    fill_sym_box(grid, 0, 3, 15, 16, 27, 30, 0)  # Hollow chest cowl
    fill_sym_box(grid, 2, 4, 15, 17, 28, 31, 1)  # Arched fuel tank lobes
    fill_sym_box(grid, 3, 4, 16, 17, 29, 30, 3)  # Pearl white tank stripes
    fill_sym_box(grid, 4, 4, 15, 16, 27, 28, 2)  # Deep navy fairing undercut
    fill_sym_box(grid, 2, 3, 15, 16, 32, 32, 1)  # Upper tank shoulder deck
    fill_sym_box(grid, 3, 3, 16, 16, 32, 32, 6)  # Chrome fuel-cap accents
    # Aerodynamic pointed front nose cowl jutting forward at center chest!
    fill_sym_box(grid, 0, 2, 16, 17, 25, 30, 1)
    fill_sym_box(grid, 0, 1, 17, 18, 25, 29, 1)
    fill_sym_box(grid, 0, 1, 18, 18, 26, 27, 8)  # GLOWING SPORTBIKE HEADLIGHT CORE!
    fill_sym_box(grid, 2, 2, 17, 17, 26, 27, 9)  # Crimson intake accents flanking headlight
    fill_sym_box(grid, 0, 1, 17, 18, 25, 25, 2)  # Deep navy chin fairing lip
    # Raked Electric-Cyan Windscreen crowning the upper chest! (Y: 14..17, Z: 29..33)
    fill_sym_box(grid, 0, 1, 16, 17, 29, 30, 7)
    fill_sym_box(grid, 0, 1, 15, 16, 31, 32, 7)
    fill_sym_box(grid, 0, 1, 14, 15, 32, 33, 7)
    # Collar armor framing neck
    fill_sym_box(grid, 2, 4, 10, 13, 32, 33, 2)
    fill_sym_box(grid, 3, 4, 12, 13, 33, 33, 8)  # Gold collar accent

    # --- BACKPACK: TAIL SECTION & TWIN UPSWEPT CHROME EXHAUST PIPES (Y: 3..8, Z: 22..38) ---
    fill_sym_box(grid, 0, 4, 5, 8, 23, 32, 1)
    fill_sym_box(grid, 0, 3, 6, 7, 24, 31, 0)   # Hollow backpack interior
    fill_sym_box(grid, 0, 2, 4, 5, 24, 31, 2)   # Deep navy rear tail fairing
    fill_sym_box(grid, 0, 0, 4, 4, 25, 30, 3)   # White tail stripe
    fill_sym_box(grid, 0, 1, 3, 4, 30, 32, 9)   # Glowing crimson LED tail light on back!
    fill_sym_box(grid, 1, 2, 4, 5, 22, 24, 5)   # Lower engine-frame thrusters
    # TWIN UPSWEPT POLISHED CHROME EXHAUST CANNONS rising boldly behind shoulders!
    fill_sym_box(grid, 3, 4, 4, 6, 25, 32, 6)   # Lower exhaust pipes
    fill_sym_box(grid, 3, 4, 4, 5, 32, 39, 6)   # Tall upswept chrome canisters
    fill_sym_box(grid, 4, 4, 4, 5, 35, 36, 8)   # Anodized gold heatshield bands
    fill_sym_box(grid, 3, 4, 4, 5, 40, 40, 4)   # Dark exhaust muzzle bores

    # --- ICONIC LARGE FRONT-WHEEL SHOULDERS & GOLD INVERTED FORKS (Z: 28..38) ---
    # Heavy triple-clamp axle bridge
    fill_sym_box(grid, 5, 8, 10, 12, 29, 32, 5)
    fill_sym_box(grid, 6, 7, 10, 12, 30, 31, 8)  # Gold fork clamp bridge
    # LARGE SPORTBIKE FRONT WHEELS AS SHOULDERS! (x_off: 7..9, Y: 7..15, Z: 28..37)
    fill_sym_moto_wheel_x(
        grid, 7, 9, cy=11.0, cz=32.5,
        r_outer=4.35, r_rim=2.55, r_hub=1.05,
        tire_col=4, rim_col=6, rotor_col=5, hub_col=8,
    )
    fill_sym_box(grid, 7, 8, 10, 12, 31, 33, 5)  # Solid inner shoulder axle
    fill_sym_box(grid, 9, 9, 11, 11, 35, 35, 9)  # Red rim stripe fleck
    # Anodized Gold Inverted Front Fork Bars & Blue Fender Cowls over shoulder wheels!
    fill_sym_box(grid, 6, 10, 8, 14, 37, 37, 1)  # Blue curved front fender pauldron
    fill_sym_box(grid, 7, 9, 9, 13, 38, 38, 3)   # White racing stripe crown
    fill_sym_box(grid, 6, 10, 14, 14, 35, 37, 8)  # Anodized gold fork struts on front
    fill_sym_box(grid, 6, 9, 7, 7, 35, 36, 8)    # Gold rear fork caliper
    # Handlebar wing-tips jutting slightly from upper shoulder wheels
    fill_sym_box(grid, 10, 11, 10, 11, 36, 37, 4)
    fill_sym_box(grid, 11, 11, 12, 12, 36, 37, 6)  # Chrome lever tip

    # --- AGILE ARMS & CYBER-BIKER WEAPONS (Z: 15..29) ---
    # Upper arms with anodized gold fork-piston detail
    fill_sym_box(grid, 7, 8, 10, 12, 23, 29, 5)
    fill_sym_box(grid, 8, 8, 10, 12, 25, 28, 8)  # Gold inverted fork bicep piston
    # Sleek armored cyber-forearms
    fill_sym_box(grid, 7, 9, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 8, 8, 10, 13, 18, 21, 0)  # Hollow forearm interior
    fill_sym_box(grid, 7, 9, 14, 14, 18, 21, 3)  # White front forearm trim
    fill_sym_box(grid, 9, 9, 10, 13, 18, 21, 2)  # Deep navy outer guard
    fill_sym_box(grid, 9, 9, 11, 12, 19, 20, 6)  # Chrome cuff brace
    # Mechanical fists
    fill_sym_box(grid, 7, 8, 10, 13, 15, 16, 4)
    fill_sym_box(grid, 7, 8, 13, 13, 15, 16, 6)  # Chrome knuckles

    # RIGHT HAND (+X, viewer's left): GOLD FORK-LANCE / CYAN ENERGY TONFA BLADE
    fill_box(grid, cx_r + 7, cx_r + 8, 13, 16, 15, 16, 5)   # Grip mount
    fill_box(grid, cx_r + 7, cx_r + 8, 16, 21, 15, 16, 8)   # Anodized gold fork shaft
    fill_box(grid, cx_r + 8, cx_r + 8, 15, 17, 17, 17, 6)   # Chrome handguard
    fill_box(grid, cx_r + 7, cx_r + 8, 17, 23, 16, 17, 7)   # Glowing electric cyan energy blade!
    fill_box(grid, cx_r + 8, cx_r + 8, 22, 23, 15, 16, 7)   # Tapered blade tip

    # LEFT FOREARM (-X, viewer's right): FAIRING COWL SHIELD & CHROME EXHAUST BLASTER
    fill_box(grid, cx_l - 10, cx_l - 9, 11, 16, 17, 21, 1)  # Cobalt blue fairing shield
    fill_box(grid, cx_l - 10, cx_l - 10, 12, 15, 18, 20, 3)  # White shield stripe
    fill_box(grid, cx_l - 10, cx_l - 9, 16, 17, 18, 20, 6)  # Twin chrome exhaust barrels
    fill_box(grid, cx_l - 10, cx_l - 10, 14, 15, 19, 19, 9)  # Crimson fairing sensor

    # --- FULL-FACE CYBER-BIKER HELMET HEAD (Z: 33..41) ---
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 5)  # Neck
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 1)   # Metallic blue full-face helmet
    fill_sym_box(grid, 0, 0, 9, 13, 38, 39, 3)   # Pearl white center helmet stripe
    fill_sym_box(grid, 0, 2, 10, 14, 38, 38, 1)  # Aero brow overhang
    # Large wrap-around Electric-Cyan Helmet Visor!
    fill_sym_box(grid, 0, 2, 14, 14, 36, 37, 7)
    # Polished chrome chin-guard faceplate
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 6)
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 2)
    # Side helmet ear fins
    fill_sym_box(grid, 3, 3, 10, 12, 35, 37, 3)
    fill_sym_box(grid, 3, 3, 11, 11, 36, 37, 8)
    # Swept Anodized-Gold V-Crest & Crimson Forehead Jewel
    fill_sym_box(grid, 0, 0, 14, 15, 38, 39, 9)  # Crimson forehead jewel
    fill_sym_box(grid, 1, 1, 13, 14, 39, 40, 8)  # Inner gold V-crest
    fill_sym_box(grid, 2, 3, 12, 13, 40, 41, 8)  # Swept outer gold V-crest tips

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
    v_a = export_vox(model_a, "motorcycle_a.vox")
    v_b = export_vox(model_b, "motorcycle_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SPORT MOTORCYCLE -> CYBER-BIKER ROBOT",
        "1. SPORT MOTORCYCLE",
        "2. CYBER-BIKER ROBOT",
        "preview_motorcycle.png",
        yaw_a=44, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"motorcycle: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
