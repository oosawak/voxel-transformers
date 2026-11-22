import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Japanese Weasel (Itachi) -> Slender High-Speed Scout Robot!
# Elongated lithe body -> Sleek Torso, Quick nimble legs -> Agile Runner Legs!
PALETTE = {
    1: (202, 118, 44, 255),   # Warm Cinnamon-Russet Weasel Fur & Main Armor
    2: (142, 74, 26, 255),    # Deep Chestnut-Brown Dorsal Shading & Armor Bevels
    3: (246, 234, 200, 255),  # Soft Cream-Ivory Throat, Belly & Chest Plates
    4: (56, 36, 26, 255),     # Dark Umber-Brown Face Mask, Paws & Tail Tip
    5: (64, 70, 84, 255),     # Sleek Dark Gunmetal Inner Joints & Claws
    6: (242, 188, 54, 255),   # Amber-Gold Speed Trim & Collar Fittings
    7: (208, 52, 42, 255),    # Vermilion Scout Scarf & Accent Cord
    8: (116, 238, 86, 255),   # Bright Leaf-Green Glowing Eyes & Sensor Core
    9: (226, 166, 94, 255),   # Warm Pale Tan Fur Highlights
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


def count_components_6(grid):
    """Return number of 6-connected components and min Z."""
    xs, ys, zs = np.nonzero(grid)
    if len(xs) == 0:
        return 0, -1
    occupied = set(zip(xs.tolist(), ys.tolist(), zs.tolist()))
    visited = set()
    comps = 0
    for start in occupied:
        if start in visited:
            continue
        comps += 1
        q = deque([start])
        visited.add(start)
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nb = (x + dx, y + dy, z + dz)
                if nb in occupied and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
    return comps, int(zs.min())


# ============================================================
# FORM A: ITACHI (JAPANESE WEASEL — LONG LITHE BODY & NIMBLE LEGS) (20 x 56 x 22)
# ============================================================
def build_a():
    grid = np.zeros((20, 56, 22), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 9.5

    # --- 1. LONG, SLENDER, ARCHING WEASEL BODY (細長い体!) (Y: 16..44, Z: 5..15) ---
    # Classic sinuous arched mustelid spine: low nimble hindquarters -> high supple arch -> long sleek neck!
    spine_nodes = [
        # (y, z_center, rx, rz)
        (16, 7.5,  2.5, 2.3),
        (17, 8.2,  3.1, 2.8),
        (18, 8.8,  3.4, 3.0),
        (19, 9.4,  3.5, 3.0),  # Hind haunches
        (20, 10.0, 3.4, 2.9),
        (21, 10.5, 3.2, 2.8),
        (22, 11.0, 3.1, 2.7),
        (23, 11.4, 3.0, 2.7),  # Sinuous arched weasel back!
        (24, 11.6, 3.0, 2.7),
        (25, 11.7, 3.0, 2.7),
        (26, 11.6, 3.0, 2.7),
        (27, 11.4, 3.1, 2.7),
        (28, 11.1, 3.2, 2.8),
        (29, 10.8, 3.3, 2.8),
        (30, 10.5, 3.4, 2.9),
        (31, 10.2, 3.4, 2.9),  # Sleek shoulders
        (32, 10.1, 3.3, 2.8),
        (33, 10.2, 3.1, 2.7),
        (34, 10.5, 2.9, 2.6),
        (35, 11.0, 2.7, 2.5),  # Long agile weasel neck!
        (36, 11.7, 2.6, 2.5),
        (37, 12.5, 2.5, 2.5),
        (38, 13.4, 2.5, 2.5),
        (39, 14.2, 2.6, 2.5),
        (40, 14.9, 2.7, 2.5),
    ]
    for y, zc, rx, rz in spine_nodes:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(int(zc - rz - 1), int(zc + rz + 2)):
                if 0 <= z < Z:
                    dz = z - zc
                    if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                        if z <= zc - rz * 0.42 and dx <= rx * 0.72:
                            col = 3  # Soft cream-ivory throat & belly!
                        elif z >= zc + rz * 0.55 and dx <= rx * 0.65:
                            col = 2  # Deep chestnut dorsal stripe
                        elif z >= zc and (y % 4 == 0) and dx >= rx * 0.65:
                            col = 9  # Pale tan fur highlight
                        else:
                            col = 1  # Warm cinnamon-russet fur
                        grid[x, y, z] = col

    # Subtle Vermilion & Gold Scout Collar Scarf around neck (links cleanly to robot!)
    fill_sym_box(grid, 0, 2, 35, 37, 10, 14, 7)
    fill_sym_box(grid, 0, 1, 37, 38, 10, 11, 6)  # Gold scarf clasp on throat

    # --- 2. FOUR QUICK, NIMBLE WEASEL LEGS (素早い脚!) (Z: 0..10) ---
    def build_weasel_leg(side_sign, y_hip, y_knee, y_paw, is_front):
        x_hip = cx + side_sign * 2.5
        x_paw = cx + side_sign * 2.7
        z_top = 9
        for z in range(0, z_top + 1):
            t = z / float(z_top)
            if t < 0.45:
                s = t / 0.45
                ly = y_paw * (1 - s) + y_knee * s
            else:
                s = (t - 0.45) / 0.55
                ly = y_knee * (1 - s) + y_hip * s
            lx = x_paw * (1 - t) + x_hip * t
            rx_l = 1.25 if z <= 5 else 1.65
            ry_l = 1.55 if z <= 1 else (1.30 if z <= 5 else 1.85)
            for x in range(int(lx - 2), int(lx + 3)):
                for y in range(int(ly - 2), int(ly + 3)):
                    if 0 <= x < X and 0 <= y < Y:
                        if ((x - lx) / rx_l) ** 2 + ((y - ly) / ry_l) ** 2 <= 1.0:
                            if z <= 2:
                                col = 4  # Dark umber nimble paws!
                            elif z == 3 and is_front:
                                col = 6  # Gold ankle speed-ring
                            else:
                                col = 1
                            grid[x, y, z] = col
        # Grounded quick paws at z=0
        px0, px1 = int(round(x_paw - 1.0)), int(round(x_paw + 1.0))
        fill_box(grid, px0, px1, int(round(y_paw - 0.5)), int(round(y_paw + 1.8)), 0, 1, 4)

    # Dynamic darting stride!
    build_weasel_leg(+1, y_hip=32.0, y_knee=30.5, y_paw=35.0, is_front=True)
    build_weasel_leg(-1, y_hip=32.0, y_knee=29.0, y_paw=31.0, is_front=True)
    build_weasel_leg(+1, y_hip=19.0, y_knee=16.5, y_paw=21.5, is_front=False)
    build_weasel_leg(-1, y_hip=19.0, y_knee=15.0, y_paw=18.0, is_front=False)

    # --- 3. KEEN WEASEL HEAD, DARK FACE MASK & ROUNDED EARS (Y: 40..53, Z: 12..21) ---
    fill_sphere_local(grid, cx, 43.0, 16.0, 3.0, 3.6, 2.8, 1)
    # Dark umber weasel bandit-mask around eyes & snout bridge!
    fill_sym_box(grid, 0, 2, 44, 48, 15, 17, 4)
    # Bright keen leaf-green eyes!
    fill_sym_box(grid, 2, 2, 45, 46, 16, 17, 8)
    # Tapered sleek muzzle, cream chin & dark nose!
    fill_sym_box(grid, 0, 1, 46, 50, 14, 16, 4)
    fill_sym_box(grid, 0, 1, 46, 49, 13, 14, 3)  # Cream lower jaw & chin!
    fill_sym_box(grid, 0, 0, 50, 52, 15, 16, 4)  # Small dark nose tip
    # Alert rounded weasel ears with cream inner edge
    fill_sym_box(grid, 2, 3, 41, 43, 18, 20, 1)
    fill_sym_box(grid, 2, 3, 41, 41, 19, 20, 2)
    fill_sym_box(grid, 2, 2, 43, 43, 19, 19, 3)  # Cream inner ear

    # --- 4. LONG BUSHY TAPERED WEASEL TAIL WITH DARK TIP (Y: 1..17, Z: 5..14) ---
    tail_nodes = [
        (cx,       16.0,  7.5, 1.8, 1),
        (cx,       14.2,  7.0, 1.8, 1),
        (cx + 0.3, 12.4,  6.8, 1.8, 1),
        (cx + 0.6, 10.6,  7.0, 1.7, 2),
        (cx + 0.9,  8.8,  7.6, 1.7, 1),
        (cx + 1.1,  7.0,  8.5, 1.6, 1),
        (cx + 1.2,  5.3,  9.6, 1.5, 2),
        (cx + 1.1,  3.8, 10.8, 1.3, 4),  # Dark umber weasel tail tip!
        (cx + 0.9,  2.5, 12.0, 1.1, 4),
    ]
    prev_t = None
    for txc, tyc, tzc, tr, tcol in tail_nodes:
        if prev_t is not None:
            draw_6conn_line(grid, prev_t, (txc, tyc, tzc), tcol)
        prev_t = (txc, tyc, tzc)
        fill_sphere_local(grid, txc, tyc, tzc, tr, 1.6, tr, tcol)

    # Keep slender weasel solid inside so voxel count sits cleanly above 1,200
    return grid


# ============================================================
# FORM B: ITACHI AGILE SCOUT ROBOT (38 x 26 x 46)
# Elongated body -> Sleek Vertical Torso, Quick legs -> Agile Runner Legs!
# ============================================================
def build_b():
    grid = np.zeros((38, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18
    cx_r = X // 2      # 19

    # --- 1. SWIFT RUNNER PAW-BOOTS & AGILE DIGI-STYLE LEGS (素早い脚がロボの脚!) (Z: 0..20) ---
    # Sleek dark-umber claw-runner feet with speed heel spurs!
    fill_sym_box(grid, 2, 4, 10, 17, 0, 1, 4)    # Dark umber paw sole
    fill_sym_box(grid, 2, 4, 11, 17, 1, 2, 1)    # Cinnamon-russet instep
    fill_sym_box(grid, 2, 2, 17, 18, 0, 1, 4)    # Split runner claws
    fill_sym_box(grid, 4, 4, 17, 18, 0, 1, 4)
    fill_sym_box(grid, 3, 3, 8, 10, 0, 2, 5)     # Speed heel spur
    fill_sym_box(grid, 2, 4, 11, 15, 3, 3, 6)    # Gold ankle speed-ring!

    # Sleek Tapered Runner Greaves (Z: 4..15)
    fill_sym_box(grid, 2, 4, 10, 14, 4, 14, 1)   # Warm cinnamon-russet shins
    fill_sym_box(grid, 3, 3, 14, 15, 5, 13, 3)   # Cream front shin speed-stripe
    fill_sym_box(grid, 4, 4, 11, 13, 5, 12, 2)   # Chestnut outer calf armor
    fill_sym_box(grid, 3, 4, 9, 10, 7, 12, 5)    # Rear leg sprint thrusters!
    # Aerodynamic Swept Knee Guards
    fill_sym_box(grid, 2, 4, 14, 16, 13, 16, 2)
    fill_sym_box(grid, 3, 3, 16, 17, 14, 16, 6)  # Gold knee ridge

    # Athletic Thighs & Nimble Waist (Z: 15..23)
    fill_sym_box(grid, 2, 4, 10, 14, 15, 20, 5)
    fill_sym_box(grid, 2, 4, 13, 15, 16, 19, 1)
    fill_sym_box(grid, 3, 4, 14, 15, 17, 18, 9)
    fill_sym_box(grid, 0, 3, 10, 14, 20, 23, 5)  # Slim agile waist pelvis
    fill_sym_box(grid, 1, 4, 14, 15, 18, 21, 1)  # Sleek front tassets
    fill_sym_box(grid, 4, 5, 10, 14, 19, 22, 2)  # Hip thrusters
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 3)  # Cream center front plate
    fill_sym_box(grid, 0, 0, 16, 16, 21, 21, 6)  # Gold belt core

    # Dynamic Sweeping Weasel Tail Stabilizer curving out behind waist! (clearly visible in REAR VIEW)
    cx_f = (X - 1) / 2.0
    tail_r = [
        (cx_f,       9.5, 20.5, 1.3, 1),
        (cx_f,       8.0, 19.0, 1.5, 1),
        (cx_f,       6.5, 17.5, 1.6, 2),
        (cx_f,       5.0, 16.5, 1.5, 1),
        (cx_f,       3.6, 16.2, 1.4, 1),
        (cx_f,       2.5, 17.0, 1.2, 4),
        (cx_f,       1.8, 18.2, 1.0, 4),
    ]
    prev_t = None
    for txc, tyc, tzc, tr, tcol in tail_r:
        if prev_t is not None:
            draw_6conn_line(grid, prev_t, (txc, tyc, tzc), tcol)
        prev_t = (txc, tyc, tzc)
        fill_sphere_local(grid, txc, tyc, tzc, tr, 1.3, tr, tcol)

    # --- 2. SLENDER ELONGATED WEASEL-BODY TORSO (細長い体が胴体!) (Z: 23..35) ---
    fill_sym_box(grid, 0, 3, 10, 14, 23, 26, 1)  # Slender elongated abdomen!
    fill_sym_box(grid, 0, 2, 14, 15, 23, 26, 3)  # Cream-ivory belly stripe continuing up torso!
    # Sleek Streamlined Scout Chest (Z: 27..34)
    fill_sym_box(grid, 0, 5, 9, 15, 27, 33, 1)   # Warm cinnamon-russet chest
    fill_sym_box(grid, 0, 3, 15, 16, 27, 33, 3)  # Crisp cream-ivory chest bib (from weasel throat!)
    fill_sym_box(grid, 3, 5, 14, 16, 28, 32, 2)  # Chestnut chest bevels
    fill_sym_box(grid, 0, 1, 16, 16, 29, 31, 6)  # Gold center speed badge
    fill_sym_box(grid, 0, 0, 16, 17, 30, 30, 8)  # Glowing leaf-green core
    # Flowing Vermilion Scout Scarf wrapping the collar & streaming slightly back! (Z: 33..35)
    fill_sym_box(grid, 0, 4, 10, 15, 33, 34, 7)
    fill_sym_box(grid, 1, 2, 7, 10, 32, 34, 7)
    fill_sym_box(grid, 1, 2, 5, 7, 30, 32, 7)
    # Compact Rear Back Thrusters (Y: 7..9, Z: 26..32)
    fill_sym_box(grid, 0, 3, 7, 9, 26, 32, 2)
    fill_sym_box(grid, 1, 2, 6, 7, 26, 28, 5)

    # --- 3. SLEEK AERODYNAMIC SHOULDERS & CLAWED ARMS (Z: 15..35) ---
    fill_sym_box(grid, 5, 7, 11, 14, 30, 33, 5)
    fill_sym_box(grid, 6, 8, 10, 15, 29, 34, 1)  # Swept cinnamon shoulder armor
    fill_sym_box(grid, 7, 9, 11, 14, 32, 34, 2)  # Chestnut top ridge
    fill_sym_box(grid, 8, 9, 11, 14, 31, 31, 6)  # Gold speed stripe
    # Slender Agile Arms with Dual Weasel-Claw Speed Blades!
    fill_sym_box(grid, 6, 7, 11, 14, 23, 29, 5)  # Upper arms
    fill_sym_box(grid, 6, 8, 11, 15, 17, 22, 1)  # Forearms
    fill_sym_box(grid, 8, 8, 12, 14, 18, 21, 3)  # Cream forearm trim
    fill_sym_box(grid, 6, 8, 12, 15, 16, 17, 4)  # Dark umber paw-gauntlets!
    # Forward swept twin speed-claws on BOTH gauntlets!
    fill_sym_box(grid, 8, 8, 15, 19, 17, 18, 5)
    fill_sym_box(grid, 8, 8, 18, 20, 17, 17, 6)  # Gold claw tips!

    # --- 4. KEEN WEASEL-MASK SCOUT HEAD & ALERT EARS (Z: 34..45) ---
    fill_sym_box(grid, 0, 1, 11, 14, 34, 35, 5)  # Neck
    fill_sym_box(grid, 0, 2, 10, 15, 35, 40, 1)  # Cinnamon helmet
    fill_sym_box(grid, 0, 2, 14, 16, 35, 36, 3)  # Cream chin/jaw guard
    fill_sym_box(grid, 0, 2, 14, 16, 37, 38, 4)  # Dark umber weasel bandit-mask visor!
    fill_sym_box(grid, 1, 2, 16, 16, 37, 38, 8)  # Bright glowing leaf-green eyes!
    fill_sym_box(grid, 0, 0, 16, 16, 37, 38, 4)  # Dark nose bridge
    fill_sym_box(grid, 0, 2, 11, 15, 40, 41, 2)  # Chestnut helmet crown
    fill_sym_box(grid, 0, 0, 15, 16, 39, 41, 6)  # Gold forehead speed-crest
    # Alert Swept Rounded Weasel Sensor-Ears (Z: 40..44)
    fill_sym_box(grid, 2, 3, 11, 13, 40, 43, 1)
    fill_sym_box(grid, 3, 3, 11, 12, 42, 44, 4)  # Dark ear tips
    fill_sym_box(grid, 2, 2, 13, 13, 41, 42, 3)  # Cream inner ears

    # Keep slender weasel solid inside so voxel count sits cleanly above 1,200
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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=46, pitch_a=20, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "itachi_a.vox")
    v_b = export_vox(model_b, "itachi_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: ITACHI (WEASEL) -> AGILE SCOUT ROBOT",
        "1. ITACHI (JAPANESE WEASEL)",
        "2. ITACHI SCOUT ROBOT",
        "preview_itachi.png",
        yaw_a=46, pitch_a=20, yaw_b=28, pitch_b=18,
    )
    print(f"itachi: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
