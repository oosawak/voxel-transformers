import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Tora (Tiger) -> Gallant & Dignified Striped Maid Robot!
# Tiger ears, bold black stripes on vivid amber-gold, long striped tail, crisp white apron & headdress!
PALETTE = {
    1: (242, 152, 34, 255),   # Vivid Golden-Orange Tiger Fur & Hair
    2: (206, 104, 18, 255),   # Deep Amber-Orange Shading
    3: (28, 28, 34, 255),     # Bold Jet-Black Tiger Stripes & Maid Dress
    4: (248, 246, 240, 255),  # Crisp Snow-White Tiger Belly, Apron & Headdress
    5: (208, 38, 44, 255),    # Gallant Crimson Neck Ribbon & Sash Trim
    6: (246, 206, 56, 255),   # Radiant Gold Trim & Collar Clasp
    7: (252, 224, 204, 255),  # Warm Porcelain Faceplate
    8: (68, 72, 84, 255),     # Dark Iron Boot Trim & Joints
    9: (255, 226, 62, 255),   # Sharp Glowing Amber-Gold Eyes
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
# FORM A: TORA (GALLANT STRIPED TIGER) (22 x 46 x 22)
# ============================================================
def build_a():
    grid = np.zeros((22, 46, 22), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 10.5

    # Lithe striped tiger body (Y: 11..32, Z: 6..16)
    for y in range(11, 33):
        rx = 3.8 if 12 <= y <= 16 else (3.3 if 17 <= y <= 21 else (4.2 if 22 <= y <= 29 else 3.4))
        zb = 7 if y <= 21 else (6 if y <= 28 else 8)
        zt = 15 if y <= 21 else 16
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                if (dx / rx) ** 2 + ((z - zc) / rz) ** 2 <= 1.0:
                    if z <= zb + 1 and dx <= rx * 0.7:
                        col = 4  # Crisp white belly
                    elif y in (13, 17, 21, 25, 29) and z >= zb + 2:
                        col = 3  # Bold black tiger stripes!
                    elif z >= zt - 1 and dx <= 1.4:
                        col = 2
                    else:
                        col = 1
                    grid[x, y, z] = col

    # White chest bib & crimson maid-ribbon collar
    fill_sym_box(grid, 0, 2, 29, 33, 7, 13, 4)
    fill_sym_box(grid, 0, 3, 29, 32, 11, 16, 5)   # Crimson ribbon collar!
    fill_sym_box(grid, 0, 1, 32, 33, 10, 11, 6)   # Gold brooch!

    # Four muscular striped legs grounded at z=0
    for ly, fy in [(13, 14), (27, 29)]:
        fill_sym_box(grid, 2, 3, ly - 1, ly + 1, 2, 9, 1)
        fill_sym_box(grid, 2, 3, ly - 1, ly + 1, 4, 4, 3)  # Leg stripe
        fill_sym_box(grid, 2, 3, ly - 1, ly + 1, 7, 7, 3)
        fill_sym_box(grid, 2, 3, fy - 1, fy + 2, 0, 1, 4)  # White tiger paws!

    # Proud Tiger Head, Rounded Ears & Amber Eyes (Y: 32..43, Z: 10..20)
    fill_sphere_local(grid, cx, 35.5, 14.5, 3.8, 3.8, 3.6, 1)
    fill_sym_box(grid, 0, 2, 38, 42, 12, 14, 4)   # White muzzle
    fill_sym_box(grid, 0, 1, 38, 42, 14, 15, 1)   # Orange nose bridge
    fill_sym_box(grid, 0, 1, 42, 43, 14, 15, 5)   # Nose
    fill_sym_box(grid, 0, 1, 38, 41, 11, 11, 4)   # Chin
    fill_sym_box(grid, 0, 2, 35, 39, 17, 18, 3)   # Forehead "王" stripes
    fill_sym_box(grid, 2, 3, 38, 39, 15, 16, 3)
    fill_sym_box(grid, 2, 3, 39, 39, 15, 16, 9)   # Glowing amber eyes!
    fill_sym_box(grid, 3, 4, 33, 35, 17, 19, 1)   # Rounded tiger ears
    fill_sym_box(grid, 3, 4, 33, 33, 18, 19, 3)   # Black ear backs

    # Long expressive striped tiger tail (Y: 2..12, Z: 9..19)
    tail_pts = [
        (cx,       11.0, 13.0, 1),
        (cx + 0.5,  8.5, 11.5, 3),
        (cx + 1.0,  6.0, 11.0, 1),
        (cx + 1.4,  3.8, 12.2, 3),
        (cx + 1.2,  2.5, 15.0, 1),
        (cx + 0.8,  2.8, 17.8, 3),
    ]
    for i in range(len(tail_pts) - 1):
        p0, p1 = tail_pts[i][:3], tail_pts[i + 1][:3]
        draw_6conn_line(grid, p0, p1, tail_pts[i][3], pad=(0, 0, 0))
        fill_sphere_local(grid, p1[0], p1[1], p1[2], 1.1, 1.1, 1.1, tail_pts[i + 1][3])

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: TORA GALLANT STRIPED MAID ROBOT (38 x 24 x 46)
# ============================================================
def build_b():
    grid = np.zeros((38, 24, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18
    cx_r = X // 2      # 19

    # --- 1. GALLANT HEEL-BOOTS & TIGER-STRIPED OVER-KNEE STOCKINGS (Z: 0..12) ---
    fill_sym_box(grid, 2, 4, 10, 16, 0, 2, 3)     # Sleek black boots
    fill_sym_box(grid, 2, 4, 15, 17, 0, 1, 3)
    fill_sym_box(grid, 2, 4, 11, 15, 3, 11, 1)    # Vivid golden-orange tiger stockings!
    for sz in (5, 8, 10):
        fill_sym_box(grid, 2, 4, 11, 15, sz, sz, 3)  # Bold black tiger stripes on stockings!
    fill_sym_box(grid, 2, 4, 11, 15, 3, 3, 6)     # Gold boot cuff

    # --- 2. DIGNIFIED TIGER-STRIPED MAID SKIRT + CRISP WHITE APRON & BACK BOW (Z: 10..22) ---
    for z in range(10, 23):
        r_x = 8 - (z - 10) // 3
        r_y = 5 - (z - 10) // 4
        y0, y1 = 12 - r_y, 13 + r_y
        if z == 10:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 4)  # Crisp white lace hem!
        else:
            # Gallant black skirt with vivid golden-orange tiger stripe panels on sides!
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 3)
            if z in (12, 13, 16, 17, 20):
                fill_sym_box(grid, max(3, r_x - 2), r_x, y0 + 1, y1 - 1, z, z, 1)
            # Crisp WHITE APRON covering front of skirt!
            ap_w = max(2, r_x - 3)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 4)
            if z == 11:
                fill_sym_box(grid, 0, ap_w + 1, y1, y1, z, z, 4)
    # Waist sash & crisp white back bow
    fill_sym_box(grid, 0, 4, 9, 16, 22, 23, 4)
    fill_sym_box(grid, 2, 5, 7, 9, 20, 23, 4)
    fill_sym_box(grid, 0, 1, 7, 8, 21, 22, 5)     # Crimson center bow knot
    fill_sym_box(grid, 1, 2, 7, 8, 15, 19, 4)

    # LONG STRIPED TIGER TAIL arching proudly behind the maid skirt!
    tail_r = [
        (cx_r,     8, 18, 1),
        (cx_r + 1, 6, 16, 3),
        (cx_r + 3, 4, 15, 1),
        (cx_r + 5, 3, 16, 3),
        (cx_r + 6, 3, 19, 1),
        (cx_r + 5, 4, 22, 3),
    ]
    for i in range(len(tail_r) - 1):
        draw_6conn_line(grid, tail_r[i][:3], tail_r[i + 1][:3], tail_r[i][3])
        fill_sphere_local(grid, tail_r[i + 1][0], tail_r[i + 1][1], tail_r[i + 1][2], 0.9, 0.9, 0.9, tail_r[i + 1][3])

    # --- 3. GALLANT MAID BODICE, WHITE APRON BIB & CRIMSON RIBBON (Z: 23..33) ---
    fill_sym_box(grid, 0, 4, 10, 15, 23, 32, 3)   # Sharp black bodice
    fill_sym_box(grid, 0, 2, 15, 16, 23, 30, 4)   # Crisp white apron bib!
    fill_sym_box(grid, 2, 3, 14, 16, 29, 32, 4)   # Frilly white straps
    fill_sym_box(grid, 2, 3, 9, 10, 24, 32, 4)    # Rear straps
    fill_sym_box(grid, 0, 3, 11, 15, 32, 33, 4)   # Crisp white collar
    fill_sym_box(grid, 0, 2, 15, 17, 30, 32, 5)   # Bold crimson neck ribbon!
    fill_sym_box(grid, 0, 0, 17, 17, 31, 31, 6)   # Gold brooch

    # --- 4. PUFF SLEEVES & GALLANT POSE ARMS (Z: 16..33) ---
    fill_sym_box(grid, 5, 8, 11, 14, 28, 32, 3)   # Black puff sleeves with gold/tiger trim
    fill_sym_box(grid, 7, 8, 12, 13, 29, 31, 1)
    fill_sym_box(grid, 5, 8, 11, 14, 27, 27, 4)   # White lace sleeve hem
    # Left arm (-X): Poised firmly on hip/side
    fill_box(grid, cx_l - 8, cx_l - 6, 11, 14, 20, 26, 3)
    fill_box(grid, cx_l - 8, cx_l - 6, 11, 14, 19, 19, 4)  # White cuff
    fill_box(grid, cx_l - 7, cx_l - 6, 12, 14, 17, 18, 7)
    # Right arm (+X): Holding an upright ornate brass-and-white broom/staff like a samurai halberd!
    fill_box(grid, cx_r + 6, cx_r + 8, 11, 15, 21, 26, 3)
    fill_box(grid, cx_r + 7, cx_r + 9, 14, 17, 20, 22, 4)  # White cuff
    fill_box(grid, cx_r + 8, cx_r + 9, 16, 18, 20, 21, 7)  # Hand
    fill_box(grid, cx_r + 10, cx_r + 10, 17, 18, 4, 34, 2) # Tall upright broom handle!
    fill_box(grid, cx_r + 10, cx_r + 10, 17, 18, 34, 35, 6)# Gold finial
    fill_box(grid, cx_r + 9, cx_r + 11, 16, 19, 1, 5, 1)   # Broom bristles
    fill_box(grid, cx_r + 9, cx_r + 11, 16, 19, 5, 5, 5)   # Crimson ribbon wrap

    # --- 5. DIGNIFIED HEAD, TIGER-STRIPED HAIR, FRILLY HEADDRESS & TIGER EARS! (Z: 33..45) ---
    fill_sym_box(grid, 0, 1, 12, 14, 33, 34, 7)
    fill_sym_box(grid, 0, 3, 10, 15, 34, 41, 1)   # Vivid golden-orange hair!
    fill_sym_box(grid, 0, 3, 9, 10, 27, 39, 1)    # Flowing back hair
    fill_sym_box(grid, 2, 3, 9, 10, 31, 31, 3)    # Black tiger-stripe hair highlights!
    fill_sym_box(grid, 2, 3, 9, 10, 35, 35, 3)
    # Gallant Faceplate
    fill_sym_box(grid, 0, 2, 15, 16, 34, 39, 7)
    fill_sym_box(grid, 1, 2, 16, 16, 36, 37, 9)   # Sharp glowing amber eyes!
    fill_sym_box(grid, 0, 0, 16, 16, 36, 37, 7)
    fill_sym_box(grid, 0, 2, 15, 16, 39, 40, 1)   # Bangs
    fill_sym_box(grid, 2, 2, 16, 16, 39, 40, 3)   # Tiger-stripe bang accent

    # FRILLY WHITE MAID HEADDRESS (Z: 40..43)
    fill_sym_box(grid, 0, 4, 13, 15, 41, 42, 4)
    fill_sym_box(grid, 0, 3, 14, 15, 42, 43, 4)
    fill_sym_box(grid, 3, 4, 14, 15, 41, 41, 5)   # Crimson side bows

    # ROUNDED TIGER EARS rising cleanly beside the maid headdress! (Z: 41..45)
    fill_sym_box(grid, 3, 5, 11, 13, 42, 44, 1)
    fill_sym_box(grid, 4, 5, 11, 11, 43, 44, 3)   # Black back of tiger ears
    fill_sym_box(grid, 4, 4, 13, 13, 43, 43, 4)   # White inner ear tuft

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=44, pitch_a=20, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "tora_a.vox")
    v_b = export_vox(model_b, "tora_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #03: TORA (TIGER) -> GALLANT MAID ROBOT",
        "1. TORA (TIGER)",
        "2. TORA MAID ROBOT",
        "preview_tora.png",
        yaw_a=44, pitch_a=20, yaw_b=28, pitch_b=18,
    )
    print(f"tora: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
