import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (240, 244, 250, 255),  # Pure Shinkansen White
    2: (185, 195, 210, 255),  # Silver-Grey Roof / Shading
    3: (24, 88, 192, 255),    # Iconic Shinkansen Cobalt Blue
    4: (44, 48, 58, 255),     # Dark Charcoal Undercarriage / Joints
    5: (32, 56, 98, 255),     # Dark Tinted Window Glass
    6: (105, 212, 255, 255),  # Cyan Glass Glint / Robot Visor
    7: (255, 225, 95, 255),   # Warm Headlight / Chest Core
    8: (225, 48, 55, 255),    # Signal Red Accent / Tail Light
    9: (118, 128, 144, 255),  # Metallic Steel Pantograph / Coupler
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
# FORM A: SHINKANSEN BULLET TRAIN (14 x 46 x 14)
# ==========================================
def build_a():
    grid = np.zeros((14, 46, 14), dtype=np.uint8)

    # Dark undercarriage & bogies (Y: 2..39, Z: 0..2)
    fill_sym_box(grid, 0, 2, 2, 39, 1, 1, 4)
    for by in (6, 11, 21, 26, 33, 37):
        fill_sym_box(grid, 1, 2, by, by + 1, 0, 1, 4)
        fill_sym_box(grid, 2, 2, by, by, 0, 0, 9)
    fill_sym_box(grid, 0, 1, 0, 1, 1, 2, 9)  # Rear coupler

    # Main passenger car body (Y: 2..30, Z: 2..8)
    fill_sym_box(grid, 0, 3, 2, 30, 2, 7, 1)
    fill_sym_box(grid, 0, 2, 2, 30, 8, 8, 1)  # Curved roof
    fill_sym_box(grid, 0, 1, 2, 30, 9, 9, 2)  # Roof fairing
    fill_sym_box(grid, 3, 3, 2, 32, 2, 2, 2)  # Lower skirt

    # Iconic twin cobalt-blue stripes
    fill_sym_box(grid, 3, 3, 2, 35, 3, 3, 3)
    fill_sym_box(grid, 3, 3, 2, 33, 6, 6, 3)
    # Rear gangway & red tail lights
    fill_sym_box(grid, 2, 2, 2, 2, 3, 4, 8)
    fill_sym_box(grid, 0, 1, 2, 2, 3, 6, 9)

    # Passenger windows
    for wy in range(4, 29, 3):
        fill_sym_box(grid, 3, 3, wy, wy + 1, 4, 5, 5)
        fill_sym_box(grid, 3, 3, wy + 1, wy + 1, 5, 5, 6)

    # Aerodynamic nose section (Y: 31..44)
    fill_sym_box(grid, 0, 3, 31, 34, 2, 6, 1)
    fill_sym_box(grid, 0, 2, 31, 34, 7, 7, 1)
    fill_sym_box(grid, 0, 1, 31, 33, 8, 8, 2)
    # Cockpit windshield
    fill_sym_box(grid, 0, 2, 33, 36, 6, 7, 5)
    fill_sym_box(grid, 0, 1, 34, 35, 7, 7, 6)
    # Sleek tapered duckbill nose
    fill_sym_box(grid, 0, 2, 35, 39, 2, 5, 1)
    fill_sym_box(grid, 0, 1, 40, 42, 2, 4, 1)
    fill_sym_box(grid, 0, 0, 43, 44, 2, 3, 1)
    # Blue nose stripe
    fill_sym_box(grid, 2, 2, 35, 39, 3, 3, 3)
    fill_sym_box(grid, 1, 1, 40, 42, 3, 3, 3)
    fill_sym_box(grid, 0, 0, 43, 44, 2, 2, 3)
    # Headlights & nose ridge
    fill_sym_box(grid, 0, 0, 37, 42, 5, 5, 2)
    fill_sym_box(grid, 2, 2, 38, 39, 4, 4, 7)
    fill_sym_box(grid, 1, 1, 41, 42, 4, 4, 7)

    # Roof AC units & Single-arm Pantograph (Z: 10..13)
    fill_sym_box(grid, 0, 1, 5, 9, 10, 10, 9)
    fill_sym_box(grid, 0, 1, 22, 26, 10, 10, 9)
    fill_sym_box(grid, 0, 1, 14, 17, 10, 10, 4)
    fill_sym_box(grid, 0, 0, 15, 16, 11, 11, 9)
    fill_sym_box(grid, 0, 0, 16, 17, 12, 12, 9)
    fill_sym_box(grid, 0, 2, 16, 16, 13, 13, 9)
    fill_sym_box(grid, 2, 2, 16, 16, 13, 13, 8)

    return grid


