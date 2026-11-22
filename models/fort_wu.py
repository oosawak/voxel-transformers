import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Wu Fort / Toride (呉・砦): Wooden Watchtower & Spiked Palisade with Wu Crimson Banner (呉＝赤)
PALETTE = {
    1: (204, 40, 46, 255),    # Wu Crimson Red War Curtain, Roof Trim & Flag (呉＝赤)
    2: (128, 22, 32, 255),    # Deep Burgundy Flag Shading
    3: (146, 98, 56, 255),    # Palisade Timber Logs & Watchtower Deck
    4: (100, 64, 36, 255),    # Dark Timber Posts, Crossbeams & Shadows
    5: (132, 114, 92, 255),   # Packed Earth Fort Ground Base
    6: (74, 62, 68, 255),     # Dark Plum-Slate Watchtower Roof Tiles
    7: (244, 198, 52, 255),   # Bright Gold Flag Emblem, Finial & Gate Trim
    8: (146, 144, 148, 255),  # Stone Footings & Fort Corner Stones
    9: (44, 38, 42, 255),     # Dark Shadow Accents & Ladder Rungs
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(int(x0), int(x1))), min(X - 1, max(int(x0), int(x1)))
    y0, y1 = max(0, min(int(y0), int(y1))), min(Y - 1, max(int(y0), int(y1)))
    z0, z1 = max(0, min(int(z0), int(z1))), min(Z - 1, max(int(z0), int(z1)))
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


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
# WU FORT / TORIDE (呉・砦: 小さな櫓＋柵) (24 x 24 x 30)
# ============================================================
def build_a():
    grid = np.zeros((24, 24, 30), dtype=np.uint8)
    X, Y, Z = grid.shape

    # --- 1. PACKED-EARTH GROUND BASE (Z=0) ---
    fill_box(grid, 2, 21, 2, 21, 0, 0, 5)
    for sx, sy in ((2, 2), (20, 2), (2, 20), (20, 20)):
        fill_box(grid, sx, sx + 1, sy, sy + 1, 0, 1, 8)

    # --- 2. POINTED WOODEN PALISADE FENCE (木柵, Z: 1..8) ---
    fill_box(grid, 2, 21, 2, 2, 1, 6, 3)
    fill_box(grid, 2, 2, 2, 21, 1, 6, 3)
    fill_box(grid, 21, 21, 2, 21, 1, 6, 3)
    fill_box(grid, 2, 8, 21, 21, 1, 6, 3)
    fill_box(grid, 15, 21, 21, 21, 1, 6, 3)
    for hz in (2, 5):
        fill_box(grid, 2, 21, 2, 2, hz, hz, 4)
        fill_box(grid, 2, 2, 2, 21, hz, hz, 4)
        fill_box(grid, 21, 21, 2, 21, hz, hz, 4)
        fill_box(grid, 2, 8, 21, 21, hz, hz, 4)
        fill_box(grid, 15, 21, 21, 21, hz, hz, 4)
    for p in range(2, 22, 2):
        fill_box(grid, p, p, 2, 2, 7, 7, 3)
        fill_box(grid, 2, 2, p, p, 7, 7, 3)
        fill_box(grid, 21, 21, p, p, 7, 7, 3)
        if p <= 8 or p >= 15:
            fill_box(grid, p, p, 21, 21, 7, 7, 3)

    # Front Timber Fort Gate Frame & Wu Crimson Signboard
    fill_box(grid, 8, 8, 21, 21, 1, 8, 4)
    fill_box(grid, 15, 15, 21, 21, 1, 8, 4)
    fill_box(grid, 7, 16, 21, 21, 8, 8, 4)
    fill_box(grid, 9, 14, 21, 21, 7, 7, 1)
    fill_box(grid, 11, 12, 21, 21, 7, 7, 7)

    # --- 3. CENTRAL WOODEN WATCHTOWER / YAGURA (小さな櫓, Z: 1..22) ---
    for px in (8, 15):
        for py in (7, 14):
            fill_box(grid, px, px, py, py, 1, 1, 8)
            fill_box(grid, px, px, py, py, 2, 17, 4)
    fill_box(grid, 8, 15, 7, 7, 5, 5, 4)
    fill_box(grid, 8, 15, 14, 14, 5, 5, 4)
    fill_box(grid, 8, 8, 7, 14, 5, 5, 4)
    fill_box(grid, 15, 15, 7, 14, 5, 5, 4)
    fill_box(grid, 11, 11, 15, 15, 1, 10, 4)
    fill_box(grid, 13, 13, 15, 15, 1, 10, 4)
    for lz in (2, 4, 6, 8, 10):
        fill_box(grid, 11, 13, 15, 15, lz, lz, 9)

    fill_box(grid, 7, 16, 6, 15, 10, 10, 4)
    fill_box(grid, 7, 16, 6, 15, 11, 11, 3)

    # Wu Crimson War Curtain (陣幕)
    fill_box(grid, 7, 16, 6, 6, 12, 13, 1)
    fill_box(grid, 7, 16, 15, 15, 12, 13, 1)
    fill_box(grid, 7, 7, 6, 15, 12, 13, 1)
    fill_box(grid, 16, 16, 6, 15, 12, 13, 1)
    fill_box(grid, 7, 16, 6, 6, 14, 14, 4)
    fill_box(grid, 7, 16, 15, 15, 14, 14, 4)
    fill_box(grid, 7, 7, 6, 15, 14, 14, 4)
    fill_box(grid, 16, 16, 6, 15, 14, 14, 4)
    fill_box(grid, 11, 12, 15, 15, 12, 13, 7)

    # Watchtower Roof (Z: 18..21)
    fill_box(grid, 6, 17, 5, 16, 18, 18, 2)
    fill_box(grid, 7, 16, 6, 15, 19, 19, 6)
    fill_box(grid, 8, 15, 7, 14, 20, 20, 6)
    fill_box(grid, 9, 14, 9, 12, 21, 21, 1)
    for cx in (6, 17):
        for cy in (5, 16):
            fill_box(grid, cx, cx, cy, cy, 19, 19, 1)

    # --- 4. TALL WU CRIMSON WATCHTOWER FLAG (Z: 22..29) ---
    fill_box(grid, 12, 12, 10, 10, 22, 28, 4)
    fill_box(grid, 12, 12, 10, 10, 29, 29, 7)
    fill_box(grid, 12, 12, 11, 16, 24, 28, 1)
    fill_box(grid, 12, 12, 13, 14, 25, 27, 7)
    fill_box(grid, 12, 12, 11, 16, 24, 24, 2)

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
    v_a = export_vox(model_a, "fort_wu_a.vox")
    comp_a, minz_a = count_components_6(model_a)
    render_preview_single(
        model_a, v_a,
        "THREE KINGDOMS MAP OBJECT: WU FORT (FORT_WU)",
        "WU FORT (WATCHTOWER + PALISADE)",
        "preview_fort_wu.png",
    )
    print(f"fort_wu: A={v_a} voxels {model_a.shape} (comp={comp_a}, minZ={minz_a})")
