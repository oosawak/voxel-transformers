import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Uma (Chestnut Horse) -> Slender Long-Legged Equestrian Maid Robot!
# Horse ears, flowing dark mane, long flowing tail, tall slender legs, crisp white apron & headdress!
PALETTE = {
    1: (176, 98, 46, 255),    # Rich Chestnut-Bay Horse Coat & Hair (栗毛)
    2: (122, 62, 28, 255),    # Deep Chestnut Shading
    3: (48, 32, 24, 255),     # Dark Espresso Flowing Mane, Tail & Tall Boots
    4: (248, 246, 242, 255),  # Crisp White Blaze, Fetlocks, Apron & Headdress
    5: (28, 96, 68, 255),     # Classic Equestrian Hunter-Green Maid Dress!
    6: (212, 46, 48, 255),    # Equestrian Crimson Neck Ribbon & Saddle Trim
    7: (242, 198, 56, 255),   # Brass Stirrup-Gold Trim & Brooch
    8: (252, 226, 206, 255),  # Warm Porcelain Faceplate
    9: (82, 212, 134, 255),   # Bright Emerald-Green Eyes
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
# FORM A: UMA (GRACEFUL CHESTNUT HORSE WITH LONG LEGS & MANE) (20 x 44 x 34)
# ============================================================
def build_a():
    grid = np.zeros((20, 44, 34), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 9.5

    # Sleek Athletic Horse Barrel Body (Y: 11..30, Z: 13..22)
    for y in range(11, 31):
        rx = 4.0 if 13 <= y <= 28 else 3.0
        zb = 13 if 14 <= y <= 27 else 14
        zt = 22
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                if (dx / rx) ** 2 + ((z - zc) / rz) ** 2 <= 1.0:
                    grid[x, y, z] = 2 if z <= zb + 1 else 1

    # Hunter-Green Equestrian Saddle Blanket with White Lace & Gold Trim!
    fill_sym_box(grid, 0, 4, 16, 25, 20, 22, 5)
    fill_sym_box(grid, 4, 4, 16, 25, 18, 20, 5)
    fill_sym_box(grid, 4, 4, 16, 25, 17, 17, 4)   # White saddle lace trim!
    fill_sym_box(grid, 4, 4, 16, 25, 18, 18, 7)   # Gold border

    # FOUR LONG SLENDER HORSE LEGS WITH WHITE FETLOCKS & DARK HOOVES! (脚は細長く!) (Z: 0..15)
    leg_coords = [(13, 12), (27, 29)]
    for y_top, y_bot in leg_coords:
        for sign in (-1, 1):
            lx = int(round(cx + sign * 2.8))
            draw_6conn_line(grid, (lx, y_top, 14), (lx, y_bot, 2), 1, pad=(0, 1, 0))
            fill_box(grid, lx, lx, y_bot - 1, y_bot + 1, 2, 4, 4)  # Crisp white fetlock socks!
            fill_box(grid, lx, lx, y_bot - 1, y_bot + 1, 0, 1, 3)  # Dark hooves at z=0!

    # Graceful Arched Horse Neck & Flowing Dark Espresso Mane! (Y: 27..35, Z: 17..29)
    for step in range(10):
        ny = 27 + int(round(step * 0.7))
        nz = 19 + step
        fill_sphere_local(grid, cx, ny, nz, 2.3, 2.4, 2.2, 1)
        # Flowing dark espresso mane cascading down back of neck!
        fill_sym_box(grid, 0, 1, ny - 3, ny - 1, nz, nz + 1, 3)
    # Crimson Equestrian Ribbon Collar
    fill_sym_box(grid, 0, 2, 29, 32, 18, 20, 6)
    fill_sym_box(grid, 0, 1, 32, 33, 18, 19, 7)

    # Noble Horse Head with White Forehead Blaze & Pointed Horse Ears (Y: 32..42, Z: 22..33)
    fill_sym_box(grid, 0, 2, 32, 37, 25, 30, 1)
    fill_sym_box(grid, 0, 1, 37, 42, 23, 27, 1)   # Elongated horse muzzle
    fill_sym_box(grid, 0, 0, 35, 42, 27, 29, 4)   # Classic white horse blaze!
    fill_sym_box(grid, 2, 2, 35, 37, 27, 28, 3)
    fill_sym_box(grid, 2, 2, 36, 37, 27, 28, 9)   # Emerald eyes!
    # Perky Pointed Horse Ears (馬耳!)
    fill_sym_box(grid, 1, 2, 33, 34, 30, 33, 1)
    fill_sym_box(grid, 2, 2, 34, 34, 31, 32, 3)

    # LONG FLOWING DARK HORSE TAIL sweeping gracefully to near ground! (長い尻尾!) (Y: 4..12, Z: 4..20)
    tail_pts = [(cx, 11, 20), (cx, 8, 18), (cx, 6, 13), (cx, 5, 8), (cx, 6, 4)]
    for i in range(len(tail_pts) - 1):
        draw_6conn_line(grid, tail_pts[i], tail_pts[i + 1], 3, pad=(1, 1, 0))

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: UMA LONG-LEGGED EQUESTRIAN MAID ROBOT (38 x 26 x 52)
# Horse ears, flowing mane, long flowing ponytail/tail, slender long riding-boot legs!
# ============================================================
def build_b():
    grid = np.zeros((38, 26, 52), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18
    cx_r = X // 2      # 19

    # --- 1. TALL SLENDER LONG LEGS IN EQUESTRIAN RIDING BOOTS & WHITE STOCKINGS! (脚は細長く!) (Z: 0..17) ---
    fill_sym_box(grid, 2, 3, 10, 16, 0, 2, 3)     # Sleek dark riding boots
    fill_sym_box(grid, 2, 3, 15, 17, 0, 1, 3)
    fill_sym_box(grid, 2, 3, 11, 14, 3, 9, 3)     # Tall slender riding boots!
    fill_sym_box(grid, 2, 3, 11, 14, 9, 9, 7)     # Brass boot top trim
    fill_sym_box(grid, 2, 3, 11, 14, 10, 16, 4)   # Long slender white over-knee stockings!

    # --- 2. HUNTER-GREEN MAID SKIRT + CRISP WHITE APRON & LONG FLOWING HORSE TAIL! (Z: 15..27) ---
    for z in range(15, 28):
        r_x = 8 - (z - 15) // 3
        r_y = 5 - (z - 15) // 4
        y0, y1 = 13 - r_y, 14 + r_y
        if z == 15:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 4)  # Crisp white lace hem!
        else:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 5)  # Equestrian hunter-green skirt!
            ap_w = max(2, r_x - 2)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 4) # Crisp white apron!
            if z == 16:
                fill_sym_box(grid, 0, ap_w + 1, y1, y1, z, z, 4)
    # Waist sash & back bow
    fill_sym_box(grid, 0, 4, 10, 17, 27, 28, 4)
    fill_sym_box(grid, 2, 5, 8, 10, 25, 28, 4)
    fill_sym_box(grid, 0, 1, 8, 9, 26, 27, 6)     # Crimson knot

    # LONG FLOWING DARK HORSE TAIL cascading down the back of the skirt! (長い尻尾!)
    cx_f = (X - 1) / 2.0
    tail_b = [(cx_f, 9, 23), (cx_f, 6, 20), (cx_f, 4, 15), (cx_f, 3, 10), (cx_f, 4, 6)]
    for i in range(len(tail_b) - 1):
        draw_6conn_line(grid, tail_b[i], tail_b[i + 1], 3, pad=(1, 1, 0))

    # --- 3. SLENDER MAID BODICE, WHITE APRON BIB & CRIMSON RIBBON (Z: 28..38) ---
    fill_sym_box(grid, 0, 4, 11, 16, 28, 37, 5)   # Hunter-green bodice
    fill_sym_box(grid, 0, 2, 16, 17, 28, 35, 4)   # Crisp white apron bib!
    fill_sym_box(grid, 2, 3, 15, 17, 34, 37, 4)   # White ruffled straps
    fill_sym_box(grid, 2, 3, 10, 11, 29, 37, 4)   # Rear straps
    fill_sym_box(grid, 0, 3, 12, 16, 37, 38, 4)   # White collar
    fill_sym_box(grid, 0, 2, 16, 18, 35, 37, 6)   # Equestrian crimson neck ribbon!
    fill_sym_box(grid, 0, 0, 18, 18, 36, 36, 7)   # Gold horseshoe brooch!

    # --- 4. PUFF SLEEVES & POISED SLENDER ARMS (Z: 21..38) ---
    fill_sym_box(grid, 5, 7, 12, 15, 33, 37, 5)
    fill_sym_box(grid, 5, 7, 12, 15, 32, 32, 4)   # White ruffle
    fill_box(grid, cx_l - 7, cx_l - 6, 12, 15, 24, 31, 5)
    fill_box(grid, cx_l - 7, cx_l - 6, 12, 15, 23, 23, 4)  # White cuff
    fill_box(grid, cx_l - 7, cx_l - 6, 13, 15, 21, 22, 8)
    fill_box(grid, cx_r + 6, cx_r + 7, 12, 16, 25, 31, 5)
    fill_box(grid, cx_r + 6, cx_r + 8, 15, 18, 24, 26, 4)
    fill_box(grid, cx_r + 7, cx_r + 8, 17, 19, 24, 25, 8)

    # --- 5. HEAD, FLOWING CHESTNUT & ESPRESSO MANE-HAIR, HEADDRESS & POINTED HORSE EARS! (Z: 38..51) ---
    fill_sym_box(grid, 0, 1, 13, 15, 38, 39, 8)
    fill_sym_box(grid, 0, 3, 11, 16, 39, 46, 1)   # Chestnut hair
    # Flowing dark mane-ponytail cascading down back of head! (たてがみ!)
    fill_sym_box(grid, 0, 2, 8, 11, 32, 45, 3)
    fill_sym_box(grid, 0, 1, 7, 9, 29, 39, 3)
    fill_sym_box(grid, 3, 4, 13, 16, 34, 44, 1)   # Side hair
    # Noble Maid Faceplate
    fill_sym_box(grid, 0, 2, 16, 17, 39, 44, 8)
    fill_sym_box(grid, 1, 2, 17, 17, 41, 42, 9)   # Bright emerald eyes!
    fill_sym_box(grid, 0, 0, 17, 17, 41, 42, 8)
    fill_sym_box(grid, 0, 2, 16, 17, 44, 45, 1)   # Chestnut bangs
    fill_sym_box(grid, 0, 0, 17, 17, 44, 45, 4)   # White horse-blaze bang streak!

    # FRILLY WHITE MAID HEADDRESS (Z: 45..48)
    fill_sym_box(grid, 0, 4, 14, 16, 46, 47, 4)
    fill_sym_box(grid, 0, 3, 15, 16, 47, 48, 4)
    fill_sym_box(grid, 3, 4, 15, 16, 46, 46, 6)   # Crimson side bows

    # PERKY POINTED HORSE EARS (馬耳!) rising sharply above the headdress! (Z: 46..51)
    fill_sym_box(grid, 2, 3, 12, 14, 46, 49, 1)
    fill_sym_box(grid, 3, 3, 12, 13, 49, 51, 3)   # Dark ear tips!
    fill_sym_box(grid, 2, 2, 14, 14, 47, 49, 4)   # White inner ear tuft

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
    v_a = export_vox(model_a, "uma_a.vox")
    v_b = export_vox(model_b, "uma_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #07: UMA (HORSE) -> LONG-LEGGED MAID ROBOT",
        "1. UMA (CHESTNUT HORSE)",
        "2. UMA EQUESTRIAN MAID ROBOT",
        "preview_uma.png",
        yaw_a=44, pitch_a=20, yaw_b=28, pitch_b=18,
    )
    print(f"uma: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
