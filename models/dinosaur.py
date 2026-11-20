import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (186, 48, 42, 255),    # Crimson T-Rex Hide / Scales
    2: (122, 26, 30, 255),    # Deep Maroon Dorsal Spine / Stripes
    3: (228, 212, 174, 255),  # Warm Cream Underbelly / Lower Jaw
    4: (246, 242, 230, 255),  # Bone Ivory Razor Teeth & Claws
    5: (52, 56, 64, 255),     # Dark Metallic Mechanical Frame / Joints
    6: (255, 192, 36, 255),   # Fierce Amber Dino Eyes / Chest Core
    7: (44, 204, 120, 255),   # Emerald Tech Robot Visor
    8: (116, 122, 134, 255),  # Gunmetal Steel Ribbing / Plates
    9: (32, 32, 38, 255),     # Obsidian Talons / Mouth Interior
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(x0, x1)), min(X - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


# ==========================================
# FORM A: TYRANNOSAURUS REX (18 x 46 x 24)
# ==========================================
def build_a():
    grid = np.zeros((18, 46, 24), dtype=np.uint8)

    # --- POWERFUL HIND LEGS & 3-TOED CLAWED FEET (Z: 0..14) ---
    # Feet with 3 splayed claws
    fill_sym_box(grid, 3, 6, 18, 23, 0, 1, 1)
    fill_sym_box(grid, 3, 3, 24, 25, 0, 1, 4)    # Inner ivory claw
    fill_sym_box(grid, 5, 5, 24, 26, 0, 1, 4)    # Center ivory claw
    fill_sym_box(grid, 6, 6, 23, 24, 0, 1, 4)    # Outer ivory claw
    fill_sym_box(grid, 4, 5, 17, 18, 0, 1, 9)    # Heel dewclaw
    # Reverse-jointed lower shin angling back-up
    for step in range(5):
        fill_sym_box(grid, 4, 5, 19 - step // 2, 21 - step // 2, 2 + step, 3 + step, 1)
    # Massive muscular T-Rex thighs!
    fill_sym_box(grid, 3, 6, 17, 23, 7, 13, 1)
    fill_sym_box(grid, 6, 6, 18, 22, 10, 12, 2)  # Maroon tiger stripes
    fill_sym_box(grid, 4, 5, 19, 22, 7, 8, 3)    # Cream underside

    # --- BULKY HORIZONTAL TORSO (Y: 16..31, Z: 9..17) ---
    fill_sym_box(grid, 0, 3, 16, 29, 10, 16, 1)
    fill_sym_box(grid, 0, 2, 18, 28, 11, 15, 0)  # Hollow torso core
    fill_sym_box(grid, 0, 2, 17, 30, 9, 10, 3)   # Warm cream ribbed belly
    fill_sym_box(grid, 0, 1, 17, 29, 17, 17, 2)  # Deep maroon dorsal back
    # Dorsal spines along back
    for sy in range(18, 30, 3):
        fill_sym_box(grid, 0, 0, sy, sy + 1, 18, 18, 2)
    # Tiny iconic T-Rex forelimbs!
    fill_sym_box(grid, 3, 4, 28, 30, 9, 11, 1)
    fill_sym_box(grid, 3, 4, 30, 32, 8, 9, 1)
    fill_sym_box(grid, 3, 4, 33, 33, 8, 8, 4)    # Tiny 2-clawed hands

    # --- MUSCULAR S-CURVED NECK (Y: 28..35, Z: 13..20) ---
    for step in range(5):
        fill_sym_box(grid, 0, 2, 28 + step, 32 + step, 13 + step, 17 + step, 1)
        fill_sym_box(grid, 0, 1, 29 + step, 31 + step, 12 + step, 13 + step, 3)
        fill_sym_box(grid, 0, 0, 28 + step, 30 + step, 18 + step, 18 + step, 2)

    # --- MASSIVE T-REX HEAD WITH OPEN JAWS & TEETH (Y: 33..45, Z: 14..23) ---
    # Upper cranium & snout
    fill_sym_box(grid, 0, 3, 33, 38, 18, 22, 1)
    fill_sym_box(grid, 0, 2, 39, 44, 18, 21, 1)
    fill_sym_box(grid, 0, 1, 45, 45, 18, 20, 1)
    fill_sym_box(grid, 2, 3, 36, 39, 22, 23, 2)  # Fierce maroon brow ridges!
    fill_sym_box(grid, 3, 3, 36, 37, 20, 21, 6)  # Glowing amber eyes!
    fill_sym_box(grid, 2, 2, 43, 44, 20, 20, 9)  # Nostrils
    # Upper ivory razor teeth!
    for ty in (38, 40, 42, 44):
        fill_sym_box(grid, 2, 2, ty, ty, 17, 17, 4)
    # Open mouth interior & fierce lower jaw!
    fill_sym_box(grid, 0, 1, 35, 38, 16, 17, 9)
    fill_sym_box(grid, 0, 2, 34, 43, 14, 15, 3)  # Cream lower jaw
    fill_sym_box(grid, 0, 2, 35, 42, 15, 15, 1)  # Red jaw lip
    for ty in (39, 41, 43):
        fill_sym_box(grid, 2, 2, ty, ty, 16, 16, 4)  # Lower teeth

    # --- LONG COUNTER-BALANCING TAIL (Y: 0..16, Z: 11..16) ---
    fill_sym_box(grid, 0, 2, 11, 16, 11, 15, 1)
    fill_sym_box(grid, 0, 1, 11, 16, 10, 11, 3)
    fill_sym_box(grid, 0, 1, 5, 10, 12, 15, 1)
    fill_sym_box(grid, 0, 1, 5, 10, 11, 11, 3)
    fill_sym_box(grid, 0, 0, 0, 4, 13, 14, 1)
    # Tail dorsal stripes & spines
    for sy in range(2, 16, 3):
        fill_sym_box(grid, 0, 0, sy, sy + 1, 16 if sy >= 11 else 15, 16 if sy >= 11 else 15, 2)

    return grid


# ==========================================
# FORM B: T-REX BEAST ROBOT (32 x 28 x 39)
# ==========================================
def build_b():
    grid = np.zeros((32, 28, 39), dtype=np.uint8)

    # --- FEET (Z: 0..2) - Clawed T-Rex Dino Feet! ---
    fill_sym_box(grid, 2, 5, 11, 18, 0, 1, 5)
    fill_sym_box(grid, 2, 5, 12, 18, 1, 2, 1)
    # 3 Ivory dino toe talons in front!
    fill_sym_box(grid, 2, 2, 19, 20, 0, 1, 4)
    fill_sym_box(grid, 4, 4, 19, 21, 0, 1, 4)
    fill_sym_box(grid, 5, 5, 18, 19, 0, 1, 4)
    fill_sym_box(grid, 3, 4, 10, 11, 0, 1, 9)    # Heel spur

    # --- LOWER LEGS (Z: 3..14) - Muscular T-Rex Hind Legs! ---
    fill_sym_box(grid, 2, 5, 12, 17, 3, 13, 1)
    fill_sym_box(grid, 5, 5, 13, 16, 5, 11, 2)   # Maroon scale stripes
    fill_sym_box(grid, 3, 4, 17, 18, 5, 10, 8)   # Metallic shin guard
    fill_sym_box(grid, 3, 4, 17, 18, 11, 14, 2)  # Maroon knee spikes
    fill_sym_box(grid, 3, 4, 18, 19, 12, 13, 4)  # Ivory knee fang

    # --- THIGHS (Z: 14..19) - Cream & Metallic Dino Thighs ---
    fill_sym_box(grid, 2, 4, 12, 16, 14, 19, 3)
    fill_sym_box(grid, 2, 3, 13, 15, 14, 15, 5)
    fill_sym_box(grid, 4, 4, 13, 15, 15, 18, 1)

    # --- WAIST / PELVIS (Z: 19..22) + TINY T-REX ARMS FOLDED AT RIBS! ---
    fill_sym_box(grid, 0, 4, 12, 16, 19, 21, 5)
    fill_sym_box(grid, 0, 4, 16, 17, 20, 21, 1)
    fill_sym_box(grid, 0, 1, 16, 18, 19, 22, 2)
    fill_sym_box(grid, 0, 0, 18, 18, 20, 21, 6)  # Amber belt core
    # Folded tiny T-Rex claws tucked adorably on waist flanks!
    fill_sym_box(grid, 4, 5, 16, 18, 21, 22, 1)
    fill_sym_box(grid, 4, 5, 19, 19, 21, 21, 4)

    # --- TORSO / CHEST (Z: 22..31) - Dino Ribcage & Cream Underbelly! ---
    fill_sym_box(grid, 0, 5, 11, 17, 22, 31, 1)
    fill_sym_box(grid, 0, 3, 16, 18, 22, 25, 3)  # Cream dino belly abs
    fill_sym_box(grid, 0, 4, 16, 18, 26, 30, 8)  # Metallic ribcage chest armor
    fill_sym_box(grid, 1, 3, 18, 18, 26, 29, 3)  # Cream/bone rib slats
    fill_sym_box(grid, 0, 1, 18, 19, 27, 29, 6)  # Glowing amber beast reactor!
    fill_sym_box(grid, 3, 5, 16, 18, 28, 31, 2)  # Maroon armored chest ridges

    # --- LONG SEGMENTED T-REX TAIL EXTENDING FROM BACK WAIST (Y: 0..11) ---
    # Sweeps dramatically left (-X) so it is proudly visible in front 3/4 view too!
    fill_box(grid, 14, 17, 8, 11, 18, 22, 1)
    fill_box(grid, 14, 17, 8, 11, 22, 23, 2)     # Dorsal spine ridge
    fill_box(grid, 11, 15, 5, 8, 16, 20, 1)
    fill_box(grid, 11, 15, 5, 8, 15, 16, 3)      # Cream underside
    fill_box(grid, 12, 14, 5, 8, 20, 21, 2)
    fill_box(grid, 7, 11, 3, 6, 14, 17, 1)
    fill_box(grid, 8, 10, 3, 6, 17, 18, 2)
    fill_box(grid, 4, 7, 2, 5, 13, 15, 1)
    fill_box(grid, 2, 4, 3, 5, 14, 15, 2)        # Tail tip sweeping outward!
    # Dorsal back-spine plates on upper back
    fill_sym_box(grid, 0, 2, 9, 10, 23, 30, 5)
    for sz in (24, 27, 30):
        fill_sym_box(grid, 0, 0, 8, 9, sz, sz + 1, 2)

    # --- RIGHT ARM (+X): ENTIRE T-REX HEAD AS CHOMP-CANNON FOREARM! ---
    # Right shoulder (neck scales + maroon dorsal spikes)
    fill_box(grid, 21, 25, 12, 17, 27, 32, 1)
    fill_box(grid, 22, 25, 13, 16, 32, 33, 2)
    fill_box(grid, 24, 25, 14, 15, 33, 34, 4)    # Shoulder spike
    # Right upper arm (metallic beast joint)
    fill_box(grid, 22, 24, 13, 16, 22, 26, 5)
    fill_box(grid, 22, 24, 13, 16, 23, 25, 8)
    # MASSIVE T-REX HEAD FOREARM facing forward (+Y)! (X: 21..27, Y: 14..26, Z: 15..22)
    fill_box(grid, 21, 27, 14, 20, 18, 22, 1)    # Cranium
    fill_box(grid, 22, 26, 21, 26, 19, 21, 1)    # Upper snout
    fill_box(grid, 22, 26, 17, 20, 22, 22, 2)    # Maroon brow ridge
    fill_box(grid, 21, 21, 18, 19, 20, 21, 6)    # Fierce amber eyes on both sides!
    fill_box(grid, 27, 27, 18, 19, 20, 21, 6)
    # Upper ivory teeth
    for ty in (21, 23, 25):
        fill_box(grid, 22, 22, ty, ty, 18, 18, 4)
        fill_box(grid, 26, 26, ty, ty, 18, 18, 4)
    # Open dark mouth + Cream lower jaw + Lower teeth!
    fill_box(grid, 23, 25, 18, 22, 17, 18, 9)
    fill_box(grid, 22, 26, 16, 25, 15, 16, 3)    # Lower jaw
    for ty in (22, 24):
        fill_box(grid, 22, 22, ty, ty, 17, 17, 4)
        fill_box(grid, 26, 26, ty, ty, 17, 17, 4)

    # --- LEFT ARM (-X): ARMORED DINO CLAW + TAIL-BLADE SHIELD ---
    fill_box(grid, 6, 10, 12, 17, 27, 32, 1)     # Left shoulder
    fill_box(grid, 6, 9, 13, 16, 32, 33, 2)
    fill_box(grid, 7, 9, 13, 16, 22, 26, 5)      # Upper arm
    fill_box(grid, 7, 10, 12, 17, 16, 21, 1)     # Forearm
    fill_box(grid, 6, 7, 13, 17, 16, 21, 2)      # Maroon scale shield
    fill_box(grid, 6, 6, 15, 17, 17, 20, 4)      # Bone-claw edge on forearm
    fill_box(grid, 8, 9, 13, 16, 13, 15, 5)      # Left fist
    fill_box(grid, 8, 9, 16, 19, 13, 15, 4)      # Twin wrist bone claws!

    # --- HEAD (Z: 32..38) - Dino-Knight Helmet with Emerald Visor ---
    fill_sym_box(grid, 0, 1, 13, 15, 31, 32, 5)
    fill_sym_box(grid, 0, 2, 12, 16, 32, 36, 5)  # Dark metallic helmet
    fill_sym_box(grid, 0, 2, 13, 16, 36, 37, 1)  # Crimson dino crown
    fill_sym_box(grid, 0, 0, 13, 17, 37, 38, 2)  # Maroon dinosaur crest
    fill_sym_box(grid, 0, 1, 16, 17, 34, 35, 7)  # Glowing emerald tech visor
    fill_sym_box(grid, 0, 1, 16, 17, 32, 33, 8)  # Steel mouthplate
    fill_sym_box(grid, 2, 3, 14, 16, 33, 35, 4)  # Ivory cheek fangs

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=24, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "dinosaur_a.vox")
    v_b = export_vox(model_b, "dinosaur_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: TYRANNOSAURUS REX -> BEAST ROBOT",
        "1. TYRANNOSAURUS REX",
        "2. T-REX BEAST ROBOT",
        "preview_dinosaur.png",
        yaw_a=48, pitch_a=20, yaw_b=34, pitch_b=20,
    )
    print(f"dinosaur: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
