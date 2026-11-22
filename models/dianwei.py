import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

PALETTE = {
    1: (94, 104, 118, 255),   # Heavy Rhino-Hide Gunmetal Gray
    2: (38, 76, 158, 255),    # Wei Royal Blue Armor
    3: (58, 64, 76, 255),     # Dark Iron Plate
    4: (236, 188, 54, 255),   # Gold Rivets / Trim
    5: (242, 238, 226, 255),  # Massive Ivory Rhino Horn
    6: (184, 36, 44, 255),    # War Sash Crimson
    7: (236, 190, 156, 255),  # Weathered Skin
    8: (24, 26, 34, 255),     # Charcoal Iron
    9: (255, 148, 36, 255),   # Blazing Orange Eye
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
    # Towering Wei Bodyguard Dian Wei with Twin Short Halberds (40x24x42)
    grid = np.zeros((40, 24, 42), dtype=np.uint8)
    fill_sym_box(grid, 1, 5, 9, 14, 0, 2, 8)
    fill_sym_box(grid, 1, 5, 9, 14, 3, 11, 3)
    fill_sym_box(grid, 2, 4, 14, 14, 8, 10, 4)
    # Waist Sash (Crimson + Gold)
    fill_box(grid, 13, 26, 8, 15, 11, 16, 6)
    fill_box(grid, 17, 22, 15, 16, 12, 15, 4)
    # Heavy Plated Chest (Gunmetal + Wei Blue)
    fill_box(grid, 12, 27, 8, 15, 16, 27, 2)
    fill_box(grid, 14, 25, 15, 16, 18, 25, 1)
    fill_box(grid, 17, 22, 16, 16, 20, 24, 4)
    # Hulking Bare Arms & Iron Pauldrons
    fill_sym_box(grid, 8, 10, 9, 14, 23, 27, 3)
    fill_sym_box(grid, 8, 10, 10, 13, 27, 27, 4)
    fill_sym_box(grid, 8, 10, 9, 14, 15, 22, 7)
    fill_sym_box(grid, 8, 10, 10, 14, 14, 15, 3)
    # TWIN SHORT IRON HALBERDS (双鉄戟) - One in Each Hand!
    for hx, side in ((29, 1), (9, -1)):
        fill_box(grid, hx, hx + 1, 13, 14, 8, 32, 3)
        fill_box(grid, hx, hx + 1, 13, 14, 30, 35, 5)
        fill_box(grid, hx + side * 2, hx + side * 2, 13, 14, 26, 30, 5)
        fill_box(grid, hx + side, hx + side, 13, 14, 27, 29, 1)
    # Shaved Fierce Head with Iron Brow-Band
    fill_box(grid, 16, 23, 9, 14, 28, 37, 7)
    fill_box(grid, 17, 18, 14, 14, 32, 33, 9)
    fill_box(grid, 21, 22, 14, 14, 32, 33, 9)
    fill_box(grid, 15, 24, 8, 15, 34, 36, 3)  # heavy iron headband
    fill_box(grid, 19, 20, 14, 15, 35, 37, 4)
    hollow_interior_26(grid, 1, 36)
    return grid


def build_b():
    # Dian Wei Juggernaut Rhino Siege Mecha (48x26x48)
    grid = np.zeros((48, 26, 48), dtype=np.uint8)
    fill_sym_box(grid, 2, 6, 9, 17, 0, 2, 8)
    fill_sym_box(grid, 2, 6, 10, 15, 3, 13, 1)
    fill_sym_box(grid, 3, 5, 15, 16, 10, 14, 4)
    fill_sym_box(grid, 2, 5, 10, 15, 14, 18, 3)
    fill_box(grid, 16, 31, 9, 16, 18, 22, 6)
    fill_box(grid, 21, 26, 16, 17, 18, 22, 4)
    fill_box(grid, 15, 32, 9, 16, 23, 34, 2)
    fill_box(grid, 17, 30, 16, 17, 24, 33, 1)
    fill_box(grid, 21, 26, 17, 18, 26, 31, 9)
    # Massive Riveted Pauldrons & Arms
    fill_sym_box(grid, 9, 13, 9, 16, 29, 36, 1)
    fill_sym_box(grid, 10, 13, 10, 15, 35, 36, 4)
    fill_sym_box(grid, 9, 12, 10, 15, 19, 28, 3)
    fill_sym_box(grid, 9, 12, 11, 16, 16, 18, 8)
    # Twin Mecha Halberd-Axes!
    for hx, side in ((35, 1), (11, -1)):
        fill_box(grid, hx, hx + 1, 16, 17, 8, 36, 3)
        fill_box(grid, hx, hx + 1, 16, 17, 34, 40, 5)
        fill_box(grid, hx + side * 2, hx + side * 3, 16, 17, 29, 34, 5)
        fill_box(grid, hx + side, hx + side, 16, 17, 30, 33, 4)
    # Rhino-Horned Mecha Head!
    fill_box(grid, 20, 27, 10, 15, 35, 42, 1)
    fill_box(grid, 21, 26, 15, 16, 37, 39, 9)
    fill_box(grid, 19, 28, 9, 16, 41, 44, 2)
    draw_6conn_line(grid, (23, 16, 41), (23, 21, 47), 5, pad=(1, 0, 0))
    hollow_interior_26(grid, 1, 43)
    return grid


def build_c():
    # Massive Armored Rhinoceros (犀) (28x44x26)
    grid = np.zeros((28, 44, 26), dtype=np.uint8)
    # 4 Heavy Pillar Rhino Legs
    for lx0, lx1 in ((7, 10), (17, 20)):
        fill_box(grid, lx0, lx1, 23, 27, 0, 2, 8)
        fill_box(grid, lx0, lx1, 23, 27, 3, 10, 1)
        fill_box(grid, lx0, lx1, 7, 11, 0, 2, 8)
        fill_box(grid, lx0, lx1, 7, 11, 3, 10, 1)
    # Armored Segmented Rhino Torso (gunmetal hide plates + dark iron seams)
    fill_box(grid, 7, 20, 7, 28, 9, 19, 1)
    fill_box(grid, 8, 19, 17, 27, 19, 21, 1)  # thick shoulder hump
    # Armor Hide Fold Seams (signature rhino armored plates!)
    fill_box(grid, 7, 20, 14, 14, 10, 19, 3)
    fill_box(grid, 7, 20, 22, 22, 10, 20, 3)
    # Wei Royal-Blue & Gold War Barding on Back
    fill_box(grid, 7, 20, 15, 21, 13, 20, 2)
    fill_box(grid, 8, 19, 16, 20, 20, 20, 4)
    # Low Charging Heavy Rhino Head
    fill_box(grid, 9, 18, 28, 36, 9, 18, 1)
    fill_box(grid, 10, 17, 36, 41, 9, 14, 3)  # massive blunt snout
    fill_box(grid, 9, 9, 33, 34, 14, 15, 9)   # blazing orange eyes
    fill_box(grid, 18, 18, 33, 34, 14, 15, 9)
    # Small Back-Swept Rhino Ears
    fill_box(grid, 9, 10, 29, 31, 18, 20, 3)
    fill_box(grid, 17, 18, 29, 31, 18, 20, 3)
    # ICONIC CURVED IVORY RHINO HORNS (tall front horn + secondary horn)!
    draw_6conn_line(grid, (13, 39, 14), (13, 42, 24), 5, pad=(1, 1, 0))
    fill_box(grid, 13, 14, 42, 43, 23, 25, 5)
    fill_box(grid, 12, 15, 34, 36, 15, 19, 5)  # secondary horn
    # Short Stiff Rhino Tail
    draw_6conn_line(grid, (13, 7, 14), (13, 4, 9), 3, pad=(0, 0, 0))
    hollow_interior_26(grid, 1, 20)
    return grid
if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "dianwei_a.vox")
    v_b = export_vox(model_b, "dianwei_b.vox")
    v_c = export_vox(model_c, "dianwei_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview_3(
        [
            ("1. DIAN WEI (CHARACTER)", model_a, v_a, 28, 18),
            ("2. DIAN WEI ROBOT", model_b, v_b, 28, 18),
            ("3. ARMORED RHINO (BEAST)", model_c, v_c, 46, 20),
        ],
        "THREE KINGDOMS #25: DIAN WEI - CHARACTER / ROBOT / ARMORED RHINO",
        "preview_dianwei.png",
    )
    print(f"dianwei: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
