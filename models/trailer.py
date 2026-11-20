import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (212, 38, 42, 255),    # Crimson Tractor Cab Red
    2: (32, 76, 168, 255),    # Royal Blue Chassis / Legs / Helmet
    3: (224, 232, 240, 255),  # Chrome Silver Grille / Trailer / Stacks
    4: (136, 146, 162, 255),  # Steel Grey Trailer Ribbing / Tanks
    5: (36, 38, 44, 255),     # Heavy Rubber Tires / Joints
    6: (72, 188, 242, 255),   # Sky Blue Cab Windshield / Visor
    7: (255, 190, 38, 255),   # Amber Clearance Lights / Headlights
    8: (64, 70, 82, 255),     # Dark Underframe / Mechanical Core
    9: (245, 247, 252, 255),  # Crisp White Racing Stripe
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


def fill_wheel_sym(grid, x_off0, x_off1, yc, zc, r, tire_col=5, hub_col=3):
    """Fill symmetric truck wheels centered at (yc, zc) with radius r."""
    for dy in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d2 = dy * dy + dz * dz
            if d2 <= r * r + 1:
                fill_sym_box(grid, x_off0, x_off1, yc + dy, yc + dy, zc + dz, zc + dz, tire_col)
            if d2 <= max(0, (r - 1) * (r - 1)):
                fill_sym_box(grid, x_off1, x_off1, yc + dy, yc + dy, zc + dz, zc + dz, hub_col)


# ==========================================
# FORM A: SEMI TRAILER TRUCK (14 x 40 x 15)
# ==========================================
def build_a():
    grid = np.zeros((14, 40, 15), dtype=np.uint8)

    # --- TRACTOR CHASSIS (Y: 20..37) ---
    fill_sym_box(grid, 0, 2, 20, 37, 1, 3, 2)
    fill_sym_box(grid, 0, 1, 20, 36, 2, 3, 8)
    fill_sym_box(grid, 0, 1, 21, 35, 2, 2, 0)     # Hollow chassis core
    fill_sym_box(grid, 0, 4, 37, 38, 1, 2, 3)     # Front chrome bumper
    fill_sym_box(grid, 3, 4, 27, 30, 1, 3, 3)     # Side fuel tanks
    fill_sym_box(grid, 4, 4, 28, 29, 2, 2, 4)

    # --- RED CAB-OVER TRACTOR CAB (Y: 30..37, Z: 3..11) ---
    fill_sym_box(grid, 0, 4, 30, 37, 3, 10, 1)
    fill_sym_box(grid, 0, 3, 31, 36, 4, 9, 0)     # Hollow cab interior
    fill_sym_box(grid, 0, 3, 31, 36, 11, 11, 1)
    fill_sym_box(grid, 4, 4, 30, 37, 6, 6, 9)     # White racing stripe
    fill_sym_box(grid, 0, 4, 37, 37, 6, 6, 9)
    # Chrome front radiator grille
    fill_sym_box(grid, 0, 1, 37, 38, 3, 6, 3)
    fill_sym_box(grid, 0, 0, 38, 38, 4, 5, 4)
    # Headlights & amber clearance roof lights
    fill_sym_box(grid, 2, 3, 37, 37, 3, 4, 7)
    fill_sym_box(grid, 0, 0, 36, 36, 12, 12, 7)
    fill_sym_box(grid, 2, 2, 36, 36, 12, 12, 7)
    # Split blue windshield & side windows
    fill_sym_box(grid, 1, 3, 37, 37, 7, 9, 6)
    fill_sym_box(grid, 4, 4, 32, 35, 7, 9, 6)
    # Twin vertical chrome exhaust smokestacks behind cab!
    fill_sym_box(grid, 4, 5, 29, 30, 4, 13, 3)
    fill_sym_box(grid, 5, 5, 29, 29, 12, 14, 4)
    # Fifth-wheel hitch
    fill_sym_box(grid, 0, 1, 22, 26, 4, 4, 8)

    # --- SILVER BOX TRAILER (Y: 2..27, Z: 5..13) ---
    fill_sym_box(grid, 0, 3, 3, 26, 4, 4, 8)
    fill_sym_box(grid, 2, 2, 19, 20, 1, 3, 8)     # Landing gear
    # Hollowed silver trailer shell
    fill_sym_box(grid, 0, 4, 2, 27, 5, 13, 3)
    fill_sym_box(grid, 0, 3, 3, 26, 5, 12, 0)
    fill_sym_box(grid, 0, 2, 4, 25, 4, 4, 0)      # Hollow underframe center
    for ry in range(4, 26, 4):
        fill_sym_box(grid, 4, 4, ry, ry, 6, 12, 4)
        fill_sym_box(grid, 0, 3, ry, ry, 13, 13, 4)
    # Blue/Red/White trailer stripes
    fill_sym_box(grid, 4, 4, 2, 27, 8, 9, 2)
    fill_sym_box(grid, 4, 4, 2, 27, 10, 10, 1)
    fill_sym_box(grid, 4, 4, 2, 27, 7, 7, 9)
    # Rear doors & red tail lights
    fill_sym_box(grid, 0, 3, 2, 2, 6, 12, 4)
    fill_sym_box(grid, 2, 3, 2, 2, 5, 5, 1)

    # --- HEAVY TRUCK WHEELS ---
    fill_wheel_sym(grid, 3, 5, 34, 2, 2)  # Front cab
    fill_wheel_sym(grid, 3, 5, 25, 2, 2)  # Rear cab 1
    fill_wheel_sym(grid, 3, 5, 20, 2, 2)  # Rear cab 2
    fill_wheel_sym(grid, 3, 5, 10, 2, 2)  # Trailer 1
    fill_wheel_sym(grid, 3, 5, 5, 2, 2)   # Trailer 2

    return grid


