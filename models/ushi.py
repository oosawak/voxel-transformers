import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Ushi (Holstein Cow) -> Gentle Tall & Plump Maid Robot!
# Cow ears & curved horns, golden cowbell on crimson ribbon, classic black-and-white Holstein spots!
PALETTE = {
    1: (246, 246, 248, 255),  # Crisp Milk-White Cow Coat, Apron & Headdress
    2: (34, 36, 44, 255),     # Glossy Jet-Black Holstein Spots, Hair & Dress
    3: (72, 76, 88, 255),     # Soft Charcoal Shading & Hooves
    4: (238, 214, 152, 255),  # Warm Ivory-Cream Curved Cow Horns
    5: (244, 174, 184, 255),  # Gentle Pink Cow Muzzle & Inner Ears
    6: (214, 46, 54, 255),    # Bright Crimson Cow-Collar & Maid Neck Ribbon
    7: (246, 202, 52, 255),   # Radiant Golden Cowbell (Suzu) & Trim
    8: (252, 224, 204, 255),  # Warm Porcelain Faceplate
    9: (76, 178, 242, 255),   # Gentle Sky-Blue Glowing Eyes
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


def fill_sphere_local(grid, cx, cy, cz, rx, ry, rz, col):
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
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2 <= 1.0:
                    grid[x, y, z] = col


def draw_6conn_line(grid, p0, p1, col, pad=(0, 0, 0), only_empty=False):
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


# ============================================================
# FORM A: USHI (GENTLE LARGE HOLSTEIN COW) (24 x 42 x 24)
# ============================================================
def build_a():
    grid = np.zeros((24, 42, 24), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 11.5

    # Big gentle barrel-chested Holstein cow body (Y: 8..29, Z: 7..19)
    def cow_spot(x, y, z):
        # Asymmetric classic Holstein black cow spots!
        if ((x - 15) ** 2 + (y - 18) ** 2 + (z - 15) ** 2) <= 22:
            return 2
        if ((x - 8) ** 2 + (y - 12) ** 2 + (z - 14) ** 2) <= 20:
            return 2
        if ((x - 9) ** 2 + (y - 24) ** 2 + (z - 13) ** 2) <= 18:
            return 2
        return 1

    for y in range(8, 30):
        rx = 5.4 if 11 <= y <= 26 else (4.2 if y in (9, 10, 27, 28) else 3.2)
        zb = 7 if 11 <= y <= 26 else 8
        zt = 18 if y <= 25 else 19
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                if (dx / rx) ** 2 + ((z - zc) / rz) ** 2 <= 1.0:
                    grid[x, y, z] = cow_spot(x, y, z)

    # Four sturdy grounded cow legs with dark hooves (Z: 0..9)
    for ly in (11, 25):
        fill_sym_box(grid, 3, 4, ly - 1, ly + 1, 2, 9, 1)
        fill_sym_box(grid, 3, 4, ly - 1, ly + 1, 0, 1, 3)  # Cloven dark hooves
    # Spot on front right leg
    fill_box(grid, 15, 16, 24, 26, 4, 6, 2)

    # Crimson Collar Ribbon & Big Radiant Golden Cowbell (鈴つきのリボン!) (Y: 28..33)
    fill_sym_box(grid, 0, 4, 28, 31, 10, 17, 6)
    fill_sym_box(grid, 0, 1, 31, 33, 8, 11, 7)    # Hanging golden cowbell!
    fill_sym_box(grid, 0, 0, 32, 32, 8, 8, 3)

    # Gentle Wide Cow Head, Pink Muzzle, Side Ears & Curved Horns (Y: 30..40, Z: 12..23)
    fill_sym_box(grid, 0, 3, 30, 36, 13, 20, 1)
    fill_box(grid, 12, 15, 31, 36, 16, 20, 2)     # Cute black eye-patch spot!
    fill_sym_box(grid, 0, 3, 36, 40, 12, 16, 5)   # Big soft pink cow muzzle!
    fill_sym_box(grid, 2, 2, 40, 40, 14, 15, 3)   # Nostrils
    # Gentle sky-blue eyes
    fill_sym_box(grid, 3, 3, 34, 36, 17, 18, 2)
    fill_sym_box(grid, 3, 3, 35, 36, 17, 18, 9)
    # Sideways Cow Ears (牛の耳)
    fill_sym_box(grid, 4, 6, 32, 33, 18, 19, 2)
    fill_sym_box(grid, 5, 6, 33, 33, 18, 18, 5)   # Pink inner ear
    # Curved Ivory Cow Horns (牛の角)
    draw_6conn_line(grid, (15, 33, 20), (17, 34, 23), 4)
    draw_6conn_line(grid, (8,  33, 20), (6,  34, 23), 4)

    # Hanging Cow Tail with fluffy black tuft (Y: 4..9, Z: 6..15)
    draw_6conn_line(grid, (11, 8, 15), (11, 5, 8), 1)
    fill_sphere_local(grid, 11.5, 5.0, 6.5, 1.5, 1.5, 1.8, 2)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: USHI GENTLE TALL MAID ROBOT (42 x 26 x 48)
# ============================================================
def build_b():
    grid = np.zeros((42, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 20
    cx_r = X // 2      # 21

    # --- 1. STURDY MARY-JANE HOOF-SHOES & HOLSTEIN-SPOTTED STOCKINGS (Z: 0..12) ---
    fill_sym_box(grid, 3, 5, 10, 16, 0, 2, 3)     # Sturdy dark shoes
    fill_sym_box(grid, 3, 5, 15, 17, 0, 1, 2)     # Rounded toes
    fill_sym_box(grid, 3, 5, 11, 15, 3, 11, 1)    # Crisp white stockings
    # Holstein cow spots on stockings!
    fill_box(grid, cx_r + 3, cx_r + 5, 13, 15, 5, 7, 2)
    fill_box(grid, cx_l - 5, cx_l - 3, 13, 15, 8, 10, 2)
    fill_sym_box(grid, 3, 5, 11, 15, 3, 3, 6)     # Crimson shoe strap

    # --- 2. VOLUMINOUS LONG HOLSTEIN MAID SKIRT + WIDE WHITE APRON & BACK BOW (Z: 10..23) ---
    for z in range(10, 24):
        r_x = 9 - (z - 10) // 3
        r_y = 6 - (z - 10) // 4
        y0, y1 = 13 - r_y, 14 + r_y
        if z == 10:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 1)  # Wide white petticoat frill hem!
        else:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 2)  # Classic black maid skirt!
            # Bold white Holstein cow-spots wrapping sides of black skirt!
            if 13 <= z <= 17:
                fill_box(grid, cx_r + r_x - 1, cx_r + r_x, 12, 15, z, z, 1)
            if 16 <= z <= 20:
                fill_box(grid, cx_l - r_x, cx_l - r_x + 1, 11, 14, z, z, 1)
            # Crisp WHITE APRON covering front of skirt!
            ap_w = max(3, r_x - 3)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 1)
            if z == 11:
                fill_sym_box(grid, 0, ap_w + 1, y1, y1, z, z, 1)
    # Waist sash & big gentle white maid back-bow
    fill_sym_box(grid, 0, 5, 10, 17, 23, 24, 1)
    fill_sym_box(grid, 2, 5, 8, 10, 21, 24, 1)    # Back bow loops
    fill_sym_box(grid, 0, 1, 8, 9, 22, 23, 6)     # Crimson center knot
    fill_sym_box(grid, 1, 2, 8, 9, 16, 20, 1)     # Hanging bow tails

    # Cute Cow Tail with black tuft peeking behind the skirt!
    draw_6conn_line(grid, (cx_r, 9, 18), (cx_r + 3, 5, 12), 1)
    fill_sphere_local(grid, cx_r + 3.5, 4.5, 11.0, 1.4, 1.4, 1.6, 2)

    # --- 3. GENEROUS MAID BODICE, WHITE APRON BIB & BELL-BEARING CRIMSON RIBBON! (Z: 24..34) ---
    fill_sym_box(grid, 0, 5, 10, 16, 24, 33, 2)   # Full black bodice
    fill_sym_box(grid, 0, 3, 16, 17, 24, 31, 1)   # Wide crisp white apron bib!
    fill_sym_box(grid, 3, 4, 15, 17, 30, 33, 1)   # Frilly white apron straps
    fill_sym_box(grid, 3, 4, 9, 10, 25, 33, 1)    # Rear apron straps
    fill_sym_box(grid, 0, 4, 11, 16, 33, 34, 1)   # White maid collar
    # ICONIC CRIMSON NECK RIBBON + BIG RADIANT GOLDEN COWBELL! (鈴つきのリボン!)
    fill_sym_box(grid, 0, 3, 16, 18, 32, 33, 6)   # Wide crimson ribbon bow!
    fill_sym_box(grid, 0, 1, 18, 19, 30, 32, 7)   # Big gleaming golden cowbell!
    fill_sym_box(grid, 0, 0, 19, 19, 30, 30, 3)

    # --- 4. BIG PUFF SLEEVES & RELAXED ARMS HOLDING MILK PITCHER (Z: 17..34) ---
    fill_sym_box(grid, 6, 9, 11, 15, 29, 33, 2)   # Generous black puff sleeves
    fill_sym_box(grid, 6, 9, 11, 15, 28, 28, 1)   # White lace ruffle
    # Left arm (-X)
    fill_box(grid, cx_l - 8, cx_l - 6, 12, 15, 21, 27, 2)
    fill_box(grid, cx_l - 8, cx_l - 6, 12, 15, 20, 20, 1)  # White cuff
    fill_box(grid, cx_l - 8, cx_l - 6, 13, 15, 18, 19, 8)  # Hand
    # Right arm (+X): Relaxed pose holding a cute white milk pitcher!
    fill_box(grid, cx_r + 6, cx_r + 8, 12, 16, 22, 27, 2)
    fill_box(grid, cx_r + 7, cx_r + 9, 15, 18, 21, 23, 1)  # White cuff
    fill_box(grid, cx_r + 8, cx_r + 9, 17, 19, 21, 22, 8)  # Hand
    fill_box(grid, cx_r + 9, cx_r + 11, 18, 20, 21, 25, 1) # Fresh milk pitcher!
    fill_box(grid, cx_r + 9, cx_r + 11, 18, 20, 25, 25, 7) # Gold pitcher rim

    # --- 5. HEAD, BLACK-AND-WHITE HAIR, FRILLY HEADDRESS, COW EARS & CURVED HORNS! (Z: 34..47) ---
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 8)   # Neck
    fill_sym_box(grid, 0, 4, 10, 16, 35, 42, 2)   # Glossy black hair with white streak!
    fill_box(grid, cx_r + 2, cx_r + 4, 12, 16, 36, 41, 1)  # White Holstein hair highlight!
    fill_sym_box(grid, 0, 4, 9, 10, 30, 40, 2)    # Long gentle back hair
    # Gentle Maid Faceplate
    fill_sym_box(grid, 0, 2, 16, 17, 35, 40, 8)   # Porcelain face
    fill_sym_box(grid, 1, 2, 17, 17, 37, 38, 9)   # Gentle sky-blue eyes!
    fill_sym_box(grid, 0, 0, 17, 17, 37, 38, 8)
    fill_sym_box(grid, 2, 2, 17, 17, 36, 36, 5)   # Soft pink blush
    fill_sym_box(grid, 0, 3, 16, 17, 40, 41, 2)   # Bangs

    # FRILLY WHITE MAID HEADDRESS (Z: 41..44)
    fill_sym_box(grid, 0, 4, 14, 16, 42, 43, 1)
    fill_sym_box(grid, 0, 3, 15, 16, 43, 44, 1)
    fill_sym_box(grid, 3, 4, 15, 16, 42, 42, 6)   # Crimson side bows

    # SIDEWAYS COW EARS & CURVED IVORY HORNS! (Z: 40..47)
    fill_sym_box(grid, 5, 7, 12, 14, 40, 41, 2)   # Cow ears
    fill_sym_box(grid, 6, 7, 14, 14, 40, 40, 5)   # Pink inner ears
    draw_6conn_line(grid, (cx_r + 3, 13, 43), (cx_r + 6, 14, 46), 4)
    draw_6conn_line(grid, (cx_r + 6, 14, 46), (cx_r + 5, 14, 47), 4)
    draw_6conn_line(grid, (cx_l - 3, 13, 43), (cx_l - 6, 14, 46), 4)
    draw_6conn_line(grid, (cx_l - 6, 14, 46), (cx_l - 5, 14, 47), 4)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=42, pitch_a=22, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "ushi_a.vox")
    v_b = export_vox(model_b, "ushi_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #02: USHI (COW) -> GENTLE MAID ROBOT",
        "1. USHI (HOLSTEIN COW)",
        "2. USHI MAID ROBOT",
        "preview_ushi.png",
        yaw_a=42, pitch_a=22, yaw_b=28, pitch_b=18,
    )
    print(f"ushi: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
