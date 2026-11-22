import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# West Sea Dragon King / Saikai Ryuo (西海竜王・敖閏) -> Pure-White Silver Dragon Robot!
# White-themed (白): Noble Pearlescent Cloud-Sea Dragon -> White Dragon Knight Robot with horns, whiskers & tail!
PALETTE = {
    1: (242, 246, 252, 255),  # Pure Pearl-White Dragon Scales & Armor (白基調)
    2: (192, 204, 224, 255),  # Cool Silver-Blue Shading & Scale Seams
    3: (132, 178, 232, 255),  # Frost-Blue Belly Scales & Cloud Mist
    4: (242, 204, 82, 255),   # Pale Champagne-Gold Antler Horns & Crown
    5: (152, 168, 194, 255),  # Honed Platinum-Silver Whiskers & Trim
    6: (72, 92, 128, 255),    # Deep Steel-Blue Inner Frame & Claws
    7: (42, 52, 74, 255),     # Dark Indigo Joints
    8: (178, 234, 255, 255),  # Crystalline Ice-Blade Spear Edge
    9: (76, 224, 255, 255),   # Luminous Frost-Cyan Dragon Eyes & Pearl Core!
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


def draw_frost_spear(grid, hx, hy, z_bot, z_top):
    """Draw the West Sea Dragon King's Silver-Frost Dragon Lance (白竜氷槍)."""
    fill_box(grid, hx, hx, hy, hy, z_bot, z_top - 8, 6)
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_top - 9, z_top - 8, 4)
    fill_box(grid, hx, hx, hy, hy, z_top - 7, z_top, 8)
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_top - 7, z_top - 4, 8)
    fill_box(grid, hx, hx, hy, hy, z_top - 6, z_top - 3, 9)


