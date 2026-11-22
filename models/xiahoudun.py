import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

PALETTE = {
    1: (38, 76, 162, 255),    # Wei Royal Blue
    2: (48, 54, 68, 255),     # Dark Steel Armor
    3: (188, 34, 42, 255),    # Fierce Crimson Cloak
    4: (228, 184, 56, 255),   # Wei Gold Trim
    5: (86, 56, 38, 255),     # Deep Bear Brown
    6: (56, 36, 24, 255),     # Dark Umber Fur
    7: (238, 198, 166, 255),  # Warm Skin
    8: (20, 22, 28, 255),     # Jet Black (eyepatch / hair)
    9: (255, 168, 36, 255),   # Blazing Amber Eye
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
    # One-Eyed Fierce Wei General Xiahou Dun (38x22x44)
    grid = np.zeros((38, 22, 44), dtype=np.uint8)
    fill_sym_box(grid, 1, 4, 8, 13, 0, 2, 8)
    fill_sym_box(grid, 1, 4, 8, 13, 3, 12, 2)
    fill_sym_box(grid, 2, 4, 13, 13, 8, 11, 1)
    fill_box(grid, 13, 24, 8, 14, 12, 16, 1)
    fill_box(grid, 17, 20, 14, 14, 9, 16, 4)
    fill_box(grid, 13, 24, 8, 13, 17, 27, 1)
    fill_box(grid, 14, 23, 13, 14, 18, 26, 2)
    fill_box(grid, 16, 21, 14, 14, 21, 24, 4)
    # Flowing Crimson War Cloak
    fill_box(grid, 13, 24, 6, 7, 5, 27, 3)
    # Spiked Pauldrons & Arms
    fill_sym_box(grid, 6, 8, 8, 13, 22, 27, 2)
    fill_sym_box(grid, 6, 8, 9, 12, 27, 28, 4)
    fill_sym_box(grid, 6, 8, 9, 12, 16, 21, 1)
    fill_sym_box(grid, 6, 8, 10, 13, 14, 15, 7)
    # Long Heavy Broad-Saber (朴刀)
    fill_box(grid, 27, 28, 12, 13, 5, 22, 5)
    fill_box(grid, 27, 28, 12, 13, 22, 23, 4)
    fill_box(grid, 27, 29, 13, 13, 24, 39, 2)
    fill_box(grid, 29, 29, 14, 14, 25, 38, 4)
    # Fierce Head with UNMISTAKABLE BLACK EYEPATCH (隻眼)!
    fill_box(grid, 15, 22, 8, 13, 28, 35, 7)
    fill_box(grid, 15, 22, 8, 10, 28, 36, 8)
    fill_box(grid, 15, 17, 13, 14, 31, 33, 8)  # black eyepatch!
    fill_box(grid, 18, 22, 13, 13, 33, 33, 8)  # strap
    fill_box(grid, 20, 21, 13, 13, 31, 32, 9)  # single blazing amber eye!
    fill_box(grid, 14, 23, 7, 14, 35, 37, 1)
    fill_box(grid, 15, 22, 8, 13, 38, 39, 8)
    fill_box(grid, 18, 19, 13, 14, 36, 38, 4)
    draw_6conn_line(grid, (18, 9, 39), (18, 5, 43), 3, pad=(1, 1, 0))
    hollow_interior_26(grid, 1, 38)
    return grid


def build_b():
    # Xiahou Dun One-Eyed Bear-Brute Mecha (46x26x48)
    grid = np.zeros((46, 26, 48), dtype=np.uint8)
    fill_sym_box(grid, 2, 6, 9, 17, 0, 2, 8)
    fill_sym_box(grid, 2, 6, 10, 15, 3, 13, 1)
    fill_sym_box(grid, 2, 6, 15, 16, 10, 14, 4)
    fill_sym_box(grid, 2, 5, 10, 15, 14, 18, 2)
    fill_box(grid, 16, 29, 9, 16, 18, 22, 2)
    fill_box(grid, 21, 24, 16, 17, 18, 22, 4)
    fill_box(grid, 15, 30, 9, 16, 23, 34, 1)
    fill_box(grid, 17, 28, 16, 17, 24, 33, 2)
    fill_box(grid, 20, 25, 17, 18, 26, 31, 4)
    fill_box(grid, 21, 24, 18, 18, 27, 30, 9)
    # Crimson Armored Cape Thruster
    fill_box(grid, 17, 28, 6, 8, 12, 34, 3)
    # Spiked Massive Shoulders & Arms
    fill_sym_box(grid, 8, 12, 9, 16, 29, 36, 2)
    fill_sym_box(grid, 10, 11, 11, 14, 36, 38, 4)
    fill_sym_box(grid, 9, 11, 10, 15, 20, 28, 1)
    fill_sym_box(grid, 9, 11, 11, 16, 17, 19, 8)
    # Giant Mecha Broad-Saber
    fill_box(grid, 33, 35, 15, 17, 8, 22, 2)
    fill_box(grid, 33, 35, 15, 17, 22, 24, 4)
    fill_box(grid, 33, 36, 16, 17, 25, 44, 2)
    fill_box(grid, 36, 36, 17, 17, 26, 43, 9)
    # Asymmetrical One-Eyed Mecha Head!
    fill_box(grid, 19, 26, 10, 15, 35, 42, 1)
    fill_box(grid, 19, 22, 15, 16, 37, 40, 8)
    fill_box(grid, 24, 26, 15, 16, 38, 39, 9)
    fill_box(grid, 18, 27, 9, 16, 42, 44, 2)
    fill_box(grid, 22, 23, 15, 16, 42, 46, 4)
    draw_6conn_line(grid, (22, 11, 44), (22, 6, 47), 3, pad=(1, 1, 0))
    hollow_interior_26(grid, 1, 43)
    return grid


def build_c():
    # Massive One-Eyed Armored Bear (大きな熊) (26x40x26)
    grid = np.zeros((26, 40, 26), dtype=np.uint8)
    # 4 Pillar Bear Legs
    for lx0, lx1 in ((6, 9), (16, 19)):
        fill_box(grid, lx0, lx1, 22, 26, 0, 2, 8)
        fill_box(grid, lx0, lx1, 22, 26, 3, 10, 5)
        fill_box(grid, lx0, lx1, 7, 11, 0, 2, 8)
        fill_box(grid, lx0, lx1, 7, 11, 3, 10, 5)
    # Muscular Bear Torso & Humped Shoulders
    fill_box(grid, 6, 19, 7, 27, 9, 18, 5)
    fill_box(grid, 7, 18, 17, 27, 17, 21, 6)
    fill_box(grid, 8, 17, 9, 25, 18, 19, 6)
    # Wei Royal-Blue & Gold Shoulder Barding + Crimson War Scarf
    fill_box(grid, 6, 19, 19, 25, 14, 20, 1)
    fill_box(grid, 7, 18, 20, 24, 20, 21, 4)
    fill_box(grid, 7, 18, 25, 27, 10, 15, 3)
    # Short Round Bear Tail
    fill_box(grid, 11, 14, 4, 6, 13, 16, 6)
    # Huge Bear Head with Eyepatch & Single Glowing Amber Eye!
    fill_box(grid, 8, 17, 27, 34, 12, 21, 5)
    fill_box(grid, 10, 15, 34, 38, 13, 17, 6)
    fill_box(grid, 12, 13, 38, 39, 16, 17, 8)
    fill_box(grid, 11, 14, 34, 37, 12, 13, 7)
    fill_box(grid, 8, 10, 32, 35, 18, 20, 8)   # black eyepatch!
    fill_box(grid, 16, 17, 33, 34, 18, 19, 9)  # single blazing amber eye!
    fill_box(grid, 8, 10, 28, 30, 21, 23, 6)
    fill_box(grid, 15, 17, 28, 30, 21, 23, 6)
    hollow_interior_26(grid, 1, 22)
    return grid
if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "xiahoudun_a.vox")
    v_b = export_vox(model_b, "xiahoudun_b.vox")
    v_c = export_vox(model_c, "xiahoudun_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview_3(
        [
            ("1. XIAHOU DUN (CHARACTER)", model_a, v_a, 28, 18),
            ("2. XIAHOU DUN ROBOT", model_b, v_b, 28, 18),
            ("3. ARMORED BEAR (BEAST)", model_c, v_c, 44, 20),
        ],
        "THREE KINGDOMS #19: XIAHOU DUN - CHARACTER / ROBOT / ARMORED BEAR",
        "preview_xiahoudun.png",
    )
    print(f"xiahoudun: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
