import struct
import math
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (242, 245, 250, 255),  # Pure White Steel Wheel Rim & A-Frame
    2: (144, 182, 218, 255),  # Sky Steel Blue Spokes & Truss Shading
    3: (232, 54, 64, 255),    # Carnival Red Gondola / Armor
    4: (252, 202, 38, 255),   # Sunny Yellow Gondola / Central Hub Star
    5: (42, 134, 228, 255),   # Ocean Blue Gondola / Chest Trim
    6: (48, 198, 128, 255),   # Mint Green Gondola / Robot Visor
    7: (46, 54, 80, 255),     # Deep Indigo Platform & Mechanical Joints
    8: (226, 68, 168, 255),   # Neon Magenta Gondola / Accent
    9: (255, 242, 166, 255),  # Warm Carnival Bulb Illumination
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


def draw_line_xz(grid, x0, z0, x1, z1, y0, y1, col):
    """Draw a 3D line segment in the X-Z plane across Y range [y0..y1]."""
    steps = max(abs(x1 - x0), abs(z1 - z0), 1) * 2
    for i in range(steps + 1):
        t = i / steps
        x = int(round(x0 + (x1 - x0) * t))
        z = int(round(z0 + (z1 - z0) * t))
        fill_box(grid, x, x, y0, y1, z, z, col)


def draw_ring_xz(grid, cx, cz, r, y0, y1, col, bulb_col=None):
    """Draw a circular Ferris wheel rim in the X-Z plane."""
    for deg in range(0, 360, 2):
        rad = math.radians(deg)
        x = int(round(cx + r * math.cos(rad)))
        z = int(round(cz + r * math.sin(rad)))
        c = bulb_col if (bulb_col is not None and deg % 30 == 0) else col
        fill_box(grid, x, x, y0, y1, z, z, c)


# ==========================================
# FORM A: GIANT FERRIS WHEEL (38 x 18 x 42)
# ==========================================
def build_a():
    grid = np.zeros((38, 18, 42), dtype=np.uint8)
    cx, cy, cz = 18.5, 8.5, 22.0

    # --- BOARDING PLATFORM BASE (Z: 0..2) ---
    fill_sym_box(grid, 0, 12, 2, 15, 0, 1, 7)
    fill_sym_box(grid, 0, 10, 4, 13, 0, 0, 0)     # Hollow underside
    fill_sym_box(grid, 0, 5, 14, 16, 0, 0, 4)     # Yellow boarding stairs
    fill_sym_box(grid, 0, 4, 14, 15, 1, 1, 4)
    # Ticket booth kiosk on front-left platform
    fill_box(grid, 6, 9, 12, 15, 2, 5, 3)
    fill_box(grid, 7, 8, 15, 15, 3, 4, 9)
    fill_box(grid, 6, 9, 12, 15, 6, 6, 1)

    # --- STURDY A-FRAME SUPPORT TOWERS (Front Y=12..13 & Rear Y=4..5) ---
    for y_leg0, y_leg1 in ((4, 5), (12, 13)):
        draw_line_xz(grid, 8, 2, 18, 22, y_leg0, y_leg1, 1)
        draw_line_xz(grid, 9, 2, 19, 22, y_leg0, y_leg1, 2)
        draw_line_xz(grid, 29, 2, 19, 22, y_leg0, y_leg1, 1)
        draw_line_xz(grid, 28, 2, 18, 22, y_leg0, y_leg1, 2)
        # Cross-bracing on A-frame
        fill_box(grid, 12, 25, y_leg0, y_leg1, 9, 9, 2)
    # Central Horizontal Axle & Glowing Golden Hub Star!
    fill_sym_box(grid, 0, 1, 3, 14, 21, 23, 7)
    fill_sym_box(grid, 0, 2, 6, 11, 20, 24, 4)    # Sunny yellow hub disc
    fill_sym_box(grid, 0, 1, 5, 12, 21, 23, 9)    # Bright hub light core

    # --- TWIN WHITE STEEL RIMS & RADIAL SPOKES (Y=6..7 and Y=10..11) ---
    R_outer = 15.0
    R_inner = 11.0
    for ry in (6, 11):
        draw_ring_xz(grid, cx, cz, R_outer, ry, ry, 1, bulb_col=9)
        draw_ring_xz(grid, cx, cz, R_inner, ry, ry, 2)
    # 8 Radial Spokes connecting hub to rims + crossbars!
    gondola_colors = [3, 4, 5, 6, 8, 3, 4, 5]
    for k in range(8):
        ang = math.radians(k * 45)
        gx = int(round(cx + R_outer * math.cos(ang)))
        gz = int(round(cz + R_outer * math.sin(ang)))
        draw_line_xz(grid, int(round(cx)), int(round(cz)), gx, gz, 6, 6, 2)
        draw_line_xz(grid, int(round(cx)), int(round(cz)), gx, gz, 11, 11, 2)
        # Crossbar axle holding hanging gondola between the two rims!
        fill_box(grid, gx, gx, 6, 11, gz, gz, 7)
        # Colorful Hanging Passenger Gondola Cabin suspended below crossbar!
        gcol = gondola_colors[k]
        fill_box(grid, gx - 1, gx + 1, 7, 10, gz - 3, gz - 1, gcol)
        fill_box(grid, gx - 1, gx + 1, 7, 10, gz - 1, gz - 1, 1)    # White cabin roof
        fill_box(grid, gx, gx, 7, 10, gz - 2, gz - 2, 9)            # Warm cabin window!

    return grid


