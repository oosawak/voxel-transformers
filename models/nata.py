import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Nezha / Nata (哪吒) -> Wind-Fire Wheel Speedster Robot!
# Universe Ring (乾坤圏), Red Armillary Sash (混天綾), Wind-Fire Wheels (風火二輪 -> Robot legs become wheels!)
PALETTE = {
    1: (218, 34, 46, 255),    # Blazing Lotus-Crimson Armillary Sash (混天綾) & Tunic
    2: (146, 20, 34, 255),    # Deep Ruby Sash Shading & Skirt
    3: (246, 200, 44, 255),   # Radiant Golden Universe Ring (乾坤圏) & Wheel Hubs
    4: (246, 134, 34, 255),   # Wind-Fire Wheel Flame Orange (風火二輪!)
    5: (244, 246, 252, 255),  # Pure Lotus-White Armor & Trousers
    6: (34, 36, 50, 255),     # Glossy Jet-Black Twin-Bun Hair (お団子) & Tires
    7: (252, 220, 196, 255),  # Youthful Warrior Face
    8: (206, 218, 232, 255),  # Honed Silver Fire-Tipped Spear Blade
    9: (106, 242, 255, 255),  # Luminous Lotus-Cyan Eyes & Wind-Jet Core!
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(int(x0), int(x1))), min(X - 1, max(int(x0), int(x1)))
    y0, y1 = max(0, min(int(y0), int(y1))), min(Y - 1, max(int(y0), int(y1)))
    z0, z1 = max(0, min(int(z0), int(z1))), min(Z - 1, max(int(z0), int(z1)))
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


def draw_6conn_line(grid, p0, p1, col, pad=(0, 0, 0)):
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


def draw_fire_wheel_yz(grid, x0, x1, cy, cz, radius, rim_col=4, hub_col=3, tire_col=6):
    """Draw a thick 6-connected Wind-Fire Wheel (風火二輪) in Y-Z plane."""
    X, Y, Z = grid.shape
    for x in range(max(0, x0), min(X, x1 + 1)):
        for dy in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                d = np.sqrt(dy * dy + dz * dz)
                y, z = cy + dy, cz + dz
                if 0 <= y < Y and 0 <= z < Z:
                    if radius - 1.2 <= d <= radius + 0.35:
                        grid[x, y, z] = rim_col if (dy + dz) % 2 == 0 else tire_col
                    elif d <= 1.5:
                        grid[x, y, z] = hub_col
                    elif d < radius - 1.2 and (dy == 0 or dz == 0):
                        grid[x, y, z] = hub_col


def hollow_interior_26(grid, z_min, z_max):
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


def draw_universe_ring_xy(grid, cx, cy, cz, r=3):
    """Draw Nata's iconic Golden Universe Ring (乾坤圏) held proudly by his arm."""
    X, Y, Z = grid.shape
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d = np.sqrt(dx * dx + dz * dz)
            if r - 1.15 <= d <= r + 0.35:
                x, z = cx + dx, cz + dz
                if 0 <= x < X and 0 <= cy < Y and 0 <= z < Z:
                    grid[x, cy, z] = 3


