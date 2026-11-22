import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Inoshishi (Wild Boar) -> Sturdy, Powerhouse Maid Robot!
# Prominent ivory tusks (牙), pointed boar ears (猪耳), sturdy solid build (がっしりした体格)!
PALETTE = {
    1: (94, 62, 44, 255),     # Deep Bristly Umber-Brown Boar Coat & Hair
    2: (58, 38, 28, 255),     # Dark Espresso Mane Ridge, Dress & Sturdy Boots
    3: (158, 114, 72, 255),   # Warm Bronze-Tan Boar Stripes & Trim
    4: (250, 248, 242, 255),  # Pure Ivory-White Sharp Tusks, Apron & Headdress
    5: (146, 36, 44, 255),    # Deep Burgundy-Crimson Maid Dress & Neck Ribbon
    6: (224, 146, 134, 255),  # Dusky Rose Boar Snout Disc & Blush
    7: (242, 194, 52, 255),   # Burnished Brass Collar Brooch & Armor Studs
    8: (248, 220, 198, 255),  # Warm Porcelain Faceplate
    9: (255, 168, 42, 255),   # Fiery Amber-Gold Determined Eyes
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
# FORM A: INOSHISHI (STURDY WILD BOAR WITH CURVED TUSKS) (24 x 42 x 22)
# ============================================================
def build_a():
    grid = np.zeros((24, 42, 22), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 11.5

    # Broad Heavy Charging Wild Boar Body (Y: 9..29, Z: 5..18)
    for y in range(9, 30):
        rx = 4.6 if y < 14 else (5.6 if y <= 26 else 4.8)
        zb = 5 if 12 <= y <= 27 else 6
        zt = 16 if y < 16 else (18 if y <= 27 else 17)
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                if (dx / rx) ** 2 + ((z - zc) / rz) ** 2 <= 1.0:
                    if z >= zt - 1 and dx <= 1.4:
                        col = 2  # Dark bristly dorsal mane ridge!
                    elif z in (9, 12) and dx >= rx - 1.2:
                        col = 3  # Warm bronze-tan wild boar side stripes!
                    else:
                        col = 1
                    grid[x, y, z] = col
    # Bristly dark dorsal ridge crest along neck & shoulders
    fill_sym_box(grid, 0, 0, 14, 28, 18, 19, 2)

    # Burgundy maid sash & white lace trim across back
    fill_sym_box(grid, 0, 5, 16, 23, 15, 17, 5)
    fill_sym_box(grid, 5, 5, 16, 23, 13, 15, 5)
    fill_sym_box(grid, 5, 5, 16, 23, 12, 12, 4)   # White lace edge!
    fill_sym_box(grid, 0, 1, 28, 30, 8, 10, 7)    # Gold neck badge

    # Four Sturdy Grounded Boar Legs with Cloven Hooves (Z: 0..8)
    for ly in (12, 24):
        fill_sym_box(grid, 3, 4, ly - 1, ly + 1, 2, 8, 1)
        fill_sym_box(grid, 3, 4, ly - 1, ly + 1, 0, 1, 2)  # Dark hooves

    # Broad Wedge-Shaped Boar Head, Flat Snout Disc, Boar Ears & PROMINENT IVORY TUSKS! (Y: 28..40, Z: 7..19)
    fill_sym_box(grid, 0, 4, 28, 34, 8, 16, 1)
    fill_sym_box(grid, 0, 2, 34, 38, 8, 13, 1)    # Tapered snout
    fill_sym_box(grid, 0, 2, 39, 40, 9, 12, 6)    # Classic flat boar snout disc!
    fill_sym_box(grid, 1, 1, 40, 40, 10, 11, 2)   # Nostrils
    # Fierce amber eyes
    fill_sym_box(grid, 3, 4, 32, 34, 13, 14, 2)
    fill_sym_box(grid, 4, 4, 33, 34, 13, 14, 9)
    # Pointed Alert Boar Ears (猪耳!)
    fill_sym_box(grid, 3, 4, 29, 31, 16, 19, 1)
    fill_sym_box(grid, 4, 4, 29, 30, 18, 19, 2)
    # PROMINENT CURVED WHITE IVORY BOAR TUSKS! (牙!) sweeping boldly outward & upward!
    draw_6conn_line(grid, (14, 36, 9), (17, 38, 13), 4)
    draw_6conn_line(grid, (17, 38, 13), (17, 38, 15), 4)
    draw_6conn_line(grid, (9,  36, 9), (6,  38, 13), 4)
    draw_6conn_line(grid, (6,  38, 13), (6,  38, 15), 4)

    # Short tufted boar tail (Y: 5..9, Z: 9..13)
    draw_6conn_line(grid, (11, 9, 12), (11, 6, 9), 1)
    fill_box(grid, 11, 12, 5, 6, 8, 9, 2)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: INOSHISHI STURDY POWERHOUSE MAID ROBOT (44 x 26 x 46)
# Broad sturdy silhouette (がっしりした体格), ivory boar tusks on shoulders/collar, boar ears & headdress!
# ============================================================
def build_b():
    grid = np.zeros((44, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21
    cx_r = X // 2      # 22

    # --- 1. STURDY HEAVY BOOTS & SOLID LEGS (がっしりした体格!) (Z: 0..12) ---
    fill_sym_box(grid, 3, 6, 9, 16, 0, 2, 2)      # Broad sturdy espresso boots
    fill_sym_box(grid, 3, 6, 15, 17, 0, 2, 2)
    fill_sym_box(grid, 3, 6, 10, 15, 3, 3, 7)     # Brass boot strap
    fill_sym_box(grid, 3, 5, 10, 15, 4, 11, 3)    # Sturdy bronze-tan leg stockings

    # --- 2. BROAD BURGUNDY & UMBER MAID SKIRT + HEAVY CRISP WHITE APRON (Z: 10..22) ---
    for z in range(10, 23):
        r_x = 9 - (z - 10) // 4
        r_y = 6 - (z - 10) // 4
        y0, y1 = 13 - r_y, 14 + r_y
        if z == 10:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 4)  # Crisp white lace hem!
        else:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 5)  # Deep burgundy maid skirt
            if z in (13, 17):
                fill_sym_box(grid, max(4, r_x - 2), r_x, y0 + 1, y1 - 1, z, z, 3)  # Bronze boar-stripe accent
            ap_w = max(3, r_x - 3)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 4) # Broad white maid apron!
            if z == 11:
                fill_sym_box(grid, 0, ap_w + 1, y1, y1, z, z, 4)
    # Waist sash & crisp white back bow + little boar tail
    fill_sym_box(grid, 0, 5, 10, 17, 22, 23, 4)
    fill_sym_box(grid, 2, 5, 8, 10, 20, 23, 4)
    fill_sym_box(grid, 0, 1, 8, 9, 21, 22, 5)
    draw_6conn_line(grid, (cx_r, 8, 16), (cx_r, 5, 13), 1)
    fill_box(grid, cx_r - 1, cx_r + 1, 4, 5, 12, 13, 2)

    # --- 3. BROAD STURDY BODICE, WHITE APRON BIB & CURVED TUSK-COLLAR RIBBON! (Z: 23..34) ---
    fill_sym_box(grid, 0, 5, 10, 16, 23, 33, 5)   # Broad burgundy bodice
    fill_sym_box(grid, 0, 3, 16, 17, 23, 30, 4)   # Broad white apron bib!
    fill_sym_box(grid, 3, 4, 15, 17, 29, 33, 4)   # White ruffled straps
    fill_sym_box(grid, 3, 4, 9, 10, 24, 33, 4)    # Rear straps
    fill_sym_box(grid, 0, 4, 11, 16, 33, 34, 4)   # White collar
    fill_sym_box(grid, 0, 2, 16, 18, 31, 33, 2)   # Espresso ribbon bow
    fill_sym_box(grid, 0, 1, 18, 18, 31, 32, 7)   # Brass clasp!
    # SIGNATURE CURVED IVORY BOAR TUSKS (牙!) framing the maid's collar & armored shoulders!
    draw_6conn_line(grid, (cx_r + 4, 15, 31), (cx_r + 6, 17, 35), 4)
    draw_6conn_line(grid, (cx_l - 4, 15, 31), (cx_l - 6, 17, 35), 4)

    # --- 4. BROAD STURDY PUFF-ARMOR SHOULDERS, TUSK PAULDRONS & POWERFUL ARMS (Z: 15..36) ---
    fill_sym_box(grid, 6, 10, 11, 16, 28, 34, 1)  # Broad sturdy umber puff-armor shoulders!
    fill_sym_box(grid, 7, 10, 11, 16, 34, 34, 2)  # Dark bristly shoulder ridge
    fill_sym_box(grid, 6, 10, 11, 16, 27, 27, 4)  # White lace shoulder trim
    # Giant curved ivory boar tusks sweeping up from outer shoulders! (牙!)
    draw_6conn_line(grid, (cx_r + 9, 14, 32), (cx_r + 13, 15, 36), 4)
    draw_6conn_line(grid, (cx_l - 9, 14, 32), (cx_l - 13, 15, 36), 4)
    # Sturdy powerful forearms with white lace cuffs
    fill_box(grid, cx_l - 10, cx_l - 7, 11, 15, 19, 26, 1)
    fill_box(grid, cx_l - 10, cx_l - 7, 11, 15, 18, 18, 4) # White cuff
    fill_box(grid, cx_l - 9, cx_l - 7, 12, 15, 15, 17, 8)  # Sturdy fist
    fill_box(grid, cx_r + 7, cx_r + 10, 11, 16, 19, 26, 1)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 18, 18, 4) # White cuff
    fill_box(grid, cx_r + 7, cx_r + 9, 13, 16, 15, 17, 8)  # Sturdy fist

    # --- 5. HEAD, BRISTLY UMBER HAIR, WHITE HEADDRESS, BOAR EARS & CHEEK TUSKS! (Z: 34..45) ---
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 8)
    fill_sym_box(grid, 0, 3, 10, 16, 35, 42, 1)   # Wild bristly umber hair!
    fill_sym_box(grid, 0, 4, 9, 11, 29, 40, 2)    # Dark bristly back mane-hair!
    fill_sym_box(grid, 3, 4, 13, 16, 32, 40, 1)
    # Determined Maid Faceplate
    fill_sym_box(grid, 0, 2, 16, 17, 35, 40, 8)
    fill_sym_box(grid, 1, 2, 17, 17, 37, 38, 9)   # Fiery amber determined eyes!
    fill_sym_box(grid, 0, 0, 17, 17, 37, 38, 8)
    fill_sym_box(grid, 0, 2, 16, 17, 40, 41, 1)   # Bangs

    # FRILLY WHITE MAID HEADDRESS (Z: 41..44)
    fill_sym_box(grid, 0, 4, 14, 16, 42, 43, 4)
    fill_sym_box(grid, 0, 3, 15, 16, 43, 44, 4)
    fill_sym_box(grid, 3, 4, 15, 16, 42, 42, 5)   # Burgundy side bows

    # POINTED BOAR EARS (猪耳!) rising firmly beside the headdress! (Z: 41..45)
    fill_sym_box(grid, 3, 5, 12, 14, 42, 44, 1)
    fill_sym_box(grid, 4, 5, 12, 13, 44, 45, 2)
    fill_sym_box(grid, 4, 4, 14, 14, 43, 43, 6)   # Dusky rose inner ear

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
    v_a = export_vox(model_a, "inoshishi_a.vox")
    v_b = export_vox(model_b, "inoshishi_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #12: INOSHISHI (BOAR) -> STURDY MAID ROBOT",
        "1. INOSHISHI (WILD BOAR)",
        "2. INOSHISHI STURDY MAID ROBOT",
        "preview_inoshishi.png",
        yaw_a=42, pitch_a=20, yaw_b=28, pitch_b=18,
    )
    print(f"inoshishi: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
