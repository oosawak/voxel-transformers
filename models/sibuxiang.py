import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Sibuxiang (四不象) — Taikobo's mythical steed -> Quadruped Beast-Type Mecha! (鹿のような不思議な獣 -> 獣型のロボ!)
# Combines deer antlers (鹿の角), horse hooves (馬の蹄), ox tail (牛の尾), cloud-celadon fur & Taikobo's saddle!
PALETTE = {
    1: (244, 240, 228, 255),  # Luminous Cream-Ivory Mythical Beast Coat & Armor
    2: (196, 186, 168, 255),  # Warm Sand-Pearl Shading & Mane
    3: (64, 174, 178, 255),   # Celestial Jade-Cyan Cloud Markings & Thruster Trim (matches Taikobo!)
    4: (246, 202, 54, 255),   # Radiant Golden Branched Deer Antlers (鹿の角!) & Saddle Trim
    5: (196, 46, 52, 255),    # Imperial Crimson Taikobo Saddle Blanket
    6: (52, 46, 54, 255),     # Dark Sturdy Hooves & Mechanical Leg Joints
    7: (116, 128, 146, 255),  # Gunmetal Beast-Mecha Skeleton
    8: (224, 152, 86, 255),   # Warm Golden-Tan Ox Tail Tuft & Neck Ruff
    9: (102, 246, 255, 255),  # Luminous Mystical-Cyan Beast Eyes & Cloud-Thruster Core!
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


def draw_stag_antlers(grid, cx_l, cx_r, y_base, z_base, span_x=8, rise_z=10):
    """Draw graceful branched golden stag antlers (鹿の角!)."""
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        draw_6conn_line(grid, (bx + sign * 2, y_base, z_base), (bx + sign * (span_x - 2), y_base - 1, z_base + rise_z * 0.55), 4)
        draw_6conn_line(grid, (bx + sign * (span_x - 2), y_base - 1, z_base + rise_z * 0.55), (bx + sign * span_x, y_base - 2, z_base + rise_z), 4)
        # Forward brow-tine & inner crown-tine!
        draw_6conn_line(grid, (bx + sign * 4, y_base, z_base + rise_z * 0.35), (bx + sign * 5, y_base + 3, z_base + rise_z * 0.65), 4)
        draw_6conn_line(grid, (bx + sign * (span_x - 2), y_base - 1, z_base + rise_z * 0.6), (bx + sign * (span_x - 4), y_base - 1, z_base + rise_z - 1), 4)


# ============================================================
# FORM A: SIBUXIANG MYTHICAL DEER-LIKE BEAST (鹿のような不思議な獣) (32 x 42 x 38)
# ============================================================
def build_a():
    grid = np.zeros((32, 42, 38), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 15
    cx_r = X // 2      # 16

    # --- 1. FOUR GRACEFUL HOOVED LEGS (馬の蹄!) GROUNDED AT Z=0..12 ---
    # Front legs (Y: 25..29)
    fill_sym_box(grid, 2, 4, 25, 28, 0, 2, 6)     # Sturdy dark horse hooves!
    fill_sym_box(grid, 2, 4, 26, 28, 3, 12, 1)    # Cream-white legs
    fill_sym_box(grid, 3, 4, 25, 25, 3, 6, 3)     # Celestial cloud-tufts at fetlocks!
    # Hind legs (Y: 11..15)
    fill_sym_box(grid, 2, 4, 11, 14, 0, 2, 6)
    fill_sym_box(grid, 2, 4, 12, 14, 3, 12, 1)
    fill_sym_box(grid, 3, 4, 11, 11, 3, 6, 3)

    # --- 2. GRACEFUL MYTHICAL BEAST TORSO & TAIKOBO'S SADDLE BLANKET (Z: 11..21) ---
    fill_sym_box(grid, 0, 5, 11, 29, 11, 19, 1)   # Sleek ivory-cream body
    fill_sym_box(grid, 5, 5, 15, 25, 13, 17, 3)   # Celadon-cyan cloud swirls on flanks!
    # Taikobo's Imperial Crimson & Gold Saddle Blanket on Back!
    fill_sym_box(grid, 0, 5, 15, 24, 17, 20, 5)   # Crimson saddle cloth
    fill_sym_box(grid, 0, 5, 15, 24, 17, 17, 4)   # Gold saddle fringe
    fill_sym_box(grid, 0, 3, 17, 22, 20, 21, 4)   # Saddle seat frame
    # Long Flowing Ox Tail with Golden Tuft (牛の尾!) (Y: 3..11)
    tail_a = [(cx_r, 11, 16), (cx_r, 7, 13), (cx_r, 4, 9), (cx_r, 5, 6)]
    for i in range(len(tail_a) - 1):
        draw_6conn_line(grid, tail_a[i], tail_a[i + 1], 2)
    fill_box(grid, cx_l, cx_r + 1, 3, 6, 4, 7, 8)  # Lush tufted ox-tail brush!

    # --- 3. ARCHED NECK, FLUFFY RUFF, GENTLE MYTHICAL FACE & BRANCHED DEER ANTLERS! (Z: 18..37) ---
    fill_sym_box(grid, 0, 3, 25, 31, 18, 25, 1)   # Graceful arched stag neck
    fill_sym_box(grid, 0, 4, 24, 28, 17, 22, 8)   # Fluffy golden-tan neck mane ruff!
    fill_sym_box(grid, 0, 3, 28, 35, 23, 28, 1)   # Gentle mythical deer-head
    fill_sym_box(grid, 0, 2, 35, 39, 23, 26, 1)   # Long deer/horse muzzle!
    fill_sym_box(grid, 0, 1, 39, 39, 24, 25, 6)   # Cute dark nose
    fill_sym_box(grid, 2, 3, 33, 34, 26, 27, 9)   # Wise luminous cyan beast eyes!
    fill_sym_box(grid, 3, 5, 29, 31, 27, 29, 2)   # Long perked donkey-deer ears!
    # ICONIC GRACEFUL BRANCHED GOLDEN DEER ANTLERS (鹿の角!)
    draw_stag_antlers(grid, cx_l, cx_r, y_base=31, z_base=28, span_x=8, rise_z=9)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: SIBUXIANG QUADRUPED BEAST-TYPE MECHA ROBOT (獣型のロボ!) (38 x 48 x 42)
# ============================================================
def build_b():
    grid = np.zeros((38, 48, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 18
    cx_r = X // 2      # 19

    # --- 1. FOUR ARMORED QUADRUPED MECHA-STAG LEGS & HOOF THRUSTERS! (獣型ロボ!) (Z: 0..16) ---
    # Front Armored Legs (Y: 28..34)
    fill_sym_box(grid, 3, 6, 28, 34, 0, 2, 6)     # Heavy armored hoof-feet!
    fill_sym_box(grid, 4, 5, 34, 35, 0, 1, 4)     # Gold hoof-claws
    fill_sym_box(grid, 3, 6, 29, 33, 3, 14, 1)    # Pure-ivory mechanical forelegs!
    fill_sym_box(grid, 4, 5, 33, 34, 4, 12, 3)    # Cyan leg vents
    fill_sym_box(grid, 3, 6, 33, 35, 9, 12, 4)    # Gold articulated knee shields!
    fill_sym_box(grid, 6, 7, 28, 32, 12, 17, 3)   # Armored cyan shoulder-flank pods!
    # Hind Armored Legs (Y: 10..16)
    fill_sym_box(grid, 3, 6, 10, 16, 0, 2, 6)
    fill_sym_box(grid, 4, 5, 16, 17, 0, 1, 4)
    fill_sym_box(grid, 3, 6, 11, 15, 3, 14, 1)    # Heavy hind mecha legs
    fill_sym_box(grid, 4, 5, 15, 16, 4, 12, 3)
    fill_sym_box(grid, 3, 6, 10, 12, 9, 13, 4)    # Gold rear hock joints!
    fill_sym_box(grid, 6, 7, 11, 15, 12, 17, 3)   # Rear hip thruster pods!

    # --- 2. ARMORED QUADRUPED BEAST CHASSIS, CLOUD-THRUSTER FLANKS & SADDLE TURRET! (Z: 11..25) ---
    fill_sym_box(grid, 0, 6, 11, 34, 12, 22, 1)   # Sleek armored quadruped body!
    fill_sym_box(grid, 0, 5, 12, 33, 11, 12, 7)   # Gunmetal under-chassis
    # Glowing Celestial-Cyan Cloud-Jet Thruster Fins on Both Flanks!
    fill_sym_box(grid, 6, 8, 16, 28, 14, 20, 3)   # Cyan wing-thruster pods!
    fill_sym_box(grid, 7, 8, 18, 26, 16, 18, 9)   # Luminous cyan energy cores!
    fill_sym_box(grid, 6, 8, 14, 16, 15, 19, 4)   # Golden rear thruster nozzles!
    # Armored Imperial Crimson & Gold Saddle Cockpit Deck on Back!
    fill_sym_box(grid, 0, 5, 16, 28, 21, 24, 5)   # Crimson armored saddle deck!
    fill_sym_box(grid, 0, 5, 16, 28, 24, 24, 4)   # Gold deck rails
    fill_sym_box(grid, 0, 2, 20, 25, 24, 26, 9)   # Glowing Bagua cockpit canopy!
    # Articulated Mechanical Ox-Tail Whip with Gold Energy Blade! (Y: 2..11)
    tail_b = [(cx_r, 11, 19), (cx_r, 6, 17), (cx_r, 3, 12), (cx_r, 4, 8)]
    for i in range(len(tail_b) - 1):
        draw_6conn_line(grid, tail_b[i], tail_b[i + 1], 7, pad=(1, 0, 0))
    fill_box(grid, cx_l - 1, cx_r + 1, 2, 5, 6, 10, 4)  # Golden mechanical tail-fin!
    fill_box(grid, cx_l, cx_r, 2, 3, 7, 9, 9)           # Cyan tail-tip emitter!

    # --- 3. ARMORED MECHA-STAG NECK, LION-MANE COLLAR, BEAST VISOR HEAD & GIANT ANTLERS! (Z: 18..41) ---
    fill_sym_box(grid, 0, 4, 29, 36, 19, 28, 1)   # Heavy armored curved neck!
    fill_sym_box(grid, 0, 5, 28, 35, 18, 23, 4)   # Golden armored mane collar!
    fill_sym_box(grid, 0, 2, 36, 37, 20, 26, 3)   # Cyan chest radiator grill
    # Sleek Armored Mythical Beast Mecha Head (Z: 25..32)
    fill_sym_box(grid, 0, 4, 33, 40, 25, 31, 1)   # Ivory mecha-stag cranium!
    fill_sym_box(grid, 0, 3, 40, 45, 25, 29, 1)   # Armored angular beast snout!
    fill_sym_box(grid, 0, 2, 41, 45, 24, 25, 7)   # Gunmetal articulated lower jaw!
    fill_sym_box(grid, 0, 3, 39, 41, 28, 30, 7)   # Dark visor housing
    fill_sym_box(grid, 2, 4, 39, 41, 28, 30, 9)   # Luminous cyan beast-mecha optic visor!
    fill_sym_box(grid, 0, 1, 41, 44, 29, 31, 4)   # Golden nose-ridge crest!
    # Armored Swept Sensor Ears!
    fill_sym_box(grid, 4, 6, 34, 37, 29, 32, 3)
    # GIGANTIC ARMORED GOLDEN BRANCHED STAG ANTLER-ANTENNAS (鹿の角装甲!) (Z: 31..41)
    draw_stag_antlers(grid, cx_l, cx_r, y_base=36, z_base=31, span_x=11, rise_z=10)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=44, pitch_a=20, yaw_b=44, pitch_b=20):
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
    v_a = export_vox(model_a, "sibuxiang_a.vox")
    v_b = export_vox(model_b, "sibuxiang_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #21: SIBUXIANG (TAIKOBO'S STEED) -> BEAST-TYPE MECHA",
        "1. SIBUXIANG (MYTHICAL BEAST)",
        "2. SIBUXIANG ROBOT (BEAST MECHA)",
        "preview_sibuxiang.png",
    )
    print(f"sibuxiang: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
