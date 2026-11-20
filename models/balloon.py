import math
import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (246, 244, 236, 255),  # Crisp Balloon White (Band / Highlights)
    2: (224, 48, 56, 255),    # Crimson Balloon Red (Gores / Crest)
    3: (248, 200, 44, 255),   # Sunny Golden Yellow (Gores / Flame Core)
    4: (42, 118, 220, 255),   # Royal Sky Blue (Gores / Leg Armor)
    5: (166, 112, 58, 255),   # Warm Wicker Brown (Gondola Basket / Waist)
    6: (106, 66, 34, 255),    # Dark Wicker & Leather Brown (Weave / Boots)
    7: (210, 176, 108, 255),  # Antique Brass & Sandbag Tan (Trim / Sandbags)
    8: (46, 52, 66, 255),     # Dark Iron Charcoal (Throat / Cables / Joints)
    9: (255, 118, 28, 255),   # Glowing Burner Orange (Flame / Chest Core / Visor)
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


def fill_wicker_box(grid, x0, x1, y0, y1, z0, z1, hollow=False):
    """Fill a woven wicker basket box with alternating warm/dark wicker checkerboard."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(x0, x1)), min(X - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if hollow and (x0 < x < x1) and (y0 < y < y1) and (z > z0):
                    continue
                col = 5 if ((x + y + z) % 2 == 0) else 6
                grid[x, y, z] = col


def extract_connected_shell(solid):
    """Return boolean mask of outer surface voxels using 18-neighborhood for a lean 6-connected shell."""
    X, Y, Z = solid.shape
    padded = np.pad(solid, 1, mode='constant', constant_values=False)
    interior = np.ones_like(solid, dtype=bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx == 0 and dy == 0 and dz == 0) or (abs(dx) + abs(dy) + abs(dz) == 3):
                    continue
                interior &= padded[1 + dx:1 + dx + X, 1 + dy:1 + dy + Y, 1 + dz:1 + dz + Z]
    return solid & (~interior)


# ==========================================
# FORM A: HOT AIR BALLOON (24 x 24 x 44)
# ==========================================
def build_a():
    grid = np.zeros((24, 24, 44), dtype=np.uint8)
    cx, cy = 11.5, 11.5

    # --- WOVEN WICKER GONDOLA BASKET (Z: 0..6) ---
    # Solid dark wooden runner base (Z=0)
    fill_box(grid, 9, 14, 9, 14, 0, 0, 6)
    fill_sym_box(grid, 2, 2, 9, 14, 0, 0, 8)  # Iron floor skids
    # Woven hollow wicker walls (Z=1..5)
    fill_wicker_box(grid, 8, 15, 8, 15, 1, 5, hollow=True)
    # Dark leather padded gondola rim (Z=6)
    for x in range(8, 16):
        for y in range(8, 16):
            if x in (8, 15) or y in (8, 15):
                grid[x, y, 6] = 6
    # Brass corner reinforcement brackets on basket rim
    for bx in (8, 15):
        for by in (8, 15):
            grid[bx, by, 6] = 7
            grid[bx, by, 5] = 7
    # Brass front aeronaut crest plate (+Y front face)
    fill_sym_box(grid, 0, 1, 15, 15, 3, 4, 7)
    fill_sym_box(grid, 0, 0, 15, 15, 3, 3, 2)
    # Twin interior brass fuel tanks inside basket floor
    fill_box(grid, 9, 10, 9, 10, 1, 4, 7)
    fill_box(grid, 13, 14, 13, 14, 1, 4, 7)
    grid[9, 9, 5] = 8
    grid[14, 14, 5] = 8

    # --- HANGING SANDBAGS ON GONDOLA EXTERIOR (Z: 2..5) ---
    # Plump tan sandbags hanging cleanly around all 4 sides of the wicker basket
    for sx in (7, 16):
        fill_box(grid, sx, sx, 10, 13, 2, 3, 7)
        grid[sx, 10, 4] = 6
        grid[sx, 13, 4] = 6
        grid[sx, 11, 3] = 1  # Crisp canvas highlight
        grid[sx, 12, 2] = 6  # Separation crease between twin bags
    for sy in (7, 16):
        fill_sym_box(grid, 1, 2, sy, sy, 2, 3, 7)
        fill_sym_box(grid, 2, 2, sy, sy, 4, 4, 6)

    # --- 4 TAUT SUSPENSION CABLES & OPEN BURNER FRAME (Z: 6..15) ---
    for bx in (8, 15):
        for by in (8, 15):
            # Vertical taut suspension cable from basket corner Z=7..15
            fill_box(grid, bx, bx, by, by, 7, 15, 8)
            # Brass rigging coupler at Z=10
            grid[bx, by, 10] = 7

    # Sleek iron X-cross burner frame at Z=9 (open sides so flame blazes in full view!)
    fill_box(grid, 8, 15, 11, 12, 9, 9, 8)
    fill_box(grid, 11, 12, 8, 15, 9, 9, 8)
    fill_box(grid, 8, 8, 8, 15, 9, 9, 8)
    fill_box(grid, 15, 15, 8, 15, 9, 9, 8)

    # Brass & Iron Burner Manifold (Z=9..10)
    fill_box(grid, 10, 13, 10, 13, 9, 10, 8)
    fill_box(grid, 10, 13, 10, 13, 10, 10, 7)

    # --- ROARING GLOWING ORANGE BURNER FLAME (Z: 11..15) ---
    # Tall, bold, unmistakable glowing orange burner plume rising right into the dark throat!
    fill_box(grid, 10, 13, 10, 13, 11, 13, 9)
    fill_box(grid, 11, 12, 11, 12, 14, 15, 9)
    # Hot golden-yellow flame heart
    fill_box(grid, 11, 12, 11, 12, 11, 13, 3)
    # Dancing flame tips around base
    grid[10, 11, 14] = 9
    grid[13, 12, 14] = 9
    grid[11, 13, 14] = 9
    grid[12, 10, 14] = 9

    # --- BULBOUS TEARDROP BALLOON ENVELOPE (Z: 15..42, HOLLOW 6-CONNECTED SHELL) ---
    def envelope_radius(z):
        if z < 15 or z > 42:
            return 0.0
        if z <= 31:
            # Classic teardrop flare from throat (R=4.5) to full equator (R=9.4)
            t = (z - 15.0) / 16.0
            return 4.5 + 4.9 * math.sin(t * math.pi * 0.5) ** 0.85
        else:
            # Lush hemispherical crown dome (z=31..42)
            dz = (z - 31.0) / 11.0
            if dz >= 1.0:
                return 0.0
            return 9.4 * math.sqrt(max(0.0, 1.0 - dz * dz))

    solid = np.zeros((24, 24, 44), dtype=bool)
    for z in range(15, 43):
        base_r = envelope_radius(z)
        if base_r <= 0.5:
            continue
        for x in range(24):
            for y in range(24):
                dx = x + 0.5 - cx
                dy = y + 0.5 - cy
                dist = math.hypot(dx, dy)
                angle = math.atan2(dy, dx)
                gore_puff = 0.24 * abs(math.sin(angle * 6.0)) * min(1.0, (z - 15.0) / 8.0)
                if dist <= base_r + gore_puff:
                    solid[x, y, z] = True

    shell = extract_connected_shell(solid)

    # Paint vertical striped gores + crisp white equatorial band onto shell
    gore_colors = [2, 3, 4]  # Crimson Red, Sunny Golden Yellow, Royal Sky Blue
    for z in range(15, 43):
        for x in range(24):
            for y in range(24):
                if not shell[x, y, z]:
                    continue

                dx = x + 0.5 - cx
                dy = y + 0.5 - cy
                dist = math.hypot(dx, dy)

                # Leave hollow dark throat opening at bottom (z=15..16) so burner flame shines inside!
                if z == 15 and dist < 3.3:
                    continue
                if z == 16 and dist < 2.7:
                    continue

                # Dark fireproof throat skirt at z=15..16
                if z == 15:
                    grid[x, y, z] = 8
                    continue
                if z == 16:
                    grid[x, y, z] = 7 if ((x + y) % 2 == 0) else 8
                    continue

                # 12 vertical gores around circumference
                angle = (math.atan2(dy, dx) + math.pi) % (2.0 * math.pi)
                gore_idx = int(angle / (2.0 * math.pi / 12.0)) % 12
                col = gore_colors[gore_idx % 3]

                # Crisp white equatorial band with festive stepped trim (z=29..31)
                chevron = 1 if (gore_idx % 2 == 0) else 0
                if 29 <= z <= 31:
                    col = 1
                elif z == 28 and chevron == 0:
                    col = 1
                elif z == 32 and chevron == 1:
                    col = 1
                # Upper decorative white crown ring (z=39)
                elif z == 39:
                    col = 1
                # Brass deflation valve / crown cap at top (z=42)
                elif z >= 42:
                    col = 7

                grid[x, y, z] = col

    # Ensure the 4 cables at (8,8), (8,15), (15,8), (15,15) solidly meet the throat skirt at Z=15..16
    for bx in (8, 15):
        for by in (8, 15):
            grid[bx, by, 15] = 8
            grid[bx, by, 16] = 8
            ix = 9 if bx == 8 else 14
            iy = 9 if by == 8 else 14
            grid[ix, by, 15] = 8
            grid[bx, iy, 15] = 8

    # Crown finial button at top of envelope (Z=42..43)
    fill_box(grid, 11, 12, 11, 12, 42, 43, 7)

    return grid


# ==========================================
# FORM B: AERONAUT BALLOON ROBOT (36 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((36, 24, 42), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 17
    cx_r = X // 2      # 18

    # --- 1. GROUNDED AERONAUT BOOTS / FEET (Z: 0..3) ---
    # Heavy dark iron soles + dark leather explorer boots + brass toe caps
    fill_sym_box(grid, 3, 6, 8, 15, 0, 1, 8)
    fill_sym_box(grid, 3, 6, 9, 15, 1, 2, 6)
    fill_sym_box(grid, 3, 6, 15, 16, 0, 2, 7)   # Brass armored toe cap
    fill_sym_box(grid, 4, 5, 16, 17, 0, 1, 7)   # Front toe tip
    fill_sym_box(grid, 3, 6, 8, 9, 0, 2, 8)     # Iron heel spur
    fill_sym_box(grid, 3, 6, 10, 14, 3, 3, 1)   # Crisp white ankle gaiter cuff

    # --- 2. CABLE-BOUND LOWER LEGS / SHINS (Z: 4..13) ---
    # Sturdy inner dark-iron frame
    fill_sym_box(grid, 3, 5, 10, 13, 4, 13, 8)
    # Royal sky-blue front shin greaves + white center stripe
    fill_sym_box(grid, 3, 5, 13, 14, 4, 11, 4)
    fill_sym_box(grid, 4, 4, 14, 14, 5, 10, 1)
    # Warm leather/wicker side shin panels wrapped with taut dark suspension cables
    fill_sym_box(grid, 6, 6, 10, 13, 4, 11, 6)
    for cz in (5, 8, 11):
        # Horizontal cable-wrap straps & brass buckles around legs
        fill_sym_box(grid, 3, 6, 9, 14, cz, cz, 8)
        fill_sym_box(grid, 6, 6, 11, 12, cz, cz, 7)  # Brass cable buckle on outer leg
        fill_sym_box(grid, 3, 5, 14, 14, cz, cz, 7)  # Front brass strap clasp
    # Rear calf stabilizers
    fill_sym_box(grid, 4, 5, 9, 9, 5, 11, 5)
    # Domed crimson & brass knee guards (Z=11..14)
    fill_sym_box(grid, 3, 5, 14, 15, 11, 13, 2)
    fill_sym_box(grid, 4, 4, 15, 15, 12, 13, 3)  # Yellow knee jewel
    fill_sym_box(grid, 3, 5, 14, 14, 14, 14, 7)  # Brass knee brow

    # --- 3. CABLE-BOUND THIGHS (Z: 14..18) ---
    fill_sym_box(grid, 3, 5, 10, 13, 14, 18, 8)  # Dark iron cable-core thigh
    fill_sym_box(grid, 3, 5, 13, 14, 15, 17, 1)  # Crisp white thigh plates
    fill_sym_box(grid, 5, 5, 11, 13, 15, 17, 7)  # Brass outer thigh strut
    fill_sym_box(grid, 3, 5, 10, 13, 16, 16, 8)  # Mid-thigh cable band

    # --- 4. WOVEN WICKER GONDOLA WAIST / PELVIS (Z: 18..22) ---
    # Unmistakable boxy woven brown wicker gondola basket forming the robot's waist!
    fill_wicker_box(grid, cx_l - 5, cx_r + 5, 8, 15, 18, 21, hollow=False)
    # Hollow interior of waist slightly to keep voxel count clean
    fill_box(grid, cx_l - 3, cx_r + 3, 10, 13, 19, 20, 0)
    # Dark leather padded gondola basket rim at Z=22
    fill_sym_box(grid, 0, 5, 8, 15, 22, 22, 6)
    fill_box(grid, cx_l - 3, cx_r + 3, 10, 13, 22, 22, 8)  # Solid waist axle core
    # Brass corner brackets on gondola waist (front & back corners)
    fill_sym_box(grid, 5, 5, 15, 15, 18, 22, 7)
    fill_sym_box(grid, 5, 5, 8, 8, 18, 22, 7)
    # Front basket prow / belt buckle & center codpiece (Z=17..22)
    fill_sym_box(grid, 0, 1, 14, 16, 17, 21, 6)
    fill_sym_box(grid, 0, 1, 16, 16, 19, 21, 7)  # Brass aeronaut belt buckle
    fill_sym_box(grid, 0, 0, 16, 16, 20, 20, 2)  # Crimson center crest
    # Hip joint connectors to thighs
    fill_sym_box(grid, 2, 4, 10, 13, 18, 18, 8)

    # --- SANDBAG HIP PODS ON GONDOLA WAIST (Z: 17..21) ---
    # Plump hanging tan sandbags on both hips (x_off=6..7) directly tied to basket waist!
    fill_sym_box(grid, 6, 7, 10, 13, 17, 20, 7)  # Sandbag body
    fill_sym_box(grid, 7, 7, 11, 12, 18, 19, 1)  # Highlight patch on sandbag
    fill_sym_box(grid, 6, 6, 10, 13, 21, 21, 6)  # Rope cinch tie
    fill_sym_box(grid, 5, 6, 11, 12, 21, 22, 6)  # Strap attached to basket rim

    # --- 5. GRAND ROUNDED STRIPED BALLOON-GORE CHEST CUIRASS (Z: 23..33) ---
    # 4 short taut suspension cable struts bridging wicker waist (Z=22) to balloon torso (Z=24)
    fill_sym_box(grid, 4, 4, 9, 9, 23, 24, 8)
    fill_sym_box(grid, 4, 4, 14, 14, 23, 24, 8)
    fill_sym_box(grid, 0, 3, 9, 14, 23, 24, 8)  # Dark iron inner waist-chest core

    # Rounded bulbous striped chest cuirass built as a sculpted ellipsoid shell
    # Center: x=17.5, y=12.0, z=28.0; rx=7.4, ry=6.3, rz=5.5
    chest_solid = np.zeros((X, Y, Z), dtype=bool)
    for z in range(23, 34):
        for y in range(6, 19):
            for x in range(10, 26):
                dx = (x + 0.5 - 17.5) / 7.2
                dy = (y + 0.5 - 11.8) / 6.2
                dz = (z + 0.5 - 28.0) / 5.5
                # Slightly broader upper chest for heroic V-taper
                if z >= 29:
                    dx *= 0.92
                if dx * dx + dy * dy + dz * dz <= 1.0:
                    chest_solid[x, y, z] = True

    # Write 6-connected hollow outer shell of chest cuirass with vertical balloon gores + white band
    chest_shell = extract_connected_shell(chest_solid)
    for z in range(23, 34):
        for y in range(6, 19):
            for x in range(10, 26):
                if not chest_shell[x, y, z]:
                    continue

                x_off = abs(x - cx_r) if x >= cx_r else abs(cx_l - x)
                # Vertical balloon gore stripes radiating symmetrically from sternum:
                # x_off 0..1: Red (2) / center core; 2..3: Yellow (3); 4..5: Blue (4); 6..7: Red (2)
                if x_off <= 1:
                    col = 2
                elif x_off <= 3:
                    col = 3
                elif x_off <= 5:
                    col = 4
                else:
                    col = 2

                # Crisp white equatorial band wrapping around mid-lower chest cuirass (Z=26..27)
                if z == 26 or (z == 27 and x_off >= 2):
                    col = 1
                # Brass lower hem trim where chest meets cables/gondola
                elif z == 23:
                    col = 7 if (x_off % 2 == 0) else 8
                # Upper throat collar trim
                elif z == 33 and x_off <= 3:
                    col = 7

                grid[x, y, z] = col

    # --- BLAZING ORANGE BURNER CORE IN CHEST / COLLAR (Z: 26..32, Front +Y) ---
    # Dark iron throat bezel & brass ring around chest burner core
    fill_sym_box(grid, 0, 2, 16, 17, 27, 31, 8)
    fill_sym_box(grid, 0, 2, 17, 17, 27, 27, 7)
    fill_sym_box(grid, 0, 2, 17, 17, 31, 31, 7)
    fill_sym_box(grid, 2, 2, 17, 17, 27, 31, 7)
    # Glowing orange burner flame core blazing right out of the chest!
    fill_sym_box(grid, 0, 1, 17, 18, 28, 30, 9)
    fill_sym_box(grid, 0, 0, 18, 18, 29, 29, 3)  # White-hot golden-yellow heart
    # Secondary collar burner vents just below chin (Z=32)
    fill_sym_box(grid, 0, 1, 14, 15, 32, 32, 9)
    fill_sym_box(grid, 2, 2, 14, 15, 32, 33, 7)  # Brass collar lapels

    # --- 6. MASSIVE CURVED STRIPED BALLOON-DOME SHOULDER PAULDRONS (Z: 27..36) ---
    # Thick shoulder axles connecting torso to pauldrons
    fill_sym_box(grid, 6, 10, 10, 13, 29, 31, 8)
    fill_sym_box(grid, 7, 8, 10, 13, 30, 31, 7)

    # Sculpt massive symmetrical balloon-dome pauldrons (6-connected hollow domes!)
    for side in (-1, 1):
        scx = (cx_r + 10.5) if side == 1 else (cx_l - 10.5)
        scy = 11.8
        scz = 30.8
        p_solid = np.zeros((X, Y, Z), dtype=bool)
        for z in range(27, 37):
            for y in range(6, 18):
                for x in range(1, X - 1):
                    dx = (x + 0.5 - scx) / 4.5
                    dy = (y + 0.5 - scy) / 4.5
                    dz = (z + 0.5 - scz) / 4.9
                    # Slight flared dome profile (full rounded top, curved bell bottom)
                    if dz < 0:
                        r2 = (dx * 0.92) ** 2 + (dy * 0.92) ** 2 + (dz * 1.15) ** 2
                    else:
                        r2 = dx * dx + dy * dy + dz * dz
                    if r2 <= 1.0:
                        p_solid[x, y, z] = True

        p_shell = extract_connected_shell(p_solid)
        # Paint hollow pauldron dome surface with balloon gores!
        gore_cols = [2, 3, 4]  # Red, Yellow, Blue
        for z in range(27, 37):
            for y in range(6, 18):
                for x in range(1, X - 1):
                    if not p_shell[x, y, z]:
                        continue
                    # Open bottom underside of dome slightly so arm exits naturally
                    if z == 27 and math.hypot(x + 0.5 - scx, y + 0.5 - scy) < 2.5:
                        continue

                    ang = (math.atan2(y + 0.5 - scy, x + 0.5 - scx) + math.pi) % (2.0 * math.pi)
                    g_idx = int(ang / (2.0 * math.pi / 9.0)) % 9
                    col = gore_cols[g_idx % 3]

                    # Crisp white equatorial stripe around each balloon-dome shoulder!
                    if z == 31:
                        col = 1
                    elif z == 27:
                        col = 8  # Dark throat trim rim at bottom of pauldron
                    elif z == 28 and (x + y) % 2 == 0:
                        col = 7  # Brass rivet trim
                    elif z >= 35:
                        col = 7  # Brass dome crown finial

                    grid[x, y, z] = col

        # Brass finial button atop each balloon shoulder dome (Z=36)
        fx = int(round(scx - 0.5))
        fy = int(round(scy - 0.5))
        fill_box(grid, fx, fx + 1, fy, fy + 1, 35, 36, 7)

    # --- 7. ARMS, GAUNTLETS & AERONAUT PROPS (Z: 15..29) ---
    # Upper arms (cable-bound dark iron pistons emerging from pauldrons)
    fill_sym_box(grid, 9, 11, 10, 12, 23, 29, 8)
    fill_sym_box(grid, 9, 11, 10, 12, 25, 26, 7)  # Brass elbow ring
    # Forearms / Sky-Explorer Gauntlets (Z=17..23, slightly forward)
    fill_sym_box(grid, 9, 12, 10, 14, 17, 22, 4)  # Royal sky-blue gauntlets
    fill_sym_box(grid, 10, 11, 14, 14, 18, 21, 1) # Crisp white gauntlet stripe
    fill_sym_box(grid, 9, 12, 10, 14, 22, 22, 7)  # Brass elbow cuff
    fill_sym_box(grid, 9, 12, 10, 14, 17, 17, 6)  # Dark leather wrist cuff
    fill_sym_box(grid, 12, 12, 11, 13, 18, 21, 5) # Wicker side forearm guard
    # Fists (Z=15..16)
    fill_sym_box(grid, 9, 11, 11, 14, 15, 16, 8)
    fill_sym_box(grid, 9, 11, 14, 14, 15, 16, 7)  # Brass knuckles

    # RIGHT HAND (+X, viewer's left): Forward-pointing Brass Burner Flare-Lance!
    # Projects cleanly forward (+Y) so both balloon-dome shoulder pauldrons & sandbag hips stay unobstructed!
    rx = cx_r + 10  # x = 28
    fill_box(grid, rx - 1, rx + 1, 14, 19, 15, 17, 8)   # Dark iron lance receiver mounted to fist
    fill_box(grid, rx - 1, rx + 1, 15, 18, 16, 17, 7)   # Brass barrel shroud
    fill_box(grid, rx, rx + 1, 19, 21, 15, 17, 7)       # Flared brass burner nozzle bell
    fill_box(grid, rx, rx + 1, 21, 23, 16, 16, 9)       # Glowing orange burner pilot jet!
    grid[rx, 22, 16] = 3                                # Hot golden flame tip
    fill_box(grid, rx, rx, 16, 18, 18, 18, 2)           # Crimson fin sight atop lance

    # LEFT FOREARM (-X, viewer's right): Round Brass & Striped Compass Buckler Shield!
    lx = cx_l - 13  # x = 4
    fill_box(grid, lx, lx + 1, 10, 14, 18, 22, 7)   # Brass outer shield rim
    fill_box(grid, lx, lx, 11, 13, 19, 21, 1)       # Crisp white compass face
    grid[lx, 12, 20] = 7                            # Center brass pin
    grid[lx, 12, 21] = 2                            # Red North needle
    grid[lx, 12, 19] = 4                            # Blue South needle
    grid[lx, 13, 20] = 3                            # Yellow East mark
    grid[lx, 11, 20] = 3                            # Yellow West mark
    # Mount cleanly to outer left forearm
    fill_box(grid, lx + 1, lx + 2, 11, 13, 19, 21, 8)

    # --- 8. BRASS-TRIMMED AERONAUT HELMET / HEAD (Z: 33..41) ---
    # Sturdy neck
    fill_sym_box(grid, 0, 1, 10, 12, 33, 34, 8)
    # Main rounded aviator helmet dome (Z=34..39)
    fill_sym_box(grid, 0, 2, 9, 14, 34, 38, 4)   # Royal sky-blue helmet shell
    fill_sym_box(grid, 0, 2, 10, 13, 39, 39, 4)  # Rounded crown top
    fill_sym_box(grid, 0, 0, 10, 14, 38, 40, 2)  # Crimson center helmet stripe
    # Antique brass trim along brow, chin, and ear-cups
    fill_sym_box(grid, 0, 2, 14, 14, 38, 38, 7)  # Brass brow band
    fill_sym_box(grid, 3, 3, 10, 12, 35, 37, 7)  # Brass ear-cup headphones
    fill_sym_box(grid, 3, 3, 11, 11, 36, 36, 9)  # Glowing ear-cup jewel
    # Dark iron face mask & brass chin guard
    fill_sym_box(grid, 0, 2, 14, 14, 34, 35, 8)
    fill_sym_box(grid, 0, 0, 14, 15, 34, 35, 7)  # Brass respirator chin guard
    # EXPRESSIVE GLOWING AERONAUT GOGGLES / VISOR (Z=36..37, Y=14..15)
    fill_sym_box(grid, 0, 2, 14, 15, 36, 37, 7)  # Brass goggle frame
    fill_sym_box(grid, 1, 2, 15, 15, 36, 37, 9)  # Glowing orange goggle lenses
    fill_sym_box(grid, 1, 1, 15, 15, 37, 37, 3)  # Bright golden eye glint
    fill_sym_box(grid, 0, 0, 15, 15, 36, 37, 8)  # Crisp dark nose bridge between goggles
    # Brass & Crimson Sky-Explorer Helmet Crest / Finial (Z=40..41)
    fill_sym_box(grid, 0, 0, 11, 13, 40, 41, 7)
    fill_sym_box(grid, 0, 0, 13, 14, 40, 40, 2)

    # --- 9. BACKPACK: TWIN PROPANE BURNER THRUSTERS + FOLDED ENVELOPE PACK (Y: 4..7) ---
    # Central folded colorful balloon pack on upper back
    fill_sym_box(grid, 0, 3, 5, 7, 25, 32, 1)
    fill_sym_box(grid, 0, 0, 5, 5, 25, 32, 2)  # Red stripe
    fill_sym_box(grid, 1, 1, 5, 5, 25, 32, 3)  # Yellow stripe
    fill_sym_box(grid, 2, 2, 5, 5, 25, 32, 4)  # Blue stripe
    fill_sym_box(grid, 0, 3, 5, 6, 28, 29, 1)  # White cross-band
    # Twin antique-brass propane burner thruster cylinders flanking the pack
    fill_sym_box(grid, 3, 4, 4, 6, 24, 32, 7)
    fill_sym_box(grid, 3, 4, 4, 6, 33, 33, 8)  # Top valve caps
    fill_sym_box(grid, 3, 4, 4, 6, 23, 23, 8)  # Bottom thruster nozzles
    fill_sym_box(grid, 3, 4, 5, 5, 22, 22, 9)  # Glowing orange pilot flame vents!
    # Solid brackets connecting backpack to rear chest
    fill_sym_box(grid, 1, 3, 7, 8, 26, 31, 8)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=36, pitch_a=20, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "balloon_a.vox")
    v_b = export_vox(model_b, "balloon_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: HOT AIR BALLOON -> AERONAUT BALLOON ROBOT",
        "1. HOT AIR BALLOON",
        "2. AERONAUT BALLOON ROBOT",
        "preview_balloon.png",
        yaw_a=36, pitch_a=20, yaw_b=32, pitch_b=20,
    )
    print(f"balloon: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
