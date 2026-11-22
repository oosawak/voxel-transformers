import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Tori (Rooster / Phoenix-Plumed Bird) -> Feathered Bustle-Skirt Maid Robot!
# Red cockscomb (鶏冠), wing/feather motifs (羽根の意匠), lush iridescent tail plumes as rear skirt bustle!
PALETTE = {
    1: (248, 246, 240, 255),  # Crisp Snow-White Rooster Plumage, Apron & Headdress
    2: (218, 212, 200, 255),  # Soft Cream-Pearl Feather Shading
    3: (218, 38, 42, 255),    # Vivid Scarlet Cockscomb, Wattle & Neck Ribbon (鶏冠)
    4: (26, 98, 108, 255),    # Iridescent Deep Teal-Emerald Tail Plumes & Maid Dress!
    5: (48, 168, 152, 255),   # Luminous Iridescent Turquoise-Green Feather Sheen
    6: (244, 186, 46, 255),   # Golden Beak, Rooster Legs & Dress Trim
    7: (206, 118, 34, 255),   # Warm Amber-Orange Neck Hackle Feathers & Hair
    8: (252, 226, 208, 255),  # Warm Porcelain Faceplate
    9: (255, 198, 44, 255),   # Bright Dawn-Gold Glowing Eyes
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
# FORM A: TORI (PROUD ROOSTER WITH COCKSCOMB & LUSH TAIL PLUMES) (24 x 40 x 30)
# ============================================================
def build_a():
    grid = np.zeros((24, 40, 30), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 11.5

    # Plump Proud White Rooster Body (Y: 13..29, Z: 7..18)
    fill_sphere_local(grid, cx, 21.0, 12.0, 5.2, 7.2, 5.2, 1)
    # Sculpted Folded Side Wings (羽根の意匠!)
    fill_sym_box(grid, 5, 6, 16, 25, 10, 15, 1)
    fill_sym_box(grid, 6, 6, 16, 23, 10, 12, 4)   # Teal wingbar feathers!
    fill_sym_box(grid, 6, 6, 17, 24, 13, 13, 6)   # Gold wing trim

    # Two Golden Grounded Rooster Legs & Claws (Z: 0..8)
    for sign in (-1, 1):
        lx = int(round(cx + sign * 2.5))
        fill_box(grid, lx, lx, 20, 21, 1, 8, 6)
        fill_box(grid, lx - 1, lx + 1, 20, 23, 0, 0, 6)  # 3-toed bird foot!
        fill_box(grid, lx, lx, 18, 24, 0, 0, 6)

    # Upright Amber-Gold Hackle Neck, Head, Beak, Wattle & Iconic Scarlet Cockscomb! (Y: 24..37, Z: 14..29)
    fill_sphere_local(grid, cx, 26.5, 17.5, 3.2, 3.4, 3.8, 7)  # Golden-amber hackle neck!
    fill_sphere_local(grid, cx, 28.0, 21.5, 2.8, 3.2, 3.0, 1)  # White head
    fill_sym_box(grid, 0, 1, 31, 35, 20, 22, 6)   # Sharp golden rooster beak!
    fill_sym_box(grid, 0, 0, 35, 36, 20, 21, 6)
    fill_sym_box(grid, 0, 1, 30, 32, 17, 19, 3)   # Scarlet rooster wattle!
    fill_sym_box(grid, 2, 2, 29, 30, 21, 22, 4)
    fill_sym_box(grid, 2, 2, 30, 30, 21, 22, 9)   # Dawn-gold eyes!
    # ICONIC SCARLET COCKSCOMB (鶏冠!) crowning top of head! (Z: 24..29)
    fill_sym_box(grid, 0, 0, 25, 31, 24, 26, 3)
    fill_sym_box(grid, 0, 0, 26, 27, 27, 28, 3)
    fill_sym_box(grid, 0, 0, 29, 30, 27, 29, 3)

    # LUSH ARCHING IRIDESCENT TEAL & GOLD ROOSTER TAIL PLUMES (尾羽!) (Y: 2..15, Z: 10..27)
    plumes = [
        (0.0, 14, 15,  5, 26, 4),
        (0.0, 14, 14,  2, 22, 5),
        (2.0, 14, 14,  5, 23, 4),
        (-2.0, 14, 14, 5, 23, 4),
        (3.0, 14, 13,  7, 19, 6),
        (-3.0, 14, 13, 7, 19, 6),
    ]
    for dx_p, y0, z0, y1, z1, col_p in plumes:
        ym = (y0 + y1) * 0.45
        zm = max(z0, z1) + 2
        draw_6conn_line(grid, (cx + dx_p * 0.5, y0, z0), (cx + dx_p, ym, zm), col_p, pad=(0, 1, 0))
        draw_6conn_line(grid, (cx + dx_p, ym, zm), (cx + dx_p, y1, z1 - 3), col_p, pad=(0, 0, 0))

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: TORI FEATHER-BUSTLE MAID ROBOT (40 x 28 x 48)
# Scarlet cockscomb atop headdress, wing-feather sleeves/shoulders, tail plumes as grand rear skirt bustle!
# ============================================================
def build_b():
    grid = np.zeros((40, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 19
    cx_r = X // 2      # 20
    cx_f = (X - 1) / 2.0

    # --- 1. GOLDEN SHOES & CRISP WHITE STOCKINGS (Z: 0..11) ---
    fill_sym_box(grid, 2, 4, 12, 18, 0, 2, 6)     # Golden bird-themed shoes
    fill_sym_box(grid, 2, 4, 17, 19, 0, 1, 3)     # Scarlet shoe tips
    fill_sym_box(grid, 2, 3, 13, 16, 3, 11, 1)    # Crisp white stockings
    fill_sym_box(grid, 2, 3, 13, 16, 9, 9, 4)     # Teal garter band

    # --- 2. TEAL-EMERALD MAID SKIRT + CRISP WHITE APRON + GRAND TAIL-PLUME REAR BUSTLE! (Z: 10..22) ---
    for z in range(10, 23):
        r_x = 8 - (z - 10) // 3
        r_y = 5 - (z - 10) // 4
        y0, y1 = 14 - r_y, 15 + r_y
        if z == 10:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 1)  # Crisp white lace hem!
        elif z == 11:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 6)  # Gold hem trim
        else:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 4)  # Iridescent deep teal maid skirt!
            ap_w = max(2, r_x - 2)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 1) # Crisp white apron!
    # Waist sash & white back bow
    fill_sym_box(grid, 0, 4, 11, 18, 22, 23, 1)
    fill_sym_box(grid, 2, 5, 9, 11, 20, 23, 1)
    fill_sym_box(grid, 0, 1, 9, 10, 21, 22, 3)    # Scarlet bow knot

    # SIGNATURE ROOSTER TAIL PLUMES AS A GRAND VICTORIAN REAR SKIRT BUSTLE! (尾羽がスカートの後ろ飾り!)
    bustle_plumes = [
        (0.0, 10, 20,  2, 12, 5),   # Center sweeping turquoise plume!
        (2.5, 10, 20,  3, 11, 4),   # Inner teal plumes
        (-2.5, 10, 20, 3, 11, 4),
        (5.0, 10, 19,  4, 10, 6),   # Outer golden tail plumes!
        (-5.0, 10, 19, 4, 10, 6),
        (7.5, 11, 18,  6, 11, 4),   # Flaring side plumes visible even from FRONT 3/4 view!
        (-7.5, 11, 18, 6, 11, 4),
    ]
    for dx_b, y0, z0, y1, z1, col_b in bustle_plumes:
        ym = (y0 + y1) * 0.45
        zm = z0 + 3
        draw_6conn_line(grid, (cx_f + dx_b * 0.4, y0, z0), (cx_f + dx_b, ym, zm), col_b, pad=(0, 1, 0))
        draw_6conn_line(grid, (cx_f + dx_b, ym, zm), (cx_f + dx_b * 1.1, y1, z1), col_b)

    # --- 3. TEAL MAID BODICE, WHITE APRON BIB & SCARLET RIBBON (Z: 23..33) ---
    fill_sym_box(grid, 0, 4, 12, 17, 23, 32, 4)   # Teal bodice
    fill_sym_box(grid, 0, 2, 17, 18, 23, 30, 1)   # Crisp white apron bib!
    fill_sym_box(grid, 2, 3, 16, 18, 29, 32, 1)   # White ruffled straps
    fill_sym_box(grid, 2, 3, 11, 12, 24, 32, 1)   # Rear straps
    fill_sym_box(grid, 0, 3, 13, 17, 32, 33, 1)   # White collar
    fill_sym_box(grid, 0, 2, 17, 19, 30, 32, 3)   # Scarlet neck ribbon!
    fill_sym_box(grid, 0, 0, 19, 19, 31, 31, 6)   # Gold brooch!

    # --- 4. WING-FEATHER PUFF SLEEVES & FEATHERED ARMS (羽根の意匠!) (Z: 16..35) ---
    fill_sym_box(grid, 5, 8, 13, 16, 28, 32, 1)   # Snow-white feathered puff sleeves!
    # Sweeping miniature wing-feather shoulder ornaments flaring cleanly outward!
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        draw_6conn_line(grid, (bx + sign * 7, 13, 31), (bx + sign * 12, 10, 35), 1)
        draw_6conn_line(grid, (bx + sign * 7, 13, 29), (bx + sign * 11, 10, 32), 5)
        draw_6conn_line(grid, (bx + sign * 7, 13, 28), (bx + sign * 10, 11, 29), 6)
    fill_box(grid, cx_l - 7, cx_l - 6, 13, 16, 20, 27, 4)
    fill_box(grid, cx_l - 7, cx_l - 6, 13, 16, 19, 19, 1)
    fill_box(grid, cx_l - 7, cx_l - 6, 14, 16, 17, 18, 8)
    fill_box(grid, cx_r + 6, cx_r + 7, 13, 17, 21, 27, 4)
    fill_box(grid, cx_r + 6, cx_r + 8, 16, 19, 20, 22, 1)
    fill_box(grid, cx_r + 7, cx_r + 8, 18, 20, 20, 21, 8)

    # --- 5. HEAD, AMBER-GOLD HACKLE HAIR, WHITE HEADDRESS & SCARLET COCKSCOMB! (Z: 33..47) ---
    fill_sym_box(grid, 0, 1, 14, 16, 33, 34, 8)
    fill_sym_box(grid, 0, 3, 12, 17, 34, 41, 7)   # Warm amber-gold hackle hair!
    fill_sym_box(grid, 0, 3, 11, 12, 28, 39, 7)   # Feathered back hair
    fill_sym_box(grid, 3, 4, 14, 17, 31, 39, 7)
    # Bright Maid Faceplate
    fill_sym_box(grid, 0, 2, 17, 18, 34, 39, 8)
    fill_sym_box(grid, 1, 2, 18, 18, 36, 37, 9)   # Dawn-gold eyes!
    fill_sym_box(grid, 0, 0, 18, 18, 36, 37, 8)
    fill_sym_box(grid, 0, 2, 17, 18, 39, 40, 7)

    # FRILLY WHITE FEATHER-WING HEADDRESS (Z: 40..43)
    fill_sym_box(grid, 0, 4, 15, 17, 41, 42, 1)
    fill_sym_box(grid, 0, 3, 16, 17, 42, 43, 1)
    fill_sym_box(grid, 3, 5, 15, 17, 41, 43, 1)   # Winged side-feathers on headdress!
    fill_sym_box(grid, 3, 4, 16, 17, 41, 41, 3)   # Scarlet ribbon accents

    # ICONIC SCARLET COCKSCOMB (鶏冠!) rising proudly above the white maid headdress! (Z: 42..47)
    fill_sym_box(grid, 0, 0, 12, 17, 42, 44, 3)
    fill_sym_box(grid, 0, 0, 16, 17, 45, 47, 3)   # Front comb peak
    fill_sym_box(grid, 0, 0, 13, 14, 45, 46, 3)   # Rear comb peak

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=44, pitch_a=20, yaw_b=30, pitch_b=18):
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
    v_a = export_vox(model_a, "tori_a.vox")
    v_b = export_vox(model_b, "tori_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #10: TORI (ROOSTER) -> FEATHER-BUSTLE MAID ROBOT",
        "1. TORI (ROOSTER)",
        "2. TORI FEATHER MAID ROBOT",
        "preview_tori.png",
        yaw_a=44, pitch_a=20, yaw_b=30, pitch_b=18,
    )
    print(f"tori: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
