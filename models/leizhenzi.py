import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Leizhenzi (雷震子) -> Thunder-Winged Aerial Robot!
# Giant Wind-Thunder Wings on back (背中の大きな翼 -> armored mecha wings!),
# Golden Cudgel (黄金棍), cobalt-blue skin (青い肌)!
PALETTE = {
    1: (46, 118, 206, 255),   # Iconic Cobalt-Blue Thunder-God Skin & Armor (青い肌!)
    2: (24, 68, 146, 255),    # Deep Storm-Blue Wing Membrane & Shading
    3: (246, 198, 46, 255),   # Radiant Golden Cudgel (黄金棍!), Beak & Lightning Trim
    4: (186, 138, 24, 255),   # Burnished Gold Armor Shading
    5: (202, 34, 44, 255),    # Fiery Crimson Hair, Loincloth & Wing-Joints
    6: (34, 34, 48, 255),     # Dark Storm-Iron Frame & Talons
    7: (118, 178, 244, 255),  # Sky-Blue Thunder Highlight
    8: (242, 246, 252, 255),  # Crisp Lightning-White Wingtips
    9: (255, 242, 74, 255),   # Blazing Electric-Yellow Eyes & Thunder Core!
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


def draw_golden_cudgel(grid, hx, hy, z_bot, z_top):
    """Draw Leizhenzi's radiant Golden Cudgel (黄金棍)."""
    fill_box(grid, hx, hx, hy, hy, z_bot, z_top, 3)
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_top - 2, z_top, 9)
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_bot, z_bot + 1, 4)


