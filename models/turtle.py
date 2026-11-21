import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (66, 150, 88, 255),    # Sea-Turtle Olive / Emerald Green Skin
    2: (30, 84, 52, 255),     # Dark Forest Green Scute Border & Shading
    3: (176, 110, 48, 255),   # Warm Amber / Brown Domed Shell Hexagonal Scutes
    4: (236, 220, 174, 255),  # Sandy Cream Plastron (Underbelly / Chest Armor)
    5: (52, 62, 74, 255),     # Dark Slate Mechanical Joints & Frame
    6: (52, 224, 232, 255),   # Glowing Ocean-Cyan Accents, Visor & Eyes
    7: (238, 188, 60, 255),   # Gold Trim on Shell Ridges & Crest
    8: (26, 116, 122, 255),   # Deep Teal Flipper Spots & Fin Trim
    9: (244, 250, 255, 255),  # Bright White Eye Glint & Core Specular
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


def hollow_interior_26(grid, z_min, z_max):
    """Hollow strictly interior voxels (all 26 neighbors occupied) to preserve 6-connectivity."""
    X, Y, Z = grid.shape
    to_clear = []
    for x in range(1, X - 1):
        for y in range(1, Y - 1):
            for z in range(max(1, z_min), min(Z - 1, z_max + 1)):
                if grid[x, y, z] == 0:
                    continue
                if np.all(grid[x - 1:x + 2, y - 1:y + 2, z - 1:z + 2] > 0):
                    to_clear.append((x, y, z))
    for x, y, z in to_clear:
        grid[x, y, z] = 0


def scute_color(u, v, rad_norm):
    """Return hexagonal carapace scute color for normalized shell coordinates (u, v)."""
    # Marginal outer rim of the shell
    if rad_norm > 0.87:
        # Alternating dark forest green & gold marginal scute notches
        angle = np.arctan2(v, u)
        seg = int(np.floor((angle + np.pi) / (np.pi / 7.0)))
        return 7 if (seg % 2 == 0 and rad_norm > 0.91) else 2

    # Voronoi hexagonal scute centers in (u, v) plane
    # Central vertebral row + left/right costal rows
    centers = [
        (0.0, -0.58), (0.0, 0.0), (0.0, 0.58),
        (-0.56, -0.32), (0.56, -0.32),
        (-0.56, 0.32), (0.56, 0.32),
        (-0.48, -0.82), (0.48, -0.82),
        (-0.48, 0.82), (0.48, 0.82),
    ]
    dists = sorted(np.hypot(u - cu, v - cv) for cu, cv in centers)
    gap = dists[1] - dists[0]

    # Crisp dark forest green hexagonal seam lines between scutes
    if gap < 0.085:
        return 2
    # Gold central keel ridge & subtle inner scute bosses
    if abs(u) < 0.10 and abs(v) < 0.72 and dists[0] < 0.16:
        return 7
    if gap < 0.135 and dists[0] > 0.18:
        return 7 if (abs(u) < 0.28 and abs(v) < 0.65) else 3
    return 3


