import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Wu Castle / Shiro (呉・城): Imperial Keep with Stone Base, Battlements & Crimson Red Banners (呉＝赤)
PALETTE = {
    1: (204, 40, 46, 255),    # Wu Crimson Red Banners, Trim & Roof Accents (呉＝赤)
    2: (128, 22, 32, 255),    # Deep Burgundy Shading & Dark Tile Trim
    3: (138, 136, 142, 255),  # Sloped Stone Base & Wall Granite (石垣)
    4: (96, 94, 102, 255),    # Dark Stone Blocks & Battlement Shading
    5: (242, 236, 224, 255),  # Crisp Ivory Castle Plaster Walls (白壁)
    6: (72, 62, 68, 255),     # Dark Plum-Slate Keep Roof Tiles (瓦屋根)
    7: (116, 72, 42, 255),    # Lacquered Timber Beams, Columns & Great Gate Doors
    8: (244, 198, 52, 255),   # Bright Gold Roof Ornaments (鯱) & Gate Studs
    9: (40, 36, 40, 255),     # Deep Window Recesses & Iron Gate Bands
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


def add_tiered_roof(grid, x0, x1, y0, y1, z_base, height, tile_col, trim_col, accent_col):
    for step in range(height):
        rx0, rx1 = x0 + step, x1 - step
        ry0, ry1 = y0 + step, y1 - step
        if rx0 > rx1 or ry0 > ry1:
            break
        col = tile_col if step > 0 else trim_col
        fill_box(grid, rx0, rx1, ry0, ry1, z_base + step, z_base + step, col)
        if step == 0:
            for cx in (rx0, rx1):
                for cy in (ry0, ry1):
                    fill_box(grid, cx, cx, cy, cy, z_base + 1, z_base + 1, accent_col)
    top_z = z_base + height - 1
    rx0, rx1 = x0 + height - 1, x1 - height + 1
    cy = (y0 + y1) // 2
    if rx0 <= rx1:
        fill_box(grid, rx0, rx1, cy, cy + 1, top_z + 1, top_z + 1, accent_col)


# ============================================================
# WU CASTLE / SHIRO (呉・城: 天守＋城壁＋石垣) (34 x 34 x 40)
# ============================================================
def build_a():
    grid = np.zeros((34, 34, 40), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 16
    cx_r = X // 2      # 17

    # --- 1. SLOPED STONE FOUNDATION (石垣, Z: 0..6) ---
    fill_box(grid, 2, 31, 2, 31, 0, 1, 4)
    fill_box(grid, 3, 30, 3, 30, 2, 4, 3)
    fill_box(grid, 4, 29, 4, 29, 5, 6, 3)
    for z, off in ((1, 2), (3, 3), (5, 4)):
        for p in range(off + 1, X - off - 1, 4):
            fill_box(grid, p, p + 1, off, off, z, z, 4)
            fill_box(grid, p, p + 1, Y - 1 - off, Y - 1 - off, z, z, 4)
            fill_box(grid, off, off, p, p + 1, z, z, 4)
            fill_box(grid, X - 1 - off, X - 1 - off, p, p + 1, z, z, 4)

    # --- 2. OUTER CASTLE WALLS & 4 CORNER BASTIONS (城壁, Z: 7..13) ---
    fill_box(grid, 4, 29, 4, 5, 7, 11, 5)
    fill_box(grid, 4, 29, 28, 29, 7, 11, 5)
    fill_box(grid, 4, 5, 4, 29, 7, 11, 5)
    fill_box(grid, 28, 29, 4, 29, 7, 11, 5)
    fill_box(grid, 4, 29, 4, 5, 12, 12, 4)
    fill_box(grid, 4, 29, 28, 29, 12, 12, 4)
    fill_box(grid, 4, 5, 4, 29, 12, 12, 4)
    fill_box(grid, 28, 29, 4, 29, 12, 12, 4)
    for p in range(5, 29, 3):
        fill_box(grid, p, p + 1, 4, 4, 13, 13, 3)
        fill_box(grid, p, p + 1, 29, 29, 13, 13, 3)
        fill_box(grid, 4, 4, p, p + 1, 13, 13, 3)
        fill_box(grid, 29, 29, p, p + 1, 13, 13, 3)
    for bx0, by0 in ((3, 3), (27, 3), (3, 27), (27, 27)):
        fill_box(grid, bx0, bx0 + 3, by0, by0 + 3, 7, 13, 5)
        fill_box(grid, bx0, bx0 + 3, by0, by0 + 3, 12, 12, 1)  # Wu crimson band
        fill_box(grid, bx0 - 1, bx0 + 4, by0 - 1, by0 + 4, 14, 14, 6)
        fill_box(grid, bx0 + 1, bx0 + 2, by0 + 1, by0 + 2, 15, 15, 2)

    # --- 3. FRONT GATEHOUSE (城門, +Y face, Y: 28..31, Z: 0..15) ---
    fill_sym_box(grid, 0, 4, 28, 31, 0, 1, 4)
    fill_sym_box(grid, 3, 5, 28, 30, 2, 12, 3)
    fill_sym_box(grid, 0, 2, 29, 30, 2, 8, 7)
    fill_sym_box(grid, 0, 0, 30, 30, 2, 8, 9)
    fill_sym_box(grid, 1, 2, 30, 30, 5, 5, 9)
    fill_sym_box(grid, 1, 1, 30, 30, 7, 7, 8)
    fill_sym_box(grid, 0, 4, 28, 30, 9, 12, 5)
    fill_sym_box(grid, 0, 3, 30, 30, 10, 11, 1)  # Wu crimson gate plaque
    fill_sym_box(grid, 0, 1, 30, 30, 10, 11, 8)  # Gold gate crest
    add_tiered_roof(grid, cx_l - 5, cx_r + 5, 27, 31, 13, 3, 6, 2, 1)
    for side_x in (cx_l - 6, cx_r + 6):
        fill_box(grid, side_x, side_x, 29, 29, 13, 19, 7)
        fill_box(grid, side_x, side_x, 30, 30, 15, 18, 1)
        fill_box(grid, side_x, side_x, 30, 30, 16, 16, 8)

    # --- 4. CENTRAL 3-TIERED KEEP / TENSHU (本丸・天守, Z: 7..36) ---
    fill_box(grid, 9, 24, 8, 23, 7, 9, 4)

    # Tier 1 Keep (Z: 10..16)
    fill_box(grid, 10, 23, 9, 22, 10, 16, 5)
    fill_box(grid, 10, 23, 9, 22, 10, 10, 7)
    fill_box(grid, 10, 23, 9, 22, 15, 15, 1)     # Wu crimson trim
    for px in (10, 23):
        for py in (9, 22):
            fill_box(grid, px, px, py, py, 10, 16, 1)  # Crimson lacquer corner columns!
    for wx in (13, 19):
        fill_box(grid, wx, wx + 1, 22, 22, 12, 13, 9)
        fill_box(grid, wx, wx + 1, 9, 9, 12, 13, 9)
    add_tiered_roof(grid, 7, 26, 6, 25, 16, 3, 6, 2, 1)

    # Tier 2 Keep (Z: 19..24)
    fill_box(grid, 11, 22, 10, 21, 19, 24, 5)
    fill_box(grid, 11, 22, 10, 21, 23, 23, 1)
    for px in (11, 22):
        for py in (10, 21):
            fill_box(grid, px, px, py, py, 19, 24, 1)
    for wx in (14, 18):
        fill_box(grid, wx, wx + 1, 21, 21, 20, 21, 9)
        fill_box(grid, wx, wx + 1, 10, 10, 20, 21, 9)
    add_tiered_roof(grid, 9, 24, 8, 23, 24, 3, 6, 2, 1)

    # Tier 3 Top Keep Chamber (Z: 27..31)
    fill_box(grid, 13, 20, 12, 19, 27, 31, 5)
    fill_box(grid, 13, 20, 12, 19, 27, 27, 1)
    fill_box(grid, 15, 18, 19, 19, 28, 30, 9)
    fill_box(grid, 15, 18, 12, 12, 28, 30, 9)
    fill_box(grid, 13, 13, 14, 17, 28, 30, 9)
    fill_box(grid, 20, 20, 14, 17, 28, 30, 9)
    # Grand Top Keep Roof (Z: 31..34) + Gold Shachihoko (Z: 35..36)
    add_tiered_roof(grid, 10, 23, 9, 22, 31, 4, 6, 1, 8)
    fill_box(grid, 13, 14, 15, 16, 35, 36, 8)
    fill_box(grid, 19, 20, 15, 16, 35, 36, 8)

    # --- 5. GRAND WU CRIMSON RED FLAG ON REAR-RIGHT BASTION (Z: 15..39) ---
    fill_box(grid, 28, 28, 4, 4, 15, 38, 7)
    fill_box(grid, 28, 28, 4, 4, 39, 39, 8)
    fill_box(grid, 28, 28, 5, 11, 31, 37, 1)     # Large Wu Crimson Flag!
    fill_box(grid, 28, 28, 7, 9, 33, 35, 8)      # Gold emblem
    fill_box(grid, 28, 28, 5, 11, 31, 31, 2)     # Burgundy lower hem

    hollow_interior_26(grid, 1, Z - 2)
    fill_box(grid, 5, 28, 5, 28, 0, 4, 0)
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


def render_voxel_iso(grid, yaw_deg=35, pitch_deg=24, scale=None, img_size=(340, 340), margin=14):
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


def render_preview_single(grid, v_cnt, title_banner, label, out_path, yaw=34, pitch=24):
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
    for idx_v, (v_label, vyaw) in enumerate([("REAR VIEW", yaw + 170), ("SIDE VIEW", yaw + 85)]):
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
    v_a = export_vox(model_a, "castle_wu_a.vox")
    comp_a, minz_a = count_components_6(model_a)
    render_preview_single(
        model_a, v_a,
        "THREE KINGDOMS MAP OBJECT: WU CASTLE (CASTLE_WU)",
        "WU MAIN CASTLE (KEEP + WALLS + STONE BASE)",
        "preview_castle_wu.png",
    )
    print(f"castle_wu: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a})")
