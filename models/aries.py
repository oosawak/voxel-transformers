import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

PALETTE = {
    1: (246, 198, 52, 255),   # Golden Fleece Gold
    2: (250, 240, 212, 255),  # Warm Ivory Wool / Face
    3: (196, 134, 34, 255),   # Burnished Horn Bronze
    4: (34, 52, 108, 255),    # Celestial Midnight Navy
    5: (204, 42, 54, 255),    # Star-Gem Crimson
    6: (34, 34, 44, 255),     # Dark Hooves / Frame
    7: (82, 232, 255, 255),   # Starlight Cyan Eye
    8: (255, 228, 108, 255),  # Bright Star Gold Highlight
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


def render_preview(forms, title_banner, out_path):
    n = len(forms)
    cw, ch = 48 + n * 398 + (n - 1) * 16, 540
    canvas = Image.new("RGBA", (cw, ch), (18, 22, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, cw, 20):
        draw.line([(gx, 0), (gx, ch)], fill=(26, 32, 50, 255), width=1)
    for gy in range(0, ch, 20):
        draw.line([(0, gy), (cw, gy)], fill=(26, 32, 50, 255), width=1)
    draw.text((24, 16), title_banner, fill=(224, 232, 255, 255))
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(forms):
        bx, by, w, h = 24 + idx * 414, 48, 398, 468
        draw.rectangle([bx, by, bx + w, by + h], fill=(12, 16, 26, 255), outline=(72, 88, 126, 255), width=2)
        draw.text((bx + 14, by + 12), label, fill=(242, 245, 255, 255))
        gx, gy, gz = m_grid.shape
        draw.text((bx + 14, by + 30), f"Grid: {gx}x{gy}x{gz} | Voxels: {v_cnt}", fill=(142, 168, 212, 255))
        r_front = render_voxel_iso(m_grid, yaw_deg=yaw, pitch_deg=pitch, img_size=(386, 266), margin=12)
        canvas.paste(r_front, (bx + 6, by + 48), r_front)
        rx0, ry0 = bx + 242, by + 318
        draw.rectangle([rx0, ry0, rx0 + 146, ry0 + 140], fill=(18, 22, 34, 255), outline=(54, 68, 96, 255))
        r_rear = render_voxel_iso(m_grid, yaw_deg=yaw + 170, pitch_deg=pitch, img_size=(140, 120), margin=8)
        canvas.paste(r_rear, (rx0 + 3, ry0 + 16), r_rear)
        draw.text((rx0 + 8, ry0 + 5), "REAR VIEW", fill=(128, 148, 186, 255))
        draw.text((bx + 14, by + 406), f"Z-Slices: {gz} layers", fill=(166, 186, 220, 255))
        for pi in range(1, len(PALETTE) + 1):
            px0, py0 = bx + 14 + (pi - 1) * 20, by + 430
            draw.rectangle([px0, py0, px0 + 15, py0 + 15], fill=PALETTE[pi], outline=(76, 90, 118, 255))
    canvas.save(out_path)

def build_a():
    # Golden-Fleece Ram (金色の毛の牡羊) (28x42x28)
    grid = np.zeros((28, 42, 28), dtype=np.uint8)
    # 4 Sturdy Ram Legs (dark hooves + ivory shins + golden wool upper)
    for lx0, lx1 in ((8, 10), (17, 19)):
        fill_box(grid, lx0, lx1, 24, 26, 0, 2, 6)
        fill_box(grid, lx0, lx1, 24, 26, 3, 9, 2)
        fill_box(grid, lx0, lx1, 10, 12, 0, 2, 6)
        fill_box(grid, lx0, lx1, 10, 12, 3, 9, 2)
    # Fluffy Golden Fleece Torso (stepped wool tufts for rich fleece texture!)
    fill_box(grid, 7, 20, 10, 27, 9, 18, 1)
    fill_box(grid, 8, 19, 11, 26, 18, 20, 8)
    fill_box(grid, 6, 21, 13, 24, 11, 16, 1)
    # Celestial Midnight-Navy & Crimson Zodiac Star Blanket
    fill_box(grid, 6, 21, 15, 22, 13, 20, 4)
    fill_box(grid, 7, 20, 16, 21, 20, 20, 8)
    fill_box(grid, 12, 15, 17, 20, 20, 21, 5)
    # Fluffy Golden Ram Tail
    fill_box(grid, 12, 15, 6, 9, 14, 17, 8)
    # Proud Woolly Neck & Ivory Ram Head
    fill_box(grid, 9, 18, 26, 31, 13, 22, 1)
    fill_box(grid, 10, 17, 30, 36, 16, 23, 2)
    fill_box(grid, 11, 16, 36, 40, 15, 20, 2)  # ram snout
    fill_box(grid, 12, 15, 40, 40, 16, 17, 6)  # dark nose
    fill_box(grid, 10, 17, 31, 35, 23, 24, 8)  # golden fleece forelock
    fill_box(grid, 10, 10, 34, 35, 19, 20, 7)  # starlight cyan eyes
    fill_box(grid, 17, 17, 34, 35, 19, 20, 7)
    # ICONIC CURLED SPIRAL RAM HORNS wrapping outward, back, down & forward!
    for side in (-1, 1):
        hx = 10 if side == -1 else 17
        pts = [
            (hx, 33, 23),
            (hx + side * 4, 32, 25),
            (hx + side * 7, 29, 24),
            (hx + side * 8, 27, 20),
            (hx + side * 7, 29, 16),
            (hx + side * 5, 34, 16),
            (hx + side * 6, 37, 18),
        ]
        for i in range(len(pts) - 1):
            col = 3 if i % 2 == 0 else 1
            draw_6conn_line(grid, pts[i], pts[i + 1], col, pad=(1, 0, 1))
    hollow_interior_26(grid, 1, 21)
    return grid


def build_b():
    # Aries Golden-Fleece Ram-Horn Robot (48x26x48)
    grid = np.zeros((48, 26, 48), dtype=np.uint8)
    # Armored Boots & Golden-Fleece Greaves (reusing ram hooves & wool!)
    fill_sym_box(grid, 2, 5, 9, 17, 0, 2, 6)
    fill_sym_box(grid, 2, 5, 16, 18, 0, 2, 3)
    fill_sym_box(grid, 2, 5, 10, 15, 3, 13, 1)
    fill_sym_box(grid, 2, 5, 15, 16, 11, 14, 8)
    fill_sym_box(grid, 2, 4, 10, 15, 14, 18, 2)
    # Celestial Navy Waist & Skirt
    fill_box(grid, 17, 30, 9, 16, 18, 22, 4)
    fill_box(grid, 22, 25, 16, 17, 18, 22, 5)
    # Golden Fleece Torso with Ram-Head Chest Emblem!
    fill_box(grid, 16, 31, 9, 16, 23, 34, 1)
    fill_box(grid, 18, 29, 16, 17, 24, 33, 4)
    fill_box(grid, 21, 26, 17, 18, 26, 31, 2)  # ivory ram face chest crest
    fill_box(grid, 22, 25, 18, 18, 27, 29, 5)  # crimson zodiac gem
    # Navy & Gold Celestial Back Cape/Thruster
    fill_box(grid, 18, 29, 6, 8, 18, 34, 4)
    fill_box(grid, 20, 27, 5, 6, 20, 32, 8)
    # GIANT SPIRAL RAM-HORN PAULDRONS (the ram's horns transformed into shoulder armor!)
    fill_sym_box(grid, 8, 12, 9, 16, 29, 36, 1)
    for side in (-1, 1):
        cx = 23 if side == -1 else 24
        pts = [
            (cx + side * 12, 13, 35),
            (cx + side * 16, 12, 39),
            (cx + side * 19, 11, 36),
            (cx + side * 18, 12, 30),
            (cx + side * 15, 15, 31),
        ]
        for i in range(len(pts) - 1):
            draw_6conn_line(grid, pts[i], pts[i + 1], 3 if i % 2 == 0 else 8, pad=(1, 1, 0))
    # Arms & Golden Ram-Horn Scepter/Hammer
    fill_sym_box(grid, 8, 10, 10, 15, 20, 28, 2)
    fill_sym_box(grid, 8, 10, 11, 16, 17, 19, 6)
    fill_box(grid, 33, 34, 16, 17, 10, 38, 3)
    fill_box(grid, 31, 36, 15, 18, 35, 40, 1)
    fill_box(grid, 32, 35, 16, 17, 36, 39, 5)
    # Ram-Horned Celestial Mecha Head
    fill_box(grid, 20, 27, 10, 15, 35, 42, 2)
    fill_box(grid, 21, 26, 15, 16, 37, 39, 7)  # cyan starlight visor
    fill_box(grid, 19, 28, 9, 16, 41, 44, 1)
    draw_6conn_line(grid, (27, 13, 43), (32, 12, 47), 3, pad=(0, 0, 1))
    draw_6conn_line(grid, (20, 13, 43), (15, 12, 47), 3, pad=(0, 0, 1))
    hollow_interior_26(grid, 1, 42)
    return grid
if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    v_a = export_vox(model_a, "aries_a.vox")
    v_b = export_vox(model_b, "aries_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        [
            ("1. GOLDEN RAM", model_a, v_a, 45, 20),
            ("2. ARIES ROBOT", model_b, v_b, 28, 18),
        ],
        "ZODIAC #01: ARIES - GOLDEN RAM / ARIES ROBOT",
        "preview_aries.png",
    )
    print(f"aries: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b})")
