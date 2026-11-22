import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

PALETTE = {
    1: (224, 172, 44, 255),   # Veteran Burnished Gold Armor & Hawk Trim
    2: (36, 134, 72, 255),    # Shu Emerald Under-Robe & Wing Accents
    3: (128, 84, 46, 255),    # Rich Golden-Brown Hawk Plumage & Great Bow
    4: (78, 50, 28, 255),     # Deep Umber Wingtips & Quiver
    5: (244, 244, 248, 255),  # Long Veteran White Beard (白髭) & Hawk Breast
    6: (186, 198, 214, 255),  # Steel Arrowheads & Helmet Trim
    7: (244, 208, 184, 255),  # Weathered Veteran Face
    8: (42, 44, 54, 255),     # Dark Boots, Rock Perch & Joints
    9: (255, 224, 58, 255),   # Keen Golden Sharpshooter Eyes (射手の目)!
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
    grid = np.zeros((38, 24, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    # Veteran Boots, Gold-Emerald Armor & Back Quiver (Z: 0..29)
    fill_sym_box(grid, 2, 4, 9, 14, 0, 2, 8)
    fill_sym_box(grid, 2, 4, 10, 14, 2, 13, 2)
    fill_sym_box(grid, 3, 4, 14, 15, 4, 12, 1)
    fill_sym_box(grid, 0, 5, 9, 14, 13, 19, 1)
    fill_sym_box(grid, 0, 5, 14, 15, 17, 19, 3)
    fill_sym_box(grid, 0, 5, 9, 15, 19, 28, 1)    # Burnished gold veteran cuirass
    fill_sym_box(grid, 1, 4, 15, 15, 21, 27, 2)   # Shu emerald chest inlay
    # Full Feathered Quiver on Back (Y: 6..8, Z: 16..31)
    fill_box(grid, cx_l - 3, cx_l + 1, 6, 8, 16, 27, 4)
    for qx in (cx_l - 2, cx_l, cx_l + 1):
        fill_box(grid, qx, qx, 6, 7, 28, 31, 5)   # White arrow fletching!
    # Arms Drawing GREAT WAR BOW (大弓!)
    fill_sym_box(grid, 5, 7, 10, 14, 24, 29, 1)
    fill_box(grid, cx_l - 8, cx_l - 5, 11, 18, 20, 23, 2)
    fill_box(grid, cx_l - 8, cx_l - 7, 18, 20, 21, 22, 7)  # Bow hand!
    bx = cx_l - 9
    draw_6conn_line(grid, (bx, 20, 22), (bx, 18, 34), 3, pad=(0, 1, 0))
    draw_6conn_line(grid, (bx, 20, 22), (bx, 18, 10), 3, pad=(0, 1, 0))
    draw_6conn_line(grid, (bx, 17, 11), (bx, 17, 33), 5)   # Taut bowstring!
    fill_box(grid, cx_r + 5, cx_r + 7, 11, 16, 20, 24, 2)
    fill_box(grid, cx_r + 6, cx_r + 8, 15, 18, 21, 22, 7)
    draw_6conn_line(grid, (cx_r + 7, 17, 22), (bx - 2, 22, 22), 3)  # Nocked arrow!
    fill_box(grid, bx - 3, bx - 2, 22, 22, 22, 22, 6)      # Steel arrowhead!
    # Veteran Head, LONG FLOWING WHITE BEARD & Gold Helmet (Z: 29..40)
    fill_sym_box(grid, 0, 1, 10, 13, 29, 30, 7)
    fill_sym_box(grid, 0, 3, 10, 14, 30, 36, 7)
    fill_sym_box(grid, 1, 2, 14, 15, 33, 33, 9)   # Keen sharpshooter eyes!
    fill_sym_box(grid, 0, 2, 14, 16, 24, 31, 5)   # Flowing white veteran beard!
    fill_sym_box(grid, 0, 1, 15, 16, 20, 24, 5)
    fill_sym_box(grid, 0, 3, 9, 15, 36, 39, 1)    # Gold veteran helm
    fill_sym_box(grid, 0, 1, 10, 14, 39, 41, 2)
    hollow_interior_26(grid, 1, Z - 2)
    return grid


def build_b():
    grid = np.zeros((48, 26, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    # Veteran Gold-Emerald Sniper Mecha Legs
    fill_sym_box(grid, 3, 6, 9, 17, 0, 2, 8)
    fill_sym_box(grid, 3, 6, 10, 17, 1, 3, 1)
    fill_sym_box(grid, 3, 6, 10, 15, 4, 14, 1)
    fill_sym_box(grid, 4, 5, 15, 16, 5, 13, 2)
    fill_sym_box(grid, 3, 6, 15, 17, 12, 15, 6)
    # Waist & Skirt
    fill_sym_box(grid, 3, 5, 10, 15, 15, 19, 8)
    fill_sym_box(grid, 0, 5, 10, 15, 19, 22, 8)
    fill_sym_box(grid, 2, 6, 15, 16, 16, 21, 1)
    fill_sym_box(grid, 2, 6, 16, 16, 16, 17, 2)
    fill_sym_box(grid, 6, 7, 10, 15, 17, 21, 2)
    fill_sym_box(grid, 0, 1, 15, 17, 17, 22, 6)
    # Heavy Archer Cuirass & Twin Quiver-Missile Backpack!
    fill_sym_box(grid, 0, 4, 10, 15, 22, 24, 8)
    fill_sym_box(grid, 0, 7, 9, 16, 25, 33, 1)
    fill_sym_box(grid, 1, 5, 16, 17, 26, 32, 2)
    fill_sym_box(grid, 0, 2, 17, 18, 28, 30, 9)
    fill_sym_box(grid, 2, 5, 6, 9, 22, 34, 4)     # Twin arrow-pod pack
    fill_sym_box(grid, 3, 4, 6, 8, 35, 37, 5)     # Arrow fin tips!
    # Asymmetric Sniper Shoulder Shield & GIANT ENERGY GREATBOW!
    fill_sym_box(grid, 7, 9, 11, 15, 29, 32, 8)
    fill_sym_box(grid, 8, 12, 10, 16, 28, 34, 1)
    fill_box(grid, cx_l - 13, cx_l - 11, 11, 16, 29, 37, 2)  # Left sniper shoulder shield!
    fill_sym_box(grid, 8, 10, 11, 15, 22, 28, 8)
    fill_box(grid, cx_l - 11, cx_l - 8, 12, 18, 17, 22, 1)
    fill_box(grid, cx_r + 8, cx_r + 11, 11, 16, 16, 21, 1)
    # Giant Energy Greatbow mounted on left arm!
    bx = cx_l - 12
    draw_6conn_line(grid, (bx, 18, 20), (bx - 3, 21, 38), 1, pad=(0, 1, 0))
    draw_6conn_line(grid, (bx, 18, 20), (bx - 3, 21, 6), 1, pad=(0, 1, 0))
    draw_6conn_line(grid, (bx - 2, 20, 8), (bx - 2, 20, 36), 9)  # Glowing energy string!
    # Head with Armored White Beard-Guard & Sniper Visor!
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 8)
    fill_sym_box(grid, 0, 3, 11, 16, 35, 42, 1)
    fill_sym_box(grid, 0, 2, 16, 18, 28, 36, 5)   # Armored white beard-plate!
    fill_sym_box(grid, 1, 2, 17, 17, 38, 39, 9)   # Sharpshooter visor!
    fill_sym_box(grid, 0, 3, 15, 18, 40, 42, 2)
    fill_sym_box(grid, 0, 1, 17, 18, 42, 45, 6)
    hollow_interior_26(grid, 1, Z - 2)
    return grid


def build_c():
    # SHARPSHOOTER HAWK (鷹: 射手の目を持つ鷹) (44 x 32 x 36)
    grid = np.zeros((44, 32, 36), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    # Craggy Perch Rock (Z: 0..4, minZ=0) & Golden Talons
    fill_sym_box(grid, 0, 6, 12, 20, 0, 3, 8)
    fill_sym_box(grid, 2, 4, 15, 19, 3, 9, 1)     # Gripping golden hawk talons connected to body!
    # Tail Feathers sloping back
    draw_6conn_line(grid, (cx_r, 14, 11), (cx_r, 4, 5), 4, pad=(2, 1, 0))
    fill_sym_box(grid, 0, 3, 3, 6, 4, 6, 5)
    # Sleek Muscular Hawk Body (Z: 8..22)
    fill_sym_box(grid, 0, 4, 12, 22, 9, 21, 3)    # Golden-brown back
    fill_sym_box(grid, 0, 4, 19, 23, 10, 20, 5)   # Crisp white speckled hawk breast
    fill_sym_box(grid, 1, 3, 22, 23, 14, 19, 2)   # Shu emerald chest collar!
    # Wide Swept Arched Hawk Wings! (X: 2..41, Z: 15..32)
    for sign in (-1, 1):
        ox = cx_r if sign == 1 else cx_l
        draw_6conn_line(grid, (ox + sign * 3, 17, 19), (ox + sign * 11, 15, 27), 3, pad=(1, 1, 1))
        draw_6conn_line(grid, (ox + sign * 11, 15, 27), (ox + sign * 19, 13, 30), 4, pad=(1, 1, 0))
        for i in range(5):
            fx0 = ox + sign * (6 + i * 3)
            fy0 = 16 - i // 2
            fz0 = 21 + (i * 2 if i < 3 else 5 - (i - 3))
            # Tie feather root solidly onto the wing spar
            draw_6conn_line(grid, (ox + sign * (5 + i * 3), 16 - i // 2, min(28, 20 + i * 2)), (fx0, fy0, fz0), 3)
            draw_6conn_line(grid, (fx0, fy0, fz0), (fx0 + sign * 2, fy0 - 5, max(12, fz0 - 7)), 3 if i < 3 else 4, pad=(1, 0, 0))
            if i == 1:
                draw_6conn_line(grid, (fx0, fy0, fz0), (fx0 + sign * 1, fy0 - 3, fz0 - 4), 1)
    # Keen Sharp-Eyed Hawk Head & Hooked Golden Beak! (Z: 21..31)
    fill_sym_box(grid, 0, 3, 17, 24, 22, 29, 3)
    fill_sym_box(grid, 0, 2, 18, 24, 28, 30, 5)   # White veteran hawk crown!
    fill_sym_box(grid, 3, 3, 21, 22, 25, 27, 9)   # Piercing golden sharpshooter eyes!
    fill_sym_box(grid, 0, 1, 24, 28, 24, 26, 1)   # Sharp hooked beak
    fill_sym_box(grid, 0, 0, 27, 28, 22, 24, 1)
    hollow_interior_26(grid, 1, Z - 2)
    return grid
if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "huangzhong_a.vox")
    v_b = export_vox(model_b, "huangzhong_b.vox")
    v_c = export_vox(model_c, "huangzhong_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview_3(
        [
            ("1. HUANG ZHONG (CHARACTER)", model_a, v_a, 28, 18),
            ("2. HUANG ZHONG ROBOT", model_b, v_b, 28, 18),
            ("3. SHARPSHOOTER HAWK (BEAST)", model_c, v_c, 38, 22),
        ],
        "THREE KINGDOMS #12: HUANG ZHONG - CHARACTER / ROBOT / SHARPSHOOTER HAWK",
        "preview_huangzhong.png",
    )
    print(f"huangzhong: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}) | "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}) | "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
