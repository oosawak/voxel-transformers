import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across both Date Shigezane Robot (Form A) and Giant Gold & Red Centipede (Form B)
PALETTE = {
    1: (44, 48, 60, 255),     # Kuro-Urushi Charcoal-Black Samurai Armor & Centipede Joints
    2: (84, 90, 108, 255),    # Tempered Gunmetal Frame & Inter-Segment Armor Trim
    3: (204, 28, 36, 255),    # Vivid Crimson-Red Centipede Carapace Plates
    4: (132, 16, 24, 255),    # Deep Carmine Lacquer Shading & Flank Plates
    5: (248, 200, 44, 255),   # Gleaming Gold Giant Centipede Crest & Carapace Edging
    6: (206, 126, 26, 255),   # Golden-Amber Articulated Centipede Legs & Bronze Trim
    7: (226, 234, 246, 255),  # Forged Steel War Spear Blade & Mandible Fang Edge
    8: (60, 242, 150, 255),   # Glowing Emerald-Venom Eyes & Samurai Visor
    9: (244, 86, 40, 255),    # Bright Vermilion Dorsal Ridge & Odoshi Lacing
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(int(x0), int(x1))), min(X - 1, max(int(x0), int(x1)))
    y0, y1 = max(0, min(int(y0), int(y1))), min(Y - 1, max(int(y0), int(y1)))
    z0, z1 = max(0, min(int(z0), int(z1))), min(Z - 1, max(int(z0), int(z1)))
    grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center (requires even X dimension)."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


def set_voxel(grid, x, y, z, col):
    """Set a single voxel safely if within bounds."""
    X, Y, Z = grid.shape
    ix, iy, iz = int(round(x)), int(round(y)), int(round(z))
    if 0 <= ix < X and 0 <= iy < Y and 0 <= iz < Z:
        grid[ix, iy, iz] = col


def draw_line_6conn(grid, p0, p1, col, thickness=0, thick_z=0):
    """Draw a strictly 6-connected voxel path between 3D points p0 and p1."""
    x0, y0, z0 = [int(round(v)) for v in p0]
    x1, y1, z1 = [int(round(v)) for v in p1]
    cx, cy, cz = x0, y0, z0

    def stamp(px, py, pz):
        if thickness == 0 and thick_z == 0:
            set_voxel(grid, px, py, pz, col)
        else:
            fill_box(grid, px - thickness, px + thickness, py - thickness, py + thickness, pz - thick_z, pz + thick_z, col)

    stamp(cx, cy, cz)
    steps = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) * 3 + 1
    for i in range(1, steps + 1):
        t = i / steps
        tx = int(round(x0 + (x1 - x0) * t))
        ty = int(round(y0 + (y1 - y0) * t))
        tz = int(round(z0 + (z1 - z0) * t))
        while cx != tx or cy != ty or cz != tz:
            dx, dy, dz = abs(tx - cx), abs(ty - cy), abs(tz - cz)
            if dx >= dy and dx >= dz and cx != tx:
                cx += 1 if tx > cx else -1
            elif dy >= dz and cy != ty:
                cy += 1 if ty > cy else -1
            elif cz != tz:
                cz += 1 if tz > cz else -1
            stamp(cx, cy, cz)


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


def check_6_connected(grid):
    """Return the number of 6-connected components in the non-empty voxel grid."""
    X, Y, Z = grid.shape
    xs, ys, zs = np.nonzero(grid)
    if len(xs) == 0:
        return 0
    visited = np.zeros_like(grid, dtype=bool)
    components = 0
    for sx, sy, sz in zip(xs, ys, zs):
        if visited[sx, sy, sz]:
            continue
        components += 1
        q = deque([(int(sx), int(sy), int(sz))])
        visited[sx, sy, sz] = True
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < X and 0 <= ny < Y and 0 <= nz < Z and not visited[nx, ny, nz] and grid[nx, ny, nz] > 0:
                    visited[nx, ny, nz] = True
                    q.append((nx, ny, nz))
    return components