# ============================================================
# FORM A: LEIZHENZI (BLUE-SKINNED WINGED THUNDER WARRIOR) (48 x 24 x 42)
# ============================================================
def build_a():
    grid = np.zeros((48, 24, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # Talon Boots & Blue-Skinned Legs (Z: 0..14)
    fill_sym_box(grid, 2, 4, 10, 15, 0, 2, 6)
    fill_sym_box(grid, 2, 4, 11, 14, 3, 5, 3)     # Gold ankle bands
    fill_sym_box(grid, 2, 4, 11, 14, 6, 14, 1)    # Cobalt-blue legs

    # Crimson & Gold Waistcloth & Muscular Cobalt-Blue Torso (Z: 14..28)
    fill_sym_box(grid, 0, 4, 10, 15, 14, 18, 5)   # Crimson loincloth
    fill_sym_box(grid, 0, 4, 10, 16, 17, 18, 3)   # Gold thunder belt
    fill_sym_box(grid, 0, 4, 10, 15, 19, 28, 1)   # Cobalt-blue skin torso (青い肌!)
    fill_sym_box(grid, 0, 3, 15, 16, 22, 26, 3)   # Golden chest harness!
    fill_sym_box(grid, 0, 1, 16, 16, 23, 25, 9)   # Lightning amulet

    # HUGE OUTSTRETCHED WIND-THUNDER WINGS ON BACK! (背中の大きな翼!) (Z: 16..40)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        # Upper wing leading bone curving high & wide!
        draw_6conn_line(grid, (bx + sign * 2, 10, 26), (bx + sign * 11, 7, 36), 2, pad=(0, 0, 1))
        draw_6conn_line(grid, (bx + sign * 11, 7, 36), (bx + sign * 20, 6, 39), 2, pad=(0, 0, 0))
        # Sweeping wing membrane feather-blades!
        for tip_x, tip_z in [(20, 34), (18, 28), (14, 22), (9, 17)]:
            draw_6conn_line(grid, (bx + sign * 4, 9, 25), (bx + sign * tip_x, 7, tip_z), 2, pad=(0, 0, 1))
            # Electric gold lightning veins!
            draw_6conn_line(grid, (bx + sign * 4, 10, 26), (bx + sign * (tip_x - 3), 8, tip_z + 2), 9)

    # Arms & Radiant GOLDEN CUDGEL (黄金棍!) (Z: 16..40)
    fill_box(grid, cx_l - 7, cx_l - 5, 11, 15, 19, 27, 1)
    fill_box(grid, cx_l - 7, cx_l - 5, 12, 15, 18, 18, 3)
    fill_box(grid, cx_r + 5, cx_r + 7, 11, 15, 20, 27, 1)
    fill_box(grid, cx_r + 6, cx_r + 9, 14, 17, 19, 21, 1)
    draw_golden_cudgel(grid, cx_r + 9, 16, z_bot=2, z_top=39)

    # Fierce Cobalt-Blue Thunder-Bird Head, Golden Beak & Spiky Crimson Hair! (Z: 28..39)
    fill_sym_box(grid, 0, 2, 11, 16, 28, 34, 1)   # Cobalt-blue face!
    fill_sym_box(grid, 0, 1, 16, 18, 29, 31, 3)   # Iconic golden thunder-bird beak!
    fill_sym_box(grid, 1, 2, 16, 16, 32, 33, 9)   # Blazing electric-yellow eyes!
    fill_sym_box(grid, 0, 3, 10, 16, 34, 37, 5)   # Spiky crimson flame-hair!
    fill_sym_box(grid, 0, 2, 11, 15, 37, 39, 5)
    fill_sym_box(grid, 0, 1, 16, 16, 35, 36, 3)   # Gold forehead band

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: LEIZHENZI ARMORED THUNDER-WING ROBOT (翼が装甲になるロボ!) (56 x 26 x 46)
# ============================================================
def build_b():
    grid = np.zeros((56, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 27
    cx_r = X // 2      # 28

    # Aerodynamic Talon Boots & Cobalt-Blue Greaves (Z: 0..16)
    fill_sym_box(grid, 2, 5, 10, 17, 0, 2, 6)
    fill_sym_box(grid, 2, 5, 17, 19, 0, 1, 3)     # Golden eagle-talon toes!
    fill_sym_box(grid, 2, 5, 11, 16, 3, 14, 1)    # Cobalt-blue greaves
    fill_sym_box(grid, 3, 4, 16, 17, 4, 13, 7)    # Sky-blue vents
    fill_sym_box(grid, 2, 5, 16, 18, 12, 15, 3)   # Gold knee guards

    # Waist Armor (Z: 15..23)
    fill_sym_box(grid, 2, 4, 11, 15, 15, 19, 6)
    fill_sym_box(grid, 0, 5, 11, 15, 19, 22, 2)
    fill_sym_box(grid, 1, 5, 16, 17, 16, 21, 5)   # Crimson waist tassets
    fill_sym_box(grid, 0, 1, 16, 18, 18, 22, 3)

    # Thunder-God Chest Cuirass & MASSIVE ARMORED MECHA THUNDER-WINGS! (翼が装甲になる!) (Z: 18..44)
    fill_sym_box(grid, 0, 4, 11, 15, 22, 24, 6)
    fill_sym_box(grid, 0, 6, 10, 17, 25, 33, 1)   # Cobalt-blue armored chest
    fill_sym_box(grid, 1, 5, 17, 18, 26, 32, 3)   # Gold thunder breastplate
    fill_sym_box(grid, 0, 2, 18, 19, 27, 31, 5)   # Crimson center frame
    fill_sym_box(grid, 0, 1, 19, 19, 28, 30, 9)   # Blazing lightning reactor core!
    # MASSIVE ARMORED MECHA WINGS (wing-thruster binders + layered armor feather blades!)
    fill_sym_box(grid, 0, 4, 8, 10, 25, 33, 2)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        # Heavy armored upper wing-binder spar (gold + cobalt-blue!)
        draw_6conn_line(grid, (bx + sign * 3, 9, 30), (bx + sign * 14, 7, 40), 1, pad=(1, 0, 1))
        draw_6conn_line(grid, (bx + sign * 14, 7, 40), (bx + sign * 25, 6, 44), 3, pad=(0, 0, 1))
        # Four armored thunder-wing feather-blades fanning wide!
        for tip_x, tip_z, col_b in [(25, 37, 1), (22, 31, 2), (18, 25, 1), (13, 19, 2)]:
            draw_6conn_line(grid, (bx + sign * 4, 8, 28), (bx + sign * tip_x, 6, tip_z), col_b, pad=(0, 0, 1))
            fill_box(grid, bx + sign * tip_x, bx + sign * tip_x, 6, 7, tip_z, tip_z + 1, 9)  # Electric wingtips!

    # Wing-Mounted Pauldrons, Arms & Giant GOLDEN CUDGEL! (Z: 15..45)
    fill_sym_box(grid, 6, 8, 12, 15, 29, 32, 6)
    fill_sym_box(grid, 7, 11, 11, 16, 28, 34, 1)
    fill_sym_box(grid, 8, 12, 12, 15, 33, 35, 3)
    fill_sym_box(grid, 7, 9, 12, 15, 22, 28, 6)
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 21, 1)
    fill_box(grid, cx_l - 10, cx_l - 8, 13, 15, 14, 15, 3)
    fill_box(grid, cx_r + 7, cx_r + 10, 12, 16, 17, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 13, 15, 19, 17, 20, 3)
    draw_golden_cudgel(grid, cx_r + 13, 18, z_bot=2, z_top=44)

    # Thunder-Bird Robot Head: GOLDEN BEAK MASK & CRIMSON LIGHTNING CREST! (Z: 34..45)
    fill_sym_box(grid, 0, 1, 12, 15, 34, 35, 6)
    fill_sym_box(grid, 0, 3, 11, 17, 35, 41, 1)   # Cobalt-blue helm
    fill_sym_box(grid, 0, 1, 17, 19, 35, 37, 3)   # Armored golden beak-mask!
    fill_sym_box(grid, 0, 2, 17, 18, 38, 39, 6)   # Visor recess
    fill_sym_box(grid, 1, 2, 18, 18, 38, 39, 9)   # Electric-yellow eyes!
    fill_sym_box(grid, 0, 3, 11, 17, 41, 43, 5)   # Crimson lightning hair-crest!
    fill_sym_box(grid, 0, 1, 16, 18, 42, 45, 9)   # Gold-yellow lightning horn!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: GIANT BLUE THUNDER BIRD / GARUDA (鳥 — 青基調の大きな鳥!) (52 x 34 x 36)
# ============================================================
def build_c():
    grid = np.zeros((52, 34, 36), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 25
    cx_r = X // 2      # 26

    # Powerful Golden Eagle Talons & Storm-Rock Perch grounded at Z=0..9
    fill_sym_box(grid, 2, 5, 13, 21, 0, 1, 3)     # Spreading golden eagle talons!
    fill_sym_box(grid, 2, 5, 21, 22, 0, 0, 6)     # Sharp dark claws
    fill_sym_box(grid, 3, 4, 15, 18, 2, 8, 3)     # Sturdy golden raptor legs!

    # Majestic Cobalt-Blue Raptor Body & Golden Breast Plume (青基調!) (Z: 7..24)
    fill_sym_box(grid, 0, 5, 11, 23, 8, 20, 1)    # Cobalt-blue bird torso!
    fill_sym_box(grid, 0, 4, 21, 25, 10, 20, 7)   # Sky-blue & gold chest feathers!
    fill_sym_box(grid, 0, 2, 24, 25, 12, 18, 3)   # Golden lightning breastplate plume
    # Sweeping Fan-Shaped Tail Feathers behind! (Y: 2..11, Z: 6..13)
    for dx_t in (-4, -2, 0, 2, 4):
        bx_t = (cx_r if dx_t >= 0 else cx_l) + dx_t
        draw_6conn_line(grid, (cx_r if dx_t >= 0 else cx_l, 11, 11), (bx_t, 3, 7), 2, pad=(0, 0, 1))
        fill_box(grid, bx_t, bx_t, 2, 3, 6, 8, 9)  # Electric-yellow tail tips!

    # MASSIVE OUTSTRETCHED BLUE-AND-GOLD THUNDER WINGS! (大きな鳥!) (X: 2..49, Z: 14..35)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        # Leading golden-and-cobalt wing spar sweeping high & wide!
        draw_6conn_line(grid, (bx + sign * 4, 17, 19), (bx + sign * 14, 15, 29), 1, pad=(0, 1, 1))
        draw_6conn_line(grid, (bx + sign * 14, 15, 29), (bx + sign * 24, 13, 33), 3, pad=(0, 0, 1))
        # Sweeping layered primary wing feathers!
        for tip_x, tip_z, col_w in [(24, 28, 1), (22, 22, 2), (18, 17, 1), (13, 13, 2)]:
            draw_6conn_line(grid, (bx + sign * 5, 16, 17), (bx + sign * tip_x, 12, tip_z), col_w, pad=(0, 0, 1))
            fill_box(grid, bx + sign * tip_x, bx + sign * tip_x, 12, 13, tip_z, tip_z + 1, 9)

    # Fierce Cobalt-Blue Thunder-Eagle Head, Hooked Golden Beak & Crimson Crest! (Z: 20..33)
    fill_sym_box(grid, 0, 3, 18, 25, 20, 27, 1)   # Cobalt-blue raptor neck & head
    fill_sym_box(grid, 0, 2, 25, 31, 22, 25, 3)   # Powerful hooked golden eagle beak!
    fill_sym_box(grid, 0, 1, 30, 32, 20, 23, 3)   # Sharp hooked beak tip!
    fill_sym_box(grid, 2, 3, 24, 25, 25, 26, 9)   # Blazing electric-yellow raptor eyes!
    # Sweeping Crimson Thunder-Crest Plume on Head!
    fill_sym_box(grid, 0, 2, 17, 25, 27, 30, 5)
    draw_6conn_line(grid, (cx_r, 18, 29), (cx_r, 13, 33), 5, pad=(1, 0, 0))
    fill_sym_box(grid, 0, 1, 13, 15, 32, 33, 9)   # Lightning crest tip!

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


def render_preview(models, title_banner, out_path):
    n = len(models)
    cw = 24 + n * 398 + (n - 1) * 16 + 24
    canvas = Image.new("RGBA", (cw, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, cw, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (cw, gy)], fill=(28, 34, 48, 255), width=1)
    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(models):
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


if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "leizhenzi_a.vox")
    v_b = export_vox(model_b, "leizhenzi_b.vox")
    v_c = export_vox(model_c, "leizhenzi_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview(
        [
            ("1. LEIZHENZI (CHARACTER)", model_a, v_a, 28, 18),
            ("2. LEIZHENZI ROBOT", model_b, v_b, 28, 18),
            ("3. THUNDER BIRD (BEAST)", model_c, v_c, 34, 22),
        ],
        "CLASSICS ROBO #13: LEIZHENZI (FENGSHEN) - 3-FORM TRANSFORMATION",
        "preview_leizhenzi.png",
    )
    print(f"leizhenzi: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}), "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}), "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
