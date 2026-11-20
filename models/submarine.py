import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (48, 60, 78, 255),     # Naval Slate Upper Pressure Hull
    2: (80, 94, 114, 255),    # Lighter Naval Grey Armor Highlight
    3: (172, 44, 46, 255),    # Anti-Fouling Crimson Lower Hull
    4: (26, 32, 42, 255),     # Deep Hull Shadow / Ballast Vents / Joints
    5: (220, 174, 52, 255),   # Brass Propeller & Deep-Sea Trim
    6: (38, 212, 236, 255),   # Sonar Cyan Viewport / Visor
    7: (155, 246, 255, 255),  # Bright Aqua Sonar Reactor Core
    8: (238, 198, 46, 255),   # Hazard Yellow Depth Markings
    9: (162, 174, 188, 255),  # Steel Silver Periscope & Torpedo Tubes
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
# FORM A: ATTACK SUBMARINE (18 x 46 x 17)
# ==========================================
def build_a():
    grid = np.zeros((18, 46, 17), dtype=np.uint8)

    # --- TEARDROP PRESSURE HULL (Y: 4..44, Z: 1..8) ---
    # Mid-body cylinder (Y: 14..38)
    fill_sym_box(grid, 0, 3, 14, 38, 2, 7, 1)
    fill_sym_box(grid, 0, 2, 14, 38, 1, 8, 1)
    fill_sym_box(grid, 0, 1, 16, 36, 3, 6, 0)     # Hollow hull interior
    # Anti-fouling crimson red lower hull! (Z: 1..3)
    fill_sym_box(grid, 0, 3, 14, 38, 2, 3, 3)
    fill_sym_box(grid, 0, 2, 14, 38, 1, 1, 3)
    # Rounded Sonar Bow (Y: 39..44)
    fill_sym_box(grid, 0, 2, 39, 41, 2, 7, 1)
    fill_sym_box(grid, 0, 2, 39, 41, 2, 3, 3)
    fill_sym_box(grid, 0, 1, 42, 43, 3, 6, 1)
    fill_sym_box(grid, 0, 1, 42, 43, 3, 3, 3)
    fill_sym_box(grid, 0, 0, 44, 44, 4, 5, 2)
    # Twin torpedo tubes & yellow bow depth markings
    fill_sym_box(grid, 1, 1, 42, 43, 5, 5, 9)
    fill_sym_box(grid, 2, 2, 40, 40, 4, 5, 8)
    # Upper deck casing & ballast vents
    fill_sym_box(grid, 0, 1, 12, 38, 8, 8, 2)
    for vy in range(16, 36, 4):
        fill_sym_box(grid, 3, 3, vy, vy + 1, 5, 5, 4)

    # Tapered Stern (Y: 4..13)
    fill_sym_box(grid, 0, 2, 9, 13, 2, 7, 1)
    fill_sym_box(grid, 0, 2, 9, 13, 2, 3, 3)
    fill_sym_box(grid, 0, 1, 5, 8, 3, 6, 1)
    fill_sym_box(grid, 0, 1, 5, 8, 3, 3, 3)
    fill_sym_box(grid, 0, 0, 3, 4, 4, 5, 4)

    # --- CRUCIFORM STERN TAIL FINS & BRASS PROPELLER (Y: 1..10) ---
    # Horizontal stern diving planes
    fill_sym_box(grid, 2, 6, 5, 8, 4, 4, 2)
    fill_sym_box(grid, 5, 6, 5, 7, 4, 4, 8)       # Yellow fin tip stripes
    # Vertical upper & lower rudder
    fill_sym_box(grid, 0, 0, 5, 9, 7, 10, 2)
    fill_sym_box(grid, 0, 0, 5, 8, 0, 2, 3)
    # Gleaming 4-blade Brass Propeller at very stern (Y: 1..2)!
    fill_sym_box(grid, 0, 0, 2, 2, 4, 5, 5)
    fill_sym_box(grid, 0, 2, 1, 1, 4, 5, 5)
    fill_sym_box(grid, 0, 0, 1, 1, 2, 7, 5)

    # --- CONNING TOWER (SAIL), DIVING PLANES & PERISCOPE (Y: 24..34, Z: 9..16) ---
    fill_sym_box(grid, 0, 1, 24, 33, 9, 12, 1)
    fill_sym_box(grid, 0, 1, 25, 32, 13, 13, 2)
    # Cyan bridge viewport on sail front
    fill_sym_box(grid, 0, 1, 33, 33, 11, 12, 6)
    fill_sym_box(grid, 0, 0, 33, 33, 12, 12, 7)
    # Forward Sail Diving Planes (wings sticking out from tower!)
    fill_sym_box(grid, 2, 5, 28, 31, 11, 11, 2)
    fill_sym_box(grid, 5, 5, 28, 30, 11, 11, 8)
    # Periscope & Radar Mast
    fill_box(grid, 9, 9, 30, 30, 14, 16, 9)       # Periscope shaft
    fill_box(grid, 9, 9, 30, 31, 16, 16, 9)       # Periscope head
    fill_box(grid, 9, 9, 31, 31, 16, 16, 6)       # Cyan optical lens
    fill_box(grid, 8, 8, 27, 27, 14, 15, 9)       # Sonar/comms mast

    return grid


