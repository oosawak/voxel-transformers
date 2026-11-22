import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Tu Xingsun / Doko-son (土行孫) -> Compact Subterranean Burrowing-Drill Robot!
# Compact short stature (小柄な体格!), Golden Binding-Immortal Rope (捆仙縄!), earth-burrowing drill motif!
PALETTE = {
    1: (176, 114, 52, 255),   # Earthy Terracotta-Ochre Tunic & Burrower Armor
    2: (116, 68, 34, 255),    # Deep Soil-Brown Boots, Vest & Shading
    3: (248, 206, 48, 255),   # Gleaming Golden Binding-Immortal Rope (捆仙縄!) & Drills
    4: (212, 152, 28, 255),   # Amber Rope Coil Shading
    5: (64, 72, 88, 255),     # Heavy Subterranean Iron Drill-Claws & Frame
    6: (186, 198, 214, 255),  # Honed Steel Burrowing Auger Tips
    7: (250, 216, 188, 255),  # Crafty Compact Warrior Face
    8: (192, 46, 38, 255),    # Crimson Bandana & Belt Knot
    9: (102, 246, 158, 255),  # Bright Subterranean-Radar Emerald Eyes & Goggles!
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


def draw_rope_loop_xy(grid, cx, cy, cz, r=3):
    """Draw a 6-connected glowing golden coil of Binding-Immortal Rope (捆仙縄!)."""
    X, Y, Z = grid.shape
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d = np.sqrt(dx * dx + dz * dz)
            if r - 1.15 <= d <= r + 0.35:
                x, z = cx + dx, cz + dz
                if 0 <= x < X and 0 <= cy < Y and 0 <= z < Z:
                    grid[x, cy, z] = 3 if (dx + dz) % 2 == 0 else 4


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
# FORM A: TU XINGSUN (COMPACT SHORT STATURE + BINDING ROPE) (34 x 24 x 32)
# ============================================================
def build_a():
    grid = np.zeros((34, 24, 32), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 16
    cx_r = X // 2      # 17

    # Earth-Mound Burrow Base + Short Agile Stance (小柄な体格!) (Z: 0..10)
    fill_sym_box(grid, 0, 6, 9, 16, 0, 1, 2)      # Freshly dug soil rim at feet (地面に潜る術!)
    fill_sym_box(grid, 2, 4, 10, 15, 2, 4, 5)     # Heavy digging boots
    fill_sym_box(grid, 2, 4, 11, 14, 5, 9, 1)     # Short ochre trousers

    # Compact Sturdy Torso & Coiled GOLDEN BINDING-IMMORTAL ROPE (捆仙縄!) (Z: 9..19)
    fill_sym_box(grid, 0, 4, 10, 15, 9, 19, 1)    # Earthy ochre tunic
    fill_sym_box(grid, 0, 5, 10, 16, 10, 11, 8)   # Crimson waist sash
    fill_sym_box(grid, 0, 4, 9, 10, 11, 18, 2)    # Digging pack on back
    # Diagonal Golden Binding-Immortal Rope sash coiled across chest!
    for i in range(8):
        rx = cx_l - 4 + i
        rz = 11 + i
        fill_box(grid, rx, rx + 1, 15, 16, rz, rz, 3)
        fill_box(grid, rx, rx + 1, 9, 10, rz, rz, 3)

    # Compact Arms: Iron Digging Claw (Left) + Coiled Golden Binding-Rope Lasso (Right)!
    fill_box(grid, cx_l - 7, cx_l - 5, 11, 15, 13, 18, 1)
    fill_box(grid, cx_l - 8, cx_l - 6, 14, 17, 12, 14, 5)   # Iron burrowing claw
    fill_box(grid, cx_l - 8, cx_l - 6, 17, 19, 12, 13, 6)   # Steel digging tines!
    fill_box(grid, cx_r + 5, cx_r + 7, 11, 15, 13, 18, 1)
    fill_box(grid, cx_r + 6, cx_r + 9, 14, 17, 13, 15, 7)   # Hand holding Binding-Immortal Rope!
    draw_rope_loop_xy(grid, cx_r + 10, 17, 16, r=3)         # Iconic coiled golden rope loop!
    fill_box(grid, cx_r + 7, cx_r + 8, 17, 17, 14, 15, 3)   # Connects solidly into hand!

    # Expressive Compact Head, Crimson Bandana & Burrower Goggles/Conical Cap! (Z: 19..30)
    fill_sym_box(grid, 0, 3, 10, 16, 19, 25, 7)   # Expressive cheeky face
    fill_sym_box(grid, 1, 2, 16, 16, 22, 23, 9)   # Sharp clever eyes
    fill_sym_box(grid, 0, 1, 16, 17, 19, 20, 2)   # Pointed goatee
    fill_sym_box(grid, 0, 4, 10, 16, 25, 26, 8)   # Crimson headband
    fill_sym_box(grid, 0, 3, 11, 15, 27, 29, 2)   # Pointed earth-burrower cap!
    fill_sym_box(grid, 0, 1, 12, 14, 30, 31, 6)   # Mini steel drill-tip on cap!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: TU XINGSUN COMPACT SUBTERRANEAN DRILL ROBOT (小柄ロボ!) (46 x 26 x 36)
# ============================================================
def build_b():
    grid = np.zeros((46, 26, 36), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 22
    cx_r = X // 2      # 23

    # Heavy Excavator Tread-Feet & Compact Stocky Legs (小柄な体格ロボ!) (Z: 0..11)
    fill_sym_box(grid, 2, 6, 9, 18, 0, 3, 5)      # Heavy subterranean tread-boots!
    fill_sym_box(grid, 3, 5, 18, 19, 0, 2, 6)     # Steel rock-cleats
    fill_sym_box(grid, 2, 5, 11, 16, 4, 10, 1)    # Compact ochre greaves
    fill_sym_box(grid, 3, 4, 16, 17, 5, 9, 3)     # Gold stripes
    fill_sym_box(grid, 2, 5, 16, 18, 9, 11, 5)    # Armored knee dozers

    # Stocky Compact Earth-Driller Torso & Twin Rear Drill-Packs (Z: 11..25)
    fill_sym_box(grid, 0, 6, 10, 17, 11, 15, 2)   # Heavy waist
    fill_sym_box(grid, 0, 2, 17, 18, 12, 14, 8)   # Crimson belt emblem
    fill_sym_box(grid, 0, 7, 10, 18, 15, 24, 1)   # Broad compact burrowing chest!
    fill_sym_box(grid, 1, 5, 18, 19, 16, 23, 2)   # Heavy armored chestplate
    fill_sym_box(grid, 0, 2, 19, 20, 18, 21, 3)   # Golden rope-winch chest core!
    fill_sym_box(grid, 0, 1, 20, 20, 19, 20, 9)   # Glowing subterranean radar core!
    # Rear Twin Exhaust & Mole-Scoop Backpack
    fill_sym_box(grid, 0, 5, 7, 10, 15, 24, 5)
    fill_sym_box(grid, 3, 5, 6, 7, 17, 23, 3)

    # TWIN GIANT BURROWING DRILL-ARMS + GOLDEN BINDING-IMMORTAL ROPE! (Z: 11..28)
    fill_sym_box(grid, 7, 9, 12, 15, 20, 23, 5)
    fill_sym_box(grid, 8, 11, 11, 16, 19, 25, 1)  # Rugged earth-shaker pauldrons
    fill_sym_box(grid, 9, 12, 12, 15, 24, 26, 3)  # Gold shoulder guards
    # Left Arm (-X): GIANT CONICAL STEEL & GOLD EARTH-BURROWING DRILL! (地面に潜る術!)
    fill_box(grid, cx_l - 12, cx_l - 8, 12, 17, 14, 19, 5)
    fill_box(grid, cx_l - 13, cx_l - 9, 17, 20, 14, 18, 6)  # Drill base cone
    fill_box(grid, cx_l - 12, cx_l - 10, 21, 22, 15, 17, 3) # Spiraling gold drill bands!
    fill_box(grid, cx_l - 11, cx_l - 11, 23, 24, 16, 16, 6) # Sharp auger tip!
    # Right Arm (+X): Winch Gauntlet wielding Giant Golden BINDING-IMMORTAL ROPE (捆仙縄!)
    fill_box(grid, cx_r + 8, cx_r + 12, 12, 17, 14, 19, 5)
    fill_box(grid, cx_r + 10, cx_r + 13, 16, 20, 14, 18, 3) # Gold rope launcher
    draw_rope_loop_xy(grid, cx_r + 14, 20, 17, r=4)         # Giant golden Binding-Immortal Rope ring!

    # Compact Subterranean Robot Head WITH ROOF DRILL-SPIKE & EMERALD RADAR GOGGLES! (Z: 24..35)
    fill_sym_box(grid, 0, 4, 10, 18, 24, 30, 1)   # Stocky armored helm
    fill_sym_box(grid, 0, 3, 18, 19, 25, 26, 5)   # Heavy steel jaw
    fill_sym_box(grid, 0, 3, 18, 19, 27, 28, 9)   # Wide glowing emerald burrow-radar visor!
    fill_sym_box(grid, 0, 4, 11, 18, 29, 30, 8)   # Crimson bandana crest
    # Iconic Head-Mounted Burrowing Drill Cone!
    fill_sym_box(grid, 0, 2, 12, 16, 31, 32, 6)
    fill_sym_box(grid, 0, 1, 13, 15, 33, 34, 3)
    fill_sym_box(grid, 0, 0, 14, 14, 35, 35, 6)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM C: SUBTERRANEAN MOLE (もぐら — 小柄で大きな前足!) (32 x 32 x 22)
# ============================================================
def build_c():
    grid = np.zeros((32, 32, 22), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 15
    cx_r = X // 2      # 16

    # Freshly Dug Earth Mound Base grounded at Z=0..2 (地面に潜る術!)
    fill_sym_box(grid, 0, 9, 8, 24, 0, 1, 2)
    fill_sym_box(grid, 0, 7, 10, 22, 2, 2, 1)

    # Compact Plump Oval Mole Body (小柄な体格!) (Z: 2..15)
    fill_sym_box(grid, 0, 6, 9, 23, 3, 13, 2)     # Dark velvety soil-brown mole body!
    fill_sym_box(grid, 0, 5, 10, 22, 13, 15, 2)   # Rounded mole back
    fill_sym_box(grid, 0, 4, 12, 24, 3, 9, 1)     # Warm ochre belly fur
    # Tu Xingsun's Crimson Bandana & Coiled Golden Binding-Immortal Rope around neck!
    fill_sym_box(grid, 0, 6, 19, 21, 5, 15, 8)    # Crimson bandana collar
    fill_sym_box(grid, 0, 6, 17, 18, 6, 15, 3)    # Golden Binding-Immortal Rope coil!
    # Tiny stubby mole tail
    fill_sym_box(grid, 0, 1, 6, 9, 6, 8, 7)

    # ICONIC OVERSIZED BROAD PADDLE-LIKE DIGGING FOREPAWS! (大きな前足!) (Z: 2..9)
    fill_sym_box(grid, 6, 11, 18, 25, 3, 7, 7)    # Huge broad rosy-peach mole digging hands!
    fill_sym_box(grid, 7, 11, 24, 26, 3, 6, 5)    # Heavy iron knuckle plates
    # Four prominent sharp steel digging claws on each giant paw!
    for cx_off in (7, 9, 11):
        fill_sym_box(grid, cx_off, cx_off, 26, 29, 3, 5, 6)
    # Small hind feet tucked at rear
    fill_sym_box(grid, 5, 7, 10, 13, 2, 4, 7)

    # Pointed Mole Head, Rosy Cone Snout & Clever Emerald Goggle-Eyes! (Y: 22..31, Z: 6..18)
    fill_sym_box(grid, 0, 4, 22, 27, 6, 14, 2)    # Rounded mole head
    fill_sym_box(grid, 0, 2, 27, 30, 7, 11, 7)    # Pointed rosy-peach mole snout!
    fill_sym_box(grid, 0, 1, 30, 31, 8, 9, 8)     # Cute crimson mole nose tip!
    fill_sym_box(grid, 2, 3, 26, 27, 11, 12, 9)   # Bright emerald subterranean eyes!
    # Tiny steel burrowing cap-drill on top of mole head!
    fill_sym_box(grid, 0, 2, 22, 26, 14, 16, 5)
    fill_sym_box(grid, 0, 1, 23, 25, 17, 18, 3)
    fill_sym_box(grid, 0, 0, 24, 24, 19, 19, 6)

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
    v_a = export_vox(model_a, "tuxingsun_a.vox")
    v_b = export_vox(model_b, "tuxingsun_b.vox")
    v_c = export_vox(model_c, "tuxingsun_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview(
        [
            ("1. TU XINGSUN (CHARACTER)", model_a, v_a, 28, 18),
            ("2. TU XINGSUN ROBOT", model_b, v_b, 28, 18),
            ("3. SUBTERRANEAN MOLE (BEAST)", model_c, v_c, 38, 22),
        ],
        "CLASSICS ROBO #15: TU XINGSUN (FENGSHEN) - 3-FORM TRANSFORMATION",
        "preview_tuxingsun.png",
    )
    print(f"tuxingsun: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}), "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}), "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
