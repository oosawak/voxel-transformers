import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (244, 246, 252, 255),  # Orbital Pure White (Main Fuselage / Armor)
    2: (182, 192, 208, 255),  # Aerospace Light Grey (Panel Trim / Shading)
    3: (34, 38, 48, 255),     # Roll-Pattern Jet Black (Bands / Joints / Nozzles)
    4: (228, 52, 46, 255),    # Mission Crimson Red (Nose Cone / Fins / Stripes)
    5: (248, 126, 36, 255),   # Launch Orange (Booster Accents / Fairing Trim)
    6: (26, 52, 92, 255),     # Deep Space Navy (Porthole Rim / Dark Glass)
    7: (92, 224, 255, 255),   # Glowing Cyan (Observation Porthole / Visor / Core)
    8: (255, 212, 72, 255),   # Bright Amber/Yellow (Thruster Flame / Gold Vents)
    9: (116, 126, 144, 255),  # Metallic Titanium Steel (Engine Bells / Frame / Lance)
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


def fill_cyl_ring(grid, cx, cy, z0, z1, r_out, r_in, col):
    """Fill a vertical cylinder or hollow cylindrical ring centered at (cx, cy)."""
    X, Y, Z = grid.shape
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    x0 = max(0, int(np.floor(cx - r_out)))
    x1 = min(X - 1, int(np.ceil(cx + r_out)))
    y0 = max(0, int(np.floor(cy - r_out)))
    y1 = min(Y - 1, int(np.ceil(cy + r_out)))
    r_out2 = r_out * r_out
    r_in2 = r_in * r_in if r_in > 0 else -1.0
    for x in range(x0, x1 + 1):
        dx = x - cx
        for y in range(y0, y1 + 1):
            dy = y - cy
            d2 = dx * dx + dy * dy
            if r_in2 < d2 <= r_out2:
                grid[x, y, z0:z1 + 1] = col


