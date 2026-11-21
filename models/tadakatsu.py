import struct
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across Honda Tadakatsu Robot (Form A) and Armored Battle Stag (Form B)
PALETTE = {
    1: (44, 48, 58, 255),     # Jet-Black Lacquered Armor (Kuro-ito-odoshi)
    2: (76, 84, 98, 255),     # Glossy Obsidian / Dark Steel Bevels, Joints & Hooves
    3: (138, 76, 44, 255),    # Rich Chestnut Stag Coat / Dark Lacquered Wood
    4: (204, 134, 56, 255),   # Warm Amber-Wood Prayer Beads (O-Juzu) & Antler Roots
    5: (244, 194, 54, 255),   # Burnished Gold Trim & Towering Deer Antlers (Kazuno)
    6: (228, 236, 246, 255),  # Gleaming Silver Tonbokiri Spearhead & Blade Plates
    7: (162, 174, 190, 255),  # Cool Steel Blade Fuller & Metallic Accents
    8: (246, 244, 236, 255),  # Pure Ivory-White Tail Underside & Battle Cords
    9: (228, 54, 44, 255),    # Crimson Eyes, Agemaki Knot & Spear Tassel
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


def fill_sym_line(grid, p0, p1, col, thickness=1):
    """Draw a guaranteed 6-connected symmetrical stepped line between (x_off, y, z) points."""
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    steps = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1) * 3
    prev = (x0, y0, z0)
    fill_sym_box(grid, x0, x0 + thickness - 1, y0, y0 + thickness - 1, z0, z0 + thickness - 1, col)
    for i in range(1, steps + 1):
        t = i / steps
        nx = int(round(x0 + (x1 - x0) * t))
        ny = int(round(y0 + (y1 - y0) * t))
        nz = int(round(z0 + (z1 - z0) * t))
        px, py, pz = prev
        # Step one axis at a time to guarantee strict 6-connectivity
        while (px, py, pz) != (nx, ny, nz):
            if px != nx:
                px += 1 if nx > px else -1
            elif py != ny:
                py += 1 if ny > py else -1
            elif pz != nz:
                pz += 1 if nz > pz else -1
            fill_sym_box(
                grid,
                px, px + thickness - 1,
                py, py + thickness - 1,
                pz, pz + thickness - 1,
                col,
            )
        prev = (nx, ny, nz)


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


def add_tadakatsu_antlers(grid, x_root, y_root, z_root):
    """
    Build Tadakatsu's unmistakable towering golden-amber branching deer antlers.
    Shared directly between Robot A's kabuto and Stag B's crown!
    All branches are strictly 6-connected with graceful tapered tines.
    """
    # Stout amber-wood pedicle / antler root socket
    fill_sym_box(grid, x_root, x_root + 1, y_root, y_root + 1, z_root, z_root + 1, 4)
    fill_sym_line(grid, (x_root + 1, y_root, z_root + 1), (x_root + 3, y_root - 1, z_root + 2), 4, thickness=2)

    # Graceful sweeping main beam: arcs outward, gently back, then curves tall & inward at the crown
    fill_sym_line(grid, (x_root + 3, y_root - 1, z_root + 2), (x_root + 6, y_root - 2, z_root + 5), 5, thickness=1)
    fill_sym_line(grid, (x_root + 3, y_root - 1, z_root + 3), (x_root + 6, y_root - 2, z_root + 6), 5, thickness=1)
    fill_sym_line(grid, (x_root + 6, y_root - 2, z_root + 6), (x_root + 8, y_root - 2, z_root + 9), 5, thickness=1)
    fill_sym_line(grid, (x_root + 6, y_root - 1, z_root + 6), (x_root + 8, y_root - 1, z_root + 9), 5, thickness=1)
    fill_sym_line(grid, (x_root + 8, y_root - 1, z_root + 9), (x_root + 8, y_root, z_root + 12), 5, thickness=1)
    fill_sym_line(grid, (x_root + 8, y_root, z_root + 12), (x_root + 7, y_root + 1, z_root + 14), 5, thickness=1)

    # Tine 1: Forward-curving brow tine sweeping boldly forward & up
    fill_sym_line(grid, (x_root + 3, y_root, z_root + 2), (x_root + 4, y_root + 3, z_root + 4), 5, thickness=1)
    fill_sym_line(grid, (x_root + 4, y_root + 3, z_root + 4), (x_root + 3, y_root + 4, z_root + 7), 5, thickness=1)

    # Tine 2: Mid-forward trez tine branching high & forward
    fill_sym_line(grid, (x_root + 6, y_root - 1, z_root + 6), (x_root + 6, y_root + 2, z_root + 9), 5, thickness=1)
    fill_sym_line(grid, (x_root + 6, y_root + 2, z_root + 9), (x_root + 5, y_root + 3, z_root + 12), 5, thickness=1)

    # Tine 3: Outer royal tine flaring gracefully outward & high
    fill_sym_line(grid, (x_root + 8, y_root - 2, z_root + 9), (x_root + 10, y_root - 2, z_root + 12), 5, thickness=1)
    fill_sym_line(grid, (x_root + 10, y_root - 2, z_root + 12), (x_root + 10, y_root - 1, z_root + 14), 5, thickness=1)

    # Tine 4: Inner rear crown fork
    fill_sym_line(grid, (x_root + 8, y_root - 1, z_root + 10), (x_root + 6, y_root - 3, z_root + 13), 5, thickness=1)