# ==========================================
# FORM B: SUBMARINE DIVER ROBOT (30 x 22 x 39)
# ==========================================
def build_b():
    grid = np.zeros((30, 22, 39), dtype=np.uint8)

    # --- FEET (Z: 0..2) - Deep-Sea Flipper Boots + Brass Heel Propellers! ---
    fill_sym_box(grid, 2, 4, 7, 15, 0, 1, 4)
    fill_sym_box(grid, 2, 4, 12, 16, 1, 2, 3)     # Crimson lower-hull toes
    fill_sym_box(grid, 3, 3, 14, 16, 1, 2, 8)     # Yellow toe markings
    # Brass propeller turbines mounted on heels!
    fill_sym_box(grid, 2, 4, 6, 7, 1, 2, 5)
    fill_sym_box(grid, 3, 3, 5, 5, 0, 3, 5)

    # --- LOWER LEGS (Z: 3..14) - Split Navy/Red Stern Hull + Tail Fins! ---
    fill_sym_box(grid, 2, 4, 9, 13, 3, 13, 1)
    fill_sym_box(grid, 4, 4, 9, 13, 4, 12, 3)     # Crimson lower hull stripe
    fill_sym_box(grid, 3, 3, 13, 14, 5, 10, 2)
    fill_sym_box(grid, 2, 3, 13, 14, 11, 14, 2)   # Knee diving armor
    fill_sym_box(grid, 3, 3, 14, 14, 12, 13, 8)   # Yellow depth mark on knees
    # Cruciform Submarine Tail Fins jutting off outer calves!
    fill_sym_box(grid, 5, 7, 10, 12, 5, 9, 2)
    fill_sym_box(grid, 7, 7, 10, 12, 6, 8, 8)     # Yellow fin tip

    # --- THIGHS (Z: 14..19) ---
    fill_sym_box(grid, 2, 3, 9, 12, 14, 19, 4)
    fill_sym_box(grid, 2, 3, 12, 13, 15, 18, 2)
    fill_sym_box(grid, 3, 3, 10, 11, 16, 18, 9)

    # --- WAIST / PELVIS (Z: 19..22) - Crimson Anti-Fouling Hull Belt! ---
    fill_sym_box(grid, 0, 4, 9, 13, 19, 21, 3)    # Crimson waist hull!
    fill_sym_box(grid, 0, 1, 13, 14, 19, 22, 1)
    fill_sym_box(grid, 0, 0, 14, 14, 20, 21, 8)   # Yellow hazard buckle
    fill_sym_box(grid, 4, 4, 10, 12, 19, 21, 2)

    # --- TORSO / CHEST (Z: 22..31) - Rounded Submarine Pressure Bow & Sonar Core! ---
    fill_sym_box(grid, 0, 4, 8, 14, 22, 31, 1)
    fill_sym_box(grid, 0, 3, 13, 14, 22, 24, 3)   # Crimson lower bow abs
    # Rounded bulging sonar bow chest!
    fill_sym_box(grid, 0, 4, 14, 16, 25, 30, 1)
    fill_sym_box(grid, 0, 3, 16, 17, 26, 29, 2)
    # Glowing Cyan/Aqua Sonar Viewport Core in center chest!
    fill_sym_box(grid, 0, 1, 17, 18, 27, 29, 6)
    fill_sym_box(grid, 0, 0, 18, 18, 28, 28, 7)
    # Twin Silver Torpedo Tube Ports flanking chest + yellow depth lines!
    fill_sym_box(grid, 3, 3, 16, 17, 28, 29, 9)
    fill_sym_box(grid, 4, 4, 15, 16, 26, 27, 8)

    # --- BACKPACK (Y: 3..7) - Conning Tower (Sail) & Periscope Sensor! ---
    fill_sym_box(grid, 0, 3, 5, 7, 22, 31, 1)
    fill_sym_box(grid, 0, 2, 3, 5, 24, 33, 2)     # Conning tower sail fin on back!
    fill_sym_box(grid, 0, 1, 3, 3, 29, 32, 6)     # Rear bridge light
    # Tall Steel Periscope peeking over RIGHT shoulder (+X)!
    fill_box(grid, 17, 17, 6, 7, 32, 38, 9)
    fill_box(grid, 17, 17, 7, 9, 37, 38, 9)
    fill_box(grid, 17, 17, 9, 9, 37, 38, 6)       # Cyan optical periscope lens!
    # Rear brass underwater thruster pods
    fill_sym_box(grid, 2, 3, 4, 5, 22, 24, 5)

    # --- SHOULDERS & ARMS (Z: 14..33) - Diving Plane Shoulders & Torpedo Forearms! ---
    fill_sym_box(grid, 5, 8, 9, 13, 27, 32, 1)    # Pressurized dome shoulders
    fill_sym_box(grid, 6, 8, 10, 12, 32, 32, 2)
    # Sail Diving Planes jutting upward/outward from shoulders!
    fill_sym_box(grid, 9, 11, 10, 12, 30, 31, 2)
    fill_sym_box(grid, 11, 11, 10, 12, 31, 31, 8) # Yellow plane tips
    # Upper arms (dark ballast joints)
    fill_sym_box(grid, 6, 7, 10, 12, 22, 26, 4)
    fill_sym_box(grid, 6, 7, 10, 12, 23, 25, 9)
    # Cylindrical hull forearms + Silver Twin Torpedo Launcher Pods!
    fill_sym_box(grid, 6, 8, 9, 13, 16, 21, 1)
    fill_sym_box(grid, 8, 8, 10, 12, 17, 20, 3)   # Red hull stripe on arms
    fill_sym_box(grid, 7, 8, 13, 16, 17, 20, 9)   # Forward torpedo pods!
    fill_sym_box(grid, 7, 8, 16, 16, 18, 19, 8)   # Yellow torpedo warhead tips
    # Brass-accented diver claw fists
    fill_sym_box(grid, 6, 7, 10, 12, 13, 15, 4)
    fill_sym_box(grid, 6, 7, 12, 13, 13, 14, 5)

    # --- HEAD (Z: 32..38) - Deep-Sea Diver / Sub-Commander Helmet ---
    fill_sym_box(grid, 0, 1, 10, 11, 31, 32, 4)
    fill_sym_box(grid, 0, 2, 9, 13, 32, 36, 1)    # Navy diving dome
    fill_sym_box(grid, 0, 2, 10, 12, 36, 37, 2)
    fill_sym_box(grid, 0, 0, 11, 13, 37, 38, 8)   # Yellow fin crest
    fill_sym_box(grid, 0, 1, 13, 14, 33, 35, 6)   # Big glowing cyan sonar visor!
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 7)   # Bright aqua glint
    fill_sym_box(grid, 3, 3, 10, 11, 33, 35, 5)   # Brass diver ear-valves

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
    v_a = export_vox(model_a, "submarine_a.vox")
    v_b = export_vox(model_b, "submarine_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: ATTACK SUBMARINE -> DEEP-SEA ROBOT",
        "1. ATTACK SUBMARINE",
        "2. SUBMARINE DIVER ROBOT",
        "preview_submarine.png",
        yaw_a=44, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"submarine: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
