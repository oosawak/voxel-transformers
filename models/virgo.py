import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

PALETTE = {
    1: (248, 246, 240, 255),  # Pure Goddess Ivory Chiton / Owl Face
    2: (246, 202, 62, 255),   # Celestial Gold Wings / Wheat Sheaf
    3: (54, 146, 98, 255),    # Wisdom Olive-Emerald
    4: (162, 146, 224, 255),  # Starlight Lavender Sash
    5: (212, 184, 144, 255),  # Owl Cream-Tan Plumage
    6: (118, 84, 56, 255),    # Owl Deep Wisdom Umber
    7: (248, 214, 188, 255),  # Fair Skin
    8: (236, 190, 82, 255),   # Golden Goddess Hair
    9: (76, 198, 252, 255),   # Star-Sapphire Eye
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
    # Winged Maiden Goddess Astraea with Golden Wheat Sheaf (40x22x42)
    grid = np.zeros((40, 22, 42), dtype=np.uint8)
    # Draped Ivory Goddess Gown (z=0..15)
    fill_box(grid, 15, 24, 8, 13, 0, 1, 2)    # golden hem
    fill_box(grid, 15, 24, 8, 13, 2, 14, 1)
    fill_box(grid, 17, 22, 13, 14, 2, 14, 4)  # lavender central drape
    # Emerald-Olive & Gold Waist Sash
    fill_box(grid, 15, 24, 7, 14, 14, 16, 3)
    fill_box(grid, 18, 21, 14, 14, 14, 16, 2)
    # Ivory Chiton Bodice with Gold Clasp
    fill_box(grid, 16, 23, 8, 13, 17, 26, 1)
    fill_box(grid, 17, 22, 13, 14, 18, 25, 4)
    fill_box(grid, 18, 21, 14, 14, 22, 24, 2)
    # Graceful Angelic Celestial Wings on Back!
    fill_box(grid, 17, 22, 6, 7, 19, 25, 2)
    for side in (-1, 1):
        cx = 19 if side == -1 else 20
        draw_6conn_line(grid, (cx + side * 3, 7, 24), (cx + side * 14, 4, 33), 1, pad=(1, 0, 1))
        draw_6conn_line(grid, (cx + side * 3, 7, 20), (cx + side * 12, 4, 24), 2, pad=(1, 0, 0))
        draw_6conn_line(grid, (cx + side * 11, 5, 31), (cx + side * 16, 4, 34), 2, pad=(0, 0, 0))
    # Arms
    fill_sym_box(grid, 4, 6, 9, 12, 22, 26, 1)
    fill_sym_box(grid, 4, 6, 9, 12, 16, 21, 7)
    fill_sym_box(grid, 4, 6, 10, 13, 14, 15, 2)
    # Golden Wheat Sheaf (麦の穂 / Spica!) held in Right Hand
    draw_6conn_line(grid, (26, 13, 12), (28, 14, 28), 3, pad=(0, 0, 0))
    fill_box(grid, 27, 30, 13, 15, 21, 29, 2)  # rich golden wheat head!
    # Olive-Gold Justice Scepter in Left Hand
    fill_box(grid, 11, 12, 13, 14, 8, 28, 2)
    fill_box(grid, 10, 13, 13, 14, 27, 30, 9)  # star Spica gem
    # Goddess Head, Flowing Golden Hair & Laurel Crown
    fill_box(grid, 18, 21, 9, 12, 27, 27, 7)
    fill_box(grid, 16, 23, 8, 13, 28, 34, 7)
    fill_box(grid, 15, 24, 7, 10, 22, 36, 8)   # long flowing golden hair!
    fill_box(grid, 17, 18, 13, 13, 31, 32, 9)  # sapphire eyes
    fill_box(grid, 21, 22, 13, 13, 31, 32, 9)
    fill_box(grid, 15, 24, 8, 14, 35, 37, 2)   # golden laurel crown
    fill_box(grid, 18, 21, 14, 14, 36, 38, 3)  # olive jewel
    hollow_interior_26(grid, 1, 34)
    return grid


def build_b():
    # Virgo Winged Celestial Valkyrie Mecha (48x26x46)
    grid = np.zeros((48, 26, 46), dtype=np.uint8)
    fill_sym_box(grid, 2, 4, 10, 16, 0, 2, 2)
    fill_sym_box(grid, 2, 4, 10, 15, 3, 13, 1)
    fill_sym_box(grid, 2, 4, 15, 16, 10, 13, 3)
    fill_sym_box(grid, 2, 4, 10, 15, 14, 17, 4)
    # Flared Goddess Skirt Armor
    fill_box(grid, 17, 30, 9, 16, 15, 21, 1)
    fill_box(grid, 19, 28, 16, 17, 16, 21, 4)
    fill_box(grid, 22, 25, 17, 17, 16, 20, 3)
    # Ivory & Gold Valkyrie Torso
    fill_box(grid, 18, 29, 10, 15, 22, 32, 1)
    fill_box(grid, 19, 28, 15, 16, 23, 31, 2)
    fill_box(grid, 22, 25, 16, 17, 25, 29, 9)
    # Grand Angelic Wing Array on Back!
    fill_box(grid, 20, 27, 7, 9, 23, 31, 2)
    for side in (-1, 1):
        cx = 23 if side == -1 else 24
        draw_6conn_line(grid, (cx + side * 3, 7, 30), (cx + side * 20, 4, 43), 1, pad=(1, 0, 1))
        draw_6conn_line(grid, (cx + side * 3, 7, 26), (cx + side * 18, 4, 34), 2, pad=(1, 0, 1))
        draw_6conn_line(grid, (cx + side * 11, 5, 37), (cx + side * 21, 4, 44), 2, pad=(0, 0, 0))
    # Shoulders & Arms
    fill_sym_box(grid, 6, 9, 10, 15, 28, 33, 2)
    fill_sym_box(grid, 7, 9, 10, 15, 19, 27, 1)
    fill_sym_box(grid, 7, 9, 11, 15, 16, 18, 3)
    # Golden Spica Justice Lance (Right)
    fill_box(grid, 33, 34, 16, 17, 6, 42, 2)
    fill_box(grid, 32, 35, 15, 18, 37, 44, 9)
    # Winged Tiara Mecha Head
    fill_box(grid, 20, 27, 10, 15, 33, 40, 1)
    fill_box(grid, 21, 26, 15, 16, 35, 37, 9)
    fill_box(grid, 19, 28, 9, 16, 39, 41, 2)
    draw_6conn_line(grid, (23, 14, 41), (17, 13, 45), 2, pad=(0, 0, 0))
    draw_6conn_line(grid, (24, 14, 41), (30, 13, 45), 2, pad=(0, 0, 0))
    hollow_interior_26(grid, 1, 40)
    return grid


def build_c():
    # Celestial Owl of Wisdom (梟) perched on a marble olive-trimmed pillar (34x28x38)
    grid = np.zeros((34, 28, 38), dtype=np.uint8)
    # Ivory Marble & Olive-Emerald Pedestal (z=0..4)
    fill_box(grid, 11, 22, 9, 18, 0, 2, 1)
    fill_box(grid, 12, 21, 10, 17, 3, 4, 3)
    # Golden Owl Talons solidly anchored into plump body
    fill_box(grid, 13, 15, 13, 16, 5, 10, 2)
    fill_box(grid, 18, 20, 13, 16, 5, 10, 2)
    fill_box(grid, 13, 15, 16, 18, 4, 5, 2)
    fill_box(grid, 18, 20, 16, 18, 4, 5, 2)
    # Plump Regal Owl Body (warm ivory breast, cream-tan & umber plumage)
    fill_box(grid, 11, 22, 9, 19, 9, 22, 5)
    fill_box(grid, 12, 21, 17, 20, 10, 21, 1)  # pure ivory wisdom breast
    fill_box(grid, 14, 19, 20, 20, 13, 18, 4)  # lavender-gold breast chevron
    fill_box(grid, 16, 17, 20, 21, 15, 17, 2)
    # Sculpted Folded-Spread Owl Wings flanking torso!
    for side in (-1, 1):
        cx = 16 if side == -1 else 17
        draw_6conn_line(grid, (cx + side * 6, 13, 19), (cx + side * 14, 11, 25), 6, pad=(1, 1, 1))
        draw_6conn_line(grid, (cx + side * 6, 13, 14), (cx + side * 12, 10, 17), 5, pad=(1, 1, 0))
        draw_6conn_line(grid, (cx + side * 11, 11, 23), (cx + side * 15, 11, 27), 2, pad=(0, 0, 0))
    # Short Rounded Owl Tail
    fill_box(grid, 13, 20, 6, 9, 8, 12, 6)
    fill_box(grid, 14, 19, 5, 6, 7, 10, 2)
    # Iconic Round Owl Head, Ivory Facial Disc, Wise Sapphire Eyes & Ear Tufts!
    fill_box(grid, 11, 22, 10, 19, 22, 31, 6)
    fill_box(grid, 12, 21, 18, 20, 23, 30, 1)  # heart-shaped ivory facial disc!
    fill_box(grid, 13, 15, 20, 21, 26, 28, 9)  # big wise star-sapphire owl eyes!
    fill_box(grid, 18, 20, 20, 21, 26, 28, 9)
    fill_box(grid, 16, 17, 20, 22, 24, 26, 2)  # hooked golden owl beak
    # Prominent Golden-Umber Owl Ear Tufts!
    draw_6conn_line(grid, (12, 16, 31), (9, 15, 36), 6, pad=(1, 0, 0))
    draw_6conn_line(grid, (21, 16, 31), (24, 15, 36), 6, pad=(1, 0, 0))
    fill_box(grid, 9, 10, 15, 16, 35, 36, 2)
    fill_box(grid, 23, 24, 15, 16, 35, 36, 2)
    hollow_interior_26(grid, 1, 30)
    return grid
if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "virgo_a.vox")
    v_b = export_vox(model_b, "virgo_b.vox")
    v_c = export_vox(model_c, "virgo_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview(
        [
            ("1. GODDESS ASTRAEA", model_a, v_a, 28, 18),
            ("2. VIRGO ROBOT", model_b, v_b, 28, 18),
            ("3. WISDOM OWL", model_c, v_c, 38, 20),
        ],
        "ZODIAC #06: VIRGO - GODDESS ASTRAEA / VIRGO ROBOT / WISDOM OWL",
        "preview_virgo.png",
    )
    print(f"virgo: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