# ============================================================
# FORM A: NATA / NEZHA ON WIND-FIRE WHEELS WITH UNIVERSE RING & RED SASH (40 x 26 x 46)
# ============================================================
def build_a():
    grid = np.zeros((40, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 19
    cx_r = X // 2      # 20

    # --- 1. TWIN BLAZING WIND-FIRE WHEELS UNDER FEET (風火二輪!) (Z: 0..6) ---
    draw_fire_wheel_yz(grid, cx_r + 2, cx_r + 4, cy=13, cz=3, radius=3, rim_col=4, hub_col=3, tire_col=1)
    draw_fire_wheel_yz(grid, cx_l - 4, cx_l - 2, cy=13, cz=3, radius=3, rim_col=4, hub_col=3, tire_col=1)
    # Flame trails flickering behind both Wind-Fire Wheels!
    fill_sym_box(grid, 2, 4, 8, 10, 2, 4, 4)
    fill_sym_box(grid, 3, 3, 6, 8, 3, 4, 3)

    # --- 2. YOUTHFUL LOTUS WARRIOR BODY (Z: 6..30) ---
    fill_sym_box(grid, 2, 4, 11, 15, 6, 8, 6)     # Martial shoes planted solidly on wheels!
    fill_sym_box(grid, 2, 4, 11, 15, 9, 16, 5)    # White martial pants
    fill_sym_box(grid, 0, 5, 10, 16, 16, 20, 1)   # Scarlet lotus-petal skirt
    fill_sym_box(grid, 0, 5, 16, 16, 16, 17, 3)   # Gold skirt hem
    fill_sym_box(grid, 0, 4, 10, 16, 20, 29, 5)   # White tunic
    fill_sym_box(grid, 0, 3, 15, 17, 21, 28, 1)   # Iconic Red Lotus Apron (肚兜!)
    fill_sym_box(grid, 0, 2, 17, 17, 23, 26, 3)   # Golden lotus embroidery!
    fill_sym_box(grid, 0, 4, 10, 16, 28, 29, 3)   # Golden collar

    # --- 3. FLOWING RED ARMILLARY SASH (混天綾) ARCHING GRACEFULLY BEHIND SHOULDERS! ---
    sash_pts = [
        (cx_l - 6, 13, 23), (cx_l - 9, 10, 27), (cx_l - 9, 8, 35),
        (cx_l - 4, 7, 40), (cx_r + 4, 7, 40),
        (cx_r + 9, 8, 35), (cx_r + 9, 10, 27), (cx_r + 6, 13, 23)
    ]
    for i in range(len(sash_pts) - 1):
        draw_6conn_line(grid, sash_pts[i], sash_pts[i + 1], 1, pad=(0, 0, 1))
    # Trailing sash tails hanging down from both arms
    draw_6conn_line(grid, (cx_l - 9, 10, 27), (cx_l - 11, 9, 14), 1)
    draw_6conn_line(grid, (cx_r + 9, 10, 27), (cx_r + 11, 9, 14), 1)

    # --- 4. ARMS: GOLDEN UNIVERSE RING (乾坤圏) ON LEFT ARM + FIRE-TIPPED SPEAR ON RIGHT! ---
    fill_box(grid, cx_l - 7, cx_l - 5, 11, 15, 22, 28, 5)
    fill_box(grid, cx_l - 8, cx_l - 6, 14, 18, 20, 22, 7)   # Left arm holding Universe Ring!
    draw_universe_ring_xy(grid, cx_l - 10, 18, 22, r=3)     # GOLDEN UNIVERSE RING (乾坤圏!)
    fill_box(grid, cx_l - 8, cx_l - 7, 18, 18, 21, 22, 3)   # Connects solidly into hand!

    fill_box(grid, cx_r + 5, cx_r + 7, 11, 15, 22, 28, 5)
    fill_box(grid, cx_r + 6, cx_r + 9, 14, 17, 21, 23, 7)   # Right hand holding Fire-Tipped Spear
    fill_box(grid, cx_r + 9, cx_r + 9, 16, 16, 7, 36, 3)    # Golden spear shaft
    fill_box(grid, cx_r + 9, cx_r + 9, 16, 16, 37, 43, 8)   # Silver spearhead
    fill_box(grid, cx_r + 8, cx_r + 10, 16, 16, 36, 38, 4)  # Flame tassel!

    # --- 5. YOUTHFUL HEAD & ICONIC TWIN HAIR-BUNS (お団子ヘア!) (Z: 29..40) ---
    fill_sym_box(grid, 0, 2, 11, 16, 29, 35, 7)   # Youthful heroic face
    fill_sym_box(grid, 1, 2, 16, 16, 32, 33, 9)   # Bright determined eyes
    fill_sym_box(grid, 0, 3, 10, 16, 34, 37, 6)   # Glossy black hair
    fill_sym_box(grid, 0, 2, 16, 16, 35, 36, 1)   # Crimson headband
    # Twin Round Hair-Buns tied with Red Ribbons!
    fill_sym_box(grid, 3, 5, 11, 15, 36, 39, 6)
    fill_sym_box(grid, 3, 4, 11, 15, 36, 36, 1)   # Red hair-bun ribbons!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: NATA WIND-FIRE WHEEL ROBOT (脚が車輪になるロボ!) (48 x 28 x 48)
# ============================================================
def build_b():
    grid = np.zeros((48, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # --- 1. ICONIC WIND-FIRE WHEEL LEGS! (ロボでは脚が車輪になる!) (Z: 0..17) ---
    # Twin Giant Blazing Wind-Fire Wheels acting directly as the Robot's lower legs / roller-wheels!
    draw_fire_wheel_yz(grid, cx_r + 3, cx_r + 6, cy=14, cz=6, radius=6, rim_col=4, hub_col=3, tire_col=6)
    draw_fire_wheel_yz(grid, cx_l - 6, cx_l - 3, cy=14, cz=6, radius=6, rim_col=4, hub_col=3, tire_col=6)
    # Armored Wheel-Fork Struts & Blazing Flame-Exhaust Fins!
    fill_sym_box(grid, 2, 5, 12, 16, 6, 17, 5)    # White wheel-fork leg struts!
    fill_sym_box(grid, 3, 5, 16, 18, 12, 16, 1)   # Crimson wheel-fender knee shields!
    fill_sym_box(grid, 3, 4, 18, 18, 13, 15, 3)   # Gold knee crests
    fill_sym_box(grid, 3, 5, 6, 9, 5, 8, 4)       # Blazing flame exhaust behind wheel hubs!
    fill_sym_box(grid, 4, 5, 4, 6, 6, 8, 3)

    # --- 2. THIGHS & LOTUS-PETAL WAIST ARMOR (Z: 17..24) ---
    fill_sym_box(grid, 2, 4, 12, 16, 17, 20, 6)
    fill_sym_box(grid, 0, 5, 12, 16, 20, 23, 5)
    fill_sym_box(grid, 1, 5, 16, 18, 17, 22, 1)   # Lotus-petal red tassets
    fill_sym_box(grid, 1, 5, 18, 18, 17, 17, 3)   # Gold hem
    fill_sym_box(grid, 0, 1, 17, 19, 19, 23, 3)   # Gold waist emblem

    # --- 3. LOTUS-ARMOR CHEST & ARMORED RED ARMILLARY SASH HALO (混天綾!) (Z: 23..45) ---
    fill_sym_box(grid, 0, 4, 12, 16, 23, 25, 6)
    fill_sym_box(grid, 0, 6, 11, 18, 26, 33, 5)   # Pure lotus-white cuirass
    fill_sym_box(grid, 1, 5, 18, 19, 27, 32, 1)   # Crimson lotus breastplate (肚兜装甲!)
    fill_sym_box(grid, 0, 2, 19, 20, 28, 31, 3)   # Gold lotus frame
    fill_sym_box(grid, 0, 1, 20, 20, 29, 30, 9)   # Glowing wind-cyan core!
    # Rear Wind-Jet Pack + Armored Arching Red Armillary Ribbon Wings!
    fill_sym_box(grid, 0, 4, 8, 11, 26, 33, 1)
    sash_b = [
        (cx_l - 4, 9, 31), (cx_l - 12, 7, 34), (cx_l - 14, 6, 42),
        (cx_l - 7, 6, 46), (cx_r + 7, 6, 46),
        (cx_r + 14, 6, 42), (cx_r + 12, 7, 34), (cx_r + 4, 9, 31)
    ]
    for i in range(len(sash_b) - 1):
        draw_6conn_line(grid, sash_b[i], sash_b[i + 1], 1, pad=(0, 0, 1))
    # Flowing armored ribbon tips down sides
    draw_6conn_line(grid, (cx_l - 12, 7, 34), (cx_l - 15, 7, 20), 1)
    draw_6conn_line(grid, (cx_r + 12, 7, 34), (cx_r + 15, 7, 20), 1)

    # --- 4. PAULDRONS, UNIVERSE RING SHIELD & FIRE-TIPPED LANCE (Z: 15..46) ---
    fill_sym_box(grid, 6, 8, 13, 16, 29, 32, 6)
    fill_sym_box(grid, 7, 11, 11, 17, 28, 34, 1)  # Crimson lotus pauldrons
    fill_sym_box(grid, 8, 12, 12, 16, 33, 35, 3)  # Gold trim
    fill_sym_box(grid, 7, 9, 13, 16, 22, 28, 5)
    # Left Arm (-X): GIANT GOLDEN UNIVERSE RING (乾坤圏) mounted on forearm!
    fill_box(grid, cx_l - 11, cx_l - 7, 13, 17, 17, 22, 5)
    fill_box(grid, cx_l - 12, cx_l - 10, 15, 19, 18, 21, 3)
    draw_universe_ring_xy(grid, cx_l - 13, 19, 20, r=4)
    # Right Arm (+X): Holding Fire-Tipped Energy Spear!
    fill_box(grid, cx_r + 7, cx_r + 10, 13, 17, 18, 22, 5)
    fill_box(grid, cx_r + 9, cx_r + 13, 16, 20, 18, 20, 3)
    fill_box(grid, cx_r + 13, cx_r + 13, 19, 19, 4, 37, 3)
    fill_box(grid, cx_r + 13, cx_r + 13, 19, 19, 38, 46, 8)
    fill_box(grid, cx_r + 12, cx_r + 14, 19, 19, 36, 39, 4)

    # --- 5. LOTUS SPEEDSTER ROBOT HEAD WITH TWIN-BUN SENSOR PODS! (Z: 34..44) ---
    fill_sym_box(grid, 0, 1, 13, 16, 34, 35, 6)
    fill_sym_box(grid, 0, 2, 12, 18, 35, 41, 5)   # White lotus helm
    fill_sym_box(grid, 0, 2, 18, 19, 35, 36, 8)   # Silver chinplate
    fill_sym_box(grid, 0, 2, 18, 19, 37, 38, 6)   # Dark eye recess
    fill_sym_box(grid, 1, 2, 19, 19, 37, 38, 9)   # Glowing lotus-cyan eyes!
    fill_sym_box(grid, 0, 1, 18, 19, 40, 43, 3)   # Golden lotus V-crest!
    # Iconic Armored Twin Hair-Bun Sensor Pods!
    fill_sym_box(grid, 3, 6, 12, 16, 39, 43, 6)
    fill_sym_box(grid, 3, 4, 12, 16, 39, 40, 1)   # Crimson ribbon rings!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


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
    with open(filename, 'wb') as f:
        f.write(b'VOX ' + struct.pack('<I', 150) + main_chunk)
    return len(voxels)


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
    cx, cy, cz = (xs.min() + xs.max() + 1) / 2.0, (ys.min() + ys.max() + 1) / 2.0, (zs.min() + zs.max() + 1) / 2.0
    yaw, pitch = np.radians(yaw_deg), np.radians(pitch_deg)
    cos_y, sin_y, cos_p, sin_p = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)

    def project_unit(x, y, z):
        dx, dy, dz = x - cx, y - cy, z - cz
        rx = -dx * cos_y + dy * sin_y
        ry = dx * sin_y + dy * cos_y
        return rx, ry * sin_p - dz * cos_p, ry * cos_p + dz * sin_p

    corners = [(x, y, z) for x in (xs.min(), xs.max() + 1) for y in (ys.min(), ys.max() + 1) for z in (zs.min(), zs.max() + 1)]
    proj_c = [project_unit(x, y, z) for x, y, z in corners]
    min_rx, max_rx = min(p[0] for p in proj_c), max(p[0] for p in proj_c)
    min_sy, max_sy = min(p[1] for p in proj_c), max(p[1] for p in proj_c)
    if scale is None:
        scale = min((img_size[0] - 2 * margin) / max(1e-5, max_rx - min_rx),
                    (img_size[1] - 2 * margin) / max(1e-5, max_sy - min_sy), 9.5)
    ox = img_size[0] / 2.0 - ((min_rx + max_rx) / 2.0) * scale
    oy = img_size[1] / 2.0 - ((min_sy + max_sy) / 2.0) * scale

    def project(x, y, z):
        rx, sy, depth = project_unit(x, y, z)
        return (rx * scale + ox, sy * scale + oy), depth

    visible = []
    for x, y, z in zip(xs, ys, zs):
        x, y, z = int(x), int(y), int(z)
        if (0 < x < X - 1 and 0 < y < Y - 1 and 0 < z < Z - 1 and
                grid[x - 1, y, z] and grid[x + 1, y, z] and grid[x, y - 1, z] and
                grid[x, y + 1, z] and grid[x, y, z - 1] and grid[x, y, z + 1]):
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
    vx_dir, vy_dir, vz_dir = sin_y * cos_p, cos_y * cos_p, sin_p
    for _, x, y, z, c in visible:
        base_col = PALETTE[c]
        for verts, normal, light in faces:
            nx, ny, nz = normal
            nnx, nny, nnz = x + nx, y + ny, z + nz
            if 0 <= nnx < X and 0 <= nny < Y and 0 <= nnz < Z and grid[nnx, nny, nnz] > 0:
                continue
            if nx * vx_dir + ny * vy_dir + nz * vz_dir <= 1e-6:
                continue
            poly = [project(x + vx, y + vy, z + vz)[0] for vx, vy, vz in verts]
            fcol = shade_color(base_col, light)
            draw.polygon(poly, fill=fcol, outline=shade_color(fcol, 0.85))
    return img


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=28, pitch_a=18, yaw_b=28, pitch_b=18):
    canvas = Image.new("RGBA", (860, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, 860, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (860, gy)], fill=(28, 34, 48, 255), width=1)
    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate([(label_a, grid_a, v_a, yaw_a, pitch_a), (label_b, grid_b, v_b, yaw_b, pitch_b)]):
        bx, by, w, h = 24 + idx * 414, 48, 398, 468
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
            px0, py0 = bx + 14 + (pi - 1) * 20, by + 430
            draw.rectangle([px0, py0, px0 + 15, py0 + 15], fill=PALETTE[pi], outline=(70, 82, 105, 255))
    canvas.save(out_path)


if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    v_a = export_vox(model_a, "nata_a.vox")
    v_b = export_vox(model_b, "nata_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #10: NATA / NEZHA (FENGSHEN) -> WIND-FIRE WHEEL ROBOT",
        "1. NATA (CHARACTER)",
        "2. NATA ROBOT (WHEEL LEGS)",
        "preview_nata.png",
    )
    print(f"nata: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
