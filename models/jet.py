import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (244, 247, 252, 255),  # Crisp Airline Fuselage White
    2: (190, 200, 214, 255),  # Metallic Wing Silver / Belly Shading
    3: (22, 82, 188, 255),    # Royal Airline Blue (Livery & Tail)
    4: (216, 40, 56, 255),    # Crimson Airline Stripe & Accent
    5: (40, 46, 58, 255),     # Dark Charcoal Landing Gear / Joints
    6: (26, 44, 78, 255),     # Deep Tinted Cockpit & Passenger Windows
    7: (96, 218, 255, 255),   # Sky Cyan Glass Glint / Visor / Turbine Glow
    8: (255, 206, 72, 255),   # Warm Gold Engine Intake Ring / Chest Core
    9: (116, 128, 146, 255),  # Gunmetal Engine Cowling / Steel Detail
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


# ==========================================
# FORM A: PASSENGER JET (46 x 48 x 18)
# ==========================================
def build_a():
    grid = np.zeros((46, 48, 18), dtype=np.uint8)

    # --- MAIN FUSELAGE (Y: 12..36, Z: 2..9) - Rounded 8x8 cross-section ---
    fill_sym_box(grid, 0, 1, 12, 36, 2, 2, 2)  # Silver lower belly
    fill_sym_box(grid, 0, 2, 12, 36, 3, 3, 2)  # Silver lower chine
    fill_sym_box(grid, 0, 3, 12, 36, 4, 7, 1)  # Crisp white cabin walls
    fill_sym_box(grid, 0, 2, 12, 36, 8, 8, 1)  # Upper cabin shoulder
    fill_sym_box(grid, 0, 1, 12, 36, 9, 9, 1)  # Roof crown

    # Hollow unseen cabin interior to keep voxel count lean and crisp
    fill_sym_box(grid, 0, 1, 13, 35, 4, 7, 0)

    # Royal blue & crimson airline livery stripes along both flanks
    fill_sym_box(grid, 3, 3, 12, 36, 4, 4, 3)  # Royal blue cheatline
    fill_sym_box(grid, 3, 3, 12, 36, 5, 5, 4)  # Crimson pinstripe

    # Row of dark passenger windows along both flanks (Z=6)
    for wy in range(13, 36, 2):
        fill_sym_box(grid, 3, 3, wy, wy, 6, 6, 6)
    # Cabin entry doors with subtle silver frame
    fill_sym_box(grid, 3, 3, 35, 35, 5, 7, 2)
    fill_sym_box(grid, 3, 3, 13, 13, 5, 7, 2)
    # Top fuselage anti-collision beacon & sleek satcom fairing
    fill_sym_box(grid, 0, 0, 24, 24, 10, 10, 4)
    fill_sym_box(grid, 0, 0, 16, 18, 10, 10, 1)

    # --- NOSE & COCKPIT SECTION (Y: 37..46, +Y is FRONT) ---
    # Y: 37..39
    fill_sym_box(grid, 0, 1, 37, 39, 3, 3, 2)
    fill_sym_box(grid, 0, 2, 37, 39, 4, 7, 1)
    fill_sym_box(grid, 0, 1, 37, 38, 8, 8, 1)
    fill_sym_box(grid, 2, 2, 37, 39, 4, 4, 3)  # Blue stripe taper
    fill_sym_box(grid, 2, 2, 37, 39, 5, 5, 4)  # Crimson stripe taper

    # Y: 40..42 (Nose taper + cockpit brow)
    fill_sym_box(grid, 0, 1, 40, 42, 3, 3, 2)
    fill_sym_box(grid, 0, 2, 40, 41, 4, 6, 1)
    fill_sym_box(grid, 0, 1, 42, 42, 4, 6, 1)
    fill_sym_box(grid, 2, 2, 40, 41, 4, 4, 3)
    fill_sym_box(grid, 2, 2, 40, 41, 5, 5, 4)
    fill_sym_box(grid, 1, 1, 42, 42, 4, 4, 3)
    fill_sym_box(grid, 1, 1, 42, 42, 5, 5, 4)

    # Dark wrap-around cockpit windshield with cyan glint
    fill_sym_box(grid, 0, 2, 39, 40, 6, 7, 6)
    fill_sym_box(grid, 0, 1, 41, 41, 6, 7, 6)
    fill_sym_box(grid, 0, 1, 40, 41, 7, 7, 7)  # Cyan windshield reflection
    fill_sym_box(grid, 2, 2, 39, 39, 6, 6, 6)

    # Aerodynamic nose radome (Y: 43..46)
    fill_sym_box(grid, 0, 1, 43, 44, 4, 5, 1)
    fill_sym_box(grid, 1, 1, 43, 44, 4, 4, 3)
    fill_sym_box(grid, 0, 0, 45, 46, 4, 5, 1)
    fill_sym_box(grid, 0, 0, 46, 46, 4, 4, 2)

    # --- REAR TAIL CONE (Y: 2..11, -Y is REAR) ---
    # Smoothly slopes upward from belly to APU tail cone
    fill_sym_box(grid, 0, 2, 9, 11, 4, 7, 1)
    fill_sym_box(grid, 0, 1, 9, 11, 3, 3, 2)
    fill_sym_box(grid, 0, 1, 9, 11, 8, 8, 1)
    fill_sym_box(grid, 2, 2, 9, 11, 4, 5, 3)
    fill_sym_box(grid, 2, 2, 9, 11, 6, 6, 4)

    fill_sym_box(grid, 0, 1, 6, 8, 5, 8, 1)
    fill_sym_box(grid, 1, 1, 6, 8, 5, 6, 3)
    fill_sym_box(grid, 1, 1, 6, 8, 7, 7, 4)

    fill_sym_box(grid, 0, 1, 3, 5, 6, 7, 1)
    fill_sym_box(grid, 1, 1, 3, 5, 6, 6, 3)
    fill_sym_box(grid, 0, 0, 2, 2, 6, 7, 9)  # Gunmetal APU exhaust
    fill_sym_box(grid, 0, 0, 2, 2, 6, 6, 5)  # Dark exhaust port

    # --- SWEPT MAIN WINGS (X_off: 3..21, swept back along Y with smooth 6-connected dihedral) ---
    # Wing root fairing connecting solidly into fuselage
    fill_sym_box(grid, 3, 4, 18, 30, 3, 4, 2)
    prev_z = 4
    for step in range(18):
        xo = 4 + step
        # Leading edge sweeps back from y=29 at root to y=15 at tip
        y_lead = 29 - int(step * 0.80)
        # Chord tapers from 9 voxels at root down to 3 voxels at tip
        chord = max(3, 9 - int(step * 0.36))
        y_trail = y_lead - chord + 1
        # Gentle upward dihedral
        z_wing = 4 if step < 7 else (5 if step < 14 else 6)
        # Main wing airfoil (white upper, silver trailing flaps)
        fill_sym_box(grid, xo, xo, y_trail, y_lead, z_wing, z_wing, 1)
        # Ensure solid 6-connected bridge whenever dihedral steps up
        if z_wing > prev_z:
            fill_sym_box(grid, xo, xo, y_trail, y_lead, prev_z, prev_z, 2)
        if step < 6:
            # Thicker inner wing root for clean structural transition
            fill_sym_box(grid, xo, xo, y_trail + 1, y_lead - 1, z_wing - 1, z_wing - 1, 2)
        # Silver trailing edge flaps / ailerons
        fill_sym_box(grid, xo, xo, y_trail, y_trail, z_wing, z_wing, 2)
        # Royal blue & crimson airline wing accent near outer section
        if 14 <= step <= 17:
            fill_sym_box(grid, xo, xo, y_lead - 1, y_lead, z_wing, z_wing, 3)
            if step >= 16:
                fill_sym_box(grid, xo, xo, y_trail + 1, y_lead - 2, z_wing, z_wing, 4)
        prev_z = z_wing

    # Upturned aerodynamic winglets (X_off: 21..22, Z: 6..9, solidly 6-connected)
    fill_sym_box(grid, 21, 21, 13, 15, 6, 7, 3)
    fill_sym_box(grid, 22, 22, 12, 14, 7, 8, 3)
    fill_sym_box(grid, 22, 22, 12, 13, 9, 9, 4)
    fill_sym_box(grid, 22, 22, 14, 14, 8, 8, 8)  # Wingtip navigation strobe

    # --- TWIN UNDER-WING TURBOFAN JET ENGINES (X_off: 7..10, Y: 20..29, Z: 1..4) ---
    # Pylons linking engines solidly to main wings
    fill_sym_box(grid, 8, 9, 22, 26, 4, 4, 9)
    fill_sym_box(grid, 8, 9, 23, 25, 3, 4, 2)

    # Cylindrical engine nacelles (4x4 rounded cross-section: X_off 7..10, Z 1..4)
    fill_sym_box(grid, 8, 9, 22, 28, 1, 4, 1)
    fill_sym_box(grid, 7, 10, 22, 28, 2, 3, 1)
    # Royal blue & crimson livery bands around nacelle cowling
    fill_sym_box(grid, 7, 10, 25, 26, 2, 3, 3)
    fill_sym_box(grid, 8, 9, 25, 26, 1, 1, 3)
    fill_sym_box(grid, 8, 9, 25, 26, 4, 4, 3)
    fill_sym_box(grid, 7, 10, 24, 24, 2, 3, 4)
    fill_sym_box(grid, 8, 9, 24, 24, 1, 1, 4)

    # Front gold intake lip ring + dark turbine cavity + glowing cyan spinner (Y: 28..29)
    fill_sym_box(grid, 8, 9, 29, 29, 1, 4, 8)
    fill_sym_box(grid, 7, 10, 29, 29, 2, 3, 8)
    fill_sym_box(grid, 8, 9, 29, 29, 2, 3, 5)  # Dark intake throat
    fill_sym_box(grid, 8, 9, 28, 28, 2, 3, 7)  # Glowing cyan turbofan core
    fill_sym_box(grid, 8, 8, 29, 29, 2, 2, 7)  # Bright turbine spinner tip

    # Rear gunmetal exhaust nozzle cone (Y: 20..21)
    fill_sym_box(grid, 8, 9, 20, 21, 2, 3, 9)
    fill_sym_box(grid, 8, 9, 20, 20, 2, 2, 5)

    # --- TALL SWEPT VERTICAL TAIL STABILIZER (X_off: 0, Z: 8..17) ---
    for dz in range(10):
        z = 8 + dz
        y_front = 14 - dz
        y_back = max(1, 5 - dz // 2)
        # Main royal blue airline tail fin
        fill_sym_box(grid, 0, 0, y_back, y_front, z, z, 3)
        # Crisp white leading edge
        fill_sym_box(grid, 0, 0, y_front, y_front, z, z, 1)
        # Bold crimson diagonal airline logo stripe across the fin
        slash_y0 = max(y_back, y_front - 3)
        slash_y1 = max(y_back, y_front - 2)
        if dz >= 1:
            fill_sym_box(grid, 0, 0, slash_y0, slash_y1, z, z, 4)
        # Gold airline crest accent stripe
        if 3 <= dz <= 7 and y_front - 4 >= y_back:
            fill_sym_box(grid, 0, 0, y_front - 4, y_front - 4, z, z, 8)
    # Fin tip highlight
    fill_sym_box(grid, 0, 0, 1, 5, 17, 17, 4)
    fill_sym_box(grid, 0, 0, 4, 5, 17, 17, 8)

    # --- HORIZONTAL TAIL STABILIZERS (X_off: 1..9, Z: 6..7, 6-connected) ---
    prev_zh = 6
    for step in range(9):
        xo = 1 + step
        y_lead = 9 - int(step * 0.65)
        y_trail = max(2, y_lead - max(2, 5 - step // 2) + 1)
        z_h = 6 if step < 4 else 7
        fill_sym_box(grid, xo, xo, y_trail, y_lead, z_h, z_h, 1)
        if z_h > prev_zh:
            fill_sym_box(grid, xo, xo, y_trail, y_lead, prev_zh, prev_zh, 2)
        fill_sym_box(grid, xo, xo, y_trail, y_trail, z_h, z_h, 2)
        if step >= 7:
            fill_sym_box(grid, xo, xo, y_trail, y_lead, z_h, z_h, 3)
        prev_zh = z_h

    # --- LANDING GEAR (Z: 0..3) - Grounded solidly at Z=0 ---
    # Nose gear (Y: 38..39)
    fill_sym_box(grid, 0, 0, 38, 39, 1, 3, 9)  # Strut
    fill_sym_box(grid, 0, 0, 38, 39, 0, 1, 5)  # Dual nose wheels
    fill_sym_box(grid, 0, 0, 39, 39, 2, 2, 8)  # Taxi light

    # Twin main landing gear bogies under wing roots (X_off: 3..4, Y: 20..23)
    fill_sym_box(grid, 3, 3, 21, 22, 1, 3, 9)  # Struts joining wing root
    fill_sym_box(grid, 3, 4, 20, 23, 0, 1, 5)  # Heavy multi-wheel bogies
    fill_sym_box(grid, 4, 4, 21, 22, 0, 0, 9)  # Wheel hubs

    return grid


# ==========================================
# FORM B: JETLINER SKY ROBOT (40 x 24 x 44)
# ==========================================
def build_b():
    grid = np.zeros((40, 24, 44), dtype=np.uint8)

    # --- FEET (Z: 0..2) - Wide planted landing-gear soles + armored jet toes ---
    fill_sym_box(grid, 3, 6, 8, 15, 0, 1, 5)   # Dark charcoal grounded soles
    fill_sym_box(grid, 3, 6, 12, 16, 1, 2, 3)  # Royal blue armored toe caps
    fill_sym_box(grid, 4, 5, 14, 16, 2, 2, 1)  # White aero toe ridge
    fill_sym_box(grid, 3, 3, 15, 16, 1, 1, 4)  # Crimson inner toe trim
    fill_sym_box(grid, 3, 6, 7, 9, 0, 2, 9)    # Gunmetal heel landing struts

    # --- LOWER LEGS (Z: 3..14) - Split White Fuselage Halves w/ Windows & Stripes ---
    # Sleek ankle taper at Z=3..4 widening into fuselage shins at Z=5..14
    fill_sym_box(grid, 3, 5, 9, 13, 3, 4, 2)
    fill_sym_box(grid, 3, 6, 9, 14, 5, 14, 1)   # Crisp white fuselage leg armor
    fill_sym_box(grid, 4, 5, 10, 12, 6, 13, 0)  # Hollow unseen shin interior
    # Royal blue & crimson airline stripes running vertically along leg flanks
    fill_sym_box(grid, 6, 6, 10, 13, 5, 13, 3)  # Outer blue fuselage livery
    fill_sym_box(grid, 6, 6, 13, 13, 5, 13, 4)  # Outer crimson stripe
    fill_sym_box(grid, 3, 3, 14, 14, 5, 13, 3)  # Inner shin royal blue trim
    # Vertical row of passenger windows on outer calf (Form A fuselage motif!)
    for wz in (6, 8, 10, 12):
        fill_sym_box(grid, 6, 6, 11, 11, wz, wz, 6)
        fill_sym_box(grid, 6, 6, 12, 12, wz, wz, 7)
    # Sculpted aerospace knee guards
    fill_sym_box(grid, 3, 5, 14, 15, 12, 15, 3)
    fill_sym_box(grid, 4, 4, 15, 16, 13, 14, 1)
    fill_sym_box(grid, 4, 4, 15, 15, 12, 12, 8)  # Gold knee sensor
    # Folded horizontal tail stabilizers mounted vertically on rear calves
    for dz in range(8):
        z = 4 + dz
        y_back = 7 - min(2, dz // 3)
        fill_sym_box(grid, 4, 5, y_back, 8, z, z, 1)
        fill_sym_box(grid, 4, 4, y_back, y_back, z, z, 2)
    fill_sym_box(grid, 4, 5, 5, 6, 10, 11, 3)
    fill_sym_box(grid, 4, 5, 5, 5, 11, 11, 4)

    # --- THIGHS (Z: 15..20) - Tapered heroic stance ---
    fill_sym_box(grid, 3, 5, 10, 13, 15, 17, 2)  # Lower thigh
    fill_sym_box(grid, 2, 4, 10, 13, 18, 20, 2)  # Upper thigh angled inward to hip
    fill_sym_box(grid, 3, 5, 13, 14, 16, 18, 1)  # White front thigh plates
    fill_sym_box(grid, 2, 4, 13, 14, 18, 19, 1)
    fill_sym_box(grid, 5, 5, 11, 12, 16, 17, 3)  # Blue side stripe
    fill_sym_box(grid, 3, 4, 10, 12, 15, 15, 5)  # Dark knee joint

    # --- WAIST / PELVIS (Z: 20..23) ---
    fill_sym_box(grid, 0, 4, 9, 14, 20, 22, 5)   # Charcoal waist frame
    fill_sym_box(grid, 0, 3, 13, 15, 21, 22, 1)  # White front skirt plates
    fill_sym_box(grid, 2, 3, 14, 15, 20, 21, 1)  # Split lower front skirts
    fill_sym_box(grid, 2, 3, 15, 15, 20, 20, 4)  # Crimson skirt hem
    fill_sym_box(grid, 0, 1, 14, 15, 20, 23, 3)  # Royal blue central codpiece
    fill_sym_box(grid, 0, 0, 15, 15, 21, 22, 8)  # Gold winged belt emblem
    fill_sym_box(grid, 4, 5, 10, 13, 20, 22, 1)  # White side hip skirts
    fill_sym_box(grid, 5, 5, 11, 12, 20, 21, 3)  # Blue hip accent

    # --- TORSO / CHEST (Z: 23..32) - Folded Passenger Jet Cockpit Nose! ---
    fill_sym_box(grid, 0, 4, 9, 14, 23, 32, 1)   # Core white fuselage chest
    fill_sym_box(grid, 0, 3, 9, 13, 23, 25, 2)   # Lower silver abdomen
    fill_sym_box(grid, 0, 3, 10, 13, 25, 30, 0)  # Hollow unseen deep torso core
    # Broad heroic chest wings / airline livery chevrons
    fill_sym_box(grid, 3, 5, 10, 14, 27, 31, 1)
    fill_sym_box(grid, 3, 5, 14, 15, 28, 30, 3)  # Royal blue chest vents
    fill_sym_box(grid, 3, 4, 14, 15, 27, 27, 4)  # Crimson lower chest stripe
    fill_sym_box(grid, 4, 4, 15, 15, 29, 29, 8)  # Gold chest intake slats
    # High heroic collar guards
    fill_sym_box(grid, 2, 4, 10, 13, 32, 33, 3)
    fill_sym_box(grid, 3, 4, 11, 13, 33, 33, 1)

    # Folded Jet Cockpit Nose projecting proudly from chest (Y: 14..18, Z: 25..31)
    fill_sym_box(grid, 0, 2, 14, 16, 25, 31, 1)  # Nose body
    fill_sym_box(grid, 0, 1, 17, 17, 25, 28, 1)  # Tapered radome nose
    fill_sym_box(grid, 0, 0, 18, 18, 25, 27, 1)  # Nose tip
    # Dark cockpit windshield with cyan glint on upper chest
    fill_sym_box(grid, 0, 2, 15, 16, 29, 31, 6)
    fill_sym_box(grid, 0, 1, 16, 16, 30, 31, 7)  # Cyan windshield reflection
    # Converging airline blue/crimson livery stripes on chest nose
    fill_sym_box(grid, 2, 2, 15, 16, 26, 26, 3)
    fill_sym_box(grid, 2, 2, 15, 16, 27, 27, 4)
    fill_sym_box(grid, 1, 1, 17, 17, 26, 26, 3)
    fill_sym_box(grid, 1, 1, 17, 17, 27, 27, 4)
    # Glowing gold & cyan sky-core emblem on nose center
    fill_sym_box(grid, 0, 0, 18, 18, 26, 26, 8)
    fill_sym_box(grid, 0, 0, 17, 17, 28, 28, 7)

    # --- BACKPACK & GRAND SWEPT JET WINGS (Y: 2..8, Z: 21..42) ---
    # Rear fuselage spine backpack
    fill_sym_box(grid, 0, 3, 6, 8, 23, 31, 2)    # Silver rear hull
    fill_sym_box(grid, 0, 2, 7, 8, 25, 30, 0)    # Hollow unseen backpack core
    fill_sym_box(grid, 0, 2, 5, 6, 24, 30, 1)    # White dorsal housing
    fill_sym_box(grid, 0, 1, 5, 5, 25, 29, 3)    # Blue spine stripe
    fill_sym_box(grid, 0, 0, 5, 5, 26, 28, 4)    # Crimson spine accent
    # Twin backpack vernier thrusters
    fill_sym_box(grid, 2, 3, 5, 6, 21, 23, 9)
    fill_sym_box(grid, 2, 3, 5, 6, 21, 21, 7)    # Glowing cyan jet exhaust

    # Grand Swept Main Jetliner Wings unfolding proudly from back (X_off: 3..19)
    fill_sym_box(grid, 3, 4, 6, 7, 26, 31, 9)    # Wing root hinge mounts
    for step in range(15):
        xo = 4 + step
        z_bot = 26 + int(step * 0.86)
        chord_h = max(3, 7 - int(step * 0.25))
        z_top = min(42, z_bot + chord_h - 1)
        # Sweep gently backward in Y for dynamic 3D swept-wing silhouette
        y_w = 6 - int(step * 0.24)
        # Main white wing blade (1-2 voxels thick, 6-connected across steps)
        fill_sym_box(grid, xo, xo, y_w, y_w + 1, z_bot, z_top, 1)
        # Silver trailing edge (bottom edge of upright wings)
        fill_sym_box(grid, xo, xo, y_w, y_w, z_bot, z_bot, 2)
        # Bold royal blue & crimson airline livery stripes across wings
        if step >= 2:
            fill_sym_box(grid, xo, xo, y_w, y_w + 1, z_top, z_top, 3)
        if 4 <= step <= 13:
            fill_sym_box(grid, xo, xo, y_w + 1, y_w + 1, z_top - 1, z_top - 1, 4)
        # Wingtip upturned winglets & navigation gold trim
        if step >= 13:
            fill_sym_box(grid, xo, xo, y_w, y_w + 1, z_bot, z_top, 3)
            fill_sym_box(grid, xo, xo, y_w + 1, y_w + 1, z_top, z_top, 4)
    # Dramatic sharp wingtip points (X_off: 18..19)
    fill_sym_box(grid, 18, 18, 3, 4, 39, 42, 3)
    fill_sym_box(grid, 19, 19, 3, 4, 41, 42, 4)
    fill_sym_box(grid, 19, 19, 4, 4, 42, 42, 8)

    # --- SHOULDERS & ARMS (Z: 14..34) - Turbofan Forearms + Wing-Blades! ---
    # Broad heroic aerospace shoulder pauldrons (X_off: 5..10, Z: 28..34)
    fill_sym_box(grid, 5, 10, 9, 14, 28, 32, 1)  # White shoulder armor
    fill_sym_box(grid, 6, 9, 10, 13, 29, 31, 0)  # Hollow unseen shoulder interior
    fill_sym_box(grid, 6, 10, 10, 13, 32, 33, 3) # Royal blue upper shoulder cap
    fill_sym_box(grid, 9, 10, 10, 13, 33, 34, 4) # Upturned crimson shoulder fin
    fill_sym_box(grid, 10, 10, 10, 13, 29, 32, 3)# Outer blue livery panel
    fill_sym_box(grid, 7, 9, 14, 14, 29, 31, 2)  # Silver front intake vent
    fill_sym_box(grid, 7, 9, 14, 14, 30, 30, 6)  # Dark intake slot
    # Shoulder joint connector to torso
    fill_sym_box(grid, 5, 6, 10, 13, 28, 31, 5)

    # Upper arms (X_off: 7..8, Z: 23..27) - Clean clearance from widened hips
    fill_sym_box(grid, 7, 8, 10, 13, 23, 27, 5)  # Charcoal frame
    fill_sym_box(grid, 7, 8, 11, 13, 24, 26, 9)  # Gunmetal armor cuff

    # Chunky Twin Turbofan Forearms (X_off: 7..10, Y: 9..15, Z: 16..22)
    fill_sym_box(grid, 7, 10, 10, 14, 16, 22, 1) # White turbofan cowling
    fill_sym_box(grid, 8, 9, 11, 13, 17, 21, 0)  # Hollow unseen forearm interior
    fill_sym_box(grid, 7, 10, 10, 14, 19, 20, 3) # Royal blue nacelle band
    fill_sym_box(grid, 7, 10, 10, 14, 18, 18, 4) # Crimson nacelle stripe
    # Forward-facing turbofan intake ring & glowing turbine core on forearm front!
    fill_sym_box(grid, 7, 10, 15, 15, 17, 20, 8) # Warm gold intake lip
    fill_sym_box(grid, 8, 9, 15, 15, 18, 19, 5)  # Dark stator throat
    fill_sym_box(grid, 8, 9, 15, 15, 18, 18, 7)  # Glowing cyan turbine core
    # Rear elbow exhaust nozzle
    fill_sym_box(grid, 8, 9, 9, 9, 20, 22, 9)
    fill_sym_box(grid, 8, 9, 9, 9, 21, 21, 5)

    # Outer Forearm Swept Wing-Blades (X_off: 11..12, Z: 15..24) - Main Wing Arms!
    for dz in range(9):
        z = 15 + dz
        y_f = 13 - dz // 3
        fill_sym_box(grid, 11, 11, y_f - 2, y_f, z, z, 1)
        fill_sym_box(grid, 11, 11, y_f - 2, y_f - 2, z, z, 2)
        if dz >= 2:
            fill_sym_box(grid, 12, 12, y_f - 2, y_f - 1, z, z, 3 if dz < 6 else 4)
    fill_sym_box(grid, 12, 12, 10, 11, 23, 24, 1)  # Sharp elbow winglet tip

    # Articulated Fists (Z: 14..15)
    fill_sym_box(grid, 7, 9, 11, 13, 14, 15, 5)

    # Right-hand Sky-Commander Aero-Blade (+X side, Y: 14..23)
    cx_r = grid.shape[0] // 2  # 20
    fill_box(grid, cx_r + 7, cx_r + 8, 13, 15, 14, 15, 9)  # Hilt
    fill_box(grid, cx_r + 7, cx_r + 8, 15, 16, 13, 16, 8)  # Gold crossguard
    fill_box(grid, cx_r + 7, cx_r + 8, 17, 21, 14, 16, 1)  # Aero wing-blade body
    fill_box(grid, cx_r + 8, cx_r + 8, 17, 22, 15, 16, 7)  # Glowing cyan energy edge
    fill_box(grid, cx_r + 7, cx_r + 8, 22, 23, 15, 15, 7)  # Piercing blade tip

    # --- HEAD & TALL VERTICAL TAIL FIN CREST (Z: 32..43) - 尾翼が頭飾り! ---
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 5)  # Charcoal neck
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 1)   # White aerospace commander helmet
    fill_sym_box(grid, 0, 2, 10, 12, 38, 38, 3)  # Royal blue crown rim
    fill_sym_box(grid, 3, 3, 10, 12, 35, 37, 3)  # Blue ear-comms pods
    fill_sym_box(grid, 3, 3, 11, 11, 36, 36, 8)  # Gold ear sensor
    # Expressive face: silver chinplate + wide glowing sky-cyan pilot visor
    fill_sym_box(grid, 0, 1, 13, 14, 34, 34, 2)  # Silver faceplate/chin
    fill_sym_box(grid, 0, 1, 13, 14, 35, 36, 7)  # Bright sky-cyan wrap-around visor
    fill_sym_box(grid, 2, 2, 13, 14, 35, 36, 6)  # Dark visor frame
    fill_sym_box(grid, 0, 2, 13, 14, 37, 37, 3)  # Royal blue helmet brow
    fill_sym_box(grid, 0, 0, 14, 14, 37, 37, 8)  # Gold forehead sensor gem

    # Sleek Swept Aero V-Fin flanking the brow (solidly 6-connected)
    fill_sym_box(grid, 1, 2, 13, 14, 38, 38, 8)
    fill_sym_box(grid, 2, 3, 13, 13, 38, 39, 8)
    fill_sym_box(grid, 3, 4, 13, 13, 39, 40, 1)

    # Tall Swept Vertical Tail Stabilizer Crest rising from helmet crown (Z: 38..43)!
    for dz in range(6):
        z = 38 + dz
        y_front = 13 - dz
        y_back = max(5, 9 - dz)
        fill_sym_box(grid, 0, 0, y_back, y_front, z, z, 3)  # Royal blue tail crest
        fill_sym_box(grid, 0, 0, y_front, y_front, z, z, 1)  # Crisp white leading edge
        if y_front - 1 >= y_back:
            fill_sym_box(grid, 0, 0, y_front - 1, y_front - 1, z, z, 4)  # Crimson stripe
        if dz >= 2 and y_front - 2 >= y_back:
            fill_sym_box(grid, 0, 0, y_front - 2, y_front - 2, z, z, 8)  # Gold crest bar
    fill_sym_box(grid, 0, 0, 5, 8, 43, 43, 4)  # Crimson crest peak

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=42, pitch_a=26, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "jet_a.vox")
    v_b = export_vox(model_b, "jet_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: PASSENGER JET -> JETLINER SKY ROBOT",
        "1. PASSENGER JET",
        "2. JETLINER SKY ROBOT",
        "preview_jet.png",
        yaw_a=42, pitch_a=26, yaw_b=32, pitch_b=20,
    )
    print(f"jet: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