# ==========================================
# FORM A: SEA TURTLE (34 x 34 x 13)
# ==========================================
def build_a():
    grid = np.zeros((34, 34, 13), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 16.5

    # --- DOMED HEXAGONAL CARAPACE & SANDY CREAM PLASTRON (Y: 6..24, Z: 1..10) ---
    shell_cy = 14.8
    shell_rx = 7.6
    shell_ry_f = 9.4
    shell_ry_b = 8.8

    for x in range(X):
        dx = x - cx
        if abs(dx) > shell_rx + 0.5:
            continue
        for y in range(5, 25):
            dy = y - shell_cy
            ry = shell_ry_f if dy >= 0 else shell_ry_b
            # Slight heart-shaped taper toward rear of sea turtle shell
            taper = 1.0 - 0.16 * max(0.0, -dy / shell_ry_b)
            eff_rx = shell_rx * taper
            r2 = (dx / eff_rx) ** 2 + (dy / ry) ** 2
            if r2 > 1.0:
                continue
            r = np.sqrt(r2)

            # Plastron underside (Z: 1..3) — flat grounded belly with gentle upward edge curve
            z_bot = 1 if r < 0.76 else 2
            # Domed carapace top (Z: 4..10)
            dome_h = 6.2 * np.sqrt(max(0.0, 1.0 - r2 * 0.92))
            z_top = int(round(3.6 + dome_h))
            z_top = max(3, min(10, z_top))

            u = dx / eff_rx
            v = dy / ry
            col_top = scute_color(u, v, r)

            for z in range(z_bot, z_top + 1):
                if z <= 2:
                    # Sandy cream plastron with subtle central seam
                    if z == 1 and (abs(dx) < 0.8 or (int(round(dy)) % 4 == 0 and r < 0.7)):
                        grid[x, y, z] = 7 if abs(dx) < 0.8 else 4
                    else:
                        grid[x, y, z] = 4
                elif z == 3:
                    # Transition ridge: cream underbelly inside, dark green rim outside
                    grid[x, y, z] = 2 if r > 0.78 else 4
                elif z == z_top or r > 0.80:
                    grid[x, y, z] = col_top
                else:
                    grid[x, y, z] = 3

    # Subtle grounded plastron base pad at Z=0 so turtle rests cleanly
    fill_sym_box(grid, 0, 4, 10, 19, 0, 0, 4)
    fill_sym_box(grid, 0, 3, 9, 20, 0, 0, 4)
    fill_sym_box(grid, 0, 0, 11, 18, 0, 0, 2)

    # --- LONG SWEPT WING-LIKE FRONT FLIPPERS (x_off: 6..16, Y: 10..23, Z: 1..5) ---
    # Sea turtle front flippers sweep wide outward and gracefully back
    # (x_off, y_back, y_front, z0, z1)
    front_flipper = [
        (6,  18, 22, 2, 4),
        (7,  18, 22, 2, 4),
        (8,  17, 22, 2, 4),
        (9,  16, 22, 2, 4),
        (10, 15, 21, 2, 3),
        (11, 14, 20, 2, 3),
        (12, 13, 19, 2, 3),
        (13, 12, 18, 1, 3),
        (14, 11, 16, 1, 2),
        (15, 10, 14, 1, 2),
        (16, 10, 12, 1, 1),
    ]
    for x_off, y0, y1, z0, z1 in front_flipper:
        fill_sym_box(grid, x_off, x_off, y0, y1, z0, z1, 1)
        # Dark forest green armored leading edge
        fill_sym_box(grid, x_off, x_off, y1, y1, z0, z1, 2)
        # Sandy cream pale inner trailing edge
        if x_off <= 13:
            fill_sym_box(grid, x_off, x_off, y0, y0, z0, z0, 4)
        # Iconic deep teal sea-turtle flipper spots along upper surface
        if x_off in (8, 10, 12, 14):
            mid_y = (y0 + y1) // 2
            fill_sym_box(grid, x_off, x_off, mid_y, mid_y + 1, z1, z1, 8)
        if x_off in (9, 11, 13):
            fill_sym_box(grid, x_off, x_off, y1 - 1, y1 - 1, z1, z1, 8)

    # --- SMALLER SWEPT REAR FLIPPERS & STUBBY TAIL (Y: 1..8, Z: 1..4) ---
    rear_flipper = [
        # (y, x_off0, x_off1, z0, z1)
        (7, 3, 5, 2, 3),
        (6, 3, 6, 2, 3),
        (5, 4, 7, 1, 3),
        (4, 4, 8, 1, 2),
        (3, 5, 8, 1, 2),
        (2, 6, 8, 1, 1),
    ]
    for y, x0, x1, z0, z1 in rear_flipper:
        fill_sym_box(grid, x0, x1, y, y, z0, z1, 1)
        fill_sym_box(grid, x1, x1, y, y, z0, z1, 2)
        if y in (5, 3):
            fill_sym_box(grid, x0 + 1, x1 - 1, y, y, z1, z1, 8)
    # Stubby sea turtle tail
    fill_sym_box(grid, 0, 1, 5, 6, 2, 3, 1)
    fill_sym_box(grid, 0, 0, 3, 5, 2, 3, 2)

    # --- SCULPTED SEA TURTLE NECK & HEAD EXTENDING FORWARD (+Y: 23..32, Z: 3..10) ---
    # Neck emerging smoothly from front shell opening
    fill_sym_box(grid, 0, 2, 23, 26, 3, 6, 1)
    fill_sym_box(grid, 0, 1, 24, 26, 3, 3, 4)   # Cream throat underside
    fill_sym_box(grid, 0, 1, 24, 26, 6, 6, 2)   # Dark dorsal neck scales
    fill_sym_box(grid, 2, 2, 24, 25, 4, 5, 8)   # Teal neck spots

    # Rounded sculpted sea turtle head (Y: 26..32, Z: 4..9)
    head_slices = [
        # (y, rx, z_bot, z_top)
        (26, 2.7, 4, 8),
        (27, 3.1, 4, 9),
        (28, 3.2, 4, 9),
        (29, 3.1, 4, 9),
        (30, 2.8, 4, 8),
        (31, 2.2, 5, 8),
        (32, 1.5, 5, 7),
    ]
    for y, rx, zb, zt in head_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    if z == zb and y <= 31:
                        col = 4  # Sandy cream lower jaw
                    elif z == zt and dx <= 1.7:
                        col = 2  # Dark forest green crown scales
                    elif dx >= rx - 0.8 and (y + z) % 2 == 0 and y <= 28:
                        col = 8  # Deep teal cheek spots
                    else:
                        col = 1  # Olive-emerald turtle skin
                    grid[x, y, z] = col

    # Subtle beak nose ridge & smile line
    fill_sym_box(grid, 0, 1, 32, 32, 5, 6, 2)
    fill_sym_box(grid, 0, 0, 32, 32, 6, 7, 1)
    # Expressive bright ocean-cyan eyes with white specular glint
    fill_sym_box(grid, 2, 3, 29, 30, 7, 7, 5)   # Dark eye socket framing
    fill_sym_box(grid, 3, 3, 29, 30, 7, 7, 6)   # Ocean-cyan iris
    fill_sym_box(grid, 3, 3, 30, 30, 7, 7, 9)   # Bright white eye glint
    fill_sym_box(grid, 2, 2, 29, 30, 8, 8, 2)   # Expressive brow ridge

    # Hollow unseen shell interior to stay cleanly within 800-2,500 target
    hollow_interior_26(grid, 2, 9)

    return grid


# ==========================================
# FORM B: SEA-TURTLE GUARDIAN ROBOT (34 x 26 x 42)
# ==========================================
def build_b():
    grid = np.zeros((34, 26, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0   # 16.5
    cx_l = X // 2 - 1    # 16 (-X robot left)
    cx_r = X // 2        # 17 (+X robot right)

    # --- AMPHIBIOUS GUARDIAN BOOTS & WEBBED TOES (Z: 0..3) ---
    fill_sym_box(grid, 2, 6, 9, 16, 0, 1, 5)    # Dark slate heavy sole
    fill_sym_box(grid, 3, 5, 7, 9, 0, 2, 5)     # Rear stabilizer heel
    fill_sym_box(grid, 2, 6, 11, 16, 1, 2, 1)   # Emerald green foot armor
    fill_sym_box(grid, 3, 5, 13, 17, 1, 2, 2)   # Dark forest green toe guard
    # Webbed sea-turtle front claws
    fill_sym_box(grid, 2, 2, 17, 18, 0, 1, 4)   # Sandy cream inner claw
    fill_sym_box(grid, 4, 4, 17, 18, 0, 1, 4)   # Center cream claw
    fill_sym_box(grid, 6, 6, 17, 18, 0, 1, 4)   # Outer cream claw
    fill_sym_box(grid, 3, 5, 12, 15, 2, 3, 7)   # Gold ankle trim bar
    fill_sym_box(grid, 3, 5, 10, 13, 2, 3, 5)   # Ankle joint

    # --- LOWER LEGS WITH REAR-FLIPPER CALF FINS & HEX KNEE GUARDS (Z: 4..14) ---
    fill_sym_box(grid, 3, 5, 9, 13, 4, 13, 5)   # Inner dark slate frame
    fill_sym_box(grid, 2, 6, 11, 14, 4, 12, 1)  # Olive-emerald shin plating
    fill_sym_box(grid, 3, 5, 14, 14, 5, 11, 4)  # Sandy cream front shin panel (plastron echo)
    fill_sym_box(grid, 3, 5, 9, 10, 4, 12, 2)   # Dark forest green calf guard
    # Rear-flipper swept hydro-fins on outer calves (from Form A rear flippers!)
    fill_sym_box(grid, 6, 7, 8, 12, 4, 11, 1)
    fill_sym_box(grid, 7, 8, 7, 10, 4, 9, 8)    # Deep teal spotted fin blade
    fill_sym_box(grid, 8, 8, 6, 8, 4, 7, 6)     # Glowing ocean-cyan trailing edge
    # Rear calf hydro-jet nozzles
    fill_sym_box(grid, 3, 5, 8, 8, 6, 8, 5)
    fill_sym_box(grid, 4, 4, 7, 7, 6, 7, 6)
    # Sculpted hexagonal amber-and-gold knee guards (echoing carapace scutes!)
    fill_sym_box(grid, 2, 6, 13, 15, 12, 14, 2)
    fill_sym_box(grid, 3, 5, 15, 16, 12, 14, 3)
    fill_sym_box(grid, 3, 5, 16, 16, 13, 13, 7)
    fill_sym_box(grid, 4, 4, 16, 16, 13, 13, 6)

    # --- THIGHS & PLASTRON PELVIS SKIRT (Z: 14..22) ---
    fill_sym_box(grid, 3, 5, 9, 13, 14, 19, 5)
    fill_sym_box(grid, 3, 5, 12, 14, 15, 18, 1)
    fill_sym_box(grid, 3, 4, 14, 14, 16, 18, 4) # Cream front thigh strip
    fill_sym_box(grid, 5, 5, 10, 12, 15, 18, 8) # Teal side thigh panel
    # Pelvis / Waist
    fill_sym_box(grid, 0, 5, 9, 13, 19, 22, 5)
    fill_sym_box(grid, 2, 5, 13, 14, 19, 21, 4) # Plastron front hip plates
    fill_sym_box(grid, 2, 5, 14, 14, 21, 21, 7) # Gold waist trim
    fill_sym_box(grid, 5, 6, 10, 13, 19, 21, 2) # Side hip scute guards
    fill_sym_box(grid, 6, 6, 11, 12, 20, 20, 3)
    # Center hexagonal belt buckle
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 2)
    fill_sym_box(grid, 0, 1, 15, 15, 20, 21, 3)
    fill_sym_box(grid, 0, 0, 15, 15, 20, 20, 6)

    # --- HEROIC TORSO WITH PLASTRON & HEX SCUTE CHEST MOTIF (Z: 22..33) ---
    # Tapered mechanical abdomen
    fill_sym_box(grid, 0, 4, 9, 13, 22, 24, 5)
    fill_sym_box(grid, 0, 3, 13, 14, 22, 24, 4)
    fill_sym_box(grid, 0, 1, 14, 14, 22, 24, 2)
    # Broad armored torso core
    fill_sym_box(grid, 0, 6, 8, 14, 25, 32, 2)
    fill_sym_box(grid, 0, 5, 13, 16, 25, 31, 4)  # Sandy cream Plastron chest plate!
    fill_sym_box(grid, 0, 4, 15, 17, 26, 30, 4)
    # Plastron horizontal & vertical scute seam lines across cream chest
    fill_sym_box(grid, 0, 5, 16, 16, 28, 28, 2)
    fill_sym_box(grid, 3, 3, 15, 17, 25, 31, 2)
    # Prominent Amber/Gold Hexagonal Scute Emblem & Ocean-Cyan Core on Center Chest!
    fill_sym_box(grid, 0, 2, 16, 17, 26, 30, 2)  # Dark green hex border
    fill_sym_box(grid, 0, 2, 17, 17, 27, 29, 3)  # Warm amber hex scute
    fill_sym_box(grid, 0, 1, 17, 17, 26, 30, 3)
    fill_sym_box(grid, 0, 1, 17, 18, 27, 29, 7)  # Gold inner hex frame
    fill_sym_box(grid, 0, 1, 18, 18, 28, 28, 6)  # Glowing ocean-cyan hydro-core!
    fill_sym_box(grid, 0, 0, 18, 18, 29, 29, 9)  # Bright white core glint
    # Upper golden collar armor & side chest vents
    fill_sym_box(grid, 2, 5, 12, 15, 31, 32, 1)
    fill_sym_box(grid, 2, 4, 14, 16, 31, 32, 7)  # Gold collarbone plates
    fill_sym_box(grid, 4, 5, 14, 15, 26, 29, 3)  # Side amber scute accents

    # --- MASSIVE DOMED HEXAGONAL SHELL SHIELD / BACKPACK (Y: 2..8, Z: 19..35) ---
    # Directly Form A's iconic patterned sea-turtle carapace mounted vertically on the back!
    sh_cz = 27.0
    sh_rx = 7.8
    sh_rz = 8.4
    for x in range(X):
        dx = x - cx
        if abs(dx) > sh_rx + 0.5:
            continue
        for z in range(18, 36):
            dz = z - sh_cz
            # Gentle sea-turtle heart taper toward bottom of back-shield
            taper = 1.0 - 0.14 * max(0.0, -dz / sh_rz)
            eff_rx = sh_rx * taper
            r2 = (dx / eff_rx) ** 2 + (dz / sh_rz) ** 2
            if r2 > 1.0:
                continue
            r = np.sqrt(r2)
            # Dome projects rearward toward -Y (Y=8 at torso back out to Y=2 at shell apex)
            dome_depth = 5.4 * np.sqrt(max(0.0, 1.0 - r2 * 0.90))
            y_outer = int(round(7.6 - dome_depth))
            y_outer = max(2, min(8, y_outer))

            u = dx / eff_rx
            v = dz / sh_rz
            col_surf = scute_color(u, v, r)

            for y in range(y_outer, 9):
                if y == y_outer or r > 0.82:
                    grid[x, y, z] = col_surf
                elif y == 8:
                    grid[x, y, z] = 4  # Cream inner shell backing
                else:
                    grid[x, y, z] = 3

    # Solid spine mount connecting back shell cleanly to torso
    fill_sym_box(grid, 0, 4, 7, 9, 23, 31, 5)
    # Twin ocean-cyan hydro-thrusters tucked under lower rim of back shell
    fill_sym_box(grid, 2, 3, 5, 7, 19, 21, 5)
    fill_sym_box(grid, 2, 3, 4, 5, 19, 20, 6)

    # --- SHOULDERS & SWEPT FLIPPER-BLADE ARMS (Z: 13..34) - DIRECTLY FORM A'S FLIPPERS! ---
    # Shoulder joints
    fill_sym_box(grid, 5, 7, 10, 12, 29, 31, 5)
    # Rounded Sea-Turtle Shoulder Pauldrons (olive green + teal spots + amber/gold crest)
    fill_sym_box(grid, 6, 11, 9, 14, 28, 33, 1)
    fill_sym_box(grid, 7, 11, 10, 13, 33, 34, 2)  # Dark forest green top rim
    fill_sym_box(grid, 8, 10, 11, 13, 34, 34, 7)  # Gold crest ridge
    fill_sym_box(grid, 7, 10, 14, 14, 29, 32, 3)  # Amber front scute plate on shoulder
    fill_sym_box(grid, 11, 11, 9, 13, 28, 32, 8)  # Deep teal outer shoulder spot panel
    fill_sym_box(grid, 11, 11, 11, 12, 30, 31, 6) # Cyan hydro-dot

    # Articulated Upper Arms
    fill_sym_box(grid, 7, 9, 10, 12, 23, 28, 5)
    fill_sym_box(grid, 8, 9, 12, 13, 24, 27, 1)
    fill_sym_box(grid, 9, 9, 10, 12, 24, 27, 2)

    # Sweeping Sea-Turtle Flipper-Fin Forearms (both arms visibly formed from Form A's long flippers!)
    fill_sym_box(grid, 7, 10, 9, 14, 16, 22, 1)   # Olive-emerald forearm shell
    fill_sym_box(grid, 7, 8, 13, 14, 17, 21, 4)   # Cream inner flipper trim
    fill_sym_box(grid, 10, 11, 9, 14, 17, 23, 1)  # Outer flipper wing body
    # Long graceful swept flipper wing-fin flaring outward & downward along outer forearm!
    flipper_arm_fin = [
        # (x_off, y0, y1, z0, z1)
        (11, 8, 13, 15, 24),
        (12, 8, 13, 14, 22),
        (13, 9, 13, 13, 20),
        (14, 10, 13, 12, 18),
        (15, 11, 13, 11, 15),
    ]
    for x_off, y0, y1, z0, z1 in flipper_arm_fin:
        fill_sym_box(grid, x_off, x_off, y0, y1, z0, z1, 1)
        # Dark green armored leading edge
        fill_sym_box(grid, x_off, x_off, y1, y1, z0, z1, 2)
        # Deep teal sea-turtle spots on the flipper blade
        if x_off in (11, 13):
            fill_sym_box(grid, x_off, x_off, y0 + 1, y1 - 1, z0 + 2, z1 - 2, 8)
        # Glowing ocean-cyan hydro-cutting edge along lower/outer fin tip!
        if x_off >= 13:
            fill_sym_box(grid, x_off, x_off, y1, y1, z0, z0 + 2, 6)
        if x_off == 15:
            fill_sym_box(grid, x_off, x_off, y0, y1, z0, z0 + 1, 6)

    # Armored Mecha Fists
    fill_sym_box(grid, 7, 9, 10, 13, 14, 15, 5)
    fill_sym_box(grid, 8, 9, 13, 13, 14, 15, 2)

    # RIGHT HAND (+X, viewer's left): EXTENDED FLIPPER HYDRO-BLADE extending forward (+Y)
    fill_box(grid, cx_r + 8, cx_r + 9, 14, 17, 14, 16, 5)    # Wrist hilt mount
    fill_box(grid, cx_r + 8, cx_r + 9, 15, 16, 16, 17, 7)    # Gold guard
    fill_box(grid, cx_r + 8, cx_r + 9, 17, 22, 14, 16, 1)    # Olive flipper blade core
    fill_box(grid, cx_r + 9, cx_r + 9, 18, 21, 15, 15, 8)    # Teal spot stripe
    fill_box(grid, cx_r + 9, cx_r + 9, 17, 24, 14, 15, 6)    # Glowing ocean-cyan energy edge
    fill_box(grid, cx_r + 8, cx_r + 9, 23, 25, 14, 15, 6)    # Tapered hydro-blade tip
    fill_box(grid, cx_r + 9, cx_r + 9, 25, 25, 14, 14, 9)    # White tip glint

    # --- TURTLE HEAD AS ROBOT HEAD (Z: 33..41) - UNMISTAKABLY FORM A'S SEA TURTLE HEAD! ---
    # Mechanical neck & collar
    fill_sym_box(grid, 0, 1, 10, 13, 32, 34, 5)
    fill_sym_box(grid, 0, 1, 13, 13, 33, 33, 4)  # Cream throat continuation

    # Sculpted Sea Turtle Head sitting right on the robot's shoulders (Y: 9..18, Z: 34..40)
    robot_head_slices = [
        # (y, rx, z_bot, z_top)
        (9,  2.4, 35, 39),
        (10, 3.0, 34, 40),
        (11, 3.3, 34, 40),
        (12, 3.4, 34, 40),
        (13, 3.3, 34, 40),
        (14, 3.0, 34, 40),
        (15, 2.7, 34, 39),
        (16, 2.2, 34, 38),
        (17, 1.6, 35, 38),
        (18, 1.1, 35, 37),
    ]
    for y, rx, zb, zt in robot_head_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    if z == zb and y >= 11:
                        col = 4  # Sandy cream turtle lower jaw/chin!
                    elif z == zt and dx <= 1.8:
                        col = 2  # Dark forest green turtle crown scales
                    elif dx >= rx - 0.8 and y in (10, 11, 12) and z in (35, 36):
                        col = 8  # Deep teal turtle cheek spots
                    else:
                        col = 1  # Olive-emerald turtle head skin
                    grid[x, y, z] = col

    # Unmistakable sculpted sea-turtle beak snout tip
    fill_sym_box(grid, 0, 1, 17, 18, 35, 36, 2)
    fill_sym_box(grid, 0, 0, 18, 18, 36, 37, 1)
    fill_sym_box(grid, 0, 0, 17, 17, 34, 34, 4)  # Cream lower beak lip
    # Bright side-set sea-turtle eyes glowing ocean-cyan with crisp white glint!
    fill_sym_box(grid, 2, 3, 14, 15, 37, 37, 5)  # Subtle dark eye rim
    fill_sym_box(grid, 3, 3, 14, 15, 37, 37, 6)  # Glowing ocean-cyan turtle eyes
    fill_sym_box(grid, 2, 2, 16, 16, 37, 37, 6)  # Forward visor-eye wrap
    fill_sym_box(grid, 3, 3, 15, 15, 37, 37, 9)  # Bright white specular eye glint
    # Sleek compact Gold Guardian Forehead Crest (leaves olive-green turtle dome unmistakable!)
    fill_sym_box(grid, 0, 0, 15, 17, 38, 39, 7)
    fill_sym_box(grid, 1, 1, 15, 16, 39, 39, 7)
    fill_sym_box(grid, 0, 0, 14, 15, 40, 40, 7)
    fill_sym_box(grid, 0, 0, 17, 17, 38, 38, 6)  # Ocean-cyan forehead jewel

    # Hollow unseen interiors across legs, torso, shoulders & back-shell for crisp voxel count
    hollow_interior_26(grid, 1, 39)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=28, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "turtle_a.vox")
    v_b = export_vox(model_b, "turtle_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SEA TURTLE -> SEA-TURTLE GUARDIAN ROBOT",
        "1. SEA TURTLE",
        "2. SEA-TURTLE GUARDIAN ROBOT",
        "preview_turtle.png",
        yaw_a=38, pitch_a=28, yaw_b=32, pitch_b=20,
    )
    print(f"turtle: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