# ==========================================
# FORM B: SHINKANSEN ROBOT (30 x 22 x 39)
# ==========================================
def build_b():
    grid = np.zeros((30, 22, 39), dtype=np.uint8)

    # --- FEET (Z: 0..2) - Dark train bogies + blue/white nose toes ---
    fill_sym_box(grid, 2, 4, 7, 15, 0, 1, 4)
    fill_sym_box(grid, 2, 4, 12, 16, 1, 2, 3)
    fill_sym_box(grid, 3, 3, 14, 16, 2, 2, 1)
    fill_sym_box(grid, 2, 4, 7, 8, 0, 2, 9)

    # --- LOWER LEGS (Z: 3..13) - Split passenger car halves with windows & blue stripes ---
    fill_sym_box(grid, 2, 4, 9, 13, 3, 13, 1)
    fill_sym_box(grid, 4, 4, 9, 13, 4, 12, 3)
    fill_sym_box(grid, 2, 2, 13, 13, 4, 12, 3)
    for wz in (4, 7, 10):
        fill_sym_box(grid, 4, 4, 10, 11, wz, wz + 1, 5)
        fill_sym_box(grid, 4, 4, 11, 11, wz + 1, wz + 1, 6)
    fill_sym_box(grid, 2, 3, 13, 14, 11, 14, 3)
    fill_sym_box(grid, 3, 3, 14, 15, 12, 13, 1)

    # --- THIGHS (Z: 14..19) ---
    fill_sym_box(grid, 2, 3, 9, 12, 14, 19, 2)
    fill_sym_box(grid, 2, 3, 12, 13, 15, 18, 1)
    fill_sym_box(grid, 2, 3, 10, 11, 14, 14, 4)

    # --- WAIST / PELVIS (Z: 19..22) ---
    fill_sym_box(grid, 0, 4, 9, 13, 19, 21, 4)
    fill_sym_box(grid, 0, 3, 12, 14, 20, 21, 1)
    fill_sym_box(grid, 0, 1, 13, 14, 19, 22, 3)
    fill_sym_box(grid, 0, 0, 14, 14, 20, 21, 7)
    fill_sym_box(grid, 4, 4, 10, 12, 19, 21, 1)
    fill_sym_box(grid, 4, 4, 11, 11, 19, 20, 3)

    # --- TORSO / CHEST (Z: 22..31) - Shinkansen Nose & Cockpit ---
    fill_sym_box(grid, 0, 4, 8, 13, 22, 31, 1)
    fill_sym_box(grid, 0, 3, 8, 12, 22, 24, 2)
    fill_sym_box(grid, 0, 2, 13, 14, 23, 30, 1)
    # Aerodynamic Shinkansen nose jutting from chest!
    fill_sym_box(grid, 0, 2, 14, 16, 24, 28, 1)
    fill_sym_box(grid, 0, 1, 17, 18, 24, 27, 1)
    fill_sym_box(grid, 0, 0, 19, 19, 24, 26, 1)
    # Blue Shinkansen stripes on chest nose
    fill_sym_box(grid, 2, 2, 14, 16, 25, 25, 3)
    fill_sym_box(grid, 1, 1, 17, 18, 25, 25, 3)
    fill_sym_box(grid, 0, 0, 19, 19, 25, 25, 3)
    fill_sym_box(grid, 3, 3, 13, 14, 26, 29, 3)
    # Cockpit windshield on upper chest
    fill_sym_box(grid, 0, 2, 14, 15, 28, 30, 5)
    fill_sym_box(grid, 0, 1, 15, 16, 29, 30, 6)
    # Headlights
    fill_sym_box(grid, 2, 2, 16, 16, 27, 27, 7)
    fill_sym_box(grid, 3, 3, 14, 14, 27, 27, 7)

    # --- BACKPACK (Y: 4..7) - Roof AC + Split Pantograph Wings ---
    fill_sym_box(grid, 0, 3, 5, 7, 22, 30, 2)
    fill_sym_box(grid, 0, 2, 4, 5, 24, 29, 9)
    for i in range(5):
        fill_sym_box(grid, 3 + i, 4 + i, 5, 6, 28 + i, 29 + i, 9 if i < 3 else 8)
    fill_sym_box(grid, 2, 2, 4, 5, 22, 24, 4)

    # --- SHOULDERS & ARMS (Z: 14..33) ---
    fill_sym_box(grid, 5, 9, 9, 13, 27, 32, 1)
    fill_sym_box(grid, 6, 9, 10, 12, 32, 33, 3)
    fill_sym_box(grid, 9, 9, 10, 12, 28, 31, 3)
    fill_sym_box(grid, 7, 8, 13, 13, 29, 30, 5)
    # Upper arm
    fill_sym_box(grid, 6, 7, 10, 12, 22, 26, 4)
    fill_sym_box(grid, 6, 7, 10, 12, 23, 25, 9)
    # Forearm
    fill_sym_box(grid, 6, 8, 9, 13, 16, 21, 1)
    fill_sym_box(grid, 8, 8, 10, 12, 17, 20, 3)
    fill_sym_box(grid, 6, 8, 13, 14, 17, 20, 2)
    fill_sym_box(grid, 7, 7, 14, 14, 18, 19, 5)
    # Fists & Right hand Rail-Blade
    fill_sym_box(grid, 6, 7, 10, 12, 14, 15, 4)
    fill_box(grid, 21, 22, 13, 20, 14, 15, 9)
    fill_box(grid, 21, 22, 15, 19, 15, 15, 6)

    # --- HEAD (Z: 32..38) ---
    fill_sym_box(grid, 0, 1, 10, 11, 31, 32, 4)
    fill_sym_box(grid, 0, 2, 9, 13, 32, 36, 1)
    fill_sym_box(grid, 0, 2, 10, 12, 36, 37, 3)
    fill_sym_box(grid, 0, 1, 13, 14, 33, 34, 6)
    fill_sym_box(grid, 0, 0, 13, 14, 35, 36, 8)
    fill_sym_box(grid, 1, 1, 13, 14, 36, 37, 3)
    fill_sym_box(grid, 2, 3, 12, 13, 37, 38, 3)
    fill_sym_box(grid, 3, 3, 10, 11, 33, 35, 2)

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


def render_voxel_iso(grid, yaw_deg=35, pitch_deg=25, scale=None, img_size=(386, 266), margin=14):
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
    v_a = export_vox(model_a, "shinkansen_a.vox")
    v_b = export_vox(model_b, "shinkansen_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SHINKANSEN -> ROBOT",
        "1. SHINKANSEN MODE",
        "2. SHINKANSEN ROBOT",
        "preview_shinkansen.png",
        yaw_a=42, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"shinkansen: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
