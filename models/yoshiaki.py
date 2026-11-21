import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across Mogami Yoshiaki Robot (Form A) & Mogami River Salmon (Form B)
PALETTE = {
    1: (206, 218, 230, 255),  # Gleaming Silver-Steel (Armor Plates / Salmon Silver Scales)
    2: (244, 249, 255, 255),  # Bright Chrome / Specular White (Edge Highlights / Belly / Teeth / Foam)
    3: (32, 50, 84, 255),     # Deep River-Indigo (Kabuto / Back Armor / Salmon Dorsal Back & Gills)
    4: (66, 96, 136, 255),    # Steel-Slate Blue (Fin Webbing / Armor Shading / River Wave)
    5: (216, 36, 48, 255),    # Vivid Crimson-Red (Samurai Lacing / Crest / Salmon Spawning Bands)
    6: (142, 22, 34, 255),    # Deep Lacquer Crimson (Armor Underside / Deep Spawning Stripes)
    7: (44, 48, 56, 255),     # Heavy Forged Iron (Iron Command Baton / Inner Joints / Pupils)
    8: (238, 192, 62, 255),   # Warlord Gold Trim (Maedate Boss / Baton Rings / Salmon Eye Iris)
    9: (72, 228, 250, 255),   # Luminous River-Cyan (Samurai Visor Eyes / Core / River Glint)
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(x0, x1)), min(X - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center (requires even X)."""
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


def count_connected_components_6(grid):
    """Count 6-connected components of nonzero voxels."""
    X, Y, Z = grid.shape
    visited = np.zeros(grid.shape, dtype=bool)
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
                if 0 <= nx < X and 0 <= ny < Y and 0 <= nz < Z and not visited[nx, ny, nz] and grid[nx, ny, nz] > 0:
                    visited[nx, ny, nz] = True
                    q.append((nx, ny, nz))
    return comps


# ============================================================
# FORM A: MOGAMI YOSHIAKI ROBOT (44 x 28 x 44)
# ============================================================
def build_a():
    grid = np.zeros((44, 28, 44), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21 (-X: robot left, viewer's right)
    cx_r = X // 2      # 22 (+X: robot right, viewer's left)

    # --- 1. GROUNDED SAMURAI ARMORED BOOTS (Z: 0..4) ---
    fill_sym_box(grid, 2, 5, 10, 17, 0, 1, 7)    # Heavy forged-iron soles
    fill_sym_box(grid, 2, 5, 11, 17, 1, 2, 3)    # Deep river-indigo foot armor
    fill_sym_box(grid, 3, 4, 17, 19, 1, 2, 1)    # Silver-steel sabaton toe guard
    fill_sym_box(grid, 3, 4, 19, 19, 2, 3, 2)    # Upturned chrome samurai toe point
    fill_sym_box(grid, 2, 5, 12, 16, 3, 3, 5)    # Vivid crimson ankle lacing cuff
    fill_sym_box(grid, 3, 4, 10, 11, 1, 3, 4)    # Slate heel counterweight

    # --- 2. LOWER LEGS / SUNEATE SHIN GREAVES (Z: 4..14) ---
    fill_sym_box(grid, 2, 5, 11, 16, 4, 13, 1)   # Clean gleaming silver-steel greaves
    fill_sym_box(grid, 3, 4, 16, 17, 5, 12, 2)   # Bright chrome front shin ridge
    fill_sym_box(grid, 2, 2, 11, 15, 4, 13, 3)   # Inner river-indigo plate
    fill_sym_box(grid, 5, 5, 11, 15, 4, 13, 3)   # Outer river-indigo plate
    fill_sym_box(grid, 2, 5, 11, 12, 4, 13, 4)   # Rear slate calf armor
    # Two clean, bold crimson spawning-band chevrons on each shin
    fill_sym_box(grid, 4, 5, 13, 16, 7, 8, 5)
    fill_sym_box(grid, 3, 4, 15, 16, 6, 7, 5)
    fill_sym_box(grid, 4, 5, 13, 16, 10, 11, 5)
    fill_sym_box(grid, 3, 4, 15, 16, 10, 10, 6)
    # Rear calf swept fin spurs (echoing salmon pelvic/anal fins)
    fill_sym_box(grid, 3, 4, 9, 10, 7, 11, 3)
    fill_sym_box(grid, 3, 4, 8, 9, 6, 9, 1)
    fill_sym_box(grid, 3, 4, 8, 8, 6, 7, 5)
    # Armored Samurai Knee Guards (Z: 12..15)
    fill_sym_box(grid, 2, 5, 16, 17, 12, 14, 3)
    fill_sym_box(grid, 3, 4, 17, 18, 12, 15, 1)
    fill_sym_box(grid, 3, 4, 18, 18, 13, 14, 5)
    fill_sym_box(grid, 3, 4, 17, 17, 15, 15, 8)  # Gold knee crest

    # --- 3. THIGHS (Z: 14..19) ---
    fill_sym_box(grid, 2, 4, 12, 15, 14, 18, 7)  # Forged-iron inner thigh frame
    fill_sym_box(grid, 2, 4, 13, 16, 15, 18, 1)  # Gleaming silver thigh cuisse
    fill_sym_box(grid, 4, 5, 12, 15, 15, 18, 3)  # Indigo outer thigh plate
    fill_sym_box(grid, 2, 4, 16, 16, 16, 16, 5)  # Crimson thigh band

    # --- 4. WAIST & FORKED TAIL-FIN KUSAZURI SKIRT (Z: 16..22) ---
    fill_sym_box(grid, 0, 4, 11, 16, 19, 21, 7)  # Waist structural core
    fill_sym_box(grid, 0, 4, 15, 17, 20, 21, 6)  # Deep crimson samurai obi sash
    fill_sym_box(grid, 0, 3, 16, 17, 21, 21, 5)  # Vivid crimson top sash
    fill_sym_box(grid, 0, 1, 17, 18, 20, 21, 8)  # Gold warlord belt buckle
    fill_sym_box(grid, 0, 0, 18, 18, 20, 21, 9)  # River-cyan waist gem

    # Front split FORKED TAIL-FIN tassets (clean V-notched kusazuri!)
    fill_sym_box(grid, 2, 5, 16, 17, 18, 20, 3)
    fill_sym_box(grid, 2, 5, 17, 17, 19, 19, 5)  # Crimson odoshi lacing
    fill_sym_box(grid, 2, 2, 16, 17, 16, 17, 1)  # Inner forked tail tip
    fill_sym_box(grid, 5, 5, 16, 17, 16, 17, 1)  # Outer forked tail tip
    fill_sym_box(grid, 3, 4, 16, 17, 18, 18, 4)  # Open V-fork recess below z=18
    # Center front armored groin tab
    fill_sym_box(grid, 0, 1, 16, 17, 17, 19, 3)
    fill_sym_box(grid, 0, 0, 17, 17, 17, 19, 1)
    fill_sym_box(grid, 0, 1, 17, 17, 17, 17, 5)

    # Side hip FORKED TAIL-FIN plates (flaring boldly out in X with crisp fore/aft V-fork!)
    fill_sym_box(grid, 5, 6, 11, 16, 19, 21, 3)
    fill_sym_box(grid, 6, 7, 11, 16, 18, 20, 4)
    fill_sym_box(grid, 6, 8, 11, 12, 15, 18, 1)  # Sweeping rear forked tail lobe
    fill_sym_box(grid, 6, 8, 15, 16, 15, 18, 1)  # Sweeping front forked tail lobe
    fill_sym_box(grid, 8, 8, 11, 11, 15, 17, 5)  # Vivid crimson fin edge
    fill_sym_box(grid, 8, 8, 16, 16, 15, 17, 5)
    fill_sym_box(grid, 6, 7, 12, 15, 19, 19, 5)  # Crimson belt-fin trim
    fill_sym_box(grid, 7, 7, 13, 14, 19, 20, 2)  # Chrome fin rib

    # Rear forked tail-fin skirt plate (crisp V-fork in REAR VIEW!)
    fill_sym_box(grid, 0, 4, 10, 11, 18, 20, 3)
    fill_sym_box(grid, 2, 5, 9, 10, 16, 18, 4)
    fill_sym_box(grid, 3, 5, 9, 10, 14, 16, 1)   # Twin rear forked tail tips
    fill_sym_box(grid, 5, 5, 9, 9, 14, 16, 5)    # Crimson outer edge
    fill_sym_box(grid, 0, 4, 10, 10, 19, 19, 5)  # Crimson horizontal sash

    # --- 5. TORSO / SAMURAI DO CUIRASS WITH ARMORED GILL PLATES (Z: 22..33) ---
    # Tapered crimson-laced abdomen (Z: 22..24)
    fill_sym_box(grid, 0, 4, 11, 16, 22, 24, 7)
    fill_sym_box(grid, 0, 3, 15, 17, 22, 24, 6)
    fill_sym_box(grid, 0, 3, 16, 17, 23, 23, 5)  # Crimson odoshi lame
    fill_sym_box(grid, 1, 2, 17, 17, 22, 24, 1)  # Silver ab vertical plates

    # Broad Warlord Chest Core (Z: 25..32)
    fill_sym_box(grid, 0, 5, 11, 17, 25, 31, 3)  # Deep river-indigo inner cuirass
    fill_sym_box(grid, 0, 5, 15, 18, 25, 31, 1)  # Gleaming silver-steel breastplate
    fill_sym_box(grid, 0, 4, 18, 18, 26, 30, 2)  # Specular silver chest bevel
    # Curved Armored Gill-Plate Pectorals (matching salmon operculum!)
    fill_sym_box(grid, 3, 5, 16, 18, 27, 31, 3)  # Outer indigo gill armor
    fill_sym_box(grid, 4, 5, 17, 18, 28, 30, 4)  # Slate gill bevel
    fill_sym_box(grid, 2, 4, 18, 18, 26, 26, 5)  # Bold crimson spawning V-slash
    fill_sym_box(grid, 3, 5, 18, 18, 29, 29, 5)  # Upper crimson gill-seam trim
    # Center Warlord Sternum Emblem & River-Cyan Core
    fill_sym_box(grid, 0, 1, 18, 19, 27, 31, 8)  # Gold warlord chest frame
    fill_sym_box(grid, 0, 1, 18, 19, 28, 30, 3)
    fill_sym_box(grid, 0, 0, 19, 19, 28, 30, 9)  # Glowing river-cyan core
    fill_sym_box(grid, 0, 1, 18, 19, 31, 31, 8)  # Top gold crest bar
    # High Samurai Collar / Gorget (Z: 32..33)
    fill_sym_box(grid, 0, 4, 11, 16, 32, 32, 3)
    fill_sym_box(grid, 2, 4, 12, 16, 33, 33, 3)
    fill_sym_box(grid, 2, 4, 16, 16, 32, 33, 5)  # Crimson collar trim
    fill_sym_box(grid, 3, 4, 12, 15, 33, 33, 1)  # Silver collar rim

    # --- 6. BACKPACK & PROMINENT SWEPT SALMON DORSAL FIN BACK-ARMOR (Y: 1..11, Z: 22..43) ---
    # Clean armored indigo & silver backpack housing
    fill_sym_box(grid, 0, 4, 8, 11, 23, 31, 3)
    fill_sym_box(grid, 1, 4, 7, 8, 24, 30, 4)
    fill_sym_box(grid, 2, 3, 7, 7, 25, 29, 1)    # Silver back armor panels
    fill_sym_box(grid, 2, 3, 7, 7, 27, 27, 5)    # Crimson trim
    # Twin compact lower river-jet vents
    fill_sym_box(grid, 2, 3, 6, 8, 22, 24, 7)
    fill_sym_box(grid, 2, 3, 6, 6, 22, 23, 9)

    # SIGNATURE SWEPT SALMON DORSAL FIN ARMOR (背びれが背部の装甲)!
    # Tall, bold, unmistakable swept dorsal fin blade rising from the back to Z=43, Y=1!
    # Clean diagonal radiating silver fin rays + crisp vivid crimson leading spine edge!
    dorsal_rows = [
        # (z, y_back, y_front)
        (25, 5, 9),
        (26, 4, 9),
        (27, 4, 9),
        (28, 3, 9),
        (29, 3, 9),
        (30, 3, 9),
        (31, 2, 10),
        (32, 2, 10),
        (33, 2, 10),
        (34, 2, 9),
        (35, 1, 9),
        (36, 1, 8),
        (37, 1, 8),
        (38, 1, 7),
        (39, 1, 6),
        (40, 1, 5),
        (41, 1, 4),
        (42, 1, 3),
        (43, 1, 2),
    ]
    for z, yb, yf in dorsal_rows:
        for y in range(yb, yf + 1):
            if y == yf or (z >= 42 and y == yf):
                col = 5  # Crisp vivid crimson leading dorsal spine!
            elif y == yf - 1 and z >= 31:
                col = 2  # Gleaming chrome spine highlight right behind crimson edge!
            elif y == yb and z >= 33:
                col = 2 if (z % 2 == 0) else 1  # Bright silver serrated trailing fin edge (pops against dark bg!)
            elif (z + y) % 4 == 0:
                col = 1  # Clean diagonal radiating silver fin-ray ribs!
            elif y >= yf - 3:
                col = 3  # Deep river-indigo fin core
            else:
                col = 4  # Steel-slate fin webbing
            fill_sym_box(grid, 0, 0, y, y, z, z, col)
        # Sculpted 4-voxel base shoulder where dorsal fin anchors into the backpack
        if 26 <= z <= 34:
            fill_sym_box(grid, 1, 1, max(yb + 2, 6), min(yf, 9), z, z, 3)
            if z in (28, 31, 34):
                fill_sym_box(grid, 1, 1, 6, 8, z, z, 1)

    # Compact swept side-fin stabilizers lower on the backpack (don't crowd the main dorsal fin!)
    for z, x0, x1, y0, y1 in [
        (27, 4, 5, 7, 8),
        (28, 4, 6, 6, 8),
        (29, 5, 6, 6, 7),
        (30, 5, 7, 5, 7),
        (31, 6, 7, 5, 6),
    ]:
        fill_sym_box(grid, x0, x1, y0, y1, z, z, 3)
        fill_sym_box(grid, x1, x1, y0, y1, z, z, 1)
        if z == 31:
            fill_sym_box(grid, x1, x1, y0, y1, z, z, 5)

    # --- 7. FORKED TAIL-FIN SAMURAI SODE PAULDRONS (Z: 27..38, x_off: 6..12) ---
    fill_sym_box(grid, 5, 8, 12, 15, 29, 31, 7)  # Heavy iron shoulder axle
    fill_sym_box(grid, 6, 9, 12, 16, 29, 32, 3)  # Inner pauldron dome
    # Sweeping FORKED TAIL-FIN shoulder armor with unmistakable crisp V-notch at z=34!
    pauldron_profile = [
        # (z, x0, x1, y0, y1)
        (38, 10, 11, 12, 15),  # Upper forked tail-fin tip!
        (37, 8,  11, 11, 16),
        (36, 7,  11, 11, 16),
        (35, 6,  10, 11, 17),
        (34, 6,  9,  11, 17),  # Deep crisp V-notch between upper & lower tail-fin lobes!
        (33, 6,  10, 11, 17),
        (32, 7,  11, 11, 17),  # Lower sweeping forked tail-fin lobe!
        (31, 8,  12, 11, 17),
        (30, 9,  12, 11, 16),
        (29, 10, 12, 12, 15),
        (28, 11, 12, 12, 15),
    ]
    for z, x0, x1, y0, y1 in pauldron_profile:
        fill_sym_box(grid, x0, x1, y0, y1, z, z, 3)
        # Clean silver fin-ray plates
        if z in (37, 35, 32, 30):
            fill_sym_box(grid, x0 + 1, x1, y1, y1, z, z, 1)
            fill_sym_box(grid, x1, x1, y0, y1, z, z, 1)
        # Vivid crimson upper & lower outer fin edges
        if z in (38, 36, 31, 28):
            fill_sym_box(grid, x1, x1, y0, y1, z, z, 5)
            fill_sym_box(grid, x0 + 1, x1, y1, y1, z, z, 5)
        fill_sym_box(grid, x0 + 1, x1 - 1, y0, y0, z, z, 4)
    # Gold warlord rivet boss & chrome fin tips
    fill_sym_box(grid, 8, 9, 17, 17, 33, 34, 8)
    fill_sym_box(grid, 10, 11, 13, 14, 38, 38, 2)
    fill_sym_box(grid, 12, 12, 13, 14, 30, 31, 2)

    # --- 8. ARMS, LEFT GILL-BUCKLER & RIGHT HEAVY IRON COMMAND BATON (鉄の指揮棒) ---
    # Upper arms (Z: 22..29)
    fill_sym_box(grid, 7, 9, 12, 15, 22, 28, 7)  # Forged-iron upper arm
    fill_sym_box(grid, 8, 9, 13, 15, 24, 27, 1)  # Silver bicep armor
    fill_sym_box(grid, 8, 9, 13, 15, 25, 25, 5)  # Crimson arm band

    # LEFT ARM (-X, viewer's right): Forearm + Curved Gill-Plate Buckler Shield
    fill_box(grid, cx_l - 10, cx_l - 7, 12, 16, 16, 22, 1)   # Gleaming silver forearm
    fill_box(grid, cx_l - 10, cx_l - 8, 13, 16, 18, 18, 5)   # Crimson wrist stripe
    fill_box(grid, cx_l - 9, cx_l - 7, 13, 16, 13, 15, 7)    # Forged-iron left fist
    fill_box(grid, cx_l - 9, cx_l - 8, 16, 16, 14, 14, 1)    # Silver knuckle guard
    # Curved Gill-Plate / Fin Buckler mounted on outer left forearm
    fill_box(grid, cx_l - 12, cx_l - 11, 12, 17, 15, 22, 3)  # Deep indigo buckler core
    fill_box(grid, cx_l - 12, cx_l - 12, 13, 16, 16, 21, 1)  # Silver buckler face
    fill_box(grid, cx_l - 12, cx_l - 12, 12, 17, 15, 15, 5)  # Crimson lower edge
    fill_box(grid, cx_l - 12, cx_l - 12, 12, 17, 22, 22, 5)  # Crimson upper edge
    fill_box(grid, cx_l - 12, cx_l - 12, 14, 15, 18, 19, 8)  # Gold Mogami crest boss
    fill_box(grid, cx_l - 11, cx_l - 11, 17, 18, 17, 20, 2)  # Chrome leading blade edge

    # RIGHT ARM (+X, viewer's left — hero showcase!): Extended slightly OUTWARD (+X)
    # holding Mogami Yoshiaki's FAMOUS HEAVY IRON COMMAND BATON (鉄の指揮棒) in full crisp silhouette!
    fill_box(grid, cx_r + 8, cx_r + 11, 13, 16, 18, 22, 1)   # Silver forearm angling outward
    fill_box(grid, cx_r + 9, cx_r + 12, 14, 16, 18, 21, 1)   # Extended wrist cuff
    fill_box(grid, cx_r + 10, cx_r + 12, 14, 16, 19, 19, 5)  # Crimson wrist stripe
    fill_box(grid, cx_r + 11, cx_r + 13, 14, 17, 17, 20, 7)  # Heavy forged-iron gripping fist
    fill_box(grid, cx_r + 12, cx_r + 13, 16, 17, 18, 19, 1)  # Silver armored fingers

    # HEAVY IRON COMMAND BATON / KANABO (鉄の指揮棒)
    # Angled BOLDLY OUTWARD (+X: +12 -> +20) and UPWARD (+Z: 13 -> 39) with modest +Y (15 -> 19)
    # so it stands out 100% cleanly in silhouette against the dark background on viewer-left!
    # Crimson warlord tassel hanging below the pommel (Z: 10..13)
    fill_box(grid, cx_r + 11, cx_r + 12, 15, 16, 10, 12, 5)
    fill_box(grid, cx_r + 11, cx_r + 11, 15, 15, 9, 10, 6)
    fill_box(grid, cx_r + 11, cx_r + 12, 15, 16, 13, 14, 8)  # Gold pommel ring
    # Heavy forged-iron baton shaft climbing cleanly outward & upward (full face overlap at every step!)
    baton_segs = [
        # (x0, x1, y0, y1, z0, z1, col)
        (12, 13, 15, 16, 14, 17, 7),  # Lower grip shaft
        (12, 13, 15, 16, 17, 20, 7),  # Through fist
        (13, 14, 15, 17, 20, 21, 8),  # Gold warlord hand-guard collar!
        (13, 15, 16, 17, 21, 23, 7),  # Forged-iron mid shaft
        (14, 16, 16, 18, 23, 25, 7),  # Thickening iron baton
        (15, 17, 16, 18, 25, 28, 7),  # Heavy octagonal iron kanabo shaft
        (16, 18, 17, 19, 28, 31, 7),  # Massive iron smashing body
        (17, 19, 17, 19, 31, 35, 7),  # Heavy iron warhead!
        (17, 19, 17, 19, 35, 36, 8),  # Gold warlord crown collar!
        (18, 19, 18, 19, 37, 38, 1),  # Silver iron cap
        (18, 18, 18, 18, 39, 39, 2),  # Chrome finial spike!
    ]
    for x0, x1, y0, y1, z0, z1, col in baton_segs:
        fill_box(grid, cx_r + x0, cx_r + x1, y0, y1, z0, z1, col)
    # Gleaming silver iron studs & crimson lacquer war-band along the heavy kanabo!
    for sx, sy, sz, scol in [
        (15, 18, 26, 1), (17, 17, 26, 2),
        (16, 19, 29, 2), (18, 18, 29, 1), (16, 17, 29, 1),
        (17, 19, 32, 2), (19, 18, 32, 2), (17, 17, 32, 1),
        (18, 19, 34, 1), (19, 19, 34, 2),
    ]:
        grid[cx_r + sx, sy, sz] = scol
    # Vivid crimson warlord grip/collar wrap around mid-baton
    fill_box(grid, cx_r + 16, cx_r + 18, 17, 19, 30, 30, 5)
    fill_box(grid, cx_r + 14, cx_r + 16, 16, 18, 24, 24, 5)

    # --- 9. ARMORED SAMURAI KABUTO HEAD & SILVER-CRIMSON FIN CREST (Z: 33..43) ---
    fill_sym_box(grid, 0, 1, 13, 15, 32, 33, 7)  # Iron neck joint
    # Deep river-indigo kabuto helmet bowl
    fill_sym_box(grid, 0, 2, 12, 16, 34, 38, 3)
    fill_sym_box(grid, 0, 2, 12, 15, 39, 39, 3)
    fill_sym_box(grid, 0, 1, 13, 15, 39, 39, 1)  # Silver crown ridge
    # Flared Samurai Shikoro neck-guard (wrapping sides & back)
    fill_sym_box(grid, 2, 3, 11, 15, 34, 36, 3)
    fill_sym_box(grid, 0, 3, 11, 12, 34, 36, 3)
    fill_sym_box(grid, 0, 4, 10, 14, 34, 34, 5)  # Crimson shikoro bottom trim
    fill_sym_box(grid, 0, 3, 11, 14, 35, 35, 1)  # Silver shikoro mid-tier
    # Fierce Samurai Faceplate / Menpo & Glowing River-Cyan Eyes
    fill_sym_box(grid, 0, 1, 16, 17, 34, 35, 7)  # Forged-iron menpo mask
    fill_sym_box(grid, 0, 0, 17, 17, 34, 34, 5)  # Crimson chin guard
    fill_sym_box(grid, 2, 2, 16, 16, 34, 35, 1)  # Silver cheek plates
    fill_sym_box(grid, 0, 1, 16, 17, 36, 36, 9)  # Glowing river-cyan samurai eyes!
    fill_sym_box(grid, 2, 2, 16, 17, 36, 36, 3)  # Indigo brow wing
    fill_sym_box(grid, 0, 2, 16, 17, 37, 37, 3)  # Kabuto visor (mabizashi)
    fill_sym_box(grid, 0, 2, 17, 17, 37, 37, 5)  # Crimson brow rim

    # SILVER-AND-CRIMSON FIN CREST (KABUTO MAEDATE & KUWAGATA, Z: 37..43)!
    fill_sym_box(grid, 0, 0, 17, 18, 37, 39, 8)  # Gold warlord central maedate boss
    crest_segs = [
        (1, 2, 17, 17, 38, 39, 2),
        (2, 3, 16, 17, 39, 40, 2),
        (3, 4, 16, 17, 40, 41, 1),
        (4, 5, 16, 16, 41, 42, 2),
        (5, 5, 15, 16, 42, 43, 2),
    ]
    for x0, x1, y0, y1, z0, z1, col in crest_segs:
        fill_sym_box(grid, x0, x1, y0, y1, z0, z1, col)
    # Vivid crimson inner edge lining the silver fin-crest
    fill_sym_box(grid, 1, 2, 17, 17, 39, 39, 5)
    fill_sym_box(grid, 2, 3, 17, 17, 40, 40, 5)
    fill_sym_box(grid, 3, 4, 16, 16, 41, 41, 5)
    fill_sym_box(grid, 4, 4, 16, 16, 42, 42, 5)
    # Central dorsal-fin kabuto plume sweeping back over the helmet crown
    fill_sym_box(grid, 0, 0, 15, 17, 40, 41, 1)
    fill_sym_box(grid, 0, 0, 13, 16, 41, 42, 5)
    fill_sym_box(grid, 0, 0, 12, 14, 42, 43, 2)

    # Hollow strictly interior voxels to hit ~2,900-3,400 cleanly
    hollow_interior_26(grid, 1, 40)

    return grid


# ============================================================
# FORM B: MOGAMI RIVER SALMON (22 x 52 x 28)
# Dynamic upstream-leaping salmon (最上川の鮭・遡上の姿)
# ============================================================
def build_b():
    grid = np.zeros((22, 52, 28), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_base = (X - 1) / 2.0  # 10.5

    def body_center_x(y):
        # Graceful upstream swimming S-wave flex (gentle & muscular)
        t = (y - 10.0) / 39.0
        return cx_base + 1.25 * np.sin(t * 2.0 * np.pi - 0.5)

    def body_center_z(y):
        # Sleek leaping arch: tail low (z~10.5), mid-body arching cleanly (z~13.8), head thrusting upstream (z~14.2)
        t = np.clip((y - 10.0) / 39.0, 0.0, 1.0)
        return 10.4 + 3.4 * np.sin(t * 2.2) + 1.2 * t

    # --- 1. SLEEK SCULPTED MOGAMI RIVER WAVE-CREST BASE (Z: 0..9, Y: 18..34) ---
    # Sweeping curling river wave crest grounding the leaping salmon cleanly at Z=0!
    for y in range(18, 35):
        bx = body_center_x(y)
        # Wave crest peaks under mid-belly (y=23..30) and tapers smoothly into foaming trailing wake
        dist_peak = abs(y - 26.5)
        h_max = int(round(9.5 - dist_peak * 0.72))
        h_max = max(2, min(9, h_max))
        w_half = max(1.6, 3.8 - dist_peak * 0.22)
        for z in range(0, h_max + 1):
            # Sweep slightly backward as wave curls up
            zw = w_half * (1.0 - 0.55 * (z / max(1.0, float(h_max))))
            for x in range(X):
                dx = abs(x - bx)
                if dx <= zw:
                    if z <= 1:
                        col = 3  # Deep river-indigo water base
                    elif z == h_max or (z == h_max - 1 and dx >= zw - 0.8):
                        col = 2 if (z == h_max) else 1  # Crisp white-silver curling foam crest!
                    elif z == 2 and y in (21, 25, 29, 32) and dx >= zw - 1.1:
                        col = 9  # Subtle river-cyan rapid glint
                    elif dx >= zw - 1.0:
                        col = 4  # Steel-slate wave swell
                    else:
                        col = 3 if z <= 3 else 4
                    grid[x, y, z] = col

    # Dynamic curling white-foam wave tongues anchored cleanly at Z=0..3
    for y_t, z_t, x_off in [(34, 3, -1), (35, 2, -1), (33, 4, 2), (17, 3, 1), (16, 2, 1)]:
        tx = int(round(body_center_x(y_t))) + x_off
        if 1 <= tx < X - 1:
            fill_box(grid, tx, tx, y_t, y_t, 0, z_t, 4)
            grid[tx, y_t, z_t] = 2

    # --- 2. SLEEK STREAMLINED SALMON BODY WITH BOLD CRIMSON SPAWNING BANDS (Y: 10..40) ---
    # Streamlined laterally-compressed salmon torpedo profile: (y, rx_width, rz_height)
    body_profile = [
        (10, 1.15, 1.65),  # Narrow muscular caudal peduncle
        (11, 1.35, 1.90),
        (12, 1.55, 2.15),
        (13, 1.75, 2.40),
        (14, 1.95, 2.65),
        (15, 2.15, 2.95),
        (16, 2.35, 3.20),
        (17, 2.55, 3.45),
        (18, 2.75, 3.70),
        (19, 2.95, 3.90),
        (20, 3.10, 4.10),
        (21, 3.25, 4.25),
        (22, 3.35, 4.40),
        (23, 3.45, 4.50),
        (24, 3.55, 4.60),
        (25, 3.60, 4.65),
        (26, 3.65, 4.65),  # Sleek muscular peak!
        (27, 3.65, 4.65),
        (28, 3.65, 4.60),
        (29, 3.60, 4.55),
        (30, 3.55, 4.45),
        (31, 3.50, 4.35),
        (32, 3.45, 4.25),
        (33, 3.40, 4.15),
        (34, 3.35, 4.05),
        (35, 3.30, 3.95),  # Behind gill plates
        (36, 3.35, 3.90),  # Armored gill plate (operculum) flare
        (37, 3.30, 3.85),
        (38, 3.20, 3.75),
        (39, 3.05, 3.60),
        (40, 2.85, 3.40),
    ]
    # Five clean, bold crimson-red spawning bands (婚姻色) striping the silver flanks!
    band_ys = [16.5, 20.8, 25.0, 29.2, 33.4]

    for y, rx, rz in body_profile:
        bx = body_center_x(y)
        bz = body_center_z(y)
        for x in range(X):
            dx = x - bx
            if abs(dx) > rx + 0.25:
                continue
            for z in range(max(0, int(np.floor(bz - rz))), min(Z, int(np.ceil(bz + rz)) + 1)):
                dz = z - bz
                norm2 = (dx / rx) ** 2 + (dz / rz) ** 2
                if norm2 <= 1.0:
                    z_rel = dz / rz  # -1 bottom .. +1 top
                    if z_rel > 0.44:
                        # Deep river-indigo dorsal back with subtle dark spots
                        if z_rel > 0.68 and (y % 4 == 0) and abs(dx) > 0.7:
                            col = 7
                        else:
                            col = 3
                    elif z_rel > 0.26:
                        col = 4  # Smooth steel-slate back-to-flank transition
                    elif z_rel < -0.56:
                        col = 2  # Gleaming bright silver-white salmon belly
                    else:
                        # Gleaming silver-scaled flanks
                        col = 1
                        if 0.14 <= z_rel <= 0.26:
                            col = 2  # Crisp specular silver lateral highlight!
                        # Clean, bold wavy crimson spawning bands (婚姻色)
                        y_slanted = y - dz * 0.40
                        for by_c in band_ys:
                            dist = abs(y_slanted - by_c)
                            width = 1.15 - 0.32 * abs(z_rel)
                            if dist <= width and -0.48 <= z_rel <= 0.30:
                                col = 5 if dist <= width * 0.68 else 6
                                break
                    grid[x, y, z] = col

    # --- 3. ARMORED GILL PLATES (鰓蓋, OPERCULUM, Y: 35..39) ---
    # Sculpted curved indigo-and-silver operculum plates matching robot's chest/shoulders!
    for y in range(35, 40):
        bx = body_center_x(y)
        bz = body_center_z(y)
        gill_r = 3.55 if y in (36, 37) else 3.25
        z_lo = int(round(bz - 2.6 + (y - 36) * 0.25))
        z_hi = int(round(bz + 2.2 - abs(y - 37) * 0.35))
        for sign in (-1, 1):
            gx = int(round(bx + sign * gill_r))
            if 0 <= gx < X:
                for z in range(max(0, z_lo), min(Z, z_hi + 1)):
                    if y == 35:
                        col = 5 if (bz - 1.3 <= z <= bz + 1.0) else 7  # Crimson/dark gill slit seam!
                    elif y == 36:
                        col = 2 if z >= z_hi - 1 else 1  # Gleaming silver operculum edge
                    elif y == 37:
                        col = 8 if z == int(round(bz + 0.5)) else 3  # Deep indigo plate + gold rivet accent
                    else:
                        col = 4  # Steel-slate forward cheek
                    grid[gx, y, z] = col

    # --- 4. STREAMLINED HEAD & ICONIC HOOKED KYPE JAW (鼻曲がり, Y: 41..50) ---
    head_profile = [
        (41, 2.65, 3.20),
        (42, 2.40, 2.95),
        (43, 2.15, 2.65),
        (44, 1.85, 2.35),
        (45, 1.60, 2.00),
        (46, 1.35, 1.65),
    ]
    for y, rx, rz in head_profile:
        bx = body_center_x(y)
        bz = body_center_z(y) + (y - 40) * 0.14
        for x in range(X):
            dx = x - bx
            if abs(dx) > rx + 0.25:
                continue
            for z in range(max(0, int(np.floor(bz - rz))), min(Z, int(np.ceil(bz + rz)) + 1)):
                dz = z - bz
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    z_rel = dz / rz
                    if z_rel > 0.22:
                        col = 3  # Dark river-indigo crown
                    elif z_rel < -0.45:
                        col = 1  # Silver lower jaw base
                    elif y >= 43 and -0.15 <= z_rel <= 0.22:
                        col = 5  # Crimson spawning cheek/snout flush
                    else:
                        col = 4
                    grid[x, y, z] = col

    # Fierce open spawning mouth & ICONIC HOOKED KYPE JAW (鼻曲がり, Y: 44..50)!
    bx_m = int(round(body_center_x(46)))
    bz_m = int(round(body_center_z(46))) + 1
    # Dark forged-iron mouth cavity (Y: 44..47)
    fill_box(grid, bx_m - 1, bx_m + 1, 44, 46, bz_m - 1, bz_m, 7)
    # Upper hooked snout sweeping forward to Y=50 then curving cleanly DOWNWARD!
    fill_box(grid, bx_m - 1, bx_m + 1, 45, 47, bz_m + 1, bz_m + 2, 3)
    fill_box(grid, bx_m - 1, bx_m + 1, 47, 49, bz_m + 1, bz_m + 2, 5)  # Crimson hooked snout
    fill_box(grid, bx_m - 1, bx_m + 1, 48, 50, bz_m, bz_m + 1, 3)      # Sweeping upper kype arch
    fill_box(grid, bx_m, bx_m, 49, 50, bz_m - 1, bz_m, 5)              # Sharp downward hooked kype tip!
    # Lower jaw thrusting forward & hooking sharply UPWARD!
    fill_box(grid, bx_m - 1, bx_m + 1, 44, 46, bz_m - 2, bz_m - 2, 1)
    fill_box(grid, bx_m - 1, bx_m + 1, 46, 48, bz_m - 2, bz_m - 2, 5)
    fill_box(grid, bx_m - 1, bx_m + 1, 47, 49, bz_m - 2, bz_m - 1, 1)  # Upturned lower kype jaw!
    fill_box(grid, bx_m, bx_m, 49, 49, bz_m - 1, bz_m, 2)              # Bright ivory lower kype hook tip!
    # Crisp gleaming white spawning teeth lining upper & lower jaws!
    for ty in (45, 47):
        grid[bx_m - 1, ty, bz_m] = 2
        grid[bx_m + 1, ty, bz_m] = 2
        grid[bx_m - 1, ty, bz_m - 1] = 2
        grid[bx_m + 1, ty, bz_m - 1] = 2

    # Expressive Salmon Eyes on both sides of head (Y: 42..43)
    eye_z = int(round(body_center_z(42.5))) + 1
    for sign in (-1, 1):
        ex = int(round(body_center_x(42.5) + sign * 2.4))
        if 0 <= ex < X:
            grid[ex, 42, eye_z] = 8      # Warlord gold iris
            grid[ex, 43, eye_z] = 7      # Dark iron pupil
            grid[ex, 42, eye_z + 1] = 8  # Upper gold iris
            grid[ex, 43, eye_z + 1] = 9  # Luminous river-cyan eye glint!

    # --- 5. PROMINENT SWEPT DORSAL FIN (背びれ — matches robot back-fin armor!) ---
    # Tall, crisp backward-swept dorsal fin with continuous diagonal silver fin rays!
    dorsal_slices = [
        # (y, h_fin)
        (31, 2),
        (30, 4),
        (29, 6),
        (28, 7),
        (27, 8),
        (26, 8),
        (25, 8),
        (24, 7),
        (23, 7),
        (22, 6),
        (21, 5),
        (20, 4),
        (19, 3),
        (18, 2),
    ]
    prev_dx = None
    for y, h_fin in dorsal_slices:
        bx = int(round(body_center_x(y)))
        bz_top = int(round(body_center_z(y) + 3.8))
        xs_fill = [bx] if prev_dx is None or prev_dx == bx else [bx, prev_dx]
        for dz in range(0, h_fin + 1):
            z = bz_top + dz
            if z >= Z:
                continue
            # Continuous radiating fin rays (constant y + dz tilts cleanly backward like real dorsal rays!)
            if y >= 29 or (y == 28 and dz >= h_fin - 1) or (y == 27 and dz == h_fin):
                col = 5  # Crisp vivid crimson leading spine edge!
            elif y == 28 or (y == 27 and dz >= h_fin - 2):
                col = 2  # Bright chrome highlight spine behind crimson edge!
            elif dz == h_fin and y <= 25:
                col = 2 if (y % 2 == 0) else 1  # Bright silver top fin edge
            elif (y + dz) % 4 == 0:
                col = 1  # Continuous diagonal silver fin rays!
            elif dz <= 2:
                col = 3  # Deep indigo base
            else:
                col = 4  # Steel-slate fin webbing
            for fx in xs_fill:
                if 0 <= fx < X:
                    grid[fx, y, z] = col
            if dz <= 3 and bx + 1 < X:
                grid[bx + 1, y, z] = col
        prev_dx = bx

    # --- 6. SIGNATURE SALMON ADIPOSE FIN (脂びれ, Y: 13..16) ---
    prev_ax = None
    for y, h_ad in [(16, 2), (15, 3), (14, 3), (13, 2)]:
        bx = int(round(body_center_x(y)))
        bz_top = int(round(body_center_z(y) + 2.0))
        xs_fill = [bx] if prev_ax is None or prev_ax == bx else [bx, prev_ax]
        for dz in range(0, h_ad + 1):
            z = bz_top + dz
            if 0 <= z < Z:
                col = 5 if dz == h_ad else 3
                for fx in xs_fill:
                    grid[fx, y, z] = col
        prev_ax = bx

    # --- 7. SWEPT PECTORAL FINS (胸びれ, Y: 29..36, flaring gracefully outward ±X) ---
    for sign in (-1, 1):
        pect_steps = [
            # (y, o0, o1, z_lo, z_hi)
            (36, 3, 4, 10, 12),
            (35, 3, 5, 9,  12),
            (34, 3, 6, 9,  11),
            (33, 4, 7, 8,  11),
            (32, 4, 7, 8,  10),
            (31, 5, 7, 8,  10),
            (30, 5, 7, 8,  9),
            (29, 6, 7, 8,  9),
        ]
        for y, o0, o1, zl, zh in pect_steps:
            bx = body_center_x(y)
            for off in range(o0, o1 + 1):
                fx = int(round(bx + sign * off))
                if 0 <= fx < X:
                    for z in range(zl, zh + 1):
                        if y == 36 or (off == o1 and z == zh):
                            col = 5  # Crimson leading fin edge
                        elif off == o1:
                            col = 1  # Silver outer tip
                        elif (y + off) % 3 == 0:
                            col = 1  # Silver fin rays
                        else:
                            col = 4 if off > o0 + 1 else 3
                        grid[fx, y, z] = col

    # --- 8. PELVIC FINS (腹びれ, Y: 22..27) & ANAL FIN (尻びれ, Y: 14..20) ---
    for sign in (-1, 1):
        for y, o0, o1, zl, zh in [
            (27, 1, 3, 8, 10),
            (26, 1, 3, 7, 10),
            (25, 2, 4, 7, 9),
            (24, 2, 4, 6, 9),
            (23, 2, 4, 6, 8),
            (22, 3, 4, 6, 7),
        ]:
            bx = body_center_x(y)
            for off in range(o0, o1 + 1):
                fx = int(round(bx + sign * off))
                if 0 <= fx < X:
                    for z in range(zl, zh + 1):
                        col = 5 if y == 27 else (1 if off == o1 else 4)
                        grid[fx, y, z] = col

    prev_anx = None
    for y, depth in [(20, 2), (19, 3), (18, 4), (17, 4), (16, 4), (15, 3), (14, 2)]:
        bx = int(round(body_center_x(y)))
        bz_bot = int(round(body_center_z(y) - 2.6))
        xs_fill = [bx] if prev_anx is None or prev_anx == bx else [bx, prev_anx]
        for dz in range(0, depth + 1):
            z = bz_bot - dz
            if 0 <= z < Z:
                col = 5 if y == 20 else (1 if dz == depth else (4 if dz >= 2 else 3))
                for fx in xs_fill:
                    grid[fx, y, z] = col
        prev_anx = bx

    # --- 9. WIDE FORKED CAUDAL TAIL FIN (尾びれ — matches robot skirt/pauldrons!) ---
    # 100% 6-connected via prev_tx bridging across any X sweep step, with clean radial silver rays!
    tail_slices = [
        # (y, upper_z0, upper_z1, lower_z0, lower_z1)
        (10, 10, 12, 9,  10),
        (9,  10, 13, 8,  10),
        (8,  10, 14, 7,  10),
        (7,  11, 15, 6,  10),
        (6,  11, 16, 5,  9),   # Deep crisp V-fork opens at z=10!
        (5,  12, 17, 4,  8),
        (4,  13, 18, 4,  7),
        (3,  14, 19, 3,  6),
        (2,  16, 20, 3,  5),
        (1,  18, 20, 3,  4),   # Sharp sweeping forked caudal tips!
    ]
    z_tail_mid = 10.5
    prev_tx = int(round(body_center_x(10)))
    for y, uz0, uz1, lz0, lz1 in tail_slices:
        tx = int(round(body_center_x(10) + (10 - y) * 0.22))
        tx = max(1, min(X - 2, tx))
        # Bridge across prev_tx whenever X shifts so tail is guaranteed 100% 6-connected!
        x_range = range(min(tx, prev_tx), max(tx, prev_tx) + 1)
        for z in list(range(uz0, uz1 + 1)) + list(range(lz0, lz1 + 1)):
            if not (0 <= z < Z):
                continue
            is_outer_edge = (z == uz1 or z == lz0)
            is_inner_fork = (z == uz0 or z == lz1) and y <= 6
            # Smooth radial angle ray lines fanning cleanly from peduncle (y=10, z=10.5)
            dy_r = max(1.0, 10.5 - y)
            dz_r = abs(z - z_tail_mid)
            slope = dz_r / dy_r
            is_ray = (0.38 <= slope <= 0.52) or (0.78 <= slope <= 0.92)
            if is_outer_edge:
                col = 5 if y <= 8 else 3  # Vivid crimson outer tail fin trim!
            elif is_inner_fork:
                col = 2 if y <= 4 else 1  # Bright gleaming silver inner V-fork edge!
            elif is_ray and y <= 8:
                col = 1  # Clean radiating silver fin rays!
            elif y >= 8:
                col = 3  # Deep river-indigo tail root
            else:
                col = 4  # Steel-slate tail webbing
            for fx in x_range:
                grid[fx, y, z] = col
            if y >= 7 and tx - 1 >= 0:
                grid[tx - 1, y, z] = 3
        prev_tx = tx

    # Hollow strictly interior voxels inside the bulky salmon torso/wave base
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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=34, pitch_a=20, yaw_b=56, pitch_b=18):
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
    c_a = count_connected_components_6(model_a)
    c_b = count_connected_components_6(model_b)
    v_a = export_vox(model_a, "yoshiaki_a.vox")
    v_b = export_vox(model_b, "yoshiaki_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: MOGAMI YOSHIAKI ROBOT -> UPSTREAM SALMON",
        "1. MOGAMI YOSHIAKI ROBOT",
        "2. MOGAMI RIVER SALMON (UPSTREAM)",
        "preview_yoshiaki.png",
        yaw_a=34, pitch_a=20, yaw_b=56, pitch_b=18,
    )
    print(f"yoshiaki: A={v_a} voxels {model_a.shape} (6-comp={c_a}, z0={int(np.sum(model_a[:, :, 0] > 0))}), "
          f"B={v_b} voxels {model_b.shape} (6-comp={c_b}, z0={int(np.sum(model_b[:, :, 0] > 0))})")
