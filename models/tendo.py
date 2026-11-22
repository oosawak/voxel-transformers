import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Form A: Gray-dominant Tendo Robot (subtle white accent on right wing-binder)
# Form B: Half-bird Gerwalk form (bird legs + wings, iridescent blue begins to emerge!)
# Form C: Saburo's Glossy Structural-Blue Crow (full iridescent blue sheen, ONE wing retains original white!)
PALETTE = {
    1: (144, 152, 166, 255),  # Cool Slate-Gray Armor (dominant in Form A)
    2: (196, 204, 218, 255),  # Light Metallic Silver-Gray Armor Highlights
    3: (44, 48, 58, 255),     # Dark Charcoal-Slate Frame, Beak & Talons
    4: (22, 42, 94, 255),     # Deep Raven Midnight-Blue (structural base)
    5: (36, 102, 204, 255),   # Glossy Cobalt-Sapphire Structural Blue
    6: (92, 192, 250, 255),   # Luminous Iridescent Cerulean-Cyan Specular Sheen!
    7: (66, 56, 156, 255),    # Iridescent Violet-Indigo Shadow Sheen
    8: (246, 248, 252, 255),  # Pure Original White (preserved on ONE wing of Saburo's crow!)
    9: (248, 198, 48, 255),   # Sharp Amber-Gold Eyes & Crest Accent
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(int(x0), int(x1))), min(X - 1, max(int(x0), int(x1)))
    y0, y1 = max(0, min(int(y0), int(y1))), min(Y - 1, max(int(y0), int(y1)))
    z0, z1 = max(0, min(int(z0), int(z1))), min(Z - 1, max(int(z0), int(z1)))
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center (requires even X)."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


def fill_sphere_local(grid, cx, cy, cz, rx, ry, rz, col):
    """Fill an ellipsoid centered at (cx, cy, cz)."""
    X, Y, Z = grid.shape
    x0 = max(0, int(np.floor(cx - rx)))
    x1 = min(X - 1, int(np.ceil(cx + rx)))
    y0 = max(0, int(np.floor(cy - ry)))
    y1 = min(Y - 1, int(np.ceil(cy + ry)))
    z0 = max(0, int(np.floor(cz - rz)))
    z1 = min(Z - 1, int(np.ceil(cz + rz)))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                d2 = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                if d2 <= 1.0:
                    grid[x, y, z] = col


def draw_6conn_line(grid, p0, p1, col, pad=(0, 0, 0), only_empty=False):
    """Draw a guaranteed 6-connected line between 3D points p0 and p1."""
    X, Y, Z = grid.shape
    x0, y0, z0 = int(round(p0[0])), int(round(p0[1])), int(round(p0[2]))
    x1, y1, z1 = int(round(p1[0])), int(round(p1[1])), int(round(p1[2]))
    steps = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1) * 2
    prev = None
    px, py, pz = pad

    def stamp(cx_, cy_, cz_):
        xa, xb = max(0, cx_ - px), min(X - 1, cx_ + px)
        ya, yb = max(0, cy_ - py), min(Y - 1, cy_ + py)
        za, zb = max(0, cz_ - pz), min(Z - 1, cz_ + pz)
        if only_empty:
            sub = grid[xa:xb + 1, ya:yb + 1, za:zb + 1]
            sub[sub == 0] = col
        else:
            grid[xa:xb + 1, ya:yb + 1, za:zb + 1] = col

    for i in range(steps + 1):
        t = i / steps
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        z = int(round(z0 + (z1 - z0) * t))
        if prev is not None:
            ox, oy, oz = prev
            if x != ox:
                stamp(x, oy, oz)
                ox = x
            if y != oy:
                stamp(ox, y, oz)
                oy = y
            if z != oz:
                stamp(ox, oy, z)
        else:
            stamp(x, y, z)
        prev = (x, y, z)


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