def hollow_interior(grid, z_min=1, z_max=None):
    """Remove strictly interior voxels (26-neighbor surrounded) so shell stays watertight and 6-connected."""
    X, Y, Z = grid.shape
    if z_max is None:
        z_max = Z - 2
    occ = grid > 0
    interior = np.ones((X - 2, Y - 2, z_max - z_min + 1), dtype=bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                interior &= occ[
                    1 + dx:X - 1 + dx,
                    1 + dy:Y - 1 + dy,
                    z_min + dz:z_max + 1 + dz,
                ]
    grid[1:X - 1, 1:Y - 1, z_min:z_max + 1][interior] = 0


# ==========================================
# FORM A: SPACE ROCKET (24 x 18 x 48)
# ==========================================
def build_a():
    grid = np.zeros((24, 18, 48), dtype=np.uint8)
    cx = 11.5
    cy = 8.5

    # --- 1. CORE ENGINE CLUSTER & THRUSTER GLOW (Z: 0..5) ---
    # Central main engine bell (dark metallic steel + charcoal rim)
    fill_cyl_ring(grid, cx, cy, 1, 2, 3.7, 2.2, 3)
    fill_cyl_ring(grid, cx, cy, 3, 4, 3.2, 1.8, 9)
    fill_cyl_ring(grid, cx, cy, 5, 5, 4.35, 0.0, 3)  # Base heat shield bulkhead
    # Bright amber/yellow & orange thruster glow beneath main bell (grounded at Z=0)
    fill_cyl_ring(grid, cx, cy, 0, 1, 2.5, 0.0, 8)
    fill_cyl_ring(grid, cx, cy, 2, 3, 2.0, 0.0, 5)
    # Flanking vernier nozzles (+Y and -Y)
    for vy in (cy - 2.6, cy + 2.6):
        fill_cyl_ring(grid, cx, vy, 2, 4, 1.4, 0.0, 9)
        fill_cyl_ring(grid, cx, vy, 1, 1, 1.2, 0.0, 8)

    # --- 2. FIRST STAGE MAIN CORE FUSELAGE (Z: 6..21) ---
    # Clean white cylindrical main stage
    fill_cyl_ring(grid, cx, cy, 6, 21, 4.4, 0.0, 1)
    # Iconic Saturn-V black & white roll-pattern checker band (Z: 6..9)
    for x in range(24):
        for y in range(18):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= 4.4 * 4.4:
                if (dx > 0 and dy > 0) or (dx < 0 and dy < 0):
                    grid[x, y, 6:10] = 3
    # Crisp crimson & orange mission accent band (Z: 10..11)
    fill_cyl_ring(grid, cx, cy, 10, 10, 4.45, 3.2, 4)
    fill_cyl_ring(grid, cx, cy, 11, 11, 4.45, 3.2, 5)
    # Upper first-stage black roll ring (Z: 20..21)
    fill_cyl_ring(grid, cx, cy, 20, 21, 4.45, 3.2, 3)
    # Front/rear grey instrumentation conduits along clean white hull (Z: 12..19)
    fill_sym_box(grid, 0, 0, 13, 13, 12, 19, 2)
    fill_sym_box(grid, 0, 0, 4, 4, 12, 19, 2)

    # Front & rear aerodynamic core stabilizer fins (+Y and -Y, Z: 2..10)
    for dz in range(9):
        reach = 3 - (dz // 3)
        fill_sym_box(grid, 0, 0, 13, 13 + reach, 2 + dz, 2 + dz, 4 if dz < 7 else 2)
        fill_sym_box(grid, 0, 0, 4 - reach, 4, 2 + dz, 2 + dz, 4 if dz < 7 else 2)
    fill_sym_box(grid, 0, 0, 12, 14, 4, 6, 3)
    fill_sym_box(grid, 0, 0, 3, 5, 4, 6, 3)

    # --- 3. INTERSTAGE COLLAR & UPPER CREW STAGE (Z: 22..33) ---
    # Ribbed black interstage ring (Z: 22..24)
    fill_cyl_ring(grid, cx, cy, 22, 24, 4.1, 0.0, 3)
    for ax in (-3.6, 3.6):
        fill_cyl_ring(grid, cx + ax, cy, 22, 24, 0.8, 0.0, 9)
    fill_sym_box(grid, 0, 0, 12, 12, 22, 24, 9)
    fill_sym_box(grid, 0, 0, 5, 5, 22, 24, 9)

    # Upper cylindrical crew / payload stage (Z: 25..33) - becomes Robot Chest!
    fill_cyl_ring(grid, cx, cy, 25, 33, 4.1, 0.0, 1)
    fill_cyl_ring(grid, cx, cy, 25, 25, 4.15, 2.8, 5)
    fill_cyl_ring(grid, cx, cy, 26, 26, 4.15, 2.8, 4)
    fill_cyl_ring(grid, cx, cy, 32, 33, 4.15, 2.8, 3)
    fill_sym_box(grid, 4, 4, 8, 9, 27, 31, 2)  # Fairing panel seam

    # Iconic Front Observation Porthole on +Y face (Z: 27..30)
    fill_sym_box(grid, 0, 1, 12, 13, 27, 30, 6)  # Deep navy circular frame
    fill_sym_box(grid, 2, 2, 12, 12, 28, 29, 6)
    fill_sym_box(grid, 0, 1, 13, 13, 28, 29, 7)  # Glowing cyan glass
    # Rear umbilical panel on -Y face
    fill_sym_box(grid, 0, 1, 4, 4, 27, 30, 9)
    fill_sym_box(grid, 0, 0, 4, 4, 28, 29, 3)

    # --- 4. POINTED NOSE CONE FAIRING & ESCAPE SPIRE (Z: 34..47) ---
    # Sleek, continuously tapering nose cone - transforms into Robot's pointed rocket-helmet!
    cone_profile = [
        (34, 3.9, 1),
        (35, 3.7, 1),
        (36, 3.4, 4),  # Crimson red nose cone collar
        (37, 3.1, 4),
        (38, 2.8, 5),  # Launch orange accent ring
        (39, 2.5, 1),  # Sleek white nose fairing
        (40, 2.2, 1),
        (41, 1.9, 1),
        (42, 1.6, 1),
        (43, 1.3, 4),  # Crimson upper nose tip
        (44, 1.0, 4),
        (45, 0.8, 9),  # Sleek metallic escape spire base
    ]
    for z, rad, col in cone_profile:
        fill_cyl_ring(grid, cx, cy, z, z, rad, 0.0, col)
    # Subtle cyan visor sensor slit on front of nose fairing (Z: 35)
    fill_sym_box(grid, 0, 1, 12, 12, 35, 35, 7)
    fill_sym_box(grid, 2, 2, 11, 11, 35, 35, 6)
    # Sharp launch escape spire tip (Z: 46..47)
    fill_sym_box(grid, 0, 0, 8, 9, 46, 46, 9)
    fill_sym_box(grid, 0, 0, 8, 9, 47, 47, 4)

    # --- 5. TWIN SOLID ROCKET BOOSTERS (SRBs) (+X and -X) ---
    # These become the Robot's thruster-footed legs!
    for side in (-1, 1):
        bx = cx + side * 7.0  # Centers at x = 4.5 and x = 18.5
        # Booster engine bell (Z: 0..3) grounded at Z=0
        fill_cyl_ring(grid, bx, cy, 1, 2, 2.25, 1.2, 3)
        fill_cyl_ring(grid, bx, cy, 3, 3, 2.0, 0.0, 9)
        fill_cyl_ring(grid, bx, cy, 0, 1, 1.35, 0.0, 8)  # Bright amber thruster glow
        fill_cyl_ring(grid, bx, cy, 2, 2, 1.1, 0.0, 5)   # Orange inner glow

        # Booster main cylinder (Z: 4..20) - clean white with crisp mission bands
        fill_cyl_ring(grid, bx, cy, 4, 20, 2.35, 0.0, 1)
        fill_cyl_ring(grid, bx, cy, 6, 6, 2.4, 1.2, 4)    # Lower crimson stripe
        fill_cyl_ring(grid, bx, cy, 7, 7, 2.4, 1.2, 5)    # Orange stripe
        fill_cyl_ring(grid, bx, cy, 13, 14, 2.4, 1.2, 3)  # Black roll-pattern band
        fill_cyl_ring(grid, bx, cy, 19, 20, 2.4, 1.2, 4)  # Upper crimson collar

        # Booster conical nose cap (Z: 21..26) - becomes Robot knee armor!
        for z, rad, col in [
            (21, 2.1, 5),
            (22, 1.8, 4),
            (23, 1.5, 4),
            (24, 1.2, 1),
            (25, 0.9, 1),
            (26, 0.7, 4),
        ]:
            fill_cyl_ring(grid, bx, cy, z, z, rad, 0.0, col)

    # Heavy steel/black booster struts connecting SRBs solidly to main core
    fill_sym_box(grid, 4, 5, 8, 9, 8, 9, 9)
    fill_sym_box(grid, 4, 5, 8, 9, 10, 10, 3)
    fill_sym_box(grid, 4, 5, 8, 9, 18, 19, 9)
    fill_sym_box(grid, 4, 5, 8, 9, 17, 17, 3)

    # Outer swept crimson booster fins (x_off: 9..11, Z: 2..11) - preserved on robot calves!
    for dz in range(10):
        outer = 11 - (dz // 4)
        fill_sym_box(grid, 9, outer, 8, 9, 2 + dz, 2 + dz, 4)
        if dz >= 2:
            fill_sym_box(grid, outer, outer, 8, 9, 2 + dz, 2 + dz, 2 if dz % 3 == 0 else 4)
    fill_sym_box(grid, 8, 9, 8, 9, 2, 4, 3)

    # Hollow strictly 26-connected interior voxels to keep shell watertight & ~1,900-2,300 voxels
    hollow_interior(grid, z_min=2, z_max=43)
    return grid


# ==========================================
# FORM B: ROCKET VANGUARD ROBOT (34 x 24 x 48)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 48), dtype=np.uint8)
    cx = 16.5
    cy = 11.5

    # --- 1. THRUSTER-FOOTED BOOTS (Z: 0..4) - Booster Engine Bells & Armored Toes ---
    # Grounded thruster nozzle soles with visible amber/orange glow!
    fill_sym_box(grid, 3, 7, 8, 14, 1, 2, 3)       # Dark engine nozzle rim
    fill_sym_box(grid, 3, 7, 9, 13, 0, 0, 9)       # Metallic landing ring
    fill_sym_box(grid, 4, 6, 9, 13, 0, 1, 8)       # Glowing amber thruster sole
    fill_sym_box(grid, 7, 7, 10, 12, 0, 1, 8)      # Side nozzle glow visible in 3/4 view!
    fill_sym_box(grid, 3, 3, 10, 12, 0, 1, 8)      # Inner nozzle glow
    fill_sym_box(grid, 4, 6, 8, 8, 0, 1, 5)        # Orange rear thruster core
    fill_sym_box(grid, 4, 6, 6, 8, 0, 2, 9)        # Heel stabilizer strut
    # Forward armored toe unit (Y: 14..17, Z: 0..3)
    fill_sym_box(grid, 3, 7, 14, 16, 0, 2, 1)      # White space-boot forefoot
    fill_sym_box(grid, 4, 6, 16, 17, 0, 1, 4)      # Crimson toe cap
    fill_sym_box(grid, 4, 6, 14, 16, 2, 3, 4)      # Crimson armored instep
    fill_sym_box(grid, 5, 5, 15, 16, 3, 3, 5)      # Orange trim stripe
    # Ankle collar (Z: 3..4)
    fill_sym_box(grid, 4, 6, 9, 13, 3, 4, 9)
    fill_sym_box(grid, 4, 6, 10, 12, 3, 4, 3)

    # --- 2. LOWER LEGS / CALVES (Z: 4..16) - Twin Side Solid Rocket Boosters! ---
    for side in (-1, 1):
        lx = cx + side * 5.0  # Centers at x = 11.5 and x = 21.5
        # Cylindrical white rocket booster body
        fill_cyl_ring(grid, lx, cy, 4, 15, 2.7, 0.0, 1)
        # Signature booster bands matching Form A directly!
        fill_cyl_ring(grid, lx, cy, 5, 5, 2.75, 1.5, 4)    # Lower crimson stripe
        fill_cyl_ring(grid, lx, cy, 6, 6, 2.75, 1.5, 5)    # Orange accent stripe
        fill_cyl_ring(grid, lx, cy, 10, 11, 2.75, 1.5, 3)  # Black roll-pattern band
        fill_cyl_ring(grid, lx, cy, 14, 14, 2.75, 1.5, 4)  # Upper crimson band
        # Rear calf vernier booster thruster (Y: 7..8, Z: 6..10)
        fill_cyl_ring(grid, lx, cy - 3.0, 7, 10, 1.1, 0.0, 9)
        fill_cyl_ring(grid, lx, cy - 3.0, 6, 6, 0.9, 0.0, 8)

    # Outer red booster fins mounted on outer calves (x_off: 8..10, Z: 4..13)!
    for dz in range(10):
        outer = 10 - (dz // 4)
        fill_sym_box(grid, 8, outer, 10, 12, 4 + dz, 4 + dz, 4)
        if dz >= 1:
            fill_sym_box(grid, outer, outer, 11, 12, 4 + dz, 4 + dz, 2 if dz % 3 == 0 else 4)
    fill_sym_box(grid, 7, 8, 10, 12, 5, 11, 3)  # Fin mounting bracket

    # Conical booster-cap knee armor (Z: 14..17, Y: 13..16)
    fill_sym_box(grid, 4, 6, 13, 15, 14, 16, 4)
    fill_sym_box(grid, 4, 6, 15, 15, 15, 16, 5)
    fill_sym_box(grid, 5, 5, 15, 16, 15, 17, 1)
    fill_sym_box(grid, 5, 5, 16, 16, 16, 16, 4)

    # --- 3. THIGHS (Z: 16..21) ---
    fill_sym_box(grid, 4, 6, 9, 13, 16, 21, 9)     # Metallic steel inner leg frame
    fill_sym_box(grid, 3, 6, 10, 13, 17, 20, 1)    # White armored thigh plating
    fill_sym_box(grid, 4, 5, 13, 14, 17, 20, 2)    # Front bevel panel
    fill_sym_box(grid, 6, 6, 11, 12, 17, 20, 5)    # Orange side fuel-line stripe
    fill_sym_box(grid, 4, 5, 9, 10, 16, 17, 3)     # Knee rear joint

    # --- 4. WAIST / PELVIS (Z: 20..24) - Core Interstage Pelvis ---
    fill_sym_box(grid, 0, 5, 9, 14, 21, 23, 3)     # Dark interstage hip block
    fill_sym_box(grid, 2, 5, 10, 13, 20, 22, 9)    # Heavy steel hip axles
    # Front waist armor & central buckle
    fill_sym_box(grid, 0, 4, 13, 15, 22, 23, 1)    # White front waist skirt
    fill_sym_box(grid, 0, 1, 13, 15, 20, 23, 4)    # Crimson central codpiece
    fill_sym_box(grid, 0, 1, 15, 15, 21, 22, 5)    # Orange center ridge
    fill_sym_box(grid, 0, 0, 15, 15, 22, 22, 8)    # Golden/amber buckle vent
    # Side hip skirts
    fill_sym_box(grid, 6, 7, 10, 13, 20, 23, 1)
    fill_sym_box(grid, 7, 7, 11, 12, 21, 22, 4)
    # Rear waist core thruster
    fill_sym_box(grid, 0, 2, 7, 9, 21, 23, 9)
    fill_sym_box(grid, 0, 1, 7, 7, 21, 22, 8)

    # --- 5. TORSO / CHEST (Z: 24..36) - Cylindrical Rocket Stage Directly! ---
    # Abdomen / Lower Stage with Saturn-V Black & White Roll Pattern (Z: 24..27)
    fill_cyl_ring(grid, cx, cy, 24, 27, 4.4, 0.0, 1)
    for x in range(34):
        for y in range(24):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= 4.45 * 4.45:
                if (dx > 0 and dy > 0) or (dx < 0 and dy < 0):
                    grid[x, y, 24:27] = 3
    # Crimson & orange mission belt separating lower/upper rocket stages (Z: 27..28)
    fill_cyl_ring(grid, cx, cy, 27, 27, 4.6, 3.0, 4)
    fill_cyl_ring(grid, cx, cy, 28, 28, 4.8, 3.0, 5)

    # Upper Chest - Cylindrical White Upper Rocket Stage (Z: 28..35)
    fill_cyl_ring(grid, cx, cy, 28, 35, 5.1, 0.0, 1)
    # Sculpted white rocket-stage chest armor preserving cylindrical feel
    fill_sym_box(grid, 0, 5, 12, 15, 29, 34, 1)
    fill_sym_box(grid, 3, 4, 15, 16, 30, 34, 1)
    fill_sym_box(grid, 3, 4, 16, 16, 31, 32, 5)    # Orange chest intake vents
    fill_sym_box(grid, 4, 5, 14, 15, 34, 34, 4)    # Red collarbone stripes
    fill_sym_box(grid, 5, 5, 11, 14, 29, 33, 2)    # Grey fairing seam panels
    # Black upper interstage collar (Z: 35..36)
    fill_cyl_ring(grid, cx, cy, 35, 36, 4.2, 0.0, 3)
    fill_sym_box(grid, 2, 4, 12, 14, 35, 36, 2)    # Collar armor guards

    # Central Observation Porthole / Rocket Core on Chest (Z: 29..33, Y: 15..17)
    fill_sym_box(grid, 0, 2, 15, 16, 29, 33, 6)    # Deep space navy porthole housing
    fill_sym_box(grid, 0, 1, 16, 17, 30, 32, 7)    # Bright glowing cyan observation core!
    fill_sym_box(grid, 2, 2, 16, 16, 31, 31, 9)    # Metallic porthole bolts
    fill_sym_box(grid, 0, 1, 16, 16, 29, 29, 9)
    fill_sym_box(grid, 0, 1, 16, 16, 33, 33, 9)

    # --- 6. THRUSTER BACKPACK & SWEEPING FAIRING WINGS (Y: 3..8, Z: 22..41) ---
    # Core thruster pack bolted cleanly to back of cylindrical torso
    fill_sym_box(grid, 0, 4, 6, 9, 26, 35, 2)
    fill_sym_box(grid, 0, 3, 5, 7, 27, 34, 1)
    fill_sym_box(grid, 0, 1, 5, 6, 28, 33, 3)      # Center black roll stripe on pack
    fill_sym_box(grid, 2, 3, 5, 6, 32, 34, 4)      # Red top pack accents
    # Twin bold main rocket engine bells protruding downward from backpack (Z: 22..26)
    for side in (-1, 1):
        nx = cx + side * 2.5
        fill_cyl_ring(grid, nx, 5.5, 24, 26, 1.65, 0.0, 9)
        fill_cyl_ring(grid, nx, 5.5, 23, 24, 1.75, 0.9, 3)
        fill_cyl_ring(grid, nx, 5.5, 22, 23, 1.15, 0.0, 8)  # Glowing amber exhaust
        fill_cyl_ring(grid, nx, 5.5, 24, 25, 0.95, 0.0, 5)  # Orange core glow

    # Sweeping split fairing wing panels extending up & outward from backpack (Z: 30..41)
    fill_sym_box(grid, 4, 5, 6, 8, 30, 34, 9)      # Heavy wing root hinge
    for i in range(8):
        x0 = 5 + i
        x1 = 6 + i
        z0 = 31 + i
        z1 = 34 + i
        y_back = 6 - (i // 3)
        fill_sym_box(grid, x0, x1, y_back, y_back + 1, z0, z1, 1)
        fill_sym_box(grid, x0, x1, y_back, y_back + 1, z1, z1, 4)
        if i >= 2:
            fill_sym_box(grid, x0, x1, y_back, y_back + 1, z1 - 1, z1 - 1, 5)
        if i in (2, 5):
            fill_sym_box(grid, x0, x1, y_back, y_back + 1, z0, z0, 3)

    # --- 7. SWEEPING FAIRING SHOULDER PAULDRONS & ARMS (Z: 16..38) ---
    # Shoulder connector axles solidly joining torso to pauldrons
    fill_sym_box(grid, 5, 7, 10, 13, 31, 34, 3)
    fill_sym_box(grid, 5, 6, 11, 12, 32, 33, 9)

    # Sweeping upper-fairing shoulder pauldrons (x_off: 6..12, Z: 31..38)
    fill_sym_box(grid, 6, 10, 9, 14, 31, 35, 1)    # Main white curved fairing armor
    fill_sym_box(grid, 7, 11, 9, 14, 34, 36, 1)    # Flared upper pauldron flare
    fill_sym_box(grid, 8, 12, 10, 13, 36, 37, 4)   # Crimson sweeping shoulder tip
    fill_sym_box(grid, 10, 12, 10, 13, 37, 38, 5)  # Launch orange outer winglet tip
    fill_sym_box(grid, 10, 11, 10, 13, 31, 34, 3)  # Black roll-pattern band on outer shoulder
    fill_sym_box(grid, 7, 9, 14, 15, 32, 34, 2)    # Grey front shoulder louver
    fill_sym_box(grid, 8, 9, 15, 15, 33, 33, 8)    # Amber vernier thruster dot

    # Upper Arms (x_off: 7..9, Z: 25..30)
    fill_sym_box(grid, 7, 9, 10, 13, 25, 30, 3)
    fill_sym_box(grid, 7, 9, 11, 12, 26, 29, 9)
    fill_sym_box(grid, 8, 9, 10, 13, 27, 29, 2)

    # Forearms / Gauntlets (x_off: 8..11, Z: 18..24) - clean heroic spacing from hips
    fill_sym_box(grid, 8, 10, 10, 14, 18, 24, 1)   # White astronaut gauntlet
    fill_sym_box(grid, 10, 11, 10, 13, 19, 23, 4)  # Crimson outer forearm fin
    fill_sym_box(grid, 8, 10, 10, 14, 21, 21, 3)   # Black roll stripe
    fill_sym_box(grid, 8, 9, 14, 14, 20, 22, 2)    # Grey front cuff
    fill_sym_box(grid, 8, 9, 14, 14, 19, 19, 7)    # Glowing cyan wrist comm

    # Fists (Z: 16..17)
    fill_sym_box(grid, 8, 10, 11, 13, 16, 17, 3)
    fill_sym_box(grid, 8, 10, 13, 14, 16, 17, 9)

    # RIGHT HAND (+X side, x >= 17): Orbital Thruster Lance / Plasma Rifle!
    # Gripped cleanly in right fist (x: 25..27, y: 11..14, z: 16..17)
    fill_box(grid, 26, 27, 9, 20, 16, 18, 9)       # Metallic steel barrel & receiver
    fill_box(grid, 26, 27, 11, 17, 17, 19, 1)      # White upper weapon shroud
    fill_box(grid, 26, 27, 14, 16, 18, 19, 4)      # Crimson mission stripe
    fill_box(grid, 26, 27, 18, 19, 17, 18, 3)      # Black muzzle collar
    fill_box(grid, 26, 27, 20, 23, 17, 17, 7)      # Extended glowing cyan plasma lance tip!
    fill_box(grid, 26, 27, 8, 9, 16, 17, 8)        # Amber rear counter-thruster

    # LEFT FOREARM (-X side, x < 17): Fairing Thermal Heat-Shield!
    # Mounted solidly to left outer forearm (x: 5..6)
    fill_box(grid, 4, 6, 11, 13, 19, 23, 9)        # Shield mounting bracket
    fill_box(grid, 3, 4, 9, 15, 17, 26, 1)         # Curved white fairing shield body
    fill_box(grid, 3, 3, 10, 14, 18, 25, 3)        # Black thermal heat-tile center
    fill_box(grid, 3, 3, 11, 13, 20, 24, 4)        # Crimson vanguard emblem
    fill_box(grid, 3, 3, 12, 12, 21, 23, 5)        # Orange nose stripe
    fill_box(grid, 3, 4, 15, 15, 20, 24, 4)        # Front-edge crimson stripe visible in front 3/4!
    fill_box(grid, 3, 4, 15, 15, 21, 22, 5)        # Front-edge orange accent
    fill_box(grid, 3, 4, 10, 14, 26, 27, 4)        # Pointed upper shield crest
    fill_box(grid, 3, 4, 11, 13, 16, 16, 2)        # Lower beveled tip

    # --- 8. POINTED ROCKET-HELMET HEAD (Z: 36..47) - Transformed Nose Cone! ---
    # Neck column (Z: 36..37)
    fill_sym_box(grid, 0, 1, 10, 13, 36, 37, 3)
    fill_sym_box(grid, 0, 1, 11, 12, 36, 37, 9)

    # Helmet main housing (Z: 37..40)
    fill_sym_box(grid, 0, 2, 9, 14, 37, 40, 1)     # White helmet shell
    fill_sym_box(grid, 3, 3, 10, 13, 38, 40, 2)    # Side cheek armor
    fill_sym_box(grid, 3, 3, 11, 12, 39, 40, 9)    # Ear comm pods
    fill_sym_box(grid, 4, 4, 11, 11, 40, 42, 4)    # Red twin ear antennas!
    # Faceplate & Fierce Glowing Cyan Visor (Y: 14..15)
    fill_sym_box(grid, 0, 1, 14, 14, 37, 38, 2)    # Chin / faceplate
    fill_sym_box(grid, 0, 0, 14, 15, 37, 37, 4)    # Red heroic chin guard
    fill_sym_box(grid, 0, 2, 14, 15, 39, 40, 6)    # Deep navy visor recess
    fill_sym_box(grid, 0, 2, 15, 15, 39, 39, 7)    # Bright glowing cyan visor!
    fill_sym_box(grid, 0, 1, 15, 15, 40, 40, 7)

    # Unmistakable Tall Pointed Rocket Nose-Cone Helmet Crown (Z: 41..47)!
    fill_cyl_ring(grid, cx, cy, 41, 41, 2.8, 0.0, 4)  # Crimson nose-cone collar
    fill_cyl_ring(grid, cx, cy, 42, 42, 2.4, 0.0, 5)  # Launch orange accent ring
    fill_cyl_ring(grid, cx, cy, 43, 43, 2.0, 0.0, 1)  # Tapering white nose cone
    fill_cyl_ring(grid, cx, cy, 44, 44, 1.5, 0.0, 1)  # Upper white nose cone
    fill_cyl_ring(grid, cx, cy, 45, 45, 1.1, 0.0, 4)  # Crimson nose tip
    fill_sym_box(grid, 0, 0, 11, 12, 46, 46, 9)       # Metallic escape-spire crest!
    fill_sym_box(grid, 0, 0, 11, 12, 47, 47, 4)       # Red spire tip!
    # Compact swept V-fin brow crest framing the nose cone (Z: 40..42)
    fill_sym_box(grid, 0, 0, 15, 15, 40, 41, 4)
    fill_sym_box(grid, 1, 2, 14, 15, 41, 41, 1)
    fill_sym_box(grid, 2, 3, 13, 14, 42, 42, 4)

    # Hollow strictly 26-connected interior voxels (watertight, 6-connected, ~2,800-3,500 voxels)
    hollow_interior(grid, z_min=2, z_max=45)
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


def render_voxel_iso(grid, yaw_deg=35, pitch_deg=25, scale=None, img_size=(386, 266), margin=14):
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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=36, pitch_a=22, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "rocket_a.vox")
    v_b = export_vox(model_b, "rocket_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SPACE ROCKET -> ROCKET VANGUARD ROBOT",
        "1. SPACE ROCKET",
        "2. ROCKET VANGUARD ROBOT",
        "preview_rocket.png",
        yaw_a=36, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"rocket: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
