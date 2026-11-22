import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Ryu (Jade & Gold Dragon) -> Dragon-Girl Maid Robot (竜娘風)!
# Jade-emerald & radiant gold, horns, dragon wings, long tail, crisp white apron & headdress!
PALETTE = {
    1: (34, 152, 114, 255),   # Rich Jade-Emerald Dragon Scales & Hair (翡翠色)
    2: (20, 98, 76, 255),     # Deep Forest-Jade Maid Dress & Wing Shading
    3: (96, 206, 164, 255),   # Luminous Pale-Jade Scale Highlights & Wing Membrane
    4: (244, 198, 52, 255),   # Radiant Imperial Gold Horns, Trim & Belly Plates (金)
    5: (188, 138, 28, 255),   # Burnished Antique Gold Shading
    6: (248, 248, 244, 255),  # Crisp Pearl-White Apron, Frills & Headdress
    7: (212, 46, 54, 255),    # Imperial Crimson Neck Ribbon & Sash Bow
    8: (252, 226, 208, 255),  # Warm Porcelain Faceplate
    9: (255, 214, 58, 255),   # Glowing Golden-Amber Dragon Eyes
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
# FORM A: RYU (JADE & GOLD WINGED DRAGON) (42 x 50 x 30)
# ============================================================
def build_a():
    grid = np.zeros((42, 50, 30), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 20.5
    cx_l = X // 2 - 1   # 20
    cx_r = X // 2       # 21

    # Graceful Jade Dragon Body with Golden Belly Plates (Y: 16..34, Z: 6..15)
    for y in range(16, 35):
        rx = 3.2 if y < 20 else (3.9 if y <= 30 else 3.2)
        zb = 6 if 21 <= y <= 30 else 7
        zt = 14 if y <= 24 else 15
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                if (dx / rx) ** 2 + ((z - zc) / rz) ** 2 <= 1.0:
                    if z <= zb + 1:
                        col = 4 if (y % 2 == 0) else 5  # Golden dragon belly plates!
                    elif z >= zt - 1 and dx <= 1.2:
                        col = 3  # Luminous jade dorsal scales
                    else:
                        col = 1
                    grid[x, y, z] = col
        if y % 2 == 0:
            fill_sym_box(grid, 0, 0, y, y, zt + 1, zt + 2, 4)  # Golden dorsal spine crest!

    # Four Grounded Clawed Jade Legs (Z: 0..9)
    for ly, fy in [(19, 20), (29, 31)]:
        fill_sym_box(grid, 3, 4, ly - 1, ly + 1, 2, 9, 2)
        fill_sym_box(grid, 3, 4, fy - 1, fy + 2, 0, 1, 1)
        fill_sym_box(grid, 3, 4, fy + 2, fy + 3, 0, 0, 6)  # Pearl white dragon claws!

    # Raised S-Curved Jade Neck with Crimson Maid-Ribbon Collar (Y: 33..40, Z: 11..22)
    neck_pts = [(33, 12), (35, 14), (36, 16), (37, 18), (38, 20)]
    for i, (ny, nz) in enumerate(neck_pts):
        fill_sphere_local(grid, cx, ny, nz, 2.3, 2.2, 2.2, 1)
        fill_sym_box(grid, 0, 1, ny + 1, ny + 2, nz - 2, nz - 1, 4)  # Gold throat plates
    fill_sym_box(grid, 0, 2, 34, 37, 14, 16, 7)  # Imperial crimson collar ribbon!
    fill_sym_box(grid, 0, 1, 37, 38, 14, 15, 6)  # White lace trim

    # Noble Dragon Head, Golden Antler Horns & Glowing Golden Eyes (Y: 38..48, Z: 17..28)
    fill_sym_box(grid, 0, 2, 38, 43, 18, 22, 1)
    fill_sym_box(grid, 0, 1, 43, 48, 18, 21, 1)  # Snout
    fill_sym_box(grid, 0, 1, 42, 47, 17, 18, 4)  # Gold lower jaw
    fill_sym_box(grid, 2, 2, 41, 43, 20, 21, 9)  # Golden dragon eyes!
    # Sweeping Golden Dragon Horns (角!)
    draw_6conn_line(grid, (cx_r + 1, 40, 22), (cx_r + 5, 36, 27), 4)
    draw_6conn_line(grid, (cx_l - 1, 40, 22), (cx_l - 5, 36, 27), 4)
    draw_6conn_line(grid, (cx_r + 3, 38, 25), (cx_r + 4, 39, 28), 4)
    draw_6conn_line(grid, (cx_l - 3, 38, 25), (cx_l - 4, 39, 28), 4)

    # Unfolded Jade & Gold Dragon Wings (翼!) (Z: 12..27)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        def wx(off):
            return bx + sign * off
        spar = [(wx(3), 27, 14), (wx(9), 26, 20), (wx(16), 24, 26), (wx(19), 22, 27)]
        for i in range(len(spar) - 1):
            draw_6conn_line(grid, spar[i], spar[i + 1], 4)
        for xo in range(5, 19):
            u = (xo - 5) / 13.0
            lz = int(round(15 + 11 * u))
            ly = int(round(27 - 4 * u))
            ty = ly - int(round(9 - 2 * u))
            tz = lz - 5
            draw_6conn_line(grid, (wx(xo), ly, lz), (wx(xo), ty, tz), 3 if xo % 3 == 0 else 2, only_empty=True)

    # Long Sweeping Jade & Gold Dragon Tail (長い尾!) (Y: 2..17, Z: 7..17)
    tail_pts = [
        (cx,       16.0, 10.5),
        (cx + 1.5, 13.0,  9.5),
        (cx + 3.5, 10.0,  9.0),
        (cx + 5.0,  7.0, 10.0),
        (cx + 5.5,  4.0, 12.5),
        (cx + 4.5,  2.0, 16.0),
    ]
    for i in range(len(tail_pts) - 1):
        draw_6conn_line(grid, tail_pts[i], tail_pts[i + 1], 1, pad=(1, 0, 0))
        p0, p1 = tail_pts[i], tail_pts[i + 1]
        draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), 4)
    fill_sphere_local(grid, cx + 4.5, 2.0, 16.5, 1.5, 1.5, 1.5, 4)  # Gold tail plume!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: RYU DRAGON-GIRL MAID ROBOT (50 x 28 x 48)