def check_6_connected(grid):
    """Return number of 6-connected components and min Z."""
    xs, ys, zs = np.nonzero(grid)
    if len(xs) == 0:
        return 0, -1
    occupied = set(zip(xs.tolist(), ys.tolist(), zs.tolist()))
    visited = set()
    components = 0
    for start in occupied:
        if start in visited:
            continue
        components += 1
        q = deque([start])
        visited.add(start)
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nb = (x + dx, y + dy, z + dz)
                if nb in occupied and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
    return components, int(zs.min())


# ============================================================
# FORM A: TENDO ROBOT (GRAY-DOMINANT BASE) (40 x 26 x 45)
# ============================================================
def build_a():
    grid = np.zeros((40, 26, 45), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 19 (-X, robot left / viewer's right)
    cx_r = X // 2      # 20 (+X, robot right / viewer's left — carries the white feather wing!)

    # --- 1. GRAY ARMORED BOOTS WITH SUBTLE TALON TOES (Z: 0..3) ---
    fill_sym_box(grid, 2, 5, 9, 16, 0, 1, 3)      # Charcoal sole
    fill_sym_box(grid, 2, 5, 10, 16, 1, 2, 1)     # Slate-gray boot armor
    fill_sym_box(grid, 2, 2, 16, 17, 0, 1, 3)     # Split avian toe-guards
    fill_sym_box(grid, 4, 4, 16, 18, 0, 1, 2)
    fill_sym_box(grid, 5, 5, 16, 17, 0, 1, 3)
    fill_sym_box(grid, 3, 4, 8, 9, 0, 2, 3)       # Rear talon-heel spur
    fill_sym_box(grid, 3, 4, 11, 14, 3, 4, 3)     # Ankle joint

    # --- 2. SLEEK GRAY GREAVES / SHIN ARMOR (Z: 4..14) ---
    fill_sym_box(grid, 2, 5, 10, 15, 4, 13, 1)    # Cool slate-gray armor
    fill_sym_box(grid, 3, 4, 15, 16, 5, 12, 2)    # Silver-gray shin bevel
    fill_sym_box(grid, 5, 5, 11, 14, 6, 11, 2)    # Outer feather-fin plate
    fill_sym_box(grid, 3, 4, 9, 10, 6, 10, 3)     # Rear calf thruster
    # Sharp avian knee guards
    fill_sym_box(grid, 2, 5, 14, 16, 12, 15, 1)
    fill_sym_box(grid, 3, 4, 16, 17, 13, 15, 2)
    fill_sym_box(grid, 3, 4, 16, 16, 12, 12, 4)   # Subtle hint of deep blue seam

    # --- 3. THIGHS & GRAY KUSAZURI WAIST ARMOR (Z: 14..22) ---
    fill_sym_box(grid, 2, 4, 10, 14, 14, 19, 3)
    fill_sym_box(grid, 2, 5, 12, 15, 15, 18, 1)
    fill_sym_box(grid, 3, 4, 15, 15, 16, 17, 2)
    fill_sym_box(grid, 0, 5, 10, 14, 19, 22, 3)   # Pelvis core
    fill_sym_box(grid, 1, 5, 14, 15, 17, 21, 1)   # Front gray tassets
    fill_sym_box(grid, 1, 5, 15, 15, 17, 17, 2)   # Silver lower hem
    fill_sym_box(grid, 5, 6, 10, 14, 17, 21, 1)   # Side hip plates
    fill_sym_box(grid, 0, 5, 9, 10, 17, 21, 1)    # Rear gray tail-skirt
    fill_sym_box(grid, 0, 1, 15, 16, 19, 22, 2)   # Center front loin plate
    fill_sym_box(grid, 0, 0, 16, 16, 20, 21, 9)   # Small gold buckle dot

    # --- 4. GRAY SAMURAI-MECHA CHEST CUIRASS (Z: 22..32) ---
    fill_sym_box(grid, 0, 4, 10, 14, 22, 24, 3)
    fill_sym_box(grid, 0, 3, 14, 15, 22, 24, 1)
    fill_sym_box(grid, 0, 6, 9, 15, 25, 31, 1)    # Main slate-gray torso
    fill_sym_box(grid, 0, 5, 15, 16, 25, 31, 2)   # Silver-gray angled chest plates
    fill_sym_box(grid, 2, 5, 16, 16, 27, 30, 1)   # Layered gray breastplate
    fill_sym_box(grid, 0, 1, 16, 17, 27, 29, 3)   # Dark charcoal chest center
    fill_sym_box(grid, 0, 0, 17, 17, 28, 28, 5)   # Single faint dormant blue core!
    fill_sym_box(grid, 1, 4, 11, 14, 31, 32, 2)   # High silver-gray collar

    # --- 5. FOLDED BACK WING-BINDERS (GRAY, WITH ORIGINAL WHITE ON RIGHT WING +X!) ---
    fill_sym_box(grid, 0, 4, 7, 9, 24, 31, 3)     # Backpack frame
    fill_sym_box(grid, 0, 3, 6, 7, 25, 30, 1)     # Gray central housing
    # Left wing-binder (-X, viewer's right): purely gray tones
    for i in range(13):
        z_w = 21 + i
        x_w = 4 + i // 4
        y_w = 6 - i // 5
        fill_box(grid, cx_l - (x_w + 1), cx_l - x_w, y_w, y_w + 2, z_w, z_w, 1)
        fill_box(grid, cx_l - (x_w + 2), cx_l - (x_w + 1), y_w, y_w + 1, z_w, z_w, 2 if i % 2 == 0 else 3)
    # Right wing-binder (+X, viewer's left): gray outer + ORIGINAL WHITE inner feather edge!
    for i in range(13):
        z_w = 21 + i
        x_w = 4 + i // 4
        y_w = 6 - i // 5
        fill_box(grid, cx_r + x_w, cx_r + x_w + 1, y_w, y_w + 2, z_w, z_w, 1)
        fill_box(grid, cx_r + x_w + 1, cx_r + x_w + 2, y_w, y_w + 1, z_w, z_w, 8 if i >= 3 else 2)

    # --- 6. LAYERED GRAY SHOULDER PAULDRONS & ARMS (Z: 14..33) ---
    fill_sym_box(grid, 6, 8, 11, 14, 28, 31, 3)
    fill_sym_box(grid, 7, 10, 10, 15, 27, 32, 1)  # Layered slate-gray pauldrons
    fill_sym_box(grid, 8, 10, 10, 15, 31, 32, 2)  # Silver upper bevel
    fill_sym_box(grid, 10, 10, 11, 14, 28, 30, 3) # Charcoal seam
    # Subtle white feather trim on right shoulder (+X) echoing the white wing!
    fill_box(grid, cx_r + 9, cx_r + 10, 11, 14, 32, 33, 8)
    # Arms
    fill_sym_box(grid, 7, 8, 11, 14, 22, 27, 3)   # Upper arms
    fill_sym_box(grid, 7, 9, 11, 15, 16, 21, 1)   # Forearm gauntlets
    fill_sym_box(grid, 9, 9, 12, 14, 17, 20, 2)   # Silver forearm blade-guard
    fill_sym_box(grid, 7, 8, 12, 14, 14, 15, 3)   # Armored fists

    # --- 7. GRAY RAVEN-CRESTED HEAD (Z: 32..43) ---
    fill_sym_box(grid, 0, 1, 11, 14, 32, 33, 3)   # Neck
    fill_sym_box(grid, 0, 2, 10, 14, 33, 39, 1)   # Slate-gray helmet dome
    fill_sym_box(grid, 0, 3, 10, 13, 33, 36, 2)   # Silver-gray cheek/neck plates
    fill_sym_box(grid, 0, 2, 14, 15, 33, 35, 3)   # Dark beak-like face mask
    fill_sym_box(grid, 0, 0, 15, 16, 34, 35, 2)   # Subtle pointed gray mask ridge
    fill_sym_box(grid, 0, 2, 14, 15, 36, 37, 3)   # Eye visor recess
    fill_sym_box(grid, 1, 2, 15, 15, 36, 36, 9)   # Sharp amber-gold eyes!
    # Swept-back gray bird-crest on helmet crown
    fill_sym_box(grid, 0, 1, 14, 16, 38, 39, 2)
    draw_6conn_line(grid, (cx_r, 15, 39), (cx_r + 2, 12, 43), 2)
    draw_6conn_line(grid, (cx_l, 15, 39), (cx_l - 2, 12, 43), 2)
    fill_sym_box(grid, 0, 0, 11, 15, 39, 41, 1)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: HALF-BIRD INTERMEDIATE (BIRD LEGS + WINGS, BLUE EMERGING!) (52 x 34 x 42)
# ============================================================
def build_b():
    grid = np.zeros((52, 34, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 25 (-X, robot left / viewer's right)
    cx_r = X // 2      # 26 (+X, robot right / viewer's left — retains white feathers!)

    # --- 1. REVERSE-JOINTED BIRD LEGS & CLAWED TALONS (Z: 0..17) ---
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        def lx(off):
            return int(round(bx + sign * off))

        # Grounded 3-toed front talons + rear hallux claw (Z: 0..2)
        fill_box(grid, lx(3), lx(5), 14, 18, 0, 1, 3)
        # Three forward spreading avian toes!
        draw_6conn_line(grid, (lx(3), 18, 1), (lx(2), 22, 0), 3)
        draw_6conn_line(grid, (lx(4), 18, 1), (lx(4), 23, 0), 3)
        draw_6conn_line(grid, (lx(5), 18, 1), (lx(6), 22, 0), 3)
        # Rear claw
        draw_6conn_line(grid, (lx(4), 14, 1), (lx(4), 11, 0), 3)

        # Lower avian tarsus angling BACKWARD & UP to reverse-joint ankle (Z: 1..9)
        draw_6conn_line(grid, (lx(4), 17, 1), (lx(4), 12, 8), 3, pad=(1, 1, 0))
        # Blue-tinted armor emerging on ankle-joint!
        fill_box(grid, lx(3), lx(5), 11, 13, 7, 9, 4)
        fill_box(grid, lx(4), lx(5), 11, 12, 8, 9, 5)
        # Upper avian drumstick angling FORWARD & UP to hip (Z: 9..16)
        draw_6conn_line(grid, (lx(4), 12, 9), (lx(4), 18, 16), 1, pad=(1, 1, 1))
        # Iridescent blue armor scales emerging along front of thighs!
        fill_box(grid, lx(3), lx(5), 16, 19, 12, 16, 4)
        fill_box(grid, lx(4), lx(5), 18, 19, 13, 15, 5)
        fill_box(grid, lx(4), lx(4), 19, 19, 14, 15, 6)  # Emerging cerulean sheen!

    # --- 2. FORWARD-LEANING HALF-BIRD TORSO (GRAY SHIFTING TO STRUCTURAL BLUE!) (Z: 16..31) ---
    fill_sym_box(grid, 0, 5, 13, 21, 16, 20, 3)   # Pelvis & waist
    fill_sym_box(grid, 0, 5, 14, 22, 20, 29, 1)   # Core slate-gray torso
    # Emerging glossy structural blue sweeping across the chest & breastbone!
    fill_sym_box(grid, 0, 4, 21, 23, 21, 28, 4)   # Deep midnight-blue chest
    fill_sym_box(grid, 0, 3, 22, 24, 22, 27, 5)   # Glossy cobalt chest keel!
    fill_sym_box(grid, 0, 1, 24, 24, 24, 26, 6)   # Cerulean structural highlight!
    fill_sym_box(grid, 2, 4, 22, 23, 22, 24, 7)   # Violet-indigo iridescent tint
    fill_sym_box(grid, 3, 5, 17, 21, 25, 29, 2)   # Remaining silver-gray side plates
    # Tail feathers emerging backward from lower back (gray + deep blue tips!)
    for i in range(9):
        ty = 12 - i
        tz = 17 - i // 3
        hw = 2 + i // 3
        col_t = 1 if i < 3 else (4 if i < 6 else 5)
        fill_sym_box(grid, 0, hw, ty, ty, tz, tz + 1, col_t)
        if i >= 6:
            fill_sym_box(grid, hw, hw, ty, ty, tz + 1, tz + 1, 6)

    # --- 3. HALF-TRANSFORMED ARMS / TALONED GAUNTLETS (Z: 16..29) ---
    fill_sym_box(grid, 6, 8, 17, 21, 24, 28, 1)   # Gray shoulder armor
    fill_sym_box(grid, 7, 8, 19, 21, 27, 28, 5)   # Blue sheen on upper shoulders
    fill_sym_box(grid, 6, 7, 18, 21, 19, 23, 3)   # Upper arm
    fill_sym_box(grid, 6, 8, 19, 25, 17, 19, 1)   # Forward-angled forearms
    fill_sym_box(grid, 7, 8, 22, 25, 18, 19, 4)   # Blue emerging on forearm gauntlets
    fill_sym_box(grid, 6, 8, 25, 27, 17, 18, 3)   # Clawed avian hands

    # --- 4. UNFOLDING WINGS (BLUE EMERGING + ONE WING RETAINS ORIGINAL WHITE!) (Z: 18..40) ---
    fill_sym_box(grid, 0, 4, 12, 15, 22, 29, 4)   # Wing root pack
    for sign in (-1, 1):
        bx_o = cx_r if sign == 1 else cx_l
        def wx(off):
            return bx_o + sign * off
        is_white_wing = (sign == 1)  # Right wing (+X, viewer's left foreground!) keeps original white!

        # Main wing spar rising high and wide
        spar = [
            (wx(4),  15, 26),
            (wx(9),  14, 30),
            (wx(14), 13, 35),
            (wx(20), 12, 38),
            (wx(24), 11, 40),
        ]
        for i in range(len(spar) - 1):
            col_s = 1 if i == 0 else (4 if i == 1 else 5)
            draw_6conn_line(grid, spar[i], spar[i + 1], col_s)
            p0, p1 = spar[i], spar[i + 1]
            draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), 6 if i >= 2 else 2)

        # Fanned wing feathers (transitioning gray -> cobalt/cerulean blue; white retained on right wing!)
        feathers = [
            (22, 11, 39, 25, 10, 31),
            (18, 12, 37, 23, 10, 25),
            (14, 13, 34, 19, 11, 21),
            (10, 14, 31, 15, 12, 18),
            (7,  14, 28, 11, 12, 17),
        ]
        for fi, (sx, sy, sz, ex, ey, ez) in enumerate(feathers):
            if is_white_wing and fi in (0, 1, 2):
                col_f = 8  # Original crisp white feathers on Saburo's right wing!
                col_b = 2 if fi == 2 else 8
            else:
                col_f = 5 if fi < 3 else 4
                col_b = 6 if fi == 0 else (1 if fi >= 3 else 7)
            draw_6conn_line(grid, (wx(sx), sy, sz), (wx(ex), ey, ez), col_f)
            draw_6conn_line(grid, (wx(sx), sy, sz - 1), (wx(ex), ey, ez - 1), col_b)
            draw_6conn_line(grid, (wx(sx), sy + 1, sz - 1), (wx(ex), ey + 1, ez - 1), 1 if fi >= 3 else col_f, only_empty=True)

        # Solid inner wing coverts bridging spar to body (ensuring rich silhouette & 6-connectivity)
        for xo in range(5, 16):
            zt = int(round(26 + (xo - 4) * 0.9))
            zb = int(round(21 + (xo - 5) * 0.25))
            ym = 14 if xo < 11 else 13
            if is_white_wing and xo >= 10:
                c_fill = 8
            elif xo >= 10:
                c_fill = 5
            elif xo >= 7:
                c_fill = 4
            else:
                c_fill = 1  # Still gray near shoulder root!
            draw_6conn_line(grid, (wx(xo), ym, zb), (wx(xo), ym, min(zt, 36)), c_fill, only_empty=True)

    # --- 5. HALF-BIRD HEAD WITH EMERGING CROW BEAK & BLUE CREST (Z: 29..38) ---
    fill_sym_box(grid, 0, 1, 18, 22, 29, 31, 3)   # Forward-craning neck
    fill_sym_box(grid, 0, 2, 18, 24, 31, 36, 1)   # Gray helmet-skull
    fill_sym_box(grid, 0, 2, 19, 23, 35, 36, 5)   # Glossy blue emerging on crown!
    fill_sym_box(grid, 0, 1, 20, 23, 36, 37, 6)   # Cerulean crown sheen
    # Emerging pointed dark crow beak!
    fill_sym_box(grid, 0, 1, 24, 27, 32, 34, 3)
    fill_sym_box(grid, 0, 0, 27, 29, 32, 33, 3)
    # Sharp amber eyes framed in deep blue
    fill_sym_box(grid, 2, 2, 22, 24, 33, 35, 4)
    fill_sym_box(grid, 2, 2, 23, 24, 34, 34, 9)
    # Swept-back crest feathers turning blue
    draw_6conn_line(grid, (cx_r + 1, 21, 36), (cx_r + 2, 16, 39), 5)
    draw_6conn_line(grid, (cx_l - 1, 21, 36), (cx_l - 2, 16, 39), 5)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: SABURO'S GLOSSY BLUE CROW (STRUCTURAL BLUE + ONE WHITE WING!) (56 x 46 x 36)
# ============================================================
def build_c():
    grid = np.zeros((56, 46, 36), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 27.5
    cx_l = X // 2 - 1   # 27 (-X, crow left / viewer's right)
    cx_r = X // 2       # 28 (+X, crow right / viewer's left — retains ORIGINAL WHITE!)

    # Structural-color iridescent crow plumage shader!
    # Light-facing top/front surfaces gleam cerulean-cyan (6) & glossy cobalt (5);
    # mid-feathers show deep midnight-blue (4) & iridescent violet-indigo (7)!
    def structural_blue(y, z, zb, zt, dx, rx):
        if z >= zt - 1 and dx <= rx * 0.65:
            return 6  # Luminous cerulean-cyan specular structural highlight!
        if z >= zt - 2:
            return 5  # Rich glossy cobalt-sapphire structural blue!
        if z <= zb + 1:
            return 7 if (y % 2 == 0) else 4  # Iridescent violet-indigo underside sheen!
        if (y + z) % 3 == 0:
            return 5
        return 4

    # --- 1. SLEEK AERODYNAMIC CROW BODY (Y: 14..34, Z: 9..20) ---
    body_slices = [
        # (y, rx, zb, zt)
        (14, 2.2, 11, 15),
        (15, 2.9, 10, 16),
        (16, 3.5, 10, 16),
        (17, 4.0, 9,  17),
        (18, 4.4, 9,  17),
        (19, 4.7, 9,  18),
        (20, 4.9, 9,  18),
        (21, 5.0, 9,  19),
        (22, 5.1, 9,  19),
        (23, 5.1, 9,  19),
        (24, 5.0, 9,  20),
        (25, 4.9, 10, 20),
        (26, 4.7, 10, 20),
        (27, 4.4, 11, 20),
        (28, 4.0, 12, 20),
        (29, 3.6, 13, 21),
        (30, 3.3, 14, 22),
        (31, 3.1, 16, 23),
        (32, 3.0, 17, 24),
    ]
    for y, rx, zb, zt in body_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    grid[x, y, z] = structural_blue(y, z, zb, zt, dx, rx)

    # Shimmering iridescent breast plumage sheen on front chest (Y: 27..31)
    fill_sym_box(grid, 0, 2, 27, 30, 13, 17, 5)
    fill_sym_box(grid, 0, 1, 29, 31, 15, 17, 6)

    # --- 2. TWO GROUNDED CROW LEGS & TALONS (Z: 0..12) ---
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        def lx(off):
            return int(round(bx + sign * off))
        # Feathered blue thighs tucked under belly
        fill_sphere_local(grid, cx + sign * 3.0, 20.5, 10.0, 1.8, 2.2, 2.5, 4)
        fill_box(grid, lx(2), lx(4), 19, 22, 8, 10, 5)
        # Slender dark tarsus angling down-forward
        draw_6conn_line(grid, (lx(3), 19, 8), (lx(3), 22, 1), 3, pad=(0, 1, 0))
        # Three grounded forward crow toes + rear hallux!
        fill_box(grid, lx(2), lx(4), 21, 23, 0, 1, 3)
        draw_6conn_line(grid, (lx(2), 23, 0), (lx(1), 26, 0), 3)
        draw_6conn_line(grid, (lx(3), 23, 0), (lx(3), 27, 0), 3)
        draw_6conn_line(grid, (lx(4), 23, 0), (lx(5), 26, 0), 3)
        draw_6conn_line(grid, (lx(3), 21, 0), (lx(3), 18, 0), 3)

    # --- 3. FANNED GLOSSY BLUE CROW TAIL FEATHERS (Y: 2..15, Z: 9..16) ---
    for i in range(13):
        ty = 14 - i
        tz = 13 - i // 4
        hw = 2 + i // 3
        for xo in range(0, hw + 1):
            if xo == hw:
                col_tf = 6 if (i >= 6) else 5
            elif (xo + i) % 3 == 0:
                col_tf = 7
            else:
                col_tf = 4 if i < 7 else 5
            fill_sym_box(grid, xo, xo, ty, ty, tz, tz + 1, col_tf)

    # --- 4. PROUD CROW HEAD, SLEEK BEAK & KEEN AMBER EYES (Y: 31..44, Z: 19..28) ---
    fill_sphere_local(grid, cx, 33.5, 23.0, 3.2, 3.6, 3.4, 4)
    # Glossy cerulean-cobalt crown gleam!
    fill_sym_box(grid, 0, 2, 32, 36, 25, 26, 5)
    fill_sym_box(grid, 0, 1, 33, 36, 26, 26, 6)
    # Subtle swept nape feathers
    fill_sym_box(grid, 0, 2, 30, 32, 24, 25, 7)
    fill_sym_box(grid, 0, 1, 29, 30, 25, 25, 5)
    # Sharp amber-gold crow eyes with dark ring
    fill_sym_box(grid, 2, 3, 34, 36, 23, 24, 3)
    fill_sym_box(grid, 3, 3, 35, 36, 23, 24, 9)
    # Strong curved dark crow beak (Y: 36..44)
    fill_sym_box(grid, 0, 1, 36, 39, 21, 24, 3)
    fill_sym_box(grid, 0, 1, 39, 41, 21, 23, 3)
    fill_sym_box(grid, 0, 0, 41, 44, 21, 22, 3)
    fill_sym_box(grid, 0, 0, 43, 44, 20, 21, 3)   # Hooked beak tip
    fill_sym_box(grid, 0, 0, 37, 41, 24, 24, 1)   # Subtle metallic beak ridge gleam

    # --- 5. GRAND SPREAD CROW WINGS: STRUCTURAL GLOSSY BLUE + ORIGINAL WHITE ON ONE WING (+X)! ---
    for sign in (-1, 1):
        bx_o = cx_r if sign == 1 else cx_l
        def wx(off):
            return bx_o + sign * off
        is_white_wing = (sign == 1)  # Saburo's crow: RIGHT wing (+X, viewer's left foreground!) retains crisp white!

        # Muscular wing shoulder mount
        fill_box(grid, wx(3), wx(6), 22, 28, 16, 20, 4)
        fill_box(grid, wx(4), wx(6), 24, 28, 18, 20, 5)

        # Graceful arched wing leading edge: Shoulder -> Wrist -> High Wingtip
        lead_pts = [
            (wx(5),  26, 19),
            (wx(10), 27, 23),
            (wx(16), 26, 28),
            (wx(22), 24, 32),
            (wx(26), 22, 34),
        ]
        for i in range(len(lead_pts) - 1):
            # Even on the white wing, the shoulder & leading edge carry structural blue so it reads as ONE blue crow with original white remaining on the wing!
            c_top = 6 if (not is_white_wing or i < 2) else 8
            c_mid = 5 if (not is_white_wing or i < 2) else 2
            draw_6conn_line(grid, lead_pts[i], lead_pts[i + 1], c_top)
            p0, p1 = lead_pts[i], lead_pts[i + 1]
            draw_6conn_line(grid, (p0[0], p0[1] - 1, p0[2] - 1), (p1[0], p1[1] - 1, p1[2] - 1), c_mid)

        # Sweeping wing covert & primary flight-feather fan!
        # Dense 6-connected feather ribs from leading edge back to trailing edge
        for xo in range(6, 27):
            u = (xo - 6) / 20.0
            if xo <= 16:
                t1 = (xo - 5) / 11.0
                ly = 26 + 1 * np.sin(t1 * np.pi)
                lz = 19 + 9 * t1
            else:
                t2 = (xo - 16) / 10.0
                ly = 26 - 4 * t2
                lz = 28 + 6 * t2
            # Trailing edge sweeps back gracefully with scalloped feather fingers at tips
            ty = ly - (13 - 4 * u)
            tz = lz - (5 + 2 * np.sin(u * np.pi))
            if xo >= 21 and xo % 2 == 0:
                ty -= 2  # Distinct primary crow flight-feather fingers!

            if is_white_wing:
                # Saburo's crow signature: crisp ORIGINAL WHITE across the broad middle & primary feathers of ONE wing!
                if xo >= 10:
                    c_rib = 8
                    c_tip = 2 if (xo % 4 == 0) else 8
                else:
                    c_rib = 5 if xo >= 8 else 4
                    c_tip = 8 if xo >= 8 else 6
            else:
                # Full glossy structural blue wing (iridescent cobalt + cerulean sheen + violet shadows!)
                if xo % 4 == 0:
                    c_rib = 6  # Luminous cerulean sheen
                elif xo % 4 == 2:
                    c_rib = 7  # Iridescent violet-indigo band
                else:
                    c_rib = 5  # Glossy cobalt-sapphire
                c_tip = 4 if xo < 20 else 6

            draw_6conn_line(grid, (wx(xo), ly, lz), (wx(xo), ty, tz), c_rib)
            draw_6conn_line(grid, (wx(xo), ly, lz - 1), (wx(xo), ty, tz - 1), c_tip, only_empty=True)

    hollow_interior_26(grid, 1, Z - 2)
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


def render_voxel_iso(grid, yaw_deg=35, pitch_deg=25, scale=None, img_size=(386, 266), margin=12):
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


def render_preview(grid_a, v_a, grid_b, v_b, grid_c, v_c, title_banner,
                   label_a, label_b, label_c, out_path,
                   yaw_a=28, pitch_a=18, yaw_b=30, pitch_b=20, yaw_c=38, pitch_c=24):
    canvas = Image.new("RGBA", (1274, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, 1274, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (1274, gy)], fill=(28, 34, 48, 255), width=1)

    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))

    models = [
        (label_a, grid_a, v_a, yaw_a, pitch_a),
        (label_b, grid_b, v_b, yaw_b, pitch_b),
        (label_c, grid_c, v_c, yaw_c, pitch_c),
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
    model_c = build_c()
    v_a = export_vox(model_a, "tendo_a.vox")
    v_b = export_vox(model_b, "tendo_b.vox")
    v_c = export_vox(model_c, "tendo_c.vox")
    comp_a, minz_a = check_6_connected(model_a)
    comp_b, minz_b = check_6_connected(model_b)
    comp_c, minz_c = check_6_connected(model_c)
    render_preview(
        model_a, v_a, model_b, v_b, model_c, v_c,
        "TRANSFORMING VOXEL MODEL: TENDO ROBOT -> HALF-BIRD -> SABURO'S BLUE CROW",
        "1. TENDO ROBOT (GRAY BASE)",
        "2. HALF-BIRD FORM (BLUE EMERGING)",
        "3. BLUE CROW (ONE WHITE WING)",
        "preview_tendo.png",
        yaw_a=28, pitch_a=18, yaw_b=30, pitch_b=20, yaw_c=38, pitch_c=24,
    )
    print(f"tendo: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b}), "
          f"C={v_c} voxels {model_c.shape} (comp={comp_c}, minZ={minz_c})")
