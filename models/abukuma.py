import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Swift Abukuma River Boat (associated with Shiroishi Castle / bestowed by Hideyoshi) -> Agile Robot!
# Slender elongated hull -> Legs & Torso, Rowers' Oars (Kai) -> Arms!
PALETTE = {
    1: (192, 138, 78, 255),   # Warm Cedar River-Boat Planking (杉材船体)
    2: (128, 84, 42, 255),    # Rich Darker Timber & Oar Shafts
    3: (64, 42, 26, 255),     # Deep Keel Wood & Frame Joints
    4: (32, 98, 136, 255),    # Abukuma River Deep Blue-Teal Hull Trim
    5: (86, 188, 218, 255),   # Bright River-Cyan Waterline & Speed Accent
    6: (206, 48, 42, 255),    # Hideyoshi-Bestowed Vermilion-Red Trim
    7: (244, 198, 52, 255),   # Radiant Gold Bow Ornament & Oar Bands
    8: (244, 240, 230, 255),  # Crisp White Cabin Curtain & Yakata Trim
    9: (255, 224, 76, 255),   # Glowing Amber-Gold Eyes & River Lantern
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(int(x0), int(x1))), min(X - 1, max(int(x0), int(x1)))
    y0, y1 = max(0, min(int(y0), int(y1))), min(Y - 1, max(int(y0), int(y1)))
    z0, z1 = max(0, min(int(z0), int(z1))), min(Z - 1, max(int(z0), int(z1)))
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center (requires even X)."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


