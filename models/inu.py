import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Inu (Faithful Shiba Inu Dog) -> Loyal Upright Maid Robot!
# Shiba ears, curled wagging tail, warm golden-tan & cream fur, classic deep navy maid dress & red collar ribbon!
PALETTE = {
    1: (218, 146, 62, 255),   # Warm Shiba-Inu Golden-Tan Fur & Hair
    2: (168, 102, 38, 255),   # Rich Amber-Brown Shading
    3: (248, 240, 220, 255),  # Soft Cream-White Shiba Belly, Cheeks & Paws
    4: (34, 48, 92, 255),     # Faithful Deep Navy Maid Dress & Shoes
    5: (248, 248, 252, 255),  # Crisp Pure-White Apron, Frills & Headdress
    6: (216, 44, 46, 255),    # Iconic Red Dog-Collar & Maid Neck Ribbon!
    7: (246, 204, 54, 255),   # Golden Collar Tag / Brooch
    8: (252, 226, 206, 255),  # Warm Porcelain Faceplate
    9: (72, 168, 242, 255),   # Loyal Bright Sapphire-Blue Eyes
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
# FORM A: INU (FAITHFUL SHIBA INU DOG) (22 x 40 x 26)
# ============================================================
def build_a():
    grid = np.zeros((22, 40, 26), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 10.5

    # Alert Seated/Standing Faithful Shiba Inu Body (Y: 11..28, Z: 7..17)
    for y in range(11, 29):
        rx = 4.0 if 13 <= y <= 26 else 3.2
        zb = 7 if 14 <= y <= 26 else 8
        zt = 16 if y <= 23 else 17
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                if (dx / rx) ** 2 + ((z - zc) / rz) ** 2 <= 1.0:
                    grid[x, y, z] = 3 if (z <= zb + 1 and dx <= rx * 0.72) else 1

    # Cream chest bib, Navy maid capelet & Iconic Red Dog Collar with Gold Tag!
    fill_sym_box(grid, 0, 2, 25, 29, 8, 14, 3)
    fill_sym_box(grid, 0, 4, 16, 23, 15, 17, 4)   # Navy maid capelet
    fill_sym_box(grid, 0, 4, 16, 23, 14, 14, 5)   # White lace edge
    fill_sym_box(grid, 0, 3, 25, 28, 11, 17, 6)   # Iconic red dog collar!
    fill_sym_box(grid, 0, 1, 28, 29, 10, 12, 7)   # Gold collar tag!

    # Four Grounded Shiba Legs with Cream Socks (Z: 0..9)
    for ly, fy in [(13, 14), (25, 26)]:
        fill_sym_box(grid, 2, 3, ly - 1, ly + 1, 3, 9, 1)
        fill_sym_box(grid, 2, 3, fy - 1, fy + 2, 0, 2, 3)  # Cream Shiba paws!

    # Loyal Shiba Inu Head, Cream Cheeks, Perky Triangle Ears & Bright Eyes (Y: 26..37, Z: 14..25)
    fill_sphere_local(grid, cx, 29.5, 18.0, 4.0, 4.0, 3.8, 1)
    fill_sym_box(grid, 0, 3, 30, 33, 15, 17, 3)   # Fluffy Shiba cream cheeks!
    fill_sym_box(grid, 0, 1, 33, 37, 15, 18, 3)   # Muzzle
    fill_sym_box(grid, 0, 1, 33, 36, 17, 18, 1)   # Nose bridge
    fill_sym_box(grid, 0, 0, 37, 38, 17, 18, 4)   # Cute dark nose!
    fill_sym_box(grid, 2, 2, 32, 33, 18, 19, 4)
    fill_sym_box(grid, 2, 2, 33, 33, 18, 19, 9)   # Loyal bright eyes!
    fill_sym_box(grid, 1, 2, 33, 33, 20, 20, 3)   # Classic Shiba cream eyebrow dots!
    # Perky Pointed Shiba Ears! (犬耳!)
    fill_sym_box(grid, 2, 3, 28, 30, 21, 24, 1)
    fill_sym_box(grid, 3, 3, 28, 29, 24, 25, 2)
    fill_sym_box(grid, 2, 2, 30, 30, 22, 23, 3)

    # ICONIC CURLED FLUFFY SHIBA TAIL (巻き尾!) resting proudly over back! (Y: 6..13, Z: 13..22)
    tail_pts = [(cx, 12, 15), (cx, 9, 16), (cx, 7, 19), (cx, 9, 21), (cx, 11, 20)]
    for i in range(len(tail_pts) - 1):
        draw_6conn_line(grid, tail_pts[i], tail_pts[i + 1], 1, pad=(1, 1, 0))
    fill_sphere_local(grid, cx, 10.5, 20.5, 1.4, 1.4, 1.4, 3)  # Cream tail tip!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: INU FAITHFUL UPRIGHT MAID ROBOT (38 x 24 x 46)
# Dog ears, fluffy curled Shiba tail, dutiful upright stance, navy dress & red collar ribbon!
# ============================================================
def build_b():
    grid = np.zeros((38, 24, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18
    cx_r = X // 2      # 19
    cx_f = (X - 1) / 2.0

    # --- 1. DUTIFUL UPRIGHT STANCE: NAVY SHOES & CRISP WHITE STOCKINGS (Z: 0..11) ---
    fill_sym_box(grid, 2, 4, 10, 16, 0, 2, 4)     # Neat navy Mary-Jane shoes
    fill_sym_box(grid, 2, 4, 15, 17, 0, 1, 4)
    fill_sym_box(grid, 2, 3, 11, 14, 3, 11, 5)    # Crisp white stockings
    fill_sym_box(grid, 2, 3, 11, 14, 9, 9, 6)     # Red ribbon garter

    # --- 2. CLASSIC NAVY MAID SKIRT + CRISP WHITE APRON & CURLED SHIBA TAIL! (Z: 10..22) ---
    for z in range(10, 23):
        r_x = 8 - (z - 10) // 3
        r_y = 5 - (z - 10) // 4
        y0, y1 = 12 - r_y, 13 + r_y
        if z == 10:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 5)  # Crisp white lace hem!
        else:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 4)  # Classic faithful navy maid skirt!
            ap_w = max(2, r_x - 2)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 5) # Crisp white apron!
            if z == 11:
                fill_sym_box(grid, 0, ap_w + 1, y1, y1, z, z, 5)
    # Waist sash & crisp white back bow
    fill_sym_box(grid, 0, 4, 9, 16, 22, 23, 5)
    fill_sym_box(grid, 2, 5, 7, 9, 20, 23, 5)
    fill_sym_box(grid, 0, 1, 7, 8, 21, 22, 6)     # Red bow knot
    # FLUFFY CURLED SHIBA TAIL wagging cleanly behind the skirt!
    tail_b = [(cx_f, 8, 17), (cx_f, 5, 17), (cx_f, 4, 20), (cx_f, 6, 22)]
    for i in range(len(tail_b) - 1):
        draw_6conn_line(grid, tail_b[i], tail_b[i + 1], 1, pad=(1, 0, 0))
    fill_sphere_local(grid, cx_f, 6.0, 22.0, 1.3, 1.3, 1.3, 3)

    # --- 3. FAITHFUL NAVY BODICE, WHITE APRON BIB & RED COLLAR RIBBON + GOLD TAG (Z: 23..33) ---
    fill_sym_box(grid, 0, 4, 10, 15, 23, 32, 4)   # Navy bodice
    fill_sym_box(grid, 0, 2, 15, 16, 23, 30, 5)   # Crisp white apron bib!
    fill_sym_box(grid, 2, 3, 14, 16, 29, 32, 5)   # White ruffled straps
    fill_sym_box(grid, 2, 3, 9, 10, 24, 32, 5)    # Rear straps
    fill_sym_box(grid, 0, 3, 11, 15, 32, 33, 5)   # White collar
    fill_sym_box(grid, 0, 2, 15, 17, 30, 32, 6)   # Red dog-collar maid neck ribbon!
    fill_sym_box(grid, 0, 0, 17, 17, 30, 31, 7)   # Golden dog-tag brooch!

    # --- 4. PUFF SLEEVES & DUTIFUL HANDS CLASPED NEATLY IN FRONT! (忠実そうな立ち姿!) (Z: 19..33) ---
    fill_sym_box(grid, 5, 7, 11, 14, 28, 32, 4)   # Navy puff sleeves
    fill_sym_box(grid, 5, 7, 11, 14, 27, 27, 5)   # White lace ruffle
    # Both arms neatly angled forward-inward clasping hands politely over the white apron!
    fill_sym_box(grid, 5, 7, 12, 15, 22, 26, 4)
    fill_sym_box(grid, 3, 6, 15, 17, 21, 23, 5)   # Crisp white cuffs
    fill_sym_box(grid, 0, 2, 16, 18, 21, 22, 8)   # Dutifully clasped hands!

    # --- 5. HEAD, GOLDEN-SHIBA BOB HAIR, WHITE HEADDRESS & PERKY SHIBA EARS! (Z: 33..45) ---
    fill_sym_box(grid, 0, 1, 12, 14, 33, 34, 8)
    fill_sym_box(grid, 0, 3, 10, 15, 34, 41, 1)   # Warm Shiba golden-tan bob hair!
    fill_sym_box(grid, 0, 3, 9, 10, 29, 39, 2)    # Neat back bob
    fill_sym_box(grid, 3, 4, 12, 15, 31, 39, 1)
    # Loyal Maid Faceplate
    fill_sym_box(grid, 0, 2, 15, 16, 34, 39, 8)
    fill_sym_box(grid, 1, 2, 16, 16, 36, 37, 9)   # Faithful sapphire-blue eyes!
    fill_sym_box(grid, 0, 0, 16, 16, 36, 37, 8)
    fill_sym_box(grid, 0, 2, 15, 16, 39, 40, 1)   # Neat bangs

    # FRILLY WHITE MAID HEADDRESS (Z: 40..43)
    fill_sym_box(grid, 0, 4, 13, 15, 41, 42, 5)
    fill_sym_box(grid, 0, 3, 14, 15, 42, 43, 5)
    fill_sym_box(grid, 3, 4, 14, 15, 41, 41, 6)   # Red side bows

    # PERKY TRIANGULAR SHIBA DOG EARS! (犬耳!) (Z: 41..45)
    fill_sym_box(grid, 2, 4, 11, 13, 41, 43, 1)
    fill_sym_box(grid, 3, 4, 11, 12, 44, 45, 2)
    fill_sym_box(grid, 3, 3, 13, 13, 42, 43, 3)   # Cream inner dog ears!

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=42, pitch_a=20, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "inu_a.vox")
    v_b = export_vox(model_b, "inu_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #11: INU (SHIBA DOG) -> FAITHFUL MAID ROBOT",
        "1. INU (SHIBA INU DOG)",
        "2. INU FAITHFUL MAID ROBOT",
        "preview_inu.png",
        yaw_a=42, pitch_a=20, yaw_b=28, pitch_b=18,
    )
    print(f"inu: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
