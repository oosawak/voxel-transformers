import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Daji / Dakki (妲己) 【このシリーズの顔】 -> Nine-Tailed Fox Empress Valkyrie Robot!
# Enchanting Nine-Tailed Fox Spirit (九尾の狐): pointed fox ears & ALL NINE distinct fanning fox tails
# transform into sleek armored fox-ear crests & NINE armored wing-tail binder blades!
PALETTE = {
    1: (248, 244, 248, 255),  # Pure Pearl-White Nine-Tail Fox Fur & Valkyrie Armor
    2: (218, 36, 78, 255),    # Imperial Crimson-Rose Court Dress & Armored Tail Tips!
    3: (244, 126, 168, 255),  # Bewitching Sakura-Magenta Silk Ribbons & Inner Fox Ears
    4: (248, 202, 54, 255),   # Radiant Imperial Gold Empress Hairpins, Crown & Armor Trim
    5: (146, 20, 56, 255),    # Deep Wine-Crimson Dress Folds & Shading
    6: (34, 28, 44, 255),     # Glossy Jet-Black Hair & Sleek Valkyrie Frame
    7: (254, 226, 212, 255),  # Enchanting Porcelain Face
    8: (224, 186, 214, 255),  # Soft Lavender-Pearl Tail Shading
    9: (255, 224, 82, 255),   # Luminous Golden Fox-Fire Eyes & Bewitching Core!
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


def draw_nine_tails(grid, cx, y_root, z_root, specs, armored=False):
    """
    Draw ALL NINE distinct gracefully fanning fox tails (九尾の狐 — 9本の尾!).
    Each entry in specs is (mid_dx, mid_dy, mid_dz, tip_dx, tip_dy, tip_dz).
    Every tail emerges from a unified tail-root fan hub so 6-connectivity is guaranteed!
    """
    for idx, (mdx, mdy, mdz, tdx, tdy, tdz) in enumerate(specs):
        p0 = (cx, y_root, z_root)
        p1 = (cx + mdx, y_root + mdy, z_root + mdz)
        p2 = (cx + tdx, y_root + tdy, z_root + tdz)
        if armored:
            # Sleek layered mecha wing-tail binders: white armor core + gold rib + glowing crimson tip!
            draw_6conn_line(grid, p0, p1, 1, pad=(0, 0, 1))
            draw_6conn_line(grid, p1, p2, 1, pad=(0, 0, 0))
            # Gold armor trim along tail spine
            draw_6conn_line(grid, (p0[0], p0[1] - 1, p0[2]), (p1[0], p1[1] - 1, p1[2]), 4 if idx % 2 == 0 else 3)
            # Glowing crimson-rose & gold blade tip!
            fill_box(grid, p2[0] - 1, p2[0] + 1, p2[1], p2[1], p2[2] - 1, p2[2] + 1, 2)
            fill_box(grid, p2[0], p2[0], p2[1], p2[1], p2[2], p2[2] + 1, 9)
        else:
            # Soft lush white-fur fox tails with enchanting sakura-crimson tips!
            draw_6conn_line(grid, p0, p1, 1, pad=(0, 0, 1))
            draw_6conn_line(grid, p1, p2, 1, pad=(0, 0, 0))
            fill_box(grid, p2[0], p2[0], p2[1], p2[1], p2[2] - 1, p2[2] + 1, 2)
            fill_box(grid, p2[0], p2[0], p2[1] + 1, p2[1] + 1, p2[2], p2[2], 3)


# ============================================================
# FORM A: DAKKI / DAJI NINE-TAILED FOX EMPRESS (52 x 28 x 46)
# ============================================================
def build_a():
    grid = np.zeros((52, 28, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 25
    cx_r = X // 2      # 26

    # --- 1. FLOWING IMPERIAL CRIMSON-AND-GOLD COURT GOWN (Z: 0..27) ---
    fill_sym_box(grid, 1, 4, 13, 18, 0, 1, 4)     # Golden court slippers
    fill_sym_box(grid, 0, 5, 11, 18, 1, 12, 2)    # Graceful flared crimson court skirt
    fill_sym_box(grid, 0, 5, 11, 18, 1, 2, 4)     # Golden hem embroidery
    fill_sym_box(grid, 0, 2, 18, 19, 2, 14, 1)    # Pure-white pleated front panel
    fill_sym_box(grid, 0, 1, 19, 19, 3, 13, 3)    # Sakura-pink central silk streamer
    # Slender Waist, Sakura-Gold Obi & Royal Bodice (Z: 13..26)
    fill_sym_box(grid, 0, 3, 12, 18, 13, 17, 3)   # Lush sakura-magenta obi sash!
    fill_sym_box(grid, 0, 1, 18, 19, 14, 16, 4)   # Gold imperial obi clasp
    fill_sym_box(grid, 0, 3, 12, 18, 18, 26, 2)   # Crimson court bodice
    fill_sym_box(grid, 0, 2, 18, 18, 19, 25, 1)   # White silk neckline
    fill_sym_box(grid, 1, 3, 17, 18, 25, 26, 4)   # Golden embroidered collar

    # Graceful Wide Court Sleeves & Floating Silk Ribbon (Z: 15..27)
    fill_box(grid, cx_l - 6, cx_l - 4, 13, 17, 17, 25, 2)
    fill_box(grid, cx_l - 7, cx_l - 5, 13, 17, 14, 17, 3)   # Flowing sakura sleeve cuff
    fill_box(grid, cx_l - 6, cx_l - 5, 17, 19, 17, 18, 7)   # Delicate hand
    fill_box(grid, cx_r + 4, cx_r + 6, 13, 17, 17, 25, 2)
    fill_box(grid, cx_r + 5, cx_r + 7, 13, 17, 14, 17, 3)
    fill_box(grid, cx_r + 5, cx_r + 7, 17, 20, 18, 20, 7)   # Raised hand conjuring fox-fire!
    fill_box(grid, cx_r + 6, cx_r + 8, 19, 21, 21, 23, 9)   # Floating golden fox-fire flame!

    # --- 2. ALL NINE DISTINCT FANNING WHITE FOX TAILS! (九尾の狐 — 9本の尾!) ---
    # Tail-root cushion anchored cleanly to back of obi!
    fill_sym_box(grid, 0, 3, 9, 12, 12, 16, 1)
    nine_tail_specs_a = [
        (0,   -3, 16,   0,  -4, 28),   # #1 Center crowning tail rising high behind crown!
        (4,   -3, 14,   9,  -4, 26),   # #2 Upper-right tail
        (-4,  -3, 14,  -9,  -4, 26),   # #3 Upper-left tail
        (8,   -3, 10,  16,  -4, 21),   # #4 Mid-upper-right tail
        (-8,  -3, 10, -16,  -4, 21),   # #5 Mid-upper-left tail
        (11,  -2,  4,  20,  -3, 13),   # #6 Mid-lower-right tail
        (-11, -2,  4, -20,  -3, 13),   # #7 Mid-lower-left tail
        (10,  -2, -2,  18,  -2,  4),   # #8 Lower-right sweeping tail
        (-10, -2, -2, -18,  -2,  4),   # #9 Lower-left sweeping tail
    ]
    draw_nine_tails(grid, cx_r, y_root=10, z_root=14, specs=nine_tail_specs_a, armored=False)

    # --- 3. ENCHANTING HEAD, ORNATE GOLD EMPRESS CROWN & POINTED FOX EARS (狐耳!) (Z: 26..42) ---
    fill_sym_box(grid, 0, 2, 13, 18, 26, 33, 7)   # Porcelain face
    fill_sym_box(grid, 1, 2, 18, 18, 29, 30, 9)   # Bewitching golden fox eyes!
    fill_sym_box(grid, 0, 3, 12, 18, 32, 35, 6)   # Glossy jet-black court hair
    fill_sym_box(grid, 0, 3, 11, 12, 24, 33, 6)   # Long flowing black back-hair
    # Ornate Imperial Gold Phoenix Hairpins & Diadem!
    fill_sym_box(grid, 0, 2, 15, 19, 34, 37, 4)   # Imperial gold diadem
    fill_sym_box(grid, 0, 1, 19, 19, 35, 36, 2)   # Ruby jewel
    fill_sym_box(grid, 4, 6, 14, 15, 34, 35, 4)   # Horizontal golden hairpins!
    # ICONIC PROMINENT POINTED WHITE-AND-SAKURA FOX EARS (狐耳!)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        fill_box(grid, bx + sign * 2, bx + sign * 4, 13, 16, 35, 38, 1)  # White fur ear base
        fill_box(grid, bx + sign * 3, bx + sign * 4, 14, 16, 39, 41, 1)  # Tall pointed ear tip!
        fill_box(grid, bx + sign * 3, bx + sign * 4, 14, 15, 41, 42, 2)  # Crimson ear tip!
        fill_box(grid, bx + sign * 3, bx + sign * 3, 16, 16, 36, 39, 3)  # Soft sakura inner ear!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: DAKKI NINE-TAILED FOX VALKYRIE EMPRESS ROBOT (58 x 28 x 50)
# Fox Ears -> Armored Fox-Ear Crest Antennas;
# 9 Tails -> NINE DISTINCT ARMORED WING-TAIL BINDER BLADES!
# ============================================================
def build_b():
    grid = np.zeros((58, 28, 50), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 28
    cx_r = X // 2      # 29

    # --- 1. SLEEK VALKYRIE HIGH-HEEL BOOTS & PEARL-WHITE GREAVES (Z: 0..17) ---
    fill_sym_box(grid, 2, 4, 12, 19, 0, 2, 2)     # Crimson valkyrie heels
    fill_sym_box(grid, 2, 4, 19, 20, 0, 1, 4)     # Gold pointed toe-guards
    fill_sym_box(grid, 2, 4, 13, 18, 3, 15, 1)    # Sleek pearl-white valkyrie greaves!
    fill_sym_box(grid, 3, 3, 18, 19, 4, 14, 3)    # Sakura energy stripes
    fill_sym_box(grid, 2, 4, 17, 19, 13, 16, 4)   # Gold fox-crest knee guards!
    fill_sym_box(grid, 3, 3, 19, 19, 14, 15, 2)

    # --- 2. SLENDER VALKYRIE WAIST & CRIMSON-GOLD OBI SKIRT ARMOR (Z: 15..24) ---
    fill_sym_box(grid, 2, 4, 13, 17, 16, 20, 6)   # Sleek black inner thighs
    fill_sym_box(grid, 0, 4, 13, 17, 20, 23, 2)   # Crimson waist armor
    fill_sym_box(grid, 1, 5, 17, 19, 15, 22, 2)   # Flared imperial crimson skirt tassets!
    fill_sym_box(grid, 1, 5, 19, 19, 15, 16, 4)   # Gold skirt trim
    fill_sym_box(grid, 5, 6, 13, 17, 17, 22, 1)   # Pearl-white hip fins
    fill_sym_box(grid, 0, 1, 18, 20, 17, 23, 3)   # Sakura-pink obi core!
    fill_sym_box(grid, 0, 1, 20, 20, 20, 22, 4)   # Gold waist emblem

    # --- 3. IMPERIAL FOX-EMPRESS VALKYRIE CHEST CUIRASS (Z: 23..35) ---
    fill_sym_box(grid, 0, 3, 13, 17, 23, 25, 6)   # Slender mecha waist
    fill_sym_box(grid, 0, 5, 12, 19, 26, 34, 1)   # Pearl-white valkyrie cuirass
    fill_sym_box(grid, 1, 5, 18, 20, 27, 33, 2)   # Imperial crimson breastplate!
    fill_sym_box(grid, 0, 2, 20, 21, 28, 32, 4)   # Radiant gold fox-crest collar!
    fill_sym_box(grid, 0, 1, 21, 21, 29, 31, 9)   # Luminous golden fox-fire core!
    fill_sym_box(grid, 0, 4, 9, 12, 24, 33, 6)    # Tail-binder backpack core!
    fill_sym_box(grid, 0, 4, 9, 12, 20, 24, 2)    # Lower tail-fan manifold!

    # --- 4. ALL NINE DISTINCT ARMORED WING-TAIL BINDER BLADES! (9本の装甲尾!) ---
    nine_tail_specs_b = [
        (0,   -3, 17,   0,  -4, 28),   # #1 Center crowning armored tail-spire!
        (5,   -3, 15,  11,  -4, 27),   # #2 Upper-right armored tail blade
        (-5,  -3, 15, -11,  -4, 27),   # #3 Upper-left armored tail blade
        (10,  -3, 11,  19,  -4, 22),   # #4 Mid-upper-right tail blade
        (-10, -3, 11, -19,  -4, 22),   # #5 Mid-upper-left tail blade
        (13,  -2,  4,  25,  -3, 13),   # #6 Wide mid-lower-right tail blade
        (-13, -2,  4, -25,  -3, 13),   # #7 Wide mid-lower-left tail blade
        (12,  -2, -3,  22,  -2,  2),   # #8 Sweeping lower-right tail blade
        (-12, -2, -3, -22,  -2,  2),   # #9 Sweeping lower-left tail blade
    ]
    draw_nine_tails(grid, cx_r, y_root=10, z_root=21, specs=nine_tail_specs_b, armored=True)

    # --- 5. WINGED EMPRESS PAULDRONS & FOX-FIRE SCEPTER (Z: 15..45) ---
    fill_sym_box(grid, 5, 7, 13, 17, 30, 33, 6)
    fill_sym_box(grid, 6, 10, 12, 18, 29, 35, 1)  # Pearl-white lotus pauldrons
    fill_sym_box(grid, 7, 11, 13, 17, 34, 36, 4)  # Gold empress shoulder crests!
    fill_sym_box(grid, 9, 11, 14, 16, 30, 33, 2)  # Crimson side inlay
    fill_sym_box(grid, 6, 8, 13, 17, 23, 29, 6)
    fill_box(grid, cx_l - 9, cx_l - 6, 13, 18, 17, 22, 1)
    fill_box(grid, cx_l - 9, cx_l - 7, 14, 18, 17, 18, 3)
    fill_box(grid, cx_l - 9, cx_l - 7, 15, 17, 15, 16, 4)
    # Right Arm (+X): Wielding Golden Nine-Tail Fox-Fire Scepter!
    fill_box(grid, cx_r + 6, cx_r + 9, 13, 18, 18, 23, 1)
    fill_box(grid, cx_r + 8, cx_r + 11, 16, 20, 18, 21, 4)
    fill_box(grid, cx_r + 11, cx_r + 11, 19, 19, 4, 36, 4)   # Slender golden scepter
    fill_box(grid, cx_r + 10, cx_r + 12, 18, 20, 37, 40, 9)  # Blazing fox-fire crystal!
    fill_box(grid, cx_r + 9, cx_r + 13, 19, 19, 36, 37, 2)   # Crimson lotus collar

    # --- 6. NINE-TAILED FOX VALKYRIE ROBOT HEAD WITH TALL ARMORED FOX EARS! (狐耳装甲!) (Z: 34..49) ---
    fill_sym_box(grid, 0, 1, 14, 17, 34, 35, 6)
    fill_sym_box(grid, 0, 2, 12, 19, 35, 41, 1)   # Pearl-white valkyrie helm!
    fill_sym_box(grid, 0, 2, 19, 20, 35, 36, 8)   # Delicate silver chinplate
    fill_sym_box(grid, 0, 2, 19, 20, 37, 38, 6)   # Dark eye visor
    fill_sym_box(grid, 1, 2, 20, 20, 37, 38, 9)   # Luminous golden fox-eyes!
    # Imperial Gold Crown Diadem & Side Hairpin Antennas!
    fill_sym_box(grid, 0, 2, 16, 20, 40, 43, 4)
    fill_sym_box(grid, 0, 1, 20, 20, 41, 43, 2)   # Crimson forehead jewel
    fill_sym_box(grid, 4, 6, 15, 16, 40, 41, 4)   # Golden hairpin side-fins!
    # ICONIC TALL ARMORED FOX-EAR SENSOR CRESTS (狐耳装甲!) (Z: 41..49)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        fill_box(grid, bx + sign * 2, bx + sign * 4, 13, 17, 41, 44, 1)  # White armored ear base
        fill_box(grid, bx + sign * 3, bx + sign * 5, 14, 17, 45, 48, 1)  # Swept tall armored fox ears!
        fill_box(grid, bx + sign * 4, bx + sign * 5, 14, 16, 48, 49, 2)  # Crimson armored tips!
        fill_box(grid, bx + sign * 3, bx + sign * 4, 17, 17, 42, 46, 3)  # Glowing sakura inner-ear sensors!

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=24, pitch_a=16, yaw_b=24, pitch_b=16):
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
    v_a = export_vox(model_a, "dakki_a.vox")
    v_b = export_vox(model_b, "dakki_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "CLASSICS ROBO #17: DAKKI / DAJI (FLAGSHIP!) -> NINE-TAILED FOX VALKYRIE ROBOT",
        "1. DAKKI (NINE-TAILED FOX)",
        "2. DAKKI ROBOT (9 ARMORED TAILS)",
        "preview_dakki.png",
    )
    print(f"dakki: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
