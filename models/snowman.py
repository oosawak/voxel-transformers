import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (244, 249, 255, 255),  # Crisp Fresh Snow-White
    2: (180, 210, 236, 255),  # Cool Ice-Blue Snow Shading / Frost Trim
    3: (218, 42, 50, 255),    # Vibrant Festive Knit Scarf Red & Bucket Stripe
    4: (146, 22, 34, 255),    # Deeper Crimson Scarf Shadow
    5: (106, 134, 166, 255),  # Galvanized Steel-Blue Bucket / Kabuto Helm
    6: (104, 66, 38, 255),    # Warm Woody Dark Brown Twig Arms
    7: (248, 132, 26, 255),   # Bright Carrot Orange (Nose & Helmet Crest)
    8: (34, 38, 46, 255),     # Coal-Black Buttons, Eyes & Dark Mecha Joints
    9: (80, 236, 255, 255),   # Glowing Icy-Cyan Robot Visor / Frost Core
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


def fill_ellipsoid(grid, cx, cy, cz, rx, ry, rz, col, shade_col=None, shade_z=None):
    """Fill a rounded ellipsoid with optional lower ice-blue snow shading."""
    X, Y, Z = grid.shape
    for x in range(X):
        dx = (x - cx) / rx
        if abs(dx) > 1.05:
            continue
        for y in range(Y):
            dy = (y - cy) / ry
            if abs(dy) > 1.05:
                continue
            for z in range(Z):
                dz = (z - cz) / rz
                if dx * dx + dy * dy + dz * dz <= 1.0:
                    c = col
                    if shade_col is not None and shade_z is not None and z <= shade_z:
                        c = shade_col
                    elif shade_col is not None and dy < -0.52 and dz < 0.25:
                        c = shade_col
                    grid[x, y, z] = c


def hollow_interior_26(grid, z_min, z_max):
    """Hollow only strictly interior voxels (all 26 neighbors occupied) so 6-connectivity is preserved."""
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


def paint_front_surface(grid, x, z, col, protrude=0):
    """Paint the frontmost (+Y) occupied voxel at (x, z), optionally protruding +Y."""
    X, Y, Z = grid.shape
    if not (0 <= x < X and 0 <= z < Z):
        return
    ys = np.nonzero(grid[x, :, z])[0]
    if len(ys) == 0:
        return
    y_front = int(ys.max())
    if protrude > 0:
        for dy in range(1, protrude + 1):
            if y_front + dy < Y:
                grid[x, y_front + dy, z] = col
    else:
        grid[x, y_front, z] = col


