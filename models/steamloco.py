import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (36, 38, 44, 255),     # Locomotive Black Boiler / Cab
    2: (66, 70, 80, 255),     # Charcoal Iron Shading / Smoke Deflectors
    3: (228, 178, 48, 255),   # Polished Brass Bands / Whistle / Number Plate
    4: (196, 38, 40, 255),    # Crimson Driving Wheels & Buffer Beam
    5: (190, 200, 212, 255),  # Polished Steel Connecting Rods & Rims
    6: (255, 112, 26, 255),   # Furnace Firebox Orange Glow
    7: (255, 224, 92, 255),   # Warm Headlight & Robot Eyes
    8: (22, 22, 26, 255),     # Coal Pile & Deep Iron Shadow
    9: (234, 240, 248, 255),  # Puffing White Steam
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


def fill_drive_wheel_sym(grid, x_off, yc, zc, r, col_spoke=4, col_rim=5):
    """Fill symmetric spoked steam locomotive driving wheels."""
    for dy in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d2 = dy * dy + dz * dz
            if d2 <= r * r + 1:
                c = col_rim if d2 >= r * r - 1 else col_spoke
                fill_sym_box(grid, x_off, x_off, yc + dy, yc + dy, zc + dz, zc + dz, c)
    fill_sym_box(grid, x_off, x_off, yc, yc, zc, zc, 3)  # Brass axle hub


# ==========================================
# FORM A: STEAM LOCOMOTIVE (16 x 46 x 19)
# ==========================================
def build_a():
    grid = np.zeros((16, 46, 19), dtype=np.uint8)

    # --- RUNNING CHASSIS & COWCATCHER (Y: 2..44, Z: 1..4) ---
    fill_sym_box(grid, 0, 2, 3, 41, 2, 4, 8)      # Heavy iron frame
    fill_sym_box(grid, 0, 1, 4, 39, 2, 3, 0)      # Hollow chassis core
    # Crimson front buffer beam & slatted cowcatcher (pilot)
    fill_sym_box(grid, 0, 4, 40, 41, 2, 4, 4)
    fill_sym_box(grid, 0, 3, 42, 43, 1, 2, 4)
    fill_sym_box(grid, 0, 2, 44, 44, 1, 1, 5)
    fill_sym_box(grid, 1, 1, 42, 43, 1, 2, 1)     # Cowcatcher slats
    fill_sym_box(grid, 3, 3, 42, 42, 1, 2, 1)
    # Front piston cylinders
    fill_sym_box(grid, 3, 4, 34, 38, 2, 4, 2)
    fill_sym_box(grid, 4, 4, 38, 38, 3, 3, 3)

    # --- ICONIC RED-SPOKED DRIVING WHEELS & STEEL CONNECTING RODS ---
    fill_drive_wheel_sym(grid, 4, 31, 2, 2)
    fill_drive_wheel_sym(grid, 4, 25, 2, 2)
    fill_drive_wheel_sym(grid, 4, 19, 2, 2)
    # Small pony & tender wheels
    fill_drive_wheel_sym(grid, 4, 37, 1, 1, col_spoke=4, col_rim=5)
    fill_drive_wheel_sym(grid, 4, 10, 1, 1, col_spoke=2, col_rim=5)
    fill_drive_wheel_sym(grid, 4, 5, 1, 1, col_spoke=2, col_rim=5)
    # Gleaming horizontal steel connecting rod linking all 3 driving wheels!
    fill_sym_box(grid, 5, 5, 19, 36, 2, 2, 5)

    # --- CYLINDRICAL BLACK BOILER WITH BRASS BANDS (Y: 20..40, Z: 5..12) ---
    fill_sym_box(grid, 0, 3, 20, 39, 6, 10, 1)
    fill_sym_box(grid, 0, 2, 20, 39, 5, 11, 1)
    fill_sym_box(grid, 0, 2, 21, 38, 6, 10, 0)    # Hollow boiler interior
    fill_sym_box(grid, 0, 1, 20, 39, 12, 12, 2)   # Boiler top highlight
    # Gleaming brass boiler bands!
    for by in (24, 29, 34, 38):
        fill_sym_box(grid, 3, 3, by, by, 6, 10, 3)
        fill_sym_box(grid, 0, 2, by, by, 11, 11, 3)
    # Smokebox front door, brass number plate & glowing golden headlight!
    fill_sym_box(grid, 0, 2, 40, 40, 6, 10, 2)
    fill_sym_box(grid, 0, 1, 40, 40, 7, 9, 1)
    fill_sym_box(grid, 0, 1, 41, 41, 7, 7, 3)     # Brass number plate (D51!)
    fill_sym_box(grid, 0, 0, 40, 41, 11, 12, 3)   # Brass headlight casing
    fill_sym_box(grid, 0, 0, 41, 41, 11, 12, 7)   # Glowing headlight!
    # Twin D51 Smoke Deflectors flanking front smokebox!
    fill_sym_box(grid, 4, 4, 35, 40, 5, 11, 2)
    fill_sym_box(grid, 4, 4, 35, 40, 11, 11, 3)   # Brass top edge trim

    # --- SMOKESTACK, STEAM DOME & PUFFING STEAM (Z: 12..18) ---
    fill_sym_box(grid, 0, 1, 35, 37, 12, 15, 1)   # Tall smokestack
    fill_sym_box(grid, 0, 1, 35, 37, 15, 15, 3)   # Brass funnel rim
    fill_sym_box(grid, 0, 1, 28, 31, 12, 14, 1)   # Steam dome
    fill_sym_box(grid, 0, 0, 29, 30, 14, 14, 3)   # Brass whistle
    # Cute white steam puffs trailing back from stack!
    fill_sym_box(grid, 0, 0, 35, 36, 16, 17, 9)
    fill_sym_box(grid, 0, 1, 32, 34, 17, 18, 9)

    # --- ENGINEER'S CAB & FIREBOX GLOW (Y: 13..20, Z: 5..14) ---
    fill_sym_box(grid, 0, 4, 13, 20, 5, 12, 1)
    fill_sym_box(grid, 0, 3, 14, 19, 6, 11, 0)    # Hollow cab
    fill_sym_box(grid, 0, 4, 12, 20, 13, 13, 2)   # Overhanging cab roof
    fill_sym_box(grid, 0, 3, 13, 19, 14, 14, 2)
    fill_sym_box(grid, 4, 4, 15, 18, 9, 11, 6)    # Glowing orange cab window!
    fill_sym_box(grid, 4, 4, 16, 17, 10, 10, 7)
    fill_sym_box(grid, 4, 4, 14, 19, 7, 7, 3)     # Brass cab stripe

    # --- COAL TENDER (Y: 2..11, Z: 4..11) ---
    fill_sym_box(grid, 0, 4, 2, 11, 4, 10, 1)
    fill_sym_box(grid, 0, 3, 3, 10, 5, 8, 0)      # Hollow tender
    fill_sym_box(grid, 4, 4, 2, 11, 6, 6, 4)      # Red tender stripe
    fill_sym_box(grid, 0, 3, 3, 10, 9, 10, 8)     # Mound of black coal
    fill_sym_box(grid, 0, 2, 4, 9, 11, 11, 8)

    return grid