# ============================================================
# FORM A: WEST SEA DRAGON KING IN WHITE CLOUD-DRAGON FORM (竜の姿) (36 x 34 x 42)
# ============================================================
def build_a():
    grid = np.zeros((36, 34, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = X // 2  # 18

    # Swirling Cloud-Mist Base grounded at Z=0..2
    fill_box(grid, cx - 8, cx + 6, 12, 21, 0, 1, 2)
    fill_box(grid, cx - 6, cx + 4, 14, 19, 2, 2, 3)
    fill_box(grid, cx - 8, cx - 5, 19, 21, 2, 3, 1)
    fill_box(grid, cx + 4, cx + 6, 19, 21, 2, 3, 1)

    # Graceful Ascending Pearlescent White Dragon Coil
    spine = [
        (cx - 8, 16, 4), (cx - 4, 10, 8), (cx + 5, 10, 11), (cx + 9, 17, 15),
        (cx + 3, 22, 19), (cx - 6, 20, 23), (cx - 5, 13, 27), (cx, 15, 31),
        (cx, 19, 34)
    ]
    for i in range(len(spine) - 1):
        draw_6conn_line(grid, spine[i], spine[i + 1], 1, pad=(2, 2, 2))
        p0, p1 = spine[i], spine[i + 1]
        draw_6conn_line(grid, (p0[0], p0[1] + 2, p0[2] - 1), (p1[0], p1[1] + 2, p1[2] - 1), 3, pad=(1, 0, 0))
        # Crystalline silver-blue dorsal crest
        draw_6conn_line(grid, (p0[0], p0[1] - 2, p0[2] + 2), (p1[0], p1[1] - 2, p1[2] + 2), 8, pad=(0, 0, 0))

    # Graceful Silver-Plumed Tail
    draw_6conn_line(grid, (cx - 8, 16, 4), (cx - 13, 20, 4), 1, pad=(1, 1, 1))
    draw_6conn_line(grid, (cx - 13, 20, 4), (cx - 14, 24, 7), 8, pad=(1, 0, 1))
    fill_box(grid, cx - 15, cx - 13, 24, 26, 6, 9, 9)

    # Claws & Ice-Crystal Pearl
    draw_6conn_line(grid, (cx + 3, 22, 19), (cx + 8, 26, 18), 1, pad=(1, 1, 1))
    fill_box(grid, cx + 7, cx + 10, 26, 28, 17, 18, 6)
    draw_6conn_line(grid, (cx - 6, 20, 23), (cx - 9, 25, 24), 1, pad=(1, 1, 1))
    fill_box(grid, cx - 11, cx - 9, 25, 27, 23, 25, 9)  # Frost Dragon Pearl!

    # Noble Pure-White Dragon Head, Champagne-Gold Antlers & Long Flowing Whiskers! (Z: 31..41)
    fill_box(grid, cx - 3, cx + 3, 17, 25, 32, 37, 1)
    fill_box(grid, cx - 2, cx + 2, 25, 29, 32, 35, 1)
    fill_box(grid, cx - 2, cx + 2, 24, 28, 31, 32, 3)
    fill_box(grid, cx - 2, cx + 2, 28, 29, 33, 33, 2)
    fill_box(grid, cx - 3, cx - 2, 23, 24, 35, 36, 9)
    fill_box(grid, cx + 2, cx + 3, 23, 24, 35, 36, 9)
    fill_box(grid, cx - 4, cx + 4, 15, 18, 32, 38, 2)   # Flowing silver mane!
    for sign in (-1, 1):
        draw_6conn_line(grid, (cx + sign * 2, 19, 37), (cx + sign * 6, 15, 41), 4)
        draw_6conn_line(grid, (cx + sign * 4, 17, 39), (cx + sign * 7, 17, 40), 4)
        draw_6conn_line(grid, (cx + sign * 2, 28, 33), (cx + sign * 7, 30, 32), 5)
        draw_6conn_line(grid, (cx + sign * 7, 30, 32), (cx + sign * 10, 27, 29), 5)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: WEST SEA DRAGON KING WHITE KNIGHT ROBOT (48 x 28 x 48)
# ============================================================
def build_b():
    grid = np.zeros((48, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # White Dragon-Knight Greaves & Claws (Z: 0..16)
    fill_sym_box(grid, 2, 5, 11, 18, 0, 2, 6)
    fill_sym_box(grid, 2, 5, 18, 20, 0, 1, 2)
    fill_sym_box(grid, 2, 5, 12, 17, 3, 14, 1)    # Crisp pure-white greaves
    fill_sym_box(grid, 3, 4, 17, 18, 4, 13, 3)    # Frost-blue scale inlay
    fill_sym_box(grid, 2, 5, 17, 19, 12, 15, 4)   # Champagne-gold knee guards
    fill_sym_box(grid, 3, 4, 19, 19, 13, 14, 9)

    # Waist Armor & Pearlescent White Dragon Tail (竜の尾!) (Z: 15..24)
    fill_sym_box(grid, 2, 4, 12, 16, 15, 19, 7)
    fill_sym_box(grid, 0, 5, 12, 16, 19, 22, 6)
    fill_sym_box(grid, 1, 5, 16, 18, 16, 21, 1)
    fill_sym_box(grid, 1, 5, 18, 18, 16, 16, 4)
    fill_sym_box(grid, 0, 1, 17, 19, 18, 22, 3)
    fill_sym_box(grid, 0, 1, 19, 19, 20, 21, 4)
    # Sweeping White Dragon Tail
    tail_pts = [(cx_r, 12, 20), (cx_r + 3, 7, 18), (cx_r + 7, 4, 15), (cx_r + 10, 5, 19), (cx_r + 12, 7, 25)]
    for i in range(len(tail_pts) - 1):
        draw_6conn_line(grid, tail_pts[i], tail_pts[i + 1], 1, pad=(1, 1, 1))
    fill_box(grid, cx_r + 11, cx_r + 14, 6, 8, 24, 28, 8)  # Frost-crystal tail plume!

    # Pure-White Chest Cuirass & Cloud-Wing Backpack (Z: 22..36)
    fill_sym_box(grid, 0, 4, 12, 16, 22, 24, 7)
    fill_sym_box(grid, 0, 6, 11, 18, 25, 33, 1)
    fill_sym_box(grid, 1, 5, 18, 19, 26, 32, 3)
    fill_sym_box(grid, 0, 2, 19, 20, 27, 31, 4)
    fill_sym_box(grid, 0, 1, 20, 20, 28, 30, 9)
    fill_sym_box(grid, 0, 4, 8, 11, 25, 33, 2)
    fill_sym_box(grid, 3, 7, 7, 9, 28, 37, 1)     # Sleek white cloud-dragon dorsal fins!
    fill_sym_box(grid, 5, 7, 7, 8, 35, 39, 8)

    # Noble White Dragon Pauldrons & FROST DRAGON LANCE! (Z: 15..46)
    fill_sym_box(grid, 6, 8, 13, 16, 29, 32, 7)
    fill_sym_box(grid, 7, 11, 11, 17, 28, 34, 1)
    fill_sym_box(grid, 8, 12, 12, 16, 33, 35, 4)
    fill_sym_box(grid, 10, 12, 13, 15, 29, 32, 3)
    fill_sym_box(grid, 7, 9, 13, 16, 22, 28, 7)
    fill_box(grid, cx_l - 10, cx_l - 7, 13, 17, 16, 21, 1)
    fill_box(grid, cx_l - 10, cx_l - 8, 14, 16, 14, 15, 6)
    fill_box(grid, cx_r + 7, cx_r + 10, 13, 17, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 13, 16, 20, 17, 20, 4)
    draw_frost_spear(grid, cx_r + 13, 19, z_bot=2, z_top=45)

    # White Dragon Robot Head: ANTLER HORNS & SILVER WHISKERS (角と髭!) (Z: 34..47)
    fill_sym_box(grid, 0, 1, 13, 16, 34, 35, 7)
    fill_sym_box(grid, 0, 3, 11, 18, 35, 41, 1)
    fill_sym_box(grid, 0, 2, 18, 20, 35, 37, 2)
    fill_sym_box(grid, 0, 2, 18, 19, 38, 39, 6)
    fill_sym_box(grid, 1, 2, 19, 19, 38, 39, 9)
    fill_sym_box(grid, 0, 1, 16, 19, 41, 44, 4)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        draw_6conn_line(grid, (bx + sign * 2, 15, 41), (bx + sign * 7, 12, 46), 4)
        draw_6conn_line(grid, (bx + sign * 4, 14, 43), (bx + sign * 8, 15, 45), 4)
        draw_6conn_line(grid, (bx + sign * 2, 20, 36), (bx + sign * 7, 21, 35), 5)
        draw_6conn_line(grid, (bx + sign * 7, 21, 35), (bx + sign * 9, 19, 32), 5)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=34, pitch_a=20, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "saikai_a.vox")
    v_b = export_vox(model_b, "saikai_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #08: WEST SEA DRAGON KING (AO RUN) -> WHITE DRAGON ROBOT",
        "1. WEST SEA DRAGON (DRAGON FORM)",
        "2. WEST SEA DRAGON ROBOT",
        "preview_saikai.png",
    )
    print(f"saikai: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