# ============================================================
# FORM A: DATE SHIGEZANE ROBOT (46 x 26 x 50)
# ============================================================
def build_a():
    grid = np.zeros((46, 26, 50), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 22 (-X, robot left, viewer right)
    cx_r = X // 2      # 23 (+X, robot right, viewer left)

    # --- GROUNDED SAMURAI ARMORED BOOTS / SABATONS (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 8, 16, 0, 2, 1)       # Kuro-urushi charcoal-black boot body
    fill_sym_box(grid, 4, 5, 10, 15, 1, 2, 3)      # Crimson carapace instep plate
    fill_sym_box(grid, 4, 5, 15, 17, 1, 2, 5)      # Gleaming gold samurai toe cap
    fill_sym_box(grid, 3, 3, 16, 17, 0, 1, 6)      # Inner golden-amber centipede toe claw
    fill_sym_box(grid, 6, 6, 16, 17, 0, 1, 6)      # Outer golden-amber centipede toe claw
    fill_sym_box(grid, 4, 5, 7, 8, 0, 2, 2)        # Gunmetal heel spur stabilizer
    fill_sym_box(grid, 3, 5, 9, 14, 3, 4, 2)       # Gunmetal ankle joint

    # --- SEGMENTED CENTIPEDE GREAVES / LOWER LEGS (Z: 4..14) ---
    fill_sym_box(grid, 3, 5, 9, 13, 4, 14, 1)      # Kuro-urushi black inner shin armor
    # 3 distinct overlapping crimson-red & gold centipede carapace rings around black shins!
    for rz in (5, 8, 11):
        fill_sym_box(grid, 3, 6, 9, 14, rz, rz + 1, 3)       # Crimson carapace ring
        fill_sym_box(grid, 4, 5, 14, 14, rz, rz, 9)          # Vermilion dorsal ridge
        fill_sym_box(grid, 3, 6, 14, 14, rz + 1, rz + 1, 5)  # Gleaming gold upper edge
        fill_sym_box(grid, 6, 6, 9, 13, rz, rz, 4)           # Deep carmine side flange
        fill_sym_box(grid, 3, 6, 8, 8, rz, rz + 1, 4)        # Rear calf carapace wrap
        fill_sym_box(grid, 4, 5, 8, 8, rz + 1, rz + 1, 5)    # Rear gold edge
        # Crisp black inter-ring gap below each ring
        fill_sym_box(grid, 3, 5, 13, 14, rz - 1, rz - 1, 1)
        # Tucked golden-amber centipede flank legs folded along outer greaves!
        fill_sym_box(grid, 7, 7, 10, 12, rz + 1, rz + 1, 6)
        fill_sym_box(grid, 7, 7, 10, 11, rz, rz, 6)
        fill_sym_box(grid, 7, 7, 12, 12, rz + 1, rz + 1, 5)

    # Pointed Black & Gold Samurai Knee Armor (Z: 13..16)
    fill_sym_box(grid, 3, 5, 13, 15, 13, 15, 1)
    fill_sym_box(grid, 4, 5, 14, 15, 14, 15, 3)
    fill_sym_box(grid, 4, 4, 15, 16, 14, 15, 5)    # Gold knee crest

    # --- BLACK-ARMORED THIGHS & LAYERED KUSAZURI TASSETS (Z: 15..22) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 19, 1)     # Kuro-urushi charcoal-black thighs
    fill_sym_box(grid, 3, 5, 10, 12, 16, 18, 2)    # Gunmetal knee-hip pistons
    fill_sym_box(grid, 4, 5, 13, 14, 16, 18, 1)    # Black haidate front thigh plates
    fill_sym_box(grid, 4, 5, 14, 14, 17, 17, 5)    # Gold thigh trim line

    # Pelvis Core & Segmented Samurai Kusazuri Skirt (Z: 18..22)
    fill_sym_box(grid, 0, 5, 9, 14, 19, 22, 1)     # Solid kuro-urushi black waist core
    # Front central codpiece / loin guard
    fill_sym_box(grid, 0, 1, 14, 15, 18, 21, 1)
    fill_sym_box(grid, 0, 1, 15, 15, 19, 20, 3)
    fill_sym_box(grid, 0, 1, 15, 15, 18, 18, 5)
    fill_sym_box(grid, 0, 0, 15, 16, 20, 21, 5)    # Gold Date waist crest
    fill_sym_box(grid, 0, 0, 16, 16, 20, 20, 8)    # Glowing emerald waist gem
    # Side & front flared segmented kusazuri plates (black + crimson + gold hem)
    fill_sym_box(grid, 2, 6, 9, 14, 20, 21, 1)
    fill_sym_box(grid, 2, 6, 9, 14, 19, 19, 3)
    fill_sym_box(grid, 2, 6, 9, 14, 18, 18, 4)
    fill_sym_box(grid, 2, 6, 14, 14, 18, 18, 5)    # Gold bottom front skirt trim
    fill_sym_box(grid, 6, 7, 9, 13, 18, 20, 3)     # Outer hip carapace flank
    fill_sym_box(grid, 7, 7, 10, 12, 18, 18, 5)    # Gold outer hip trim
    fill_sym_box(grid, 7, 7, 10, 12, 19, 19, 6)    # Tucked golden hip centipede leg
    # Rear kusazuri skirt plates
    fill_sym_box(grid, 0, 5, 8, 8, 18, 20, 1)
    fill_sym_box(grid, 0, 5, 8, 8, 19, 19, 3)
    fill_sym_box(grid, 0, 5, 8, 8, 18, 18, 5)

    # --- HEROIC DATE-CLAN TORSO WITH SEGMENTED CENTIPEDE CARAPACE BANDS (Z: 22..32) ---
    # Tapered black samurai abdomen with crimson odoshi cords
    fill_sym_box(grid, 0, 4, 9, 14, 22, 24, 1)
    fill_sym_box(grid, 0, 3, 14, 15, 22, 24, 1)
    fill_sym_box(grid, 0, 2, 15, 15, 22, 22, 5)    # Gold belt buckle bar
    fill_sym_box(grid, 1, 3, 14, 15, 23, 23, 3)    # Crimson waist cord lacing
    # Tucked golden-amber centipede legs hugging the waist flanks!
    fill_sym_box(grid, 5, 5, 10, 13, 22, 24, 6)
    fill_sym_box(grid, 5, 5, 13, 13, 23, 23, 5)

    # Broad Kuro-Urushi Black Samurai Chest overlaid with Crimson & Gold Centipede Bands (Z: 25..31)
    fill_sym_box(grid, 0, 6, 8, 15, 25, 31, 1)     # Kuro-urushi black armor cuirass (Do)
    # Three crisp crimson-red centipede carapace bands separated by black lacquer grooves!
    for bz in (25, 28, 30):
        fill_sym_box(grid, 0, 5, 14, 16, bz, bz, 3)        # Vivid crimson carapace band
        fill_sym_box(grid, 1, 4, 16, 16, bz, bz, 9 if bz == 30 else 3)
        fill_sym_box(grid, 5, 6, 10, 14, bz, bz, 4)        # Deep carmine side wrap
    # Gold edge trim along bottom & top pectoral bands + central sternum ridge
    fill_sym_box(grid, 0, 5, 15, 15, 26, 26, 5)
    fill_sym_box(grid, 0, 5, 15, 15, 29, 29, 5)
    fill_sym_box(grid, 0, 1, 15, 16, 25, 31, 5)    # Central golden sternum spine
    fill_sym_box(grid, 0, 0, 16, 17, 28, 29, 8)    # Glowing emerald samurai core
    fill_sym_box(grid, 0, 1, 16, 16, 27, 27, 1)
    fill_sym_box(grid, 0, 1, 16, 16, 30, 30, 5)
    # High black-and-gold samurai gorget / collar
    fill_sym_box(grid, 0, 4, 9, 14, 31, 32, 1)
    fill_sym_box(grid, 2, 4, 13, 15, 31, 32, 5)    # Gold collar lapels

    # --- CENTIPEDE CARAPACE BACKPACK & TAIL PINCERS (Y: 4..8, Z: 21..35) ---
    fill_sym_box(grid, 0, 4, 6, 8, 22, 31, 1)      # Charcoal backpack mount
    for pz in (22, 25, 28):
        fill_sym_box(grid, 0, 4, 5, 7, pz, pz + 1, 3)      # Crimson dorsal carapace plates
        fill_sym_box(grid, 0, 2, 4, 5, pz, pz + 1, 9)      # Vermilion dorsal spine ridge
        fill_sym_box(grid, 0, 4, 5, 5, pz + 1, pz + 1, 5)  # Gold carapace rim
        # Folded golden-amber centipede legs tucked cleanly on backpack flanks!
        fill_sym_box(grid, 5, 5, 6, 7, pz, pz + 1, 6)
        fill_sym_box(grid, 5, 5, 5, 5, pz + 1, pz + 1, 5)
    # Twin upturned rear centipede tail pincers (cerci) rising behind the shoulders!
    fill_sym_box(grid, 2, 3, 5, 6, 30, 32, 4)
    fill_sym_box(grid, 3, 3, 4, 5, 32, 34, 6)
    fill_sym_box(grid, 4, 4, 4, 4, 34, 35, 5)

    # --- MASSIVE SEGMENTED CENTIPEDE SHOULDER PAULDRONS / SODE (Z: 26..35) ---
    fill_sym_box(grid, 6, 8, 10, 13, 28, 31, 2)    # Heavy gunmetal shoulder axle
    # Tiered arched black, crimson-red & gold centipede carapace pauldrons
    fill_sym_box(grid, 6, 10, 9, 14, 32, 33, 3)    # Upper crimson carapace tier
    fill_sym_box(grid, 7, 10, 10, 13, 34, 34, 9)   # Vermilion top carapace crest
    fill_sym_box(grid, 6, 11, 9, 14, 33, 33, 5)    # Gleaming gold upper flange
    fill_sym_box(grid, 10, 11, 9, 14, 34, 34, 5)   # Flared samurai sode gold wingtip
    # Black lacquer groove between upper & mid sode plates
    fill_sym_box(grid, 7, 10, 9, 14, 31, 31, 1)
    # Mid crimson carapace ring of pauldron
    fill_sym_box(grid, 7, 11, 9, 14, 29, 30, 3)
    fill_sym_box(grid, 11, 11, 9, 14, 30, 30, 5)   # Gold segment rim
    fill_sym_box(grid, 8, 10, 9, 14, 28, 28, 1)    # Black lacquer groove
    # Lower crimson carapace ring of pauldron
    fill_sym_box(grid, 8, 11, 9, 14, 26, 27, 3)
    fill_sym_box(grid, 8, 11, 9, 14, 26, 26, 5)    # Gold lower trim
    # Tucked golden-amber centipede legs curving along outer edge of both pauldrons!
    for sz in (27, 30, 32):
        fill_sym_box(grid, 12, 12, 10, 12, sz, sz, 6)
        fill_sym_box(grid, 12, 12, 11, 12, sz - 1, sz - 1, 6)
        fill_sym_box(grid, 12, 12, 13, 13, sz, sz, 5)

    # --- ARMS & GAUNTLETS (Z: 15..28) ---
    # Black-armored upper arms descending inside pauldrons
    fill_sym_box(grid, 8, 9, 10, 12, 23, 28, 1)
    fill_sym_box(grid, 8, 9, 10, 12, 24, 25, 2)    # Gunmetal elbow joint

    # RIGHT ARM (+X, viewer's left): Samurai forearm angled cleanly outward to hold War Spear!
    fill_box(grid, cx_r + 8, cx_r + 10, 10, 14, 17, 22, 1)     # Black inner forearm
    fill_box(grid, cx_r + 9, cx_r + 11, 10, 14, 18, 22, 3)     # Crimson carapace vambrace
    fill_box(grid, cx_r + 10, cx_r + 11, 11, 13, 19, 21, 9)    # Vermilion arm plate ridge
    fill_box(grid, cx_r + 9, cx_r + 11, 10, 14, 18, 18, 5)     # Gold wrist cuff
    # Extended armored right wrist & fist holding war spear clear of shoulder pauldron!
    fill_box(grid, cx_r + 9, cx_r + 13, 12, 15, 15, 17, 1)     # Armored samurai right hand
    fill_box(grid, cx_r + 11, cx_r + 13, 14, 16, 15, 17, 2)    # Gripping knuckles

    # Heavy Date-Clan War Spear / Naginata held proudly at x = cx_r + 15 (clear of pauldron!)
    fill_box(grid, cx_r + 13, cx_r + 15, 15, 16, 15, 17, 5)    # Golden grip collar (6-conn!)
    # Long black & crimson lacquered spear shaft (Z: 2..34)
    fill_box(grid, cx_r + 15, cx_r + 15, 15, 16, 3, 34, 1)
    for wz in (7, 11, 21, 25, 29):
        fill_box(grid, cx_r + 15, cx_r + 15, 15, 16, wz, wz + 1, 3)  # Crimson shaft wrapping
    fill_box(grid, cx_r + 15, cx_r + 15, 15, 16, 1, 3, 5)      # Golden butt-cap finial
    fill_box(grid, cx_r + 15, cx_r + 15, 15, 16, 32, 35, 5)    # Golden spear collar (habaki)
    # Twin centipede-mandible golden cross-guard prongs!
    fill_box(grid, cx_r + 14, cx_r + 16, 14, 17, 34, 35, 5)
    fill_box(grid, cx_r + 15, cx_r + 15, 17, 18, 35, 36, 6)
    fill_box(grid, cx_r + 15, cx_r + 15, 13, 14, 35, 36, 6)
    # Broad Sweeping Forged-Steel War Blade (Z: 36..48)
    fill_box(grid, cx_r + 15, cx_r + 15, 15, 16, 36, 44, 2)    # Gunmetal blade spine
    fill_box(grid, cx_r + 15, cx_r + 15, 16, 18, 36, 44, 7)    # Gleaming forged-steel cutting edge
    fill_box(grid, cx_r + 15, cx_r + 15, 17, 19, 43, 46, 7)    # Sweeping curved naginata belly
    fill_box(grid, cx_r + 15, cx_r + 15, 18, 19, 46, 48, 7)    # Razor upward spear tip

    # LEFT ARM (-X, viewer's right): Segmented Centipede Carapace Gauntlet Shield
    fill_box(grid, cx_l - 10, cx_l - 8, 10, 14, 17, 22, 1)     # Black inner forearm
    fill_box(grid, cx_l - 11, cx_l - 9, 10, 14, 18, 22, 3)     # Crimson carapace vambrace
    fill_box(grid, cx_l - 10, cx_l - 8, 11, 14, 15, 17, 1)     # Left armored fist
    fill_box(grid, cx_l - 10, cx_l - 9, 14, 15, 15, 16, 5)     # Gold knuckle plate
    # Curved Centipede Carapace Buckler mounted on outer left arm
    fill_box(grid, cx_l - 12, cx_l - 11, 10, 16, 16, 24, 3)    # Vivid crimson shield body
    fill_box(grid, cx_l - 12, cx_l - 12, 11, 15, 17, 23, 9)    # Vermilion raised carapace dome
    fill_box(grid, cx_l - 12, cx_l - 11, 10, 16, 16, 16, 5)    # Bottom gold rim
    fill_box(grid, cx_l - 12, cx_l - 11, 10, 16, 20, 20, 5)    # Mid gold carapace seam
    fill_box(grid, cx_l - 12, cx_l - 11, 10, 16, 24, 24, 5)    # Top gold rim
    # Twin menacing claw pincers jutting forward from gauntlet shield!
    fill_box(grid, cx_l - 12, cx_l - 11, 16, 18, 17, 18, 6)
    fill_box(grid, cx_l - 12, cx_l - 12, 18, 19, 17, 17, 7)
    fill_box(grid, cx_l - 12, cx_l - 11, 16, 18, 22, 23, 6)
    fill_box(grid, cx_l - 12, cx_l - 12, 18, 19, 23, 23, 7)

    # --- SAMURAI KABUTO HELMET & SIGNATURE GIANT GOLDEN CENTIPEDE CREST (大ムカデ前立て) (Z: 32..49) ---
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 2)    # Armored neck column
    # Black Kuro-Urushi Kabuto Dome & Wide Flared Shikoro Neck Guard
    fill_sym_box(grid, 0, 3, 9, 14, 34, 39, 1)     # Kuro-urushi black helmet bowl
    fill_sym_box(grid, 0, 2, 10, 13, 40, 40, 1)    # Rounded kabuto crown
    fill_sym_box(grid, 0, 4, 8, 12, 33, 36, 1)     # Wide flared samurai shikoro neck-guard
    fill_sym_box(grid, 0, 4, 8, 10, 35, 35, 2)     # Gunmetal shikoro rib
    fill_sym_box(grid, 0, 4, 8, 11, 34, 34, 3)     # Crimson odoshi lacing on shikoro
    fill_sym_box(grid, 0, 4, 8, 12, 33, 33, 5)     # Gold bottom shikoro rim
    # Fierce Samurai Faceplate (Menpo) & Glowing Emerald-Venom Eyes
    fill_sym_box(grid, 0, 2, 14, 15, 34, 35, 2)    # Gunmetal armored menpo mask
    fill_sym_box(grid, 0, 0, 15, 15, 34, 34, 5)    # Gold chin ornament
    fill_sym_box(grid, 0, 2, 14, 15, 36, 36, 8)    # Glowing emerald-venom samurai eyes!
    fill_sym_box(grid, 0, 3, 14, 15, 37, 37, 1)    # Deep black kabuto brow visor (mabizashi)
    fill_sym_box(grid, 0, 3, 15, 15, 37, 37, 5)    # Gold brow edge

    # SIGNATURE DATE SHIGEZANE GIANT GOLDEN CENTIPEDE CREST (大ムカデ前立て)!
    # Slender, sculpted, unmistakably segmented golden centipede arching boldly UP & FORWARD
    # from the black kabuto crown with crisp protruding golden leg pairs and sweeping antennae!
    # Tail anchor running over kabuto crown & forehead mount
    fill_sym_box(grid, 0, 0, 10, 15, 40, 41, 5)
    fill_sym_box(grid, 0, 1, 14, 15, 37, 39, 5)
    fill_sym_box(grid, 1, 2, 11, 11, 41, 41, 6)    # Rearmost tiny golden legs on crown
    fill_sym_box(grid, 1, 2, 13, 13, 41, 41, 6)
    # 6 crisp arching golden centipede body segments climbing Z: 40 -> 47, Y: 15 -> 21
    crest_segs = [
        # (y_c, z_c, leg_xoff, col_ring)
        (15, 40, 2, 5),
        (16, 41, 3, 6),
        (17, 43, 3, 5),
        (18, 44, 3, 6),
        (19, 46, 3, 5),
        (20, 47, 2, 6),
    ]
    for idx_c, (cy_c, cz_c, leg_xo, c_ring) in enumerate(crest_segs):
        # Connect smoothly to previous segment
        if idx_c > 0:
            py_c, pz_c = crest_segs[idx_c - 1][0], crest_segs[idx_c - 1][1]
            fill_sym_box(grid, 0, 0, py_c, cy_c, pz_c, cz_c, 5)
        fill_sym_box(grid, 0, 1, cy_c, cy_c, cz_c, cz_c, c_ring)
        fill_sym_box(grid, 0, 0, cy_c, cy_c, cz_c + 1, cz_c + 1, 5)
        # Distinct tiny protruding golden centipede legs fanning left & right!
        fill_sym_box(grid, 2, leg_xo, cy_c, cy_c, cz_c, cz_c, 5 if c_ring == 6 else 6)
    # Raised golden centipede crest head, tiny emerald eyes & sweeping wide antennae!
    fill_sym_box(grid, 0, 1, 21, 22, 47, 48, 5)
    fill_sym_box(grid, 1, 1, 22, 22, 48, 48, 8)    # Tiny glowing eyes on crest head
    # Sweeping golden antennae arching upward & outward (6-connected!)
    fill_sym_box(grid, 1, 2, 22, 23, 48, 48, 5)
    fill_sym_box(grid, 2, 2, 23, 23, 48, 49, 5)
    fill_sym_box(grid, 3, 4, 23, 24, 49, 49, 5)
    # Tiny forward golden crest mandibles
    fill_sym_box(grid, 1, 1, 23, 24, 47, 47, 6)

    # Hollow strictly interior voxels to keep count cleanly within 2,600-3,500
    hollow_interior_26(grid, 1, 47)

    return grid


