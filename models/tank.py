import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (96, 114, 72, 255),    # Olive Drab Main Armor
    2: (66, 80, 50, 255),     # Dark Olive Camo / Shadow Armor
    3: (166, 152, 112, 255),  # Sand Tan Camo / Trim
    4: (46, 50, 56, 255),     # Gunmetal Tracks / Barrel / Joints
    5: (114, 120, 128, 255),  # Steel Grey Road Wheels / Hatches / Muzzle
    6: (220, 46, 46, 255),    # Bright Red Targeting Visor / Sensor
    7: (255, 226, 112, 255),  # Warm Headlights / Optics
    8: (28, 30, 34, 255),     # Deep Charcoal Tread Recess / Vents
    9: (198, 166, 72, 255),   # Brass Gold Insignia / Ammo Trim
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
# FORM A: MAIN BATTLE TANK (20 x 38 x 15)
# ==========================================
def build_a():
    grid = np.zeros((20, 38, 15), dtype=np.uint8)

    # --- TWIN CATERPILLAR TRACK ASSEMBLIES (Y: 3..26, Z: 0..4) ---
    fill_sym_box(grid, 5, 8, 4, 25, 0, 4, 4)
    fill_sym_box(grid, 5, 8, 3, 26, 1, 3, 4)
    fill_sym_box(grid, 6, 7, 5, 24, 1, 3, 0)      # Hollow track cores
    # Tread cleat texture & recessed road wheels
    for ty in range(4, 26, 2):
        fill_sym_box(grid, 5, 8, ty, ty, 0, 0, 8)
        fill_sym_box(grid, 5, 8, ty, ty, 4, 4, 8)
    for wy in (6, 10, 14, 18, 22):
        fill_sym_box(grid, 8, 8, wy, wy + 1, 1, 2, 5)
    # Front/rear sprockets
    fill_sym_box(grid, 8, 8, 4, 4, 2, 3, 5)
    fill_sym_box(grid, 8, 8, 25, 25, 2, 3, 5)

    # --- ARMORED HULL & SLOPED GLACIS (Y: 3..27, Z: 2..7) ---
    fill_sym_box(grid, 0, 5, 4, 24, 2, 7, 1)
    fill_sym_box(grid, 0, 4, 5, 23, 3, 6, 0)      # Hollow hull interior
    # Sloped front glacis plate
    fill_sym_box(grid, 0, 5, 25, 26, 3, 6, 1)
    fill_sym_box(grid, 0, 5, 27, 27, 3, 4, 2)
    # Armored side skirts over upper tracks
    fill_sym_box(grid, 6, 8, 4, 26, 5, 6, 1)
    fill_sym_box(grid, 8, 8, 7, 23, 5, 5, 2)
    fill_sym_box(grid, 8, 8, 11, 15, 6, 6, 3)     # Tan camo stripe on skirt
    # Front headlights & tow hooks
    fill_sym_box(grid, 6, 7, 26, 26, 6, 6, 7)
    fill_sym_box(grid, 2, 3, 27, 27, 4, 4, 5)
    # Rear engine exhaust grilles
    fill_sym_box(grid, 1, 4, 5, 9, 7, 7, 8)
    fill_sym_box(grid, 2, 3, 3, 3, 4, 5, 8)

    # --- LOW-PROFILE ANGLED TURRET (Y: 8..22, Z: 8..12) ---
    fill_sym_box(grid, 0, 5, 10, 19, 8, 11, 1)
    fill_sym_box(grid, 0, 4, 11, 21, 8, 11, 1)
    fill_sym_box(grid, 0, 3, 12, 18, 9, 10, 0)    # Hollow turret interior
    # Turret rear bustle rack & camo accents
    fill_sym_box(grid, 0, 4, 7, 9, 9, 11, 2)
    fill_sym_box(grid, 1, 3, 8, 9, 11, 11, 3)     # Sand tan stowage pack
    fill_sym_box(grid, 4, 5, 13, 17, 10, 11, 3)   # Tan camo patch
    # Smoke grenade launchers on turret cheeks
    fill_sym_box(grid, 5, 6, 19, 20, 9, 10, 4)
    # Commander cupola, hatch, red optics & radio antenna
    fill_box(grid, 6, 8, 12, 15, 12, 12, 2)
    fill_box(grid, 7, 7, 13, 14, 13, 13, 5)
    fill_box(grid, 11, 13, 12, 14, 12, 12, 5)
    fill_box(grid, 12, 13, 20, 21, 11, 12, 6)     # Gunner targeting sight
    fill_box(grid, 6, 6, 9, 9, 12, 14, 4)         # Whip antenna

    # --- LONG MAIN TANK CANNON (Y: 21..37, Z: 9..10) ---
    fill_sym_box(grid, 0, 1, 21, 23, 9, 10, 2)    # Gun mantlet
    fill_sym_box(grid, 0, 0, 24, 36, 9, 10, 4)    # Long gunmetal barrel
    fill_sym_box(grid, 0, 1, 28, 30, 9, 10, 5)    # Bore evacuator (fume extractor)
    fill_sym_box(grid, 0, 1, 36, 37, 9, 10, 5)    # Muzzle brake
    fill_sym_box(grid, 0, 0, 37, 37, 9, 10, 8)    # Bore opening

    return grid


