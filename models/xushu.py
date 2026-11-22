import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

PALETTE = {
    1: (244, 246, 250, 255),  # Pure White Sage Robe & Crane Plumage (白い鶴)
    2: (52, 112, 168, 255),   # Serene Sky-Indigo Wandering Strategist Cloak
    3: (36, 146, 98, 255),    # Jade-Teal Sage Trim & Bamboo Moss Base
    4: (26, 28, 36, 255),     # Jet-Black Crane Wingtips, Legs & Cap Trim
    5: (212, 42, 46, 255),    # Iconic Red-Crowned Crane Crest (丹頂)!
    6: (238, 196, 62, 255),   # Pale-Gold Crane Beak & Sword Fittings
    7: (250, 222, 200, 255),  # Calm Scholar Face
    8: (192, 204, 220, 255),  # Cool Silver Sword Blade & Wing Shading
    9: (102, 232, 244, 255),  # Luminous Sage Eyes & Core
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


def render_preview_3(forms, title_banner, out_path):
    cw, ch = 1274, 540
    canvas = Image.new("RGBA", (cw, ch), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, cw, 20):
        draw.line([(gx, 0), (gx, ch)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, ch, 20):
        draw.line([(0, gy), (cw, gy)], fill=(28, 34, 48, 255), width=1)
    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(forms):
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
        for pi in range(1, len(PALETTE) + 1):
            px0, py0 = bx + 14 + (pi - 1) * 20, by + 430
            draw.rectangle([px0, py0, px0 + 15, py0 + 15], fill=PALETTE[pi], outline=(70, 82, 105, 255))
    canvas.save(out_path)

def build_a():
    grid = np.zeros((36, 22, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    # Boots & Serene Flowing White-and-Blue Sage Robes (Z: 0..19)
    fill_sym_box(grid, 2, 4, 9, 14, 0, 2, 4)
    for z in range(2, 18):
        rw = 5 - (z - 2) // 9
        fill_sym_box(grid, 0, rw, 8, 14, z, z, 1 if z < 11 else 2)
        if z in (2, 11):
            fill_sym_box(grid, 0, rw, 8, 14, z, z, 3)
        fill_sym_box(grid, 0, 1, 14, 15, z, z, 1)
    fill_sym_box(grid, 0, 5, 8, 15, 17, 19, 3)
    # Sage Torso & Flowing Hooded Cloak (Z: 19..30)
    fill_sym_box(grid, 0, 4, 8, 14, 19, 28, 1)
    fill_sym_box(grid, 1, 4, 14, 15, 20, 27, 2)
    fill_sym_box(grid, 0, 5, 6, 8, 5, 30, 2)      # Long wandering scholar cloak
    fill_sym_box(grid, 0, 5, 6, 6, 5, 6, 1)
    # Wide Sleeves & Gentleman's Straight Sword
    fill_box(grid, cx_l - 7, cx_l - 5, 9, 13, 21, 27, 2)
    fill_box(grid, cx_l - 7, cx_l - 5, 12, 15, 19, 21, 7)
    fill_box(grid, cx_r + 5, cx_r + 7, 9, 13, 21, 27, 2)
    fill_box(grid, cx_r + 6, cx_r + 9, 13, 17, 20, 22, 7)
    sx = cx_r + 9
    fill_box(grid, sx, sx, 16, 17, 17, 20, 3)
    fill_box(grid, sx - 1, sx + 1, 16, 17, 21, 21, 6)
    fill_box(grid, sx, sx, 16, 17, 22, 37, 8)
    # Calm Sage Head, Scholar Hood & Tall Hat (Z: 29..41)
    fill_sym_box(grid, 0, 1, 10, 13, 29, 30, 7)
    fill_sym_box(grid, 0, 2, 10, 14, 30, 36, 7)
    fill_sym_box(grid, 1, 2, 14, 14, 33, 33, 4)
    fill_sym_box(grid, 0, 3, 7, 15, 35, 39, 2)    # Hooded sage cap!
    fill_sym_box(grid, 0, 2, 9, 14, 39, 41, 1)    # White top knot
    fill_sym_box(grid, 0, 1, 14, 15, 37, 38, 5)   # Crimson crane-crest brooch!
    hollow_interior_26(grid, 1, Z - 2)
    return grid


def build_b():
    grid = np.zeros((46, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    # Sleek White-Blue Sage Mecha Legs
    fill_sym_box(grid, 2, 5, 10, 17, 0, 2, 4)
    fill_sym_box(grid, 2, 5, 11, 16, 3, 14, 1)
    fill_sym_box(grid, 3, 4, 15, 16, 5, 13, 2)
    fill_sym_box(grid, 2, 5, 15, 17, 12, 15, 3)
    # Waist & Scholar Robe Tassets
    fill_sym_box(grid, 2, 4, 11, 15, 15, 19, 4)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 4)
    fill_sym_box(grid, 1, 5, 15, 16, 14, 21, 1)
    fill_sym_box(grid, 1, 5, 16, 16, 14, 15, 2)
    fill_sym_box(grid, 5, 6, 11, 15, 15, 21, 2)
    fill_sym_box(grid, 0, 1, 15, 17, 17, 22, 3)
    # Crane-Wing Chest & Swept White-Black Wing Backpack
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 4)
    fill_sym_box(grid, 0, 6, 10, 16, 25, 33, 1)
    fill_sym_box(grid, 1, 5, 16, 17, 26, 32, 2)
    fill_sym_box(grid, 0, 2, 17, 18, 28, 30, 9)
    fill_sym_box(grid, 0, 4, 7, 10, 24, 32, 2)
    for sign in (-1, 1):
        ox = cx_r if sign == 1 else cx_l
        draw_6conn_line(grid, (ox + sign * 3, 8, 30), (ox + sign * 16, 5, 41), 1, pad=(0, 0, 1))
        draw_6conn_line(grid, (ox + sign * 12, 6, 37), (ox + sign * 16, 5, 41), 4)
        draw_6conn_line(grid, (ox + sign * 3, 8, 26), (ox + sign * 13, 5, 32), 8)
    # Shoulders, Arms & Jade Sage Sword
    fill_sym_box(grid, 6, 8, 12, 15, 29, 32, 4)
    fill_sym_box(grid, 7, 11, 11, 16, 28, 34, 2)
    fill_sym_box(grid, 8, 11, 11, 16, 34, 34, 1)
    fill_sym_box(grid, 7, 9, 12, 15, 22, 28, 4)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 1)
    fill_box(grid, cx_l - 9, cx_l - 7, 13, 15, 14, 15, 4)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 12, 15, 18, 16, 19, 3)
    sx = cx_r + 13
    fill_box(grid, sx, sx, 17, 18, 14, 19, 3)
    fill_box(grid, sx - 1, sx + 1, 17, 18, 20, 21, 6)
    fill_box(grid, sx, sx, 17, 18, 22, 42, 8)
    fill_box(grid, sx, sx, 18, 18, 24, 39, 9)
    # Hooded Crane-Sage Helm with Red Crown Gem
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 4)
    fill_sym_box(grid, 0, 2, 11, 16, 35, 41, 1)
    fill_sym_box(grid, 1, 2, 16, 17, 38, 39, 9)
    fill_sym_box(grid, 0, 3, 10, 17, 40, 44, 2)
    fill_sym_box(grid, 0, 1, 17, 18, 42, 44, 5)
    hollow_interior_26(grid, 1, Z - 2)
    return grid


def build_c():
    # WHITE CRANE (白い鶴: 丹頂鶴) (40 x 36 x 42)
    grid = np.zeros((40, 36, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    # Mossy Pond Stone Base (Z: 0..2, minZ=0) & Tall Slender Black Crane Legs (Z: 2..15)
    fill_sym_box(grid, 0, 5, 13, 21, 0, 1, 3)
    fill_sym_box(grid, 1, 4, 14, 20, 1, 2, 2)
    fill_sym_box(grid, 2, 2, 17, 18, 2, 15, 4)    # Tall slender black crane legs!
    fill_sym_box(grid, 2, 3, 18, 20, 2, 2, 4)     # Delicate crane feet
    # Graceful Oval Pure-White Crane Body & Black Tail Plumes (Z: 14..23, Y: 10..24)
    fill_sym_box(grid, 0, 4, 13, 23, 15, 22, 1)
    fill_sym_box(grid, 0, 3, 8, 14, 14, 19, 4)    # Iconic black tail/secondary plume!
    # Poised Spread White Wings with Crisp Black Wingtips! (X: 2..37, Z: 19..34)
    for sign in (-1, 1):
        ox = cx_r if sign == 1 else cx_l
        draw_6conn_line(grid, (ox + sign * 3, 18, 20), (ox + sign * 11, 16, 26), 1, pad=(1, 1, 1))
        draw_6conn_line(grid, (ox + sign * 11, 16, 26), (ox + sign * 17, 14, 31), 1, pad=(1, 1, 0))
        for i in range(5):
            fx0 = ox + sign * (6 + i * 2)
            fy0 = 17 - i // 2
            fz0 = 21 + i * 2
            col_f = 4 if i >= 3 else 1
            draw_6conn_line(grid, (fx0, fy0, fz0), (fx0 + sign * 2, fy0 - 5, max(15, fz0 - 6)), col_f, pad=(1, 0, 0))
    # Long Graceful S-Curved Crane Neck, Red Crown (丹頂) & Slender Gold Beak! (Z: 20..41)
    draw_6conn_line(grid, (cx_r, 22, 20), (cx_r, 25, 29), 1, pad=(1, 1, 1))
    draw_6conn_line(grid, (cx_r, 25, 29), (cx_r, 23, 37), 1, pad=(1, 1, 1))
    fill_sym_box(grid, 0, 1, 24, 26, 26, 33, 4)   # Black crane throat stripe!
    fill_sym_box(grid, 0, 2, 22, 27, 36, 40, 1)   # White crane head
    fill_sym_box(grid, 0, 1, 23, 26, 40, 41, 5)   # ICONIC CRIMSON CROWN (丹頂)!
    fill_sym_box(grid, 2, 2, 25, 26, 38, 38, 4)   # Poised dark eyes
    draw_6conn_line(grid, (cx_r, 27, 38), (cx_r, 34, 37), 6)  # Long slender golden crane beak!
    hollow_interior_26(grid, 1, Z - 2)
    return grid
if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "xushu_a.vox")
    v_b = export_vox(model_b, "xushu_b.vox")
    v_c = export_vox(model_c, "xushu_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview_3(
        [
            ("1. XU SHU (CHARACTER)", model_a, v_a, 28, 18),
            ("2. XU SHU ROBOT", model_b, v_b, 28, 18),
            ("3. WHITE CRANE (BEAST)", model_c, v_c, 42, 20),
        ],
        "THREE KINGDOMS #14: XU SHU - CHARACTER / ROBOT / WHITE CRANE",
        "preview_xushu.png",
    )
    print(f"xushu: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
