import math
import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (168, 76, 54, 255),    # Dutch Terracotta Brick
    2: (224, 206, 174, 255),  # Warm Cream Plaster / Stucco
    3: (128, 82, 46, 255),    # Oak Timber / Sail Lattice
    4: (48, 54, 68, 255),     # Dark Slate Roof / Knight Armor & Joints
    5: (58, 114, 82, 255),    # Classic Dutch Windmill Green
    6: (132, 140, 152, 255),  # Weathered Limestone / Forged Steel
    7: (255, 212, 84, 255),   # Cozy Lantern Glow / Gold Visor & Crest
    8: (68, 42, 26, 255),     # Deep Walnut Wood / Heavy Spars & Door
    9: (248, 245, 236, 255),  # Bright Sailcloth White / Ivory Trim
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


def _in_octagon(dx, dy, r):
    """True if (dx, dy) lies inside a regular-looking chamfered octagon of radius r."""
    ax, ay = abs(dx), abs(dy)
    return ax <= r and ay <= r and (ax + ay) <= r * 1.44


def fill_oct_ring(grid, cx, cy, z, r_outer, r_inner, col, edge_col=None):
    """Fill a hollow (or solid if r_inner < 0) octagonal slice at height z."""
    X, Y, Z = grid.shape
    if not (0 <= z < Z):
        return
    r_ceil = int(math.ceil(r_outer)) + 1
    for x in range(max(0, int(cx - r_ceil)), min(X, int(cx + r_ceil) + 1)):
        for y in range(max(0, int(cy - r_ceil)), min(Y, int(cy + r_ceil) + 1)):
            dx = x - cx
            dy = y - cy
            if _in_octagon(dx, dy, r_outer):
                if r_inner < 0 or not _in_octagon(dx, dy, r_inner):
                    if edge_col is not None and abs(abs(dx) - abs(dy)) <= 0.6 and (abs(dx) + abs(dy)) >= r_outer * 1.15:
                        grid[x, y, z] = edge_col
                    else:
                        grid[x, y, z] = col


def draw_sail_blade(grid, cx, cz, y_base, dx, dz, px, pz, s_max, width=3.5, sweep_y=0, root_accent=False):
    """Draw one crisp, 6-connected diagonal windmill lattice sail blade.

    (dx, dz): unit-sign diagonal direction along the blade (each +-1).
    (px, pz): perpendicular trailing direction (each +-1, dx*px + dz*pz == 0).
    sweep_y: optional Y offset step for outer half (e.g. -1 for swept-back wings).
    """
    X, Y, Z = grid.shape
    inv_s2 = 1.0 / math.sqrt(2.0)
    span = int(math.ceil(s_max * inv_s2 + width + 2))
    x0 = max(0, int(math.floor(cx - span)))
    x1 = min(X - 1, int(math.ceil(cx + span)))
    z0 = max(0, int(math.floor(cz - span)))
    z1 = min(Z - 1, int(math.ceil(cz + span)))

    # Rung positions along blade length s
    rungs = [3.6, 7.2, 10.8, 14.4, s_max - 0.5]

    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            rx = x - cx
            rz = z - cz
            s = (rx * dx + rz * dz) * inv_s2
            t = (rx * px + rz * pz) * inv_s2

            if s < 0.0 or s > s_max + 0.35:
                continue

            # Determine Y layer(s) with overlap at transition for strict 6-connectivity
            if sweep_y == 0:
                ys = (y_base,)
            else:
                split_s = s_max * 0.45
                if s < split_s - 0.8:
                    ys = (y_base,)
                elif s <= split_s + 0.9:
                    ys = (y_base, y_base + sweep_y)
                else:
                    ys = (y_base + sweep_y,)

            col = 0
            # Main dark walnut spar (0.78 > 1/sqrt(2) guarantees strict 6-connectivity along 45 deg)
            if -0.78 <= t <= 0.78:
                col = 8
                if root_accent and 1.2 <= s <= 3.0:
                    col = 5
            # Sail lattice & cloth (starts away from hub at s >= 3.2)
            elif 3.2 <= s <= s_max + 0.1 and 0.78 < t <= width + 0.45:
                on_outer_rail = t >= width - 0.25
                on_mid_rail = 1.9 <= t <= 2.35 and s <= 6.2
                on_rung = any(abs(s - r) <= 0.38 for r in rungs)
                if on_outer_rail or on_rung or on_mid_rail:
                    col = 3
                elif s < 6.4:
                    # Open wooden lattice window near root for authentic Dutch mill look
                    if 1.45 <= t <= 2.75 and abs(s - 5.0) <= 0.8:
                        col = 0
                    else:
                        col = 2
                else:
                    # Crisp bright sailcloth canvas with warm cream border near spar
                    col = 2 if t < 1.2 else 9

            if col:
                for yy in ys:
                    if 0 <= yy < Y:
                        # Don't overwrite main dark spar with lighter lattice
                        if grid[x, yy, z] != 8 or col == 8:
                            grid[x, yy, z] = col


