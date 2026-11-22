import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Wei Infantry / Hohei (魏・歩兵): Royal Blue faction armor (青), sword & kite shield!
PALETTE = {
    1: (36, 92, 192, 255),    # Wei Royal Blue Surcoat & Shield Face (魏＝青)
    2: (22, 54, 126, 255),    # Deep Wei Navy Shading & Tunic
    3: (176, 188, 206, 255),  # Iron-Steel Helmet, Sword Blade & Shield Rim
    4: (96, 108, 126, 255),   # Dark Gunmetal Lamellar Armor & Boots
    5: (228, 188, 62, 255),   # Brass-Gold Shield Boss, Pommel & Belt Clasp
    6: (128, 84, 48, 255),    # Leather Straps & Hilt
    7: (248, 214, 188, 255),  # Soldier Face & Hands
    8: (42, 46, 58, 255),     # Dark Charcoal Undersuit
    9: (106, 212, 255, 255),  # Bright Wei Crest Accent & Eyes
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
# WEI INFANTRY / HOHEI (魏・歩兵: 剣と盾) (26 x 20 x 28)
# ============================================================
def build_a():
    grid = np.zeros((26, 20, 28), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 12
    cx_r = X // 2      # 13

    # Compact Tactical Boots & Greaves (Z: 0..9)
    fill_sym_box(grid, 1, 3, 8, 12, 0, 1, 8)      # Boots
    fill_sym_box(grid, 1, 3, 9, 11, 2, 8, 4)      # Iron greaves
    fill_sym_box(grid, 2, 2, 11, 11, 3, 7, 1)     # Wei blue shin trim

    # Wei Blue Armored Tunic & Lamellar Chestplate (Z: 8..18)
    fill_sym_box(grid, 0, 3, 8, 12, 8, 12, 1)     # Blue armored skirt
    fill_sym_box(grid, 0, 3, 8, 12, 11, 12, 6)    # Leather belt
    fill_sym_box(grid, 0, 0, 12, 12, 11, 12, 5)   # Brass belt buckle
    fill_sym_box(grid, 0, 3, 8, 12, 13, 18, 4)    # Iron lamellar cuirass
    fill_sym_box(grid, 0, 2, 12, 12, 14, 17, 1)   # Wei blue tabard chest!
    fill_sym_box(grid, 0, 3, 7, 8, 10, 17, 2)     # Short navy rear surcoat

    # Left Arm (-X) holding WEI IRON-RIMMED KITE SHIELD (盾!)
    fill_box(grid, cx_l - 5, cx_l - 4, 9, 12, 13, 17, 1)
    fill_box(grid, cx_l - 6, cx_l - 5, 11, 13, 11, 13, 7)   # Hand gripping shield
    # Tall Iron-Rimmed Wei Blue Kite Shield in front-left!
    fill_box(grid, cx_l - 8, cx_l - 4, 14, 15, 8, 17, 3)    # Steel shield rim
    fill_box(grid, cx_l - 7, cx_l - 5, 15, 15, 9, 16, 1)    # Wei royal blue shield face!
    fill_box(grid, cx_l - 6, cx_l - 6, 15, 16, 12, 13, 5)   # Brass boss
    fill_box(grid, cx_l - 7, cx_l - 5, 14, 15, 7, 7, 3)     # Pointed kite tip!
    fill_box(grid, cx_l - 6, cx_l - 5, 13, 14, 11, 13, 6)   # Shield grip connecting solidly to hand!

    # Right Arm (+X) holding HAN STRAIGHT SWORD (剣!)
    fill_box(grid, cx_r + 4, cx_r + 5, 9, 12, 13, 17, 1)
    fill_box(grid, cx_r + 5, cx_r + 6, 11, 14, 12, 13, 7)   # Right hand gripping sword!
    fill_box(grid, cx_r + 6, cx_r + 6, 14, 14, 10, 13, 6)   # Hilt
    fill_box(grid, cx_r + 5, cx_r + 7, 14, 14, 14, 14, 5)   # Brass crossguard
    fill_box(grid, cx_r + 6, cx_r + 6, 14, 14, 15, 25, 3)   # Gleaming straight iron sword blade!
    fill_box(grid, cx_r + 6, cx_r + 6, 15, 15, 15, 23, 3)   # Thickened blade edge!

    # Head & Wei Spiked Iron Infantry Helmet (Z: 18..27)
    fill_sym_box(grid, 0, 2, 8, 12, 18, 22, 7)    # Determined soldier face
    fill_sym_box(grid, 1, 1, 12, 12, 20, 20, 8)   # Eyes
    fill_sym_box(grid, 0, 2, 8, 12, 22, 24, 4)    # Iron helmet bowl
    fill_sym_box(grid, 0, 2, 7, 8, 19, 23, 4)     # Rear neck-guard flaps
    fill_sym_box(grid, 0, 1, 9, 12, 24, 25, 1)    # Wei blue helmet ridge
    fill_sym_box(grid, 0, 0, 10, 11, 26, 27, 3)   # Wei iron helmet spike!

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


def render_voxel_iso(grid, yaw_deg=30, pitch_deg=20, scale=None, img_size=(340, 340), margin=14):
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
                    (img_size[1] - 2 * margin) / max(1e-5, max_sy - min_sy), 10.5)
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


def render_preview_single(grid, v_cnt, title_banner, label, out_path, yaw=28, pitch=18):
    cw, ch = 640, 480
    canvas = Image.new("RGBA", (cw, ch), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, cw, 20):
        draw.line([(gx, 0), (gx, ch)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, ch, 20):
        draw.line([(0, gy), (cw, gy)], fill=(28, 34, 48, 255), width=1)
    draw.text((22, 14), title_banner, fill=(210, 225, 250, 255))
    bx, by, bw, bh = 22, 42, 596, 418
    draw.rectangle([bx, by, bx + bw, by + bh], fill=(14, 17, 24, 255), outline=(65, 80, 110, 255), width=2)
    draw.text((bx + 14, by + 10), label, fill=(235, 240, 255, 255))
    gx, gy, gz = grid.shape
    draw.text((bx + 14, by + 28), f"Grid: {gx}x{gy}x{gz} | Voxels: {v_cnt} | Z-Slices: {gz}", fill=(130, 155, 195, 255))
    r_front = render_voxel_iso(grid, yaw_deg=yaw, pitch_deg=pitch, img_size=(340, 320), margin=12)
    canvas.paste(r_front, (bx + 14, by + 50), r_front)
    # Rear view & Side view insets on right column
    for idx_v, (v_label, vyaw) in enumerate([("REAR VIEW", yaw + 170), ("SIDE VIEW", yaw + 75)]):
        rx0, ry0 = bx + 372, by + 48 + idx_v * 168
        draw.rectangle([rx0, ry0, rx0 + 210, ry0 + 158], fill=(20, 24, 34, 255), outline=(50, 62, 85, 255))
        draw.text((rx0 + 8, ry0 + 5), v_label, fill=(120, 140, 175, 255))
        rv = render_voxel_iso(grid, yaw_deg=vyaw, pitch_deg=pitch, img_size=(198, 134), margin=8)
        canvas.paste(rv, (rx0 + 6, ry0 + 18), rv)
    for pi in range(1, len(PALETTE) + 1):
        px0, py0 = bx + 14 + (pi - 1) * 22, by + 388
        draw.rectangle([px0, py0, px0 + 16, py0 + 16], fill=PALETTE[pi], outline=(70, 82, 105, 255))
    canvas.save(out_path)


if __name__ == "__main__":
    model_a = build_a()
    v_a = export_vox(model_a, "hohei_wei_a.vox")
    comp_a, minz_a = count_components_6(model_a)
    render_preview_single(
        model_a, v_a,
        "THREE KINGDOMS UNIT: WEI INFANTRY (HOHEI_WEI)",
        "WEI INFANTRY (SWORD & SHIELD)",
        "preview_hohei_wei.png",
    )
    print(f"hohei_wei: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a})")
