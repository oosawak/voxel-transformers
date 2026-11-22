import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Hitsuji (Fluffy White Sheep) -> Fluffy Wool-Hair White-Dominant Maid Robot!
# Fluffy cloud-like wool hair (もこもこの髪), small curled horns (小さな角), white-dominant palette (白基調)!
PALETTE = {
    1: (250, 248, 242, 255),  # Fluffy Pure-White Sheep Wool, Apron & Headdress (白基調)
    2: (224, 218, 206, 255),  # Soft Warm-Cream Wool Curls & Dress Shading
    3: (116, 158, 208, 255),  # Soft Pastel Sky-Blue Maid Dress Trim & Sash
    4: (68, 96, 146, 255),    # Gentle Slate-Blue Ribbon Shading & Shoes
    5: (224, 186, 122, 255),  # Warm Caramel-Ivory Small Curled Sheep Horns!
    6: (244, 152, 168, 255),  # Soft Pastel Rose Neck Ribbon & Blush
    7: (246, 206, 68, 255),   # Golden Shepherd Bell on Neck Ribbon
    8: (252, 224, 204, 255),  # Warm Peach-Porcelain Sheep Face & Maid Faceplate
    9: (106, 198, 252, 255),  # Gentle Sparkling Sky-Blue Eyes
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
# FORM A: HITSUJI (FLUFFY CLOUD-LIKE WHITE SHEEP) (24 x 36 x 24)
# ============================================================
def build_a():
    grid = np.zeros((24, 36, 24), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 11.5

    # Fluffy Cloud-Like Wool Body composed of overlapping soft wool puffs! (Y: 8..26, Z: 6..18)
    wool_puffs = [
        (0.0, 17.0, 12.0, 6.2, 7.8, 5.2, 1),
        (3.8, 13.0, 13.0, 3.2, 3.5, 3.2, 1),
        (4.0, 19.0, 13.5, 3.4, 3.6, 3.4, 1),
        (3.2, 23.0, 13.0, 3.2, 3.2, 3.2, 2),
        (0.0, 12.0, 15.0, 3.8, 3.5, 3.0, 1),
        (0.0, 18.0, 16.0, 4.0, 4.0, 3.0, 1),
        (0.0, 23.0, 15.5, 3.8, 3.5, 3.0, 1),
        (0.0,  9.5, 11.5, 3.0, 2.8, 2.8, 2),  # Fluffy round wool tail puff!
    ]
    for xo, wy, wz, rx, ry, rz, col in wool_puffs:
        fill_sphere_local(grid, cx + xo, wy, wz, rx, ry, rz, col)
        if xo > 0:
            fill_sphere_local(grid, cx - xo, wy, wz, rx, ry, rz, col)

    # Pastel Sky-Blue Maid Ribbon & Golden Shepherd Bell around neck!
    fill_sym_box(grid, 0, 3, 24, 27, 9, 15, 3)
    fill_sym_box(grid, 0, 1, 27, 28, 9, 11, 7)    # Gold bell!

    # Four Cute Grounded Sheep Legs (Z: 0..8)
    for ly in (12, 22):
        fill_sym_box(grid, 2, 3, ly - 1, ly + 1, 2, 8, 8)
        fill_sym_box(grid, 2, 3, ly - 1, ly + 1, 0, 1, 4)  # Little slate hooves

    # Cute Peach-Porcelain Sheep Face, Fluffy Wool Cap, Droopy Ears & Small Curled Horns! (Y: 25..34, Z: 11..21)
    fill_sphere_local(grid, cx, 29.0, 14.5, 3.4, 3.8, 3.2, 8)
    fill_sphere_local(grid, cx, 28.0, 18.0, 3.5, 3.2, 2.4, 1)  # Fluffy wool forelock cap!
    fill_sym_box(grid, 2, 2, 31, 32, 15, 16, 4)
    fill_sym_box(grid, 2, 2, 32, 32, 15, 16, 9)   # Gentle sky-blue eyes!
    fill_sym_box(grid, 0, 0, 33, 33, 13, 14, 6)   # Cute pink nose!
    # Droopy soft sheep ears
    fill_sym_box(grid, 4, 5, 27, 29, 14, 16, 8)
    # Small Curled Caramel Horns (小さな角!)
    for sign in (-1, 1):
        hx = int(round(cx + sign * 3.0))
        draw_6conn_line(grid, (hx, 28, 18), (hx + sign * 2, 27, 20), 5)
        draw_6conn_line(grid, (hx + sign * 2, 27, 20), (hx + sign * 2, 29, 19), 5)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: HITSUJI FLUFFY WHITE-DOMINANT MAID ROBOT (38 x 24 x 46)
# White-dominant dress & apron, fluffy cloud-wool hair (もこもこの髪), small curled horns (小さな角)!
# ============================================================
def build_b():
    grid = np.zeros((38, 24, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18
    cx_r = X // 2      # 19
    cx_f = (X - 1) / 2.0

    # --- 1. SOFT SLATE-BLUE MARY-JANE SHOES & FLUFFY-CUFFED WHITE STOCKINGS (Z: 0..11) ---
    fill_sym_box(grid, 2, 4, 10, 15, 0, 2, 4)     # Gentle slate-blue shoes
    fill_sym_box(grid, 2, 4, 14, 16, 0, 1, 4)
    fill_sym_box(grid, 2, 3, 11, 14, 3, 11, 1)    # Pure-white stockings
    fill_sym_box(grid, 2, 4, 11, 14, 3, 4, 2)     # Fluffy cream wool ankle cuffs!

    # --- 2. WHITE-DOMINANT FLUFFY MAID SKIRT WITH PASTEL SKY-BLUE TRIM & WHITE APRON (Z: 10..22) ---
    for z in range(10, 23):
        r_x = 8 - (z - 10) // 3
        r_y = 5 - (z - 10) // 4
        y0, y1 = 12 - r_y, 13 + r_y
        if z == 10:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 1)  # Fluffy white wool-frill hem!
        elif z == 11:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 3)  # Soft pastel sky-blue dress trim band!
        else:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 2)  # Warm cream-white main maid skirt (白基調!)
            ap_w = max(2, r_x - 2)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 1) # Crisp bright pure-white apron!
    # Sky-blue waist ribbon & fluffy white back bow + fluffy sheep tail puff!
    fill_sym_box(grid, 0, 4, 9, 16, 22, 23, 3)    # Pastel sky-blue waist sash
    fill_sym_box(grid, 2, 5, 7, 9, 20, 23, 1)     # Big fluffy white back bow!
    fill_sym_box(grid, 0, 1, 7, 8, 21, 22, 6)     # Rose bow center
    fill_sphere_local(grid, cx_f, 6.2, 15.5, 2.4, 2.4, 2.4, 1)  # Fluffy round sheep tail!

    # --- 3. WHITE-DOMINANT MAID BODICE, APRON BIB & ROSE-RIBBON BELL (Z: 23..33) ---
    fill_sym_box(grid, 0, 4, 10, 15, 23, 32, 2)   # Cream-white bodice
    fill_sym_box(grid, 3, 4, 14, 15, 24, 31, 3)   # Pastel blue side trim
    fill_sym_box(grid, 0, 2, 15, 16, 23, 30, 1)   # Pure-white apron bib!
    fill_sym_box(grid, 2, 3, 14, 16, 29, 32, 1)   # White ruffled straps
    fill_sym_box(grid, 2, 3, 9, 10, 24, 32, 1)    # Rear straps
    fill_sym_box(grid, 0, 3, 11, 15, 32, 33, 1)   # Fluffy white collar
    fill_sym_box(grid, 0, 2, 15, 17, 30, 32, 6)   # Soft rose neck ribbon!
    fill_sym_box(grid, 0, 0, 17, 17, 30, 31, 7)   # Tiny golden shepherd bell!

    # --- 4. FLUFFY WOOL PUFF SLEEVES & GENTLE ARMS (Z: 16..33) ---
    fill_sphere_local(grid, cx_r + 6.0, 12.5, 30.0, 2.4, 2.4, 2.6, 1)  # Fluffy wool-cloud puff sleeves!
    fill_sphere_local(grid, cx_l - 6.0, 12.5, 30.0, 2.4, 2.4, 2.6, 1)
    fill_box(grid, cx_l - 7, cx_l - 6, 11, 14, 20, 27, 2)
    fill_box(grid, cx_l - 7, cx_l - 6, 11, 14, 19, 19, 1)
    fill_box(grid, cx_l - 7, cx_l - 6, 12, 14, 17, 18, 8)
    fill_box(grid, cx_r + 6, cx_r + 7, 11, 15, 21, 27, 2)
    fill_box(grid, cx_r + 6, cx_r + 8, 14, 17, 20, 22, 1)
    fill_box(grid, cx_r + 7, cx_r + 8, 16, 18, 20, 21, 8)

    # --- 5. FLUFFY CLOUD-WOOL HAIR (もこもこの髪!), FRILLY HEADDRESS & SMALL CURLED HORNS! (Z: 33..45) ---
    fill_sym_box(grid, 0, 1, 12, 14, 33, 34, 8)
    # Sculpted Fluffy Cloud-Like White Sheep Hair Curls enveloping head & framing face!
    fill_sphere_local(grid, cx_f, 12.5, 38.0, 4.4, 4.0, 4.2, 1)
    for xo, hy, hz, hr in [
        (4.2, 13.0, 35.5, 2.4),   # Fluffy wool side-puffs!
        (4.5, 11.5, 38.5, 2.4),
        (3.2, 10.0, 33.5, 2.4),   # Fluffy rear cloud-curls!
        (0.0,  9.5, 34.5, 2.8),
        (2.4, 12.5, 41.0, 2.2),   # Fluffy cloud crown!
        (0.0, 12.0, 41.5, 2.5),
    ]:
        fill_sphere_local(grid, cx_f + xo, hy, hz, hr, hr, hr, 1)
        if xo > 0:
            fill_sphere_local(grid, cx_f - xo, hy, hz, hr, hr, hr, 1)
    # Sweet Faceplate peeking cleanly from fluffy wool hair!
    fill_sym_box(grid, 0, 2, 15, 17, 34, 38, 8)
    fill_sym_box(grid, 1, 2, 17, 17, 36, 37, 9)   # Gentle sky-blue eyes!
    fill_sym_box(grid, 0, 0, 17, 17, 36, 37, 8)
    fill_sym_box(grid, 2, 2, 17, 17, 35, 35, 6)   # Soft rosy blush

    # FRILLY WHITE & SKY-BLUE MAID HEADDRESS (Z: 40..44)
    fill_sym_box(grid, 0, 4, 15, 17, 40, 41, 3)   # Pastel sky-blue headdress ribbon band!
    fill_sym_box(grid, 0, 3, 15, 17, 42, 43, 1)   # Scalloped pure-white lace brim!
    fill_sym_box(grid, 3, 4, 16, 17, 40, 41, 6)   # Rose side bows

    # SMALL CURLED CARAMEL SHEEP HORNS (小さな角!) curling adorably beside the fluffy wool hair! (Z: 38..44)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        draw_6conn_line(grid, (bx + sign * 4, 14, 41), (bx + sign * 6, 13, 43), 5)
        draw_6conn_line(grid, (bx + sign * 6, 13, 43), (bx + sign * 7, 14, 41), 5)
        draw_6conn_line(grid, (bx + sign * 7, 14, 41), (bx + sign * 6, 15, 39), 5)

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
    v_a = export_vox(model_a, "hitsuji_a.vox")
    v_b = export_vox(model_b, "hitsuji_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #08: HITSUJI (SHEEP) -> FLUFFY WHITE MAID ROBOT",
        "1. HITSUJI (FLUFFY SHEEP)",
        "2. HITSUJI FLUFFY MAID ROBOT",
        "preview_hitsuji.png",
        yaw_a=42, pitch_a=22, yaw_b=28, pitch_b=18,
    )
    print(f"hitsuji: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