# ==========================================
# FORM A: HONDA TADAKATSU ROBOT (46 x 26 x 55)
# ==========================================
def build_a():
    grid = np.zeros((46, 26, 55), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 22 (-X, robot left / viewer right)
    cx_r = X // 2      # 23 (+X, robot right / viewer left)

    # --- ARMORED SAMURAI BOOTS / WARAJI GREAVE FEET (Z: 0..3) ---
    fill_sym_box(grid, 2, 5, 8, 16, 0, 1, 2)     # Dark steel armored sole
    fill_sym_box(grid, 3, 5, 7, 9, 0, 2, 1)      # Lacquered heel guard
    fill_sym_box(grid, 2, 5, 9, 16, 1, 2, 1)     # Jet-black lacquered foot armor
    fill_sym_box(grid, 3, 4, 15, 17, 1, 2, 5)    # Burnished gold toe cap
    fill_sym_box(grid, 2, 5, 9, 15, 3, 3, 2)     # Steel ankle joint
    fill_sym_box(grid, 3, 4, 15, 15, 3, 3, 9)    # Crimson ankle cord tie

    # --- SUNEATE SHIN GREAVES & GOLD KNEE GUARDS (Z: 4..15) ---
    fill_sym_box(grid, 2, 5, 9, 14, 4, 13, 1)    # Black-lacquered cylindrical greaves
    fill_sym_box(grid, 3, 4, 14, 15, 5, 11, 2)   # Glossy front shin bevel
    # Gold vertical lacquer trim ribs & chestnut inner cord bands
    for rz in (5, 8, 11):
        fill_sym_box(grid, 2, 5, 10, 14, rz, rz, 2)
    fill_sym_box(grid, 5, 5, 11, 13, 5, 12, 5)   # Outer gold greave trim strip
    fill_sym_box(grid, 2, 2, 10, 13, 5, 13, 3)   # Inner chestnut lacing detail
    # Rear calf thruster / vent fin
    fill_sym_box(grid, 3, 4, 8, 9, 6, 11, 2)
    fill_sym_box(grid, 3, 4, 8, 8, 7, 9, 5)
    # Sculpted Samurai Knee Armor (Tateage)
    fill_sym_box(grid, 2, 5, 14, 16, 12, 15, 1)
    fill_sym_box(grid, 3, 5, 15, 16, 13, 15, 5)  # Burnished gold knee crest
    fill_sym_box(grid, 3, 4, 16, 16, 14, 14, 9)  # Crimson center stud

    # --- HAIDATE THIGHS (Z: 14..19) ---
    fill_sym_box(grid, 2, 5, 10, 14, 14, 19, 2)  # Dark steel frame
    fill_sym_box(grid, 3, 5, 11, 14, 15, 18, 1)  # Black armored thigh plates
    fill_sym_box(grid, 3, 4, 14, 15, 16, 18, 3)  # Chestnut quilted haidate front
    fill_sym_box(grid, 5, 5, 11, 13, 16, 18, 5)  # Outer gold thigh stripe

    # --- WAIST, OBI SASH & FLARED KUSAZURI TASSETS (Z: 18..24) ---
    fill_sym_box(grid, 0, 5, 9, 14, 19, 23, 2)   # Inner waist frame
    # Front, Side & Rear flared black-lacquered Kusazuri panels with gold lower borders
    fill_sym_box(grid, 2, 6, 13, 15, 18, 22, 1)  # Front-left/right tassets
    fill_sym_box(grid, 2, 6, 14, 15, 18, 19, 5)  # Gold lower border
    fill_sym_box(grid, 5, 6, 9, 14, 18, 22, 1)   # Side tassets
    fill_sym_box(grid, 6, 6, 9, 14, 18, 19, 5)   # Side gold trim
    fill_sym_box(grid, 1, 5, 8, 9, 18, 22, 1)    # Rear tassets
    fill_sym_box(grid, 1, 5, 8, 8, 18, 19, 5)    # Rear gold trim
    # Central groin armor & white/crimson war sash (Obi)
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 1)
    fill_sym_box(grid, 0, 1, 15, 16, 21, 22, 8)  # Crisp white obi wrap
    fill_sym_box(grid, 0, 0, 16, 16, 20, 22, 5)  # Burnished gold buckle crest
    fill_sym_box(grid, 0, 1, 14, 15, 19, 19, 5)
    # Rear crimson/white Agemaki bow knot at waist
    fill_sym_box(grid, 0, 1, 7, 8, 20, 22, 9)
    fill_sym_box(grid, 2, 2, 7, 7, 19, 21, 9)
    fill_sym_box(grid, 2, 2, 7, 7, 17, 18, 8)    # White tassel tips

    # --- KURO-ITO-ODOSHI TORSO / CUIRASS (Z: 23..34) ---
    # Tapered abdomen
    fill_sym_box(grid, 0, 4, 9, 14, 23, 25, 1)
    fill_sym_box(grid, 0, 3, 14, 15, 23, 25, 2)
    fill_sym_box(grid, 0, 2, 15, 15, 24, 24, 5)  # Gold waist trim band
    # Broad Heroic Samurai Chest Plate (Do) - Sleek Jet-Black Lacquer framing the O-Juzu beads!
    fill_sym_box(grid, 0, 6, 8, 15, 26, 33, 1)
    fill_sym_box(grid, 0, 5, 14, 16, 26, 32, 1)
    # Horizontal Kuro-ito lacquer lamellar ribs
    for cz in (27, 30):
        fill_sym_box(grid, 0, 5, 15, 16, cz, cz, 2)
    fill_sym_box(grid, 0, 4, 14, 15, 33, 33, 5)  # Subtle thin gold collar trim
    fill_sym_box(grid, 0, 1, 16, 16, 29, 31, 5)  # Gold Honda chest crest
    fill_sym_box(grid, 0, 0, 16, 16, 30, 30, 9)  # Crimson core jewel
    # Collar / Shoulder Mantle (Watagami)
    fill_sym_box(grid, 2, 5, 9, 14, 33, 34, 1)
    fill_sym_box(grid, 3, 5, 13, 14, 34, 34, 5)

    # --- ICONIC LARGE WOODEN/AMBER PRAYER BEADS (大数珠, O-JUZU) ---
    # Draped unmistakably in a bold, clearly separated chain of chunky amber-wood beads across the jet-black chest!
    front_beads = [
        # (x_off, y_front, z_center) - sweeping deep U-drape with crisp 1-voxel dark cord notches between beads
        (0, 17, 25),  # Lowest center bead (chunky 2x2 across centerline)
        (2, 17, 26),
        (4, 17, 28),
        (5, 16, 31),
        (5, 14, 33),  # Over shoulder top
        (5, 11, 34),
        (5, 8,  33),  # Over rear shoulder
    ]
    # Dark lacquered cord linking beads solidly to chest (100% 6-connected)
    fill_sym_line(grid, (0, 16, 25), (4, 16, 28), 1, thickness=1)
    fill_sym_line(grid, (4, 16, 28), (5, 15, 31), 1, thickness=1)
    fill_sym_line(grid, (5, 15, 31), (5, 13, 33), 1, thickness=1)
    fill_sym_line(grid, (5, 13, 33), (5, 8,  33), 1, thickness=1)
    for bx_off, by, bz in front_beads:
        if bx_off == 0:
            fill_sym_box(grid, 0, 1, by - 1, by, bz, bz + 1, 4)
            fill_sym_box(grid, 0, 0, by, by, bz, bz, 3)
        else:
            fill_sym_box(grid, bx_off, bx_off + 1, by - 1, by, bz, bz + 1, 4)
            fill_sym_box(grid, bx_off + 1, bx_off + 1, by, by, bz, bz, 3)

    # --- BACKPACK / SAMURAI BACKPLATE & FOLDED CREST RIDGE (Y: 5..8, Z: 24..34) ---
    fill_sym_box(grid, 0, 5, 6, 8, 25, 33, 1)
    fill_sym_box(grid, 0, 4, 5, 6, 26, 32, 2)
    # Rear prayer-bead drape across upper back
    fill_sym_line(grid, (0, 5, 28), (4, 6, 32), 3, thickness=1)
    for bx_off, by, bz in [(0, 5, 28), (2, 5, 29), (4, 6, 31)]:
        fill_sym_box(grid, bx_off, bx_off + 1, by - 1, by, bz, bz + 1, 4)
    # Silver dorsal blade spine mount (hints at Stag B's Tonbokiri back ridge!)
    fill_sym_box(grid, 0, 0, 4, 5, 25, 33, 6)
    fill_sym_box(grid, 0, 0, 5, 5, 26, 32, 7)
    # Crimson agemaki shoulder bow & gold upper vents on back
    fill_sym_box(grid, 2, 3, 5, 5, 25, 26, 5)
    fill_sym_box(grid, 1, 2, 4, 5, 32, 33, 9)

    # --- LAYERED O-SODE SAMURAI SHOULDER PAULDRONS (Z: 26..35, x_off: 6..11) ---
    fill_sym_box(grid, 6, 8, 10, 13, 29, 32, 2)  # Shoulder axle hub
    # Sweeping curved multi-tier black-lacquered O-Sode shields
    for tier, (z0, z1, x0, x1) in enumerate([
        (33, 35, 6, 9),
        (31, 32, 7, 10),
        (29, 30, 8, 11),
        (27, 28, 8, 11),
    ]):
        fill_sym_box(grid, x0, x1, 9, 14, z0, z1, 1)
        # Gold trim on outer/top edge of each sode tier
        fill_sym_box(grid, x1, x1, 9, 14, z0, z0, 5)
        if tier == 0:
            fill_sym_box(grid, x0, x1, 9, 14, z1, z1, 5)
        if tier == 2:
            fill_sym_box(grid, x1, x1, 11, 12, z0, z1, 9)  # Crimson sode cord stud

    # --- ARMS & ARMORED KOTE GAUNTLETS (Z: 15..29) ---
    # Upper arms descending inside sode
    fill_sym_box(grid, 7, 9, 10, 13, 23, 28, 2)
    fill_sym_box(grid, 8, 9, 10, 13, 24, 26, 3)  # Chestnut under-sleeve

    # LEFT ARM (-X, viewer's right): Armored Forearm + Sleek Silver/Black Flank Blade Guard
    fill_box(grid, cx_l - 10, cx_l - 7, 10, 14, 17, 22, 1)   # Black lacquer kote forearm
    fill_box(grid, cx_l - 10, cx_l - 10, 11, 13, 18, 21, 5)  # Gold outer cuff strip
    fill_box(grid, cx_l - 9, cx_l - 7, 10, 13, 15, 16, 2)    # Armored left fist
    fill_box(grid, cx_l - 9, cx_l - 8, 13, 14, 15, 16, 5)    # Gold knuckle guard
    # Sleek wrist-mounted black & silver blade-buckler (becomes Stag B's flank blade plate!)
    fill_box(grid, cx_l - 11, cx_l - 11, 11, 14, 16, 23, 1)
    fill_box(grid, cx_l - 12, cx_l - 11, 12, 13, 17, 24, 6)  # Gleaming silver blade edge
    fill_box(grid, cx_l - 11, cx_l - 11, 12, 13, 19, 20, 5)  # Gold center boss

    # RIGHT ARM (+X, viewer's left): Reaching proudly outward to hold TONBOKIRI cleanly clear of the antlers!
    fill_box(grid, cx_r + 7, cx_r + 10, 10, 14, 19, 23, 1)   # Right forearm armor
    fill_box(grid, cx_r + 10, cx_r + 10, 11, 13, 20, 22, 5)  # Gold forearm strip
    # Forearm angled outward (+X) & slightly forward (+Y) to grip the spear shaft with clear silhouette separation
    fill_box(grid, cx_r + 9, cx_r + 13, 12, 16, 18, 20, 1)
    fill_box(grid, cx_r + 12, cx_r + 15, 14, 17, 17, 19, 2)  # Armored hand gripping shaft
    fill_box(grid, cx_r + 13, cx_r + 15, 16, 17, 18, 19, 5)  # Gold gauntlet fingers

    # --- LEGENDARY SPEAR TONBOKIRI (蜻蛉切) (X: cx_r+14..16, Y: 14..17, Z: 0..54) ---
    sx = cx_r + 15  # x = 38 (cleanly separated from towering golden antlers!)
    sy = 15
    # Grounded gold butt-cap (Ishizuki) planted firmly on the battlefield at Z=0
    fill_box(grid, sx - 1, sx, sy, sy + 1, 0, 2, 5)
    # Long jet-black lacquered spear shaft with chestnut & gold spiral bindings (Z: 3..36)
    fill_box(grid, sx - 1, sx, sy, sy + 1, 3, 35, 1)
    for gz in (6, 11, 16, 22, 27, 32):
        fill_box(grid, sx - 1, sx, sy, sy + 1, gz, gz, 5)
    for wz in (8, 9, 24, 25, 29, 30):
        fill_box(grid, sx - 1, sx, sy, sy + 1, wz, wz, 3)
    # Ornate gold collar & flowing crimson/white tassel (Z: 35..38)
    fill_box(grid, sx - 1, sx + 1, sy - 1, sy + 2, 36, 37, 5)
    fill_box(grid, sx - 2, sx - 1, sy - 1, sy, 34, 36, 9)    # Crimson tassel streamer
    fill_box(grid, sx - 2, sx - 2, sy - 1, sy, 32, 33, 8)    # White tassel tip
    fill_box(grid, sx + 1, sx + 1, sy + 1, sy + 2, 34, 36, 9)
    # GLEAMING SILVER TONBOKIRI SPEARHEAD (Z: 38..54)
    blade_profile = [
        # (z, dx0, dx1, dy0, dy1)
        (38, -1, 1, -1, 2),
        (39, -1, 1, -1, 2),
        (40, -1, 1, -1, 2),
        (41, -1, 1, -1, 2),
        (42, -1, 1, -1, 2),
        (43, -1, 1,  0, 2),
        (44, -1, 1,  0, 2),
        (45, -1, 0,  0, 2),
        (46, -1, 0,  0, 2),
        (47, -1, 0,  0, 1),
        (48, -1, 0,  0, 1),
        (49, -1, 0,  0, 1),
        (50,  0, 0,  0, 1),
        (51,  0, 0,  0, 1),
        (52,  0, 0,  0, 0),
        (53,  0, 0,  0, 0),
        (54,  0, 0,  0, 0),
    ]
    for bz, dx0, dx1, dy0, dy1 in blade_profile:
        fill_box(grid, sx + dx0, sx + dx1, sy + dy0, sy + dy1, bz, bz, 6)
    # Cool steel central blade ridge (shinogi) along the spearhead for gleaming metallic bevel!
    for bz in range(38, 50):
        grid[sx, sy + 1, bz] = 7
        if bz <= 44:
            grid[sx - 1, sy, bz] = 7

    # --- SAMURAI KABUTO HEAD & TOWERING DEER ANTLERS (Z: 34..53) ---
    # Armored neck & gold gorget (Nodowa)
    fill_sym_box(grid, 0, 1, 10, 13, 33, 35, 2)
    fill_sym_box(grid, 0, 2, 13, 14, 34, 35, 5)
    # Kabuto Helmet Dome (Kuro-urushi black lacquer)
    fill_sym_box(grid, 0, 3, 9, 14, 36, 40, 1)
    fill_sym_box(grid, 0, 2, 10, 13, 41, 41, 1)
    fill_sym_box(grid, 0, 1, 10, 13, 42, 42, 2)  # Top tehen-kanamono ring
    fill_sym_box(grid, 0, 0, 11, 12, 42, 42, 5)  # Gold crown rivet
    # Sweeping Shikoro (tiered black-and-gold neck guard flaring out at sides & back)
    fill_sym_box(grid, 0, 4, 8, 12, 35, 37, 1)
    fill_sym_box(grid, 0, 4, 8, 11, 35, 35, 5)   # Gold lower shikoro trim
    fill_sym_box(grid, 3, 4, 11, 13, 36, 38, 1)  # Fukigaeshi ear turnbacks
    fill_sym_box(grid, 4, 4, 12, 13, 37, 38, 5)  # Gold ear-guard trim
    # Fierce Samurai Faceplate (Menpo) & Glowing Crimson Eyes
    fill_sym_box(grid, 0, 2, 14, 15, 35, 36, 2)  # Dark steel menpo jaw mask
    fill_sym_box(grid, 0, 0, 15, 15, 35, 35, 5)  # Gold chin crest
    fill_sym_box(grid, 1, 2, 14, 15, 37, 37, 9)  # Fierce glowing crimson eyes!
    fill_sym_box(grid, 0, 0, 14, 15, 37, 37, 1)  # Nasal bridge divider
    # Kabuto Visor Brim (Mabizashi) & Gold Forehead Crest
    fill_sym_box(grid, 0, 3, 14, 16, 38, 39, 1)
    fill_sym_box(grid, 0, 3, 15, 16, 38, 38, 5)  # Gold visor rim
    fill_sym_box(grid, 0, 0, 16, 16, 39, 41, 5)  # Central gold maedate ridge
    fill_sym_box(grid, 0, 0, 16, 16, 40, 40, 9)  # Crimson center dot

    # UNMISTAKABLE TOWERING GOLDEN-AMBER BRANCHING DEER ANTLERS (鹿角の兜そのまま!)
    add_tadakatsu_antlers(grid, x_root=2, y_root=12, z_root=39)

    # Hollow interior bulk to keep voxel count cleanly in target budget (~2,800-3,500)
    hollow_interior_26(grid, 1, 52)
    return grid


