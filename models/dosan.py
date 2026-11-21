import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across Saito Dosan Robot (Form A) and Giant Mottled Viper (Form B)
PALETTE = {
    1: (86, 108, 56, 255),    # Mottled Dark Olive-Green Viper Scale Armor
    2: (188, 158, 98, 255),   # Earthy Tan / Ochre Ventral Belly Plates & Scale Halos
    3: (146, 68, 36, 255),    # Rust-Brown Mamushi Saddle Blotches & Trim
    4: (44, 46, 40, 255),     # Dark Charcoal-Black Viper Markings & Inner Joints
    5: (208, 160, 52, 255),   # Antique Bronze-Gold Warlord Crest & Spear Fittings
    6: (246, 240, 224, 255),  # Ivory-White Venom Fangs & Gleaming Blade Edge
    7: (218, 40, 46, 255),    # Crimson Forked Tongue & Samurai Armor Lacing
    8: (255, 214, 34, 255),   # Glowing Amber Viper Slit Eyes & Chest Core
    9: (126, 134, 146, 255),  # Tempered Steel Blade & Warlord Faceplate
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


def mamushi_pattern(u, v):
    """Authentic Japanese mamushi (pit-viper) mottled coin/saddle pattern (まだら模様).
    Returns palette index in {1 (olive), 2 (tan), 3 (rust), 4 (charcoal)}.
    Produces bold, readable rust-brown blotches rimmed in charcoal with earthy-tan halos.
    """
    period_u = 8.0
    period_v = 7.0
    band = int(np.floor(u / period_u))
    cu = (u % period_u) - period_u * 0.5
    cv = ((v + (period_v * 0.5 if (band % 2) else 0.0)) % period_v) - period_v * 0.5
    dist = abs(cu) * 0.85 + abs(cv) * 1.05
    if dist <= 1.55:
        return 3  # Rich rust-brown saddle core
    elif dist <= 2.35:
        return 4  # Dark charcoal-black blotch rim
    elif dist <= 3.05:
        return 2 if ((int(round(u)) + int(round(v))) % 2 == 0) else 1  # Tan halo border
    return 1      # Dark olive-green viper scale base


def fill_mottled_box(grid, x0, x1, y0, y1, z0, z1, phase=0):
    """Fill a box with bold, readable mamushi viper-scale mottling."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(x0, x1)), min(X - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                grid[x, y, z] = mamushi_pattern(x + y * 0.7 + phase, z * 1.1)


def fill_sym_mottled_box(grid, x_off0, x_off1, y0, y1, z0, z1, phase=0):
    """Symmetrically fill a box with mirrored mamushi viper-scale mottling."""
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1
    cx_r = X // 2
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    for dx in range(x_off0, x_off1 + 1):
        xl = cx_l - dx
        xr = cx_r + dx
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                col = mamushi_pattern(dx * 1.1 + y * 0.7 + phase, z * 1.1)
                if 0 <= xl < X:
                    grid[xl, y, z] = col
                if 0 <= xr < X:
                    grid[xr, y, z] = col


def fill_coiled_leg_ring(grid, z_mid, x_off0, x_off1, y0, y1, slope=0.25, phase=0):
    """Sculpt a thick, unmistakably rounded coiled-snake ring tier on each lower leg.
    Features a dark charcoal coil groove at the bottom, earthy-tan belly band along the lower edge,
    and bold mottled olive/rust/charcoal viper scales across the bulging upper coil!
    """
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1
    cx_r = X // 2
    xc = (x_off0 + x_off1) / 2.0
    yc = (y0 + y1) / 2.0
    rx = (x_off1 - x_off0) / 2.0 + 0.55
    ry = (y1 - y0) / 2.0 + 0.55
    rz = 1.65

    for dx in range(x_off0, x_off1 + 1):
        z_local = z_mid + slope * (dx - xc)
        for y in range(y0, y1 + 1):
            for z in range(max(0, int(np.floor(z_local - rz))), min(Z, int(np.ceil(z_local + rz)) + 1)):
                nx = (dx - xc) / rx
                ny = (y - yc) / ry
                nz = (z - z_local) / rz
                if nx * nx + ny * ny + nz * nz <= 1.0:
                    # Underside rim shows earthy-tan ventral belly band + dark coil groove!
                    if nz <= -0.52:
                        col = 4
                    elif nz <= -0.10 and (y >= yc - 0.5 or dx <= x_off0 + 1):
                        col = 2
                    else:
                        col = mamushi_pattern(dx * 1.2 + y * 0.8 + phase, (z - z_mid) * 1.6 + phase * 0.5)
                    xl = cx_l - dx
                    xr = cx_r + dx
                    if 0 <= xl < X:
                        grid[xl, y, z] = col
                    if 0 <= xr < X:
                        grid[xr, y, z] = col


def count_components_6(grid):
    """Verify 6-connectivity of all occupied voxels."""
    pts = set(zip(*np.nonzero(grid)))
    if not pts:
        return 0
    comps = 0
    while pts:
        comps += 1
        start = next(iter(pts))
        q = deque([start])
        pts.remove(start)
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nb = (x + dx, y + dy, z + dz)
                if nb in pts:
                    pts.remove(nb)
                    q.append(nb)
    return comps


# ============================================================
# FORM A: SAITO DOSAN ROBOT ("VIPER OF MINO") (44 x 28 x 46)
# ============================================================
def build_a():
    grid = np.zeros((44, 28, 46), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21 (-X: robot left)
    cx_r = X // 2      # 22 (+X: robot right)

    # --- 1. GROUNDED COILED VIPER BOOTS (Z: 0..4) ---
    # Heavy charcoal grounded soles & heel spurs
    fill_sym_box(grid, 2, 7, 10, 16, 0, 1, 4)
    fill_sym_box(grid, 3, 6, 9, 10, 0, 2, 4)
    # Bottom viper-coil boot ring wrapping solidly around the foot
    fill_coiled_leg_ring(grid, z_mid=2.2, x_off0=2, x_off1=7, y0=10, y1=16, slope=0.20, phase=1)
    # Segmented tan ventral toe armor & steel warlord claws
    fill_sym_box(grid, 3, 6, 16, 17, 1, 2, 2)
    fill_sym_box(grid, 3, 6, 17, 17, 0, 0, 4)
    fill_sym_box(grid, 3, 3, 18, 18, 0, 1, 9)  # Inner claw
    fill_sym_box(grid, 6, 6, 18, 18, 0, 1, 9)  # Outer claw
    fill_sym_box(grid, 4, 5, 17, 17, 2, 2, 5)  # Bronze-gold toe crest
    # Crisp dark coil groove separating boot from shin coils
    fill_sym_box(grid, 3, 6, 11, 15, 4, 4, 4)

    # --- 2. THICK LAYERED COILED LOWER LEGS (Z: 4..15) ---
    # Three bold, rounded, stacked helical snake-coil tiers forming Dosan's lower legs! (とぐろがロボの下半身になる)
    fill_sym_box(grid, 3, 5, 11, 14, 4, 16, 4)  # Solid inner leg structural core
    fill_coiled_leg_ring(grid, z_mid=6.2,  x_off0=2, x_off1=6, y0=10, y1=16, slope=-0.28, phase=4)
    fill_coiled_leg_ring(grid, z_mid=9.8,  x_off0=2, x_off1=6, y0=10, y1=16, slope=0.28,  phase=9)
    fill_coiled_leg_ring(grid, z_mid=13.2, x_off0=2, x_off1=6, y0=10, y1=16, slope=-0.24, phase=14)

    # Crimson samurai odoshi side-lacing & bronze-gold clasps locking the coils into greaves
    fill_sym_box(grid, 6, 6, 12, 13, 6, 13, 7)
    fill_sym_box(grid, 6, 6, 12, 13, 9, 10, 5)

    # Sharp fanged viper-scale knee guards (Z: 14..17)
    fill_sym_box(grid, 3, 5, 16, 16, 14, 16, 1)
    fill_sym_box(grid, 4, 5, 17, 17, 14, 16, 5)  # Bronze-gold knee crest
    fill_sym_box(grid, 4, 5, 17, 18, 16, 16, 6)  # Twin ivory knee fangs

    # --- 3. THIGHS & BOLD COILED VIPER-RING SKIRT ARMOR (KUSAZURI) (Z: 16..23) ---
    # Armored thighs
    fill_sym_box(grid, 2, 4, 10, 15, 16, 20, 4)
    fill_sym_box(grid, 3, 4, 12, 15, 16, 19, 9)

    # Sculptural Thick Coiled Snake-Ring Waist Skirt (2 clearly stacked horizontal coil rings!)
    # Lower flared skirt coil (Z: 17..19)
    for z in range(17, 20):
        for dx in range(0, 9):
            for y in range(9, 17):
                nx = dx / 8.6
                ny = (y - 12.8) / 4.2
                d2 = nx * nx + ny * ny
                if 0.45 <= d2 <= 1.04:
                    if y >= 15 and dx <= 1 and z == 17:
                        continue  # Front skirt split over thighs
                    if z == 17:
                        col = 2 if (y >= 12 or dx >= 6) else 4  # Tan ventral belly rim under coil!
                    else:
                        col = mamushi_pattern(dx * 1.2 + y * 0.9 + 2, z * 1.4)
                    grid[cx_l - dx, y, z] = col
                    grid[cx_r + dx, y, z] = col

    # Dark recessed coil seam between lower skirt coil and upper waist coil (Z: 20)
    for dx in range(0, 8):
        for y in range(10, 16):
            if (dx / 7.6) ** 2 + ((y - 12.8) / 3.5) ** 2 <= 1.0:
                grid[cx_l - dx, y, 20] = 4
                grid[cx_r + dx, y, 20] = 4

    # Upper coiled waist belt ring (Z: 21..22)
    for z in range(21, 23):
        for dx in range(0, 7):
            for y in range(10, 16):
                if (dx / 6.6) ** 2 + ((y - 12.8) / 3.3) ** 2 <= 1.04:
                    col = 2 if (z == 21 and y >= 14) else mamushi_pattern(dx * 1.2 + y + 7, z * 1.2)
                    grid[cx_l - dx, y, z] = col
                    grid[cx_r + dx, y, z] = col

    # Front warlord ventral-scale apron (前垂れ), crimson lacing & gold viper-fang belt buckle
    fill_sym_box(grid, 0, 2, 16, 17, 17, 20, 2)
    fill_sym_box(grid, 0, 2, 17, 17, 18, 18, 4)
    fill_sym_box(grid, 0, 1, 17, 17, 17, 17, 7)  # Crimson hem
    fill_sym_box(grid, 2, 2, 16, 17, 17, 19, 7)  # Crimson cords
    fill_sym_box(grid, 0, 1, 16, 18, 20, 22, 5)  # Antique gold belt buckle
    fill_sym_box(grid, 0, 0, 18, 18, 21, 21, 8)  # Amber belt jewel
    fill_sym_box(grid, 1, 1, 18, 18, 20, 20, 6)  # Buckle ivory fangs
    fill_sym_box(grid, 8, 8, 12, 13, 17, 19, 7)  # Side skirt crimson ties

    # Rear Coiled Viper Tail sweeping dynamically out from rear skirt! (Unmistakable in REAR VIEW!)
    fill_box(grid, cx_r - 1, cx_r + 2, 7, 10, 17, 19, 1)
    fill_box(grid, cx_r + 1, cx_r + 3, 6, 8, 16, 18, 3)
    fill_box(grid, cx_r + 2, cx_r + 4, 5, 7, 15, 17, 4)
    fill_box(grid, cx_r + 2, cx_r + 3, 5, 6, 13, 15, 2)
    fill_box(grid, cx_r + 1, cx_r + 2, 5, 6, 12, 13, 1)
    fill_box(grid, cx_r - 1, cx_r + 1, 5, 6, 11, 12, 4)
    fill_box(grid, cx_l - 1, cx_l,     5, 5, 10, 11, 5)  # Tapered gold-tipped viper tail end!

    # --- 4. WARLORD TORSO / VIPER-SCALE CUIRASS (Z: 23..34) ---
    # Sleek tapered armored waist with ribbed earthy-tan ventral abdominal plates
    fill_sym_box(grid, 0, 4, 11, 15, 23, 25, 4)
    fill_sym_box(grid, 0, 3, 15, 16, 23, 25, 2)
    fill_sym_box(grid, 0, 3, 16, 16, 24, 24, 4)
    fill_sym_box(grid, 4, 4, 12, 15, 23, 25, 7)  # Crimson waist lacing

    # Broad Cunning Sengoku Warlord Chest (Z: 26..33)
    fill_sym_mottled_box(grid, 0, 6, 10, 16, 26, 33, phase=2)
    fill_sym_mottled_box(grid, 2, 5, 16, 17, 27, 32, phase=6)
    # Center ribbed tan ventral breastplate & crimson samurai lacing
    fill_sym_box(grid, 0, 2, 16, 17, 26, 31, 2)
    fill_sym_box(grid, 0, 2, 17, 17, 27, 27, 4)
    fill_sym_box(grid, 2, 3, 17, 17, 28, 30, 7)  # Crimson odoshi chest lacing
    # Triangular Bronze-Gold Viper-Head Chest Crest + Glowing Amber Core + Twin Ivory Fangs!
    fill_sym_box(grid, 0, 2, 17, 18, 29, 32, 5)
    fill_sym_box(grid, 0, 1, 18, 18, 28, 31, 4)
    fill_sym_box(grid, 0, 0, 18, 19, 29, 30, 8)  # Glowing amber chest core
    fill_sym_box(grid, 2, 2, 17, 18, 27, 28, 6)  # Twin chest fangs
    # High samurai collar framing the kabuto
    fill_sym_box(grid, 0, 4, 10, 15, 33, 34, 4)
    fill_sym_box(grid, 2, 4, 11, 15, 34, 34, 5)
    fill_sym_box(grid, 0, 3, 10, 10, 34, 35, 4)

    # --- 5. VIPER-SPINE BACKPACK & WARLORD FIN STREAMERS (Y: 6..10, Z: 24..36) ---
    fill_sym_mottled_box(grid, 0, 4, 7, 10, 24, 33, phase=10)
    fill_sym_box(grid, 0, 1, 6, 7, 24, 33, 4)    # Central dorsal spine groove
    for z in (25, 27, 29, 31):
        fill_sym_box(grid, 0, 0, 6, 6, z, z, 5)  # Gold dorsal spine studs
    fill_sym_box(grid, 2, 3, 6, 7, 26, 30, 3)    # Rust saddle blotch plates
    # Twin dramatic angled crimson/gold warlord back-fins
    fill_sym_box(grid, 4, 5, 7, 8, 29, 34, 4)
    fill_sym_box(grid, 5, 6, 6, 7, 31, 36, 7)
    fill_sym_box(grid, 5, 6, 6, 6, 36, 37, 5)

    # --- 6. FLARED VIPER-HOOD SAMURAI SODE PAULDRONS (Z: 29..36) ---
    fill_sym_box(grid, 6, 9, 11, 14, 30, 33, 4)
    fill_sym_box(grid, 7, 9, 12, 14, 31, 32, 9)

    sode_layers = [
        (36, 7,  11, 11, 15),
        (35, 7,  12, 11, 15),
        (34, 7,  12, 10, 15),
        (33, 8,  12, 10, 15),
        (32, 9,  12, 10, 15),
        (31, 10, 12, 10, 15),
        (30, 10, 12, 11, 15),
        (29, 10, 11, 11, 15),
    ]
    for z, x0, x1, y0, y1 in sode_layers:
        fill_sym_mottled_box(grid, x0, x1, y0, y1, z, z, phase=z + 2)
        if z in (36, 35):
            fill_sym_box(grid, x1, x1, y0, y1, z, z, 5)
        if z in (33, 30):
            fill_sym_box(grid, x1, x1, y0 + 1, y1 - 1, z, z, 7)
        if z == 29:
            fill_sym_box(grid, x0, x1, y0, y1, z, z, 5)
    # Sharp ivory fang-spikes jutting cleanly from pauldron fronts
    fill_sym_box(grid, 11, 12, 16, 16, 34, 35, 6)
    fill_sym_box(grid, 12, 12, 17, 17, 35, 36, 6)

    # --- 7. ARMS, FANGED VIPER BUCKLER & HEROIC CURVED SERPENTINE SPEAR ---
    # Upper arms (Z: 23..29)
    fill_sym_box(grid, 8, 9, 11, 14, 24, 29, 4)
    fill_sym_box(grid, 8, 9, 11, 14, 26, 27, 7)  # Crimson bicep cords
    fill_sym_box(grid, 8, 9, 12, 14, 23, 24, 9)  # Steel elbow joint

    # LEFT ARM (-X, viewer's right): Armored Forearm + Fanged Viper-Head Buckler Shield
    fill_mottled_box(grid, cx_l - 10, cx_l - 8, 11, 15, 17, 23, phase=3)
    fill_box(grid, cx_l - 10, cx_l - 8, 15, 15, 18, 22, 2)   # Tan front vambrace
    fill_box(grid, cx_l - 10, cx_l - 8, 12, 15, 14, 16, 4)   # Armored left fist
    fill_box(grid, cx_l - 10, cx_l - 9, 15, 16, 15, 16, 9)
    # Sleek Triangular Viper-Head Forearm Shield with Twin Ivory Fang Blades
    fill_mottled_box(grid, cx_l - 12, cx_l - 11, 11, 17, 16, 24, phase=6)
    fill_box(grid, cx_l - 12, cx_l - 12, 13, 16, 19, 21, 3)  # Rust crown blotch
    fill_box(grid, cx_l - 12, cx_l - 12, 14, 15, 16, 23, 5)  # Gold center ridge
    fill_box(grid, cx_l - 12, cx_l - 12, 16, 17, 20, 20, 8)  # Glowing amber eye stud
    # Sleek 1-voxel-sharp twin ivory fang blades
    fill_box(grid, cx_l - 12, cx_l - 11, 17, 19, 17, 17, 6)
    fill_box(grid, cx_l - 12, cx_l - 12, 19, 20, 16, 17, 6)
    fill_box(grid, cx_l - 12, cx_l - 11, 17, 19, 22, 22, 6)
    fill_box(grid, cx_l - 12, cx_l - 12, 19, 20, 22, 23, 6)

    # RIGHT ARM (+X, viewer's left foreground): Reaching out boldly to hold Menacing Curved Viper-Spear!
    fill_mottled_box(grid, cx_r + 8, cx_r + 11, 12, 15, 17, 23, phase=5)
    fill_box(grid, cx_r + 9, cx_r + 11, 15, 16, 17, 22, 2)   # Tan forearm guard
    fill_box(grid, cx_r + 11, cx_r + 12, 14, 16, 18, 20, 5)  # Gold gauntlet cuff
    # Right fist gripping the spear cleanly outside & forward of the shoulder!
    fill_box(grid, cx_r + 11, cx_r + 14, 15, 18, 16, 18, 4)
    fill_box(grid, cx_r + 12, cx_r + 14, 17, 18, 17, 18, 9)

    # MENACING CURVED SERPENTINE SPEAR / VIPER NAGINATA (sweeping dramatically outward in +X!)
    sx = cx_r + 14  # x = 36, cleanly outside pauldron!
    # Sleek reinforced dark charcoal spear shaft with antique gold grip rings
    fill_box(grid, sx, sx, 16, 17, 5, 29, 4)
    for rz in (8, 12, 21, 25):
        fill_box(grid, sx, sx, 16, 17, rz, rz, 5)
    # Sharp bronze-gold & steel spear butt-cap
    fill_box(grid, sx, sx, 16, 17, 3, 4, 5)
    fill_box(grid, sx, sx, 16, 16, 2, 2, 9)
    # Fanged Gold Viper-Mouth Collar + Flowing Crimson Tassel (Z: 28..30)
    fill_box(grid, sx - 1, sx + 1, 15, 18, 28, 30, 5)
    fill_box(grid, sx, sx + 1, 18, 19, 29, 30, 6)  # Collar fangs
    fill_box(grid, sx + 1, sx + 1, 15, 16, 24, 28, 7)
    fill_box(grid, sx + 2, sx + 2, 15, 15, 20, 24, 7)
    # Dramatic Outward-Sweeping S-Curved Serpentine Naginata Blade (Z: 30..45)
    # Sweeps boldly OUTWARD (+X) and upward (+Z) so its curved viper-blade silhouette slashes across the sky!
    blade_segs = [
        # (x0, x1, y0, y1, z0, z1)
        (sx,     sx + 1, 16, 18, 30, 32),
        (sx + 1, sx + 2, 16, 18, 32, 34),
        (sx + 2, sx + 3, 17, 19, 34, 36),
        (sx + 3, sx + 4, 17, 19, 36, 38),
        (sx + 3, sx + 5, 17, 19, 38, 40),
        (sx + 4, sx + 6, 18, 20, 40, 42),
        (sx + 5, sx + 6, 18, 20, 42, 43),
        (sx + 6, sx + 7, 18, 20, 43, 44),
        (sx + 7, sx + 7, 19, 20, 44, 45),  # Razor-sharp sweeping outward blade tip!
    ]
    for bx0, bx1, by0, by1, bz0, bz1 in blade_segs:
        fill_box(grid, bx0, bx1, by0, by1, bz0, bz1, 9)  # Tempered steel blade body
        fill_box(grid, bx1, bx1, by0, by1, bz0, bz1, 6)  # Gleaming ivory outer cutting edge (+X)
        fill_box(grid, bx0, bx1, by1, by1, bz0, bz1, 6)  # Gleaming ivory front edge (+Y)
    # Wicked rear gold & ivory viper-fang barb on inner blade spine
    fill_box(grid, sx, sx + 1, 15, 17, 34, 35, 5)
    fill_box(grid, sx - 1, sx, 15, 16, 35, 36, 6)

    # --- 8. HEAD: SHARP FANGED VIPER-CREST KABUTO (Z: 34..45) ---
    # Raised proud neck so kabuto sits heroically above collar
    fill_sym_box(grid, 0, 1, 11, 14, 33, 35, 4)
    # Kabuto helmet dome (hachi)
    fill_sym_box(grid, 0, 3, 10, 15, 36, 39, 1)
    fill_sym_box(grid, 0, 2, 10, 15, 40, 40, 4)
    fill_sym_box(grid, 0, 1, 11, 14, 41, 41, 1)
    fill_sym_box(grid, 0, 0, 10, 15, 40, 41, 5)   # Central antique gold kabuto ridge
    # Sweeping samurai shikoro neck-guard flaps
    fill_sym_box(grid, 3, 4, 9, 14, 35, 37, 4)
    fill_sym_box(grid, 4, 5, 9, 13, 34, 36, 1)
    fill_sym_box(grid, 4, 5, 9, 13, 34, 34, 7)    # Crimson shikoro lacing hem
    fill_sym_box(grid, 0, 4, 9, 10, 35, 37, 4)
    fill_sym_box(grid, 0, 4, 9, 9,  35, 35, 5)

    # Fierce Cunning Faceplate & Bright Piercing Glowing Amber Slit Eyes!
    fill_sym_box(grid, 0, 2, 15, 16, 35, 36, 9)   # Dark steel menpo jaw mask
    fill_sym_box(grid, 0, 1, 16, 16, 35, 35, 4)   # Menacing mouth vent
    fill_sym_box(grid, 0, 0, 16, 16, 36, 37, 4)   # Nasal bridge dividing the slit eyes
    fill_sym_box(grid, 1, 2, 15, 16, 37, 37, 8)   # GLOWING AMBER SLIT EYES (clearly visible!)
    fill_sym_box(grid, 0, 2, 15, 16, 38, 38, 4)   # Aggressive dark brow rim

    # RAZOR-SHARP SWEPT FANGED VIPER-CREST MAEDATE (Z: 39..45, cleanly above eyes!)
    fill_sym_box(grid, 0, 1, 15, 16, 39, 40, 5)   # Bronze-gold central viper emblem
    fill_sym_box(grid, 0, 0, 16, 16, 39, 39, 7)   # Crimson warlord jewel
    # Sleek, sweeping, razor-sharp golden-and-ivory viper-fang horns soaring to Z=45!
    crest_segs = [
        (1, 2, 15, 16, 39, 40, 5),
        (2, 3, 15, 16, 40, 41, 5),
        (3, 4, 15, 16, 41, 42, 6),
        (4, 5, 15, 15, 42, 43, 6),
        (5, 5, 15, 15, 43, 45, 6),  # Sharp tall curved ivory viper-fang crest tips!
    ]
    for x0, x1, y0, y1, z0, z1, ccol in crest_segs:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, ccol)
    # Downward cheek-fang prongs flanking the menpo
    fill_sym_box(grid, 3, 3, 15, 16, 36, 37, 6)

    # Hollow strictly interior bulk cleanly while keeping 100% 6-connectivity
    hollow_interior_26(grid, 1, Z - 2)
    return grid


# ============================================================
# FORM B: GIANT MOTTLED VIPER (美濃の蝮・大蛇) (36 x 38 x 38)
# ============================================================
def build_b():
    grid = np.zeros((36, 38, 38), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 17.5
    cy_coil = 14.8

    def stamp_serpent_slice(px, py, pz, rx, ry, rz, arc_idx, mode="coil", ground_flat=False):
        """Stamp an ellipsoidal cross-section of the viper with bold mamushi coin/saddle blotches
        (まだら模様) and segmented earthy-tan ventral belly plates!"""
        x0 = max(0, int(np.floor(px - rx - 0.5)))
        x1 = min(X - 1, int(np.ceil(px + rx + 0.5)))
        y0 = max(0, int(np.floor(py - ry - 0.5)))
        y1 = min(Y - 1, int(np.ceil(py + ry + 0.5)))
        z0 = max(0, int(np.floor(pz - rz - 0.5)))
        z1 = min(Z - 1, int(np.ceil(pz + rz + 0.5)))
        if ground_flat:
            z0 = 0
        for x in range(x0, x1 + 1):
            dx = (x - px) / rx
            if abs(dx) > 1.05:
                continue
            for y in range(y0, y1 + 1):
                dy = (y - py) / ry
                if dx * dx + dy * dy > 1.1:
                    continue
                for z in range(z0, z1 + 1):
                    if ground_flat and z < pz:
                        dz = max(0.0, (pz - z) / (rz + 1.1))
                    else:
                        dz = (z - pz) / rz
                    if dx * dx + dy * dy + dz * dz <= 1.0:
                        if mode == "coil":
                            is_belly = (z <= pz - rz * 0.45)
                            is_ridge = (z >= pz + rz * 0.65 and abs(dx) < 0.32 and abs(dy) < 0.32)
                            if is_belly:
                                col = 2 if (arc_idx % 3 != 0) else 4
                            elif is_ridge and (arc_idx % 5 == 0):
                                col = 5  # Subtle bronze-gold dorsal spine stud
                            else:
                                # Evenly spaced vivid mamushi blotches across all 3 stacked coils!
                                rad_ang = np.arctan2(z - pz, np.hypot(x - px, y - py))
                                v_coord = (rad_ang / np.pi) * 8.0 + 3.5
                                col = mamushi_pattern(arc_idx * 0.62, v_coord)
                        else:
                            # Rearing upper body: front (+Y) = segmented tan belly scutes!
                            # Back (-Y) & flanks = bold mottled olive/rust/charcoal mamushi pattern!
                            if dy >= 0.42 and abs(dx) <= 0.72:
                                col = 2 if ((int(round(z)) % 2) == 0) else 4
                            elif dy <= -0.68 and abs(dx) <= 0.30 and (int(round(z)) % 3 == 0):
                                col = 5  # Gold warlord spine accent
                            else:
                                side_v = (dx + 1.2) * 3.2
                                col = mamushi_pattern(arc_idx * 0.55, side_v)
                        grid[x, y, z] = col

    # --- 1. THICK STACKED COILED BASE (とぐろ) (Z: 0..14) ---
    # 3 proud stacked rings resting solidly on z=0, directly echoing Dosan Robot's lower body!
    coil_keyframes = [
        (0.00, -0.35 * np.pi, 13.0, 0.9, 1.00),  # Pointed tail tip curling out at right-rear
        (0.05, -0.15 * np.pi, 12.2, 1.5, 1.65),  # Tapering tail thickening
        (0.11,  0.10 * np.pi, 11.4, 2.3, 2.40),  # Entering Ring 1 (outer base coil)
        (0.22,  0.65 * np.pi, 11.0, 2.5, 2.68),  # Ring 1 front (+Y)
        (0.34,  1.25 * np.pi, 10.6, 2.5, 2.68),  # Ring 1 left-back
        (0.45,  1.80 * np.pi, 10.1, 3.0, 2.65),  # Ring 1 wrapping back to +X
        (0.51,  2.10 * np.pi,  9.2, 5.4, 2.60),  # Stepping crisply onto Ring 2!
        (0.61,  2.65 * np.pi,  8.6, 6.4, 2.58),  # Ring 2 front (+Y) stacked on Ring 1!
        (0.71,  3.25 * np.pi,  8.0, 7.0, 2.55),  # Ring 2 left-back
        (0.79,  3.78 * np.pi,  7.4, 7.8, 2.52),  # Ring 2 rear-right
        (0.84,  4.10 * np.pi,  6.6, 9.9, 2.48),  # Stepping crisply onto Ring 3!
        (0.91,  4.55 * np.pi,  5.9, 10.9, 2.45), # Ring 3 proud front coil (+Y)
        (0.96,  5.05 * np.pi,  5.2, 12.0, 2.40), # Ring 3 sweeping around -X
        (1.00,  5.50 * np.pi,  4.7, 13.3, 2.35), # Rear center (-Y) launching upward!
    ]

    def interp_kf(kfs, t):
        for i in range(len(kfs) - 1):
            if kfs[i][0] <= t <= kfs[i + 1][0]:
                t0, th0, R0, z0, r0 = kfs[i]
                t1, th1, R1, z1, r1 = kfs[i + 1]
                f = (t - t0) / max(1e-6, t1 - t0)
                fs = f * f * (3.0 - 2.0 * f)
                return (
                    th0 + (th1 - th0) * f,
                    R0 + (R1 - R0) * fs,
                    z0 + (z1 - z0) * fs,
                    r0 + (r1 - r0) * fs,
                )
        return kfs[-1][1:]

    n_coil_steps = 250
    for i in range(n_coil_steps + 1):
        t = i / n_coil_steps
        theta, R, zc, rt = interp_kf(coil_keyframes, t)
        px = cx + R * np.cos(theta)
        py = cy_coil + (R * 0.94) * np.sin(theta)
        gflat = (t <= 0.45)
        stamp_serpent_slice(px, py, zc, rt, rt, rt * 0.90, arc_idx=i, mode="coil", ground_flat=gflat)

    # Pointed dark charcoal & gold-tipped viper tail end
    t0_th, t0_R, _, _ = coil_keyframes[0][1:]
    tx0 = int(round(cx + t0_R * np.cos(t0_th)))
    ty0 = int(round(cy_coil + (t0_R * 0.94) * np.sin(t0_th)))
    fill_box(grid, tx0 - 1, tx0 + 1, ty0 - 1, ty0 + 1, 0, 1, 4)
    fill_box(grid, tx0 + 1, tx0 + 1, ty0 - 1, ty0,     0, 0, 5)

    # --- 2. POWERFULLY REARING S-CURVE UPPER BODY & NECK (Z: 13..32) ---
    rear_keyframes = [
        # (u, dx, y, z, rx, ry, rz)
        (0.00,  0.0, 10.4, 13.3, 2.40, 2.35, 2.30),  # Fused cleanly into Ring 3 rear
        (0.18,  1.2,  9.2, 17.0, 2.55, 2.38, 2.30),  # Muscular rear arch
        (0.38,  1.5, 10.4, 21.2, 2.65, 2.35, 2.25),  # Rising powerfully with organic S-sway
        (0.60,  0.8, 13.6, 25.6, 2.65, 2.30, 2.20),  # Proud flared chest & tan belly scutes!
        (0.80,  0.2, 17.4, 29.6, 2.25, 2.15, 2.05),  # Sweeping forward into strike arch
        (0.92,  0.0, 19.6, 31.8, 1.95, 1.95, 1.85),  # Sleek narrow neck right behind broad head!
        (1.00,  0.0, 21.2, 32.5, 2.05, 1.95, 1.85),  # Skull occiput junction
    ]

    def interp_rear(kfs, u):
        for i in range(len(kfs) - 1):
            if kfs[i][0] <= u <= kfs[i + 1][0]:
                a, b = kfs[i], kfs[i + 1]
                f = (u - a[0]) / max(1e-6, b[0] - a[0])
                fs = f * f * (3.0 - 2.0 * f)
                return tuple(a[k] + (b[k] - a[k]) * fs for k in range(1, 7))
        return kfs[-1][1:]

    n_rear_steps = 110
    for i in range(n_rear_steps + 1):
        u = i / n_rear_steps
        dx_s, py, pz, rx, ry, rz = interp_rear(rear_keyframes, u)
        stamp_serpent_slice(cx + dx_s, py, pz, rx, ry, rz, arc_idx=250 + i, mode="rear", ground_flat=False)

    # Subtle crimson warlord scale accents on rearing neck flanks
    for z_mark in (22, 26):
        u_m = (z_mark - 13.3) / 19.2
        dx_s, py, pz, rx, ry, rz = interp_rear(rear_keyframes, min(1.0, max(0.0, u_m)))
        xm_l = int(round(cx + dx_s - rx + 0.5))
        xm_r = int(round(cx + dx_s + rx - 0.5))
        ym = int(round(py))
        if 0 <= xm_l < X and 0 <= ym < Y:
            grid[xm_l, ym, z_mark] = 7
        if 0 <= xm_r < X and 0 <= ym < Y:
            grid[xm_r, ym, z_mark] = 7

    # --- 3. SLEEK TRIANGULAR FANGED PIT-VIPER HEAD POISED TO STRIKE (Y: 20..37, Z: 25..36) ---
    # Classic flat, wide arrowhead pit-viper skull flaring sharply wider than the sleek neck!
    upper_head_slices = [
        # (y, x_off_max, z_bot, z_top)
        (20, 3, 32, 34),  # Neck-skull rear taper
        (21, 5, 32, 35),  # Dramatic flaring angular venom-gland cheeks!
        (22, 6, 32, 35),  # Widest triangular pit-viper arrowhead wing!
        (23, 6, 32, 35),  # Broad rear jaw corners
        (24, 5, 32, 35),  # Tapering smoothly toward eyes
        (25, 5, 32, 35),  # Behind eye sockets
        (26, 4, 32, 35),  # Eye sockets
        (27, 4, 32, 35),  # Overhanging brow & glowing amber eyes
        (28, 3, 32, 34),  # Narrowing viper snout bridge
        (29, 3, 32, 34),  # Upper jaw
        (30, 2, 32, 34),  # Upper fang sockets
        (31, 2, 32, 34),  # Forward snout
        (32, 1, 32, 34),  # Sharp triangular nose
        (33, 1, 32, 33),  # Upturned pit-viper snout tip!
        (34, 0, 33, 33),  # Crisp pointed snout apex
    ]
    for y, xmax, zb, zt in upper_head_slices:
        for dx in range(0, xmax + 1):
            for z in range(zb, zt + 1):
                # Bevel top outer corners for sleek flat viper crown
                if z == zt and dx == xmax and xmax >= 3:
                    continue
                if z == zb and dx < xmax and y >= 25:
                    col = 7  # Deep crimson inner upper palate
                elif z == zt and dx <= 1 and y in (22, 23, 25, 26, 28, 29):
                    col = 4  # Iconic dark charcoal mamushi V-chevron crown marking
                elif z >= zt - 1 and dx >= xmax - 1 and 22 <= y <= 25:
                    col = 3  # Rich rust-brown venom-gland temporal stripe
                elif z == zt and dx == 0 and y in (24, 27, 30):
                    col = 5  # Subtle bronze-gold crown ridge
                else:
                    col = mamushi_pattern(y * 1.1 + dx, z + dx * 0.8)
                fill_sym_box(grid, dx, dx, y, y, z, z, col)

    # Aggressive overhanging dark-olive & bronze-gold supraocular brow ridges!
    fill_sym_box(grid, 3, 4, 25, 28, 35, 35, 4)  # Dark brow ridge
    fill_sym_box(grid, 3, 3, 25, 27, 36, 36, 5)  # Bronze-gold warlord viper brow crest!

    # FIERCE GLOWING AMBER VIPER SLIT EYES (8)
    fill_sym_box(grid, 4, 4, 26, 28, 33, 34, 4)  # Dark recessed eye socket
    fill_sym_box(grid, 4, 4, 27, 28, 33, 33, 8)  # Bright glowing amber slit eye!
    fill_sym_box(grid, 4, 4, 27, 27, 34, 34, 8)  # Upper glowing amber iris
    # Heat-sensing loreal pit on snout side
    fill_sym_box(grid, 2, 2, 30, 30, 33, 33, 4)

    # TWIN RAZOR-SHARP CURVED IVORY VENOM FANGS (6) hanging cleanly over the wide-open crimson maw!
    fill_sym_box(grid, 2, 2, 31, 31, 31, 32, 6)  # Fang root emerging cleanly from upper jaw
    fill_sym_box(grid, 2, 2, 30, 31, 30, 30, 6)  # Slightly backward-curving fang shaft
    fill_sym_box(grid, 2, 2, 30, 30, 28, 29, 6)  # Razor-sharp 1-voxel-wide venom fang tip!

    # WIDE-OPEN STRIKING LOWER JAW (Z: 25..31) — wide vertical gap so fangs pop starkly!
    # Rear jaw hinge solidly fused to skull venom-gland cheeks
    fill_sym_box(grid, 3, 5, 22, 24, 30, 32, 4)
    fill_sym_box(grid, 4, 5, 22, 23, 29, 31, 1)
    # Deep crimson inner throat cavity
    fill_sym_box(grid, 0, 2, 22, 25, 28, 31, 7)
    fill_sym_box(grid, 0, 2, 24, 26, 27, 29, 7)

    # Sleek open lower mandible angling downward & forward to Y=31, Z=25..26
    lower_jaw_slices = [
        (24, 4, 28, 29),
        (25, 4, 27, 28),
        (26, 3, 26, 27),
        (27, 3, 26, 27),
        (28, 2, 25, 26),
        (29, 2, 25, 26),
        (30, 1, 25, 26),
        (31, 1, 25, 26),
    ]
    for y, xmax, zb, zt in lower_jaw_slices:
        fill_sym_box(grid, 0, xmax, y, y, zb, zb, 2)  # Earthy-tan chin scales underneath
        fill_sym_box(grid, xmax, xmax, y, y, zb, zt, 1 if (y % 2 == 0) else 4)
        if xmax >= 1:
            fill_sym_box(grid, 0, xmax - 1, y, y, zt, zt, 7)  # Crimson inner mouth floor

    # SLEEK FORKED CRIMSON TONGUE (7) flicking gracefully out of the open fanged maw!
    # 100% 6-connected with a crisp unmistakable V-fork!
    fill_sym_box(grid, 0, 0, 26, 32, 26, 26, 7)  # Anchored along mouth floor
    fill_sym_box(grid, 0, 0, 32, 34, 26, 27, 7)  # Extending out & slightly up
    # Crisp 1-voxel-thin V-fork branches (every step shares a face!)
    fill_sym_box(grid, 0, 1, 34, 34, 27, 27, 7)  # Fork split (face-connected along X)
    fill_sym_box(grid, 1, 1, 34, 35, 27, 27, 7)  # Mid-prong
    fill_sym_box(grid, 1, 2, 35, 35, 27, 27, 7)  # Outer flare
    fill_sym_box(grid, 2, 2, 35, 37, 27, 28, 7)  # Sharp upturned forked crimson tongue tips!

    # Hollow strictly interior bulk of thick coils & rearing torso to stay neatly in budget
    hollow_interior_26(grid, 1, Z - 2)
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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=32, pitch_a=20, yaw_b=38, pitch_b=22):
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
    c_a = count_components_6(model_a)
    c_b = count_components_6(model_b)
    v_a = export_vox(model_a, "dosan_a.vox")
    v_b = export_vox(model_b, "dosan_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SAITO DOSAN ROBOT -> GIANT MOTTLED VIPER",
        "1. SAITO DOSAN ROBOT (VIPER OF MINO)",
        "2. GIANT MOTTLED VIPER (MAMUSHI)",
        "preview_dosan.png",
        yaw_a=32, pitch_a=20, yaw_b=38, pitch_b=22,
    )
    print(f"dosan: A={v_a} voxels {model_a.shape} (comps={c_a}), B={v_b} voxels {model_b.shape} (comps={c_b})")