# ============================================================
# FORM B: GIANT GOLD & RED CENTIPEDE (大ムカデ) (38 x 62 x 26)
# ============================================================
def build_b():
    grid = np.zeros((38, 62, 26), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 18.5

    # Spine points for 10 commanding, clearly-separated armored body segments curving
    # in a sleek dramatic S-bend with the front 3 segments rearing up into an attack pose!
    # Format: (x_center, y_center, z_center, rx, ry, rz, is_raised)
    segments = [
        # Rear segments (tail -> mid-body), grounded with crisp articulated legs on z=0
        (cx - 2.6,  9.5,  4.4, 3.4, 1.75, 2.2, False),  # 0: Rear tapered segment
        (cx - 4.4, 14.0,  4.6, 4.2, 1.85, 2.5, False),  # 1
        (cx - 4.0, 18.6,  4.8, 4.7, 1.90, 2.7, False),  # 2
        (cx - 1.6, 23.2,  5.0, 4.9, 1.90, 2.8, False),  # 3
        (cx + 1.8, 27.8,  5.0, 5.0, 1.90, 2.8, False),  # 4
        (cx + 4.4, 32.4,  5.0, 4.9, 1.90, 2.8, False),  # 5
        (cx + 4.2, 37.0,  5.2, 4.8, 1.90, 2.7, False),  # 6
        # Reared-up front attacking segments curving boldly upward!
        (cx + 2.2, 41.2,  7.4, 4.6, 1.85, 2.6, True),   # 7: Rearing arch
        (cx + 0.4, 44.8, 10.6, 4.4, 1.85, 2.5, True),   # 8: High chest segment
        (cx + 0.0, 48.2, 13.8, 4.1, 1.80, 2.4, True),   # 9: Neck collar segment
    ]

    # --- 1. CONTINUOUS KURO-URUSHI CHARCOAL-BLACK UNDER-SPINE & INTER-SEGMENT JOINTS ---
    # Clearly visible dark armored waist rings between every red-and-gold carapace plate!
    for i in range(len(segments) - 1):
        x0, y0, z0 = segments[i][0], segments[i][1], segments[i][2]
        x1, y1, z1 = segments[i + 1][0], segments[i + 1][1], segments[i + 1][2]
        for step in range(1, 8):
            t = step / 8.0
            jx = x0 + (x1 - x0) * t
            jy = y0 + (y1 - y0) * t
            jz = z0 + (z1 - z0) * t
            rx_j = 3.0 if (step in (3, 4, 5)) else 3.3
            rz_j = 2.0 if (step in (3, 4, 5)) else 2.2
            for ix in range(max(0, int(jx - 5)), min(X, int(jx + 6))):
                for iy in range(max(0, int(jy - 2)), min(Y, int(jy + 3))):
                    for iz in range(max(1, int(jz - 3)), min(Z, int(jz + 4))):
                        d2 = ((ix - jx) / rx_j) ** 2 + ((iy - jy) / 1.45) ** 2 + ((iz - jz) / rz_j) ** 2
                        if d2 <= 1.0:
                            grid[ix, iy, iz] = 2 if (iz >= jz + 0.7 and step == 4) else 1

    # --- 2. SCULPTED GLOSSY CRIMSON-RED & GOLD DORSAL CARAPACE PLATES (TERGITES) ---
    # Directly reuses the samurai robot's crimson-red plates edged in gleaming gold!
    for idx, (sx, sy, sz, rx, ry, rz, is_raised) in enumerate(segments):
        if idx == 0:
            tx, ty = segments[1][0] - sx, segments[1][1] - sy
        elif idx == len(segments) - 1:
            tx, ty = sx - segments[idx - 1][0], sy - segments[idx - 1][1]
        else:
            tx, ty = segments[idx + 1][0] - segments[idx - 1][0], segments[idx + 1][1] - segments[idx - 1][1]
        norm = max(1e-5, np.hypot(tx, ty))
        ux, uy = tx / norm, ty / norm       # Forward unit vector along spine
        nx, ny = uy, -ux                    # Right perpendicular unit vector

        for ix in range(max(0, int(sx - rx - 2)), min(X, int(sx + rx + 3))):
            for iy in range(max(0, int(sy - ry - 3)), min(Y, int(sy + ry + 4))):
                dx, dy = ix - sx, iy - sy
                along = dx * ux + dy * uy
                across = dx * nx + dy * ny
                if abs(along) > ry + 0.4 or abs(across) > rx + 0.4:
                    continue
                for iz in range(max(1, int(sz - rz - 1)), min(Z, int(sz + rz + 2))):
                    dz = iz - sz
                    d2 = (across / rx) ** 2 + (along / ry) ** 2 + (dz / rz) ** 2
                    if d2 <= 1.0:
                        if dz < -0.55:
                            # Kuro-urushi charcoal-black underbelly with gunmetal sternite plates
                            col = 2 if abs(across) < rx * 0.42 else 1
                        elif dz < 0.35 and abs(across) > rx * 0.72:
                            # Deep carmine armored side overhang with crisp gleaming gold tip
                            col = 5 if abs(across) > rx * 0.88 else 4
                        else:
                            # Glossy Crimson-Red Dorsal Carapace Plate edged cleanly in Gold!
                            is_gold_rim = (
                                along > ry * 0.56
                                or along < -ry * 0.62
                                or (abs(across) > rx * 0.84 and dz >= 0.1)
                            )
                            if is_gold_rim:
                                col = 5  # Crisp gleaming gold carapace rim!
                            elif abs(across) <= 1.05 and dz >= rz * 0.62:
                                col = 9  # Sleek vermilion dorsal spine ridge!
                            else:
                                col = 3  # Rich glossy crimson-red carapace!
                        grid[ix, iy, iz] = col

        # --- 3. CRISP, INDIVIDUALLY READABLE ARTICULATED GOLDEN-AMBER LEGS! ---
        for side in (-1, 1):
            stride = 0.55 if ((idx + (0 if side == 1 else 1)) % 2 == 0) else -0.45
            p_hip = (
                sx + side * nx * (rx - 1.1) + ux * (stride * 0.15),
                sy + side * ny * (rx - 1.1) + uy * (stride * 0.15),
                sz - 0.5,
            )
            if not is_raised:
                out_reach = 3.6 if idx > 0 else 2.8
                foot_reach = 5.4 if idx > 0 else 4.2
                p_knee = (
                    sx + side * nx * (rx + out_reach * 0.55) + ux * (stride * 0.55),
                    sy + side * ny * (rx + out_reach * 0.55) + uy * (stride * 0.55),
                    sz + 0.8,
                )
                p_ankle = (
                    sx + side * nx * (rx + foot_reach * 0.84) + ux * (stride * 0.9),
                    sy + side * ny * (rx + foot_reach * 0.84) + uy * (stride * 0.9),
                    1.6,
                )
                p_claw = (
                    sx + side * nx * (rx + foot_reach) + ux * (stride * 1.0),
                    sy + side * ny * (rx + foot_reach) + uy * (stride * 1.0),
                    0.0,
                )
                # Sleek arched femur -> golden-amber knee -> dark grounded claw (clear separation!)
                draw_line_6conn(grid, p_hip, p_knee, 6, thickness=0, thick_z=0)
                draw_line_6conn(grid, (p_hip[0], p_hip[1], p_hip[2] + 1), (p_knee[0], p_knee[1], p_knee[2]), 6, thickness=0)
                draw_line_6conn(grid, p_knee, p_ankle, 6, thickness=0)
                draw_line_6conn(grid, p_ankle, p_claw, 1, thickness=0)
                set_voxel(grid, p_claw[0], p_claw[1], 0, 1)
                set_voxel(grid, p_claw[0] - side * nx * 0.8, p_claw[1] - side * ny * 0.8, 0, 1)
                # Gleaming gold knee joint cap!
                set_voxel(grid, p_knee[0], p_knee[1], p_knee[2] + 1, 5)
            else:
                # Raised attacking front legs splayed cleanly outward & hooked forward!
                p_knee = (
                    sx + side * nx * (rx + 2.8) + ux * 0.8,
                    sy + side * ny * (rx + 2.8) + uy * 0.8,
                    sz + 0.9,
                )
                p_tip = (
                    sx + side * nx * (rx + 4.2) + ux * 2.8,
                    sy + side * ny * (rx + 4.2) + uy * 2.8,
                    sz - 2.4,
                )
                draw_line_6conn(grid, p_hip, p_knee, 6, thickness=0)
                draw_line_6conn(grid, (p_hip[0], p_hip[1], p_hip[2] + 1), (p_knee[0], p_knee[1], p_knee[2]), 6, thickness=0)
                draw_line_6conn(grid, p_knee, p_tip, 6, thickness=0)
                set_voxel(grid, p_knee[0], p_knee[1], p_knee[2] + 1, 5)
                set_voxel(grid, p_tip[0], p_tip[1], p_tip[2], 7)

    # --- 4. REAR TAIL SEGMENT & MENACING TWIN TAIL FORCEPS / UROPODS (Y: 1..9, Z: 2..9) ---
    tx0, ty0, tz0 = segments[0][0], segments[0][1], segments[0][2]
    fill_box(grid, tx0 - 2.4, tx0 + 2.4, ty0 - 3.2, ty0 - 1, tz0 - 1, tz0 + 1.4, 3)
    fill_box(grid, tx0 - 2.4, tx0 + 2.4, ty0 - 3.2, ty0 - 3.2, tz0 + 1, tz0 + 1.4, 5)
    fill_box(grid, tx0 - 1.5, tx0 + 1.5, ty0 - 3.2, ty0 - 1, tz0 - 2, tz0 - 1, 1)
    for side in (-1, 1):
        tp0 = (tx0 + side * 1.5, ty0 - 2.6, tz0)
        tp1 = (tx0 + side * 3.4, ty0 - 5.2, tz0 + 1.2)
        tp2 = (tx0 + side * 4.2, ty0 - 7.6, tz0 + 2.8)
        tp3 = (tx0 + side * 2.4, ty0 - 8.6, tz0 + 3.6)
        draw_line_6conn(grid, tp0, tp1, 4, thickness=0, thick_z=1)
        draw_line_6conn(grid, tp1, tp2, 6, thickness=0)
        draw_line_6conn(grid, tp2, tp3, 5, thickness=0)
        set_voxel(grid, tp3[0], tp3[1], tp3[2], 7)

    # --- 5. FIERCE ARMORED CENTIPEDE HEAD, GLOWING EYES, MANDIBLES & SWEPT ANTENNAE (Y: 49..61, Z: 12..25) ---
    hx, hy, hz = cx, 52.4, 15.8
    # Dark armored neck joint bridging segment 9 to head
    draw_line_6conn(grid, (segments[-1][0], segments[-1][1], segments[-1][2]), (hx, hy - 1.8, hz), 1, thickness=1, thick_z=1)

    # Broad armored centipede head shield (echoing Date Shigezane's black/crimson/gold kabuto!)
    for ix in range(int(hx - 6), int(hx + 7)):
        for iy in range(int(hy - 4), int(hy + 5)):
            for iz in range(int(hz - 3), int(hz + 5)):
                if not (0 <= ix < X and 0 <= iy < Y and 0 <= iz < Z):
                    continue
                d2 = ((ix - hx) / 4.8) ** 2 + ((iy - hy) / 3.3) ** 2 + ((iz - hz) / 2.8) ** 2
                if d2 <= 1.0:
                    if iz < hz - 0.8:
                        col = 1  # Dark kuro-urushi armored jaw base
                    elif abs(ix - hx) <= 1.2 and iz >= hz + 1.4:
                        col = 5  # Gleaming gold Date-clan crown crest stripe
                    elif iy >= hy + 2.0 and iz >= hz + 0.2:
                        col = 5  # Gold armored brow trim
                    elif iz >= hz + 0.4:
                        col = 3  # Vivid crimson head carapace dome
                    else:
                        col = 4  # Deep carmine armored cheeks
                    grid[ix, iy, iz] = col

    # Glowing Emerald-Venom Centipede Eye Clusters framed by dark samurai brow ridges!
    for side in (-1, 1):
        ex = int(round(hx + side * 3.8))
        fill_box(grid, ex, ex, int(hy + 1), int(hy + 2.5), int(hz + 0.2), int(hz + 1.5), 8)
        set_voxel(grid, ex + side * 0.5, hy + 1.5, hz + 1.0, 8)
        fill_box(grid, ex - 1, ex + 1, int(hy + 1), int(hy + 2.5), int(hz + 2.2), int(hz + 2.2), 1)

    # Raised golden Date-clan kabuto crest ridge atop head
    fill_box(grid, hx - 1.2, hx + 1.2, hy - 2.2, hy + 1.2, hz + 2.4, hz + 3.2, 5)
    fill_box(grid, hx - 0.4, hx + 0.4, hy - 2.0, hy + 1.8, hz + 3.2, hz + 3.4, 9)

    # MENACING CURVED PINCER MANDIBLES (TOXICOGNATHS) — reusing the robot's forged-steel war blade!
    for side in (-1, 1):
        m0 = (hx + side * 2.8, hy + 2.0, hz - 1.2)
        m1 = (hx + side * 4.8, hy + 4.4, hz - 2.0)
        m2 = (hx + side * 4.2, hy + 6.8, hz - 1.4)
        m3 = (hx + side * 1.8, hy + 7.8, hz - 0.6)
        draw_line_6conn(grid, m0, m1, 6, thickness=0, thick_z=1)
        draw_line_6conn(grid, (m0[0], m0[1], m0[2] + 1), (m1[0], m1[1], m1[2] + 1), 1, thickness=0)
        draw_line_6conn(grid, m1, m2, 5, thickness=0, thick_z=1)
        draw_line_6conn(grid, (m1[0], m1[1], m1[2] + 1), (m2[0], m2[1], m2[2] + 1), 7, thickness=0)
        draw_line_6conn(grid, m2, m3, 7, thickness=0)
        set_voxel(grid, hx + side * 3.0, hy + 6.0, hz - 1.2, 7)

    # LONG GRACEFULLY ARCHING GOLDEN ANTENNAE — sweeping upward, forward, & back in proud arcs!
    for side in (-1, 1):
        a0 = (hx + side * 1.6, hy + 2.4, hz + 1.6)
        a1 = (hx + side * 3.6, hy + 4.6, hz + 4.4)
        a2 = (hx + side * 6.4, hy + 5.6, hz + 6.8)
        a3 = (hx + side * 9.6, hy + 4.6, hz + 8.4)
        a4 = (hx + side * 12.2, hy + 2.2, hz + 8.8)
        draw_line_6conn(grid, a0, a1, 5, thickness=0, thick_z=1)
        draw_line_6conn(grid, a1, a2, 6, thickness=0)
        draw_line_6conn(grid, a2, a3, 5, thickness=0)
        draw_line_6conn(grid, a3, a4, 5, thickness=0)
        set_voxel(grid, a1[0], a1[1], a1[2] + 1, 5)

    # Hollow strictly interior voxels of body segments & head to stay cleanly in 2,000-3,400
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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=34, pitch_a=20, yaw_b=46, pitch_b=28):
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
    c_a = check_6_connected(model_a)
    c_b = check_6_connected(model_b)
    v_a = export_vox(model_a, "shigezane_a.vox")
    v_b = export_vox(model_b, "shigezane_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: DATE SHIGEZANE ROBOT -> GIANT CENTIPEDE",
        "1. DATE SHIGEZANE ROBOT",
        "2. GIANT GOLD & RED CENTIPEDE",
        "preview_shigezane.png",
        yaw_a=34, pitch_a=20, yaw_b=40, pitch_b=26,
    )
    print(f"shigezane: A={v_a} voxels {model_a.shape} (6-conn={c_a}, z0={np.count_nonzero(model_a[:,:,0])}), "
          f"B={v_b} voxels {model_b.shape} (6-conn={c_b}, z0={np.count_nonzero(model_b[:,:,0])})")