# Gold & Jade, Dragon Horns, Dragon Wings, Long Tail, Crisp White Apron & Headdress!
# ============================================================
def build_b():
    grid = np.zeros((50, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 24
    cx_r = X // 2      # 25

    # --- 1. JADE-AND-GOLD BOOTS & PEARL STOCKINGS (Z: 0..11) ---
    fill_sym_box(grid, 2, 4, 11, 17, 0, 2, 2)     # Deep jade shoes
    fill_sym_box(grid, 2, 4, 16, 18, 0, 1, 4)     # Gold toe trim
    fill_sym_box(grid, 2, 3, 12, 15, 3, 11, 6)    # Pearl-white stockings
    fill_sym_box(grid, 2, 3, 12, 15, 9, 9, 4)     # Gold garter band

    # --- 2. DEEP JADE & GOLD MAID SKIRT + CRISP WHITE APRON & BACK BOW (Z: 10..22) ---
    for z in range(10, 23):
        r_x = 8 - (z - 10) // 3
        r_y = 5 - (z - 10) // 4
        y0, y1 = 13 - r_y, 14 + r_y
        if z == 10:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 6)  # White lace petticoat hem
        elif z == 11:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 4)  # Imperial gold skirt border!
        else:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 2)  # Deep emerald-jade maid skirt!
            ap_w = max(2, r_x - 2)
            fill_sym_box(grid, 0, ap_w, y1, y1, z, z, 6) # Crisp white apron!
    # White waist sash & back bow
    fill_sym_box(grid, 0, 4, 10, 17, 22, 23, 6)
    fill_sym_box(grid, 2, 5, 8, 10, 20, 23, 6)
    fill_sym_box(grid, 0, 1, 8, 9, 21, 22, 7)     # Crimson center knot
    fill_sym_box(grid, 1, 2, 8, 9, 15, 19, 6)

    # LONG JADE & GOLD DRAGON TAIL sweeping gracefully from beneath the skirt!
    tail_b = [
        (cx_r,      9, 16),
        (cx_r + 2,  6, 14),
        (cx_r + 5,  4, 12),
        (cx_r + 9,  3, 12),
        (cx_r + 12, 4, 15),
        (cx_r + 13, 6, 19),
    ]
    for i in range(len(tail_b) - 1):
        draw_6conn_line(grid, tail_b[i], tail_b[i + 1], 1, pad=(0, 0, 1))
        p0, p1 = tail_b[i], tail_b[i + 1]
        draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), 4)
    fill_sphere_local(grid, cx_r + 13, 6, 20, 1.3, 1.3, 1.4, 4)  # Golden tail tuft!

    # --- 3. JADE & GOLD BODICE, WHITE APRON BIB & CRIMSON RIBBON (Z: 23..33) ---
    fill_sym_box(grid, 0, 4, 11, 16, 23, 32, 2)   # Jade maid bodice
    fill_sym_box(grid, 0, 2, 16, 17, 23, 30, 6)   # Crisp white apron bib!
    fill_sym_box(grid, 2, 3, 15, 17, 29, 32, 6)   # White ruffled straps
    fill_sym_box(grid, 2, 3, 10, 11, 24, 32, 6)   # Rear apron straps
    fill_sym_box(grid, 0, 3, 12, 16, 32, 33, 6)   # White collar
    fill_sym_box(grid, 0, 2, 16, 18, 30, 32, 7)   # Imperial crimson neck ribbon!
    fill_sym_box(grid, 0, 0, 18, 18, 31, 31, 4)   # Gold brooch!

    # --- 4. UNFOLDED JADE & GOLD DRAGON WINGS ON BACK! (翼!) (Z: 20..42) ---
    fill_sym_box(grid, 0, 3, 9, 11, 25, 31, 2)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        def wx(off):
            return bx + sign * off
        spar = [(wx(3), 10, 29), (wx(9), 8, 34), (wx(16), 7, 39), (wx(21), 6, 41)]
        for i in range(len(spar) - 1):
            draw_6conn_line(grid, spar[i], spar[i + 1], 4)
            p0, p1 = spar[i], spar[i + 1]
            draw_6conn_line(grid, (p0[0], p0[1], p0[2] - 1), (p1[0], p1[1], p1[2] - 1), 5)
        # Wing membrane ribs in luminous pale jade & deep emerald!
        for xo in range(5, 21):
            u = (xo - 5) / 15.0
            zt = int(round(30 + 11 * u))
            zb = int(round(23 + 4 * u - 3 * np.sin(u * np.pi)))
            ym = 8 if xo < 13 else 7
            draw_6conn_line(grid, (wx(xo), ym, zb), (wx(xo), ym, zt - 1), 3 if xo % 2 == 0 else 1, only_empty=True)

    # --- 5. PUFF SLEEVES & ARMS HOLDING GOLDEN TEA TRAY (Z: 16..33) ---
    fill_sym_box(grid, 5, 7, 12, 15, 28, 32, 2)   # Jade puff sleeves
    fill_sym_box(grid, 5, 7, 12, 15, 27, 27, 6)   # White lace ruffle
    fill_box(grid, cx_l - 7, cx_l - 6, 12, 15, 20, 26, 2)
    fill_box(grid, cx_l - 7, cx_l - 6, 12, 15, 19, 19, 6)  # White cuff
    fill_box(grid, cx_l - 7, cx_l - 6, 13, 15, 17, 18, 8)
    # Right arm (+X): Holding an ornate golden teapot tray!
    fill_box(grid, cx_r + 6, cx_r + 7, 12, 16, 21, 26, 2)
    fill_box(grid, cx_r + 6, cx_r + 8, 15, 18, 20, 22, 6)  # White cuff
    fill_box(grid, cx_r + 7, cx_r + 8, 17, 19, 20, 21, 8)
    fill_box(grid, cx_r + 7, cx_r + 12, 17, 21, 21, 21, 4) # Golden tea tray!
    fill_box(grid, cx_r + 9, cx_r + 10, 18, 20, 22, 24, 3) # Jade porcelain teapot!
    fill_box(grid, cx_r + 9, cx_r + 10, 19, 19, 25, 25, 4) # Gold lid

    # --- 6. DRAGON-GIRL HEAD, JADE HAIR, FRILLY HEADDRESS & GOLDEN DRAGON HORNS! (Z: 33..47) ---
    fill_sym_box(grid, 0, 1, 13, 15, 33, 34, 8)
    fill_sym_box(grid, 0, 3, 11, 16, 34, 41, 1)   # Lush jade-emerald hair!
    fill_sym_box(grid, 0, 3, 10, 11, 26, 39, 1)   # Long flowing jade back hair!
    fill_sym_box(grid, 3, 4, 13, 16, 29, 39, 1)   # Side locks
    # Dragon-Maid Faceplate
    fill_sym_box(grid, 0, 2, 16, 17, 34, 39, 8)
    fill_sym_box(grid, 1, 2, 17, 17, 36, 37, 9)   # Glowing golden dragon eyes!
    fill_sym_box(grid, 0, 0, 17, 17, 36, 37, 8)
    fill_sym_box(grid, 0, 2, 16, 17, 39, 40, 1)   # Jade bangs

    # FRILLY WHITE MAID HEADDRESS (Z: 40..43)
    fill_sym_box(grid, 0, 4, 14, 16, 41, 42, 6)
    fill_sym_box(grid, 0, 3, 15, 16, 42, 43, 6)
    fill_sym_box(grid, 3, 4, 15, 16, 41, 41, 7)   # Crimson side bows

    # RADIANT GOLDEN DRAGON ANTLER HORNS rising gracefully above headdress! (角!) (Z: 41..47)
    draw_6conn_line(grid, (cx_r + 2, 14, 41), (cx_r + 6, 12, 46), 4)
    draw_6conn_line(grid, (cx_r + 4, 13, 44), (cx_r + 5, 14, 47), 4)
    draw_6conn_line(grid, (cx_l - 2, 14, 41), (cx_l - 6, 12, 46), 4)
    draw_6conn_line(grid, (cx_l - 4, 13, 44), (cx_l - 5, 14, 47), 4)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=40, pitch_a=22, yaw_b=26, pitch_b=18):
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
    v_a = export_vox(model_a, "ryu_a.vox")
    v_b = export_vox(model_b, "ryu_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #05: RYU (DRAGON) -> DRAGON-GIRL MAID ROBOT",
        "1. RYU (JADE & GOLD DRAGON)",
        "2. RYU DRAGON MAID ROBOT",
        "preview_ryu.png",
        yaw_a=40, pitch_a=22, yaw_b=26, pitch_b=18,
    )
    print(f"ryu: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
