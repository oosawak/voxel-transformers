import math
import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (224, 52, 62, 255),    # Vivid Crimson / Coral-Red Octopus Skin & Armor
    2: (158, 28, 44, 255),    # Deep Burgundy Shading / Creases / Dark Armor
    3: (252, 232, 224, 255),  # Pale Cream / Pinkish-White Suction Cups (吸盤)
    4: (44, 56, 74, 255),     # Dark Slate / Deep-Sea Mechanical Joints & Frame
    5: (255, 206, 48, 255),   # Bright Golden-Yellow Expressive Eyes / Visor
    6: (48, 226, 214, 255),   # Glowing Aqua / Teal Sea-Energy Accents & Core
    7: (248, 114, 62, 255),   # Coral-Orange Mantle Spots & Crest Highlights
    8: (68, 30, 48, 255),     # Dark Purple-Brown Inner Shadow & Pupils
    9: (245, 248, 255, 255),  # Pearl White Eye Glint & Metallic Highlight
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


def set_voxel(grid, x, y, z, col):
    X, Y, Z = grid.shape
    if 0 <= x < X and 0 <= y < Y and 0 <= z < Z:
        grid[x, y, z] = col


def set_sym_voxel(grid, x_off, y, z, col):
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    set_voxel(grid, cx_l - x_off, y, z, col)
    set_voxel(grid, cx_r + x_off, y, z, col)


def stamp_ball(grid, fx, fy, fz, rad, col, overwrite=True):
    """Stamp a small rounded voxel sphere at floating point coordinates."""
    X, Y, Z = grid.shape
    r_int = int(math.ceil(rad))
    x0 = max(0, int(math.floor(fx - r_int)))
    x1 = min(X - 1, int(math.ceil(fx + r_int)))
    y0 = max(0, int(math.floor(fy - r_int)))
    y1 = min(Y - 1, int(math.ceil(fy + r_int)))
    z0 = max(0, int(math.floor(fz - r_int)))
    z1 = min(Z - 1, int(math.ceil(fz + r_int)))
    r2 = rad * rad
    for x in range(x0, x1 + 1):
        dx = x - fx
        for y in range(y0, y1 + 1):
            dy = y - fy
            for z in range(z0, z1 + 1):
                dz = z - fz
                if dx * dx + dy * dy + dz * dz <= r2:
                    if overwrite or grid[x, y, z] == 0:
                        grid[x, y, z] = col


def connect_6(grid, p0, p1, col):
    """Connect two integer voxel points with a guaranteed 6-connected path."""
    x, y, z = p0
    tx, ty, tz = p1
    set_voxel(grid, x, y, z, col)
    while (x, y, z) != (tx, ty, tz):
        if x != tx:
            x += 1 if tx > x else -1
        elif y != ty:
            y += 1 if ty > y else -1
        elif z != tz:
            z += 1 if tz > z else -1
        set_voxel(grid, x, y, z, col)


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


def hollow_interior_6(grid, z_min, z_max):
    """Hollow strictly unseen interior voxels while mathematically preserving 6-connectivity."""
    X, Y, Z = grid.shape
    candidates = []
    for x in range(1, X - 1):
        for y in range(1, Y - 1):
            for z in range(max(1, z_min), min(Z - 1, z_max + 1)):
                if grid[x, y, z] == 0:
                    continue
                if (grid[x - 1, y, z] and grid[x + 1, y, z] and
                        grid[x, y - 1, z] and grid[x, y + 1, z] and
                        grid[x, y, z - 1] and grid[x, y, z + 1]):
                    candidates.append((x, y, z))

    dirs6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    for x, y, z in candidates:
        sub = grid[x - 1:x + 2, y - 1:y + 2, z - 1:z + 2] > 0
        # Collect occupied 6-face-neighbors in local (0..2) coords
        face_nbs = [(1 + dx, 1 + dy, 1 + dz) for dx, dy, dz in dirs6 if sub[1 + dx, 1 + dy, 1 + dz]]
        if not face_nbs:
            continue
        # BFS inside the 3x3x3 cube excluding center (1,1,1)
        visited = {face_nbs[0]}
        stack = [face_nbs[0]]
        while stack:
            cx0, cy0, cz0 = stack.pop()
            for dx, dy, dz in dirs6:
                nx, ny, nz = cx0 + dx, cy0 + dy, cz0 + dz
                if 0 <= nx <= 2 and 0 <= ny <= 2 and 0 <= nz <= 2 and (nx, ny, nz) != (1, 1, 1):
                    if sub[nx, ny, nz] and (nx, ny, nz) not in visited:
                        visited.add((nx, ny, nz))
                        stack.append((nx, ny, nz))
        if all(nb in visited for nb in face_nbs):
            grid[x, y, z] = 0