# ==========================================
# FORM A: DUTCH WINDMILL (36 x 28 x 44)
# ==========================================
def build_a():
    grid = np.zeros((36, 28, 44), dtype=np.uint8)
    cx = 17.5
    cy = 12.5

    # --- 1. OCTAGONAL STONE FOUNDATION PLINTH (Z: 0..1) ---
    fill_oct_ring(grid, cx, cy, 0, 7.2, 5.2, 6)
    fill_oct_ring(grid, cx, cy, 1, 6.8, 5.0, 6)
    # Stone front doorstep leading into arched doorway (+Y)
    fill_sym_box(grid, 0, 2, 19, 20, 0, 0, 6)
    fill_sym_box(grid, 0, 1, 19, 19, 1, 1, 6)

    # --- 2. LOWER OCTAGONAL TERRACOTTA BRICK TOWER (Z: 2..11, hollow) ---
    for z in range(2, 12):
        t = (z - 2) / 9.0
        r_out = 6.5 - 0.7 * t
        r_in = r_out - 1.35
        edge = 6 if (z % 2 == 0) else 1
        fill_oct_ring(grid, cx, cy, z, r_out, r_in, 1, edge_col=edge)

    # Front arched dark walnut wooden door (+Y face, Z: 2..7)
    fill_sym_box(grid, 0, 1, 18, 19, 2, 6, 8)
    fill_sym_box(grid, 0, 0, 18, 19, 7, 7, 8)
    # Oak door frame & glowing transom lantern above door
    fill_sym_box(grid, 2, 2, 18, 19, 2, 6, 3)
    fill_sym_box(grid, 1, 1, 18, 19, 7, 7, 3)
    fill_sym_box(grid, 0, 0, 19, 19, 8, 8, 7)

    # Lower brick side & rear cozy lit windows (Z: 5..7)
    for x_side in (11, 24):
        fill_box(grid, x_side, x_side, 12, 13, 5, 7, 7)
        fill_box(grid, x_side, x_side, 11, 11, 5, 7, 5)
        fill_box(grid, x_side, x_side, 14, 14, 5, 7, 5)
        fill_box(grid, x_side, x_side, 12, 13, 4, 4, 6)
        fill_box(grid, x_side, x_side, 12, 13, 8, 8, 3)
    # Rear window
    fill_sym_box(grid, 0, 0, 6, 7, 5, 7, 7)
    fill_sym_box(grid, 1, 1, 6, 7, 5, 7, 5)

    # --- 3. CANTILEVERED WOODEN DUTCH GALLERY / WALKWAY (Z: 10..13) ---
    # Diagonal oak support braces underneath deck
    for bx, by in [
        (10, 12), (25, 12), (17, 5), (18, 5), (17, 19), (18, 19),
        (12, 7), (23, 7), (12, 17), (23, 17),
    ]:
        fill_box(grid, bx, bx, by, by, 10, 10, 3)
    # Solid gallery deck ring (Z: 11)
    fill_oct_ring(grid, cx, cy, 11, 7.8, 4.8, 3)
    # Perimeter gallery railing (Z: 12 posts, Z: 13 Dutch green + white top rail)
    for x in range(9, 27):
        for y in range(4, 21):
            dx, dy = x - cx, y - cy
            if _in_octagon(dx, dy, 7.8) and not _in_octagon(dx, dy, 6.75):
                # Corner / regular vertical posts at Z=12
                if (x + y) % 2 == 0:
                    grid[x, y, 12] = 9 if (x + y) % 4 == 0 else 5
                # Continuous top handrail at Z=13
                grid[x, y, 13] = 5

    # --- 4. UPPER TAPERING CREAM PLASTER & TIMBER TOWER (Z: 12..25, hollow) ---
    for z in range(12, 26):
        t = (z - 12) / 13.0
        r_out = 5.6 - 1.35 * t
        r_in = r_out - 1.25
        # Timber ring bands at gallery base, mid-tower, and cap collar
        if z in (12, 18, 25):
            ring_col = 3
            edge_c = 8
        elif z == 24:
            ring_col = 5
            edge_c = 9
        else:
            ring_col = 2
            edge_c = 3
        fill_oct_ring(grid, cx, cy, z, r_out, r_in, ring_col, edge_col=edge_c)

    # Cozy warm-lit upper windows with dark frames & green shutters
    # Front upper window (+Y, Z: 15..17)
    fill_sym_box(grid, 0, 0, 17, 18, 15, 17, 7)
    fill_sym_box(grid, 1, 1, 17, 17, 15, 17, 5)
    fill_sym_box(grid, 0, 1, 17, 17, 14, 14, 8)
    # Side upper windows (Z: 20..21)
    for x_side in (13, 22):
        fill_box(grid, x_side, x_side, 12, 13, 20, 21, 7)
        fill_box(grid, x_side, x_side, 11, 11, 20, 21, 5)
        fill_box(grid, x_side, x_side, 14, 14, 20, 21, 5)
    # Rear upper window
    fill_sym_box(grid, 0, 0, 7, 8, 15, 17, 7)
    fill_sym_box(grid, 1, 1, 8, 8, 15, 17, 5)

    # --- 5. ROUNDED DARK-SLATE ROTATING CAP ROOF (Z: 26..33, hollow) ---
    cap_specs = [
        (26, 4.7, 3.2, 4, 5),
        (27, 4.8, 3.3, 4, 4),
        (28, 4.6, 3.1, 4, 4),
        (29, 4.1, 2.7, 4, 6),
        (30, 3.4, 2.0, 4, 4),
        (31, 2.5, 1.1, 4, 6),
        (32, 1.5, -1.0, 4, 4),
    ]
    for z, r_o, r_i, col, ecol in cap_specs:
        # Cap overhangs slightly toward front (+Y) to house the sail shaft
        fill_oct_ring(grid, cx, cy + 0.5, z, r_o, r_i, col, edge_col=ecol)

    # Dutch green front gable / "beard" plate under the sail hub (+Y)
    fill_sym_box(grid, 0, 2, 17, 18, 26, 28, 5)
    fill_sym_box(grid, 0, 1, 18, 18, 29, 30, 4)
    fill_sym_box(grid, 1, 2, 18, 18, 26, 26, 9)  # Ivory trim on beard

    # Roof ridge & golden weathervane finial (Z: 32..35)
    fill_sym_box(grid, 0, 0, 11, 15, 32, 32, 6)
    fill_sym_box(grid, 0, 0, 13, 13, 33, 34, 4)
    fill_sym_box(grid, 0, 0, 13, 14, 34, 34, 7)
    fill_sym_box(grid, 0, 0, 13, 13, 35, 35, 7)

    # --- 6. REAR TAILPOLE / KRUIPALEN (Y: 2..8, Z: 11..28) ---
    # Classic Dutch diagonal beams extending from back of cap down to gallery deck
    fill_sym_box(grid, 0, 0, 6, 9, 27, 27, 8)
    fill_sym_box(grid, 1, 2, 6, 8, 26, 26, 3)
    # Main central tailpole sloping down from (y=7, z=27) to (y=3, z=12)
    for step in range(16):
        z_p = 27 - step
        y_p = max(3, int(round(7.0 - step * 0.27)))
        fill_sym_box(grid, 0, 0, y_p, y_p + 1, z_p, z_p, 8 if step % 3 == 0 else 3)
    # Side diagonal braces meeting the tailpole and connecting solidly to the cap & gallery
    prev_x, prev_y = 2, 7
    for step in range(13):
        z_b = 26 - step
        y_b = max(4, int(round(7.0 - step * 0.23)))
        x_off = max(1, int(round(2.0 - step * 0.1)))
        fill_sym_box(grid, min(x_off, prev_x), max(x_off, prev_x), min(y_b, prev_y), max(y_b, prev_y), z_b, z_b, 3)
        prev_x, prev_y = x_off, y_b
    # Tie tailpole base solidly into gallery deck at Y=3..5, Z=11..14
    fill_sym_box(grid, 0, 1, 3, 5, 11, 14, 3)
    fill_sym_box(grid, 0, 0, 3, 4, 12, 13, 8)

    # --- 7. FRONT SAIL HUB & FOUR HUGE X-SHAPED LATTICE SAILS (Y: 18..24) ---
    hub_z = 27.5
    # Heavy oak/walnut windshaft emerging from front of cap
    fill_sym_box(grid, 0, 1, 18, 22, 26, 29, 8)
    fill_sym_box(grid, 0, 1, 21, 22, 27, 28, 4)
    # Golden decorative hub boss cap (+Y tip)
    fill_sym_box(grid, 0, 0, 23, 23, 27, 28, 7)

    # Four iconic cross-shaped lattice sails at 45 degrees (4-fold rotational symmetry!)
    blades = [
        (1, 1, 1, -1),    # Top-Right
        (-1, 1, 1, 1),    # Top-Left
        (-1, -1, -1, 1),  # Bottom-Left
        (1, -1, -1, -1),  # Bottom-Right
    ]
    for dx, dz, px, pz in blades:
        draw_sail_blade(grid, cx, hub_z, y_base=22, dx=dx, dz=dz, px=px, pz=pz, s_max=19.2, width=3.8)

    return grid


