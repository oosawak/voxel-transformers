import math
import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (212, 222, 234, 255),  # Polished Alien Silver-Chrome (Main Saucer Hull / Armor)
    2: (138, 152, 172, 255),  # Brushed Titanium Mid-Grey (Bevels / Limbs / Trim)
    3: (52, 62, 78, 255),     # Dark Gunmetal Slate (Rim Channel / Under-Hull / Frame)
    4: (30, 36, 48, 255),     # Deep Void Charcoal (Recesses / Visor Base / Joints)
    5: (86, 68, 152, 255),    # Cosmic Violet-Indigo (Alien Tech Inlays / Stripes)
    6: (42, 186, 162, 255),   # Translucent Emerald-Teal Dome Glass
    7: (122, 252, 218, 255),  # Bright Alien Plasma Cyan (Dome Glint / Rim Lights / Conduits)
    8: (172, 255, 78, 255),   # Radioactive Lime Plasma (Rim Lights / Alien Visor Eyes)
    9: (255, 186, 56, 255),   # Solar Amber Tractor-Beam Core (Underside Emitter / Chest Core)
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


def fill_ring_z(grid, cx, cy, z, r_in, r_out, col, sx=1.0, sy=1.0):
    """Fill an elliptical/circular ring at slice z where r_in <= r <= r_out."""
    X, Y, Z = grid.shape
    if not (0 <= z < Z):
        return
    r_in2 = r_in * r_in
    r_out2 = r_out * r_out
    for x in range(X):
        dx = (x - cx) / sx
        for y in range(Y):
            dy = (y - cy) / sy
            d2 = dx * dx + dy * dy
            if r_in2 <= d2 <= r_out2:
                grid[x, y, z] = col