# ==========================================
# FORM A: OCTOPUS (34 x 34 x 24)
# ==========================================
def build_a():
    grid = np.zeros((34, 34, 24), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 16.5
    cy = 16.5

    # --- 1. CENTRAL BODY BASE / TENTACLE SKIRT (Z: 1..7) ---
    base_profile = [
        (1, 3.6, 16.5, 3.4, 3.6),
        (2, 4.6, 16.6, 4.2, 4.4),
        (3, 5.1, 16.7, 4.7, 4.9),
        (4, 5.1, 16.8, 4.6, 4.9),
        (5, 4.9, 16.8, 4.4, 4.7),
        (6, 4.7, 16.5, 4.2, 4.5),
        (7, 4.5, 16.0, 4.1, 4.3),
    ]
    for z, rx, yc, ry_b, ry_f in base_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.3:
                continue
            for y in range(Y):
                dy = y - yc
                ry = ry_f if dy >= 0 else ry_b
                if (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0:
                    if z <= 2:
                        col = 2
                    elif dy < -ry_b * 0.55 and z <= 4:
                        col = 2
                    else:
                        col = 1
                    grid[x, y, z] = col

    # Subtle dark purple-brown mouth underside at Z=1
    fill_sym_box(grid, 0, 1, 15, 17, 1, 1, 8)

    # --- 2. EIGHT CLEARLY COUNTABLE CURLING TENTACLES WITH CREAM SUCTION CUPS ---
    # Four symmetric pairs (8 arms total), radiating cleanly around the body
    # (angle_deg from +Y front, reach, wave_amp, curl_height, wave_phase)
    tentacle_specs = [
        (23.0,  14.2,  1.2, 4.8,  0.3),   # Pair 1: Front-inner pair
        (65.0,  14.8, -1.4, 5.0,  0.1),   # Pair 2: Front-outer pair
        (114.0, 14.5,  1.3, 4.6, -0.2),   # Pair 3: Rear-outer pair
        (157.0, 13.8, -1.1, 4.4,  0.2),   # Pair 4: Rear-inner pair
    ]

    for deg, reach, wave_amp, curl_h, phase in tentacle_specs:
        for side in (-1, 1):
            ang = math.radians(deg * side)
            ux = math.sin(ang)
            uy = math.cos(ang)
            # Perpendicular outward-tangential direction for S-curve & visible side suction cups
            tx = uy * side
            ty = -ux * side

            pts = []
            steps = 56
            for i in range(steps + 1):
                t = i / float(steps)
                # Radial extension with slight inward curl at very tip
                r = 3.2 + (reach - 3.2) * (t ** 0.92)
                if t > 0.78:
                    u = (t - 0.78) / 0.22
                    r -= 1.5 * (u ** 1.7)

                # Playful organic S-wave sideways
                sway = wave_amp * math.sin(t * math.pi * 1.45 + phase) * (t ** 0.7) * side

                # Height profile: arches down from body to rest firmly on Z=0..2, then curls up at tip!
                if t < 0.25:
                    u = t / 0.25
                    z_val = 3.2 * (1.0 - u) + 1.4 * u
                elif t < 0.68:
                    u = (t - 0.25) / 0.43
                    z_val = 1.4 - 0.25 * math.sin(u * math.pi)
                else:
                    u = (t - 0.68) / 0.32
                    z_val = 1.35 + curl_h * (u ** 1.45)

                fx = cx + ux * r + tx * sway
                fy = cy + uy * r + ty * sway
                fz = z_val
                rad = 1.75 * (1.0 - t) + 0.62 * t
                pts.append((t, fx, fy, fz, rad))

            # First pass: crimson skin body with burgundy underside shading
            prev_i = None
            for t, fx, fy, fz, rad in pts:
                stamp_ball(grid, fx, fy, fz, rad, 1)
                # Burgundy shading along lower back/underside
                if t < 0.85:
                    stamp_ball(grid, fx, fy, max(0.2, fz - rad * 0.45), max(0.55, rad * 0.68), 2, overwrite=False)
                # Ensure 6-connected spine even on narrow tips
                cur_i = (int(round(fx)), int(round(fy)), int(round(fz)))
                if prev_i is not None and cur_i != prev_i:
                    connect_6(grid, prev_i, cur_i, 1)
                prev_i = cur_i

            # Ensure mid-tentacle rests solidly on Z=0 ground plane
            for t, fx, fy, fz, rad in pts:
                if 0.24 <= t <= 0.66:
                    gx_i, gy_i = int(round(fx)), int(round(fy))
                    set_voxel(grid, gx_i, gy_i, 0, 2)

            # Second pass: unmistakable PALE CREAM SUCTION CUPS (color 3) along lower-sides & curled tips!
            cup_ts = [0.22, 0.35, 0.48, 0.61, 0.74, 0.86]
            for ct in cup_ts:
                idx = min(len(pts) - 1, int(round(ct * steps)))
                _, fx, fy, fz, rad = pts[idx]
                # Place suction cup dots on the lower-outer side flanks so they are clearly visible in 3/4 view
                for fl in (-1.0, 1.0):
                    sx = int(round(fx + tx * fl * (rad * 0.85)))
                    sy = int(round(fy + ty * fl * (rad * 0.85)))
                    sz = max(0, int(round(fz - 0.5)))
                    set_voxel(grid, sx, sy, sz, 3)
                # On the upward-curling tips, suction cups face outward along the outer curve!
                if ct >= 0.72:
                    sx_out = int(round(fx + ux * (rad * 0.82)))
                    sy_out = int(round(fy + uy * (rad * 0.82)))
                    sz_out = int(round(fz - 0.25))
                    set_voxel(grid, sx_out, sy_out, sz_out, 3)
            # Keep very tip cap crimson for crisp organic curl silhouette
            _, tfx, tfy, tfz, _ = pts[-1]
            set_voxel(grid, int(round(tfx)), int(round(tfy)), int(round(tfz)), 1)

    # --- 3. BIG BULBOUS ROUNDED MANTLE / HEAD TILTED SLIGHTLY BACK (Z: 7..22) ---
    # (z, rx, yc, ry_back, ry_front)
    mantle_profile = [
        (7,  4.8, 16.0, 4.3, 4.6),
        (8,  5.2, 15.6, 4.8, 5.0),
        (9,  5.6, 15.2, 5.2, 5.2),
        (10, 6.0, 14.8, 5.6, 5.4),
        (11, 6.3, 14.3, 6.0, 5.6),
        (12, 6.6, 13.8, 6.3, 5.8),
        (13, 6.8, 13.3, 6.5, 5.9),
        (14, 6.9, 12.9, 6.6, 5.9),
        (15, 6.9, 12.5, 6.6, 5.8),
        (16, 6.7, 12.1, 6.4, 5.6),
        (17, 6.4, 11.8, 6.1, 5.3),
        (18, 5.9, 11.5, 5.6, 4.9),
        (19, 5.2, 11.3, 5.0, 4.4),
        (20, 4.3, 11.1, 4.1, 3.7),
        (21, 3.1, 11.0, 3.0, 2.7),
        (22, 1.7, 10.9, 1.6, 1.5),
    ]
    for z, rx, yc, ry_b, ry_f in mantle_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.3:
                continue
            for y in range(Y):
                dy = y - yc
                ry = ry_f if dy >= 0 else ry_b
                d2 = (dx / rx) ** 2 + (dy / ry) ** 2
                if d2 <= 1.0:
                    # Deep burgundy underside & rear lower contour shading
                    if (dy < -ry_b * 0.55 and z <= 13) or (z <= 9 and dy < -1.5):
                        col = 2
                    else:
                        col = 1
                    grid[x, y, z] = col

    # Organic Coral-Orange Mantle Spots (color 7) sculpted cleanly onto the bulbous dome
    spot_centers = [
        (3.4, 14.2, 19.6, 1.45),
        (5.5, 12.2, 16.5, 1.65),
        (2.4, 8.6,  18.2, 1.45),
        (5.1, 16.6, 14.2, 1.35),
        (1.6, 16.8, 16.5, 1.25),
        (4.2, 7.6,  14.0, 1.45),
    ]
    for sx_off, sy, sz, sr in spot_centers:
        for side in (-1, 1):
            fx = cx + sx_off * side
            for x in range(max(0, int(fx - 2)), min(X, int(fx + 3))):
                for y in range(max(0, int(sy - 2)), min(Y, int(sy + 3))):
                    for z in range(max(0, int(sz - 2)), min(Z, int(sz + 3))):
                        if grid[x, y, z] == 1:
                            if (x - fx) ** 2 + (y - sy) ** 2 + (z - sz) ** 2 <= sr * sr:
                                grid[x, y, z] = 7

    # --- 4. LARGE EXPRESSIVE EYES & BROW RIDGES (Y: 19..22, Z: 6..11) ---
    # Raised crimson brow arches above eyes
    fill_sym_box(grid, 2, 4, 19, 21, 10, 11, 1)
    fill_sym_box(grid, 2, 4, 21, 21, 10, 10, 7)  # Coral-orange brow highlight
    # Sculpted eye sockets protruding on front-sides of head
    fill_sym_box(grid, 2, 4, 19, 21, 7, 9, 1)
    # Large golden-yellow expressive eyes (color 5)
    fill_sym_box(grid, 2, 4, 21, 22, 7, 9, 5)
    fill_sym_box(grid, 4, 4, 20, 21, 7, 9, 5)
    # Dark purple-brown expressive pupils (color 8)
    fill_sym_box(grid, 3, 3, 22, 22, 7, 8, 8)
    fill_sym_box(grid, 4, 4, 21, 21, 8, 8, 8)
    # Crisp pearl-white eye glints (color 9)
    fill_sym_box(grid, 2, 2, 22, 22, 9, 9, 9)
    # Lower crimson eyelid rim
    fill_sym_box(grid, 2, 4, 20, 21, 6, 6, 2)

    # Expressive front cheek/mouth dimple below eyes (Z: 4..5, Y: 21)
    fill_sym_box(grid, 0, 1, 20, 21, 5, 6, 1)
    fill_sym_box(grid, 0, 0, 21, 21, 4, 4, 8)
    fill_sym_box(grid, 1, 1, 21, 21, 4, 4, 2)

    # Hollow unseen bulbous mantle & base interior to keep voxel count sleek (~1,600-2,200)
    hollow_interior_26(grid, 2, 21)

    return grid


# ==========================================
# FORM B: KRAKEN OCTOPUS ROBOT (40 x 26 x 44)
# ==========================================
def build_b():
    grid = np.zeros((40, 26, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 19.5
    cx_l = X // 2 - 1   # 19
    cx_r = X // 2       # 20

    # --- 1. TENTACLE-CLAD FEET WITH SUCTION-CUP SOLES & TRIM (Z: 0..3) ---
    # Wider heroic stance (x_off: 3..7) with dark slate mecha sole
    fill_sym_box(grid, 3, 7, 8, 15, 0, 1, 4)
    fill_sym_box(grid, 4, 6, 7, 8, 0, 2, 4)
    # Twin curling crimson tentacle-toes gripping the ground at front (2 bundled tentacles per leg!)
    fill_sym_box(grid, 3, 4, 14, 18, 0, 2, 1)  # Inner front tentacle toe
    fill_sym_box(grid, 6, 7, 14, 18, 0, 2, 1)  # Outer front tentacle toe
    fill_sym_box(grid, 3, 7, 11, 15, 1, 3, 1)  # Upper vamp crimson tentacle wrap
    fill_sym_box(grid, 3, 7, 8, 11, 1, 2, 2)   # Burgundy heel wrap
    # Rear curled tentacle heel spur
    fill_sym_box(grid, 4, 6, 5, 7, 0, 2, 1)
    # Unmistakable PALE CREAM SUCTION-CUP SOLES & TOE PADS (color 3)!
    fill_sym_box(grid, 3, 4, 15, 18, 0, 0, 3)  # Inner toe suction pad
    fill_sym_box(grid, 6, 7, 15, 18, 0, 0, 3)  # Outer toe suction pad
    fill_sym_box(grid, 7, 7, 10, 11, 0, 0, 3)  # Outer side suction cups
    fill_sym_box(grid, 7, 7, 13, 14, 0, 0, 3)
    fill_sym_box(grid, 5, 5, 15, 16, 1, 1, 3)  # Toe cleft suction accent
    fill_sym_box(grid, 4, 6, 5, 6, 0, 0, 3)    # Heel tentacle suction pad
    # Dark slate mecha ankle joint
    fill_sym_box(grid, 4, 6, 9, 13, 3, 4, 4)

    # --- 2. TENTACLE-CLAD LOWER LEGS (2 PAIRED TENTACLES PER LEG, Z: 4..15) ---
    # Inner dark slate mecha shin core
    fill_sym_box(grid, 4, 6, 9, 13, 4, 14, 4)
    # Front shin tentacle column (crimson + coral highlight + cream suction dots!)
    fill_sym_box(grid, 3, 6, 11, 14, 4, 13, 1)
    fill_sym_box(grid, 4, 6, 14, 15, 5, 12, 1)
    fill_sym_box(grid, 5, 5, 15, 15, 6, 11, 7)  # Coral-orange shin ridge
    # Rear/outer calf tentacle column wrapping diagonally around shin
    fill_sym_box(grid, 3, 6, 8, 10, 4, 13, 2)
    fill_sym_box(grid, 6, 7, 9, 13, 5, 12, 1)   # Outer wrapped tentacle coil
    fill_sym_box(grid, 4, 6, 7, 8, 5, 11, 1)    # Rear calf tentacle ridge
    # Pale cream suction cup dots running visibly up BOTH outer, front-inner, & rear shin flanks!
    for sz in (5, 7, 9, 11):
        fill_sym_box(grid, 7, 7, 11, 12, sz, sz, 3)  # Outer leg suction cups
        fill_sym_box(grid, 3, 3, 13, 14, sz, sz, 3)  # Front-inner leg suction cups
        fill_sym_box(grid, 5, 5, 7, 7, sz, sz, 3)    # Rear calf suction cups
    # Sculpted Kraken knee guards with aqua sea-energy jewel
    fill_sym_box(grid, 3, 6, 13, 16, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 16, 16, 13, 14, 6)  # Glowing aqua knee core
    fill_sym_box(grid, 4, 5, 15, 15, 15, 15, 7)  # Coral knee brow

    # --- 3. SLEEK MECHA THIGHS & TENTACLE-HIP TASSETS (Z: 15..22) ---
    # Exposed dark slate mechanical thigh frame for crisp robot silhouette!
    fill_sym_box(grid, 4, 6, 9, 13, 15, 20, 4)
    fill_sym_box(grid, 4, 5, 12, 14, 16, 19, 2)  # Burgundy front thigh armor
    fill_sym_box(grid, 5, 5, 14, 14, 17, 18, 3)  # Pale cream thigh trim
    fill_sym_box(grid, 6, 6, 10, 13, 16, 19, 1)  # Outer crimson tentacle thigh strap
    fill_sym_box(grid, 6, 6, 11, 12, 17, 17, 3)  # Suction dot on thigh strap
    fill_sym_box(grid, 6, 6, 11, 12, 19, 19, 3)

    # Pelvis / waist core (Z: 19..23)
    fill_sym_box(grid, 0, 5, 9, 14, 20, 22, 4)
    fill_sym_box(grid, 0, 4, 13, 15, 20, 22, 2)
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 1)  # Center armored groin plate
    fill_sym_box(grid, 0, 1, 16, 16, 20, 21, 5)  # Golden-yellow waist emblem
    fill_sym_box(grid, 0, 0, 16, 16, 21, 21, 6)  # Aqua waist gem
    # Curled crimson & cream tentacle-hip tassets flanking the waist
    fill_sym_box(grid, 6, 7, 9, 14, 18, 22, 1)
    fill_sym_box(grid, 7, 7, 10, 10, 19, 19, 3)  # Hip tentacle suction dots
    fill_sym_box(grid, 7, 7, 12, 12, 19, 19, 3)
    fill_sym_box(grid, 7, 7, 14, 14, 20, 20, 3)
    fill_sym_box(grid, 6, 7, 8, 9, 18, 20, 2)

    # --- 4. BULBOUS OCTOPUS-MANTLE TORSO / CHEST (Z: 23..35) ---
    # Directly sculpted from Form A's big rounded crimson head/mantle!
    # Tapered dark slate mechanical abdomen for crisp heroic waist!
    fill_sym_box(grid, 0, 4, 9, 14, 22, 24, 4)
    fill_sym_box(grid, 0, 3, 13, 15, 23, 24, 2)
    fill_sym_box(grid, 1, 2, 15, 15, 23, 24, 3)  # Pale cream ventral rib trim

    # Sculpted rounded bulbous crimson octopus-head chest dome! (Z: 24..34)
    torso_profile = [
        (24, 5.2, 12.0, 4.4, 4.4),
        (25, 6.0, 12.2, 5.0, 5.2),
        (26, 6.6, 12.4, 5.4, 5.8),
        (27, 7.0, 12.6, 5.6, 6.2),
        (28, 7.2, 12.7, 5.8, 6.4),
        (29, 7.2, 12.7, 5.8, 6.4),
        (30, 7.0, 12.5, 5.7, 6.0),
        (31, 6.6, 12.2, 5.5, 5.5),
        (32, 6.0, 11.8, 5.2, 4.8),
        (33, 5.0, 11.2, 4.8, 3.8),
        (34, 3.8, 10.2, 4.0, 2.6),
    ]
    for z, rx, yc, ry_b, ry_f in torso_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.3:
                continue
            for y in range(Y):
                dy = y - yc
                ry = ry_f if dy >= 0 else ry_b
                if (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0:
                    if dy < -ry_b * 0.65 and z <= 27:
                        col = 2
                    elif z == 24 and dy > 1.5:
                        col = 2
                    else:
                        col = 1
                    grid[x, y, z] = col

    # Coral-orange mantle spots on upper bulbous chest & rear dorsal dome (echoing Form A!)
    fill_sym_box(grid, 3, 5, 15, 17, 30, 31, 7)
    fill_sym_box(grid, 4, 5, 14, 16, 26, 27, 7)
    fill_sym_box(grid, 2, 4, 7, 8, 30, 32, 7)
    fill_sym_box(grid, 3, 4, 6, 7, 26, 28, 7)

    # Glowing Aqua Sea-Energy Core + Golden-Yellow Kraken Emblem on Center Chest!
    fill_sym_box(grid, 0, 2, 17, 19, 27, 30, 4)  # Dark slate core housing
    fill_sym_box(grid, 0, 1, 19, 19, 28, 29, 6)  # Glowing aqua sea-energy core
    fill_sym_box(grid, 2, 2, 18, 19, 28, 29, 5)  # Golden-yellow side brackets
    fill_sym_box(grid, 0, 1, 18, 19, 30, 30, 5)  # Golden-yellow upper crest
    fill_sym_box(grid, 0, 1, 18, 19, 27, 27, 3)  # Pale cream lower trim
    # Dorsal aqua hydro-vents on rear rounded mantle shell
    fill_sym_box(grid, 2, 3, 5, 6, 27, 30, 4)
    fill_sym_box(grid, 2, 3, 5, 5, 28, 29, 6)
    fill_sym_box(grid, 0, 1, 6, 7, 32, 34, 2)

    # --- 5. SHOULDERS & PAIRED TENTACLE-ARMS (Z: 13..35, x_off: 7..13) ---
    # Shoulder joint axle
    fill_sym_box(grid, 6, 9, 10, 13, 29, 32, 4)
    # Rounded crimson tentacle-coiled shoulder pauldrons with cream suction trim!
    fill_sym_box(grid, 7, 12, 9, 15, 29, 34, 1)
    fill_sym_box(grid, 8, 11, 10, 14, 34, 35, 1)
    fill_sym_box(grid, 9, 11, 11, 13, 35, 35, 7)  # Coral-orange shoulder spot
    fill_sym_box(grid, 12, 12, 10, 14, 29, 33, 1)
    fill_sym_box(grid, 12, 12, 11, 13, 30, 32, 2)
    # Pale cream suction cup dots along lower/front/outer shoulder rim!
    fill_sym_box(grid, 8, 8, 15, 15, 30, 30, 3)
    fill_sym_box(grid, 10, 10, 15, 15, 30, 30, 3)
    fill_sym_box(grid, 12, 12, 10, 10, 31, 31, 3)
    fill_sym_box(grid, 12, 12, 13, 13, 31, 31, 3)

    # Upper arms (slate inner joint wrapped in crimson tentacle band)
    fill_sym_box(grid, 9, 11, 10, 13, 23, 29, 4)
    fill_sym_box(grid, 10, 11, 10, 13, 25, 28, 1)
    fill_sym_box(grid, 11, 11, 11, 12, 26, 26, 3)  # Bicep suction dot

    # Muscular Bundled Tentacle Forearms (Z: 15..23, x_off: 9..13)
    fill_sym_box(grid, 9, 12, 9, 15, 16, 23, 1)
    fill_sym_box(grid, 12, 13, 10, 14, 17, 22, 1)
    fill_sym_box(grid, 9, 12, 9, 10, 16, 22, 2)    # Burgundy rear shadow
    fill_sym_box(grid, 10, 11, 15, 15, 17, 22, 7)  # Coral-orange dorsal ridge
    # Prominent Pale Cream Suction Cups along BOTH sides & underside of forearms!
    for fz in (17, 19, 21):
        fill_sym_box(grid, 13, 13, 11, 11, fz, fz, 3)
        fill_sym_box(grid, 13, 13, 13, 13, fz, fz, 3)
        fill_sym_box(grid, 9, 9, 13, 14, fz, fz, 3)
    # Tentacle-claw fists (Z: 13..15)
    fill_sym_box(grid, 9, 12, 10, 14, 14, 15, 4)
    fill_sym_box(grid, 10, 12, 13, 15, 13, 15, 1)
    fill_sym_box(grid, 10, 12, 14, 15, 13, 13, 3)  # Suction cup finger tips

    # --- 6. RIGHT-ARM EXTENDED KRAKEN TENTACLE-WHIP (+X, viewer's left) ---
    # Sweeping boldly OUTWARD (+X) & UPWARD (+Z) with slight forward curl so it pops cleanly in silhouette!
    whip_pts = []
    for i in range(36):
        t = i / 35.0
        wx = cx_r + 11.5 + 7.4 * (t ** 0.80)
        wy = 14.2 + 3.2 * math.sin(t * math.pi * 1.1) + 2.0 * t
        wz = 14.5 + 10.5 * (t ** 1.35) + 1.8 * math.sin(t * math.pi * 1.6)
        wrad = 1.20 * (1.0 - t) + 0.62 * t
        whip_pts.append((t, wx, wy, wz, wrad))
    prev_i = None
    for t, wx, wy, wz, wrad in whip_pts:
        col = 6 if t > 0.80 else 1
        stamp_ball(grid, wx, wy, wz, wrad, col)
        cur_i = (int(round(wx)), int(round(wy)), int(round(wz)))
        if prev_i is not None and cur_i != prev_i:
            connect_6(grid, prev_i, cur_i, col)
        prev_i = cur_i
    # Cream suction cups lining the front/underside of the Kraken tentacle whip!
    for ct in (0.18, 0.34, 0.50, 0.66, 0.78):
        idx = int(round(ct * 35))
        _, wx, wy, wz, wrad = whip_pts[idx]
        set_voxel(grid, int(round(wx)), int(round(wy + wrad * 0.8)), int(round(wz - 0.6)), 3)
        set_voxel(grid, int(round(wx + 0.3)), int(round(wy - wrad * 0.7)), int(round(wz - 0.6)), 3)

    # --- 7. LEFT-ARM TENTACLE-SHIELD COIL (-X, viewer's right) ---
    # Coiled defensive tentacle buckler wrapped on outer left forearm with cream suction cups
    fill_box(grid, cx_l - 14, cx_l - 13, 11, 17, 16, 22, 1)
    fill_box(grid, cx_l - 14, cx_l - 14, 12, 16, 17, 21, 2)
    fill_box(grid, cx_l - 14, cx_l - 14, 13, 15, 18, 20, 6)  # Aqua energy center
    for sz in (16, 19, 22):
        set_voxel(grid, cx_l - 14, 11, sz, 3)
        set_voxel(grid, cx_l - 14, 17, sz, 3)
    set_voxel(grid, cx_l - 14, 14, 16, 3)
    set_voxel(grid, cx_l - 14, 14, 22, 3)

    # --- 8. TWO DRAMATIC UPPER SHOULDER/BACK TENTACLE WHIPS (Pair 4 of 8 tentacles!) ---
    # Sprouting from rear upper shoulders, sweeping UP, OUT, and CURLING FORWARD like a Kraken!
    for side in (-1, 1):
        prev_i = None
        back_pts = []
        for i in range(44):
            t = i / 43.0
            bx = cx + side * (5.5 + 11.2 * (t ** 0.78) + 1.8 * math.sin(t * math.pi * 1.4))
            by = 8.0 - 4.0 * math.sin(t * math.pi * 0.75) + 8.5 * (t ** 2.1)
            bz = 30.0 + 11.5 * math.sin(t * math.pi * 0.72) + 1.5 * t
            brad = 1.60 * (1.0 - t) + 0.62 * t
            back_pts.append((t, bx, by, bz, brad))

        for t, bx, by, bz, brad in back_pts:
            stamp_ball(grid, bx, by, bz, brad, 1)
            if t < 0.75:
                stamp_ball(grid, bx, by - 0.5, bz - 0.4, max(0.55, brad * 0.65), 2, overwrite=False)
            cur_i = (int(round(bx)), int(round(by)), int(round(bz)))
            if prev_i is not None and cur_i != prev_i:
                connect_6(grid, prev_i, cur_i, 1)
            prev_i = cur_i

        # Prominent pale cream suction cups along the inner/lower face of both Kraken back-tentacles!
        for ct in (0.20, 0.34, 0.48, 0.62, 0.75, 0.87):
            idx = int(round(ct * 43))
            _, bx, by, bz, brad = back_pts[idx]
            set_voxel(grid, int(round(bx - side * brad * 0.5)), int(round(by + brad * 0.65)), int(round(bz - brad * 0.65)), 3)
            set_voxel(grid, int(round(bx)), int(round(by - brad * 0.7)), int(round(bz - brad * 0.5)), 3)

    # --- 9. HEROIC KRAKEN ROBOT HEAD (Z: 34..42) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 13, 33, 35, 4)
    # Sleek rounded crimson Kraken helmet
    fill_sym_box(grid, 0, 2, 9, 14, 35, 39, 1)
    fill_sym_box(grid, 0, 3, 10, 13, 36, 38, 4)   # Dark slate cheek vents
    fill_sym_box(grid, 0, 2, 10, 14, 39, 40, 1)
    fill_sym_box(grid, 0, 1, 10, 13, 40, 41, 7)   # Coral-orange crown ridge
    fill_sym_box(grid, 3, 3, 11, 12, 37, 37, 3)   # Cream ear suction dot
    fill_sym_box(grid, 0, 1, 14, 15, 35, 36, 3)   # Pale cream chin/mouthplate
    fill_sym_box(grid, 0, 0, 15, 15, 35, 35, 4)
    # Bright Golden-Yellow Expressive Kraken Visor + Aqua Glint!
    fill_sym_box(grid, 0, 2, 14, 15, 37, 38, 5)
    fill_sym_box(grid, 2, 2, 13, 14, 37, 37, 5)
    fill_sym_box(grid, 0, 0, 15, 15, 37, 37, 8)   # Center visor nose-bridge
    fill_sym_box(grid, 1, 1, 15, 15, 38, 38, 9)   # Pearl glint
    # Swept crimson & coral brow-tentacle crest horns!
    fill_sym_box(grid, 0, 0, 15, 15, 39, 40, 6)   # Glowing aqua forehead jewel
    fill_sym_box(grid, 1, 2, 14, 15, 39, 40, 7)
    fill_sym_box(grid, 2, 3, 12, 14, 40, 42, 1)
    fill_sym_box(grid, 3, 4, 10, 12, 41, 42, 1)
    fill_sym_box(grid, 3, 3, 11, 11, 40, 40, 3)   # Tiny crest suction dot

    # Hollow all strictly unseen 6-interior voxels to stay squarely in target budget
    hollow_interior_6(grid, 1, 41)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=36, pitch_a=24, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "octopus_a.vox")
    v_b = export_vox(model_b, "octopus_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: OCTOPUS -> KRAKEN OCTOPUS ROBOT",
        "1. OCTOPUS",
        "2. KRAKEN OCTOPUS ROBOT",
        "preview_octopus.png",
        yaw_a=36, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"octopus: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
