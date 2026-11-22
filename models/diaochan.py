import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

PALETTE = {
    1: (236, 98, 146, 255),   # Graceful Sakura-Rose Dancer Robe
    2: (182, 42, 88, 255),    # Deep Rose-Crimson Skirt & Ribbon Shading
    3: (248, 206, 72, 255),   # Golden Hairpins, Trim & Marten Coat!
    4: (252, 242, 226, 255),  # Crisp Silk-Ivory Sleeves & Marten Throat Patch
    5: (106, 68, 42, 255),    # Rich Sable-Brown Marten Tail & Paws
    6: (255, 168, 198, 255),  # Soft Blossom-Pink Flowing Silk Ribbons (羽衣)
    7: (254, 226, 212, 255),  # Porcelain Fair Face
    8: (36, 30, 42, 255),     # Glossy Dark Hair, Boots & Marten Eyes
    9: (128, 232, 255, 255),  # Sparkling Celestial Eyes & Core
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
    grid = np.zeros((36, 22, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    # Graceful Layered Flowing Dancer Dress (Z: 0..19)
    for z in range(0, 18):
        rw = 6 - (z * 2) // 11
        fill_sym_box(grid, 0, rw, 8, 15, z, z, 1 if z % 3 != 0 else 2)
        if z in (0, 1):
            fill_sym_box(grid, 0, rw, 8, 15, z, z, 3)
        fill_sym_box(grid, 0, 1, 15, 15, z, z, 4)
    fill_sym_box(grid, 0, 4, 8, 15, 17, 19, 3)    # Gold sash waist
    # Slender Bodice & Wide Silk Sleeves (Z: 19..28)
    fill_sym_box(grid, 0, 4, 9, 14, 19, 27, 4)
    fill_sym_box(grid, 1, 3, 14, 15, 20, 26, 1)
    fill_sym_box(grid, 4, 7, 10, 14, 19, 26, 6)   # Wide flowing dancer sleeves
    fill_sym_box(grid, 6, 8, 12, 15, 18, 20, 7)   # Delicate hands
    # ICONIC SWIRLING FLOATING SILK RIBBONS (羽衣) arching over shoulders!
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        draw_6conn_line(grid, (bx + sign * 6, 12, 24), (bx + sign * 11, 10, 32), 6)
        draw_6conn_line(grid, (bx + sign * 11, 10, 32), (bx + sign * 7, 7, 36), 6)
        draw_6conn_line(grid, (bx + sign * 7, 7, 36), (bx + sign * 1, 7, 37), 6)
        draw_6conn_line(grid, (bx + sign * 6, 12, 20), (bx + sign * 10, 9, 12), 1)
    # Fair Head, Twin Court Hair Loops & Golden Hairpins (Z: 28..40)
    fill_sym_box(grid, 0, 1, 10, 13, 28, 29, 7)
    fill_sym_box(grid, 0, 2, 10, 14, 29, 35, 7)
    fill_sym_box(grid, 1, 2, 14, 14, 32, 32, 8)
    fill_sym_box(grid, 0, 3, 9, 14, 34, 37, 8)    # Glossy dark hair
    fill_sym_box(grid, 2, 4, 10, 13, 36, 39, 8)   # Twin high court hair loops!
    fill_sym_box(grid, 3, 5, 11, 12, 38, 39, 3)   # Golden hairpins!
    fill_sym_box(grid, 0, 1, 14, 15, 36, 38, 3)   # Gold forehead ornament
    hollow_interior_26(grid, 1, Z - 2)
    return grid


def build_b():
    grid = np.zeros((46, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    # Slender Feminine Dancer-Mecha Legs (Z: 0..16)
    fill_sym_box(grid, 2, 4, 10, 16, 0, 2, 2)
    fill_sym_box(grid, 2, 4, 11, 15, 3, 15, 4)
    fill_sym_box(grid, 3, 3, 15, 16, 4, 14, 1)
    fill_sym_box(grid, 2, 4, 15, 17, 13, 15, 3)
    # Flared Petal Skirt Armor (Z: 14..22)
    fill_sym_box(grid, 2, 4, 11, 15, 15, 19, 2)
    fill_sym_box(grid, 0, 4, 11, 15, 19, 22, 1)
    fill_sym_box(grid, 1, 6, 15, 17, 14, 21, 1)
    fill_sym_box(grid, 1, 6, 17, 17, 14, 15, 3)
    fill_sym_box(grid, 5, 7, 10, 16, 15, 21, 6)
    fill_sym_box(grid, 0, 5, 9, 10, 14, 21, 2)
    # Sleek Rose-Ivory Chest & Holographic Ribbon-Wing Halo! (Z: 22..43)
    fill_sym_box(grid, 0, 3, 11, 15, 22, 24, 2)
    fill_sym_box(grid, 0, 5, 10, 16, 25, 32, 4)
    fill_sym_box(grid, 0, 3, 16, 17, 26, 31, 1)
    fill_sym_box(grid, 0, 1, 17, 18, 28, 30, 9)
    fill_sym_box(grid, 0, 4, 8, 10, 25, 31, 2)
    for sign in (-1, 1):
        ox = cx_r if sign == 1 else cx_l
        draw_6conn_line(grid, (ox + sign * 3, 9, 29), (ox + sign * 14, 7, 39), 6, pad=(0, 0, 1))
        draw_6conn_line(grid, (ox + sign * 14, 7, 39), (ox + sign * 17, 8, 28), 1, pad=(0, 0, 1))
        draw_6conn_line(grid, (ox + sign * 17, 8, 28), (ox + sign * 12, 9, 19), 6)
    # Petal Pauldrons & Twin Energy Fans
    fill_sym_box(grid, 5, 8, 11, 15, 28, 33, 6)
    fill_sym_box(grid, 6, 9, 12, 15, 32, 33, 3)
    fill_sym_box(grid, 6, 8, 12, 15, 21, 27, 4)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        fill_box(grid, bx + sign * 7, bx + sign * 9, 12, 16, 16, 21, 1)
        fx = bx + sign * 10
        fill_box(grid, fx, fx, 16, 19, 16, 22, 6)
        fill_box(grid, fx, fx, 18, 20, 17, 21, 3)
    # Court-Tiara Dancer Helm with Twin Wing-Loops (Z: 33..44)
    fill_sym_box(grid, 0, 1, 12, 15, 33, 34, 4)
    fill_sym_box(grid, 0, 2, 11, 16, 34, 40, 4)
    fill_sym_box(grid, 1, 2, 16, 17, 37, 38, 9)
    fill_sym_box(grid, 0, 3, 11, 17, 39, 41, 1)
    fill_sym_box(grid, 2, 4, 12, 15, 40, 43, 3)   # Twin gold mecha hair-loops!
    hollow_interior_26(grid, 1, Z - 2)
    return grid


def build_c():
    # GOLDEN MARTEN (貂: テン) (20 x 44 x 24)
    grid = np.zeros((20, 44, 24), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    # 4 Agile Dark Sable-Brown Marten Legs & Paws (Z: 0..8)
    fill_sym_box(grid, 2, 3, 27, 31, 0, 2, 5)
    fill_sym_box(grid, 2, 3, 27, 29, 3, 8, 5)
    fill_sym_box(grid, 2, 3, 12, 16, 0, 2, 5)
    fill_sym_box(grid, 2, 3, 12, 14, 3, 8, 5)
    # Lithe Long Arched Golden-Amber Marten Body (Y: 11..33, Z: 6..15)
    fill_sym_box(grid, 0, 3, 12, 32, 7, 13, 3)    # Sleek golden-yellow marten fur!
    fill_sym_box(grid, 0, 3, 18, 28, 9, 14, 3)    # Graceful arched back
    fill_sym_box(grid, 0, 2, 24, 33, 7, 11, 4)    # Iconic cream-ivory marten throat patch!
    # Diaochan's Sakura-Pink & Gold Silk Ribbon Collar!
    fill_sym_box(grid, 0, 3, 30, 32, 8, 14, 1)
    draw_6conn_line(grid, (cx_r + 3, 30, 12), (cx_r + 6, 25, 15), 6)  # Trailing silk ribbon!
    draw_6conn_line(grid, (cx_l - 3, 30, 12), (cx_l - 6, 25, 15), 6)
    # Long Bushy Sable-Brown Marten Tail (Y: 1..12)
    draw_6conn_line(grid, (cx_r, 11, 11), (cx_r, 5, 14), 5, pad=(2, 1, 1))
    draw_6conn_line(grid, (cx_r, 5, 14), (cx_r, 2, 17), 5, pad=(1, 1, 1))
    # Cute Pointed Marten Head, Rounded Ears & Glossy Dark Eyes (Y: 31..42, Z: 11..22)
    draw_6conn_line(grid, (cx_r, 31, 12), (cx_r, 34, 16), 3, pad=(2, 2, 1))
    fill_sym_box(grid, 0, 3, 32, 38, 13, 19, 3)
    fill_sym_box(grid, 0, 2, 37, 42, 13, 16, 4)   # Cute tapered ivory snout
    fill_sym_box(grid, 0, 0, 41, 42, 15, 16, 8)   # Tiny dark nose
    fill_sym_box(grid, 2, 3, 36, 37, 16, 17, 8)   # Glossy dark eyes
    fill_sym_box(grid, 2, 3, 33, 35, 19, 21, 5)   # Rounded dark-rimmed marten ears!
    hollow_interior_26(grid, 1, Z - 2)
    return grid
if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "diaochan_a.vox")
    v_b = export_vox(model_b, "diaochan_b.vox")
    v_c = export_vox(model_c, "diaochan_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview_3(
        [
            ("1. DIAOCHAN (CHARACTER)", model_a, v_a, 28, 18),
            ("2. DIAOCHAN ROBOT", model_b, v_b, 28, 18),
            ("3. GOLDEN MARTEN (BEAST)", model_c, v_c, 52, 20),
        ],
        "THREE KINGDOMS #13: DIAOCHAN - CHARACTER / ROBOT / GOLDEN MARTEN",
        "preview_diaochan.png",
    )
    print(f"diaochan: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
