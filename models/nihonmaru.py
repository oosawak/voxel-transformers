import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Hideyoshi's Grand Flagship Atakebune "Nihonmaru" -> Samurai Warship Robot!
# Hull -> Legs & Waist, Yagura (Tower Deckhouse) -> Chest, Manmaku & Sail -> Back Wings/Halo!
PALETTE = {
    1: (208, 42, 36, 255),    # Vermilion-Crimson Lacquered Bulwarks & Yagura (朱塗り)
    2: (138, 24, 26, 255),    # Deep Crimson Lacquer Shading
    3: (126, 78, 40, 255),    # Warm Dark Ship Timber Hull Planking
    4: (68, 42, 24, 255),     # Deep Hull Keel Wood & Frame Joints
    5: (244, 198, 48, 255),   # Radiant Toyotomi Gold Trim, Prow & Ornaments
    6: (246, 240, 224, 255),  # Cream-White Grand Square Sail & Manmaku White Stripe
    7: (54, 52, 108, 255),    # Royal Indigo-Purple Manmaku Stripe & Yagura Roof Tiles
    8: (74, 80, 92, 255),     # Dark Iron Oar-Ports, Cannon & Fittings
    9: (255, 222, 72, 255),   # Glowing Amber-Gold Eyes & Flagship Lanterns
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
# FORM A: NIHONMARU (HIDEYOSHI'S GRAND ATAKEBUNE) (32 x 58 x 44)
# ============================================================
def build_a():
    grid = np.zeros((30, 52, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 14
    cx_r = X // 2      # 15

    # --- 1. MASSIVE ATAKEBUNE WOODEN HULL (Y: 4..48, Z: 0..9) ---
    for y in range(4, 49):
        if y < 9:
            hw = 4 + (y - 4) // 2
            zb = max(0, 2 - (y - 4) // 2)
        elif y <= 36:
            hw = 6
            zb = 0
        else:
            t = (y - 36) / 12.0
            hw = max(1, int(round(6 * (1.0 - t * 0.85))))
            zb = int(round(t * 4.5))
        zt = 8 + (2 if y >= 43 else 0)
        for z in range(zb, zt + 1):
            w_z = max(1, hw - (2 if z <= zb + 1 else (1 if z <= zb + 2 else 0)))
            col = 4 if z <= zb + 1 else (3 if z <= 5 else 1)
            fill_sym_box(grid, 0, w_z, y, y, z, z, col)
        fill_sym_box(grid, hw, hw, y, y, zt, zt, 5)
    # Ornate upturned gold prow ornament at bow (Y: 47..50)
    fill_sym_box(grid, 0, 1, 47, 49, 8, 12, 1)
    fill_sym_box(grid, 0, 1, 49, 50, 10, 14, 5)
    # Banks of rowing oars protruding cleanly along both hull flanks!
    for oy in range(12, 35, 5):
        draw_6conn_line(grid, (cx_r + 6, oy, 4), (cx_r + 12, oy - 2, 1), 3)
        draw_6conn_line(grid, (cx_l - 6, oy, 4), (cx_l - 12, oy - 2, 1), 3)
        fill_sym_box(grid, 6, 6, oy, oy, 5, 5, 8)

    # --- 2. STRIPED MANMAKU CURTAIN WALLS (幔幕) (Z: 9..12) ---
    for y in range(8, 38):
        m_col = 6 if (y % 4 in (0, 1)) else 7
        fill_sym_box(grid, 6, 6, y, y, 9, 11, m_col)
        fill_sym_box(grid, 6, 6, y, y, 12, 12, 5)
    for xo in range(0, 7):
        m_col = 6 if (xo % 2 == 0) else 7
        fill_sym_box(grid, xo, xo, 37, 37, 9, 11, m_col)
        fill_sym_box(grid, xo, xo, 8, 8, 9, 11, m_col)
    fill_sym_box(grid, 0, 6, 37, 37, 12, 12, 5)
    fill_sym_box(grid, 0, 6, 8, 8, 12, 12, 5)

    # --- 3. GRAND MULTI-TIERED CRIMSON & GOLD YAGURA (楼) (Y: 10..29, Z: 9..25) ---
    fill_sym_box(grid, 0, 5, 10, 29, 9, 15, 1)
    for gy in range(13, 27, 4):
        fill_sym_box(grid, 5, 5, gy, gy + 1, 12, 13, 8)
    fill_sym_box(grid, 0, 7, 9, 30, 16, 16, 7)
    fill_sym_box(grid, 0, 6, 10, 29, 17, 17, 5)
    fill_sym_box(grid, 0, 4, 12, 24, 18, 22, 1)
    fill_sym_box(grid, 0, 3, 24, 24, 19, 21, 5)
    fill_sym_box(grid, 0, 2, 24, 24, 20, 20, 9)
    fill_sym_box(grid, 4, 4, 15, 22, 20, 21, 8)
    fill_sym_box(grid, 0, 5, 11, 25, 23, 23, 7)
    fill_sym_box(grid, 0, 3, 12, 24, 24, 24, 7)
    fill_sym_box(grid, 0, 2, 13, 23, 25, 25, 5)
    fill_sym_box(grid, 0, 1, 14, 22, 26, 26, 5)

    # --- 4. TALL MAST & BILLOWING CREAM-WHITE GRAND SQUARE SAIL (帆) (Y: 30..36, Z: 9..40) ---
    fill_sym_box(grid, 0, 0, 31, 32, 9, 39, 4)
    fill_sym_box(grid, 0, 10, 32, 32, 37, 37, 4)
    fill_sym_box(grid, 0, 9, 32, 32, 16, 16, 4)
    for sz in range(17, 37):
        billow = int(round(2.2 * np.sin((sz - 16) / 21.0 * np.pi)))
        sy_s = 32 + billow
        for xo in range(0, 10):
            if sz in (19, 20, 33, 34):
                col = 1
            elif 24 <= sz <= 29 and xo <= 3:
                col = 5 if (sz in (24, 29) or xo == 3 or (sz == 26 and xo <= 1)) else 1
            elif xo % 4 == 0:
                col = 7
            else:
                col = 6
            fill_sym_box(grid, xo, xo, sy_s, sy_s, sz, sz, col)
    fill_sym_box(grid, 0, 1, 32, 34, 26, 26, 4)
    fill_sym_box(grid, 0, 1, 32, 33, 17, 17, 4)
    fill_sym_box(grid, 0, 1, 32, 33, 36, 36, 4)
    fill_sym_box(grid, 0, 0, 31, 32, 39, 40, 5)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: NIHONMARU WARSHIP ROBOT (48 x 28 x 48)
# Hull -> Legs & Waist, Yagura -> Chest, Manmaku & Sail -> Back Halo/Wings!
# ============================================================
def build_b():
    grid = np.zeros((48, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # --- 1. SPLIT HULL BOW BOOTS & ATAKEBUNE HULL GREAVES (船体が脚!) (Z: 0..15) ---
    # Heavy pointed warship-prow boots!
    fill_sym_box(grid, 3, 6, 10, 19, 0, 1, 4)     # Dark keel sole
    fill_sym_box(grid, 3, 6, 11, 19, 1, 3, 3)     # Ship timber hull boot
    fill_sym_box(grid, 4, 5, 19, 21, 1, 3, 1)     # Crimson upturned bow toe!
    fill_sym_box(grid, 4, 5, 20, 21, 3, 4, 5)     # Golden prow ornament toe-tip!
    fill_sym_box(grid, 3, 5, 9, 10, 0, 2, 4)      # Heel rudder-spur

    # Armored Ship-Hull Greaves with Crimson Bulwarks & Oar-Ports (Z: 4..15)
    fill_sym_box(grid, 3, 6, 11, 16, 4, 14, 3)    # Dark hull timber shins
    fill_sym_box(grid, 4, 6, 14, 17, 5, 13, 1)    # Crimson lacquered hull-side bulwark
    fill_sym_box(grid, 6, 6, 12, 16, 6, 12, 5)    # Gold gunwale side trim
    # Oar-ports visible along outer legs!
    fill_sym_box(grid, 6, 6, 13, 13, 7, 8, 8)
    fill_sym_box(grid, 6, 6, 13, 13, 10, 11, 8)
    # Golden Knee Prow Shields
    fill_sym_box(grid, 3, 6, 16, 18, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 17, 18, 13, 15, 5)

    # --- 2. THIGHS & HULL-STERN WAIST ARMOR (船体が腰!) (Z: 15..23) ---
    fill_sym_box(grid, 3, 5, 11, 16, 15, 19, 4)
    fill_sym_box(grid, 3, 5, 14, 16, 15, 18, 3)
    # Waist Hull Skirt with Striped Manmaku Side-Tassets
    fill_sym_box(grid, 0, 5, 11, 16, 19, 22, 4)
    fill_sym_box(grid, 2, 6, 16, 17, 17, 21, 3)   # Timber hull front skirt
    fill_sym_box(grid, 2, 6, 17, 17, 17, 17, 5)   # Gold gunwale hem
    fill_sym_box(grid, 6, 7, 11, 16, 17, 21, 1)   # Crimson hull hip plates
    fill_sym_box(grid, 7, 7, 12, 15, 17, 17, 5)
    fill_sym_box(grid, 0, 5, 10, 11, 17, 21, 3)   # Rear hull waist
    fill_sym_box(grid, 0, 1, 16, 18, 19, 22, 1)   # Center front crimson apron
    fill_sym_box(grid, 0, 1, 18, 18, 20, 21, 5)   # Gold buckle

    # --- 3. HEROIC YAGURA (楼) CHEST FORTRESS (楼が胸!) (Z: 22..34) ---
    fill_sym_box(grid, 0, 4, 11, 16, 22, 24, 4)
    fill_sym_box(grid, 0, 7, 10, 18, 25, 32, 1)   # Grand crimson Yagura chest deckhouse!
    # Gunports & golden command balcony across chest!
    fill_sym_box(grid, 4, 6, 18, 18, 27, 28, 8)   # Side gunports
    fill_sym_box(grid, 0, 3, 18, 19, 26, 30, 5)   # Golden Yagura command veranda centerpiece!
    fill_sym_box(grid, 0, 2, 19, 19, 27, 29, 1)   # Crimson inner frame
    fill_sym_box(grid, 0, 1, 19, 20, 28, 28, 9)   # Glowing golden flagship lantern core!
    # Sweeping Indigo-Tiled Yagura Roof Eaves crowning the upper chest! (Z: 32..34)
    fill_sym_box(grid, 0, 8, 10, 19, 32, 33, 7)
    fill_sym_box(grid, 0, 7, 11, 18, 34, 34, 5)   # Gold chest-roof ridge trim!

    # --- 4. GRAND BACK MOTIF: UNFURLED SQUARE SAIL (帆) + DRAPED STRIPED MANMAKU (幔幕) WINGS! ---
    fill_sym_box(grid, 0, 4, 8, 10, 24, 33, 4)    # Mast backpack mount
    # Central Mast rising behind head & shoulders supporting the Grand Sail Halo!
    fill_sym_box(grid, 0, 0, 7, 8, 24, 45, 4)
    fill_sym_box(grid, 0, 14, 7, 7, 43, 43, 4)    # Upper sail yardarm
    fill_sym_box(grid, 0, 13, 7, 7, 28, 28, 4)    # Lower sail boom
    # Broad Cream-White Square Sail Banner unfurled like a magnificent War-God Halo behind back! (Z: 28..44)
    for sz in range(29, 44):
        for xo in range(0, 14):
            if sz in (30, 42):
                col = 1  # Crimson sail war-stripes!
            elif 34 <= sz <= 39 and xo <= 3:
                col = 5 if (sz in (34, 39) or xo == 3) else 1  # Gold crest on sail!
            elif xo % 5 == 0:
                col = 7  # Sail seam line
            else:
                col = 6  # Cream-white sail canvas!
            fill_sym_box(grid, xo, xo, 6, 6, sz, sz, col)
    # Draped Striped MANMAKU Curtain Wings cascading below the sail on BOTH sides! (Z: 17..28)
    for xo in range(7, 16):
        m_col = 6 if (xo % 2 == 0) else 7         # Iconic white & royal-indigo Manmaku stripes!
        z_bot = 17 + (xo - 7) // 2
        fill_sym_box(grid, xo, xo, 7, 7, z_bot, 28, m_col)
        fill_sym_box(grid, xo, xo, 7, 7, 28, 28, 5)  # Gold curtain rope!
        fill_sym_box(grid, xo, xo, 7, 7, z_bot, z_bot, 5)  # Gold lower tassel hem

    # --- 5. SHOULDERS & OAR-ARMED ARMS (Z: 14..34) ---
    fill_sym_box(grid, 7, 9, 12, 16, 28, 32, 4)
    # Layered Crimson & Gold Yagura-Eave Shoulder Pauldrons
    fill_sym_box(grid, 8, 12, 11, 17, 28, 33, 1)
    fill_sym_box(grid, 8, 13, 11, 17, 33, 34, 7)  # Tiled roof shoulder cap!
    fill_sym_box(grid, 9, 13, 12, 16, 34, 34, 5)  # Gold eave trim
    fill_sym_box(grid, 12, 12, 12, 16, 29, 32, 5) # Gold outer shoulder boss
    # Upper arms
    fill_sym_box(grid, 9, 11, 12, 16, 22, 27, 4)
    # Left Arm (-X, viewer's right): Armored Crimson Forearm & Fist
    fill_box(grid, cx_l - 12, cx_l - 9, 12, 17, 16, 21, 1)
    fill_box(grid, cx_l - 12, cx_l - 9, 13, 17, 16, 16, 5)
    fill_box(grid, cx_l - 11, cx_l - 9, 13, 16, 14, 15, 8)
    # Right Arm (+X, viewer's left): Wielding Great Golden-Banded War Oar-Halberd!
    fill_box(grid, cx_r + 9, cx_r + 12, 12, 17, 17, 22, 1)
    fill_box(grid, cx_r + 11, cx_r + 14, 15, 19, 16, 19, 5)
    fill_box(grid, cx_r + 13, cx_r + 15, 17, 20, 15, 18, 8)
    # War Oar-Polearm held cleanly clear on right (+X)
    ox_p = cx_r + 15
    fill_box(grid, ox_p, ox_p + 1, 18, 19, 5, 34, 3)   # Wooden oar shaft
    fill_box(grid, ox_p, ox_p + 1, 18, 19, 28, 36, 5)  # Golden gilded oar-blade!
    fill_box(grid, ox_p - 1, ox_p + 2, 18, 19, 31, 36, 1)  # Crimson oar-blade crest!
    fill_box(grid, ox_p, ox_p + 1, 18, 19, 37, 39, 5)  # Blade tip

    # --- 6. HEAD WITH TOYOTOMI GOLDEN SUNBURST CREST (Z: 34..47) ---
    fill_sym_box(grid, 0, 1, 13, 16, 34, 35, 4)
    fill_sym_box(grid, 0, 2, 12, 17, 35, 40, 1)   # Crimson kabuto skull
    fill_sym_box(grid, 0, 3, 11, 15, 35, 37, 7)   # Indigo shikoro neck-guard
    fill_sym_box(grid, 0, 2, 16, 18, 35, 36, 8)   # Dark iron menpo jaw for crisp contrast
    fill_sym_box(grid, 0, 0, 18, 18, 35, 35, 5)   # Gold chin boss
    fill_sym_box(grid, 0, 2, 16, 18, 37, 38, 4)   # Dark eye visor
    fill_sym_box(grid, 1, 2, 18, 18, 37, 38, 9)   # Glowing amber-gold eyes!
    fill_sym_box(grid, 0, 0, 18, 18, 37, 38, 8)   # Dark nose bridge separating eyes!
    fill_sym_box(grid, 0, 2, 16, 19, 39, 39, 5)   # Gold brow visor
    # Iconic Hideyoshi Radiant Golden Sunburst Rays Crest (馬藺後立 / Sunburst Crown)!
    for ray_dx, ray_dz in [(-4, 5), (-2, 6), (0, 7), (2, 6), (4, 5)]:
        draw_6conn_line(grid, (cx_r + (0 if ray_dx >= 0 else -1), 17, 40),
                        (cx_r + ray_dx + (0 if ray_dx >= 0 else -1), 17, 40 + ray_dz), 5)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=44, pitch_a=22, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "nihonmaru_a.vox")
    v_b = export_vox(model_b, "nihonmaru_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: NIHONMARU (ATAKEBUNE) -> FLAGSHIP ROBOT",
        "1. NIHONMARU (GRAND ATAKEBUNE)",
        "2. NIHONMARU WARSHIP ROBOT",
        "preview_nihonmaru.png",
        yaw_a=44, pitch_a=22, yaw_b=28, pitch_b=18,
    )
    print(f"nihonmaru: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