# ==========================================
# FORM B: WINDMILL VALKYRIE ROBOT (42 x 26 x 46)
# ==========================================
def build_b():
    grid = np.zeros((42, 26, 46), dtype=np.uint8)
    cx = 20.5

    # --- 1. FEET (Z: 0..3) - Stone Plinth Sabatons + Brick Toe Armor ---
    fill_sym_box(grid, 3, 5, 9, 17, 0, 1, 6)    # Weathered stone plinth sole
    fill_sym_box(grid, 3, 5, 13, 19, 0, 1, 4)   # Dark slate front foot pad
    fill_sym_box(grid, 4, 4, 11, 16, 0, 0, 0)   # Hollow sole underside
    fill_sym_box(grid, 3, 5, 14, 19, 2, 2, 1)   # Terracotta brick toe armor
    fill_sym_box(grid, 4, 4, 16, 19, 2, 3, 1)   # Raised armored toe ridge
    fill_sym_box(grid, 4, 4, 15, 16, 3, 3, 7)   # Gold ankle buckle
    fill_sym_box(grid, 3, 5, 8, 10, 0, 2, 8)    # Walnut heel spur
    fill_sym_box(grid, 3, 5, 11, 14, 2, 3, 4)   # Ankle joint block

    # --- 2. LOWER LEGS / GREAVES (Z: 3..15) - Split Octagonal Brick & Plaster Tower! ---
    # Lower half (Z: 3..10): Terracotta brick tower halves with limestone corner quoins
    fill_sym_box(grid, 3, 5, 10, 15, 3, 10, 1)
    fill_sym_box(grid, 4, 4, 11, 14, 4, 9, 0)   # Hollow core
    # Stone quoins along outer/front edges of brick tower legs
    for qz in (4, 6, 8, 10):
        fill_sym_box(grid, 5, 5, 15, 15, qz, qz, 6)
        fill_sym_box(grid, 3, 3, 15, 15, qz, qz, 6)
        fill_sym_box(grid, 5, 5, 10, 10, qz, qz, 6)
    # Cozy warm-lit windmill window embedded on outer calf of each leg!
    fill_sym_box(grid, 5, 5, 12, 13, 6, 8, 7)
    fill_sym_box(grid, 5, 5, 11, 11, 6, 8, 5)
    fill_sym_box(grid, 5, 5, 14, 14, 6, 8, 5)
    fill_sym_box(grid, 5, 5, 12, 13, 5, 5, 8)
    fill_sym_box(grid, 5, 5, 12, 13, 9, 9, 3)
    # Front shin timber beam & brick panel
    fill_sym_box(grid, 4, 4, 15, 16, 4, 9, 1)
    fill_sym_box(grid, 4, 4, 16, 16, 5, 8, 3)

    # Upper half of greave (Z: 11..15): Cream plaster upper tower + Dutch green gallery knee guard
    fill_sym_box(grid, 3, 5, 10, 15, 11, 14, 2)
    fill_sym_box(grid, 4, 4, 11, 14, 11, 13, 0)  # Hollow core
    fill_sym_box(grid, 3, 5, 10, 15, 11, 11, 3)  # Oak timber band between brick & plaster
    # Knee armor (gallery balustrade motif)
    fill_sym_box(grid, 3, 5, 15, 16, 12, 15, 5)
    fill_sym_box(grid, 4, 4, 16, 17, 13, 15, 9)
    fill_sym_box(grid, 4, 4, 17, 17, 14, 14, 7)  # Gold knee crest

    # --- 3. THIGHS (Z: 15..21) - Tapered Cream Plaster Columns & Oak Struts ---
    fill_sym_box(grid, 3, 5, 11, 14, 15, 21, 2)
    fill_sym_box(grid, 4, 4, 12, 13, 16, 20, 0)  # Hollow inside thigh
    fill_sym_box(grid, 5, 5, 12, 13, 16, 20, 3)  # Outer oak timber beam
    fill_sym_box(grid, 3, 5, 14, 15, 16, 20, 2)  # Front plaster thigh plate
    fill_sym_box(grid, 4, 4, 15, 15, 17, 19, 6)  # Steel ridge

    # --- 4. WAIST / VALKYRIE SKIRT ARMOR (Z: 20..24) - Windmill Gallery Motif ---
    fill_sym_box(grid, 0, 4, 10, 15, 20, 23, 4)  # Dark slate pelvis core
    fill_sym_box(grid, 1, 3, 11, 14, 21, 22, 0)  # Hollow pelvis core
    # Hip joint bars connecting solidly into thighs
    fill_sym_box(grid, 2, 5, 11, 14, 20, 21, 4)
    # Front & rear armored tassets (Dutch green + oak trim + ivory border)
    fill_sym_box(grid, 2, 5, 15, 16, 20, 23, 5)
    fill_sym_box(grid, 2, 5, 16, 16, 20, 20, 9)
    fill_sym_box(grid, 2, 5, 9, 10, 20, 23, 5)
    # Side hip skirts
    fill_sym_box(grid, 6, 6, 11, 14, 19, 23, 5)
    fill_sym_box(grid, 6, 6, 12, 13, 20, 22, 3)
    fill_sym_box(grid, 6, 6, 11, 14, 19, 19, 9)
    # Central codpiece featuring the windmill's arched dark walnut door & lantern!
    fill_sym_box(grid, 0, 1, 15, 17, 20, 23, 8)
    fill_sym_box(grid, 0, 1, 16, 17, 23, 23, 3)
    fill_sym_box(grid, 0, 0, 17, 17, 21, 22, 7)
    # Slim armored waist (Z: 23..25)
    fill_sym_box(grid, 0, 3, 10, 15, 23, 25, 4)
    fill_sym_box(grid, 0, 2, 11, 14, 24, 24, 0)  # Hollow waist interior
    fill_sym_box(grid, 0, 3, 15, 15, 24, 24, 3)

    # --- 5. TORSO / CHEST ARMOR (Z: 25..34) - Plaster Tower + Lit Window Core + Slate Collar ---
    fill_sym_box(grid, 0, 5, 10, 16, 25, 32, 2)  # Main cream plaster chest block
    fill_sym_box(grid, 0, 4, 11, 15, 26, 31, 0)  # Hollow inside torso
    # Terracotta brick lower chest ribs & side armor
    fill_sym_box(grid, 4, 5, 11, 15, 25, 28, 1)
    fill_sym_box(grid, 0, 4, 15, 16, 25, 26, 3)  # Oak timber chest belt
    # Sculpted knight pectoral plates (plaster + oak trim)
    fill_sym_box(grid, 2, 4, 16, 17, 27, 31, 2)
    fill_sym_box(grid, 4, 5, 16, 16, 28, 31, 3)
    fill_sym_box(grid, 2, 4, 17, 17, 30, 31, 5)  # Dutch green upper chest trim
    fill_sym_box(grid, 3, 3, 17, 17, 28, 29, 9)  # Ivory highlight

    # Iconic glowing windmill window chest reactor! (+Y center)
    fill_sym_box(grid, 0, 1, 16, 18, 27, 31, 8)  # Walnut window frame
    fill_sym_box(grid, 0, 1, 18, 18, 28, 30, 7)  # Bright warm golden glow
    fill_sym_box(grid, 0, 0, 18, 18, 29, 29, 9)  # Bright center cross glint
    fill_sym_box(grid, 0, 1, 17, 18, 31, 31, 3)  # Timber lintel

    # Rounded dark-slate collar / gorget (from windmill cap roof!) (Z: 32..34)
    fill_sym_box(grid, 0, 5, 10, 16, 32, 33, 4)
    fill_sym_box(grid, 2, 4, 11, 15, 34, 34, 4)
    fill_sym_box(grid, 1, 4, 16, 16, 32, 33, 5)  # Dutch green beard/collar trim
    fill_sym_box(grid, 0, 1, 16, 16, 32, 32, 7)  # Gold throat brooch

    # --- 6. SHOULDERS (Z: 28..36, X_off: 6..10) - Split Rounded Dark-Slate Cap Roof Pauldrons ---
    # Inner shoulder joint
    fill_sym_box(grid, 5, 7, 11, 14, 29, 32, 4)
    # Domed dark-slate windmill-cap pauldrons!
    fill_sym_box(grid, 6, 10, 10, 16, 30, 34, 4)
    fill_sym_box(grid, 7, 9, 11, 15, 30, 34, 0)  # Hollow inside pauldron
    fill_sym_box(grid, 7, 10, 11, 15, 35, 35, 4) # Curved slate roof crown
    fill_sym_box(grid, 8, 9, 12, 14, 36, 36, 6)  # Limestone/steel roof ridge peak
    # Architectural accents on pauldrons
    fill_sym_box(grid, 6, 10, 10, 16, 30, 30, 5) # Dutch green lower roof eaves
    fill_sym_box(grid, 10, 10, 11, 15, 31, 34, 6)# Steel outer trim band
    fill_sym_box(grid, 10, 10, 12, 14, 32, 33, 7)# Warm gold rivet/window accent
    fill_sym_box(grid, 7, 9, 16, 16, 31, 33, 9)  # Crisp ivory gable edge

    # --- 7. ARMS & GAUNTLETS (Z: 15..29) ---
    # Upper arms (oak timber + dark slate joints)
    fill_sym_box(grid, 7, 8, 11, 14, 24, 29, 4)
    fill_sym_box(grid, 8, 8, 12, 13, 25, 28, 3)
    # Elbow joints
    fill_sym_box(grid, 7, 8, 11, 14, 23, 24, 6)
    # Forearms / knight vambraces (cream plaster + terracotta brick + gold cuff)
    fill_sym_box(grid, 7, 9, 11, 15, 17, 23, 2)
    fill_sym_box(grid, 8, 8, 12, 14, 18, 22, 0)  # Hollow forearm interior
    fill_sym_box(grid, 9, 9, 11, 15, 18, 22, 1)  # Outer terracotta armor plate
    fill_sym_box(grid, 7, 9, 15, 15, 18, 22, 3)  # Front oak beam guard
    fill_sym_box(grid, 7, 9, 11, 15, 17, 17, 7)  # Gold wrist cuff
    # Fists (Z: 15..16)
    fill_sym_box(grid, 7, 8, 12, 14, 15, 16, 4)

    # --- 8. RIGHT HAND (+X): TAILPOLE WIND-LANCE HALBERD (Viewer's left in front view) ---
    # Right fist is at x = 28..29, y = 12..14, z = 15..16
    # Gripped angled/upright knight halberd (oak tailpole shaft + steel/ivory/gold blade)
    fill_box(grid, 28, 29, 14, 16, 15, 16, 8)    # Solid grip bridge into right fist
    # Tall walnut & oak shaft (Z: 8..27 at Y=16..17)
    fill_box(grid, 29, 29, 16, 17, 8, 25, 8)
    for sz in (11, 18, 22):
        fill_box(grid, 29, 29, 16, 17, sz, sz + 1, 3)
    fill_box(grid, 29, 29, 16, 17, 7, 7, 7)      # Gold butt cap
    # Dutch green & gold halberd collar / cross-guard (Z: 24..25)
    fill_box(grid, 28, 30, 15, 18, 24, 25, 5)
    fill_box(grid, 29, 29, 17, 18, 24, 25, 7)
    # Gleaming forged-steel & ivory wind-lance blade rising high (Z: 26..34)
    fill_box(grid, 29, 29, 16, 18, 26, 30, 6)
    fill_box(grid, 29, 29, 18, 19, 26, 31, 9)    # Bright ivory cutting edge (+Y)
    fill_box(grid, 29, 29, 17, 18, 31, 33, 9)    # Tapered spear tip
    fill_box(grid, 29, 29, 17, 17, 34, 34, 7)    # Gold tip finial
    fill_box(grid, 29, 29, 15, 15, 27, 29, 7)    # Rear gold halberd hook

    # --- 9. LEFT FOREARM (-X): MILL-CREST KITE SHIELD (Viewer's right in front view) ---
    # Left forearm outer face is at x = 20-9 = 11, y = 11..15, z = 17..23
    fill_box(grid, 10, 10, 10, 16, 15, 24, 5)    # Dutch green shield rim
    fill_box(grid, 9, 9, 11, 15, 16, 23, 1)      # Terracotta brick shield face
    fill_box(grid, 9, 10, 12, 14, 14, 15, 5)     # Tapered lower kite point
    fill_box(grid, 9, 9, 13, 13, 13, 13, 7)      # Gold bottom tip
    # Iconic windmill cross emblem embossed on shield!
    fill_box(grid, 9, 9, 13, 13, 17, 22, 9)
    fill_box(grid, 9, 9, 11, 15, 19, 20, 9)
    fill_box(grid, 9, 9, 13, 13, 19, 20, 7)      # Gold center boss
    # Connect shield mount bracket solidly to forearm
    fill_box(grid, 10, 11, 12, 14, 18, 22, 4)

    # --- 10. NOBLE VALKYRIE KNIGHT HEAD (Z: 33..42) ---
    # Neck
    fill_sym_box(grid, 0, 1, 12, 14, 33, 34, 4)
    # Helmet main dome (dark slate roof cap!)
    fill_sym_box(grid, 0, 2, 10, 15, 35, 39, 4)
    fill_sym_box(grid, 0, 1, 11, 14, 40, 40, 4)
    fill_sym_box(grid, 0, 1, 11, 14, 36, 38, 0)  # Hollow helmet interior
    # Cream plaster knight faceplate / chin guard
    fill_sym_box(grid, 0, 1, 15, 16, 35, 36, 2)
    fill_sym_box(grid, 0, 0, 16, 16, 35, 35, 1)  # Terracotta chin gem
    # Crisp warm golden visor slit (Z: 37) framed by dark slate brow (Z: 38)
    fill_sym_box(grid, 0, 1, 15, 16, 37, 37, 7)
    fill_sym_box(grid, 0, 2, 15, 16, 38, 38, 4)  # Distinct dark slate helmet brow!
    fill_sym_box(grid, 0, 0, 16, 16, 39, 40, 7)  # Small golden forehead jewel/crest center
    # Swept Valkyrie Winged Crest / Tiara (Z: 39..43)
    fill_sym_box(grid, 1, 1, 15, 16, 39, 39, 7)
    fill_sym_box(grid, 2, 2, 14, 15, 39, 40, 7)
    fill_sym_box(grid, 3, 3, 13, 14, 40, 41, 9)
    fill_sym_box(grid, 4, 4, 12, 13, 41, 42, 9)
    # Steel ear pods
    fill_sym_box(grid, 3, 3, 12, 13, 36, 38, 6)

    # --- 11. MASSIVE X-SHAPED WINDMILL SAIL CROSS-WING BACKPACK (Y: 4..10) ---
    # Heavy central rotor-hub backpack bolted solidly to torso back (Y: 6..10, Z: 25..32)
    fill_sym_box(grid, 0, 4, 7, 10, 25, 32, 4)   # Dark slate backpack housing
    fill_sym_box(grid, 0, 3, 8, 9, 26, 31, 0)    # Hollow backpack interior
    fill_sym_box(grid, 0, 3, 6, 7, 26, 31, 8)    # Deep walnut windmill windshaft hub
    fill_sym_box(grid, 0, 2, 5, 6, 27, 30, 6)    # Forged steel rotor bearing
    fill_sym_box(grid, 0, 1, 5, 5, 28, 29, 7)    # Golden rear hub cap (pops in REAR VIEW!)
    # Dutch green vents & thruster nozzles on lower backpack
    fill_sym_box(grid, 2, 3, 7, 8, 25, 26, 5)
    fill_sym_box(grid, 2, 3, 7, 8, 24, 24, 6)
    fill_sym_box(grid, 1, 2, 7, 8, 32, 33, 5)

    # FOUR HUGE ICONIC LATTICE WINDMILL SAILS AS A GRAND X-SHAPED CROSS-WING!
    # Hub center at (cx=20.5, cz=28.5), mounted at y=6 sweeping back to y=5 for dramatic 3D flare!
    wing_cz = 28.5
    upper_blades = [
        (1, 1, 1, -1),    # Top-Right wing (viewer's upper left)
        (-1, 1, -1, -1),  # Top-Left wing (symmetric mirror for heroic Valkyrie wings!)
    ]
    lower_blades = [
        (1, -1, 1, 1),    # Bottom-Right wing
        (-1, -1, -1, 1),  # Bottom-Left wing
    ]
    for dx, dz, px, pz in upper_blades:
        draw_sail_blade(
            grid, cx, wing_cz, y_base=6,
            dx=dx, dz=dz, px=px, pz=pz,
            s_max=23.0, width=3.9, sweep_y=-1, root_accent=True,
        )
    for dx, dz, px, pz in lower_blades:
        draw_sail_blade(
            grid, cx, wing_cz, y_base=6,
            dx=dx, dz=dz, px=px, pz=pz,
            s_max=22.0, width=3.7, sweep_y=-1, root_accent=True,
        )

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=34, pitch_a=20, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "windmill_a.vox")
    v_b = export_vox(model_b, "windmill_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: DUTCH WINDMILL -> WINDMILL VALKYRIE ROBOT",
        "1. DUTCH WINDMILL",
        "2. WINDMILL VALKYRIE ROBOT",
        "preview_windmill.png",
        yaw_a=34, pitch_a=20, yaw_b=32, pitch_b=20,
    )
    print(f"windmill: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
