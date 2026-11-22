import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

PALETTE = {
    1: (250, 118, 68, 255),   # Bright Wu Blossom Coral-Orange
    2: (248, 146, 178, 255),  # Sakura Pink
    3: (212, 46, 72, 255),    # Lively Wu Crimson
    4: (252, 212, 64, 255),   # Sunlit Gold
    5: (250, 246, 242, 255),  # Crisp Ivory Silk
    6: (52, 152, 92, 255),    # Emerald Leaf Stem (butterfly base)
    7: (248, 214, 190, 255),  # Fair Skin
    8: (42, 34, 48, 255),     # Dark Hair / Butterfly Body
    9: (106, 232, 252, 255),  # Sparkling Sky-Cyan
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
    # Lively Young Wu Princess Xiao Qiao with Twin Buns & Twin Fans (36x22x40)
    grid = np.zeros((36, 22, 40), dtype=np.uint8)
    # Cute Boots & Short Layered Petal Skirt
    fill_sym_box(grid, 1, 3, 9, 13, 0, 2, 3)
    fill_sym_box(grid, 1, 3, 9, 13, 3, 7, 5)
    # Flared Blossom Skirt (coral-orange, sakura pink, gold edge)
    fill_box(grid, 12, 23, 8, 14, 7, 13, 1)
    fill_box(grid, 13, 22, 8, 14, 7, 8, 4)
    fill_box(grid, 15, 20, 14, 14, 8, 13, 2)
    # Waist Ribbon & Back Bow
    fill_box(grid, 13, 22, 8, 14, 14, 15, 3)
    fill_box(grid, 15, 20, 6, 7, 11, 16, 2)  # big cute back ribbon bow!
    # Bodice
    fill_box(grid, 14, 21, 9, 13, 16, 25, 1)
    fill_box(grid, 15, 20, 13, 14, 17, 24, 5)
    fill_box(grid, 16, 19, 14, 14, 20, 23, 4)
    # Puffed Sleeves & Arms
    fill_sym_box(grid, 4, 6, 9, 12, 21, 25, 2)
    fill_sym_box(grid, 4, 6, 9, 12, 16, 20, 5)
    fill_sym_box(grid, 4, 6, 10, 13, 14, 15, 7)
    # TWIN BUTTERFLY FANS (双扇) in both hands!
    draw_6conn_line(grid, (24, 14, 15), (30, 14, 22), 2, pad=(1, 0, 1))
    fill_box(grid, 27, 29, 14, 14, 19, 22, 4)
    draw_6conn_line(grid, (11, 14, 15), (5, 14, 22), 2, pad=(1, 0, 1))
    fill_box(grid, 6, 8, 14, 14, 19, 22, 4)
    # Neck & Cheerful Face
    fill_box(grid, 16, 19, 9, 12, 26, 26, 7)
    fill_box(grid, 14, 21, 8, 13, 27, 33, 7)
    fill_box(grid, 14, 21, 8, 10, 27, 34, 8)
    fill_box(grid, 15, 16, 13, 13, 30, 31, 8)
    fill_box(grid, 19, 20, 13, 13, 30, 31, 8)
    fill_box(grid, 14, 21, 7, 13, 34, 36, 8)
    # Iconic Twin Hair Buns (お団子ヘア) with Gold & Pink Ribbons!
    fill_sym_box(grid, 4, 6, 9, 12, 34, 38, 8)
    fill_sym_box(grid, 4, 6, 12, 13, 35, 37, 4)
    fill_sym_box(grid, 5, 6, 8, 9, 31, 34, 2)
    hollow_interior_26(grid, 1, 35)
    return grid


def build_b():
    # Xiao Qiao Butterfly-Wing Mecha (46x26x44)
    grid = np.zeros((46, 26, 44), dtype=np.uint8)
    fill_sym_box(grid, 2, 4, 10, 16, 0, 2, 3)
    fill_sym_box(grid, 2, 4, 10, 15, 3, 13, 5)
    fill_sym_box(grid, 2, 4, 15, 16, 10, 13, 4)
    fill_sym_box(grid, 2, 4, 10, 15, 14, 16, 2)
    # Flared Skirt Armor
    fill_box(grid, 16, 29, 9, 16, 15, 20, 1)
    fill_box(grid, 18, 27, 16, 17, 16, 20, 2)
    fill_box(grid, 21, 24, 17, 17, 16, 19, 4)
    # Chest & Core
    fill_box(grid, 17, 28, 10, 15, 21, 31, 5)
    fill_box(grid, 19, 26, 15, 16, 22, 30, 1)
    fill_box(grid, 21, 24, 16, 17, 24, 28, 9)
    # Graceful Butterfly Wings on Back!
    fill_box(grid, 20, 25, 7, 9, 22, 30, 3)
    for side in (-1, 1):
        cx = 22 if side == -1 else 23
        draw_6conn_line(grid, (cx + side * 3, 7, 29), (cx + side * 18, 4, 40), 1, pad=(1, 0, 2))
        draw_6conn_line(grid, (cx + side * 3, 7, 25), (cx + side * 14, 4, 20), 2, pad=(1, 0, 2))
        draw_6conn_line(grid, (cx + side * 11, 5, 35), (cx + side * 17, 4, 38), 4, pad=(1, 0, 1))
        fill_box(grid, cx + side * 12, cx + side * 13, 5, 5, 33, 35, 9)
    # Shoulders & Arms with Twin Energy Fans
    fill_sym_box(grid, 6, 9, 10, 15, 27, 32, 2)
    fill_sym_box(grid, 7, 9, 10, 15, 19, 26, 5)
    fill_sym_box(grid, 7, 9, 11, 15, 16, 18, 4)
    draw_6conn_line(grid, (31, 16, 17), (38, 16, 24), 2, pad=(1, 0, 1))
    draw_6conn_line(grid, (14, 16, 17), (7, 16, 24), 2, pad=(1, 0, 1))
    # Mecha Head with Twin Bun Sensor Pods
    fill_box(grid, 19, 26, 10, 15, 32, 39, 5)
    fill_box(grid, 20, 25, 15, 16, 34, 36, 9)
    fill_box(grid, 19, 26, 10, 16, 38, 40, 1)
    fill_sym_box(grid, 4, 6, 10, 14, 38, 42, 3)
    fill_sym_box(grid, 4, 6, 14, 14, 39, 41, 4)
    hollow_interior_26(grid, 1, 39)
    return grid


def build_c():
    # Light Graceful Butterfly (軽やかな蝶) alighting on a blossom (44x34x32)
    grid = np.zeros((44, 34, 32), dtype=np.uint8)
    # Emerald Leaf & Blossom Pedestal (z=0..8)
    fill_box(grid, 17, 26, 12, 21, 0, 1, 6)
    fill_box(grid, 20, 23, 15, 18, 2, 7, 6)
    fill_box(grid, 17, 26, 13, 20, 7, 8, 5)   # white flower petals
    fill_box(grid, 19, 24, 15, 18, 8, 9, 4)   # golden flower center
    # Slender Segmented Butterfly Body (dark slate-plum & gold stripes)
    fill_box(grid, 20, 23, 11, 24, 10, 13, 8)
    for sy in (13, 16, 19):
        fill_box(grid, 20, 23, sy, sy, 10, 13, 4)
    # Butterfly Head, Sparkling Cyan Eyes & Delicate Curved Antennae!
    fill_box(grid, 20, 23, 24, 27, 11, 14, 8)
    fill_box(grid, 20, 20, 26, 27, 12, 13, 9)
    fill_box(grid, 23, 23, 26, 27, 12, 13, 9)
    draw_6conn_line(grid, (20, 26, 14), (16, 31, 19), 4, pad=(0, 0, 0))
    draw_6conn_line(grid, (23, 26, 14), (27, 31, 19), 4, pad=(0, 0, 0))
    # WIDE GRACEFUL BUTTERFLY WINGS (Upper Forewings + Lower Hindwings)!
    for side in (-1, 1):
        cx = 20 if side == -1 else 23
        # Forewing (sweeping outward & upward, vibrant coral-orange & sakura-pink with crimson border & gold spots!)
        for step in range(1, 19):
            wx = cx + side * step
            z_bot = 12 + int(step * 0.55)
            z_top = 15 + int(step * 0.85)
            y_back = 15 + int(step * 0.15)
            y_front = 23 + int(step * 0.35)
            if step > 15:
                y_front -= (step - 15) * 2
                z_top -= (step - 15)
            for yy in range(y_back, y_front + 1):
                z_mid = int(round(z_bot + (z_top - z_bot) * (yy - y_back) / max(1, y_front - y_back)))
                col = 1 if (step < 14) else 3
                if yy == y_front or yy == y_back or step >= 17:
                    col = 3  # crimson scalloped border
                elif 7 <= step <= 11 and abs(yy - (y_back + y_front) // 2) <= 2:
                    col = 4  # golden wing jewel
                elif step >= 12 and step <= 14 and abs(yy - (y_back + y_front) // 2) <= 1:
                    col = 9  # sparkling cyan highlight
                elif step < 7:
                    col = 2  # sakura pink inner wing
                fill_box(grid, wx, wx, yy, yy, z_mid, z_mid + 1, col)
        # Hindwing (sweeping outward & slightly back/down, scalloped sakura-pink & gold)
        for step in range(1, 14):
            wx = cx + side * step
            y_back = 7 - int(step * 0.25)
            y_front = 16
            if step > 10:
                y_back += (step - 10) * 2
            z_base = 11 + int(step * 0.25)
            for yy in range(max(2, y_back), y_front + 1):
                col = 2
                if yy <= max(2, y_back) + 1 or step >= 12:
                    col = 3
                elif 5 <= step <= 8 and 9 <= yy <= 12:
                    col = 4
                fill_box(grid, wx, wx, yy, yy, z_base, z_base + 1, col)
    return grid
if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "xiaoqiao_a.vox")
    v_b = export_vox(model_b, "xiaoqiao_b.vox")
    v_c = export_vox(model_c, "xiaoqiao_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview_3(
        [
            ("1. XIAO QIAO (CHARACTER)", model_a, v_a, 28, 18),
            ("2. XIAO QIAO ROBOT", model_b, v_b, 28, 18),
            ("3. BUTTERFLY (BEAST)", model_c, v_c, 34, 24),
        ],
        "THREE KINGDOMS #22: XIAO QIAO - CHARACTER / ROBOT / BUTTERFLY",
        "preview_xiaoqiao.png",
    )
    print(f"xiaoqiao: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