# ==========================================
# FORM B: ARMORED BATTLE STAG (30 x 44 x 49)
# ==========================================
def build_b():
    grid = np.zeros((30, 44, 49), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 14.5

    # --- FOUR SLENDER POWERFUL STAG LEGS (Z: 0..19) ---
    # Standing tall and regal!
    # Front Legs (Y: 25..28, x_off: 2..3) - straight, athletic, armored shins
    fill_sym_box(grid, 2, 3, 25, 27, 0, 1, 2)    # Dark cloven hooves
    fill_sym_box(grid, 2, 3, 27, 27, 0, 0, 1)    # Front hoof bevel
    fill_sym_box(grid, 2, 3, 25, 26, 2, 2, 5)    # Gold fetlock ring
    fill_sym_box(grid, 2, 3, 25, 26, 3, 9, 3)    # Chestnut lower cannon bone
    fill_sym_box(grid, 2, 3, 26, 27, 3, 10, 1)   # Black-lacquered front shin guard
    fill_sym_box(grid, 2, 3, 27, 27, 9, 10, 5)   # Gold knee cap!
    # Muscular upper forelegs & armored shoulders
    fill_sym_box(grid, 2, 4, 24, 27, 11, 16, 3)
    fill_sym_box(grid, 3, 4, 25, 27, 12, 16, 1)  # Black lacquer shoulder-guard plate
    fill_sym_box(grid, 4, 4, 25, 27, 12, 12, 5)  # Gold shoulder plate trim

    # Hind Legs (Y: 7..14, x_off: 2..4) - authentic deer angled hock & muscular thigh!
    fill_sym_box(grid, 2, 3, 8, 10, 0, 1, 2)     # Rear cloven hooves
    fill_sym_box(grid, 2, 3, 10, 10, 0, 0, 1)
    fill_sym_box(grid, 2, 3, 8, 9, 2, 2, 5)      # Gold rear fetlock ring
    # Slender angled hind cannon stepping gracefully back to the hock joint
    fill_sym_box(grid, 2, 3, 8, 9, 3, 6, 3)
    fill_sym_box(grid, 2, 3, 7, 8, 6, 9, 3)
    fill_sym_box(grid, 2, 3, 8, 9, 4, 9, 1)      # Black-lacquered shin guard
    fill_sym_box(grid, 2, 3, 6, 7, 9, 10, 2)     # Crisp deer hock spur
    fill_sym_box(grid, 2, 3, 7, 9, 10, 12, 3)
    # Sweeping muscular chestnut & black-armored haunch/thigh
    fill_sym_box(grid, 2, 4, 8, 13, 12, 17, 3)
    fill_sym_box(grid, 3, 4, 9, 13, 14, 18, 1)   # Black-lacquered thigh barding
    fill_sym_box(grid, 4, 4, 9, 13, 14, 14, 5)   # Gold lower barding rim

    # --- SLEEK ATHLETIC ARMORED STAG BODY (Y: 7..29, Z: 14..25) ---
    # Deep proud chest tapering gracefully through the flank to a muscular rump
    body_slices = [
        # (y, rx, z_bot, z_top)
        (7,  2.6, 18, 23),
        (8,  3.5, 17, 23),
        (9,  4.0, 16, 24),
        (10, 4.3, 16, 24),
        (11, 4.4, 16, 24),
        (12, 4.4, 16, 24),
        (13, 4.2, 16, 24),
        (14, 3.9, 17, 23),
        (15, 3.7, 17, 23),
        (16, 3.6, 17, 23),
        (17, 3.7, 17, 23),
        (18, 3.8, 16, 23),
        (19, 4.0, 16, 23),
        (20, 4.1, 16, 23),
        (21, 4.2, 15, 24),
        (22, 4.3, 15, 24),
        (23, 4.4, 15, 24),
        (24, 4.5, 14, 24),
        (25, 4.5, 14, 24),  # Proud deep stag chest
        (26, 4.4, 14, 24),
        (27, 4.1, 15, 23),
        (28, 3.6, 16, 23),
        (29, 2.8, 17, 22),
    ]
    for y, rx, zb, zt in body_slices:
        zc = (zb + zt) / 2.0
        rz = (zt - zb) / 2.0 + 0.35
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for z in range(zb, zt + 1):
                dz = z - zc
                if (dx / rx) ** 2 + (dz / rz) ** 2 <= 1.0:
                    # Pure ivory-white underside along belly & chest bottom
                    if z <= zb + 1 and dx <= rx * 0.65:
                        col = 8
                    # Sleek jet-black lacquered battle saddle & chest armor
                    elif (12 <= y <= 23 and z >= 20) or (y >= 25 and z >= 17):
                        col = 1
                    # Subtle gold trim border along bottom of black saddle barding
                    elif 12 <= y <= 23 and z == 19 and dx >= rx - 1.1:
                        col = 5
                    # Warm tawny highlight along upper chestnut coat
                    elif z >= zt - 2 and dx >= rx - 1.4:
                        col = 4
                    else:
                        col = 3
                    grid[x, y, z] = col

    # --- ARMORED BREASTPLATE & CHEST CREST (Y: 28..30, Z: 16..23) ---
    fill_sym_box(grid, 0, 2, 28, 29, 17, 22, 1)
    fill_sym_box(grid, 0, 2, 29, 29, 18, 18, 5)  # Gold breastplate trim
    fill_sym_box(grid, 0, 1, 29, 30, 19, 21, 5)  # Burnished gold chest crest
    fill_sym_box(grid, 0, 0, 30, 30, 20, 20, 9)  # Crimson center jewel
    # Gold saddle rim across shoulders & rump
    fill_sym_box(grid, 0, 3, 12, 12, 20, 24, 5)
    fill_sym_box(grid, 0, 3, 23, 23, 20, 24, 5)

    # --- TONBOKIRI SPEAR-BLADE MOTIF (槍の意匠) ON BACK & FLANKS! ---
    # 1. Sleek Gleaming Silver Dorsal Spear-Blade Crest Ridge along the stag's spine!
    fill_sym_box(grid, 0, 1, 12, 22, 24, 24, 1)
    fill_sym_box(grid, 0, 1, 21, 22, 24, 25, 5)  # Gold blade collar at withers
    fill_sym_box(grid, 0, 0, 22, 23, 25, 25, 9)  # Crimson tassel accent
    # Sweeping silver Tonbokiri spearhead ridge rising cleanly along Y: 8..21, Z: 25..29
    dorsal_blade = [
        # (y, z0, z1) - sleek tapered spear-blade profile sweeping backward to a sharp point
        (21, 25, 26),
        (20, 25, 27),
        (19, 25, 27),
        (18, 25, 28),
        (17, 25, 28),
        (16, 25, 29),
        (15, 25, 29),
        (14, 25, 29),
        (13, 25, 28),
        (12, 25, 28),
        (11, 25, 27),
        (10, 26, 27),
        (9,  26, 27),
        (8,  27, 27),
    ]
    for by, bz0, bz1 in dorsal_blade:
        fill_sym_box(grid, 0, 0, by, by, bz0, bz1, 6)
        if bz1 - bz0 >= 2:
            fill_sym_box(grid, 0, 0, by, by, bz0 + 1, bz0 + 1, 7)  # Steel fuller line
    # 2. Twin Flank Spear-Blade Armor Plates (sweeping sleekly back on both flanks)
    for by, z0, z1, x_off in [
        (21, 19, 21, 4),
        (20, 19, 22, 4),
        (19, 19, 22, 5),
        (18, 19, 22, 5),
        (17, 20, 22, 5),
        (16, 20, 22, 5),
        (15, 20, 22, 5),
        (14, 21, 22, 5),
        (13, 21, 22, 5),
        (12, 22, 22, 4),
    ]:
        fill_sym_box(grid, x_off, x_off, by, by, z0, z1, 6)
        if z1 > z0:
            fill_sym_box(grid, x_off, x_off, by, by, z0, z0, 7)
    # Gold & black rivet mount anchoring flank blades into saddle
    fill_sym_box(grid, 4, 5, 20, 21, 20, 21, 5)
    fill_sym_box(grid, 4, 4, 14, 19, 20, 21, 1)

    # --- WHITE RUMP PATCH & PROUD STAG TAIL WITH PURE WHITE UNDERSIDE (Y: 2..8, Z: 17..26) ---
    # Classic deer white rump shield visible cleanly from rear view
    fill_sym_box(grid, 0, 2, 6, 7, 18, 21, 8)
    fill_sym_box(grid, 0, 1, 6, 7, 17, 22, 8)
    # Raised perky stag tail: chestnut/black dorsal surface, unmistakable pure ivory-white underside!
    fill_sym_box(grid, 0, 1, 5, 7, 22, 23, 3)    # Chestnut tail root
    fill_sym_box(grid, 0, 0, 3, 6, 23, 24, 3)    # Upper tail ridge
    fill_sym_box(grid, 0, 0, 2, 4, 24, 26, 1)    # Dark tail tip curling up
    fill_sym_box(grid, 0, 1, 5, 6, 20, 21, 8)    # Unmistakable white tail underside!
    fill_sym_box(grid, 0, 0, 3, 5, 21, 23, 8)    # Crisp white underside sweeping up to tip

    # --- TALL PROUD ARCHED STAG NECK (Y: 25..34, Z: 21..33) ---
    neck_slices = [
        # (z, y_center, rx, ry)
        (22, 27.5, 3.6, 3.2),
        (23, 28.0, 3.4, 3.0),
        (24, 28.6, 3.1, 2.8),
        (25, 29.2, 2.9, 2.7),
        (26, 29.8, 2.7, 2.6),
        (27, 30.3, 2.6, 2.5),
        (28, 30.8, 2.5, 2.4),
        (29, 31.3, 2.4, 2.4),
        (30, 31.7, 2.4, 2.3),
        (31, 32.0, 2.3, 2.3),
        (32, 32.3, 2.3, 2.3),
    ]
    for nz, nyc, rx, ry in neck_slices:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for y in range(int(nyc - ry - 1), int(nyc + ry + 2)):
                if not (0 <= y < Y):
                    continue
                dy = y - nyc
                if (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0:
                    if dy > ry * 0.45 and dx <= rx * 0.6:
                        col = 8  # Crisp ivory-white stag throat patch
                    elif dy < -ry * 0.45 and dx <= 1.5:
                        col = 1  # Black-lacquered dorsal neck mane armor
                    else:
                        col = 3  # Rich chestnut coat
                    grid[x, y, nz] = col
    # Gold dorsal neck-armor rivets along back of neck
    for nz in (24, 27, 30):
        ny_back = int(round(27.5 + (nz - 22) * 0.48 - 2.3))
        fill_sym_box(grid, 0, 0, ny_back, ny_back, nz, nz, 5)

    # --- ICONIC PRAYER-BEAD COLLAR (大数珠) DRAPED AROUND THE STAG'S NECK! ---
    collar_beads = [
        # (x_off, y_pos, z_pos)
        (0, 31, 22),  # Lowest front-center bead resting over chest
        (2, 31, 23),
        (3, 30, 24),
        (3, 28, 25),
        (3, 26, 26),
        (1, 25, 27),  # Back nape beads
    ]
    fill_sym_line(grid, (0, 30, 22), (3, 29, 24), 1, thickness=1)
    fill_sym_line(grid, (3, 29, 24), (3, 26, 26), 1, thickness=1)
    fill_sym_line(grid, (3, 26, 26), (0, 25, 27), 1, thickness=1)
    for bx_off, by, bz in collar_beads:
        if bx_off == 0:
            fill_sym_box(grid, 0, 1, by, by + 1, bz, bz + 1, 4)
            fill_sym_box(grid, 0, 0, by + 1, by + 1, bz, bz, 3)
        else:
            fill_sym_box(grid, bx_off, bx_off + 1, by, by + 1, bz, bz + 1, 4)
            fill_sym_box(grid, bx_off + 1, bx_off + 1, by + 1, by + 1, bz, bz, 3)

    # --- NOBLE ARMORED STAG HEAD, CHAMFRON & ALERT EARS (Y: 28..42, Z: 30..37) ---
    # Sculpted cranium & cheeks
    fill_sym_box(grid, 0, 2, 30, 35, 31, 35, 3)
    fill_sym_box(grid, 0, 1, 31, 35, 36, 36, 3)
    # Sleek tapered muzzle reaching proudly forward to Y=41..42
    fill_sym_box(grid, 0, 1, 36, 38, 31, 34, 3)
    fill_sym_box(grid, 0, 1, 39, 40, 31, 33, 3)
    fill_sym_box(grid, 0, 0, 41, 41, 31, 32, 3)
    # White chin / jaw underside & glossy black stag nose tip
    fill_sym_box(grid, 0, 1, 35, 39, 30, 30, 8)
    fill_sym_box(grid, 0, 0, 40, 41, 30, 30, 8)
    fill_sym_box(grid, 0, 0, 41, 42, 31, 32, 1)  # Glossy black nose
    # Black-lacquered & gold-trimmed forehead chamfron (echoes Robot A's kabuto!)
    fill_sym_box(grid, 0, 2, 31, 36, 35, 36, 1)
    fill_sym_box(grid, 0, 1, 36, 39, 34, 34, 1)
    fill_sym_box(grid, 0, 2, 35, 36, 35, 35, 5)  # Gold brow-band linking to antler bases
    fill_sym_box(grid, 0, 0, 32, 39, 35, 36, 5)  # Burnished gold chamfron nose-ridge
    fill_sym_box(grid, 0, 0, 37, 38, 35, 35, 9)  # Crimson battle gem on forehead
    # Fierce crimson eyes framed by dark brow
    fill_sym_box(grid, 2, 2, 34, 35, 33, 33, 9)
    fill_sym_box(grid, 2, 2, 34, 35, 34, 34, 1)
    # Alert pointed stag ears sweeping crisply outward & back (chestnut outer, warm ivory/amber inner)
    fill_sym_box(grid, 2, 3, 29, 30, 34, 35, 3)
    fill_sym_box(grid, 4, 5, 28, 29, 35, 36, 3)
    fill_sym_box(grid, 6, 6, 27, 28, 36, 37, 3)
    fill_sym_box(grid, 3, 5, 29, 29, 35, 36, 8)  # Crisp ivory-white inner ear tint

    # --- MAGNIFICENT TOWERING BRANCHING ANTLERS (立派な角!) ---
    # Reused directly from Robot A's Honda Tadakatsu kabuto!
    add_tadakatsu_antlers(grid, x_root=1, y_root=32, z_root=35)

    # Hollow interior bulk to keep voxel count cleanly within budget (~1,800-3,000)
    hollow_interior_26(grid, 1, 47)
    return grid


# ==========================================
# CONNECTIVITY DIAGNOSTIC HELPER
# ==========================================
def count_connected_components_6(grid):
    """Return number of 6-connected components of non-zero voxels."""
    X, Y, Z = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    xs, ys, zs = np.nonzero(grid)
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
                if 0 <= nx < X and 0 <= ny < Y and 0 <= nz < Z and not visited[nx, ny, nz] and grid[nx, ny, nz] > 0:
                    visited[nx, ny, nz] = True
                    q.append((nx, ny, nz))
    return comps


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
    comp_a = count_connected_components_6(model_a)
    comp_b = count_connected_components_6(model_b)
    v_a = export_vox(model_a, "tadakatsu_a.vox")
    v_b = export_vox(model_b, "tadakatsu_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: HONDA TADAKATSU ROBOT -> ARMORED BATTLE STAG",
        "1. HONDA TADAKATSU ROBOT (TONBOKIRI)",
        "2. ARMORED BATTLE STAG (SHIKA)",
        "preview_tadakatsu.png",
        yaw_a=32, pitch_a=20, yaw_b=48, pitch_b=20,
    )
    print(f"tadakatsu: A={v_a} voxels {model_a.shape} (6-comp={comp_a}), B={v_b} voxels {model_b.shape} (6-comp={comp_b})")
