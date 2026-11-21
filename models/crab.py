import math
import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (234, 62, 34, 255),    # Rich Vermilion / Boiled-Crab Red-Orange Shell
    2: (164, 28, 22, 255),    # Deep Crimson Carapace Shading & Lower Armor
    3: (250, 234, 204, 255),  # Warm Cream / Ivory Underbelly & Claw Teeth/Tips
    4: (36, 40, 48, 255),     # Dark Charcoal Joints & Eye Pupils
    5: (82, 92, 108, 255),    # Gunmetal Mecha Inner Frame & Pistons
    6: (252, 152, 38, 255),   # Bright Golden-Orange Shell Ridge Accents & Trim
    7: (64, 228, 246, 255),   # Glowing Cyan Robot Visor & Chest Core
    8: (214, 174, 126, 255),  # Sandy-Tan Leg Accents & Claw Inner Plating
    9: (246, 250, 255, 255),  # Bright White Eye Stalks & Glints
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


def draw_sym_segment(grid, p0, p1, r0, r1, col, steps=18, shadow_col=None):
    """Draw a symmetric tapered 3D segment from (x_off, y, z) p0 to p1."""
    X = grid.shape[0]
    cx = (X - 1) / 2.0
    for side in (-1, 1):
        prev_i = None
        for i in range(steps + 1):
            t = i / float(steps)
            xo = p0[0] + (p1[0] - p0[0]) * t
            fy = p0[1] + (p1[1] - p0[1]) * t
            fz = p0[2] + (p1[2] - p0[2]) * t
            fx = cx + side * (xo + 0.5)
            rad = r0 + (r1 - r0) * t
            stamp_ball(grid, fx, fy, fz, rad, col)
            if shadow_col is not None and rad >= 0.9:
                stamp_ball(grid, fx, fy, fz - 0.55, max(0.55, rad * 0.7), shadow_col, overwrite=False)
            cur_i = (int(round(fx)), int(round(fy)), int(round(fz)))
            if prev_i is not None and cur_i != prev_i:
                connect_6(grid, prev_i, cur_i, col)
            prev_i = cur_i


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
        face_nbs = [(1 + dx, 1 + dy, 1 + dz) for dx, dy, dz in dirs6 if sub[1 + dx, 1 + dy, 1 + dz]]
        if not face_nbs:
            continue
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
# FORM A: CRAB (40 x 28 x 16)
# ==========================================
def build_a():
    grid = np.zeros((40, 28, 16), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 19.5

    # --- 1. BROAD SCULPTED SERRATED CARAPACE (甲羅, Z: 3..11) ---
    # Wide iconic oval-hexagonal crab shell, cream underbelly below, domed vermilion top
    # (z, rx, yc, ry_back, ry_front)
    shell_profile = [
        (3,  6.2, 11.2, 4.2, 4.6),
        (4,  7.6, 11.4, 5.0, 5.4),
        (5,  8.8, 11.6, 5.6, 6.0),
        (6,  9.6, 11.8, 6.0, 6.2),
        (7,  9.8, 11.8, 6.0, 6.1),
        (8,  9.0, 11.6, 5.6, 5.5),
        (9,  7.6, 11.4, 4.8, 4.7),
        (10, 5.8, 11.2, 3.8, 3.6),
        (11, 3.4, 11.0, 2.4, 2.2),
    ]
    for z, rx, yc, ry_b, ry_f in shell_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.3:
                continue
            for y in range(Y):
                dy = y - yc
                ry = ry_f if dy >= 0 else ry_b
                # Subtle hexagonal pinch at rear corners for authentic crab carapace silhouette
                eff_rx = rx * (0.92 if dy < -2.0 else 1.0)
                if (dx / eff_rx) ** 2 + (dy / ry) ** 2 <= 1.0:
                    if z <= 4:
                        col = 3  # Warm cream/ivory crab underbelly!
                    elif z == 5 and dy > 2.0:
                        col = 8  # Sandy-tan front mouth underside
                    elif z == 5:
                        col = 2  # Deep crimson lower carapace lip
                    elif z == 6 and dy < -3.5:
                        col = 2
                    else:
                        col = 1  # Rich vermilion red-orange carapace!
                    grid[x, y, z] = col

    # Sculpted carapace H-grooves & golden-orange dorsal ridge highlights (Z: 9..11)
    fill_sym_box(grid, 0, 2, 10, 12, 11, 11, 6)  # Golden-orange central shell crown highlight
    fill_sym_box(grid, 3, 4, 10, 13, 10, 10, 2)  # Deep crimson anatomical carapace crease
    fill_sym_box(grid, 5, 6, 11, 14, 9, 9, 6)    # Outer golden-orange shell ridge
    fill_sym_box(grid, 1, 3, 7, 8, 9, 9, 2)      # Rear carapace contour ridge
    fill_sym_box(grid, 0, 3, 16, 17, 7, 7, 6)    # Frontal brow ridge

    # Serrated lateral & frontal carapace spikes (iconic crab shell margin!)
    serrations = [
        (1, 18, 7),
        (4, 18, 7),
        (7, 17, 7),
        (9, 15, 7),
        (10, 13, 7),
        (10, 10, 7),
    ]
    for sx, sy, sz in serrations:
        set_sym_voxel(grid, sx, sy, sz, 6)
        set_sym_voxel(grid, sx, sy, sz - 1, 2)

    # Cream/ivory mouthparts / mandibles at front bottom of carapace
    fill_sym_box(grid, 0, 2, 17, 18, 4, 5, 3)
    fill_sym_box(grid, 1, 1, 18, 18, 4, 4, 8)
    fill_sym_box(grid, 0, 0, 18, 18, 5, 5, 4)

    # --- 2. TWIN STALKED CRAB EYES ON FRONT (Y: 17..19, Z: 8..13) ---
    # Eye socket bases
    fill_sym_box(grid, 2, 3, 17, 18, 8, 8, 6)
    # Bright white angled eye stalks (color 9) rising up & slightly forward
    fill_sym_box(grid, 2, 3, 18, 18, 9, 11, 9)
    fill_sym_box(grid, 3, 3, 19, 19, 11, 12, 9)
    # Glossy dark charcoal crab eye beads (color 4) with white glint (9)
    fill_sym_box(grid, 2, 3, 18, 20, 12, 13, 4)
    set_sym_voxel(grid, 2, 20, 13, 9)  # Crisp white glint!
    set_sym_voxel(grid, 3, 18, 12, 1)  # Tiny red rear eyelid cap

    # --- 3. TWO MASSIVE CURVED PINCER CLAWS HELD FORWARD (ハサミ, Y: 14..26, Z: 2..11) ---
    # Jointed arm segments (merus + carpus) emerging cleanly from front-side carapace
    draw_sym_segment(grid, (7.0, 15.0, 6.0), (11.5, 17.2, 6.2), 1.6, 1.4, 1, steps=14, shadow_col=2)
    draw_sym_segment(grid, (11.5, 17.2, 6.2), (12.8, 20.0, 6.0), 1.5, 1.9, 1, steps=12, shadow_col=2)
    # Dark charcoal & sandy-tan elbow joint accent
    fill_sym_box(grid, 11, 12, 17, 18, 5, 6, 4)
    fill_sym_box(grid, 12, 13, 17, 18, 7, 7, 6)  # Elbow carapace spike

    # Swollen muscular claw palm (propodus) curving forward & inward
    draw_sym_segment(grid, (12.2, 19.5, 6.0), (10.5, 22.8, 6.2), 2.35, 2.55, 1, steps=16, shadow_col=2)
    # Golden-orange ridge on top of swollen claw palm + warm cream underside!
    fill_sym_box(grid, 10, 12, 20, 23, 8, 8, 6)
    fill_sym_box(grid, 10, 12, 20, 23, 3, 4, 3)

    # UPPER MOVABLE PINCER FINGER (dactylus) curving inward toward centerline!
    draw_sym_segment(grid, (10.0, 22.8, 7.8), (6.4, 25.2, 9.2), 1.40, 1.02, 1, steps=16, shadow_col=6)
    draw_sym_segment(grid, (6.4, 25.2, 9.2), (4.2, 24.4, 7.8), 1.02, 0.70, 1, steps=12)
    # Warm cream/ivory serrated crusher teeth along underside of upper pincer!
    set_sym_voxel(grid, 8, 24, 7, 3)
    set_sym_voxel(grid, 6, 25, 8, 3)
    set_sym_voxel(grid, 4, 24, 7, 3)

    # LOWER FIXED PINCER FINGER curving forward & inward beneath upper pincer (clear open V-gap!)
    draw_sym_segment(grid, (10.0, 22.8, 4.2), (6.4, 25.2, 3.2), 1.30, 0.92, 2, steps=16, shadow_col=3)
    draw_sym_segment(grid, (6.4, 25.2, 3.2), (4.2, 24.6, 4.4), 0.92, 0.68, 3, steps=12)
    # Warm cream/ivory serrated crusher teeth along top of lower pincer!
    set_sym_voxel(grid, 8, 24, 5, 3)
    set_sym_voxel(grid, 6, 25, 4, 3)
    set_sym_voxel(grid, 4, 25, 5, 3)

    # --- 4. SIX (3 PAIRS) ARTICULATED WALKING LEGS SPLAYED SYMMETRICALLY (Z: 0..6) ---
    # (root_xo, root_y, knee_xo, knee_y, knee_z, tip_xo, tip_y)
    leg_specs = [
        (7.5, 12.8, 13.0, 14.0, 5.6, 17.5, 15.2),  # Pair 1: Front walking legs
        (7.8, 10.2, 14.0,  9.8, 5.8, 18.2,  9.5),  # Pair 2: Middle walking legs (widest)
        (6.8,  7.4, 12.4,  5.2, 5.4, 16.5,  2.8),  # Pair 3: Rear walking legs
    ]
    for rx, ry, kx, ky, kz, tx, ty in leg_specs:
        # Upper leg (merus): vermilion shell with crimson underside
        draw_sym_segment(grid, (rx, ry, 4.8), (kx, ky, kz), 1.15, 0.95, 1, steps=14, shadow_col=2)
        # Charcoal knee joint
        set_sym_voxel(grid, int(round(kx)), int(round(ky)), int(round(kz)), 4)
        set_sym_voxel(grid, int(round(kx)), int(round(ky)), int(round(kz)) + 1, 6)
        # Mid leg (carpus/propodus): angling down toward ground
        mx = (kx + tx) * 0.52
        my = (ky + ty) * 0.52
        mz = 2.6
        draw_sym_segment(grid, (kx, ky, kz), (mx, my, mz), 0.92, 0.78, 1, steps=12, shadow_col=8)
        # Lower pointed crab claw tip (dactylus): sandy-tan & warm cream gripping Z=0!
        draw_sym_segment(grid, (mx, my, mz), (tx, ty, 0.3), 0.76, 0.55, 8, steps=12)
        set_sym_voxel(grid, int(round(tx)), int(round(ty)), 0, 3)

    # Hollow unseen carapace core to hit crisp voxel budget
    hollow_interior_26(grid, 4, 10)

    return grid


# ==========================================
# FORM B: HEAVY BRAWLER CRAB ROBOT (42 x 26 x 42)
# ==========================================
def build_b():
    grid = np.zeros((42, 26, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 20.5

    # --- 1. HEAVY CRUSTACEAN BRAWLER BOOTS (Z: 0..3) ---
    # Heavy charcoal soles & gunmetal heel spurs
    fill_sym_box(grid, 2, 6, 8, 15, 0, 1, 4)
    fill_sym_box(grid, 3, 5, 6, 8, 0, 2, 5)
    # Split armored crustacean front claws/toes
    fill_sym_box(grid, 2, 3, 14, 17, 0, 2, 1)
    fill_sym_box(grid, 5, 6, 14, 17, 0, 2, 1)
    fill_sym_box(grid, 2, 3, 17, 18, 0, 1, 3)  # Warm cream armored toe tips
    fill_sym_box(grid, 5, 6, 17, 18, 0, 1, 3)
    fill_sym_box(grid, 2, 6, 11, 15, 1, 3, 1)  # Vermilion boot shell
    fill_sym_box(grid, 3, 5, 14, 15, 2, 3, 6)  # Golden-orange instep ridge
    fill_sym_box(grid, 2, 6, 8, 10, 1, 2, 2)   # Deep crimson heel wrap
    # Ankle joint
    fill_sym_box(grid, 3, 5, 9, 13, 3, 4, 5)

    # --- 2. THICK ARMORED LOWER LEGS & KNEE GUARDS (Z: 4..15) ---
    fill_sym_box(grid, 3, 5, 9, 13, 4, 14, 5)  # Gunmetal inner frame
    fill_sym_box(grid, 2, 6, 11, 14, 4, 13, 1) # Vermilion front shin armor
    fill_sym_box(grid, 3, 5, 14, 15, 5, 12, 1)
    fill_sym_box(grid, 4, 4, 15, 15, 6, 11, 6) # Golden-orange shin crest
    fill_sym_box(grid, 2, 6, 8, 10, 4, 13, 2)  # Deep crimson calf plating
    fill_sym_box(grid, 6, 6, 10, 13, 5, 12, 2) # Outer side shin plate
    fill_sym_box(grid, 6, 6, 11, 12, 7, 10, 8) # Sandy-tan mechanical calf panel
    # Rear hydraulic calf pistons
    fill_sym_box(grid, 3, 5, 7, 8, 5, 11, 4)
    fill_sym_box(grid, 4, 4, 7, 7, 6, 10, 9)
    # Heavy spiked brawler knee guards
    fill_sym_box(grid, 2, 6, 13, 16, 12, 15, 1)
    fill_sym_box(grid, 3, 5, 16, 16, 13, 15, 6)
    fill_sym_box(grid, 4, 4, 16, 16, 14, 14, 7)  # Glowing cyan knee sensor

    # --- 3. MUSCULAR THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 20, 5)
    fill_sym_box(grid, 3, 5, 12, 14, 16, 19, 4)  # Dark charcoal inner thigh armor
    fill_sym_box(grid, 4, 4, 14, 14, 17, 18, 8)  # Sandy-tan front piston accent
    fill_sym_box(grid, 5, 5, 10, 13, 16, 19, 2)

    # --- 4. WAIST / PELVIS + 6 FOLDED WALKING-LEG HIP-SKIRTS / TASSETS (腰回り, Z: 14..23) ---
    # Heavy armored pelvis core
    fill_sym_box(grid, 0, 5, 9, 14, 20, 23, 5)
    fill_sym_box(grid, 0, 4, 13, 15, 20, 22, 3)  # Warm cream crab-underbelly waist plate!
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 1)  # Vermilion center codpiece
    fill_sym_box(grid, 0, 1, 16, 16, 20, 21, 6)  # Golden-orange belt buckle
    fill_sym_box(grid, 0, 0, 16, 16, 21, 21, 7)  # Cyan belt gem
    # Rear waist armor plate
    fill_sym_box(grid, 0, 4, 7, 9, 19, 22, 2)
    fill_sym_box(grid, 0, 2, 7, 8, 20, 21, 1)

    # ALL 6 CRAB WALKING LEGS (3 SYMMETRICAL PAIRS) FOLDED AROUND THE WAIST AS ARMORED HIP-SKIRTS!
    # Clearly legible vermilion upper leg -> charcoal/gold knee -> tapered sandy-tan/cream claw tip!
    # Pair 1: Front-side crab-leg tassets (Z: 15..22, Y: 14..16)
    draw_sym_segment(grid, (4.2, 13.8, 21.6), (7.6, 15.8, 19.6), 1.05, 0.90, 1, steps=12, shadow_col=2)
    set_sym_voxel(grid, 8, 16, 20, 6)  # Golden knee ridge
    set_sym_voxel(grid, 8, 16, 19, 4)  # Articulated charcoal knee joint
    draw_sym_segment(grid, (7.6, 15.8, 19.6), (7.0, 16.4, 15.2), 0.85, 0.56, 1, steps=12)
    draw_sym_segment(grid, (7.2, 16.2, 17.0), (7.0, 16.4, 15.0), 0.72, 0.52, 8, steps=6)
    set_sym_voxel(grid, 7, 16, 14, 3)  # Warm cream claw tip

    # Pair 2: Wide mid-side crab-leg hip-skirts (Z: 14..22, Y: 10..12)
    draw_sym_segment(grid, (5.2, 11.2, 21.6), (9.6, 11.2, 19.6), 1.12, 0.92, 1, steps=14, shadow_col=2)
    set_sym_voxel(grid, 10, 11, 20, 6)  # Golden-orange knee spine
    set_sym_voxel(grid, 10, 11, 19, 4)
    draw_sym_segment(grid, (9.6, 11.2, 19.6), (9.2, 11.2, 14.6), 0.88, 0.56, 1, steps=12)
    draw_sym_segment(grid, (9.4, 11.2, 16.8), (9.2, 11.2, 14.6), 0.72, 0.52, 8, steps=6)
    set_sym_voxel(grid, 9, 11, 14, 3)  # Cream claw tip

    # Pair 3: Rear-side crab-leg tail-tassets (Z: 14..22, Y: 5..9 — clearly visible from rear view!)
    draw_sym_segment(grid, (4.2, 8.4, 21.4), (7.8, 6.2, 19.2), 1.05, 0.90, 1, steps=12, shadow_col=2)
    set_sym_voxel(grid, 8, 6, 20, 6)
    set_sym_voxel(grid, 8, 6, 19, 4)
    draw_sym_segment(grid, (7.8, 6.2, 19.2), (7.2, 5.2, 14.8), 0.85, 0.56, 1, steps=12)
    draw_sym_segment(grid, (7.4, 5.6, 16.8), (7.2, 5.2, 14.8), 0.72, 0.52, 8, steps=6)
    set_sym_voxel(grid, 7, 5, 14, 3)  # Cream claw tip

    # --- 5. BROAD SERRATED CARAPACE CHEST & REAR SHELL BACKPACK (胸, Z: 23..34) ---
    # Segmented warm-cream crab-sternum abdomen (Z: 23..25)
    fill_sym_box(grid, 0, 4, 9, 14, 23, 25, 5)
    fill_sym_box(grid, 0, 3, 13, 15, 23, 25, 3)  # Warm cream crab belly plates!
    fill_sym_box(grid, 0, 3, 15, 15, 24, 24, 8)  # Horizontal abdominal segment line

    # Broad Armored Red-Orange Carapace Chest (Z: 25..33)
    fill_sym_box(grid, 0, 6, 8, 15, 25, 32, 1)
    fill_sym_box(grid, 0, 5, 14, 17, 26, 32, 1)  # Protruding broad carapace breastplate!
    fill_sym_box(grid, 0, 4, 17, 18, 27, 31, 1)
    fill_sym_box(grid, 5, 6, 14, 16, 26, 31, 2)  # Deep crimson outer chest bevel
    # Golden-orange serrated carapace ridges sweeping cleanly across upper & lower chest!
    fill_sym_box(grid, 2, 5, 16, 17, 32, 32, 6)
    fill_sym_box(grid, 1, 4, 16, 17, 26, 26, 6)
    fill_sym_box(grid, 3, 5, 17, 17, 28, 30, 2)  # Anatomical carapace chest grooves
    # Glowing Cyan Hexagonal Brawler Chest Core
    fill_sym_box(grid, 0, 1, 18, 18, 28, 30, 4)  # Dark charcoal bezel
    fill_sym_box(grid, 0, 1, 18, 18, 29, 30, 7)  # Glowing cyan reactor core
    fill_sym_box(grid, 0, 0, 18, 18, 28, 28, 7)
    fill_sym_box(grid, 2, 2, 18, 18, 29, 30, 6)  # Golden-orange core side fins
    # High armored crab collar flanking neck
    fill_sym_box(grid, 2, 5, 10, 14, 32, 33, 2)
    fill_sym_box(grid, 3, 5, 13, 14, 33, 33, 6)

    # Rear Sculpted Carapace Shell Backpack (Y: 4..8, Z: 23..34)
    fill_sym_box(grid, 0, 5, 5, 8, 24, 32, 1)
    fill_sym_box(grid, 0, 4, 4, 5, 25, 31, 1)
    fill_sym_box(grid, 0, 3, 4, 4, 26, 30, 2)    # Rear carapace dome shading
    fill_sym_box(grid, 0, 2, 4, 4, 28, 29, 6)    # Rear golden-orange carapace ridge
    fill_sym_box(grid, 4, 5, 5, 6, 26, 32, 6)    # Serrated rear carapace spikes
    # Twin hydro-thrusters under rear carapace
    fill_sym_box(grid, 2, 3, 3, 5, 23, 26, 5)
    fill_sym_box(grid, 2, 3, 3, 3, 23, 24, 7)    # Glowing cyan thruster ports

    # --- 6. CURVED SERRATED SHELL SHOULDER PAULDRONS (肩, Z: 29..37, x_off: 7..15) ---
    # Heavy gunmetal shoulder bridge
    fill_sym_box(grid, 6, 10, 10, 13, 29, 32, 5)
    # Massive Domed Crab-Carapace Half-Shells arching over BOTH shoulders!
    fill_sym_box(grid, 7, 14, 8, 15, 30, 35, 1)
    fill_sym_box(grid, 8, 13, 9, 14, 35, 36, 1)
    fill_sym_box(grid, 9, 12, 10, 13, 36, 37, 1)
    fill_sym_box(grid, 14, 15, 9, 14, 29, 34, 1)  # Outer flared shell lip
    fill_sym_box(grid, 14, 15, 9, 14, 29, 30, 2)  # Deep crimson underside lip
    fill_sym_box(grid, 8, 13, 10, 13, 29, 29, 3)  # Warm cream inner shell lining!
    # Iconic Golden-Orange Serrated Crab-Shell Spikes along outer shoulder curve!
    fill_sym_box(grid, 9, 12, 10, 13, 37, 37, 6)  # Crown ridge
    fill_sym_box(grid, 14, 15, 14, 15, 32, 34, 6) # Front carapace spike
    fill_sym_box(grid, 15, 16, 11, 12, 31, 33, 6) # Lateral carapace spike
    fill_sym_box(grid, 14, 15, 8, 9, 32, 34, 6)   # Rear carapace spike
    fill_sym_box(grid, 8, 13, 15, 15, 31, 32, 2)  # Front shell contour groove

    # --- 7. HUGE SYMMETRICAL PINCER CLAW ARMS / GAUNTLETS (両腕, Z: 12..29, x_off: 10..19) ---
    # Muscular gunmetal & crimson upper arms descending from beneath the shell pauldrons
    fill_sym_box(grid, 10, 13, 10, 13, 24, 29, 5)
    fill_sym_box(grid, 11, 13, 10, 13, 25, 28, 4)
    fill_sym_box(grid, 12, 14, 11, 13, 25, 27, 1)  # Outer bicep shell guard
    # Elbow hinge joint
    fill_sym_box(grid, 11, 14, 10, 14, 22, 24, 5)
    fill_sym_box(grid, 14, 15, 11, 12, 23, 24, 6)  # Elbow spur

    # COLOSSAL SYMMETRICAL CRAB PINCER GAUNTLETS (both Left & Right arms!)
    # Massive bulbous vermilion claw palm (propodus) forming the heavy forearm
    fill_sym_box(grid, 11, 17, 10, 17, 15, 22, 1)
    fill_sym_box(grid, 12, 18, 11, 16, 16, 21, 1)
    fill_sym_box(grid, 17, 18, 12, 16, 17, 20, 6)  # Golden-orange outer claw crest
    fill_sym_box(grid, 11, 17, 10, 16, 15, 16, 2)  # Deep crimson lower claw shell
    fill_sym_box(grid, 11, 11, 11, 16, 16, 21, 3)  # Warm cream inner forearm claw plate!
    fill_sym_box(grid, 13, 16, 9, 10, 16, 21, 2)   # Rear elbow carapace dome
    # Gunmetal hydraulic hinge piston at pincer base
    fill_sym_box(grid, 11, 12, 15, 17, 17, 19, 5)
    fill_sym_box(grid, 17, 18, 15, 16, 18, 19, 4)

    # HUGE UPPER CURVED PINCER JAW projecting forward along +Y (Z: 19..23, Y: 17..25)
    fill_sym_box(grid, 12, 17, 17, 20, 20, 22, 1)
    fill_sym_box(grid, 12, 16, 20, 22, 20, 22, 1)
    fill_sym_box(grid, 13, 16, 22, 24, 19, 21, 1)
    fill_sym_box(grid, 13, 15, 24, 25, 18, 19, 1)  # Sharp downward-hooked pincer fang tip!
    fill_sym_box(grid, 14, 16, 18, 22, 22, 23, 6)  # Golden-orange upper jaw ridge
    # Warm cream/ivory serrated crusher teeth along underside of upper pincer!
    fill_sym_box(grid, 13, 15, 18, 18, 19, 19, 3)
    fill_sym_box(grid, 13, 15, 20, 20, 19, 19, 3)
    fill_sym_box(grid, 13, 15, 22, 22, 18, 18, 3)

    # HUGE LOWER CURVED PINCER JAW projecting forward along +Y (Z: 12..15, Y: 17..24)
    # Wide dramatic open V-gap (Z: 16..18, Y: 18..23) between the crusher jaws!
    fill_sym_box(grid, 12, 17, 17, 19, 13, 15, 2)
    fill_sym_box(grid, 12, 16, 19, 21, 12, 14, 1)
    fill_sym_box(grid, 13, 15, 21, 23, 13, 14, 1)
    fill_sym_box(grid, 13, 15, 23, 24, 14, 15, 3)  # Upward-hooked cream tip!
    # Warm cream/ivory serrated crusher teeth along top of lower pincer!
    fill_sym_box(grid, 13, 15, 18, 18, 16, 16, 3)
    fill_sym_box(grid, 13, 15, 20, 20, 15, 15, 3)

    # --- 8. HEROIC CRAB-BRAWLER HEAD WITH STALKED-EYE ANTENNAE (Z: 33..41) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 13, 32, 34, 5)
    # Armored vermilion crab helmet
    fill_sym_box(grid, 0, 2, 9, 14, 34, 38, 1)
    fill_sym_box(grid, 0, 3, 10, 13, 35, 37, 1)
    fill_sym_box(grid, 0, 2, 10, 14, 38, 39, 1)
    fill_sym_box(grid, 0, 1, 10, 13, 39, 39, 6)  # Golden-orange helmet crest ridge
    # Warm cream/ivory faceplate & armored chin guard
    fill_sym_box(grid, 0, 1, 14, 15, 34, 35, 3)
    fill_sym_box(grid, 0, 0, 15, 15, 34, 34, 8)
    # Side helmet ear pods
    fill_sym_box(grid, 3, 3, 10, 12, 35, 37, 2)
    fill_sym_box(grid, 3, 3, 11, 11, 36, 37, 6)
    # Glowing Cyan Brawler Visor (popping intensely against red-orange helmet!)
    fill_sym_box(grid, 0, 2, 14, 15, 36, 37, 7)
    fill_sym_box(grid, 2, 2, 13, 14, 36, 37, 7)
    # Serrated brow overhang
    fill_sym_box(grid, 0, 2, 14, 15, 38, 38, 1)
    fill_sym_box(grid, 0, 0, 15, 15, 38, 39, 6)  # Forehead golden crest jewel
    # Twin Iconic Stalked-Eye Crest Antennae (unmistakable echo of Form A's crab eye-stalks!)
    fill_sym_box(grid, 2, 2, 13, 14, 39, 40, 9)  # Crisp white stalks
    fill_sym_box(grid, 3, 3, 13, 14, 40, 41, 4)  # Dark glossy sensor beads
    set_sym_voxel(grid, 3, 14, 41, 7)            # Glowing cyan eye-stalk glint!

    # Hollow all strictly unseen 6-interior voxels to stay squarely in target budget
    hollow_interior_6(grid, 1, 40)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=26, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "crab_a.vox")
    v_b = export_vox(model_b, "crab_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: CRAB -> HEAVY BRAWLER CRAB ROBOT",
        "1. CRAB",
        "2. HEAVY BRAWLER CRAB ROBOT",
        "preview_crab.png",
        yaw_a=38, pitch_a=26, yaw_b=32, pitch_b=20,
    )
    print(f"crab: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