# ==========================================
# FORM B: TANK HEAVY-ASSAULT ROBOT (32 x 24 x 39)
# ==========================================
def build_b():
    grid = np.zeros((32, 24, 39), dtype=np.uint8)

    # --- FEET (Z: 0..3) - Heavy armored tank hull bumpers & track treads ---
    fill_sym_box(grid, 2, 5, 7, 16, 0, 1, 4)
    fill_sym_box(grid, 2, 5, 8, 16, 1, 2, 2)
    fill_sym_box(grid, 3, 4, 14, 17, 1, 2, 5)     # Steel tow-bumper toes
    fill_sym_box(grid, 2, 5, 7, 8, 0, 2, 8)

    # --- LOWER LEGS (Z: 3..14) - Upright Caterpillar Track Assemblies! ---
    fill_sym_box(grid, 2, 4, 9, 14, 3, 13, 1)     # Olive side skirt shins
    fill_sym_box(grid, 3, 4, 14, 15, 5, 11, 2)    # Dark olive shin plate
    fill_sym_box(grid, 3, 4, 14, 15, 11, 14, 3)   # Tan knee armor
    # Full tank treads running vertically up outer legs with road wheels!
    fill_sym_box(grid, 5, 6, 8, 13, 2, 13, 4)
    for tz in range(3, 13, 2):
        fill_sym_box(grid, 5, 6, 8, 8, tz, tz, 8)
        fill_sym_box(grid, 5, 6, 13, 13, tz, tz, 8)
    for wz in (4, 7, 10):
        fill_sym_box(grid, 6, 6, 10, 11, wz, wz + 1, 5)  # Steel road wheels!

    # --- THIGHS (Z: 14..19) ---
    fill_sym_box(grid, 2, 4, 9, 13, 14, 19, 4)
    fill_sym_box(grid, 2, 3, 12, 13, 15, 18, 5)
    fill_sym_box(grid, 4, 4, 10, 12, 16, 18, 2)

    # --- WAIST / PELVIS (Z: 19..22) ---
    fill_sym_box(grid, 0, 4, 9, 14, 19, 21, 2)
    fill_sym_box(grid, 0, 4, 13, 15, 20, 21, 1)
    fill_sym_box(grid, 0, 1, 14, 15, 19, 22, 3)   # Tan belt crotch armor
    fill_sym_box(grid, 0, 0, 15, 15, 20, 21, 9)   # Brass belt emblem
    fill_sym_box(grid, 4, 5, 10, 13, 19, 21, 1)   # Side hip skirts

    # --- TORSO / CHEST (Z: 22..31) - Sloped Tank Front Glacis Plate! ---
    fill_sym_box(grid, 0, 5, 8, 14, 22, 31, 1)
    fill_sym_box(grid, 0, 4, 13, 15, 22, 24, 2)   # Armored lower hull abs
    # Sloped upper glacis chest plate jutting forward
    fill_sym_box(grid, 0, 5, 14, 16, 25, 30, 1)
    fill_sym_box(grid, 0, 4, 16, 17, 26, 29, 2)
    fill_sym_box(grid, 1, 3, 16, 17, 27, 28, 3)   # Tan reactive armor blocks
    # Twin hull headlights on upper chest flanks + brass emblem
    fill_sym_box(grid, 4, 5, 15, 16, 29, 30, 7)   # Tank headlights!
    fill_sym_box(grid, 0, 0, 17, 17, 28, 29, 9)   # Brass star insignia
    fill_sym_box(grid, 1, 2, 14, 15, 22, 23, 8)   # Engine vent slats

    # --- BACKPACK & FOLDED TANK TURRET (Y: 3..8, Z: 22..34) ---
    fill_sym_box(grid, 0, 4, 4, 7, 22, 32, 2)     # Folded tank turret body
    fill_sym_box(grid, 0, 3, 3, 4, 24, 30, 1)
    fill_sym_box(grid, 1, 3, 3, 4, 25, 27, 8)     # Engine exhaust grilles
    # MASSIVE MAIN TANK CANNON mounted over RIGHT SHOULDER (+X)!
    fill_box(grid, 20, 22, 5, 12, 32, 35, 2)      # Turret gun mantlet mount
    fill_box(grid, 20, 21, 12, 23, 33, 34, 4)     # Long cannon barrel pointing forward!
    fill_box(grid, 20, 22, 16, 18, 33, 34, 5)     # Bore evacuator
    fill_box(grid, 20, 22, 22, 23, 33, 34, 5)     # Muzzle brake
    # Left shoulder commander cupola & smoke launchers (-X)
    fill_box(grid, 10, 12, 6, 9, 32, 34, 5)       # Cupola hatch
    fill_box(grid, 10, 11, 10, 11, 32, 33, 4)     # Smoke launchers
    fill_box(grid, 11, 11, 6, 6, 35, 38, 4)       # Radio whip antenna

    # --- SHOULDERS & ARMS (Z: 14..32) - Heavy Tank Side-Skirt Armor ---
    fill_sym_box(grid, 6, 9, 9, 14, 27, 31, 1)    # Blocky shoulder armor
    fill_sym_box(grid, 7, 9, 10, 13, 31, 31, 3)   # Tan shoulder top
    fill_sym_box(grid, 9, 9, 10, 13, 28, 30, 2)
    # Upper arms (gunmetal heavy joints)
    fill_sym_box(grid, 6, 8, 10, 12, 22, 26, 4)
    fill_sym_box(grid, 7, 8, 10, 12, 23, 25, 5)
    # Forearms (armored olive gauntlets with reactive plates)
    fill_sym_box(grid, 6, 9, 9, 13, 16, 21, 1)
    fill_sym_box(grid, 9, 9, 10, 13, 17, 20, 3)   # Side reactive shield plates
    fill_sym_box(grid, 6, 8, 13, 14, 17, 20, 2)
    # Heavy fists
    fill_sym_box(grid, 7, 8, 10, 12, 13, 15, 4)
    # Left arm twin-barrel autocannon
    fill_box(grid, 6, 7, 14, 20, 16, 17, 4)
    fill_box(grid, 6, 7, 19, 20, 16, 17, 5)

    # --- HEAD (Z: 32..37) - Angular Military Tank-Commander Helmet ---
    fill_sym_box(grid, 0, 1, 10, 12, 31, 32, 4)
    fill_sym_box(grid, 0, 2, 9, 13, 32, 36, 1)    # Olive helmet
    fill_sym_box(grid, 0, 2, 10, 14, 36, 37, 2)   # Sloped helmet brow
    fill_sym_box(grid, 0, 1, 13, 14, 33, 34, 6)   # Glowing red targeting visor
    fill_sym_box(grid, 0, 1, 13, 14, 32, 32, 5)   # Steel chin guard
    fill_sym_box(grid, 2, 3, 10, 12, 33, 35, 3)   # Tan comms earpods

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
    v_a = export_vox(model_a, "tank_a.vox")
    v_b = export_vox(model_b, "tank_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: BATTLE TANK -> HEAVY ASSAULT ROBOT",
        "1. MAIN BATTLE TANK",
        "2. TANK ASSAULT ROBOT",
        "preview_tank.png",
        yaw_a=38, pitch_a=24, yaw_b=34, pitch_b=20,
    )
    print(f"tank: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
