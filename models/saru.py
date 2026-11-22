import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Saru (Japanese Macaque / Monkey) -> Energetic Long-Armed Maid Robot!
# Monkey ears, long energetic arms, curled tail, lively cheerful pose holding feather duster high!
PALETTE = {
    1: (178, 112, 58, 255),   # Warm Cinnamon-Brown Monkey Fur & Hair
    2: (124, 72, 34, 255),    # Deep Chestnut Fur Shading
    3: (242, 204, 166, 255),  # Soft Warm Tan Monkey Face, Ears & Belly
    4: (216, 56, 42, 255),    # Energetic Vermilion-Red Maid Dress & Ribbons!
    5: (146, 32, 28, 255),    # Deep Crimson Dress Shading & Shoes
    6: (248, 246, 242, 255),  # Crisp Pure-White Apron, Frills & Headdress
    7: (246, 204, 54, 255),   # Bright Sun-Gold Collar Brooch & Trim
    8: (244, 148, 154, 255),  # Cute Macaque Rosy Blush & Cheek Accents
    9: (255, 198, 44, 255),   # Sparkling Amber-Gold Lively Eyes
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
# FORM A: SARU (LIVELY SEATED/PLAYFUL MONKEY) (24 x 36 x 28)
# ============================================================
def build_a():
    grid = np.zeros((24, 36, 28), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 11.5

    # Upright Playful Monkey Torso (Y: 13..24, Z: 3..18)
    fill_sphere_local(grid, cx, 18.0, 9.0, 4.6, 4.8, 5.5, 1)
    fill_sphere_local(grid, cx, 19.5, 13.5, 4.0, 4.0, 4.5, 1)
    # Soft tan monkey belly + Vermilion maid-vest & crisp white trim!
    fill_sym_box(grid, 0, 2, 22, 23, 7, 15, 3)
    fill_sym_box(grid, 0, 4, 15, 22, 12, 16, 4)   # Energetic vermilion monkey vest!
    fill_sym_box(grid, 0, 2, 22, 23, 12, 15, 6)   # Crisp white vest bib
    fill_sym_box(grid, 0, 1, 23, 24, 15, 16, 7)   # Gold pin

    # Grounded Bent Hind Monkey Legs & Feet (Z: 0..7, solidly connected to torso)
    fill_sym_box(grid, 2, 5, 15, 21, 0, 7, 1)
    fill_sym_box(grid, 3, 5, 20, 24, 0, 1, 3)     # Agile monkey feet!

    # LONG ENERGETIC MONKEY ARMS (長い腕!) — Left supporting ground, Right waving high!
    # Left arm (-X) planted playfully forward at z=0
    draw_6conn_line(grid, (7, 19, 15), (5, 24, 8), 1, pad=(1, 1, 0))
    draw_6conn_line(grid, (5, 24, 8), (6, 27, 1), 1, pad=(1, 1, 0))
    fill_box(grid, 5, 7, 26, 29, 0, 1, 3)
    # Right arm (+X) raised cheerfully upward!
    draw_6conn_line(grid, (16, 19, 15), (19, 21, 19), 1, pad=(1, 1, 0))
    draw_6conn_line(grid, (19, 21, 19), (20, 23, 24), 1, pad=(1, 1, 0))
    fill_box(grid, 19, 21, 22, 24, 24, 26, 3)     # Raised playful hand!

    # Expressive Monkey Head, Tan Face Mask & Round Side Ears (Y: 16..27, Z: 17..26)
    fill_sphere_local(grid, cx, 20.5, 21.0, 4.2, 4.2, 4.0, 1)
    fill_sym_box(grid, 0, 3, 23, 25, 18, 22, 3)   # Warm tan monkey face!
    fill_sym_box(grid, 0, 2, 25, 26, 18, 20, 3)   # Cheeky muzzle
    fill_sym_box(grid, 1, 2, 25, 25, 21, 22, 5)
    fill_sym_box(grid, 1, 2, 25, 25, 21, 21, 9)   # Sparkling amber eyes!
    fill_sym_box(grid, 2, 3, 25, 25, 19, 19, 8)   # Rosy macaque blush!
    # Round Monkey Ears on sides of head (猿耳!)
    fill_sym_box(grid, 4, 6, 19, 21, 20, 23, 1)
    fill_sym_box(grid, 5, 6, 21, 21, 21, 22, 3)

    # CURLED PLAYFUL MONKEY TAIL (曲がった尻尾!) spiraling behind body! (Y: 3..14, Z: 6..21)
    tail_pts = [
        (cx,       13,  7),
        (cx + 0.5,  9,  7),
        (cx + 1.0,  6, 10),
        (cx + 1.0,  5, 14),
        (cx + 0.5,  6, 18),
        (cx + 0.0,  9, 20),
        (cx + 0.0, 11, 18),
    ]
    for i in range(len(tail_pts) - 1):
        draw_6conn_line(grid, tail_pts[i], tail_pts[i + 1], 1, pad=(0, 0, 0))

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: SARU ENERGETIC LONG-ARMED MAID ROBOT (44 x 26 x 46)
# Monkey ears, long energetic arms (one raised high!), curled tail, lively stance!
# ============================================================
def build_b():
    grid = np.zeros((44, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21
    cx_r = X // 2      # 22

    # --- 1. ENERGETIC STEPPING STANCE: CRIMSON SHOES & WHITE STOCKINGS (Z: 0..11) ---
    # Dynamic cheerful stepping pose (right leg slightly forward!)
    fill_box(grid, cx_r + 2, cx_r + 4, 12, 18, 0, 2, 5)  # Right shoe stepping forward!
    fill_box(grid, cx_r + 2, cx_r + 3, 13, 16, 3, 11, 6) # Right white stocking
    fill_box(grid, cx_l - 4, cx_l - 2, 9, 15, 0, 2, 5)   # Left shoe stepping back!
    fill_box(grid, cx_l - 3, cx_l - 2, 10, 13, 3, 11, 6) # Left white stocking
    fill_sym_box(grid, 2, 3, 12, 14, 9, 9, 4)

    # --- 2. LIVELY VERMILION MAID SKIRT + CRISP WHITE APRON & CURLED MONKEY TAIL! (Z: 10..22) ---
    for z in range(10, 23):
        r_x = 8 - (z - 10) // 3
        r_y = 5 - (z - 10) // 4
        y0, y1 = 13 - r_y, 14 + r_y
        if z == 10:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 6)  # Crisp white lace hem!
        else:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 4)  # Energetic vermilion maid skirt!
            ap_w = max(2, r_x - 2)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 6) # Crisp white apron!
            if z == 11:
                fill_sym_box(grid, 0, ap_w + 1, y1, y1, z, z, 6)
    # White waist sash & back bow
    fill_sym_box(grid, 0, 4, 10, 17, 22, 23, 6)
    fill_sym_box(grid, 2, 5, 8, 10, 20, 23, 6)
    fill_sym_box(grid, 0, 1, 8, 9, 21, 22, 7)     # Gold center bow knot

    # CURLED PLAYFUL MONKEY TAIL spiraling high behind the maid skirt! (曲がった尻尾!)
    tail_b = [
        (cx_r,      9, 17),
        (cx_r + 2,  6, 15),
        (cx_r + 5,  4, 15),
        (cx_r + 7,  4, 19),
        (cx_r + 6,  5, 23),
        (cx_r + 3,  6, 24),
        (cx_r + 2,  6, 22),
    ]
    for i in range(len(tail_b) - 1):
        draw_6conn_line(grid, tail_b[i], tail_b[i + 1], 1)

    # --- 3. VERMILION MAID BODICE, WHITE APRON BIB & GOLD-PINNED RIBBON (Z: 23..33) ---
    fill_sym_box(grid, 0, 4, 11, 16, 23, 32, 4)   # Vermilion bodice
    fill_sym_box(grid, 0, 2, 16, 17, 23, 30, 6)   # Crisp white apron bib!
    fill_sym_box(grid, 2, 3, 15, 17, 29, 32, 6)   # White ruffled straps
    fill_sym_box(grid, 2, 3, 10, 11, 24, 32, 6)   # Rear straps
    fill_sym_box(grid, 0, 3, 12, 16, 32, 33, 6)   # White collar
    fill_sym_box(grid, 0, 2, 16, 18, 30, 32, 5)   # Deep crimson neck ribbon!
    fill_sym_box(grid, 0, 0, 18, 18, 31, 31, 7)   # Bright gold brooch!

    # --- 4. PUFF SLEEVES & LONG ENERGETIC ARMS (長い腕・元気な姿勢!) (Z: 13..42) ---
    fill_sym_box(grid, 5, 7, 12, 15, 28, 32, 4)   # Vermilion puff sleeves
    fill_sym_box(grid, 5, 7, 12, 15, 27, 27, 6)   # White lace ruffle
    # Left Arm (-X, viewer's right): Long nimble arm swinging cheerfully down & out!
    draw_6conn_line(grid, (cx_l - 7, 13, 27), (cx_l - 10, 13, 21), 1, pad=(1, 1, 0))
    draw_6conn_line(grid, (cx_l - 10, 13, 21), (cx_l - 12, 15, 15), 1, pad=(1, 1, 0))
    fill_box(grid, cx_l - 13, cx_l - 11, 14, 16, 15, 16, 6)  # White lace cuff!
    fill_box(grid, cx_l - 13, cx_l - 11, 14, 16, 13, 14, 3)  # Agile hand!
    # Right Arm (+X, viewer's left): Long arm RAISED CHEERFULLY HIGH waving a fluffy duster!
    draw_6conn_line(grid, (cx_r + 7, 13, 29), (cx_r + 12, 14, 33), 1, pad=(1, 1, 0))
    draw_6conn_line(grid, (cx_r + 12, 14, 33), (cx_r + 15, 16, 39), 1, pad=(1, 1, 0))
    fill_box(grid, cx_r + 14, cx_r + 16, 15, 17, 38, 39, 6)  # White cuff!
    fill_box(grid, cx_r + 14, cx_r + 16, 15, 17, 40, 41, 3)  # Raised cheerful hand!
    draw_6conn_line(grid, (cx_r + 15, 16, 41), (cx_r + 18, 17, 44), 7)  # Gold duster handle
    fill_sphere_local(grid, cx_r + 18.5, 17.5, 44.0, 1.8, 1.8, 1.8, 6)  # White feather duster puff!

    # --- 5. ENERGETIC HEAD, SPIKY CINNAMON HAIR, HEADDRESS & ROUND MONKEY EARS! (Z: 33..45) ---
    fill_sym_box(grid, 0, 1, 13, 15, 33, 34, 3)
    fill_sym_box(grid, 0, 3, 11, 16, 34, 41, 1)   # Lively short spiky cinnamon hair!
    fill_sym_box(grid, 0, 3, 10, 11, 30, 39, 2)   # Back hair
    fill_sym_box(grid, 3, 4, 13, 16, 32, 39, 1)
    # Cheerful Faceplate
    fill_sym_box(grid, 0, 2, 16, 17, 34, 39, 3)
    fill_sym_box(grid, 1, 2, 17, 17, 36, 37, 9)   # Sparkling lively amber eyes!
    fill_sym_box(grid, 0, 0, 17, 17, 36, 37, 3)
    fill_sym_box(grid, 2, 2, 17, 17, 35, 35, 8)   # Cute rosy macaque blush!
    fill_sym_box(grid, 0, 2, 16, 17, 39, 40, 1)   # Bangs

    # FRILLY WHITE MAID HEADDRESS (Z: 40..44)
    fill_sym_box(grid, 0, 4, 14, 16, 41, 42, 6)
    fill_sym_box(grid, 0, 3, 15, 16, 42, 43, 6)
    fill_sym_box(grid, 3, 4, 15, 16, 41, 41, 4)   # Vermilion side bows

    # ROUND MONKEY EARS (猿耳!) on both sides of head! (Z: 36..40)
    fill_sym_box(grid, 4, 6, 13, 15, 36, 40, 1)
    fill_sym_box(grid, 5, 6, 15, 15, 37, 39, 3)   # Tan inner monkey ears!

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=20, yaw_b=26, pitch_b=18):
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
    v_a = export_vox(model_a, "saru_a.vox")
    v_b = export_vox(model_b, "saru_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #09: SARU (MONKEY) -> ENERGETIC MAID ROBOT",
        "1. SARU (PLAYFUL MONKEY)",
        "2. SARU ENERGETIC MAID ROBOT",
        "preview_saru.png",
        yaw_a=38, pitch_a=20, yaw_b=26, pitch_b=18,
    )
    print(f"saru: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