# ==========================================
# FORM A: FLYING SAUCER UFO (30 x 30 x 14)
# ==========================================
def build_a():
    grid = np.zeros((30, 30, 14), dtype=np.uint8)
    cx, cy = 14.5, 14.5

    # --- Z=0: Underside Tractor-Beam Emitter Ring ---
    fill_ring_z(grid, cx, cy, 0, 0.0, 5.6, 3)   # Outer gunmetal emitter bezel
    fill_ring_z(grid, cx, cy, 0, 2.1, 4.1, 9)   # Glowing amber tractor-beam ring
    fill_ring_z(grid, cx, cy, 0, 0.0, 2.1, 7)   # Bright cyan tractor focus core

    # --- Z=1: Lower Hull Inner Bevel (hollow interior r < 4.2) ---
    fill_ring_z(grid, cx, cy, 1, 4.2, 9.2, 3)
    fill_ring_z(grid, cx, cy, 1, 7.6, 9.2, 2)
    # Four diagonal cosmic-violet thruster inlays on lower hull
    for ang_deg in (45, 135, 225, 315):
        ang = math.radians(ang_deg)
        for rad in (6.5, 7.5):
            px = int(round(cx + rad * math.cos(ang)))
            py = int(round(cy + rad * math.sin(ang)))
            fill_box(grid, px - 1, px + 1, py - 1, py + 1, 1, 1, 5)

    # --- Z=2: Lower Saucer Hull Outer Bevel (hollow interior r < 7.8) ---
    fill_ring_z(grid, cx, cy, 2, 7.8, 12.6, 3)
    fill_ring_z(grid, cx, cy, 2, 11.2, 12.6, 2)

    # --- Z=3: Widest Saucer Rim Lower Channel (hollow interior r < 11.2) ---
    fill_ring_z(grid, cx, cy, 3, 11.2, 14.3, 3)

    # --- Z=4: Widest Saucer Rim Upper Lip (hollow interior r < 10.6) ---
    fill_ring_z(grid, cx, cy, 4, 10.6, 14.3, 2)
    fill_ring_z(grid, cx, cy, 4, 10.6, 12.9, 1)

    # 12 Glowing Plasma Rim Lights spaced evenly around the perimeter (Z=3..4)
    for i in range(12):
        ang = math.radians(i * 30 + 15)
        light_col = 7 if i % 2 == 0 else 8
        for rad in (13.3, 14.1):
            px = int(round(cx + rad * math.cos(ang)))
            py = int(round(cy + rad * math.sin(ang)))
            if 0 <= px < 30 and 0 <= py < 30:
                grid[px, py, 3] = light_col
                grid[px, py, 4] = light_col
        # Add subtle adjacent glow voxel along tangent on the outer rim at Z=3
        tang = ang + math.radians(4.5)
        tx = int(round(cx + 13.8 * math.cos(tang)))
        ty = int(round(cy + 13.8 * math.sin(tang)))
        if 0 <= tx < 30 and 0 <= ty < 30:
            grid[tx, ty, 3] = light_col

    # --- Z=5: Upper Saucer Hull Main Deck (hollow interior r < 8.6) ---
    fill_ring_z(grid, cx, cy, 5, 8.6, 12.9, 1)
    fill_ring_z(grid, cx, cy, 5, 11.8, 12.9, 2)

    # --- Z=6: Upper Saucer Hull Mid-Deck (hollow interior r < 6.0) ---
    fill_ring_z(grid, cx, cy, 6, 6.0, 10.4, 1)
    fill_ring_z(grid, cx, cy, 6, 9.4, 10.4, 2)

    # Radial gunmetal panel seams & cosmic-violet alien tech arcs on upper deck (Z=5..6)
    for x in range(30):
        for y in range(30):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            ang = math.degrees(math.atan2(dy, dx)) % 360
            # 4 cardinal panel seam grooves
            if (min(abs(ang - 0), abs(ang - 360)) < 5.0 or
                    abs(ang - 90) < 5.0 or abs(ang - 180) < 5.0 or abs(ang - 270) < 5.0):
                if 9.2 <= r <= 12.5 and grid[x, y, 5] > 0:
                    grid[x, y, 5] = 3
                if 6.8 <= r <= 9.8 and grid[x, y, 6] > 0:
                    grid[x, y, 6] = 3
            # 4 diagonal cosmic-violet armor arcs
            for diag in (45, 135, 225, 315):
                if abs(ang - diag) < 12.0:
                    if 9.6 <= r <= 11.5 and grid[x, y, 5] > 0:
                        grid[x, y, 5] = 5
                    if 7.2 <= r <= 8.8 and grid[x, y, 6] > 0:
                        grid[x, y, 6] = 5

    # 4 radial amber/cyan emitter nodes on upper saucer deck (front +Y node slightly larger)
    fill_sym_box(grid, 0, 1, 25, 25, 5, 5, 9)
    fill_sym_box(grid, 0, 0, 26, 26, 5, 5, 7)
    fill_sym_box(grid, 0, 1, 22, 22, 6, 6, 9)
    for px, py in ((14, 4), (15, 4), (25, 14), (25, 15), (4, 14), (4, 15)):
        grid[px, py, 5] = 9

    # --- Z=7: Dome Collar Ring + Sealed Cockpit Floor ---
    fill_ring_z(grid, cx, cy, 7, 4.6, 8.0, 3)   # Dark gunmetal dome collar
    fill_ring_z(grid, cx, cy, 7, 6.8, 8.0, 2)   # Titanium collar bevel
    fill_ring_z(grid, cx, cy, 7, 0.0, 4.8, 4)   # Dark recessed cockpit interior base
    fill_ring_z(grid, cx, cy, 7, 1.5, 3.6, 6)   # Glowing green/teal interior under-glow
    # 4 Collar emitter lights (cardinal)
    for px, py in ((14, 21), (15, 21), (14, 8), (15, 8), (21, 14), (21, 15), (8, 14), (8, 15)):
        grid[px, py, 7] = 8

    # --- Z=8..13: Translucent Glowing Central Glass Dome (hollow hemisphere, 6-connected cap) ---
    dome_z0 = 7.2
    dome_r = 5.5
    for z in range(8, 14):
        dz = z - dome_z0
        if dz > dome_r:
            continue
        r_out = math.sqrt(max(0.0, dome_r * dome_r - dz * dz))
        r_in = max(0.0, r_out - 1.8) if z < 11 else 0.0
        for x in range(30):
            dx = x - cx
            for y in range(30):
                dy = y - cy
                r = math.hypot(dx, dy)
                if r_in <= r <= r_out:
                    # Translucent emerald-teal glass with bright cyan specular highlights
                    if z >= 12 and r <= 1.8:
                        col = 7
                    elif dx > 0.3 and dy > 0.3 and z in (9, 10, 11):
                        col = 7  # Front-right glossy glass glint
                    elif dx < -1.0 and dy < -1.0 and z == 10:
                        col = 7  # Rear subtle glass glint
                    elif z == 8 and (abs(dx) < 0.8 or abs(dy) < 0.8):
                        col = 2  # 4 metallic dome base clamp struts
                    elif z == 9 and dy > 2.2 and abs(dx) <= 2.2:
                        col = 8  # Faint lime internal glow visible from front
                    else:
                        col = 6
                    grid[x, y, z] = col

    return grid