# ==========================================
# FORM B: STEAM LOCOMOTIVE ROBOT (30 x 22 x 39)
# ==========================================
def build_b():
    grid = np.zeros((30, 22, 39), dtype=np.uint8)

    # --- FEET (Z: 0..3) - Split Slatted Red/Black Cowcatcher Boots! ---
    fill_sym_box(grid, 2, 4, 7, 15, 0, 1, 1)
    fill_sym_box(grid, 2, 4, 12, 16, 1, 2, 4)     # Crimson cowcatcher toes!
    fill_sym_box(grid, 3, 3, 15, 17, 0, 1, 5)     # Steel pilot spikes
    fill_sym_box(grid, 2, 4, 7, 8, 0, 2, 2)

    # --- LOWER LEGS (Z: 3..14) - Coal Tender Shins + Red Driving Wheels! ---
    fill_sym_box(grid, 2, 4, 9, 13, 3, 13, 1)
    fill_sym_box(grid, 3, 3, 13, 14, 4, 11, 2)
    fill_sym_box(grid, 2, 3, 13, 14, 11, 14, 3)   # Brass knee caps
    fill_sym_box(grid, 3, 3, 14, 14, 12, 13, 4)   # Red knee badge
    # Iconic red-spoked driving wheels mounted on outer calves!
    fill_drive_wheel_sym(grid, 5, 11, 6, 2)
    fill_drive_wheel_sym(grid, 5, 11, 11, 2)
    fill_sym_box(grid, 6, 6, 11, 11, 6, 11, 5)    # Vertical steel connecting rod!

    # --- THIGHS (Z: 14..19) - Steel Piston Thighs ---
    fill_sym_box(grid, 2, 3, 9, 12, 14, 19, 2)
    fill_sym_box(grid, 3, 3, 12, 13, 15, 18, 5)   # Steel piston rods
    fill_sym_box(grid, 2, 3, 10, 11, 14, 15, 8)

    # --- WAIST / PELVIS (Z: 19..22) - Crimson Buffer Beam Waist! ---
    fill_sym_box(grid, 0, 4, 9, 13, 19, 21, 1)
    fill_sym_box(grid, 0, 4, 13, 14, 20, 21, 4)   # Red buffer beam belt
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 3)   # Brass buckle plate
    fill_sym_box(grid, 0, 0, 15, 15, 20, 21, 6)   # Furnace ember core
    fill_sym_box(grid, 4, 4, 10, 12, 19, 21, 2)

    # --- TORSO / CHEST (Z: 22..31) - Cylindrical Boiler, Brass Bands & Headlight! ---
    fill_sym_box(grid, 0, 4, 8, 14, 22, 31, 1)
    # Glowing orange firebox grate at abdomen! (Z: 22..25)
    fill_sym_box(grid, 0, 2, 14, 15, 22, 24, 6)
    fill_sym_box(grid, 0, 1, 15, 15, 23, 23, 7)
    fill_sym_box(grid, 1, 1, 15, 15, 22, 24, 8)   # Furnace grate bars
    # Rounded Boiler Drum Chest with Brass Rings & Headlight Core! (Z: 25..31)
    fill_sym_box(grid, 0, 4, 14, 16, 25, 30, 1)
    fill_sym_box(grid, 0, 3, 16, 17, 26, 29, 2)   # Smokebox front door!
    fill_sym_box(grid, 0, 1, 17, 18, 27, 29, 3)   # Brass headlight rim
    fill_sym_box(grid, 0, 0, 18, 18, 28, 28, 7)   # Glowing locomotive headlight!
    # Brass boiler bands wrapping chest sides
    fill_sym_box(grid, 3, 4, 14, 16, 26, 26, 3)
    fill_sym_box(grid, 3, 4, 14, 16, 29, 29, 3)
    fill_sym_box(grid, 0, 2, 14, 16, 31, 31, 3)   # Brass collar trim

    # --- BACKPACK (Y: 4..7) - Steam Boiler Back + Tall Smokestack with Steam! ---
    fill_sym_box(grid, 0, 3, 5, 7, 22, 30, 2)
    fill_sym_box(grid, 0, 2, 4, 5, 24, 28, 8)     # Coal hopper backpack
    # Twin tall smokestacks rising proudly behind shoulders!
    fill_sym_box(grid, 3, 4, 6, 7, 30, 36, 1)
    fill_sym_box(grid, 3, 4, 6, 7, 36, 36, 3)     # Brass stack rims
    fill_sym_box(grid, 3, 4, 5, 6, 37, 38, 9)     # White steam puffs!

    # --- SHOULDERS & ARMS (Z: 14..33) - D51 Smoke Deflectors + Piston Forearms! ---
    # Sweeping D51 Smoke Deflector Pauldrons!
    fill_sym_box(grid, 5, 9, 9, 14, 27, 32, 2)
    fill_sym_box(grid, 9, 9, 9, 14, 27, 33, 1)    # High vertical deflector fin!
    fill_sym_box(grid, 9, 9, 9, 14, 33, 33, 3)    # Brass edge trim
    fill_sym_box(grid, 6, 8, 13, 14, 29, 30, 4)   # Red shoulder accent
    # Upper arms (steel piston joints)
    fill_sym_box(grid, 6, 7, 10, 12, 22, 26, 8)
    fill_sym_box(grid, 7, 7, 10, 12, 23, 25, 5)
    # Forearms (black cab armor + gleaming steel connecting-rod boosters!)
    fill_sym_box(grid, 6, 8, 9, 13, 16, 21, 1)
    fill_sym_box(grid, 9, 9, 10, 12, 16, 22, 5)   # Steel connecting rod!
    fill_sym_box(grid, 6, 8, 13, 14, 17, 18, 3)   # Brass wrist cuffs
    # Heavy iron fists
    fill_sym_box(grid, 6, 7, 10, 12, 13, 15, 2)
    fill_sym_box(grid, 6, 7, 13, 13, 14, 15, 3)   # Brass knuckles!
    # Right hand Steam-Hammer / Furnace Wrench
    fill_box(grid, 21, 22, 13, 20, 14, 15, 5)
    fill_box(grid, 20, 23, 18, 21, 13, 17, 1)
    fill_box(grid, 20, 23, 19, 20, 14, 16, 6)     # Glowing furnace hammer head!

    # --- HEAD (Z: 32..38) - Iron Engineer-Knight Helmet ---
    fill_sym_box(grid, 0, 1, 10, 11, 31, 32, 8)
    fill_sym_box(grid, 0, 2, 9, 13, 32, 36, 1)    # Black iron helmet
    fill_sym_box(grid, 0, 2, 10, 14, 36, 37, 2)   # Engineer cap brim
    fill_sym_box(grid, 0, 1, 13, 14, 34, 34, 7)   # Glowing ember-yellow eyes
    fill_sym_box(grid, 0, 1, 13, 14, 32, 33, 5)   # Steel iron faceplate
    fill_sym_box(grid, 0, 0, 13, 14, 36, 38, 3)   # Brass loco number-plate crest!
    fill_sym_box(grid, 3, 3, 10, 11, 34, 36, 3)   # Brass whistle ear vents

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
    v_a = export_vox(model_a, "steamloco_a.vox")
    v_b = export_vox(model_b, "steamloco_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: STEAM LOCOMOTIVE -> IRON ROBOT",
        "1. STEAM LOCOMOTIVE (D51)",
        "2. STEAM LOCO ROBOT",
        "preview_steamloco.png",
        yaw_a=42, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"steamloco: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
