import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across Tokugawa Ieyasu Shogun Robot & Armored Tanuki
PALETTE = {
    1: (132, 76, 44, 255),    # Rich Chestnut Brown (Primary Armor / Tanuki Main Fur)
    2: (168, 108, 66, 255),   # Warm Tawny Chestnut Highlight (Fur Ridge / Armor Bevels)
    3: (64, 38, 24, 255),     # Deep Espresso Dark-Brown (Tanuki Mask, Ear Tips, Tail Stripes / Kabuto)
    4: (240, 194, 52, 255),   # Gleaming Kin-dami Gold (Shida Fern Crest, Gold Armor, Gunbai)
    5: (184, 134, 34, 255),   # Burnished Antique Gold (Ornate Borders & Recessed Gold Trim)
    6: (242, 226, 190, 255),  # Warm Cream Ivory (Plump Belly Plate, Tanuki Muzzle/Cheeks, Blade Edge)
    7: (46, 44, 42, 255),     # Dark Bronze-Charcoal (Inner Frame, Joints, Menpo, Nose & Claws)
    8: (182, 42, 36, 255),    # Deep Shogun Crimson (Armor Lacing, Tassels, Ceremonial Collar Cord)
    9: (76, 232, 168, 255),   # Luminous Aoi Jade-Emerald Glow (Robot & Tanuki Eyes / Emblem Gem)
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


def count_components_6(grid):
    """Return number of 6-connected occupied components in the voxel grid."""
    X, Y, Z = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    comps = 0
    xs, ys, zs = np.nonzero(grid)
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


# ============================================================
# FORM A: TOKUGAWA IEYASU SHOGUN ROBOT (42 x 26 x 45)
# Heavy, broad-shouldered, stately chestnut & Kin-dami gold
# shogun robot with iconic Shida fern-leaf crest, rounded
# cream armored belly, massive stable legs, gold gunbai fan &
# ceremonial samurai tachi sword.
# ============================================================
def build_a():
    grid = np.zeros((42, 26, 45), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 20 (-X, robot left / viewer's right)
    cx_r = X // 2      # 21 (+X, robot right / viewer's left)

    # --- MASSIVE STABLE FEET / ARMORED BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 2, 6, 7, 16, 0, 1, 7)    # Heavy dark bronze-charcoal soles
    fill_sym_box(grid, 3, 5, 6, 7, 0, 2, 3)     # Espresso heel counterweight
    fill_sym_box(grid, 2, 6, 8, 16, 1, 2, 1)    # Rich chestnut armored boot body
    fill_sym_box(grid, 3, 5, 16, 17, 0, 2, 3)   # Dark espresso armored toe guard
    fill_sym_box(grid, 3, 5, 16, 17, 2, 2, 4)   # Gleaming Kin-dami gold toe trim
    fill_sym_box(grid, 2, 6, 9, 15, 3, 3, 3)    # Dark espresso ankle guard
    fill_sym_box(grid, 3, 5, 14, 15, 3, 3, 4)   # Front gold ankle buckle
    fill_sym_box(grid, 3, 5, 9, 14, 3, 4, 7)    # Dark mechanical ankle joint

    # --- MASSIVE STABLE LOWER LEGS / SUNEATE GREAVES (Z: 4..14) ---
    # Rich chestnut-brown dominant armor with crisp gold bands & crimson lacing!
    fill_sym_box(grid, 2, 6, 8, 14, 4, 13, 1)   # Broad rich chestnut shin armor
    fill_sym_box(grid, 3, 5, 14, 15, 5, 11, 1)  # Chestnut front shin ridge
    fill_sym_box(grid, 4, 4, 15, 15, 5, 11, 2)  # Subtle tawny center bevel
    # Horizontal gold shin bands & crimson odoshi cord accents (balanced chestnut vs gold)
    fill_sym_box(grid, 2, 6, 8, 15, 6, 6, 5)    # Lower burnished gold band
    fill_sym_box(grid, 2, 6, 9, 15, 7, 7, 8)    # Crimson lacing band
    fill_sym_box(grid, 2, 6, 8, 15, 10, 10, 4)  # Upper Kin-dami gold band
    fill_sym_box(grid, 2, 2, 9, 13, 5, 13, 7)   # Inner leg dark charcoal frame
    fill_sym_box(grid, 6, 6, 9, 13, 5, 12, 3)   # Outer dark-brown greave trim
    # Rear calf armor detail
    fill_sym_box(grid, 3, 5, 7, 8, 5, 11, 3)
    fill_sym_box(grid, 4, 4, 7, 7, 7, 10, 4)
    # Ornate Tateage Knee Guards (chestnut base + gleaming gold knee crest!)
    fill_sym_box(grid, 2, 6, 14, 15, 11, 14, 3)
    fill_sym_box(grid, 3, 5, 15, 16, 12, 14, 4)
    fill_sym_box(grid, 4, 4, 16, 16, 13, 14, 5)
    fill_sym_box(grid, 3, 5, 14, 15, 15, 15, 4)
    fill_sym_box(grid, 3, 5, 15, 15, 11, 11, 8)  # Crimson knee tie cord

    # --- STURDY THIGHS & HEAVY KUSAZURI TASSETS (Z: 14..21) ---
    fill_sym_box(grid, 2, 5, 9, 14, 14, 19, 7)  # Dark charcoal hip/thigh core
    fill_sym_box(grid, 2, 5, 11, 14, 15, 18, 3)  # Dark-brown armored haidate thigh plates
    fill_sym_box(grid, 3, 4, 14, 15, 16, 17, 1)  # Chestnut thigh plate
    # Heavy Pelvis & Flared Layered Kusazuri Tasset Skirt (Z: 16..20)
    fill_sym_box(grid, 0, 6, 8, 15, 18, 20, 1)  # Chestnut hip block
    # Front tassets (rich chestnut panels, crimson lacing, gleaming gold hem!)
    fill_sym_box(grid, 2, 5, 15, 16, 16, 19, 1)
    fill_sym_box(grid, 2, 5, 16, 16, 18, 18, 3)
    fill_sym_box(grid, 2, 5, 16, 16, 17, 17, 8)  # Crimson lacing
    fill_sym_box(grid, 2, 5, 15, 16, 16, 16, 4)  # Gold lower skirt hem
    # Side tassets (wide stately silhouette)
    fill_sym_box(grid, 6, 7, 9, 14, 16, 19, 1)
    fill_sym_box(grid, 7, 7, 9, 14, 17, 17, 8)
    fill_sym_box(grid, 6, 7, 9, 14, 16, 16, 4)
    # Rear tassets
    fill_sym_box(grid, 0, 5, 7, 8, 16, 19, 1)
    fill_sym_box(grid, 0, 5, 7, 7, 17, 17, 8)
    fill_sym_box(grid, 0, 5, 7, 8, 16, 16, 4)
    # Center front groin tasset & Tokugawa gold belt buckle
    fill_sym_box(grid, 0, 1, 15, 17, 17, 20, 3)
    fill_sym_box(grid, 0, 1, 16, 17, 19, 20, 4)
    fill_sym_box(grid, 0, 1, 17, 17, 17, 18, 8)
    fill_sym_box(grid, 0, 0, 17, 17, 19, 20, 9)  # Small Aoi jade belt gem

    # --- WIDE HEAVY SHOGUN TORSO WITH ROUNDED CREAM ARMORED BELLY (Z: 20..32) ---
    # Core broad torso shell (rich chestnut brown dominant)
    fill_sym_box(grid, 0, 6, 8, 15, 20, 31, 1)
    fill_sym_box(grid, 0, 7, 9, 14, 22, 30, 1)
    # Crimson waist sash / obi framing the lower belly
    fill_sym_box(grid, 0, 6, 14, 16, 20, 20, 8)
    fill_sym_box(grid, 0, 5, 15, 17, 20, 20, 5)  # Burnished gold belt rim

    # ROUNDED ARMORED CREAM BELLY PLATE (丸い腹, Z: 21..26, Y: 14..18)
    # Smooth convex curved warm cream belly framed by chestnut flanks & Kin-dami gold border!
    belly_rows = [
        # (z, x_cream_max, y_front, x_gold_rim)
        (21, 3, 17, 5),
        (22, 4, 18, 5),
        (23, 4, 18, 6),
        (24, 4, 18, 6),
        (25, 3, 17, 5),
        (26, 2, 17, 4),
    ]
    for bz, x_cr, yf, x_gr in belly_rows:
        # Chestnut side flanks + crisp gold armor border around the cream belly
        fill_sym_box(grid, 0, x_gr, 14, yf - 1, bz, bz, 3)
        fill_sym_box(grid, x_cr + 1, x_gr, 15, yf - 1, bz, bz, 4)
        # Plump warm cream rounded belly plate bulging out cleanly
        fill_sym_box(grid, 0, x_cr, 15, yf, bz, bz, 6)
    # Crisp Kin-dami gold rim outlining top/bottom/sides of the rounded cream belly
    fill_sym_box(grid, 0, 3, 17, 18, 21, 21, 4)
    fill_sym_box(grid, 0, 3, 17, 17, 26, 26, 4)
    fill_sym_box(grid, 4, 4, 17, 17, 22, 25, 5)
    # Rich chestnut/espresso armored ribs along the wide flanks
    fill_sym_box(grid, 6, 7, 10, 15, 22, 25, 1)
    fill_sym_box(grid, 7, 7, 11, 14, 23, 24, 5)

    # IMPOSING UPPER CHEST / CHESTNUT & KIN-DAMI GOLD BREASTPLATE (Z: 27..32)
    fill_sym_box(grid, 0, 7, 9, 16, 27, 31, 1)   # Broad heavy rich chestnut chest!
    fill_sym_box(grid, 0, 6, 15, 17, 27, 31, 1)  # Chestnut breastplate body
    # Gleaming Kin-dami gold chest framing (high contrast against rich chestnut!)
    fill_sym_box(grid, 0, 6, 16, 17, 27, 27, 4)  # Lower gold pectoral trim
    fill_sym_box(grid, 0, 6, 16, 17, 31, 31, 4)  # Upper gold collar trim
    fill_sym_box(grid, 5, 6, 16, 17, 27, 31, 4)  # Outer gold pectoral borders
    # Dark espresso center medallion recess & gleaming golden Mitsuba-aoi crest!
    fill_sym_box(grid, 0, 2, 17, 17, 28, 30, 3)
    fill_sym_box(grid, 0, 1, 18, 18, 28, 30, 4)  # Gold circular Tokugawa crest boss
    fill_sym_box(grid, 0, 0, 18, 18, 29, 29, 9)  # Luminous Aoi jade center jewel
    # Crimson samurai chest cords (odoshi) flanking the gold medallion
    fill_sym_box(grid, 3, 4, 17, 17, 28, 28, 8)
    fill_sym_box(grid, 3, 4, 17, 17, 30, 30, 8)
    # Heavy Shogun Collar / Throat Guard (Nodowa)
    fill_sym_box(grid, 0, 5, 9, 15, 32, 32, 3)
    fill_sym_box(grid, 0, 4, 14, 16, 31, 32, 4)
    fill_sym_box(grid, 0, 2, 16, 16, 31, 32, 8)

    # --- BACKPACK WITH FOLDED STRIPED TANUKI TAIL (Y: 2..8, Z: 19..32) ---
    fill_sym_box(grid, 0, 5, 5, 8, 21, 31, 1)    # Heavy chestnut armored back housing
    fill_sym_box(grid, 3, 5, 4, 6, 23, 30, 3)    # Espresso recessed side pods
    fill_sym_box(grid, 3, 5, 4, 5, 29, 30, 4)    # Upper gold trim caps
    fill_sym_box(grid, 3, 5, 4, 5, 23, 24, 4)    # Lower gold trim caps
    fill_sym_box(grid, 2, 4, 4, 4, 28, 29, 8)    # Crimson samurai agemaki back cords!
    fill_sym_box(grid, 3, 3, 3, 4, 27, 28, 8)
    # Prominent Folded Bushy Striped Tanuki Tail tucked cleanly down center of backpack!
    tail_pack = [
        (29, 1, 4, 2),
        (28, 2, 3, 3),  # Bold dark stripe
        (27, 2, 3, 1),  # Chestnut
        (26, 2, 2, 2),  # Tawny
        (25, 2, 2, 3),  # Bold dark stripe
        (24, 2, 2, 1),  # Chestnut
        (23, 2, 2, 3),  # Bold dark stripe
        (22, 2, 3, 1),  # Chestnut
        (21, 1, 3, 3),  # Dark tail tip
        (20, 1, 4, 3),
    ]
    for tz, tw, ty_back, tcol in tail_pack:
        fill_sym_box(grid, 0, tw, ty_back, 6, tz, tz, tcol)

    # --- MASSIVE TIERED SHOGUN O-SODE SHOULDER PAULDRONS (x_off: 7..13, Z: 25..34) ---
    fill_sym_box(grid, 6, 9, 10, 14, 27, 31, 7)   # Heavy dark charcoal shoulder axle
    # Multi-tiered broad samurai o-sode shoulder shields (rich chestnut + gleaming gold trim!)
    sode_tiers = [
        # (z, x0, x1, y0, y1, col)
        (34, 8,  10, 10, 14, 4),  # Top gleaming gold shoulder crest
        (33, 7,  11, 9,  15, 3),  # Espresso upper shoulder cap
        (32, 7,  12, 8,  15, 1),  # Wide chestnut plate
        (31, 7,  12, 8,  15, 4),  # Gleaming Kin-dami gold band
        (30, 8,  13, 8,  15, 1),  # Widest chestnut o-sode tier
        (29, 8,  13, 8,  15, 8),  # Crimson odoshi lacing tier
        (28, 9,  13, 8,  15, 1),  # Chestnut lower plate
        (27, 9,  13, 9,  15, 3),  # Espresso lower trim
        (26, 10, 13, 9,  14, 4),  # Gleaming gold bottom flare edge
    ]
    for sz, sx0, sx1, sy0, sy1, scol in sode_tiers:
        fill_sym_box(grid, sx0, sx1, sy0, sy1, sz, sz, scol)
    # Crisp front/rear gold framing on o-sode pauldrons
    fill_sym_box(grid, 11, 13, 15, 15, 27, 31, 4)
    fill_sym_box(grid, 11, 13, 8, 8, 27, 31, 5)
    fill_sym_box(grid, 13, 13, 10, 13, 28, 30, 4)  # Outer gold boss

    # --- HEAVY ARMS & KOTE GAUNTLETS (Z: 14..27) ---
    # Upper arms descending inside the pauldrons
    fill_sym_box(grid, 8, 10, 10, 13, 21, 27, 7)
    fill_sym_box(grid, 8, 10, 10, 13, 23, 25, 3)
    # Thick armored forearms / kote gauntlets (rich chestnut + gold trim)
    fill_sym_box(grid, 8, 11, 10, 14, 16, 21, 1)
    fill_sym_box(grid, 11, 11, 10, 14, 17, 20, 3)  # Outer dark-brown gauntlet guard
    fill_sym_box(grid, 11, 11, 11, 13, 18, 19, 4)  # Gold gauntlet boss
    fill_sym_box(grid, 9, 10, 14, 14, 17, 20, 2)   # Front tawny bevel
    fill_sym_box(grid, 8, 11, 10, 14, 16, 16, 4)   # Gold wrist cuff
    # Heavy fists (slightly forward for weapon grip)
    fill_sym_box(grid, 8, 10, 11, 15, 14, 16, 7)
    fill_sym_box(grid, 8, 10, 14, 15, 15, 16, 3)

    # --- RIGHT HAND (+X, viewer's left): CEREMONIAL GOLDEN GUNBAI WAR FAN (軍配) ---
    # Extended boldly OUTWARD (+X) & FORWARD (+Y) so the iconic gourd-shaped Tokugawa war fan
    # stands out cleanly against the dark background with zero overlap against the torso!
    # Extended armored wrist/grip bridge reaching outward
    fill_box(grid, cx_r + 10, cx_r + 13, 14, 16, 15, 16, 7)  # Right hand extending outward
    fill_box(grid, cx_r + 12, cx_r + 13, 15, 16, 11, 19, 7)  # Dark lacquered Gunbai handle
    fill_box(grid, cx_r + 12, cx_r + 13, 15, 16, 12, 13, 4)  # Gold pommel collar
    # Hanging crimson tassel beneath handle (6-connected!)
    fill_box(grid, cx_r + 12, cx_r + 13, 15, 16, 9, 11, 8)
    fill_box(grid, cx_r + 13, cx_r + 13, 16, 16, 8, 9, 8)
    # Angled gourd/paddle-shaped Gunbai war fan head held cleanly out to the side (x = cx_r+12..19)
    gunbai_rows = [
        # (z, x_start, x_end, y_base)
        (18, 13, 15, 16),
        (19, 12, 17, 17),
        (20, 12, 18, 17),
        (21, 12, 18, 17),
        (22, 13, 17, 17),  # Classic gourd waist pinch!
        (23, 13, 17, 17),
        (24, 12, 18, 17),  # Upper wide gourd lobe!
        (25, 12, 18, 17),
        (26, 13, 17, 17),
        (27, 14, 16, 17),
    ]
    for gz, gx0, gx1, gy in gunbai_rows:
        for gx in range(gx0, gx1 + 1):
            is_edge = (gx in (gx0, gx1) or gz in (18, 27))
            col = 4 if is_edge else 3  # Gleaming Kin-dami gold rim around dark espresso lacquer face!
            fill_box(grid, cx_r + gx, cx_r + gx, gy, gy + 1, gz, gz, col)
    # Gleaming Kin-dami gold central rib & Tokugawa sun/aoi emblem on Gunbai face!
    fill_box(grid, cx_r + 15, cx_r + 15, 17, 19, 19, 26, 4)
    fill_box(grid, cx_r + 14, cx_r + 16, 18, 18, 24, 25, 4)
    fill_box(grid, cx_r + 15, cx_r + 15, 18, 19, 24, 25, 8)  # Crimson sun-disc accent on fan!
    fill_box(grid, cx_r + 15, cx_r + 15, 17, 18, 28, 28, 4)  # Top gold finial

    # --- LEFT HAND (-X, viewer's right): CEREMONIAL SAMURAI TACHI / KATANA SWORD ---
    # Held cleanly forward & angled upward-outward, completely clear of the left shoulder!
    fill_box(grid, cx_l - 10, cx_l - 9, 13, 16, 14, 15, 8)   # Crimson tsuka hilt inside fist
    fill_box(grid, cx_l - 10, cx_l - 9, 12, 13, 13, 14, 4)   # Gold kashira pommel
    fill_box(grid, cx_l - 11, cx_l - 9, 16, 17, 14, 16, 4)   # Gleaming gold round tsuba handguard
    # Sweeping upright-forward samurai katana blade (stepped with face-overlap for 100% 6-connectivity!)
    blade_segs = [
        # (x_off, y0, y1, z0, z1)
        (10, 17, 18, 15, 17),
        (11, 17, 19, 17, 19),
        (11, 18, 20, 19, 21),
        (12, 18, 20, 21, 23),
        (12, 19, 21, 23, 25),
        (13, 19, 21, 25, 27),
        (13, 19, 21, 27, 29),
        (14, 19, 20, 29, 31),
        (14, 19, 20, 31, 32),
    ]
    for bx_off, by0, by1, bz0, bz1 in blade_segs:
        fill_box(grid, cx_l - bx_off, cx_l - bx_off, by0, by0, bz0, bz1, 7)
        fill_box(grid, cx_l - bx_off, cx_l - bx_off, by0 + 1, by1, bz0, bz1, 6)
    fill_box(grid, cx_l - 10, cx_l - 10, 17, 18, 15, 16, 4)  # Gold habaki blade collar

    # --- HEAD: ICONIC TOKUGAWA IEYASU SHIDA-GUSOKU KABUTO (Z: 32..44) ---
    fill_sym_box(grid, 0, 2, 10, 13, 32, 33, 7)   # Sturdy neck
    # Main Kabuto helmet bowl (Hachi) in deep espresso brown & chestnut
    fill_sym_box(grid, 0, 3, 9, 15, 34, 38, 3)
    fill_sym_box(grid, 0, 2, 9, 14, 39, 40, 3)    # Taller stately kabuto dome
    fill_sym_box(grid, 0, 1, 10, 13, 40, 41, 1)   # Chestnut crown dome
    fill_sym_box(grid, 0, 0, 11, 12, 41, 41, 4)   # Golden tehen finial ring
    # Flared Samurai Shikoro neck-guard plates sweeping around sides & rear
    fill_sym_box(grid, 3, 4, 8, 13, 34, 36, 1)
    fill_sym_box(grid, 4, 5, 8, 12, 33, 34, 1)
    fill_sym_box(grid, 4, 5, 8, 12, 33, 33, 4)    # Gold shikoro hem
    fill_sym_box(grid, 0, 4, 7, 8, 33, 36, 1)     # Rear shikoro drape
    fill_sym_box(grid, 0, 4, 7, 7, 34, 34, 8)     # Rear crimson lacing
    fill_sym_box(grid, 0, 4, 7, 8, 33, 33, 4)     # Rear gold hem
    # Golden Fukigaeshi ear-flaps framing the face
    fill_sym_box(grid, 3, 4, 13, 15, 35, 37, 4)
    fill_sym_box(grid, 4, 4, 14, 15, 36, 36, 8)
    # Samurai Menpo face mask & fierce glowing Aoi jade eyes!
    fill_sym_box(grid, 0, 2, 15, 16, 34, 35, 7)   # Dark charcoal armored menpo jaw
    fill_sym_box(grid, 0, 1, 16, 16, 34, 34, 4)   # Gold chin guard / samurai mustache trim
    fill_sym_box(grid, 0, 2, 15, 16, 36, 36, 7)   # Eye recess shadow
    fill_sym_box(grid, 1, 2, 16, 16, 36, 36, 9)   # Glowing Aoi jade samurai eyes!
    fill_sym_box(grid, 0, 3, 15, 16, 37, 37, 4)   # Gleaming Kin-dami gold brow visor (mabizashi)

    # ICONIC GOLDEN SHIDA FERN-LEAF KABUTO CREST (歯朶前立, Z: 37..44, Y: 16)
    # Crisp, thin (1-voxel-deep blades), wide-sweeping golden fern-leaf fronds with serrated pinnae!
    fill_sym_box(grid, 0, 1, 16, 17, 37, 38, 4)   # Central golden sun-orb mount on brow
    fill_sym_box(grid, 0, 0, 17, 17, 38, 38, 8)   # Crimson lacquer heart dot on crest mount
    # Sweeping thin golden fern arch with rhythmic serrated fern-leaf notches!
    fern_segs = [
        # Main sweeping golden fern stem (1 voxel thick in Y=16 for crisp blade silhouette!)
        (1, 2, 16, 16, 38, 39, 4),
        (2, 3, 16, 16, 39, 40, 4),
        (3, 4, 16, 16, 40, 41, 4),
        (4, 5, 16, 16, 41, 42, 4),
        (5, 6, 16, 16, 42, 43, 4),
        (6, 7, 16, 16, 43, 44, 4),  # Graceful high outer sweeping fern tip!
        # Distinct serrated fern-leaf pinnae (frond leaflets) along top & outer arch
        (2, 2, 16, 16, 41, 41, 5),  # Inner leaflet 1
        (3, 3, 16, 16, 42, 42, 4),  # Inner leaflet 2
        (4, 4, 16, 16, 43, 43, 5),  # Upper leaflet 3
        (5, 5, 16, 16, 44, 44, 4),  # Peak leaflet 4
        (5, 6, 16, 16, 40, 40, 5),  # Lower outer fern barb
        (7, 8, 16, 16, 42, 42, 5),  # Lower sweeping tip barb
    ]
    for fx0, fx1, fy0, fy1, fz0, fz1, fcol in fern_segs:
        fill_sym_box(grid, fx0, fx1, fy0, fy1, fz0, fz1, fcol)

    # Hollow strictly interior bulk while preserving 100% 6-connectivity
    hollow_interior_26(grid, 1, 41)

    return grid


# ============================================================
# FORM B: ARMORED TANUKI / JAPANESE RACCOON DOG (26 x 42 x 26)
# Expressive, sturdy Japanese raccoon dog with rich chestnut fur,
# iconic dark-brown eye-mask patches, pointed muzzle, round
# dark-tipped ears, plump round cream-and-gold belly, lush bushy
# dark-striped tail, and sleek golden shoulder & forehead armor.
# ============================================================
def build_b():
    grid = np.zeros((26, 42, 26), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 12.5

    # --- FOUR STURDY DARK-PAWED TANUKI LEGS WITH GOLD ANKLE CUFFS (Z: 0..10) ---
    leg_specs = [
        # (leg_cy, x_off_center, is_front)
        (26.5, 4.4, True),
        (15.5, 4.7, False),
    ]
    for leg_cy, x_off_c, is_front in leg_specs:
        for z in range(0, 11):
            if z <= 1:
                rx_l, ry_l = 1.9, 2.3
                y_shift = 0.5
            elif z <= 5:
                rx_l, ry_l = 1.6, 1.8
                y_shift = 0.0
            else:
                rx_l, ry_l = 2.1, 2.3
                y_shift = -0.3 if is_front else 0.2
            for sign in (-1, 1):
                lcx = cx + sign * x_off_c
                lcy = leg_cy + y_shift
                for x in range(int(lcx - 3), int(lcx + 4)):
                    for y in range(int(lcy - 3), int(lcy + 4)):
                        if 0 <= x < X and 0 <= y < Y:
                            if ((x - lcx) / rx_l) ** 2 + ((y - lcy) / ry_l) ** 2 <= 1.0:
                                if z <= 3:
                                    col = 3  # Iconic dark-brown tanuki paws & lower legs!
                                elif z == 4:
                                    col = 4  # Sleek carried-over Kin-dami gold ankle band!
                                else:
                                    col = 1  # Rich chestnut upper legs/haunches
                                grid[x, y, z] = col
        # Dark charcoal claws at front (+Y) of each paw
        claw_y = int(round(leg_cy + 2.8))
        fill_sym_box(grid, 3, 3, claw_y, claw_y, 0, 0, 7)
        fill_sym_box(grid, 5, 5, claw_y, claw_y, 0, 0, 7)

    # --- PLUMP ROUNDED TANUKI BODY & ICONIC CREAM-AND-GOLD BELLY (Y: 12..30, Z: 3..18) ---
    # Generously rounded barrel body with plump low-hanging cream belly (丸い腹) and sleek gold trim!
    body_slices = [
        # (y, rx, z_bot, z_top)
        (12, 4.4, 8,  14),
        (13, 5.6, 7,  15),
        (14, 6.4, 6,  16),
        (15, 7.0, 5,  17),
        (16, 7.5, 4,  17),
        (17, 7.9, 4,  18),
        (18, 8.2, 3,  18),
        (19, 8.4, 3,  18),  # Peak plump round tanuki belly width & low belly curve!
        (20, 8.4, 3,  18),
        (21, 8.2, 3,  18),
        (22, 7.9, 4,  18),
        (23, 7.5, 4,  18),
        (24, 7.0, 5,  18),
        (25, 6.5, 5,  18),
        (26, 6.0, 6,  18),
        (27, 5.4, 6,  17),
        (28, 4.8, 7,  17),
        (29, 4.0, 8,  16),
        (30, 3.0, 9,  15),
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
                    # Smooth curved belly border arching gently up toward the proud chest
                    t_chest = max(0.0, (y - 23) / 6.0)
                    belly_line_z = 9.0 + 2.4 * t_chest - 0.12 * max(0, 17 - y)
                    if z <= belly_line_z - 0.8 and y >= 15:
                        col = 6  # Plump warm cream belly (丸い腹)!
                    elif abs(z - belly_line_z) <= 0.65 and 16 <= y <= 29:
                        # Clean sleek Kin-dami gold armor trim arching along the belly rim!
                        col = 4
                    elif z >= zt - 1 and dx <= 1.6 and 14 <= y <= 26:
                        col = 3  # Classic dark-brown tanuki dorsal fur stripe along spine!
                    elif z >= zt - 2 and dx <= rx * 0.62:
                        col = 2  # Warm tawny chestnut fur highlight across upper back
                    else:
                        col = 1  # Rich chestnut brown fur
                    grid[x, y, z] = col

    # Plump warm cream front chest bib & ceremonial crimson collar + gold Aoi pendant!
    fill_sym_box(grid, 0, 3, 29, 30, 9, 13, 6)    # Proud cream chest fur
    fill_sym_box(grid, 0, 2, 30, 31, 10, 12, 6)
    fill_sym_box(grid, 0, 4, 28, 30, 14, 14, 8)   # Crimson ceremonial collar cord!
    fill_sym_box(grid, 0, 1, 30, 31, 13, 14, 4)   # Gleaming Kin-dami gold collar medallion!
    fill_sym_box(grid, 0, 0, 31, 31, 13, 13, 9)   # Tiny Aoi jade jewel on collar

    # --- SLEEK CONTOURED GOLDEN SHOULDER ARMOR PLATES (Carried over from Robot O-Sode) ---
    # Hugs the tanuki's sturdy shoulders organically (chestnut plate center + gold rim + crimson lacing)
    pauldron_rows = [
        # (z, x_off0, x_off1, y0, y1, col)
        (16, 5, 6, 23, 27, 4),  # Sleek upper gold shoulder trim
        (15, 6, 7, 23, 28, 1),  # Rich chestnut armor plate center
        (14, 6, 7, 23, 28, 8),  # Crimson odoshi lacing line!
        (13, 6, 7, 23, 27, 4),  # Lower gleaming gold pauldron rim
    ]
    for pz, px0, px1, py0, py1, pcol in pauldron_rows:
        fill_sym_box(grid, px0, px1, py0, py1, pz, pz, pcol)
    # Front/rear gold edges on the sleek shoulder plates
    fill_sym_box(grid, 6, 7, 28, 28, 13, 15, 4)
    fill_sym_box(grid, 6, 7, 23, 23, 13, 15, 5)
    # Subtle golden saddle trim ridge across middle back
    fill_sym_box(grid, 2, 4, 19, 22, 18, 18, 4)
    fill_sym_box(grid, 3, 4, 20, 21, 18, 18, 8)  # Crimson back cord detail

    # --- EXPRESSIVE TANUKI HEAD (Y: 28..40, Z: 13..24) ---
    # Thick fluffy chestnut neck merging cleanly into shoulders
    fill_sym_box(grid, 0, 3, 27, 30, 13, 18, 1)
    fill_sym_box(grid, 0, 2, 28, 30, 18, 19, 2)

    # Rounded fluffy-cheeked Tanuki head slices
    head_slices = [
        # (y, rx, zb, zt)
        (29, 4.4, 14, 20),
        (30, 5.1, 14, 21),
        (31, 5.7, 13, 21),
        (32, 6.0, 13, 22),  # Wide adorable fluffy tanuki cheeks!
        (33, 5.7, 13, 22),
        (34, 5.1, 14, 21),
        (35, 4.3, 14, 21),
        (36, 3.3, 15, 20),
    ]
    for y, rx, zb, zt in head_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.3
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    if z <= zb + 2 and y >= 31:
                        col = 6  # Fluffy warm cream tanuki cheeks & chin!
                    elif z >= zt - 1 and dx <= 2.6:
                        col = 2  # Warm tawny chestnut crown
                    else:
                        col = 1  # Rich chestnut head fur
                    grid[x, y, z] = col

    # ICONIC DARK-BROWN TANUKI EYE-MASK PATCHES (狸の顔)!
    # Bold deep espresso oval patches wrapping cleanly around expressive bright eyes!
    fill_sym_box(grid, 1, 4, 33, 35, 16, 19, 3)   # Broad dark-brown eye mask wrap
    fill_sym_box(grid, 1, 3, 35, 36, 17, 19, 3)   # Forward face mask plane
    fill_sym_box(grid, 2, 4, 32, 34, 16, 18, 3)   # Cheek-side mask flare
    # Crisp warm cream nose-bridge stripe separating the two dark eye masks
    fill_sym_box(grid, 0, 0, 35, 37, 16, 19, 6)
    # Expressive bright glowing Aoi jade eyes visible from BOTH front & 3/4 side!
    fill_sym_box(grid, 2, 3, 35, 36, 17, 18, 9)   # Bright glowing eyes inside dark mask
    fill_sym_box(grid, 3, 3, 35, 35, 18, 18, 3)   # Soft rounded upper mask brow
    fill_sym_box(grid, 2, 2, 36, 36, 18, 18, 7)   # Crisp dark pupil accent

    # POINTED TANUKI MUZZLE & DARK CHARCOAL NOSE TIP (Y: 36..41, Z: 14..17)
    fill_sym_box(grid, 0, 2, 36, 37, 15, 17, 6)   # Cream muzzle base
    fill_sym_box(grid, 0, 1, 37, 39, 15, 17, 6)   # Tapered cream snout
    fill_sym_box(grid, 0, 1, 37, 39, 17, 17, 2)   # Tawny upper snout bridge
    fill_sym_box(grid, 0, 0, 39, 40, 15, 16, 6)   # Pointed muzzle tip
    fill_sym_box(grid, 0, 0, 40, 41, 16, 16, 7)   # Crisp dark charcoal button nose!
    fill_sym_box(grid, 0, 1, 37, 38, 14, 14, 3)   # Cute dark-brown mouth / lower lip line

    # ROUND DARK-TIPPED TANUKI EARS (x_off: 3..5, Y: 30..33, Z: 20..24)
    # Unmistakably rounded ears set cleanly on both sides of the chestnut crown!
    fill_sym_box(grid, 3, 5, 30, 32, 20, 22, 1)   # Chestnut ear base
    fill_sym_box(grid, 3, 5, 31, 32, 23, 23, 3)   # Rounded dark-brown upper rim
    fill_sym_box(grid, 4, 4, 31, 32, 24, 24, 3)   # Rounded dark-brown ear tip!
    fill_sym_box(grid, 5, 5, 31, 32, 21, 22, 3)   # Outer dark-brown rim
    fill_sym_box(grid, 3, 4, 32, 33, 21, 22, 6)   # Warm cream inner ear pocket facing +Y!

    # SLEEK GOLDEN FOREHEAD TIARA & MINIATURE SHIDA FERN CREST (Y: 34..36, Z: 20..23)
    # Delicate, graceful Kin-dami gold forehead armor trim that lets the round ears & chestnut crown shine!
    fill_sym_box(grid, 0, 2, 35, 36, 20, 20, 4)   # Sleek gold brow tiara band
    fill_sym_box(grid, 0, 0, 36, 36, 20, 21, 4)   # Center gold sun-crest mount
    fill_sym_box(grid, 0, 0, 36, 36, 20, 20, 8)   # Tiny crimson center dot (matches Robot!)
    fill_sym_box(grid, 1, 1, 35, 35, 21, 22, 4)   # Delicate miniature golden V-fern crest
    fill_sym_box(grid, 2, 2, 34, 34, 22, 23, 4)   # Swept fern-crest tips clearly inside the ears

    # --- LUSH BUSHY DARK-STRIPED TANUKI TAIL (Y: 1..13, Z: 10..22) ---
    # Plump, fluffy, generously curved striped tail sweeping back (-Y) and proudly up (+Z)
    # so it reads super clearly from BOTH the front 3/4 view AND the rear view!
    tail_segs = [
        # (ty, tz, rx_t, ry_t, rz_t, col)
        (12.2, 12.2, 2.7, 1.5, 2.6, 1),  # Chestnut root anchored deeply in rump
        (10.6, 12.7, 3.0, 1.6, 2.9, 3),  # Bold dark-brown ring 1
        (9.0,  13.5, 3.2, 1.6, 3.1, 2),  # Warm tawny chestnut band
        (7.4,  14.5, 3.3, 1.6, 3.2, 1),  # Rich chestnut band
        (5.8,  15.7, 3.3, 1.6, 3.2, 3),  # Bold dark-brown ring 2
        (4.4,  17.0, 3.1, 1.6, 3.0, 2),  # Warm tawny band
        (3.2,  18.4, 2.8, 1.5, 2.7, 1),  # Rich chestnut band
        (2.2,  19.8, 2.4, 1.5, 2.3, 3),  # Bold dark-brown fluffy tip!
        (1.4,  21.0, 1.8, 1.3, 1.8, 3),  # Plump rounded dark tail tip
    ]
    for ty, tz, rx_t, ry_t, rz_t, tcol in tail_segs:
        fill_sphere_local(grid, cx, ty, tz, rx_t, ry_t, rz_t, tcol)

    # Hollow strictly interior bulk while preserving 100% 6-connectivity
    hollow_interior_26(grid, 1, 24)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=32, pitch_a=20, yaw_b=40, pitch_b=18):
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
    v_a = export_vox(model_a, "ieyasu_a.vox")
    v_b = export_vox(model_b, "ieyasu_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: TOKUGAWA IEYASU ROBOT -> ARMORED TANUKI",
        "1. TOKUGAWA IEYASU SHOGUN ROBOT",
        "2. ARMORED TANUKI (RACCOON DOG)",
        "preview_ieyasu.png",
        yaw_a=32, pitch_a=20, yaw_b=40, pitch_b=18,
    )
    print(f"ieyasu: A={v_a} voxels {model_a.shape} (6-comps={c_a}), B={v_b} voxels {model_b.shape} (6-comps={c_b})")
