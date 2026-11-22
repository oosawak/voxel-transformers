import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Nezumi (Rat / Mouse) -> Petite & Nimble Maid Robot!
# Round ears, long slender tail, silver-grey fur -> petite maid hair & dress with crisp white apron/headdress!
PALETTE = {
    1: (186, 192, 204, 255),  # Soft Silver-Grey Mouse Fur & Hair
    2: (126, 134, 150, 255),  # Shaded Slate-Grey Shading & Stockings
    3: (48, 56, 86, 255),     # Deep Navy-Slate Maid Dress & Shoes
    4: (246, 248, 252, 255),  # Crisp Pure-White Apron, Frills & Headdress
    5: (242, 162, 182, 255),  # Soft Rose-Pink Inner Ears, Nose & Long Tail
    6: (218, 56, 88, 255),    # Bright Berry-Crimson Maid Neck Ribbon & Bow
    7: (252, 224, 206, 255),  # Warm Porcelain Faceplate
    8: (244, 198, 62, 255),   # Golden Collar Pin & Cheese-Gold Accent
    9: (255, 112, 148, 255),  # Bright Ruby-Rose Glowing Eyes
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


def fill_sphere_local(grid, cx, cy, cz, rx, ry, rz, col):
    X, Y, Z = grid.shape
    x0 = max(0, int(np.floor(cx - rx)))
    x1 = min(X - 1, int(np.ceil(cx + rx)))
    y0 = max(0, int(np.floor(cy - ry)))
    y1 = min(Y - 1, int(np.ceil(cy + ry)))
    z0 = max(0, int(np.floor(cz - rz)))
    z1 = min(Z - 1, int(np.ceil(cz + rz)))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2 <= 1.0:
                    grid[x, y, z] = col


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


# ============================================================
# FORM A: NEZUMI (PETITE NIMBLE MOUSE) (22 x 44 x 20)
# ============================================================
def build_a():
    grid = np.zeros((22, 44, 20), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 10.5

    # Plump, nimble teardrop mouse body (Y: 16..34, Z: 2..13)
    body_slices = [
        (16, 3.2, 4, 10),
        (17, 4.2, 3, 11),
        (18, 4.8, 2, 12),
        (19, 5.2, 2, 13),
        (20, 5.4, 2, 13),
        (21, 5.5, 2, 13),
        (22, 5.5, 2, 13),
        (23, 5.3, 2, 13),
        (24, 5.0, 2, 13),
        (25, 4.7, 2, 12),
        (26, 4.4, 3, 12),
        (27, 4.0, 3, 12),
        (28, 3.8, 3, 12),
        (29, 3.7, 4, 12),
        (30, 3.6, 4, 12),
    ]
    for y, rx, zb, zt in body_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    if z <= zb + 1 and dx <= rx * 0.7:
                        col = 4  # Crisp white mouse underbelly (becomes apron!)
                    elif z >= zt - 1 and dx <= 1.5:
                        col = 2  # Slate-grey dorsal stripe
                    else:
                        col = 1  # Soft silver-grey mouse fur
                    grid[x, y, z] = col

    # Navy maid-saddle cape & crimson ribbon around neck (shared with maid robot!)
    fill_sym_box(grid, 0, 4, 22, 27, 11, 13, 3)   # Navy capelet
    fill_sym_box(grid, 0, 4, 22, 27, 10, 10, 4)   # White lace cape trim
    fill_sym_box(grid, 0, 3, 28, 30, 6, 12, 6)    # Berry-crimson ribbon collar!
    fill_sym_box(grid, 0, 1, 30, 31, 6, 7, 8)     # Gold charm pin!

    # Four nimble pink mouse paws grounded at z=0 (connected solidly into belly)
    for py, x_off in [(19, 3), (27, 3)]:
        fill_sym_box(grid, x_off - 1, x_off + 1, py - 1, py + 2, 0, 4, 2)
        fill_sym_box(grid, x_off - 1, x_off + 1, py + 1, py + 3, 0, 1, 5)  # Cute pink toes!

    # Cute pointed mouse head & pink nose (Y: 30..41, Z: 5..14)
    fill_sphere_local(grid, cx, 33.0, 9.0, 3.6, 4.0, 3.5, 1)
    fill_sym_box(grid, 0, 2, 36, 39, 6, 9, 1)
    fill_sym_box(grid, 0, 1, 39, 41, 6, 8, 1)
    fill_sym_box(grid, 0, 0, 41, 42, 7, 8, 5)     # Cute pink mouse nose!
    fill_sym_box(grid, 0, 1, 35, 39, 5, 6, 4)     # White cheek/chin
    # Bright glowing ruby-rose mouse eyes (embedded cleanly on head!)
    fill_sym_box(grid, 2, 2, 35, 37, 9, 10, 3)
    fill_sym_box(grid, 2, 2, 36, 37, 9, 10, 9)

    # ICONIC BIG ROUND MOUSE EARS (丸い耳!) with soft pink inner discs (Z: 11..18)
    for sign in (-1, 1):
        ex = cx + sign * 4.2
        fill_sphere_local(grid, ex, 31.5, 14.5, 2.8, 1.3, 3.0, 1)
        fill_sphere_local(grid, ex, 32.3, 14.5, 1.8, 0.8, 2.0, 5)  # Rose-pink inner ear!

    # LONG SLENDER CURVING PINK MOUSE TAIL (長い尻尾!) (Y: 2..17, Z: 2..11)
    tail_pts = [
        (cx,       16, 6),
        (cx + 0.5, 13, 5),
        (cx + 2.0, 10, 4),
        (cx + 3.5,  7, 4),
        (cx + 4.5,  4, 6),
        (cx + 3.5,  2, 9),
        (cx + 2.0,  2, 11),
    ]
    for i in range(len(tail_pts) - 1):
        draw_6conn_line(grid, tail_pts[i], tail_pts[i + 1], 5)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: NEZUMI PETITE MAID ROBOT (34 x 24 x 40)
# ============================================================
def build_b():
    grid = np.zeros((34, 24, 40), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 16
    cx_r = X // 2      # 17

    # --- 1. PETITE MARY-JANE SHOES & SLATE STOCKINGS (Z: 0..10) ---
    fill_sym_box(grid, 2, 4, 10, 15, 0, 1, 3)     # Navy maid shoes
    fill_sym_box(grid, 2, 4, 14, 16, 0, 1, 3)     # Rounded toes
    fill_sym_box(grid, 2, 4, 11, 14, 2, 2, 4)     # White ankle socks ruffle
    fill_sym_box(grid, 2, 3, 11, 14, 3, 10, 2)    # Slate-grey tights / nimble legs!
    fill_sym_box(grid, 2, 3, 14, 14, 7, 8, 4)     # White knee-sock stripe

    # --- 2. FLARED NAVY MAID SKIRT + CRISP WHITE APRON & BACK BOW (Z: 9..19) ---
    for z in range(9, 20):
        # Cute petite A-line bell-skirt flare!
        r_x = 7 - (z - 9) // 3
        r_y = 5 - (z - 9) // 4
        y0, y1 = 12 - r_y, 13 + r_y
        if z == 9:
            # Frilly white lace petticoat hem!
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 4)
        else:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 3)  # Deep navy maid skirt
            # Crisp WHITE APRON draping down front of skirt!
            ap_w = max(2, r_x - 2)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 4)
            if z == 10:
                fill_sym_box(grid, 0, ap_w + 1, y1, y1, z, z, 4)  # White apron ruffle edge!
    # Big Crisp White Apron Sash & Maid Back-Bow! (clearly visible in REAR VIEW)
    fill_sym_box(grid, 0, 4, 9, 16, 19, 20, 4)    # White waist sash
    fill_sym_box(grid, 2, 4, 7, 9, 17, 20, 4)     # Big fluffy white back bow loops!
    fill_sym_box(grid, 0, 1, 7, 8, 18, 19, 6)     # Crimson center bow knot
    fill_sym_box(grid, 1, 2, 7, 8, 13, 16, 4)     # Hanging white bow ribbons

    # LONG SLENDER PINK MOUSE TAIL curving lively out from under the back bow!
    tail_b = [
        (cx_r,     8, 16),
        (cx_r + 1, 5, 14),
        (cx_r + 3, 3, 12),
        (cx_r + 5, 2, 13),
        (cx_r + 6, 3, 16),
        (cx_r + 5, 4, 19),
    ]
    for i in range(len(tail_b) - 1):
        draw_6conn_line(grid, tail_b[i], tail_b[i + 1], 5)

    # --- 3. PETITE MAID BODICE, WHITE APRON BIB & BERRY-CRIMSON NECK RIBBON (Z: 20..28) ---
    fill_sym_box(grid, 0, 3, 10, 15, 20, 22, 3)   # Trim waist bodice
    fill_sym_box(grid, 0, 4, 10, 15, 23, 27, 3)   # Navy maid bodice
    fill_sym_box(grid, 0, 2, 15, 16, 20, 26, 4)   # Crisp white apron bib on chest!
    fill_sym_box(grid, 2, 3, 14, 16, 25, 27, 4)   # White frilled apron shoulder-straps!
    fill_sym_box(grid, 2, 3, 9, 10, 21, 27, 4)    # Rear apron straps
    # White Peter-Pan collar + Iconic Berry-Crimson Neck Ribbon & Gold Pin!
    fill_sym_box(grid, 0, 3, 11, 15, 27, 28, 4)   # White collar
    fill_sym_box(grid, 0, 2, 15, 17, 26, 27, 6)   # Berry-crimson neck ribbon bow!
    fill_sym_box(grid, 0, 0, 17, 17, 26, 26, 8)   # Gold pin

    # --- 4. PUFF SLEEVES, WHITE CUFFS & NIMBLE ARMS (Z: 15..28) ---
    fill_sym_box(grid, 5, 7, 11, 14, 24, 27, 3)   # Navy puff sleeves!
    fill_sym_box(grid, 5, 7, 11, 14, 23, 23, 4)   # White puff-sleeve ruffle
    # Left Arm (-X): Cute nimble bent forearm with white cuff
    fill_box(grid, cx_l - 7, cx_l - 6, 11, 14, 18, 22, 1)
    fill_box(grid, cx_l - 7, cx_l - 6, 11, 14, 17, 17, 4)  # White cuff
    fill_box(grid, cx_l - 7, cx_l - 6, 12, 14, 15, 16, 7)  # Hand
    # Right Arm (+X): Cheerfully holding a miniature silver feather duster!
    fill_box(grid, cx_r + 6, cx_r + 7, 11, 15, 19, 22, 1)
    fill_box(grid, cx_r + 6, cx_r + 8, 14, 17, 18, 20, 4)  # White cuff
    fill_box(grid, cx_r + 7, cx_r + 8, 16, 18, 18, 19, 7)  # Hand
    draw_6conn_line(grid, (cx_r + 8, 17, 18), (cx_r + 10, 19, 25), 8)  # Gold duster handle
    fill_sphere_local(grid, cx_r + 10.5, 19.5, 26.5, 2.0, 2.0, 2.2, 4)  # Fluffy white duster!

    # --- 5. PETITE MAID HEAD, SILVER HAIR, FRILLY WHITE HEADDRESS & BIG ROUND MOUSE EARS! (Z: 28..39) ---
    fill_sym_box(grid, 0, 1, 12, 14, 28, 29, 7)   # Neck
    fill_sym_box(grid, 0, 3, 10, 15, 29, 35, 1)   # Silver-grey bob hair!
    fill_sym_box(grid, 0, 3, 9, 10, 26, 33, 1)    # Cute bob hair back
    fill_sym_box(grid, 3, 4, 12, 15, 27, 34, 1)   # Side hair framing face
    # Cute Maid Robot Faceplate
    fill_sym_box(grid, 0, 2, 15, 16, 29, 33, 7)   # Porcelain face
    fill_sym_box(grid, 1, 2, 16, 16, 31, 32, 9)   # Bright ruby-rose anime eyes!
    fill_sym_box(grid, 0, 0, 16, 16, 31, 32, 7)   # Nose bridge
    fill_sym_box(grid, 2, 2, 16, 16, 30, 30, 5)   # Subtle pink cheek blush!
    fill_sym_box(grid, 0, 2, 15, 16, 34, 34, 1)   # Silver bangs

    # FRILLY WHITE MAID HEADDRESS (カチューシャ型ヘッドドレス!) arching cleanly across crown!
    fill_sym_box(grid, 0, 3, 13, 15, 35, 36, 4)
    fill_sym_box(grid, 0, 2, 14, 15, 36, 37, 4)   # Scalloped frill top
    fill_sym_box(grid, 3, 4, 13, 15, 34, 35, 4)   # Side headdress lace flaps
    fill_sym_box(grid, 3, 3, 15, 15, 35, 35, 6)   # Tiny berry-crimson headdress bows!

    # ICONIC BIG ROUND MOUSE EARS rising proudly behind the maid headdress! (Z: 34..39)
    cx_f = (X - 1) / 2.0
    for sign in (-1, 1):
        ex = cx_f + sign * 4.5
        fill_sphere_local(grid, ex, 12.0, 36.5, 2.6, 1.3, 2.6, 1)
        fill_sphere_local(grid, ex, 12.8, 36.5, 1.6, 0.8, 1.7, 5)  # Rose-pink inner ears!

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
    cx = (xs.min() + xs.max() + 1) / 2.0
    cy = (ys.min() + ys.max() + 1) / 2.0
    cz = (zs.min() + zs.max() + 1) / 2.0
    yaw, pitch = np.radians(yaw_deg), np.radians(pitch_deg)
    cos_y, sin_y = np.cos(yaw), np.sin(yaw)
    cos_p, sin_p = np.cos(pitch), np.sin(pitch)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=42, pitch_a=22, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "nezumi_a.vox")
    v_b = export_vox(model_b, "nezumi_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #01: NEZUMI (MOUSE) -> PETITE MAID ROBOT",
        "1. NEZUMI (MOUSE)",
        "2. NEZUMI MAID ROBOT",
        "preview_nezumi.png",
        yaw_a=42, pitch_a=22, yaw_b=28, pitch_b=18,
    )
    print(f"nezumi: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