# ==========================================
# FORM B: TRAILER ROBOT (30 x 22 x 39)
# ==========================================
def build_b():
    grid = np.zeros((30, 22, 39), dtype=np.uint8)

    # --- FEET (Z: 0..2) ---
    fill_sym_box(grid, 2, 4, 7, 15, 0, 1, 2)
    fill_sym_box(grid, 2, 4, 12, 16, 0, 1, 8)
    fill_sym_box(grid, 3, 3, 14, 16, 1, 2, 3)
    fill_sym_box(grid, 2, 4, 7, 8, 0, 2, 8)

    # --- LOWER LEGS (Z: 3..13) - Blue tractor rear chassis + outer truck tires ---
    fill_sym_box(grid, 2, 4, 9, 13, 3, 13, 2)
    fill_sym_box(grid, 3, 3, 13, 14, 4, 11, 3)
    fill_sym_box(grid, 2, 3, 13, 14, 11, 14, 2)
    fill_sym_box(grid, 3, 3, 14, 14, 12, 13, 7)
    fill_wheel_sym(grid, 5, 6, 10, 5, 2)
    fill_wheel_sym(grid, 5, 6, 10, 10, 2)

    # --- THIGHS (Z: 14..19) ---
    fill_sym_box(grid, 2, 3, 9, 12, 14, 19, 3)
    fill_sym_box(grid, 2, 3, 10, 11, 14, 15, 8)
    fill_sym_box(grid, 3, 3, 10, 11, 16, 18, 4)

    # --- WAIST / PELVIS (Z: 19..22) - Chrome front bumper waist ---
    fill_sym_box(grid, 0, 4, 9, 13, 19, 21, 3)
    fill_sym_box(grid, 0, 1, 12, 14, 19, 22, 7)
    fill_sym_box(grid, 2, 3, 13, 14, 20, 21, 4)
    fill_sym_box(grid, 4, 4, 10, 12, 19, 21, 1)

    # --- TORSO / CHEST (Z: 22..31) - Red Tractor Cab Front! ---
    fill_sym_box(grid, 0, 2, 9, 14, 22, 24, 3)    # Chrome radiator grille abs
    fill_sym_box(grid, 0, 1, 14, 14, 22, 24, 4)
    fill_sym_box(grid, 3, 3, 9, 13, 22, 24, 1)
    fill_sym_box(grid, 0, 5, 9, 14, 25, 31, 1)    # Broad red cab chest
    fill_sym_box(grid, 0, 5, 13, 14, 25, 25, 9)   # White cab stripe
    # Split blue cab windshields!
    fill_sym_box(grid, 1, 3, 14, 15, 26, 30, 6)
    fill_sym_box(grid, 0, 0, 14, 15, 25, 31, 1)   # Center cab pillar
    # Amber clearance lights on collarbone
    fill_sym_box(grid, 0, 0, 13, 14, 31, 31, 7)
    fill_sym_box(grid, 3, 3, 13, 14, 31, 31, 7)

    # --- BACKPACK (Y: 5..8) - Folded Silver Trailer Panels ---
    fill_sym_box(grid, 0, 3, 6, 8, 21, 30, 8)
    fill_sym_box(grid, 3, 7, 5, 6, 22, 31, 3)
    fill_sym_box(grid, 4, 6, 4, 4, 24, 30, 4)
    fill_sym_box(grid, 4, 7, 5, 6, 25, 26, 2)     # Blue trailer stripe
    fill_sym_box(grid, 4, 7, 5, 6, 27, 27, 1)     # Red trailer stripe
    fill_wheel_sym(grid, 2, 2, 6, 20, 1)

    # --- SHOULDERS & ARMS (Z: 14..37) - Cab doors + Chrome Smokestacks ---
    fill_sym_box(grid, 6, 9, 9, 13, 27, 32, 1)
    fill_sym_box(grid, 9, 9, 10, 12, 28, 29, 9)
    # Twin chrome exhaust smokestacks!
    fill_sym_box(grid, 8, 9, 9, 10, 32, 37, 3)
    fill_sym_box(grid, 9, 9, 9, 9, 36, 38, 4)
    # Upper arms
    fill_sym_box(grid, 6, 7, 10, 12, 22, 26, 4)
    fill_sym_box(grid, 7, 7, 10, 12, 23, 25, 3)
    # Forearms + silver fuel tank canisters
    fill_sym_box(grid, 6, 8, 9, 13, 16, 21, 1)
    fill_sym_box(grid, 9, 9, 10, 12, 17, 20, 3)
    fill_sym_box(grid, 6, 8, 13, 13, 17, 17, 9)
    # Blue fists
    fill_sym_box(grid, 6, 7, 10, 12, 13, 15, 2)
    # Right hand ion blaster
    fill_box(grid, 21, 22, 12, 20, 14, 16, 5)
    fill_box(grid, 21, 22, 17, 20, 15, 16, 3)
    # Left forearm trailer-panel shield
    fill_box(grid, 4, 5, 10, 15, 15, 22, 3)
    fill_box(grid, 4, 4, 11, 14, 18, 18, 2)
    fill_box(grid, 4, 4, 11, 14, 19, 19, 1)

    # --- HEAD (Z: 32..38) - Blue Helmet & Silver Faceplate ---
    fill_sym_box(grid, 0, 1, 10, 11, 31, 32, 8)
    fill_sym_box(grid, 0, 2, 9, 13, 32, 37, 2)
    fill_sym_box(grid, 0, 1, 13, 14, 32, 33, 3)
    fill_sym_box(grid, 0, 1, 13, 14, 34, 35, 6)
    fill_sym_box(grid, 0, 0, 11, 14, 36, 38, 2)
    fill_sym_box(grid, 3, 3, 10, 11, 34, 38, 2)

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
    v_a = export_vox(model_a, "trailer_a.vox")
    v_b = export_vox(model_b, "trailer_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: TRAILER TRUCK -> ROBOT",
        "1. TRAILER TRUCK MODE",
        "2. TRAILER ROBOT",
        "preview_trailer.png",
        yaw_a=40, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"trailer: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
