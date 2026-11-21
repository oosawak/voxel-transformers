import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (246, 194, 24, 255),   # Iconic Construction Yellow / Amber (Cab, Boom, Chest, Armor)
    2: (196, 138, 16, 255),   # Shaded Ochre / Deep Amber (Shading, Fenders, Lower Armor)
    3: (34, 38, 46, 255),     # Heavy Rubber Tire Charcoal / Hazard Black Stripes
    4: (78, 86, 98, 255),     # Gunmetal Steel (Chassis, Outriggers, Turntable, Joints)
    5: (158, 168, 182, 255),  # Brushed Steel (Telescopic Inner Boom, Lattice, Cable, Pistons)
    6: (212, 220, 232, 255),  # Bright Chrome / Silver (Wheel Hubs, Crane Hook, Faceplate)
    7: (80, 206, 244, 255),   # Bright Cyan Cab Glass / Robot Visor
    8: (234, 52, 42, 255),    # Signal Warning Red (Beacons, Tail Lights, Crest Jewel)
    9: (255, 238, 128, 255),  # Warm Headlight Glow / Cannon Energy Core
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


def fill_sym_wheel_x(
    grid, x_off0, x_off1, cy, cz, r_outer, r_rim, r_hub,
    tire_col=3, rim_col=1, hub_col=6,
):
    """Draw a pair of symmetrical heavy truck wheels along the X axis."""
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1
    cx_r = X // 2
    y_min = max(0, int(np.floor(cy - r_outer - 1)))
    y_max = min(Y - 1, int(np.ceil(cy + r_outer + 1)))
    z_min = max(0, int(np.floor(cz - r_outer - 1)))
    z_max = min(Z - 1, int(np.ceil(cz + r_outer + 1)))

    for y in range(y_min, y_max + 1):
        for z in range(z_min, z_max + 1):
            dist = np.hypot(y - cy, z - cz)
            if dist > r_outer:
                continue
            for x_off in range(x_off0, x_off1 + 1):
                is_outer = (x_off == x_off1)
                if dist <= r_hub:
                    col = hub_col if is_outer else 4
                elif dist <= r_rim:
                    col = rim_col if is_outer else 4
                else:
                    col = tire_col
                xl = cx_l - x_off
                xr = cx_r + x_off
                if 0 <= xl < X:
                    grid[xl, y, z] = col
                if 0 <= xr < X:
                    grid[xr, y, z] = col