def paint_sym_front(grid, x_off, z, col, protrude=0):
    """Symmetrically paint the frontmost (+Y) voxel at offset x_off and height z."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    paint_front_surface(grid, cx_l - x_off, z, col, protrude=protrude)
    paint_front_surface(grid, cx_r + x_off, z, col, protrude=protrude)


# ==========================================
# FORM A: 2-TIER JAPANESE SNOWMAN (28 x 22 x 32)
# ==========================================
def build_a():
    grid = np.zeros((28, 22, 32), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 13.5
    cy = 10.5

    # --- TIER 1: BIG ROUND LOWER SNOWBALL (Z: 0..13) ---
    fill_ellipsoid(grid, cx, cy, 6.4, rx=7.4, ry=7.2, rz=6.9, col=1, shade_col=2, shade_z=2)

    # --- TIER 2: MEDIUM ROUND UPPER SNOWBALL / HEAD (Z: 13..24) ---
    fill_ellipsoid(grid, cx, cy, 18.6, rx=5.4, ry=5.2, rz=5.2, col=1, shade_col=2, shade_z=15)

    # Solid inner snow neck bridge so both tiers fuse into a single 6-connected body
    fill_sym_box(grid, 0, 3, 8, 13, 12, 15, 1)

    # --- COAL BELLY BUTTONS ON LOWER SNOWBALL (Front +Y) ---
    for bz in (5, 9):
        paint_sym_front(grid, 0, bz, 8, protrude=1)
        paint_sym_front(grid, 0, bz + 1, 8, protrude=1)

    # --- COZY FESTIVE RED KNIT SCARF AROUND NECK (Z: 13..15) ---
    for z, r_sc in [(13, 5.9), (14, 6.0), (15, 5.5)]:
        for x in range(X):
            dx = x - cx
            for y in range(Y):
                dy = y - cy
                d2 = (dx / r_sc) ** 2 + (dy / (r_sc - 0.1)) ** 2
                if 0.60 <= d2 <= 1.0:
                    col = 4 if (z == 13 or (x + y) % 3 == 0) else 3
                    grid[x, y, z] = col

    # Hanging front-left scarf tail (draping down over lower snowball)
    for z, y_tail in [(13, 16), (12, 17), (11, 17), (10, 17), (9, 18), (8, 18)]:
        col = 4 if z % 2 == 0 else 3
        fill_box(grid, 16, 18, y_tail - 1, y_tail, z, z, col)
    fill_box(grid, 16, 16, 17, 18, 7, 7, 3)
    fill_box(grid, 18, 18, 17, 18, 7, 7, 4)

    # Short fluttering rear scarf tail (-Y)
    for z, y_back in [(13, 4), (12, 3), (11, 3), (10, 2)]:
        col = 4 if z % 2 == 0 else 3
        fill_box(grid, 10, 12, y_back, y_back + 1, z, z, col)

    # --- CHEERFUL COAL EYES, SMILE & BRIGHT CARROT NOSE (Z: 16..22) ---
    paint_sym_front(grid, 2, 20, 8, protrude=1)
    paint_sym_front(grid, 2, 21, 8, protrude=1)
    # Cheerful curved coal pebble smile
    paint_sym_front(grid, 0, 17, 8)
    paint_sym_front(grid, 1, 17, 8)
    paint_sym_front(grid, 2, 18, 8)
    paint_sym_front(grid, 3, 18, 8)

    # Bright Carrot Nose sticking straight forward along +Y (cleanly centered!)
    fill_sym_box(grid, 0, 0, 15, 16, 19, 20, 7)
    fill_sym_box(grid, 0, 0, 17, 19, 19, 19, 7)
    fill_sym_box(grid, 0, 0, 20, 20, 19, 19, 7)

    # --- WOODY BROWN BRANCH / TWIG ARMS STICKING OUT SIDES (Z: 10..18) ---
    # Deeply anchored at x_off=5..7 into lower snowball so strictly 6-connected!
    branch_segments = [
        (5, 8, 10, 11, 10, 11),
        (8, 9, 10, 11, 11, 12),
        (9, 10, 10, 11, 12, 13),
        (10, 11, 10, 11, 13, 14),
        (11, 12, 10, 11, 14, 15),
    ]
    for x0, x1, y0, y1, z0, z1 in branch_segments:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, 6)
    # Forked 3-twig fingers at tips (strictly 6-connected)
    fill_sym_box(grid, 12, 13, 10, 10, 15, 16, 6)  # Center twig
    fill_sym_box(grid, 13, 13, 10, 10, 16, 17, 6)
    fill_sym_box(grid, 11, 11, 11, 11, 15, 17, 6)  # Upper thumb twig
    fill_sym_box(grid, 12, 12, 11, 12, 14, 15, 6)  # Forward twig
    fill_sym_box(grid, 12, 13, 12, 12, 15, 15, 6)

    # --- UPTURNED GALVANIZED BUCKET HAT ON HEAD (Z: 23..30) ---
    bucket_layers = [
        (23, 4.9, 4.8, 2),  # Flared ice-silver rolled metal brim
        (24, 4.5, 4.4, 5),  # Steel-blue galvanized bucket wall
        (25, 4.3, 4.2, 3),  # Festive red bucket band
        (26, 4.1, 4.0, 5),
        (27, 3.9, 3.8, 5),
        (28, 3.7, 3.6, 5),
        (29, 3.5, 3.4, 5),
        (30, 3.2, 3.1, 2),  # Flat top rim highlight
    ]
    for z, rx, ry, col in bucket_layers:
        for x in range(X):
            dx = (x - cx) / rx
            for y in range(Y):
                dy = (y - cy) / ry
                d2 = dx * dx + dy * dy
                if d2 <= 1.0:
                    if z == 30 and d2 < 0.65:
                        grid[x, y, z] = 5
                    else:
                        grid[x, y, z] = col
    # Dark bucket wire handle resting neatly around sides of rim
    fill_sym_box(grid, 4, 4, 10, 11, 24, 25, 8)
    fill_sym_box(grid, 4, 4, 11, 13, 23, 24, 8)

    # Hollow unseen interiors of both snowballs & bucket
    hollow_interior_26(grid, 1, 29)

    return grid


# ==========================================
# FORM B: FROST-KNIGHT SNOWMAN ROBOT (34 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 16.5
    cy = 11.5

    # --- CHUNKY SNOW-BOOT FEET WITH ICE-BLUE TREADS (Z: 0..4) ---
    fill_sym_box(grid, 2, 5, 7, 16, 0, 1, 2)     # Cool ice-blue frost tread sole
    fill_sym_box(grid, 2, 5, 7, 8, 0, 1, 8)      # Coal-black heel cleat
    fill_sym_box(grid, 3, 4, 15, 17, 0, 1, 2)    # Armored snow-boot toe
    fill_sym_box(grid, 2, 5, 8, 15, 1, 3, 1)     # Crisp snow-white boot shell
    fill_sym_box(grid, 3, 4, 15, 16, 2, 2, 5)    # Steel-blue toe strap
    fill_sym_box(grid, 2, 5, 9, 13, 3, 3, 5)     # Steel-blue ankle cuff
    fill_sym_box(grid, 3, 4, 9, 12, 3, 4, 8)     # Coal-black ankle joint

    # --- SNOW-CLAD LOWER LEGS & FROST KNEE GUARDS (Z: 4..14) ---
    fill_sym_box(grid, 3, 4, 9, 12, 4, 13, 8)    # Inner joint core
    fill_sym_box(grid, 2, 5, 10, 13, 4, 12, 1)   # Plump snow-white shin armor
    fill_sym_box(grid, 2, 5, 8, 10, 4, 12, 2)    # Cool ice-blue calf shading
    fill_sym_box(grid, 5, 5, 9, 12, 5, 11, 2)    # Outer frost panel
    fill_sym_box(grid, 3, 4, 7, 8, 5, 10, 5)     # Steel-blue rear calf thruster
    fill_sym_box(grid, 3, 4, 7, 7, 6, 7, 9)      # Glowing icy-cyan vent
    # Sculpted frost knee guards
    fill_sym_box(grid, 2, 5, 12, 14, 11, 14, 1)
    fill_sym_box(grid, 3, 4, 14, 15, 12, 14, 2)
    fill_sym_box(grid, 3, 4, 15, 15, 13, 13, 9)  # Glowing cyan knee crystal

    # --- THIGHS (Z: 14..18) ---
    fill_sym_box(grid, 2, 4, 9, 13, 14, 17, 8)   # Dark coal-black joint thighs
    fill_sym_box(grid, 2, 4, 12, 13, 14, 17, 1)  # Front snow-white thigh plate
    fill_sym_box(grid, 4, 4, 10, 12, 15, 17, 2)  # Ice-blue side bevel

    # --- ROUNDED SNOW-WAIST / PELVIS (Z: 17..23) - LOWER SNOWBALL! ---
    fill_ellipsoid(grid, cx, cy, 20.0, rx=6.1, ry=5.1, rz=3.5, col=1, shade_col=2, shade_z=18)
    # Compact central steel-blue frost buckle (keeps rounded white snowball silhouette clear!)
    fill_sym_box(grid, 0, 1, 15, 16, 19, 21, 5)
    fill_sym_box(grid, 0, 0, 16, 16, 20, 20, 9)  # Glowing icy-cyan waist core
    # Coal waist rivets echoing snowman buttons
    paint_sym_front(grid, 3, 20, 8, protrude=1)
    fill_sym_box(grid, 0, 2, 6, 7, 19, 21, 5)    # Rear steel waist stabilizer

    # --- ROUNDED SNOW-ARMOR TORSO (Z: 23..32) - UPPER SNOWBALL! ---
    fill_ellipsoid(grid, cx, cy, 27.5, rx=6.6, ry=5.6, rz=5.0, col=1, shade_col=2, shade_z=24)

    # Iconic Coal Buttons & Glowing Frost Core on Snow-Chest!
    fill_sym_box(grid, 0, 1, 16, 17, 27, 28, 9)  # Glowing icy-cyan frost core
    fill_sym_box(grid, 2, 2, 16, 16, 27, 28, 2)  # Ice-blue frost collar around core
    # Signature coal-black snowman buttons above & below chest core
    paint_sym_front(grid, 0, 25, 8, protrude=1)
    paint_sym_front(grid, 0, 30, 8, protrude=1)
    paint_sym_front(grid, 3, 26, 8)
    paint_sym_front(grid, 3, 29, 8)

    # --- COZY FESTIVE RED KNIT SCARF COLLAR & FLOWING TAILS (Z: 20..33) ---
    fill_sym_box(grid, 0, 5, 8, 15, 31, 32, 3)
    fill_sym_box(grid, 0, 4, 14, 16, 31, 32, 3)
    fill_sym_box(grid, 1, 3, 15, 16, 31, 31, 4)  # Knit crease shadow
    fill_sym_box(grid, 4, 5, 10, 14, 32, 33, 3)  # Raised scarf collar flanks
    # Front scarf tail draped neatly over right side of chest (clear of center coal buttons!)
    for z, y_t in [(31, 16), (30, 16), (29, 17), (28, 17), (27, 17), (26, 16), (25, 16), (24, 16)]:
        col = 4 if z % 2 == 0 else 3
        fill_box(grid, 20, 21, y_t - 1, y_t, z, z, col)
    fill_box(grid, 20, 20, 15, 16, 23, 23, 3)
    fill_box(grid, 21, 21, 15, 16, 23, 23, 4)

    # Rear cryo-pack & wind-swept red scarf cape tail (-Y)
    fill_sym_box(grid, 2, 4, 5, 7, 25, 30, 5)    # Twin steel-blue frost tanks
    fill_sym_box(grid, 2, 3, 4, 5, 25, 26, 9)    # Glowing icy-cyan vents
    for z, y_b in [(31, 7), (30, 6), (29, 6), (28, 5), (27, 5), (26, 5), (25, 4), (24, 4), (23, 4), (22, 4)]:
        col = 4 if z % 2 == 0 else 3
        fill_box(grid, 15, 18, y_b, y_b + 1, z, z, col)
    fill_box(grid, 15, 16, 4, 4, 21, 21, 3)
    fill_box(grid, 17, 18, 4, 4, 21, 21, 4)

    # --- SNOW SHOULDER MOUNTS & GNARLED WOODY BRANCH-ARMS (Z: 13..33) - 枝の腕がそのまま腕! ---
    fill_sym_box(grid, 6, 8, 10, 13, 27, 31, 1)
    fill_sym_box(grid, 7, 8, 10, 13, 31, 32, 2)  # Frost-dusted shoulder cap
    fill_sym_box(grid, 8, 9, 10, 12, 28, 30, 8)  # Coal joint socket

    # Articulated Gnarled Woody Branch Upper Arms (col = 6)
    fill_sym_box(grid, 9, 10, 10, 13, 23, 30, 6)
    # Natural wooden branch sprout sticking up from shoulder with snow cap!
    fill_sym_box(grid, 11, 11, 11, 12, 28, 31, 6)
    fill_sym_box(grid, 12, 12, 11, 11, 30, 32, 6)
    fill_sym_box(grid, 11, 12, 11, 12, 32, 32, 1)

    # Articulated Gnarled Woody Branch Forearms (col = 6) with sprouting side-twigs
    fill_sym_box(grid, 9, 11, 10, 13, 16, 22, 6)
    fill_sym_box(grid, 10, 11, 12, 14, 17, 21, 6)
    fill_sym_box(grid, 12, 12, 10, 11, 19, 21, 6)
    fill_sym_box(grid, 13, 13, 10, 10, 21, 22, 6)
    fill_sym_box(grid, 12, 12, 12, 12, 17, 18, 6)
    fill_sym_box(grid, 9, 11, 11, 13, 16, 16, 2)  # Frost-ice wrist ring

    # Forked Twig-Claw Hands (Z: 13..15)
    fill_sym_box(grid, 9, 10, 11, 13, 14, 15, 6)
    fill_sym_box(grid, 9, 9, 13, 14, 13, 14, 6)
    fill_sym_box(grid, 10, 10, 13, 14, 13, 14, 6)
    fill_sym_box(grid, 10, 11, 11, 12, 13, 14, 6)

    # Right-hand Frost-Crystal Branch Staff (+X, viewer's left)
    # Held slightly outward & forward (x=28..29, y=15..16) so staff & crystal spearhead read super cleanly!
    fill_box(grid, 26, 29, 13, 15, 14, 15, 6)     # Twig grip extending cleanly to staff
    fill_box(grid, 28, 29, 15, 16, 7, 30, 6)      # Tall gnarled woody branch staff
    fill_box(grid, 28, 29, 15, 16, 28, 29, 3)     # Festive red scarf ribbon tie
    fill_box(grid, 30, 30, 15, 16, 23, 24, 6)     # Side twig knob on staff
    # Glowing Icy-Cyan Frost-Crystal Spearhead rising proudly clear of shoulder!
    fill_box(grid, 27, 30, 14, 17, 30, 32, 2)
    fill_box(grid, 28, 29, 14, 17, 31, 36, 9)
    fill_box(grid, 28, 29, 15, 16, 36, 38, 9)
    fill_box(grid, 28, 29, 15, 16, 38, 39, 1)

    # Left forearm Frost-Snow Buckler with Branch Rim (-X)
    fill_box(grid, 4, 5, 10, 15, 16, 22, 2)
    fill_box(grid, 4, 4, 11, 14, 17, 21, 1)
    fill_box(grid, 4, 4, 12, 13, 18, 20, 9)
    fill_box(grid, 5, 5, 10, 15, 16, 16, 6)

    # --- BUCKET-HELM / KABUTO HELMET HEAD (Z: 32..41) - バケツが兜! ---
    fill_sym_box(grid, 0, 1, 10, 13, 32, 33, 8)
    fill_sym_box(grid, 0, 2, 9, 14, 33, 36, 1)
    fill_sym_box(grid, 0, 1, 14, 15, 33, 34, 1)
    fill_sym_box(grid, 0, 1, 14, 15, 34, 34, 2)
    # Glowing Icy-Cyan Robot Visor peeking fiercely from under the bucket brim!
    fill_sym_box(grid, 0, 2, 14, 15, 35, 35, 9)
    fill_sym_box(grid, 2, 2, 13, 14, 35, 35, 9)

    # UPTURNED GALVANIZED BUCKET KABUTO HELMET (Z: 36..41)
    fill_sym_box(grid, 0, 4, 8, 16, 36, 36, 2)    # Crisp silver-ice rolled bucket rim
    fill_sym_box(grid, 0, 3, 8, 15, 37, 37, 3)    # Festive red bucket band
    fill_sym_box(grid, 0, 3, 9, 14, 38, 40, 5)    # Tapered galvanized steel-blue bucket crown
    fill_sym_box(grid, 0, 2, 9, 14, 40, 41, 5)    # Flat upturned bucket top
    fill_sym_box(grid, 0, 2, 10, 13, 41, 41, 2)
    # Bucket wire-handle ear-guards / samurai kabuto fukigaeshi
    fill_sym_box(grid, 4, 4, 9, 13, 34, 36, 8)
    fill_sym_box(grid, 3, 4, 8, 9, 34, 35, 5)

    # ICONIC BRIGHT CARROT-ORANGE KABUTO HORN CREST! (Z: 37..40, +Y)
    fill_sym_box(grid, 0, 1, 15, 16, 37, 38, 7)
    fill_sym_box(grid, 0, 0, 16, 18, 37, 38, 7)
    fill_sym_box(grid, 0, 0, 18, 19, 38, 39, 7)
    fill_sym_box(grid, 0, 0, 15, 16, 39, 40, 7)

    # Hollow unseen interiors of snow-torso & snow-waist
    hollow_interior_26(grid, 18, 31)

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
    v_a = export_vox(model_a, "snowman_a.vox")
    v_b = export_vox(model_b, "snowman_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SNOWMAN -> FROST-KNIGHT SNOWMAN ROBOT",
        "1. JAPANESE SNOWMAN",
        "2. FROST-KNIGHT SNOWMAN ROBOT",
        "preview_snowman.png",
        yaw_a=34, pitch_a=20, yaw_b=32, pitch_b=20,
    )
    print(f"snowman: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