# ==========================================
# FORM B: UFO GALACTIC ROBOT (36 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((36, 24, 42), dtype=np.uint8)
    cx = 17.5
    cy = 11.5

    # --- 1. HOVERING DISC-RING FEET (Z: 0..3) ---
    # Each foot is a grounded mini-saucer ring centered at x_off = 5.0 (x=12.5, x=22.5)
    for fx in (12.5, 22.5):
        fy = 12.0
        # Z=0: Grounded circular hover emitter ring (amber + cyan glow inside gunmetal sole)
        fill_ring_z(grid, fx, fy, 0, 0.0, 3.6, 3)
        fill_ring_z(grid, fx, fy, 0, 1.5, 2.7, 9)
        fill_ring_z(grid, fx, fy, 0, 0.0, 1.5, 7)
        # Z=1: Saucer foot rim with glowing perimeter lights
        fill_ring_z(grid, fx, fy, 1, 0.0, 3.8, 3)
        fill_ring_z(grid, fx, fy, 1, 0.0, 2.7, 2)
        for i in range(8):
            ang = math.radians(i * 45)
            lx = int(round(fx + 3.4 * math.cos(ang)))
            ly = int(round(fy + 3.4 * math.sin(ang)))
            if 0 <= lx < 36 and 0 <= ly < 24:
                grid[lx, ly, 1] = 7 if i % 2 == 0 else 8
        # Z=2: Bevelled silver upper foot disc
        fill_ring_z(grid, fx, fy, 2, 0.0, 2.9, 1)
        fill_ring_z(grid, fx, fy, 2, 0.0, 1.8, 2)
        # Front toe accent
        fill_box(grid, int(fx - 1), int(fx + 1), 14, 15, 2, 2, 5)
        # Z=3: Ankle collar connecting foot to shin
        fill_ring_z(grid, fx, fy - 0.5, 3, 0.0, 2.0, 3)

    # --- 2. SLEEK LOWER LEGS / SHINS (Z: 4..13) ---
    fill_sym_box(grid, 4, 6, 10, 13, 4, 13, 1)   # Main silver greave
    fill_sym_box(grid, 4, 6, 9, 10, 4, 12, 3)    # Dark gunmetal rear calf
    fill_sym_box(grid, 6, 6, 10, 12, 5, 11, 2)   # Outer brushed titanium fairing
    fill_sym_box(grid, 6, 6, 11, 11, 5, 11, 7)   # Glowing cyan energy conduit stripe
    fill_sym_box(grid, 5, 5, 13, 14, 5, 11, 2)   # Front shin crest
    fill_sym_box(grid, 5, 5, 14, 14, 7, 10, 8)   # Lime plasma shin strip
    # Knee armor guards (Z: 11..14)
    fill_sym_box(grid, 4, 6, 13, 14, 11, 14, 5)  # Cosmic violet knee guard
    fill_sym_box(grid, 5, 5, 14, 15, 12, 13, 1)  # Silver knee cap
    fill_sym_box(grid, 5, 5, 9, 9, 6, 10, 7)     # Rear calf hover vent
    # Hollow unseen inner shin core
    fill_sym_box(grid, 5, 5, 11, 12, 5, 11, 0)

    # --- 3. THIGHS (Z: 14..18) ---
    fill_sym_box(grid, 4, 5, 10, 12, 14, 18, 3)  # Gunmetal inner frame
    fill_sym_box(grid, 4, 6, 11, 13, 14, 18, 2)  # Titanium thigh armor
    fill_sym_box(grid, 4, 5, 13, 13, 15, 17, 1)  # Silver front thigh plate
    fill_sym_box(grid, 6, 6, 11, 12, 15, 17, 7)  # Outer thigh cyan conduit

    # --- 4. PELVIS & FLARING SAUCER-RIM WAIST SKIRT (Z: 18..22) ---
    # Solid pelvis core connecting thighs to torso (hollow inner block)
    fill_sym_box(grid, 0, 5, 9, 13, 18, 21, 3)
    fill_sym_box(grid, 0, 3, 9, 13, 21, 22, 4)
    fill_sym_box(grid, 0, 2, 10, 12, 19, 21, 0)

    # Flaring circular/elliptical saucer waist skirt (unmistakable split saucer hull!)
    # Z=21: Upper skirt hull bevel connecting directly to pelvis
    fill_ring_z(grid, cx, cy, 21, 3.0, 7.6, 1, sx=1.18, sy=0.95)
    fill_ring_z(grid, cx, cy, 21, 6.2, 7.6, 2, sx=1.18, sy=0.95)
    # Z=20: Wide saucer skirt rim with gunmetal edge & perimeter plasma lights!
    fill_ring_z(grid, cx, cy, 20, 5.2, 8.8, 1, sx=1.18, sy=0.96)
    fill_ring_z(grid, cx, cy, 20, 7.5, 8.8, 3, sx=1.18, sy=0.96)
    # Z=19: Lower flaring saucer lip
    fill_ring_z(grid, cx, cy, 19, 7.2, 9.0, 3, sx=1.18, sy=0.96)
    fill_ring_z(grid, cx, cy, 19, 8.1, 9.0, 2, sx=1.18, sy=0.96)

    # Cosmic-violet armor inlays on upper waist skirt (Z=21)
    for ang_deg in (45, 135, 225, 315):
        ang = math.radians(ang_deg)
        px = int(round(cx + 6.0 * 1.18 * math.cos(ang)))
        py = int(round(cy + 6.0 * 0.95 * math.sin(ang)))
        fill_box(grid, px - 1, px + 1, py - 1, py + 1, 21, 21, 5)

    # 12 Glowing Perimeter Plasma Lights around the Saucer Waist Skirt (Z=19..20)
    for i in range(12):
        ang = math.radians(i * 30 + 15)
        light_col = 7 if i % 2 == 0 else 8
        px = int(round(cx + 8.6 * 1.18 * math.cos(ang)))
        py = int(round(cy + 8.6 * 0.96 * math.sin(ang)))
        if 0 <= px < 36 and 0 <= py < 24:
            grid[px, py, 20] = light_col
            grid[px, py, 19] = light_col

    # Front waist centerpiece & belt buckle
    fill_sym_box(grid, 0, 1, 14, 16, 19, 22, 1)
    fill_sym_box(grid, 0, 1, 16, 17, 19, 21, 5)
    fill_sym_box(grid, 0, 0, 17, 17, 20, 21, 8)

    # --- 5. TORSO & GLOWING TRACTOR-BEAM CHEST CORE (Z: 22..32) ---
    # Sleek tapered abdomen (Z: 22..24)
    fill_sym_box(grid, 0, 3, 9, 13, 22, 24, 3)
    fill_sym_box(grid, 0, 2, 13, 14, 22, 24, 2)
    fill_sym_box(grid, 2, 3, 13, 13, 23, 24, 7)  # Glowing cyan waist conduits
    fill_sym_box(grid, 0, 1, 10, 12, 22, 24, 0)  # Hollow ab core

    # Broad upper alien-tech chest (Z: 25..31)
    fill_sym_box(grid, 0, 5, 8, 14, 25, 31, 1)
    fill_sym_box(grid, 0, 4, 8, 13, 25, 26, 2)
    fill_sym_box(grid, 4, 5, 12, 14, 26, 30, 5)  # Cosmic violet pectoral flanks
    fill_sym_box(grid, 2, 5, 13, 14, 30, 31, 2)  # Clavicle titanium trim
    fill_sym_box(grid, 3, 4, 14, 14, 30, 30, 7)  # Collar cyan accents
    # Hollow interior of chest to keep voxel budget crisp
    fill_sym_box(grid, 0, 4, 9, 12, 26, 30, 0)

    # Iconic Underside Tractor-Beam Emitter glowing on the Chest Core!
    core_cz = 27.5
    for x in range(14, 22):
        for z in range(24, 32):
            r = math.hypot(x - cx, z - core_cz)
            if r <= 3.3:
                grid[x, 14, z] = 3  # Gunmetal emitter housing
            if r <= 2.9:
                grid[x, 15, z] = 3  # Protruding bezel
            if 1.1 <= r <= 2.2:
                grid[x, 15, z] = 9  # Glowing solar amber tractor-beam ring!
            if r < 1.1:
                grid[x, 15, z] = 7  # Bright cyan core
                grid[x, 16, z] = 7

    # --- 6. BACKPACK / ANTIGRAV DRIVE PACK (Y: 5..8, Z: 24..32) ---
    fill_sym_box(grid, 0, 4, 6, 8, 24, 31, 2)
    fill_sym_box(grid, 0, 3, 5, 6, 25, 30, 3)
    fill_sym_box(grid, 0, 2, 7, 7, 26, 29, 0)  # Hollow backpack interior
    # Twin glowing antigrav disc vents on back
    for bx in (14.5, 20.5):
        for x in range(12, 24):
            for z in range(25, 31):
                r = math.hypot(x - bx, z - 27.5)
                if r <= 2.1:
                    grid[x, 5, z] = 3
                if 0.9 <= r <= 1.6:
                    grid[x, 5, z] = 9
                if r < 0.9:
                    grid[x, 5, z] = 7
    # Swept cosmic-violet rear stabilizer fins
    for i in range(4):
        fill_sym_box(grid, 3 + i, 4 + i, 5, 6, 29 + i, 30 + i, 5 if i < 3 else 7)

    # --- 7. NECK COLLAR & BUBBLE-DOME ROBOT HEAD (Z: 31..41) ---
    # Dome collar ring (matching Form A Z=7 dome collar!)
    fill_ring_z(grid, cx, cy, 31, 0.0, 4.4, 3)
    fill_ring_z(grid, cx, cy, 32, 0.0, 4.6, 3)
    fill_ring_z(grid, cx, cy, 32, 3.4, 4.6, 2)
    # Collar lime indicator lights
    for lx, ly in ((15, 15), (20, 15), (15, 8), (20, 8)):
        grid[lx, ly, 32] = 8

    # Bubble-dome head: glowing translucent glass hemisphere + alien visor eyes inside!
    head_cz = 34.4
    head_r = 4.9
    # Dark recessed inner faceplate core for deep visor contrast
    fill_box(grid, 15, 20, 12, 15, 33, 37, 4)
    for z in range(33, 42):
        dz = (z - head_cz) * 0.94
        if abs(dz) > head_r:
            continue
        r_out = math.sqrt(max(0.0, head_r * head_r - dz * dz))
        r_in = max(0.0, r_out - 1.55) if z < 39 else 0.0
        for x in range(12, 24):
            dx = x - cx
            for y in range(6, 18):
                dy = y - cy
                r = math.hypot(dx, dy)
                if r_in <= r <= r_out:
                    if z >= 39 and r <= 2.1:
                        col = 7  # Bright cyan dome apex glint
                    elif dx > 0.5 and dy > 0.2 and z in (36, 37, 38):
                        col = 7  # Specular highlight on dome
                    elif z == 33 and r >= 3.6:
                        col = 2  # Metallic dome rim seal
                    else:
                        col = 6  # Emerald-teal translucent dome glass
                    grid[x, y, z] = col

    # Unmistakable Glowing Alien Visor Eyes inside the front of the Bubble Dome!
    # Recessed dark visor faceplate (y=15..16, z=34..36)
    fill_sym_box(grid, 0, 2, 15, 16, 34, 36, 4)
    # Bright glowing alien eyes (slanted lime + cyan inner glint!)
    fill_sym_box(grid, 1, 2, 16, 16, 35, 36, 8)
    fill_sym_box(grid, 1, 1, 16, 16, 36, 36, 7)
    # Dome brow highlight directly above visor
    fill_sym_box(grid, 0, 2, 15, 16, 37, 37, 7)
    # Alien telemetry ear-pods / antennae on dome collar sides
    fill_sym_box(grid, 4, 5, 11, 12, 33, 35, 2)
    fill_sym_box(grid, 5, 5, 11, 12, 36, 38, 3)
    fill_sym_box(grid, 5, 5, 11, 12, 39, 39, 8)

    # --- 8. CURVED SEMICIRCULAR SAUCER SHOULDER PAULDRONS (Z: 27..36) ---
    # Solid shoulder connector struts from torso out to pauldrons & upper arms
    fill_sym_box(grid, 5, 9, 10, 13, 28, 31, 3)
    fill_sym_box(grid, 6, 9, 10, 12, 29, 30, 2)

    # Build true tilted semicircular saucer halves on both shoulders!
    theta = math.radians(28.0)
    ct, st = math.cos(theta), math.sin(theta)
    pivot_x_off = 6.8
    pivot_z = 31.4

    for side in (-1, 1):  # -1 = left (-X), +1 = right (+X)
        px0 = cx + side * pivot_x_off
        for x in range(0, 36):
            dx_world = (x - px0) * side
            if dx_world < -1.8:
                continue
            for y in range(3, 21):
                v = y - cy
                for z in range(25, 38):
                    dz_world = z - pivot_z
                    u = dx_world * ct - dz_world * st
                    w = dx_world * st + dz_world * ct
                    if u < -1.2:
                        continue
                    r_disc = math.hypot(u + 0.6, v)
                    if r_disc > 8.1:
                        continue

                    col = 0
                    # Upper curved saucer dome deck (hollow beneath w < 0.4 inside rim)
                    if 0.5 <= w <= 2.2 and r_disc <= 6.4:
                        if 2.7 <= r_disc <= 4.3 and abs(v) < 3.8:
                            col = 5  # Cosmic violet alien stripe
                        elif r_disc >= 5.3:
                            col = 2  # Titanium bevel
                        else:
                            col = 1  # Polished silver saucer shell
                    # Widest semicircular saucer rim with glowing plasma lights!
                    elif -1.0 <= w <= 0.7 and 4.6 <= r_disc <= 8.0:
                        if w >= 0.0 and r_disc <= 7.0:
                            col = 1  # Upper silver rim
                        elif r_disc >= 6.6:
                            ang = math.degrees(math.atan2(v, u + 0.6))
                            col = 3
                            for light_ang, lcol in ((-60, 7), (-30, 8), (0, 7), (30, 8), (60, 7)):
                                if abs(ang - light_ang) < 9.5 and w >= -0.8:
                                    col = lcol
                                    break
                        else:
                            col = 2
                    # Inner shoulder bridge thickness so pauldron joins solidly to strut
                    elif -1.4 <= w <= 0.6 and r_disc <= 4.2 and u <= 2.6 and abs(v) <= 2.4:
                        col = 3

                    if col > 0:
                        grid[x, y, z] = col

    # --- 9. SLEEK ALIEN ARMS & PLASMA RAY EMITTER (Z: 14..28) ---
    # Upper arms positioned heroically wide (x_off: 8..10) to frame the flaring saucer skirt!
    fill_sym_box(grid, 8, 10, 10, 12, 23, 28, 3)
    fill_sym_box(grid, 9, 10, 10, 12, 24, 27, 2)
    fill_sym_box(grid, 10, 10, 11, 11, 24, 27, 7)  # Glowing cyan bicep conduit

    # Elbow joints
    fill_sym_box(grid, 9, 10, 10, 12, 21, 22, 4)
    fill_sym_box(grid, 10, 10, 10, 11, 21, 22, 5)

    # Sleek Forearms / Vambraces (x_off: 9..11, y: 10..14)
    fill_sym_box(grid, 9, 11, 10, 14, 16, 20, 1)
    fill_sym_box(grid, 9, 10, 10, 12, 16, 20, 2)
    fill_sym_box(grid, 11, 11, 11, 13, 16, 20, 5)  # Violet outer gauntlet trim
    fill_sym_box(grid, 11, 11, 12, 12, 17, 19, 8)  # Lime forearm energy strip
    fill_sym_box(grid, 10, 10, 14, 14, 17, 19, 7)  # Front cyan conduit

    # Articulated Alien Fists (Z: 14..15)
    fill_sym_box(grid, 9, 10, 11, 13, 14, 15, 4)

    # Right-Arm Galactic Tractor-Ray Blaster (+X side: x=27..29, extending forward to y=22)
    fill_box(grid, 27, 29, 13, 19, 15, 17, 3)      # Dark gunmetal receiver
    fill_box(grid, 27, 29, 14, 18, 17, 17, 1)      # Silver upper housing
    fill_box(grid, 28, 28, 15, 20, 16, 16, 9)      # Glowing amber emitter barrel
    fill_box(grid, 27, 29, 19, 19, 15, 17, 2)      # Front saucer-dish emitter ring
    fill_box(grid, 28, 28, 20, 22, 16, 16, 7)      # Bright cyan plasma muzzle tip
    fill_box(grid, 28, 28, 16, 18, 18, 18, 8)      # Top lime sight fin

    # Left-Arm Curved Mini-Saucer Energy Fin (-X side: x=5..6)
    fill_box(grid, 5, 6, 10, 14, 17, 20, 3)
    fill_box(grid, 5, 5, 11, 13, 18, 19, 7)
    fill_box(grid, 5, 5, 12, 12, 17, 20, 9)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=36, pitch_a=28, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "ufo_a.vox")
    v_b = export_vox(model_b, "ufo_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: FLYING SAUCER UFO -> UFO GALACTIC ROBOT",
        "1. FLYING SAUCER UFO",
        "2. UFO GALACTIC ROBOT",
        "preview_ufo.png",
        yaw_a=36, pitch_a=28, yaw_b=32, pitch_b=20,
    )
    print(f"ufo: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
