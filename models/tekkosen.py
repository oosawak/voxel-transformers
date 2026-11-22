import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Oda Nobunaga's Ironclad Warship "Tekkosen" -> Heavy Ironclad Juggernaut Robot!
# Iron armor plates -> Robot armor, Ship hull -> Legs!
PALETTE = {
    1: (88, 96, 108, 255),    # Heavy Forged Gunmetal Iron Armor Plates
    2: (146, 156, 172, 255),  # Brushed Steel Plate Edges, Rivets & Bevels
    3: (40, 44, 52, 255),     # Deep Black-Iron Frame, Cannons & Gunports
    4: (106, 68, 38, 255),    # Dark Warship Lower Timber Hull
    5: (62, 38, 22, 255),     # Deep Keel Wood & Hull Shading
    6: (198, 40, 42, 255),    # Oda Crimson War Trim & Flag Accent
    7: (236, 188, 52, 255),   # Burnished Gold Oda Crest & Fittings
    8: (218, 212, 196, 255),  # Smoked Canvas War Banner / Trim
    9: (255, 138, 36, 255),   # Blazing Cannon-Fire Amber-Orange Visor & Ports
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
# FORM A: TEKKOSEN (NOBUNAGA'S IRONCLAD WARSHIP) (28 x 58 x 36)
# ============================================================
def build_a():
    grid = np.zeros((26, 52, 34), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 12
    cx_r = X // 2      # 13

    # --- 1. HEAVY DARK-TIMBER & IRON-SHOD LOWER HULL (Y: 4..49, Z: 0..7) ---
    for y in range(4, 50):
        if y < 9:
            hw = 4 + (y - 4) // 2
            zb = max(0, 2 - (y - 4) // 3)
        elif y <= 37:
            hw = 7
            zb = 0
        else:
            t = (y - 37) / 12.0
            hw = max(1, int(round(7 * (1.0 - t * 0.85))))
            zb = int(round(t * 4.0))
        for z in range(zb, 8):
            w_z = max(1, hw - (2 if z <= zb + 1 else (1 if z == zb + 2 else 0)))
            if z <= zb + 1:
                col = 5  # Deep keel wood
            elif z <= 4:
                col = 4  # Dark ship timber
            else:
                col = 2 if (y % 5 == 0) else 1
            fill_sym_box(grid, 0, w_z, y, y, z, z, col)
    # Heavy Forged Iron Ramming Prow at Bow (Y: 47..51, Z: 4..11)
    fill_sym_box(grid, 0, 1, 46, 50, 5, 10, 3)
    fill_sym_box(grid, 0, 0, 49, 51, 7, 11, 2)
    fill_sym_box(grid, 0, 1, 47, 49, 8, 9, 6)  # Crimson war-prow stripe

    # --- 2. RIVETED IRON-PLATED BOX FORTRESS CASEMATE (鉄の装甲板!) (Y: 8..39, Z: 8..16) ---
    for y in range(8, 40):
        for z in range(8, 17):
            hw = 7 if z <= 12 else 6
            is_seam = (y % 5 == 0 or z in (8, 12, 16))
            col = 2 if is_seam else 1
            fill_sym_box(grid, 0, hw, y, y, z, z, col)
    # Prominent Iron Rivets & Matchlock/Cannon Gunports (大筒・鉄砲狭間) along BOTH flanks!
    for gy in range(11, 37, 6):
        fill_sym_box(grid, 7, 7, gy, gy + 1, 10, 11, 3)  # Lower gunport recess
        fill_sym_box(grid, 6, 8, gy, gy, 10, 10, 3)      # Protruding iron cannon barrel!
        fill_sym_box(grid, 8, 8, gy, gy, 10, 10, 9)      # Glowing cannon-fire muzzle!
        fill_sym_box(grid, 6, 6, gy + 2, gy + 2, 13, 14, 3)  # Upper matchlock loop-hole
    # Heavy Forward Twin Bow Siege Cannons (Y: 39..44)
    fill_sym_box(grid, 2, 3, 38, 43, 10, 11, 3)
    fill_sym_box(grid, 2, 3, 43, 43, 10, 11, 9)
    # Sloped Ironclad Armored Roof Deck with Crimson Trim
    fill_sym_box(grid, 0, 6, 9, 38, 16, 16, 2)
    fill_sym_box(grid, 0, 5, 10, 37, 17, 17, 1)
    fill_sym_box(grid, 5, 5, 10, 37, 17, 17, 6)  # Oda crimson armor trim!

    # --- 3. IRON-PLATED UPPER COMMAND BRIDGE & ODA MOKKO BANNER MAST (Z: 18..33) ---
    fill_sym_box(grid, 0, 4, 14, 26, 18, 22, 1)  # Armored iron bridge citadel
    fill_sym_box(grid, 0, 4, 14, 26, 22, 22, 2)  # Steel bridge roof
    fill_sym_box(grid, 0, 3, 26, 26, 20, 21, 3)  # Bridge viewing slit
    fill_sym_box(grid, 1, 2, 26, 26, 20, 20, 9)  # Glowing amber bridge eyes
    fill_sym_box(grid, 0, 1, 26, 27, 18, 19, 7)  # Gold Oda emblem on bow bridge!
    # Stout Iron-Banded Mast & Oda War Banner (Y: 29..31, Z: 17..33)
    fill_sym_box(grid, 0, 0, 29, 30, 17, 32, 3)
    fill_sym_box(grid, 0, 0, 29, 30, 32, 33, 7)  # Gold spearhead masthead
    fill_sym_box(grid, 0, 5, 30, 30, 31, 31, 3)  # Crossbar
    fill_sym_box(grid, 0, 5, 30, 31, 22, 30, 3)  # Black-iron war flag
    fill_sym_box(grid, 0, 5, 31, 31, 22, 23, 6)  # Crimson lower border
    fill_sym_box(grid, 0, 5, 31, 31, 29, 30, 6)  # Crimson upper border
    fill_sym_box(grid, 0, 2, 31, 31, 25, 27, 7)  # Gold Oda Mokko crest!
    fill_sym_box(grid, 0, 0, 31, 31, 26, 26, 3)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: TEKKOSEN IRONCLAD ROBOT (44 x 26 x 46)
# Iron armor plates -> Robot's heavy riveted armor, Ship hull -> Legs!
# ============================================================
def build_b():
    grid = np.zeros((44, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21
    cx_r = X // 2      # 22

    # --- 1. SPLIT WARSHIP HULL LEGS & IRON-RAM BOOTS (船体が脚!) (Z: 0..15) ---
    # Heavy Ironclad Ship-Bow Boots
    fill_sym_box(grid, 3, 6, 9, 18, 0, 1, 5)     # Deep keel sole
    fill_sym_box(grid, 3, 6, 10, 18, 1, 3, 4)    # Dark timber lower hull foot
    fill_sym_box(grid, 4, 6, 17, 19, 1, 3, 3)    # Iron ramming prow toe-cap!
    fill_sym_box(grid, 4, 5, 18, 19, 3, 3, 2)    # Brushed steel toe edge
    fill_sym_box(grid, 3, 5, 8, 9, 0, 2, 5)      # Rear heel

    # Massive Ship-Hull & Iron-Belt Greaves (Z: 4..15)
    fill_sym_box(grid, 3, 6, 10, 15, 4, 14, 4)   # Dark timber ship-hull inner leg
    fill_sym_box(grid, 3, 6, 14, 16, 4, 13, 1)   # Riveted gunmetal iron shin plates!
    fill_sym_box(grid, 6, 6, 11, 15, 5, 13, 1)   # Outer iron hull armor
    # Rivet seams & brushed steel bands across iron shin plates
    fill_sym_box(grid, 3, 6, 15, 16, 6, 6, 2)
    fill_sym_box(grid, 3, 6, 15, 16, 10, 10, 2)
    fill_sym_box(grid, 6, 6, 12, 14, 8, 8, 6)    # Crimson waterline trim
    # Heavy Boxy Ironclad Knee Shields
    fill_sym_box(grid, 3, 6, 15, 17, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 17, 17, 13, 15, 2)
    fill_sym_box(grid, 4, 5, 17, 17, 14, 14, 7)  # Gold rivet boss

    # --- 2. THIGHS & IRON-PLATED WAIST SKIRT (Z: 15..23) ---
    fill_sym_box(grid, 3, 5, 10, 15, 15, 19, 3)
    fill_sym_box(grid, 3, 5, 13, 15, 15, 18, 1)
    fill_sym_box(grid, 0, 5, 10, 15, 19, 22, 3)
    # Riveted Angular Iron Tasset Plates
    fill_sym_box(grid, 2, 6, 15, 16, 17, 21, 1)
    fill_sym_box(grid, 2, 6, 16, 16, 17, 17, 2)
    fill_sym_box(grid, 2, 6, 16, 16, 20, 20, 6)  # Oda crimson belt stripe
    fill_sym_box(grid, 6, 7, 10, 15, 17, 21, 1)  # Side iron hip shields
    fill_sym_box(grid, 7, 7, 11, 14, 19, 19, 2)
    fill_sym_box(grid, 0, 5, 9, 10, 17, 21, 1)
    fill_sym_box(grid, 0, 1, 15, 17, 19, 22, 3)  # Center iron codpiece
    fill_sym_box(grid, 0, 1, 17, 17, 20, 21, 7)  # Gold Oda waist seal

    # --- 3. HEAVY IRONCLAD CASEMATE CHEST ARMOR (鉄の装甲板が鎧!) (Z: 22..33) ---
    fill_sym_box(grid, 0, 4, 10, 15, 22, 24, 3)
    fill_sym_box(grid, 0, 7, 9, 17, 25, 32, 1)   # Massive riveted gunmetal iron cuirass!
    fill_sym_box(grid, 0, 6, 16, 18, 26, 31, 1)  # Angled front ironclad plate
    # Steel plate border seams & rivets
    fill_sym_box(grid, 0, 6, 17, 18, 25, 25, 2)
    fill_sym_box(grid, 0, 6, 17, 18, 31, 31, 2)
    fill_sym_box(grid, 6, 6, 16, 17, 26, 31, 2)
    # Built-in Twin Chest Cannon Ports (echoing ship's bow cannons!)
    fill_sym_box(grid, 4, 5, 17, 18, 28, 29, 3)
    fill_sym_box(grid, 4, 4, 18, 18, 28, 29, 9)  # Glowing cannon-port vents!
    # Oda Crimson & Gold Center Chest Crest
    fill_sym_box(grid, 0, 2, 18, 18, 27, 30, 6)
    fill_sym_box(grid, 0, 1, 18, 19, 28, 29, 7)
    fill_sym_box(grid, 0, 0, 19, 19, 28, 29, 3)
    fill_sym_box(grid, 1, 5, 10, 15, 32, 33, 2)  # Heavy steel collar

    # Rear Ironclad Bridge Backpack & Twin Smokestack/Cannon Thrusters (Y: 5..9, Z: 23..35)
    fill_sym_box(grid, 0, 5, 6, 9, 24, 32, 1)
    fill_sym_box(grid, 0, 4, 5, 6, 25, 31, 2)
    fill_sym_box(grid, 0, 2, 5, 5, 27, 29, 6)
    # Twin Shoulder-Mounted Naval Siege Cannons rising from backpack! (Z: 31..38)
    fill_sym_box(grid, 3, 4, 6, 9, 31, 37, 3)
    fill_sym_box(grid, 3, 4, 8, 11, 35, 37, 3)   # Forward-pointing heavy iron siege barrels!
    fill_sym_box(grid, 3, 4, 11, 11, 36, 36, 9)  # Glowing cannon muzzles!

    # --- 4. BULKY IRON-PLATED SHIELD SHOULDERS & ARMS (Z: 14..35) ---
    fill_sym_box(grid, 7, 9, 11, 15, 28, 32, 3)
    # Massive Riveted Ironclad Casemate Shoulder Shields!
    fill_sym_box(grid, 8, 12, 10, 16, 27, 34, 1)
    fill_sym_box(grid, 8, 12, 10, 16, 34, 34, 2) # Brushed steel top edge
    fill_sym_box(grid, 12, 12, 10, 16, 27, 33, 2)# Steel outer rim
    fill_sym_box(grid, 12, 12, 11, 15, 30, 31, 6)# Oda crimson stripe
    fill_sym_box(grid, 9, 11, 16, 16, 29, 31, 3) # Shoulder gunport detail
    fill_sym_box(grid, 10, 10, 16, 16, 30, 30, 7)# Gold rivet
    # Heavy Armored Arms
    fill_sym_box(grid, 8, 10, 11, 15, 22, 27, 3) # Upper arms
    # Left Arm (-X, viewer's right): Riveted Ironclad Bulwark Tower-Shield Gauntlet!
    fill_box(grid, cx_l - 12, cx_l - 8, 11, 16, 15, 21, 1)
    fill_box(grid, cx_l - 13, cx_l - 12, 11, 18, 14, 24, 1) # Huge attached iron plate shield!
    fill_box(grid, cx_l - 13, cx_l - 13, 12, 17, 15, 23, 2)
    fill_box(grid, cx_l - 13, cx_l - 13, 14, 15, 18, 20, 6) # Crimson shield emblem
    fill_box(grid, cx_l - 11, cx_l - 9, 12, 15, 13, 15, 3)  # Iron fist
    # Right Arm (+X, viewer's left): Heavy Forearm Naval Cannon Gauntlet!
    fill_box(grid, cx_r + 8, cx_r + 12, 11, 17, 16, 21, 1)
    fill_box(grid, cx_r + 11, cx_r + 13, 12, 22, 17, 20, 3) # Heavy mounted iron deck-cannon!
    fill_box(grid, cx_r + 11, cx_r + 13, 15, 16, 17, 20, 7) # Gold barrel reinforcement band
    fill_box(grid, cx_r + 12, cx_r + 12, 22, 23, 18, 19, 9) # Glowing cannon bore!
    fill_box(grid, cx_r + 9, cx_r + 11, 13, 16, 14, 16, 3)  # Fist

    # --- 5. NANBAN-DO IRONCLAD KABUTO HEAD & ODA CREST (Z: 33..45) ---
    fill_sym_box(grid, 0, 1, 12, 15, 33, 34, 3)
    fill_sym_box(grid, 0, 3, 11, 16, 34, 40, 1)  # Heavy forged iron Nanban helmet
    fill_sym_box(grid, 0, 4, 10, 14, 34, 37, 3)  # Dark iron shikoro neck-guard
    fill_sym_box(grid, 0, 2, 16, 17, 34, 36, 2)  # Steel face guard
    fill_sym_box(grid, 0, 2, 16, 17, 37, 38, 3)  # Deep eye visor slot
    fill_sym_box(grid, 1, 2, 17, 17, 37, 38, 9)  # Blazing cannon-fire orange eyes!
    fill_sym_box(grid, 0, 3, 16, 18, 39, 39, 2)  # Steel brow visor
    # Gold Oda-Crest Helmet Horns (Z: 40..45)
    fill_sym_box(grid, 0, 1, 17, 18, 40, 42, 7)
    fill_sym_box(grid, 0, 0, 18, 18, 40, 41, 6)
    draw_6conn_line(grid, (cx_r + 1, 17, 41), (cx_r + 5, 16, 45), 7)
    draw_6conn_line(grid, (cx_l - 1, 17, 41), (cx_l - 5, 16, 45), 7)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=42, pitch_a=22, yaw_b=28, pitch_b=18):
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
    v_a = export_vox(model_a, "tekkosen_a.vox")
    v_b = export_vox(model_b, "tekkosen_b.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: TEKKOSEN (NOBUNAGA IRONCLAD) -> ARMORED ROBOT",
        "1. TEKKOSEN (IRONCLAD WARSHIP)",
        "2. TEKKOSEN IRONCLAD ROBOT",
        "preview_tekkosen.png",
        yaw_a=42, pitch_a=22, yaw_b=28, pitch_b=18,
    )
    print(f"tekkosen: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a}), "
          f"B={v_b} voxels {model_b.shape} (comp={comp_b}, minZ={minz_b})")
