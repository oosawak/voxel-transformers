import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# SERIES FLAGSHIP EXTRA (#13): NEKO (Tuxedo Black Cat) -> Classic Iconic Nekomimi Maid Robot!
# Crafted with extra love & detail as the face of the Zodiac Maid Robot series!
PALETTE = {
    1: (30, 32, 42, 255),     # Glossy Jet-Black Tuxedo Cat Fur, Hair & Victorian Maid Dress
    2: (62, 68, 86, 255),     # Soft Midnight-Slate Sheen & Pleat Shading
    3: (248, 250, 254, 255),  # Crisp Pure-White Cat Paws/Bib, Frilly Apron, Lace & Headdress
    4: (212, 218, 232, 255),  # Delicate Silver-White Lace Shadow & Tea Tray
    5: (224, 42, 62, 255),    # Classic Crimson Cat-Collar Ribbon, Neck Bow & Garters!
    6: (248, 206, 56, 255),   # Radiant Golden Cat Bell (Suzu) & Teacup Trim
    7: (248, 166, 192, 255),  # Soft Sakura-Pink Inner Cat Ears, Nose & Blush
    8: (252, 228, 210, 255),  # Warm Porcelain Faceplate
    9: (68, 236, 148, 255),   # Luminous Emerald-Mint Cat Eyes!
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
# FORM A: NEKO (GRACEFUL SEATED TUXEDO BLACK CAT) (22 x 36 x 28)
# ============================================================
def build_a():
    grid = np.zeros((22, 36, 28), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 10.5

    # Graceful Seated Tuxedo Cat Body (classic elegant upright seated cat silhouette!) (Y: 11..26, Z: 2..18)
    body_slices = [
        (11, 3.8, 2, 10),
        (12, 4.8, 2, 12),
        (13, 5.2, 2, 13),
        (14, 5.4, 2, 14),
        (15, 5.3, 2, 15),
        (16, 5.0, 2, 16),
        (17, 4.7, 2, 16),
        (18, 4.4, 3, 17),
        (19, 4.2, 4, 17),
        (20, 4.0, 5, 17),
        (21, 3.9, 6, 17),
        (22, 3.8, 7, 17),
        (23, 3.6, 8, 17),
    ]
    for y, rx, zb, zt in body_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                if (dx / rx) ** 2 + ((z - zc) / rz) ** 2 <= 1.0:
                    if z >= zt - 1 and dx <= 1.2:
                        col = 2  # Glossy slate-black fur highlight
                    else:
                        col = 1  # Glossy jet-black tuxedo coat
                    grid[x, y, z] = col

    # Crisp Snow-White Tuxedo Chest Bib (becomes maid apron!)
    fill_sym_box(grid, 0, 2, 22, 25, 7, 14, 3)
    fill_sym_box(grid, 0, 1, 25, 25, 9, 13, 3)
    # Classic Crimson Cat Collar Ribbon & Radiant Golden Bell (鈴!)
    fill_sym_box(grid, 0, 3, 19, 24, 15, 17, 5)
    fill_sym_box(grid, 0, 1, 24, 26, 13, 15, 6)   # Golden cat bell!
    fill_sym_box(grid, 0, 0, 26, 26, 13, 13, 1)

    # Seated Hind Haunches & Neat Upright Front Legs with Crisp White "Mitten" Paws! (Z: 0..11)
    fill_sym_box(grid, 3, 5, 12, 19, 0, 5, 1)     # Seated haunches
    fill_sym_box(grid, 3, 5, 18, 21, 0, 1, 3)     # White hind paws!
    fill_sym_box(grid, 2, 3, 21, 24, 2, 11, 1)    # Neat upright front legs!
    fill_sym_box(grid, 2, 3, 22, 26, 0, 2, 3)     # Crisp white tuxedo mitten paws!

    # Adorable Round Tuxedo Cat Head, Pink Nose, Luminous Emerald Eyes & Perky Ears (Y: 19..31, Z: 16..27)
    fill_sphere_local(grid, cx, 23.5, 20.0, 4.4, 4.2, 3.8, 1)
    # Crisp white tuxedo whisker pads & chin!
    fill_sym_box(grid, 0, 2, 26, 28, 17, 19, 3)
    fill_sym_box(grid, 0, 1, 28, 29, 17, 18, 3)
    fill_sym_box(grid, 0, 0, 29, 29, 19, 19, 7)   # Cute sakura-pink cat nose!
    # Luminous Emerald-Mint Cat Eyes!
    fill_sym_box(grid, 2, 3, 26, 27, 20, 21, 2)
    fill_sym_box(grid, 2, 3, 27, 27, 20, 21, 9)
    # Perky Pointed Black Cat Ears with Soft Pink Inner Ears! (Z: 22..27)
    fill_sym_box(grid, 2, 4, 22, 24, 23, 25, 1)
    fill_sym_box(grid, 3, 4, 22, 23, 25, 27, 1)
    fill_sym_box(grid, 3, 3, 24, 24, 23, 25, 7)   # Sakura-pink inner ears!

    # Graceful S-Curved Black Cat Tail with White Tip arching high! (Y: 2..12, Z: 4..20)
    tail_pts = [
        (cx,       11.0,  5.0),
        (cx + 1.0,  8.0,  5.0),
        (cx + 2.5,  5.0,  7.0),
        (cx + 3.0,  3.5, 11.0),
        (cx + 2.5,  3.5, 15.5),
        (cx + 1.5,  4.5, 19.0),
        (cx + 0.5,  6.0, 20.0),
    ]
    for i in range(len(tail_pts) - 1):
        c_t = 3 if i == len(tail_pts) - 2 else 1  # Crisp white cat tail tip!
        draw_6conn_line(grid, tail_pts[i], tail_pts[i + 1], c_t, pad=(0, 0, 0))
    fill_sphere_local(grid, cx + 0.5, 6.0, 20.0, 1.1, 1.1, 1.1, 3)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: NEKO — ICONIC FLAGSHIP NEKOMIMI MAID ROBOT! (44 x 28 x 48)
# Classic Victorian black & crisp-white maid dress, scalloped lace petticoat,
# pleated white frill apron with grand back bow, frilly maid headdress framing perky cat ears,
# crimson bell-ribbon, silver tea tray with golden-rimmed teacup, curling tuxedo cat tail!
# ============================================================
def build_b():
    grid = np.zeros((44, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21
    cx_r = X // 2      # 22

    # --- 1. CLASSIC MARY-JANE SHOES & WHITE OVER-KNEE STOCKINGS WITH CRIMSON GARTERS (Z: 0..12) ---
    fill_sym_box(grid, 2, 4, 11, 17, 0, 2, 1)     # Glossy black Mary-Jane maid shoes
    fill_sym_box(grid, 2, 4, 16, 18, 0, 1, 1)
    fill_sym_box(grid, 2, 4, 12, 16, 2, 2, 3)     # White shoe-strap ruffle
    fill_sym_box(grid, 2, 3, 12, 15, 3, 11, 3)    # Pure-white over-knee stockings!
    fill_sym_box(grid, 2, 3, 12, 15, 9, 9, 5)     # Crimson garter ribbon!

    # --- 2. VOLUMINOUS TIERED VICTORIAN MAID SKIRT + SCALLOPED LACE APRON + GRAND BACK BOW (Z: 10..23) ---
    for z in range(10, 24):
        # Classic graceful flared Victorian maid bell-skirt!
        t = (z - 10) / 13.0
        r_x = int(round(9.5 - 4.5 * (t ** 0.9)))
        r_y = int(round(6.2 - 3.0 * (t ** 0.9)))
        y0, y1 = 13 - r_y, 14 + r_y
        if z == 10:
            # Scalloped pure-white lace petticoat peeking gracefully beneath the black dress!
            for xo in range(0, r_x + 1):
                col_l = 3 if (xo % 2 == 0) else 4
                fill_sym_box(grid, xo, xo, y0, y1, z, z, col_l)
        elif z == 11:
            fill_sym_box(grid, 0, r_x, y0, y1, z, z, 3)  # Crisp white lower lace trim!
        else:
            # Glossy black Victorian skirt with subtle vertical pleat shading!
            for xo in range(0, r_x + 1):
                col_s = 2 if (xo % 3 == 0 and z < 20) else 1
                fill_sym_box(grid, xo, xo, y0, y1, z, z, col_s)
            # Crisp PLEATED WHITE MAID APRON draping smoothly down the front!
            ap_w = max(2, r_x - 3)
            for xo in range(0, ap_w + 1):
                col_a = 4 if (xo == ap_w or (xo % 2 == 1 and z == 12)) else 3
                fill_sym_box(grid, xo, xo, y1, y1 + 1, z, z, col_a)
            if z == 12:
                # Scalloped frilly bottom apron hem!
                fill_sym_box(grid, 0, ap_w + 1, y1, y1 + 1, z, z, 3)

    # Crisp White Waist Sash & GRAND BUTTERFLY BACK MAID BOW! (stunning in REAR VIEW!)
    fill_sym_box(grid, 0, 5, 10, 18, 22, 23, 3)   # Crisp waist band
    fill_sym_box(grid, 2, 6, 7, 10, 20, 24, 3)    # Wide fluffy butterfly back bow wings!
    fill_sym_box(grid, 3, 5, 7, 8, 21, 23, 4)     # Bow fold shading
    fill_sym_box(grid, 0, 1, 7, 9, 21, 22, 5)     # Crimson velvet bow center knot!
    fill_sym_box(grid, 1, 3, 7, 8, 14, 19, 3)     # Flowing back bow ribbon tails!

    # EXPRESSIVE CURLING TUXEDO CAT TAIL arching gracefully out to the side (visible in FRONT & REAR!)
    tail_b = [
        (cx_r,      9, 17),
        (cx_r + 2,  6, 15),
        (cx_r + 5,  4, 15),
        (cx_r + 9,  4, 17),
        (cx_r + 12, 5, 21),
        (cx_r + 13, 7, 25),
        (cx_r + 12, 9, 28),
    ]
    for i in range(len(tail_b) - 1):
        c_t = 3 if i == len(tail_b) - 2 else 1    # White tuxedo cat tail tip!
        draw_6conn_line(grid, tail_b[i], tail_b[i + 1], c_t)
    fill_sphere_local(grid, cx_r + 12, 9, 28, 1.0, 1.0, 1.0, 3)

    # --- 3. CLASSIC VICTORIAN MAID BODICE, FRILLY APRON BIB & CRIMSON BELL-RIBBON! (Z: 23..34) ---
    fill_sym_box(grid, 0, 4, 11, 16, 23, 32, 1)   # Fitted jet-black maid bodice
    fill_sym_box(grid, 0, 2, 16, 17, 23, 30, 3)   # Crisp white apron bib!
    fill_sym_box(grid, 2, 3, 15, 17, 28, 32, 3)   # Frilly white winged apron shoulder-ruffles!
    fill_sym_box(grid, 3, 4, 15, 17, 30, 32, 3)   # Outer shoulder frill flare
    fill_sym_box(grid, 2, 3, 10, 11, 24, 32, 3)   # Rear apron straps
    # Crisp White Maid Collar + ICONIC CRIMSON NECK RIBBON & GOLDEN CAT BELL! (Z: 30..34)
    fill_sym_box(grid, 0, 3, 12, 16, 32, 33, 3)   # White lace collar
    fill_sym_box(grid, 0, 2, 16, 18, 30, 32, 5)   # Classic crimson maid neck ribbon bow!
    fill_sym_box(grid, 0, 1, 18, 19, 30, 31, 6)   # Radiant golden cat bell (suzu)!
    fill_sym_box(grid, 0, 0, 19, 19, 30, 30, 1)

    # --- 4. PUFF SLEEVES, WHITE LACE CUFFS & SILVER TEA TRAY WITH TEACUP! (Z: 17..33) ---
    fill_sym_box(grid, 5, 7, 12, 15, 28, 32, 1)   # Classic black Victorian puff sleeves
    fill_sym_box(grid, 5, 7, 12, 15, 27, 27, 3)   # White lace puff-sleeve ruffle!
    # Left Arm (-X, viewer's right): Graceful poised maid arm lightly holding skirt edge!
    fill_box(grid, cx_l - 8, cx_l - 6, 12, 15, 21, 26, 1)
    fill_box(grid, cx_l - 8, cx_l - 6, 12, 15, 20, 20, 3)  # Crisp white lace cuff
    fill_box(grid, cx_l - 8, cx_l - 6, 13, 15, 18, 19, 8)  # Poised hand
    # Right Arm (+X, viewer's left foreground!): Serving a gleaming SILVER TEA TRAY WITH PORCELAIN TEACUP!
    fill_box(grid, cx_r + 6, cx_r + 8, 12, 16, 22, 26, 1)
    fill_box(grid, cx_r + 7, cx_r + 9, 15, 18, 21, 23, 3)  # White lace cuff
    fill_box(grid, cx_r + 8, cx_r + 9, 17, 19, 21, 22, 8)  # Serving hand!
    # Gleaming Silver Tea Tray & Cute Porcelain Teacup with Golden Trim!
    fill_box(grid, cx_r + 7, cx_r + 14, 17, 23, 22, 22, 4) # Silver serving tray!
    fill_box(grid, cx_r + 7, cx_r + 14, 23, 23, 23, 23, 3) # Tray rim highlight
    fill_box(grid, cx_r + 9, cx_r + 12, 19, 21, 23, 25, 3) # Porcelain teacup!
    fill_box(grid, cx_r + 9, cx_r + 12, 19, 21, 25, 25, 6) # Golden cup rim!
    fill_box(grid, cx_r + 10, cx_r + 11, 20, 20, 24, 24, 5)# Crimson tea inside!

    # --- 5. ICONIC NEKOMIMI MAID HEAD: LONG BLACK HAIR, FRILLY LACE HEADDRESS & PERKY CAT EARS! (Z: 33..47) ---
    fill_sym_box(grid, 0, 1, 13, 15, 33, 34, 8)   # Neck
    fill_sym_box(grid, 0, 3, 11, 16, 34, 41, 1)   # Glossy jet-black maid hair!
    fill_sym_box(grid, 0, 4, 10, 11, 25, 39, 1)   # Long flowing glossy back hair!
    fill_sym_box(grid, 1, 2, 10, 10, 31, 35, 2)   # Glossy hair sheen highlight
    fill_sym_box(grid, 3, 4, 13, 16, 29, 39, 1)   # Long side-locks framing cheeks!
    # Expressive Anime-Mecha Cat-Maid Faceplate!
    fill_sym_box(grid, 0, 2, 16, 17, 34, 39, 8)   # Porcelain face
    fill_sym_box(grid, 1, 2, 17, 17, 36, 37, 9)   # Luminous emerald-mint cat eyes!
    fill_sym_box(grid, 0, 0, 17, 17, 36, 37, 8)   # Nose bridge
    fill_sym_box(grid, 2, 2, 17, 17, 35, 35, 7)   # Cute sakura-pink cheek blush!
    fill_sym_box(grid, 0, 2, 16, 17, 39, 40, 1)   # Sleek black bangs!

    # ICONIC SCALLOPED FRILLY WHITE VICTORIAN MAID HEADDRESS (Z: 40..44)
    fill_sym_box(grid, 0, 4, 14, 16, 41, 42, 3)   # Wide arched white lace headdress!
    fill_sym_box(grid, 0, 3, 15, 17, 42, 43, 3)   # High ruffled lace brim!
    fill_sym_box(grid, 1, 1, 16, 17, 43, 44, 3)   # Scalloped lace peaks!
    fill_sym_box(grid, 3, 3, 16, 17, 42, 43, 3)
    fill_sym_box(grid, 4, 5, 14, 16, 39, 41, 3)   # Side lace lappets!
    fill_sym_box(grid, 3, 4, 15, 17, 41, 41, 5)   # Crimson ribbon bows on headdress!

    # PERKY POINTED BLACK CAT EARS WITH SAKURA-PINK INNER EARS! (猫耳!) (Z: 41..47)
    fill_sym_box(grid, 2, 4, 12, 14, 42, 44, 1)   # Cat ear base
    fill_sym_box(grid, 3, 4, 12, 13, 44, 46, 1)   # Sharp cat ear tips!
    fill_sym_box(grid, 4, 4, 12, 13, 46, 47, 1)   # Perky apex!
    fill_sym_box(grid, 3, 3, 14, 14, 43, 45, 7)   # Soft sakura-pink inner cat ears!

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=40, pitch_a=20, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "neko_a.vox")
    v_b = export_vox(model_b, "neko_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "ZODIAC MAID ROBOT #13 (EXTRA): NEKO (CAT) -> NEKOMIMI MAID ROBOT",
        "1. NEKO (TUXEDO BLACK CAT)",
        "2. NEKO CLASSIC MAID ROBOT",
        "preview_neko.png",
        yaw_a=40, pitch_a=20, yaw_b=28, pitch_b=18,
    )
    print(f"neko: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