# ==========================================
# FORM B: FERRIS WHEEL HALO ROBOT (38 x 22 x 42)
# ==========================================
def build_b():
    grid = np.zeros((38, 22, 42), dtype=np.uint8)

    # --- FEET (Z: 0..2) - Dark Indigo Boarding-Platform Boots + Yellow Step Toes ---
    fill_sym_box(grid, 2, 5, 8, 16, 0, 1, 7)
    fill_sym_box(grid, 2, 5, 13, 17, 1, 2, 1)
    fill_sym_box(grid, 3, 4, 15, 17, 1, 2, 4)     # Yellow boarding-step toes!

    # --- LOWER LEGS (Z: 3..14) - Tall White & Sky-Blue A-Frame Support Tower Legs! ---
    fill_sym_box(grid, 2, 4, 10, 14, 3, 13, 1)
    fill_sym_box(grid, 4, 4, 10, 14, 4, 12, 2)    # Sky-blue truss struts
    fill_sym_box(grid, 3, 3, 14, 15, 5, 10, 7)    # Indigo inner frame
    fill_sym_box(grid, 2, 3, 14, 15, 11, 14, 8)   # Neon Magenta gondola knee pods!
    fill_sym_box(grid, 3, 3, 15, 15, 12, 13, 9)   # Glowing bulb accent

    # --- THIGHS (Z: 14..19) ---
    fill_sym_box(grid, 2, 3, 10, 13, 14, 19, 2)
    fill_sym_box(grid, 2, 3, 11, 12, 14, 15, 7)
    fill_sym_box(grid, 3, 3, 13, 14, 15, 18, 1)

    # --- WAIST / PELVIS (Z: 19..22) ---
    fill_sym_box(grid, 0, 4, 10, 14, 19, 21, 7)
    fill_sym_box(grid, 0, 4, 14, 15, 20, 21, 1)
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 5)   # Ocean blue hip plate
    fill_sym_box(grid, 0, 0, 16, 16, 20, 21, 4)   # Yellow belt star
    fill_sym_box(grid, 4, 5, 11, 13, 19, 21, 8)   # Magenta side skirts

    # --- TORSO / CHEST (Z: 22..31) - White Truss Torso & Glowing Golden Axle Hub Core! ---
    fill_sym_box(grid, 0, 4, 9, 15, 22, 31, 1)
    fill_sym_box(grid, 0, 3, 14, 15, 22, 24, 2)   # Sky-blue truss abs
    fill_sym_box(grid, 0, 4, 15, 16, 25, 30, 5)   # Ocean blue chest plate
    # Giant Glowing Golden Ferris-Wheel Axle Hub right on center chest!
    fill_sym_box(grid, 0, 2, 16, 17, 26, 30, 4)
    fill_sym_box(grid, 0, 1, 17, 18, 27, 29, 9)   # Bright carnival reactor core!
    fill_sym_box(grid, 3, 4, 15, 16, 29, 31, 1)   # White collarbone truss

    # --- BACKPACK: GIANT CELESTIAL FERRIS-WHEEL RING HALO! (Y: 5..7, Z: 16..41) ---
    fill_sym_box(grid, 0, 3, 6, 9, 22, 30, 7)     # Hub axle mount on back
    cx_h, cz_h, R_h = 18.5, 28.0, 12.5
    draw_ring_xz(grid, cx_h, cz_h, R_h, 6, 7, 1, bulb_col=9)
    draw_ring_xz(grid, cx_h, cz_h, R_h - 3.0, 6, 6, 2)
    # Radial spokes + colorful mini-gondola thruster pods around the back halo!
    halo_cols = [3, 4, 5, 6, 8, 3, 4, 5]
    for k in range(8):
        ang = math.radians(k * 45 + 22.5)
        hx = int(round(cx_h + R_h * math.cos(ang)))
        hz = int(round(cz_h + R_h * math.sin(ang)))
        draw_line_xz(grid, int(round(cx_h)), int(round(cz_h)), hx, hz, 6, 6, 2)
        # Colorful mini-gondola pod mounted around halo rim!
        if hz >= 18:
            fill_box(grid, hx - 1, hx + 1, 5, 7, hz - 1, hz + 1, halo_cols[k])
            fill_box(grid, hx, hx, 5, 7, hz, hz, 9)

    # --- SHOULDERS & ARMS (Z: 14..34) - Colorful Passenger Gondola Armor! ---
    # RIGHT SHOULDER (+X: 24..28): Carnival Red Gondola Cabin!
    fill_box(grid, 24, 28, 10, 15, 27, 32, 3)
    fill_box(grid, 24, 28, 10, 15, 32, 33, 1)     # White gondola roof cap
    fill_box(grid, 25, 27, 15, 15, 29, 30, 9)     # Glowing cabin window!
    # LEFT SHOULDER (-X: 9..13): Ocean Blue Gondola Cabin!
    fill_box(grid, 9, 13, 10, 15, 27, 32, 5)
    fill_box(grid, 9, 13, 10, 15, 32, 33, 1)      # White gondola roof cap
    fill_box(grid, 10, 12, 15, 15, 29, 30, 9)     # Glowing cabin window!
    # Upper arms (indigo steel truss joints)
    fill_sym_box(grid, 6, 7, 11, 13, 22, 26, 7)
    fill_sym_box(grid, 7, 7, 11, 13, 23, 25, 2)
    # RIGHT FOREARM (+X): Sunny Yellow Gondola Gauntlet!
    fill_box(grid, 25, 28, 10, 15, 16, 21, 4)
    fill_box(grid, 28, 28, 11, 14, 17, 20, 1)
    fill_box(grid, 26, 27, 15, 15, 18, 19, 9)
    # LEFT FOREARM (-X): Mint Green Gondola Gauntlet!
    fill_box(grid, 9, 12, 10, 15, 16, 21, 6)
    fill_box(grid, 9, 9, 11, 14, 17, 20, 1)
    fill_box(grid, 10, 11, 15, 15, 18, 19, 9)
    # Fists
    fill_sym_box(grid, 7, 8, 11, 13, 13, 15, 7)
    # Right hand Carnival Light-Staff / Spoke-Lance
    fill_box(grid, 26, 27, 14, 21, 14, 15, 1)
    fill_box(grid, 26, 27, 20, 21, 13, 16, 4)
    fill_box(grid, 26, 27, 21, 21, 14, 15, 9)

    # --- HEAD (Z: 32..38) - White & Gold Carnival Crown Helmet ---
    fill_sym_box(grid, 0, 1, 11, 12, 31, 32, 7)
    fill_sym_box(grid, 0, 2, 10, 14, 32, 36, 1)   # White helmet
    fill_sym_box(grid, 0, 2, 11, 13, 36, 37, 5)   # Ocean blue crown
    fill_sym_box(grid, 0, 1, 14, 15, 33, 34, 6)   # Glowing mint-green visor!
    fill_sym_box(grid, 0, 0, 14, 15, 36, 38, 4)   # Golden carnival star crest!
    fill_sym_box(grid, 1, 2, 14, 15, 37, 38, 4)   # Crown V-crest
    fill_sym_box(grid, 3, 3, 11, 12, 34, 36, 9)   # Glowing bulb ear-caps

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
    v_a = export_vox(model_a, "ferriswheel_a.vox")
    v_b = export_vox(model_b, "ferriswheel_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: FERRIS WHEEL -> CARNIVAL HALO ROBOT",
        "1. GIANT FERRIS WHEEL",
        "2. FERRIS WHEEL ROBOT",
        "preview_ferriswheel.png",
        yaw_a=28, pitch_a=18, yaw_b=28, pitch_b=18,
    )
    print(f"ferriswheel: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
