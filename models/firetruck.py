import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (222, 34, 38, 255),    # Fire Engine Bright Red
    2: (242, 245, 250, 255),  # Rescue Ladder White / Safety Stripe
    3: (198, 208, 222, 255),  # Chrome Bumper / Grille / Ladder Rails
    4: (36, 38, 44, 255),     # Heavy Rubber Tires / Inner Joints
    5: (74, 196, 242, 255),   # Cab Windshield Cyan / Robot Visor
    6: (255, 78, 78, 255),    # Flashing Emergency Siren Lightbar
    7: (255, 206, 36, 255),   # Caution Yellow Outriggers / Badge / Lights
    8: (116, 126, 140, 255),  # Steel Roll-Up Shutter Doors / Turntable
    9: (152, 22, 28, 255),    # Deep Crimson Shading
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


def fill_wheel_sym(grid, x_off0, x_off1, yc, zc, r, tire_col=4, hub_col=3):
    """Fill symmetric fire-truck wheels."""
    for dy in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d2 = dy * dy + dz * dz
            if d2 <= r * r + 1:
                fill_sym_box(grid, x_off0, x_off1, yc + dy, yc + dy, zc + dz, zc + dz, tire_col)
            if d2 <= max(0, (r - 1) * (r - 1)):
                fill_sym_box(grid, x_off1, x_off1, yc + dy, yc + dy, zc + dz, zc + dz, hub_col)


# ==========================================
# FORM A: LADDER FIRE TRUCK (16 x 42 x 20)
# ==========================================
def build_a():
    grid = np.zeros((16, 42, 20), dtype=np.uint8)

    # --- CHASSIS & OUTRIGGERS (Y: 3..39, Z: 2..3) ---
    fill_sym_box(grid, 0, 3, 3, 38, 2, 3, 4)
    fill_sym_box(grid, 0, 2, 4, 37, 2, 3, 0)      # Hollow chassis core
    fill_sym_box(grid, 0, 4, 39, 40, 2, 3, 3)     # Chrome front bumper
    fill_sym_box(grid, 4, 4, 20, 21, 2, 3, 7)     # Yellow stabilizer outriggers

    # --- FORWARD FLAT-NOSE FIRE CAB (Y: 29..39, Z: 4..11) ---
    fill_sym_box(grid, 0, 4, 29, 39, 4, 11, 1)
    fill_sym_box(grid, 0, 3, 30, 38, 5, 10, 0)    # Hollow cab interior
    fill_sym_box(grid, 0, 4, 39, 39, 6, 6, 2)     # Crisp white safety stripe
    fill_sym_box(grid, 4, 4, 29, 39, 6, 6, 2)
    # Chrome front grille & warm headlights
    fill_sym_box(grid, 0, 2, 39, 40, 4, 5, 3)
    fill_sym_box(grid, 3, 4, 39, 39, 4, 5, 7)     # Headlights
    # Wide panoramic cyan windshield & side windows
    fill_sym_box(grid, 0, 3, 39, 39, 8, 10, 5)
    fill_sym_box(grid, 4, 4, 32, 37, 8, 10, 5)
    # Flashing red emergency lightbar on cab roof!
    fill_sym_box(grid, 1, 3, 37, 38, 12, 12, 6)
    fill_sym_box(grid, 0, 0, 37, 38, 12, 12, 2)

    # --- REAR EQUIPMENT BODY WITH ROLL-UP SHUTTERS (Y: 3..28, Z: 4..10) ---
    fill_sym_box(grid, 0, 4, 3, 28, 4, 10, 1)
    fill_sym_box(grid, 0, 3, 4, 27, 5, 9, 0)      # Hollow equipment bay
    fill_sym_box(grid, 4, 4, 3, 28, 6, 6, 2)      # White safety stripe
    # Silver roll-up shutter equipment doors!
    fill_sym_box(grid, 4, 4, 22, 27, 4, 9, 8)
    fill_sym_box(grid, 4, 4, 13, 18, 4, 9, 8)
    fill_sym_box(grid, 4, 4, 5, 9, 5, 9, 8)
    for sz in (5, 7, 9):
        fill_sym_box(grid, 4, 4, 22, 27, sz, sz, 3)
        fill_sym_box(grid, 4, 4, 13, 18, sz, sz, 3)
    # Rear yellow reflective chevrons & red tail lights
    fill_sym_box(grid, 0, 3, 3, 3, 5, 9, 7)
    fill_sym_box(grid, 1, 2, 3, 3, 6, 8, 1)
    fill_sym_box(grid, 3, 4, 3, 3, 4, 4, 6)

    # --- TURNTABLE & EXTENDING WHITE LATTICE RESCUE LADDER (Y: 8..39, Z: 11..19) ---
    fill_sym_box(grid, 0, 2, 8, 14, 11, 12, 8)    # Rotating turntable base
    fill_sym_box(grid, 1, 2, 11, 13, 12, 13, 3)   # Hydraulic lift cylinders
    # Angled white lattice ladder rising forward over cab roof!
    for step in range(25):
        ly = 13 + step
        lz = 12 + (step * 7) // 24
        # Twin outer ladder rails (white/chrome)
        fill_sym_box(grid, 2, 2, ly, ly, lz, lz + 1, 2)
        if step % 3 == 0:
            # Open ladder rungs!
            fill_sym_box(grid, 0, 1, ly, ly, lz, lz, 3)
    # Rescue basket & chrome water monitor nozzle at ladder tip! (Y: 37..40, Z: 17..19)
    fill_sym_box(grid, 0, 2, 37, 40, 17, 17, 2)
    fill_sym_box(grid, 2, 2, 37, 40, 18, 19, 2)
    fill_sym_box(grid, 0, 2, 40, 40, 18, 19, 7)   # Yellow basket bumper
    fill_sym_box(grid, 0, 0, 39, 41, 19, 19, 3)   # Water cannon nozzle!

    # --- HEAVY FIRE-TRUCK WHEELS ---
    fill_wheel_sym(grid, 3, 5, 34, 2, 2)  # Front cab axle
    fill_wheel_sym(grid, 3, 5, 16, 2, 2)  # Rear tandem 1
    fill_wheel_sym(grid, 3, 5, 10, 2, 2)  # Rear tandem 2

    return grid


