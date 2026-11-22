import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

PALETTE = {
    1: (62, 198, 234, 255),   # Aqua-Silver Fish (Fish 1)
    2: (242, 102, 132, 255),  # Coral-Rose Fish (Fish 2)
    3: (248, 206, 58, 255),   # Golden Zodiac Ribbon Cord (結ぶ紐)
    4: (28, 52, 112, 255),    # Deep Starry Ocean Wave Base
    5: (146, 244, 255, 255),  # Sparkling Cyan Fin Glow
    6: (248, 246, 250, 255),  # Pearl Belly / Star Foam
    7: (250, 168, 192, 255),  # Soft Rose Fin Highlight
    8: (30, 34, 48, 255),     # Dark Eye / Joint Slate
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
    # Two Celestial Fishes Tied Together by a Golden Ribbon Cord (結ばれた2匹の魚) (44x32x34)
    grid = np.zeros((44, 32, 34), dtype=np.uint8)
    # Starry Ocean Wave Crest Base (z=0..5)
    fill_box(grid, 8, 35, 10, 22, 0, 2, 4)
    fill_box(grid, 10, 33, 12, 20, 3, 4, 1)
    fill_box(grid, 14, 29, 13, 19, 4, 5, 6)  # foamy wave crest
    # GOLDEN RIBBON CORD (結ぶ紐) anchored to wave crest (z=4) & tying both fishes' tails together!
    fill_box(grid, 20, 23, 14, 17, 4, 8, 3)  # central golden ribbon knot!
    draw_6conn_line(grid, (20, 16, 7), (10, 16, 11), 3, pad=(0, 0, 1))
    draw_6conn_line(grid, (23, 16, 7), (33, 16, 11), 3, pad=(0, 0, 1))
    # FISH 1 (LEFT — Aqua-Silver & Cyan, leaping upward & curving right at top, x=4..18, z=10..31)
    draw_6conn_line(grid, (10, 16, 11), (6, 16, 18), 1, pad=(2, 2, 1))   # lower body
    draw_6conn_line(grid, (6, 16, 18), (9, 16, 26), 1, pad=(2, 2, 2))    # plump mid body
    draw_6conn_line(grid, (9, 16, 26), (17, 16, 30), 1, pad=(1, 2, 1))   # head curving right!
    fill_box(grid, 7, 11, 15, 17, 20, 25, 6)   # pearl belly highlight
    fill_box(grid, 15, 16, 14, 14, 29, 30, 8)  # fish 1 eye
    fill_box(grid, 15, 16, 18, 18, 29, 30, 8)
    # Fish 1 Flowing Dorsal & Tail Fins (Sparkling Cyan)
    draw_6conn_line(grid, (4, 16, 19), (2, 16, 26), 5, pad=(0, 1, 1))
    draw_6conn_line(grid, (10, 16, 11), (6, 16, 5), 5, pad=(1, 1, 0))
    draw_6conn_line(grid, (10, 16, 11), (13, 16, 6), 5, pad=(0, 1, 0))
    # FISH 2 (RIGHT — Coral-Rose & Pearl, leaping upward & curving left at top, x=25..39, z=10..31)
    draw_6conn_line(grid, (33, 16, 11), (37, 16, 18), 2, pad=(2, 2, 1))
    draw_6conn_line(grid, (37, 16, 18), (34, 16, 26), 2, pad=(2, 2, 2))
    draw_6conn_line(grid, (34, 16, 26), (26, 16, 30), 2, pad=(1, 2, 1))
    fill_box(grid, 32, 36, 15, 17, 20, 25, 6)  # pearl belly highlight
    fill_box(grid, 27, 28, 14, 14, 29, 30, 8)  # fish 2 eye
    fill_box(grid, 27, 28, 18, 18, 29, 30, 8)
    # Fish 2 Flowing Dorsal & Tail Fins (Soft Rose)
    draw_6conn_line(grid, (39, 16, 19), (41, 16, 26), 7, pad=(0, 1, 1))
    draw_6conn_line(grid, (33, 16, 11), (37, 16, 5), 7, pad=(1, 1, 0))
    draw_6conn_line(grid, (33, 16, 11), (30, 16, 6), 7, pad=(0, 1, 0))
    # Upper Golden Constellation Ribbon Arc echoing the Pisces knot!
    draw_6conn_line(grid, (11, 16, 16), (21, 16, 19), 3, pad=(0, 0, 0))
    draw_6conn_line(grid, (21, 16, 19), (32, 16, 16), 3, pad=(0, 0, 0))
    hollow_interior_26(grid, 1, 29)
    return grid


def build_b():
    # Pisces Twin-Fish Finned Ocean Robot (Aqua-Left / Coral-Rose-Right + Golden Ribbon) (48x26x48)
    grid = np.zeros((48, 26, 48), dtype=np.uint8)
    # Harmonious Split Finned Legs (Left Aqua, Right Coral-Rose)
    fill_box(grid, 18, 21, 9, 17, 0, 2, 4)
    fill_box(grid, 26, 29, 9, 17, 0, 2, 4)
    fill_box(grid, 18, 21, 10, 15, 3, 13, 1)
    fill_box(grid, 26, 29, 10, 15, 3, 13, 2)
    fill_box(grid, 17, 17, 11, 14, 5, 12, 5)   # left aqua ankle fin
    fill_box(grid, 30, 30, 11, 14, 5, 12, 7)   # right rose ankle fin
    fill_box(grid, 18, 21, 15, 16, 11, 14, 3)
    fill_box(grid, 26, 29, 15, 16, 11, 14, 3)
    fill_box(grid, 19, 21, 10, 15, 14, 18, 6)
    fill_box(grid, 26, 28, 10, 15, 14, 18, 6)
    # Golden Ribbon Knot Waist & Pearl-Indigo Ocean Torso!
    fill_box(grid, 17, 30, 9, 16, 18, 22, 3)
    fill_box(grid, 17, 23, 9, 16, 23, 34, 1)
    fill_box(grid, 24, 30, 9, 16, 23, 34, 2)
    fill_box(grid, 19, 28, 16, 17, 24, 33, 4)
    fill_box(grid, 21, 26, 17, 18, 26, 31, 3)  # golden Pisces knot core
    fill_box(grid, 22, 25, 18, 18, 27, 30, 5)
    # Flowing Twin Tail-Fin Back Wings & Golden Ribbon Streamers!
    fill_box(grid, 19, 28, 6, 8, 24, 33, 4)
    draw_6conn_line(grid, (19, 7, 30), (5, 4, 41), 5, pad=(1, 0, 1))
    draw_6conn_line(grid, (19, 7, 26), (8, 5, 31), 3, pad=(0, 0, 1))
    draw_6conn_line(grid, (28, 7, 30), (42, 4, 41), 7, pad=(1, 0, 1))
    draw_6conn_line(grid, (28, 7, 26), (39, 5, 31), 3, pad=(0, 0, 1))
    # TWIN FISH-HEAD PAULDRONS (Left Aqua Fish, Right Coral-Rose Fish!) & Arms
    fill_box(grid, 11, 16, 9, 16, 29, 36, 1)
    fill_box(grid, 11, 13, 16, 17, 32, 34, 5)  # aqua fish crest
    fill_box(grid, 31, 36, 9, 16, 29, 36, 2)
    fill_box(grid, 34, 36, 16, 17, 32, 34, 7)  # rose fish crest
    fill_box(grid, 13, 15, 10, 15, 20, 28, 6)
    fill_box(grid, 32, 34, 10, 15, 20, 28, 6)
    fill_box(grid, 13, 15, 11, 16, 17, 19, 3)
    fill_box(grid, 32, 34, 11, 16, 17, 19, 3)
    # Twin Fin-Blades (Left Cyan, Right Rose)!
    draw_6conn_line(grid, (13, 16, 18), (9, 19, 34), 5, pad=(1, 0, 1))
    draw_6conn_line(grid, (34, 16, 18), (38, 19, 34), 7, pad=(1, 0, 1))
    # Finned Crown Mecha Head
    fill_box(grid, 20, 27, 10, 15, 35, 42, 6)
    fill_box(grid, 21, 26, 15, 16, 37, 39, 5)
    fill_box(grid, 19, 23, 9, 16, 41, 43, 1)
    fill_box(grid, 24, 28, 9, 16, 41, 43, 2)
    draw_6conn_line(grid, (20, 12, 43), (15, 10, 47), 5, pad=(0, 0, 0))
    draw_6conn_line(grid, (27, 12, 43), (32, 10, 47), 7, pad=(0, 0, 0))
    fill_box(grid, 23, 24, 15, 16, 42, 45, 3)
    hollow_interior_26(grid, 1, 42)
    return grid
if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    v_a = export_vox(model_a, "pisces_a.vox")
    v_b = export_vox(model_b, "pisces_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        [
            ("1. TIED TWIN FISHES", model_a, v_a, 24, 18),
            ("2. PISCES ROBOT", model_b, v_b, 28, 18),
        ],
        "ZODIAC #12: PISCES - TIED TWIN FISHES / PISCES ROBOT",
        "preview_pisces.png",
    )
    print(f"pisces: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b})")