def draw_6conn_line(grid, p0, p1, col, pad=(0, 0, 0), only_empty=False):
    """Draw a guaranteed 6-connected line between 3D points p0 and p1."""
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
    """Hollow strictly interior voxels (all 26 neighbors occupied) to preserve 6-connectivity."""
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
    """Return number of 6-connected components and min Z."""
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
# FORM A: ABUKUMA RIVER SWIFT BOAT (川船・早船) (36 x 60 x 20)
# ============================================================
def build_a():
    grid = np.zeros((36, 60, 20), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 17
    cx_r = X // 2      # 18

    # --- 1. LONG, SLEEK, NARROW HIGH-SPEED RIVER HULL (Y: 2..57, Z: 0..10) ---
    for y in range(2, 58):
        # Smooth needle-sharp pointed bow (+Y) and tapered upturned stern (-Y)!
        if y < 14:
            t = (14 - y) / 12.0
            hw = max(0, int(round(4.5 * (1.0 - t * 0.85))))
            zb = int(round(t * 4.0))
            zt = 5 + int(round(t * 4.5))
        elif y <= 40:
            hw = 4
            zb = 0
            zt = 5
        else:
            t = (y - 40) / 17.0
            hw = max(0, int(round(4.5 * (1.0 - t * 0.90))))
            zb = int(round(t * 5.0))
            zt = 5 + int(round(t * 5.5))

        for z in range(zb, zt + 1):
            w_z = max(0, hw - (1 if z == zb and hw > 1 else 0))
            if z == zb:
                col = 3  # Dark flat-bottom river keel
            elif z == zb + 1:
                col = 4  # River-blue waterline stripe
            elif z == zt:
                col = 6 if (14 <= y <= 44) else 7  # Hideyoshi vermilion gunwale + gold prow!
            else:
                col = 1 if (y % 2 == 0) else 2     # Warm cedar hull planking!
            fill_sym_box(grid, 0, w_z, y, y, z, z, col)
        # Bright cyan swift-water accent dot along waterline
        if 14 <= y <= 40 and y % 4 == 0:
            fill_sym_box(grid, hw, hw, y, y, 2, 2, 5)

    # Graceful Upturned Gold-Capped Bow Finial (+Y) & Rear Rudder Oar (-Y)
    fill_sym_box(grid, 0, 0, 56, 58, 9, 12, 7)
    fill_sym_box(grid, 0, 0, 54, 56, 8, 10, 6)
    draw_6conn_line(grid, (cx_r, 4, 6), (cx_r, 1, 1), 2)
    draw_6conn_line(grid, (cx_l, 4, 6), (cx_l, 1, 1), 2)

    # --- 2. STREAMLINED LOW YAKATA RIVER CANOPY (苫・屋形) (Y: 16..34, Z: 5..12) ---
    # Open-sided low wooden river pavilion with white-and-river-blue curtains!
    fill_sym_box(grid, 0, 3, 17, 33, 5, 5, 2)     # Deck floor
    for py in (17, 22, 28, 33):
        fill_sym_box(grid, 3, 3, py, py, 6, 9, 3) # Cedar canopy posts
    # Rolled white & indigo river curtains along upper canopy eaves
    fill_sym_box(grid, 3, 3, 18, 32, 8, 9, 8)
    fill_sym_box(grid, 3, 3, 18, 32, 9, 9, 4)
    # Gently arched streamlined dark-wood & vermilion-trimmed roof
    fill_sym_box(grid, 0, 4, 16, 34, 10, 10, 2)
    fill_sym_box(grid, 0, 3, 16, 34, 11, 11, 1)
    fill_sym_box(grid, 0, 1, 17, 33, 12, 12, 6)   # Vermilion roof ridge
    fill_sym_box(grid, 0, 0, 33, 35, 11, 12, 7)   # Gold front roof finial
    fill_sym_box(grid, 0, 0, 34, 34, 8, 9, 9)     # Glowing river lantern under front eave!

    # --- 3. PAIRED SWIFT ROWING OARS (漕ぎ手の櫂 — BECOME ROBOT'S ARMS!) ---
    # Three sleek pairs of long gold-banded cedar rowing oars sweeping cleanly outward on BOTH sides!
    oar_ys = (20, 27, 36)
    for oy in oar_ys:
        for sign in (-1, 1):
            bx = cx_r if sign == 1 else cx_l
            def ox(off):
                return bx + sign * off
            # Oarlock pivot on gunwale
            fill_box(grid, ox(4), ox(5), oy, oy, 5, 6, 7)
            # Long sweeping wooden oar shaft angling out & back
            draw_6conn_line(grid, (ox(5), oy, 5), (ox(13), oy - 4, 2), 2)
            # Gold oar band near blade
            fill_box(grid, ox(11), ox(12), oy - 3, oy - 3, 2, 3, 7)
            # Broad paddle blade skimming river level (Z: 1..2)
            draw_6conn_line(grid, (ox(13), oy - 4, 2), (ox(16), oy - 6, 1), 1, pad=(0, 1, 0))
            fill_box(grid, ox(16), ox(16), oy - 7, oy - 5, 1, 1, 5)  # River-cyan water-spray edge on blade!

    # Small Hideyoshi-bestowed banner pennant near stern (Y: 11..14, Z: 6..16)
    fill_sym_box(grid, 0, 0, 13, 13, 6, 16, 3)
    fill_sym_box(grid, 0, 0, 10, 13, 12, 15, 6)
    fill_sym_box(grid, 0, 0, 11, 12, 13, 14, 7)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: ABUKUMA SWIFT RIVER-BOAT ROBOT (44 x 24 x 46)
# Slender hull -> Sleek Legs & Torso, Rowers' Oars -> Agile Arms & Oar-Blades!
# ============================================================
def build_b():
    grid = np.zeros((44, 24, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21
    cx_r = X // 2      # 22

    # --- 1. SLEEK POINTED BOAT-BOW BOOTS & STREAMLINED HULL LEGS (細長い船体が脚!) (Z: 0..16) ---
    # Sleek high-speed pointed boat-prow feet!
    fill_sym_box(grid, 2, 4, 9, 17, 0, 1, 3)      # Dark keel sole
    fill_sym_box(grid, 2, 4, 10, 17, 1, 2, 4)     # River-blue waterline foot
    fill_sym_box(grid, 3, 3, 17, 19, 1, 2, 1)     # Pointed cedar boat-prow toe!
    fill_sym_box(grid, 3, 3, 19, 20, 2, 3, 7)     # Upturned gold bow finial toe!
    fill_sym_box(grid, 3, 3, 8, 9, 0, 2, 3)       # Rudder heel spur

    # Slender Aerodynamic Cedar-Hull Greaves (Z: 3..15)
    fill_sym_box(grid, 2, 4, 10, 14, 3, 14, 1)    # Warm cedar hull shins
    fill_sym_box(grid, 3, 3, 14, 15, 4, 13, 4)    # River-blue front hull keel-ridge!
    fill_sym_box(grid, 4, 4, 11, 14, 5, 12, 6)    # Vermilion bestowed-boat side gunwale
    fill_sym_box(grid, 4, 4, 12, 13, 7, 10, 5)    # Cyan speed-waterline highlight
    # Pointed Gold-Trimmed Knee Prows
    fill_sym_box(grid, 2, 4, 14, 16, 13, 16, 4)
    fill_sym_box(grid, 3, 3, 16, 17, 14, 16, 7)

    # --- 2. SLIM THIGHS & BOAT-STERN WAIST (Z: 15..23) ---
    fill_sym_box(grid, 2, 4, 10, 14, 15, 19, 3)
    fill_sym_box(grid, 2, 4, 12, 14, 16, 18, 2)
    fill_sym_box(grid, 0, 4, 10, 14, 19, 22, 3)   # Slim pelvis
    fill_sym_box(grid, 1, 4, 14, 15, 18, 21, 1)   # Cedar front tassets
    fill_sym_box(grid, 1, 4, 15, 15, 18, 18, 6)   # Vermilion waist hem
    fill_sym_box(grid, 4, 5, 10, 14, 18, 21, 4)   # River-blue hip fins
    fill_sym_box(grid, 5, 5, 11, 13, 19, 20, 5)
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 6)   # Vermilion loin flap
    fill_sym_box(grid, 0, 0, 16, 16, 21, 21, 7)   # Gold waist seal

    # --- 3. STREAMLINED HULL & YAKATA-CANOPY TORSO (細長い船体が胴体!) (Z: 22..34) ---
    fill_sym_box(grid, 0, 3, 10, 14, 22, 25, 3)   # Narrow agile waist
    fill_sym_box(grid, 0, 3, 14, 15, 22, 25, 4)   # River-blue abdomen
    # Slender Hull-Deck & White-Curtained Yakata Chest Armor (Z: 26..33)
    fill_sym_box(grid, 0, 5, 9, 15, 26, 32, 1)    # Cedar planking chest
    fill_sym_box(grid, 0, 4, 15, 16, 26, 31, 4)   # River-blue central hull breastplate
    fill_sym_box(grid, 1, 4, 15, 16, 29, 31, 8)   # White yakata curtain chest inlay!
    fill_sym_box(grid, 0, 1, 16, 17, 27, 30, 6)   # Vermilion Hideyoshi chest badge
    fill_sym_box(grid, 0, 0, 17, 17, 28, 29, 9)   # Glowing river-lantern chest core!
    fill_sym_box(grid, 1, 4, 10, 14, 32, 33, 6)   # Vermilion collar
    fill_sym_box(grid, 2, 4, 13, 15, 33, 33, 7)   # Gold collarbone trim
    # Rear Sleek Stern-Hull Backpack & Rudder Fin (Y: 5..9, Z: 21..35)
    fill_sym_box(grid, 0, 3, 7, 9, 24, 32, 2)
    fill_sym_box(grid, 0, 2, 6, 7, 25, 31, 1)
    fill_sym_box(grid, 0, 0, 4, 6, 21, 35, 4)     # Vertical rudder fin on back!
    fill_sym_box(grid, 0, 0, 4, 5, 33, 36, 7)     # Gold stern finial

    # --- 4. ROWERS' OARS (漕ぎ手の櫂) TRANSFORMED INTO AGILE ARMS & TWIN OAR-BLADE GAUNTLETS! ---
    fill_sym_box(grid, 5, 7, 11, 14, 29, 32, 3)   # Oarlock shoulder joints!
    # Swept Canoe-Hull Shoulder Pauldrons
    fill_sym_box(grid, 6, 9, 10, 15, 29, 33, 1)
    fill_sym_box(grid, 7, 10, 11, 14, 32, 33, 4)  # River-blue upper pauldron
    fill_sym_box(grid, 9, 10, 11, 14, 31, 31, 7)  # Gold oarlock band!
    # Upper Arms made from twin banded cedar Oar Shafts!
    fill_sym_box(grid, 7, 8, 11, 14, 23, 28, 2)
    fill_sym_box(grid, 7, 8, 11, 14, 25, 25, 7)   # Gold shaft collar

    # BOTH FOREARMS: Broad Sculpted Wooden Rowing-Oar Blades (櫂が腕!) with Cyan Water-Spray Edges!
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        def ax(off):
            return bx + sign * off
        # Forearm oar-shaft housing
        fill_box(grid, ax(7), ax(9), 11, 15, 16, 22, 2)
        fill_box(grid, ax(7), ax(9), 12, 15, 16, 16, 7)  # Gold cuff
        fill_box(grid, ax(7), ax(8), 12, 14, 14, 15, 3)  # Gripping hand
        # Attached Sweeping Broad Cedar Oar-Paddle Blade extending forward & back along each forearm!
        fill_box(grid, ax(10), ax(10), 10, 19, 15, 21, 1)  # Broad cedar paddle blade!
        fill_box(grid, ax(10), ax(11), 16, 21, 16, 20, 1)  # Extended forward paddle tip!
        fill_box(grid, ax(11), ax(11), 19, 22, 17, 19, 5)  # Cyan water-cutting paddle edge!
        fill_box(grid, ax(10), ax(10), 11, 18, 18, 18, 7)  # Gold central oar rib!
        fill_box(grid, ax(10), ax(10), 9, 11, 16, 20, 6)   # Vermilion rear blade accent!

    # --- 5. SLEEK RIVER-SCOUT HEAD & GOLD BOW-CREST (Z: 33..45) ---
    fill_sym_box(grid, 0, 1, 11, 14, 33, 34, 3)
    fill_sym_box(grid, 0, 2, 10, 14, 34, 39, 4)   # River-blue sleek helmet
    fill_sym_box(grid, 0, 3, 10, 13, 34, 36, 1)   # Cedar cheek-fins
    fill_sym_box(grid, 0, 2, 14, 15, 34, 35, 8)   # Crisp white jaw-guard
    fill_sym_box(grid, 0, 2, 14, 15, 36, 37, 3)   # Visor frame
    fill_sym_box(grid, 1, 2, 15, 15, 36, 37, 9)   # Glowing amber eyes!
    fill_sym_box(grid, 0, 2, 14, 16, 38, 38, 6)   # Vermilion brow band
    # Swept-back Golden River-Prow Crest & Fin
    fill_sym_box(grid, 0, 0, 12, 16, 39, 42, 7)
    draw_6conn_line(grid, (cx_r, 15, 39), (cx_r + 4, 12, 44), 7)
    draw_6conn_line(grid, (cx_l, 15, 39), (cx_l - 4, 12, 44), 7)
    fill_sym_box(grid, 0, 0, 15, 16, 40, 41, 5)   # Cyan crest jewel

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ==========================================
# MAGICA-VOXEL (.vox) EXPORTER
# ==========================================
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
    header = b'VOX ' + struct.pack('<I', 150)

    with open(filename, 'wb') as f:
        f.write(header + main_chunk)
    return len(voxels)


# ==========================================
# TRUE ISOMETRIC / 3D VOXEL RENDERER
# ==========================================
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

    yaw = np.radians(yaw_deg)
    pitch = np.radians(pitch_deg)
    cos_y, sin_y = np.cos(yaw), np.sin(yaw)
    cos_p, sin_p = np.cos(pitch), np.sin(pitch)

    def project_unit(x, y, z):
        dx, dy, dz = x - cx, y - cy, z - cz
        rx = -dx * cos_y + dy * sin_y
        ry = dx * sin_y + dy * cos_y
        sy = ry * sin_p - dz * cos_p
        depth = ry * cos_p + dz * sin_p
        return rx, sy, depth

    corners = [
        (x, y, z)
        for x in (xs.min(), xs.max() + 1)
        for y in (ys.min(), ys.max() + 1)
        for z in (zs.min(), zs.max() + 1)
    ]
    proj_c = [project_unit(x, y, z) for x, y, z in corners]
    min_rx = min(p[0] for p in proj_c)
    max_rx = max(p[0] for p in proj_c)
    min_sy = min(p[1] for p in proj_c)
    max_sy = max(p[1] for p in proj_c)

    if scale is None:
        sx_fit = (img_size[0] - 2 * margin) / max(1e-5, max_rx - min_rx)
        sy_fit = (img_size[1] - 2 * margin) / max(1e-5, max_sy - min_sy)
        scale = min(sx_fit, sy_fit, 9.5)

    ox = img_size[0] / 2.0 - ((min_rx + max_rx) / 2.0) * scale
    oy = img_size[1] / 2.0 - ((min_sy + max_sy) / 2.0) * scale

    def project(x, y, z):
        rx, sy, depth = project_unit(x, y, z)
        return (rx * scale + ox, sy * scale + oy), depth

    visible = []
    for x, y, z in zip(xs, ys, zs):
        x, y, z = int(x), int(y), int(z)
        if (0 < x < X - 1 and 0 < y < Y - 1 and 0 < z < Z - 1 and
                grid[x - 1, y, z] and grid[x + 1, y, z] and
                grid[x, y - 1, z] and grid[x, y + 1, z] and
                grid[x, y, z - 1] and grid[x, y, z + 1]):
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

    vx_dir = sin_y * cos_p
    vy_dir = cos_y * cos_p
    vz_dir = sin_p

    for _, x, y, z, c in visible:
        base_col = PALETTE[c]
        for verts, normal, light in faces:
            nx, ny, nz = normal
            nnx, nny, nnz = x + nx, y + ny, z + nz
            if 0 <= nnx < X and 0 <= nny < Y and 0 <= nnz < Z and grid[nnx, nny, nnz] > 0:
                continue
            dot = nx * vx_dir + ny * vy_dir + nz * vz_dir
            if dot <= 1e-6:
                continue
            poly = [project(x + vx, y + vy, z + vz)[0] for vx, vy, vz in verts]
            fcol = shade_color(base_col, light)
            draw.polygon(poly, fill=fcol, outline=shade_color(fcol, 0.85))
    return img


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=46, pitch_a=24, yaw_b=28, pitch_b=18):
    canvas = Image.new("RGBA", (860, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, 860, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (860, gy)], fill=(28, 34, 48, 255), width=1)

    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))

    models = [
        (label_a, grid_a, v_a, yaw_a, pitch_a),
        (label_b, grid_b, v_b, yaw_b, pitch_b),
    ]
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(models):
        bx = 24 + idx * 414
        by = 48
        w, h = 398, 468
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
            px0 = bx + 14 + (pi - 1) * 20
            py0 = by + 430
            draw.rectangle([px0, py0, px0 + 15, py0 + 15], fill=PALETTE[pi], outline=(70, 82, 105, 255))

    canvas.save(out_path)


if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    v_a = export_vox(model_a, "abukuma_a.vox")
    v_b = export_vox(model_b, "abukuma_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: ABUKUMA RIVER BOAT -> SWIFT OAR ROBOT",
        "1. ABUKUMA SWIFT RIVER BOAT",
        "2. ABUKUMA RIVER ROBOT",
        "preview_abukuma.png",
        yaw_a=46, pitch_a=24, yaw_b=28, pitch_b=18,
    )
    print(f"abukuma: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