# ==========================================
# FORM B: FIRE-RESCUE LADDER ROBOT (32 x 24 x 44)
# ==========================================
def build_b():
    grid = np.zeros((32, 24, 44), dtype=np.uint8)

    # --- FEET (Z: 0..2) - Heavy yellow outrigger-stabilizer rescue boots! ---
    fill_sym_box(grid, 2, 4, 7, 15, 0, 1, 4)
    fill_sym_box(grid, 2, 4, 12, 16, 1, 2, 7)     # Yellow outrigger toes!
    fill_sym_box(grid, 3, 3, 14, 16, 1, 2, 3)     # Chrome bumper tips
    fill_sym_box(grid, 2, 4, 7, 8, 0, 2, 8)

    # --- LOWER LEGS (Z: 3..14) - Red equipment bays + white stripe + truck tires! ---
    fill_sym_box(grid, 2, 4, 9, 13, 3, 13, 1)
    fill_sym_box(grid, 3, 3, 13, 14, 4, 11, 2)    # Crisp white shin stripe
    fill_sym_box(grid, 2, 3, 13, 14, 11, 14, 3)   # Chrome knee shields
    fill_sym_box(grid, 3, 3, 14, 14, 12, 13, 7)   # Yellow reflective knee mark
    # Fire truck tires mounted on outer calves!
    fill_wheel_sym(grid, 5, 6, 11, 6, 2)
    fill_wheel_sym(grid, 5, 6, 11, 11, 2)

    # --- THIGHS (Z: 14..19) - Crisp White & Steel Rescue Thighs ---
    fill_sym_box(grid, 2, 3, 9, 12, 14, 19, 2)
    fill_sym_box(grid, 2, 3, 10, 11, 14, 15, 4)
    fill_sym_box(grid, 3, 3, 10, 11, 16, 18, 8)

    # --- WAIST / PELVIS (Z: 19..22) - Chrome Front Bumper Belt! ---
    fill_sym_box(grid, 0, 4, 9, 13, 19, 21, 3)    # Chrome bumper waist!
    fill_sym_box(grid, 0, 1, 13, 14, 19, 22, 1)
    fill_sym_box(grid, 0, 0, 14, 14, 20, 21, 7)   # Yellow rescue badge buckle
    fill_sym_box(grid, 4, 4, 10, 12, 19, 21, 9)

    # --- TORSO / CHEST (Z: 22..31) - Red Fire-Engine Cab Front & Siren Lightbar! ---
    fill_sym_box(grid, 0, 4, 8, 14, 22, 31, 1)
    fill_sym_box(grid, 0, 2, 14, 15, 22, 24, 3)   # Chrome radiator grille abs!
    fill_sym_box(grid, 0, 1, 15, 15, 22, 24, 8)
    fill_sym_box(grid, 0, 5, 14, 15, 25, 25, 2)   # Crisp white safety stripe
    # Wide cyan cab windshield across upper chest!
    fill_sym_box(grid, 0, 4, 14, 16, 26, 30, 5)
    fill_sym_box(grid, 0, 0, 15, 16, 26, 30, 1)   # Center windshield pillar
    fill_sym_box(grid, 4, 4, 15, 16, 26, 27, 7)   # Cab headlights on chest flanks
    # Flashing Red Emergency Siren Lightbar on collarbone!
    fill_sym_box(grid, 1, 4, 14, 15, 31, 32, 6)
    fill_sym_box(grid, 0, 0, 14, 15, 31, 32, 2)

    # --- BACKPACK & SHOULDER-MOUNTED WHITE RESCUE LADDER CANNON! ---
    fill_sym_box(grid, 0, 3, 5, 7, 22, 31, 8)     # Turntable backpack
    fill_sym_box(grid, 0, 2, 4, 5, 24, 29, 9)
    # MASSIVE WHITE LATTICE RESCUE LADDER towering over outer RIGHT SHOULDER (+X)!
    # Positioned clear of the firefighter helmet so face & visor stay 100% visible!
    for step in range(14):
        ly = 6 + step
        lz = 32 + (step * 9) // 13
        fill_box(grid, 22, 22, ly, ly, lz, lz + 1, 2)  # Inner white rail
        fill_box(grid, 25, 25, ly, ly, lz, lz + 1, 2)  # Outer white rail
        if step % 2 == 0:
            fill_box(grid, 23, 24, ly, ly, lz, lz, 3)  # Open chrome rungs!
    # Support mount connecting ladder to right shoulder/backpack
    fill_box(grid, 22, 24, 6, 10, 30, 32, 8)
    # Rescue water monitor nozzle at tip of ladder cannon!
    fill_box(grid, 22, 25, 19, 21, 41, 43, 7)     # Yellow tip guard
    fill_box(grid, 23, 24, 20, 23, 42, 43, 3)     # Chrome water cannon barrel!

    # --- SHOULDERS & ARMS (Z: 14..32) - Red Bays with Silver Roll-Up Shutters! ---
    fill_sym_box(grid, 5, 9, 9, 13, 27, 31, 1)
    fill_sym_box(grid, 6, 9, 10, 12, 31, 31, 2)   # White shoulder trim
    fill_sym_box(grid, 9, 9, 10, 12, 28, 30, 8)   # Silver roll-up shutter on shoulders!
    # Upper arms (steel hydraulic joints)
    fill_sym_box(grid, 6, 7, 10, 12, 22, 26, 4)
    fill_sym_box(grid, 7, 7, 10, 12, 23, 25, 3)
    # Forearms (red equipment panels + silver roll-up shutter doors)
    fill_sym_box(grid, 6, 8, 9, 13, 16, 21, 1)
    fill_sym_box(grid, 8, 8, 10, 12, 17, 20, 8)   # Shutter slats
    fill_sym_box(grid, 8, 8, 10, 12, 18, 18, 3)
    fill_sym_box(grid, 6, 8, 13, 13, 17, 17, 2)   # White wrist stripe
    # Heavy rescue fists
    fill_sym_box(grid, 6, 7, 10, 12, 13, 15, 4)
    # Left forearm Twin-Barrel Chrome High-Pressure Water Nozzle!
    fill_box(grid, 7, 8, 13, 20, 16, 17, 3)
    fill_box(grid, 7, 8, 19, 21, 16, 17, 5)       # Pressurized water jet tip!
    # Right hand Fire-Rescue Axe!
    fill_box(grid, 23, 23, 13, 14, 10, 21, 7)     # Yellow fiberglass handle
    fill_box(grid, 23, 23, 14, 17, 18, 22, 3)     # Chrome axe blade

    # --- HEAD (Z: 32..38) - Iconic Firefighter Helmet! ---
    fill_sym_box(grid, 0, 1, 10, 11, 31, 32, 4)
    fill_sym_box(grid, 0, 2, 9, 13, 32, 35, 3)    # Chrome face frame
    fill_sym_box(grid, 0, 1, 13, 14, 33, 34, 5)   # Glowing cyan rescue visor!
    # Red Firefighter Helmet Dome with Flared Neck-Brim!
    fill_sym_box(grid, 0, 2, 9, 14, 35, 37, 1)
    fill_sym_box(grid, 0, 3, 8, 11, 34, 35, 1)    # Rear firefighter neck-guard brim!
    fill_sym_box(grid, 0, 0, 11, 14, 37, 38, 1)   # Helmet comb ridge
    fill_sym_box(grid, 0, 0, 14, 15, 35, 37, 7)   # Yellow Fire-Chief shield badge!

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
    v_a = export_vox(model_a, "firetruck_a.vox")
    v_b = export_vox(model_b, "firetruck_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: LADDER FIRE TRUCK -> RESCUE ROBOT",
        "1. LADDER FIRE TRUCK",
        "2. FIRE-RESCUE ROBOT",
        "preview_firetruck.png",
        yaw_a=40, pitch_a=22, yaw_b=34, pitch_b=20,
    )
    print(f"firetruck: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