# ==========================================
# FORM A: MOBILE CRANE TRUCK (18 x 40 x 28)
# ==========================================
def build_a():
    grid = np.zeros((18, 40, 28), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 8 (-X left)
    cx_r = grid.shape[0] // 2      # 9 (+X right)

    # --- THREE HEAVY MULTI-AXLE WHEELS (Z: 0..5, x_off: 4..5) ---
    # Tandem rear axles + heavy front steerable axle
    for wy in (7.0, 14.0, 28.0):
        fill_sym_wheel_x(
            grid, 4, 5, cy=wy, cz=2.5,
            r_outer=2.75, r_rim=1.55, r_hub=0.75,
            tire_col=3, rim_col=1, hub_col=6,
        )
        # Heavy gunmetal axle housing spanning across wheels
        fill_sym_box(grid, 0, 3, int(wy), int(wy), 2, 3, 4)

    # --- HEAVY CRANE CARRIER CHASSIS & DECK (Y: 2..34, Z: 3..6) ---
    fill_sym_box(grid, 0, 4, 2, 34, 4, 6, 4)
    # Hollow unseen inner chassis core to keep voxel budget sleek
    fill_sym_box(grid, 0, 3, 4, 32, 4, 5, 0)
    fill_sym_box(grid, 0, 3, 9, 15, 6, 6, 0)   # Hollow under turntable
    fill_sym_box(grid, 0, 4, 27, 32, 6, 6, 0)  # Hollow under front cab
    # Yellow side deck skirts & wheel arch fenders
    fill_sym_box(grid, 5, 5, 2, 34, 6, 6, 1)
    fill_sym_box(grid, 5, 5, 3, 4, 4, 5, 2)
    fill_sym_box(grid, 5, 5, 10, 11, 4, 5, 2)
    fill_sym_box(grid, 5, 5, 17, 24, 4, 5, 2)
    fill_sym_box(grid, 5, 5, 31, 33, 4, 5, 2)
    # Fuel tank & hydraulic fluid reservoir between mid and front axles
    fill_sym_box(grid, 4, 5, 21, 24, 3, 4, 5)
    fill_sym_box(grid, 5, 5, 22, 23, 4, 4, 4)
    # Hazard black-and-yellow striped front & rear bumpers
    fill_sym_box(grid, 0, 5, 34, 35, 3, 4, 1)
    for hx in (0, 2, 4):
        fill_sym_box(grid, hx, hx, 35, 35, 3, 4, 3)
    fill_sym_box(grid, 0, 5, 1, 2, 3, 5, 1)
    for hx in (1, 3, 5):
        fill_sym_box(grid, hx, hx, 1, 1, 3, 4, 3)
    # Rear red tail lights
    fill_sym_box(grid, 4, 5, 1, 1, 5, 5, 8)
    fill_sym_box(grid, 2, 3, 1, 1, 5, 5, 9)

    # --- DEPLOYED HEAVY OUTRIGGER STABILIZER ARMS (Front-Mid Y=19..20 & Rear Y=2..3) ---
    for oy in (2, 19):
        # Gunmetal outrigger beam extending outward to x_off=7
        fill_sym_box(grid, 5, 7, oy, oy + 1, 4, 5, 4)
        # Yellow/black hazard outer housing
        fill_sym_box(grid, 6, 7, oy, oy + 1, 5, 5, 1)
        fill_sym_box(grid, 7, 7, oy, oy, 5, 5, 3)
        # Vertical silver hydraulic jack cylinder & wide dark stabilizer foot pad touching ground
        fill_sym_box(grid, 7, 7, oy, oy, 1, 3, 5)
        fill_sym_box(grid, 6, 8, oy, oy + 1, 0, 0, 3)
        fill_sym_box(grid, 7, 7, oy, oy + 1, 1, 1, 4)

    # --- LOW-PROFILE FRONT CARRIER CAB (Y: 26..34, Z: 6..12) ---
    fill_sym_box(grid, 0, 5, 26, 33, 6, 11, 1)
    fill_sym_box(grid, 0, 4, 27, 32, 7, 10, 0)  # Hollow cab interior
    fill_sym_box(grid, 0, 4, 27, 32, 12, 12, 1)  # Slightly chamfered cab roof
    fill_sym_box(grid, 0, 5, 34, 34, 5, 8, 1)    # Lower cab front nose
    # Recessed lower front grille & bright headlights
    fill_sym_box(grid, 0, 2, 34, 34, 5, 7, 3)
    fill_sym_box(grid, 0, 2, 34, 34, 6, 6, 6)    # Chrome grille bar
    fill_sym_box(grid, 3, 4, 34, 34, 5, 6, 9)    # Warm glowing headlights
    fill_sym_box(grid, 5, 5, 34, 34, 5, 5, 8)    # Corner amber/red markers
    # Wide cyan front windshield & side windows
    fill_sym_box(grid, 0, 4, 33, 33, 9, 11, 7)
    fill_sym_box(grid, 0, 0, 33, 33, 9, 11, 3)   # Center windshield pillar
    fill_sym_box(grid, 5, 5, 28, 32, 9, 11, 7)   # Side cab windows
    fill_sym_box(grid, 5, 5, 30, 30, 9, 11, 3)   # Door mullion
    fill_sym_box(grid, 5, 5, 27, 33, 7, 7, 2)    # Deep ochre side crease
    # Twin red warning beacons on cab roof corners
    fill_sym_box(grid, 4, 4, 28, 29, 12, 13, 8)
    # Side mirrors
    fill_sym_box(grid, 6, 6, 32, 32, 9, 11, 3)
    fill_sym_box(grid, 5, 6, 32, 32, 11, 11, 4)

    # --- ROTATING TURNTABLE, COUNTERWEIGHT & CRANE OPERATOR BOOTH (Y: 3..18, Z: 7..14) ---
    # Slewing ring turntable pedestal (Y: 8..16, Z: 7..8)
    fill_sym_box(grid, 0, 3, 8, 16, 7, 8, 4)
    fill_sym_box(grid, 0, 4, 9, 15, 7, 8, 4)
    fill_sym_box(grid, 0, 3, 9, 15, 7, 8, 0)  # Hollow interior
    # Turntable upper yellow platform & heavy rear counterweight (Y: 3..15, Z: 9..13)
    fill_sym_box(grid, 0, 4, 3, 14, 9, 12, 1)
    fill_sym_box(grid, 0, 3, 5, 13, 9, 11, 0)  # Hollow interior
    # Heavy gunmetal & hazard-striped rear counterweight slab (Y: 2..6, Z: 9..13)
    fill_sym_box(grid, 0, 4, 2, 6, 9, 13, 4)
    fill_sym_box(grid, 0, 3, 3, 6, 9, 12, 0)  # Hollow counterweight core
    fill_sym_box(grid, 0, 4, 2, 2, 9, 11, 1)
    for hx in (0, 2, 4):
        fill_sym_box(grid, hx, hx, 2, 2, 9, 10, 3)  # Rear hazard stripes
    fill_sym_box(grid, 3, 4, 2, 2, 12, 13, 8)  # Red counterweight warning lights
    # Side Crane Operator Glass Booth on -X side of turntable (X: cx_l-5..cx_l-2, Y: 10..16, Z: 9..14)
    fill_box(grid, cx_l - 5, cx_l - 2, 10, 16, 9, 14, 1)
    fill_box(grid, cx_l - 4, cx_l - 3, 11, 15, 10, 13, 0)  # Hollow booth
    fill_box(grid, cx_l - 5, cx_l - 3, 16, 16, 10, 13, 7)  # Front cyan glass
    fill_box(grid, cx_l - 5, cx_l - 5, 11, 15, 11, 13, 7)  # Side cyan glass
    fill_box(grid, cx_l - 5, cx_l - 5, 13, 13, 11, 13, 3)  # Window pillar
    fill_box(grid, cx_l - 4, cx_l - 3, 13, 14, 15, 15, 8)  # Operator booth beacon
    # Winch cable drum on top of turntable behind boom pivot
    fill_sym_box(grid, 0, 2, 6, 9, 13, 14, 4)
    fill_sym_box(grid, 0, 1, 7, 8, 13, 14, 5)  # Steel cable spool

    # --- ELEVATED TELESCOPIC CRANE BOOM (Y: 8..38, Z: 11..27) ---
    # Solid pivot turret cheeks holding the boom base
    fill_sym_box(grid, 2, 2, 7, 13, 12, 15, 2)
    fill_sym_box(grid, 2, 2, 9, 10, 13, 14, 6)  # Pivot hinge pin

    # Stage 1: Heavy yellow outer telescopic boom box (Y: 9..23, rising smoothly Z: 12..21)
    for i in range(15):
        y = 9 + i
        z_bot = 12 + (i * 8) // 14
        fill_sym_box(grid, 0, 1, y, y, z_bot, z_bot + 3, 1)
        # Side ochre & steel lattice reinforcement pattern
        if i % 3 == 0:
            fill_sym_box(grid, 1, 1, y, y, z_bot + 1, z_bot + 2, 5)
        elif i % 3 == 1:
            fill_sym_box(grid, 1, 1, y, y, z_bot, z_bot, 2)
        # Hollow core along center
        if 1 <= i <= 13:
            fill_sym_box(grid, 0, 0, y, y, z_bot + 1, z_bot + 2, 0)

    # Hydraulic Boom-Lift Cylinder connecting turntable (Y=15, Z=9) up to boom underside (Y=20, Z=18)
    # Use 6-connected staircase (fill both vertical and horizontal step) so zero voxels float!
    prev_y = 15
    for k in range(10):
        cy = 15 + (k * 5) // 9
        cz = 9 + k
        col = 4 if k < 5 else 6  # Gunmetal cylinder + gleaming chrome piston rod
        fill_sym_box(grid, 0, 0, min(prev_y, cy), max(prev_y, cy), cz, cz, col)
        prev_y = cy

    # Hazard black-and-yellow telescopic collar at Stage 1 -> Stage 2 junction (Y: 23..24)
    fill_sym_box(grid, 0, 1, 23, 24, 20, 23, 3)
    fill_sym_box(grid, 0, 1, 24, 24, 21, 22, 1)

    # Stage 2: Brushed steel inner telescopic extension (Y: 24..33, rising Z: 21..26)
    for i in range(10):
        y = 24 + i
        z_bot = 21 + (i * 4) // 9
        fill_sym_box(grid, 0, 1, y, y, z_bot, z_bot + 2, 5)
        # Hollow unseen center of Stage 2 except ends
        if 1 <= i <= 8:
            fill_sym_box(grid, 0, 0, y, y, z_bot + 1, z_bot + 1, 0)
        # Yellow top spine stripe
        fill_sym_box(grid, 0, 0, y, y, z_bot + 2, z_bot + 2, 1)

    # Stage 3: Boom Head Sheave & Pulley Assembly (Y: 34..38, Z: 24..27)
    fill_sym_box(grid, 0, 1, 34, 37, 24, 27, 1)
    fill_sym_box(grid, 1, 1, 35, 37, 25, 26, 3)  # Hazard cheek plates
    fill_sym_box(grid, 0, 0, 37, 38, 24, 26, 6)  # Chrome tip pulley wheel
    fill_sym_box(grid, 0, 0, 35, 35, 27, 27, 8)  # Tip aviation warning beacon

    # --- HOIST CABLE & HEAVY METAL HOOK DANGLING CLEAR IN FRONT OF CAB (Y: 36..39, Z: 13..24) ---
    # Sleek 1-voxel steel hoist cable descending cleanly from pulley tip
    fill_box(grid, cx_r, cx_r, 37, 37, 19, 24, 5)
    # Heavy yellow-and-black hazard pulley hook block (Y: 36..38, Z: 17..18)
    fill_sym_box(grid, 0, 1, 36, 38, 17, 18, 1)
    fill_sym_box(grid, 1, 1, 36, 38, 17, 17, 3)  # Hazard stripe
    fill_box(grid, cx_r, cx_r, 37, 37, 16, 16, 4)  # Swivel shackle
    # Iconic J-shaped gleaming chrome heavy crane hook hanging clearly above cab nose (Z: 12..15)
    fill_box(grid, cx_r, cx_r, 37, 37, 13, 15, 6)  # Hook shank
    fill_box(grid, cx_r, cx_r, 37, 39, 12, 13, 6)  # Bottom hook saddle curve
    fill_box(grid, cx_r, cx_r, 39, 39, 14, 15, 6)  # Upward curved hook tip
    fill_box(grid, cx_r, cx_r, 38, 38, 15, 15, 8)  # Red safety latch

    return grid


# ==========================================
# FORM B: HEROIC CRANE ROBOT (34 x 28 x 42)
# ==========================================
def build_b():
    grid = np.zeros((34, 28, 42), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 16 (-X robot left, viewer's right)
    cx_r = grid.shape[0] // 2      # 17 (+X robot right, viewer's left)

    # --- HEAVY OUTRIGGER STABILIZER BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 3, 7, 8, 17, 0, 1, 3)    # Heavy rubber stabilizer pads
    fill_sym_box(grid, 3, 7, 7, 9, 0, 2, 4)     # Gunmetal heel spurs
    fill_sym_box(grid, 3, 7, 11, 17, 1, 2, 1)   # Yellow armored boot shell
    fill_sym_box(grid, 4, 6, 10, 16, 1, 1, 0)   # Hollow unseen boot interior
    fill_sym_box(grid, 4, 6, 14, 18, 1, 2, 2)   # Deep ochre toe bumper
    fill_sym_box(grid, 4, 6, 18, 18, 1, 1, 3)   # Hazard black toe edge
    fill_sym_box(grid, 5, 5, 18, 18, 1, 2, 1)   # Hazard yellow center stripe

    # --- HEAVY WHEEL-MOUNTED LOWER LEGS / SHINS (Z: 3..15) ---
    fill_sym_box(grid, 3, 6, 9, 14, 3, 14, 1)
    fill_sym_box(grid, 4, 5, 10, 13, 4, 13, 0)  # Hollow leg interior
    fill_sym_box(grid, 3, 6, 14, 14, 4, 12, 2)  # Ochre front shin armor
    fill_sym_box(grid, 4, 5, 14, 15, 5, 11, 4)  # Folded outrigger jack on shin front
    fill_sym_box(grid, 4, 5, 15, 15, 6, 9, 5)   # Steel piston on shin
    fill_sym_box(grid, 3, 3, 10, 13, 4, 13, 4)  # Inner gunmetal leg frame
    # Heavy knee guards with hazard stripe
    fill_sym_box(grid, 3, 6, 14, 16, 12, 15, 1)
    fill_sym_box(grid, 4, 5, 16, 16, 13, 15, 3)
    fill_sym_box(grid, 4, 5, 16, 16, 14, 14, 1)
    # Dual tandem rear crane wheels mounted along outer calves (x_off: 7..8)
    for wz in (5.0, 10.5):
        fill_sym_wheel_x(
            grid, 7, 8, cy=11.0, cz=wz,
            r_outer=2.45, r_rim=1.35, r_hub=0.65,
            tire_col=3, rim_col=1, hub_col=6,
        )
    # Rear calf mudguard & red tail lights
    fill_sym_box(grid, 4, 6, 8, 9, 5, 12, 4)
    fill_sym_box(grid, 5, 6, 8, 8, 11, 12, 8)

    # --- MECHANICAL THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 3, 6, 9, 13, 15, 20, 4)
    fill_sym_box(grid, 4, 5, 10, 12, 2, 19, 0)  # Continuous hollow interior through shin & thigh
    fill_sym_box(grid, 3, 6, 13, 14, 16, 19, 5)  # Brushed steel thigh plates
    fill_sym_box(grid, 6, 6, 10, 12, 16, 19, 2)  # Outer ochre trim

    # --- WAIST / HEAVY HAZARD PELVIS (Z: 19..23) ---
    fill_sym_box(grid, 0, 6, 9, 13, 20, 22, 4)
    fill_sym_box(grid, 0, 5, 10, 12, 20, 23, 0)  # Hollow waist & lower torso floor core
    # Front waist skirts with yellow/black hazard belt
    fill_sym_box(grid, 2, 5, 13, 14, 19, 22, 1)
    fill_sym_box(grid, 2, 5, 14, 14, 21, 21, 3)
    fill_sym_box(grid, 3, 3, 14, 14, 21, 21, 1)
    # Center codpiece
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 2)
    fill_sym_box(grid, 0, 1, 15, 15, 20, 22, 1)
    fill_sym_box(grid, 0, 0, 15, 15, 21, 21, 8)  # Red buckle accent
    # Side hip outrigger armor guards
    fill_sym_box(grid, 6, 7, 9, 13, 20, 22, 1)
    fill_sym_box(grid, 7, 7, 10, 12, 20, 21, 3)

    # --- TORSO & PROMINENT TRUCK CAB CHEST (Z: 23..33) ---
    # Core torso housing
    fill_sym_box(grid, 0, 6, 8, 14, 23, 32, 1)
    fill_sym_box(grid, 0, 5, 9, 13, 24, 31, 0)  # Hollow torso core
    # Recessed gunmetal mechanical abs
    fill_sym_box(grid, 0, 4, 13, 14, 23, 24, 4)
    fill_sym_box(grid, 1, 3, 14, 14, 23, 24, 5)
    # PROMINENT CRANE TRUCK CAB CHEST (Y: 14..18, Z: 24..32)
    fill_sym_box(grid, 0, 5, 14, 17, 25, 31, 1)
    fill_sym_box(grid, 0, 4, 14, 17, 25, 31, 0)  # Hollow cab chest & partition wall interior
    fill_sym_box(grid, 0, 4, 14, 17, 32, 32, 1)  # Cab roof chest collar
    fill_sym_box(grid, 0, 5, 18, 18, 25, 30, 1)  # Front cab fascia
    # Broad Cyan Truck Cab Windshield across Upper Chest (Z: 28..30, Y: 18)
    fill_sym_box(grid, 0, 4, 18, 18, 28, 30, 7)
    fill_sym_box(grid, 0, 0, 18, 18, 28, 30, 3)  # Center windshield pillar
    fill_sym_box(grid, 4, 4, 18, 18, 28, 30, 3)  # Outer windshield frame
    # Truck Radiator Grille & Bright Glowing Headlights on Lower Chest (Z: 25..27, Y: 18)
    fill_sym_box(grid, 0, 2, 18, 18, 25, 27, 3)
    fill_sym_box(grid, 0, 2, 18, 18, 26, 26, 6)  # Chrome grille slat
    fill_sym_box(grid, 3, 4, 18, 18, 25, 26, 9)  # Twin warm glowing headlights!
    fill_sym_box(grid, 5, 5, 17, 18, 25, 26, 2)  # Deep ochre side cheek
    # Hazard black-and-yellow front truck bumper along bottom of chest (Z: 24, Y: 17..18)
    fill_sym_box(grid, 0, 4, 17, 18, 24, 24, 1)
    for hx in (0, 2, 4):
        fill_sym_box(grid, hx, hx, 18, 18, 24, 24, 3)
    # Twin Red Cab Roof Warning Beacons perched on upper chest corners!
    fill_sym_box(grid, 4, 4, 14, 15, 32, 33, 8)
    # Collar armor framing neck
    fill_sym_box(grid, 2, 4, 10, 13, 32, 33, 2)

    # --- TURNTABLE & COUNTERWEIGHT BACKPACK (Y: 4..8, Z: 22..33) ---
    # Heavy rear counterweight block at mid/lower back
    fill_sym_box(grid, 0, 5, 5, 8, 22, 31, 4)
    fill_sym_box(grid, 0, 4, 6, 8, 23, 30, 0)  # Hollow backpack & rear torso partition wall
    # Circular/octagonal gunmetal & steel slewing turntable gear on upper back (Y: 4..5, Z: 26..32)
    fill_sym_box(grid, 0, 3, 4, 5, 26, 32, 4)
    fill_sym_box(grid, 0, 2, 5, 5, 27, 31, 0)  # Hollow behind turntable face
    fill_sym_box(grid, 0, 2, 4, 4, 27, 31, 5)  # Steel turntable ring
    fill_sym_box(grid, 0, 1, 4, 4, 28, 30, 3)  # Inner gear hub
    fill_sym_box(grid, 0, 0, 4, 4, 29, 29, 6)  # Chrome center axle
    # Lower counterweight hazard stripes & red warning lights
    fill_sym_box(grid, 0, 4, 4, 5, 22, 25, 1)
    fill_sym_box(grid, 0, 3, 5, 5, 23, 24, 0)  # Hollow behind counterweight face
    for hx in (1, 3):
        fill_sym_box(grid, hx, hx, 4, 4, 23, 24, 3)
    fill_sym_box(grid, 4, 4, 4, 4, 25, 25, 8)  # Red rear warning lights
    # Twin hydraulic crane stabilizer pipes rising behind shoulders
    fill_sym_box(grid, 4, 5, 6, 7, 31, 35, 5)
    fill_sym_box(grid, 4, 5, 6, 7, 34, 35, 4)

    # --- HEAVY SHOULDER PAULDRONS WITH FRONT WHEELS (Z: 27..35, x_off: 6..11) ---
    # Shoulder axle bridge
    fill_sym_box(grid, 6, 8, 10, 12, 29, 31, 4)
    # Massive yellow & ochre angular construction pauldrons
    fill_sym_box(grid, 7, 11, 8, 14, 28, 34, 1)
    fill_sym_box(grid, 8, 10, 9, 13, 29, 33, 0)  # Hollow shoulder interior
    fill_sym_box(grid, 7, 10, 9, 13, 35, 35, 2)  # Top ochre armor cap
    fill_sym_box(grid, 7, 11, 14, 14, 29, 33, 2)  # Front pauldron bevel
    # Hazard black-and-yellow stripe across upper shoulder front
    fill_sym_box(grid, 8, 10, 14, 14, 32, 33, 3)
    fill_sym_box(grid, 9, 9, 14, 14, 32, 33, 1)
    # Front crane wheels integrated onto outer shoulder sides (x_off: 11..12)
    fill_sym_wheel_x(
        grid, 11, 12, cy=11.0, cz=31.0,
        r_outer=2.45, r_rim=1.35, r_hub=0.65,
        tire_col=3, rim_col=1, hub_col=6,
    )

    # --- UPPER ARMS & FOREARMS (Z: 15..28) ---
    # Rugged gunmetal upper arms
    fill_sym_box(grid, 8, 10, 10, 12, 23, 28, 4)
    fill_sym_box(grid, 9, 9, 11, 11, 24, 27, 0)  # Hollow upper arm core
    fill_sym_box(grid, 9, 10, 10, 12, 25, 26, 5)  # Steel elbow hydraulic band
    # Blocky armored yellow forearms
    fill_sym_box(grid, 8, 11, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 9, 10, 10, 13, 18, 21, 0)  # Hollow forearm interior
    fill_sym_box(grid, 8, 11, 14, 14, 18, 21, 2)  # Front ochre forearm cuff
    fill_sym_box(grid, 9, 10, 14, 14, 19, 20, 3)  # Hazard cuff band

    # --- RIGHT ARM (+X, viewer's left): MASSIVE TELESCOPIC BOOM CANNON + HOOK CLAW ---
    # Mounted solidly on outer/upper right forearm (X: cx_r + 10..13 = 27..30), angled boldly forward & up!
    # Cleanly clear below the right shoulder pauldron (shoulder bottom is Z=28, cannon top stays <= Z=25!)
    # Heavy breech & turntable clamp anchored into right forearm (Y: 6..16, Z: 19..23)
    fill_box(grid, cx_r + 10, cx_r + 13, 7, 16, 19, 23, 1)
    fill_box(grid, cx_r + 10, cx_r + 12, 8, 15, 20, 22, 0)  # Hollow cannon breech & forearm join
    # Rear counterweight cap & gunmetal breech block
    fill_box(grid, cx_r + 10, cx_r + 13, 5, 7, 19, 23, 4)
    fill_box(grid, cx_r + 11, cx_r + 12, 6, 6, 20, 22, 0)   # Hollow rear breech
    fill_box(grid, cx_r + 11, cx_r + 12, 5, 5, 20, 22, 8)   # Red breech status light
    # Hazard black-and-yellow stripes along outer yellow boom cannon casing
    for by in (9, 12, 15):
        fill_box(grid, cx_r + 13, cx_r + 13, by, by, 20, 22, 3)
    # Top hydraulic recoil rail on boom cannon
    fill_box(grid, cx_r + 11, cx_r + 12, 9, 17, 24, 24, 5)
    fill_box(grid, cx_r + 11, cx_r + 12, 10, 11, 24, 24, 4)
    # Telescopic Stage 2 brushed steel cannon barrel extending boldly forward & slightly up (Y: 17..25, Z: 20..24)
    fill_box(grid, cx_r + 10, cx_r + 13, 16, 17, 19, 23, 3)  # Black telescopic collar
    fill_box(grid, cx_r + 10, cx_r + 12, 18, 22, 20, 23, 5)  # Steel barrel mid
    fill_box(grid, cx_r + 10, cx_r + 12, 22, 25, 21, 24, 5)  # Slightly elevated outer telescopic barrel
    fill_box(grid, cx_r + 11, cx_r + 11, 19, 24, 21, 23, 0)  # Hollow bore
    fill_box(grid, cx_r + 11, cx_r + 12, 18, 21, 23, 23, 1)  # Yellow upper barrel rail
    fill_box(grid, cx_r + 11, cx_r + 12, 22, 24, 24, 24, 1)  # Yellow raised barrel rail
    # Cannon muzzle brake & glowing energy core (Y: 26..27, Z: 21..24)
    fill_box(grid, cx_r + 10, cx_r + 12, 26, 27, 21, 24, 4)
    fill_box(grid, cx_r + 11, cx_r + 11, 26, 27, 22, 23, 9)  # Glowing cannon core!
    fill_box(grid, cx_r + 10, cx_r + 12, 26, 26, 24, 24, 8)  # Red targeting sight
    # Right Wrist & Under-slung Steel Grapple-Claw Hand (Z: 14..16, Y: 10..16)
    fill_box(grid, cx_r + 8, cx_r + 10, 10, 13, 15, 16, 4)   # Right wrist
    fill_box(grid, cx_r + 8, cx_r + 10, 14, 16, 15, 16, 6)   # Chrome twin hook fingers
    fill_box(grid, cx_r + 9, cx_r + 9, 15, 16, 15, 15, 0)    # Claw gap

    # --- LEFT HAND (-X, viewer's right): ICONIC CRANE PULLEY BLOCK & GIANT CURVED HOOK CLAW ---
    # Heavy yellow-and-black hazard pulley-sheave cuff on left wrist (X: cx_l - 11..-8, Y: 10..14, Z: 14..16)
    fill_box(grid, cx_l - 11, cx_l - 8, 10, 14, 14, 16, 1)
    fill_box(grid, cx_l - 10, cx_l - 9, 11, 13, 15, 15, 0)   # Hollow wrist block
    fill_box(grid, cx_l - 11, cx_l - 8, 11, 11, 14, 16, 3)   # Hazard stripe
    fill_box(grid, cx_l - 11, cx_l - 8, 13, 13, 14, 16, 3)   # Hazard stripe
    fill_box(grid, cx_l - 10, cx_l - 9, 14, 15, 15, 16, 4)   # Heavy steel swivel shackle
    # Giant curved gleaming chrome Crane Hook Claw with unmistakable open J-curve (Y: 15..21, Z: 11..16)
    fill_box(grid, cx_l - 10, cx_l - 9, 15, 16, 12, 15, 6)   # Hook stem descending
    fill_box(grid, cx_l - 10, cx_l - 9, 16, 20, 11, 12, 6)   # Heavy curved lower hook saddle
    fill_box(grid, cx_l - 10, cx_l - 9, 20, 21, 12, 15, 6)   # Swept upward sharp hook tip
    fill_box(grid, cx_l - 10, cx_l - 9, 17, 19, 13, 14, 0)   # Crisp open hook throat gap!
    fill_box(grid, cx_l - 10, cx_l - 9, 17, 18, 15, 15, 8)   # Red safety latch bar
    # Compact steel winch cable spool mounted on outer left forearm
    fill_box(grid, cx_l - 12, cx_l - 12, 10, 13, 18, 21, 4)
    fill_box(grid, cx_l - 12, cx_l - 12, 11, 12, 19, 20, 5)

    # --- HEROIC HARD-HAT CONSTRUCTION HEAD & VISOR (Z: 33..41) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 4)
    # Main head block
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 1)
    fill_sym_box(grid, 0, 1, 10, 12, 35, 37, 0)  # Hollow head core
    # Iconic construction hard-hat helmet crown & visor brim
    fill_sym_box(grid, 0, 3, 9, 14, 38, 39, 1)
    fill_sym_box(grid, 0, 2, 10, 13, 40, 40, 2)  # Ochre hard-hat ridge
    fill_sym_box(grid, 0, 2, 14, 15, 38, 38, 3)  # Hazard visor trim
    # Bright cyan wrap-around visor
    fill_sym_box(grid, 0, 2, 14, 14, 36, 37, 7)
    # Brushed chrome faceplate mouthguard
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 6)
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 4)
    # Side helmet ear pods
    fill_sym_box(grid, 3, 3, 10, 12, 35, 37, 2)
    fill_sym_box(grid, 3, 3, 11, 11, 36, 37, 6)
    # Red forehead warning beacon jewel & swept V-crest antennae
    fill_sym_box(grid, 0, 0, 15, 15, 38, 39, 8)
    fill_sym_box(grid, 1, 1, 14, 15, 39, 40, 1)
    fill_sym_box(grid, 2, 3, 13, 14, 40, 41, 1)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=24, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "crane_a.vox")
    v_b = export_vox(model_b, "crane_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: MOBILE CRANE TRUCK -> CRANE CANNON ROBOT",
        "1. MOBILE CRANE TRUCK",
        "2. CRANE CANNON ROBOT",
        "preview_crane.png",
        yaw_a=40, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"crane: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
