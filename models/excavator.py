import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (240, 180, 22, 255),   # Construction Yellow Body / Boom
    2: (186, 132, 16, 255),   # Deep Ochre Shaded Yellow
    3: (36, 38, 42, 255),     # Industrial Black Tracks / Bucket / Stripes
    4: (122, 130, 140, 255),  # Steel Grey Rollers / Cylinders / Teeth
    5: (218, 226, 236, 255),  # Bright Chrome Hydraulic Piston Rods
    6: (76, 188, 224, 255),   # Operator Cab Glass Cyan / Visor
    7: (238, 96, 24, 255),    # Safety Orange Warning Beacon
    8: (242, 244, 248, 255),  # Hazard White Trim
    9: (64, 68, 76, 255),     # Dark Gunmetal Undercarriage / Joints
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
# FORM A: HYDRAULIC EXCAVATOR (18 x 42 x 24)
# ==========================================
def build_a():
    grid = np.zeros((18, 42, 24), dtype=np.uint8)

    # --- CRAWLER TRACKS & UNDERCARRIAGE (Y: 4..23, Z: 0..5) ---
    fill_sym_box(grid, 4, 7, 5, 22, 0, 4, 3)
    fill_sym_box(grid, 4, 7, 4, 23, 1, 3, 3)
    fill_sym_box(grid, 5, 6, 6, 21, 1, 3, 0)      # Hollow track cores
    for wy in (7, 11, 15, 19):
        fill_sym_box(grid, 7, 7, wy, wy + 1, 1, 2, 4)  # Steel rollers
    # Dark undercarriage & slewing ring turntable
    fill_sym_box(grid, 0, 3, 8, 19, 2, 4, 9)
    fill_sym_box(grid, 0, 4, 9, 18, 5, 5, 4)

    # --- ROTATING UPPER HOUSE (Y: 3..21, Z: 6..13) ---
    # Yellow engine deck & counterweight at rear (Y: 3..14)
    fill_sym_box(grid, 0, 6, 4, 15, 6, 12, 1)
    fill_sym_box(grid, 0, 5, 5, 14, 7, 11, 0)     # Hollow engine bay
    fill_sym_box(grid, 0, 2, 9, 18, 3, 3, 0)      # Hollow undercarriage core
    fill_sym_box(grid, 0, 5, 3, 4, 6, 11, 2)      # Rounded rear counterweight
    # Black & yellow hazard stripes along counterweight rear & sides!
    for hx in (4, 6, 8, 10, 12):
        fill_box(grid, hx, hx, 3, 3, 7, 8, 3)
    fill_sym_box(grid, 6, 6, 5, 11, 7, 7, 3)
    fill_box(grid, 11, 13, 7, 11, 12, 13, 9)      # Engine vent + exhaust pipe
    fill_box(grid, 12, 12, 9, 9, 14, 15, 3)

    # Right side forward machinery deck (+X: 9..14, Y: 15..20)
    fill_box(grid, 9, 14, 15, 20, 6, 10, 1)
    fill_box(grid, 14, 14, 16, 19, 7, 9, 2)

    # Operator Glass Cabin on LEFT side (-X: 3..8, Y: 13..21, Z: 6..15)
    fill_box(grid, 3, 8, 13, 21, 6, 8, 1)         # Cab lower door
    fill_box(grid, 3, 8, 13, 21, 9, 14, 6)        # Panoramic cyan glass!
    fill_box(grid, 4, 7, 14, 20, 9, 13, 0)        # Hollow cab interior
    # Dark window corner pillars
    fill_box(grid, 3, 3, 13, 13, 9, 14, 3)
    fill_box(grid, 8, 8, 13, 13, 9, 14, 3)
    fill_box(grid, 3, 3, 21, 21, 9, 14, 3)
    fill_box(grid, 8, 8, 21, 21, 9, 14, 3)
    fill_box(grid, 3, 8, 13, 21, 15, 15, 1)       # Yellow cab roof
    fill_box(grid, 5, 6, 16, 17, 16, 17, 7)       # Glowing orange roof beacon!

    # --- ARTICULATED HYDRAULIC BOOM, STICK & TOOTHED BUCKET (X: 9..12) ---
    # Boom base pivot & rising main boom (Y: 16..29, Z: 9..22)
    fill_box(grid, 9, 12, 16, 19, 9, 12, 9)
    for step in range(11):
        by = 18 + step
        bz = 11 + step
        fill_box(grid, 10, 11, by, by + 1, bz, bz + 2, 1)
        if step % 3 == 0:
            fill_box(grid, 10, 11, by, by, bz + 2, bz + 2, 2)
    # Boom hydraulic cylinder (under boom)
    for step in range(6):
        fill_box(grid, 10, 11, 19 + step, 19 + step, 9 + step, 9 + step, 4 if step < 3 else 5)
    # Upper boom elbow & downward dipper stick (Y: 29..37, Z: 10..22)
    fill_box(grid, 9, 12, 28, 30, 21, 23, 9)      # Pivot pin
    for step in range(10):
        sy = 30 + (step * 7) // 10
        sz = 21 - step
        fill_box(grid, 10, 11, sy, sy + 1, sz, sz + 1, 1)
    # Stick hydraulic piston along top of boom
    for step in range(5):
        fill_box(grid, 10, 11, 23 + step, 23 + step, 19 + step // 2, 19 + step // 2, 4 if step < 3 else 5)
    # Curved Black Excavator Bucket with Steel Digging Teeth! (Y: 32..40, Z: 4..12)
    fill_box(grid, 9, 12, 35, 39, 9, 11, 3)       # Bucket top/back wall
    fill_box(grid, 9, 12, 37, 40, 5, 9, 3)        # Bucket curved rear
    fill_box(grid, 9, 12, 33, 39, 4, 5, 3)        # Bucket scoop bottom
    fill_box(grid, 9, 9, 34, 38, 5, 10, 3)        # Side cheeks
    fill_box(grid, 12, 12, 34, 38, 5, 10, 3)
    # Sharp steel digging teeth pointing toward ground/front!
    fill_box(grid, 9, 9, 31, 32, 4, 4, 4)
    fill_box(grid, 11, 11, 31, 32, 4, 4, 4)
    fill_box(grid, 12, 12, 31, 32, 4, 4, 4)

    return grid


# ==========================================
# FORM B: EXCAVATOR CONSTRUCTION ROBOT (32 x 26 x 39)
# ==========================================
def build_b():
    grid = np.zeros((32, 26, 39), dtype=np.uint8)

    # --- FEET (Z: 0..2) - Wide heavy black crawler bases ---
    fill_sym_box(grid, 2, 5, 8, 17, 0, 1, 3)
    fill_sym_box(grid, 2, 5, 13, 18, 1, 2, 9)
    fill_sym_box(grid, 3, 4, 15, 18, 1, 2, 1)     # Yellow bulldozer-blade toes

    # --- LOWER LEGS (Z: 3..14) - Vertical Black Crawler Tracks + Yellow Knee Armor ---
    fill_sym_box(grid, 2, 4, 10, 14, 3, 13, 1)    # Yellow inner shins
    fill_sym_box(grid, 5, 6, 9, 14, 2, 13, 3)     # Outer black crawler treads!
    for wz in (4, 7, 10):
        fill_sym_box(grid, 6, 6, 11, 12, wz, wz + 1, 4)  # Steel track rollers
    fill_sym_box(grid, 3, 4, 14, 15, 5, 10, 2)
    fill_sym_box(grid, 2, 4, 14, 15, 11, 14, 1)   # Yellow heavy knee pads
    fill_sym_box(grid, 3, 3, 15, 15, 12, 13, 3)   # Hazard knee mark

    # --- THIGHS (Z: 14..19) - Chrome Hydraulic Pistons & Gunmetal ---
    fill_sym_box(grid, 2, 4, 10, 13, 14, 19, 9)
    fill_sym_box(grid, 3, 3, 13, 14, 15, 18, 5)   # Gleaming chrome piston rods!
    fill_sym_box(grid, 4, 4, 11, 12, 15, 18, 2)

    # --- WAIST / PELVIS (Z: 19..22) - Black & Yellow Hazard Stripe Belt! ---
    fill_sym_box(grid, 0, 4, 10, 14, 19, 21, 9)
    fill_sym_box(grid, 0, 4, 14, 15, 20, 21, 1)
    for hx in (12, 14, 17, 19):
        fill_box(grid, hx, hx, 15, 15, 20, 21, 3)  # Hazard stripes!
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 3)
    fill_sym_box(grid, 0, 0, 16, 16, 20, 21, 7)    # Orange warning buckle

    # --- TORSO / CHEST (Z: 22..31) - Yellow Upper House + Left-Chest Operator Cab! ---
    fill_sym_box(grid, 0, 5, 9, 15, 22, 31, 1)
    fill_sym_box(grid, 0, 3, 14, 15, 22, 24, 9)    # Hydraulic engine core abs
    fill_sym_box(grid, 1, 2, 15, 15, 22, 24, 5)    # Chrome pistons on abs
    # LEFT CHEST (-X: 11..15): Iconic Glass Operator Cabin embedded in chest!
    fill_box(grid, 11, 15, 15, 17, 25, 30, 6)      # Panoramic cyan cab glass!
    fill_box(grid, 11, 11, 15, 17, 25, 30, 3)      # Black cab frame
    fill_box(grid, 15, 15, 15, 17, 25, 30, 3)
    fill_box(grid, 11, 15, 15, 17, 31, 31, 1)      # Cab roof cap
    fill_box(grid, 12, 13, 15, 16, 32, 33, 7)      # Flashing orange beacon!
    # RIGHT CHEST (+X: 16..20): Yellow engine hood with exhaust vents
    fill_box(grid, 16, 20, 15, 16, 25, 30, 2)
    fill_box(grid, 17, 19, 16, 16, 26, 29, 9)      # Dark grille vents
    fill_box(grid, 17, 19, 16, 16, 30, 30, 8)      # White safety trim

    # --- BACKPACK (Y: 5..8) - Rear Counterweight Block + Exhaust Pipe ---
    fill_sym_box(grid, 0, 4, 6, 8, 22, 30, 2)
    fill_sym_box(grid, 0, 4, 5, 6, 23, 28, 1)
    for hx in (12, 14, 17, 19):
        fill_box(grid, hx, hx, 5, 5, 24, 25, 3)    # Rear hazard stripes
    fill_box(grid, 18, 19, 6, 7, 30, 35, 3)        # Vertical exhaust stack

    # --- RIGHT ARM (+X): GIANT ARTICULATED EXCAVATOR BOOM & TOOTHED BUCKET! ---
    fill_box(grid, 21, 25, 10, 15, 27, 32, 1)      # Yellow boom shoulder pivot
    fill_box(grid, 22, 24, 11, 14, 32, 33, 9)
    # Hydraulic upper arm with chrome piston!
    fill_box(grid, 22, 24, 11, 14, 22, 26, 9)
    fill_box(grid, 24, 24, 12, 13, 21, 27, 5)      # Gleaming chrome piston!
    # Yellow stick forearm extending forward
    fill_box(grid, 22, 25, 11, 19, 17, 21, 1)
    fill_box(grid, 23, 24, 14, 18, 21, 22, 5)      # Upper forearm hydraulic rod
    # MASSIVE BLACK TOOTHED EXCAVATOR BUCKET CLAW! (X: 21..26, Y: 19..25, Z: 13..20)
    fill_box(grid, 21, 26, 19, 23, 18, 20, 3)      # Upper scoop hood
    fill_box(grid, 21, 26, 19, 21, 14, 18, 3)      # Scoop backplate
    fill_box(grid, 21, 26, 19, 24, 13, 14, 3)      # Lower scoop jaw
    fill_box(grid, 21, 21, 19, 23, 14, 19, 3)      # Side walls
    fill_box(grid, 26, 26, 19, 23, 14, 19, 3)
    # Sharp steel excavator digging teeth!
    fill_box(grid, 21, 21, 24, 25, 13, 14, 4)
    fill_box(grid, 23, 24, 24, 25, 13, 14, 4)
    fill_box(grid, 26, 26, 24, 25, 13, 14, 4)

    # --- LEFT ARM (-X): HEAVY CONSTRUCTION CLAW ARM ---
    fill_box(grid, 6, 10, 10, 15, 27, 32, 1)       # Left shoulder
    fill_box(grid, 6, 8, 11, 14, 32, 32, 2)
    fill_box(grid, 7, 9, 11, 14, 22, 26, 9)        # Upper arm
    fill_box(grid, 6, 9, 10, 15, 16, 21, 1)        # Yellow forearm
    fill_box(grid, 6, 6, 11, 14, 17, 20, 3)        # Black guard plate
    fill_box(grid, 7, 8, 11, 14, 13, 15, 9)        # Industrial claw fist
    fill_box(grid, 7, 8, 15, 16, 13, 14, 4)

    # --- HEAD (Z: 32..37) - Yellow Construction Hard-Hat Helmet ---
    fill_sym_box(grid, 0, 1, 11, 13, 31, 32, 9)
    fill_sym_box(grid, 0, 2, 10, 14, 32, 35, 9)    # Dark face core
    fill_sym_box(grid, 0, 2, 10, 15, 35, 37, 1)    # Yellow hard-hat dome + brim!
    fill_sym_box(grid, 0, 0, 11, 15, 37, 38, 2)    # Hard-hat top ridge
    fill_sym_box(grid, 0, 1, 14, 15, 33, 34, 6)    # Cyan industrial visor
    fill_sym_box(grid, 0, 1, 14, 15, 32, 32, 4)    # Steel chin grille

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
    v_a = export_vox(model_a, "excavator_a.vox")
    v_b = export_vox(model_b, "excavator_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: HYDRAULIC EXCAVATOR -> CONSTRUCTION ROBOT",
        "1. HYDRAULIC EXCAVATOR",
        "2. EXCAVATOR ROBOT",
        "preview_excavator.png",
        yaw_a=-42, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"excavator: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
