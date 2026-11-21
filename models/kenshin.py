import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across Uesugi Kenshin Robot (Form A) and Dragon of Echigo (Form B)
PALETTE = {
    1: (246, 250, 255, 255),  # Snow-White Monk Headwrap / Surcoat / Dragon Mane
    2: (204, 228, 248, 255),  # Pale Frost-Ice / Surcoat Shading / Primary Dragon Scales
    3: (132, 206, 246, 255),  # Pale Ice-Blue Scales & Haori Trim
    4: (68, 136, 200, 255),   # Glacial Blue Scale Contours & Armor Accents
    5: (34, 54, 104, 255),    # Deep Navy-Indigo Samurai Armor & Dragon Dorsal/Belly Plates
    6: (22, 32, 58, 255),     # Midnight Slate Joints / Boots / Katana Hilt
    7: (126, 252, 255, 255),  # Luminous Pale-Cyan Spirit Glow / Eyes / Blade Edge
    8: (168, 184, 204, 255),  # Gleaming Ice-Silver Katana / Antlers / Whiskers / Claws
    9: (234, 200, 96, 255),   # Noble Pale Gold Bishamonten Crest / Tsuba / Clasps
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


def hollow_interior_26(grid, z_min, z_max):
    """Hollow strictly interior voxels (all 26 neighbors occupied) to preserve 6-connectivity."""
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


def fill_sphere_local(grid, cx, cy, cz, rx, ry, rz, col):
    """Fill an ellipsoid centered at (cx, cy, cz)."""
    X, Y, Z = grid.shape
    x0 = max(0, int(np.floor(cx - rx)))
    x1 = min(X - 1, int(np.ceil(cx + rx)))
    y0 = max(0, int(np.floor(cy - ry)))
    y1 = min(Y - 1, int(np.ceil(cy + ry)))
    z0 = max(0, int(np.floor(cz - rz)))
    z1 = min(Z - 1, int(np.ceil(cz + rz)))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                d2 = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                if d2 <= 1.0:
                    grid[x, y, z] = col


def fill_line_6conn(grid, p0, p1, col):
    """Draw a guaranteed 6-connected single-voxel polyline from p0 to p1."""
    X, Y, Z = grid.shape
    x0, y0, z0 = int(round(p0[0])), int(round(p0[1])), int(round(p0[2]))
    x1, y1, z1 = int(round(p1[0])), int(round(p1[1])), int(round(p1[2]))
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    steps = max(abs(dx), abs(dy), abs(dz), 1) * 3
    cx_i, cy_i, cz_i = x0, y0, z0
    if 0 <= cx_i < X and 0 <= cy_i < Y and 0 <= cz_i < Z:
        grid[cx_i, cy_i, cz_i] = col
    for s in range(1, steps + 1):
        t = s / steps
        tx = int(round(x0 + dx * t))
        ty = int(round(y0 + dy * t))
        tz = int(round(z0 + dz * t))
        while cx_i != tx or cy_i != ty or cz_i != tz:
            # Step one axis at a time to guarantee strict 6-connectivity
            if abs(tx - cx_i) >= abs(ty - cy_i) and abs(tx - cx_i) >= abs(tz - cz_i) and cx_i != tx:
                cx_i += 1 if tx > cx_i else -1
            elif abs(ty - cy_i) >= abs(tz - cz_i) and cy_i != ty:
                cy_i += 1 if ty > cy_i else -1
            elif cz_i != tz:
                cz_i += 1 if tz > cz_i else -1
            if 0 <= cx_i < X and 0 <= cy_i < Y and 0 <= cz_i < Z:
                grid[cx_i, cy_i, cz_i] = col


def fill_capsule(grid, p0, p1, r, col, steps=None):
    """Fill a 6-connected capsule along segment p0 -> p1."""
    p0 = np.array(p0, dtype=float)
    p1 = np.array(p1, dtype=float)
    dist = float(np.linalg.norm(p1 - p0))
    if steps is None:
        steps = max(2, int(np.ceil(dist * 2.5)))
    fill_line_6conn(grid, p0, p1, col)
    if r >= 0.8:
        for i in range(steps + 1):
            t = i / steps
            p = p0 * (1.0 - t) + p1 * t
            fill_sphere_local(grid, p[0], p[1], p[2], r, r, r, col)


def count_6_components(grid):
    """Count 6-connected components of occupied voxels."""
    xs, ys, zs = np.nonzero(grid)
    if len(xs) == 0:
        return 0
    X, Y, Z = grid.shape
    visited = np.zeros(grid.shape, dtype=bool)
    comps = 0
    for sx, sy, sz in zip(xs, ys, zs):
        if visited[sx, sy, sz]:
            continue
        comps += 1
        q = deque([(int(sx), int(sy), int(sz))])
        visited[sx, sy, sz] = True
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < X and 0 <= ny < Y and 0 <= nz < Z and grid[nx, ny, nz] > 0 and not visited[nx, ny, nz]:
                    visited[nx, ny, nz] = True
                    q.append((nx, ny, nz))
    return comps


# ==========================================
# FORM A: UESUGI KENSHIN ROBOT (48 x 28 x 44)
# Noble "God of War" Samurai Robot in Snow-White Monk Headwrap & Surcoat over Deep Navy Armor
# ==========================================
def build_a():
    grid = np.zeros((48, 28, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 23 (-X robot left)
    cx_r = X // 2      # 24 (+X robot right)

    # --- GROUNDED SAMURAI WAR BOOTS / TABI-ARMORED FEET (Z: 0..3) ---
    fill_sym_box(grid, 2, 5, 9, 17, 0, 1, 6)     # Midnight slate grounded soles
    fill_sym_box(grid, 2, 5, 10, 17, 1, 2, 5)    # Deep navy armored boot shell
    fill_sym_box(grid, 3, 4, 16, 18, 0, 1, 8)    # Gleaming silver armored toe guard
    fill_sym_box(grid, 3, 4, 16, 17, 2, 2, 3)    # Ice-blue instep trim
    fill_sym_box(grid, 2, 5, 8, 9, 0, 2, 6)      # Rear heel spur
    fill_sym_box(grid, 2, 5, 10, 15, 3, 3, 1)    # Snow-white monk gaiter wrap at ankle

    # --- LOWER LEGS / SUNEATE SHIN ARMOR (Z: 4..14) ---
    fill_sym_box(grid, 2, 5, 10, 15, 4, 13, 5)   # Deep navy-indigo suneate shin armor
    fill_sym_box(grid, 2, 3, 10, 11, 4, 13, 2)   # Pale frost-white inner calf cloth fold
    fill_sym_box(grid, 3, 4, 15, 15, 5, 11, 4)   # Glacial blue central shin ridge
    fill_sym_box(grid, 3, 3, 15, 15, 6, 10, 3)   # Pale ice-blue front shin highlight
    fill_sym_box(grid, 5, 5, 11, 14, 5, 12, 8)   # Silver outer calf plate edge
    for lz in (6, 9):
        fill_sym_box(grid, 2, 5, 10, 15, lz, lz, 6)
        fill_sym_box(grid, 3, 4, 15, 15, lz, lz, 3)
    # Sculpted Samurai Knee Guards (Tateage)
    fill_sym_box(grid, 2, 5, 14, 16, 11, 14, 5)
    fill_sym_box(grid, 3, 4, 16, 16, 12, 14, 3)
    fill_sym_box(grid, 3, 4, 16, 16, 13, 13, 9)  # Pale gold knee crest

    # --- THIGHS & HAKAMA TROUSERS (Z: 14..19) ---
    fill_sym_box(grid, 2, 5, 10, 14, 14, 19, 6)  # Inner dark frame
    fill_sym_box(grid, 2, 5, 10, 14, 15, 18, 1)  # Snow-white hakama cloth
    fill_sym_box(grid, 4, 5, 11, 14, 15, 18, 2)  # Pale frost hakama pleat shading
    fill_sym_box(grid, 3, 4, 14, 15, 15, 17, 5)  # Deep navy haidate thigh plate

    # --- WAIST, KUSAZURI TASSETS & FLOWING WHITE SURCOAT SKIRT (Z: 15..22) ---
    # Tapered Samurai Waist & Deep Navy Obi Sash
    fill_sym_box(grid, 0, 4, 10, 15, 19, 22, 5)
    fill_sym_box(grid, 0, 4, 14, 16, 20, 21, 4)  # Glacial blue obi wrap
    fill_sym_box(grid, 0, 1, 15, 16, 20, 22, 9)  # Pale gold waist clasp
    fill_sym_box(grid, 0, 0, 16, 16, 21, 21, 7)  # Glowing pale-cyan waist gem

    # Front draped snow-white surcoat panels (白装束前垂れ) flaring gracefully over thighs
    fill_sym_box(grid, 1, 4, 15, 16, 16, 19, 1)  # White draped front panels
    fill_sym_box(grid, 1, 4, 16, 16, 16, 16, 3)  # Pale ice-blue hem glow trim
    fill_sym_box(grid, 2, 3, 16, 16, 17, 18, 2)  # Subtle cloth pleat
    fill_sym_box(grid, 0, 0, 15, 16, 17, 19, 5)  # Center split showing deep navy armor
    # Side flared kusazuri armor plates (navy + white drape + ice-blue trim)
    fill_sym_box(grid, 5, 6, 10, 15, 15, 20, 5)
    fill_sym_box(grid, 6, 6, 11, 14, 16, 20, 1)
    fill_sym_box(grid, 6, 6, 11, 14, 15, 15, 3)
    fill_sym_box(grid, 6, 6, 12, 13, 19, 19, 9)
    # Rear flowing white surcoat tail (draping cleanly down behind legs)
    fill_sym_box(grid, 0, 5, 8, 9, 14, 21, 1)
    fill_sym_box(grid, 1, 4, 8, 8, 13, 14, 2)
    fill_sym_box(grid, 0, 5, 8, 8, 14, 14, 3)    # Ice-blue hem trim on rear surcoat
    fill_sym_box(grid, 0, 1, 8, 9, 15, 21, 5)    # Central navy dorsal ridge stripe

    # --- NOBLE SAMURAI TORSO: DEEP NAVY DOU UNDER DRAPED WHITE SURCOAT (Z: 22..32) ---
    fill_sym_box(grid, 0, 5, 9, 15, 22, 31, 5)   # Deep navy-indigo cuirass (紺鎧)
    fill_sym_box(grid, 0, 4, 15, 16, 23, 30, 5)  # Broad armored chest front
    fill_sym_box(grid, 0, 3, 15, 16, 22, 24, 6)  # Tapered abdomen armor
    fill_sym_box(grid, 1, 2, 16, 16, 23, 24, 4)

    # Iconic Draped Snow-White Monk Surcoat (白装束・陣羽織) framing the navy cuirass!
    fill_sym_box(grid, 3, 5, 14, 17, 24, 31, 1)  # Snow-white draped chest surcoat sides
    fill_sym_box(grid, 4, 5, 16, 17, 25, 30, 2)  # Frost-white fold contour
    fill_sym_box(grid, 3, 3, 16, 17, 24, 30, 3)  # Pale ice-blue inner lapel trim
    # V-shaped white kimono/surcoat collar sweeping across upper chest
    fill_sym_box(grid, 2, 3, 15, 17, 29, 31, 1)
    fill_sym_box(grid, 1, 2, 15, 17, 27, 29, 1)
    fill_sym_box(grid, 1, 1, 16, 17, 26, 27, 3)  # Ice-blue collar edge
    # Center exposed deep-navy breastplate with glowing pale-cyan Bishamonten core & gold crest
    fill_sym_box(grid, 0, 2, 16, 17, 25, 28, 5)
    fill_sym_box(grid, 0, 1, 17, 17, 26, 28, 9)  # Pale gold Bishamonten emblem frame
    fill_sym_box(grid, 0, 0, 17, 18, 27, 28, 7)  # Glowing pale-cyan dragon spirit core
    fill_sym_box(grid, 0, 2, 10, 14, 31, 32, 1)  # White monk collar rim around neck

    # --- REAR DRAPED WHITE HAORI CAPE & DRAGON DORSAL SPINE PACK (Y: 5..9, Z: 20..33) ---
    fill_sym_box(grid, 0, 5, 7, 9, 21, 31, 1)    # Broad flowing white back surcoat
    fill_sym_box(grid, 2, 4, 6, 7, 22, 30, 2)    # Draped cape contour
    fill_sym_box(grid, 4, 5, 7, 8, 21, 29, 3)    # Pale ice-blue outer cape border
    # Deep navy dorsal spine ridge (becomes Dragon's dorsal ridge!)
    fill_sym_box(grid, 0, 1, 6, 8, 21, 32, 5)
    for sz in (22, 25, 28, 31):
        fill_sym_box(grid, 0, 0, 5, 6, sz, sz + 1, 5)
        fill_sym_box(grid, 0, 0, 5, 5, sz + 1, sz + 1, 7)
    # Twin dragon-scale rear stabilizer fins on upper back
    fill_sym_box(grid, 2, 3, 5, 6, 28, 31, 4)
    fill_sym_box(grid, 3, 4, 5, 6, 30, 32, 3)

    # --- FLOWING WHITE-AND-NAVY SHOULDER / HAORI PLATES (Z: 25..34) ---
    fill_sym_box(grid, 5, 8, 10, 14, 28, 31, 6)  # Shoulder joint core
    # Sweeping multi-tier samurai O-Sode + draped white haori mantle!
    fill_sym_box(grid, 5, 10, 9, 16, 31, 32, 1)
    fill_sym_box(grid, 6, 9, 10, 15, 33, 33, 1)
    fill_sym_box(grid, 7, 8, 11, 14, 34, 34, 2)
    fill_sym_box(grid, 6, 10, 16, 16, 31, 32, 3) # Glowing pale ice-blue front lip
    fill_sym_box(grid, 5, 6, 10, 15, 32, 33, 9)  # Pale gold shoulder clasp
    # Mid & lower tiered flowing haori / o-sode plates flaring gracefully outward
    fill_sym_box(grid, 8, 11, 9, 16, 28, 30, 1)  # White draped outer shoulder wing
    fill_sym_box(grid, 11, 11, 10, 15, 28, 30, 3)# Pale ice-blue edge
    fill_sym_box(grid, 9, 12, 9, 15, 26, 27, 5)  # Deep navy lower samurai armor tier
    fill_sym_box(grid, 11, 12, 10, 14, 26, 26, 3)# Ice-blue trim along navy plate
    fill_sym_box(grid, 10, 12, 10, 14, 25, 25, 2)# Frost-white lower tassel edge

    # --- ARMS (Z: 15..28) ---
    fill_sym_box(grid, 7, 9, 10, 14, 23, 28, 5)  # Upper arms
    fill_sym_box(grid, 7, 9, 11, 13, 25, 26, 1)  # White inner sleeve wrap
    # Left forearm (Kote armored sleeve)
    fill_box(grid, cx_l - 10, cx_l - 7, 10, 15, 17, 22, 5)
    fill_box(grid, cx_l - 10, cx_l - 8, 14, 15, 18, 21, 1)
    fill_box(grid, cx_l - 10, cx_l - 10, 11, 14, 18, 21, 3)
    fill_box(grid, cx_l - 10, cx_l - 7, 11, 14, 17, 17, 8)
    fill_box(grid, cx_l - 10, cx_l - 7, 11, 15, 15, 17, 6)  # Left fist

    # --- LEFT ARM (-X, cx_l): NOBLE DRAGON-CREST KATANA SCABBARD (鞘) & SAGEO CORD ---
    scabbard_pts = [
        (cx_l - 9, 16, 15),
        (cx_l - 9, 15, 16),
        (cx_l - 9, 14, 16),
        (cx_l - 9, 13, 17),
        (cx_l - 9, 12, 17),
        (cx_l - 9, 11, 18),
        (cx_l - 9, 10, 18),
        (cx_l - 9, 9, 19),
        (cx_l - 9, 8, 19),
        (cx_l - 9, 7, 20),
        (cx_l - 9, 6, 20),
        (cx_l - 9, 5, 21),
    ]
    for idx, (sx, sy, sz) in enumerate(scabbard_pts):
        col = 9 if idx in (1, 11) else (3 if idx % 3 == 0 else 5)
        fill_box(grid, sx - 1, sx, sy, sy + 1, sz, sz + 1, col)
    fill_box(grid, cx_l - 11, cx_l - 10, 13, 14, 13, 16, 1)
    fill_box(grid, cx_l - 11, cx_l - 11, 13, 14, 11, 13, 3)

    # --- RIGHT ARM (+X, cx_r): POISED OUTWARD HOLDING GLEAMING SILVER & ICE-BLUE KATANA ---
    # Right forearm angled clearly OUTWARD (+X) & slightly forward (+Y) so the katana silhouette
    # stands out dramatically against the dark background with zero overlap over the white shoulder!
    fill_box(grid, cx_r + 8, cx_r + 11, 11, 15, 19, 23, 5)   # Elbow & upper kote
    fill_box(grid, cx_r + 10, cx_r + 13, 13, 17, 17, 20, 5)  # Outstretched navy forearm
    fill_box(grid, cx_r + 10, cx_r + 12, 16, 17, 18, 20, 1)  # White forearm trim
    fill_box(grid, cx_r + 12, cx_r + 13, 14, 17, 17, 19, 8)  # Silver wrist cuff
    fill_box(grid, cx_r + 13, cx_r + 15, 15, 18, 16, 18, 6)  # Armored fist gripping katana

    # Katana Tsuka (sleek wrapped midnight navy hilt), compact Gold Pommel, and crisp Gold Tsuba guard
    fill_box(grid, cx_r + 13, cx_r + 14, 14, 16, 13, 15, 6)  # Sleek lower wrapped hilt
    fill_box(grid, cx_r + 13, cx_r + 14, 14, 15, 12, 12, 9)  # Compact pale gold pommel cap
    fill_box(grid, cx_r + 14, cx_r + 16, 17, 19, 18, 18, 9)  # Crisp flat pale gold Tsuba guard plate!

    # Sweeping curved Katana blade rising boldly OUTWARD (+X) & UP (+Z) against the dark backdrop!
    blade_pts = [
        (cx_r + 15, 18, 19),
        (cx_r + 17, 20, 24),
        (cx_r + 19, 21, 30),
        (cx_r + 21, 22, 36),
        (cx_r + 22, 21, 41),  # Classic subtle katana sori curvature at tip!
    ]
    for i in range(len(blade_pts) - 1):
        p0, p1 = blade_pts[i], blade_pts[i + 1]
        # Silver steel blade back spine
        fill_line_6conn(grid, p0, p1, 8)
        # Ice-blue steel flat
        fill_line_6conn(grid, (p0[0] + 1, p0[1], p0[2]), (p1[0] + 1, p1[1], p1[2]), 3 if i < 3 else 2)
        # Razor-bright gleaming frost-white & cyan-ice edge (+Y front)
        edge_col = 7 if i >= 2 else 1
        fill_line_6conn(grid, (p0[0], p0[1] + 1, p0[2]), (p1[0], p1[1] + 1, p1[2]), edge_col)
    # Sharp gleaming katana kissaki tip
    grid[cx_r + 22, 21, 42] = 7
    grid[cx_r + 22, 22, 41] = 1

    # --- HEAD: ICONIC SNOW-WHITE MONK HEADWRAP (白頭巾) & NOBLE BISHAMONTEN CREST (Z: 32..43) ---
    fill_sym_box(grid, 0, 1, 11, 13, 31, 33, 6)  # Neck
    # Classic rounded snow-white monk headwrap dome (白頭巾)
    fill_sym_box(grid, 0, 3, 9, 15, 33, 39, 1)
    fill_sym_box(grid, 0, 2, 9, 15, 39, 41, 1)   # Smoothly rounded tall monk cloth dome!
    fill_sym_box(grid, 0, 1, 10, 14, 42, 42, 2)  # Top soft cloth crown fold
    fill_sym_box(grid, 3, 3, 10, 14, 34, 38, 2)  # Subtle cloth fold shading on sides
    fill_sym_box(grid, 3, 3, 11, 13, 35, 36, 1)

    # Clear, Noble Warrior Face framed cleanly inside the Snow-White Headwrap!
    fill_sym_box(grid, 0, 1, 15, 15, 34, 37, 6)  # Deep shadow face recess (no overhang blocking eyes!)
    fill_sym_box(grid, 0, 1, 15, 15, 34, 35, 5)  # Deep navy samurai menpo jaw plate
    fill_sym_box(grid, 0, 2, 15, 15, 33, 33, 1)  # White cloth wrap beneath chin
    fill_sym_box(grid, 2, 2, 15, 15, 34, 37, 1)  # White cloth cheek folds framing face
    # Fierce, crisp glowing pale-cyan eyes cleanly visible at front face!
    fill_sym_box(grid, 1, 1, 15, 15, 36, 36, 7)
    fill_sym_box(grid, 0, 0, 15, 15, 36, 36, 6)  # Sharp dark nose bridge between eyes
    # Clean snow-white brow wrap band above eyes
    fill_sym_box(grid, 0, 2, 15, 15, 37, 38, 1)
    fill_sym_box(grid, 0, 2, 15, 15, 38, 38, 2)

    # Noble Upright Pale-Gold & Ice-Silver Bishamonten Forehead Crest (sleek V-crest + jewel!)
    fill_sym_box(grid, 0, 1, 16, 16, 38, 39, 9)  # Pale gold forehead mount
    fill_sym_box(grid, 0, 0, 16, 16, 39, 40, 7)  # Glowing pale-cyan dragon-jewel center
    fill_sym_box(grid, 0, 0, 16, 16, 41, 43, 9)  # Slender central gold finial spire
    fill_sym_box(grid, 1, 2, 16, 16, 39, 40, 8)  # Sleek sweeping ice-silver dragon-brow wings
    fill_sym_box(grid, 2, 3, 15, 16, 40, 41, 8)  # Swept-back silver tips (foreshadowing dragon antlers!)

    # Draped snow-white headwrap cloth streamers cascading smoothly down back of neck & shoulders
    fill_sym_box(grid, 0, 3, 8, 9, 32, 38, 1)
    fill_sym_box(grid, 1, 3, 7, 8, 30, 35, 1)
    fill_sym_box(grid, 2, 3, 7, 7, 28, 31, 2)
    fill_sym_box(grid, 2, 2, 7, 7, 27, 28, 3)

    # Hollow strictly interior bulk to keep cleanly in target voxel budget
    hollow_interior_26(grid, 1, 41)

    return grid


# ==========================================
# FORM B: DRAGON OF ECHIGO (40 x 48 x 40)
# Majestic Sinuous Pale Ice-Blue Eastern Serpentine Dragon (越後の龍・青白い龍)
# ==========================================
def build_b():
    grid = np.zeros((40, 48, 40), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 19.5

    # --- 1. SINUOUS 3D S-CURVED SERPENTINE BODY SPINE ---
    # Dynamic coiled & rearing Eastern dragon S-curve with crisp open negative space!
    # Control points: (x_offset_from_cx, y, z, radius_xy, radius_z)
    ctrl_pts = [
        # High curling tail tip whipping gracefully at the rear-left
        (-7.5,  3.5, 25.5, 0.95, 0.95),
        (-9.0,  6.0, 20.5, 1.25, 1.25),
        (-6.5,  8.5, 14.0, 1.65, 1.60),
        (-1.5, 10.5,  8.0, 2.05, 1.95),
        # Grounded Rear Coil (sweeps toward +X, resting solidly near z=3.8)
        ( 5.5, 13.5,  4.0, 2.45, 2.20),
        ( 9.5, 18.0,  3.8, 2.60, 2.30),
        ( 7.5, 22.5,  8.5, 2.70, 2.50),
        # Soaring Mid-Body Arch (sweeps dramatically toward -X and high z=17.5!)
        ( 0.0, 25.0, 15.5, 2.75, 2.55),
        (-7.5, 26.5, 17.8, 2.75, 2.55),
        (-9.5, 29.0, 14.0, 2.70, 2.50),
        # Grounded Front Torso Coil (curves back to center +Y, z=8..9)
        (-4.5, 32.5,  8.8, 2.80, 2.60),
        ( 2.0, 34.5,  8.5, 2.85, 2.65),
        # Majestic Rearing Chest & Graceful Arched S-Neck!
        ( 4.0, 34.8, 13.8, 2.65, 2.55),
        ( 2.2, 33.2, 20.0, 2.40, 2.35),
        ( 0.0, 33.0, 26.2, 2.25, 2.25),
        ( 0.0, 35.0, 30.8, 2.15, 2.15),  # High arched neck entering dragon head!
    ]

    def catmull_rom(pts, n_samples=180):
        arr = np.array(pts, dtype=float)
        padded = np.vstack([arr[0], arr, arr[-1]])
        out = []
        segs = len(arr) - 1
        for s in range(segs):
            p0, p1, p2, p3 = padded[s], padded[s + 1], padded[s + 2], padded[s + 3]
            n_sub = max(9, n_samples // segs)
            for j in range(n_sub):
                u = j / n_sub
                u2, u3 = u * u, u * u * u
                val = 0.5 * (
                    (2.0 * p1)
                    + (-p0 + p2) * u
                    + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * u2
                    + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * u3
                )
                out.append(val)
        out.append(arr[-1])
        return np.array(out)

    spine = catmull_rom(ctrl_pts, n_samples=185)
    n_sp = len(spine)

    # First pass: Luminous Pale Ice-Blue & Snow-White Scales (青白い龍) + Crisp Navy Dorsal & Belly Plates
    for idx, (xoff, sy, sz, rxy, rz) in enumerate(spine):
        sx = cx + xoff
        x0 = max(0, int(np.floor(sx - rxy - 0.5)))
        x1 = min(X - 1, int(np.ceil(sx + rxy + 0.5)))
        y0 = max(0, int(np.floor(sy - rxy - 0.5)))
        y1 = min(Y - 1, int(np.ceil(sy + rxy + 0.5)))
        z0 = max(0, int(np.floor(sz - rz - 0.5)))
        z1 = min(Z - 1, int(np.ceil(sz + rz + 0.5)))

        p_prev = spine[max(0, idx - 1)][:3]
        p_next = spine[min(n_sp - 1, idx + 1)][:3]
        tang = p_next - p_prev
        t_norm = np.linalg.norm(tang)
        if t_norm > 1e-6:
            tang = tang / t_norm
        dorsal = np.array([0.0, -tang[2] * 0.85, max(0.35, 1.0 - abs(tang[2]) * 0.65)])
        dorsal /= np.linalg.norm(dorsal)

        band = (idx // 3) % 2
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    dx, dy, dz = x - sx, y - sy, z - sz
                    d2 = (dx / rxy) ** 2 + (dy / rxy) ** 2 + (dz / rz) ** 2
                    if d2 <= 1.0:
                        proj_d = (dx * dorsal[0] + dy * dorsal[1] + dz * dorsal[2]) / max(1.0, rz)
                        if proj_d < -0.50:
                            # Crisp segmented deep-navy ventral belly plates (from robot armor!)
                            col = 5 if band == 0 else 4
                        elif proj_d > 0.64:
                            # Deep navy dorsal spine armor strip
                            col = 5
                        elif proj_d > 0.20:
                            # Pale ice-blue scales (青白い龍 primary hue!)
                            col = 3 if (idx + x + y) % 3 != 0 else 2
                        else:
                            # Luminous pale frost-ice & snow-white lower flank scales
                            col = 2 if band == 0 else 1
                        grid[x, y, z] = col

    # Second pass: Prominent Deep-Navy Dorsal Ridge Spines & Glowing Cyan/Gold Scale Crests (100% 6-connected!)
    for idx in range(6, n_sp - 6, 4):
        xoff, sy, sz, rxy, rz = spine[idx]
        sx = cx + xoff
        p_prev = spine[max(0, idx - 2)][:3]
        p_next = spine[min(n_sp - 1, idx + 2)][:3]
        tang = p_next - p_prev
        tang /= max(1e-6, np.linalg.norm(tang))
        dorsal = np.array([0.0, -tang[2] * 0.9, max(0.3, 1.0 - abs(tang[2]) * 0.65)])
        dorsal /= np.linalg.norm(dorsal)

        fin_h = 1.6 if idx < n_sp - 32 else 2.0
        p_base = np.array([sx, sy, sz]) + dorsal * (rz * 0.5)
        p_mid = np.array([sx, sy, sz]) + dorsal * (rz + fin_h * 0.65) - tang * 0.35
        p_tip = np.array([sx, sy, sz]) + dorsal * (rz + fin_h) - tang * 0.75
        fill_line_6conn(grid, p_base, p_mid, 5)
        # Anchor tip cleanly from p_mid using 6-connected line!
        if idx >= n_sp - 36:
            tip_col = 1
        elif idx % 16 == 6:
            tip_col = 9  # Subtle pale gold armor clasp on spine
        else:
            tip_col = 7 if (idx % 8 == 2) else 3
        fill_line_6conn(grid, p_mid, p_tip, tip_col)

    # --- 2. FLOWING SNOW-WHITE & NAVY FEATHERED NECK MANE (DISTINCT TUFTS, NOT A FLAT WALL!) ---
    # Echoes Kenshin's draped snow-white monk headwrap & flowing white surcoat!
    for idx in range(n_sp - 44, n_sp - 2, 4):
        frac = (idx - (n_sp - 44)) / 42.0
        xoff, sy, sz, rxy, rz = spine[idx]
        sx = cx + xoff
        tuft_len = 2.6 + 2.2 * np.sin(frac * np.pi)
        # Central navy-and-white crest tuft + flanking snow-white mane locks streaming back (-Y)
        m_c0 = (sx, sy - 1.0, sz)
        m_c1 = (sx, sy - 1.4 - tuft_len * 0.85, sz - 0.8)
        fill_capsule(grid, m_c0, m_c1, 0.85, 5 if (idx // 4) % 2 == 0 else 1, steps=6)
        for side in (-1.0, 1.0):
            m0 = (sx + side * 1.4, sy - 0.6, sz + 0.3)
            m1 = (sx + side * (2.3 + 0.7 * frac), sy - 1.0 - tuft_len, sz - 0.9)
            fill_capsule(grid, m0, m1, 0.82, 1, steps=6)
            m2 = (m1[0] + side * 0.4, m1[1] - 1.0, m1[2] - 0.4)
            fill_line_6conn(grid, m1, m2, 3 if (idx // 4) % 2 == 0 else 2)

    # --- 3. SWEEPING ICE-SILVER & SNOW-WHITE DRAGON TAIL PLUME (TAIL TIP) ---
    tail_origin = np.array([cx - 7.5, 3.5, 25.5])
    plume_rays = [
        (np.array([cx - 5.5, 1.5, 31.8]), 0.88, 1),  # High snow-white plume
        (np.array([cx - 9.0, 2.0, 30.8]), 0.85, 3),  # Pale ice-blue flame plume
        (np.array([cx - 6.8, 0.8, 28.8]), 0.88, 8),  # Gleaming silver central blade-plume
        (np.array([cx - 10.5, 3.5, 28.0]), 0.82, 7), # Glowing cyan spirit wisp
        (np.array([cx - 4.8, 2.2, 27.2]), 0.85, 5),  # Deep navy base anchor plume
    ]
    for p_end, rad, col in plume_rays:
        fill_capsule(grid, tail_origin, p_end, rad, col, steps=8)

    # --- 4. MAJESTIC EASTERN DRAGON HEAD (Y: 33..46, Z: 27..39, facing +Y) ---
    # Sculpted pale ice-blue cranium
    fill_sphere_local(grid, cx, 36.0, 32.8, 3.2, 3.2, 2.5, 2)
    fill_sphere_local(grid, cx, 37.0, 33.8, 2.7, 2.7, 1.7, 3)
    # Deep navy armored crown ridge & pale gold brow crest (echoes Kenshin's helmet crest!)
    fill_sym_box(grid, 0, 1, 33, 38, 34, 35, 5)
    fill_sym_box(grid, 0, 0, 35, 39, 35, 35, 9)
    fill_sym_box(grid, 0, 0, 37, 38, 35, 36, 7)

    # Long sculpted Eastern Dragon Upper Snout (Y: 38..46, Z: 31..34)
    for y in range(38, 46):
        frac = (y - 38) / 7.0
        half_w = int(round(2.5 - 0.8 * frac))
        fill_sym_box(grid, 0, half_w, y, y, 31, 33, 2 if y % 2 == 0 else 3)
        fill_sym_box(grid, 0, max(0, half_w - 1), y, y, 33, 33, 1)  # Snow-white nose bridge
    # Flared upturned Eastern dragon nose / nostrils
    fill_sym_box(grid, 0, 2, 44, 46, 31, 33, 3)
    fill_sym_box(grid, 0, 1, 45, 46, 33, 34, 1)   # Upturned snow-white snout ridge
    fill_sym_box(grid, 1, 1, 46, 46, 32, 32, 5)   # Deep navy nostrils

    # Fierce Glowing Pale-Cyan Dragon Eyes framed by Sculpted Navy Brow Ridges!
    fill_sym_box(grid, 2, 3, 36, 39, 34, 34, 5)   # Deep navy arched brow ridge
    fill_sym_box(grid, 2, 3, 36, 38, 35, 35, 1)   # White eyebrow ridge highlight
    fill_sym_box(grid, 3, 3, 37, 39, 32, 33, 7)   # Bright glowing pale-cyan dragon eyes!
    fill_sym_box(grid, 2, 3, 36, 39, 31, 31, 4)   # Cheek scales

    # Open Roaring Lower Jaw (crisp wide roar gap showing glowing cyan breath & sharp white fangs!)
    fill_sym_box(grid, 0, 2, 35, 39, 28, 29, 4)   # Rear jaw hinge
    fill_sym_box(grid, 0, 1, 36, 44, 26, 27, 5)   # Deep navy armored lower jaw angled open
    fill_sym_box(grid, 0, 1, 42, 44, 27, 27, 2)   # Lower jaw tip
    # Glowing icy spirit breath deep inside open roaring mouth
    fill_sym_box(grid, 0, 1, 36, 39, 28, 30, 7)
    # Razor-sharp Snow-White Dragon Fangs cleanly visible in the open roar!
    fill_sym_box(grid, 1, 1, 43, 44, 30, 30, 1)   # Upper front fangs hanging down
    fill_sym_box(grid, 2, 2, 40, 41, 30, 30, 1)   # Upper mid fangs
    fill_sym_box(grid, 1, 1, 42, 43, 28, 28, 1)   # Lower front fangs rising up
    # Flowing snow-white dragon goatee / beard under chin
    fill_sym_box(grid, 0, 1, 37, 40, 25, 26, 1)
    fill_sym_box(grid, 0, 0, 36, 38, 23, 25, 1)
    fill_sym_box(grid, 0, 0, 35, 36, 22, 23, 3)

    # Flowing Snow-White & Navy Cheek Mane Plumes framing the dragon's head
    for side in (-1, 1):
        fill_capsule(grid, (cx + side * 2.8, 35.0, 32.2), (cx + side * 5.2, 30.5, 31.2), 0.95, 1, steps=6)
        fill_capsule(grid, (cx + side * 2.5, 34.5, 30.8), (cx + side * 4.6, 30.0, 28.8), 0.88, 5, steps=6)
        fill_capsule(grid, (cx + side * 2.5, 35.5, 33.8), (cx + side * 4.4, 32.0, 34.8), 0.85, 3, steps=6)

    # --- MAJESTIC BRANCHING ICE-SILVER STAG ANTLERS (100% 6-CONNECTED!) ---
    for side in (-1, 1):
        a_base = (cx + side * 1.8, 35.0, 34.5)
        a_mid = (cx + side * 3.8, 31.8, 37.4)
        a_tip = (cx + side * 5.2, 27.8, 38.8)
        fill_line_6conn(grid, a_base, a_mid, 8)
        fill_line_6conn(grid, (a_base[0], a_base[1], a_base[2] + 0.5), (a_mid[0], a_mid[1], a_mid[2] + 0.5), 8)
        fill_line_6conn(grid, a_mid, a_tip, 8)
        # Forward upper antler tine
        a_tine1 = (cx + side * 4.2, 33.8, 39.0)
        fill_line_6conn(grid, a_mid, a_tine1, 1)
        # Secondary outer tine
        a_tine2 = (cx + side * 6.5, 29.8, 37.0)
        fill_line_6conn(grid, a_mid, a_tine2, 2)
        # Pale gold antler collar ring at base
        fill_sphere_local(grid, cx + side * 1.8, 35.0, 34.6, 0.9, 0.9, 0.9, 9)

    # --- LONG FLOWING ICE-SILVER & WHITE EASTERN DRAGON WHISKERS (CLASSIC S-SWEEP, 100% 6-CONNECTED!) ---
    for side in (-1, 1):
        w0 = (cx + side * 2.0, 44.0, 31.5)
        w1 = (cx + side * 5.8, 45.2, 29.8)
        w2 = (cx + side * 9.5, 43.2, 27.8)
        w3 = (cx + side * 12.2, 40.5, 29.6)
        fill_line_6conn(grid, w0, w1, 8)
        fill_line_6conn(grid, w1, w2, 1)
        fill_line_6conn(grid, w2, w3, 7)

    # --- 5. FOUR COMPACT CLAWED EASTERN DRAGON LEGS TUCKED ALONG THE S-CURVED BODY ---
    def build_dragon_leg(hip, knee, ankle, paw, side_sign, grounded=True):
        # Deep navy shoulder/thigh armor plate (carried over from robot armor!)
        fill_sphere_local(grid, hip[0], hip[1], hip[2], 2.0, 2.0, 1.9, 5)
        fill_sphere_local(grid, hip[0] + side_sign * 0.6, hip[1], hip[2] + 0.5, 1.3, 1.4, 1.3, 3)
        # Upper leg (hip -> knee)
        fill_capsule(grid, hip, knee, 1.35, 2, steps=8)
        # Trailing snow-white dragon elbow/hock plume
        tuft_end = (knee[0] + side_sign * 0.8, knee[1] - 2.6, knee[2] + 0.5)
        fill_capsule(grid, knee, tuft_end, 0.82, 1, steps=6)
        # Lower leg (knee -> ankle -> paw)
        fill_capsule(grid, knee, ankle, 1.15, 3, steps=8)
        fill_capsule(grid, ankle, paw, 1.1, 4, steps=6)
        # Paw base & 3 gleaming silver dragon claws (100% 6-connected!)
        px, py, pz = paw
        if grounded:
            pz = 1.0
        fill_sphere_local(grid, px, py, pz, 1.35, 1.5, 1.0, 5)
        for c_off in (-1.4, 0.0, 1.4):
            c_start = (px + c_off * 0.5, py + 0.4, pz)
            c_end = (px + c_off * 1.15, py + 2.6, 0.0 if grounded else max(0.5, pz - 0.5))
            fill_line_6conn(grid, c_start, c_end, 8)
            if grounded:
                fill_line_6conn(grid, (c_start[0], c_start[1], 1.0), (c_end[0], c_end[1] - 0.6, 1.0), 8)
        # Rear dewclaw
        fill_line_6conn(grid, (px, py - 0.4, pz), (px, py - 1.8, 0.0 if grounded else max(0.5, pz - 0.4)), 8)

    # FRONT RIGHT LEG (+X, viewer's left): Planted boldly on ground (z=0) supporting rearing chest!
    build_dragon_leg(
        hip=(cx + 4.5, 34.0, 10.5),
        knee=(cx + 9.2, 33.0, 7.0),
        ankle=(cx + 9.8, 36.0, 3.5),
        paw=(cx + 10.0, 38.0, 1.0),
        side_sign=1.0,
        grounded=True,
    )

    # FRONT LEFT LEG (-X, viewer's right): Raised dynamically beside chest, clutching the glowing Dragon Pearl (宝珠)!
    build_dragon_leg(
        hip=(cx - 4.0, 33.0, 10.5),
        knee=(cx - 8.8, 33.5, 9.8),
        ankle=(cx - 8.5, 37.2, 12.2),
        paw=(cx - 7.2, 39.0, 13.8),
        side_sign=-1.0,
        grounded=False,
    )
    # Glowing Ice-Cyan Dragon Pearl / Spirit Orb (越後の宝珠) held firmly inside the raised claws
    fill_sphere_local(grid, cx - 7.0, 40.8, 13.8, 1.75, 1.75, 1.75, 7)
    fill_sphere_local(grid, cx - 7.0, 41.1, 14.3, 0.9, 0.9, 0.9, 1)
    fill_capsule(grid, (cx - 7.2, 39.0, 13.8), (cx - 7.0, 40.8, 13.8), 0.95, 8, steps=4)

    # HIND RIGHT LEG (+X): Planted firmly on ground (z=0) along the rear coil!
    build_dragon_leg(
        hip=(cx + 9.0, 18.0, 5.0),
        knee=(cx + 13.4, 16.5, 4.5),
        ankle=(cx + 13.4, 19.2, 2.2),
        paw=(cx + 13.2, 21.2, 1.0),
        side_sign=1.0,
        grounded=True,
    )

    # HIND LEFT LEG (-X): Anchored to rear coil & planted firmly on ground (z=0) for rock-solid stance!
    build_dragon_leg(
        hip=(cx + 5.2, 14.5, 5.0),
        knee=(cx - 1.5, 15.5, 4.5),
        ankle=(cx - 3.8, 18.2, 2.2),
        paw=(cx - 4.2, 20.5, 1.0),
        side_sign=-1.0,
        grounded=True,
    )

    # Ensure grounded feet & rear belly coil touch z=0 cleanly with zero gap
    for x in range(X):
        for y in range(Y):
            if grid[x, y, 1] > 0 and grid[x, y, 0] == 0:
                if y >= 12:
                    grid[x, y, 0] = 6 if grid[x, y, 1] in (5, 8) else grid[x, y, 1]

    # Hollow strictly interior bulk to land in sweet-spot voxel budget (2,200-3,400)
    hollow_interior_26(grid, 1, 37)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=34, pitch_a=20, yaw_b=46, pitch_b=20):
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
    v_a = export_vox(model_a, "kenshin_a.vox")
    v_b = export_vox(model_b, "kenshin_b.vox")
    c_a = count_6_components(model_a)
    c_b = count_6_components(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: UESUGI KENSHIN ROBOT -> DRAGON OF ECHIGO",
        "1. UESUGI KENSHIN ROBOT (GOD OF WAR)",
        "2. DRAGON OF ECHIGO (EASTERN DRAGON)",
        "preview_kenshin.png",
        yaw_a=34, pitch_a=20, yaw_b=48, pitch_b=20,
    )
    print(f"kenshin: A={v_a} voxels {model_a.shape} (6-comp={c_a}), B={v_b} voxels {model_b.shape} (6-comp={c_b})")
