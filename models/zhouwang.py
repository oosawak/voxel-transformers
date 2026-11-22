import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# King Zhou / Zhouwang (紂王) -> Tyrant Black-and-Gold Emperor Boss Robot!
# King of Yin (殷の王), black-and-gold royal robes (黒と金の王衣), beaded imperial mortarboard crown (冕冠),
# intimidating tyrant presence (威圧感のある姿)!
PALETTE = {
    1: (24, 22, 32, 255),     # Pitch-Obsidian Imperial Yin Royal Robe & Armor (黒基調!)
    2: (54, 48, 66, 255),     # Dark Royal Charcoal Trim & Inner Joints
    3: (246, 198, 46, 255),   # Dazzling Imperial Gold Embroidery, Crown & Greatsword (金基調!)
    4: (182, 132, 24, 255),   # Ancient Shang-Bronze Gold Shading
    5: (178, 22, 38, 255),    # Tyrannical Blood-Crimson Inner Robe & Cloak Lining
    6: (244, 242, 236, 255),  # Pearl-Bead Crown Tassels (冕冠の珠!)
    7: (242, 212, 190, 255),  # Arrogant Stern King Face
    8: (212, 220, 234, 255),  # Gleaming Royal Broadsword Edge
    9: (255, 58, 48, 255),    # Menacing Blazing Crimson-Red Tyrant Eyes & Core!
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


def draw_tyrant_sword(grid, hx, hy, z_hilt, z_tip):
    """Draw King Zhou's heavy Imperial Black-and-Gold Royal Broadsword (殷王大剣)."""
    fill_box(grid, hx, hx, hy, hy, z_hilt - 3, z_hilt, 3)
    fill_box(grid, hx - 2, hx + 2, hy, hy, z_hilt + 1, z_hilt + 2, 3)
    fill_box(grid, hx - 1, hx + 1, hy, hy, z_hilt + 3, z_tip - 2, 1)
    fill_box(grid, hx - 1, hx - 1, hy, hy, z_hilt + 3, z_tip - 3, 8)
    fill_box(grid, hx + 1, hx + 1, hy, hy, z_hilt + 3, z_tip - 3, 8)
    fill_box(grid, hx, hx, hy, hy, z_hilt + 3, z_tip, 3)  # Golden dragon fuller!


# ============================================================
# FORM A: KING ZHOU / ZHOUWANG (BLACK & GOLD TYRANT EMPEROR) (40 x 26 x 46)
# ============================================================
def build_a():
    grid = np.zeros((40, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 19
    cx_r = X // 2      # 20

    # Towering Imposing Black-and-Gold Royal Yin Robes (黒と金の王衣!) (Z: 0..30)
    fill_sym_box(grid, 2, 4, 11, 16, 0, 1, 3)     # Gold royal boots
    fill_sym_box(grid, 0, 5, 11, 16, 1, 15, 1)    # Grand flared pitch-black royal lower robe!
    fill_sym_box(grid, 0, 5, 11, 16, 1, 3, 3)     # Broad dazzling imperial gold hem!
    fill_sym_box(grid, 0, 2, 16, 17, 3, 16, 3)    # Gold dragon front apron!
    fill_sym_box(grid, 0, 1, 17, 17, 5, 15, 5)    # Blood-crimson vertical trim
    # Broad Imposing Upper Royal Coat & High Tyrannical Collar (Z: 16..31)
    fill_sym_box(grid, 0, 5, 11, 16, 16, 30, 1)   # Obsidian black imperial coat
    fill_sym_box(grid, 0, 5, 11, 17, 16, 18, 3)   # Broad golden king's belt!
    fill_sym_box(grid, 1, 4, 16, 17, 20, 29, 3)   # Golden imperial dragon chest embroidery!
    fill_sym_box(grid, 0, 2, 17, 17, 22, 27, 1)   # Black dragon core
    fill_sym_box(grid, 0, 1, 17, 17, 24, 25, 9)   # Crimson ruby clasp
    fill_sym_box(grid, 2, 5, 11, 13, 30, 33, 3)   # Towering royal high-collar framing head!
    # Wide Sweeping Black-and-Crimson Royal Mantle on Back
    fill_sym_box(grid, 0, 6, 9, 10, 5, 30, 1)
    fill_sym_box(grid, 0, 4, 10, 10, 7, 29, 5)    # Blood-crimson lining!
    fill_sym_box(grid, 0, 6, 9, 9, 5, 6, 3)

    # Grand Wide Sleeves & Royal Broadsword! (Z: 15..42)
    fill_box(grid, cx_l - 8, cx_l - 5, 12, 15, 16, 29, 1)
    fill_box(grid, cx_l - 8, cx_l - 5, 12, 15, 16, 17, 3)
    fill_box(grid, cx_l - 7, cx_l - 5, 15, 17, 18, 20, 7)
    fill_box(grid, cx_r + 5, cx_r + 8, 12, 15, 17, 29, 1)
    fill_box(grid, cx_r + 6, cx_r + 9, 15, 18, 18, 20, 7)
    draw_tyrant_sword(grid, cx_r + 9, 17, z_hilt=19, z_tip=41)

    # Arrogant Tyrant King Head & ICONIC BEADED IMPERIAL CROWN (冕冠!) (Z: 30..44)
    fill_sym_box(grid, 0, 2, 11, 16, 30, 37, 7)   # Stern arrogant king face
    fill_sym_box(grid, 0, 2, 16, 17, 29, 31, 1)   # Heavy dark royal beard
    fill_sym_box(grid, 1, 2, 16, 16, 34, 35, 9)   # Menacing blazing red eyes!
    fill_sym_box(grid, 0, 3, 10, 16, 37, 40, 1)   # Black crown cap
    fill_sym_box(grid, 0, 2, 16, 17, 38, 39, 3)   # Gold forehead band
    # ICONIC FLAT-TOP EMPEROR MORTARBOARD CROWN (冕冠) WITH HANGING PEARL BEADS!
    fill_sym_box(grid, 0, 5, 9, 19, 41, 42, 1)    # Wide flat imperial mortarboard!
    fill_sym_box(grid, 0, 5, 9, 19, 42, 42, 3)    # Dazzling golden crown rim!
    for bx_p in (cx_l - 3, cx_l - 1, cx_r + 1, cx_r + 3):
        fill_box(grid, bx_p, bx_p, 19, 19, 37, 40, 6)  # Hanging pearl bead strings in front!
        fill_box(grid, bx_p, bx_p, 9, 9, 38, 40, 6)    # Hanging beads in rear!

    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: KING ZHOU IMPERIAL TYRANT EMPEROR BOSS ROBOT (52 x 28 x 52)
# ============================================================
def build_b():
    grid = np.zeros((52, 28, 52), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 25
    cx_r = X // 2      # 26

    # Imposing Black-and-Gold Emperor Boots & Towering Greaves (威圧感のある姿!) (Z: 0..17)
    fill_sym_box(grid, 3, 6, 11, 18, 0, 2, 1)
    fill_sym_box(grid, 3, 6, 18, 20, 0, 2, 3)     # Heavy golden toe-claws
    fill_sym_box(grid, 3, 6, 12, 17, 3, 15, 1)    # Towering obsidian greaves
    fill_sym_box(grid, 4, 5, 17, 18, 4, 14, 3)    # Dazzling imperial-gold shin plates
    fill_sym_box(grid, 3, 6, 17, 19, 13, 16, 3)   # Golden Taotie knee armor!
    fill_sym_box(grid, 4, 5, 19, 19, 14, 15, 9)   # Glowing crimson knee gems

    # Heavy Royal Skirt Armor & Throne-Mantle Tassets (Z: 15..24)
    fill_sym_box(grid, 3, 5, 12, 16, 16, 20, 2)
    fill_sym_box(grid, 0, 6, 12, 16, 20, 23, 1)
    fill_sym_box(grid, 2, 7, 17, 18, 15, 22, 1)   # Tall black imperial tassets
    fill_sym_box(grid, 2, 7, 18, 18, 15, 16, 3)   # Broad golden hem!
    fill_sym_box(grid, 0, 2, 17, 19, 17, 23, 3)   # Gold waist apron
    fill_sym_box(grid, 0, 1, 19, 19, 19, 22, 5)   # Blood-crimson core

    # Towering Tyrant Emperor Chest Cuirass, High Royal Collar & Imperial Cape! (Z: 23..40)
    fill_sym_box(grid, 0, 5, 12, 16, 23, 25, 2)
    fill_sym_box(grid, 0, 6, 12, 17, 26, 35, 1)   # Massive obsidian emperor chest!
    fill_sym_box(grid, 1, 5, 17, 18, 27, 34, 3)   # Dazzling golden Taotie-mask breastplate!
    fill_sym_box(grid, 0, 3, 18, 19, 28, 33, 1)   # Black dragon relief
    fill_sym_box(grid, 0, 1, 19, 19, 30, 31, 9)   # Menacing blazing crimson reactor!
    # Towering Tyrannical High-Collar Arch rising behind head!
    fill_sym_box(grid, 2, 6, 11, 13, 35, 40, 1)
    fill_sym_box(grid, 3, 6, 13, 14, 35, 40, 3)   # Golden inner collar trim!
    # Grand Rear Obsidian & Blood-Crimson Cape-Wings!
    fill_sym_box(grid, 0, 4, 10, 12, 26, 35, 2)
    fill_sym_box(grid, 0, 6, 9, 10, 11, 34, 1)
    fill_sym_box(grid, 0, 4, 10, 10, 13, 32, 5)
    fill_sym_box(grid, 0, 6, 9, 9, 11, 12, 3)

    # Colossal Imperial-Gold Pauldrons & Giant Royal Broadsword! (Z: 15..49)
    fill_sym_box(grid, 6, 8, 12, 16, 30, 34, 2)
    fill_sym_box(grid, 7, 12, 12, 17, 29, 36, 1)  # Massive obsidian throne pauldrons!
    fill_sym_box(grid, 8, 13, 12, 16, 35, 37, 3)  # Dazzling golden royal crests!
    fill_sym_box(grid, 12, 13, 13, 15, 31, 34, 5) # Crimson accents
    fill_sym_box(grid, 7, 9, 12, 16, 22, 29, 2)
    fill_box(grid, cx_l - 11, cx_l - 7, 12, 16, 15, 22, 1)
    fill_box(grid, cx_l - 11, cx_l - 7, 13, 16, 15, 16, 3)
    fill_box(grid, cx_l - 10, cx_l - 7, 13, 15, 13, 14, 2)
    fill_box(grid, cx_r + 7, cx_r + 11, 12, 16, 16, 22, 1)
    fill_box(grid, cx_r + 9, cx_r + 13, 15, 18, 16, 20, 3)
    draw_tyrant_sword(grid, cx_r + 13, 18, z_hilt=18, z_tip=48)

    # Tyrant Emperor Robot Head & ARMORED BEADED MORTARBOARD CROWN (冕冠!) (Z: 35..50)
    fill_sym_box(grid, 0, 2, 12, 16, 35, 36, 2)
    fill_sym_box(grid, 0, 3, 12, 17, 36, 43, 1)   # Obsidian tyrant helm
    fill_sym_box(grid, 0, 2, 17, 18, 36, 38, 3)   # Golden face-mask jaw!
    fill_sym_box(grid, 1, 2, 18, 18, 39, 40, 9)   # Menacing blazing crimson visor eyes!
    # Giant Armored Imperial Mortarboard Crown (冕冠) with Pearl-Sensor Tassels!
    fill_sym_box(grid, 0, 6, 11, 20, 44, 45, 1)   # Imposing flat royal mortarboard!
    fill_sym_box(grid, 0, 6, 11, 20, 46, 46, 3)   # Dazzling golden top plate!
    fill_sym_box(grid, 0, 2, 14, 18, 47, 48, 3)   # Top crown spire!
    for bx_p in (cx_l - 4, cx_l - 2, cx_r + 2, cx_r + 4):
        fill_box(grid, bx_p, bx_p, 20, 20, 40, 43, 6)  # Front hanging golden/pearl curtain!
        fill_box(grid, bx_p, bx_p, 11, 11, 41, 43, 6)

    hollow_interior_26(grid, 1, Z - 2)
    return grid


def draw_6conn_line_c(grid, p0, p1, col, pad=(0, 0, 0)):
    X, Y, Z = grid.shape
    x0, y0, z0 = int(round(p0[0])), int(round(p0[1])), int(round(p0[2]))
    x1, y1, z1 = int(round(p1[0])), int(round(p1[1])), int(round(p1[2]))
    steps = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1) * 2
    prev = None
    px, py, pz = pad

    def stamp(cx_, cy_, cz_):
        xa, xb = max(0, cx_ - px), min(X - 1, cx_ + px)
        ya, yb = max(0, cy_ - py), min(Y - 1, cy_ + py)
        za, zb = max(0, cz_ - pz), min(Z - 1, cz_ + pz)
        grid[xa:xb + 1, ya:yb + 1, za:zb + 1] = col

    for i in range(steps + 1):
        t = i / steps
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        z = int(round(z0 + (z1 - z0) * t))
        if prev is not None:
            ox, oy, oz = prev
            if x != ox:
                stamp(x, oy, oz)
                ox = x
            if y != oy:
                stamp(ox, y, oz)
                oy = y
            if z != oz:
                stamp(ox, oy, z)
        else:
            stamp(x, y, z)
        prev = (x, y, z)


# ============================================================
# FORM C: MYTHICAL BLACK SWALLOW / XUANNIAO (玄鳥 — ツバメ、黒い鳥!) (48 x 38 x 32)
# ============================================================
def build_c():
    grid = np.zeros((48, 38, 32), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23
    cx_r = X // 2      # 24

    # Royal Shang-Bronze Perch & Golden Bird Claws grounded at Z=0..7
    fill_sym_box(grid, 0, 5, 16, 22, 0, 2, 4)     # Ancient bronze Yin pedestal!
    fill_sym_box(grid, 0, 5, 16, 22, 2, 2, 3)     # Gold rim
    fill_sym_box(grid, 2, 3, 18, 22, 3, 7, 3)     # Golden swallow legs & talons!

    # Sleek Aerodynamic Obsidian-Black Swallow Body (玄鳥 — 黒い鳥!) (Z: 7..20)
    fill_sym_box(grid, 0, 4, 15, 27, 8, 17, 1)    # Glossy obsidian swallow body!
    fill_sym_box(grid, 0, 3, 21, 28, 9, 15, 6)    # Sleek pearl-white swallow breast!
    fill_sym_box(grid, 0, 3, 25, 29, 14, 18, 5)   # Iconic blood-crimson swallow throat!
    fill_sym_box(grid, 0, 2, 27, 29, 12, 14, 3)   # Imperial gold chest band!

    # ICONIC DEEPLY FORKED TWIN SWALLOW TAIL STREAMERS! (ツバメの二股尾!) (Y: 2..15, Z: 5..14)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        draw_6conn_line_c(grid, (bx + sign * 1, 15, 11), (bx + sign * 5, 8, 8), 1, pad=(0, 0, 1))
        draw_6conn_line_c(grid, (bx + sign * 5, 8, 8), (bx + sign * 8, 2, 5), 1, pad=(0, 0, 0))
        fill_box(grid, bx + sign * 8, bx + sign * 8, 2, 3, 5, 6, 3)  # Gold forked tail-tips!

    # WIDE SWEPT POINTED BLACK-AND-GOLD SWALLOW WINGS! (X: 2..45, Z: 13..30)
    for sign in (-1, 1):
        bx = cx_r if sign == 1 else cx_l
        # Sharp aerodynamic swept leading wing-edge!
        draw_6conn_line_c(grid, (bx + sign * 3, 21, 16), (bx + sign * 13, 19, 25), 1, pad=(0, 1, 1))
        draw_6conn_line_c(grid, (bx + sign * 13, 19, 25), (bx + sign * 22, 16, 29), 3, pad=(0, 0, 1))
        # Swept back-angled primary swallow wing feathers!
        for tip_x, tip_y, tip_z in [(21, 13, 24), (17, 11, 20), (13, 11, 16), (9, 12, 13)]:
            draw_6conn_line_c(grid, (bx + sign * 4, 19, 15), (bx + sign * tip_x, tip_y, tip_z), 1, pad=(0, 0, 1))
            fill_box(grid, bx + sign * tip_x, bx + sign * tip_x, tip_y, tip_y, tip_z, tip_z, 3 if tip_x > 16 else 2)

    # Regal Black Swallow Head, Sharp Golden Beak, Blazing Crimson Eyes & Crown Crest! (Z: 17..29)
    fill_sym_box(grid, 0, 3, 24, 30, 17, 23, 1)   # Sleek black swallow head
    fill_sym_box(grid, 0, 1, 30, 35, 19, 21, 3)   # Sharp pointed golden swallow beak!
    fill_sym_box(grid, 2, 3, 29, 30, 21, 22, 9)   # Blazing crimson tyrant bird eyes!
    # Imperial Gold Crown Crest (homage to Zhouwang's crown!)
    fill_sym_box(grid, 0, 2, 24, 30, 23, 25, 3)
    draw_6conn_line_c(grid, (cx_r, 25, 25), (cx_r, 20, 29), 3, pad=(1, 0, 0))
    fill_sym_box(grid, 0, 1, 20, 21, 28, 29, 5)   # Crimson crown plume tip!

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


def render_voxel_iso(grid, yaw_deg=35, pitch_deg=25, scale=None, img_size=(386, 266), margin=12):
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
                    (img_size[1] - 2 * margin) / max(1e-5, max_sy - min_sy), 9.5)
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


def render_preview(models, title_banner, out_path):
    n = len(models)
    cw = 24 + n * 398 + (n - 1) * 16 + 24
    canvas = Image.new("RGBA", (cw, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, cw, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (cw, gy)], fill=(28, 34, 48, 255), width=1)
    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(models):
        bx, by, w, h = 24 + idx * 414, 48, 398, 468
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
        for pi in range(1, len(PALETTE) + 1):
            px0, py0 = bx + 14 + (pi - 1) * 20, by + 430
            draw.rectangle([px0, py0, px0 + 15, py0 + 15], fill=PALETTE[pi], outline=(70, 82, 105, 255))
    canvas.save(out_path)


if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    model_c = build_c()
    v_a = export_vox(model_a, "zhouwang_a.vox")
    v_b = export_vox(model_b, "zhouwang_b.vox")
    v_c = export_vox(model_c, "zhouwang_c.vox")
    comp_a, minz_a = count_components_6(model_a)
    comp_b, minz_b = count_components_6(model_b)
    comp_c, minz_c = count_components_6(model_c)
    render_preview(
        [
            ("1. KING ZHOU (EMPEROR)", model_a, v_a, 28, 18),
            ("2. KING ZHOU ROBOT", model_b, v_b, 28, 18),
            ("3. BLACK SWALLOW (XUANNIAO)", model_c, v_c, 36, 22),
        ],
        "CLASSICS ROBO #20: KING ZHOU / ZHOUWANG (FENGSHEN) - 3-FORM TRANSFORMATION",
        "preview_zhouwang.png",
    )
    print(f"zhouwang: A={v_a} {model_a.shape} (c={comp_a},z={minz_a}), "
          f"B={v_b} {model_b.shape} (c={comp_b},z={minz_b}), "
          f"C={v_c} {model_c.shape} (c={comp_c},z={minz_c})")
