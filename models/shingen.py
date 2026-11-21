import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across Takeda Shingen Robot & Tiger of Kai so parts visibly transform!
PALETTE = {
    1: (208, 34, 28, 255),    # Blazing Takeda Crimson-Vermilion Armor (Akazonae)
    2: (132, 18, 24, 255),    # Deep Crimson Lacquer Shading & Inner Plates
    3: (246, 136, 22, 255),   # Fiery Vivid Orange-Gold Tiger Fur & Striped Plates
    4: (250, 246, 236, 255),  # Crisp Snow-White Suwa Kabuto Yak-Hair Mane & Tiger Chest/Muzzle
    5: (24, 24, 30, 255),     # Bold Jet-Black Tiger Stripes & Gunbai Lacquer
    6: (244, 194, 42, 255),   # Radiant Takeda Gold Demon Horns, Takeda-bishi & Fittings
    7: (74, 72, 82, 255),     # Dark Iron / Gunmetal Joints & Samurai Menpo Mask
    8: (255, 238, 92, 255),   # Glowing Bright Amber-Gold Eyes & Crest Gem
    9: (212, 84, 14, 255),    # Deep Burnt-Orange Tiger Back Shading & Armor Bevel
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


def count_components_6(grid):
    """Verify 6-connectivity: returns number of 6-connected components."""
    X, Y, Z = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    xs, ys, zs = np.nonzero(grid)
    comps = 0
    for sx, sy, sz in zip(xs, ys, zs):
        sx, sy, sz = int(sx), int(sy), int(sz)
        if visited[sx, sy, sz]:
            continue
        comps += 1
        q = deque([(sx, sy, sz)])
        visited[sx, sy, sz] = True
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < X and 0 <= ny < Y and 0 <= nz < Z:
                    if grid[nx, ny, nz] > 0 and not visited[nx, ny, nz]:
                        visited[nx, ny, nz] = True
                        q.append((nx, ny, nz))
    return comps


# ==========================================
# FORM A: TAKEDA SHINGEN ROBOT (44 x 26 x 46)
# ==========================================
def build_a():
    grid = np.zeros((44, 26, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21 (-X, robot left)
    cx_r = X // 2      # 22 (+X, robot right, foreground in 3/4 view)

    # --- 1. ARMORED SAMURAI BOOTS & TIGER-CLAW TOES (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 8, 15, 0, 1, 5)     # Heavy jet-black lacquered sole
    fill_sym_box(grid, 4, 5, 7, 9, 0, 2, 7)      # Iron heel spur
    fill_sym_box(grid, 3, 6, 9, 15, 1, 2, 1)     # Blazing Takeda crimson footplate
    fill_sym_box(grid, 3, 6, 14, 16, 1, 2, 9)    # Burnt-orange armored toe cap
    # Three crisp white tiger-paw toes at front of each boot
    fill_sym_box(grid, 3, 3, 16, 17, 0, 1, 4)
    fill_sym_box(grid, 5, 5, 16, 17, 0, 1, 4)
    fill_sym_box(grid, 6, 6, 15, 16, 0, 1, 4)
    # Gold ankle collar & dark iron ankle joint
    fill_sym_box(grid, 3, 5, 9, 14, 3, 4, 7)
    fill_sym_box(grid, 3, 5, 14, 15, 3, 3, 6)

    # --- 2. TIGER-STRIPED SHIN ARMOR / SUNEATE (Z: 4..14) ---
    # Clean athletic leg spacing (inner gap x_off 0..2 completely open!)
    fill_sym_box(grid, 3, 5, 9, 13, 4, 14, 7)
    # Fiery orange-gold shin plates wrapping front & outer sides
    fill_sym_box(grid, 3, 6, 10, 14, 4, 12, 3)
    fill_sym_box(grid, 3, 5, 14, 15, 5, 11, 3)
    fill_sym_box(grid, 6, 6, 11, 13, 5, 11, 9)   # Outer burnt-orange bevel
    # Bold jet-black tiger stripes across shins!
    for sz in (5, 8, 11):
        fill_sym_box(grid, 3, 6, 11, 15, sz, sz, 5)
    fill_sym_box(grid, 6, 6, 10, 12, 6, 6, 5)
    fill_sym_box(grid, 6, 6, 10, 12, 9, 9, 5)
    # Blazing crimson Takeda inner & rear calf armor
    fill_sym_box(grid, 3, 3, 9, 13, 5, 12, 1)
    fill_sym_box(grid, 3, 5, 8, 9, 5, 12, 1)
    fill_sym_box(grid, 4, 5, 8, 8, 7, 10, 2)
    fill_sym_box(grid, 4, 4, 8, 8, 8, 9, 6)      # Rear gold calf rivet
    # Heroic Crimson & Gold Samurai Knee Guards
    fill_sym_box(grid, 3, 6, 14, 16, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 15, 16, 13, 14, 6)
    fill_sym_box(grid, 4, 4, 16, 16, 13, 14, 1)

    # --- 3. THIGHS & BLAZING CRIMSON KUSAZURI TASSETS (Z: 15..22) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 19, 7)   # Thigh inner frame
    fill_sym_box(grid, 3, 5, 12, 14, 15, 18, 1)  # Crimson thigh haidate plates
    fill_sym_box(grid, 4, 5, 14, 14, 16, 17, 2)
    # Pelvis & Waist core
    fill_sym_box(grid, 0, 5, 9, 14, 19, 22, 2)
    # Flared Blazing Crimson Kusazuri Samurai Skirt Lames (Front, Sides, Back)
    for kz in (17, 19, 21):
        fill_sym_box(grid, 2, 6, 14, 15, kz, kz, 1)
        fill_sym_box(grid, 5, 7, 9, 14, kz, kz, 1)
        fill_sym_box(grid, 1, 5, 8, 9, kz, kz, 1)
    for kz in (18, 20):
        fill_sym_box(grid, 2, 6, 14, 15, kz, kz, 2)
        fill_sym_box(grid, 5, 7, 9, 14, kz, kz, 2)
        fill_sym_box(grid, 1, 5, 8, 9, kz, kz, 2)
    # Gold tasset hem & crimson-gold waist obi sash
    fill_sym_box(grid, 2, 6, 15, 15, 17, 17, 6)
    fill_sym_box(grid, 6, 7, 10, 13, 17, 17, 6)
    fill_sym_box(grid, 0, 1, 14, 16, 18, 22, 1)  # Center crimson loin flap
    fill_sym_box(grid, 0, 1, 15, 16, 20, 21, 6)  # Gold Takeda belt buckle
    fill_sym_box(grid, 0, 0, 16, 16, 20, 21, 8)  # Glowing amber belt jewel

    # Rear Curved Striped Tiger Tail (clearly visible in REAR VIEW!)
    tail_segs = [
        (0, 0, 7, 8, 19, 20, 3),
        (0, 0, 6, 7, 18, 19, 5),
        (0, 0, 5, 6, 16, 18, 3),
        (0, 0, 4, 5, 15, 16, 5),
        (0, 0, 4, 5, 13, 15, 3),
        (0, 0, 3, 4, 12, 13, 5),
    ]
    for x0, x1, y0, y1, z0, z1, col in tail_segs:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)

    # --- 4. BLAZING CRIMSON DO-MARU TORSO & TAKEDA-BISHI CREST (Z: 22..33) ---
    # Sleek tapered samurai abdomen with Akazonae red lacing
    fill_sym_box(grid, 0, 4, 9, 14, 22, 24, 2)
    fill_sym_box(grid, 0, 4, 14, 15, 22, 24, 1)
    fill_sym_box(grid, 0, 3, 15, 15, 23, 23, 2)
    fill_sym_box(grid, 1, 2, 15, 15, 22, 22, 6)
    # Broad Blazing Takeda Crimson Chest Armor (Z: 25..32)
    fill_sym_box(grid, 0, 6, 8, 15, 25, 32, 1)
    fill_sym_box(grid, 0, 5, 14, 16, 25, 31, 1)
    fill_sym_box(grid, 5, 6, 9, 14, 26, 26, 2)
    fill_sym_box(grid, 5, 6, 9, 14, 29, 29, 2)
    # Jet-black lacquered breastplate centerpiece framing Gold Takeda-bishi 4-Diamond Crest!
    fill_sym_box(grid, 0, 3, 16, 16, 26, 30, 5)
    fill_sym_box(grid, 0, 0, 16, 17, 29, 30, 6)  # Top diamond
    fill_sym_box(grid, 0, 0, 16, 17, 26, 27, 6)  # Bottom diamond
    fill_sym_box(grid, 2, 2, 16, 17, 28, 28, 6)  # Side diamonds
    fill_sym_box(grid, 1, 1, 16, 17, 27, 29, 6)  # Inner diamond cluster
    fill_sym_box(grid, 0, 0, 17, 17, 28, 28, 8)  # Glowing amber center jewel
    # Fiery orange tiger-collar & snow-white fur trim along upper collar
    fill_sym_box(grid, 2, 5, 15, 16, 31, 32, 3)
    fill_sym_box(grid, 3, 4, 16, 16, 31, 31, 5)
    fill_sym_box(grid, 0, 2, 14, 16, 32, 32, 4)  # Snow-white collar trim
    fill_sym_box(grid, 2, 5, 10, 14, 32, 33, 1)  # Crimson shoulder-strap collar
    fill_sym_box(grid, 3, 4, 11, 13, 33, 33, 6)  # Gold collar rivets

    # --- REAR SAMURAI BACKPACK (Y: 5..8, Z: 23..32) ---
    fill_sym_box(grid, 0, 5, 6, 8, 24, 31, 1)
    fill_sym_box(grid, 0, 4, 5, 6, 25, 30, 2)
    fill_sym_box(grid, 2, 4, 5, 6, 25, 31, 3)    # Folded tiger-striped dorsal plates
    fill_sym_box(grid, 2, 4, 5, 5, 27, 27, 5)
    fill_sym_box(grid, 2, 4, 5, 5, 29, 29, 5)
    fill_sym_box(grid, 0, 1, 5, 5, 27, 29, 6)    # Rear gold Takeda emblem
    fill_sym_box(grid, 0, 0, 5, 5, 28, 28, 1)
    fill_sym_box(grid, 1, 3, 4, 5, 23, 25, 7)    # Iron thrusters

    # --- 5. FIERY TIGER-STRIPED SODE SHOULDER PAULDRONS (Z: 27..34) ---
    fill_sym_box(grid, 6, 9, 10, 13, 29, 32, 7)  # Shoulder axle mounts
    sode_layers = [
        (34, 7, 10, 9, 14, 1),   # Top blazing crimson ridge
        (33, 7, 11, 9, 14, 3),   # Vivid fiery orange-gold
        (32, 7, 11, 8, 15, 5),   # Bold jet-black tiger stripe!
        (31, 8, 12, 8, 15, 3),   # Vivid fiery orange-gold
        (30, 8, 12, 8, 15, 9),   # Burnt-orange shading
        (29, 8, 12, 8, 15, 5),   # Bold jet-black tiger stripe!
        (28, 8, 12, 9, 14, 3),   # Vivid fiery orange-gold
        (27, 9, 12, 9, 14, 1),   # Bottom blazing crimson trim
    ]
    for z, x0, x1, y0, y1, col in sode_layers:
        fill_sym_box(grid, x0, x1, y0, y1, z, z, col)
    fill_sym_box(grid, 7, 10, 14, 15, 34, 34, 6)
    fill_sym_box(grid, 11, 12, 11, 12, 33, 34, 6)
    fill_sym_box(grid, 12, 12, 9, 14, 27, 27, 6)
    fill_sym_box(grid, 7, 7, 8, 15, 28, 33, 1)

    # --- 6. ARMS & TAKEDA'S CLASSIC WAR FAN (GUNBAI) (Z: 9..30) ---
    # Upper arms
    fill_sym_box(grid, 8, 10, 10, 13, 22, 28, 7)
    fill_sym_box(grid, 8, 10, 10, 13, 24, 26, 1)
    fill_sym_box(grid, 9, 10, 11, 12, 22, 23, 6)

    # LEFT ARM (-X, viewer's right): Armored Crimson & Tiger-Striped Forearm Gauntlet + Claws
    fill_box(grid, cx_l - 11, cx_l - 8, 10, 14, 16, 21, 1)
    fill_box(grid, cx_l - 11, cx_l - 11, 10, 14, 17, 20, 3)
    fill_box(grid, cx_l - 11, cx_l - 11, 11, 13, 18, 18, 5)
    fill_box(grid, cx_l - 11, cx_l - 8, 14, 15, 16, 17, 6)
    fill_box(grid, cx_l - 10, cx_l - 8, 11, 14, 13, 15, 7)
    fill_box(grid, cx_l - 11, cx_l - 11, 13, 15, 14, 15, 4)
    fill_box(grid, cx_l - 10, cx_l - 10, 15, 16, 13, 14, 4)
    fill_box(grid, cx_l - 8, cx_l - 8, 15, 16, 13, 14, 4)

    # RIGHT ARM (+X, viewer's left foreground!): Angled OUTWARD & FORWARD holding TAKEDA'S GUNBAI WAR FAN!
    # Extending forearm smoothly outward (+X) so Gunbai stands cleanly clear of the body silhouette!
    fill_box(grid, cx_r + 8, cx_r + 12, 10, 14, 17, 21, 1)    # Forearm extending outward
    fill_box(grid, cx_r + 11, cx_r + 14, 11, 16, 17, 20, 1)   # Forward-angled wrist armor
    fill_box(grid, cx_r + 12, cx_r + 13, 11, 15, 18, 20, 3)   # Tiger-orange outer vambrace
    fill_box(grid, cx_r + 12, cx_r + 13, 13, 13, 18, 20, 5)   # Tiger stripe
    fill_box(grid, cx_r + 12, cx_r + 14, 15, 17, 17, 20, 6)   # Gold wrist cuff
    fill_box(grid, cx_r + 13, cx_r + 15, 16, 19, 17, 19, 7)   # Iron fist gripping Gunbai

    # ICONIC TAKEDA WAR FAN (GUNBAI / 軍配) held cleanly clear of right shoulder & leg!
    gx_mid = cx_r + 15  # X = 37 (clear silhouette!)
    fill_box(grid, gx_mid, gx_mid + 1, 18, 19, 13, 21, 6)     # Gold fan handle shaft
    fill_box(grid, gx_mid, gx_mid + 1, 18, 19, 14, 16, 5)     # Black lacquered grip
    # Hanging blazing crimson war tassel beneath pommel
    fill_box(grid, gx_mid, gx_mid + 1, 18, 19, 12, 12, 6)
    fill_box(grid, gx_mid, gx_mid + 1, 18, 19, 9, 11, 1)
    fill_box(grid, gx_mid - 1, gx_mid, 18, 19, 9, 10, 1)

    # Broad Gourd-Shaped Gunbai Paddle Blade facing viewer cleanly!
    gunbai_rows = [
        (20, -2, 3),
        (21, -3, 4),
        (22, -4, 5),
        (23, -4, 5),
        (24, -4, 5),
        (25, -4, 5),
        (26, -3, 4),
        (27, -3, 4),
        (28, -2, 3),
        (29, -1, 2),
    ]
    for z, dxl, dxr in gunbai_rows:
        for dx in range(dxl, dxr + 1):
            px = gx_mid + dx
            is_rim = (dx == dxl or dx == dxr or z in (20, 29))
            if is_rim:
                col = 6  # Radiant Takeda gold rim
            elif dx in (0, 1) and z <= 22:
                col = 6  # Central gold spine rib
            else:
                col = 5  # Jet-black lacquered iron war-fan face
            fill_box(grid, px, px, 18, 19, z, z, col)

    # Blazing Crimson War Sun & Gold Takeda Diamond on BOTH sides of the Gunbai!
    fill_box(grid, gx_mid - 1, gx_mid + 2, 18, 19, 23, 26, 1)
    fill_box(grid, gx_mid - 2, gx_mid + 3, 18, 19, 24, 25, 1)
    fill_box(grid, gx_mid, gx_mid + 1, 18, 19, 24, 25, 6)
    fill_box(grid, gx_mid, gx_mid + 1, 19, 19, 24, 25, 8)

    # --- 7. SUWA HOSSHO KABUTO HEAD (諏訪法性の兜) WITH SNOW-WHITE YAK-HAIR MANE & SWEEPING GOLDEN DEMON HORNS! ---
    # Neck & Crimson Throat Guard (Nodowa)
    fill_sym_box(grid, 0, 1, 10, 13, 32, 34, 7)
    fill_sym_box(grid, 0, 2, 13, 14, 33, 33, 1)

    # Core Kabuto Skull & Crimson Bowl (Z: 34..39)
    fill_sym_box(grid, 0, 2, 9, 14, 34, 39, 1)
    fill_sym_box(grid, 0, 3, 9, 13, 34, 36, 1)   # Crimson shikoro neck-guard
    fill_sym_box(grid, 0, 3, 9, 12, 34, 34, 6)   # Gold shikoro edge

    # Fierce Samurai Face & Menpo Mask — CLEARLY VISIBLE with Bright Glowing Amber Eyes!
    fill_sym_box(grid, 0, 2, 14, 15, 34, 37, 7)  # Dark iron menpo mask
    fill_sym_box(grid, 0, 1, 15, 16, 34, 35, 2)  # Fierce crimson chin/mouth guard
    fill_sym_box(grid, 1, 2, 15, 16, 35, 35, 4)  # White samurai mustache/fang accent
    fill_sym_box(grid, 0, 2, 14, 16, 36, 37, 5)  # Jet-black eye shadow frame
    fill_sym_box(grid, 1, 2, 16, 16, 36, 37, 8)  # BRIGHT GLOWING AMBER-GOLD SAMURAI EYES!
    fill_sym_box(grid, 0, 0, 16, 16, 36, 37, 7)  # Crisp dark iron nose bridge separating both eyes!
    fill_sym_box(grid, 0, 2, 14, 16, 38, 38, 1)  # Blazing crimson kabuto brow visor (mabizashi)
    fill_sym_box(grid, 0, 2, 16, 16, 38, 38, 6)  # Gold brow trim

    # VOLUMINOUS SNOW-WHITE YAK-HAIR MANE (白熊 / HAGUMA) ENVELOPING THE KABUTO!
    # Lush snow-white yak-hair crown & billowing side/rear locks clearly visible from front AND back!
    fill_sym_box(grid, 0, 3, 8, 15, 39, 41, 4)   # Lush high snow-white yak-hair dome!
    fill_sym_box(grid, 0, 2, 9, 14, 42, 42, 4)   # Fluffy upper snow-white crown
    # Side voluminous flowing mane tufts framing helmet & cheeks
    fill_sym_box(grid, 3, 5, 8, 14, 35, 40, 4)
    fill_sym_box(grid, 4, 6, 9, 13, 36, 39, 4)
    fill_sym_box(grid, 5, 6, 10, 12, 34, 36, 4)  # Lower hanging yak-hair locks
    fill_sym_box(grid, 3, 4, 13, 15, 37, 40, 4)  # Forward-framing white cheek tufts
    # Lush cascading yak-hair mane down the BACK of the kabuto (stunning in REAR VIEW!)
    fill_sym_box(grid, 0, 4, 6, 8, 35, 40, 4)
    fill_sym_box(grid, 0, 4, 5, 7, 32, 36, 4)
    fill_sym_box(grid, 1, 3, 5, 6, 31, 33, 4)
    fill_sym_box(grid, 0, 0, 5, 6, 30, 32, 4)
    # Sculpted shaggy texture notches
    fill_sym_box(grid, 2, 2, 5, 5, 33, 33, 0)
    fill_sym_box(grid, 5, 5, 8, 8, 35, 35, 0)
    fill_sym_box(grid, 3, 3, 15, 15, 41, 41, 0)

    # ICONIC SWEEPING GOLDEN DEMON HORNS (諏訪法性の兜 / ONI-GATA KUWAGATA)!
    # Crisp Golden Oni Maedate Centerpiece leaving white yak-hair crown proudly visible above!
    fill_sym_box(grid, 0, 1, 15, 17, 39, 40, 6)
    fill_sym_box(grid, 0, 0, 17, 17, 39, 40, 1)  # Crimson oni crest jewel
    # Sleek, wide, gracefully sweeping golden demon horns arching outward, upward & curving inward at sharp tips!
    horn_segs = [
        (1, 2, 16, 16, 39, 40),
        (2, 3, 15, 16, 40, 40),
        (3, 4, 15, 16, 40, 41),
        (4, 5, 14, 15, 41, 42),
        (5, 6, 14, 15, 42, 42),
        (6, 7, 13, 14, 42, 43),
        (7, 7, 13, 14, 43, 44),
        (6, 7, 13, 14, 44, 45),
        (5, 6, 13, 14, 45, 45),  # Razor-sharp inward-curving demon horn tips!
    ]
    for x0, x1, y0, y1, z0, z1 in horn_segs:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, 6)

    # Hollow strictly interior voxels to stay cleanly in ~3,100-3,500 budget
    hollow_interior_26(grid, 1, 43)
    return grid


# ==========================================
# FORM B: TIGER OF KAI (甲斐の虎) (26 x 50 x 26)
# ==========================================
def build_b():
    grid = np.zeros((26, 50, 26), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 12.5

    # Helper to color tiger fur with fiery orange-gold, burnt-orange back, crisp white belly, and bold jet-black vertical stripes!
    def tiger_fur_color(x, y, z, zb, zt, dx, rx):
        # Crisp white chest & underbelly
        if z <= zb + 1 and dx <= rx * 0.72:
            return 4
        if z == zb + 2 and dx <= rx * 0.45 and y >= 25:
            return 4
        # Bold jet-black vertical tiger stripes wrapping from spine down flanks
        y_shift = int(round((z - zb) * 0.16))
        y_eff = y - y_shift
        if (y_eff in (11, 15, 19, 23, 27, 30) or (y_eff in (12, 20, 28) and z >= zb + 4)) and z >= zb + 2:
            if dx >= rx * 0.22 or z >= zt - 1:
                return 5
        # Deep burnt-orange dorsal back shading
        if z >= zt - 1 and dx <= rx * 0.65:
            return 9
        return 3  # Blazing fiery vivid orange-gold fur

    # --- 1. LITHE, MUSCULAR PROWLING TIGER BODY (Y: 9..33, Z: 7..19) ---
    # Sleek elongated apex-predator proportions: powerful haunches -> supple tucked waist -> deep muscular shoulders!
    body_slices = [
        # (y, rx, zb, zt)
        (9,  3.1, 11, 17),   # Rounded muscular rump
        (10, 4.0, 10, 18),   # Powerful hindquarters
        (11, 4.5, 9,  19),
        (12, 4.6, 9,  19),
        (13, 4.4, 9,  19),
        (14, 4.1, 9,  18),
        (15, 3.8, 9,  18),   # Agile tucked feline waist
        (16, 3.7, 9,  18),
        (17, 3.7, 9,  18),
        (18, 3.8, 9,  18),
        (19, 4.0, 9,  18),   # Ribcage deepening
        (20, 4.3, 8,  18),
        (21, 4.6, 8,  18),
        (22, 4.8, 8,  18),
        (23, 5.0, 7,  19),
        (24, 5.2, 7,  19),   # Massive muscular shoulders
        (25, 5.3, 7,  19),
        (26, 5.3, 7,  20),
        (27, 5.2, 7,  20),
        (28, 5.0, 7,  20),
        (29, 4.7, 8,  19),
        (30, 4.4, 8,  19),
        (31, 4.1, 9,  19),   # Muscular neck
        (32, 3.9, 10, 19),
        (33, 3.8, 11, 19),
    ]
    for y, rx, zb, zt in body_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.25:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    grid[x, y, z] = tiger_fur_color(x, y, z, zb, zt, dx, rx)

    # Crisp Snow-White Tiger Chest Bib sweeping cleanly up the front chest (Y: 28..35)
    fill_sym_box(grid, 0, 2, 28, 32, 8, 14, 4)
    fill_sym_box(grid, 0, 1, 32, 35, 10, 15, 4)

    # --- 2. FOUR POWERFUL PROWLING LEGS WITH BOLD BLACK STRIPES & WHITE PAWS (Z: 0..14) ---
    def build_leg(side_sign, y_hip, y_knee, y_paw, is_front):
        x_hip = cx + side_sign * (4.1 if is_front else 3.8)
        x_paw = cx + side_sign * (4.2 if is_front else 4.0)
        z_top = 14
        for z in range(0, z_top + 1):
            t = z / float(z_top)
            if t < 0.45:
                s = t / 0.45
                ly = y_paw * (1 - s) + y_knee * s
            else:
                s = (t - 0.45) / 0.55
                ly = y_knee * (1 - s) + y_hip * s
            lx = x_paw * (1 - t) + x_hip * t
            if z <= 1:
                rx_l, ry_l = 1.85, 2.35
            elif z <= 5:
                rx_l, ry_l = 1.50, 1.70
            elif z <= 9:
                rx_l, ry_l = 1.75, 2.10
            else:
                rx_l, ry_l = 2.15, 2.65 if not is_front else 2.40
            for x in range(int(lx - 3), int(lx + 4)):
                for y in range(int(ly - 3), int(ly + 4)):
                    if 0 <= x < X and 0 <= y < Y:
                        if ((x - lx) / rx_l) ** 2 + ((y - ly) / ry_l) ** 2 <= 1.0:
                            if z <= 1 and y >= ly - 0.3:
                                col = 4
                            elif z <= 2 and (x - cx) * side_sign < abs(x_paw - cx) - 0.4:
                                col = 4
                            elif z in (4, 7, 10, 13) and (x - cx) * side_sign >= abs(lx - cx) - 0.6:
                                col = 5
                            elif z == 11 and y >= ly + 0.5:
                                col = 5
                            else:
                                col = 3
                            grid[x, y, z] = col
        # Crisp white tiger paws + subtle black claws
        px0 = int(round(x_paw - 1.5))
        px1 = int(round(x_paw + 1.5))
        py_front = int(round(y_paw + 2.0))
        fill_box(grid, px0, px1, int(round(y_paw)), py_front, 0, 1, 4)
        fill_box(grid, px0, px0, py_front + 1, py_front + 1, 0, 0, 5)
        fill_box(grid, int(round(x_paw)), int(round(x_paw)), py_front + 1, py_front + 1, 0, 0, 5)
        fill_box(grid, px1, px1, py_front + 1, py_front + 1, 0, 0, 5)
        # Blazing crimson & gold Takeda armored ankle cuff on forelegs
        if is_front:
            cuff_y = int(round(y_paw * 0.55 + y_knee * 0.45))
            fill_box(grid, int(round(x_paw - 1.5)), int(round(x_paw + 1.5)), cuff_y - 1, cuff_y + 2, 3, 4, 1)
            fill_box(grid, int(round(x_paw - 1.5)), int(round(x_paw + 1.5)), cuff_y + 2, cuff_y + 2, 4, 4, 6)

    # Athletic prowling stride with clean separation between forelegs & hindlegs!
    build_leg(+1, y_hip=27.5, y_knee=26.5, y_paw=31.5, is_front=True)
    build_leg(-1, y_hip=27.5, y_knee=25.0, y_paw=28.0, is_front=True)
    build_leg(+1, y_hip=12.5, y_knee=9.5,  y_paw=13.5, is_front=False)
    build_leg(-1, y_hip=12.5, y_knee=8.0,  y_paw=11.0, is_front=False)

    # --- 3. BLAZING CRIMSON TAKEDA ARMORED COLLAR, SHOULDER SODE & SLEEK GOLDEN HORNS ---
    # Blazing Crimson Dorsal Saddle & Shoulder Plates across muscular shoulders (echoes Akazonae!)
    fill_sym_box(grid, 0, 4, 23, 30, 19, 20, 1)
    fill_sym_box(grid, 0, 3, 24, 29, 20, 20, 2)
    fill_sym_box(grid, 0, 1, 24, 29, 20, 21, 6)  # Gold dorsal Takeda spine crest
    # Flared Blazing Crimson Takeda Shoulder Armor Wings (clearly visible on BOTH flanks!)
    fill_sym_box(grid, 4, 5, 24, 30, 15, 19, 1)
    fill_sym_box(grid, 5, 6, 25, 29, 16, 18, 1)
    fill_sym_box(grid, 6, 6, 26, 28, 17, 17, 6)  # Gold Takeda diamond stud on shoulder plate!
    fill_sym_box(grid, 5, 6, 25, 29, 15, 15, 6)  # Gold lower shoulder edge trim

    # Iconic Blazing Crimson Armored Neck Collar (Akazonae collar framing white mane!)
    fill_sym_box(grid, 0, 5, 30, 33, 13, 21, 1)
    fill_sym_box(grid, 0, 5, 30, 30, 14, 20, 2)  # Dark crimson layered collar seam
    fill_sym_box(grid, 0, 4, 31, 33, 21, 21, 6)  # Gold collar crest trim
    # Gold Takeda-bishi Chest Medallion hanging proudly on snow-white chest!
    fill_sym_box(grid, 0, 2, 33, 34, 10, 13, 1)  # Crimson medallion plate
    fill_sym_box(grid, 0, 1, 34, 35, 11, 12, 6)  # Radiant Takeda gold diamond!
    fill_sym_box(grid, 0, 0, 35, 35, 11, 12, 8)  # Amber gem gleam

    # Sleek Swept-Back Golden Demon-Horn Collar Crests (transformed from Suwa Kabuto horns!)
    collar_horns = [
        (3, 4, 31, 32, 20, 21),
        (4, 5, 30, 31, 21, 22),
        (5, 5, 29, 30, 22, 23),
        (5, 6, 27, 29, 23, 24),
        (6, 6, 26, 27, 24, 25),
        (5, 6, 25, 26, 25, 25),  # Sleek tapered golden horn tips!
    ]
    for x0, x1, y0, y1, z0, z1 in collar_horns:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, 6)

    # --- 4. SCULPTED SHAGGY SNOW-WHITE MANE TUFTS FROM SUWA KABUTO (白熊) ---
    # Tapered, spiky, flame-like white mane ruffs (NOT a flat block!) framing the tiger's cheeks & throat
    fill_sym_box(grid, 0, 4, 33, 36, 13, 21, 4)
    # Sculpted layered cheek-ruff spikes flaring outward cleanly
    fill_sym_box(grid, 4, 6, 33, 36, 14, 20, 4)
    fill_sym_box(grid, 5, 7, 33, 35, 16, 19, 4)  # Mid-cheek main spike
    fill_sym_box(grid, 6, 7, 32, 34, 17, 18, 4)  # Swept-back outer fur tip
    fill_sym_box(grid, 5, 6, 34, 36, 13, 15, 4)  # Lower cheek tuft
    fill_sym_box(grid, 3, 5, 34, 37, 12, 13, 4)  # Shaggy throat ruff
    fill_sym_box(grid, 0, 3, 33, 35, 21, 22, 4)  # White mane crown behind ears
    # Carve organic fur notches so the snow-white tufts read as dynamic wild yak-hair locks!
    fill_sym_box(grid, 6, 7, 35, 36, 19, 20, 0)
    fill_sym_box(grid, 6, 6, 33, 33, 15, 15, 0)
    fill_sym_box(grid, 5, 5, 36, 36, 14, 14, 0)
    fill_sym_box(grid, 2, 2, 33, 33, 22, 22, 0)

    # --- 5. FIERCE SCULPTED TIGER HEAD, FOREHEAD STRIPES & BRIGHT GLOWING AMBER EYES (Y: 35..48, Z: 12..24) ---
    head_slices = [
        # (y, rx, zb, zt)
        (36, 4.5, 13, 22),
        (37, 4.6, 13, 22),
        (38, 4.5, 13, 22),
        (39, 4.3, 13, 22),
        (40, 4.0, 13, 21),
        (41, 3.7, 13, 21),
        (42, 3.3, 13, 20),
    ]
    for y, rx, zb, zt in head_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    if z <= 15 and dx >= 1.4:
                        col = 4  # Crisp white cheeks
                    elif z <= 14:
                        col = 4
                    elif z in (16, 18) and y in (38, 40) and dx >= rx - 1.1:
                        col = 5  # Bold black cheek stripes
                    elif z >= zt - 1 and (y in (38, 40, 42) or dx < 0.8):
                        col = 5 if (dx < 0.8 or (y in (38, 40) and dx <= 2.6)) else 3  # Classic "王" tiger brow stripes!
                    else:
                        col = 3
                    grid[x, y, z] = col

    # Rounded Tiger Ears with jet-black backs & iconic white rear ear-spots!
    fill_sym_box(grid, 3, 4, 37, 39, 21, 23, 3)  # Vivid orange ear rim
    fill_sym_box(grid, 3, 4, 36, 37, 21, 23, 5)  # Jet-black back of ears
    fill_sym_box(grid, 4, 4, 36, 36, 22, 22, 4)  # Iconic white tiger ear-spot on rear!
    fill_sym_box(grid, 3, 3, 39, 39, 22, 22, 4)  # White inner ear tuft

    # Fierce Glowing Amber-Gold Eyes (high, crisp, bold black feline eyeliner!)
    fill_sym_box(grid, 2, 3, 41, 42, 18, 20, 5)  # Bold black eyeliner socket
    fill_sym_box(grid, 2, 3, 42, 42, 18, 19, 8)  # BRIGHT GLOWING AMBER-GOLD EYES!
    fill_sym_box(grid, 1, 3, 41, 42, 20, 20, 3)  # Fierce brow ridge
    fill_sym_box(grid, 2, 3, 42, 42, 20, 20, 5)  # Angry black brow stripe

    # Broad Snow-White Muzzle, Vivid Orange Nose Bridge & Snarling Fanged Jaw (Y: 42..48)
    fill_sym_box(grid, 0, 1, 42, 46, 17, 19, 3)  # Vivid orange tiger nose bridge
    fill_sym_box(grid, 0, 1, 44, 45, 19, 19, 9)  # Burnt-orange bridge highlight
    fill_sym_box(grid, 0, 1, 46, 47, 17, 18, 2)  # Broad dark crimson tiger nose
    fill_sym_box(grid, 0, 0, 47, 47, 17, 17, 5)  # Black nostril crease
    # Plump Crisp Snow-White Whisker Pads
    fill_sym_box(grid, 0, 2, 42, 46, 15, 16, 4)
    fill_sym_box(grid, 2, 3, 42, 45, 15, 16, 4)
    fill_sym_box(grid, 2, 2, 45, 45, 16, 16, 5)  # Whisker dot accent
    # Open Roaring Mouth with Sharp White Fangs & Snow-White Lower Jaw!
    fill_sym_box(grid, 0, 1, 42, 45, 13, 14, 2)  # Deep crimson roaring mouth interior
    fill_sym_box(grid, 1, 1, 45, 45, 14, 14, 4)  # Sharp upper white canine fangs!
    fill_sym_box(grid, 0, 2, 42, 46, 12, 12, 4)  # Strong crisp white lower jaw/chin
    fill_sym_box(grid, 1, 1, 45, 45, 13, 13, 4)  # Lower white fangs
    fill_sym_box(grid, 0, 1, 46, 46, 12, 12, 5)  # Black lower lip line

    # --- 6. LONG EXPRESSIVE STRIPED TIGER TAIL IN S-CURVE (Y: 1..10, Z: 12..22) ---
    tail_path = [
        (cx,       9.5, 16.0, 1.35, 3),
        (cx,       8.2, 15.2, 1.25, 5),
        (cx + 0.3, 7.0, 14.2, 1.20, 3),
        (cx + 0.7, 5.8, 13.5, 1.15, 5),
        (cx + 1.0, 4.6, 13.4, 1.15, 3),
        (cx + 1.3, 3.5, 14.0, 1.10, 5),
        (cx + 1.5, 2.7, 15.0, 1.10, 3),
        (cx + 1.6, 2.1, 16.3, 1.05, 5),
        (cx + 1.5, 1.8, 17.6, 1.05, 3),
        (cx + 1.3, 1.9, 18.9, 1.05, 5),
        (cx + 1.0, 2.2, 20.1, 1.00, 3),
        (cx + 0.7, 2.6, 21.2, 1.00, 5),  # Bold jet-black tiger tail tip!
    ]
    for txc, tyc, tzc, tr, tcol in tail_path:
        fill_sphere_local(grid, txc, tyc, tzc, tr, tr, tr, tcol)

    # Hollow strictly interior bulk of torso, legs, head to fit cleanly in budget ~2,400-3,200
    hollow_interior_26(grid, 1, 22)
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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=30, pitch_a=20, yaw_b=42, pitch_b=20):
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
    v_a = export_vox(model_a, "shingen_a.vox")
    v_b = export_vox(model_b, "shingen_b.vox")
    comp_a = count_components_6(model_a)
    comp_b = count_components_6(model_b)
    ground_a = int(np.count_nonzero(model_a[:, :, 0]))
    ground_b = int(np.count_nonzero(model_b[:, :, 0]))
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: TAKEDA SHINGEN ROBOT -> TIGER OF KAI",
        "1. TAKEDA SHINGEN ROBOT (AKAZONAE)",
        "2. TIGER OF KAI (KAI NO TORA)",
        "preview_shingen.png",
        yaw_a=28, pitch_a=18, yaw_b=44, pitch_b=19,
    )
    print(f"shingen: A={v_a} voxels {model_a.shape} (comps={comp_a}, z0={ground_a}), "
          f"B={v_b} voxels {model_b.shape} (comps={comp_b}, z0={ground_b})")
